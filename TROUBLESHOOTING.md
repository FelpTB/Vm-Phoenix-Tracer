# Troubleshooting - Erro 404

## Problema: `openai.NotFoundError: Error code: 404`

Este erro ocorre quando a API tenta fazer uma requisição para o vLLM e o endpoint não é encontrado.

## Diagnóstico

O erro 404 geralmente indica que:

1. **URL do vLLM incorreta**: A URL base do vLLM pode estar incorreta ou o servidor pode não estar acessível
2. **Caminho do endpoint incorreto**: O vLLM pode não estar usando o caminho `/v1` na URL base
3. **Servidor vLLM offline**: O servidor vLLM pode estar offline ou inacessível

## Soluções

### 1. Verificar a URL do vLLM

A URL padrão é: `https://5u888x525vvzvs-8000.proxy.runpod.net`

Verifique se:
- A URL está correta e acessível
- O servidor vLLM está rodando
- Não há problemas de rede/firewall

**Teste manual:**
```bash
curl https://5u888x525vvzvs-8000.proxy.runpod.net/health
# ou
curl https://5u888x525vvzvs-8000.proxy.runpod.net/v1/models
```

### 2. Ajustar o caminho `/v1`

Alguns servidores vLLM podem não usar o caminho `/v1` na URL base. Nesse caso, configure a variável de ambiente:

```bash
VLLM_USE_V1_PATH=false
```

Isso fará com que a API use a URL diretamente sem adicionar `/v1`.

**Exemplo:**
- Com `VLLM_USE_V1_PATH=true` (padrão): `https://vllm-server.com/v1` → chama `https://vllm-server.com/v1/chat/completions`
- Com `VLLM_USE_V1_PATH=false`: `https://vllm-server.com` → chama `https://vllm-server.com/chat/completions`

### 3. Verificar logs detalhados

A API agora inclui logs detalhados que mostram:
- A URL base configurada
- A URL completa que está sendo chamada
- O tipo e mensagem de erro

Procure por linhas como:
```
[DEBUG] Chamando vLLM: base_url=..., model=...
[ERRO] Erro ao chamar vLLM:
  Tipo: NotFoundError
  Mensagem: ...
  Base URL: ...
  URL completa esperada: ...
```

### 4. Verificar resposta de erro da API

Quando ocorre um erro 404, a API retorna uma resposta JSON com detalhes:

```json
{
  "error": {
    "message": "Endpoint não encontrado no vLLM. Verifique se a URL está correta.",
    "type": "not_found_error",
    "code": "vllm_endpoint_not_found",
    "details": {
      "vllm_url": "https://5u888x525vvzvs-8000.proxy.runpod.net",
      "base_url": "https://5u888x525vvzvs-8000.proxy.runpod.net/v1",
      "expected_endpoint": "https://5u888x525vvzvs-8000.proxy.runpod.net/v1/chat/completions",
      "original_error": "..."
    }
  }
}
```

Use essas informações para diagnosticar o problema.

## Configuração Recomendada

### Para vLLM padrão (com `/v1`):
```bash
VLLM_URL=https://seu-servidor-vllm.com
VLLM_USE_V1_PATH=true  # ou omitir (padrão é true)
```

### Para vLLM sem `/v1`:
```bash
VLLM_URL=https://seu-servidor-vllm.com
VLLM_USE_V1_PATH=false
```

### Para vLLM com caminho completo já na URL:
```bash
VLLM_URL=https://seu-servidor-vllm.com/v1
VLLM_USE_V1_PATH=false
```

## Teste Rápido

1. Verifique o health check da sua API:
   ```bash
   curl https://sua-api.com/health
   ```

2. Verifique as informações da API:
   ```bash
   curl https://sua-api.com/
   ```
   
   Isso mostrará a configuração atual do vLLM.

3. Tente uma requisição de teste:
   ```bash
   curl -X POST https://sua-api.com/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "mistralai/Ministral-3-3B-Instruct-2512",
       "messages": [{"role": "user", "content": "teste"}]
     }'
   ```

## Próximos Passos

Se o problema persistir:

1. Verifique se o servidor vLLM está acessível diretamente
2. Verifique a documentação do seu servidor vLLM para confirmar o formato da URL
3. Teste diferentes configurações de `VLLM_USE_V1_PATH`
4. Verifique os logs do servidor vLLM para ver quais requisições estão chegando
