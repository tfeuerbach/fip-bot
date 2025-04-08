import pytest
import asyncio
from app.embeds.metadata_embed import fetch_metadata_embed
from app.db.session_store import update_now_playing
from config import guild_station_map

guild_id = 123456789
station_key = "main"

@pytest.mark.asyncio
async def test_metadata_embed():
    # Simulate station metadata for this guild
    guild_station_map[guild_id] = station_key

    await asyncio.to_thread(update_now_playing,
        station_key,
        song_id="fake-song-id",
        title="Test Song – Test Artist",
        start_time=1700000000,
        end_time=1700000300,
        thumbnail_url="https://example.com/fake.jpg"
    )

    embed = await fetch_metadata_embed(guild_id)
    assert embed is not None
    assert embed.title == "Test Song – Test Artist"
