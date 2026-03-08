"""
BrewLog CLI — root Click group.

Entry point: brewlog.cli:cli (registered in pyproject.toml).
"""

from __future__ import annotations

import click

from brewlog import __version__
from brewlog.commands.add import add
from brewlog.commands.list_ import list_cmd
from brewlog.commands.show import show
from brewlog.commands.export import export
from brewlog.commands.import_ import import_cmd
from brewlog.commands.update import update
from brewlog.commands.delete import delete
from brewlog.commands.stats import stats
from brewlog.commands.search import search


ASCII_CUP = """\
    ( (
     ) )
  .______.
  |      |]
  \\      /
   `----'
"""


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="BrewLog")
@click.option(
    "--db", "db_path",
    type=str,
    default=None,
    help="Path to the SQLite database file. Defaults to ~/.brewlog/brews.db.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: str | None) -> None:
    """BrewLog - a local brew tracker using the BrewSpec format."""
    ctx.ensure_object(dict)
    if db_path is not None:
        from brewlog.serialise import validate_db_path
        resolved = validate_db_path(db_path)
        ctx.obj["db_path"] = resolved
    else:
        ctx.obj["db_path"] = None
    if ctx.invoked_subcommand is None:
        click.echo(ASCII_CUP)
        click.echo(f"BrewLog v{__version__}\n")
        click.echo(ctx.get_help())


cli.add_command(add)
cli.add_command(list_cmd, name="list")
cli.add_command(show)
cli.add_command(export)
cli.add_command(import_cmd, name="import")
cli.add_command(update)
cli.add_command(delete)
cli.add_command(stats)
cli.add_command(search)
