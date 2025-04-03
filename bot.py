import discord
import datetime
from discord.ext import commands
from config import BOT_TOKEN, intents, guild_station_map
from tasks import update_station_cache, update_song_embeds
from commands import setup_commands
from db import init_db, start_session, end_session

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
    init_db()
    update_station_cache.start()
    update_song_embeds.start()

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    guild_id = str(member.guild.id)
    user_id = str(member.id)

    # Joined the bot's VC
    if after.channel and member.guild.voice_client and after.channel == member.guild.voice_client.channel:
        station = guild_station_map.get(member.guild.id, "main")
        start_session(guild_id, user_id, station, datetime.datetime.utcnow())

    # Left VC or switched away
    elif (before.channel and member.guild.voice_client and before.channel == member.guild.voice_client.channel):
        end_session(guild_id, user_id, datetime.datetime.utcnow())

setup_commands(bot)
bot.run(BOT_TOKEN)
