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


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def list_logs():
    if not os.path.exists(LOG_DIR):
        return []
    return sorted(os.listdir(LOG_DIR), reverse=True)


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

    return render_template(
        "dashboard.html",
        config=load_config(),
        logs=list_logs()
    )


# ─────────────────────────────────────────────
# UPDATE CONFIG
# ─────────────────────────────────────────────
@app.route("/update_config", methods=["POST"])
def update_config():
    if not session.get("logged_in"):
        return redirect("/")

    config = load_config()

    # SIMPLE FIELDS
    config["days_ahead"] = int(request.form["days_ahead"])
    config["run_time"]["prep"] = request.form["prep"]
    config["run_time"]["booking"] = request.form["booking"]

    # BOOKING RULES
    for i, rule in enumerate(config["booking_rules"]):
        key_times = f"times_{i}"
        key_duration = f"duration_{i}"

        times = request.form.get(key_times, "")
        config["booking_rules"][i]["times"] = [t.strip() for t in times.split(",") if t.strip()]
        config["booking_rules"][i]["duration"] = int(request.form.get(key_duration, 1))

    save_config(config)

    return redirect("/dashboard")


# ─────────────────────────────────────────────
# LOG VIEW
# ─────────────────────────────────────────────
@app.route("/log/<filename>")
def view_log(filename):
    if not session.get("logged_in"):
        return redirect("/")

    return render_template(
        "log.html",
        filename=filename,
        content=load_log(filename)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
