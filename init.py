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
    run_script("flaskapp.py", port)

def main():
    """
    Hovedfunktion til at starte Flask-app, kalibreringsscript, initialisere database og køre hovedprogram.
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

        # Kalibreringsscript
        enable_calibration = config.getboolean("kal", "enable_calibration", fallback=True)
        if enable_calibration:
            logging.info("Kører kalibreringsscript...")
            if not run_script("kal_automation.py"):
                logging.error("Kalibreringsscriptet fejlede.")
                return

        # Hovedprogram
        logging.info("Starter hovedprogram: app.py")
        if not run_script("app.py"):
            logging.error("Hovedprogrammet fejlede.")
        
        # message_receiver.py
        logging.info("Starter program: message_receiver.py")
        if not run_script("message_receiver.py"):
            logging.error("message_receiver.py fejlede.")


    except Exception as e:
        logging.error(f"Fejl i init.py: {e}")

if __name__ == "__main__":
    main()