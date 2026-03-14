from __future__ import annotations

import json
import time
from collections.abc import Generator
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from lichess_tools.exceptions import AuthError, LichessAPIError, RateLimitError

BASE_URL = "https://lichess.org"


class LichessClient:
    def __init__(self, token: str, rate_limit_delay: float = 0.5):
        self._token = token
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LichessClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    def _raise_for_status(self, response: httpx.Response, *, streaming: bool = False) -> None:
        if response.status_code == 401:
            raise AuthError("Invalid or missing API token.", status_code=401)
        if response.status_code == 403:
            raise AuthError("Forbidden — check token scopes.", status_code=403)
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded.", status_code=429)
        if response.status_code >= 400:
            if streaming:
                response.read()
            raise LichessAPIError(
                f"API error {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get_json(self, path: str, params: dict | None = None) -> Any:
        self._throttle()
        response = self._client.get(path, params=params)
        self._raise_for_status(response)
        return response.json()

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def delete(self, path: str) -> None:
        self._throttle()
        response = self._client.delete(path)
        self._raise_for_status(response)

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def post_json(self, path: str, data: dict | None = None) -> Any:
        self._throttle()
        response = self._client.post(path, json=data)
        self._raise_for_status(response)
        if response.content:
            return response.json()
        return None

    def stream_ndjson(self, path: str, params: dict | None = None) -> Generator[dict, None, None]:
        """Stream NDJSON lines from a Lichess endpoint."""
        self._throttle()
        with self._client.stream(
            "GET",
            path,
            params=params,
            headers={"Accept": "application/x-ndjson"},
        ) as response:
            self._raise_for_status(response, streaming=True)
            for line in response.iter_lines():
                line = line.strip()
                if line:
                    yield json.loads(line)

    def stream_text(self, path: str, params: dict | None = None) -> Generator[str, None, None]:
        """Stream raw text lines (e.g. PGN) from a Lichess endpoint."""
        self._throttle()
        with self._client.stream(
            "GET",
            path,
            params=params,
            headers={"Accept": "application/x-chess-pgn"},
        ) as response:
            self._raise_for_status(response, streaming=True)
            for line in response.iter_lines():
                yield line
