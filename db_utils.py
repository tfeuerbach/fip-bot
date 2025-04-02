import os
import time
import requests
import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

fernet = Fernet(FERNET_KEY)

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("[FATAL] DATABASE_URL is not set!")
    print(f"[DB DEBUG] Connecting to: {DATABASE_URL}")
    return psycopg2.connect(DATABASE_URL)


def store_tokens(discord_id, access_token, refresh_token, expires_in=3600):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            discord_id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            expires_at BIGINT NOT NULL
        )
    """)
    encrypted_access = fernet.encrypt(access_token.encode()).decode()
    encrypted_refresh = fernet.encrypt(refresh_token.encode()).decode()
    expires_at = int(time.time()) + expires_in
    cur.execute("""
        INSERT INTO tokens (discord_id, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (discord_id) DO UPDATE
        SET access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            expires_at = EXCLUDED.expires_at
    """, (discord_id, encrypted_access, encrypted_refresh, expires_at))
    conn.commit()
    cur.close()
    conn.close()

def get_tokens(discord_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT access_token, refresh_token, expires_at FROM tokens WHERE discord_id = %s", (discord_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            print(f"[DB] No token found for discord_id: {discord_id}")
            return None

        try:
            access_token = fernet.decrypt(row[0].encode()).decode()
            refresh_token = fernet.decrypt(row[1].encode()).decode()
        except Exception as e:
            print(f"[Decrypt Error] Failed to decrypt tokens for {discord_id}: {e}")
            raise

        expires_at = row[2]
        print(f"[DB] Token fetched for {discord_id}, expires at {expires_at}, now is {int(time.time())}")

        if time.time() < expires_at:
            return {"access_token": access_token, "refresh_token": refresh_token}

        print(f"[Token Expired] Refreshing token for {discord_id}")

        token_url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        resp = requests.post(token_url, data=payload)
        data = resp.json()

        if "access_token" not in data:
            print(f"[Refresh Error] Failed to refresh token: {data}")
            return None

        new_access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        store_tokens(discord_id, new_access_token, refresh_token, expires_in)
        return {"access_token": new_access_token, "refresh_token": refresh_token}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
    