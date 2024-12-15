from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import configparser
import os
import glob
from message_parser import load_config, messages_dict, insert_example_messages

# Global konfiguration og beskeder
config = load_config()
if not messages_dict:
    insert_example_messages(config)

flask_port = int(config['Flask']['port'])

app = Flask(__name__)
app.secret_key = "yoursecretkey"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user data
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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    local_config = configparser.ConfigParser()
    local_config.read('config.txt')

    if request.method == 'POST':
        for section in local_config.sections():
            for key in local_config[section]:
                local_config[section][key] = request.form[f'{section}_{key}']
        with open('config.txt', 'w') as config_file:
            local_config.write(config_file)
        flash('Configuration saved successfully!')

    log_files = [log for log in glob.glob('**/*.log*', recursive=True) if os.path.getsize(log) > 0]

    return render_template('admin.html', config=config, log_files=log_files)

@app.route('/latest_messages', methods=['GET'])
@login_required
def latest_messages():
    global messages_dict
    if not messages_dict:
        flash("Ingen beskeder fundet!")
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
    sorted_messages = sorted(messages_dict.values(), key=lambda x: x.get('besked.nr', 0), reverse=True)
    latest_ten = sorted_messages[:10]
    return jsonify({"messages": latest_ten})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=flask_port, debug=True)