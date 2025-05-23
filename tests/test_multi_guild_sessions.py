from datetime import datetime, timedelta
from app.db.session_store import start_session, end_session, get_stats, init_db

def test_multi_guild_isolation():
    init_db()

    guilds = [f"guild_{i}" for i in range(1, 6)]
    users = [f"user_{i}" for i in range(1, 6)]
    genres = ["main", "jazz", "rock", "world", "groove"]
    now = datetime.utcnow()

    for guild_id, user_id, genre in zip(guilds, users, genres):
        start_session(guild_id, user_id, genre, now)
        end_session(guild_id, user_id, now + timedelta(minutes=10))

    for i, guild_id in enumerate(guilds):
        stats = get_stats(guild_id)
        assert len(stats) == 1
        user_id, station, seconds = stats[0]
        assert user_id == users[i]
        assert station == genres[i]
        assert seconds == 600
