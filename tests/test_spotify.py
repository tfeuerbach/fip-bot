import asyncio
import os
from app.services.spotify import fetch_spotify_url

async def test_fetch_spotify_url():
    # Known real song and artist
    url = await fetch_spotify_url("Smells Like Teen Spirit", "Nirvana")
    assert url and "open.spotify.com/track/" in url, f"Failed to fetch Spotify URL: {url}"
    print("✅ Spotify track URL:", url)

if __name__ == "__main__":
    asyncio.run(test_fetch_spotify_url())