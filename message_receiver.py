import sqlite3
import subprocess
import collections
import logging
import configparser
import json
import os
from datetime import datetime

# Logger opsætning
logging.basicConfig(
    filename="messagereceiver.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
            logging.info(f"Rå besked gemt i databasen: {raw_message}")
    except sqlite3.Error as e:
        logging.error(f"Fejl under indsættelse i databasen: {e}")

def start_message_receiver(cfg):
    """
    Starter beskedmodtagerprocessen og gemmer rå beskeder i databasen.
    """
    logging.info(f"Starter besked modtageren")
    
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

    logging.info(f"Kommando udført: {command}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    decode_format = cfg.get('Encoding', 'encoding_format')

    try:
        while True:
            output = process.stdout.readline()
            #if not output:
                #continue

            #logging.info(f"Rå output B: {output}")
            if "Alpha" not in output:
                continue
            
            logging.info(f"Rå output A: {output}")
            
            output = output.replace("<NUL>", "")
            #if output in recent_messages:
                #continue

            recent_messages.append(output)
            raw_message = output.split("Alpha:", 1)[1]
            #if len(raw_message) < int(cfg.get('multimon-ng', 'min_len')):
                #continue

            # Gem rå besked i databasen
            insert_message_into_db(raw_message)

    except Exception as e:
        logging.error(f"Fejl under beskedmodtagelse: {e}")

    finally:
        process.terminate()
        logging.info("Message receiver-processen er afsluttet.")

if __name__ == "__main__":
    try:
        cfg = load_config()
        start_message_receiver(cfg)
    except Exception as e:
        logging.error(f"Kritisk fejl: {e}")