import requests
from concurrent.futures import ThreadPoolExecutor

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
# GET AVAILABILITY (1x)
# ─────────────────────────────────────────────
def get_available_courts_for_slots(slots, config, token, member):
    url = f"{BASE_URL}/clubs/{config['club_id']}/court-slots/{slots[0]['date']}/{config['sports_package_id']}"

    params = {
        "encodedContactId": member["member_id"]
    }

    r = requests.get(url, headers=headers(token), params=params)

    if r.status_code != 200:
        print("❌ Availability error:", r.text)
        return {}

    data = r.json()

    result = {}

    for slot in slots:
        time = slot["time"]

        courts = [
            s["courtId"]
            for s in data.get("slots", [])
            if s.get("startTime") == time
        ]

        result[time] = courts

    return result


# ─────────────────────────────────────────────
# SLIMME COURT SELECTIE
# ─────────────────────────────────────────────
def select_courts_smart(slots, availability, config):
    # 1. zelfde court proberen
    common = None

    for slot in slots:
        courts = set(availability.get(slot["time"], []))

        if common is None:
            common = courts
        else:
            common = common.intersection(courts)

    if common:
        print(f"🎯 Zelfde court mogelijk: {common}")

        for p in config.get("preferred_courts", []):
            if p in common:
                return [(slot, p) for slot in slots]

        chosen = list(common)[0]
        return [(slot, chosen) for slot in slots]

    # 2. fallback → verschillende courts
    print("↪️ Geen overlap, fallback naar verschillende courts")

    selected = []
    used = set()

    for slot in slots:
        possible = availability.get(slot["time"], [])

        for p in config.get("preferred_courts", []):
            if p in possible and p not in used:
                selected.append((slot, p))
                used.add(p)
                break
        else:
            for c in possible:
                if c not in used:
                    selected.append((slot, c))
                    used.add(c)
                    break

    if len(selected) == len(slots):
        return selected

    # 3. fallback → 1 court
    print("⚠️ Slechts 1 court beschikbaar")

    for slot in slots:
        possible = availability.get(slot["time"], [])
        if possible:
            return [(slot, possible[0])]

    return None


# ─────────────────────────────────────────────
# BOOKING
# ─────────────────────────────────────────────
def try_book_fixed(slot, court_id, config, token, member):
    payload = {
        "bookedMemberEncodedContactId": member["member_id"],
        "courtId": court_id,
        "date": slot["date"],
        "startTime": slot["time"],
        "sportsPackageId": config["sports_package_id"],
        "playersEncodedContactIds": []
    }

    r1 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/bookings/court",
        headers=headers(token),
        json=payload
    )

    if r1.status_code != 200:
        return False

    ref = r1.json().get("encodedBookingReference")

    r2 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/members/me/bookings/{ref}/confirmCourt?return-booking=true",
        headers=headers(token),
        json={"courtConfirmationType": "provisional"}
    )

    return r2.status_code == 200


# ─────────────────────────────────────────────
# MAIN BOOK FUNCTION
# ─────────────────────────────────────────────
def book_slots(slots, config, token):
    members = config["members"]

    # 1. availability 1x ophalen
    availability = get_available_courts_for_slots(slots, config, token, members[0])

    print("📡 Availability:", availability)

    # 2. slimme selectie
    selected = select_courts_smart(slots, availability, config)

    if not selected:
        print("❌ Geen banen beschikbaar")
        return False

    print("🎾 Geselecteerd:", selected)

    # 3. parallel boeken
    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = []

        for i, (slot, court_id) in enumerate(selected):
            member = members[i % len(members)]

            futures.append(
                executor.submit(try_book_fixed, slot, court_id, config, token, member)
            )

        results = [f.result() for f in futures]

    return any(results)
