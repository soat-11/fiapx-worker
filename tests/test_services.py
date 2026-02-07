import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError
from src.services.s3_service import S3Service
from src.services.sqs_service import SQSService, SQSMessage
from src.utils.config import Config


@pytest.fixture
def mock_config():
    """Fixture que retorna config mockada."""
    config = Mock(spec=Config)
    config.aws_region = "us-east-1"
    config.aws_access_key_id = "test_key"
    config.aws_secret_access_key = "test_secret"
    config.sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
    config.sqs_response_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/response-queue"
    config.sqs_wait_time_seconds = 20
    config.sqs_visibility_timeout = 900
    config.s3_bucket_input = "input-bucket"
    config.s3_bucket_output = "output-bucket"
    return config


class TestS3Service:
    """Testes para S3Service."""

    @patch("boto3.client")
    def test_init(self, mock_boto3_client, mock_config):
        """Deve inicializar cliente S3 corretamente."""
        S3Service(mock_config)
        mock_boto3_client.assert_called_once_with(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
        )

    @patch("boto3.client")
    def test_download_file_success(self, mock_boto3_client, mock_config):
        """Deve fazer download de arquivo com sucesso."""
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "video.mp4")
            result = service.download_file("bucket", "key/video.mp4", local_path)

            assert result is True
            mock_s3_client.download_file.assert_called_once_with(
                "bucket", "key/video.mp4", local_path
            )

    @patch("boto3.client")
    def test_download_file_not_found(self, mock_boto3_client, mock_config):
        """Deve falhar se arquivo não existe no S3."""
        mock_s3_client = MagicMock()
        mock_s3_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "GetObject"
        )
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "video.mp4")
            result = service.download_file("bucket", "key/video.mp4", local_path)

            assert result is False

    @patch("boto3.client")
    def test_download_file_access_denied(self, mock_boto3_client, mock_config):
        """Deve falhar se acesso negado."""
        mock_s3_client = MagicMock()
        mock_s3_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "GetObject"
        )
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "video.mp4")
            result = service.download_file("bucket", "key/video.mp4", local_path)

            assert result is False

    @patch("boto3.client")
    def test_download_file_no_credentials(self, mock_boto3_client, mock_config):
        """Deve falhar se credenciais não encontradas."""
        mock_s3_client = MagicMock()
        mock_s3_client.download_file.side_effect = NoCredentialsError()
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "video.mp4")
            result = service.download_file("bucket", "key/video.mp4", local_path)

            assert result is False

    @patch("boto3.client")
    def test_upload_file_success(self, mock_boto3_client, mock_config):
        """Deve fazer upload de arquivo com sucesso."""
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Criar arquivo fake
            local_path = os.path.join(tmpdir, "result.zip")
            with open(local_path, "w") as f:
                f.write("fake zip content")

            result = service.upload_file(local_path, "bucket", "key/result.zip")

            assert result is True
            mock_s3_client.upload_file.assert_called_once_with(
                local_path, "bucket", "key/result.zip"
            )

    @patch("boto3.client")
    def test_upload_file_not_found(self, mock_boto3_client, mock_config):
        """Deve falhar se arquivo local não existe."""
        mock_s3_client = MagicMock()
        # Mockar upload_file para simular FileNotFoundError
        mock_s3_client.upload_file.side_effect = FileNotFoundError("No such file")
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        result = service.upload_file("/inexistente/file.zip", "bucket", "key/result.zip")

        assert result is False

    @patch("boto3.client")
    def test_upload_file_error(self, mock_boto3_client, mock_config):
        """Deve falhar se erro no upload."""
        mock_s3_client = MagicMock()
        mock_s3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "PutObject"
        )
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "result.zip")
            with open(local_path, "w") as f:
                f.write("fake")

            result = service.upload_file(local_path, "bucket", "key/result.zip")

            assert result is False

    @patch("boto3.client")
    def test_delete_file_success(self, mock_boto3_client, mock_config):
        """Deve deletar arquivo com sucesso."""
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        service = S3Service(mock_config)
        result = service.delete_file("bucket", "key/video.mp4")

        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="bucket", Key="key/video.mp4"
        )


class TestSQSMessage:
    """Testes para SQSMessage."""

    def test_parse_json_valid(self):
        """Deve fazer parse de JSON válido."""
        message_data = {
            "Body": '{"key": "value"}',
            "ReceiptHandle": "handle123",
            "MessageId": "msg123",
        }
        message = SQSMessage(message_data)
        parsed = message.parse_json()

        assert parsed["key"] == "value"

    def test_parse_json_invalid(self):
        """Deve falhar ao fazer parse de JSON inválido."""
        message_data = {
            "Body": "not json",
            "ReceiptHandle": "handle123",
            "MessageId": "msg123",
        }
        message = SQSMessage(message_data)

        with pytest.raises(ValueError, match="JSON válido"):
            message.parse_json()

    def test_message_attributes(self):
        """Deve extrair atributos de mensagem."""
        message_data = {
            "Body": '{"content": "test"}',
            "ReceiptHandle": "handle123",
            "MessageId": "msg123",
        }
        message = SQSMessage(message_data)

        assert message.body == '{"content": "test"}'
        assert message.receipt_handle == "handle123"
        assert message.message_id == "msg123"


class TestSQSService:
    """Testes para SQSService."""

    @patch("boto3.client")
    def test_init(self, mock_boto3_client, mock_config):
        """Deve inicializar cliente SQS corretamente."""
        SQSService(mock_config)
        mock_boto3_client.assert_called_once_with(
            "sqs",
            region_name="us-east-1",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
        )

    @patch("boto3.client")
    def test_receive_messages_success(self, mock_boto3_client, mock_config):
        """Deve receber mensagens com sucesso."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {
            "Messages": [
                {
                    "Body": '{"test": "data"}',
                    "ReceiptHandle": "handle123",
                    "MessageId": "msg123",
                }
            ]
        }
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        messages = service.receive_messages(mock_config.sqs_queue_url, max_messages=1)

        assert len(messages) == 1
        assert messages[0].message_id == "msg123"
        mock_sqs_client.receive_message.assert_called_once()

    @patch("boto3.client")
    def test_receive_messages_empty(self, mock_boto3_client, mock_config):
        """Deve retornar lista vazia se nenhuma mensagem."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {}
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        messages = service.receive_messages(mock_config.sqs_queue_url, max_messages=1)

        assert messages == []

    @patch("boto3.client")
    def test_receive_messages_queue_not_exists(self, mock_boto3_client, mock_config):
        """Deve falhar se fila não existe."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.side_effect = ClientError(
            {"Error": {"Code": "QueueDoesNotExist"}}, "ReceiveMessage"
        )
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.receive_messages(mock_config.sqs_queue_url)

        assert result is None

    @patch("boto3.client")
    def test_receive_messages_no_credentials(self, mock_boto3_client, mock_config):
        """Deve falhar se credenciais não encontradas."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.side_effect = NoCredentialsError()
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.receive_messages(mock_config.sqs_queue_url)

        assert result is None

    @patch("boto3.client")
    def test_delete_message_success(self, mock_boto3_client, mock_config):
        """Deve deletar mensagem com sucesso."""
        mock_sqs_client = MagicMock()
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.delete_message(mock_config.sqs_queue_url, "handle123")

        assert result is True
        mock_sqs_client.delete_message.assert_called_once_with(
            QueueUrl=mock_config.sqs_queue_url, ReceiptHandle="handle123"
        )

    @patch("boto3.client")
    def test_delete_message_error(self, mock_boto3_client, mock_config):
        """Deve falhar ao deletar mensagem."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.delete_message.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterValue"}}, "DeleteMessage"
        )
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.delete_message(mock_config.sqs_queue_url, "handle123")

        assert result is False

    @patch("boto3.client")
    def test_send_message_success(self, mock_boto3_client, mock_config):
        """Deve enviar mensagem com sucesso."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.send_message.return_value = {"MessageId": "new_msg_123"}
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.send_message(
            mock_config.sqs_response_queue_url, '{"test": "data"}'
        )

        assert result is True
        mock_sqs_client.send_message.assert_called_once()

    @patch("boto3.client")
    def test_send_message_error(self, mock_boto3_client, mock_config):
        """Deve falhar ao enviar mensagem."""
        mock_sqs_client = MagicMock()
        mock_sqs_client.send_message.side_effect = ClientError(
            {"Error": {"Code": "QueueDoesNotExist"}}, "SendMessage"
        )
        mock_boto3_client.return_value = mock_sqs_client

        service = SQSService(mock_config)
        result = service.send_message(
            mock_config.sqs_response_queue_url, '{"test": "data"}'
        )

        assert result is False
