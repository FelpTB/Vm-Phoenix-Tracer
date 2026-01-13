# Dockerfile para API vLLM + Phoenix
# Alternativa ao Procfile - Railway pode usar qualquer um

FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY api_server.py .

# Expor porta (Railway vai definir a variável PORT)
EXPOSE 8080

# Variável de ambiente para Python
ENV PYTHONUNBUFFERED=1

# Comando padrão (Railway pode usar PORT diretamente)
CMD gunicorn api_server:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 2 --timeout 120
