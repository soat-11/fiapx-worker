import pytest
import json
import tempfile
import os
import cv2
from unittest.mock import Mock, patch, MagicMock
from src.core.processor import VideoProcessor
from src.utils.config import Config


@pytest.fixture
def mock_config():
    """Fixture que retorna config mockada."""
    config = Mock(spec=Config)
    config.aws_region = "us-east-1"
    config.frames_per_second = 1.0
    config.image_format = "jpg"
    config.image_quality = 85
    config.log_level = "INFO"
    return config


@pytest.fixture
def processor(mock_config):
    """Fixture que retorna um VideoProcessor."""
    return VideoProcessor(mock_config)


class TestValidateMessage:
    """Testes para validação de mensagens SQS."""

    def test_valid_message(self, processor):
        """Deve validar mensagem correta."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        result = processor.validate_message(message)

        assert result["video_id"] == "uuid-12345"
        assert result["user_id"] == "auth0|67890"
        assert result["s3_input_path"] == "uploads/user-67890/raw-video.mp4"
        assert result["file_name"] == "raw-video.mp4"
        assert result["event_type"] == "video.uploaded"

    def test_missing_event_type(self, processor):
        """Deve falhar se event_type estiver faltando."""
        message = {
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="event_type inválido"):
            processor.validate_message(message)

    def test_wrong_event_type(self, processor):
        """Deve falhar se event_type for diferente de 'video.uploaded'."""
        message = {
            "event_type": "video.deleted",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="event_type inválido"):
            processor.validate_message(message)

    def test_missing_data(self, processor):
        """Deve falhar se 'data' estiver faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
        }

        with pytest.raises(ValueError, match="Campo 'data'"):
            processor.validate_message(message)

    def test_missing_video_id(self, processor):
        """Deve falhar se video_id estiver faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="video_id ausente"):
            processor.validate_message(message)

    def test_missing_user_id(self, processor):
        """Deve falhar se user_id estiver faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="user_id ausente"):
            processor.validate_message(message)

    def test_missing_s3_input_path(self, processor):
        """Deve falhar se s3_input_path estiver faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="s3_input_path ausente"):
            processor.validate_message(message)

    def test_missing_file_name(self, processor):
        """Deve falhar se file_name estiver faltando."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="file_name ausente"):
            processor.validate_message(message)

    def test_file_name_mismatch(self, processor):
        """Deve falhar se file_name não está em s3_input_path."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": {
                "video_id": "uuid-12345",
                "user_id": "auth0|67890",
                "s3_input_path": "uploads/user-67890/other-video.mp4",
                "file_name": "raw-video.mp4",
            },
        }

        with pytest.raises(ValueError, match="file_name"):
            processor.validate_message(message)

    def test_not_a_dict(self, processor):
        """Deve falhar se mensagem não for dicionário."""
        with pytest.raises(ValueError, match="dicionário JSON"):
            processor.validate_message("não é um dicionário")

    def test_data_not_a_dict(self, processor):
        """Deve falhar se 'data' não for dicionário."""
        message = {
            "event_type": "video.uploaded",
            "timestamp": "2026-02-03T12:57:11Z",
            "data": "não é um dicionário",
        }

        with pytest.raises(ValueError, match="Campo 'data'"):
            processor.validate_message(message)


class TestProcessVideo:
    """Testes para processamento de vídeo."""

    def test_file_not_found(self, processor):
        """Deve falhar se arquivo não existe."""
        with pytest.raises(FileNotFoundError):
            processor.process_video(
                "/inexistente/video.mp4", "/tmp/frames", frames_per_second=1.0
            )

    def test_invalid_video_file(self, processor):
        """Deve falhar se arquivo não é vídeo válido."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Criar arquivo fake (não é vídeo)
            fake_video = os.path.join(tmpdir, "fake.mp4")
            with open(fake_video, "w") as f:
                f.write("não é um vídeo")

            frames_dir = os.path.join(tmpdir, "frames")

            with pytest.raises(ValueError, match="Não foi possível abrir"):
                processor.process_video(fake_video, frames_dir, frames_per_second=1.0)

    @patch("src.core.processor.cv2.VideoCapture")
    def test_empty_video(self, mock_cap, processor):
        """Deve falhar se vídeo está vazio."""
        # Mock VideoCapture retornando vídeo vazio
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.get.side_effect = lambda prop: 0 if prop == cv2.CAP_PROP_FRAME_COUNT else 30
        mock_cap.return_value = mock_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_video = os.path.join(tmpdir, "fake.mp4")
            with open(fake_video, "w") as f:
                f.write("")

            frames_dir = os.path.join(tmpdir, "frames")

            with pytest.raises(ValueError, match="vazio ou inválido"):
                processor.process_video(fake_video, frames_dir, frames_per_second=1.0)


class TestGetVideoMetadata:
    """Testes para extração de metadados."""

    def test_file_not_found(self, processor):
        """Deve falhar se arquivo não existe."""
        with pytest.raises(FileNotFoundError):
            processor.get_video_metadata("/inexistente/video.mp4")

    @patch("src.core.processor.cv2.VideoCapture")
    def test_get_metadata(self, mock_cap, processor):
        """Deve retornar metadados corretos."""
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 900,
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080,
        }.get(prop, 0)
        mock_cap.return_value = mock_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_video = os.path.join(tmpdir, "fake.mp4")
            with open(fake_video, "w") as f:
                f.write("")

            metadata = processor.get_video_metadata(fake_video)

            assert metadata["fps"] == 30.0
            assert metadata["total_frames"] == 900
            assert metadata["width"] == 1920
            assert metadata["height"] == 1080
            assert metadata["duration_seconds"] == 30.0
