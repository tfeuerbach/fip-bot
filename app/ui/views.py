import discord
from config import guild_station_map, FIP_STREAMS, guild_volumes
from app.embeds.metadata_embed import fetch_metadata_embed
from app.services.spotify import fetch_spotify_url
from app.embeds.stats_embed import build_stats_embed

class StationDropdown(discord.ui.Select):
    def __init__(self):
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
        from app.handlers.station_handler import switch_station
        from app.db.session_store import get_station_now_playing

        if not interaction.response.is_done():
            await interaction.response.defer()

        genre = self.values[0]
        row = get_station_now_playing(genre)

        title = artist = ""
        if row and row[1]:  # full_title
            parts = row[1].split(" – ")
            if len(parts) == 2:
                title, artist = parts

        print(f"[Dropdown] Switching to: {genre} | Now playing: {title} - {artist}")

        spotify_url = await fetch_spotify_url(title, artist)
        print(f"[Dropdown] Spotify URL resolved: {spotify_url}")

        view = FIPControlView(guild_id=interaction.guild.id, spotify_url=spotify_url)
        await switch_station(interaction, genre, view=view)


class FIPControlView(discord.ui.View):
    def __init__(self, guild_id: int, spotify_url: str = None):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.spotify_url = spotify_url or "https://open.spotify.com"

        self.add_item(StationDropdown())

        self.spotify_button = discord.ui.Button(
            label="Open on Spotify",
            style=discord.ButtonStyle.link,
            url=self.spotify_url
        )
        self.add_item(self.spotify_button)

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.primary)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await build_stats_embed(interaction.guild)
        await interaction.message.edit(embed=embed, view=StatsView(guild_id=self.guild_id, spotify_url=self.spotify_url))
        await interaction.response.defer()

    @discord.ui.button(label="Volume +", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            current = guild_volumes.get(interaction.guild.id, 1.0)
            new_volume = min(2.0, current + 0.1)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=new_volume)
            guild_volumes[interaction.guild.id] = new_volume

            embed = await fetch_metadata_embed(interaction.guild.id)
            if embed and interaction.message:
                await interaction.message.edit(embed=embed, view=FIPControlView(guild_id=self.guild_id, spotify_url=self.spotify_url))
            await interaction.response.defer()

    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and hasattr(vc, "source"):
            current = guild_volumes.get(interaction.guild.id, 1.0)
            new_volume = max(0.1, current - 0.1)
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=new_volume)
            guild_volumes[interaction.guild.id] = new_volume

            embed = await fetch_metadata_embed(interaction.guild.id)
            if embed and interaction.message:
                await interaction.message.edit(embed=embed, view=FIPControlView(guild_id=self.guild_id, spotify_url=self.spotify_url))
            await interaction.response.defer()


class StatsView(discord.ui.View):
    def __init__(self, guild_id: int, spotify_url: str = None):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.spotify_url = spotify_url or "https://open.spotify.com"

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await fetch_metadata_embed(self.guild_id)
        if embed and interaction.message:
            await interaction.message.edit(embed=embed, view=FIPControlView(guild_id=self.guild_id, spotify_url=self.spotify_url))
        await interaction.response.defer()
