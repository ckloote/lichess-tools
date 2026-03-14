from __future__ import annotations

from collections.abc import Generator

from lichess_tools.api.client import LichessClient


class AccountsAPI:
    def __init__(self, client: LichessClient):
        self._client = client

    def list_blocked(self) -> Generator[dict, None, None]:
        """Yield all blocked users for the authenticated account."""
        yield from self._client.stream_ndjson("/api/rel/blocked")

    def unblock(self, username: str) -> None:
        """Unblock a user by username."""
        self._client.post_json(f"/api/rel/unblock/{username}")

    def get_profile(self) -> dict:
        """Get the authenticated user's profile."""
        return self._client.get_json("/api/account")
