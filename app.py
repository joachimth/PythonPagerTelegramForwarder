import sys
import subprocess
import collections
import configparser
from time import gmtime, strftime
from pytgbot import Bot
import os
import logging
from logging.handlers import RotatingFileHandler

def create_logger():
    logger = logging.getLogger('my_logger')
    handler = RotatingFileHandler('error.log', maxBytes=2000, backupCount=10)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = create_logger()

def start_multimon(cfg):
    prots = cfg.get('Frequencies', 'prot').split()
    prots = ' -a '.join(prots)
    if prots:
        prots = '-a ' + prots
    bot = Bot(cfg.get('Frequencies', 'tel_ID'))
    d = collections.deque(maxlen=100)
    call = "rtl_fm {} -d{} -f {} -s {} | multimon-ng -t raw {} -f alpha -t raw /dev/stdin -".format(cfg.get('rtl_fm', 'enable_option'), cfg.get('rtl_fm', 'device_index'), cfg.get('Frequencies', 'freq'), cfg.get('rtl_fm', 'sample_rate'), prots)
    print (call)
    mm = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
    decode_format = cfg.get('Encoding', 'encoding_format')
    fail_count = 0
    while mm.poll() is None:
        try:
            output = mm.stdout.readline().decode(decode_format)
            print (output)
            if "Alpha" not in output:
                continue
            output = output.replace("<NUL>", "")
            if output in d:
                continue
            d.append(output)
            msg = output.split("Alpha:", 1)[1]
            if int(len(msg)) < int(cfg.get('Frequencies', 'min_len')):
                continue
            time = strftime("%Y-%m-%d %H:%M", gmtime())
            print (msg)
            bot.send_message(cfg.get('Frequencies', 'rec_ID'), 'Time: ' + time + '\nMessage: ' + msg)
        except Exception as e:
            fail_count += 1
            logger.error("An error occurred: {}, Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
            if fail_count == 3:
                decode_format = 'utf-8'
                logger.error("Failed to decode message 3 times. Switching to utf-8 encoding.")
            continue

def load_config():
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
                start_multimon(cfg)
            except Exception as e:
                logger.error("An error occurred: {}, Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
            finally:
                if os.path.exists("/tmp/multimon.lock"):
                    os.remove("/tmp/multimon.lock")
    except Exception as e:
        logger.error("An error occurred: {}, Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
