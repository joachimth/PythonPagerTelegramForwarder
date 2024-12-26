import sqlite3
import logging
import json
from telegram_sender import TelegramSender

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

DB_PATH = "messages.db"

def process_and_send_messages():
    """
    Henter parsed beskeder fra databasen og sender dem til Telegram.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, parsed_fields FROM messages
                WHERE parsed_fields IS NOT NULL
                ORDER BY id DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()

            if not rows:
                logger.info("Ingen parsed beskeder til afsendelse.")
                return

            telegram_sender = TelegramSender()

            for message_id, parsed_fields in rows:
                parsed_message = json.loads(parsed_fields)
                formatted_message = "\n".join(f"{k}: {v}" for k, v in parsed_message.items())
                logger.info(f"Sender besked ID {message_id} til Telegram: {formatted_message}")
                telegram_sender.send_message(formatted_message)

    except sqlite3.Error as e:
        logger.error(f"Databasefejl under behandling af beskeder: {e}")
    except Exception as e:
        logger.error(f"Fejl under afsendelse af beskeder: {e}")

if __name__ == "__main__":
    logger.info("Starter app.py")
    try:
        process_and_send_messages()
    except Exception as e:
        logger.error(f"Kritisk fejl i app.py: {e}")