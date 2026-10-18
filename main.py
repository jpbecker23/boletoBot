import sys
import time

from core.config import INTERVALO_HORAS
from core.logger import get_logger
from services.boleto_service import arquivar_boleto, listar_pendentes, selecionar_boleto
from services.notificador import Notificador
from services.portal_service import executar_download
from services.waha_notificador import WahaNotificador

logger = get_logger(__name__)


def rotina_principal(notificador: Notificador):
    logger.info("=== Iniciando rotina do boletoBot ===")

    # Verificado em toda execução, mesmo sem boleto a enviar, para detectar
    # cedo uma sessão do WhatsApp desconectada
    if not notificador.esta_conectado():
        return "ERROR"

    boletos_pendentes = listar_pendentes()

    if boletos_pendentes:
        logger.info(
            f"Etapa 1: Boleto pendente já encontrado na pasta ('{boletos_pendentes[0]}'). "
            f"Ignorando navegação ao portal UVV."
        )
    else:
        logger.info("Etapa 1: Baixando boletos no portal da instituição...")
        try:
            executar_download()
            if not listar_pendentes():
                logger.info("Nenhum boleto encontrado no portal ou na pasta. Encerrando.")
                return "NO_BOLETOS"
        except Exception as e:
            logger.error(f"Falha ao baixar boletos: {e}")
            return "ERROR"

    logger.info("Etapa 2: Selecionando boleto dentro do prazo de envio...")
    boleto = selecionar_boleto()
    if not boleto:
        logger.info("Nenhum boleto dentro do prazo de envio. Encerrando.")
        return "NO_BOLETOS"

    logger.info(f"Etapa 3: Enviando {boleto.nome} pelo WhatsApp...")
    try:
        notificador.enviar_documento(
            boleto.caminho, legenda=f"Boleto da mensalidade UVV: {boleto.nome}"
        )
    except Exception as e:
        logger.error(f"Falha ao enviar o boleto: {e}. Ele será reenviado na próxima execução.")
        return "ERROR"

    arquivar_boleto(boleto.caminho, boleto.pasta_enviados, boleto.nome)
    logger.info("=== Rotina finalizada com sucesso! ===")
    return "SUCCESS"


def main():
    notificador = WahaNotificador()

    # Se a variável existir e for um número maior que zero, entra em modo loop (contínuo)
    if INTERVALO_HORAS and INTERVALO_HORAS.isdigit() and int(INTERVALO_HORAS) > 0:
        horas = int(INTERVALO_HORAS)
        logger.info(
            f"MODO CONTÍNUO: O bot rodará em loop a cada {horas} hora(s). "
            f"Para desligar, pare o container."
        )
        while True:
            rotina_principal(notificador)
            logger.info(f"Dormindo por {horas} hora(s)... O bot acordará no próximo ciclo.")
            time.sleep(horas * 3600)  # 3600 segundos = 1 hora
    else:
        # Execução padrão (roda apenas uma vez e se desliga)
        logger.info("MODO ÚNICO: O bot rodará uma vez e o container será desligado.")
        status = rotina_principal(notificador)
        if status == "ERROR":
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
