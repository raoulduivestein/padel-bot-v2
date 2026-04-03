import os
import json
import time
import requests
from datetime import datetime

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots
from log_utils import create_log_file, append_log

STATUS_DIR = "status"
os.makedirs(STATUS_DIR, exist_ok=True)

LOG_FILE = None
LOCK_FILE = "run.lock"

# TELEGRAM
TELEGRAM_TOKEN = "8707541665:AAEmnzJqykk6YpzHkyDGp2TQRIcjPKcg5D4"
CHAT_ID = "7106070066"


def write_status(status):
    filename = os.path.basename(LOG_FILE)
    path = f"{STATUS_DIR}/{filename}"

    json.dump({
        "status": status,
        "timestamp": datetime.now().isoformat()
    }, open(path, "w"))


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message}
        )
    except:
        pass


def log(msg):
    print(msg)
    send_telegram(msg)

    append_log(LOG_FILE, {
        "type": "log",
        "message": msg
    })


def execute_booking_flow(config, token):
    write_status("running")

    slots = generate_slots(config)

    append_log(LOG_FILE, {
        "type": "slots",
        "slots": slots
    })

    for i in range(10):
        log(f"Attempt {i+1}")

        result = book_slots(slots, config, token)

        if result.get("success"):
            append_log(LOG_FILE, {
                "type": "booking",
                "court": result["court_name"],
                "slots": result["slots"]
            })

            write_status("success")
            return

        time.sleep(0.3)

    write_status("failed")


def run_now():
    global LOG_FILE
    LOG_FILE = create_log_file()

    if os.path.exists(LOCK_FILE):
        return

    open(LOCK_FILE, "w").close()

    try:
        config = json.load(open("config.json"))

        refresh()
        token = get_valid_token()

        execute_booking_flow(config, token)

    finally:
        os.remove(LOCK_FILE)


if __name__ == "__main__":
    run_now()
