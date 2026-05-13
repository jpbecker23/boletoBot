from core.config import USER_DATA_DIR, USER_AGENT, BROWSER_ARGS


def create_context(playwright, headless=True):
    """Cria e retorna um contexto persistente do Chromium com as configs padrão do projeto."""
    context = playwright.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=headless,
        user_agent=USER_AGENT,
        args=BROWSER_ARGS,
    )
    return context
