# Instrumentação vLLM + Arize Phoenix

Este projeto fornece um cliente Python instrumentado para fazer chamadas ao vLLM (hospedado no RunPod) e enviar tracers automaticamente para o Arize Phoenix (hospedado no Railway).

## Configuração

### Variáveis de Ambiente

O código utiliza as seguintes variáveis de ambiente:

- `VLLM_URL`: URL base do vLLM (padrão: `https://5u888x525vvzvs-8000.proxy.runpod.net`)
- `VLLM_API_KEY`: API key para autenticação (padrão: `buscafornecedor`)
- `PHOENIX_COLLECTOR_ENDPOINT`: Endpoint do coletor Phoenix (padrão: `https://arize-phoenix-buscafornecedor.up.railway.app`)
- `PHOENIX_PROJECT_NAME`: Nome do projeto no Phoenix (padrão: `buscafornecedor-vllm`)

## Instalação

```bash
pip install -r requirements.txt
```

## Uso Básico

### Exemplo Simples

```python
from vllm_phoenix_client import VLLMPhoenixClient

# Criar cliente
client = VLLMPhoenixClient(
    vllm_url="https://5u888x525vvzvs-8000.proxy.runpod.net",
    api_key="buscafornecedor",
    phoenix_collector_endpoint="https://arize-phoenix-buscafornecedor.up.railway.app",
    phoenix_project_name="buscafornecedor-vllm",
)

# Fazer uma pergunta simples
resposta = client.simple_chat("Olá! Como você está?")
print(resposta)
```

### Exemplo com Controle Completo

```python
from vllm_phoenix_client import VLLMPhoenixClient

client = VLLMPhoenixClient(
    vllm_url="https://5u888x525vvzvs-8000.proxy.runpod.net",
    api_key="buscafornecedor",
    phoenix_collector_endpoint="https://arize-phoenix-buscafornecedor.up.railway.app",
    phoenix_project_name="buscafornecedor-vllm",
)

# Fazer chamada completa com parâmetros
response = client.chat_completion(
    messages=[
        {"role": "user", "content": "Explique machine learning em uma frase."}
    ],
    temperature=0.7,
    max_tokens=200,
)

print(response["choices"][0]["message"]["content"])
print(f"Tokens usados: {response['usage']['total_tokens']}")
```

### Conversação com Múltiplas Mensagens

```python
messages = [
    {"role": "user", "content": "Qual é a capital do Brasil?"}
]

response1 = client.chat_completion(messages=messages)
print(response1['choices'][0]['message']['content'])

# Adicionar resposta e continuar conversa
messages.append({
    "role": "assistant",
    "content": response1['choices'][0]['message']['content']
})
messages.append({
    "role": "user",
    "content": "Qual é a população dessa cidade?"
})

response2 = client.chat_completion(messages=messages)
print(response2['choices'][0]['message']['content'])
```

## Executar Testes

Execute o script de teste para verificar a instrumentação:

```bash
python test_vllm_phoenix.py
```

Este script executa vários testes:
1. Chat básico
2. Conversação com múltiplas mensagens
3. Chamada com parâmetros customizados
4. Múltiplas requisições em sequência

## Visualizar Tracers no Phoenix

Após executar as chamadas, acesse o dashboard do Phoenix:

```
https://arize-phoenix-buscafornecedor.up.railway.app
```

Os tracers aparecerão automaticamente no projeto `buscafornecedor-vllm`.

## Estrutura do Projeto

- `vllm_phoenix_client.py`: Cliente principal com instrumentação Phoenix
- `test_vllm_phoenix.py`: Script de testes
- `requirements.txt`: Dependências do projeto

## Dependências Principais

- `openai`: Cliente compatível com API do vLLM
- `arize-phoenix-otel`: Integração OpenTelemetry com Phoenix
- `openinference-instrumentation-openai`: Instrumentação para capturar chamadas OpenAI/vLLM
- `opentelemetry-api` / `opentelemetry-sdk`: OpenTelemetry

## Notas

- Todas as chamadas ao vLLM são automaticamente instrumentadas e enviadas para o Phoenix
- Os tracers incluem informações sobre prompts, respostas, tokens usados, latência, etc.
- O cliente é compatível com a API OpenAI, então funciona diretamente com o vLLM
