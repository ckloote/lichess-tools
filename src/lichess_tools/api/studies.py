from __future__ import annotations

from collections.abc import Generator

from lichess_tools.api.client import LichessClient


class StudiesAPI:
    def __init__(self, client: LichessClient):
        self._client = client

    def list_by_user(self, username: str) -> Generator[dict, None, None]:
        """Yield all studies for a given username."""
        yield from self._client.stream_ndjson(f"/api/study/by/{username}")

    def delete(self, study_id: str) -> None:
        """Delete a study by ID."""
        self._client.delete(f"/api/study/{study_id}")

    def export_pgn(self, study_id: str) -> Generator[str, None, None]:
        """Stream PGN lines for all chapters in a study."""
        yield from self._client.stream_text(f"/api/study/{study_id}.pgn")
