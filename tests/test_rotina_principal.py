from datetime import date, timedelta

import pytest

import main
from services import boleto_service
from services.notificador import NotificacaoError


class NotificadorFalso:
    def __init__(self, conectado=True, falhar_envio=False):
        self.conectado = conectado
        self.falhar_envio = falhar_envio
        self.enviados = []

    def esta_conectado(self):
        return self.conectado

    def enviar_documento(self, caminho_pdf, legenda):
        if self.falhar_envio:
            raise NotificacaoError("falha simulada")
        self.enviados.append(caminho_pdf)


@pytest.fixture
def pasta_boletos(tmp_path, monkeypatch):
    monkeypatch.setattr(boleto_service, "CAMINHO_BOLETOS", str(tmp_path))
    monkeypatch.setattr(main, "executar_download", lambda: None)
    return tmp_path


def criar_boleto(pasta, dias_para_vencimento):
    nome = f"{(date.today() + timedelta(days=dias_para_vencimento)).isoformat()}_parcela-1.pdf"
    (pasta / nome).write_bytes(b"%PDF")
    return nome


def test_boleto_no_prazo_e_enviado_e_arquivado(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=3)
    notificador = NotificadorFalso()

    assert main.rotina_principal(notificador) == "SUCCESS"
    assert (pasta_boletos / "enviados" / nome).exists()


def test_falha_no_envio_mantem_boleto_pendente(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=3)

    assert main.rotina_principal(NotificadorFalso(falhar_envio=True)) == "ERROR"
    assert (pasta_boletos / nome).exists()


def test_sessao_desconectada_encerra_com_erro_sem_enviar(pasta_boletos):
    criar_boleto(pasta_boletos, dias_para_vencimento=3)
    notificador = NotificadorFalso(conectado=False)

    assert main.rotina_principal(notificador) == "ERROR"
    assert notificador.enviados == []


def test_boleto_fora_do_prazo_nao_e_enviado(pasta_boletos):
    criar_boleto(pasta_boletos, dias_para_vencimento=20)
    notificador = NotificadorFalso()

    assert main.rotina_principal(notificador) == "NO_BOLETOS"
    assert notificador.enviados == []
