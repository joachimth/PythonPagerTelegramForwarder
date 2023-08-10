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

def extract_average_hz(output):
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if "average" in line:
            try:
                # Forventer, at den næste linje indeholder Hz-værdien
                hz_line = lines[i + 1].strip().split()
                print(f"hz_line: {hz_line}")
                # Håndter negativ værdi
                #is_negative = hz_line[0].startswith('-')
                value_str = hz_line[0].replace("kHz", "").replace("Hz", "").replace("-", "").replace(" ", "")
                print(f"value_str: {value_str}")
                if "kHz" in hz_line[1]:
                    value = int(float(value_str) * 1000)  # konverter kilohertz til hertz
                else:
                    value = int(value_str)
                
                #if is_negative:
                    #value = -value
                
                return value
            except IndexError:
                raise ValueError("Kan ikke finde 'average Hz' i output.")
    raise ValueError("Kan ikke finde 'average Hz' i output.")

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
        avg_hz = extract_average_hz(output3)
    except ValueError as e:
        print(f"Fejl: {e}")
        return

    if 0 = avg_hz <= 500:
        result_msg = f"Success! Den gennemsnitlige fejl efter kalibrering er {avg_hz} Hz, hvilket er indenfor det acceptable interval. Den endelige fejlværdi bliver derfor {error} ppm."
        update_config_file(error)
    else:
        result_msg = f"Fejl! Den gennemsnitlige fejl efter kalibrering er {avg_hz} Hz, hvilket ikke er indenfor det acceptable interval."

    print(result_msg)

    with open("kalrun.log", "a") as log_file:
        log_file.write(output1)
        log_file.write(output2)
        log_file.write(output3)
        log_file.write(result_msg + "\n")

if __name__ == "__main__":
    main()
