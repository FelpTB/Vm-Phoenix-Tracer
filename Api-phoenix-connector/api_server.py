"""
API Flask para repassar requisições do n8n para o vLLM com instrumentação Phoenix.
Processamento assíncrono: retorna imediatamente e processa em background.
"""
import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Optional, Dict, Any, List
from openai import OpenAI
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
import psycopg2
import traceback


# Configurações padrão
VLLM_URL = os.getenv("VLLM_URL", "https://5u888x525vvzvs-8000.proxy.runpod.net")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "buscafornecedor")
# Se VLLM_URL já inclui o caminho /v1, defina VLLM_USE_V1_PATH=false
VLLM_USE_V1_PATH = os.getenv("VLLM_USE_V1_PATH", "true").lower() == "true"
PHOENIX_COLLECTOR_ENDPOINT = os.getenv(
    "PHOENIX_COLLECTOR_ENDPOINT",
    "https://arize-phoenix-buscafornecedor.up.railway.app"
)
PHOENIX_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "buscafornecedor-vllm")
# Railway expõe a porta via variável PORT
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8080")))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# PostgreSQL/Supabase
POSTGRES_CONNECTION_STRING = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://postgres.hccolkrnyrxcbxuuajwq:1d8vUnUlDXT7cmox@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
)
POSTGRES_TABLE_SCHEMA = os.getenv("POSTGRES_TABLE_SCHEMA", "busca_fornecedor")
POSTGRES_TABLE_NAME = os.getenv("POSTGRES_TABLE_NAME", "result_vllm_test")

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
# Construir base_url: se VLLM_USE_V1_PATH=true, adiciona /v1, caso contrário usa a URL diretamente
if VLLM_USE_V1_PATH:
    vllm_base_url = f"{VLLM_URL.rstrip('/')}/v1"
else:
    vllm_base_url = VLLM_URL.rstrip('/')

vllm_client = OpenAI(
    base_url=vllm_base_url,
    api_key=VLLM_API_KEY,
)

print(f"[OK] Phoenix configurado: {PHOENIX_COLLECTOR_ENDPOINT}")
print(f"[OK] Projeto: {PHOENIX_PROJECT_NAME}")
print(f"[OK] vLLM URL base: {VLLM_URL}")
print(f"[OK] vLLM base_url (cliente OpenAI): {vllm_base_url}")
print(f"[OK] PostgreSQL configurado: {POSTGRES_TABLE_SCHEMA}.{POSTGRES_TABLE_NAME}")
print(f"[OK] API iniciada na porta {API_PORT}")


def get_db_connection():
    """Cria uma conexão com o PostgreSQL."""
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"[ERRO] Erro ao conectar ao PostgreSQL: {e}")
        return None


def save_to_postgres(vllm_input: str, vllm_output: Optional[str] = None, 
                     error: bool = False, error_message: Optional[str] = None):
    """
    Salva os resultados no PostgreSQL.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("[ERRO] Não foi possível conectar ao PostgreSQL")
            return
        
        cursor = conn.cursor()
        
        # Preparar query de inserção
        # A tabela está no schema busca_fornecedor
        query = f"""
            INSERT INTO {POSTGRES_TABLE_SCHEMA}.{POSTGRES_TABLE_NAME} 
            (vllm_input, vllm_output, error, error_message)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """
        
        cursor.execute(query, (vllm_input, vllm_output, error, error_message))
        record_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        
        print(f"[OK] Dados salvos no PostgreSQL. ID: {record_id}")
        
    except Exception as e:
        print(f"[ERRO] Erro ao salvar no PostgreSQL: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def process_request_async(request_data: Dict[str, Any]):
    """
    Processa a requisição de forma assíncrona em background.
    Faz a chamada ao vLLM e salva os resultados no PostgreSQL.
    """
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    print(f"[THREAD {thread_id}] Iniciando processamento assíncrono em thread: {thread_name}")
    
    try:
        # Preparar dados de entrada para salvar
        vllm_input_json = json.dumps(request_data, ensure_ascii=False, indent=2)
        
        messages = request_data.get("messages")
        model = request_data.get("model", "mistralai/Ministral-3-3B-Instruct-2512")
        temperature = request_data.get("temperature", 0.7)
        max_tokens = request_data.get("max_tokens")
        
        # Extrair outros parâmetros opcionais
        kwargs = {}
        optional_params = [
            "top_p", "n", "stream", "stop", "presence_penalty",
            "frequency_penalty", "logit_bias", "user", "logprobs",
            "top_logprobs", "seed"
        ]
        
        for param in optional_params:
            if param in request_data:
                kwargs[param] = request_data[param]
        
        # Fazer chamada para o vLLM (instrumentação automática do Phoenix)
        print(f"[PROCESSANDO] Chamando vLLM: base_url={vllm_base_url}, model={model}")
        
        try:
            response = vllm_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Formatar resposta completa para salvar
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
            
            vllm_output_json = json.dumps(result, ensure_ascii=False, indent=2)
            
            # Salvar sucesso no PostgreSQL
            save_to_postgres(
                vllm_input=vllm_input_json,
                vllm_output=vllm_output_json,
                error=False,
                error_message=None
            )
            
            print(f"[OK] Processamento concluído com sucesso. Model: {model}")
            
        except Exception as vllm_error:
            error_type = type(vllm_error).__name__
            error_msg = str(vllm_error)
            print(f"[ERRO] Erro ao chamar vLLM:")
            print(f"  Tipo: {error_type}")
            print(f"  Mensagem: {error_msg}")
            print(f"  Base URL: {vllm_base_url}")
            print(f"  URL completa esperada: {vllm_base_url}/chat/completions")
            traceback.print_exc()
            
            # Salvar erro no PostgreSQL
            save_to_postgres(
                vllm_input=vllm_input_json,
                vllm_output=None,
                error=True,
                error_message=f"{error_type}: {error_msg}"
            )
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[ERRO] Erro ao processar requisição assíncrona:")
        print(f"  Tipo: {error_type}")
        print(f"  Mensagem: {error_msg}")
        traceback.print_exc()
        
        # Tentar salvar erro no PostgreSQL
        try:
            vllm_input_json = json.dumps(request_data, ensure_ascii=False, indent=2)
            save_to_postgres(
                vllm_input=vllm_input_json,
                vllm_output=None,
                error=True,
                error_message=f"{error_type}: {error_msg}"
            )
        except:
            pass


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de health check."""
    # Testar conexão com PostgreSQL
    postgres_ok = False
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            postgres_ok = True
    except:
        pass
    
    return jsonify({
        "status": "ok",
        "service": "vllm-phoenix-api",
        "vllm_url": VLLM_URL,
        "phoenix_project": PHOENIX_PROJECT_NAME,
        "postgres_connected": postgres_ok
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """
    Endpoint para chat completions (assíncrono).
    Retorna imediatamente (202 Accepted) e processa em background.
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
        
        # Timestamp para confirmar resposta imediata
        request_timestamp = datetime.now().isoformat()
        
        # Log para confirmar que está recebendo a requisição
        print(f"[RECEBIDO {request_timestamp}] Nova requisição recebida. Iniciando processamento assíncrono...")
        
        # Criar uma cópia dos dados para evitar problemas de referência
        request_data_copy = json.loads(json.dumps(data))
        
        # Processar em background (thread)
        thread = threading.Thread(
            target=process_request_async, 
            args=(request_data_copy,),
            name=f"vllm-process-{int(time.time() * 1000)}"
        )
        thread.daemon = True  # Thread morre quando o processo principal morre
        
        # Iniciar thread ANTES de retornar resposta
        thread.start()
        
        print(f"[ACEITO {request_timestamp}] Requisição aceita e sendo processada em background. Thread ID: {thread.ident}")
        
        # Retornar imediatamente (ANTES de qualquer processamento)
        # Esta resposta deve ser enviada imediatamente, sem esperar o processamento
        response_data = {
            "status": "accepted",
            "message": "Request received and is being processed asynchronously",
            "object": "chat.completion.accepted",
            "accepted_at": request_timestamp
        }
        
        print(f"[RESPOSTA {request_timestamp}] Enviando resposta 202 Accepted imediatamente...")
        return jsonify(response_data), 202
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[ERRO] Erro ao receber requisição:")
        print(f"  Tipo: {error_type}")
        print(f"  Mensagem: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "error": {
                "message": error_msg,
                "type": "internal_error",
                "code": "request_reception_error"
            }
        }), 500


@app.route("/", methods=["GET"])
def root():
    """Endpoint raiz com informações da API."""
    return jsonify({
        "service": "vLLM Phoenix API (Async)",
        "version": "2.0.0",
        "mode": "asynchronous",
        "endpoints": {
            "health": "/health",
            "chat_completions": "/v1/chat/completions (async)"
        },
        "phoenix": {
            "endpoint": PHOENIX_COLLECTOR_ENDPOINT,
            "project": PHOENIX_PROJECT_NAME
        },
        "vllm": {
            "url": VLLM_URL,
            "base_url": vllm_base_url,
            "use_v1_path": VLLM_USE_V1_PATH
        },
        "postgres": {
            "table": f"{POSTGRES_TABLE_SCHEMA}.{POSTGRES_TABLE_NAME}"
        }
    })


if __name__ == "__main__":
    print(f"\n[INICIANDO] API vLLM + Phoenix (Modo Assíncrono)")
    print(f"[INFO] Endpoint principal: http://{API_HOST}:{API_PORT}/v1/chat/completions")
    print(f"[INFO] Health check: http://{API_HOST}:{API_PORT}/health")
    print(f"[INFO] Modo: Assíncrono (retorna 202 Accepted imediatamente)")
    print(f"[INFO] PostgreSQL: {POSTGRES_TABLE_SCHEMA}.{POSTGRES_TABLE_NAME}\n")
    
    # Para desenvolvimento local, use Flask dev server
    # Para produção no Railway, use gunicorn (via Procfile)
    app.run(host=API_HOST, port=API_PORT, debug=False)
