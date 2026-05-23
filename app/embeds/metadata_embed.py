import asyncio
import discord
from app.db.session_store import get_station_now_playing, get_all_station_now_playing
from config import guild_station_map, guild_volumes, EMOJIS, normalize_pikapi_url

FIP_LOGO_FALLBACK = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    "1/16/FIP_logo_2021.svg/2048px-FIP_logo_2021.svg.png"
)


async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    row = await asyncio.to_thread(get_station_now_playing, genre)

    if not row:
        print(f"[Metadata Embed] No metadata found in DB for station: {genre}")
        return None

    song_id, full_title, start_time, end_time, thumb_url = row
    volume = guild_volumes.get(guild_id, 1.0)

    title = artist = ""
    if full_title and " – " in full_title:
        title, artist = full_title.split(" – ", 1)

    thumb_url = normalize_pikapi_url(thumb_url) or FIP_LOGO_FALLBACK

    has_title = bool(title.strip() or artist.strip())

    # Treat as talk/gap only when nothing usable came back from the API.
    if not song_id and not has_title:
        embed = discord.Embed(
            title="FIP",
            description="Talk segment or unavailable metadata.",
            color=discord.Color.dark_grey(),
        )
        embed.set_thumbnail(url=thumb_url)
        embed.set_footer(text=f"Station: {genre.upper()} • 🔊 Volume: {volume:.1f}")
        return embed

    description_lines = ["[**FIP**](https://www.radiofrance.fr/fip)"]
    if start_time and end_time:
        description_lines.append(f"Start: <t:{start_time}:t> • End: <t:{end_time}:t>")

    embed = discord.Embed(
        title=f"{title} – {artist}" if artist else title,
        description="\n".join(description_lines),
        color=discord.Color.purple(),
    )
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