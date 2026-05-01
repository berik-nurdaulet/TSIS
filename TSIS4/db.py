# db.py — PostgreSQL integration via psycopg2

import psycopg2
from config import DB_DSN


def get_connection():
    return psycopg2.connect(DB_DSN)


def init_db():
    """Create tables if they don't exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS players (
        id       SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS game_sessions (
        id            SERIAL PRIMARY KEY,
        player_id     INTEGER REFERENCES players(id),
        score         INTEGER   NOT NULL,
        level_reached INTEGER   NOT NULL,
        played_at     TIMESTAMP DEFAULT NOW()
    );
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] init_db error: {e}")
        return False


def get_or_create_player(username: str) -> int | None:
    """Return player id, creating the row if necessary."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (username) VALUES (%s) "
                    "ON CONFLICT (username) DO NOTHING",
                    (username,)
                )
                cur.execute("SELECT id FROM players WHERE username = %s", (username,))
                row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        return None


def save_session(player_id: int, score: int, level_reached: int) -> bool:
    """Insert a game session row."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO game_sessions (player_id, score, level_reached) "
                    "VALUES (%s, %s, %s)",
                    (player_id, score, level_reached)
                )
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] save_session error: {e}")
        return False


def get_personal_best(player_id: int) -> int:
    """Return the highest score for a player, or 0 if none."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) FROM game_sessions WHERE player_id = %s",
                (player_id,)
            )
            row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0


def get_leaderboard(limit: int = 10) -> list[dict]:
    """
    Return top <limit> scores across all players.
    Each entry: {rank, username, score, level_reached, played_at}
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.username,
                       gs.score,
                       gs.level_reached,
                       gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
        conn.close()
        results = []
        for rank, (username, score, level, played_at) in enumerate(rows, start=1):
            results.append({
                "rank":          rank,
                "username":      username,
                "score":         score,
                "level_reached": level,
                "played_at":     played_at.strftime("%Y-%m-%d") if played_at else "-",
            })
        return results
    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []