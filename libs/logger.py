import logging
from pathlib import Path
from datetime import datetime

# Global variable for logger
_logger = None
_step = 1


def init_logger(log_name: str, log_dir: str = "logs"):
    """
    Initialise logger at start

    Args:
        log_name: File name
        log_dir: File Folder
    """
    global _logger
    global _step

    # Create folder if not exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Add timestamp to file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"{log_name}_{timestamp}.log"

    # Configuration of logger
    _logger = logging.getLogger("app")
    _logger.setLevel(logging.INFO)
    _step = 1

    # Handler file
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    _logger.addHandler(handler)


def log(message: str):
    """
    Add a message in log

    Args:
        message: Message to log
    """
    if _logger is None:
        raise RuntimeError("Logger not initialize. Call init_logger() First.")
    _logger.info(message)


def log_step(message):
    """
    Add a message in log

    Args:
        message: Message to log
    """
    global _step

    if _logger is None:
        raise RuntimeError("Logger not initialize. Call init_logger() First.")
    _logger.info(f"STEP {_step}: {message}")
    _step += 1
