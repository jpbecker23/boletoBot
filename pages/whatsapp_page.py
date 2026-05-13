import os
from core.config import USER_DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)


class WhatsAppPage:
    """Page Object para o WhatsApp Web. Encapsula seletores e interações de UI."""

    # ── Seletores ──
    CAMPO_TEXTO = 'div[contenteditable="true"]'
    QR_CANVAS = "canvas"
    BTN_ANEXAR = 'button[aria-label="Attach"], span[data-icon="plus-rounded"]'
    BTN_DOCUMENTO = 'button[aria-label="Document"], button[aria-label="Documento"]'
    BTN_ENVIAR = (
        'div[role="button"][aria-label="Enviar"], '
        'div[role="button"][aria-label="Send"], '
        'span[data-icon="send"]'
    )

    def __init__(self, page):
        self.page = page

    # ── Navegação ──

    def navegar_para_contato(self, numero: str):
        """Abre a conversa direta com o número informado."""
        logger.info(f"Abrindo conversa com {numero}...")
        self.page.goto(f"https://web.whatsapp.com/send?phone={numero}")

    def abrir_para_autenticacao(self):
        """Abre o WhatsApp Web na home para permitir scan do QR Code."""
        logger.info("Abrindo WhatsApp para autenticação...")
        self.page.goto("https://web.whatsapp.com/")

    # ── Carregamento e Autenticação ──

    def aguardar_carregamento(self, timeout=60000):
        """Aguarda pelo campo de texto (logado) ou canvas do QR Code (deslogado)."""
        logger.info("Aguardando carregamento da interface do WhatsApp...")
        self.page.wait_for_selector(
            f"{self.CAMPO_TEXTO}, {self.QR_CANVAS}", timeout=timeout
        )

    def precisa_autenticacao(self) -> bool:
        """Retorna True se o QR Code está visível na tela (usuário deslogado)."""
        return self.page.locator(self.QR_CANVAS).count() > 0

    def capturar_qr_code(self) -> str:
        """Faz screenshot do QR Code e retorna o caminho do arquivo gerado."""
        qr_path = os.path.join(USER_DATA_DIR, "qrcode.png")
        self.page.locator(self.QR_CANVAS).first.screenshot(path=qr_path)
        logger.info(f"⚠️  ABRA O ARQUIVO NO SEU PC: {qr_path}")
        logger.info("⚠️  Escaneie o QR Code com seu celular para continuar.")
        return qr_path

    def aguardar_scan_qr(self, timeout=60000):
        """Aguarda o usuário escanear o QR Code (campo de texto aparece)."""
        logger.info(
            "Aguardando você escanear o QR Code (Tempo limite: 60 segundos)..."
        )
        self.page.wait_for_selector(self.CAMPO_TEXTO, timeout=timeout)
        logger.info("✅ Autenticação realizada com sucesso!")

    def limpar_qr_code(self, qr_path: str):
        """Remove a imagem do QR Code gerada."""
        if os.path.exists(qr_path):
            os.remove(qr_path)

    # ── Envio de Arquivo ──

    def anexar_documento(self, caminho_arquivo: str):
        """Abre o menu de anexos e seleciona o arquivo via file chooser."""
        logger.info("Abrindo menu de anexos...")
        self.page.locator(self.BTN_ANEXAR).first.click()
        self.page.wait_for_timeout(1000)

        logger.info("Clicando no botão de Documento...")
        with self.page.expect_file_chooser() as fc_info:
            # WhatsApp muda constantemente as labels e varia entre Inglês e Português
            self.page.locator(self.BTN_DOCUMENTO).first.click()

        file_chooser = fc_info.value
        file_chooser.set_files(caminho_arquivo)

        logger.info("Aguardando a tela de prévia do anexo...")
        # Espera a animação do preview do PDF carregar
        self.page.wait_for_timeout(3000)

    def enviar_anexo(self):
        """Clica no botão de envio. Usa Enter como fallback de segurança."""
        logger.info("Clicando no botão de envio...")
        try:
            # Na interface nova do WhatsApp, esse botão deixou de ser um <button> e virou um <div>!
            self.page.locator(self.BTN_ENVIAR).locator("visible=true").first.click(
                timeout=10000
            )
        except Exception:
            logger.warning(
                "Botão visual não localizado. Usando método de segurança (Tecla Enter)..."
            )
            # Failsafe supremo: Na tela de prévia, a tecla Enter envia o documento
            self.page.keyboard.press("Enter")

        # Um pequeno wait para garantir que o upload do arquivo terminou no servidor deles
        self.page.wait_for_timeout(3000)

    # ── Debug ──

    def screenshot_debug(self, caminho: str):
        """Tira um screenshot full page para fins de debug."""
        self.page.screenshot(path=caminho, full_page=True)
        logger.info(f"📸 Para entender o que deu errado, abra a imagem: {caminho}")

    # ── Utilitários ──

    def aguardar(self, ms: int):
        """Wrapper para wait_for_timeout do Playwright."""
        self.page.wait_for_timeout(ms)
