from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import configparser
import os
import glob
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

@app.route('/latest_messages', methods=['GET'])
@login_required
def latest_messages():
    global messages_dict
    if not messages_dict:
        flash("Ingen beskeder fundet!", "info")
        return render_template('latest_messages.html', messages=[])
    sorted_messages = sorted(messages_dict.values(), key=lambda x: x.get('besked.nr', 0), reverse=True)
    latest_ten = sorted_messages[:10]
    return render_template('latest_messages.html', messages=latest_ten)

@app.route('/latest_messages_json', methods=['GET'])
@login_required
def latest_messages_json():
    global messages_dict
    if not messages_dict:
        return jsonify({"messages": []})

    try:
        sorted_messages = sorted(messages_dict.values(), key=lambda x: x.get('besked.nr', 0), reverse=True)
        latest_ten = sorted_messages[:10]
        return jsonify({"messages": latest_ten})
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return jsonify({"error": "Kunne ikke hente beskeder. Prøv igen senere."}), 500

@app.route('/edit_message_parsing', methods=['GET', 'POST'])
@login_required
def edit_message_parsing():
    """
    Side til redigering af MessageParsing-sektionen i config.txt.
    """
    if request.method == 'POST':
        try:
            if 'new_key' in request.form and 'new_value' in request.form:
                new_key = request.form['new_key']
                new_value = request.form['new_value']

                # Tjek om sektionen findes, ellers opret den
                if 'MessageParsing' not in config.sections():
                    config.add_section('MessageParsing')

                # Tilføj ny nøgle og værdi
                config.set('MessageParsing', new_key, new_value)

            # Opdater eksisterende nøgler
            for key, value in request.form.items():
                if key.startswith('key_'):
                    original_key = key.split('key_', 1)[1]
                    updated_value = request.form[f'value_{original_key}']
                    config.set('MessageParsing', original_key, updated_value)

            # Gem ændringer i config.txt
            with open('config.txt', 'w') as configfile:
                config.write(configfile)

            flash("Message parsing settings updated successfully!", "success")
        except Exception as e:
            logger.error(f"Error updating MessageParsing: {e}")
            flash("Failed to update MessageParsing settings!", "danger")

    # Indlæs eksisterende nøgler og værdier fra MessageParsing
    message_parsing = config.items('MessageParsing') if 'MessageParsing' in config.sections() else []
    return render_template('edit_message_parsing.html', message_parsing=message_parsing)

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

@app.route('/clear_log/<filename>')
@login_required
def clear_log(filename):
    try:
        with open(filename, 'w') as f:
            f.write("")
        flash(f'Log {filename} cleared.', 'success')
    except Exception as e:
        logger.error(f"Error clearing log {filename}: {e}")
        flash(f'Error clearing log {filename}.', 'danger')
    return redirect(url_for('admin'))

@app.route('/restart_system')
@login_required
def restart_system():
    try:
        os.system('reboot')
        flash("Systemet genstarter...", 'info')
        return redirect(url_for('admin'))
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        flash("Fejl under systemgenstart!", 'danger')
        return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=flask_port, debug=True)