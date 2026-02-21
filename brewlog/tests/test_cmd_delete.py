"""
CLI integration tests for `brewlog delete`.
Tests map to BrewLog CLI v0.2 AC-4 through AC-9.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


@pytest.fixture
def runner_no_mix(db_path, monkeypatch):
    # Default CliRunner merges stderr into output; use result.output for all checks
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(runner, date="2026-02-19T08:30:00Z", brew_type="pour_over"):
    return runner.invoke(cli, [
        "add", "--date", date, "--type", brew_type,
        "--dose", "18.0", "--water", "280.0",
    ])


# ---------------------------------------------------------------------------
# AC-4: Confirmation prompt — cancel behaviour
# ---------------------------------------------------------------------------

def test_delete_cancels_on_n(runner):
    """AC-4: responds 'n' -> 'Cancelled.' printed, exit 0."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="n\n")
    assert result.exit_code == 0
    assert "Cancelled." in result.output


def test_delete_cancels_on_empty_enter(runner):
    """AC-4: presses Enter (empty) -> cancel, exit 0."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="\n")
    assert result.exit_code == 0
    assert "Cancelled." in result.output


def test_delete_cancels_on_arbitrary_input(runner):
    """AC-4: arbitrary non-y input -> cancel, exit 0."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="no\n")
    assert result.exit_code == 0
    assert "Cancelled." in result.output


def test_delete_cancels_no_db_change(runner, db_path):
    """AC-4: cancelling does not remove the brew from DB."""
    _add_brew(runner)
    runner.invoke(cli, ["delete", "1"], input="n\n")
    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn) is not None
    finally:
        conn.close()


def test_delete_prompt_format(runner):
    """AC-4: confirmation prompt contains brew ID."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="n\n")
    assert "Delete brew #1?" in result.output


# ---------------------------------------------------------------------------
# AC-5: Confirmation prompt — confirm behaviour
# ---------------------------------------------------------------------------

def test_delete_confirms_on_y(runner):
    """AC-5: 'y' confirms -> 'Brew #1 deleted.' printed, exit 0."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="y\n")
    assert result.exit_code == 0
    assert "Brew #1 deleted." in result.output


def test_delete_confirms_on_capital_Y(runner):
    """AC-5: 'Y' also confirms."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1"], input="Y\n")
    assert result.exit_code == 0
    assert "Brew #1 deleted." in result.output


def test_delete_removes_from_db(runner, db_path):
    """AC-5: confirmed delete removes the row from DB."""
    _add_brew(runner)
    runner.invoke(cli, ["delete", "1"], input="y\n")
    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn) is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-6: --force flag
# ---------------------------------------------------------------------------

def test_delete_force_skips_prompt(runner):
    """AC-6: --force skips confirmation prompt, deletes immediately."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "1", "--force"])
    assert result.exit_code == 0
    assert "Brew #1 deleted." in result.output
    assert "Delete brew" not in result.output


def test_delete_force_removes_from_db(runner, db_path):
    """AC-6: --force removes row from DB."""
    _add_brew(runner)
    runner.invoke(cli, ["delete", "1", "--force"])
    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn) is None
    finally:
        conn.close()


def test_delete_force_nonexistent_id(runner_no_mix):
    """AC-6 + AC-7: --force on nonexistent ID -> exit 1, error message shown."""
    result = runner_no_mix.invoke(cli, ["delete", "999", "--force"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "999" in result.output


# ---------------------------------------------------------------------------
# AC-7: ID not found
# ---------------------------------------------------------------------------

def test_delete_nonexistent_id_exit_1(runner):
    """AC-7: bogus ID -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "999"])
    assert result.exit_code == 1


def test_delete_nonexistent_id_no_prompt(runner):
    """AC-7: nonexistent ID shows error without showing the confirmation prompt."""
    _add_brew(runner)
    result = runner.invoke(cli, ["delete", "999"])
    assert result.exit_code == 1
    assert "Delete brew" not in result.output


# ---------------------------------------------------------------------------
# AC-8: Non-positive ID
# ---------------------------------------------------------------------------

def test_delete_zero_id(runner):
    """AC-8: ID=0 is rejected."""
    result = runner.invoke(cli, ["delete", "0"])
    assert result.exit_code != 0


def test_delete_negative_id(runner):
    """AC-8: negative ID is rejected."""
    result = runner.invoke(cli, ["delete", "-1"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# AC-9: delete listed in welcome screen
# ---------------------------------------------------------------------------

def test_delete_shown_in_welcome_screen(tmp_path, monkeypatch):
    """AC-9: 'delete' appears in the help listing on bare 'brewlog'."""
    import brewlog.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "delete" in result.output
