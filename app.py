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

def create_logger():
    logger = logging.getLogger('my_logger')
    handler = RotatingFileHandler('error.log', maxBytes=8000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = create_logger()

def start_multimon(cfg):
    prots = cfg.get('multimon-ng', 'prot').split()
    prots = ' -a '.join(prots)
    if prots:
        prots = '-a ' + prots

    
    
    bot = Bot(os.getenv('TELEGRAM_API'))
    
    d = collections.deque(maxlen=100)

    
    call = "rtl_fm {} -d {} -l {} -g {} -p {} -f {} -s {} | multimon-ng -C {} -t raw {} -f alpha /dev/stdin -".format(cfg.get('rtl_fm', 'enable_option'), cfg.get('rtl_fm', 'device_index'), cfg.get('rtl_fm', 'squelch_level'), cfg.get('rtl_fm', 'gain'), cfg.get('rtl_fm', 'ppm_error'), cfg.get('Frequencies', 'freq'), cfg.get('rtl_fm', 'sample_rate'), cfg.get('multimon-ng','pocsag_charset'), prots)
    #        call = "rtl_fm -d0 -f "+freq+" -s 22050 | multimon-ng -t raw -a "+prot+" -f alpha -t raw /dev/stdin -"
    logger.info(f"sh call message: {call}")
    print (call)

    #error.log not working, simple hack to get content to file now..
    with open("multimon.log", "a") as log_file:
        log_file.write("\n-------------------------------------\n")
        log_file.write("Call message:\n")
        log_file.write(call)
        log_file.write("\n-------------------------------------\n")

    time = strftime("%Y-%m-%d %H:%M", gmtime())
    bot.send_message(os.getenv('TELEGRAM_REC') , 'Time: ' + time + '\nCall Message: ' + call)
    mm = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
    decode_format = cfg.get('Encoding', 'encoding_format')
    fail_count = 0
    while mm.poll() is None:
        try:
            output = mm.stdout.readline().decode(decode_format)
            print (output)
            logger.info(f"raw output: {output}")
            
            #error.log not working, simple hack to get content to file now..
            with open("multimon.log", "a") as log_file:
                log_file.write("RAW message:\n")
                log_file.write(output)
    
            if "Alpha" not in output:
                continue
            output = output.replace("<NUL>", "")
            if output in d:
                continue
            d.append(output)
            msg = output.split("Alpha:", 1)[1]
            if int(len(msg)) < int(cfg.get('multimon-ng', 'min_len')):
                continue
            time = strftime("%Y-%m-%d %H:%M", gmtime())
            print (msg)
            logger.info(f"msg: {msg}")
            chat_id = os.getenv('TELEGRAM_REC')
            logger.info(f"Chat ID: {chat_id}")
            #bot.send_message(chat_id, 'Time: ' + time + '\nMessage: ' + msg)

            #error.log not working, simple hack to get content to file now..
            with open("multimon.log", "a") as log_file:
                log_file.write("Final message:\n")
                log_file.write('Time: ' + time + '\nMessage: ' + msg)
            
            bot.send_message(os.getenv('TELEGRAM_REC') , 'Time: ' + time + '\nMessage: ' + msg)
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
        #sys.exit(1)
    try:
        open("/tmp/multimon.lock", 'w').close()
        while True:
            try:
                cfg = load_config()
                time.sleep(15)
                start_multimon(cfg)
            except Exception as e:
                logger.error("An error occurred: {}, Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
            finally:
                if os.path.exists("/tmp/multimon.lock"):
                    os.remove("/tmp/multimon.lock")
    except Exception as e:
        logger.error("An error occurred: {}, Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
