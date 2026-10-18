import os
from dotenv import load_dotenv

# Raiz do projeto. Todos os caminhos partem daqui para não depender da pasta de trabalho.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")

# Carrega .env uma única vez para todo o projeto
load_dotenv(ENV_PATH)

# ── Credenciais do Portal UVV ──
MATRICULA = os.getenv("MATRICULA")
PASSWORD = os.getenv("PASSWORD")

# ── WhatsApp ──
CONTATO = os.getenv("CONTATO")

# ── Caminhos ──
CAMINHO_BOLETOS = os.path.join(BASE_DIR, os.getenv("ARQUIVO") or "boletos")

# ── Portal UVV ──
BASE_URL_PORTAL = "https://aluno.uvv.br"
TIMEOUT_PORTAL_SEGUNDOS = 30

# ── Modo contínuo ──
INTERVALO_HORAS = os.getenv("INTERVALO_HORAS")
