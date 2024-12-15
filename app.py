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

def create_logger():
    """
    Opretter logger til applikationen med INFO-niveau som standard.
    """
    logger = logging.getLogger('my_logger')
    handler = RotatingFileHandler('app.log', maxBytes=8000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # Indstil logniveau til INFO
    return logger

logger = create_logger()

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

    call = (
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
    logger.info(f"Command executed: {call}")

    time_str = strftime("%Y-%m-%d %H:%M", gmtime())
    bot.send_message(os.getenv('TELEGRAM_REC'), f"Time: {time_str}\nCall Message: {call}")

    mm = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
    decode_format = cfg.get('Encoding', 'encoding_format')
    fail_count = 0

    while mm.poll() is None:
        try:
            output = mm.stdout.readline().decode(decode_format).strip()
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

            # Parse besked og send til Telegram
            parsed_message = parse_message_dynamic(msg, cfg)
            formatted_message = format_message(parsed_message)

            chat_id = os.getenv('TELEGRAM_REC')
            logger.info(f"Sending to Chat ID: {chat_id}")

            bot.send_message(chat_id, formatted_message)
            logger.info(f"Final parsed message: {formatted_message}")

        except Exception as e:
            fail_count += 1
            logger.error(f"Error occurred: {e}, Line: {sys.exc_info()[-1].tb_lineno}")
            if fail_count == 3:
                decode_format = 'utf-8'
                logger.error("Failed to decode message 3 times. Switching to utf-8 encoding.")
            continue

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
        while True:
            try:
                cfg = load_config()
                time.sleep(15)
                start_multimon(cfg)
            except Exception as e:
                logger.error(f"An error occurred: {e}, Line: {sys.exc_info()[-1].tb_lineno}")
            finally:
                if os.path.exists("/tmp/multimon.lock"):
                    os.remove("/tmp/multimon.lock")
    except Exception as e:
        logger.error(f"Critical error: {e}, Line: {sys.exc_info()[-1].tb_lineno}")