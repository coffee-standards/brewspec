"""
Shared interactive prompt helpers for BrewLog CLI commands.

Extracted from add.py so update.py can use the same brew type menu
without circular imports.
"""

from __future__ import annotations

import click

from brewlog.models import BREW_TYPE_ENUM


def prompt_brew_type() -> str:
    """Prompt for brew type using a numbered menu. Re-prompts on invalid selection."""
    options = sorted(BREW_TYPE_ENUM)
    n = len(options)
    while True:
        click.echo("Select brew type:")
        for i, opt in enumerate(options, start=1):
            click.echo(f"  {i}. {opt}")
        raw = click.prompt(f"Choice [1-{n}]")
        try:
            choice = int(raw)
        except ValueError:
            click.echo(f"  Invalid choice. Please enter a number between 1 and {n}.")
            continue
        if 1 <= choice <= n:
            return options[choice - 1]
        click.echo(f"  Invalid choice. Please enter a number between 1 and {n}.")
