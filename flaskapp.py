from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
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
    log_files = [log for log in glob.glob('**/*.log', recursive=True) if os.path.getsize(log) > 0]
    
    return render_template('admin.html', config=config, log_files=log_files)



@app.route('/latest_messages_json', methods=['GET'])
@login_required
def latest_messages_json():
    # Returnerer de sidste 10 beskeder som JSON
    sorted_messages = sorted(messages_dict.values(), key=lambda x: x['besked.nr'], reverse=True)
    latest_ten = sorted_messages[:10]
    return {"messages": latest_ten}


@app.route('/latest_messages', methods=['GET'])
@login_required
def latest_messages():
    global messages_dict  # Brug den globale variabel
    if not messages_dict:  # Tjek om dictionary'en er tom
        flash("Ingen beskeder fundet!")
        return render_template('latest_messages.html', messages=[])  # Returner tom liste til skabelonen
    sorted_messages = sorted(messages_dict.values(), key=lambda x: x.get('besked.nr', 0), reverse=True)
    latest_ten = sorted_messages[:10]
    return render_template('latest_messages.html', messages=latest_ten)


@app.route('/edit_message_parsing', methods=['GET', 'POST'])
@login_required
def edit_message_parsing():
    if request.method == 'POST':
        # Opdater config.txt med nye værdier
        for key in request.form:
            section, option = key.split("_", 1)
            config[section][option] = request.form[key]
        with open('config.txt', 'w') as configfile:
            config.write(configfile)
        flash("Message parsing settings updated successfully!")

    return render_template('edit_message_parsing.html', config=config['MessageParsing'])



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
