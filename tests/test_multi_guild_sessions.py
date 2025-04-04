import pytest
from datetime import datetime, timedelta
from app.db.session_store import start_session, end_session, get_all_sessions

@pytest.mark.asyncio
async def test_multi_guild_isolation():
    guilds = [f"guild_{i}" for i in range(1, 6)]
    users = [f"user_{i}" for i in range(1, 6)]
    genres = ["main", "jazz", "rock", "world", "groove"]

    now = datetime.utcnow()

    # Start sessions for 5 different guilds
    for guild_id, user_id, genre in zip(guilds, users, genres):
        start_session(guild_id, user_id, genre, now)

    # End sessions a few minutes later
    for guild_id, user_id in zip(guilds, users):
        end_session(guild_id, user_id, now + timedelta(minutes=10))

    # Fetch all sessions and group them by guild
    all_sessions = get_all_sessions()
    grouped = {}
    for session in all_sessions:
        grouped.setdefault(session.guild_id, []).append(session)

    # Assert each guild only has its own session
    for guild_id in guilds:
        assert len(grouped[guild_id]) == 1
        assert grouped[guild_id][0].user_id == f"user_{guild_id[-1]}"