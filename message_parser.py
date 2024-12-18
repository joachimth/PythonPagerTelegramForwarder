import sqlite3
import logging
import json
from configparser import ConfigParser

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("message_parser")

DB_PATH = "messages.db"

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg

def parse_message_dynamic(message, config):
    """
    Parser en besked dynamisk baseret på regler og mønstre i config.txt.
    """
    parsed = {"raw_message": message}
    try:
        # Eksempel på dynamisk parsing baseret på `config.txt`
        parsed['stednavn'] = config.get('MessageParsing', 'stednavn', fallback="Ukendt Sted")
        parsed['adresse'] = config.get('MessageParsing', 'adresse', fallback="Ukendt Adresse")
        parsed['postnr'] = config.get('MessageParsing', 'postnr', fallback="0000")
        parsed['by'] = config.get('MessageParsing', 'by', fallback="Ukendt By")
        parsed['alarmtype'] = config.get('MessageParsing', 'alarmtype', fallback="Ukendt Alarmtype")
        # Du kan tilføje mere dynamik her ved hjælp af regex-mønstre fra config
    except Exception as e:
        logger.error(f"Fejl under parsing af besked: {e}")
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
    config = load_config()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, raw_message
                FROM messages
                WHERE parsed_fields IS NULL
            """)
            rows = cursor.fetchall()

            if not rows:
                logger.info("Ingen uparrede beskeder fundet.")
                return

            for message_id, raw_message in rows:
                parsed_message = parse_message_dynamic(raw_message, config)
                update_message_in_db(message_id, parsed_message)

    except sqlite3.Error as e:
        logger.error(f"Fejl under hentning af beskeder fra databasen: {e}")

if __name__ == "__main__":
    process_unparsed_messages()