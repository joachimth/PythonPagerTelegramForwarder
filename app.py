import sqlite3
import logging
import json
from message_parser import parse_message_dynamic, format_message
from telegram_sender import TelegramSender

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

DB_PATH = "messages.db"

def fetch_raw_messages(limit=10):
    """
    Henter rå beskeder fra databasen, som endnu ikke er dekodet.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, raw_message, timestamp, parsed_fields
            FROM messages
            WHERE parsed_fields IS NULL
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def update_parsed_message_in_db(message_id, parsed_message):
    """
    Opdaterer databasen med de dekodede beskeder.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET parsed_fields = ?
                WHERE id = ?
            """, (json.dumps(parsed_message), message_id))
            conn.commit()
            logger.info(f"Besked ID {message_id} opdateret med dekodede data.")
    except Exception as e:
        logger.error(f"Fejl under opdatering af besked ID {message_id}: {e}")

def fetch_latest_parsed_messages(limit=10):
    """
    Henter de seneste dekodede beskeder fra databasen.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, parsed_fields, timestamp
            FROM messages
            WHERE parsed_fields IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def process_and_send_messages():
    """
    Henter rå beskeder fra databasen, parser dem, gemmer dekodede data og sender dem til Telegram.
    """
    try:
        # Hent rå beskeder, der mangler parsing
        messages = fetch_raw_messages()
        if not messages:
            logger.info("Ingen nye rå beskeder fundet.")
            return

        telegram_sender = TelegramSender()

        for message_id, raw_message, timestamp, parsed_fields in messages:
            try:
                logger.info(f"Behandler rå besked ID {message_id} modtaget på tidspunkt {timestamp}")

                # Parse beskeden, hvis den ikke allerede er dekodet
                if not parsed_fields:
                    parsed_message = parse_message_dynamic(raw_message)
                    update_parsed_message_in_db(message_id, parsed_message)
                else:
                    parsed_message = json.loads(parsed_fields)

                formatted_message = format_message(parsed_message)

                # Send besked til Telegram
                telegram_sender.send_message(formatted_message)
                logger.info(f"Besked sendt til Telegram: {formatted_message}")

            except json.JSONDecodeError:
                logger.error(f"Fejl i JSON-format for besked ID {message_id}.")
            except Exception as e:
                logger.error(f"Fejl under behandling af besked ID {message_id}: {e}")

    except Exception as e:
        logger.error(f"Fejl under beskedbehandling: {e}")

if __name__ == "__main__":
    logger.info("Starter app.py")
    try:
        process_and_send_messages()
    except KeyboardInterrupt:
        logger.info("App afsluttes af bruger.")
    except Exception as e:
        logger.error(f"Kritisk fejl i app.py: {e}")