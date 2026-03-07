import subprocess
import zipfile
import os
from pathlib import Path

class VideoProcessor:
    @staticmethod
    def extract_frames(video_path, output_dir):
        print(f"[Processor] Extraindo frames de {video_path}...")
        # -vf fps=1: extrai um frame por segundo de vídeo
        command = [
            'ffmpeg', '-i', str(video_path),
            '-vf', 'fps=1',
            f"{output_dir}/frame_%04d.jpg"
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Erro no FFmpeg: {result.stderr}")

    @staticmethod
    def create_zip(source_dir, zip_path):
        print(f"[Processor] Criando arquivo ZIP em {zip_path}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
        return zip_path