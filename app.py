from flask import Flask, render_template, request, redirect, session
import os
import json
import subprocess
import requests
from datetime import datetime

from token_service import get_valid_token

app = Flask(__name__)
app.secret_key = "secret"

CONFIG_FILE = "config.json"
LOG_DIR = "logs"
STATUS_DIR = "status"
BOOKINGS_FILE = "bookings.json"
PLAYERS_FILE = "players.json"

USERNAME = "admin"
PASSWORD = "padel123"


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
def load_config():
    return json.load(open(CONFIG_FILE))


def save_config(cfg):
    json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)


# ─────────────────────────────────────────────
# PLAYERS
# ─────────────────────────────────────────────
def load_players():
    if not os.path.exists(PLAYERS_FILE):
        return {}
    return json.load(open(PLAYERS_FILE))


def save_players(data):
    json.dump(data, open(PLAYERS_FILE, "w"), indent=2)


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
    logs = sorted(os.listdir(LOG_DIR), reverse=True)
    return render_template("dashboard.html", logs=logs, config=load_config())


# ─────────────────────────────────────────────
# RUN NOW
# ─────────────────────────────────────────────
@app.route("/run_now")
def run_now():
    subprocess.Popen([
        "/root/padel-bot-v2/venv/bin/python",
        "main.py",
        "run_now"
    ])
    return redirect("/dashboard")


# ─────────────────────────────────────────────
# UPDATE CONFIG
# ─────────────────────────────────────────────
@app.route("/update_config", methods=["POST"])
def update_config():
    cfg = load_config()

    cfg["days_ahead"] = int(request.form["days_ahead"])
    cfg["run_time"]["prep"] = request.form["prep"]
    cfg["run_time"]["booking"] = request.form["booking"]

    for i, rule in enumerate(cfg["booking_rules"]):
        times_raw = request.form.get(f"times_{i}", "")
        cfg["booking_rules"][i]["times"] = [
            t.strip() for t in times_raw.split(",") if t.strip()
        ]
        cfg["booking_rules"][i]["duration"] = int(
            request.form.get(f"duration_{i}", 1)
        )

    save_config(cfg)
    return redirect("/dashboard")


# ─────────────────────────────────────────────
# BOOKINGS OPHALEN
# ─────────────────────────────────────────────
@app.route("/api/fetch_bookings")
def fetch_bookings():
    if not session.get("logged_in"):
        return {"status": "error"}

    try:
        token = get_valid_token()

        url = "https://mobile-app-back.davidlloyd.co.uk/members/me/bookings?include-others-i-can-book-for"

        res = requests.get(
            url,
            headers={
                "X-Auth-Token": token,
                "User-Agent": "OneApp/149.0.0",
                "Accept": "application/json",
                "Connection": "Keep-Alive"
            },
            timeout=20
        )

        res.raise_for_status()
        data = res.json()

        bookings = data.get("bookings", [])

        court_map = {
            737381: "Court 1",
            737383: "Court 2",
            737385: "Court 3"
        }

        players_db = load_players()
        result = []

        for b in bookings:
            dt = datetime.strptime(
                f"{b['date']} {b['startTime']}",
                "%Y-%m-%d %H:%M"
            )

            booking_players = []

            for p in b["details"].get("players", []):
                pid = p["encodedContactId"]
                name = p["fullName"]

                if pid not in players_db:
                    players_db[pid] = {
                        "name": name,
                        "phone": "",
                        "rating": 3,
                        "punctuality": 3
                    }

                booking_players.append({
                    "id": pid,
                    "name": name
                })

            result.append({
                "datetime": dt.strftime("%d-%m-%Y %H:%M"),
                "timestamp": dt.timestamp(),
                "status": b.get("status"),
                "court": court_map.get(b["details"].get("courtId"), "Onbekend"),
                "players": booking_players
            })

        result.sort(key=lambda x: x["timestamp"])

        json.dump(result, open(BOOKINGS_FILE, "w"), indent=2)
        save_players(players_db)

        return {"status": "success"}

    except Exception as e:
        print("❌ Booking fetch error:", e)
        return {"status": "error"}


# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────
@app.route("/api/bookings")
def get_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []
    return json.load(open(BOOKINGS_FILE))


@app.route("/api/players")
def get_players():
    return load_players()


@app.route("/api/update_player", methods=["POST"])
def update_player():
    data = request.json
    players = load_players()

    pid = data["id"]

    if pid in players:
        if "phone" in data:
            players[pid]["phone"] = data["phone"]
        if "rating" in data:
            players[pid]["rating"] = int(data["rating"])
        if "punctuality" in data:
            players[pid]["punctuality"] = int(data["punctuality"])

    save_players(players)
    return {"status": "success"}
    
# PLAYERS
@app.route("/api/players_list")
def players_list():
    players = load_players()

    return [
        {
            "id": k,
            "name": v.get("name"),
            "phone": v.get("phone", "")
        }
        for k, v in players.items()
    ]

# ─────────────────────────────────────────────
# STATUS + LOGS
# ─────────────────────────────────────────────
@app.route("/api/status")
def api_status():
    files = sorted(os.listdir(STATUS_DIR), reverse=True)

    result = []
    for f in files:
        try:
            data = json.load(open(f"{STATUS_DIR}/{f}"))
        except:
            continue

        result.append({
            "file": f.replace(".json", ".log"),
            "status": data.get("status", "unknown")
        })

    return result


@app.route("/api/log/<filename>")
def api_log(filename):
    path = f"{LOG_DIR}/{filename}"
    if not os.path.exists(path):
        return {"lines": []}
    return {"lines": open(path, encoding="utf-8").readlines()[-100:]}


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
