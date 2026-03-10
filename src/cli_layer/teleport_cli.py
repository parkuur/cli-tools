"""Teleport CLI adapter layer.

This module keeps CLI parsing and output concerns in the adapter layer and
delegates domain behavior to ``core_lib.teleport.service.TeleportService``.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from core_lib.common import exceptions
from core_lib.common.platform import get_db_path
from core_lib.common.utils import sanitize_alias
from core_lib.logging import configure_logging
from core_lib.teleport.models import Alias
from core_lib.teleport.service import TeleportService

app = typer.Typer(add_completion=False)


def _sanitize_or_invalid(alias: str) -> str:
    try:
        return sanitize_alias(alias)
    except ValueError as exc:
        raise exceptions.InvalidPathError(str(exc)) from exc


def _render_alias_table(aliases: list[Alias]) -> None:
    console = Console(stderr=True)
    if not aliases:
        console.print("No aliases pinned.")
        return

    table = Table(title="Teleport Aliases")
    table.add_column("Alias")
    table.add_column("Path")
    table.add_column("Visits", justify="right")
    for alias in aliases:
        table.add_row(alias.alias, alias.path, str(alias.visit_count))
    console.print(table)


@app.callback(invoke_without_command=True)
def cli(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    _ctx: typer.Context,
    pin: bool = typer.Option(False, "-p", "--pin", help="Pin an alias"),
    unpin: bool = typer.Option(False, "-u", "--unpin", help="Unpin an alias"),
    show: bool = typer.Option(False, "-s", "--show", help="Show alias path(s)"),
    previous: bool = typer.Option(False, "--previous", help="Show previous path"),
    force: bool = typer.Option(False, "--force", help="Force overwrite when pinning"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging"),
    alias_arg: str | None = typer.Argument(None),
    path_arg: str | None = typer.Argument(None),
) -> None:
    """Handle all teleport CLI invocations."""
    _ = verbose
    service = TeleportService(get_db_path())
    active_modes = [pin, unpin, show, previous]
    if sum(1 for mode in active_modes if mode) > 1:
        raise typer.Exit(code=1)

    if pin:
        if alias_arg is None:
            raise typer.Exit(code=1)
        alias = _sanitize_or_invalid(alias_arg)
        path_to_pin = Path.cwd() if path_arg is None else Path(path_arg)
        service.pin(alias, path_to_pin, overwrite=force)
        typer.echo(f"Pinned {alias} -> {path_to_pin.resolve()}", err=True)
        return

    if unpin:
        if alias_arg is None:
            raise typer.Exit(code=1)
        alias = _sanitize_or_invalid(alias_arg)
        service.unpin(alias)
        typer.echo(f"Unpinned {alias}", err=True)
        return

    if show:
        if path_arg is not None:
            raise typer.Exit(code=1)
        if alias_arg is None:
            _render_alias_table(service.show())
            return
        alias = _sanitize_or_invalid(alias_arg)
        try:
            result = service.show(alias)
        except exceptions.AliasNotFoundError as exc:
            raise exceptions.AliasNotFoundError(f"Alias not found: {alias}") from exc
        typer.echo(result[0].path, err=True)
        return

    if previous:
        if alias_arg is not None or path_arg is not None:
            raise typer.Exit(code=1)
        previous_path = service.previous()
        if previous_path is None:
            raise exceptions.AliasNotFoundError("No previous path")
        typer.echo(str(previous_path))
        return

    if alias_arg is None:
        typer.echo(str(Path.home()))
        return

    if path_arg is not None:
        raise typer.Exit(code=1)

    alias = _sanitize_or_invalid(alias_arg)
    resolved = service.resolve(alias, Path.cwd())
    if resolved is None:
        raise exceptions.AliasNotFoundError(f"Alias not found: {alias}")
    typer.echo(str(resolved))


def main() -> int:
    """Run the CLI and return an integer process exit code."""
    if len(sys.argv) == 2 and sys.argv[1] == "-":
        sys.argv[1] = "--previous"

    configure_logging("DEBUG" if "--verbose" in sys.argv else "WARNING")

    try:  # pylint: disable=broad-exception-caught
        app(standalone_mode=False)
        return 0
    except typer.Exit as exc:
        return int(exc.exit_code)
    except exceptions.AliasNotFoundError as exc:
        typer.echo(str(exc), err=True)
        return 2
    except exceptions.AliasConflictError as exc:
        typer.echo(str(exc), err=True)
        return 3
    except exceptions.StorageError as exc:
        typer.echo(str(exc), err=True)
        return 4
    except OSError as exc:
        typer.echo(str(exc), err=True)
        return 4
    except exceptions.InvalidPathError as exc:
        typer.echo(str(exc), err=True)
        return 5
    except Exception as exc:  # pylint: disable=broad-exception-caught  # pragma: no cover
        typer.echo(str(exc), err=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
