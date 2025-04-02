import os
import time
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime
import aiohttp
import urllib.parse

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ENCODING = os.getenv("ENCODING", "mp3")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)
player = None

FIP_STREAMS = {
    "main": {"url": os.getenv("FIP_MAIN"), "metadata": "fip"},
    "rock": {"url": os.getenv("FIP_ROCK"), "metadata": "fip_rock"},
    "jazz": {"url": os.getenv("FIP_JAZZ"), "metadata": "fip_jazz"},
    "groove": {"url": os.getenv("FIP_GROOVE"), "metadata": "fip_groove"},
    "world": {"url": os.getenv("FIP_WORLD"), "metadata": "fip_world"},
    "nouveautes": {"url": os.getenv("FIP_NOUVEAUTES"), "metadata": "fip_nouveautes"},
    "reggae": {"url": os.getenv("FIP_REGGAE"), "metadata": "fip_reggae"},
    "electro": {"url": os.getenv("FIP_ELECTRO"), "metadata": "fip_electro"},
    "hiphop": {"url": os.getenv("FIP_HIPHOP"), "metadata": "fip_hiphop"},
    "pop": {"url": os.getenv("FIP_POP"), "metadata": "fip_pop"},
    "metal": {"url": os.getenv("FIP_METAL"), "metadata": "fip_metal"},
}

guild_station_map = {}
live_messages = {}
station_cache = {}
guild_song_ids = {}
current_genres = set()
next_update_times = {}
last_song_ids = {}

@tasks.loop(seconds=1)
async def update_station_cache():
    now = int(time.time())
    async with aiohttp.ClientSession() as session:
        for genre in current_genres:
            if genre in next_update_times and now < next_update_times[genre]:
                continue

            meta = FIP_STREAMS.get(genre)
            if not meta:
                continue

            try:
                url = f"https://fip-metadata.fly.dev/api/metadata/{meta['metadata']}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        station_cache[genre] = result

                        now_block = result.get("now", {})
                        title = now_block.get("firstLine", {}).get("title")
                        artist = now_block.get("secondLine", {}).get("title")
                        start = now_block.get("startTime")
                        end = now_block.get("endTime")

                        song = now_block.get("song", {})
                        song_id = song.get("id")

                        if song_id and last_song_ids.get(genre) == song_id:
                            continue

                        if title and artist:
                            print(f"[Cache Updated] {genre}: {title} - {artist} (Start Time: {datetime.fromtimestamp(start).strftime('%H:%M:%S')} - End Time: {datetime.fromtimestamp(end).strftime('%H:%M:%S')})")
                        else:
                            print(f"[Cache Updated] {genre}: Metadata incomplete")

                        last_song_ids[genre] = song_id

                        if start and end:
                            next_update_times[genre] = end + 1
            except Exception as e:
                print(f"Failed to fetch metadata for {genre}: {e}")

@tasks.loop(seconds=1)
async def update_song_embeds():
    for guild_id, message in list(live_messages.items()):
        genre = guild_station_map.get(guild_id)
        data = station_cache.get(genre)

        if not data or "now" not in data:
            continue

        song_data = data.get("now", {}).get("song")
        song_id = song_data.get("id") if song_data else None

        if not song_id or guild_song_ids.get(guild_id) == song_id:
            continue

        embed = await fetch_metadata_embed(guild_id)
        if embed:
            try:
                await message.edit(embed=embed, view=FIPControlView())
                guild_song_ids[guild_id] = song_id
            except discord.HTTPException as e:
                if e.code == 50027:
                    print(f"[Warning] Removing stale message for guild {guild_id}")
                    live_messages.pop(guild_id, None)
                else:
                    print(f"Failed to update message for guild {guild_id}: {e}")

async def switch_station(interaction: discord.Interaction, genre: str):
    global player

    genre = genre.lower()
    if genre not in FIP_STREAMS:
        await interaction.response.send_message("Invalid genre.", ephemeral=True)
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        return

    current_genres.clear()
    current_genres.add(genre)

    channel = interaction.user.voice.channel
    stream_url = FIP_STREAMS[genre]["url"]
    guild_id = interaction.guild.id
    guild_station_map[guild_id] = genre

    vc = interaction.guild.voice_client
    if vc:
        if vc.channel != channel:
            await vc.move_to(channel)
        if vc.is_playing():
            vc.stop()
        try:
            audio = discord.FFmpegPCMAudio(stream_url)
            vc.play(audio)
        except Exception as e:
            print(f"[Error] Failed to play new stream: {e}")
            await interaction.response.send_message("Failed to play the new station stream.", ephemeral=True)
            return
        embed = await fetch_metadata_embed(guild_id)
        await interaction.response.send_message(content=f"🔄 Switched to FIP {genre} in {channel.name}", embed=embed, view=FIPControlView())
        message = await interaction.original_response()
        live_messages[guild_id] = message
        return

    try:
        player = await channel.connect()
        audio = discord.FFmpegPCMAudio(stream_url)
        player.play(audio)
        embed = await fetch_metadata_embed(guild_id)
        await interaction.response.send_message(content=f"🎶 Now playing FIP {genre} in {channel.name}", embed=embed, view=FIPControlView())
        message = await interaction.original_response()
        live_messages[guild_id] = message
    except Exception as e:
        print(f"Error: {e}")
        await interaction.response.send_message("Something went wrong.", ephemeral=True)

class StationDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name.capitalize(), value=name)
            for name in FIP_STREAMS.keys()
        ]
        super().__init__(
            placeholder="Choose a station to switch to...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        genre = self.values[0]
        await switch_station(interaction, genre)

class FIPControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StationDropdown())

    @discord.ui.button(label="Info", style=discord.ButtonStyle.primary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await fetch_metadata_embed(interaction.guild.id)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Couldn't fetch song info.", ephemeral=True)

    @discord.ui.button(label="Volume +", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            volume = getattr(vc.source, "volume", 1.0)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=min(2.0, volume + 0.1))
            await interaction.response.send_message("🔊 Volume increased.", ephemeral=True)

    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            volume = getattr(vc.source, "volume", 1.0)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=max(0.1, volume - 0.1))
            await interaction.response.send_message("🔉 Volume decreased.", ephemeral=True)

    @discord.ui.button(label="Open on Spotify", style=discord.ButtonStyle.success)
    async def open_spotify(self, interaction: discord.Interaction, button: discord.ui.Button):
        genre = guild_station_map.get(interaction.guild.id, "main")
        metadata = station_cache.get(genre, {}).get("now", {})
        title = metadata.get("firstLine", {}).get("title", "")
        artist = metadata.get("secondLine", {}).get("title", "")

        if not title or not artist:
            await interaction.response.send_message("Song metadata is missing.", ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                query = urllib.parse.quote(f"track:{title} artist:{artist}")
                search_url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"

                # Spotify's public search endpoint requires a token.
                # We'll just redirect users to a web search for now.
                web_url = f"https://open.spotify.com/search/{urllib.parse.quote(title + ' ' + artist)}"
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Search on Spotify", url=web_url))
                await interaction.response.send_message("🎧 Click below to open this song on Spotify.", view=view, ephemeral=True)
        except Exception as e:
            print(f"[Error opening song] {e}")
            await interaction.response.send_message("Something went wrong while trying to search Spotify.", ephemeral=True)

async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    data = station_cache.get(genre)

    if not data:
        return None

    try:
        song = data.get("now", {}).get("song")
        visuals = data.get("now", {}).get("visuals", {}).get("card")
        first_line = data.get("now", {}).get("firstLine", {}).get("title") or ""
        second_line = data.get("now", {}).get("secondLine", {}).get("title") or ""

        if not song:
            return None

        embed = discord.Embed(
            title=f"{first_line} – {second_line}",
            description=f"*{song['release']['title']}* ({song['year']})",
            color=discord.Color.purple()
        )
        if visuals and visuals.get("src"):
            embed.set_thumbnail(url=visuals["src"])
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()}")
        return embed
    except Exception as e:
        print(f"Error building embed: {e}")
        return None

@bot.tree.command(name="fip_join", description="Join your voice channel and play FIP Radio")
@app_commands.describe(genre="Genre: main, rock, jazz, groove, world, nouveautes, reggae, electro, hiphop, pop, metal")
async def fip_join(interaction: discord.Interaction, genre: str = "main"):
    await switch_station(interaction, genre)

@bot.tree.command(name="fip_info", description="Show the current song playing on FIP radio")
async def fip_info(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = await fetch_metadata_embed(interaction.guild.id)
    if embed:
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Couldn't fetch song info.", ephemeral=True)

@bot.tree.command(name="fip_leave", description="Leave the voice channel")
async def fip_leave(interaction: discord.Interaction):
    global player
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        player = None
        guild_station_map.pop(interaction.guild.id, None)
        live_messages.pop(interaction.guild.id, None)
        await interaction.response.send_message("Left the voice channel.")
    else:
        await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)

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

bot.run(BOT_TOKEN)
