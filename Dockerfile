# Imagem oficial do Playwright que já contém todas as dependências de SO para rodar browsers
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Define o diretório de trabalho no container
WORKDIR /app

# Instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Garante que o Chromium necessário pelo Playwright esteja disponível
RUN playwright install chromium

COPY . .

CMD ["python", "-u", "main.py"]
