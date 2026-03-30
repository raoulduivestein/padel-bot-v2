import json
import time
from datetime import datetime, timedelta

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots


with open("config.json") as f:
    config = json.load(f)

PREP_TIME = parse_time(config["run_time"]["prep"])
BOOKING_TIME = parse_time(config["run_time"]["booking"])


def wait_until(target_time):
    """
    Wacht tot een specifiek tijdstip.
    Als dat tijdstip vandaag al voorbij is, wacht tot morgen.
    """
    now = datetime.now()

    target = now.replace(
        hour=target_time[0],
        minute=target_time[1],
        second=target_time[2],
        microsecond=0
    )

    # Alleen één keer bepalen of target naar morgen moet
    if now >= target:
        target += timedelta(days=1)

    print(f"⏳ Wachten tot {target}")

    while True:
        now = datetime.now()
        seconds_to_wait = (target - now).total_seconds()

        if seconds_to_wait <= 0:
            break

        print(f"⏳ Nog {int(seconds_to_wait)} sec wachten...")
        time.sleep(min(seconds_to_wait, 1))


def main():
    print("🚀 Padel bot gestart")

    # 1. Wachten tot prep moment
    print("⏳ Waiting for prep time...")
    wait_until(PREP_TIME)

    # 2. Token refresh vlak voor booking
    print("🔄 Token refresh net voor booking")
    refresh()

    token = get_valid_token()

    # 3. Config laden
    with open("config.json") as f:
        config = json.load(f)

    # 4. Slots genereren
    slots = generate_slots(config)
    print("🎯 Slots:", slots)

    if not slots:
        print("❌ Geen slots gegenereerd")
        return

    # 5. Wachten tot exact booking moment
    print("⏳ Waiting for booking window...")
    wait_until(BOOKING_TIME)

    print("🚀 START BOOKING!")

    # 6. Retry loop
    for i in range(10):
        print(f"🔁 Attempt {i+1}")

        success = book_slots(slots, config, token)

        if success:
            print("🎉 Booking gelukt!")
            return

        time.sleep(0.3)

    print("❌ Geen booking gelukt")


if __name__ == "__main__":
    main()
