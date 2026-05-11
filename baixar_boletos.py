import os
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://aluno.uvv.br"

LOGIN_URL = f"{BASE_URL}/Login"
BOLETOS_URL = f"{BASE_URL}/Aluno/Extrato"

session = requests.Session()

payload = {
    "Matricula": os.getenv("MATRICULA"),
    "Password": os.getenv("PASSWORD")
}

login_response = session.post(LOGIN_URL, data=payload)

response = session.get(BOLETOS_URL)

soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a", title="Imprimir Boleto")

for link in links:
    href = link["href"]

    boleto_url = BASE_URL + href

    print(boleto_url)

# print(login_response.url)
# print(login_response.status_code)

boleto_response = session.get(boleto_url)

print(boleto_response.headers["Content-Type"])