<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/FIP_logo_2021.svg/500px-FIP_logo_2021.svg.png?20220106124710" width="120px" alt="FIP logo">
</p>

<h1 align="center">🎵 FIP Radio Discord Bot 🎵</h1>

## ✨ Features

This lightweight bot streams **Radio France’s FIP stations** directly into a Discord voice channel, with live metadata and now playing info.

- 🎶 Stream FIP and all its genre stations (Jazz, Rock, Groove, etc.)
- 🧠 Auto-updating embed with now-playing info (song title, artist, release, year, cover art)
- 🔗 One-click “Open on Spotify” button (track link is pre-fetched automatically)
- 📻 Interactive dropdowns and buttons (station switch, volume, stats)
- 💬 Reuses chat messages to avoid clutter when switching stations
- 📡 Slash commands for full bot control
- 🧹 Bot automatically deletes its message when it leaves VC
- 🎨 Falls back to MusicBrainz for album covers when FIP image fails
- 🐳 Fully dockerized for self-hosting or production deployment

## 🚀 Quick Start (Docker)

Make sure you have Docker installed, then:

```bash
# Clone this repo
git clone https://github.com/yourusername/fip-bot.git
cd fip-bot

# Copy the .env example and fill in your Discord bot token + Spotify creds
cp .env.example .env

# Build and run the container
docker compose up --build -d
```

## 🔧 Environment Variables

Create a `.env` file with the following:

```env
# Required bot token from Discord Developer Portal
BOT_TOKEN=your_discord_bot_token_here

# Default encoding: mp3 or ogg
ENCODING=mp3

# FIP Stations
FIP_MAIN=https://icecast.radiofrance.fr/fip-midfi.mp3?id=radiofrance
FIP_ROCK=https://icecast.radiofrance.fr/fiprock-midfi.mp3?id=radiofrance
FIP_JAZZ=https://icecast.radiofrance.fr/fipjazz-midfi.mp3?id=radiofrance
FIP_GROOVE=https://icecast.radiofrance.fr/fipgroove-midfi.mp3?id=radiofrance
FIP_WORLD=https://icecast.radiofrance.fr/fipworld-midfi.mp3?id=radiofrance
FIP_NOUVEAUTES=https://icecast.radiofrance.fr/fipnouveautes-midfi.mp3?id=radiofrance
FIP_REGGAE=https://icecast.radiofrance.fr/fipreggae-midfi.mp3?id=radiofrance
FIP_ELECTRO=https://icecast.radiofrance.fr/fipelectro-midfi.mp3?id=radiofrance
FIP_HIPHOP=https://icecast.radiofrance.fr/fiphiphop-midfi.mp3?id=radiofrance
FIP_POP=https://icecast.radiofrance.fr/fippop-midfi.mp3?id=radiofrance
FIP_METAL=https://icecast.radiofrance.fr/fipmetal-midfi.mp3?id=radiofrance
FIP_CULTES=https://icecast.radiofrance.fr/fipcultes-midfi.mp3?id=radiofrance

# Spotify
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here

# Database
DATABASE_URL=postgresql://fipuser:fippass@db:5432/fip
```

## ⚙️ Slash Commands

- `/fip_join [genre]` — Join your VC and start a station (e.g. main, jazz, reggae, etc.)
- `/fip_leave` — Disconnect the bot from the voice channel and delete its message

## 🖱️ Embedded UI

Once connected, the bot creates an interactive message in chat with:

- 🎚 Dropdown to switch between stations
- 🔊 Volume control buttons
- 📊 Stats button — displays the top listeners per station in your server
- 🎧 **Open on Spotify** button — opens the track link directly!

## 🧠 Smart Features

- Caches current song metadata per station
- Detects and suppresses metadata updates during talk/interview segments
- Updates the same chat message when switching stations (no chat spam)
- Automatically pre-fetches Spotify track ID to generate instant links
- Falls back to MusicBrainz API to get album artwork when images are unavailable/invalid from radiofrance.fr

## 🗂️ File Structure Overview

| File / Directory                   | Purpose                                                                 |
|----------------------------------|-------------------------------------------------------------------------|
| `bot.py`                         | Entrypoint that starts the bot and registers commands & tasks          |
| `config.py`                      | Global env variables, bot state, and FIP config                        |
| `app/commands/`                  | Slash command logic                                                    |
| `app/handlers/`                  | Core logic to switch stations, VC control                              |
| `app/embeds/`                    | Embed builders (now playing, stats)                                    |
| `app/services/`                  | Spotify and MusicBrainz API calls                                      |
| `app/ui/`                        | Dropdown and button logic (Discord views)                              |
| `app/tasks/`                     | Background metadata and song embed updaters                            |
| `app/db/`                        | DB connection and session tracking                                     |
| `Dockerfile`                     | Docker image definition                                                |
| `docker-compose.yml`            | Multi-container support with database                                  |
| `requirements.txt`              | Python dependency list                                                 |
| `.env.example`                  | Sample env file to copy                                                |

## 🛠️ Contributing

Pull requests are welcome! Want to add another FIP station or feature? Go for it.

## 🧠 Built With

- [discord.py](https://github.com/Rapptz/discord.py)
- [aiohttp](https://docs.aiohttp.org/)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- Metadata from [fip-metadata.fly.dev](https://fip-metadata.fly.dev/)
- FIP Radio streams from [Radio France](https://www.radiofrance.fr/fip)

## 📄 License

MIT © 2025