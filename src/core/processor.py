import os
import json
import logging
import cv2
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from src.utils.config import Config


class VideoProcessor:
    """Processa vídeos: valida mensagens SQS e extrai frames."""

    def __init__(self, config: Config):
        """
        Inicializa o processador.
        
        Args:
            config: Instância de configuração da aplicação
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def validate_message(self, message_data: Dict) -> Dict:
        """
        Valida a estrutura da mensagem SQS e extrai dados.
        
        Esperado:
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
        
        Args:
            message_data: Dicionário com dados da mensagem
        
        Returns:
            Dicionário com dados extraídos e validados
        
        Raises:
            ValueError: Se estrutura ou validação falhar
        """
        # Validar estrutura top-level
        if not isinstance(message_data, dict):
            raise ValueError("Mensagem deve ser um dicionário JSON")

        event_type = message_data.get("event_type")
        if event_type != "video.uploaded":
            raise ValueError(
                f"event_type inválido: '{event_type}' (esperado 'video.uploaded')"
            )

        timestamp = message_data.get("timestamp")
        if not timestamp:
            raise ValueError("timestamp ausente na mensagem")

        # Validar seção 'data'
        data = message_data.get("data")
        if not isinstance(data, dict):
            raise ValueError("Campo 'data' deve ser um dicionário")

        # Extrair e validar campos obrigatórios
        video_id = data.get("video_id")
        if not video_id:
            raise ValueError("video_id ausente em data")

        user_id = data.get("user_id")
        if not user_id:
            raise ValueError("user_id ausente em data")

        s3_input_path = data.get("s3_input_path")
        if not s3_input_path:
            raise ValueError("s3_input_path ausente em data")

        file_name = data.get("file_name")
        if not file_name:
            raise ValueError("file_name ausente em data")

        # Validar que file_name está contido em s3_input_path
        if file_name not in s3_input_path:
            raise ValueError(
                f"file_name '{file_name}' não encontrado em s3_input_path '{s3_input_path}'"
            )

        self.logger.info(
            f"Mensagem validada com sucesso - video_id: {video_id}, user_id: {user_id}"
        )

        return {
            "video_id": video_id,
            "user_id": user_id,
            "s3_input_path": s3_input_path,
            "file_name": file_name,
            "event_type": event_type,
            "timestamp": timestamp,
        }

    def process_video(
        self, local_video_path: str, output_dir: str, frames_per_second: float = 1.0
    ) -> int:
        """
        Extrai frames do vídeo e salva como imagens.
        
        Vídeos são processados em frames baseado em FPS configurado.
        Imagens salvas em formato JPEG com qualidade configurada.
        
        Args:
            local_video_path: Caminho do arquivo de vídeo local
            output_dir: Diretório de saída para frames
            frames_per_second: Frames por segundo a extrair (ex: 1.0 = 1 frame/seg)
        
        Returns:
            Número de frames extraídos
        
        Raises:
            FileNotFoundError: Se vídeo não existe
            ValueError: Se vídeo não pode ser lido ou está vazio
        """
        # Validar arquivo local
        if not os.path.exists(local_video_path):
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {local_video_path}")

        # Criar diretório de saída
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Abrir vídeo
        cap = cv2.VideoCapture(local_video_path)
        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir o vídeo: {local_video_path}")

        # Informações do vídeo
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            raise ValueError(f"Vídeo vazio ou inválido: {local_video_path}")

        self.logger.info(
            f"Processando vídeo: {total_frames} frames, {fps:.2f} FPS original"
        )

        # Calcular intervalo de frames (frame skip)
        # Se frames_per_second=1, queremos 1 frame por segundo
        # intervalo = fps / frames_per_second
        frame_interval = max(1, int(fps / frames_per_second))
        self.logger.info(
            f"Extraindo 1 frame a cada {frame_interval} frames ({frames_per_second} fps)"
        )

        frame_count = 0
        extracted_count = 0
        image_format = self.config.image_format.lower()
        image_quality = self.config.image_quality

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Extrair apenas frames no intervalo
                if frame_count % frame_interval == 0:
                    # Nome do arquivo: frame_000001.jpg
                    frame_num = extracted_count + 1
                    filename = f"frame_{frame_num:06d}.{image_format}"
                    filepath = os.path.join(output_dir, filename)

                    # Salvar frame
                    if image_format == "jpg" or image_format == "jpeg":
                        cv2.imwrite(
                            filepath,
                            frame,
                            [cv2.IMWRITE_JPEG_QUALITY, image_quality],
                        )
                    else:  # png
                        cv2.imwrite(filepath, frame)

                    extracted_count += 1

                frame_count += 1

        finally:
            cap.release()

        self.logger.info(f"Processamento concluído: {extracted_count} frames extraídos")
        return extracted_count

    def get_video_metadata(self, local_video_path: str) -> Dict:
        """
        Extrai metadados do vídeo.
        
        Args:
            local_video_path: Caminho do arquivo de vídeo
        
        Returns:
            Dicionário com metadados (fps, frames, duração)
        """
        if not os.path.exists(local_video_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {local_video_path}")

        cap = cv2.VideoCapture(local_video_path)
        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir o vídeo: {local_video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = total_frames / fps if fps > 0 else 0

            return {
                "fps": fps,
                "total_frames": total_frames,
                "width": width,
                "height": height,
                "duration_seconds": duration_seconds,
            }
        finally:
            cap.release()
