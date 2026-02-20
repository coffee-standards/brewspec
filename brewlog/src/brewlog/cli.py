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
@click.pass_context
def cli(ctx: click.Context) -> None:
    """BrewLog - a local brew tracker using the BrewSpec format."""
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
