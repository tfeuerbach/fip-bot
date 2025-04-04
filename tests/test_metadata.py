import asyncio
from app.embeds.metadata_embed import fetch_metadata_embed
from config import guild_station_map, station_cache

# Mock some test data (simulating what the background task would populate)
station_cache["main"] = {
    "now": {
        "firstLine": {"title": "Test Song"},
        "secondLine": {"title": "Test Artist"},
        "song": {
            "release": {
                "title": "Fake Album",
                "label": "Fake Label"
            },
            "year": "2023",
            "interpreters": ["Test Artist"]
        },
        "visuals": {
            "card": {"src": "https://example.com/fake.jpg"}
        }
    },
    "stationName": "fip"
}
guild_station_map[123456789] = "main"  # Simulate a fake guild

async def test_metadata_embed():
    embed = await fetch_metadata_embed(123456789)
    assert embed and embed.title, "Failed to fetch or build metadata embed"
    print("✅ Embed Title:", embed.title)
    print("✅ Embed Description:", embed.description)

if __name__ == "__main__":
    asyncio.run(test_metadata_embed())