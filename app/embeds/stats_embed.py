# stats.py

import discord
from app.db.session_store import get_stats
from table2ascii import table2ascii as t2a, PresetStyle

async def build_stats_embed(guild: discord.Guild) -> discord.Embed:
    records = get_stats(str(guild.id), limit=100)
    if not records:
        return discord.Embed(
            title="📊 FIP Listening Stats",
            description="No listening data yet.",
            color=discord.Color.greyple()
        )

    body = []
    for user_id, station, seconds in records:
        minutes = seconds // 60
        try:
            member = await guild.fetch_member(int(user_id))
            username = member.display_name
        except:
            username = f"Unknown ({user_id})"
        body.append([username, station, minutes])

    output = t2a(
        header=["User", "Station", "Minutes"],
        body=body,
        style=PresetStyle.thin_compact
    )

    return discord.Embed(
        title="📊 FIP Listening Stats",
        description=f"```\n{output}\n```",
        color=discord.Color.blue()
    )
