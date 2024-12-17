import sqlite3
import logging
import json
from message_parser import parse_message_dynamic, format_message
from telegram_sender import TelegramSender

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

DB_PATH = "messages.db"

def fetch_messages_from_db(limit=10):
    """
    Henter de seneste beskeder fra databasen.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT raw_message, timestamp, parsed_fields
            FROM messages
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
    return rows

def process_and_send_messages():
    """
    Henter beskeder fra databasen, parser dem og sender dem til Telegram.
    """
    try:
        messages = fetch_messages_from_db()
        if not messages:
            logger.info("Ingen nye beskeder modtaget.")
            return

        telegram_sender = TelegramSender()

        for raw_message, timestamp, parsed_fields in messages:
            try:
                logger.info(f"Modtaget rå besked: {raw_message} på tidspunkt {timestamp}")
                
                # Hvis parsed_fields ikke er tom, brug det
                parsed_message = json.loads(parsed_fields) if parsed_fields else parse_message_dynamic(raw_message)
                formatted_message = format_message(parsed_message)

                # Send besked til Telegram
                telegram_sender.send_message(formatted_message)
                logger.info(f"Besked sendt til Telegram: {formatted_message}")

            except Exception as e:
                logger.error(f"Fejl under behandling af besked: {e}")

    except Exception as e:
        logger.error(f"Fejl under hentning af beskeder: {e}")

if __name__ == "__main__":
    logger.info("Starter app.py")
    try:
        process_and_send_messages()
    except KeyboardInterrupt:
        logger.info("App afsluttes af bruger.")
    except Exception as e:
        logger.error(f"Kritisk fejl i app.py: {e}")