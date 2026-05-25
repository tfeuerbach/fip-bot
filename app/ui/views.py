import discord
from config import guild_station_map, FIP_STREAMS, guild_volumes
from app.embeds.metadata_embed import fetch_metadata_embed, build_all_stations_embed
from app.services.spotify import fetch_spotify_url
from app.embeds.stats_embed import build_stats_embed


def _apply_volume(vc: discord.VoiceClient, guild_id: int, new_volume: float) -> bool:
    """Respawn the ffmpeg source with the new volume baked in. Opus sources can't be re-wrapped live."""
    from app.handlers.station_handler import (
        after_ffmpeg,
        channel_bitrate_kbps,
        make_ffmpeg_source,
    )

    genre = guild_station_map.get(guild_id, "main")
    stream = FIP_STREAMS.get(genre)
    if not stream or not stream.get("url"):
        return False

    source = make_ffmpeg_source(
        stream["url"],
        volume=new_volume,
        bitrate=channel_bitrate_kbps(vc.channel),
    )
    if vc.is_playing():
        vc.stop()
    vc.play(source, after=after_ffmpeg)
    guild_volumes[guild_id] = new_volume
    return True

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
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return
        current = guild_volumes.get(interaction.guild.id, 1.0)
        new_volume = min(2.0, round(current + 0.1, 2))
        if not _apply_volume(vc, interaction.guild.id, new_volume):
            return
        await self._refresh_embed(interaction)

    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return
        current = guild_volumes.get(interaction.guild.id, 1.0)
        new_volume = max(0.1, round(current - 0.1, 2))
        if not _apply_volume(vc, interaction.guild.id, new_volume):
            return
        await self._refresh_embed(interaction)

    async def _refresh_embed(self, interaction: discord.Interaction):
        if not interaction.message:
            return
        metadata_embed = await fetch_metadata_embed(interaction.guild.id)
        if not metadata_embed:
            return
        summary_embed = build_all_stations_embed()
        try:
            await interaction.message.edit(
                embeds=[summary_embed, metadata_embed],
                view=FIPControlView(guild_id=self.guild_id, spotify_url=self.spotify_url),
            )
        except discord.HTTPException as e:
            print(f"[Volume Refresh] {e}")


class StatsView(discord.ui.View):
    def __init__(self, guild_id: int, spotify_url: str = None):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.spotify_url = spotify_url or "https://open.spotify.com"

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        summary_embed = build_all_stations_embed()
        metadata_embed = await fetch_metadata_embed(self.guild_id)

        if metadata_embed and interaction.message:
            await interaction.message.edit(
                embeds=[summary_embed, metadata_embed],
                view=FIPControlView(guild_id=self.guild_id, spotify_url=self.spotify_url)
            )

        await interaction.response.defer()
