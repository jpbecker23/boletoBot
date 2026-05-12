import os
import requests

from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

TARGET_DIR = "boletos"

def executar_download():
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    BASE_URL = "https://aluno.uvv.br"
    LOGIN_URL = f"{BASE_URL}/Login"
    BOLETOS_URL = f"{BASE_URL}/Aluno/Extrato"
    
    session = requests.Session()
    
    payload = {
        "Matricula": os.getenv("MATRICULA"),
        "Password": os.getenv("PASSWORD")
    }
    
    print("Realizando login no portal...")
    login_response = session.post(LOGIN_URL, data=payload)
    
    response = session.get(BOLETOS_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")
    
    count = 0
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 9:
            continue
        
        servico = cols[0].get_text(strip=True)
        parcela = cols[1].get_text(strip=True)
        vencimento = cols[6].get_text(strip=True)
        status = cols[7].get_text(strip=True)
        
        if status.lower() != "aberto":
            continue
            
        link = row.find("a", title="Imprimir Boleto")
        if not link:
            continue
            
        href = link["href"]
        boleto_url = BASE_URL + href
        boleto_response = session.get(boleto_url)
        
        dia, mes, ano = vencimento.split("/")
        vencimento_formatado = f"{ano}-{mes}-{dia}"
        filename = f"{vencimento_formatado}_parcela-{parcela}.pdf"
        savepath = os.path.join(TARGET_DIR, filename)
        
        if os.path.exists(savepath):
            print(f"{filename} já existe.")
            continue
            
        with open(savepath, "wb") as f:
            f.write(boleto_response.content)
        print(f"{filename} salvo com sucesso.")
        count += 1
    
    if count == 0:
        print("Nenhum novo boleto encontrado.")

if __name__ == "__main__":
    executar_download()

