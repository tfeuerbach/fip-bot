import discord
import datetime
from discord.ext import commands
from config import BOT_TOKEN, intents, guild_station_map
from app.handlers.station_handler import set_bot
from app.tasks.song_updater import update_station_cache, update_song_embeds, set_song_updater_bot, refresh_old_embeds 
from app.commands import setup_commands
from app.db.session_store import init_db, start_session, end_session, populate_station_now_playing

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

    set_bot(bot)
    set_song_updater_bot(bot)
    
    init_db()

    # 🚀 Populate DB before starting tasks
    await populate_station_now_playing()

    # 🌀 Start update loops
    update_station_cache.start()
    update_song_embeds.start()
    
    print(f"🚀 [on_ready] Background tasks started.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    guild_id = str(member.guild.id)
    user_id = str(member.id)

    if after.channel and member.guild.voice_client and after.channel == member.guild.voice_client.channel:
        station = guild_station_map.get(member.guild.id, "main")
        start_session(guild_id, user_id, station, datetime.datetime.utcnow())
    elif (before.channel and member.guild.voice_client and before.channel == member.guild.voice_client.channel):
        end_session(guild_id, user_id, datetime.datetime.utcnow())

setup_commands(bot)
bot.run(BOT_TOKEN)
