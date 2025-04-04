import discord

async def update_bot_activity(bot, title, artist):
    if title and artist:
        activity = discord.Activity(type=discord.ActivityType.listening, name=f"{title} - {artist}")
        await bot.change_presence(activity=activity)