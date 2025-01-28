import logging
from ..config.settings import LOGGING_CONFIG

def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG["level"])
    
    formatter = logging.Formatter(LOGGING_CONFIG["format"])
    
    file_handler = logging.FileHandler(LOGGING_CONFIG["filename"])
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger 