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
    Udtræk gennemsnitlig frekvensfejl i Hz fra kalibreringskommandoens output.
    """
    try:
        pattern = r"average\s+([\d.-]+)\s+Hz"
        match = re.search(pattern, output)
        if match:
            avg_hz = float(match.group(1))
            logging.info(f"Fundet gennemsnitlig fejl: {avg_hz:.2f} Hz")
            return avg_hz
        else:
            logging.error("Ingen gennemsnitlig fejl fundet i output.")
            return None
    except Exception as e:
        logging.error(f"Fejl under udtrækning af gennemsnitlig fejl: {e}")
        return None

def main():
    """
    Hovedprogrammet for kalibrering.
    """
    logging.info("Starter kalibreringsproces...")

    config = configparser.ConfigParser()
    config.read("config.txt")

    # Kontroller om kalibrering er aktiveret
    enable_calibration = get_config_value(config, "kal", "enable_calibration", "false").lower() == "true"
    if not enable_calibration:
        logging.info("Kalibrering er deaktiveret. Afslutter.")
        return

    gain = get_config_value(config, "rtl_fm", "gain", "42")
    gsmband = get_config_value(config, "kal", "gsmband", "GSM900")

    # Første kommando for scanning
    command_scan = f"kal -s {gsmband} -e 0 -g {gain}"
    scan_output = run_command(command_scan)

    # Find kanal med maksimal styrke
    channel = extract_channel_with_max_power(scan_output)
    if not channel:
        logging.error("Ingen kanal fundet. Afslutter kalibrering.")
        return

    # Anden kommando for initial kalibrering
    command_calibrate = f"kal -c {channel} -e 0 -g {gain}"
    calibrate_output = run_command(command_calibrate)

    # Udtræk absolut fejl
    absolute_error = extract_absolute_error(calibrate_output)
    if absolute_error is None:
        logging.error("Absolut fejl ikke fundet. Afslutter kalibrering.")
        return

    # Tredje kommando for endelig kalibrering med funden absolut fejl
    command_final_calibrate = f"kal -c {channel} -e {absolute_error:.2f} -g {gain}"
    final_output = run_command(command_final_calibrate)

    # Udtræk gennemsnitlig fejl i Hz
    avg_hz = extract_average_hz(final_output)
    if avg_hz is None:
        logging.error("Gennemsnitlig fejl ikke fundet. Afslutter kalibrering.")
        return

    # Tjek om gennemsnitlig fejl er acceptabel
    if avg_hz <= 750:
        logging.info(f"Kalibrering succesfuld med gennemsnitlig fejl: {avg_hz:.2f} Hz.")
        update_config_value(config, "rtl_fm", "ppm_error", f"{absolute_error:.2f}")
    else:
        logging.warning(f"Kalibrering mislykkedes. Gennemsnitlig fejl: {avg_hz:.2f} Hz overstiger 750 Hz.")

if __name__ == "__main__":
    main()