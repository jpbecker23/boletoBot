import os
import shutil
from dataclasses import dataclass
from datetime import datetime

from core.config import CAMINHO_BOLETOS
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BoletoInfo:
    nome: str
    caminho: str
    pasta_enviados: str


def listar_pendentes() -> list[str]:
    """Retorna a lista de PDFs pendentes na pasta de boletos, ordenados por nome."""
    if not (os.path.exists(CAMINHO_BOLETOS) and os.path.isdir(CAMINHO_BOLETOS)):
        logger.error(f"O diretório {CAMINHO_BOLETOS} não foi encontrado.")
        return []

    boletos = [f for f in os.listdir(CAMINHO_BOLETOS) if f.endswith(".pdf")]
    boletos.sort()
    return boletos


def selecionar_boleto() -> BoletoInfo | None:
    """
    Seleciona o próximo boleto a ser enviado.

    Regra de negócio:
    - Pega o primeiro PDF da pasta (ordenado por nome = por data de vencimento)
    - Se faltar mais de 7 dias para o vencimento, não envia (retorna None)
    - Se o nome do arquivo não seguir o padrão esperado, envia por segurança (fallback)

    Retorna BoletoInfo, ou None se não houver boleto elegível.
    """
    boletos = listar_pendentes()
    if not boletos:
        logger.info("Nenhum boleto pendente na pasta.")
        return None

    pasta_enviados = os.path.join(CAMINHO_BOLETOS, "enviados")
    os.makedirs(pasta_enviados, exist_ok=True)

    boleto_selecionado = boletos[0]

    try:
        data_venc_str = boleto_selecionado.split("_")[0]
        data_venc = datetime.strptime(data_venc_str, "%Y-%m-%d")
        dias_para_vencimento = (data_venc - datetime.now()).days

        if dias_para_vencimento > 7:
            logger.info(
                f"Aguardando: {boleto_selecionado} vence em {dias_para_vencimento} dias. "
                f"(Limite para envio: 7 dias)"
            )
            return None

    except Exception as e:
        logger.warning(
            f"Formato de nome inesperado em {boleto_selecionado}. Erro: {e}"
        )
        logger.info("Enviando por segurança (fallback)...")

    return BoletoInfo(
        nome=boleto_selecionado,
        caminho=os.path.abspath(os.path.join(CAMINHO_BOLETOS, boleto_selecionado)),
        pasta_enviados=pasta_enviados,
    )


def arquivar_boleto(caminho_origem: str, pasta_enviados: str, nome: str):
    """Move o boleto enviado para a pasta 'enviados'."""
    caminho_destino = os.path.join(pasta_enviados, nome)
    shutil.move(caminho_origem, caminho_destino)
    logger.info("Boleto movido para a pasta 'enviados'.")
