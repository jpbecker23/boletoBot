import os
import sys
from dotenv import load_dotenv

# No PyInstaller, forçamos o Playwright a salvar o navegador em um local persistente
# em vez da pasta temporária _MEI que é apagada ao fechar o app.
if getattr(sys, 'frozen', False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getenv("LOCALAPPDATA", ""), "BoletoBot", "Browsers")

# Raiz do projeto (ou pasta do executável). Todos os caminhos partem daqui para não
# depender da pasta de trabalho, que no Task Scheduler é C:\Windows\System32.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")

# Carrega .env uma única vez para todo o projeto
load_dotenv(ENV_PATH)

# ── Versão do Projeto ──
VERSION = "v1.0.0"

# ── Credenciais do Portal UVV ──
MATRICULA = os.getenv("MATRICULA")
PASSWORD = os.getenv("PASSWORD")

# ── WhatsApp ──
CONTATO = os.getenv("CONTATO")

# ── Caminhos ──
CAMINHO_BOLETOS = os.path.join(BASE_DIR, os.getenv("ARQUIVO") or "boletos")
USER_DATA_DIR = os.path.join(BASE_DIR, "auth")

# ── Portal UVV ──
BASE_URL_PORTAL = "https://aluno.uvv.br"
TIMEOUT_PORTAL_SEGUNDOS = 30

# ── Browser ──
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]
# Padrão visível: o WhatsApp Web carrega com mais confiabilidade com janela.
# Em ambientes sem tela (Docker/servidor) defina HEADLESS=true.
HEADLESS = os.getenv("HEADLESS", "false").strip().lower() == "true"

# ── Docker / Modo contínuo ──
INTERVALO_HORAS = os.getenv("INTERVALO_HORAS")

# ── Timeouts (ms) ──
TIMEOUT_CARREGAMENTO_WHATSAPP = 300000
TIMEOUT_SCAN_QR = 60000
TIMEOUT_ENVIO = 10000
TIMEOUT_PREVIEW_ANEXO = 3000
TIMEOUT_CONFIRMACAO_ENVIO = 60000
TIMEOUT_AUTENTICACAO_MANUAL = 120000
TIMEOUT_FECHAMENTO = 5000
TIMEOUT_MENU_ANEXO = 1000
