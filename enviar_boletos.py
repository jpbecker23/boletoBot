import sys
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
            print(f"Aguardando: {boleto_selecionado} vence em {dias_para_vencimento} dias. (Limite para envio: 30 dias)")
            return None

    except Exception as e:
        print(f"Aviso: Formato de nome inesperado em {boleto_selecionado}. Erro: {e}")
        print("Enviando por segurança (fallback)...")

    return {
        "nome": boleto_selecionado,
        "caminho": os.path.abspath(os.path.join(CAMINHO_ARQUIVO, boleto_selecionado)),
        "pasta_enviados": pasta_enviados
    }

def enviar_arquivo(headless=True):
    boleto = selecionar_boleto()
    if not boleto:
        # Se estivermos em modo visível, talvez o usuário só queira logar
        if not headless:
             with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    USER_DATA_DIR,
                    headless=False,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = context.pages[0]
                print("Abrindo WhatsApp para autenticação...")
                page.goto("https://web.whatsapp.com/")
                print("Aguarde o carregamento e faça o login se necessário.")
                print("O navegador fechará em 2 minutos ou quando você fechar a janela.")
                page.wait_for_timeout(120000)
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=headless,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.pages[0]

        print(f"Abrindo conversa com {NUMERO_CONTATO}...")
        page.goto(f"https://web.whatsapp.com/send?phone={NUMERO_CONTATO}")

        try:
            print("Aguardando carregamento da interface do WhatsApp...")
            # Aguarda pela caixa de texto (usuário já logado) OU pelo Canvas do QR Code (usuário deslogado)
            page.wait_for_selector('div[contenteditable="true"], canvas', timeout=60000)
            
            # Se encontrar o canvas do QR code na tela
            canvas_locator = page.locator('canvas')
            if canvas_locator.count() > 0:
                print("\n⚠️  ATENÇÃO: Autenticação necessária! Gerando QR Code...")
                qr_path = os.path.join(USER_DATA_DIR, 'qrcode.png')
                
                # Tira print apenas do QR Code e salva na pasta compartilhada do Docker
                canvas_locator.first.screenshot(path=qr_path)
                
                print(f"⚠️  ABRA O ARQUIVO NO SEU PC: {qr_path}")
                print("⚠️  Escaneie o QR Code com seu celular para continuar.")
                print("Aguardando você escanear o QR Code (Tempo limite: 60 segundos)...")
                
                # Aguarda o usuário escanear e o campo de texto do chat aparecer
                page.wait_for_selector('div[contenteditable="true"]', timeout=60000)
                print("✅ Autenticação realizada com sucesso!")
                
                # Limpa a imagem do QR code que foi gerada
                if os.path.exists(qr_path):
                    os.remove(qr_path)
                    
            page.wait_for_timeout(3000)
            print("Interface carregada!")
        except Exception as e:
            print(f"Erro: O login não foi detectado, você não escaneou o QR code a tempo, ou a página demorou demais. Detalhe: {e}")
            debug_path = os.path.join(CAMINHO_ARQUIVO, 'debug_whatsapp.png')
            page.screenshot(path=debug_path, full_page=True)
            print(f"📸 Para entender o que deu errado, abra a imagem: ./boletos/debug_whatsapp.png")
            return

        print(f"Preparando envio do boleto: {boleto['nome']}")
        caminho_absoluto = boleto['caminho']

        print("Abrindo menu de anexos...")
        page.locator('button[aria-label="Attach"], span[data-icon="plus-rounded"]').first.click()
        page.wait_for_timeout(1000)

        print("Clicando no botão de Documento...")
        with page.expect_file_chooser() as fc_info:
            # WhatsApp muda constantemente as labels e varia entre Inglês e Português
            page.locator('button[aria-label="Document"], button[aria-label="Documento"]').first.click()

        file_chooser = fc_info.value
        file_chooser.set_files(caminho_absoluto)

        print("Aguardando a tela de prévia do anexo...")
        # Espera a animação do preview do PDF carregar
        page.wait_for_timeout(3000)
        
        print("Clicando no botão de envio...")
        try:
            # Na interface nova do WhatsApp, esse botão deixou de ser um <button> e virou um <div>!
            seletores = 'div[role="button"][aria-label="Enviar"], div[role="button"][aria-label="Send"], span[data-icon="send"]'
            page.locator(seletores).locator('visible=true').first.click(timeout=10000)
        except Exception:
            print("Botão visual não localizado. Usando método de segurança (Tecla Enter)...")
            # Failsafe supremo: Na tela de prévia, a tecla Enter envia o documento independentemente de como o botão é feito
            page.keyboard.press("Enter")
        
        # Um pequeno wait para garantir que o upload do arquivo terminou no servidor deles
        page.wait_for_timeout(3000)

        print("Arquivo enviado com sucesso!")

        # Arquivamento
        caminho_enviado = os.path.join(boleto['pasta_enviados'], boleto['nome'])
        shutil.move(caminho_absoluto, caminho_enviado)
        print(f"Boleto movido para a pasta 'enviados'.")

        print("Processo concluído. Fechando navegador em 5 segundos...")
        page.wait_for_timeout(5000)

if __name__ == "__main__":
    is_headless = "--visible" not in sys.argv
    enviar_arquivo(headless=is_headless)
