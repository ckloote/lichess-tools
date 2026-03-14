from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer
from dateutil import parser as dateutil_parser
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from lichess_tools.analysis.cloud import CloudEngine
from lichess_tools.analysis.pgn import parse_game_headers
from lichess_tools.api.client import LichessClient
from lichess_tools.api.games import GamesAPI
from lichess_tools.config import DB_PATH, Config
from lichess_tools.console import console
from lichess_tools.db.repository import BlunderRepository, GameRepository, open_db

app = typer.Typer(help="Work with Lichess games.")

_GAME_ID_RE = re.compile(r'\[Site "https://lichess\.org/([A-Za-z0-9]+)"')


def _get_client(cfg: Config) -> LichessClient:
    token = cfg.require_token()
    return LichessClient(token, rate_limit_delay=cfg.rate_limit_delay)


def _parse_pgn_blocks(lines: list[str]) -> list[str]:
    """Split a stream of PGN lines into individual game PGN strings."""
    games: list[str] = []
    current: list[str] = []
    in_moves = False

    for line in lines:
        if line.startswith("[") and not in_moves:
            current.append(line)
        elif line.startswith("1.") or (current and not line.startswith("[")):
            in_moves = True
            current.append(line)
        elif line == "" and in_moves:
            if current:
                games.append("\n".join(current))
                current = []
                in_moves = False
        elif line.startswith("[") and in_moves:
            # New game starting
            if current:
                games.append("\n".join(current))
            current = [line]
            in_moves = False

    if current:
        games.append("\n".join(current))

    return [g for g in games if g.strip()]


def _extract_game_id(pgn_text: str) -> str | None:
    m = _GAME_ID_RE.search(pgn_text)
    return m.group(1) if m else None


def _date_to_ms(date_str: str) -> int:
    """Parse a date string to milliseconds since epoch."""
    dt = dateutil_parser.parse(date_str)
    return int(dt.timestamp() * 1000)


@app.command("export")
def export_games(
    username: Annotated[str, typer.Argument(help="Lichess username")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output PGN file")] = None,
    since: Annotated[str, typer.Option("--since", help="Start date (e.g. 2024-01-01)")] = None,
    until: Annotated[str, typer.Option("--until", help="End date")] = None,
    max_games: Annotated[int, typer.Option("--max", help="Maximum number of games")] = None,
    perf_type: Annotated[str, typer.Option("--perf", help="Game type (e.g. blitz, rapid)")] = None,
):
    """Export games for a user as PGN."""
    cfg = Config.load()

    since_ms = _date_to_ms(since) if since else None
    until_ms = _date_to_ms(until) if until else None

    with _get_client(cfg) as client:
        api = GamesAPI(client)
        lines = list(
            api.export_by_username(
                username,
                evals=False,
                since=since_ms,
                until=until_ms,
                max_games=max_games,
                perf_type=perf_type,
            )
        )

    pgn_text = "\n".join(lines)

    if output:
        output.write_text(pgn_text)
        console.print(f"[green]Written to[/green] {output}")
    else:
        console.print(pgn_text)


@app.command("analyze")
def analyze_games(
    username: Annotated[str, typer.Argument(help="Lichess username")],
    since: Annotated[str, typer.Option("--since", help="Start date (e.g. 2024-01-01)")] = None,
    until: Annotated[str, typer.Option("--until", help="End date")] = None,
    max_games: Annotated[int, typer.Option("--max", help="Maximum number of games")] = None,
    blunder_threshold: Annotated[int, typer.Option("--blunder-threshold", help="Centipawn swing to flag")] = None,
    perf_type: Annotated[str, typer.Option("--perf", help="Game type (e.g. blitz, rapid)")] = None,
    show_results: Annotated[bool, typer.Option("--show", help="Print critical moments table")] = True,
):
    """Analyze games for critical moments (large eval swings)."""
    cfg = Config.load()
    threshold = blunder_threshold if blunder_threshold is not None else cfg.blunder_threshold

    since_ms = _date_to_ms(since) if since else None
    until_ms = _date_to_ms(until) if until else None

    conn = open_db(DB_PATH)
    game_repo = GameRepository(conn)
    blunder_repo = BlunderRepository(conn)

    total_games = 0
    total_moments = 0

    with _get_client(cfg) as client:
        api = GamesAPI(client)
        engine = CloudEngine(client, fallback_to_api=True)

        console.print(f"Streaming games for [cyan]{username}[/cyan]...")

        raw_lines: list[str] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading games...", total=None)
            for line in api.export_by_username(
                username,
                evals=True,
                since=since_ms,
                until=until_ms,
                max_games=max_games,
                perf_type=perf_type,
            ):
                raw_lines.append(line)
            progress.update(task, completed=1, total=1)

        pgn_blocks = _parse_pgn_blocks(raw_lines)
        console.print(f"Processing [bold]{len(pgn_blocks)}[/bold] game(s)...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing...", total=len(pgn_blocks))

            for pgn_text in pgn_blocks:
                game_id = _extract_game_id(pgn_text)
                if not game_id:
                    progress.advance(task)
                    continue

                headers = parse_game_headers(pgn_text)
                game_repo.upsert_game(
                    game_id,
                    username,
                    {
                        "pgn": pgn_text,
                        "white": headers.get("White", ""),
                        "black": headers.get("Black", ""),
                        "result": headers.get("Result", ""),
                        "time_control": headers.get("TimeControl", ""),
                        "opening": headers.get("Opening", ""),
                        "analyzed": False,
                    },
                )

                evals = engine.analyze_game(pgn_text)
                if evals:
                    moments = engine.find_critical_moments(game_id, evals, threshold)
                    if moments:
                        blunder_repo.save_moments(moments)
                        total_moments += len(moments)
                    game_repo.mark_analyzed(game_id)

                total_games += 1
                progress.advance(task)

    conn.close()

    console.print(
        f"\n[green]Done.[/green] {total_games} games processed, "
        f"{total_moments} critical moment(s) found (threshold: {threshold}cp)."
    )

    if show_results and total_moments > 0:
        conn = open_db(DB_PATH)
        blunder_repo = BlunderRepository(conn)
        moments = blunder_repo.list_for_username(username, min_swing=threshold)
        conn.close()

        table = Table(title=f"Critical moments for {username} (top {min(20, len(moments))})")
        table.add_column("Game ID", style="dim")
        table.add_column("Ply", justify="right")
        table.add_column("Move")
        table.add_column("Before", justify="right")
        table.add_column("After", justify="right")
        table.add_column("Swing", justify="right", style="bold red")
        table.add_column("Color")

        for row in moments[:20]:
            table.add_row(
                row["game_id"],
                str(row["ply"]),
                row["move_san"] or "",
                str(row["eval_before"]),
                str(row["eval_after"]),
                str(row["swing"]),
                row["color"] or "",
            )
        console.print(table)
