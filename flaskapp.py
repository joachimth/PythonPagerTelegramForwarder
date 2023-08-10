from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import configparser
import os
import glob

config = configparser.ConfigParser()
config.read('config.txt')
flask_port = int(config['Flask']['port'])

app = Flask(__name__)
app.secret_key = "yoursecretkey"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user data - i en reel anvendelse bør en database benyttes
users = {'joachimth@nowhere.com': {'password': 'changeme'}}

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return
    user = User()
    user.id = email
    return user

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        if (email in users) and (request.form['password'] == users[email]['password']):
            user = User()
            user.id = email
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    # Load data from config.txt
    local_config = configparser.ConfigParser()
    local_config.read('config.txt')

    if request.method == 'POST':
        # Handle form submission to update config.txt here
        for section in local_config.sections():
            for key in local_config[section]:
                local_config[section][key] = request.form[f'{section}_{key}']
        with open('config.txt', 'w') as config_file:
            local_config.write(config_file)
        flash('Configuration saved successfully!')
    
    # Henter alle .log filer
    log_files = glob.glob('**/*.log', recursive=True)
    
    return render_template('admin.html', config=config, log_files=log_files)

@app.route('/view_log/<filename>')
@login_required
def view_log(filename):
        # Slet kalrun.log ved opstart, hvis den eksisterer
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
        return render_template('log.html', content=content)
    else:
        print(f"Filen: {filename} eksisterer ikke")
        return "Filen eksisterer ikke.."

@app.route('/clear_log/<filename>')
@login_required
def clear_log(filename):
    with open(filename, 'w') as f:
        f.write("")
    flash(f'Log {filename} cleared.')
    return redirect(url_for('admin'))

@app.route('/restart_system')
@login_required
def restart_system():
    # This is a pseudo implementation, update to suit your needs
    os.system('reboot')
    return "System Restarting..."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=flask_port, debug=True)  # Sæt host til '0.0.0.0' for at tillade eksterne forbindelser til containeren
