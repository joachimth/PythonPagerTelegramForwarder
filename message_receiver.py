import subprocess
import collections
import logging
import configparser
from message_parser import parse_message_dynamic, format_message
from telegram_sender import TelegramSender

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("message_receiver")

# Global beskedbuffer
recent_messages = collections.deque(maxlen=100)

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = configparser.ConfigParser()
    cfg.read(filepath)
    return cfg

def start_message_receiver(cfg):
    """
    Starter beskedmodtagerprocessen og håndterer beskeder fra multimon-ng.
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
    decode_format = cfg.get('Encoding', 'encoding_format')

    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break

            logger.info(f"Raw output: {output.strip()}")
            if "Alpha" not in output:
                continue

            output = output.replace("<NUL>", "").strip()
            if output in recent_messages:
                continue

            recent_messages.append(output)

    except Exception as e:
        logger.error(f"Error in message processing: {e}")

    finally:
        process.terminate()
        logger.info("Message receiver process terminated.")

def fetch_latest_messages():
    """
    Henter de seneste beskeder fra `recent_messages`.
    """
    return list(recent_messages)

if __name__ == "__main__":
    try:
        cfg = load_config()
        start_message_receiver(cfg)
    except Exception as e:
        logger.error(f"Critical error: {e}")