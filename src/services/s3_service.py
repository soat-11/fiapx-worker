import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from src.utils.config import Config


class S3Service:
    """Serviço para operações com S3 (upload e download de arquivos)."""

    def __init__(self, config: Config):
        """
        Inicializa o cliente S3.
        
        Args:
            config: Instância de configuração da aplicação
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Criar cliente S3
        self.client = boto3.client(
            "s3",
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )

    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """
        Baixa um arquivo do S3 para o sistema local.
        
        Args:
            bucket: Nome do bucket S3
            key: Chave (caminho) do objeto no S3
            local_path: Caminho local onde salvar o arquivo
        
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.logger.info(f"Baixando arquivo s3://{bucket}/{key} para {local_path}")
            self.client.download_file(bucket, key, local_path)
            self.logger.info(f"Arquivo baixado com sucesso: {local_path}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchKey":
                self.logger.error(f"Arquivo não encontrado no S3: s3://{bucket}/{key}")
            elif error_code == "AccessDenied":
                self.logger.error(f"Acesso negado ao bucket {bucket}: {key}")
            else:
                self.logger.error(f"Erro ao baixar arquivo: {error_code} - {str(e)}")
            return False
        except NoCredentialsError:
            self.logger.error("Credenciais AWS não encontradas")
            return False
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao baixar arquivo: {str(e)}")
            return False

    def upload_file(self, local_path: str, bucket: str, key: str) -> bool:
        """
        Faz upload de um arquivo local para o S3.
        
        Args:
            local_path: Caminho do arquivo local
            bucket: Nome do bucket S3 de destino
            key: Chave (caminho) do objeto no S3
        
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.logger.info(f"Fazendo upload de {local_path} para s3://{bucket}/{key}")
            self.client.upload_file(local_path, bucket, key)
            self.logger.info(f"Arquivo enviado com sucesso: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            self.logger.error(f"Erro ao fazer upload: {error_code} - {str(e)}")
            return False
        except NoCredentialsError:
            self.logger.error("Credenciais AWS não encontradas")
            return False
        except FileNotFoundError:
            self.logger.error(f"Arquivo local não encontrado: {local_path}")
            return False
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao fazer upload: {str(e)}")
            return False

    def delete_file(self, bucket: str, key: str) -> bool:
        """
        Deleta um arquivo do S3.
        
        Args:
            bucket: Nome do bucket S3
            key: Chave (caminho) do objeto no S3
        
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.logger.info(f"Deletando arquivo s3://{bucket}/{key}")
            self.client.delete_object(Bucket=bucket, Key=key)
            self.logger.info(f"Arquivo deletado com sucesso: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            self.logger.error(f"Erro ao deletar arquivo: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro desconhecido ao deletar arquivo: {str(e)}")
            return False
