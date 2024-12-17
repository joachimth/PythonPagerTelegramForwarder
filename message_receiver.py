import sqlite3
import subprocess
import collections
import logging
import configparser
from message_parser import parse_message_dynamic

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("message_receiver")

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = configparser.ConfigParser()
    cfg.read(filepath)
    return cfg

def save_message_to_db(raw_message, parsed_message, db_path='messages.db'):
    """
    Gemmer både rå og dekodede beskeder i SQLite-databasen.
    """
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

def start_message_receiver(cfg):
    """
    Starter beskedmodtagerprocessen og håndterer beskeder fra multimon-ng.
    """
    prots = cfg.get('multimon-ng', 'prot').split()
    prots = ' -a '.join(prots)
    if prots:
        prots = '-a ' + prots

    recent_messages = collections.deque(maxlen=100)

    command = (
        "rtl_fm {} -d {} -l {} -g {} -p {} -f {} -s {} | multimon-ng -C {} -t raw {} -f alpha /dev/stdin -"
        .format(
            cfg.get('rtl_fm', 'enable_option'),
            cfg.get('rtl_fm', 'device_index'),
            cfg.get('rtl_fm', 'squelch_level'),
            cfg.get('rtl_fm', 'gain'),
            cfg.get('rtl_fm', 'ppm_error'),
            cfg.get('Frequencies', 'freq'),
            cfg.get('rtl_fm', 'sample_rate'),
            cfg.get('multimon-ng', 'pocsag_charset'),
            prots
        )
    )

    logger.info(f"Command executed: {command}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    decode_format = cfg.get('Encoding', 'encoding_format')

    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break

            logger.info(f"Raw output: {output.strip()}")
            if "Alpha" not in output:
                continue

            raw_message = output.replace("<NUL>", "").strip()
            if raw_message in recent_messages:
                continue

            recent_messages.append(raw_message)

            # Dekod beskeden
            parsed_message = parse_message_dynamic(raw_message, cfg)

            # Gem både rå og dekodede beskeder i databasen
            save_message_to_db(raw_message, parsed_message)

    except Exception as e:
        logger.error(f"Error in message processing: {e}")

    finally:
        process.terminate()
        logger.info("Message receiver process terminated.")

if __name__ == "__main__":
    try:
        cfg = load_config()
        start_message_receiver(cfg)
    except Exception as e:
        logger.error(f"Critical error: {e}")