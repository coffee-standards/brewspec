"""
`brewlog stats` command.

Prints a summary of brew history: total brews, most common type,
average overall rating, and rating distribution.
"""

from __future__ import annotations

import click

from brewlog import db


@click.command("stats")
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Print a summary of brew history."""
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn = db.get_connection(db_path=db_path)
    try:
        stats_data = db.get_brew_stats(conn)
    finally:
        conn.close()

    if stats_data["total"] == 0:
        click.echo("No brews logged yet. Run 'brewlog add' to log your first brew.")
        return

    click.echo("Brew Summary")
    click.echo("============")
    click.echo(f"{'Total brews:':<20}{stats_data['total']}")
    most_common = stats_data["most_common_type"] if stats_data["most_common_type"] else "None"
    click.echo(f"{'Most common type:':<20}{most_common}")

    click.echo("")
    click.echo("Ratings")
    click.echo("-------")

    avg = stats_data["avg_overall_rating"]
    if avg is None:
        click.echo(f"{'Average overall:':<20}No ratings logged")
    else:
        click.echo(f"{'Average overall:':<20}{avg}")

    click.echo("Distribution:")
    dist = stats_data["rating_distribution"]
    for star in range(1, 6):
        label = f"{star} star:" if star == 1 else f"{star} stars:"
        click.echo(f"  {label:<8}{dist[star]}")
