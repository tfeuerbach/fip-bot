# tasks.py

import time
import aiohttp
from datetime import datetime
from discord.ext import tasks
from config import (
    FIP_STREAMS,
    current_genres,
    next_update_times,
    last_song_ids,
    station_cache,
    guild_station_map,
    live_messages,
    guild_song_ids
)
from metadata import fetch_metadata_embed
from views import FIPControlView
from spotify import fetch_spotify_url

# Periodically fetch updated metadata for currently active FIP stations
@tasks.loop(seconds=1)
async def update_station_cache():
    now = int(time.time())
    async with aiohttp.ClientSession() as session:
        for genre in current_genres:
            # Skip update if it's not time yet
            if genre in next_update_times and now < next_update_times[genre]:
                continue

            try:
                url = f"https://fip-metadata.fly.dev/api/metadata/{FIP_STREAMS[genre]['metadata']}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        station_cache[genre] = data

                        # Extract the current song ID
                        song_id = data.get("now", {}).get("song", {}).get("id")

                        # If song hasn't changed, no need to update
                        if song_id and last_song_ids.get(genre) == song_id:
                            continue

                        # Update state for new song
                        last_song_ids[genre] = song_id
                        start = data["now"].get("startTime")
                        end = data["now"].get("endTime")

                        # Schedule next update for when the song ends
                        if start and end:
                            next_update_times[genre] = end + 1
            except Exception as e:
                print(f"[Metadata Fetch Error] {e}")

# Periodically update now-playing message embeds for all guilds
@tasks.loop(seconds=1)
async def update_song_embeds():
    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        data = station_cache.get(genre)
        if not data:
            continue

        # Skip if no new song is playing
        song_id = data.get("now", {}).get("song", {}).get("id")
        if not song_id or guild_song_ids.get(guild_id) == song_id:
            continue

        # Extract title and artist for Spotify lookup
        title = data.get("now", {}).get("firstLine", {}).get("title", "")
        artist = data.get("now", {}).get("secondLine", {}).get("title", "")
        spotify_url = await fetch_spotify_url(title, artist)

        # Build and send updated embed
        embed = await fetch_metadata_embed(guild_id)
        if embed:
            try:
                # Pass Spotify URL to control view so the button is accurate
                await message.edit(embed=embed, view=FIPControlView(spotify_url=spotify_url))
                guild_song_ids[guild_id] = song_id
            except Exception as e:
                print(f"[Embed Update Error] {e}")
                # If the message is gone or cannot be edited, clean up
                live_messages.pop(guild_id, None)