
# boletoBot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![GitHub last commit](https://img.shields.io/github/last-commit/jpbecker23/boletoBot)
![GitHub repo size](https://img.shields.io/github/repo-size/jpbecker23/boletoBot)
![Status](https://img.shields.io/badge/Status-v2%20em%20desenvolvimento-orange)

O **boletoBot** é um projeto pessoal criado para resolver o problema de esquecer de pagar mensalidades na data certa. Ele acessa o portal do aluno UVV, baixa o boleto em aberto e o envia pelo WhatsApp uma semana antes do vencimento.

> [!IMPORTANT]
> **Quer apenas usar o bot no Windows, sem configurar nada?** Baixe a versão estável na aba [**Releases**](https://github.com/jpbecker23/boletoBot/releases/tag/v1.0.0). As instruções de uso estão na própria release.
>
> A branch `main` contém a **v2**, ainda em desenvolvimento: uma versão para servidor, que roda 24h com Docker, sem depender do seu computador ligado. O código da v1 (Playwright + WhatsApp Web) está preservado na branch [`legacy/v1`](https://github.com/jpbecker23/boletoBot/tree/legacy/v1).

# Como Funciona

O projeto roda em dois containers: o **bot** (este código) e o [**WAHA**](https://waha.devlike.pro), uma API HTTP que mantém uma sessão do WhatsApp conectada 24h, como um aparelho vinculado.

A cada execução, o `main.py`:

1. **Verifica a conexão** com o WhatsApp, mesmo quando não há boleto a enviar, para detectar cedo uma sessão desconectada.
2. **Baixa os boletos (`portal_service.py`):** autentica no portal UVV via HTTP, lê o extrato e baixa os PDFs das parcelas com status `"aberto"` para `boletos/`, no formato `AAAA-MM-DD_parcela-X.pdf`.
3. **Seleciona (`boleto_service.py`)** o boleto cujo vencimento falta **7 dias ou menos**.
4. **Envia (`waha_notificador.py`)** o PDF pelo WhatsApp através do WAHA.
5. **Arquiva** o PDF em `boletos/enviados/` somente após o envio, evitando envios duplicados. Se o envio falhar, o boleto continua pendente.

No Docker, o bot roda em loop a cada 24 horas. Após uma execução com erro (WAHA ainda iniciando, portal fora do ar etc.), ele tenta novamente em 60 minutos.

# Stack

- **Python 3.14** com `requests` e `beautifulsoup4` para o portal.
- **WAHA** (motor GOWS, sem navegador) para o WhatsApp.
- **Docker Compose** para executar os dois serviços juntos.
- **pytest** para os testes.

# Estrutura do Projeto

```text
boletoBot/
├── core/
│   ├── config.py             # Leitura do .env e constantes
│   └── logger.py             # Logs no console e em logs/boletobot.log (com rotação)
├── services/
│   ├── portal_service.py     # Login no portal UVV e download dos boletos
│   ├── boleto_service.py     # Regra dos 7 dias e arquivamento
│   ├── notificador.py        # Interface do canal de envio
│   └── waha_notificador.py   # Envio pelo WhatsApp via WAHA
├── tests/                    # Testes unitários
├── main.py                   # Ponto de entrada da rotina
├── Dockerfile                # Imagem do bot
├── docker-compose.yaml       # Bot + WAHA
├── boletos/                  # Gerado: PDFs pendentes e enviados/
└── logs/                     # Gerado: histórico de execuções
```

# Configuração

Crie o `.env` a partir do `.env.example`. Ele nunca deve ser versionado.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `MATRICULA` / `PASSWORD` | Sim | Acesso ao portal do aluno UVV |
| `CONTATO` | Sim | Número que recebe o boleto, com DDI e DDD (ex.: `5527999999999`) |
| `WAHA_API_KEY` | Sim | Chave que o bot usa para acessar o WAHA (e que o WAHA exige) |
| `WAHA_DASHBOARD_USERNAME` / `WAHA_DASHBOARD_PASSWORD` | Sim (Docker) | Login do dashboard do WAHA |
| `WAHA_URL` | Não | Endereço do WAHA. Padrão: `http://localhost:3000` |
| `WAHA_SESSAO` | Não | Nome da sessão no WAHA. Padrão: `default` |
| `WAHA_IMAGE_TAG` | Não | Tag da imagem do WAHA. Padrão: `gows-2026.9.2` (amd64). Em servidores ARM, use `gows-arm-2026.9.2` |
| `ARQUIVO` | Não | Pasta dos boletos. Padrão: `boletos/` dentro do projeto |
| `INTERVALO_HORAS` | Não | Modo contínuo, rodando a cada X horas. Se omitido, roda uma vez e encerra |

No Docker, o `docker-compose.yaml` sobrescreve `WAHA_URL` (`http://waha:3000`, o nome do serviço na rede interna), `ARQUIVO` (`/app/boletos`), `INTERVALO_HORAS` (`24`) e define `TZ=America/Sao_Paulo`.

Para gerar uma `WAHA_API_KEY` e uma senha fortes:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> [!WARNING]
> Não use as credenciais de exemplo do quick start do WAHA: elas são públicas.

# Executando com Docker

Requer Docker com o plugin Compose.

**1. Suba os serviços**
```bash
docker compose up -d --build
```

**2. Vincule o WhatsApp**

Acesse `http://localhost:3000/dashboard`, faça login com as credenciais do dashboard, crie a sessão com o mesmo nome de `WAHA_SESSAO` (`default`, se não definida) e escaneie o QR Code pelo celular, em **WhatsApp → Aparelhos conectados**. A sessão fica salva no volume `waha_sessions` e sobrevive à recriação dos containers.

**3. Teste uma execução**
```bash
docker compose run --rm -e INTERVALO_HORAS=0 bot
```

**Comandos úteis**
```bash
docker compose logs -f bot   # acompanha os logs do bot
docker compose ps            # status dos containers
docker compose down          # derruba os containers (a sessão continua no volume)
```

# Desenvolvimento (sem Docker)

Requer Python 3.10+ e um WAHA acessível. O jeito mais simples é subir só ele: `docker compose up -d waha`.

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1  |  Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt

python main.py       # executa a rotina uma vez
python -m pytest     # executa os testes
```

# Segurança

- **O `.env` contém sua senha do portal e a API key:** nunca o versione. Em servidores, restrinja a permissão (`chmod 600 .env`).
- **A sessão do WhatsApp equivale ao seu WhatsApp logado.** Ela fica apenas no volume Docker `waha_sessions`, fora do projeto e do repositório.
- **O WAHA só é exposto em `127.0.0.1`.** Em um servidor, ninguém na internet alcança o dashboard. Para acessá-lo remotamente, use um túnel SSH:
  ```bash
  ssh -L 3000:localhost:3000 usuario@servidor
  ```
- O WAHA recebe apenas as variáveis de que precisa, e não o `.env` inteiro.

# Contribuição

Este projeto é público para ajudar outros alunos com a mesma dificuldade. Para contribuir com uma feature ou correção, abra uma Issue explicando a ideia e fique à vontade para abrir um Pull Request.
