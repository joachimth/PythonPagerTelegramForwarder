from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import configparser
import os
import glob  # Sørg for, at glob er importeret
import sqlite3
import logging
import json

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("flaskapp_logger")

# Database placering
DB_PATH = "messages.db"

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

# Hjemmeside Route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login Route
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

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Admin Dashboard Route
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

# View Log Route
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

# Clear Log Route
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

# Latest Messages Route
@app.route('/latest_messages')
@login_required
def latest_messages():
    return render_template('latest_messages.html')

# Latest Messages JSON Route
@app.route('/latest_messages_json')
@login_required
def latest_messages_json():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, raw_message, parsed_fields
                FROM messages
                ORDER BY id DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()

            # Konverter resultater til JSON-venligt format
            messages = []
            for row in rows:
                message = {
                    "id": row[0],
                    "timestamp": row[1],
                    "raw_message": row[2],
                    "parsed_fields": json.loads(row[3]) if row[3] else None
                }
                messages.append(message)

            return jsonify({"messages": messages})
    except sqlite3.Error as e:
        logger.error(f"Database error fetching messages: {e}")
        return jsonify({"error": "Kunne ikke hente beskeder."}), 500

# Edit Message Parsing Route
@app.route('/edit_message_parsing', methods=['GET', 'POST'])
@login_required
def edit_message_parsing():
    try:
        if request.method == 'POST':
            # Håndter ændringer af eksisterende eller nye parsing-regler
            local_config = configparser.ConfigParser()
            local_config.read('config.txt')

            if 'MessageParsing' not in local_config:
                local_config.add_section('MessageParsing')

            for key, value in request.form.items():
                if key.startswith('key_'):
                    original_key = key.split('key_', 1)[1]
                    updated_value = request.form[f'value_{original_key}']
                    local_config.set('MessageParsing', original_key, updated_value)
                elif key == 'new_key' and value.strip():
                    new_value = request.form['new_value']
                    local_config.set('MessageParsing', value.strip(), new_value.strip())

            with open('config.txt', 'w') as config_file:
                local_config.write(config_file)
            flash('Parsing rules updated successfully.', 'success')

        return render_template('edit_message_parsing.html', message_parsing=config.items('MessageParsing'))
    except Exception as e:
        logger.error(f"Error editing message parsing: {e}")
        flash('Failed to update parsing rules.', 'danger')
        return redirect(url_for('admin'))

# Restart System Route
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