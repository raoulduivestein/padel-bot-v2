from datetime import datetime, timedelta

def generate_slots(config):
    today = datetime.today()

    # ✅ Gebruik config
    target_date = today + timedelta(days=config["days_ahead"])

    weekday = target_date.strftime("%A").lower()
    slots = []

    for rule in config["booking_rules"]:
        if rule["day"] != weekday:
            continue

        for base_time in rule["times"]:
            hour, minute = map(int, base_time.split(":"))

            for i in range(rule["duration"]):
                slots.append({
                    "date": target_date.strftime("%Y-%m-%d"),
                    "time": f"{hour+i:02d}:{minute:02d}"
                })

    return slots
