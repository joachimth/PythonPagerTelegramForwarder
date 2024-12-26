import sqlite3
import logging
import json
import re
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

def extract_field(pattern, text, default=None):
    """
    Ekstraherer et felt baseret på et regex-mønster.
    """
    try:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default
    except Exception as e:
        logger.warning(f"Fejl under parsing med mønster '{pattern}': {e}")
        return default

def generate_google_maps_link(lat, long, adresse=None, postnr=None, by=None):
    """
    Genererer Google Maps link baseret på koordinater eller adresseoplysninger.
    """
    if lat and long:
        return f"https://www.google.com/maps?q={lat},{long}"
    elif adresse or postnr or by:
        adresse_parts = [adresse, postnr, by]
        adresse_encoded = "+".join([part.replace(" ", "+") for part in adresse_parts if part])
        return f"https://www.google.com/maps?q={adresse_encoded}"
    return ""

def parse_message_dynamic(message, cfg):
    """
    Parser en besked dynamisk baseret på regler og mønstre i config.txt.
    """
    parsed = {"raw_message": message}
    try:
        # Ekstraktion baseret på faste felter
        parsed['stednavn'] = extract_field(r"Sted:\s*(.*?)<", message)
        parsed['adresse'] = extract_field(r"Adresse:\s*(.*?)<", message)
        parsed['postnr'] = extract_field(r"Postnr:\s*(\d{4})", message)
        parsed['by'] = extract_field(r"By:\s*(.*?)<", message)
        parsed['lat'] = extract_field(r"Lat:\s*([\d.]+)", message)
        parsed['long'] = extract_field(r"Long:\s*([\d.]+)", message)

        # Generer Google Maps link
        parsed['linktilgooglemaps'] = generate_google_maps_link(
            parsed['lat'], parsed['long'], parsed['adresse'], parsed['postnr'], parsed['by']
        )

        # Dynamisk parsing fra config
        for key, patterns in cfg.items("MessageParsing"):
            if key.startswith("alarmtype") or key.startswith("alarmkald") or key.startswith("specifik"):
                parsed[key] = any(pat in message for pat in patterns.split(", "))

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
    cfg = load_config()
    try:
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