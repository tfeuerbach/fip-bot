import sys
import os
import asyncio

from app.embeds.metadata_embed import fetch_metadata_embed
from app.db.session_store import update_now_playing
from config import guild_station_map

guild_id = 123456789
station_key = "main"

# Prepare fake metadata into the DB-compatible structure
async def prepare_fake_metadata():
    # Map this guild to the 'main' station
    guild_station_map[guild_id] = station_key

    await asyncio.to_thread(update_now_playing,
        station_key,
        song_id="fake-song-id",
        title="Test Song – Test Artist",
        start_time=1700000000,
        end_time=1700000300,
        thumbnail_url="https://example.com/fake.jpg"
    )

async def test_metadata_embed():
    await prepare_fake_metadata()
    embed = await fetch_metadata_embed(guild_id)
    assert embed and embed.title, "Failed to fetch or build metadata embed"
    print("✅ Embed Title:", embed.title)
    print("✅ Embed Description:", embed.description)

if __name__ == "__main__":
    asyncio.run(test_metadata_embed())
