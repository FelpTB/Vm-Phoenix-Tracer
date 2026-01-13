"""
API Flask para repassar requisições do n8n para o vLLM com instrumentação Phoenix.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Optional, Dict, Any, List
from openai import OpenAI
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
import traceback


# Configurações padrão
VLLM_URL = os.getenv("VLLM_URL", "https://5u888x525vvzvs-8000.proxy.runpod.net")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "buscafornecedor")
PHOENIX_COLLECTOR_ENDPOINT = os.getenv(
    "PHOENIX_COLLECTOR_ENDPOINT",
    "https://arize-phoenix-buscafornecedor.up.railway.app"
)
PHOENIX_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "buscafornecedor-vllm")
# Railway expõe a porta via variável PORT
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8080")))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# Inicializar Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para requisições do n8n

# Configurar Phoenix
print("[SETUP] Configurando Phoenix...")
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = PHOENIX_COLLECTOR_ENDPOINT
os.environ["PHOENIX_PROJECT_NAME"] = PHOENIX_PROJECT_NAME

endpoint = f"{PHOENIX_COLLECTOR_ENDPOINT.rstrip('/')}/v1/traces"
tracer_provider = register(
    endpoint=endpoint,
    project_name=PHOENIX_PROJECT_NAME,
    protocol="http/protobuf",
)

# Instrumentar OpenAI client
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# Configurar cliente OpenAI (compatível com vLLM)
print("[SETUP] Configurando cliente vLLM...")
vllm_client = OpenAI(
    base_url=f"{VLLM_URL.rstrip('/')}/v1",
    api_key=VLLM_API_KEY,
)

print(f"[OK] Phoenix configurado: {PHOENIX_COLLECTOR_ENDPOINT}")
print(f"[OK] Projeto: {PHOENIX_PROJECT_NAME}")
print(f"[OK] vLLM URL: {VLLM_URL}")
print(f"[OK] API iniciada na porta {API_PORT}")


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de health check."""
    return jsonify({
        "status": "ok",
        "service": "vllm-phoenix-api",
        "vllm_url": VLLM_URL,
        "phoenix_project": PHOENIX_PROJECT_NAME
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """
    Endpoint para chat completions.
    Compatível com a API OpenAI/vLLM.
    """
    try:
        # Obter dados da requisição
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": {
                    "message": "Request body is required",
                    "type": "invalid_request_error",
                    "code": "missing_request_body"
                }
            }), 400
        
        # Validar campos obrigatórios
        if "messages" not in data:
            return jsonify({
                "error": {
                    "message": "Missing required field: messages",
                    "type": "invalid_request_error",
                    "code": "missing_messages"
                }
            }), 400
        
        messages = data.get("messages")
        model = data.get("model", "mistralai/Ministral-3-3B-Instruct-2512")
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens")
        
        # Extrair outros parâmetros opcionais
        kwargs = {}
        optional_params = [
            "top_p", "n", "stream", "stop", "presence_penalty",
            "frequency_penalty", "logit_bias", "user", "logprobs",
            "top_logprobs", "seed"
        ]
        
        for param in optional_params:
            if param in data:
                kwargs[param] = data[param]
        
        # Fazer chamada para o vLLM (instrumentação automática do Phoenix)
        response = vllm_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Formatar resposta no formato OpenAI
        result = {
            "id": response.id,
            "object": "chat.completion",
            "created": response.created if hasattr(response, 'created') else None,
            "model": response.model,
            "choices": [
                {
                    "index": choice.index if hasattr(choice, 'index') else idx,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "finish_reason": choice.finish_reason
                }
                for idx, choice in enumerate(response.choices)
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERRO] Erro ao processar requisição: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "error": {
                "message": error_msg,
                "type": "internal_error",
                "code": "processing_error"
            }
        }), 500


@app.route("/", methods=["GET"])
def root():
    """Endpoint raiz com informações da API."""
    return jsonify({
        "service": "vLLM Phoenix API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat_completions": "/v1/chat/completions"
        },
        "phoenix": {
            "endpoint": PHOENIX_COLLECTOR_ENDPOINT,
            "project": PHOENIX_PROJECT_NAME
        },
        "vllm": {
            "url": VLLM_URL
        }
    })


if __name__ == "__main__":
    print(f"\n[INICIANDO] API vLLM + Phoenix")
    print(f"[INFO] Endpoint principal: http://{API_HOST}:{API_PORT}/v1/chat/completions")
    print(f"[INFO] Health check: http://{API_HOST}:{API_PORT}/health\n")
    
    # Para desenvolvimento local, use Flask dev server
    # Para produção no Railway, use gunicorn (via Procfile)
    app.run(host=API_HOST, port=API_PORT, debug=False)
