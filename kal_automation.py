import subprocess
import re
import logging
import configparser
import os

# Opsætning af logging
logging.basicConfig(
    filename="kalibration.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_config_value(config, section, key, default=None):
    """
    Hent en værdi fra config-filen med standardværdi.
    """
    try:
        return config.get(section, key)
    except Exception as e:
        logging.warning(f"Kunne ikke hente værdien {key} fra sektionen {section}: {e}")
        return default

def update_config_value(config, section, key, value, config_file='config.txt'):
    """
    Opdater en værdi i config-filen og gem ændringer.
    """
    try:
        if section not in config.sections():
            config.add_section(section)
        config.set(section, key, value)
        with open(config_file, 'w') as file:
            config.write(file)
        logging.info(f"Opdaterede {key} i sektionen {section} med værdien {value}")
    except Exception as e:
        logging.error(f"Fejl under opdatering af config-fil: {e}")

def run_command(command):
    """
    Kør en shell-kommando og returnér dens output.
    """
    try:
        logging.info(f"Kører kommando: {command}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode != 0:
            logging.error(f"Fejl under udførelse af kommando: {command}\n{result.stderr}")
        return result.stdout
    except Exception as e:
        logging.error(f"Fejl under kørsel af kommando: {e}")
        return ""

def extract_channel_with_max_power(output):
    """
    Udtræk kanalen med maksimal styrke fra kal output.
    """
    try:
        pattern = r"chan:\s+(\d+)\s+\(.*?\)\s+power:\s+([\d.]+)"
        matches = re.findall(pattern, output)
        if matches:
            max_channel = max(matches, key=lambda x: float(x[1]))
            logging.info(f"Fundet kanal med maksimal styrke: {max_channel[0]}")
            return max_channel[0]
        else:
            logging.error("Ingen kanaler fundet i output.")
            return None
    except Exception as e:
        logging.error(f"Fejl under udtrækning af kanal med maksimal styrke: {e}")
        return None

def extract_absolute_error(output):
    """
    Udtræk absolut fejl i ppm fra kalibreringskommandoens output.
    """
    try:
        pattern = r"average absolute error: ([\d.-]+) ppm"
        match = re.search(pattern, output)
        if match:
            error_value = float(match.group(1))
            logging.info(f"Fundet absolut fejl: {error_value:.2f} ppm")
            return error_value
        else:
            logging.error("Ingen absolut fejl fundet i output.")
            return None
    except Exception as e:
        logging.error(f"Fejl under udtrækning af absolut fejl: {e}")
        return None

def extract_average_hz(output):
    """
    Ekstraherer gennemsnitlig fejl (Hz) fra output.
    """
    logging.info(f"Analyserer output:\n{output}")
    try:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "average" in line.lower():
                # Forventer, at næste linje indeholder Hz-værdien
                try:
                    hz_line = lines[i + 1].strip()
                    logging.info(f"Fundet linje med Hz: {hz_line}")
                    hz_value = re.search(r"([\d.-]+)\s*(k?Hz)", hz_line)
                    if hz_value:
                        value, unit = hz_value.groups()
                        value = float(value)
                        if unit == "kHz":
                            value *= 1000  # Konverter kHz til Hz
                        return int(value)
                except IndexError:
                    logging.error("Ingen linje efter 'average' i output.")
    except Exception as e:
        logging.error(f"Fejl under parsing af gennemsnitlig fejl: {e}", exc_info=True)

    logging.error("Ingen gennemsnitlig fejl fundet i output.")
    return None

def main():
    """
    Hovedfunktionen for kalibrering.
    """
    try:
        # Indlæs konfiguration
        cfg = load_config()

        # Indlæs nødvendige parametre fra config
        gsmband = cfg.get("kal", "gsmband")
        gain = cfg.get("rtl_fm", "gain")

        logging.info("Starter kalibreringsproces...")

        # Kør første kommando for at finde kanal med maksimal signalstyrke
        first_command = f"kal -s {gsmband} -e 0 -g {gain}"
        output1 = run_command(first_command)
        channel = extract_channel_with_max_power(output1)
        if not channel:
            logging.error("Kunne ikke finde kanal med maksimal signalstyrke.")
            return

        logging.info(f"Fundet kanal med maksimal styrke: {channel}")

        # Kør anden kommando for at finde absolut fejl
        second_command = f"kal -c {channel} -e 0 -g {gain}"
        output2 = run_command(second_command)
        absolute_error = extract_absolute_error(output2)
        if absolute_error is None:
            logging.error("Kunne ikke finde absolut fejl.")
            return

        logging.info(f"Fundet absolut fejl: {absolute_error:.2f} ppm")

        # Kør tredje kommando med den fundne fejl for at finde gennemsnitlig fejl
        third_command = f"kal -c {channel} -e {absolute_error:.2f} -g {gain}"
        output3 = run_command(third_command)
        average_hz = extract_average_hz(output3)
        if average_hz is None:
            logging.error("Ingen gennemsnitlig fejl fundet. Afslutter kalibrering.")
            return

        # Valider gennemsnitlig fejl
        if average_hz <= 750:
            logging.info(f"Kalibrering succesfuld! Gennemsnitlig fejl: {average_hz} Hz")
            update_config_file(absolute_error)
        else:
            logging.warning(f"Gennemsnitlig fejl {average_hz} Hz overskrider grænsen på 750 Hz. Kalibrering mislykkedes.")

    except Exception as e:
        logging.error(f"Uventet fejl under kalibrering: {e}", exc_info=True)

if __name__ == "__main__":
    main()