from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import tomli_w


def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "lichess-tools"


def _data_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "lichess-tools"


CONFIG_PATH = _config_dir() / "config.toml"
DB_PATH = _data_dir() / "lichess.db"


@dataclass
class Config:
    token: str = ""
    rate_limit_delay: float = 0.5
    blunder_threshold: int = 100

    @classmethod
    def load(cls) -> Config:
        # Env var takes precedence
        token_from_env = os.environ.get("LICHESS_TOKEN", "")

        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "rb") as f:
                data = tomllib.load(f)
        else:
            data = {}

        cfg = cls(
            token=token_from_env or data.get("token", ""),
            rate_limit_delay=float(data.get("rate_limit_delay", 0.5)),
            blunder_threshold=int(data.get("blunder_threshold", 100)),
        )
        return cfg

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data: dict = {}
        if self.token:
            data["token"] = self.token
        data["rate_limit_delay"] = self.rate_limit_delay
        data["blunder_threshold"] = self.blunder_threshold
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(data, f)

    def require_token(self) -> str:
        if not self.token:
            from lichess_tools.exceptions import AuthError

            raise AuthError(
                "No Lichess API token configured.\n"
                "Run: lichess config set-token YOUR_TOKEN\n"
                "Or set the LICHESS_TOKEN environment variable."
            )
        return self.token
