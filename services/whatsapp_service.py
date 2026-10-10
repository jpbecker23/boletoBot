import os
from enum import Enum

from playwright.sync_api import sync_playwright

from core.browser import create_context
from core.config import (
    CONTATO, CAMINHO_BOLETOS, USER_DATA_DIR, HEADLESS,
    TIMEOUT_FECHAMENTO, TIMEOUT_AUTENTICACAO_MANUAL
)
from core.logger import get_logger
from pages.whatsapp_page import WhatsAppPage
from services.boleto_service import selecionar_boleto, arquivar_boleto

logger = get_logger(__name__)


class ResultadoEnvio(Enum):
    ENVIADO = "ENVIADO"
    NADA_A_ENVIAR = "NADA_A_ENVIAR"
    FALHA = "FALHA"


def enviar_boleto(headless=HEADLESS) -> ResultadoEnvio:
    """
    Fluxo completo de envio de boleto via WhatsApp Web.

    1. Seleciona o boleto elegível (regra dos 7 dias)
    2. Abre o navegador com sessão persistente
    3. Navega até o contato
    4. Trata autenticação (QR Code) se necessário
    5. Anexa e envia o PDF
    6. Arquiva o boleto na pasta 'enviados'
    """
    boleto = selecionar_boleto()

    if not boleto:
        return ResultadoEnvio.NADA_A_ENVIAR

    with sync_playwright() as p:
        context = create_context(p, headless=headless)
        page = context.pages[0]
        whatsapp = WhatsAppPage(page)

        whatsapp.navegar_para_contato(CONTATO)

        try:
            whatsapp.aguardar_carregamento()

            # Se precisar autenticar (QR Code visível)
            if whatsapp.precisa_autenticacao():
                logger.warning("⚠️  ATENÇÃO: Autenticação necessária! Gerando QR Code...")
                qr_path = os.path.join(USER_DATA_DIR, "qrcode.png")
                whatsapp.capturar_qr_code(qr_path)
                whatsapp.aguardar_scan_qr()
                whatsapp.limpar_qr_code(qr_path)

            whatsapp.aguardar(3000)
            logger.info("Interface carregada!")

        except Exception as e:
            logger.error(
                f"O login não foi detectado, você não escaneou o QR code a tempo, "
                f"ou a página demorou demais. Detalhe: {e}"
            )
            debug_path = os.path.join(CAMINHO_BOLETOS, "debug_whatsapp.png")
            whatsapp.screenshot_debug(debug_path)
            return ResultadoEnvio.FALHA

        # Envio do boleto
        logger.info(f"Preparando envio do boleto: {boleto.nome}")
        whatsapp.anexar_documento(boleto.caminho)
        whatsapp.enviar_anexo()

        if not whatsapp.confirmar_envio(boleto.nome):
            debug_path = os.path.join(CAMINHO_BOLETOS, "debug_whatsapp.png")
            whatsapp.screenshot_debug(debug_path)
            logger.error("Boleto mantido como pendente para nova tentativa.")
            return ResultadoEnvio.FALHA
        logger.info("Arquivo enviado com sucesso!")

        # Arquivamento
        arquivar_boleto(boleto.caminho, boleto.pasta_enviados, boleto.nome)

        logger.info("Processo concluído. Fechando navegador em 5 segundos...")
        whatsapp.aguardar(TIMEOUT_FECHAMENTO)
        try:
            context.close()
        except Exception:
            pass
        return ResultadoEnvio.ENVIADO


def abrir_para_autenticacao():
    """Abre o WhatsApp Web em modo visível apenas para permitir scan do QR Code."""
    with sync_playwright() as p:
        context = create_context(p, headless=False)
        page = context.pages[0]
        whatsapp = WhatsAppPage(page)

        whatsapp.abrir_para_autenticacao()
        logger.info("Aguarde o carregamento e faça o login se necessário.")
        logger.info("O navegador fechará em 2 minutos ou quando você fechar a janela.")
        whatsapp.aguardar(TIMEOUT_AUTENTICACAO_MANUAL)
        try:
            context.close()
        except Exception:
            pass
