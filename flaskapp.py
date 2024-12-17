from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import configparser
import os
import glob  # Sørg for, at glob er importeret
import logging

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("flaskapp_logger")

# Besked-dictionary
messages_dict = {}

# Indlæs konfiguration
config = configparser.ConfigParser()
config.read('config.txt')
flask_port = int(config['Flask']['port'])

# Flask setup
app = Flask(__name__)
app.secret_key = "yoursecretkey"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy brugerdata
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
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    local_config = configparser.ConfigParser()
    local_config.read('config.txt')

    if request.method == 'POST':
        try:
            for section in local_config.sections():
                for key in local_config[section]:
                    local_config[section][key] = request.form[f'{section}_{key}']
            with open('config.txt', 'w') as config_file:
                local_config.write(config_file)
            flash('Configuration saved successfully!', 'success')
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            flash('Error saving configuration!', 'danger')

    log_files = [log for log in glob.glob('**/*.log*', recursive=True) if os.path.getsize(log) > 0]
    return render_template('admin.html', config=local_config, log_files=log_files)

@app.route('/view_log/<filename>')
@login_required
def view_log(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
            return render_template('log.html', content=content)
        else:
            logger.warning(f"File {filename} does not exist.")
            return "Filen eksisterer ikke.", 404
    except Exception as e:
        logger.error(f"Error viewing log: {e}")
        return "En fejl opstod under visning af log.", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=flask_port, debug=True)