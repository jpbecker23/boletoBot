import base64
import os

import requests

from core.config import CONTATO, TIMEOUT_WAHA_SEGUNDOS, WAHA_API_KEY, WAHA_SESSAO, WAHA_URL
from core.logger import get_logger
from services.notificador import NotificacaoError

logger = get_logger(__name__)

STATUS_SESSAO_CONECTADA = "WORKING"


class WahaNotificador:
    """Envia o boleto pelo WhatsApp usando a API do WAHA (https://waha.devlike.pro)."""

    def __init__(
        self,
        url: str = WAHA_URL,
        api_key: str | None = WAHA_API_KEY,
        sessao: str = WAHA_SESSAO,
        contato: str | None = CONTATO,
    ):
        if not contato:
            raise NotificacaoError("CONTATO não configurado no .env.")
        self.url = url
        self.sessao = sessao
        self.contato = contato
        self.http = requests.Session()
        if api_key:
            self.http.headers["X-Api-Key"] = api_key

    def esta_conectado(self) -> bool:
        try:
            resposta = self.http.get(
                f"{self.url}/api/sessions/{self.sessao}", timeout=TIMEOUT_WAHA_SEGUNDOS
            )
            resposta.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Não foi possível verificar a sessão do WhatsApp. {self._descrever_falha(e)}")
            return False

        status = resposta.json().get("status")
        if status != STATUS_SESSAO_CONECTADA:
            logger.error(
                f"Sessão '{self.sessao}' do WhatsApp não está conectada (status: {status}). "
                f"Acesse {self.url}/dashboard e escaneie o QR Code."
            )
            return False
        return True

    def enviar_documento(self, caminho_pdf: str, legenda: str) -> None:
        with open(caminho_pdf, "rb") as arquivo:
            conteudo = base64.b64encode(arquivo.read()).decode("ascii")

        payload = {
            "session": self.sessao,
            "chatId": self._resolver_chat_id(),
            "file": {
                "mimetype": "application/pdf",
                "filename": os.path.basename(caminho_pdf),
                "data": conteudo,
            },
            "caption": legenda,
        }
        try:
            resposta = self.http.post(
                f"{self.url}/api/sendFile", json=payload, timeout=TIMEOUT_WAHA_SEGUNDOS
            )
            resposta.raise_for_status()
        except requests.RequestException as e:
            raise NotificacaoError(f"Falha ao enviar o documento. {self._descrever_falha(e)}") from e

    def _resolver_chat_id(self) -> str:
        """
        Consulta o chatId real do contato. Números brasileiros antigos podem estar
        registrados no WhatsApp sem o 9º dígito, então montar o chatId direto do
        número pode apontar para um contato inexistente.
        """
        try:
            resposta = self.http.get(
                f"{self.url}/api/contacts/check-exists",
                params={"phone": self.contato, "session": self.sessao},
                timeout=TIMEOUT_WAHA_SEGUNDOS,
            )
            resposta.raise_for_status()
        except requests.RequestException as e:
            raise NotificacaoError(f"Falha ao verificar o contato. {self._descrever_falha(e)}") from e

        dados = resposta.json()
        if not dados.get("numberExists"):
            raise NotificacaoError(f"O número {self.contato} não possui WhatsApp.")
        return dados["chatId"]

    def _descrever_falha(self, erro: requests.RequestException) -> str:
        """Traduz a falha de comunicação com o WAHA em uma mensagem com a ação a tomar."""
        if isinstance(erro, requests.ConnectionError):
            return (
                f"WAHA inacessível em {self.url}. Verifique se o container está rodando "
                f"e o WAHA_URL no .env."
            )
        if isinstance(erro, requests.Timeout):
            return f"WAHA não respondeu em {TIMEOUT_WAHA_SEGUNDOS}s."

        status = erro.response.status_code if erro.response is not None else None
        if status == 401:
            return "API key recusada pelo WAHA. Confira o WAHA_API_KEY no .env."
        if status == 404:
            return (
                f"A sessão '{self.sessao}' não existe no WAHA. Confira o WAHA_SESSAO no .env "
                f"ou crie a sessão em {self.url}/dashboard."
            )
        return f"Erro inesperado do WAHA: {erro}"
