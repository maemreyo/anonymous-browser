import logging
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from ..config.settings import LOGGING_CONFIG

# Install rich traceback handler
install(show_locals=True)

def setup_logger_v1(name: str) -> logging.Logger:
    """
    @deprecated: Use setup_logger_v2 instead
    Configure and return a basic logger instance
    """
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

def setup_logger_v2(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    Configure and return an enhanced logger instance with Rich formatting
    
    Args:
        name: Logger name
        log_file: Optional file path for logging
        level: Logging level (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create console for rich output
    console = Console(force_terminal=True)
    
    # Configure rich handler
    rich_handler = RichHandler(
        console=console,
        enable_link_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=2,
        log_time_format="[%X]"
    )

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Add rich handler
    logger.addHandler(rich_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Alias for the latest version
setup_logger = setup_logger_v2 