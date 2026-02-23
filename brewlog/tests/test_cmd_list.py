"""
CLI integration tests for `brewlog list`.
Tests map to AC-12, AC-13, AC-14, AC-15, AC-16.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module
from brewlog.models import BrewInput


@pytest.fixture
def runner_with_db(tmp_path, monkeypatch):
    """CliRunner with a temporary DB path injected."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


def _populate_brews(db_path, n: int):
    """Insert n brews with distinct dates into the DB at db_path."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        for i in range(n):
            brew = BrewInput(
                date=f"2026-02-{i + 1:02d}T08:30:00Z",
                type="pour_over",
                dose_g=18.0,
                water_weight_g=280.0,
            )
            db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-16: Empty database
# ---------------------------------------------------------------------------

def test_list_empty_db_message(runner_with_db):
    """AC-16: friendly message when no brews."""
    result = runner_with_db.invoke(cli, ["list"])
    assert "No brews logged yet" in result.output


def test_list_empty_db_exit_zero(runner_with_db):
    """AC-16: exit code 0 when empty."""
    result = runner_with_db.invoke(cli, ["list"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# AC-13: Table headers
# ---------------------------------------------------------------------------

def test_list_shows_table_headers(runner_with_db, tmp_path):
    """AC-13: column headers in output."""
    _populate_brews(tmp_path / "test.db", 1)
    result = runner_with_db.invoke(cli, ["list"])
    assert "ID" in result.output
    assert "Date" in result.output
    assert "Type" in result.output
    assert "Method" in result.output
    assert "Dose" in result.output
    assert "Water" in result.output
    # v0.3: Rating column renamed to 'Overall Rating' (AC-38)
    assert "Overall Rating" in result.output


def test_list_header_does_not_show_tds(runner_with_db, tmp_path):
    """AC-38: TDS column removed from list view in v0.3."""
    _populate_brews(tmp_path / "test.db", 1)
    result = runner_with_db.invoke(cli, ["list"])
    # TDS column should not appear in header
    lines = result.output.split("\n")
    header_line = lines[0] if lines else ""
    assert "TDS" not in header_line


def test_list_optional_field_dash_when_absent(runner_with_db, tmp_path):
    """AC-13: missing optional field shows '-'."""
    _populate_brews(tmp_path / "test.db", 1)
    result = runner_with_db.invoke(cli, ["list"])
    # Method and rating are not set; should show '-'
    assert "-" in result.output


# ---------------------------------------------------------------------------
# AC-12: Default limit and ordering
# ---------------------------------------------------------------------------

def test_list_default_limit_20(runner_with_db, tmp_path):
    """AC-12: at most 20 rows with default call."""
    _populate_brews(tmp_path / "test.db", 25)
    result = runner_with_db.invoke(cli, ["list"])
    assert result.exit_code == 0
    # Count data rows (lines after the header separator that start with data)
    lines = result.output.strip().split("\n")
    # Count lines containing date patterns (data rows)
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 20


def test_list_order_most_recent_first(runner_with_db, tmp_path):
    """AC-12: row order matches date desc."""
    _populate_brews(tmp_path / "test.db", 3)
    result = runner_with_db.invoke(cli, ["list"])
    # The most recent date (day 03) should appear before day 01
    output = result.output
    pos_day3 = output.find("2026-02-03")
    pos_day1 = output.find("2026-02-01")
    assert pos_day3 < pos_day1, "Most recent date should appear first"


# ---------------------------------------------------------------------------
# AC-14: --limit flag
# ---------------------------------------------------------------------------

def test_list_custom_limit(runner_with_db, tmp_path):
    """AC-14: --limit 5 returns at most 5 rows."""
    _populate_brews(tmp_path / "test.db", 10)
    result = runner_with_db.invoke(cli, ["list", "--limit", "5"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 5


def test_list_limit_invalid_zero(runner_with_db):
    """AC-14: --limit 0 -> error, exit 1."""
    result = runner_with_db.invoke(cli, ["list", "--limit", "0"])
    assert result.exit_code == 1


def test_list_limit_invalid_negative(runner_with_db):
    """AC-14: --limit -1 -> error, exit 1."""
    result = runner_with_db.invoke(cli, ["list", "--limit", "-1"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-15: --all flag
# ---------------------------------------------------------------------------

def test_list_all(runner_with_db, tmp_path):
    """AC-15: --all returns all brews."""
    _populate_brews(tmp_path / "test.db", 25)
    result = runner_with_db.invoke(cli, ["list", "--all"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 25
