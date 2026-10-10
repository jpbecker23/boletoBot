import os
import requests
from bs4 import BeautifulSoup

from core.config import (
    MATRICULA, PASSWORD, BASE_URL_PORTAL, CAMINHO_BOLETOS, TIMEOUT_PORTAL_SEGUNDOS
)
from core.logger import get_logger

logger = get_logger(__name__)


class PortalAuthError(Exception):
    """Falha de autenticação no portal (credenciais inválidas ou sessão rejeitada)."""


class PortalDownloadError(Exception):
    """O portal retornou algo que não é o PDF do boleto."""


def executar_download():
    """
    Realiza login HTTP no portal UVV, busca boletos com status 'aberto',
    e baixa os PDFs para a pasta de boletos.

    Levanta PortalAuthError se o login falhar e PortalDownloadError se o
    portal devolver algo que não seja um PDF.
    """
    if not MATRICULA or not PASSWORD:
        raise PortalAuthError("MATRICULA e/ou PASSWORD não configurados no .env.")

    os.makedirs(CAMINHO_BOLETOS, exist_ok=True)

    login_url = f"{BASE_URL_PORTAL}/Login"
    boletos_url = f"{BASE_URL_PORTAL}/Aluno/Extrato"

    session = requests.Session()

    payload = {
        "Matricula": MATRICULA,
        "Password": PASSWORD,
    }

    logger.info("Realizando login no portal...")
    login_response = session.post(login_url, data=payload, timeout=TIMEOUT_PORTAL_SEGUNDOS)
    if login_response.status_code != 200 or "/Login" in login_response.url:
        raise PortalAuthError(
            "Falha ao autenticar no portal UVV. Verifique matrícula e senha."
        )

    response = session.get(boletos_url, timeout=TIMEOUT_PORTAL_SEGUNDOS)
    response.raise_for_status()
    if "/Login" in response.url:
        raise PortalAuthError(
            "Portal redirecionou para o login ao acessar o extrato. Sessão não foi aceita."
        )
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")

    count = 0
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 9:
            continue

        vencimento = cols[6].get_text(strip=True)
        status = cols[7].get_text(strip=True)
        parcela = cols[1].get_text(strip=True)

        if status.lower() != "aberto":
            continue

        link = row.find("a", title="Imprimir Boleto")
        if not link:
            continue

        dia, mes, ano = vencimento.split("/")
        vencimento_formatado = f"{ano}-{mes}-{dia}"
        filename = f"{vencimento_formatado}_parcela-{parcela}.pdf"
        savepath = os.path.join(CAMINHO_BOLETOS, filename)
        enviados_path = os.path.join(CAMINHO_BOLETOS, "enviados", filename)

        if os.path.exists(savepath) or os.path.exists(enviados_path):
            logger.info(f"{filename} já existe (pendente ou enviado).")
            continue

        href = link["href"]
        boleto_url = BASE_URL_PORTAL + href
        boleto_response = session.get(boleto_url, timeout=TIMEOUT_PORTAL_SEGUNDOS)
        boleto_response.raise_for_status()
        # Verifica a assinatura do arquivo: o portal pode responder 200 com uma página de erro em HTML
        if not boleto_response.content.startswith(b"%PDF"):
            raise PortalDownloadError(
                f"Resposta do portal para {filename} não é um PDF "
                f"(Content-Type: {boleto_response.headers.get('Content-Type')})."
            )

        with open(savepath, "wb") as f:
            f.write(boleto_response.content)
        logger.info(f"{filename} salvo com sucesso.")
        count += 1

    if count == 0:
        logger.info("Nenhum novo boleto encontrado.")
