# views.py

import discord
from config import guild_station_map, station_cache, FIP_STREAMS
from metadata import fetch_metadata_embed
from spotify import fetch_spotify_url
from handlers import switch_station  # ✅ Safe now due to decoupling

# Dropdown menu to let users switch between FIP stations
class StationDropdown(discord.ui.Select):
    def __init__(self):
        # ✅ Correct: Use actual station names from FIP_STREAMS, not guild IDs
        options = [
            discord.SelectOption(label=genre.capitalize(), value=genre)
            for genre in FIP_STREAMS.keys()
        ]

        super().__init__(
            placeholder="Choose a station to switch to...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        genre = self.values[0]

        # Try to fetch a Spotify URL for the selected genre's track
        metadata = station_cache.get(genre, {}).get("now", {})
        title = metadata.get("firstLine", {}).get("title", "")
        artist = metadata.get("secondLine", {}).get("title", "")
        url = await fetch_spotify_url(title, artist)

        # Switch station and update the message view
        await switch_station(interaction, genre, view=FIPControlView(spotify_url=url))


# Main view that gets attached to each now-playing message
class FIPControlView(discord.ui.View):
    def __init__(self, spotify_url: str = None):
        super().__init__(timeout=None)  # Persistent view

        # Add dropdown to change stations
        self.add_item(StationDropdown())

        # Add a Spotify link button — fallback if no link is ready yet
        self.add_item(discord.ui.Button(
            label="Open on Spotify",
            style=discord.ButtonStyle.link,
            url=spotify_url or "https://open.spotify.com"
        ))

    # Info button — shows metadata for current song
    @discord.ui.button(label="Info", style=discord.ButtonStyle.primary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await fetch_metadata_embed(interaction.guild.id)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Couldn't fetch song info.", ephemeral=True)

    # Volume up button
    @discord.ui.button(label="Volume +", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            volume = getattr(vc.source, "volume", 1.0)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=min(2.0, volume + 0.1))
            await interaction.response.send_message("🔊 Volume increased.", ephemeral=True)

    # Volume down button
    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            volume = getattr(vc.source, "volume", 1.0)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=max(0.1, volume - 0.1))
            await interaction.response.send_message("🔉 Volume decreased.", ephemeral=True)
