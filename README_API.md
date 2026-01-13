# API vLLM + Phoenix

API Flask que recebe requisições do n8n e repassa para o vLLM, com instrumentação automática para o Arize Phoenix.

## Características

- ✅ Endpoint `/v1/chat/completions` compatível com API OpenAI/vLLM
- ✅ Instrumentação automática Phoenix para todas as chamadas
- ✅ CORS habilitado para requisições do n8n
- ✅ Endpoint de health check
- ✅ Validação de requisições
- ✅ Tratamento de erros

## Configuração

### Variáveis de Ambiente

```bash
# vLLM
VLLM_URL=https://5u888x525vvzvs-8000.proxy.runpod.net
VLLM_API_KEY=buscafornecedor

# Phoenix
PHOENIX_COLLECTOR_ENDPOINT=https://arize-phoenix-buscafornecedor.up.railway.app
PHOENIX_PROJECT_NAME=buscafornecedor-vllm

# API (opcional)
API_PORT=8080
API_HOST=0.0.0.0
```

## Instalação

```bash
pip install -r requirements.txt
```

## Executar a API

```bash
python api_server.py
```

A API estará disponível em: `http://localhost:8080`

## Endpoints

### POST `/v1/chat/completions`

Endpoint principal para chat completions.

**Request:**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {"role": "user", "content": "Explique o que é Python."}
  ],
  "temperature": 0.7,
  "max_tokens": 200
}
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Python é uma linguagem de programação..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### GET `/health`

Health check da API.

**Response:**
```json
{
  "status": "ok",
  "service": "vllm-phoenix-api",
  "vllm_url": "https://5u888x525vvzvs-8000.proxy.runpod.net",
  "phoenix_project": "buscafornecedor-vllm"
}
```

### GET `/`

Informações sobre a API.

## Uso no n8n

### Configuração do n8n HTTP Request Node

1. **Method:** POST
2. **URL:** `http://seu-servidor:8080/v1/chat/completions`
3. **Authentication:** None (ou adicione autenticação se necessário)
4. **Body:** JSON

**Exemplo de Body no n8n:**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "user",
      "content": "={{ $json.prompt }}"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Headers:**
- `Content-Type: application/json`

## Testar a API

Execute o script de teste:

```bash
python test_api.py
```

Ou teste manualmente com curl:

```bash
# Health check
curl http://localhost:8080/health

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistralai/Ministral-3-3B-Instruct-2512",
    "messages": [
      {"role": "user", "content": "Olá! Como você está?"}
    ],
    "temperature": 0.7
  }'
```

## Visualizar Tracers no Phoenix

Todas as requisições são automaticamente instrumentadas e enviadas para o Phoenix.

Acesse: https://arize-phoenix-buscafornecedor.up.railway.app

Os tracers aparecerão no projeto: `buscafornecedor-vllm`

## Parâmetros Suportados

O endpoint `/v1/chat/completions` suporta todos os parâmetros padrão da API OpenAI:

- `model`: Nome do modelo (padrão: `mistralai/Ministral-3-3B-Instruct-2512`)
- `messages`: Array de mensagens (obrigatório)
- `temperature`: Temperatura (0.0 a 2.0)
- `max_tokens`: Número máximo de tokens
- `top_p`: Nucleus sampling
- `n`: Número de respostas
- `stream`: Streaming (boolean)
- `stop`: Sequências de parada
- `presence_penalty`: Penalidade de presença
- `frequency_penalty`: Penalidade de frequência
- `logit_bias`: Bias de logits
- `user`: ID do usuário
- E outros parâmetros padrão da API OpenAI

## Deploy

Para deploy em produção, considere usar:

- **Gunicorn:** WSGI server
- **Nginx:** Reverse proxy
- **Docker:** Containerização

Exemplo com Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 api_server:app
```

## Troubleshooting

### CORS Errors

Se encontrar erros de CORS, verifique se `flask-cors` está instalado. O código já inclui `CORS(app)` que permite todas as origens.

### Conexão com vLLM

Verifique se:
- A URL do vLLM está correta
- A API key está correta
- O vLLM está acessível

### Phoenix não recebe tracers

Verifique se:
- O endpoint do Phoenix está correto
- O projeto está configurado
- A rede permite conexão com o Phoenix

## Estrutura do Projeto

```
.
├── api_server.py          # Servidor Flask principal
├── test_api.py            # Script de testes
├── requirements.txt       # Dependências
└── README_API.md         # Esta documentação
```
