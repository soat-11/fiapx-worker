# FiapX Worker - Microserviço de Processamento de Vídeos

Microserviço assíncrono que consome mensagens de uma fila AWS SQS, baixa vídeos do S3, extrai frames em JPEG e retorna um ZIP compactado com as imagens processadas.

## Arquitetura

```
┌──────────────┐        ┌────────────────┐        ┌──────────────┐
│  Input SQS   │───────>│  FiapX Worker  │───────>│ Output SQS   │
│   (Eventos)  │        │  (Processador) │        │ (Notificações)
└──────────────┘        └────────────────┘        └──────────────┘
                              ↓
                        ┌────────────────┐
                        │  S3 Buckets    │
                        │ (Download/Upload)
                        └────────────────┘
```

## Fluxo de Processamento

1. **Recebimento**: Worker escuta fila SQS por novas mensagens
2. **Validação**: Valida estrutura JSON e schema da mensagem
3. **Download**: Baixa arquivo de vídeo do S3
4. **Processamento**: Extrai frames do vídeo (1 frame/segundo por padrão)
5. **Compressão**: Compacta todas as imagens em arquivo ZIP
6. **Upload**: Faz upload do ZIP para bucket de saída do S3
7. **Notificação**: Envia notificação de conclusão na fila de resposta
8. **Cleanup**: Deleta mensagem da fila de entrada e arquivos temporários

## Requisitos

- Python 3.11+
- ffmpeg (para processamento de vídeo)
- AWS CLI configurado ou credenciais de ambiente
- Acesso a buckets S3 e filas SQS

## Setup

### 1. Instalar Dependências do Sistema

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**Docker:**
Automaticamente instalado na imagem (vide Dockerfile)

### 2. Configurar Variáveis de Ambiente

Copie o arquivo `.env` e configure com suas credenciais AWS:

```bash
cp .env .env.local
# Editar .env com valores reais
```

**Variáveis obrigatórias:**
- `AWS_REGION`: Região AWS (ex: us-east-1)
- `AWS_ACCESS_KEY_ID`: Sua chave de acesso
- `AWS_SECRET_ACCESS_KEY`: Sua chave secreta
- `SQS_QUEUE_URL`: URL completa da fila de entrada
- `SQS_RESPONSE_QUEUE_URL`: URL completa da fila de resposta
- `S3_BUCKET_INPUT`: Nome do bucket de vídeos
- `S3_BUCKET_OUTPUT`: Nome do bucket de processados

**Variáveis opcionais:**
- `FRAMES_PER_SECOND`: Frames a extrair por segundo (default: 1.0)
- `IMAGE_FORMAT`: Formato das imagens (jpg ou png, default: jpg)
- `IMAGE_QUALITY`: Qualidade JPEG 1-100 (default: 85)
- `LOG_LEVEL`: Nível de logging (DEBUG, INFO, WARNING, ERROR, default: INFO)
- `SQS_VISIBILITY_TIMEOUT`: Timeout de visibilidade em segundos (default: 900 = 15min)
- `SQS_WAIT_TIME_SECONDS`: Long polling timeout (default: 20)

### 3. Instalar Dependências Python

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

## Execução

### Localmente

```bash
python -m src.main
```

### Via Docker

```bash
# Build
docker build -t fiapx-worker .

# Run
docker run --env-file .env fiapx-worker
```

## Estrutura de Mensagens

### Mensagem de Entrada (SQS)

```json
{
  "event_type": "video.uploaded",
  "timestamp": "2026-02-03T12:57:11Z",
  "data": {
    "video_id": "uuid-12345",
    "user_id": "auth0|67890",
    "s3_input_path": "uploads/user-67890/raw-video.mp4",
    "file_name": "raw-video.mp4"
  }
}
```

### Mensagem de Saída (SQS)

```json
{
  "event_type": "video.processed",
  "timestamp": "2026-02-03T13:15:42Z",
  "data": {
    "video_id": "uuid-12345",
    "user_id": "auth0|67890",
    "s3_output_path": "uploads/user-67890/processed/uuid-12345.zip",
    "status": "success",
    "frames_extracted": 42
  }
}
```

## Estrutura do Projeto

```
fiapx-worker/
├── src/
│   ├── main.py                 # Ponto de entrada e orquestração
│   ├── core/
│   │   ├── processor.py        # Processamento de vídeo
│   │   └── zipper.py           # Compressão de arquivos
│   ├── services/
│   │   ├── s3_service.py       # Integração com S3
│   │   └── sqs_service.py      # Integração com SQS
│   └── utils/
│       ├── config.py           # Carregamento de configuração
│       └── logger.py           # Setup de logging
├── tests/
│   ├── test_processor.py       # Testes do processor
│   └── test_services.py        # Testes dos serviços AWS
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Build da imagem Docker
├── .env                        # Variáveis de ambiente
├── .gitignore                  # Git ignore
└── README.md                   # Este arquivo
```

## Comportamento de Erro

### Falhas de Download
Se o vídeo não puder ser baixado, a mensagem **NÃO é deletada** da fila e será retentada automaticamente após o visibility timeout.

### Falhas de Processamento
Se o vídeo não puder ser processado, a mensagem **NÃO é deletada** para retry.

### Falhas de Upload
Se o ZIP não puder ser enviado para S3, a mensagem **NÃO é deletada** para retry.

### Validação de Mensagem
Se a mensagem JSON não corresponder ao schema esperado, ela é **deletada** (rejeitada) para evitar loop infinito.

### Limpeza
Diretórios temporários e arquivos de vídeo são **sempre** deletados, mesmo em caso de erro.

## Testes

### Executar testes unitários

```bash
pytest tests/ -v
```

### Testes com cobertura

```bash
pytest tests/ --cov=src --cov-report=html
```

### Testes de integração (requires LocalStack)

```bash
# Iniciar LocalStack
docker-compose up -d

# Rodar testes de integração
pytest tests/integration/ -v
```

## Logging

Logs estruturados com timestamp, nível e mensagem. Exemplo:

```
2026-02-06 10:15:42 - fiapx-worker - INFO - FiapX Worker iniciado
2026-02-06 10:15:45 - fiapx-worker - INFO - Mensagem recebida (ID: abc123)
2026-02-06 10:15:46 - fiapx-worker - INFO - [uuid-12345:auth0|67890] Iniciando processamento de vídeo
2026-02-06 10:15:47 - fiapx-worker - INFO - [uuid-12345:auth0|67890] Vídeo baixado (125.50 MB)
2026-02-06 10:16:10 - fiapx-worker - INFO - [uuid-12345:auth0|67890] 132 frames extraídos
2026-02-06 10:16:15 - fiapx-worker - INFO - [uuid-12345:auth0|67890] Processamento concluído!
```

## Performance

- **Frames por segundo**: Configurável (padrão: 1 frame/segundo)
- **Formato**: JPEG com qualidade configurável (padrão: 85%)
- **Memória**: Streaming - não carrega vídeo inteiro na RAM
- **Disco**: Usa `/tmp` temporário automaticamente limpado

## Escalabilidade

Para escalar horizontalmente:

1. Deploy múltiplas instâncias do worker
2. Apontar todas para a mesma fila SQS
3. AWS distribui mensagens entre as instâncias automaticamente
4. Visibility timeout deve acomodar o tempo máximo de processamento

## Troubleshooting

### "Module not found: cv2"
Certifique-se de que `opencv-python-headless` foi instalado:
```bash
pip install opencv-python-headless
```

### "FFmpeg not found"
Instale ffmpeg no seu sistema (vide Requisitos).

### Credenciais AWS não funcionam
Verifique:
- `.env` com credenciais corretas
- Permissões IAM para S3 e SQS
- `AWS_REGION` configurada corretamente

### Worker fica preso na mesma mensagem
Verifique:
- `VISIBILITY_TIMEOUT` é suficiente para processar o vídeo
- Não há erro lançado sem tratamento

## Contribuição

Commits devem incluir logs estruturados `self.logger.info()` para rastreabilidade.

## Licença

Propriedade do projeto FiapX.
# fiapx-terraform
