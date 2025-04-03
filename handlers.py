# handlers.py

import discord
from config import FIP_STREAMS
from state import player, guild_station_map, live_messages, current_genres
from metadata import fetch_metadata_embed

# Let the caller pass the view, to avoid circular import
async def switch_station(interaction: discord.Interaction, genre: str, view=None):
    global player

    genre = genre.lower()
    if genre not in FIP_STREAMS:
        await interaction.response.send_message("Invalid genre.", ephemeral=True)
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        return

    current_genres.clear()
    current_genres.add(genre)

    channel = interaction.user.voice.channel
    stream_url = FIP_STREAMS[genre]["url"]
    guild_id = interaction.guild.id
    guild_station_map[guild_id] = genre

    vc = interaction.guild.voice_client
    try:
        if vc:
            if vc.channel != channel:
                await vc.move_to(channel)
            if vc.is_playing():
                vc.stop()
            vc.play(discord.FFmpegPCMAudio(stream_url))
        else:
            player = await channel.connect()
            player.play(discord.FFmpegPCMAudio(stream_url))

        embed = await fetch_metadata_embed(guild_id)
        if guild_id in live_messages:
            await live_messages[guild_id].edit(
                content=f"🔄 Switched to FIP {genre} in {channel.name}",
                embed=embed,
                view=view
            )
            await interaction.response.defer()
        else:
            await interaction.response.send_message(
                content=f"🎶 Now playing FIP {genre} in {channel.name}",
                embed=embed,
                view=view
            )
            live_messages[guild_id] = await interaction.original_response()
    except Exception as e:
        print(f"[Switch Error] {e}")
        await interaction.response.send_message("Something went wrong.", ephemeral=True)
