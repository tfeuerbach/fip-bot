# song_updater.py

import asyncio
import time
import aiohttp
from datetime import datetime
from discord.ext import tasks
from config import (
    FIP_STREAMS,
    current_genres,
    next_update_times,
    last_song_ids,
    guild_station_map,
    live_messages,
    guild_song_ids
)
from app.embeds.metadata_embed import fetch_metadata_embed
from app.ui.views import FIPControlView
from app.services.spotify import fetch_spotify_url
from app.db.session_store import get_station_now_playing, update_now_playing

@tasks.loop(seconds=1)
async def update_station_cache():
    now = int(time.time())

    async with aiohttp.ClientSession() as session:
        for genre, stream in FIP_STREAMS.items():
            try:
                row = get_station_now_playing(genre)
                if not row:
                    print(f"[Metadata Fetch] No DB row found for {genre}, skipping")
                    continue

                song_id, full_title, start_time, end_time, _ = row

                if now < end_time:
                    continue  # ✅ Song still playing, skip fetch

                url = f"https://fip-metadata.fly.dev/api/metadata/{stream['metadata']}"
                print(f"[Metadata Fetch] {genre} expired. Fetching new metadata...")

                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"[Metadata Fetch Error for {genre}] HTTP {resp.status}")
                        continue

                    data = await resp.json()
                    now_block = data.get("now")
                    if not now_block:
                        raise ValueError("Missing 'now' block")

                    song = now_block.get("song")
                    song_id = song.get("id") if song else None

                    start = now_block.get("startTime")
                    end = now_block.get("endTime")
                    if start is None or end is None:
                        raise ValueError("Missing start or end time")

                    first_line = now_block.get("firstLine", {}).get("title", "")
                    second_line = now_block.get("secondLine", {}).get("title", "")
                    full_title = f"{first_line} – {second_line}"

                    visuals = now_block.get("visuals", {})
                    thumbnail_url = visuals.get("card", {}).get("src") or visuals.get("player", {}).get("src")

                    print(f"[Metadata Update] {genre}: {full_title} ({start} → {end})")
                    await asyncio.to_thread(update_now_playing, genre, song_id, full_title, start, end, thumbnail_url)

            except Exception as e:
                print(f"[Metadata Fetch Error for {genre}] {e}")

from app.db.session_store import get_station_now_playing

@tasks.loop(seconds=1)
async def update_song_embeds():
    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        row = get_station_now_playing(genre)
        if not row:
            continue

        song_id, full_title, start_time, end_time, thumbnail_url = row

        if not song_id or guild_song_ids.get(guild_id) == song_id:
            continue

        print(f"[DEBUG] New song detected for guild {guild_id}, genre {genre}, song ID: {song_id}")

        title, artist = full_title.split(" – ") if " – " in full_title else ("", "")

        spotify_url = await fetch_spotify_url(title, artist)
        embed = await fetch_metadata_embed(guild_id)

        if embed:
            try:
                await message.edit(
                    embed=embed,
                    view=FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
                )
                guild_song_ids[guild_id] = song_id
                print(f"[DEBUG] Updated embed and view for guild {guild_id}")
            except Exception as e:
                print(f"[Embed Update Error] {e}")
                live_messages.pop(guild_id, None)

