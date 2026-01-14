# Requisições Postman - API vLLM + Phoenix

**URL Base:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app`

## Endpoints Disponíveis

### 1. GET `/health`
**Descrição:** Health check da API

**Request:**
```
GET https://vm-phoenix-tracer-buscafornecedor.up.railway.app/health
```

**Response esperado:**
```json
{
  "status": "ok",
  "service": "vllm-phoenix-api",
  "vllm_url": "https://5u888x525vvzvs-8000.proxy.runpod.net",
  "phoenix_project": "buscafornecedor-vllm"
}
```

---

### 2. GET `/`
**Descrição:** Informações sobre a API

**Request:**
```
GET https://vm-phoenix-tracer-buscafornecedor.up.railway.app/
```

**Response esperado:**
```json
{
  "service": "vLLM Phoenix API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "chat_completions": "/v1/chat/completions"
  },
  "phoenix": {
    "endpoint": "https://arize-phoenix-buscafornecedor.up.railway.app",
    "project": "buscafornecedor-vllm"
  },
  "vllm": {
    "url": "https://5u888x525vvzvs-8000.proxy.runpod.net"
  }
}
```

---

### 3. POST `/v1/chat/completions`
**Descrição:** Endpoint principal para chat completions

**Headers:**
```
Content-Type: application/json
```

---

## Requisições de Teste

### Teste 1: Chat Completion - Básico

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "user",
      "content": "Explique o que é Python em uma frase."
    }
  ],
  "temperature": 0.7
}
```

**Response esperado:**
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
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

---

### Teste 2: Chat Completion - Com max_tokens

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "user",
      "content": "Explique o que é inteligência artificial."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 200
}
```

---

### Teste 3: Chat Completion - Conversação

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "user",
      "content": "Qual é a capital do Brasil?"
    },
    {
      "role": "assistant",
      "content": "A capital do Brasil é Brasília."
    },
    {
      "role": "user",
      "content": "Qual é a população aproximada dessa cidade?"
    }
  ],
  "temperature": 0.7
}
```

---

### Teste 4: Chat Completion - Alta Temperatura (Criativo)

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "user",
      "content": "Crie uma história curta sobre um robô que aprende a sonhar."
    }
  ],
  "temperature": 0.9,
  "max_tokens": 300
}
```

---

### Teste 5: Chat Completion - Com System Message

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "messages": [
    {
      "role": "system",
      "content": "Você é um assistente útil e educado que responde em português brasileiro."
    },
    {
      "role": "user",
      "content": "Me explique o que é machine learning."
    }
  ],
  "temperature": 0.7
}
```

---

### Teste 6: Chat Completion - Erro (sem messages)

**Method:** `POST`  
**URL:** `https://vm-phoenix-tracer-buscafornecedor.up.railway.app/v1/chat/completions`

**Body (JSON):**
```json
{
  "model": "mistralai/Ministral-3-3B-Instruct-2512",
  "temperature": 0.7
}
```

**Response esperado (erro 400):**
```json
{
  "error": {
    "message": "Missing required field: messages",
    "type": "invalid_request_error",
    "code": "missing_messages"
  }
}
```

---

## Como Importar no Postman

### Opção 1: Importar Coleção JSON
1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo `POSTMAN_COLLECTION.json`
4. A coleção será importada com todas as requisições

### Opção 2: Criar Manualmente
1. Crie uma nova coleção no Postman
2. Adicione cada requisição conforme descrito acima
3. Configure os headers e body conforme indicado

---

## Parâmetros Disponíveis

O endpoint `/v1/chat/completions` aceita os seguintes parâmetros:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `model` | string | Não | Nome do modelo (padrão: `mistralai/Ministral-3-3B-Instruct-2512`) |
| `messages` | array | **Sim** | Array de mensagens no formato `[{"role": "user", "content": "..."}]` |
| `temperature` | number | Não | Temperatura (0.0 a 2.0, padrão: 0.7) |
| `max_tokens` | integer | Não | Número máximo de tokens |
| `top_p` | number | Não | Nucleus sampling |
| `n` | integer | Não | Número de respostas |
| `stop` | array/string | Não | Sequências de parada |
| `presence_penalty` | number | Não | Penalidade de presença |
| `frequency_penalty` | number | Não | Penalidade de frequência |

---

## Observações

- Todas as requisições para `/v1/chat/completions` são automaticamente instrumentadas e enviadas para o Phoenix
- Os tracers podem ser visualizados em: https://arize-phoenix-buscafornecedor.up.railway.app
- O projeto no Phoenix é: `buscafornecedor-vllm`
- A API está configurada para aceitar CORS, então funciona com requisições do navegador
