import subprocess
import re
import configparser
import os

def read_config_value(section, key, config_file="config.txt"):
    """Læser en værdi fra config-filen."""
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        return config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        raise ValueError(f"Værdi '{key}' i sektion '{section}' ikke fundet i {config_file}.")

def update_config_file(key, value, config_file="config.txt"):
    """Opdaterer en specifik værdi i config-filen."""
    config = configparser.ConfigParser()
    config.read(config_file)
    section = "rtl_fm"
    if section not in config.sections():
        config.add_section(section)
    config.set(section, key, str(value))
    
    with open(config_file, "w") as file:
        config.write(file)
    
    with open("kalrun.log", "a") as log_file:
        log_file.write(f"Updated {key} in {config_file} to {value}\n")

def run_command(command):
    """Kører en shell-kommando og logger output."""
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    log_output = (
        f"Executing: {command}\n"
        f"Output:\n{result.stdout}\n"
        f"Error:\n{result.stderr}\n"
        "-------------------------------------\n"
    )
    with open("kalrun.log", "a") as log_file:
        log_file.write(log_output)
    return result.stdout

def extract_channel_with_max_power(output):
    """Finder kanalen med den højeste power fra output."""
    pattern = r"chan:\s+(\d+).*?power:\s+([\d.]+)"
    matches = re.findall(pattern, output)
    if not matches:
        raise ValueError("Ingen kanaler fundet i output.")
    max_channel = max(matches, key=lambda x: float(x[1]))
    return max_channel[0]

def extract_absolute_error(output):
    """Ekstraherer gennemsnitlig absolut fejl i ppm fra output med to decimaler."""
    pattern = r"average absolute error:\s+([-\d.]+)\s*ppm"
    match = re.search(pattern, output)
    if not match:
        raise ValueError("Kan ikke finde 'average absolute error' i output.")
    return round(float(match.group(1)), 2)  # Bevar to decimaler

def extract_average_hz(output):
    """Ekstraherer gennemsnitsfrekvensfejl i Hz fra output."""
    pattern = r"\+\s*([\d.]+)\s*(k?Hz)"
    match = re.search(pattern, output)
    if not match:
        raise ValueError("Kan ikke finde 'average Hz' i output.")
    value = float(match.group(1))
    if match.group(2) == "kHz":  # Hvis værdien er i kHz, konverter til Hz
        value *= 1000
    return int(value)

def log_message(message):
    """Logger en besked til kalrun.log."""
    with open("kalrun.log", "a") as log_file:
        log_file.write(message + "\n")

def main():
    # Læs konfigurationen
    cfg = configparser.ConfigParser()
    cfg.read("config.txt")
    
    # Tjek om kalibrering er aktiveret
    if cfg.getboolean("kal", "enable_calibration"):
        logging.info("Kalibrering er aktiveret. Starter kalibreringsprocessen...")
        # Resten af kalibreringsprocessen
        try:
            gain = get_gain_from_config()
            gsmband = get_gsmband_from_config()
            first_command = f"kal -s {gsmband} -e 0 -g {gain}"
            output1 = run_command(first_command)
            channel = extract_channel_with_max_power(output1)
            second_command = f"kal -c {channel} -e 0 -g {gain}"
            output2 = run_command(second_command)
            error = extract_absolute_error(output2)
            third_command = f"kal -c {channel} -e {error} -g {gain}"
            output3 = run_command(third_command)
            avg_hz = extract_average_hz(output3)
            if avg_hz <= 750:
                logging.info(f"Kalibrering succesfuld: Gennemsnitlig fejl {avg_hz} Hz.")
                update_config_file(error)
            else:
                logging.warning(f"Kalibrering mislykkedes: Gennemsnitlig fejl {avg_hz} Hz.")
        except Exception as e:
            logging.error(f"Fejl under kalibrering: {e}")
    else:
        logging.info("Kalibrering er deaktiveret. Springer over.")

if __name__ == "__main__":
    main()