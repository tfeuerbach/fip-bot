import discord
from db import get_stats
from table2ascii import table2ascii as t2a, PresetStyle

async def send_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    records = get_stats(str(interaction.guild.id), limit=100)

    if not records:
        await interaction.followup.send("No listening data yet.")
        return

    body = []
    for user_id, station, seconds in records:
        minutes = seconds // 60
        try:
            member = await interaction.guild.fetch_member(int(user_id))
            username = member.display_name
        except:
            username = f"Unknown ({user_id})"

        body.append([username, station, minutes])

    output = t2a(
        header=["User", "Station", "Minutes"],
        body=body,
        style=PresetStyle.thin_compact
    )

    embed = discord.Embed(
        title="📊 FIP Listening Stats",
        description=f"```\n{output}\n```",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)