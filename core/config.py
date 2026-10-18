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

# ── WhatsApp (WAHA) ──
CONTATO = os.getenv("CONTATO")
WAHA_URL = (os.getenv("WAHA_URL") or "http://localhost:3000").rstrip("/")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
WAHA_SESSAO = os.getenv("WAHA_SESSAO") or "default"
TIMEOUT_WAHA_SEGUNDOS = 60

# ── Caminhos ──
CAMINHO_BOLETOS = os.path.join(BASE_DIR, os.getenv("ARQUIVO") or "boletos")

# ── Portal UVV ──
BASE_URL_PORTAL = "https://aluno.uvv.br"
TIMEOUT_PORTAL_SEGUNDOS = 30

# ── Modo contínuo ──
INTERVALO_HORAS = os.getenv("INTERVALO_HORAS")
