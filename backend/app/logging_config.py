"""
app/logging_config.py
Konfigurasi structured logging dalam format JSON (Chapter 10).
"""
import logging
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO"):
    """
    Setup root logger dengan JSON formatter.
    Panggil sekali saja di startup (main.py).

    Output format:
    {
        "asctime": "2026-03-06 08:30:15",
        "name": "app.routers.auth",
        "levelname": "INFO",
        "message": "User login successful",
        ...extra fields...
    }
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Hindari duplikasi handler bila fungsi dipanggil > 1x
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return root_logger
