from __future__ import annotations

from typing import Annotated

import typer

from lichess_tools.api.accounts import AccountsAPI
from lichess_tools.api.client import LichessClient
from lichess_tools.config import Config
from lichess_tools.console import console

app = typer.Typer(help="Manage Lichess account relationships.")


def _get_client(cfg: Config) -> LichessClient:
    token = cfg.require_token()
    return LichessClient(token, rate_limit_delay=cfg.rate_limit_delay)


@app.command("unblock")
def unblock(
    username: Annotated[str, typer.Argument(help="Lichess username to unblock")],
):
    """Unblock a user."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        api = AccountsAPI(client)
        api.unblock(username)
    console.print(f"[green]Unblocked[/green] {username}")
