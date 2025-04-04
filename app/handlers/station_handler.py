import asyncio
import discord
import datetime
import traceback
from config import FIP_STREAMS, player, guild_station_map, live_messages, current_genres
from app.embeds.metadata_embed import fetch_metadata_embed
from app.services.spotify import fetch_spotify_url
from app.ui.views import FIPControlView
from app.db.session_store import get_station_now_playing, start_session, end_session

bot = None

def set_bot(bot_instance):
    global bot
    bot = bot_instance

async def switch_station(interaction: discord.Interaction, genre: str, view=None):
    global player

    # ✅ Always defer early to avoid timeouts
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
        if vc:
            if vc.channel != channel:
                await vc.move_to(channel)
            if vc.is_playing():
                vc.stop()
            vc.play(discord.FFmpegPCMAudio(stream_url))
            print("[DEBUG] Moved and started new stream.")
        else:
            player = await channel.connect()
            player.play(discord.FFmpegPCMAudio(stream_url))
            print("[DEBUG] Connected and started stream.")

        # ⏱ Update sessions for all non-bot users
        for member in channel.members:
            if not member.bot:
                print(f"[DEBUG] Updating session for user {member.id}")
                now = datetime.datetime.utcnow()
                end_session(str(guild_id), str(member.id), now)
                start_session(str(guild_id), str(member.id), genre, now)

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

        row = get_station_now_playing(genre)
        title = artist = ""
        if row:
            _, full_title, *_ = row
            if " – " in full_title:
                title, artist = full_title.split(" – ", 1)

        spotify_url = await fetch_spotify_url(title, artist)
        print(f"[Switch Station] Fetched Spotify URL: {spotify_url}")

        # 🎧 Update bot presence
        if title and artist and bot:
            activity = discord.Activity(type=discord.ActivityType.listening, name=f"{title} - {artist}")
            await bot.change_presence(activity=activity)

        view = FIPControlView(guild_id=guild_id, spotify_url=spotify_url)

        if guild_id in live_messages:
            await live_messages[guild_id].edit(
                content=f"🔄 Switched to FIP {genre} in {channel.name}",
                embed=embed,
                view=view
            )
            print("[DEBUG] Edited existing message.")
        else:
            await interaction.followup.send(
                content=f"🎶 Now playing FIP {genre} in {channel.name}",
                embed=embed,
                view=view
            )
            live_messages[guild_id] = await interaction.original_response()
            print("[DEBUG] Sent new message and stored reference.]")

    except Exception as e:
        print(f"[Switch Error] {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send("Something went wrong.", ephemeral=True)
        except discord.HTTPException as http_error:
            print(f"[Switch Error] Couldn't send error message: {http_error}")
