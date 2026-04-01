import requests
import json

TELEGRAM_TOKEN = "8707541665:AAEmnzJqykk6YpzHkyDGp2TQRIcjPKcg5D4"
CHAT_ID = 7106070066


BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CONFIG_FILE = "config.json"

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

TIME_OPTIONS = [
    "07:00","08:00","09:00","10:00",
    "17:00","18:00","19:00","20:00","21:00"
]


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send(text, keyboard=None):
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


# ─────────────────────────────────────────────
# FORMAT CONFIG
# ─────────────────────────────────────────────
def format_config_summary(cfg):
    text = "🎛️ CONTROL PANEL\n\n"

    text += f"📅 days_ahead: {cfg['days_ahead']}\n\n"

    text += "👥 Members:\n"
    for m in cfg["members"]:
        text += f"- {m['name']}\n"

    text += "\n🎾 Courts:\n"
    for c in cfg["preferred_courts"]:
        text += f"- {c}\n"

    text += "\n📅 Booking rules:\n"

    for r in cfg["booking_rules"]:
        times = ", ".join(r["times"]) if r["times"] else "-"
        text += (
            f"{r['day'].capitalize()}:\n"
            f"  ⏰ {times}\n"
            f"  ⏱ {r['duration']} uur\n"
        )

    return text


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main_menu():
    cfg = load_config()
    summary = format_config_summary(cfg)

    send(
        summary,
        keyboard=[
            [{"text": "📅 Days", "callback_data": "days"}],
            [{"text": "⏰ Tijden", "callback_data": "times"}],
            [{"text": "⏱ Duration", "callback_data": "duration"}],
            [{"text": "🎾 Courts", "callback_data": "courts"}],
            [{"text": "👥 Members", "callback_data": "members"}],
            [{"text": "🔄 Refresh", "callback_data": "refresh"}]
        ]
    )


# ─────────────────────────────────────────────
# DAYS MENU
# ─────────────────────────────────────────────
def days_menu():
    cfg = load_config()

    send(
        f"📅 days_ahead = {cfg['days_ahead']}",
        keyboard=[
            [
                {"text": "➖", "callback_data": "days_minus"},
                {"text": "➕", "callback_data": "days_plus"}
            ],
            [{"text": "⬅️ Back", "callback_data": "back"}]
        ]
    )


# ─────────────────────────────────────────────
# DAY SELECT
# ─────────────────────────────────────────────
def day_menu(mode):
    keyboard = []

    for d in DAYS:
        keyboard.append([{"text": d.capitalize(), "callback_data": f"{mode}_{d}"}])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("📅 Kies dag:", keyboard)


# ─────────────────────────────────────────────
# TIMES MENU (FIXED 🔥)
# ─────────────────────────────────────────────
def time_menu(day):
    cfg = load_config()

    times = []
    for r in cfg["booking_rules"]:
        if r["day"] == day:
            times = r["times"]

    keyboard = []

    for t in TIME_OPTIONS:
        mark = "✅" if t in times else "⬜"
        keyboard.append([{
            "text": f"{mark} {t}",
            "callback_data": f"time_{day}_{t}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "times"}])

    send(f"⏰ Tijden voor {day}", keyboard)


# ─────────────────────────────────────────────
# DURATION MENU
# ─────────────────────────────────────────────
def duration_menu(day):
    cfg = load_config()

    current = 1
    for r in cfg["booking_rules"]:
        if r["day"] == day:
            current = r["duration"]

    keyboard = []

    for d in [1,2,3]:
        mark = "✅" if d == current else "⬜"
        keyboard.append([{
            "text": f"{mark} {d} uur",
            "callback_data": f"dur_{day}_{d}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "duration"}])

    send(f"⏱ Duration voor {day}", keyboard)


# ─────────────────────────────────────────────
# COURTS MENU
# ─────────────────────────────────────────────
def courts_menu():
    cfg = load_config()

    keyboard = []

    for c in cfg["preferred_courts"]:
        keyboard.append([{
            "text": f"❌ {c}",
            "callback_data": f"court_remove_{c}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("🎾 Courts", keyboard)


# ─────────────────────────────────────────────
# MEMBERS MENU
# ─────────────────────────────────────────────
def members_menu():
    cfg = load_config()

    keyboard = []

    for m in cfg["members"]:
        keyboard.append([{
            "text": f"❌ {m['name']}",
            "callback_data": f"member_remove_{m['member_id']}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("👥 Members", keyboard)


# ─────────────────────────────────────────────
# CALLBACK HANDLER (FIXED 🔥)
# ─────────────────────────────────────────────
def handle(cb):
    if cb["from"]["id"] != CHAT_ID:
        return

    data = cb["data"]
    cfg = load_config()

    # NAV
    if data == "back":
        return main_menu()

    if data == "refresh":
        return main_menu()

    if data == "days":
        return days_menu()

    if data == "times":
        return day_menu("times")

    if data == "duration":
        return day_menu("duration")

    if data == "courts":
        return courts_menu()

    if data == "members":
        return members_menu()

    # 🔥 FIX: juiste handler voor times_day
    if data.startswith("times_"):
        day = data.split("_")[1]
        return time_menu(day)

    # TIMES TOGGLE
    if data.startswith("time_"):
        _, day, t = data.split("_")

        for r in cfg["booking_rules"]:
            if r["day"] == day:
                if t in r["times"]:
                    r["times"].remove(t)
                else:
                    r["times"].append(t)

        save_config(cfg)
        return time_menu(day)

    # DURATION MENU OPEN
    if data.startswith("duration_"):
        day = data.split("_")[1]
        return duration_menu(day)

    # SET DURATION
    if data.startswith("dur_"):
        _, day, d = data.split("_")

        for r in cfg["booking_rules"]:
            if r["day"] == day:
                r["duration"] = int(d)

        save_config(cfg)
        return duration_menu(day)

    # DAYS
    if data == "days_plus":
        cfg["days_ahead"] += 1

    if data == "days_minus":
        cfg["days_ahead"] = max(0, cfg["days_ahead"] - 1)

    # COURTS
    if data.startswith("court_remove_"):
        c = int(data.split("_")[2])
        cfg["preferred_courts"].remove(c)

    # MEMBERS
    if data.startswith("member_remove_"):
        mid = data.split("_")[2]
        cfg["members"] = [m for m in cfg["members"] if m["member_id"] != mid]

    save_config(cfg)
    main_menu()


# ─────────────────────────────────────────────
# LOOP
# ─────────────────────────────────────────────
def run():
    last = None
    main_menu()

    while True:
        params = {"timeout": 10}
        if last:
            params["offset"] = last + 1

        res = requests.get(f"{BASE_URL}/getUpdates", params=params).json()

        for u in res.get("result", []):
            last = u["update_id"]

            if "callback_query" in u:
                handle(u["callback_query"])


if __name__ == "__main__":
    run()

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CONFIG_FILE = "config.json"

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

TIME_OPTIONS = [
    "07:00","08:00","09:00","10:00",
    "17:00","18:00","19:00","20:00","21:00"
]


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send(text, keyboard=None):
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}

    requests.post(f"{BASE_URL}/sendMessage", json=payload)


# ─────────────────────────────────────────────
# FORMAT CONFIG (🔥 NIEUW)
# ─────────────────────────────────────────────
def format_config_summary(cfg):
    text = "🎛️ CONTROL PANEL\n\n"

    text += f"📅 days_ahead: {cfg['days_ahead']}\n\n"

    text += "👥 Members:\n"
    for m in cfg["members"]:
        text += f"- {m['name']}\n"

    text += "\n🎾 Courts:\n"
    for c in cfg["preferred_courts"]:
        text += f"- {c}\n"

    text += "\n📅 Booking rules:\n"

    for r in cfg["booking_rules"]:
        times = ", ".join(r["times"]) if r["times"] else "-"
        text += (
            f"{r['day'].capitalize()}:\n"
            f"  ⏰ {times}\n"
            f"  ⏱ {r['duration']} uur\n"
        )

    return text


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main_menu():
    cfg = load_config()
    summary = format_config_summary(cfg)

    send(
        summary,
        keyboard=[
            [{"text": "📅 Days", "callback_data": "days"}],
            [{"text": "⏰ Tijden", "callback_data": "times"}],
            [{"text": "⏱ Duration", "callback_data": "duration"}],
            [{"text": "🎾 Courts", "callback_data": "courts"}],
            [{"text": "👥 Members", "callback_data": "members"}],
            [{"text": "🔄 Refresh", "callback_data": "refresh"}]
        ]
    )


# ─────────────────────────────────────────────
# DAYS MENU
# ─────────────────────────────────────────────
def days_menu():
    cfg = load_config()

    send(
        f"📅 days_ahead = {cfg['days_ahead']}",
        keyboard=[
            [
                {"text": "➖", "callback_data": "days_minus"},
                {"text": "➕", "callback_data": "days_plus"}
            ],
            [{"text": "⬅️ Back", "callback_data": "back"}]
        ]
    )


# ─────────────────────────────────────────────
# DAY SELECT
# ─────────────────────────────────────────────
def day_menu(mode):
    keyboard = []

    for d in DAYS:
        keyboard.append([{"text": d.capitalize(), "callback_data": f"{mode}_{d}"}])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("📅 Kies dag:", keyboard)


# ─────────────────────────────────────────────
# TIMES
# ─────────────────────────────────────────────
def time_menu(day):
    cfg = load_config()

    times = []
    for r in cfg["booking_rules"]:
        if r["day"] == day:
            times = r["times"]

    keyboard = []

    for t in TIME_OPTIONS:
        mark = "✅" if t in times else "⬜"
        keyboard.append([{
            "text": f"{mark} {t}",
            "callback_data": f"time_{day}_{t}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "times"}])

    send(f"⏰ Tijden voor {day}", keyboard)


# ─────────────────────────────────────────────
# DURATION
# ─────────────────────────────────────────────
def duration_menu(day):
    cfg = load_config()

    current = 1
    for r in cfg["booking_rules"]:
        if r["day"] == day:
            current = r["duration"]

    keyboard = []

    for d in [1,2,3]:
        mark = "✅" if d == current else "⬜"
        keyboard.append([{
            "text": f"{mark} {d} uur",
            "callback_data": f"dur_{day}_{d}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "duration"}])

    send(f"⏱ Duration voor {day}", keyboard)


# ─────────────────────────────────────────────
# COURTS
# ─────────────────────────────────────────────
def courts_menu():
    cfg = load_config()

    keyboard = []

    for c in cfg["preferred_courts"]:
        keyboard.append([{
            "text": f"❌ {c}",
            "callback_data": f"court_remove_{c}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("🎾 Courts", keyboard)


# ─────────────────────────────────────────────
# MEMBERS
# ─────────────────────────────────────────────
def members_menu():
    cfg = load_config()

    keyboard = []

    for m in cfg["members"]:
        keyboard.append([{
            "text": f"❌ {m['name']}",
            "callback_data": f"member_remove_{m['member_id']}"
        }])

    keyboard.append([{"text": "⬅️ Back", "callback_data": "back"}])

    send("👥 Members", keyboard)


# ─────────────────────────────────────────────
# CALLBACK HANDLER
# ─────────────────────────────────────────────
def handle(cb):
    if cb["from"]["id"] != CHAT_ID:
        return

    data = cb["data"]
    cfg = load_config()

    # NAV
    if data == "back":
        return main_menu()

    if data == "refresh":
        return main_menu()

    if data == "days":
        return days_menu()

    if data == "times":
        return day_menu("times")

    if data == "duration":
        return day_menu("duration")

    if data == "courts":
        return courts_menu()

    if data == "members":
        return members_menu()

    # DAYS
    if data == "days_plus":
        cfg["days_ahead"] += 1

    if data == "days_minus":
        cfg["days_ahead"] = max(0, cfg["days_ahead"] - 1)

    # TIMES
    if data.startswith("time_"):
        _, day, t = data.split("_")

        for r in cfg["booking_rules"]:
            if r["day"] == day:
                if t in r["times"]:
                    r["times"].remove(t)
                else:
                    r["times"].append(t)

        save_config(cfg)
        return time_menu(day)

    # DURATION
    if data.startswith("dur_"):
        _, day, d = data.split("_")

        for r in cfg["booking_rules"]:
            if r["day"] == day:
                r["duration"] = int(d)

        save_config(cfg)
        return duration_menu(day)

    # COURTS
    if data.startswith("court_remove_"):
        c = int(data.split("_")[2])
        cfg["preferred_courts"].remove(c)

    # MEMBERS
    if data.startswith("member_remove_"):
        mid = data.split("_")[2]
        cfg["members"] = [m for m in cfg["members"] if m["member_id"] != mid]

    save_config(cfg)
    main_menu()


# ─────────────────────────────────────────────
# LOOP
# ─────────────────────────────────────────────
def run():
    last = None
    main_menu()

    while True:
        params = {"timeout": 10}
        if last:
            params["offset"] = last + 1

        res = requests.get(f"{BASE_URL}/getUpdates", params=params).json()

        for u in res.get("result", []):
            last = u["update_id"]

            if "callback_query" in u:
                handle(u["callback_query"])


if __name__ == "__main__":
    run()
