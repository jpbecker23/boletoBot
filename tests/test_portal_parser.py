from services.portal_service import BoletoPortal, extrair_boletos_abertos


def linha_extrato(parcela="3", vencimento="15/10/2026", status="Aberto", link=True):
    acao = '<a title="Imprimir Boleto" href="/Aluno/Boleto/123">imprimir</a>' if link else ""
    colunas = ["", parcela, "", "", "", "", vencimento, status, acao]
    return "<tr>" + "".join(f"<td>{c}</td>" for c in colunas) + "</tr>"


def extrato(*linhas):
    return "<table><tr><th>Cabeçalho</th></tr>" + "".join(linhas) + "</table>"


def test_extrai_parcela_aberta_com_vencimento_em_formato_iso():
    boletos = extrair_boletos_abertos(extrato(linha_extrato()))
    assert boletos == [BoletoPortal(parcela="3", vencimento="2026-10-15", href="/Aluno/Boleto/123")]


def test_nome_do_arquivo_segue_padrao_data_parcela():
    boleto = BoletoPortal(parcela="3", vencimento="2026-10-15", href="")
    assert boleto.nome_arquivo == "2026-10-15_parcela-3.pdf"


def test_status_aberto_ignora_maiusculas():
    assert len(extrair_boletos_abertos(extrato(linha_extrato(status="ABERTO")))) == 1


def test_ignora_parcela_paga():
    assert extrair_boletos_abertos(extrato(linha_extrato(status="Pago"))) == []


def test_ignora_parcela_aberta_sem_link_de_boleto():
    assert extrair_boletos_abertos(extrato(linha_extrato(link=False))) == []


def test_ignora_linhas_com_menos_de_9_colunas():
    assert extrair_boletos_abertos("<table><tr><td>Aberto</td></tr></table>") == []


def test_extrato_sem_tabela_retorna_lista_vazia():
    assert extrair_boletos_abertos("<html><body>Sem dados</body></html>") == []


def test_retorna_todas_as_parcelas_abertas():
    html = extrato(
        linha_extrato(parcela="2", vencimento="15/09/2026", status="Pago"),
        linha_extrato(parcela="3", vencimento="15/10/2026"),
        linha_extrato(parcela="4", vencimento="15/11/2026"),
    )
    assert [b.parcela for b in extrair_boletos_abertos(html)] == ["3", "4"]
