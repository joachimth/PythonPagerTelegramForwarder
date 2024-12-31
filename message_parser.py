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
        # Fjern <CR><LF> og <NUL>
        cleaned_message = message.replace("<CR><LF>", "\n").replace("<NUL>", "").strip()

        # Gennemgå dynamiske regler fra config.txt
        if "MessageParsing" in cfg.sections():
            for key, pattern in cfg.items("MessageParsing"):
                match = re.search(pattern, cleaned_message)
                if match:
                    parsed[key] = match.group(1).strip() if match.groups() else True
                else:
                    parsed[key] = None

        # Eksempel på manuelle regex-analyser for ekstra felter
        parsed['stednavn'] = parsed.get('stednavn') or re.search(r"Alpha:\s+\([A-Z]\)M\+V\n([^\n]+)", cleaned_message)
        parsed['stednavn'] = parsed['stednavn'].group(1) if parsed['stednavn'] else None

        parsed['adresse'] = parsed.get('adresse') or re.search(r"\n([^,]+)\n", cleaned_message)
        parsed['adresse'] = parsed['adresse'].group(1) if parsed['adresse'] else None

        parsed['postnr'] = parsed.get('postnr') or re.search(r"\n(\d{4})\s", cleaned_message)
        parsed['postnr'] = parsed['postnr'].group(1) if parsed['postnr'] else None

        parsed['by'] = parsed.get('by') or re.search(r"\n\d{4}\s([^\n]+)", cleaned_message)
        parsed['by'] = parsed['by'].group(1) if parsed['by'] else None

        parsed['detaljer'] = parsed.get('detaljer') or re.search(r"\nild i.*", cleaned_message)
        parsed['detaljer'] = parsed['detaljer'].group(0).strip() if parsed['detaljer'] else None

        parsed['jobnr'] = parsed.get('jobnr') or re.search(r"Job-nr:\s*(\d+)", cleaned_message)
        parsed['jobnr'] = parsed['jobnr'].group(1) if parsed['jobnr'] else None

        parsed['koordinater'] = parsed.get('koordinater') or re.search(r"N(\d+.\d+),\s*E(\d+.\d+)", cleaned_message)
        if parsed['koordinater']:
            parsed['latitude'], parsed['longitude'] = parsed['koordinater'].groups()
        else:
            parsed['latitude'], parsed['longitude'] = None, None

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

def insert_dummy_messages():
    """
    Tilføjer dummy-beskeder til databasen for testformål.
    """
    dummy_messages = [
        "(A)M+V<CR><LF>Naturbrand-Halmstak<CR><LF>Seerdrupvej 25<CR><LF>4200 Slagelse<CR><LF>ild i halmstak. mange halmballer. tlf 5163-6114<NUL>",
        "(S)M<CR><LF>Naturbrand-Mindre brand<CR><LF>Pedersborg Torv 14<CR><LF>4180 Sorø<CR><LF>Det gløder fra træ.<NUL>",
        "DAGENS PRØVE TIL ISL",
        "(A)M+V<CR><LF>Naturbrand-Halmstak K: 1<CR><LF>Seerdrupvej 25<CR><LF>4200 Slagelse<CR><LF>ild i halmstak. mange halmballer. tlf 5163-6114<CR><LF>Job-nr: 47148623<CR><LF>?RSE_1/1_0_N55.20.53,5_E011.20.22,2<NUL>"
    ]
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for message in dummy_messages:
                cursor.execute("""
                    INSERT INTO messages (raw_message)
                    VALUES (?)
                """, (message,))
            conn.commit()
            logger.info("Dummy-beskeder tilføjet til databasen.")
    except sqlite3.Error as e:
        logger.error(f"Fejl under indsættelse af dummy-beskeder: {e}")

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
    insert_dummy_messages()  # Tilføjer dummy-beskeder til databasen
    process_unparsed_messages()