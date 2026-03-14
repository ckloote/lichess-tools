class LichessAPIError(Exception):
    """Base exception for Lichess API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthError(LichessAPIError):
    """Raised when authentication fails (401/403)."""


class RateLimitError(LichessAPIError):
    """Raised when the API rate limit is hit (429)."""
