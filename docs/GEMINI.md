# Visão Geral do Projeto

O **boletoBot** é um sistema de automação e integração de processos robóticos (RPA) projetado para orquestrar o ciclo de vida completo de faturas universitárias (boletos). 

**Objetivo do Sistema:** Automatizar a extração de dados financeiros de um portal educacional (UVV) e garantir a entrega pontual do documento de cobrança via WhatsApp, eliminando a intervenção humana no fluxo de contas a pagar.

**Problema Resolvido:** Mitiga o risco de inadimplência por esquecimento e reduz o atrito operacional de login, navegação, extração de PDF e envio manual mensal.

**Fluxo Macro:**
1. **Ingestão (Scraping):** Autenticação HTTP no portal, parsing do DOM para encontrar pendências financeiras e download do artefato (PDF).
2. **Staging:** Armazenamento local com nomenclatura padronizada para fácil parsing cronológico.
3. **Orquestração de Regras:** Avaliação de heurísticas de tempo (ex: enviar apenas se `vencimento <= 7 dias`).
4. **Delivery (RPA):** Injeção em uma sessão persistente do navegador para manipulação da interface do WhatsApp Web e envio do anexo.
5. **Arquivamento:** Rotação do arquivo para um diretório de estado final (enviados).

---

# Stack Tecnológica

O projeto utiliza um ecossistema focado em automação web em Python, priorizando a simplicidade de execução local:

- **Linguagem:** Python 3.x
- **Extração de Dados (Scraping):** `requests` (Gerenciamento de Sessão HTTP) + `beautifulsoup4` (DOM Parsing estrutural).
- **Automação de UI (RPA):** `playwright` (Controle de engine Chromium via CDP - Chrome DevTools Protocol).
- **Gerenciamento de Configuração:** `python-dotenv` para injeção de dependências de ambiente.
- **Persistência de Sessão:** Sistema de arquivos local (`/auth` para o profile do Chromium).

---

# Arquitetura do Sistema

A arquitetura segue um modelo **Desacoplado Baseado em Arquivos (File-Based Decoupled Architecture)**. 
O sistema é dividido em dois processos estritamente separados que se comunicam assincronamente através do sistema de arquivos (Pasta `boletos/`).

1. **Extraction Engine (`baixar_boletos.py`):** Atua na camada de rede. É um cliente HTTP "burro" que mantém cookies de sessão em memória, forja requisições POST para autenticação e mapeia a tabela HTML de extrato financeiro para objetos de domínio implícitos. Não tem conhecimento de como o documento será entregue.
2. **Delivery Engine (`enviar_boletos.py`):** Atua na camada de apresentação/UI. Age como um *Stateful Bot*, levantando uma instância isolada do Chromium com um contexto de usuário persistente (evitando re-autenticação via QR Code). Consome a pasta de staging, aplica as regras de negócio de tempo e manipula o DOM do WhatsApp Web.

**Vantagem do Padrão:** Alta resiliência. Se o WhatsApp Web mudar seu DOM e quebrar o script de envio, a extração continua funcionando e populando o diretório de staging. Se o portal do aluno ficar offline, o script de envio ainda consegue despachar os boletos previamente cacheados.

---

# Estrutura de Pastas

A taxonomia de diretórios define o estado da aplicação:

- `/boletos/` - **(Staging Area):** Diretório transacional. Arquivos aqui são considerados "Pendentes de Processamento". A nomenclatura atua como metadado (`YYYY-MM-DD_parcela-X.pdf`).
- `/boletos/enviados/` - **(Archive/Dead-Letter):** Diretório de estado final. Arquivos processados com sucesso são movidos para cá para evitar duplicidade de execução (*idempotência no nível de arquivo*).
- `/auth/` - **(State Persistence):** Armazena o *User Data Directory* do Chromium. Contém IndexedDB, LocalStorage e Cookies do WhatsApp Web. **Crítico: O estado da autenticação vive aqui.**
- `/venv/` - **(Isolation):** Virtual environment com as dependências do projeto.
- `/.env` - **(Secrets):** Configurações de runtime e credenciais.

---

# Fluxo da Automação

O pipeline de execução segue este passo a passo técnico:

### Fase 1: Ingestão (`baixar_boletos.py`)
1. Instancia um `requests.Session()` para rastreamento automático de cookies (ex: `ASP.NET_SessionId`).
2. Dispara POST payload para `/Login` com credenciais do `.env`.
3. Navega para `/Aluno/Extrato` e converte o payload HTML usando `BeautifulSoup`.
4. Itera sobre as tags `<tr>` (linhas da tabela financeira). Valida integridade do array de colunas (`len(cols) < 9`).
5. Avalia regra de negócio: Se `status != 'aberto'`, ignora.
6. Extrai URL do hiperlink e normaliza a string de data (DD/MM/YYYY -> YYYY-MM-DD) para facilitar *sorting* léxico no OS.
7. Verifica existência do arquivo. Se não existe, realiza I/O binário (`wb`) para o diretório `/boletos/`.

### Fase 2: Delivery (`enviar_boletos.py`)
1. Analisa a pasta base. Organiza o array de strings alfabeticamente (que, devido à formatação ISO date no nome, resulta em ordenação cronológica do vencimento mais próximo).
2. Calcula o delta de tempo (`vencimento - datetime.now()`). Se `delta > 7 dias`, o processo sofre *early exit*.
3. Levanta o Chromium via Playwright com `launch_persistent_context`, anexando o diretório `/auth` e mascarando a automação (`--disable-blink-features=AutomationControlled`).
4. Navega via *Deep Link* URL (`https://web.whatsapp.com/send?phone=...`).
5. **Polling no DOM:** Aguarda o seletor da caixa de texto do chat (`div[contenteditable="true"]`).
6. Injeta cliques sequenciais nos seletores de anexo e input de arquivo (`expect_file_chooser`).
7. Realiza o upload via API do Playwright e aguarda o botão de *Send* (`span[data-testid="wds-ic-send-filled"]`).
8. Rotação de Arquivo: Aplica `shutil.move` para mover o arquivo de staging para `/enviados/`.
9. Teardown com delay arbitrário para garantir o término do tráfego WebSocket do WhatsApp antes de destruir a engine.

---

# Componentes Principais

- **`baixar_boletos.py`**: Script *Stateless* de scraping. Acoplado à estrutura DOM do sistema educacional alvo. Pode rodar em background 100% *headless*.
- **`enviar_boletos.py`**: Script *Stateful* de RPA. Acoplado à estrutura DOM do WhatsApp Web. É o gargalo de estabilidade do sistema devido a dependência de seletores CSS dinâmicos.
- **Scripts de Teste (`test.py`, `test0.py`)**: *Spikes* arquiteturais e sandboxes. Utilizados para debugar timeouts e capturar os seletores corretos do WhatsApp Web sem engatilhar o fluxo principal de envio.

---

# Dependências Críticas

1. **`playwright` + DOM do WhatsApp Web:**
   - **Risco (Alto):** A Meta/WhatsApp altera frequentemente os atributos das tags (classes, data-testids) em atualizações de web app. O fluxo de upload é extremamente suscetível a quebras.
   - **Substituição ideal:** Migração para uma API REST não-oficial de WhatsApp baseada em sockets (ex: *Baileys*, *Evolution API*, *WPPConnect*) para contornar a dependência de interface gráfica.
2. **`requests` + Portal Educacional:**
   - **Risco (Médio):** Proteções de WAF (Web Application Firewall) ou Cloudflare podem bloquear o request caso identifiquem a ausência de headers comuns de browser no futuro.
   - **Substituição:** Substituir `requests` por instâncias *headless* do próprio Playwright se o portal implementar CSRF tokens complexos ou captchas.

---

# Sistema de Configuração

Gerenciado via arquivo de ambiente `.env`, carregado pelo `dotenv`. Padrão Singleton implícito pelo sistema operacional.

- `MATRICULA` / `PASSWORD`: Autenticação do sistema de origem. *Security Risk: Plain text*.
- `CONTATO`: Chave de roteamento para o destino (Formato E.164 sem o +).
- `ARQUIVO`: Caminho absoluto do diretório de *Staging*. Ponto de acoplamento entre os dois módulos independentes.

---

# Ferramentas de Usuário (Layman-Friendly)

Para facilitar o uso por pessoas não-técnicas, o projeto inclui ferramentas de interface gráfica e automação de sistema:

1. **`configurator.py` (Configurador GUI)**:
   - Interface moderna (CustomTkinter) para gerenciar o arquivo `.env`.
   - Permite salvar credenciais e caminhos sem editar arquivos de texto.
   - Botão para **Vincular WhatsApp**, que abre o navegador para o scan do QR Code inicial.
   - Botão para **Agendar no Windows**, que automatiza a criação da tarefa diária.

2. **`scripts/setup_scheduler.ps1` (Automação de Agendamento)**:
   - Script PowerShell que cria uma Tarefa Agendada no Windows.
   - Configurado para rodar diariamente às 10:00 AM.
   - Executa sequencialmente `baixar_boletos.py` e `enviar_boletos.py` usando o interpretador do ambiente virtual.

3. **`run_configurator.bat`**:
   - Atalho simples para abrir a interface de configuração sem usar o terminal.

---

# Tratamento de Erros

O tratamento de erros atual é **Frágil e Otimista**:

- **Extração:** Não possui retentativas (Retries/Backoff Exponencial) caso a requisição HTTP falhe (HTTP 500, Timeout). Apenas falha silenciosamente e ignora o arquivo.
- **RPA (WhatsApp):** Utiliza *Timeouts* engessados (`wait_for_timeout` e `wait_for_selector`). Se a internet estiver lenta e o seletor demorar mais de 60s, a aplicação encerra. 
- **Recuperação:** Devido ao *shutil.move* ser executado apenas no final, o sistema é parcialmente *idempotente*. Uma falha no meio do envio significa que o arquivo permanecerá no staging para ser tentado novamente na próxima execução.

---

# Observabilidade

- Nível básico baseado em I/O padrão (`print`).
- **Gargalo:** Ausência de `logger` estruturado. Falhas em automações rodando via `cron` ou `Task Scheduler` ficarão invisíveis (Silenced Failures) se a saída do console não for redirecionada.
- Não existem gatilhos de alerta de falha (Ex: um ping no próprio WhatsApp avisando que o bot falhou em rodar).

---

# Segurança

- **Credenciais em Plaintext:** O arquivo `.env` carrega senhas puras na máquina local.
- **Sessão Sequestrável (Session Hijacking):** A pasta `/auth` contém a sessão ativa do WhatsApp Web. Qualquer indivíduo ou malware com acesso a este diretório pode espelhar a sessão do usuário em outro Chromium sem necessidade do aparelho celular.
- O parâmetro `user-agent` e a flag `--disable-blink-features=AutomationControlled` são usados para mitigar heurísticas básicas de detecção de bots por parte da Meta.

---

# Performance

- **Concorrência:** 100% Síncrono (Single-threaded). Para o escopo atual (1 boleto por mês), é adequado e evita complexidade de `asyncio` e race conditions.
- **Gargalos:** Inicialização a frio do Playwright (`launch_persistent_context`) e os *Hard Delays* (`page.wait_for_timeout(3000)`) usados para aguardar animações de UI.
- O parsing do DOM HTML com BeautifulSoup é O(N) na tabela e extremamente rápido (< 100ms).

---

# Débito Técnico

1. **Acoplamento a Seletores CSS Dinâmicos:** `span[data-testid="wds-ic-send-filled"]` e `button[aria-label="Document"]` podem quebrar a qualquer momento.
2. **Hardcoded Limits:** O tempo limite de "7 dias" antes do vencimento está estático no código, reduzindo a flexibilidade.
3. **Tratamento de Exceções Genéricas:** Uso de `except Exception:` sem rastrear o stack trace (`traceback`) mascara o motivo real da falha.
4. **Falta de Abstração:** Não há isolamento entre regras de negócio e manipulação de infraestrutura (requests/playwright estão misturados com a lógica de negócio).

---

# Roadmap Futuro

1. **Refatoração para Padrões de Projeto:** Implementar `Page Object Model (POM)` para o WhatsApp Web, encapsulando os seletores em uma classe separada.
2. **Resiliência:** Adicionar a biblioteca `tenacity` para realizar *retries* automáticos tanto na camada HTTP quanto no Playwright.
3. **Logging Estruturado:** Migrar os `prints` para a biblioteca nativa `logging`, salvando os eventos em um arquivo `bot.log` com níveis (`INFO`, `ERROR`, `DEBUG`).
4. **Alerta de Falha Crítica:** Se o boleto estiver vencendo em 1 dia e o sistema não conseguir enviar (ex: falha de login), notificar o admin via Telegram.
5. **Modernização Arquitetural:** Abandonar Playwright para envio e utilizar a API Graph da Meta ou instâncias headless em Node.js (baileys) para se comunicar diretamente via WebSocket com os servidores do WhatsApp, reduzindo drasticamente uso de RAM e instabilidade.

---

# Regras para Futuros Agentes de IA

Ao modificar este projeto, siga ESTRITAMENTE as regras abaixo:

1. **NÃO MUDE A ESTRUTURA FILE-BASED:** A comunicação entre `baixar` e `enviar` DEVE continuar sendo através do sistema de arquivos (`/boletos`). Não tente uni-los em um mega-script para evitar Single Point of Failure (SPOF).
2. **CUIDADO EXTREMO COM `/auth`:** Nunca versione este diretório. Se o Playwright parar de logar, recomende ao usuário apagar `/auth`, rodar uma vez em modo não-headless (`headless=False`) e refazer o scan do QR Code.
3. **MANIPULAÇÃO DO DOM DO WHATSAPP:** Antes de sugerir atualizações de seletores (`enviar_boletos.py:80-95`), assuma que o DOM mudou. Utilize estratégias de *locator* mais robustas (ex: `get_by_role`, ou xPaths textuais) ao invés de classes engessadas ou aria-labels não traduzidos, e trate as exceções explicitamente.
4. **NOMENCLATURA DE BOLETOS:** O parse (`enviar_boletos.py:31-32`) confia no formato `YYYY-MM-DD`. Se alterar a formatação no `baixar_boletos.py:64`, lembre-se de atualizar ambos.
5. **TIMEOUTS SÃO NECESSÁRIOS:** Não substitua `wait_for_timeout` completamente por waits inteligentes (`wait_for_selector`) na área do WhatsApp. A interface possui animações no DOM (fade in/out do menu de anexos) que precisam de hard delays temporais para não engolirem cliques muito rápidos do bot.

---

# Guia de Execução

### Setup de Ambiente (Local)
1. Certifique-se de ter o Python >= 3.10 instalado.
2. Execute o arquivo `run_configurator.bat`.
3. Na janela que abrir:
   - Preencha sua **Matrícula** e **Senha**.
   - Insira o **Número de Telefone** (ex: 5527999999999).
   - Clique em **Salvar Configuração**.
4. Clique em **Vincular WhatsApp** e escaneie o QR Code no navegador que abrir.
5. Clique em **Agendar no Windows** para deixar o bot rodando sozinho todos os dias.

### Execução Manual
- Se precisar rodar na hora, você pode usar os botões do configurador ou rodar via terminal:
  - `python baixar_boletos.py`
  - `python enviar_boletos.py` (use `--visible` se quiser ver o navegador).
