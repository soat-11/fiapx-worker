# Imagem leve baseada em Python
FROM python:3.9-slim

# Instala o FFmpeg (essencial para o processamento de vídeo)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os códigos do projeto
COPY . .

# Variável para ver logs em tempo real no CloudWatch
ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]