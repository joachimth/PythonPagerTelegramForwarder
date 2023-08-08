import subprocess
import threading
import configparser

def run_script(script_name, port=None):
    if port:
        command = ["python", script_name, str(port)]
    else:
        command = ["python", script_name]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Fejl under kørsel af {script_name}!")
        print(result.stderr)
        exit(1)

def run_flask_app(port):
    run_script("flaskapp.py", port)

def main():
    # Læs porten fra config.txt
    config = configparser.ConfigParser()
    config.read('config.txt')
    flask_port = int(config['Flask']['port'])

    # Kører ppm kalibreringsscript først
    run_script("kal_automation.py")

    # Start Flask app i en ny tråd
    flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,))
    flask_thread.start()

    # Fortsæt med den normale udførelse
    run_script("app.py")

if __name__ == "__main__":
    main()
