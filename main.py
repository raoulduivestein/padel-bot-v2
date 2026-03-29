import json
import time
from datetime import datetime

from token_service import refresh, get_valid_token
from slot_generator import generate_slots
from booking import book_slots

BOOKING_TIME = (7, 59, 55)
BOOKING_TIME = (0, 0, 0)


def wait_until():
    while True:
        now = datetime.now()
        if (now.hour, now.minute, now.second) >= BOOKING_TIME:
            break
        time.sleep(0.5)


def main():
    print("⏳ Waiting for booking window...")
    wait_until()

    print("🔄 Force token refresh")
    refresh()

    token = get_valid_token()

    with open("config.json") as f:
        config = json.load(f)

    slots = generate_slots(config)

    print("🎯 Slots:", slots)

    for i in range(10):
        print(f"🔁 Attempt {i+1}")

        success = book_slots(slots, config, token)

        if success:
            print("🎉 Booking gelukt!")
            return

        time.sleep(1)

    print("❌ Geen booking gelukt")


if __name__ == "__main__":
    main()