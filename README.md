
# boletoBot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![GitHub last commit](https://img.shields.io/github/last-commit/jpbecker23/boletoBot)
![GitHub repo size](https://img.shields.io/github/repo-size/jpbecker23/boletoBot)
![Status](https://img.shields.io/badge/Status-v2%20em%20desenvolvimento-orange)

O **boletoBot** é um projeto pessoal criado para resolver o problema de esquecer de pagar mensalidades na data certa. Ele acessa o portal do aluno UVV, baixa o boleto em aberto e o envia pelo WhatsApp uma semana antes do vencimento.

> [!IMPORTANT]
> **Quer apenas usar o bot no Windows?** Baixe a versão estável na aba [**Releases**](https://github.com/jpbecker23/boletoBot/releases/tag/v1.0.0). As instruções de uso estão na própria release.
>
> A branch `main` contém a **v2**, ainda em desenvolvimento: uma versão para servidor, que roda 24h sem depender do seu computador ligado. O código da v1 (Playwright + WhatsApp Web) está preservado na branch [`legacy/v1`](https://github.com/jpbecker23/boletoBot/tree/legacy/v1).

# Como Funciona

A rotina é orquestrada pelo `main.py`. Em toda execução, ela verifica primeiro se a sessão do WhatsApp está conectada:

1. **Ingestão (`portal_service.py`):** autentica no portal UVV via HTTP, lê o extrato, identifica as parcelas com status `"aberto"` e baixa os PDFs para `boletos/`, no formato `AAAA-MM-DD_parcela-X.pdf`.
2. **Seleção (`boleto_service.py`):** escolhe o boleto cujo vencimento falta **7 dias ou menos**.
3. **Envio (`waha_notificador.py`):** envia o PDF pelo WhatsApp usando a API do [WAHA](https://waha.devlike.pro), que roda como um serviço separado.
4. **Arquivamento (`boleto_service.py`):** após o envio, o PDF é movido para `boletos/enviados/`, evitando envios duplicados.

Cada execução termina com código `0` (sucesso ou nada a fazer) ou `1` (falha). O histórico fica em `logs/boletobot.log`.

# Estrutura do Projeto

```text
boletoBot/
├── boletos/              # PDFs aguardando envio
│   └── enviados/         # PDFs já enviados
├── core/                 # Configuração (.env) e logger
├── services/
│   ├── boleto_service.py   # Seleção pela regra de vencimento e arquivamento
│   ├── portal_service.py   # Login no portal UVV e download dos boletos
│   ├── notificador.py      # Interface do canal de envio
│   └── waha_notificador.py # Envio pelo WhatsApp via WAHA
├── tests/                # Testes unitários
├── logs/                 # Gerado automaticamente: histórico de execuções
└── main.py               # Ponto de entrada da rotina
```

# Desenvolvimento

Requer Python 3.10 ou superior e uma instância do [WAHA](https://waha.devlike.pro) rodando, com a sessão do WhatsApp vinculada (pelo dashboard do WAHA).

```bash
git clone https://github.com/jpbecker23/boletoBot.git
cd boletoBot
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1  |  Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt
```

Crie o `.env` a partir do `.env.example`:

```env
MATRICULA=sua_matricula_aqui
PASSWORD=sua_senha_aqui

# Destinatário (DDI + DDD + número)
CONTATO=5511999999999

# API do WhatsApp (WAHA)
WAHA_URL=http://localhost:3000
WAHA_API_KEY=sua_api_key_do_waha

# (Opcional) Pasta dos boletos. Padrão: boletos/ dentro do projeto.
ARQUIVO=/app/boletos

# (Opcional) Mantém o bot em loop, rodando a cada X horas. Se omitido, roda uma vez e encerra.
INTERVALO_HORAS=24
```

```bash
python main.py       # executa a rotina
python -m pytest     # executa os testes
```

# Segurança

- O `.env` contém sua senha do portal: nunca o versione.
- Credenciais e sessões ficam apenas no ambiente de execução (máquina local ou servidor), nunca no repositório.

# Contribuição

Este projeto é público para ajudar outros alunos com a mesma dificuldade. Para contribuir com uma feature ou correção, abra uma Issue explicando a ideia e fique à vontade para abrir um Pull Request.
