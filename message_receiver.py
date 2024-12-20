import sqlite3
import subprocess
import collections
import logging
import configparser
import json
from datetime import datetime

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("message_receiver")

DB_PATH = "messages.db"

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = configparser.ConfigParser()
    cfg.read(filepath)
    return cfg

def insert_message_into_db(raw_message):
    """
    Indsætter en rå besked i databasen.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (raw_message)
                VALUES (?)
            """, (raw_message,))
            conn.commit()
            logger.info(f"Rå besked gemt i databasen: {raw_message}")
    except sqlite3.Error as e:
        logger.error(f"Fejl under indsættelse i databasen: {e}")

def start_message_receiver(cfg):
    """
    Starter beskedmodtagerprocessen og gemmer rå beskeder i databasen.
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

    logger.info(f"Kommando udført: {command}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    decode_format = cfg.get('Encoding', 'encoding_format')

    try:
        while True:
            output = process.stdout.readline().strip()
            if not output:
                continue

            logger.info(f"Rå output: {output}")
            if "Alpha" not in output:
                continue

            output = output.replace("<NUL>", "").strip()
            if output in recent_messages:
                continue

            recent_messages.append(output)
            raw_message = output.split("Alpha:", 1)[1].strip()
            if len(raw_message) < int(cfg.get('multimon-ng', 'min_len')):
                continue

            # Gem rå besked i databasen
            insert_message_into_db(raw_message)

    except Exception as e:
        logger.error(f"Fejl under beskedmodtagelse: {e}")

    finally:
        process.terminate()
        logger.info("Message receiver-processen er afsluttet.")

if __name__ == "__main__":
    try:
        cfg = load_config()
        start_message_receiver(cfg)
    except Exception as e:
        logger.error(f"Kritisk fejl: {e}")