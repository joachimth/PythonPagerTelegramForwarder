import threading
import logging
import configparser
import os
from time import sleep
from script_runner import run_script
import telegram_sender

# Logger opsætning
LOG_FILE = "initlog.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log til fil
        logging.StreamHandler()        # Log til konsol
    ]
)
logger = logging.getLogger("init")

DB_PATH = "messages.db"

def initialize_database_if_missing():
    """
    Tjekker om databasen eksisterer og initialiserer den, hvis den mangler.
    """
    if not os.path.exists(DB_PATH):
        logger.info(f"Databasen '{DB_PATH}' mangler. Initialiserer...")
        if not run_script("initialize_database.py"):
            logger.error("Initialisering af databasen fejlede.")
            raise RuntimeError("Kunne ikke initialisere databasen.")
        logger.info(f"Databasen '{DB_PATH}' er blevet initialiseret.")
    else:
        logger.info(f"Databasen '{DB_PATH}' eksisterer allerede.")

def run_flask_app(port):
    """
    Starter Flask-applikationen.
    """
    logger.info(f"Starter Flask-app på port {port}")
    if not run_script("flaskapp.py", port):
        logger.error("Flask-app fejlede.")

def run_message_receiver():
    """
    Kører message_receiver.py.
    """
    logger.info("Starter program: message_receiver.py")
    if not run_script("message_receiver.py"):
        logger.error("message_receiver.py fejlede.")

def run_message_parser():
    """
    Kører message_parser.py i et løbende loop for at parse nye beskeder.
    """
    logger.info("Starter program: message_parser.py")
    while True:
        try:
            if not run_script("message_parser.py"):
                logger.error("message_parser.py fejlede.")
            try:
                process_unsent_messages()
            except Exception as e:
                logger.error(f"Fejl i Telegram sender kontrol loop: {e}")
            threading.Event().wait(30)  # Kontrollér hvert 30. sekund
        except Exception as e:
            logger.error(f"Fejl i message_parser loop: {e}")
            sleep(30)  # Vent længere ved fejl

def run_telegram_sender():
    """
    Starter en loop, der regelmæssigt kontrollerer og sender nye beskeder.
    """
    logger.info("Starter Telegram sender kontrol loop.")
    while True:
        try:
            process_unsent_messages()
            sleep(10)  # Kontroller hvert 10. sekund
        except Exception as e:
            logger.error(f"Fejl i Telegram sender kontrol loop: {e}")
            sleep(30)  # Vent længere ved fejl

def main():
    """
    Hovedfunktion til at starte Flask-app, kalibreringsscript, initialisere database og køre hovedprogrammer.
    """
    try:
        config = configparser.ConfigParser()
        config.read("config.txt")
        flask_port = int(config["Flask"]["port"])

        # Tjek og initialiser database, hvis den mangler
        initialize_database_if_missing()

        # Start Flask-app i en separat tråd
        flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,), daemon=True)
        flask_thread.start()

        # Kør kalibreringsscriptet
        enable_calibration = config.getboolean("kal", "enable_calibration", fallback=True)
        if enable_calibration:
            logger.info("Kører kalibreringsscript...")
            if not run_script("kal_automation.py"):
                logger.error("Kalibreringsscriptet fejlede.")
        else:
            logger.info("Kalibreringsscriptet er deaktiveret i config.txt.")

        # Start message_receiver efter kalibreringsscriptet
        receiver_thread = threading.Thread(target=run_message_receiver, daemon=True)
        receiver_thread.start()

        # Start message_parser i en separat tråd
        parser_thread = threading.Thread(target=run_message_parser, daemon=True)
        parser_thread.start()

        # Start Telegram sender i separat tråd
        #telegram_thread = threading.Thread(target=run_telegram_sender, daemon=True)
        #telegram_thread.start()

        # Hold hovedtråden kørende
        flask_thread.join()
        receiver_thread.join()
        parser_thread.join()
        #telegram_thread.join()

    except Exception as e:
        logger.error(f"Fejl i init.py: {e}")

if __name__ == "__main__":
    main()