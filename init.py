import subprocess

def run_script(script_name):
    result = subprocess.run(["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Fejl under kørsel af {script_name}!")
        print(result.stderr)
        exit(1)

def main():
    # Kører ppm kalibreringsscript først
    run_script("kal_automation.py")

    # Derefter starter app.py
    run_script("app.py")

if __name__ == "__main__":
    main()
