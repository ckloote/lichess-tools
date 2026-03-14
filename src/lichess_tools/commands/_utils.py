from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from lichess_tools.console import console


def _bulk_action(
    items: list[dict],
    *,
    preview_columns: list[tuple[str, str]],  # (header, item_key)
    action_label: str,
    dry_run: bool,
    action_fn: Callable[[dict], None],
    item_label: Callable[[dict], str] | None = None,
) -> None:
    """
    Standard bulk-action flow:
    1. Show preview table
    2. Bail out if dry_run
    3. Confirm
    4. Execute with progress bar
    5. Print summary
    """
    if not items:
        console.print("[yellow]No items matched.[/yellow]")
        return

    # Preview table
    table = Table(title=f"{action_label} — {len(items)} item(s)")
    for header, _ in preview_columns:
        table.add_column(header)
    for item in items:
        table.add_row(*[str(item.get(key, "")) for _, key in preview_columns])
    console.print(table)

    if dry_run:
        console.print(f"[dim]Dry run — no changes made.[/dim]")
        return

    typer.confirm(f"Proceed with {action_label.lower()} on {len(items)} item(s)?", abort=True)

    success = 0
    errors: list[tuple[str, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(action_label, total=len(items))
        for item in items:
            label = item_label(item) if item_label else str(item)
            try:
                action_fn(item)
                success += 1
            except Exception as exc:
                errors.append((label, str(exc)))
            finally:
                progress.advance(task)

    console.print(f"[green]Done:[/green] {success} succeeded, {len(errors)} failed.")
    if errors:
        for label, msg in errors:
            console.print(f"  [red]✗[/red] {label}: {msg}")
