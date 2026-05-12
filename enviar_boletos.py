import os
import shutil
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Configurações
NUMERO_CONTATO = os.getenv("CONTATO")
CAMINHO_ARQUIVO = os.getenv("ARQUIVO")
USER_DATA_DIR = "./auth"

def selecionar_boleto():
    if not (os.path.exists(CAMINHO_ARQUIVO) and os.path.isdir(CAMINHO_ARQUIVO)):
        print(f"Erro: O diretório {CAMINHO_ARQUIVO} não foi encontrado.")
        return None

    pasta_enviados = os.path.join(CAMINHO_ARQUIVO, 'enviados')
    os.makedirs(pasta_enviados, exist_ok=True)

    boletos = [f for f in os.listdir(CAMINHO_ARQUIVO) if f.endswith('.pdf')]
    if not boletos:
        print("Nenhum boleto pendente na pasta.")
        return None

    boletos.sort()
    boleto_selecionado = boletos[0]

    try:
        data_venc_str = boleto_selecionado.split('_')[0]
        data_venc = datetime.strptime(data_venc_str, '%Y-%m-%d')
        dias_para_vencimento = (data_venc - datetime.now()).days

        if dias_para_vencimento > 7:
            print(f"Aguardando: {boleto_selecionado} vence em {dias_para_vencimento} dias. (Limite para envio: 7 dias)")
            return None

    except Exception as e:
        print(f"Aviso: Formato de nome inesperado em {boleto_selecionado}. Erro: {e}")
        print("Enviando por segurança (fallback)...")

    return {
        "nome": boleto_selecionado,
        "caminho": os.path.abspath(os.path.join(CAMINHO_ARQUIVO, boleto_selecionado)),
        "pasta_enviados": pasta_enviados
    }

def enviar_arquivo():
    boleto = selecionar_boleto()
    if not boleto:
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.pages[0]

        print(f"Abrindo conversa com {NUMERO_CONTATO}...")
        page.goto(f"https://web.whatsapp.com/send?phone={NUMERO_CONTATO}")

        try:
            print("Aguardando carregamento da interface do WhatsApp...")
            page.wait_for_selector('div[contenteditable="true"]', timeout=60000)
            page.wait_for_timeout(3000)
            print("Interface carregada!")
        except Exception:
            print("Erro: O login não foi detectado ou a página demorou demais.")
            return

        print(f"Preparando envio do boleto: {boleto['nome']}")
        caminho_absoluto = boleto['caminho']

        print("Abrindo menu de anexos...")
        page.locator('button[aria-label="Attach"], span[data-icon="plus-rounded"]').first.click()
        page.wait_for_timeout(1000)

        print("Clicando no botão de Documento...")
        with page.expect_file_chooser() as fc_info:
            page.locator('button[aria-label="Document"]').first.click()

        file_chooser = fc_info.value
        file_chooser.set_files(caminho_absoluto)

        print("Aguardando botão de envio...")
        botao_enviar = 'span[data-testid="wds-ic-send-filled"]'
        page.wait_for_selector(botao_enviar, state="visible", timeout=20000)
        page.wait_for_timeout(3000)
        page.click(botao_enviar)

        print("Arquivo enviado com sucesso!")

        # Arquivamento
        caminho_enviado = os.path.join(boleto['pasta_enviados'], boleto['nome'])
        shutil.move(caminho_absoluto, caminho_enviado)
        print(f"Boleto movido para a pasta 'enviados'.")

        print("Processo concluído. Fechando navegador em 10 segundos...")
        page.wait_for_timeout(10000)

if __name__ == "__main__":
    enviar_arquivo()
