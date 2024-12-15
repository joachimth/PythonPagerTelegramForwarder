import sys
import time
import subprocess
import collections
import configparser
from time import gmtime, strftime
from pytgbot import Bot
import os
import logging
from logging.handlers import RotatingFileHandler
from message_parser import parse_message_dynamic, format_message

# Logger opsætning
logging.basicConfig(
    filename="multimon_restart.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("my_logger")

def start_multimon(cfg):
    """
    Starter rtl_fm og multimon-ng til at dekode POCSAG-beskeder.
    """
    prots = cfg.get('multimon-ng', 'prot').split()
    prots = ' -a '.join(prots)
    if prots:
        prots = '-a ' + prots

    bot = Bot(os.getenv('TELEGRAM_API'))
    d = collections.deque(maxlen=100)

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
    logger.info(f"Starting process: {command}")

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        decode_format = cfg.get('Encoding', 'encoding_format')
        fail_count = 0

        while process.poll() is None:
            output = process.stdout.readline().decode(decode_format).strip()
            if not output:
                continue

            logger.info(f"Raw output: {output}")
            if "Alpha" not in output:
                continue

            output = output.replace("<NUL>", "")
            if output in d:
                continue

            d.append(output)
            msg = output.split("Alpha:", 1)[1].strip()
            if len(msg) < int(cfg.get('multimon-ng', 'min_len')):
                continue

            logger.info(f"Parsed message: {msg}")

            # Parse og send til Telegram
            parsed_message = parse_message_dynamic(msg, cfg)
            formatted_message = format_message(parsed_message)

            chat_id = os.getenv('TELEGRAM_REC')
            bot.send_message(chat_id, formatted_message)
            logger.info(f"Message sent to Chat ID {chat_id}: {formatted_message}")

    except Exception as e:
        logger.error(f"Error in start_multimon: {e}", exc_info=True)
        return False  # Returnér False ved fejl
    finally:
        if process and process.poll() is None:
            process.terminate()
            logger.info("Process terminated.")

    return True  # Returnér True, hvis alt kørte korrekt

def load_config():
    """
    Indlæser konfiguration fra config.txt.
    """
    cfg = configparser.ConfigParser()
    cfg.read('config.txt')
    return cfg

if __name__ == "__main__":
    if os.path.exists("/tmp/multimon.lock"):
        logger.error("Another instance of this script is already running. Exiting.")
        sys.exit(1)

    try:
        open("/tmp/multimon.lock", 'w').close()
        retry_count = 0  # Spor antallet af genstarter
        max_retries = 5  # Maksimalt antal forsøg før afslutning

        while retry_count < max_retries:
            try:
                cfg = load_config()
                logger.info("Starting multimon process...")
                success = start_multimon(cfg)
                if success:
                    logger.info("Multimon process completed successfully.")
                    break  # Afslut, hvis processen lykkes
                else:
                    retry_count += 1
                    logger.warning(f"Multimon process failed. Retry {retry_count}/{max_retries}...")
                    time.sleep(10)  # Vent før genstart

            except Exception as e:
                logger.error(f"Critical error: {e}", exc_info=True)

        if retry_count >= max_retries:
            logger.error("Maximum retry limit reached. Exiting.")
    finally:
        if os.path.exists("/tmp/multimon.lock"):
            os.remove("/tmp/multimon.lock")
            logger.info("Lock file removed. Exiting.")