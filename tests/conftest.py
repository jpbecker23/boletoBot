import logging

import pytest


@pytest.fixture(autouse=True)
def silenciar_logs():
    """Evita que os testes escrevam no log real do bot (logs/boletobot.log)."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
