import time
import os
import requests

# Alleen nodig als je lokaal fallback wil houden
try:
    from db import get_tokens, save_tokens
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False


TOKEN_URL = "https://digitalmanager.davidlloyd.co.uk/oauth2/default/v1/token"
CLIENT_ID = "0oa3n4dj2s9UuXIRt417"


# 🔐 .env loader (simpel, zonder extra package)
def load_env():
    if not os.path.exists(".env"):
        return

    with open(".env") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


# 🔐 Refresh token ophalen
def get_refresh_token():
    load_env()

    env_token = os.getenv("REFRESH_TOKEN")

    if env_token:
        print("🔐 Refresh token uit .env")
        return env_token

    if DB_AVAILABLE:
        refresh_token, _, _ = get_tokens()
        print("💾 Refresh token uit tokens.json")
        return refresh_token

    raise Exception("❌ Geen refresh token gevonden")


# 🔄 Refresh access token
def refresh():
    refresh_token = get_refresh_token()

    print("🔄 Token refresh gestart...")

    r = requests.post(
        TOKEN_URL,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID
        },
        timeout=20
    )

    print("📡 Status:", r.status_code)
    print("📡 Response:", r.text)

    r.raise_for_status()
    data = r.json()

    new_refresh_token = data.get("refresh_token", refresh_token)
    access_token = data["access_token"]
    expires_in = data["expires_in"]

    expires_at = int(time.time()) + expires_in

    print(f"⏳ Token geldig voor {expires_in} sec")

    # 💾 lokaal opslaan (optioneel)
    if DB_AVAILABLE:
        try:
            save_tokens(
                refresh_token=new_refresh_token,
                access_token=access_token,
                expires_at=expires_at
            )
            print("💾 Tokens opgeslagen in tokens.json")
        except Exception as e:
            print("⚠️ Opslaan mislukt:", e)

    # 🔥 BELANGRIJK: check of refresh token verandert
    if new_refresh_token != refresh_token:
        print("🆕 NIEUWE REFRESH TOKEN:")
        print(new_refresh_token)
        print("👉 Update je .env bestand!")

    return access_token


# ✅ Geldige token ophalen
def get_valid_token():
    load_env()

    if DB_AVAILABLE:
        _, access_token, expires_at = get_tokens()
    else:
        access_token = None
        expires_at = 0

    now = int(time.time())

    print("🕒 Nu:", now)
    print("🕒 Expiry:", expires_at)

    # 🔄 refresh als nodig
    if not access_token or now > expires_at - 60:
        print("⚠️ Token verlopen → refresh")
        return refresh()

    print("✅ Token nog geldig")
    return access_token


# ▶️ Manual run
if __name__ == "__main__":
    print("🚀 Handmatige token refresh")
    refresh()