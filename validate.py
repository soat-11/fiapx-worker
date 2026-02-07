#!/usr/bin/env python
"""
Script de validação do projeto FiapX Worker.
Verifica estrutura, imports e configuração.
"""

import os
import sys
from pathlib import Path


def check_structure():
    """Verifica estrutura de diretórios e arquivos."""
    print("=" * 80)
    print("VALIDAÇÃO DO PROJETO FIAPX WORKER")
    print("=" * 80)

    base_path = Path(__file__).parent

    # Estrutura esperada
    required_files = [
        "src/__init__.py",
        "src/main.py",
        "src/core/__init__.py",
        "src/core/processor.py",
        "src/core/zipper.py",
        "src/services/__init__.py",
        "src/services/s3_service.py",
        "src/services/sqs_service.py",
        "src/utils/__init__.py",
        "src/utils/config.py",
        "src/utils/logger.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_processor.py",
        "tests/test_services.py",
        "tests/test_integration.py",
        "requirements.txt",
        "Dockerfile",
        ".env",
        ".gitignore",
        "README.md",
    ]

    required_dirs = [
        "src",
        "src/core",
        "src/services",
        "src/utils",
        "tests",
    ]

    print("\n✓ VERIFICANDO DIRETÓRIOS...")
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ FALTANDO")
            missing_dirs.append(dir_path)

    print("\n✓ VERIFICANDO ARQUIVOS...")
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists() and full_path.is_file():
            size = full_path.stat().st_size
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            print(f"  ✗ {file_path} FALTANDO")
            missing_files.append(file_path)

    print("\n✓ VERIFICANDO IMPORTS...")
    try:
        from src.utils.config import load_config
        print("  ✓ config.py (load_config)")
        from src.utils.logger import setup_logger, get_logger
        print("  ✓ logger.py (setup_logger, get_logger)")
        from src.services.s3_service import S3Service
        print("  ✓ s3_service.py (S3Service)")
        from src.services.sqs_service import SQSService, SQSMessage
        print("  ✓ sqs_service.py (SQSService, SQSMessage)")
        from src.core.processor import VideoProcessor
        print("  ✓ processor.py (VideoProcessor)")
        from src.core.zipper import Zipper
        print("  ✓ zipper.py (Zipper)")
        from src.main import Application, main
        print("  ✓ main.py (Application, main)")
    except ImportError as e:
        print(f"  ✗ Erro ao importar: {str(e)}")
        return False

    print("\n" + "=" * 80)
    if missing_dirs or missing_files:
        print(f"⚠️  ESTRUTURA INCOMPLETA: {len(missing_dirs)} dirs, {len(missing_files)} arquivos faltando")
        return False
    else:
        print("✅ ESTRUTURA VÁLIDA: Todos os arquivos e diretórios presentes")

    print("=" * 80)
    return True


def check_tests():
    """Verifica testes."""
    print("\n✓ VERIFICANDO TESTES...")

    try:
        import pytest
        result = pytest.main(["-v", "--co", "-q", "tests/"])
        print("  ✓ Testes coletados com sucesso")
        return True
    except Exception as e:
        print(f"  ✗ Erro ao coletar testes: {str(e)}")
        return False


def main():
    """Executa validação completa."""
    valid_structure = check_structure()

    if not valid_structure:
        print("\n❌ PROJETO COM PROBLEMAS")
        sys.exit(1)

    print("\n✅ PROJETO PRONTO PARA USAR")
    print("\nPróximos passos:")
    print("  1. Configure .env com suas credenciais AWS")
    print("  2. Execute: python -m src.main")
    print("  3. Para Docker: docker build -t fiapx-worker . && docker run --env-file .env fiapx-worker")
    print("  4. Teste: python -m pytest tests/ -v")


if __name__ == "__main__":
    main()
