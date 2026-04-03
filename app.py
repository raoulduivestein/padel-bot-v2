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
    print("✅ Config opgeslagen")


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
    subprocess.Popen(["python", "main.py"])
    return redirect("/dashboard")


@app.route("/update_config", methods=["POST"])
def update_config():
    cfg = load_config()

    cfg["days_ahead"] = int(request.form["days_ahead"])
    cfg["run_time"]["prep"] = request.form["prep"]
    cfg["run_time"]["booking"] = request.form["booking"]

    save_config(cfg)
    return redirect("/dashboard")


@app.route("/api/log/<filename>")
def api_log(filename):
    path = f"{LOG_DIR}/{filename}"

    if not os.path.exists(path):
        return {"lines": []}

    data = json.load(open(path))
    lines = [json.dumps(e) for e in data.get("events", [])]

    return {"lines": lines}


@app.route("/api/whatsapp/<filename>")
def whatsapp(filename):
    path = f"{LOG_DIR}/{filename}"

    if not os.path.exists(path):
        return {"message": ""}

    data = json.load(open(path))

    for e in data.get("events", []):
        if e.get("type") == "booking":
            slots = e["slots"]
            court = e["court"]

            return {
                "message": f"{slots[0]['date']} {slots[0]['time']} {court}"
            }

    return {"message": ""}


if __name__ == "__main__":
    app.run(debug=True)
