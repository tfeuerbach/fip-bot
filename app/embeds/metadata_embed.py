import discord
from app.services.musicbrainz import fetch_musicbrainz_cover, is_url_valid
from app.db.session_store import get_station_now_playing, get_all_station_now_playing
from config import guild_station_map, guild_volumes, FIP_STREAMS, EMOJIS

async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    row = get_station_now_playing(genre)

    if not row:
        print(f"[Metadata Embed] No metadata found in DB for station: {genre}")
        return None

    song_id, full_title, start_time, end_time, thumb_url = row
    volume = guild_volumes.get(guild_id, 1.0)

    title = artist = ""
    if full_title and " – " in full_title:
        title, artist = full_title.split(" – ", 1)

    # Check and validate thumbnail
    if thumb_url and not await is_url_valid(thumb_url):
        print(f"[Metadata Embed] Invalid thumbnail URL, falling back: {thumb_url}")
        thumb_url = await fetch_musicbrainz_cover({"title": title, "artist": artist})
        print(f"[Metadata Embed] MusicBrainz fallback URL: {thumb_url}")
        if not thumb_url:
            thumb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/FIP_logo_2021.svg/2048px-FIP_logo_2021.svg.png"
            print("[Metadata Embed] Final fallback thumbnail set to FIP logo.")

    # Handle missing song
    if not song_id:
        embed = discord.Embed(
            title=f"{title} – {artist}",
            description="Talk segment or unavailable metadata.",
            color=discord.Color.dark_grey()
        )
        if thumb_url:
            embed.set_thumbnail(url=thumb_url)
        embed.set_footer(text=f"Station: {genre.upper()} • 🔊 Volume: {volume:.1f}")
        return embed

    # Build embed
    embed = discord.Embed(
        title=f"{title} – {artist}",
        description=f"[**FIP**](https://www.radiofrance.fr/fip)\nStart: <t:{start_time}:t> • End: <t:{end_time}:t>",
        color=discord.Color.purple()
    )
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)
    embed.set_footer(text=f"Station: {genre.upper()} • 🔊 Volume: {volume:.1f}")
    return embed

STATION_ORDER = list(EMOJIS.keys())

def build_all_stations_embed():
    embed = discord.Embed(
        title="📻 FIP Station Summary",
        color=0x9b59b6
    )

    now_playing = get_all_station_now_playing()
    lines = []

    for genre in STATION_ORDER:
        emoji = EMOJIS[genre]
        entry = now_playing.get(genre)

        if entry:
            _, title, *_ = entry
            lines.append(f"{emoji} **{genre.capitalize()}**\n{title}\n")
        else:
            lines.append(f"{emoji} **{genre.capitalize()}**\n_No data available_\n")

    embed.description = "\n".join(lines)
    return embed