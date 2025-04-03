import discord
from config import guild_station_map, station_cache, FIP_STREAMS, guild_volumes
from metadata import fetch_metadata_embed
from spotify import fetch_spotify_url
from stats import send_stats  # ✅ updated

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
        from handlers import switch_station  # ⬅️ Delayed import to prevent circular reference

        genre = self.values[0]
        metadata = station_cache.get(genre, {}).get("now", {})
        title = metadata.get("firstLine", {}).get("title", "")
        artist = metadata.get("secondLine", {}).get("title", "")
        print(f"[Dropdown] Switching to: {genre} | Now playing: {title} - {artist}")

        spotify_url = await fetch_spotify_url(title, artist)
        print(f"[Dropdown] Spotify URL resolved: {spotify_url}")

        view = FIPControlView(guild_id=interaction.guild.id, spotify_url=spotify_url)
        await switch_station(interaction, genre, view=view)


class FIPControlView(discord.ui.View):
    def __init__(self, guild_id: int, spotify_url: str = None):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        self.add_item(StationDropdown())

        self.spotify_button = discord.ui.Button(
            label="Open on Spotify",
            style=discord.ButtonStyle.link,
            url=spotify_url or "https://open.spotify.com"
        )
        self.add_item(self.spotify_button)

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.primary)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_stats(interaction)

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
                await interaction.message.edit(embed=embed, view=FIPControlView(guild_id=self.guild_id))
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
                await interaction.message.edit(embed=embed, view=FIPControlView(guild_id=self.guild_id))
            await interaction.response.defer()
