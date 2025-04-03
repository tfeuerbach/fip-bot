# handlers.py

import discord
from config import FIP_STREAMS, player, guild_station_map, live_messages, current_genres
from metadata import fetch_metadata_embed

# Handles switching a Discord voice channel to a new FIP stream
# Accepts an optional `view` argument (a Discord UI view) to avoid circular import issues with views.py
async def switch_station(interaction: discord.Interaction, genre: str, view=None):
    global player

    # Normalize and validate genre
    genre = genre.lower()
    if genre not in FIP_STREAMS:
        await interaction.response.send_message("Invalid genre.", ephemeral=True)
        return

    # Check if user is in a voice channel
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        return

    # Set the current genre for background metadata polling
    current_genres.clear()
    current_genres.add(genre)

    # Resolve stream info and guild context
    channel = interaction.user.voice.channel
    stream_url = FIP_STREAMS[genre]["url"]
    guild_id = interaction.guild.id
    guild_station_map[guild_id] = genre

    # Either reuse the current voice client or connect to the channel
    vc = interaction.guild.voice_client
    try:
        if vc:
            if vc.channel != channel:
                await vc.move_to(channel)  # Move to the user’s channel if needed
            if vc.is_playing():
                vc.stop()  # Stop current playback before switching
            vc.play(discord.FFmpegPCMAudio(stream_url))  # Start new stream
        else:
            player = await channel.connect()  # Connect to channel
            player.play(discord.FFmpegPCMAudio(stream_url))

        # Generate embed with song info
        embed = await fetch_metadata_embed(guild_id)

        # If this guild already has a message, update it instead of sending a new one
        if guild_id in live_messages:
            await live_messages[guild_id].edit(
                content=f"🔄 Switched to FIP {genre} in {channel.name}",
                embed=embed,
                view=view  # Update the interactive controls
            )
            await interaction.response.defer()  # Acknowledge the interaction silently
        else:
            await interaction.response.send_message(
                content=f"🎶 Now playing FIP {genre} in {channel.name}",
                embed=embed,
                view=view
            )
            live_messages[guild_id] = await interaction.original_response()  # Track the message for future edits

    except Exception as e:
        print(f"[Switch Error] {e}")
        await interaction.response.send_message("Something went wrong.", ephemeral=True)