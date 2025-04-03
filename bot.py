# bot.py

import discord
from discord.ext import commands
from config import BOT_TOKEN, intents
from tasks import update_station_cache, update_song_embeds
from commands import setup_commands

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    update_station_cache.start()
    update_song_embeds.start()

setup_commands(bot)
bot.run(BOT_TOKEN)