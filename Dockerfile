FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema (ffmpeg necessário para OpenCV processar vídeos)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src
COPY .env .

# Garantir que outputs Python não sejam buffered (logs apareçam em tempo real)
ENV PYTHONUNBUFFERED=1

# Comando para executar a aplicação
ENTRYPOINT ["python", "-m", "src.main"]
