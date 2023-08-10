import subprocess
import re
import configparser
import sys
import os

def get_gain_from_config():
    with open("config.txt", "r") as file:
        content = file.readlines()
    
    for line in content:
        if "gain" in line:
            return line.split("=")[1].strip()
    raise ValueError("Gain værdi ikke fundet i config.txt.")

def update_config_file(new_ppm_error):
    with open("config.txt", "r") as file:
        content = file.read()

    # Finder og erstatter ppm_error linjen med den nye værdi
    content = re.sub(r"(ppm_error\s*=\s*)\d+", rf"\1{new_ppm_error}", content)

    with open("config.txt", "w") as file:
        file.write(content)

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    
    with open("kalrun.log", "a") as log_file:
        log_file.write(f"Executing: {command}\n")
        log_file.write("Output:\n")
        log_file.write(result.stdout)
        log_file.write("\nError:\n")
        log_file.write(result.stderr)
        log_file.write("\n-------------------------------------\n")

    return result.stdout

def extract_channel_with_max_power(output):
    pattern = r"chan:\s+(\d+)\s+\((\d+\.\d+)MHz\s+-\s+[\d.]+kHz\)\s+power:\s+([\d.]+)"
    matches = re.findall(pattern, output)
    if not matches:
        raise ValueError("Ingen kanaler fundet i output.")
    
    max_power_channel = max(matches, key=lambda x: float(x[2]))
    return max_power_channel[0]

def extract_absolute_error(output):
    pattern = r"average absolute error: ([\d.]+) ppm"
    match = re.search(pattern, output)
    if not match:
        raise ValueError("Kan ikke finde 'average absolute error' i output.")
    
    return round(float(match.group(1)))

def main():
    # Slet kalrun.log ved opstart, hvis den eksisterer
    if os.path.exists("kalrun.log"):
        os.remove("kalrun.log")
    
    try:
        gain = get_gain_from_config()
    except ValueError as e:
        print(f"Fejl: {e}")
        return
    
    first_command = f"kal -s GSM900 -e 0 -g {gain}"
    output1 = run_command(first_command)

    try:
        channel = extract_channel_with_max_power(output1)
    except ValueError as e:
        print(f"Fejl: {e}")
        return

    second_command = f"kal -c {channel} -e 0 -g {gain}"
    output2 = run_command(second_command)

    try:
        error = extract_absolute_error(output2)
    except ValueError as e:
        print(f"Fejl: {e}")
        return

    # Kører test igen med den fundne error som -e værdi
    third_command = f"kal -c {channel} -e {error} -g {gain}"
    output3 = run_command(third_command)

    try:
        new_error = extract_absolute_error(output3)
    except ValueError as e:
        print(f"Fejl: {e}")
        return

    if abs(new_error) <= 1:  # Antager her, at en error indenfor 1.0 ppm er tilnærmelsesvis 0.
        result_msg = "Success! Den nye error efter kalibrering er tilnærmelsesvis 0. Den afrundede fejl er {error} ppm. Derfor er config.txt også samtidig blevet opdateret."
        update_config_file(error)
    else:
        result_msg = f"Fejl! Den nye error efter kalibrering er {new_error} ppm, hvilket ikke er tæt på 0."

    print(result_msg)

    with open("kalrun.log", "a") as log_file:
        log_file.write(output1)
        log_file.write(output2)
        log_file.write(output3)
        log_file.write(result_msg + "\n")

if __name__ == "__main__":
    main()
