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
            # Ensure Spotify credentials are set
            if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
                raise ValueError("Missing Spotify credentials")

            # Step 1: Get access token via client credentials flow
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

            # Step 2: Perform search query for the track
            headers = {"Authorization": f"Bearer {access_token}"}
            query = urllib.parse.quote(f"track:{title} artist:{artist}")
            url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"

            async with session.get(url, headers=headers) as search_resp:
                search_data = await search_resp.json()
                items = search_data.get("tracks", {}).get("items", [])

                # If no match found, return None
                if not items:
                    return None

                # Return the URL of the top result
                return f"https://open.spotify.com/track/{items[0]['id']}"

    except Exception as e:
        # Log the error and return None on failure
        print(f"[Spotify Error] {e}")
        return None