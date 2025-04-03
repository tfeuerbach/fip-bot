# spotify.py

import aiohttp
import urllib.parse
import re
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Given a song title and artist, this function queries Spotify's API
# and returns a direct URL to the matching track (if found).
async def fetch_spotify_url(title, artist):
    try:
        async with aiohttp.ClientSession() as session:
            if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
                raise ValueError("Missing Spotify credentials")

            auth_data = aiohttp.BasicAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
            token_payload = {"grant_type": "client_credentials"}

            async with session.post(
                "https://accounts.spotify.com/api/token",
                data=token_payload,
                auth=auth_data
            ) as token_resp:
                token_data = await token_resp.json()
                access_token = token_data.get("access_token")

            if not access_token:
                raise Exception("Spotify token fetch failed")

            headers = {"Authorization": f"Bearer {access_token}"}
            query = f"track:{title} artist:{artist}"
            print(f"[Spotify Search] Query: {query}")
            url = f"https://api.spotify.com/v1/search?q={urllib.parse.quote(query)}&type=track&limit=1"

            async with session.get(url, headers=headers) as search_resp:
                search_data = await search_resp.json()
                items = search_data.get("tracks", {}).get("items", [])

                if not items:
                    print("[Spotify Search] No results found.")
                    return None

                first = items[0]
                print(f"[Spotify Match] Found: {first['name']} by {[a['name'] for a in first['artists']]}")

                return f"https://open.spotify.com/track/{first['id']}"

    except Exception as e:
        print(f"[Spotify Error] {e}")
        return None
