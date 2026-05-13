import os
import sys
import time
import logging
from baixar_boletos import executar_download
from enviar_boletos import enviar_arquivo

# Configuração básica de log para substituir prints isolados
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def rotina_principal():
    logging.info("=== Iniciando rotina do boletoBot ===")
    
    caminho_boletos = os.getenv("ARQUIVO", "boletos")
    boletos_pendentes = [f for f in os.listdir(caminho_boletos) if f.endswith('.pdf')] if os.path.exists(caminho_boletos) else []
    
    if boletos_pendentes:
        logging.info(f"Etapa 1: Boleto pendente já encontrado na pasta ('{boletos_pendentes[0]}'). Ignorando navegação ao portal UVV.")
    else:
        logging.info("Etapa 1: Baixando boletos no portal da instituição...")
        try:
            executar_download()
        except Exception as e:
            logging.error(f"Falha ao baixar boletos: {e}")
            return False
        
    logging.info("Etapa 2: Enviando via WhatsApp Web...")
    try:
        enviar_arquivo(headless=True)
    except Exception as e:
        logging.error(f"Falha ao comunicar com o WhatsApp: {e}")
        return False
        
    logging.info("=== Rotina finalizada com sucesso! ===")
    return True

def main():
    intervalo_str = os.getenv("INTERVALO_HORAS")
    
    # Se a variável existir e for um número maior que zero, entra em modo loop (contínuo)
    if intervalo_str and intervalo_str.isdigit() and int(intervalo_str) > 0:
        horas = int(intervalo_str)
        logging.info(f"MODO CONTÍNUO: O bot rodará em loop a cada {horas} hora(s). Para desligar, pare o container.")
        while True:
            rotina_principal()
            logging.info(f"Dormindo por {horas} hora(s)... O bot acordará no próximo ciclo.")
            time.sleep(horas * 3600) # 3600 segundos = 1 hora
    else:
        # Execução padrão (róda apenas uma vez e se desliga)
        logging.info("MODO ÚNICO: O bot rodará uma vez e o container será desligado.")
        sucesso = rotina_principal()
        if not sucesso:
            sys.exit(1)

if __name__ == "__main__":
    main()
