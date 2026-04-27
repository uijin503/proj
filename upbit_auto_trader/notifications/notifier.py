import logging

LOGGER = logging.getLogger(__name__)


class Notifier:
    def send_discord(self, message: str) -> None:
        LOGGER.info("[Discord] %s", message)

    def send_telegram(self, message: str) -> None:
        LOGGER.info("[Telegram] %s", message)
