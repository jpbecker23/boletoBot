FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# UID fixo (1000) para coincidir com o usuário padrão do host nas pastas montadas
RUN useradd --uid 1000 --create-home appuser

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser . .
RUN mkdir -p boletos logs && chown appuser:appuser boletos logs

USER appuser

CMD ["python", "main.py"]
