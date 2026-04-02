import os
import json
import time
import requests
import sys
from datetime import datetime, timedelta

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"{LOG_DIR}/run_{RUN_ID}.log"

LOCK_FILE = "run.lock"

# 🔥 TELEGRAM CONFIG
TELEGRAM_TOKEN = "8707541665:AAEmnzJqykk6YpzHkyDGp2TQRIcjPKcg5D4"
CHAT_ID = "7106070066"


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
def log(msg):
    print(msg)
    send_telegram(msg)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def parse_time(t):
    h, m, s = map(int, t.split(":"))
    return (h, m, s)


def wait_until(target_time):
    now = datetime.now()

    target = now.replace(
        hour=target_time[0],
        minute=target_time[1],
        second=target_time[2],
        microsecond=0
    )

    if now >= target:
        target += timedelta(days=1)

    log(f"⏳ Wachten tot {target}")

    while True:
        now = datetime.now()
        seconds_to_wait = (target - now).total_seconds()

        if seconds_to_wait <= 0:
            break

        print(f"⏳ Nog {int(seconds_to_wait)} sec wachten...")
        time.sleep(min(seconds_to_wait, 1))


# ─────────────────────────────────────────────
# CORE BOOKING FLOW (HERGEBRUIKBAAR)
# ─────────────────────────────────────────────
def execute_booking_flow(config, token):
    slots = generate_slots(config)
    log(f"🎯 Slots: {slots}")

    if not slots:
        log("❌ Geen slots gegenereerd")
        return False

    log("🚀 START BOOKING!")

    for i in range(10):
        log(f"🔁 Attempt {i+1}")

        success = book_slots(slots, config, token)

        if success:
            log("🎉 Booking gelukt!")
            return True

        time.sleep(0.3)

    log("❌ Geen booking gelukt")
    return False


# ─────────────────────────────────────────────
# RUN NOW (🔥 NIEUW)
# ─────────────────────────────────────────────
def run_now():
    if os.path.exists(LOCK_FILE):
        log("⚠️ Er draait al een run")
        return

    open(LOCK_FILE, "w").close()

    try:
        log("🚀 RUN NOW gestart")

        refresh()
        token = get_valid_token()

        with open("config.json") as f:
            config = json.load(f)

        execute_booking_flow(config, token)

    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


# ─────────────────────────────────────────────
# MAIN (SCHEDULED)
# ─────────────────────────────────────────────
def main():
    if os.path.exists(LOCK_FILE):
        log("⚠️ Er draait al een run")
        return

    open(LOCK_FILE, "w").close()

    try:
        log("🚀 Padel bot gestart")

        with open("config.json") as f:
            config = json.load(f)

        PREP_TIME = parse_time(config["run_time"]["prep"])
        BOOKING_TIME = parse_time(config["run_time"]["booking"])

        # 1. Wachten tot prep moment
        log("⏳ Waiting for prep time...")
        wait_until(PREP_TIME)

        # 2. Token refresh
        log("🔄 Token refresh net voor booking")
        refresh()
        token = get_valid_token()

        # 3. Slots + booking
        slots = generate_slots(config)
        log(f"🎯 Slots: {slots}")

        if not slots:
            log("❌ Geen slots gegenereerd")
            return

        # 4. Wachten tot booking moment
        log("⏳ Waiting for booking window...")
        wait_until(BOOKING_TIME)

        execute_booking_flow(config, token)

    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_now":
        run_now()
    else:
        main()
