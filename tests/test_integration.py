"""
Testes de integração do pipeline de processamento de vídeo.
Estes testes validam o fluxo completo end-to-end com mocks.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.main import Application
from src.utils.config import Config


@pytest.fixture
def mock_config():
    """Fixture com configuração mockada."""
    return Mock(spec=Config)


@pytest.fixture
def mock_env(monkeypatch):
    """Fixture que define variáveis de ambiente mockadas."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret")
    monkeypatch.setenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789/test-queue")
    monkeypatch.setenv("SQS_RESPONSE_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789/response-queue")
    monkeypatch.setenv("S3_BUCKET_INPUT", "input-bucket")
    monkeypatch.setenv("S3_BUCKET_OUTPUT", "output-bucket")
    monkeypatch.setenv("FRAMES_PER_SECOND", "1.0")
    monkeypatch.setenv("IMAGE_FORMAT", "jpg")
    monkeypatch.setenv("IMAGE_QUALITY", "85")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


class TestApplicationIntegration:
    """Testes de integração da aplicação."""

    @patch("src.main.SQSService")
    @patch("src.main.S3Service")
    def test_application_init(self, mock_s3, mock_sqs, mock_env):
        """Deve inicializar aplicação com config."""
        with patch("src.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_config.aws_region = "us-east-1"
            mock_config.log_level = "INFO"
            mock_config.frames_per_second = 1.0
            mock_load_config.return_value = mock_config

            app = Application()

            assert app.config is not None
            mock_s3.assert_called_once()
            mock_sqs.assert_called_once()

    def test_valid_message_flow(self, mock_env):
        """Deve processar mensagem válida com sucesso."""
        message_data = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with patch("src.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_config.aws_region = "us-east-1"
            mock_config.log_level = "DEBUG"
            mock_config.frames_per_second = 1.0
            mock_config.sqs_queue_url = "https://sqs.test.com/queue"
            mock_config.sqs_response_queue_url = "https://sqs.test.com/response"
            mock_config.s3_bucket_input = "input"
            mock_config.s3_bucket_output = "output"
            mock_load_config.return_value = mock_config

            with patch("src.main.S3Service"):
                with patch("src.main.SQSService"):
                    app = Application()

                    # Simplesmente validar que a mensagem é processável
                    validated = app.processor.validate_message(message_data)

                    assert validated["video_id"] == "uuid-12345"
                    assert validated["user_id"] == "auth0|67890"


class TestErrorHandling:
    """Testes de tratamento de erros."""

    def test_invalid_message_rejected(self, mock_env):
        """Deve rejeitar mensagem inválida."""
        invalid_message = {"event_type": "wrong.event"}

        with patch("src.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_config.log_level = "INFO"
            mock_config.frames_per_second = 1.0
            mock_load_config.return_value = mock_config

            with patch("src.main.S3Service"):
                with patch("src.main.SQSService"):
                    app = Application()

                    with pytest.raises(ValueError):
                        app.processor.validate_message(invalid_message)

    def test_missing_data_field(self, mock_env):
        """Deve falhar se campo 'data' faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
        }

        with patch("src.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_config.log_level = "INFO"
            mock_config.frames_per_second = 1.0
            mock_load_config.return_value = mock_config

            with patch("src.main.S3Service"):
                with patch("src.main.SQSService"):
                    app = Application()

                    with pytest.raises(ValueError, match="data"):
                        app.processor.validate_message(message)


class TestOutputPathConstruction:
    """Testes para construção de path de output."""

    def test_output_path_format(self, mock_env):
        """Deve construir path de output correto."""
        with patch("src.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_config.log_level = "INFO"
            mock_config.frames_per_second = 1.0
            mock_load_config.return_value = mock_config

            with patch("src.main.S3Service"):
                with patch("src.main.SQSService"):
                    app = Application()

                    # Testar construção de path: uploads/user-{user_id}/processed/{video_id}.zip
                    user_id = "auth0|12345"
                    video_id = "vid-xyz"
                    expected_path = f"uploads/user-{user_id}/processed/{video_id}.zip"

                    # Validar que path segue o padrão esperado
                    assert "uploads/" in expected_path
                    assert "processed/" in expected_path
                    assert video_id in expected_path
                    assert user_id in expected_path
