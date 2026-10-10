from datetime import date, timedelta

import pytest

from services import boleto_service


@pytest.fixture
def pasta_boletos(tmp_path, monkeypatch):
    monkeypatch.setattr(boleto_service, "CAMINHO_BOLETOS", str(tmp_path))
    return tmp_path


def criar_boleto(pasta, dias_para_vencimento, parcela=1):
    vencimento = date.today() + timedelta(days=dias_para_vencimento)
    nome = f"{vencimento.isoformat()}_parcela-{parcela}.pdf"
    (pasta / nome).write_bytes(b"%PDF")
    return nome


def test_pasta_vazia_nao_seleciona_boleto(pasta_boletos):
    assert boleto_service.selecionar_boleto() is None


def test_boleto_com_mais_de_7_dias_aguarda(pasta_boletos):
    criar_boleto(pasta_boletos, dias_para_vencimento=8)
    assert boleto_service.selecionar_boleto() is None


def test_boleto_com_exatamente_7_dias_e_selecionado(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=7)
    assert boleto_service.selecionar_boleto().nome == nome


def test_boleto_vencendo_hoje_e_selecionado(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=0)
    assert boleto_service.selecionar_boleto().nome == nome


def test_boleto_vencido_e_selecionado(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=-3)
    assert boleto_service.selecionar_boleto().nome == nome


def test_seleciona_o_boleto_de_vencimento_mais_proximo(pasta_boletos):
    criar_boleto(pasta_boletos, dias_para_vencimento=35, parcela=2)
    nome_proximo = criar_boleto(pasta_boletos, dias_para_vencimento=5, parcela=1)
    assert boleto_service.selecionar_boleto().nome == nome_proximo


def test_nome_fora_do_padrao_e_enviado_por_seguranca(pasta_boletos):
    (pasta_boletos / "boleto.pdf").write_bytes(b"%PDF")
    assert boleto_service.selecionar_boleto().nome == "boleto.pdf"


def test_ignora_arquivos_que_nao_sao_pdf(pasta_boletos):
    (pasta_boletos / "debug_whatsapp.png").write_bytes(b"")
    assert boleto_service.selecionar_boleto() is None


def test_arquivar_move_boleto_para_enviados(pasta_boletos):
    nome = criar_boleto(pasta_boletos, dias_para_vencimento=1)
    boleto = boleto_service.selecionar_boleto()

    boleto_service.arquivar_boleto(boleto.caminho, boleto.pasta_enviados, boleto.nome)

    assert boleto_service.listar_pendentes() == []
    assert (pasta_boletos / "enviados" / nome).exists()
