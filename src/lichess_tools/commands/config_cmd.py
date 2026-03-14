from __future__ import annotations

import typer

from lichess_tools.config import CONFIG_PATH, Config
from lichess_tools.console import console

app = typer.Typer(help="Manage lichess-tools configuration.")


@app.command("set-token")
def set_token(token: str = typer.Argument(..., help="Your Lichess personal API token")):
    """Save a Lichess API token to the config file."""
    cfg = Config.load()
    cfg.token = token
    cfg.save()
    console.print(f"[green]Token saved to[/green] {CONFIG_PATH}")


@app.command("show")
def show():
    """Display the current configuration."""
    cfg = Config.load()
    token_display = f"{cfg.token[:8]}..." if len(cfg.token) > 8 else ("(not set)" if not cfg.token else cfg.token)
    console.print(f"Config file : [cyan]{CONFIG_PATH}[/cyan]")
    console.print(f"Token       : [yellow]{token_display}[/yellow]")
    console.print(f"Rate delay  : {cfg.rate_limit_delay}s")
    console.print(f"Blunder cp  : {cfg.blunder_threshold}")
