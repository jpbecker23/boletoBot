import sys
import time

from core.config import CAMINHO_BOLETOS, INTERVALO_HORAS
from core.logger import get_logger
from services.boleto_service import listar_pendentes
from services.portal_service import executar_download
from services.whatsapp_service import enviar_boleto

logger = get_logger(__name__)


def rotina_principal():
    logger.info("=== Iniciando rotina do boletoBot ===")

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
                return False
        except Exception as e:
            logger.error(f"Falha ao baixar boletos: {e}")
            return False

    logger.info("Etapa 2: Enviando via WhatsApp Web...")
    try:
        enviar_boleto(headless=True)
    except Exception as e:
        logger.error(f"Falha ao comunicar com o WhatsApp: {e}")
        return False

    logger.info("=== Rotina finalizada com sucesso! ===")
    return True


def main():
    # Se a variável existir e for um número maior que zero, entra em modo loop (contínuo)
    if INTERVALO_HORAS and INTERVALO_HORAS.isdigit() and int(INTERVALO_HORAS) > 0:
        horas = int(INTERVALO_HORAS)
        logger.info(
            f"MODO CONTÍNUO: O bot rodará em loop a cada {horas} hora(s). "
            f"Para desligar, pare o container."
        )
        while True:
            rotina_principal()
            logger.info(f"Dormindo por {horas} hora(s)... O bot acordará no próximo ciclo.")
            time.sleep(horas * 3600)  # 3600 segundos = 1 hora
    else:
        # Execução padrão (roda apenas uma vez e se desliga)
        logger.info("MODO ÚNICO: O bot rodará uma vez e o container será desligado.")
        sucesso = rotina_principal()
        if not sucesso:
            sys.exit(1)


if __name__ == "__main__":
    main()
