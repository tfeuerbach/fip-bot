import asyncio
import time
import aiohttp
from datetime import datetime
from discord.ext import tasks
from config import (
    FIP_STREAMS,
    guild_station_map,
    live_messages,
    guild_song_ids,
    station_last_song_ids,
)
from app.embeds.metadata_embed import fetch_metadata_embed, build_all_stations_embed
from app.ui.views import FIPControlView
from app.services.spotify import fetch_spotify_url
from app.db.session_store import get_station_now_playing, update_now_playing

bot = None

def set_song_updater_bot(bot_instance):
    global bot
    bot = bot_instance

async def resend_message(guild_id, channel, genre, song_id):
    if not bot or not channel:
        print(f"[Resend] Skipped resend for guild {guild_id} — missing bot or channel.")
        return

    title, artist = ("", "")
    row = get_station_now_playing(genre)
    if row:
        _, full_title, *_ = row
        if " – " in full_title:
            title, artist = full_title.split(" – ", 1)

    spotify_url = await fetch_spotify_url(title, artist)
    metadata_embed = await fetch_metadata_embed(guild_id)
    summary_embed = build_all_stations_embed()

    if not metadata_embed:
        print(f"[Resend] Skipped resend — no metadata for guild {guild_id}")
        return

    new_message = await channel.send(
        content=f"🎶 Now playing FIP {genre} in {channel.name}",
        embeds=[summary_embed, metadata_embed],
        view=FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
    )

    live_messages[guild_id] = {"message": new_message, "channel": channel}
    guild_song_ids[guild_id] = song_id
    print(f"[Resend] ✅ Sent new message for guild {guild_id}")

@tasks.loop(seconds=1)
async def update_station_cache():
    now = int(time.time())
    async with aiohttp.ClientSession() as session:
        for genre, stream in FIP_STREAMS.items():
            try:
                row = get_station_now_playing(genre)
                if not row:
                    continue

                song_id, full_title, start_time, end_time, _ = row
                if now < end_time:
                    continue

                url = f"https://fip-metadata.fly.dev/api/metadata/{stream['metadata']}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue

                    data = await resp.json()
                    now_block = data.get("now")
                    if not now_block:
                        continue

                    song = now_block.get("song")
                    song_id = song.get("id") if song else None
                    start = now_block.get("startTime")
                    end = now_block.get("endTime")
                    if start is None or end is None:
                        continue

                    first_line = now_block.get("firstLine", {}).get("title", "")
                    second_line = now_block.get("secondLine", {}).get("title", "")
                    full_title = f"{first_line} – {second_line}"
                    visuals = now_block.get("visuals", {})
                    thumbnail_url = visuals.get("card", {}).get("src") or visuals.get("player", {}).get("src")

                    await asyncio.to_thread(update_now_playing, genre, song_id, full_title, start, end, thumbnail_url)
                    prev_song_id = station_last_song_ids.get(genre)
                    station_last_song_ids[genre] = song_id

                    if song_id and song_id != prev_song_id:
                        print(f"[Station Update] New song for {genre} → refreshing")
                        await refresh_simple_embeds()

            except Exception as e:
                print(f"[Cache Error] {genre}: {e}")

@tasks.loop(seconds=1)
async def update_song_embeds():
    now = int(time.time())

    for guild_id, data in list(live_messages.items()):
        message = data.get("message")
        channel = data.get("channel")
        genre = guild_station_map.get(guild_id)

        row = get_station_now_playing(genre)
        if not row:
            continue

        song_id, _, start_time, _, _ = row
        prev_song_id = guild_song_ids.get(guild_id)

        is_new_song = song_id and song_id != prev_song_id
        is_old_message = now - start_time >= 1800  # 30 minutes

        if is_new_song or is_old_message:
            if message:
                try:
                    await message.delete()
                except Exception:
                    pass  # Silently ignore delete errors
            live_messages.pop(guild_id, None)
            await resend_message(guild_id, channel, genre, song_id)

@tasks.loop(minutes=10)
async def refresh_simple_embeds():
    summary_embed = build_all_stations_embed()
    for guild_id, data in list(live_messages.items()):
        message = data.get("message")
        channel = data.get("channel")
        row = get_station_now_playing(guild_station_map.get(guild_id))
        if not row:
            continue

        metadata_embed = await fetch_metadata_embed(guild_id)
        if not metadata_embed:
            continue

        try:
            await message.edit(embeds=[summary_embed, metadata_embed])
        except Exception as e:
            print(f"[Refresh Embed Error] Guild {guild_id}: {e}")
