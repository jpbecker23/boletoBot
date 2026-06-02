
# boletoBot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?logo=playwright&logoColor=white)
![GitHub last commit](https://img.shields.io/github/last-commit/jpbecker23/boletoBot)
![GitHub repo size](https://img.shields.io/github/repo-size/jpbecker23/boletoBot)
![Status](https://img.shields.io/badge/Status-Ativo-success)


O **boletoBot** é um projeto pessoal criado para resolver o problema de esquecer de pagar mensalidades na data certa.

A automação atualmente acessa o portal do aluno, identifica se há faturas pendentes, faz o download do documento em PDF e o envia automaticamente para um contato do WhatsApp uma semana antes do vencimento. O objetivo é evitar o trabalho manual repetitivo de realizar login, navegar por menus, baixar o arquivo e encaminhar para si mesmo, e principalmente evitar que eu acabe esquecendo de pagar o boleto.


<p align="center">
  <img src="public/boletoBotInterface.png" width="300" alt="Interface do boletoBot">
</p>


# Configuração Rápida para Usuários não programadores

> [!IMPORTANT]
> Caso você prefira o modo tradicional com linha de comando, pode ignorar esta seção e [ir direto para o Setup](#setup).

Conversando com um amigo percebi que o estado antigo do projeto não era muito amigavável com pessoas que não são familiarizadas com programação. Por isso, atualizei o projeto para que ele seja de fácil uso para qualquer pessoa, implementei uma janela de configuração simples e direta para inserir as informações necessárias e agendar o bot.

1.  **Baixe o Executável:** Vá na aba [**Releases**](https://github.com/jpbecker23/boletoBot/releases) do repositório e baixe a versão mais recente do `BoletoBot.exe`.
2.  **Execute:** Coloque o arquivo em uma pasta de sua preferência e execute-o.
    >[!WARNING] Como o executável não é assinado digitalmente, o Windows pode mostrar um aviso de "O Windows protegeu o seu computador" ao abrir pela primeira vez. Basta clicar em "Mais informações" e depois em "Executar assim mesmo".

3.  **Configure:** Preencha seus dados de matrícula, senha e número do contato de quem vai recber o boleto na janela que abrirá.
4.  **Vincule o WhatsApp:** Clique em "Vincular WhatsApp" para abrir o navegador e ler o QR Code (isso só é feito uma vez).
5.  **Agende:** Clique em "Agendar no Windows" para que o robô trabalhe para você todos os dias às 10:00.

# Stack
- **Linguagem:** Python 3.x
- **Interface Gráfica (GUI):** `customtkinter` para uma experiência de configuração moderna e intuitiva.
- **Extração de Dados:** `requests` para sessão HTTP estática e `beautifulsoup4` para estruturação e extração das tabelas HTML.
- **Automação de UI (RPA):** `playwright` com Chromium para a operação da interface do WhatsApp Web.
- **Configuração:** `python-dotenv` para injeção limpa de credenciais locais.
- **Automação de Sistema:** PowerShell para integração e agendamento automático de tarefas no Windows.

# Estrutura do Projeto

O projeto foi refatorado para seguir o padrão **Page Object Model (POM)**, separando as responsabilidades de automação, regras de negócio, dados e visualização:

```text
boletoBot/
├── auth/                 # Pasta autogerada: armazena cookies e sessão ativa do WhatsApp
├── boletos/              # Staging area: PDFs aguardando regra de data para envio
│   └── enviados/         # Arquivo morto: faturas já processadas e enviadas
├── core/                 # Configurações do sistema, instanciador de browser e logger unificado
│   ├── browser.py
│   ├── config.py
│   └── logger.py
├── pages/                # Page Object Model do WhatsApp Web (seletores e ações de UI)
│   └── whatsapp_page.py
├── services/             # Regras de negócio da aplicação
│   ├── boleto_service.py # Listagem, seleção de boleto pela regra de vencimento e arquivamento
│   ├── portal_service.py # Login HTTP no portal UVV e ingestão de faturas abertas
│   └── whatsapp_service.py # Orquestração do fluxo de envio via WhatsApp Web
├── scripts/              # Scripts de suporte e automação (PowerShell para Windows Task Scheduler)
│   └── setup_scheduler.ps1
├── venv/                 # Ambiente virtual
├── .env                  # Variáveis de ambiente e segredos
├── configurator.py       # Interface gráfica de configuração (GUI)
├── run_configurator.bat  # Atalho amigável para lançar o configurador
├── main.py               # Orquestrador unificado de rotina principal
├── Dockerfile            # Arquivo de construção da imagem Linux com Playwright
└── docker-compose.yml    # Execução via contêiner mapeando as pastas necessárias
```

# Como Funciona

A rotina principal é orquestrada pelo arquivo `main.py` e executa as seguintes etapas:

1. **Varredura e Ingestão (`portal_service.py`):** Realiza uma requisição HTTP veloz usando `requests` e mantendo os cookies do servidor para autenticar no portal UVV. Lê o HTML do extrato, identifica as parcelas com status `"aberto"` e baixa o boleto em formato PDF para a pasta `boletos/`, salvando o arquivo no formato `AAAA-MM-DD_parcela-X.pdf`.
2. **Seleção Inteligente (`boleto_service.py`):** Analisa a pasta `boletos/`. Se houver algum boleto cuja data de vencimento falte **7 dias ou menos** (calculado de forma precisa com base na data do dia), ele é selecionado para envio.
3. **Entrega via WhatsApp Web (`whatsapp_service.py`):** Utiliza o `playwright` em modo headless (ou visível se configurado) com a sessão persistente de cookies salva em `auth/`. O robô abre a conversa com o contato definido, anexa o PDF do boleto e o envia.
4. **Arquivamento e Idempotência (`boleto_service.py`):** Assim que o envio é realizado com sucesso, o arquivo PDF correspondente é movido para a pasta `boletos/enviados/`, garantindo que não haja envios duplicados.

# Setup Tradicional (Windows/Linux sem Docker)

**1. Clone o repositório**
```bash
git clone https://github.com/jpbecker23/boletoBot.git
cd boletoBot
```

**2. Isole o ambiente**
```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
playwright install chromium
```

**4. Configure o `.env`**
O projeto conta com um arquivo `.env.example` que serve como modelo para a criação do arquivo `.env`. Preencha suas credenciais de acesso ao portal e o telefone para envio.

**5. Primeiro login do robô**
A primeira execução do WhatsApp exigirá o pareamento da sua conta (escaneamento do QR Code).
- **Via Interface Gráfica**: Execute `python configurator.py` e clique em **Vincular WhatsApp** para ler o QR Code de forma assistida.
- **Via Linha de Comando**: Você pode executar `python services/whatsapp_service.py --visible` para abrir o navegador de forma visível e realizar o login manual pelo QR Code.

Os dados da sua sessão de login serão gravados na pasta `auth/` para as próximas execuções.

**6. Automação e Agendamento**
- No Windows: Use a interface `configurator.py` para agendar via Task Scheduler ou execute o script `scripts/setup_scheduler.ps1` no PowerShell.
- No Linux: Use o `crontab` para agendar a execução do arquivo `main.py` diariamente.

---

# Setup Avançado com Docker 🐳 (Recomendado para Servidores/Linux)

A maneira mais resiliente de executar o robô no Linux (independente de versão do Python ou dependências de interface gráfica do Playwright) é através do Docker.

**1. Configure o `.env`**
Crie um arquivo `.env` na raiz (olhe o `.env.example`). Para rodar via Docker, deixe a variável `ARQUIVO` apontada nativamente para dentro do container:
```env
# O volume garantirá que essa pasta se reflita na sua raiz do host
ARQUIVO=/app/boletos
```

**2. Opcional: Modo de loop contínuo**
O bot pode rodar esporadicamente ou ficar em loop. Para ativar o loop no Docker, adicione ao seu `.env`:
```env
# Fará o bot dormir na memória e acordar sozinho a cada X horas
INTERVALO_HORAS=24
```

**3. Suba o container**
Na raiz do seu projeto, apenas execute:
```bash
docker compose up --build
```
*(Adicione a flag `-d` após as validações para rodar 100% solto em background e não travar o seu terminal)*

**4. Escaneando o QR Code pelo Docker:**
Na primeira execução, como será via terminal e invisível (headless), o container precisará do seu login no WhatsApp.
- O robô automaticamente perceberá que o WhatsApp exigiu login e vai gerar um **print da tela do QR Code**.
- Essa imagem surgirá magicamente no seu computador dentro da pasta `auth/qrcode.png`.
- Abra a imagem, escaneie com seu celular.
- O container registrará sucesso, limpará a imagem e seguirá o processo normalmente. Na próxima vez graças ao container guardar os cookies logados na pasta `auth`, não será mais cobrado escanear de novo.

# Configuração

O sistema depende de poucas, mas críticas, variáveis de ambiente configuradas no seu arquivo `.env`:

```env
# Acesso ao portal educacional
MATRICULA=sua_matricula_aqui
PASSWORD=sua_senha_aqui

# Destinatário do bot (Seu número com DDD, formato DDI+DDD)
CONTATO=5511999999999

# Caminho absoluto da pasta de transição no seu SO
ARQUIVO=C:\Caminhos\Absolutos\Ate\boletoBot\boletos
```
# Segurança

Este projeto foi construído assumindo execução estrita em localhost ou infraestrutura de uso particular e isolado:

- **Credenciais Locais:** Suas senhas da faculdade vivem abertamente no arquivo `.env`. Jamais exporte este dado.
- **Sessão do WhatsApp:** O diretório `auth/` contém sua sessão materializada. Ter esse arquivo em mãos equivale a ter o seu celular logado no WhatsApp Web. Não versione esta pasta e adicione-a imediatamente ao `.gitignore`.
- **Sensatez de Uso:** Esta automação mascara suas requisições baseada em flags padrões e destina-se puramente ao uso pessoal, não focando em contornar banimentos e tampouco desenhada para abusar do envio em massa.

# Contribuição

Irei tornar este projeto público a fim de ajudar outros alunos com a mesma dificuldade ou que apenas querem automatizar um processo chato e repetitivo. Caso você queira contribuir com o projeto, seja com uma feature nova ou uma fix abra uma Issue explicando, e sinta-se confortável para abrir um Pull Request. Melhorias arquiteturais também são muito bem-vindas. Agradeço a colaboração!
