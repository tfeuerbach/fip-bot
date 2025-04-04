import aiohttp
import re

async def fetch_musicbrainz_cover(song):
    try:
        title = song['release']['title']
        artist = song['interpreters'][0]

        async with aiohttp.ClientSession() as session:
            query_url = (
                "https://musicbrainz.org/ws/2/release/"
                f"?query=release:{title} AND artist:{artist}&fmt=json&limit=1"
            )
            async with session.get(query_url) as resp:
                if resp.status != 200:
                    print(f"[MusicBrainz] Failed query: {resp.status}")
                    return None
                data = await resp.json()
                if 'releases' not in data or not data['releases']:
                    print("[MusicBrainz] No release found.")
                    return None
                mbid = data['releases'][0]['id']

                coverart_url = f"https://coverartarchive.org/release/{mbid}/front"
                async with session.get(coverart_url) as image_resp:
                    if image_resp.status == 200:
                        return coverart_url
                    else:
                        print(f"[Cover Art Archive] No image found for MBID {mbid}")
                        return None
    except Exception as e:
        print(f"[MusicBrainz Error] {e}")
        return None

async def is_url_valid(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp.status == 200
    except:
        return False