import os
from core.logger import get_logger
from core.config import (
    TIMEOUT_CARREGAMENTO_WHATSAPP,
    TIMEOUT_SCAN_QR,
    TIMEOUT_MENU_ANEXO,
    TIMEOUT_PREVIEW_ANEXO,
    TIMEOUT_ENVIO,
    TIMEOUT_CONFIRMACAO_ENVIO
)

logger = get_logger(__name__)


class WhatsAppPage:
    """Page Object para o WhatsApp Web. Encapsula seletores e interações de UI."""

    # ── Seletores ──
    # O idioma da interface segue o idioma do celular vinculado, então os seletores
    # priorizam ícones (data-icon), que não são traduzidos, e usam os textos em
    # inglês, português e alemão apenas como reserva.
    CAMPO_TEXTO = 'div[contenteditable="true"]'
    QR_CANVAS = "canvas"
    BTN_ANEXAR = (
        'footer span[data-icon="ic-attach-file"], '
        'footer span[data-icon="plus-rounded"], '
        'footer button[aria-label="Attach"], '
        'footer button[aria-label="Anexar"], '
        'footer button[aria-label="Anhängen"]'
    )
    BTN_DOCUMENTO = (
        '[role="menuitem"][aria-label="Document"], '
        '[role="menuitem"][aria-label="Documento"], '
        '[role="menuitem"][aria-label="Dokument"]'
    )
    # Reserva: "Documento" é hoje o primeiro item do menu de anexos
    ITEM_MENU_ANEXO = '[role="menuitem"]'
    BTN_ENVIAR = (
        'span[data-icon="wds-ic-send-filled"], '
        'span[data-icon="send"], '
        '[role="button"][aria-label^="Send"], '
        '[role="button"][aria-label^="Enviar"], '
        '[role="button"][aria-label^="Senden"]'
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

    def aguardar_carregamento(self, timeout=TIMEOUT_CARREGAMENTO_WHATSAPP):
        """Aguarda pelo campo de texto (logado) ou canvas do QR Code (deslogado)."""
        logger.info("Aguardando carregamento da interface do WhatsApp...")
        try:
            self.page.wait_for_selector(
                f"{self.CAMPO_TEXTO}, {self.QR_CANVAS}", timeout=timeout
            )
        except Exception as e:
            if "Target closed" in str(e):
                logger.info("Navegador fechado durante o carregamento.")
                return
            raise e

    def precisa_autenticacao(self) -> bool:
        """Retorna True se o QR Code está visível na tela (usuário deslogado)."""
        try:
            return self.page.locator(self.QR_CANVAS).count() > 0
        except Exception:
            return False

    def capturar_qr_code(self, qr_path: str) -> str:
        """Faz screenshot do QR Code e retorna o caminho do arquivo gerado."""
        self.page.locator(self.QR_CANVAS).first.screenshot(path=qr_path)
        logger.info(f"⚠️  ABRA O ARQUIVO NO SEU PC: {qr_path}")
        logger.info("⚠️  Escaneie o QR Code com seu celular para continuar.")
        return qr_path

    def aguardar_scan_qr(self, timeout=TIMEOUT_SCAN_QR):
        """Aguarda o usuário escanear o QR Code (campo de texto aparece)."""
        logger.info(
            "Aguardando você escanear o QR Code (Tempo limite: 60 segundos)..."
        )
        try:
            self.page.wait_for_selector(self.CAMPO_TEXTO, timeout=timeout)
            logger.info("✅ Autenticação realizada com sucesso!")
        except Exception as e:
            if "Target closed" in str(e):
                logger.info("Navegador fechado durante o scan do QR Code.")
                return
            raise e

    def limpar_qr_code(self, qr_path: str):
        """Remove a imagem do QR Code gerada."""
        if os.path.exists(qr_path):
            os.remove(qr_path)

    # ── Envio de Arquivo ──

    def anexar_documento(self, caminho_arquivo: str):
        """Abre o menu de anexos e seleciona o arquivo via file chooser."""
        logger.info("Abrindo menu de anexos...")
        self.page.locator(self.BTN_ANEXAR).first.click()
        self.aguardar(TIMEOUT_MENU_ANEXO)

        logger.info("Clicando no botão de Documento...")
        botao_documento = self.page.locator(self.BTN_DOCUMENTO)
        if botao_documento.count() == 0:
            logger.warning("Opção 'Documento' não reconhecida pelo texto. Usando o 1º item do menu.")
            botao_documento = self.page.locator(self.ITEM_MENU_ANEXO)
        with self.page.expect_file_chooser() as fc_info:
            botao_documento.first.click()

        file_chooser = fc_info.value
        file_chooser.set_files(caminho_arquivo)

        logger.info("Aguardando a tela de prévia do anexo...")
        # Espera a animação do preview do PDF carregar
        self.aguardar(TIMEOUT_PREVIEW_ANEXO)

    def enviar_anexo(self):
        """Clica no botão de envio. Usa Enter como fallback de segurança."""
        logger.info("Clicando no botão de envio...")
        try:
            # Na interface nova do WhatsApp, esse botão deixou de ser um <button> e virou um <div>!
            self.page.locator(self.BTN_ENVIAR).locator("visible=true").first.click(
                timeout=TIMEOUT_ENVIO
            )
        except Exception:
            logger.warning(
                "Botão visual não localizado. Usando método de segurança (Tecla Enter)..."
            )
            # Failsafe supremo: Na tela de prévia, a tecla Enter envia o documento
            self.page.keyboard.press("Enter")

    def confirmar_envio(self, nome_arquivo: str, timeout=TIMEOUT_CONFIRMACAO_ENVIO) -> bool:
        """
        Aguarda a mensagem com o arquivo aparecer na conversa com o ícone de check (✓/✓✓).
        Não depende de classes CSS nem de idioma. Retorna False se não confirmar no timeout.
        """
        logger.info("Aguardando confirmação de envio (check na mensagem)...")
        nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
        try:
            self.page.wait_for_function(
                _JS_MENSAGEM_CONFIRMADA, arg=nome_sem_extensao, timeout=timeout
            )
            return True
        except Exception as e:
            icones = self._icones_perto_do_arquivo(nome_sem_extensao)
            logger.error(
                f"Envio não confirmado em {timeout // 1000}s. "
                f"Ícones encontrados perto do arquivo: {icones}. Detalhe: {e}"
            )
            return False

    def _icones_perto_do_arquivo(self, nome: str) -> list[str] | None:
        """Diagnóstico: nomes dos ícones (data-icon) na bolha que contém o arquivo."""
        try:
            return self.page.evaluate(_JS_ICONES_PERTO_DO_ARQUIVO, nome)
        except Exception:
            return None

    # ── Debug ──

    def screenshot_debug(self, caminho: str):
        """Tira um screenshot full page para fins de debug."""
        try:
            self.page.screenshot(path=caminho, full_page=True)
            logger.info(f"📸 Para entender o que deu errado, abra a imagem: {caminho}")
        except Exception:
            # Se a página já fechou, não tem como tirar print
            logger.warning("Não foi possível tirar screenshot de debug: Navegador já fechado.")

    # ── Utilitários ──

    def aguardar(self, ms: int):
        """Wrapper para wait_for_timeout do Playwright."""
        try:
            self.page.wait_for_timeout(ms)
        except Exception as e:
            # Se o erro for de 'Target closed', ignoramos pois o usuário provavelmente fechou a janela
            if "Target closed" in str(e) or "Target page, context or browser has been closed" in str(e):
                logger.info("Navegador fechado pelo usuário durante a espera.")
            else:
                raise e


# Sobe a partir do elemento com o nome do arquivo até o tamanho de uma bolha de mensagem
# (limitado pela altura, para não alcançar o restante da conversa).
_JS_BOLHA_DO_ARQUIVO = """
(nome) => {
  const main = document.querySelector('#main');
  if (!main) return [];
  const folhas = [...main.querySelectorAll('*')]
    .filter(e => e.children.length === 0 && (e.textContent || '').includes(nome));
  return folhas.reverse().map(folha => {
    const ancestrais = [];
    for (let no = folha; no && no !== main; no = no.parentElement) {
      if (no.getBoundingClientRect().height > 300) break;
      ancestrais.push(no);
    }
    return ancestrais[ancestrais.length - 1];
  }).filter(Boolean);
}
"""

_JS_MENSAGEM_CONFIRMADA = f"""
(nome) => {{
  const bolhas = ({_JS_BOLHA_DO_ARQUIVO})(nome);
  return bolhas.some(bolha => [...bolha.querySelectorAll('[data-icon]')]
    .some(icone => /check/i.test(icone.getAttribute('data-icon'))));
}}
"""

_JS_ICONES_PERTO_DO_ARQUIVO = f"""
(nome) => {{
  const bolhas = ({_JS_BOLHA_DO_ARQUIVO})(nome);
  return bolhas.length ? [...bolhas[0].querySelectorAll('[data-icon]')].map(e => e.getAttribute('data-icon')) : [];
}}
"""
