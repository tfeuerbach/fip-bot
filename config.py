# config.py

import os
from dotenv import load_dotenv
import discord

# Load environment variables from .env file
load_dotenv()

# Discord bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ENCODING = os.getenv("ENCODING", "mp3")  # Optional audio encoding setting

# Spotify API credentials (used to search and link songs)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Dictionary mapping each genre to its stream URL and metadata source key
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

EMOJIS = {
    "main": "🎧",
    "rock": "🎸",
    "jazz": "🎷",
    "groove": "🕺",
    "world": "🌍",
    "nouveautes": "🆕",
    "reggae": "🌿",
    "electro": "🎛️",
    "hiphop": "🎤",
    "pop": "🎶",
    "metal": "🤘",
}

# Set up Discord bot intents (controls which events the bot receives)
intents = discord.Intents.default()
intents.message_content = True     # Needed to read user messages
intents.guilds = True              # Needed for slash commands and events
intents.voice_states = True        # Needed to join and monitor voice channels

# The active voice connection (one per guild, shared globally here)
player = None

# Maps guild ID to currently selected station
guild_station_map = {}

# Maps guild ID to the latest message the bot sent (for editing/updating)
live_messages = {}

# Tracks the last played song ID per guild (to avoid redundant embed updates)
guild_song_ids = {}

# Keeps track of which genres are being played so metadata is fetched accordingly
current_genres = set()

station_last_song_ids = {}  # station: last known song_id

# Caches "next update" times for each station to avoid unnecessary polling
next_update_times = {}

# Track current volume per guild (default: 1.0)
guild_volumes = {}

# Track station summary messages for each guild 
station_summary_messages = {}

# Cleans up strings by removing quotes and ampersands
def clean(text):
    return text.replace('"', '').replace("'", '').replace("&", ' ').strip()