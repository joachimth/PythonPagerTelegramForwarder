import logging
from message_parser import process_unparsed_messages
from telegram_sender import TelegramSender
import sqlite3
import json

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

DB_PATH = "messages.db"

def fetch_parsed_messages(limit=10):
    """
    Henter de seneste parsed beskeder fra databasen.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT parsed_fields FROM messages
            WHERE parsed_fields IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
    return [json.loads(row[0]) for row in rows]

def send_messages_to_telegram():
    """
    Sender parsed beskeder til Telegram.
    """
    messages = fetch_parsed_messages()
    telegram = TelegramSender()

    for parsed_message in messages:
        try:
            formatted_message = json.dumps(parsed_message, indent=2)  # Formater til Telegram
            telegram.send_message(formatted_message)
            logger.info("Besked sendt til Telegram.")
        except Exception as e:
            logger.error(f"Fejl under afsendelse: {e}")

if __name__ == "__main__":
    process_unparsed_messages()
    send_messages_to_telegram()