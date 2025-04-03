# config.py

import os
from dotenv import load_dotenv
import discord

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ENCODING = os.getenv("ENCODING", "mp3")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

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

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# formerly state.py

player = None

# Server-specific state
guild_station_map = {}
live_messages = {}
station_cache = {}
guild_song_ids = {}
current_genres = set()
next_update_times = {}
last_song_ids = {}

# from utils.py

def clean(text):
    return text.replace('"', '').replace("'", '').replace("&", ' ').strip()