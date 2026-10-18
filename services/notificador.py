from typing import Protocol


class NotificacaoError(Exception):
    """Falha ao enviar o boleto pelo canal de notificação."""


class Notificador(Protocol):
    """Canal de envio do boleto (ex.: WhatsApp via WAHA)."""

    def esta_conectado(self) -> bool:
        """Retorna True se o canal está pronto para enviar."""
        ...

    def enviar_documento(self, caminho_pdf: str, legenda: str) -> None:
        """Envia o PDF ao destinatário. Levanta NotificacaoError em caso de falha."""
        ...
