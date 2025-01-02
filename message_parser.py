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
CONFIG_PATH = "config.txt"

def load_config(filepath=CONFIG_PATH):
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
        # Fjern <CR><LF>, <NUL> og trim beskeden
        cleaned_message = message.replace("<CR><LF>", "\n").replace("<NUL>", "").strip()

        # Gennemgå dynamiske regler fra config.txt
        if "MessageParsing" in cfg.sections():
            for key, pattern in cfg.items("MessageParsing"):
                match = re.search(pattern, cleaned_message)
                if match:
                    parsed[key] = match.group(1).strip() if match.groups() else True
                else:
                    parsed[key] = None

        # Tilføj standardfelter, hvis ikke fundet
        parsed['stednavn'] = parsed.get('stednavn') or re.search(r"\n(.+)\n", cleaned_message)
        parsed['stednavn'] = parsed['stednavn'].group(1).strip() if parsed['stednavn'] else None

        parsed['adresse'] = parsed.get('adresse') or re.search(r"\n(.+)\n\d{4}", cleaned_message)
        parsed['adresse'] = parsed['adresse'].group(1).strip() if parsed['adresse'] else None

        parsed['postnr'] = parsed.get('postnr') or re.search(r"\n(\d{4})\s", cleaned_message)
        parsed['postnr'] = parsed['postnr'].group(1) if parsed['postnr'] else None

        parsed['by'] = parsed.get('by') or re.search(r"\n\d{4}\s(.+)", cleaned_message)
        parsed['by'] = parsed['by'].group(1).strip() if parsed['by'] else None

        parsed['latlong'] = parsed.get('latlong') or re.search(r"N(\d+\.\d+),\s*E(\d+\.\d+)", cleaned_message)
        if parsed['latlong']:
            parsed['latitude'], parsed['longitude'] = parsed['latlong'].groups()
            parsed['linktilgooglemaps'] = f"https://www.google.com/maps?q={parsed['latitude']},{parsed['longitude']}"
        elif parsed['adresse']:
            # Brug adresse til Google Maps link, hvis GPS-koordinater mangler
            parsed['linktilgooglemaps'] = f"https://www.google.com/maps?q={parsed['adresse']},+{parsed['postnr']}+{parsed['by']}"
        else:
            parsed['linktilgooglemaps'] = None

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
            #logger.info(f"Besked ID {message_id} opdateret med parsed data.")
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

            #logger.info(f"Fundet {len(rows)} beskeder, der skal parses.")

            for message_id, raw_message in rows:
                #logger.info(f"Behandler besked ID {message_id}: {raw_message}")
                parsed_message = parse_message_dynamic(raw_message, cfg)
                #logger.info(f"Parsed besked: {parsed_message}")
                update_message_in_db(message_id, parsed_message)

    except sqlite3.Error as e:
        logger.error(f"Fejl under hentning af beskeder fra databasen: {e}")

if __name__ == "__main__":
    process_unparsed_messages()