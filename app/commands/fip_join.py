# app/commands/fip_join.py

import discord
from discord import app_commands
from app.ui.views import FIPControlView
from app.handlers.station_handler import switch_station

def register_fip_join(bot):
    @bot.tree.command(name="fip_join", description="Join your voice channel and play FIP Radio")
    @app_commands.describe(genre="Genre: main, rock, jazz, groove, world, nouveautes, reggae, electro, hiphop, pop, metal")
    async def fip_join(interaction: discord.Interaction, genre: str = "main"):
        view = FIPControlView(guild_id=interaction.guild.id)
        await switch_station(interaction, genre, view=view)
