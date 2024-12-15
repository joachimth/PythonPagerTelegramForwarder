import subprocess
import threading
import configparser
import logging

# Konfigurer logger til at skrive til en initlog-fil
logging.basicConfig(
    filename="initlog.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_script(script_name, port=None):
    """
    Kører et Python-script med en valgfri port som argument.
    Logger output og fejl til initlog.
    """
    command = ["python", script_name]
    if port:
        command.append(str(port))

    logging.info(f"Kører script: {' '.join(command)}")

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(f"Output fra {script_name}:\n{result.stdout}")
        if result.returncode != 0:
            logging.error(f"Fejl under kørsel af {script_name}: {result.stderr}")
            exit(1)
    except Exception as e:
        logging.error(f"Uventet fejl under kørsel af {script_name}: {e}")
        exit(1)

def run_flask_app(port):
    """
    Starter Flask-applikationen i en separat tråd.
    """
    logging.info(f"Starter Flask-app på port {port}")
    run_script("flaskapp.py", port)

def main():
    """
    Hovedfunktion til at starte Flask-app, køre kalibrering og derefter hovedprogram.
    """
    try:
        # Læs porten fra config.txt
        config = configparser.ConfigParser()
        config.read("config.txt")
        flask_port = int(config["Flask"]["port"])

        # Start Flask-app i en ny tråd
        flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,))
        flask_thread.start()
        logging.info("Flask-app tråd startet.")

        # Kør kalibreringsscript, hvis det er aktiveret i config.txt
        enable_calibration = config.getboolean("kal", "enable_calibration", fallback=True)
        if enable_calibration:
            logging.info("Kalibreringsscript er aktiveret. Kører kal_automation.py...")
            run_script("kal_automation.py")
        else:
            logging.info("Kalibreringsscript er deaktiveret i config.txt.")

        # Kør hovedprogram
        logging.info("Starter hovedprogram: app.py")
        run_script("app.py")

    except Exception as e:
        logging.error(f"Fejl i init.py: {e}")
        exit(1)

if __name__ == "__main__":
    main()