import discord
from discord import app_commands
from config import player, guild_station_map, live_messages
from metadata import fetch_metadata_embed
from handlers import switch_station
from views import FIPControlView
from db import get_stats
from table2ascii import table2ascii as t2a, PresetStyle
from handlers import bot  # ✅ Access the bot instance

def setup_commands(bot):
    @bot.tree.command(name="fip_join", description="Join your voice channel and play FIP Radio")
    @app_commands.describe(genre="Genre: main, rock, jazz, groove, world, nouveautes, reggae, electro, hiphop, pop, metal")
    async def fip_join(interaction: discord.Interaction, genre: str = "main"):
        view = FIPControlView(guild_id=interaction.guild.id)
        await switch_station(interaction, genre, view=view)

    @bot.tree.command(name="fip_leave", description="Leave the voice channel")
    async def fip_leave(interaction: discord.Interaction):
        global player
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            player = None
            guild_station_map.pop(interaction.guild.id, None)
            live_messages.pop(interaction.guild.id, None)

            # Clear bot activity
            await bot.change_presence(activity=None)

            await interaction.response.send_message("Left the voice channel.")
        else:
            await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)