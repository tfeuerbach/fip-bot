# metadata.py

import discord
from config import guild_station_map, station_cache, guild_volumes

async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    data = station_cache.get(genre)
    if not data:
        return None

    try:
        now_block = data.get("now", {})
        song = now_block.get("song") or {}
        visuals = (
            song.get("visuals", {}).get("card") or  # ✅ fallback 1
            now_block.get("visuals", {}).get("card")  # ✅ fallback 2
        )

        first_line = now_block.get("firstLine", {}).get("title", "")
        second_line = now_block.get("secondLine", {}).get("title", "")

        volume = guild_volumes.get(guild_id, 1.0)

        if not song:
            embed = discord.Embed(
                title="🔇 No metadata for the song currently playing",
                description="Talk segment or unavailable metadata.",
                color=discord.Color.dark_grey()
            )
            if visuals and visuals.get("src"):
                embed.set_thumbnail(url=visuals["src"])
            embed.set_footer(text=f"Station: {data['stationName'].upper()} • 🔊 Volume: {volume:.1f}")
            return embed

        embed = discord.Embed(
            title=f"{first_line} – {second_line}",
            description=f"*{song['release']['title']}* ({song['year']})",
            color=discord.Color.purple()
        )
        if visuals and visuals.get("src"):
            embed.set_thumbnail(url=visuals["src"])
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()} • 🔊 Volume: {volume:.1f}")
        return embed

    except Exception as e:
        print(f"Error building embed: {e}")
        return None
