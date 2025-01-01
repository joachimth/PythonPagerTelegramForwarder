import sqlite3
import logging
import json
import re
from configparser import ConfigParser

# Logger opsætning
LOG_FILE = "message_parser.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log til fil
        logging.StreamHandler()        # Log til konsol
    ]
)
logger = logging.getLogger("message_parser")

DB_PATH = "messages.db"

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg

def parse_message_dynamic(message, cfg):
    """
    Parser en besked dynamisk baseret på regler defineret i config.txt.
    """
    parsed = {"raw_message": message}
    try:
        # Fjern specialtegn
        cleaned_message = message.replace("<CR><LF>", "\n").replace("<NUL>", "").strip()

        # Gennemgå regler fra MessageParsing sektionen i config.txt
        if "MessageParsing" in cfg.sections():
            for key, pattern in cfg.items("MessageParsing"):
                try:
                    match = re.search(pattern, cleaned_message)
                    parsed[key] = match.group(1).strip() if match else None
                except re.error as regex_error:
                    logger.error(f"Fejl i regex-mønster for {key}: {regex_error}")
                    parsed[key] = None

    except Exception as e:
        logger.error(f"Fejl under parsing: {e}")
        parsed['error'] = True

    return parsed

def update_message_in_db(message_id, parsed_message):
    """
    Opdaterer en besked i databasen med de parsed felter.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET parsed_fields = ?, timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(parsed_message), message_id))
            conn.commit()
            logger.info(f"Besked ID {message_id} opdateret med parsed data.")
    except sqlite3.Error as e:
        logger.error(f"Fejl under opdatering af databasen: {e}")

def process_unparsed_messages():
    """
    Henter og parser beskeder, der endnu ikke er blevet parsed.
    """
    try:
        cfg = load_config()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, raw_message FROM messages
                WHERE parsed_fields IS NULL
            """)
            rows = cursor.fetchall()

            logger.info(f"Fundet {len(rows)} beskeder, der skal parses.")

            for message_id, raw_message in rows:
                logger.info(f"Behandler besked ID {message_id}: {raw_message}")
                parsed_message = parse_message_dynamic(raw_message, cfg)
                logger.info(f"Parsed besked: {parsed_message}")
                update_message_in_db(message_id, parsed_message)

    except sqlite3.Error as e:
        logger.error(f"Fejl under hentning af beskeder fra databasen: {e}")

if __name__ == "__main__":
    process_unparsed_messages()