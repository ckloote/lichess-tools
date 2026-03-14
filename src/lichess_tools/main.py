from __future__ import annotations

import typer

from lichess_tools.commands import accounts_cmd, config_cmd, games_cmd, studies_cmd
from lichess_tools.console import err_console
from lichess_tools.exceptions import AuthError, LichessAPIError

app = typer.Typer(
    name="lichess",
    help="CLI tools for the Lichess chess platform.",
    no_args_is_help=True,
)

app.add_typer(config_cmd.app, name="config")
app.add_typer(studies_cmd.app, name="studies")
app.add_typer(accounts_cmd.app, name="accounts")
app.add_typer(games_cmd.app, name="games")


def main() -> None:
    try:
        app()
    except AuthError as exc:
        err_console.print(f"[bold red]Auth error:[/bold red] {exc}")
        raise typer.Exit(1)
    except LichessAPIError as exc:
        err_console.print(f"[bold red]API error:[/bold red] {exc}")
        raise typer.Exit(1)
