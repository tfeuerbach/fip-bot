import os
import psycopg2
from psycopg2.extras import execute_values

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
            return  # No session found

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
