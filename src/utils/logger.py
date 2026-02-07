import logging
import sys
from typing import Optional


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger com formatação estruturada.
    
    Args:
        name: Nome do logger (geralmente __name__)
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Instância do logger configurado
    """
    # Converter string de log_level para constante logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remover handlers existentes para evitar duplicação
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Criar formatter estruturado
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger


def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Retorna um logger existente ou cria um novo se não existir.
    
    Args:
        name: Nome do logger
        log_level: Nível de logging
    
    Returns:
        Instância do logger
    """
    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():
        logger = setup_logger(name, log_level)
    
    return logger
