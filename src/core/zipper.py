import os
import zipfile
import logging
from pathlib import Path
from typing import Optional


class Zipper:
    """Serviço para compactação e validação de arquivos ZIP."""

    def __init__(self):
        """Inicializa o zipper."""
        self.logger = logging.getLogger(__name__)

    def compress_directory(self, source_dir: str, output_zip_path: str) -> bool:
        """
        Compacta um diretório em um arquivo ZIP.
        
        Args:
            source_dir: Diretório com arquivos a compactar
            output_zip_path: Caminho do arquivo ZIP a criar
        
        Returns:
            True se sucesso, False se erro
        """
        if not os.path.isdir(source_dir):
            self.logger.error(f"Diretório não existe: {source_dir}")
            return False

        # Verificar se há arquivos no diretório
        files = list(Path(source_dir).rglob("*"))
        if not any(f.is_file() for f in files):
            self.logger.error(f"Diretório vazio: {source_dir}")
            return False

        try:
            self.logger.info(f"Compactando {source_dir} para {output_zip_path}")

            with zipfile.ZipFile(
                output_zip_path, "w", zipfile.ZIP_DEFLATED
            ) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Caminho relativo dentro do ZIP (sem diretório pai)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
                        self.logger.debug(f"Adicionado ao ZIP: {arcname}")

            self.logger.info(
                f"Compactação concluída: {output_zip_path} "
                f"({os.path.getsize(output_zip_path) / (1024 * 1024):.2f} MB)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao compactar diretório: {str(e)}")
            return False

    def validate_zip(self, zip_path: str) -> bool:
        """
        Valida integridade de um arquivo ZIP.
        
        Args:
            zip_path: Caminho do arquivo ZIP
        
        Returns:
            True se válido, False se inválido/corrompido
        """
        if not os.path.exists(zip_path):
            self.logger.error(f"Arquivo ZIP não existe: {zip_path}")
            return False

        try:
            self.logger.debug(f"Validando integridade do ZIP: {zip_path}")

            with zipfile.ZipFile(zip_path, "r") as zipf:
                # testzip() retorna None se OK ou nome do primeiro arquivo corrompido
                bad_file = zipf.testzip()
                if bad_file:
                    self.logger.error(f"ZIP corrompido - arquivo afetado: {bad_file}")
                    return False

                file_count = len(zipf.namelist())
                self.logger.info(f"ZIP validado com sucesso ({file_count} arquivos)")
                return True

        except zipfile.BadZipFile:
            self.logger.error(f"Arquivo não é um ZIP válido: {zip_path}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao validar ZIP: {str(e)}")
            return False

    def extract_zip(self, zip_path: str, extract_dir: str) -> bool:
        """
        Extrai um arquivo ZIP para um diretório.
        
        Args:
            zip_path: Caminho do arquivo ZIP
            extract_dir: Diretório de destino
        
        Returns:
            True se sucesso, False se erro
        """
        if not os.path.exists(zip_path):
            self.logger.error(f"Arquivo ZIP não existe: {zip_path}")
            return False

        try:
            self.logger.info(f"Extraindo ZIP {zip_path} para {extract_dir}")

            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(extract_dir)

            self.logger.info(f"Extração concluída para {extract_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao extrair ZIP: {str(e)}")
            return False

    def get_zip_info(self, zip_path: str) -> Optional[dict]:
        """
        Retorna informações sobre um arquivo ZIP.
        
        Args:
            zip_path: Caminho do arquivo ZIP
        
        Returns:
            Dicionário com info (arquivo_count, tamanho_kompresso, tamanho_original)
            ou None se erro
        """
        if not os.path.exists(zip_path):
            self.logger.error(f"Arquivo ZIP não existe: {zip_path}")
            return None

        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                file_count = len(zipf.namelist())
                compressed_size = os.path.getsize(zip_path)
                uncompressed_size = sum(info.file_size for info in zipf.infolist())

                return {
                    "file_count": file_count,
                    "compressed_size_bytes": compressed_size,
                    "uncompressed_size_bytes": uncompressed_size,
                    "compression_ratio": (
                        100
                        * (1 - compressed_size / uncompressed_size)
                        if uncompressed_size > 0
                        else 0
                    ),
                }

        except Exception as e:
            self.logger.error(f"Erro ao obter info do ZIP: {str(e)}")
            return None
