import re
import logging
from configparser import ConfigParser

# Opsætning af logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_field(pattern, text, default=None):
    """Find og returner et felt baseret på regex-mønster."""
    try:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default
    except Exception as e:
        logging.warning(f"Fejl under parsing med mønster '{pattern}': {e}")
        return default

def generate_google_maps_link(lat, long, adresse=None, postnr=None, by=None):
    """Generér Google Maps link baseret på lat/long eller adresse/postnr/by."""
    if lat and long:
        return f"https://www.google.com/maps?q={lat},{long}"
    elif adresse or postnr or by:
        adresse_parts = [adresse, postnr, by]
        adresse_encoded = "+".join([part.replace(" ", "+") for part in adresse_parts if part])
        return f"https://www.google.com/maps?q={adresse_encoded}"
    return ""

def parse_message_dynamic(message, cfg):
    """Parser en besked dynamisk baseret på betingelser fra config.txt."""
    parsed = {}

    try:
        # Lokationsdetaljer
        parsed['stednavn'] = extract_field(r"Message:.*?\n([^\n]+)<CR><LF>", message)
        parsed['adresse'] = extract_field(r"<CR><LF>([^\d]+) \d+", message)
        parsed['postnr'] = extract_field(r"<CR><LF>(\d{4})", message, default=None)
        parsed['by'] = extract_field(r"<CR><LF>([A-Za-zæøåÆØÅ\s]+)<CR><LF>", message, default=None)

        # Koordinater og geografi
        parsed['lat'] = extract_field(r"N([\d.]+)", message, default=None)
        parsed['long'] = extract_field(r"E([\d.]+)", message, default=None)
        parsed['linktilgooglemaps'] = generate_google_maps_link(
            parsed['lat'], parsed['long'], parsed['adresse'], parsed['postnr'], parsed['by']
        )

        # Dynamisk egenskabsudtræk fra config
        for key, patterns in cfg.items("MessageParsing"):
            if key.startswith("alarmtype") or key.startswith("alarmkald"):
                parsed[key] = any(pat in message for pat in patterns.split(", "))

            elif key.startswith("bygningstype"):
                if any(pat in message for pat in patterns.split(", ")):
                    parsed['bygningstype'] = key.split("_")[1]

            elif key.startswith("specifik"):
                parsed[key] = any(pat in message for pat in patterns.split(", "))

    except Exception as e:
        logging.error(f"Fejl under parsing af besked: {e}")
        parsed['fejl'] = True

    return parsed

def load_config(filepath='config.txt'):
    """Indlæs konfiguration fra en fil."""
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg
