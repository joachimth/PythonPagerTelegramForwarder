from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
import logging
import json
import configparser
import os

# Logger opsætning
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("flaskapp")

DB_PATH = "messages.db"
CONFIG_PATH = "config.txt"

app = Flask(__name__)
app.secret_key = "yoursecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Dummy brugerdata
users = {"joachimth@nowhere.com": {"password": "changeme"}}

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return
    user = User()
    user.id = email
    return user

# Hjemmeside
@app.route("/")
def home():
    return redirect(url_for("login"))

# Login side
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        if email in users and request.form["password"] == users[email]["password"]:
            user = User()
            user.id = email
            login_user(user)
            return redirect(url_for("admin"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

# Logout rute
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# Admin dashboard
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    if request.method == "POST":
        try:
            for section in config.sections():
                for key in config[section]:
                    config[section][key] = request.form[f"{section}_{key}"]
            with open(CONFIG_PATH, "w") as config_file:
                config.write(config_file)
            flash("Configuration updated successfully!", "success")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            flash("Failed to update configuration!", "danger")

    log_files = [log for log in os.listdir(".") if log.endswith(".log")]
    return render_template("admin.html", config=config, log_files=log_files)

# Seneste beskeder JSON
@app.route("/latest_messages_json")
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

            messages = [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "raw_message": row[2],
                    "parsed_fields": json.loads(row[3]) if row[3] else None
                }
                for row in rows
            ]
            return jsonify({"messages": messages})
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Could not retrieve messages."}), 500

# Seneste beskeder side
@app.route("/latest_messages")
@login_required
def latest_messages():
    return render_template("latest_messages.html")

# Log visning
@app.route("/view_log/<filename>")
@login_required
def view_log(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as file:
                content = file.read()
            return render_template("log.html", content=content)
        flash("File does not exist.", "danger")
        return redirect(url_for("admin"))
    except Exception as e:
        logger.error(f"Error viewing log: {e}")
        flash("An error occurred while reading the log file.", "danger")
        return redirect(url_for("admin"))

# Log rydning
@app.route("/clear_log/<filename>")
@login_required
def clear_log(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "w") as file:
                file.write("")
            flash(f"Log {filename} cleared.", "success")
        else:
            flash(f"Log {filename} does not exist.", "danger")
    except Exception as e:
        logger.error(f"Error clearing log {filename}: {e}")
        flash(f"An error occurred while clearing the log.", "danger")
    return redirect(url_for("admin"))

# Redigering af parsing regler
@app.route("/edit_message_parsing", methods=["GET", "POST"])
@login_required
def edit_message_parsing():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    if request.method == "POST":
        try:
            if "new_key" in request.form and "new_value" in request.form:
                new_key = request.form["new_key"]
                new_value = request.form["new_value"]

                if "MessageParsing" not in config.sections():
                    config.add_section("MessageParsing")

                config.set("MessageParsing", new_key, new_value)

            for key, value in request.form.items():
                if key.startswith("key_"):
                    original_key = key.split("key_", 1)[1]
                    updated_value = request.form[f"value_{original_key}"]
                    config.set("MessageParsing", original_key, updated_value)

            with open(CONFIG_PATH, "w") as configfile:
                config.write(configfile)

            flash("Message parsing rules updated successfully!", "success")
        except Exception as e:
            logger.error(f"Error updating MessageParsing: {e}")
            flash("Failed to update MessageParsing settings!", "danger")

    message_parsing = config.items("MessageParsing") if "MessageParsing" in config.sections() else []
    return render_template("edit_message_parsing.html", message_parsing=message_parsing)

# System genstart
@app.route("/restart_system")
@login_required
def restart_system():
    try:
        os.system("reboot")
        flash("System is restarting...", "info")
        return redirect(url_for("admin"))
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        flash("Failed to restart system!", "danger")
        return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)