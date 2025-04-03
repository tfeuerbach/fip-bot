# spotify.py

import aiohttp
import urllib.parse
import re
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

async def fetch_spotify_url(title, artist):
    try:
        async with aiohttp.ClientSession() as session:
            if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
                raise ValueError("Missing Spotify credentials")

            auth_data = aiohttp.BasicAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
            token_payload = {"grant_type": "client_credentials"}
            async with session.post("https://accounts.spotify.com/api/token", data=token_payload, auth=auth_data) as token_resp:
                token_data = await token_resp.json()
                access_token = token_data.get("access_token")

            if not access_token:
                raise Exception("Spotify token fetch failed")

            headers = {"Authorization": f"Bearer {access_token}"}
            query = urllib.parse.quote(f"track:{title} artist:{artist}")
            url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"

            async with session.get(url, headers=headers) as search_resp:
                search_data = await search_resp.json()
                items = search_data.get("tracks", {}).get("items", [])
                if not items:
                    return None

                return f"https://open.spotify.com/track/{items[0]['id']}"
    except Exception as e:
        print(f"[Spotify Error] {e}")
        return None