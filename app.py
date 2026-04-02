from flask import Flask, render_template, request, redirect, session
import os
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

CONFIG_FILE = "config.json"
LOG_DIR = "logs"

USERNAME = "admin"
PASSWORD = "padel123"


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def list_logs():
    if not os.path.exists(LOG_DIR):
        return []

    files = sorted(os.listdir(LOG_DIR), reverse=True)
    return files


def load_log(filename):
    path = os.path.join(LOG_DIR, filename)

    if not os.path.exists(path):
        return []

    with open(path) as f:
        return f.readlines()


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")

    logs = list_logs()
    config = load_config()

    return render_template("dashboard.html", logs=logs, config=config)


# ─────────────────────────────────────────────
# VIEW LOG
# ─────────────────────────────────────────────
@app.route("/log/<filename>")
def view_log(filename):
    if not session.get("logged_in"):
        return redirect("/")

    content = load_log(filename)
    return render_template("log.html", filename=filename, content=content)


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
