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
    # Slet kalrun.log ved opstart
    if os.path.exists("kalrun.log"):
        os.remove("kalrun.log")

    try:
        gain = read_config_value("rtl_fm", "gain")
        gsmband = read_config_value("kal", "gsmband")
    except ValueError as e:
        log_message(f"Konfigurationsfejl: {e}")
        return

    # Find kanal med maksimal styrke
    try:
        command1 = f"kal -s {gsmband} -e 0 -g {gain}"
        output1 = run_command(command1)
        channel = extract_channel_with_max_power(output1)
    except ValueError as e:
        log_message(f"Fejl under første kommando: {e}")
        return

    # Udfør kalibrering på den valgte kanal
    try:
        command2 = f"kal -c {channel} -e 0 -g {gain}"
        output2 = run_command(command2)
        error_ppm = extract_absolute_error(output2)  # Bevarer to decimaler
    except ValueError as e:
        log_message(f"Fejl under anden kommando: {e}")
        return

    # Test med ny ppm-fejl og beregn gennemsnitsfejl i Hz
    try:
        command3 = f"kal -c {channel} -e {error_ppm} -g {gain}"
        output3 = run_command(command3)
        avg_hz = extract_average_hz(output3)
    except ValueError as e:
        log_message(f"Fejl under tredje kommando: {e}")
        return

    # Vurder resultaterne
    tolerance_hz = 750  # Hæv tolerancen til 750 Hz
    if avg_hz <= tolerance_hz:
        success_message = f"Kalibrering succesfuld: {avg_hz} Hz fejl (acceptablet)."
        update_config_file("ppm_error", error_ppm)
    else:
        success_message = f"Kalibrering fejlede: {avg_hz} Hz fejl (ikke acceptablet)."

    # Log resultatet
    log_message(f"Final PPM Error: {error_ppm}")
    log_message(f"Final Average Hz Error: {avg_hz} Hz")
    log_message(success_message)

if __name__ == "__main__":
    main()