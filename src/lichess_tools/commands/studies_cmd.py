from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from lichess_tools.api.client import LichessClient
from lichess_tools.api.studies import StudiesAPI
from lichess_tools.commands._utils import _bulk_action
from lichess_tools.config import Config
from lichess_tools.console import console
from lichess_tools.filters import FilterSpec, apply_filters, parse_filter
from rich.table import Table

app = typer.Typer(help="Manage Lichess studies.")

FilterOption = Annotated[
    list[str],
    typer.Option("--filter", "-f", help="Filter: key:value (e.g. name:~openings)"),
]


def _get_client(cfg: Config) -> LichessClient:
    token = cfg.require_token()
    return LichessClient(token, rate_limit_delay=cfg.rate_limit_delay)


@app.command("list")
def list_studies(
    username: Annotated[str, typer.Option("--username", "-u", help="Lichess username")] = "",
    filters: FilterOption = [],
):
    """List studies for a user (defaults to authenticated user)."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        if not username:
            profile = client.get_json("/api/account")
            username = profile["username"]

        api = StudiesAPI(client)
        specs: list[FilterSpec] = [parse_filter(f) for f in filters]

        studies = [s for s in api.list_by_user(username) if apply_filters(s, specs)]

    if not studies:
        console.print("[yellow]No studies found.[/yellow]")
        return

    table = Table(title=f"Studies for {username} ({len(studies)})")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Chapters", justify="right")
    table.add_column("Likes", justify="right")

    for s in studies:
        table.add_row(
            s.get("id", ""),
            s.get("name", ""),
            str(s.get("chapters", "")),
            str(s.get("likes", "")),
        )
    console.print(table)


@app.command("delete")
def delete_studies(
    username: Annotated[str, typer.Option("--username", "-u", help="Lichess username")] = "",
    filters: FilterOption = [],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without deleting")] = False,
):
    """Delete studies matching the given filters."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        if not username:
            profile = client.get_json("/api/account")
            username = profile["username"]

        api = StudiesAPI(client)
        specs: list[FilterSpec] = [parse_filter(f) for f in filters]
        studies = [s for s in api.list_by_user(username) if apply_filters(s, specs)]

        _bulk_action(
            studies,
            preview_columns=[("ID", "id"), ("Name", "name"), ("Chapters", "chapters")],
            action_label="Delete studies",
            dry_run=dry_run,
            action_fn=lambda s: api.delete(s["id"]),
            item_label=lambda s: s.get("name", s.get("id", "")),
        )


@app.command("export")
def export_studies(
    username: Annotated[str, typer.Option("--username", "-u", help="Lichess username")] = "",
    filters: FilterOption = [],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file (stdout if omitted)")] = None,
):
    """Export studies as PGN."""
    cfg = Config.load()
    with _get_client(cfg) as client:
        if not username:
            profile = client.get_json("/api/account")
            username = profile["username"]

        api = StudiesAPI(client)
        specs: list[FilterSpec] = [parse_filter(f) for f in filters]
        studies = [s for s in api.list_by_user(username) if apply_filters(s, specs)]

        if not studies:
            console.print("[yellow]No studies matched.[/yellow]")
            return

        lines: list[str] = []
        for study in studies:
            console.print(f"Exporting [cyan]{study.get('name', study['id'])}[/cyan]...")
            for line in api.export_pgn(study["id"]):
                lines.append(line)

        pgn_text = "\n".join(lines)
        if output:
            output.write_text(pgn_text)
            console.print(f"[green]Written to[/green] {output}")
        else:
            console.print(pgn_text)
