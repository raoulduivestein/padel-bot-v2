import os
import json
import time
import requests
import sys
import traceback
from datetime import datetime, timedelta

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots

# ─────────────────────────────────────────────
# DIRECTORIES
# ─────────────────────────────────────────────
LOG_DIR = "logs"
STATUS_DIR = "status"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)

LOG_FILE = None

# TELEGRAM
TELEGRAM_TOKEN = "8707541665:AAEmnzJqykk6YpzHkyDGp2TQRIcjPKcg5D4"
CHAT_ID = "7106070066"


# ─────────────────────────────────────────────
# LOG FILE
# ─────────────────────────────────────────────
def create_log_file():
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    return f"{LOG_DIR}/run_{run_id}.log"


def write_status(status, message=""):
    filename = os.path.basename(LOG_FILE).replace(".log", ".json")
    path = f"{STATUS_DIR}/{filename}"

    data = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    with open(path, "w") as f:
        json.dump(data, f)


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=5
        )
    except:
        pass


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
def log(msg):
    global LOG_FILE

    if LOG_FILE is None:
        LOG_FILE = create_log_file()

    print(msg)
    send_telegram(msg)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def parse_time(t):
    parts = list(map(int, t.split(":")))

    if len(parts) == 2:
        h, m = parts
        s = 0
    elif len(parts) == 3:
        h, m, s = parts
    else:
        raise ValueError(f"Invalid time format: {t}")

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

    while True:
        now = datetime.now()
        if (target - now).total_seconds() <= 0:
            break
        time.sleep(1)


# ─────────────────────────────────────────────
# BOOKING FLOW
# ─────────────────────────────────────────────
def execute_booking_flow(config, token):
    write_status("running")

    try:
        slots = generate_slots(config)
        log(f"🎯 Slots: {slots}")

        if not slots:
            write_status("failed", "geen slots")
            return False

        for i in range(10):
            log(f"🔁 Attempt {i+1}")

            success = book_slots(slots, config, token)

            if success:
                log("🎉 Booking gelukt!")
                write_status("success")
                return True

            time.sleep(0.3)

        log("❌ Geen booking gelukt")
        write_status("failed")
        return False

    except Exception as e:
        log(f"❌ Flow error: {str(e)}")
        log(traceback.format_exc())
        write_status("failed", str(e))
        return False


# ─────────────────────────────────────────────
# RUN NOW
# ─────────────────────────────────────────────
def run_now():
    global LOG_FILE
    LOG_FILE = create_log_file()

    log("🚀 RUN NOW")

    try:
        refresh()
        token = get_valid_token()

        with open("config.json") as f:
            config = json.load(f)

        execute_booking_flow(config, token)

    except Exception as e:
        log(f"❌ Run error: {str(e)}")
        log(traceback.format_exc())
        write_status("failed", str(e))


# ─────────────────────────────────────────────
# MAIN (SCHEDULED)
# ─────────────────────────────────────────────
def main():
    global LOG_FILE
    LOG_FILE = create_log_file()

    log("🚀 Scheduled run")

    try:
        with open("config.json") as f:
            config = json.load(f)

        PREP_TIME = parse_time(config["run_time"]["prep"])
        BOOKING_TIME = parse_time(config["run_time"]["booking"])

        log(f"⏳ Wachten tot PREP: {PREP_TIME}")
        wait_until(PREP_TIME)

        refresh()
        token = get_valid_token()

        log(f"⏳ Wachten tot BOOKING: {BOOKING_TIME}")
        wait_until(BOOKING_TIME)

        execute_booking_flow(config, token)

    except Exception as e:
        log(f"❌ Main error: {str(e)}")
        log(traceback.format_exc())
        write_status("failed", str(e))


# ─────────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_now":
        run_now()
    else:
        main()
