import os
from dotenv import load_dotenv

# Carrega .env uma única vez para todo o projeto
load_dotenv()

# ── Versão do Projeto ──
VERSION = "v0.2.0-beta"

# ── Credenciais do Portal UVV ──
MATRICULA = os.getenv("MATRICULA")
PASSWORD = os.getenv("PASSWORD")

# ── WhatsApp ──
CONTATO = os.getenv("CONTATO")

# ── Caminhos ──
CAMINHO_BOLETOS = os.getenv("ARQUIVO", "boletos")
USER_DATA_DIR = "./auth"

# ── Portal UVV ──
BASE_URL_PORTAL = "https://aluno.uvv.br"

# ── Browser ──
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]

# ── Docker / Modo contínuo ──
INTERVALO_HORAS = os.getenv("INTERVALO_HORAS")
