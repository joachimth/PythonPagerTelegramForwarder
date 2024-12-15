import threading
import logging
import configparser
from script_runner import run_script

# Logger opsætning
logging.basicConfig(
    filename="initlog.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_flask_app(port):
    logging.info(f"Starter Flask-app på port {port}")
    run_script("flaskapp.py", port)

def main():
    try:
        config = configparser.ConfigParser()
        config.read("config.txt")
        flask_port = int(config["Flask"]["port"])

        # Start Flask-app
        flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,))
        flask_thread.start()

        # Kalibrering
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
    except Exception as e:
        logging.error(f"Fejl i init.py: {e}")

if __name__ == "__main__":
    main()