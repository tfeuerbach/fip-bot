from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv
from db_utils import store_tokens, get_tokens

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

@app.route("/login")
def login():
    discord_id = request.args.get("user_id")
    scope = "user-library-modify"
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}&state={discord_id}"
    )
    return redirect(auth_url)

@app.route("/token/<user_id>")
def get_token(user_id):
    try:
        tokens = get_tokens(user_id)
        if not tokens:
            return {"authorized": False}, 404
        return {
            "authorized": True,
            "access_token": tokens["access_token"]
        }
    except Exception as e:
        print(f"[Auth Server Error] /token/{user_id} - {e}")
        return {"error": str(e)}, 500

@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")  # discord user id
    token_url = "https://accounts.spotify.com/api/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(token_url, data=payload)
    data = response.json()

    if "access_token" not in data or "refresh_token" not in data:
        return "❌ Spotify authorization failed."

    store_tokens(state, data["access_token"], data["refresh_token"], data.get("expires_in", 3600))

    return "✅ You can now like songs in Discord!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
