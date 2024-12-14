import re
import logging
from configparser import ConfigParser

# Opsætning af logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global dictionary til gemte beskeder
messages_dict = {}

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
    parsed = {}

    try:
        # Parse lokationsdetaljer
        parsed['stednavn'] = extract_field(r"Message:.*?\n([^\n]+)<CR><LF>", message, default=None)
        parsed['adresse'] = extract_field(r"<CR><LF>([^<]+) \d+", message, default=None)
        parsed['postnr'] = extract_field(r"<CR><LF>(\d{4})", message, default=None)
        parsed['by'] = extract_field(r"<CR><LF>\d{4} ([^\n<]+)", message, default=None)

        # Parse koordinater
        parsed['lat'] = extract_field(r"N([\d.]+)", message, default=None)
        parsed['long'] = extract_field(r"E([\d.]+)", message, default=None)
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

def format_message(data):
    """
    Formaterer dictionary til en læsbar beskedtekst.
    """
    message_parts = []

    # Tilføj relevante dele til besked
    if data.get('stednavn'):
        message_parts.append(f"Stednavn: {data['stednavn']}")
    if data.get('adresse'):
        message_parts.append(f"Adresse: {data['adresse']}")
    if data.get('postnr') and data.get('by'):
        message_parts.append(f"Postnr og by: {data['postnr']} {data['by']}")
    if data.get('linktilgooglemaps'):
        message_parts.append(f"Google Maps: {data['linktilgooglemaps']}")

    # Tilføj alarmtyper og andre detaljer
    for key, value in data.items():
        if key.startswith('alarmtype_') or key.startswith('alarmkald_') or key.startswith('specifik_'):
            if value:
                message_parts.append(f"{key.replace('_', ' ').title()}: {value}")

    # Returner samlet besked
    return "\n".join(message_parts)

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra en fil.
    """
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg

def update_messages_dict(message, cfg):
    """
    Opdaterer `messages_dict` med en ny besked.
    """
    global messages_dict

    # Parse beskeden
    parsed_message = parse_message_dynamic(message, cfg)

    # Bestem unik nøgle (fx via jobnr eller adresse)
    unique_key = parsed_message.get('adresse') or parsed_message.get('lat') or len(messages_dict)

    # Opdater eksisterende besked eller tilføj ny
    if unique_key in messages_dict:
        messages_dict[unique_key].update(parsed_message)
    else:
        messages_dict[unique_key] = parsed_message