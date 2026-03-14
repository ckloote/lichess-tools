SCHEMA_VERSION = 1

CREATE_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
"""

CREATE_GAMES = """
CREATE TABLE IF NOT EXISTS games (
    id           TEXT PRIMARY KEY,
    username     TEXT NOT NULL,
    played_at    INTEGER,
    pgn          TEXT,
    white        TEXT,
    black        TEXT,
    result       TEXT,
    time_control TEXT,
    opening      TEXT,
    analyzed     INTEGER NOT NULL DEFAULT 0
);
"""

CREATE_GAMES_IDX = """
CREATE INDEX IF NOT EXISTS idx_games_username ON games (username);
"""

CREATE_CRITICAL_MOMENTS = """
CREATE TABLE IF NOT EXISTS critical_moments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id       TEXT NOT NULL,
    ply           INTEGER NOT NULL,
    move_san      TEXT,
    eval_before   INTEGER,
    eval_after    INTEGER,
    swing         INTEGER,
    color         TEXT,
    engine        TEXT,
    FOREIGN KEY (game_id) REFERENCES games (id)
);
"""

CREATE_CRITICAL_MOMENTS_IDX = """
CREATE INDEX IF NOT EXISTS idx_moments_game_id ON critical_moments (game_id);
"""

MIGRATIONS: dict[int, list[str]] = {
    1: [
        CREATE_SCHEMA_VERSION,
        CREATE_GAMES,
        CREATE_GAMES_IDX,
        CREATE_CRITICAL_MOMENTS,
        CREATE_CRITICAL_MOMENTS_IDX,
    ],
}
