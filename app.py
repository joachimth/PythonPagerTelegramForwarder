import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from message_parser import parse_message_dynamic, format_message
from telegram_sender import TelegramSender
from message_receiver import fetch_latest_messages  # Import fra message_receiver

# Logger opsætning
def create_logger():
    """
    Opretter en logger til applikationen.
    """
    logger = logging.getLogger('app_logger')
    handler = RotatingFileHandler('app.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = create_logger()

def process_and_send_messages():
    """
    Henter de seneste beskeder fra `message_receiver` og sender dem til Telegram.
    """
    try:
        # Hent seneste beskeder
        messages = fetch_latest_messages()

        if not messages:
            logger.info("Ingen nye beskeder modtaget.")
            return

        for raw_message in messages:
            try:
                logger.info(f"Modtaget besked: {raw_message}")
                
                # Parse besked
                parsed_message = parse_message_dynamic(raw_message)
                formatted_message = format_message(parsed_message)

                # Send besked til Telegram
                #chat_id = os.getenv('TELEGRAM_REC')
                # Initialiser TelegramSender
                telegram_sender = TelegramSender()


                send_message_to_telegram(formatted_message)
                logger.info(f"Besked sendt til Telegram: {formatted_message}")

            except Exception as e:
                logger.error(f"Fejl under behandling af besked: {e}, Line: {sys.exc_info()[-1].tb_lineno}")

    except Exception as e:
        logger.error(f"Fejl under hentning af beskeder: {e}, Line: {sys.exc_info()[-1].tb_lineno}")

if __name__ == "__main__":
    """
    Hovedprogram til at hente beskeder og sende dem til Telegram.
    """
    logger.info("Starter app.py")
    try:
        while True:
            process_and_send_messages()
            time.sleep(5)  # Polling interval
    except KeyboardInterrupt:
        logger.info("App afsluttes af bruger.")
    except Exception as e:
        logger.error(f"Kritisk fejl i app.py: {e}, Line: {sys.exc_info()[-1].tb_lineno}")