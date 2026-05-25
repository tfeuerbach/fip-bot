import asyncio
import discord
import datetime
import traceback
import config
from config import FIP_STREAMS, guild_station_map, live_messages, current_genres, station_summary_messages, guild_volumes
from app.embeds.metadata_embed import fetch_metadata_embed, build_all_stations_embed
from app.services.spotify import fetch_spotify_url
from app.ui.views import FIPControlView
from app.db.session_store import get_station_now_playing, start_session, end_session

bot = None

# Input-side flags for ffmpeg (placed before -i). Aggressive reconnect + read timeout
# keep long-running icecast sessions alive through transient drops.
FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 "
    "-reconnect_streamed 1 "
    "-reconnect_at_eof 1 "
    "-reconnect_delay_max 2 "
    "-rw_timeout 15000000"  # 15s read/write timeout (microseconds)
)


def set_bot(bot_instance):
    global bot
    bot = bot_instance


def after_ffmpeg(error):
    if error:
        print(f"[FFmpeg Error] {error}")
    else:
        print("[FFmpeg] Stream ended or stopped cleanly.")


def make_ffmpeg_source(stream_url: str, *, volume: float = 1.0, bitrate: int = 128) -> discord.FFmpegOpusAudio:
    """Build an Opus source. ffmpeg encodes opus directly so Python doesn't re-encode every frame."""
    output_opts = []
    if abs(volume - 1.0) > 1e-3:
        output_opts.append(f"-filter:a volume={volume:.3f}")
    return discord.FFmpegOpusAudio(
        stream_url,
        bitrate=bitrate,
        before_options=FFMPEG_BEFORE_OPTIONS,
        options=" ".join(output_opts) if output_opts else None,
    )


def channel_bitrate_kbps(channel: discord.abc.Connectable, *, default: int = 96) -> int:
    """Clamp the channel's bitrate to the libopus-friendly range. Falls back to a safe default."""
    bps = getattr(channel, "bitrate", None) or default * 1000
    return max(64, min(bps // 1000, 384))

async def wait_voice_ready(voice_client: discord.VoiceClient, *, timeout: float = 15.0) -> None:
    """Poll until the voice client reports connected; covers post-handshake settle time."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if voice_client.is_connected():
            return
        await asyncio.sleep(0.05)
    raise discord.ClientException("Voice client did not become ready in time.")


async def switch_station(interaction: discord.Interaction, genre: str, view=None):
    if not interaction.response.is_done():
        await interaction.response.defer()

    genre = genre.lower()

    if genre not in FIP_STREAMS:
        await interaction.followup.send("Invalid genre.", ephemeral=True)
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("You're not in a voice channel!", ephemeral=True)
        return

    current_genres.clear()
    current_genres.add(genre)

    channel = interaction.user.voice.channel
    stream_url = FIP_STREAMS[genre]["url"]
    guild_id = interaction.guild.id
    guild_station_map[guild_id] = genre

    print(f"[DEBUG] Starting switch to station: {genre}")
    print(f"[DEBUG] Stream URL: {stream_url}")

    vc = interaction.guild.voice_client
    try:
        if vc and vc.channel != channel:
            await vc.move_to(channel)
            await wait_voice_ready(vc)
        elif not vc:
            vc = await channel.connect(timeout=60.0, reconnect=True)
            await wait_voice_ready(vc)

        config.player = vc

        volume = guild_volumes.get(guild_id, 1.0)
        ffmpeg_audio = make_ffmpeg_source(
            stream_url,
            volume=volume,
            bitrate=channel_bitrate_kbps(channel),
        )

        if vc.is_playing():
            vc.stop()
        vc.play(ffmpeg_audio, after=after_ffmpeg)
        print(f"[DEBUG] Playing {genre} at {volume:.1f}x in {channel.name}.")

        # Sessions: refresh listening rows for non-bot members in the channel.
        now = datetime.datetime.utcnow()
        for member in channel.members:
            if member.bot:
                continue
            await asyncio.to_thread(end_session, str(guild_id), str(member.id), now)
            await asyncio.to_thread(start_session, str(guild_id), str(member.id), genre, now)

        embed = None
        for i in range(5):
            embed = await fetch_metadata_embed(guild_id)
            if embed:
                print(f"[DEBUG] Metadata fetched on try {i+1}")
                break
            await asyncio.sleep(0.5)

        if not embed:
            print("[DEBUG] Metadata not found. Using fallback embed.")
            embed = discord.Embed(
                title=f"🎶 Now playing FIP {genre.capitalize()}",
                description="Metadata is loading...",
                color=discord.Color.blurple()
            )

        row = await asyncio.to_thread(get_station_now_playing, genre)
        title = artist = ""
        full_title = ""
        if row:
            _, full_title, *_ = row
            if " – " in full_title:
                title, artist = full_title.split(" – ", 1)

        spotify_url = await fetch_spotify_url(title, artist)
        print(f"[Switch Station] Fetched Spotify URL: {spotify_url}")

        view = FIPControlView(guild_id=guild_id, spotify_url=spotify_url)
        summary_embed = build_all_stations_embed()

        # Updated live_messages structure handling
        msg_data = live_messages.get(guild_id)

        if msg_data:
            message = msg_data["message"]
            await message.edit(
                content=f"🔄 Switched to FIP {genre} in {channel.name}",
                embeds=[summary_embed, embed],
                view=view
            )
            print("[DEBUG] Edited existing message.")
        else:
            await interaction.followup.send(
                content=f"🎶 Now playing FIP {genre} in {channel.name}",
                embeds=[summary_embed, embed],
                view=view
            )
            sent_message = await interaction.original_response()
            live_messages[guild_id] = {"message": sent_message, "channel": interaction.channel}
            station_summary_messages[guild_id] = sent_message
            print("[DEBUG] Sent new message and stored reference.]")

    except Exception as e:
        print(f"[Switch Error] {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send("Something went wrong.", ephemeral=True)
        except discord.HTTPException as http_error:
            print(f"[Switch Error] Couldn't send error message: {http_error}")