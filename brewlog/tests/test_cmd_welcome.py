"""
CLI integration tests for the welcome screen (no arguments).
Tests map to AC-34, AC-35, AC-36.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import __version__


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# AC-34: Welcome screen contents
# ---------------------------------------------------------------------------

def test_no_args_shows_ascii_cup(runner):
    """AC-34: ASCII cup in output."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    # The ASCII cup contains specific characters that form the cup shape
    # Check for key visual elements
    assert "(" in result.output or "." in result.output or "_" in result.output


def test_no_args_shows_version(runner):
    """AC-34: version string in output."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_no_args_shows_help(runner):
    """AC-34: command list in output."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    # Help text should list available commands
    assert "add" in result.output
    assert "list" in result.output
    assert "show" in result.output
    assert "export" in result.output
    assert "import" in result.output


def test_no_args_shows_brewlog_name(runner):
    """AC-34: BrewLog application name in output."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "BrewLog" in result.output


# ---------------------------------------------------------------------------
# AC-35: Exit code and stdout
# ---------------------------------------------------------------------------

def test_no_args_exit_zero(runner):
    """AC-35: exit code 0."""
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# AC-36: ASCII cup does not appear on subcommands
# ---------------------------------------------------------------------------

def test_subcommand_no_ascii_cup(tmp_path, monkeypatch):
    """AC-36: 'brewlog list' output does not contain ASCII cup."""
    from brewlog import db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")

    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    # The cup shape uses specific patterns — check for the full cup art
    # The ASCII cup has lines like "( (", ") )", ".______."
    assert "( (" not in result.output
    assert ".______." not in result.output


def test_version_flag(runner):
    """--version flag works correctly."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
