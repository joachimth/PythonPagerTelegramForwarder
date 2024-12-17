import re
import logging
from configparser import ConfigParser
import os
import sqlite3

# Sikring af logfilen
LOG_FILE = "messages.log"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as log_file:
        log_file.write("Log oprettet.\n")

# Opsætning af logging med INFO som standardniveau
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_field(pattern, text, default=None):
    """
    Finder og returnerer et felt baseret på regex-mønster.
    """
    try:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default
    except Exception as e:
        logging.warning(f"Fejl under parsing med mønster '{pattern}': {e}")
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
    parsed = {
        'stednavn': None, 'adresse': None, 'postnr': None, 'by': None,
        'lat': None, 'long': None, 'linktilgooglemaps': None,
        'alarmtype_kritisk': False, 'alarmtype_seriøs': False,
        'alarmtype_lavrisiko': False, 'alarmtype_højrisiko': False,
        'alarmkald_politi': False, 'alarmkald_brand': False,
        'alarmkald_isl': False, 'alarmkald_medicin': False,
        'alarmkald_vagt': False, 'alarmkald_specialrespons': False,
        'specifik_brandalarm': False, 'specifik_gasledningsbrud': False,
        'specifik_bygningsbrand': False
    }

    try:
        # Parse lokationsdetaljer
        parsed['stednavn'] = extract_field(r"Message:.*?\n([^\n]+)<CR><LF>", message)
        parsed['adresse'] = extract_field(r"<CR><LF>([^<]+) \d+", message)
        parsed['postnr'] = extract_field(r"<CR><LF>(\d{4})", message)
        parsed['by'] = extract_field(r"<CR><LF>\d{4} ([^\n<]+)", message)

        # Parse koordinater
        parsed['lat'] = extract_field(r"N([\d.]+)", message)
        parsed['long'] = extract_field(r"E([\d.]+)", message)
        parsed['linktilgooglemaps'] = generate_google_maps_link(
            parsed['lat'], parsed['long'], parsed['adresse'], parsed['postnr'], parsed['by']
        )

        # Parse alarmtyper og andre egenskaber fra config
        for key, patterns in cfg.items("MessageParsing"):
            if key.startswith("alarmtype") or key.startswith("alarmkald") or key.startswith("specifik"):
                parsed[key] = any(pat in message for pat in patterns.split(", "))

    except Exception as e:
        logging.error(f"Fejl under parsing af besked: {e}")
        parsed['fejl'] = True

    return parsed

def save_parsed_message_to_db(raw_message, parsed_message, db_path='messages.db'):
    """
    Gemmer en rå og dekodet besked i SQLite-databasen.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO messages (
            raw_message, stednavn, adresse, postnr, by, lat, long, linktilgooglemaps,
            alarmtype_kritisk, alarmtype_seriøs, alarmtype_lavrisiko, alarmtype_højrisiko,
            alarmkald_politi, alarmkald_brand, alarmkald_isl, alarmkald_medicin,
            alarmkald_vagt, alarmkald_specialrespons, specifik_brandalarm,
            specifik_gasledningsbrud, specifik_bygningsbrand
        ) VALUES (
            :raw_message, :stednavn, :adresse, :postnr, :by, :lat, :long, :linktilgooglemaps,
            :alarmtype_kritisk, :alarmtype_seriøs, :alarmtype_lavrisiko, :alarmtype_højrisiko,
            :alarmkald_politi, :alarmkald_brand, :alarmkald_isl, :alarmkald_medicin,
            :alarmkald_vagt, :alarmkald_specialrespons, :specifik_brandalarm,
            :specifik_gasledningsbrud, :specifik_bygningsbrand
        )
        """, {
            'raw_message': raw_message,
            **parsed_message
        })
        conn.commit()
        conn.close()
        logging.info("Dekodet besked gemt i databasen.")
    except Exception as e:
        logging.error(f"Fejl under gemning i databasen: {e}")

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra en fil.
    """
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg