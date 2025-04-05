# app/commands/fip_leave.py

import discord
from config import player, guild_station_map, live_messages

def register_fip_leave(bot):
    @bot.tree.command(name="fip_leave", description="Leave the voice channel")
    async def fip_leave(interaction: discord.Interaction):
        global player
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            player = None
            guild_station_map.pop(interaction.guild.id, None)

            # Delete live embed message
            msg = live_messages.pop(interaction.guild.id, None)
            if msg:
                try:
                    await msg.delete()
                except discord.HTTPException as e:
                    print(f"[Leave Command] Failed to delete message: {e}")

            await interaction.response.send_message("Left the voice channel.", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
