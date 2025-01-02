import subprocess
import logging

def run_script(script_name, port=None):
    command = ["python", script_name]
    if port:
        command.append(str(port))

    #logging.info(f"Kører script: {' '.join(command)}")

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #logging.info(f"Output fra {script_name}:\n{result.stdout}")
        if result.returncode != 0:
            logging.error(f"Fejl under kørsel af {script_name}: {result.stderr}")
            return False
        return True
    except Exception as e:
        logging.error(f"Uventet fejl under kørsel af {script_name}: {e}")
        return False