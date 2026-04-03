import requests
from concurrent.futures import ThreadPoolExecutor

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


def get_court_name(court_id, config):
    for c in config.get("courts", []):
        if c["id"] == court_id:
            return c["name"]
    return f"Court {court_id}"


def get_available_courts_for_slots(slots, config, token, member):
    url = f"{BASE_URL}/clubs/{config['club_id']}/court-slots/{slots[0]['date']}/{config['sports_package_id']}"

    r = requests.get(url, headers=headers(token), params={
        "encodedContactId": member["member_id"]
    })

    if r.status_code != 200:
        return {}

    data = r.json()
    result = {}

    for slot in slots:
        result[slot["time"]] = [
            s["courtId"]
            for s in data.get("slots", [])
            if s.get("startTime") == slot["time"]
        ]

    return result


def select_courts_smart(slots, availability, config):
    for slot in slots:
        possible = availability.get(slot["time"], [])
        for c in config["preferred_courts"]:
            if c in possible:
                return [(slot, c)]
    return None


def try_book(slot, court_id, config, token, member):
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


def book_slots(slots, config, token):
    members = config["members"]

    availability = get_available_courts_for_slots(slots, config, token, members[0])

    selected = select_courts_smart(slots, availability, config)

    if not selected:
        return {"success": False}

    results = []

    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = []

        for i, (slot, court_id) in enumerate(selected):
            member = members[i % len(members)]
            futures.append(
                executor.submit(try_book, slot, court_id, config, token, member)
            )

        for f in futures:
            results.append(f.result())

    if any(results):
        slot, court_id = selected[0]
        return {
            "success": True,
            "court_id": court_id,
            "court_name": get_court_name(court_id, config),
            "slots": slots
        }

    return {"success": False}
