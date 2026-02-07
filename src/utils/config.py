import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Carrega e valida configuração da aplicação via variáveis de ambiente."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # SQS Configuration
    sqs_queue_url: str
    sqs_response_queue_url: str
    sqs_visibility_timeout: int = 900  # 15 minutos
    sqs_wait_time_seconds: int = 20

    # S3 Configuration
    s3_bucket_input: str
    s3_bucket_output: str

    # Processing Configuration
    frames_per_second: float = 1.0
    image_format: str = "jpg"  # jpg ou png
    image_quality: int = 85  # para JPEG: 1-100

    # Logging Configuration
    log_level: str = "INFO"

    def __init__(self, **data):
        super().__init__(**data)
        # Validações obrigatórias
        if not self.sqs_queue_url:
            raise ValueError("SQS_QUEUE_URL é obrigatório")
        if not self.sqs_response_queue_url:
            raise ValueError("SQS_RESPONSE_QUEUE_URL é obrigatório")
        if not self.s3_bucket_input:
            raise ValueError("S3_BUCKET_INPUT é obrigatório")
        if not self.s3_bucket_output:
            raise ValueError("S3_BUCKET_OUTPUT é obrigatório")

        if self.frames_per_second <= 0:
            raise ValueError("FRAMES_PER_SECOND deve ser > 0")
        if self.image_quality < 1 or self.image_quality > 100:
            raise ValueError("IMAGE_QUALITY deve estar entre 1 e 100")


def load_config() -> Config:
    """Carrega e retorna a configuração da aplicação."""
    return Config()
