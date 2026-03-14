from __future__ import annotations

import sqlite3
from pathlib import Path

from lichess_tools.analysis.base import CriticalMoment
from lichess_tools.db.migrations import ensure_schema


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


class GameRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def upsert_game(self, game_id: str, username: str, data: dict) -> None:
        self._conn.execute(
            """
            INSERT INTO games (id, username, played_at, pgn, white, black,
                               result, time_control, opening, analyzed)
            VALUES (:id, :username, :played_at, :pgn, :white, :black,
                    :result, :time_control, :opening, :analyzed)
            ON CONFLICT(id) DO UPDATE SET
                pgn          = excluded.pgn,
                analyzed     = excluded.analyzed
            """,
            {
                "id": game_id,
                "username": username,
                "played_at": data.get("played_at"),
                "pgn": data.get("pgn"),
                "white": data.get("white"),
                "black": data.get("black"),
                "result": data.get("result"),
                "time_control": data.get("time_control"),
                "opening": data.get("opening"),
                "analyzed": int(data.get("analyzed", False)),
            },
        )
        self._conn.commit()

    def mark_analyzed(self, game_id: str) -> None:
        self._conn.execute(
            "UPDATE games SET analyzed = 1 WHERE id = ?", (game_id,)
        )
        self._conn.commit()

    def get_game(self, game_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM games WHERE id = ?", (game_id,)
        ).fetchone()

    def list_games(self, username: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM games WHERE username = ? ORDER BY played_at DESC",
            (username,),
        ).fetchall()


class BlunderRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def save_moment(self, moment: CriticalMoment) -> None:
        self._conn.execute(
            """
            INSERT INTO critical_moments
                (game_id, ply, move_san, eval_before, eval_after, swing, color, engine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                moment.game_id,
                moment.ply,
                moment.move_san,
                moment.eval_before_cp,
                moment.eval_after_cp,
                moment.swing_cp,
                moment.color,
                moment.engine,
            ),
        )
        self._conn.commit()

    def save_moments(self, moments: list[CriticalMoment]) -> None:
        self._conn.executemany(
            """
            INSERT INTO critical_moments
                (game_id, ply, move_san, eval_before, eval_after, swing, color, engine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    m.game_id,
                    m.ply,
                    m.move_san,
                    m.eval_before_cp,
                    m.eval_after_cp,
                    m.swing_cp,
                    m.color,
                    m.engine,
                )
                for m in moments
            ],
        )
        self._conn.commit()

    def list_for_game(self, game_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM critical_moments WHERE game_id = ? ORDER BY ply",
            (game_id,),
        ).fetchall()

    def list_for_username(self, username: str, min_swing: int = 0) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT cm.* FROM critical_moments cm
            JOIN games g ON g.id = cm.game_id
            WHERE g.username = ? AND cm.swing >= ?
            ORDER BY cm.swing DESC
            """,
            (username, min_swing),
        ).fetchall()
