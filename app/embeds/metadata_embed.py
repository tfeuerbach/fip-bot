import discord
import aiohttp
from app.services.musicbrainz import fetch_musicbrainz_cover, is_url_valid
from config import guild_station_map, station_cache, guild_volumes
import re

async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    data = station_cache.get(genre)
    if not data:
        return None

    try:
        now_block = data.get("now", {})
        song = now_block.get("song") or {}
        visuals = now_block.get("visuals", {})
        thumb_url = visuals.get("card", {}).get("src") or visuals.get("player", {}).get("src")

        first_line = now_block.get("firstLine", {}).get("title", "")
        second_line = now_block.get("secondLine", {}).get("title", "")
        volume = guild_volumes.get(guild_id, 1.0)

        # ✅ Validate thumbnail, fallback if 404
        if thumb_url and not await is_url_valid(thumb_url):
            print(f"[DEBUG] Primary thumbnail invalid: {thumb_url}")
            thumb_url = await fetch_musicbrainz_cover(song)
            print(f"[DEBUG] Fallback image URL from MusicBrainz: {thumb_url}")

        if not song:
            embed = discord.Embed(
                title="🔇 No metadata for the song currently playing",
                description="Talk segment or unavailable metadata.",
                color=discord.Color.dark_grey()
            )
            if thumb_url:
                embed.set_thumbnail(url=thumb_url)
            embed.set_footer(text=f"Station: {data['stationName'].upper()} • 🔊 Volume: {volume:.1f}")
            return embed

        embed = discord.Embed(
            title=f"{first_line} – {second_line}",
            description=f"*{song['release']['title']}* ({song['year']})\n[**FIP**](https://www.radiofrance.fr/fip)",
            color=discord.Color.purple()
        )
        if thumb_url:
            embed.set_thumbnail(url=thumb_url)
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()} • 🔊 Volume: {volume:.1f}")
        return embed

    except Exception as e:
        print(f"[Embed Error] {e}")
        return None
