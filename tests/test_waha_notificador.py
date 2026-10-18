import base64

import pytest
import requests

from services.notificador import NotificacaoError
from services.waha_notificador import WahaNotificador


class RespostaFalsa:
    def __init__(self, dados=None, status=200):
        self.dados = dados or {}
        self.status_code = status

    def json(self):
        return self.dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class HttpFalso:
    def __init__(self, status_sessao="WORKING", contato_existe=True, status_envio=201):
        self.headers = {}
        self.status_sessao = status_sessao
        self.contato_existe = contato_existe
        self.status_envio = status_envio
        self.enviado = None

    def get(self, url, params=None, timeout=None):
        if url.endswith("/api/contacts/check-exists"):
            return RespostaFalsa({"numberExists": self.contato_existe, "chatId": "552799990000@c.us"})
        return RespostaFalsa({"status": self.status_sessao})

    def post(self, url, json=None, timeout=None):
        self.enviado = json
        return RespostaFalsa(status=self.status_envio)


def criar_notificador(**kwargs):
    notificador = WahaNotificador(url="http://waha:3000", api_key="chave", contato="5527999990000")
    notificador.http = HttpFalso(**kwargs)
    return notificador


@pytest.fixture
def pdf(tmp_path):
    caminho = tmp_path / "2026-10-25_parcela-5.pdf"
    caminho.write_bytes(b"%PDF-1.4 conteudo")
    return str(caminho)


def test_sem_contato_configurado_levanta_erro():
    with pytest.raises(NotificacaoError):
        WahaNotificador(url="http://waha:3000", api_key=None, contato=None)


def test_api_key_e_enviada_no_cabecalho():
    notificador = WahaNotificador(url="http://waha:3000", api_key="chave", contato="5527999990000")
    assert notificador.http.headers["X-Api-Key"] == "chave"


def test_sessao_working_esta_conectada():
    assert criar_notificador(status_sessao="WORKING").esta_conectado() is True


def test_sessao_aguardando_qr_nao_esta_conectada():
    assert criar_notificador(status_sessao="SCAN_QR_CODE").esta_conectado() is False


def test_envia_pdf_em_base64_para_o_chat_id_resolvido(pdf):
    notificador = criar_notificador()

    notificador.enviar_documento(pdf, legenda="Boleto")

    enviado = notificador.http.enviado
    assert enviado["chatId"] == "552799990000@c.us"
    assert enviado["file"] == {
        "mimetype": "application/pdf",
        "filename": "2026-10-25_parcela-5.pdf",
        "data": base64.b64encode(b"%PDF-1.4 conteudo").decode("ascii"),
    }


def test_contato_sem_whatsapp_levanta_erro(pdf):
    with pytest.raises(NotificacaoError):
        criar_notificador(contato_existe=False).enviar_documento(pdf, legenda="Boleto")


def test_erro_http_no_envio_levanta_notificacao_error(pdf):
    with pytest.raises(NotificacaoError):
        criar_notificador(status_envio=500).enviar_documento(pdf, legenda="Boleto")


@pytest.mark.parametrize(
    "status_envio, variavel_indicada",
    [(401, "WAHA_API_KEY"), (404, "WAHA_SESSAO")],
)
def test_erro_http_indica_a_variavel_a_conferir(pdf, status_envio, variavel_indicada):
    with pytest.raises(NotificacaoError, match=variavel_indicada):
        criar_notificador(status_envio=status_envio).enviar_documento(pdf, legenda="Boleto")


def test_waha_inacessivel_indica_waha_url(pdf):
    notificador = criar_notificador()

    def sem_conexao(*args, **kwargs):
        raise requests.ConnectionError("recusada")

    notificador.http.post = sem_conexao
    with pytest.raises(NotificacaoError, match="WAHA_URL"):
        notificador.enviar_documento(pdf, legenda="Boleto")


def test_sessao_inexistente_nao_esta_conectada():
    notificador = criar_notificador()
    notificador.http.get = lambda *args, **kwargs: RespostaFalsa(status=404)
    assert notificador.esta_conectado() is False
