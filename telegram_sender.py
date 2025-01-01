import os
import sqlite3
import logging
from pytgbot import Bot

# Logger opsætning
LOG_FILE = "telegram_sender.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_sender")

DB_PATH = "messages.db"

class TelegramSender:
    def __init__(self, api_key=None, chat_id=None):
        self.api_key = api_key or os.getenv("TELEGRAM_API")
        self.chat_id = chat_id or os.getenv("TELEGRAM_REC")
        if not self.api_key or not self.chat_id:
            raise ValueError("Telegram API-nøgle og Chat ID skal være indstillet.")
        self.bot = Bot(self.api_key)

    def send_message(self, message):
        try:
            self.bot.send_message(self.chat_id, message)
            logging.info("Besked sendt til Telegram.")
            return True
        except Exception as e:
            logging.error(f"Fejl under afsendelse af besked: {e}")
            return False

def process_unsent_messages():
    """
    Finder og sender beskeder, der ikke tidligere er sendt til Telegram.
    """
    sender = TelegramSender()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, raw_message FROM messages
            WHERE sent_to_telegram = 0
        """)
        unsent_messages = cursor.fetchall()

        for message_id, raw_message in unsent_messages:
            if sender.send_message(raw_message):
                cursor.execute("""
                    UPDATE messages
                    SET sent_to_telegram = 1
                    WHERE id = ?
                """, (message_id,))
        conn.commit()

if __name__ == "__main__":
    process_unsent_messages()