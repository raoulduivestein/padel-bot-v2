import json
import os
from datetime import datetime

LOG_DIR = "logs"

def create_log_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    return f"{LOG_DIR}/run_{run_id}.json"

def append_log(file, entry):
    if not os.path.exists(file):
        data = {"events": []}
    else:
        with open(file) as f:
            data = json.load(f)

    data["events"].append({
        "timestamp": datetime.now().isoformat(),
        **entry
    })

    with open(file, "w") as f:
        json.dump(data, f, indent=2)
