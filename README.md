
# boletoBot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![GitHub last commit](https://img.shields.io/github/last-commit/jpbecker23/boletoBot)
![GitHub repo size](https://img.shields.io/github/repo-size/jpbecker23/boletoBot)
![Status](https://img.shields.io/badge/Status-v2%20in%20development-orange)

**boletoBot** is a personal project built to stop forgetting to pay university tuition on time. It logs into the UVV student portal, downloads the open *boleto* (Brazilian payment slip) and sends it via WhatsApp one week before the due date.

> [!IMPORTANT]
> **Just want to use the bot on Windows, with no setup?** Download the stable version from [**Releases**](https://github.com/jpbecker23/boletoBot/releases/tag/v1.0.0). Usage instructions are in the release notes.
>
> The `main` branch contains **v2**, still in development: a server version that runs 24/7 with Docker, without depending on your computer being on. The v1 code (Playwright + WhatsApp Web) is preserved in the [`legacy/v1`](https://github.com/jpbecker23/boletoBot/tree/legacy/v1) branch.

# How It Works

The project runs in two containers: the **bot** (this code) and [**WAHA**](https://waha.devlike.pro), an HTTP API that keeps a WhatsApp session connected 24/7, as a linked device.

On each run, `main.py`:

1. **Checks the WhatsApp connection**, even when there is nothing to send, to detect a disconnected session early.
2. **Downloads the boletos (`portal_service.py`):** authenticates on the UVV portal via HTTP, reads the statement and downloads the PDFs of installments with status `"aberto"` (open) to `boletos/`, named `YYYY-MM-DD_parcela-X.pdf`.
3. **Selects (`boleto_service.py`)** the boleto due in **7 days or less**.
4. **Sends (`waha_notificador.py`)** the PDF via WhatsApp through WAHA.
5. **Archives** the PDF to `boletos/enviados/` only after it is sent, preventing duplicates. If sending fails, the boleto stays pending.

In Docker, the bot runs in a loop every 24 hours. After a failed run (WAHA still starting, portal down, etc.), it retries in 60 minutes.

# Stack

- **Python 3.14** with `requests` and `beautifulsoup4` for the portal.
- **WAHA** (GOWS engine, no browser) for WhatsApp.
- **Docker Compose** to run both services together.
- **pytest** for tests.

# Project Structure

```text
boletoBot/
├── core/
│   ├── config.py             # Reads .env and defines constants
│   └── logger.py             # Logs to console and logs/boletobot.log (rotating)
├── services/
│   ├── portal_service.py     # UVV portal login and boleto download
│   ├── boleto_service.py     # 7-day rule and archiving
│   ├── notificador.py        # Delivery channel interface
│   └── waha_notificador.py   # WhatsApp delivery via WAHA
├── tests/                    # Unit tests
├── main.py                   # Routine entry point
├── Dockerfile                # Bot image
├── docker-compose.yaml       # Bot + WAHA
├── boletos/                  # Generated: pending PDFs and enviados/
└── logs/                     # Generated: run history
```

# Configuration

Create `.env` from `.env.example`. It must never be committed.

| Variable | Required | Description |
|---|---|---|
| `MATRICULA` / `PASSWORD` | Yes | UVV student portal credentials |
| `CONTATO` | Yes | Number that receives the boleto, with country and area code (e.g. `5527999999999`) |
| `WAHA_API_KEY` | Yes | Key the bot uses to access WAHA (and that WAHA requires) |
| `WAHA_DASHBOARD_USERNAME` / `WAHA_DASHBOARD_PASSWORD` | Yes (Docker) | WAHA dashboard login |
| `WAHA_URL` | No | WAHA address. Default: `http://localhost:3000` |
| `WAHA_SESSAO` | No | WAHA session name. Default: `default` |
| `WAHA_IMAGE_TAG` | No | WAHA image tag. Default: `gows-2026.9.2` (amd64). On ARM servers, use `gows-arm-2026.9.2` |
| `ARQUIVO` | No | Boletos folder. Default: `boletos/` inside the project |
| `INTERVALO_HORAS` | No | Continuous mode, running every X hours. If omitted, runs once and exits |

In Docker, `docker-compose.yaml` overrides `WAHA_URL` (`http://waha:3000`, the service name on the internal network), `ARQUIVO` (`/app/boletos`) and `INTERVALO_HORAS` (`24`), and sets `TZ=America/Sao_Paulo`.

To generate a strong `WAHA_API_KEY` and password:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

# Running with Docker

Requires Docker with the Compose plugin.

**1. Start the services**
```bash
docker compose up -d --build
```

**2. Link WhatsApp**

Open `http://localhost:3000/dashboard`, log in with the dashboard credentials, create a session with the same name as `WAHA_SESSAO` (`default` if not set) and scan the QR code with your phone under **WhatsApp → Linked devices**. The session is stored in the `waha_sessions` volume and survives container recreation.

**3. Test a run**
```bash
docker compose run --rm -e INTERVALO_HORAS=0 bot
```

**Useful commands**
```bash
docker compose logs -f bot   # follow the bot logs
docker compose ps            # container status
docker compose down          # stop the containers (the session stays in the volume)
```

# Development (without Docker)

Requires Python 3.10+ and a reachable WAHA. The easiest way is to start only WAHA: `docker compose up -d waha`.

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1  |  Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt

python main.py       # run the routine once
python -m pytest     # run the tests
```

# Security

- **`.env` holds your portal password and the API key:** never commit it. On servers, restrict its permissions (`chmod 600 .env`).
- **The WhatsApp session is equivalent to your logged-in WhatsApp.** It lives only in the `waha_sessions` Docker volume, outside the project and the repository.
- **WAHA is only exposed on `127.0.0.1`.** On a server, nobody on the internet can reach the dashboard. To access it remotely, use an SSH tunnel:
  ```bash
  ssh -L 3000:localhost:3000 user@server
  ```
- WAHA receives only the variables it needs, not the whole `.env`.

# Contributing

This project is public to help other students with the same problem. To contribute a feature or fix, open an Issue describing the idea and feel free to open a Pull Request.
