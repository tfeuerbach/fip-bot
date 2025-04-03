# commands.py

import discord
from discord import app_commands
from config import player, guild_station_map, live_messages
from metadata import fetch_metadata_embed
from handlers import switch_station
from views import FIPControlView

# Function to register slash commands onto the provided bot instance
def setup_commands(bot):
    # Slash command to join a voice channel and start playing a selected FIP station
    @bot.tree.command(name="fip_join", description="Join your voice channel and play FIP Radio")
    @app_commands.describe(genre="Genre: main, rock, jazz, groove, world, nouveautes, reggae, electro, hiphop, pop, metal")
    async def fip_join(interaction: discord.Interaction, genre: str = "main"):
        # Switch to the selected genre and update the UI with FIPControlView
        await switch_station(interaction, genre, view=FIPControlView())

    # Slash command to show current now-playing metadata for the station
    @bot.tree.command(name="fip_info", description="Show the current song playing on FIP radio")
    async def fip_info(interaction: discord.Interaction):
        await interaction.response.defer()  # Required for longer async work
        embed = await fetch_metadata_embed(interaction.guild.id)
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Couldn't fetch song info.", ephemeral=True)

    # Slash command to disconnect the bot from the voice channel
    @bot.tree.command(name="fip_leave", description="Leave the voice channel")
    async def fip_leave(interaction: discord.Interaction):
        global player
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            player = None  # Reset player object
            guild_station_map.pop(interaction.guild.id, None)  # Clean up station tracking
            live_messages.pop(interaction.guild.id, None)      # Clean up message tracking
            await interaction.response.send_message("Left the voice channel.")
        else:
            await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)