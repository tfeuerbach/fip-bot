import aiohttp
import re

async def fetch_musicbrainz_cover(song_meta: dict):
    title = song_meta.get("title", "")
    artist = song_meta.get("artist", "")

    if not title or not artist:
        raise ValueError("Missing title or artist for MusicBrainz fallback")

    query = f'recording:"{title}" AND artist:"{artist}"'
    url = f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json&limit=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "fip-bot/1.0"}) as resp:
            if resp.status != 200:
                raise Exception(f"MusicBrainz API HTTP {resp.status}")

            data = await resp.json()
            recordings = data.get("recordings", [])
            if not recordings:
                print("[MusicBrainz] No recordings found, skipping fallback cover.")
                return None

            release_id = recordings[0]["releases"][0]["id"]

        coverart_url = f"https://coverartarchive.org/release/{release_id}/front"
        return coverart_url


async def is_url_valid(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp.status == 200
    except:
        return False