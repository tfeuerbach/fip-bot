import discord
import aiohttp
from config import guild_station_map, station_cache, guild_volumes
import re

async def fetch_musicbrainz_cover(song):
    try:
        title = song['release']['title']
        artist = song['interpreters'][0]

        async with aiohttp.ClientSession() as session:
            query_url = (
                "https://musicbrainz.org/ws/2/release/"
                f"?query=release:{title} AND artist:{artist}&fmt=json&limit=1"
            )
            async with session.get(query_url) as resp:
                if resp.status != 200:
                    print(f"[MusicBrainz] Failed query: {resp.status}")
                    return None
                data = await resp.json()
                if 'releases' not in data or not data['releases']:
                    print("[MusicBrainz] No release found.")
                    return None
                mbid = data['releases'][0]['id']

                coverart_url = f"https://coverartarchive.org/release/{mbid}/front"
                async with session.get(coverart_url) as image_resp:
                    if image_resp.status == 200:
                        return coverart_url
                    else:
                        print(f"[Cover Art Archive] No image found for MBID {mbid}")
                        return None
    except Exception as e:
        print(f"[MusicBrainz Error] {e}")
        return None

async def is_url_valid(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp.status == 200
    except:
        return False

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
            description=f"*{song['release']['title']}* ({song['year']})",
            color=discord.Color.purple()
        )
        if thumb_url:
            embed.set_thumbnail(url=thumb_url)
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()} • 🔊 Volume: {volume:.1f}")
        return embed

    except Exception as e:
        print(f"[Embed Error] {e}")
        return None
