from flask import Flask, request, redirect
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
user_tokens = {}  # This should be a database in production

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
    token_data = user_tokens.get(user_id)
    if not token_data:
        return {"authorized": False}, 404
    return {"authorized": True, "access_token": token_data["access_token"]}

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

    user_tokens[state] = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }

    return "✅ You can now like songs in Discord!"

def get_access_token(discord_id):
    return user_tokens.get(str(discord_id), {}).get("access_token")

# Run this file alongside your bot
if __name__ == "__main__":
    app.run(port=8080)