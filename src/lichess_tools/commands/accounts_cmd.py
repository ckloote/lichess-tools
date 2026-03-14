from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from lichess_tools.api.accounts import AccountsAPI
from lichess_tools.api.client import LichessClient
from lichess_tools.commands._utils import _bulk_action
from lichess_tools.config import Config
from lichess_tools.console import console
from lichess_tools.filters import FilterSpec, apply_filters, parse_filter

app = typer.Typer(help="Manage Lichess account relationships.")

FilterOption = Annotated[
    list[str],
    typer.Option("--filter", "-f", help="Filter: key:value"),
]


def _get_client(cfg: Config) -> LichessClient:
    token = cfg.require_token()
    return LichessClient(token, rate_limit_delay=cfg.rate_limit_delay)


@app.command("list-blocked")
def list_blocked(
    filters: FilterOption = [],
):
    """List all blocked users."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        api = AccountsAPI(client)
        specs: list[FilterSpec] = [parse_filter(f) for f in filters]
        users = [u for u in api.list_blocked() if apply_filters(u, specs)]

    if not users:
        console.print("[yellow]No blocked users found.[/yellow]")
        return

    table = Table(title=f"Blocked users ({len(users)})")
    table.add_column("Username")
    table.add_column("Title", style="dim")
    table.add_column("Rating", justify="right")

    for u in users:
        perfs = u.get("perfs", {})
        best_rating = ""
        if perfs:
            ratings = [v.get("rating", 0) for v in perfs.values() if isinstance(v, dict)]
            if ratings:
                best_rating = str(max(ratings))
        table.add_row(
            u.get("username", ""),
            u.get("title", ""),
            best_rating,
        )
    console.print(table)


@app.command("unblock")
def unblock(
    filters: FilterOption = [],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without unblocking")] = False,
):
    """Unblock users matching the given filters."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        api = AccountsAPI(client)
        specs: list[FilterSpec] = [parse_filter(f) for f in filters]
        users = [u for u in api.list_blocked() if apply_filters(u, specs)]

        _bulk_action(
            users,
            preview_columns=[("Username", "username"), ("Title", "title")],
            action_label="Unblock users",
            dry_run=dry_run,
            action_fn=lambda u: api.unblock(u["username"]),
            item_label=lambda u: u.get("username", ""),
        )
