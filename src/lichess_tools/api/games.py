from __future__ import annotations

from collections.abc import Generator

from lichess_tools.api.client import LichessClient


class GamesAPI:
    def __init__(self, client: LichessClient):
        self._client = client

    def export_by_username(
        self,
        username: str,
        *,
        evals: bool = False,
        since: int | None = None,
        until: int | None = None,
        max_games: int | None = None,
        perf_type: str | None = None,
    ) -> Generator[str, None, None]:
        """Stream PGN text for games played by username."""
        params: dict = {
            "evals": "true" if evals else "false",
            "clocks": "false",
            "opening": "true",
            "literate": "false",
        }
        if since is not None:
            params["since"] = since
        if until is not None:
            params["until"] = until
        if max_games is not None:
            params["max"] = max_games
        if perf_type is not None:
            params["perfType"] = perf_type

        yield from self._client.stream_text(f"/api/games/user/{username}", params=params)

    def export_one(self, game_id: str, *, evals: bool = True) -> Generator[str, None, None]:
        """Stream PGN text for a single game."""
        params = {"evals": "true" if evals else "false", "opening": "true"}
        yield from self._client.stream_text(f"/game/export/{game_id}", params=params)
