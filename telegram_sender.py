import os
import logging
import sqlite3
from pytgbot import Bot
from time import sleep

# Logger opsætning
logging.basicConfig(
    filename="telegramsender.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "messages.db"

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
            logging.info(f"Sender besked til Chat ID: {self.chat_id}")
            self.bot.send_message(self.chat_id, message)
            logging.info("Besked sendt.")
        except Exception as e:
            logging.error(f"Fejl under afsendelse af besked: {e}")

    def process_unsent_messages(self):
        """
        Finder beskeder i databasen, som ikke er sendt, og sender dem.
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Find beskeder, der ikke er sendt
                cursor.execute("""
                    SELECT id, raw_message
                    FROM messages
                    WHERE sent_to_telegram IS NULL OR sent_to_telegram = 0
                """)
                unsent_messages = cursor.fetchall()

                if not unsent_messages:
                    logging.info("Ingen nye beskeder at sende.")
                    return

                logging.info(f"Fundet {len(unsent_messages)} beskeder, der skal sendes.")

                for message_id, raw_message in unsent_messages:
                    # Forsøg at sende beskeden
                    try:
                        self.send_message(raw_message)
                        # Marker beskeden som sendt
                        cursor.execute("""
                            UPDATE messages
                            SET sent_to_telegram = 1
                            WHERE id = ?
                        """, (message_id,))
                        conn.commit()
                        logging.info(f"Besked ID {message_id} markeret som sendt.")
                    except Exception as e:
                        logging.error(f"Fejl under afsendelse af besked ID {message_id}: {e}")
        except sqlite3.Error as e:
            logging.error(f"Fejl under kontrol af databasen: {e}")