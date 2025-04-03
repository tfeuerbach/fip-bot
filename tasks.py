# tasks.py

import time
import aiohttp
from datetime import datetime
from discord.ext import tasks
from config import FIP_STREAMS, current_genres, next_update_times, last_song_ids, station_cache, guild_station_map, live_messages, guild_song_ids
from metadata import fetch_metadata_embed
from views import FIPControlView

@tasks.loop(seconds=1)
async def update_station_cache():
    now = int(time.time())
    async with aiohttp.ClientSession() as session:
        for genre in current_genres:
            if genre in next_update_times and now < next_update_times[genre]:
                continue
            try:
                url = f"https://fip-metadata.fly.dev/api/metadata/{FIP_STREAMS[genre]['metadata']}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        station_cache[genre] = data

                        song_id = data.get("now", {}).get("song", {}).get("id")
                        if song_id and last_song_ids.get(genre) == song_id:
                            continue

                        last_song_ids[genre] = song_id
                        start = data["now"].get("startTime")
                        end = data["now"].get("endTime")
                        if start and end:
                            next_update_times[genre] = end + 1
            except Exception as e:
                print(f"[Metadata Fetch Error] {e}")

@tasks.loop(seconds=1)
async def update_song_embeds():
    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        data = station_cache.get(genre)
        if not data:
            continue

        song_id = data.get("now", {}).get("song", {}).get("id")
        if not song_id or guild_song_ids.get(guild_id) == song_id:
            continue

        embed = await fetch_metadata_embed(guild_id)
        if embed:
            try:
                await message.edit(embed=embed, view=FIPControlView())
                guild_song_ids[guild_id] = song_id
            except Exception as e:
                print(f"[Embed Update Error] {e}")
                live_messages.pop(guild_id, None)