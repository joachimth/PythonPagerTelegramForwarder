import threading
import logging
import configparser
import os
from script_runner import run_script

# Logger opsætning
logging.basicConfig(
    filename="initlog.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "messages.db"

def initialize_database_if_missing():
    """
    Tjekker om databasen eksisterer og initialiserer den, hvis den mangler.
    """
    if not os.path.exists(DB_PATH):
        logging.info(f"Databasen '{DB_PATH}' mangler. Initialiserer...")
        if not run_script("initialize_database.py"):
            logging.error("Initialisering af databasen fejlede.")
            raise RuntimeError("Kunne ikke initialisere databasen.")
        logging.info(f"Databasen '{DB_PATH}' er blevet initialiseret.")
    else:
        logging.info(f"Databasen '{DB_PATH}' eksisterer allerede.")

def run_flask_app(port):
    """
    Starter Flask-applikationen.
    """
    logging.info(f"Starter Flask-app på port {port}")
    if not run_script("flaskapp.py", port):
        logging.error("Flask-app fejlede.")

def run_message_receiver():
    """
    Kører message_receiver.py.
    """
    logging.info("Starter program: message_receiver.py")
    if not run_script("message_receiver.py"):
        logging.error("message_receiver.py fejlede.")

def run_message_parser():
    """
    Kører message_parser.py.
    """
    logging.info("Starter program: message_parser.py")
    while True:
        if not run_script("message_parser.py"):
            logging.error("message_parser.py fejlede.")
        #else:
            #logging.info("message_parser.py afsluttede korrekt.")
        # Kontrollér hvert 30. sekund for nye beskeder at parse
        #logging.info("Venter 30 sekunder før næste parsing.")
        threading.Event().wait(30)

def run_telegram_sender():
    """
    Starter en loop, der regelmæssigt kontrollerer og sender nye beskeder.
    """
    logging.info("Starter Telegram sender kontrol loop.")
    telegram_sender = TelegramSender()
    while True:
        try:
            telegram_sender.process_unsent_messages()
            sleep(10)  # Kontroller hvert 10. sekund
        except Exception as e:
            logging.error(f"Fejl i Telegram sender kontrol loop: {e}")
            sleep(30)  # Vent længere, hvis der opstår en fejl


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
        flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,))
        flask_thread.start()

        # Kør kalibreringsscriptet
        enable_calibration = config.getboolean("kal", "enable_calibration", fallback=True)
        if enable_calibration:
            logging.info("Kører kalibreringsscript...")
            if not run_script("kal_automation.py"):
                logging.error("Kalibreringsscriptet fejlede.")
        else:
            logging.info("Kalibreringsscriptet er deaktiveret i config.txt.")

        # Start message_receiver efter kalibreringsscriptet
        receiver_thread = threading.Thread(target=run_message_receiver)
        receiver_thread.start()

        # Start message_parser i en separat tråd
        parser_thread = threading.Thread(target=run_message_parser)
        parser_thread.start()

        # Start Telegram sender i separat tråd
        telegram_thread = threading.Thread(target=run_telegram_sender)
        telegram_thread.start()


        # Hold hovedtråden kørende
        flask_thread.join()
        receiver_thread.join()
        parser_thread.join()
        telegram_thread.join()

    except Exception as e:
        logging.error(f"Fejl i init.py: {e}")

if __name__ == "__main__":
    main()
