import os
import requests
from bs4 import BeautifulSoup

from core.config import MATRICULA, PASSWORD, BASE_URL_PORTAL, CAMINHO_BOLETOS
from core.logger import get_logger

logger = get_logger(__name__)


def executar_download():
    """
    Realiza login HTTP no portal UVV, busca boletos com status 'aberto',
    e baixa os PDFs para a pasta de boletos.
    """
    os.makedirs(CAMINHO_BOLETOS, exist_ok=True)

    login_url = f"{BASE_URL_PORTAL}/Login"
    boletos_url = f"{BASE_URL_PORTAL}/Aluno/Extrato"

    session = requests.Session()

    payload = {
        "Matricula": MATRICULA,
        "Password": PASSWORD,
    }

    logger.info("Realizando login no portal...")
    session.post(login_url, data=payload)

    response = session.get(boletos_url)
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

        href = link["href"]
        boleto_url = BASE_URL_PORTAL + href
        boleto_response = session.get(boleto_url)

        dia, mes, ano = vencimento.split("/")
        vencimento_formatado = f"{ano}-{mes}-{dia}"
        filename = f"{vencimento_formatado}_parcela-{parcela}.pdf"
        savepath = os.path.join(CAMINHO_BOLETOS, filename)

        if os.path.exists(savepath):
            logger.info(f"{filename} já existe.")
            continue

        with open(savepath, "wb") as f:
            f.write(boleto_response.content)
        logger.info(f"{filename} salvo com sucesso.")
        count += 1

    if count == 0:
        logger.info("Nenhum novo boleto encontrado.")


if __name__ == "__main__":
    executar_download()
