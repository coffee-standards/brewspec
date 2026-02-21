"""
`brewlog delete` command.

Deletes a brew by integer ID after a confirmation prompt.
--force skips the prompt.
"""

from __future__ import annotations

import sys

import click

from brewlog import db


@click.command("delete")
@click.argument("brew_id", type=int)
@click.option("--force", is_flag=True, default=False,
              help="Skip confirmation prompt and delete immediately.")
def delete(brew_id: int, force: bool) -> None:
    """Delete a brew by ID."""

    if brew_id <= 0:
        click.echo("Error: brew ID must be a positive integer.", err=True)
        sys.exit(1)

    conn = db.get_connection()
    try:
        row = db.get_brew(brew_id, conn)
        if row is None:
            click.echo(f"Error: brew #{brew_id} not found.", err=True)
            sys.exit(1)

        if not force:
            confirmed = click.confirm(f"Delete brew #{brew_id}?", default=False)
            if not confirmed:
                click.echo("Cancelled.")
                return

        db.delete_brew(brew_id, conn)
    finally:
        conn.close()

    click.echo(f"Brew #{brew_id} deleted.")
