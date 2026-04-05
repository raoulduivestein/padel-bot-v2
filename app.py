from flask import Flask, render_template, request, redirect, session, jsonify
import os, json, subprocess, requests
from token_service import get_valid_token

app = Flask(__name__)
app.secret_key = "secret"

CONFIG_FILE = "config.json"
BOOKINGS_FILE = "bookings.json"
PLAYERS_FILE = "players.json"

USERNAME = "admin"
PASSWORD = "padel123"


# ---------------- CONFIG ----------------
def load_config():
    return json.load(open(CONFIG_FILE))


def save_config(cfg):
    json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)


# ---------------- BOOKINGS ----------------
def load_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []
    return json.load(open(BOOKINGS_FILE))


def save_bookings(data):
    json.dump(data, open(BOOKINGS_FILE, "w"), indent=2)


# ---------------- PLAYERS ----------------
def load_players():
    if not os.path.exists(PLAYERS_FILE):
        return {}
    return json.load(open(PLAYERS_FILE))


def save_players(data):
    json.dump(data, open(PLAYERS_FILE, "w"), indent=2)


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("dashboard.html", config=load_config())


# ---------------- FETCH BOOKINGS ----------------
@app.route("/api/fetch_bookings")
def fetch_bookings():

    token = get_valid_token()

    url = "https://mobile-app-back.davidlloyd.co.uk/members/me/bookings?include-others-i-can-book-for"

    headers = {
        "Accept": "application/json",
        "X-App-Version": "149.0.0",
        "X-Auth-Token": token,
        "X-Requested-With": "co.uk.davidlloyd.mobileapp"
    }

    r = requests.get(url, headers=headers)
    data = r.json()

    bookings = []

    players_db = load_players()

    for b in data.get("bookings", []):

        players = []
        for p in b["details"]["players"]:
            pid = p["encodedContactId"]

            # 🔥 opslaan in players.json
            if pid not in players_db:
                players_db[pid] = {
                    "name": p["fullName"],
                    "phone": "",
                    "rating": 3,
                    "punctuality": 3
                }

            players.append({
                "id": pid,
                "name": p["fullName"]
            })

        bookings.append({
            "datetime": f"{b['date'].split('-')[2]}-{b['date'].split('-')[1]}-{b['date'].split('-')[0]} {b['startTime']}",
            "court": f"Court {b['details']['courtId']}",
            "status": b["status"],
            "duration": b["duration"],
            "encodedBookingReference": b["encodedBookingReference"],
            "players": players
        })

    save_players(players_db)
    save_bookings(bookings)

    return {"status": "success"}


# ---------------- BOOKINGS API ----------------
@app.route("/api/bookings")
def api_bookings():
    return jsonify(load_bookings())


# ---------------- PLAYERS ----------------
@app.route("/api/players")
def api_players():
    return load_players()


@app.route("/api/players_list")
def players_list():
    players = load_players()
    return [{"id": k, "name": v["name"], "phone": v.get("phone", "")} for k, v in players.items()]


@app.route("/api/update_player", methods=["POST"])
def update_player():
    data = request.json
    players = load_players()

    pid = data["id"]

    if pid not in players:
        return {"status": "error"}

    players[pid]["phone"] = data.get("phone", "")
    players[pid]["rating"] = data.get("rating", 3)
    players[pid]["punctuality"] = data.get("punctuality", 3)

    save_players(players)
    return {"status": "success"}


# ---------------- ADD PLAYER ----------------
@app.route("/api/add_player_to_booking", methods=["POST"])
def add_player():

    data = request.json

    booking_ref = data["booking_ref"]
    new_player = data["player_id"]
    current_players = data["current_players"]

    token = get_valid_token()

    all_players = list(set(current_players + [new_player]))

    url = f"https://mobile-app-back.davidlloyd.co.uk/clubs/94/members/me/bookings/{booking_ref}/players?return-booking=true"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-App-Version": "149.0.0",
        "X-Auth-Token": token,
        "X-Requested-With": "co.uk.davidlloyd.mobileapp"
    }

    payload = {
        "playersEncodedContactIds": all_players
    }

    r = requests.put(url, json=payload, headers=headers)
    r.raise_for_status()

    return {"status": "success"}


# ---------------- RUN ----------------
@app.route("/run_now")
def run_now():
    subprocess.Popen(["python3", "main.py", "run_now"])
    return redirect("/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
