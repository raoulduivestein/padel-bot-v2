import requests

BASE_URL = "https://mobile-app-back.davidlloyd.co.uk"


def headers(token):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "X-App-Version": "149.0.0",
        "X-Requested-With": "co.uk.davidlloyd.mobileapp",
        "X-Auth-Token": token
    }


def get_availability(date, config, token, member):
    url = f"{BASE_URL}/clubs/{config['club_id']}/court-slots/{date}/{config['sports_package_id']}"

    params = {
        "encodedContactId": member["member_id"]
    }

    r = requests.get(url, headers=headers(token), params=params)

    print(f"📡 Availability status ({member['name']}):", r.status_code)

    r.raise_for_status()
    data = r.json()

    print("📡 RAW:", data)

    return data


def select_court(data, target_time, config):
    slots = data.get("slots", [])

    available = []

    for slot in slots:
        if slot.get("startTime") == target_time:
            available.append(slot.get("courtId"))

    print(f"🎾 Beschikbaar om {target_time}: {available}")

    for preferred in config.get("preferred_courts", []):
        if preferred in available:
            print(f"🎯 Preferred court: {preferred}")
            return preferred

    if config.get("fallback_to_any") and available:
        print(f"↪️ Fallback court: {available[0]}")
        return available[0]

    return None


def try_book(slot, config, token, member):
    print(f"👤 Booking met {member['name']}")

    data = get_availability(slot["date"], config, token, member)

    court_id = select_court(data, slot["time"], config)

    if not court_id:
        print("❌ Geen court")
        return False

    payload = {
        "bookedMemberEncodedContactId": member["member_id"],
        "courtId": court_id,
        "date": slot["date"],
        "startTime": slot["time"],
        "sportsPackageId": config["sports_package_id"],
        "playersEncodedContactIds": []
    }

    print("📤 CREATE:", payload)

    r1 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/bookings/court",
        headers=headers(token),
        json=payload
    )

    print("📤 CREATE status:", r1.status_code)
    print("📤 CREATE resp:", r1.text)

    if r1.status_code != 200:
        return False

    ref = r1.json().get("encodedBookingReference")

    r2 = requests.post(
        f"{BASE_URL}/clubs/{config['club_id']}/members/me/bookings/{ref}/confirmCourt?return-booking=true",
        headers=headers(token),
        json={"courtConfirmationType": "provisional"}
    )

    print("📤 CONFIRM status:", r2.status_code)
    print("📤 CONFIRM resp:", r2.text)

    if r2.status_code == 200:
        print(f"✅ GEBOEKT {slot['time']} met {member['name']}")
        return True

    return False


def book_slots(slots, config, token):
    members = config["members"]

    for i, slot in enumerate(slots):
        member = members[i % len(members)]

        success = try_book(slot, config, token, member)

        if success:
            print(f"🎾 {slot['time']} geboekt met {member['name']}")

    return True