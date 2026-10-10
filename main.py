import sys
import time

from core.config import INTERVALO_HORAS
from core.logger import get_logger
from services.boleto_service import listar_pendentes
from services.portal_service import executar_download
from services.whatsapp_service import ResultadoEnvio, abrir_para_autenticacao, enviar_boleto

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
                return "NO_BOLETOS"
        except Exception as e:
            logger.error(f"Falha ao baixar boletos: {e}")
            return "ERROR"

    logger.info("Etapa 2: Enviando via WhatsApp Web...")
    try:
        resultado = enviar_boleto()
        if resultado == ResultadoEnvio.NADA_A_ENVIAR:
            logger.info("Nenhum boleto dentro do prazo de envio. Encerrando.")
            return "NO_BOLETOS"
        if resultado == ResultadoEnvio.FALHA:
            logger.error("Falha no fluxo de envio do boleto.")
            return "ERROR"
    except Exception as e:
        logger.error(f"Falha ao comunicar com o WhatsApp: {e}")
        return "ERROR"

    logger.info("=== Rotina finalizada com sucesso! ===")
    return "SUCCESS"


def main():
    if "--vincular" in sys.argv:
        abrir_para_autenticacao()
        sys.exit(0)

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
        status = rotina_principal()
        if status == "ERROR":
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
