import json
import boto3
import logging
from typing import Optional, Dict, List
from botocore.exceptions import ClientError, NoCredentialsError
from src.utils.config import Config


class SQSMessage:
    """Representa uma mensagem recebida do SQS."""

    def __init__(self, message_data: Dict):
        """
        Inicializa a mensagem.
        
        Args:
            message_data: Dicionário com Body e ReceiptHandle
        """
        self.body = message_data.get("Body", "")
        self.receipt_handle = message_data.get("ReceiptHandle", "")
        self.message_id = message_data.get("MessageId", "")

    def parse_json(self) -> Dict:
        """
        Faz parse do body como JSON.
        
        Returns:
            Dicionário com conteúdo JSON
        
        Raises:
            ValueError: Se o body não for JSON válido
        """
        try:
            return json.loads(self.body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Body da mensagem não é JSON válido: {str(e)}")


class SQSService:
    """Serviço para operações com SQS (recebimento, envio e deleção de mensagens)."""

    def __init__(self, config: Config):
        """
        Inicializa o cliente SQS.
        
        Args:
            config: Instância de configuração da aplicação
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Criar cliente SQS
        self.client = boto3.client(
            "sqs",
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )

    def receive_messages(
        self, queue_url: str, max_messages: int = 1
    ) -> Optional[List[SQSMessage]]:
        """
        Recebe mensagens da fila SQS com long polling.
        
        Args:
            queue_url: URL da fila SQS
            max_messages: Número máximo de mensagens a retornar (1-10)
        
        Returns:
            Lista de SQSMessage ou None se erro/sem mensagens
        """
        max_messages = min(max_messages, 10)  # AWS permite máximo 10
        
        try:
            self.logger.debug(f"Tentando receber {max_messages} mensagem(ns) de {queue_url}")
            
            response = self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=self.config.sqs_wait_time_seconds,
                VisibilityTimeout=self.config.sqs_visibility_timeout,
            )
            
            messages = response.get("Messages", [])
            
            if messages:
                self.logger.info(f"Recebidas {len(messages)} mensagem(ns)")
                return [SQSMessage(msg) for msg in messages]
            else:
                self.logger.debug("Nenhuma mensagem na fila")
                return []
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "QueueDoesNotExist":
                self.logger.error(f"Fila SQS não existe: {queue_url}")
            else:
                self.logger.error(f"Erro ao receber mensagens: {error_code} - {str(e)}")
            return None
        except NoCredentialsError:
            self.logger.error("Credenciais AWS não encontradas")
            return None
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao receber mensagens: {str(e)}")
            return None

    def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """
        Deleta uma mensagem da fila SQS (marca como processada).
        
        Args:
            queue_url: URL da fila SQS
            receipt_handle: Handle da mensagem a deletar
        
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.logger.debug(f"Deletando mensagem de {queue_url}")
            self.client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            self.logger.info(f"Mensagem deletada com sucesso")
            return True
        except ClientError as e:
            self.logger.error(f"Erro ao deletar mensagem: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao deletar mensagem: {str(e)}")
            return False

    def send_message(self, queue_url: str, message_body: str) -> bool:
        """
        Envia uma mensagem para a fila SQS.
        
        Args:
            queue_url: URL da fila SQS de destino
            message_body: Corpo da mensagem (string, geralmente JSON)
        
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.logger.debug(f"Enviando mensagem para {queue_url}")
            response = self.client.send_message(QueueUrl=queue_url, MessageBody=message_body)
            message_id = response.get("MessageId", "")
            self.logger.info(f"Mensagem enviada com sucesso (ID: {message_id})")
            return True
        except ClientError as e:
            self.logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao enviar mensagem: {str(e)}")
            return False
