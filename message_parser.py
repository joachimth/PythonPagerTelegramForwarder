import re
import logging
from configparser import ConfigParser

# Opsætning af logging til en separat logfil for beskedhåndtering
message_logger = logging.getLogger('message_logger')
message_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('message_processing.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
message_logger.addHandler(file_handler)

# Global dictionary til gemte beskeder
messages_dict = {}

# Opret en testbesked ved opstart
test_message = {
    "besked.nr": 0,
    "stednavn": "Test Sted",
    "adresse": "Testvej 1",
    "postnr": "0000",
    "by": "Testby",
    "lat": None,
    "long": None,
    "linktilgooglemaps": "https://www.google.com/maps?q=Testvej+1+0000+Testby",
    "alarmtype_kritisk": False,
    "alarmtype_seriøs": False,
    "alarmtype_lavrisiko": True,
    "alarmtype_højrisiko": False,
    "alarmkald_politi": False,
    "alarmkald_brand": False,
    "alarmkald_isl": False,
    "alarmkald_medicin": False,
    "alarmkald_vagt": False,
    "alarmkald_specialrespons": False,
    "specifik_brandalarm": False,
    "specifik_gasledningsbrud": False,
    "specifik_bygningsbrand": False,
}
messages_dict["test"] = test_message

def extract_field(pattern, text, default=None):
    """
    Finder og returnerer et felt baseret på regex-mønster.
    """
    try:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default
    except Exception as e:
        message_logger.warning(f"Fejl under parsing med mønster '{pattern}': {e}")
        return default

def generate_google_maps_link(lat, long, adresse=None, postnr=None, by=None):
    """
    Genererer Google Maps link baseret på koordinater eller adresseoplysninger.
    """
    try:
        if lat and long:
            return f"https://www.google.com/maps?q={lat},{long}"
        elif adresse or postnr or by:
            adresse_parts = [adresse, postnr, by]
            adresse_encoded = "+".join([part.replace(" ", "+") for part in adresse_parts if part])
            return f"https://www.google.com/maps?q={adresse_encoded}"
        return ""
    except Exception as e:
        message_logger.warning(f"Fejl under generering af Google Maps link: {e}")
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
        message_logger.error(f"Fejl under parsing af besked: {e}")
        parsed['fejl'] = True

    # Sørg for, at alle beskeder har en minimumsstruktur
    parsed.setdefault('besked.nr', len(messages_dict) + 1)
    parsed.setdefault('stednavn', "Ukendt sted")
    parsed.setdefault('adresse', "Ukendt adresse")
    parsed.setdefault('postnr', "0000")
    parsed.setdefault('by', "Ukendt by")
    parsed.setdefault('linktilgooglemaps', generate_google_maps_link(None, None, "Ukendt adresse", "0000", "Ukendt by"))

    # Log den parserede besked
    message_logger.info(f"Parsed Message: {parsed}")
    return parsed

def format_message(data):
    """
    Formaterer dictionary til en læsbar beskedtekst.
    """
    try:
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
    except Exception as e:
        message_logger.error(f"Fejl under formatering af besked: {e}")
        return "Kunne ikke formatere besked."

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra en fil.
    """
    try:
        cfg = ConfigParser()
        cfg.read(filepath)
        return cfg
    except Exception as e:
        message_logger.error(f"Fejl under indlæsning af config: {e}")
        raise

def update_messages_dict(message, cfg):
    """
    Opdaterer `messages_dict` med en ny besked.
    """
    global messages_dict

    try:
        # Parse beskeden
        parsed_message = parse_message_dynamic(message, cfg)

        # Bestem unik nøgle (fx via jobnr eller adresse)
        unique_key = parsed_message.get('adresse') or parsed_message.get('lat') or len(messages_dict)

        # Opdater eksisterende besked eller tilføj ny
        if unique_key in messages_dict:
            messages_dict[unique_key].update(parsed_message)
        else:
            messages_dict[unique_key] = parsed_message

        # Hvis der er mere end 10 beskeder, fjern testbeskeden
        if "test" in messages_dict and len(messages_dict) > 10:
            del messages_dict["test"]

        # Log opdateringen
        message_logger.info(f"Message updated in dictionary: {parsed_message}")
    except Exception as e:
        message_logger.error(f"Fejl under opdatering af messages_dict: {e}")