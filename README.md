<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/FIP_logo_2021.svg/500px-FIP_logo_2021.svg.png?20220106124710" width="120px" alt="FIP logo">
</p>

<h1 align="center">🎵 FIP Radio Discord Bot 🎵</h1>

## ✨ Features

This lightweight bot lets users stream **Radio France’s FIP stations** directly into a Discord voice channel.

- 🎶 Listen to FIP and its genre stations (Jazz, Rock, Groove, etc.)
- 📻 Interactive UI in Discord with dropdowns & buttons
- 📡 Slash commands for full control
- 🔊 Change stations, control volume, get now playing
- 🐳 Fully dockerized for production use or local hosting

## 🚀 Quick Start (Docker)

Make sure you have Docker installed, then:

```bash
# Clone this repo
git clone https://github.com/yourusername/fip-bot.git
cd fip-bot

# Copy the .env example and fill in your Discord bot token
cp .env.example .env

# Build and run the container
docker compose up --build -d
```

## 🔧 Environment Variables

Create a `.env` file with the following:

```env
BOT_TOKEN=your_discord_bot_token
ENCODING=mp3

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
```

## ⚙️ Commands

- `/fip_join [genre]` — Join your VC and start a station (e.g. main, jazz, reggae, etc.)
- `/fip_info` — Show now playing metadata (song title, release, artwork)
- `/fip_leave` — Leave the voice channel

You can also interact using the **GUI dropdown** and buttons embedded after joining a station.

## 📸 Screenshots

Coming soon!

## 🛠️ Contributing

PRs welcome! If you'd like to improve or add more stations, feel free to submit changes.

## 🧠 Built With

- [discord.py](https://github.com/Rapptz/discord.py)
- [aiohttp](https://docs.aiohttp.org/)
- FIP Radio streams from [Radio France](https://www.radiofrance.fr/fip)

## 📄 License

MIT © 2025