import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import aiohttp

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

# Map of genre to stream URLs and metadata API keys
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

# Track current station per guild
guild_station_map = {}

async def switch_station(interaction: discord.Interaction, genre: str):
    global player

    genre = genre.lower()
    if genre not in FIP_STREAMS:
        await interaction.response.send_message("Invalid genre.", ephemeral=True)
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        return

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
        audio = discord.FFmpegPCMAudio(stream_url)
        vc.play(audio)
        embed = await fetch_metadata_embed(guild_id)
        await interaction.response.send_message(content=f"🔄 Switched to FIP {genre} in {channel.name}", embed=embed, view=FIPControlView())
        return

    try:
        player = await channel.connect()
        audio = discord.FFmpegPCMAudio(stream_url)
        player.play(audio)
        embed = await fetch_metadata_embed(guild_id)
        await interaction.response.send_message(content=f"🎶 Now playing FIP {genre} in {channel.name}", embed=embed, view=FIPControlView())
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

async def fetch_metadata_embed(guild_id):
    genre = guild_station_map.get(guild_id, "main")
    metadata_url = f"https://fip-metadata.fly.dev/api/metadata/{FIP_STREAMS[genre]['metadata']}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(metadata_url) as resp:
                data = await resp.json()

        song = data["now"].get("song")
        visuals = data["now"]["visuals"]["card"]
        first_line = data["now"]["firstLine"]["title"] or ""
        second_line = data["now"]["secondLine"]["title"] or ""

        if song is None:
            return None

        embed = discord.Embed(
            title=f"{first_line} – {second_line}",
            description=f"*{song['release']['title']}* ({song['year']})",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=visuals["src"])
        embed.set_footer(text=f"Label: {song['release']['label']} • Station: {data['stationName'].upper()}")
        return embed
    except Exception as e:
        print(f"Error: {e}")
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

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

bot.run(BOT_TOKEN)