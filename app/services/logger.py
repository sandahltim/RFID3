import logging
import os
from config import LOG_FILE

_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_logger(name: str, level: int = logging.INFO, log_file: str = LOG_FILE, add_handlers: bool = True) -> logging.Logger:
    """Return a configured logger with file and console handlers.

    Parameters:
        name: Logger name.
        level: Logging level.
        log_file: Path to the log file.
        add_handlers: Whether to attach handlers. Useful when the caller
            wants to rely on existing global handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if add_handlers and not logger.handlers:
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(_formatter)
        logger.addHandler(console_handler)
    return logger
