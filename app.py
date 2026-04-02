from flask import Flask, render_template, request, redirect, session
import os
import json
import subprocess

app = Flask(__name__)
app.secret_key = "secret"

CONFIG_FILE = "config.json"
LOG_DIR = "logs"
STATUS_DIR = "status"

USERNAME = "admin"
PASSWORD = "padel123"


def load_config():
    return json.load(open(CONFIG_FILE))


def save_config(cfg):
    json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")
    logs = sorted(os.listdir(LOG_DIR), reverse=True)
    return render_template("dashboard.html", logs=logs, config=load_config())


@app.route("/run_now")
def run_now():
    subprocess.Popen([
        "/root/padel-bot-v2/venv/bin/python",
        "main.py",
        "run_now"
    ])
    return redirect("/dashboard")


# API STATUS
@app.route("/api/status")
def api_status():
    files = sorted(os.listdir(STATUS_DIR), reverse=True)
    result = []

    for f in files:
        data = json.load(open(f"{STATUS_DIR}/{f}"))
        result.append({
            "file": f.replace(".json", ".log"),
            "status": data["status"]
        })

    return result


# API LOG
@app.route("/api/log/<filename>")
def api_log(filename):
    path = f"{LOG_DIR}/{filename}"
    if not os.path.exists(path):
        return {"lines": []}

    return {"lines": open(path).readlines()[-50:]}


@app.route("/update_config", methods=["POST"])
def update_config():
    cfg = load_config()

    cfg["days_ahead"] = int(request.form["days_ahead"])
    cfg["run_time"]["prep"] = request.form["prep"]
    cfg["run_time"]["booking"] = request.form["booking"]

    save_config(cfg)
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
