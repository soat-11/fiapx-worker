import json
import os
import shutil
import tempfile
import logging
import time
from datetime import datetime
from pathlib import Path

from src.utils.config import load_config
from src.utils.logger import setup_logger
from src.services.s3_service import S3Service
from src.services.sqs_service import SQSService
from src.core.processor import VideoProcessor
from src.core.zipper import Zipper


class Application:
    """Aplicação principal: orquestra todo o pipeline de processamento."""

    def __init__(self):
        """Inicializa a aplicação carregando config e serviços."""
        # Carregar configuração
        try:
            self.config = load_config()
        except ValueError as e:
            raise RuntimeError(f"Erro ao carregar configuração: {str(e)}")

        # Configurar logging
        self.logger = setup_logger("fiapx-worker", self.config.log_level)
        self.logger.info("=" * 80)
        self.logger.info("FiapX Worker iniciado")
        self.logger.info(f"AWS Region: {self.config.aws_region}")
        self.logger.info(f"Frames per second: {self.config.frames_per_second}")
        self.logger.info("=" * 80)

        # Inicializar serviços
        self.s3_service = S3Service(self.config)
        self.sqs_service = SQSService(self.config)
        self.processor = VideoProcessor(self.config)
        self.zipper = Zipper()

    def process_message(self) -> bool:
        """
        Processa uma mensagem da fila SQS.
        
        Fluxo:
        1. Recebe mensagem SQS
        2. Valida estrutura JSON
        3. Baixa vídeo do S3
        4. Extrai frames
        5. Compacta em ZIP
        6. Faz upload do ZIP
        7. Envia notificação
        8. Deleta mensagem da fila
        
        Returns:
            True se processamento sucesso, False se erro
        """
        temp_dir = None
        sqs_message = None

        try:
            # [1] Receber mensagem da fila
            self.logger.info("Aguardando mensagens na fila...")
            messages = self.sqs_service.receive_messages(
                queue_url=self.config.sqs_queue_url, max_messages=1
            )

            if not messages or len(messages) == 0:
                self.logger.debug("Nenhuma mensagem recebida")
                return False

            sqs_message = messages[0]
            self.logger.info(f"Mensagem recebida (ID: {sqs_message.message_id})")

            # [2] Validar estrutura JSON
            try:
                message_data = sqs_message.parse_json()
            except ValueError as e:
                self.logger.error(f"Erro ao fazer parse JSON: {str(e)}")
                # Tentar deletar mensagem mesmo assim (não retornar ao processamento)
                self.sqs_service.delete_message(
                    self.config.sqs_queue_url, sqs_message.receipt_handle
                )
                return False

            # [3] Validar schema da mensagem
            try:
                validated_data = self.processor.validate_message(message_data)
            except ValueError as e:
                self.logger.error(f"Erro ao validar mensagem: {str(e)}")
                # Deletar mensagem para não retornar ao processamento
                self.sqs_service.delete_message(
                    self.config.sqs_queue_url, sqs_message.receipt_handle
                )
                return False

            video_id = validated_data["video_id"]
            user_id = validated_data["user_id"]
            s3_input_path = validated_data["s3_input_path"]
            file_name = validated_data["file_name"]

            self.logger.info(
                f"[{video_id}:{user_id}] Iniciando processamento de vídeo"
            )

            # [4] Criar diretório temporário
            temp_dir = tempfile.mkdtemp(prefix="fiapx_")
            self.logger.debug(f"[{video_id}:{user_id}] Diretório temp: {temp_dir}")

            # [5] Baixar vídeo do S3
            local_video_path = os.path.join(temp_dir, file_name)
            self.logger.info(
                f"[{video_id}:{user_id}] Baixando vídeo de {s3_input_path}"
            )

            success = self.s3_service.download_file(
                bucket=self.config.s3_bucket_input,
                key=s3_input_path,
                local_path=local_video_path,
            )

            if not success:
                self.logger.error(f"[{video_id}:{user_id}] Falha ao baixar vídeo")
                # Neste caso, a mensagem NÃO é deletada e volta à fila para retry
                return False

            # Validar arquivo baixado
            if not os.path.exists(local_video_path):
                self.logger.error(
                    f"[{video_id}:{user_id}] Arquivo não foi salvo localmente"
                )
                return False

            file_size_mb = os.path.getsize(local_video_path) / (1024 * 1024)
            self.logger.info(
                f"[{video_id}:{user_id}] Vídeo baixado ({file_size_mb:.2f} MB)"
            )

            # [6] Processar vídeo (extrair frames)
            frames_dir = os.path.join(temp_dir, "frames")
            self.logger.info(f"[{video_id}:{user_id}] Processando vídeo...")

            try:
                frame_count = self.processor.process_video(
                    local_video_path=local_video_path,
                    output_dir=frames_dir,
                    frames_per_second=self.config.frames_per_second,
                )
                self.logger.info(
                    f"[{video_id}:{user_id}] {frame_count} frames extraídos"
                )
            except Exception as e:
                self.logger.error(
                    f"[{video_id}:{user_id}] Erro ao processar vídeo: {str(e)}"
                )
                return False

            # [7] Compactar frames em ZIP
            zip_filename = f"{video_id}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            self.logger.info(f"[{video_id}:{user_id}] Compactando frames...")

            success = self.zipper.compress_directory(frames_dir, zip_path)
            if not success:
                self.logger.error(f"[{video_id}:{user_id}] Falha ao compactar")
                return False

            # Validar ZIP
            if not self.zipper.validate_zip(zip_path):
                self.logger.error(f"[{video_id}:{user_id}] ZIP corrompido")
                return False

            zip_info = self.zipper.get_zip_info(zip_path)
            if zip_info:
                self.logger.info(
                    f"[{video_id}:{user_id}] ZIP: "
                    f"{zip_info['file_count']} arquivos, "
                    f"{zip_info['compressed_size_bytes'] / (1024 * 1024):.2f} MB"
                )

            # [8] Upload ZIP para S3
            output_key = f"uploads/user-{user_id}/processed/{video_id}.zip"
            self.logger.info(
                f"[{video_id}:{user_id}] Fazendo upload para {output_key}"
            )

            success = self.s3_service.upload_file(
                local_path=zip_path,
                bucket=self.config.s3_bucket_output,
                key=output_key,
            )

            if not success:
                self.logger.error(
                    f"[{video_id}:{user_id}] Falha ao fazer upload do ZIP"
                )
                # Mensagem NÃO deletada, volta à fila para retry
                return False

            # [9] Enviar notificação de conclusão
            response_message = {
                "event_type": "video.processed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "video_id": video_id,
                    "user_id": user_id,
                    "s3_output_path": output_key,
                    "status": "success",
                    "frames_extracted": frame_count,
                },
            }

            self.logger.info(
                f"[{video_id}:{user_id}] Enviando notificação de conclusão"
            )
            success = self.sqs_service.send_message(
                queue_url=self.config.sqs_response_queue_url,
                message_body=json.dumps(response_message),
            )

            if not success:
                self.logger.error(
                    f"[{video_id}:{user_id}] Falha ao enviar notificação"
                )
                # Continue mesmo sem notificação (já fizemos upload)
                # Mas não deletamos a mensagem para retry da notificação
                return False

            # [10] Deletar mensagem da fila (apenas após sucesso completo)
            self.logger.info(f"[{video_id}:{user_id}] Deletando mensagem da fila")
            success = self.sqs_service.delete_message(
                queue_url=self.config.sqs_queue_url,
                receipt_handle=sqs_message.receipt_handle,
            )

            if not success:
                self.logger.error(
                    f"[{video_id}:{user_id}] Falha ao deletar mensagem"
                )
                # Mensagem voltará à fila após timeout, mas processamento foi sucesso
                # Continuamos mesmo assim

            self.logger.info(f"[{video_id}:{user_id}] Processamento concluído!")
            return True

        except Exception as e:
            self.logger.error(f"Erro não tratado no processamento: {str(e)}", exc_info=True)
            return False

        finally:
            # [11] Limpar diretório temporário
            if temp_dir and os.path.exists(temp_dir):
                try:
                    self.logger.debug(f"Limpando diretório temp: {temp_dir}")
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Erro ao limpar diretório temp: {str(e)}")

    def run(self):
        """Executa o loop infinito de processamento."""
        self.logger.info("Iniciando loop de processamento...")

        try:
            while True:
                try:
                    self.process_message()
                except KeyboardInterrupt:
                    self.logger.info("Interrupção solicitada pelo usuário")
                    break
                except Exception as e:
                    self.logger.error(
                        f"Erro no loop de processamento: {str(e)}", exc_info=True
                    )
                    # Continuar processando mesmo com erros
                    time.sleep(5)

        except KeyboardInterrupt:
            pass
        finally:
            self.logger.info("Worker finalizado")


def main():
    """Ponto de entrada da aplicação."""
    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"Erro fatal: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
