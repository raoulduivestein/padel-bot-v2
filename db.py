import json
import os

FILE = "tokens.json"


def get_tokens():
    if not os.path.exists(FILE):
        return None, None, 0

    with open(FILE) as f:
        data = json.load(f)

    return (
        data.get("refresh_token"),
        data.get("access_token"),
        data.get("expires_at", 0)
    )


def save_tokens(refresh_token, access_token, expires_at):
    with open(FILE, "w") as f:
        json.dump({
            "refresh_token": refresh_token,
            "access_token": access_token,
            "expires_at": expires_at
        }, f)


def get_access_token():
    _, token, _ = get_tokens()
    return token