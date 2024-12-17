import subprocess
import collections
import logging
import configparser
import sqlite3
import json
from datetime import datetime

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("message_receiver")

DB_PATH = "messages.db"

def setup_database():
    """
    Opretter SQLite-databasen, hvis den ikke allerede eksisterer.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_message TEXT,
                timestamp TEXT,
                parsed_fields TEXT
            )
        """)
        conn.commit()

def save_message_to_db(raw_message, parsed_fields):
    """
    Gemmer en besked i databasen.
    """
    timestamp = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (raw_message, timestamp, parsed_fields)
            VALUES (?, ?, ?)
        """, (raw_message, timestamp, json.dumps(parsed_fields)))
        
        # Begræns databasen til 1000 beskeder
        cursor.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 1000)")
        conn.commit()

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = configparser.ConfigParser()
    cfg.read(filepath)
    return cfg

def start_message_receiver(cfg):
    """
    Starter beskedmodtagerprocessen og gemmer rå beskeder i SQLite-databasen.
    """
    prots = cfg.get('multimon-ng', 'prot').split()
    prots = ' -a '.join(prots)
    if prots:
        prots = '-a ' + prots

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

    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break

            logger.info(f"Raw output: {output.strip()}")
            if "Alpha" not in output:
                continue

            output = output.replace("<NUL>", "").strip()

            # Gem beskeden i databasen
            parsed_fields = {}  # Dummy data for nu
            save_message_to_db(output, parsed_fields)

    except Exception as e:
        logger.error(f"Error in message processing: {e}")

    finally:
        process.terminate()
        logger.info("Message receiver process terminated.")

if __name__ == "__main__":
    try:
        setup_database()
        cfg = load_config()
        start_message_receiver(cfg)
    except Exception as e:
        logger.error(f"Critical error: {e}")