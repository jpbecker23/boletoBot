import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from core.config import BASE_DIR

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "boletobot.log")
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3

_handlers: list[logging.Handler] | None = None


def _criar_handlers() -> list[logging.Handler]:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handlers: list[logging.Handler] = []

    # No .exe sem console (--windowed) não existe stderr
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
            )
        )
    except OSError:
        # Sem permissão de escrita (ex.: container); segue apenas com o console
        pass

    for handler in handlers:
        handler.setFormatter(formatter)
    return handlers


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger padronizado (console + arquivo rotativo em logs/) para o módulo informado."""
    global _handlers
    if _handlers is None:
        _handlers = _criar_handlers()

    logger = logging.getLogger(name)

    if not logger.handlers:
        for handler in _handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
