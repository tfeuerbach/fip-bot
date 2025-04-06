import asyncio
import time
import aiohttp
from datetime import datetime
from discord.ext import tasks
from discord.errors import NotFound, HTTPException
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
                    continue  # Song still playing

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

                    start_str = datetime.fromtimestamp(start).strftime("%H:%M:%S")
                    end_str = datetime.fromtimestamp(end).strftime("%H:%M:%S")
                    print(f"[Metadata Update] {genre}: {full_title} ({start_str} → {end_str})")
                    await asyncio.to_thread(update_now_playing, genre, song_id, full_title, start, end, thumbnail_url)

                    prev_song_id = station_last_song_ids.get(genre)
                    station_last_song_ids[genre] = song_id

                    if song_id and song_id != prev_song_id:
                        print(f"[Station Update Detected] {genre} → summary refresh")
                        await refresh_simple_embeds()

            except Exception as e:
                print(f"[Metadata Fetch Error for {genre}] {e}")

@tasks.loop(seconds=1)
async def update_song_embeds():
    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        row = get_station_now_playing(genre)
        if not row:
            continue

        song_id, full_title, _, _, _ = row

        if not song_id or guild_song_ids.get(guild_id) == song_id:
            continue

        print(f"[DEBUG] New song detected for guild {guild_id}, genre {genre}, song ID: {song_id}")
        title, artist = full_title.split(" – ") if " – " in full_title else ("", "")

        spotify_url = await fetch_spotify_url(title, artist)
        metadata_embed = await fetch_metadata_embed(guild_id)
        summary_embed = build_all_stations_embed()

        if not metadata_embed:
            continue

        try:
            await message.edit(
                embeds=[summary_embed, metadata_embed],
                view=FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
            )
            guild_song_ids[guild_id] = song_id
            print(f"[DEBUG] Updated embeds for guild {guild_id}")

        except (NotFound, HTTPException) as e:
            print(f"[Embed Update Error] Guild {guild_id} | {type(e).__name__}: {e}")
            if message:
                print(f"🧵 Message ID: {getattr(message, 'id', 'Unknown')}")
                print(f"📺 Channel ID: {getattr(message.channel, 'id', 'Unknown')}")

            live_messages.pop(guild_id, None)

            try:
                if not bot:
                    raise RuntimeError("Bot is not initialized")

                guild = bot.get_guild(guild_id)
                if not guild or not guild.voice_client:
                    raise RuntimeError("Missing guild or voice_client")

                channel = guild.voice_client.channel
                print(f"[AutoResend] Resending message to channel: {channel.name} (ID: {channel.id})")

                new_message = await channel.send(
                    content=f"🎶 Now playing FIP {genre} in {channel.name}",
                    embeds=[summary_embed, metadata_embed],
                    view=FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
                )
                live_messages[guild_id] = new_message
                guild_song_ids[guild_id] = song_id
                print(f"[AutoResend] ✅ Sent new message in guild {guild_id}")

            except Exception as resend_err:
                print(f"[AutoResend Error] Guild {guild_id}: {resend_err}")

@tasks.loop(minutes=10)
async def refresh_old_embeds():
    print(f"[Embed Refresh] Starting full refresh at {datetime.utcnow().isoformat()}")
    summary_embed = build_all_stations_embed()

    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        row = get_station_now_playing(genre)

        if not row:
            continue

        song_id, full_title, _, _, _ = row
        title, artist = full_title.split(" – ") if " – " in full_title else ("", "")

        spotify_url = await fetch_spotify_url(title, artist)
        metadata_embed = await fetch_metadata_embed(guild_id)

        if not metadata_embed:
            continue

        try:
            await message.edit(
                embeds=[summary_embed, metadata_embed],
                view=FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
            )
            print(f"[Embed Refresh] Updated stale embed for guild {guild_id}")
        except Exception as e:
            print(f"[Embed Refresh Error] Guild {guild_id} | {type(e).__name__}: {e}")
            print(f"🧵 Message ID: {getattr(message, 'id', 'Unknown')}")
            print(f"📺 Channel ID: {getattr(message.channel, 'id', 'Unknown')}")

async def refresh_simple_embeds():
    summary_embed = build_all_stations_embed()

    for guild_id, message in list(live_messages.items()):
        row = get_station_now_playing(guild_station_map.get(guild_id))
        if not row:
            continue

        metadata_embed = await fetch_metadata_embed(guild_id)
        if not metadata_embed:
            continue

        try:
            await message.edit(embeds=[summary_embed, metadata_embed])
            print(f"[Summary Embed] Refreshed for guild {guild_id}")
        except Exception as e:
            print(f"[Summary Embed Error] Guild {guild_id} | {type(e).__name__}: {e}")
            print(f"🧵 Message ID: {getattr(message, 'id', 'Unknown')}")
            print(f"📺 Channel ID: {getattr(message.channel, 'id', 'Unknown')}")
