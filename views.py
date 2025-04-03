# views.py

import discord
from config import guild_station_map, station_cache
from metadata import fetch_metadata_embed
from spotify import fetch_spotify_url
from handlers import switch_station  # ✅ Safe now due to decoupling

# Dropdown menu to let users switch between FIP stations
class StationDropdown(discord.ui.Select):
    def __init__(self):
        # Create an option for each known station
        options = [
            discord.SelectOption(label=name.capitalize(), value=name)
            for name in guild_station_map.keys()
        ]
        super().__init__(
            placeholder="Choose a station to switch to...",
            min_values=1,
            max_values=1,
            options=options
        )

    # Called when the user selects a station from the dropdown
    async def callback(self, interaction: discord.Interaction):
        genre = self.values[0]
        # Switch the station and update the message view
        await switch_station(interaction, genre, view=FIPControlView())

# Main view that gets attached to each now-playing message
class FIPControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.add_item(StationDropdown())  # Add the dropdown to the view

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

    # Open on Spotify button — sets its URL dynamically via pre-fetched track
    @discord.ui.button(label="Open on Spotify", style=discord.ButtonStyle.link, custom_id="open_spotify_button")
    async def open_spotify(self, interaction: discord.Interaction, button: discord.ui.Button):
        genre = guild_station_map.get(interaction.guild.id, "main")
        metadata = station_cache.get(genre, {}).get("now", {})
        title = metadata.get("firstLine", {}).get("title", "")
        artist = metadata.get("secondLine", {}).get("title", "")
        url = await fetch_spotify_url(title, artist)
        if url:
            button.url = url  # Dynamically sets the button’s link