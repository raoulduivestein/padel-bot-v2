import json
import time
from datetime import datetime, timedelta

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots


# 🔥 Instellingen
PREP_TIME = (7, 59, 55)
BOOKING_TIME = (8, 0, 0)


# 🧠 Slimme wait (werkt ook als het avond is)
def wait_until(target_time):
    while True:
        now = datetime.now()

        target = now.replace(
            hour=target_time[0],
            minute=target_time[1],
            second=target_time[2],
            microsecond=0
        )

        # 👉 Als tijd al voorbij is → morgen
        if now >= target:
            target += timedelta(days=1)

        seconds_to_wait = (target - now).total_seconds()

        print(f"⏳ Wachten tot {target} ({int(seconds_to_wait)} sec)")

        if seconds_to_wait <= 0:
            break

        # slaap max 60 sec (sneller reageren)
        time.sleep(min(seconds_to_wait, 60))


def main():
    print("🚀 Padel bot gestart")

    # 🔥 1. Wacht tot PREP
    print("⏳ Waiting for prep time...")
    wait_until(PREP_TIME)

    # 🔥 2. Token refresh vlak voor 08:00
    print("🔄 Token refresh net voor 08:00")
    refresh()

    token = get_valid_token()

    # 🔥 3. Config laden
    with open("config.json") as f:
        config = json.load(f)

    # 🔥 4. Slots genereren
    slots = generate_slots(config)
    print("🎯 Slots:", slots)

    # 🔥 5. Wacht tot EXACT 08:00
    print("⏳ Waiting for booking window (08:00)...")
    wait_until(BOOKING_TIME)

    print("🚀 START BOOKING!")

    # 🔁 6. Retry loop
    for i in range(10):
        print(f"🔁 Attempt {i+1}")

        success = book_slots(slots, config, token)

        if success:
            print("🎉 Booking gelukt!")
            return

        time.sleep(0.3)  # 🔥 snelle retry

    print("❌ Geen booking gelukt")


if __name__ == "__main__":
    main()
