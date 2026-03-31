import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://mobile-app-back.davidlloyd.co.uk"


# ─────────────────────────────────────────────
# HEADERS
# ─────────────────────────────────────────────
def headers(token):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "X-App-Version": "149.0.0",
        "X-Requested-With": "co.uk.davidlloyd.mobileapp",
        "X-Auth-Token": token
    }


# ─────────────────────────────────────────────
# GET AVAILABILITY
# ─────────────────────────────────────────────
def get_availability(date, config, token, member):
    url = f"{BASE_URL}/clubs/{config['club_id']}/court-slots/{date}/{config['sports_package_id']}"

    params = {
        "encodedContactId": member["member_id"]
    }

    r = requests.get(url, headers=headers(token), params=params)

    print(f"📡 Availability status ({member['name']}): {r.status_code}")

    if r.status_code != 200:
        print("❌ Availability error:", r.text)
        return None

    return r.json()


# ─────────────────────────────────────────────
# SELECT COURT
# ─────────────────────────────────────────────
def select_court(data, target_time, config):
    if not data:
        return None

    slots = data.get("slots", [])

    available = [
        slot["courtId"]
        for slot in slots
        if slot.get("startTime") == target_time
    ]

    print(f"🎾 Beschikbaar om {target_time}: {available}")

    # 🎯 Preferred courts eerst
    for preferred in config.get("preferred_courts", []):
        if preferred in available:
            print(f"🎯 Preferred court gekozen: {preferred}")
            return preferred

    # 🔁 fallback
    if config.get("fallback_to_any") and available:
        print(f"↪️ Fallback court: {available[0]}")
        return available[0]

    return None


# ─────────────────────────────────────────────
# TRY BOOK
# ─────────────────────────────────────────────
def try_book(slot, config, token, member):
    print(f"👤 Booking met {member['name']} ({slot['time']})")

    data = get_availability(slot["date"], config, token, member)
    court_id = select_court(data, slot["time"], config)

    if not court_id:
        print(f"❌ Geen court beschikbaar ({slot['time']})")
        return False

    payload = {
        "bookedMemberEncodedContactId": member["member_id"],
        "courtId": court_id,
        "date": slot["date"],
        "startTime": slot["time"],
        "sportsPackageId": config["sports_package_id"],
        "playersEncodedContactIds": []
    }

    print("📤 CREATE PAYLOAD:", payload)

    # ── CREATE ─────────────────────────────
    r1 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/bookings/court",
        headers=headers(token),
        json=payload
    )

    print(f"📤 CREATE status ({slot['time']}):", r1.status_code)

    if r1.status_code != 200:
        print("❌ CREATE error:", r1.text)
        return False

    data = r1.json()
    ref = data.get("encodedBookingReference")

    if not ref:
        print("❌ Geen booking reference ontvangen")
        return False

    # ── CONFIRM ────────────────────────────
    r2 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/members/me/bookings/{ref}/confirmCourt?return-booking=true",
        headers=headers(token),
        json={"courtConfirmationType": "provisional"}
    )

    print(f"📤 CONFIRM status ({slot['time']}):", r2.status_code)

    if r2.status_code == 200:
        print(f"✅ GEBOEKT {slot['time']} met {member['name']} (court {court_id})")
        return True

    print("❌ CONFIRM error:", r2.text)
    return False


# ─────────────────────────────────────────────
# MAIN BOOKING LOOP (PARALLEL)
# ─────────────────────────────────────────────
def book_slots(slots, config, token):
    members = config["members"]

    # ❗ Check: genoeg members
    if len(members) < len(slots):
        print("❌ Niet genoeg members voor aantal slots")
        return False

    success_any = False

    # 🎯 Koppel unieke member per slot
    tasks = []
    for i, slot in enumerate(slots):
        member = members[i]
        tasks.append((slot, member))

    print(f"🚀 Start parallel booking ({len(tasks)} requests tegelijk)")

    # ⚡ Parallel uitvoeren
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [
            executor.submit(try_book, slot, config, token, member)
            for slot, member in tasks
        ]

        for future in as_completed(futures):
            try:
                success = future.result()
                if success:
                    success_any = True
            except Exception as e:
                print("❌ Thread error:", str(e))

    return success_any
