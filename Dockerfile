FROM python:3.9-slim

# Instala o FFmpeg (essencial para o processamento de vídeo)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 1. Define a pasta base na raiz para instalar as dependências
WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODO o código do projeto (Isso copia a pasta "src" para dentro do "/app")
COPY . .

# 2. Muda para a subpasta exata onde o script mora
WORKDIR /app/src/app

# 2. Muda para a subpasta exata onde o script mora
WORKDIR /app/src/app

# Variável para ver logs em tempo real no CloudWatch
ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]