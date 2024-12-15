import os
import logging
from pytgbot import Bot

# Logger opsætning
logger = logging.getLogger('telegram_sender')
logger.setLevel(logging.INFO)

class TelegramSender:
    """
    Klasse til at håndtere Telegram-beskeder.
    """
    def __init__(self, api_key=None, chat_id=None):
        self.api_key = api_key or os.getenv('TELEGRAM_API')
        self.chat_id = chat_id or os.getenv('TELEGRAM_REC')
        if not self.api_key or not self.chat_id:
            raise ValueError("Telegram API-nøgle og Chat ID skal være indstillet.")
        self.bot = Bot(self.api_key)

    def send_message(self, message):
        """
        Sender en besked til den specificerede Telegram-chat.
        """
        try:
            logger.info(f"Sender besked til Chat ID: {self.chat_id}")
            self.bot.send_message(self.chat_id, message)
            logger.info("Besked sendt.")
        except Exception as e:
            logger.error(f"Fejl under afsendelse af besked: {e}")