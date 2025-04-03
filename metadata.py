# metadata.py

import discord
from config import guild_station_map, station_cache, FIP_STREAMS
from spotify import fetch_spotify_url  # Currently unused, but may be used for future enrichments

# Builds a Discord embed with metadata for the currently playing song
# Called when a new song plays or when the user clicks the "Info" button
async def fetch_metadata_embed(guild_id):
    # Get the genre (station) currently playing for the guild
    genre = guild_station_map.get(guild_id, "main")

    # Get the cached metadata for that station
    data = station_cache.get(genre)
    if not data:
        return None

    try:
        # Parse the metadata for the "now" playing block
        now_block = data.get("now", {})
        song = now_block.get("song") or {}  # Contains artist, release, year, etc.
        visuals = now_block.get("visuals", {}).get("card")  # Album art or fallback image
        first_line = now_block.get("firstLine", {}).get("title", "")   # Usually song title
        second_line = now_block.get("secondLine", {}).get("title", "") # Usually artist name

        # If no song metadata, assume it's a talk segment or metadata is unavailable
        if not song:
            embed = discord.Embed(
                title="🔇 No metadata for the song currently playing",
                description="Talk segment or unavailable metadata.",
                color=discord.Color.dark_grey()
            )
            if visuals and visuals.get("src"):
                embed.set_thumbnail(url=visuals["src"])  # Optional artwork
            return embed

        # Build a rich embed with song + album + artwork
        embed = discord.Embed(
            title=f"{first_line} – {second_line}",  # Title and artist
            description=f"*{song['release']['title']}* ({song['year']})",  # Album + year
            color=discord.Color.purple()
        )
        if visuals and visuals.get("src"):
            embed.set_thumbnail(url=visuals["src"])
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()}")

        return embed
    except Exception as e:
        print(f"Error building embed: {e}")
        return None  # Fallback in case of unexpected error