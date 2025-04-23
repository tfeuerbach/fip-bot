import pytest
from app.services.spotify import fetch_spotify_url

@pytest.mark.asyncio
async def test_fetch_spotify_url():
    url = await fetch_spotify_url("Smells Like Teen Spirit", "Nirvana")
    assert url and "open.spotify.com/track/" in url
