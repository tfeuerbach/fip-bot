import os
import aiohttp
import psycopg2
from psycopg2.extras import execute_values
from config import FIP_STREAMS
import asyncio

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_listening (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            station TEXT NOT NULL,
            seconds_listened INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, station)
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS listening_sessions (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            station TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS station_now_playing (
            station TEXT PRIMARY KEY,
            song_id TEXT,
            title TEXT,
            start_time INTEGER,
            end_time INTEGER,
            thumbnail_url TEXT
        );
        """)
        conn.commit()

def start_session(guild_id, user_id, station, start_time):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO listening_sessions (guild_id, user_id, station, start_time)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (guild_id, user_id) DO UPDATE SET
            station = EXCLUDED.station,
            start_time = EXCLUDED.start_time;
        """, (guild_id, user_id, station, start_time))
        conn.commit()

def end_session(guild_id, user_id, end_time):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT station, start_time FROM listening_sessions
        WHERE guild_id = %s AND user_id = %s;
        """, (guild_id, user_id))
        result = cur.fetchone()

        if not result:
            return

        station, start_time = result
        seconds = int((end_time - start_time).total_seconds())

        cur.execute("""
        DELETE FROM listening_sessions
        WHERE guild_id = %s AND user_id = %s;
        """, (guild_id, user_id))

        cur.execute("""
        INSERT INTO user_listening (guild_id, user_id, station, seconds_listened)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (guild_id, user_id, station)
        DO UPDATE SET seconds_listened = user_listening.seconds_listened + EXCLUDED.seconds_listened;
        """, (guild_id, user_id, station, seconds))
        conn.commit()

def get_stats(guild_id, limit=50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT user_id, station, seconds_listened
            FROM user_listening
            WHERE guild_id = %s
            ORDER BY user_id, seconds_listened DESC
            LIMIT %s
        """, (str(guild_id), limit))
        return cur.fetchall()

def update_now_playing(station, song_id, title, start_time, end_time, thumbnail_url):
    # Title case with better handling (e.g., "in case of fire" -> "In Case of Fire")
    def title_case(s):
        return ' – '.join(part.title() for part in s.split(' – '))

    cleaned_title = title_case(title)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO station_now_playing (station, song_id, title, start_time, end_time, thumbnail_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (station)
            DO UPDATE SET
                song_id = EXCLUDED.song_id,
                title = EXCLUDED.title,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                thumbnail_url = EXCLUDED.thumbnail_url;
        """, (station, song_id, cleaned_title, start_time, end_time, thumbnail_url))
        conn.commit()

def get_station_now_playing(station):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT song_id, title, start_time, end_time, thumbnail_url
            FROM station_now_playing
            WHERE station = %s;
        """, (station,))
        return cur.fetchone()

async def populate_station_now_playing():
    async with aiohttp.ClientSession() as session:
        for genre, stream in FIP_STREAMS.items():
            try:
                url = f"https://fip-metadata.fly.dev/api/metadata/{stream['metadata']}"
                print(f"[Startup Populate] Fetching metadata for {genre} from {url}")
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"[Startup Populate Error for {genre}] HTTP {resp.status}")
                        continue

                    data = await resp.json()
                    now_block = data.get("now")
                    if not now_block:
                        raise ValueError("Missing 'now' block in metadata")

                    song = now_block.get("song")
                    song_id = song.get("id") if song else None

                    start = now_block.get("startTime")
                    end = now_block.get("endTime")

                    if start is None or end is None:
                        raise ValueError("Missing start or end time")

                    first_line = now_block.get("firstLine", {}).get("title", "")
                    second_line = now_block.get("secondLine", {}).get("title", "")
                    full_title = f"{first_line} – {second_line}"

                    visuals = now_block.get("visuals", {})
                    thumbnail_url = visuals.get("card", {}).get("src") or visuals.get("player", {}).get("src")

                    print(f"[Startup Populate] {genre}: {full_title} ({start} → {end})")
                    await asyncio.to_thread(update_now_playing, genre, song_id, full_title, start, end, thumbnail_url)

            except Exception as e:
                print(f"[Startup Populate Error for {genre}] {e}")

def get_all_station_now_playing():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT station, song_id, title, start_time, end_time, thumbnail_url FROM station_now_playing;")
        rows = cur.fetchall()
        return {row[0]: row[1:] for row in rows}  # key=station, value=(song_id, title, start_time, end_time, thumbnail)
