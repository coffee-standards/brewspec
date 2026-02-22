"""
CLI integration tests for `brewlog update`.
Tests map to BrewLog v0.2 update command acceptance criteria.

Note: v0.4 changes — rating moved to result.ratings.overall, grind is now enum.
"""

import json

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
    """CliRunner with an isolated temp DB."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(runner, date="2026-02-19T08:30:00Z", brew_type="pour_over",
              dose="18.0", water="280.0"):
    """Helper: add a brew via CLI and return the result."""
    return runner.invoke(cli, [
        "add",
        "--date", date,
        "--type", brew_type,
        "--dose", dose,
        "--water", water,
    ])


# ---------------------------------------------------------------------------
# Happy path tests
# ---------------------------------------------------------------------------

def test_update_overall_on_latest(runner, db_path, monkeypatch):
    """No ID arg — updates the latest brew's overall rating."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--overall", "4"])
    assert result.exit_code == 0
    assert "Brew #1 updated." in result.output

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        ratings = json.loads(row["result_ratings"])
        assert ratings["overall"] == 4
    finally:
        conn.close()


def test_update_by_id(runner, db_path, monkeypatch):
    """Explicit ID — updates method and notes for that brew."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "1", "--method", "V60", "--notes", "Clean finish"])
    assert result.exit_code == 0
    assert "Brew #1 updated." in result.output

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["method"] == "V60"
        assert row["notes"] == "Clean finish"
    finally:
        conn.close()


def test_update_multiple_fields(runner, db_path, monkeypatch):
    """Sets overall, method, and grind in one call."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, [
        "update", "--overall", "5", "--method", "Chemex", "--grind", "medium_coarse",
    ])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        ratings = json.loads(row["result_ratings"])
        assert ratings["overall"] == 5
        assert row["method"] == "Chemex"
        assert row["grind"] == "medium_coarse"
    finally:
        conn.close()


def test_update_defaults_to_latest_not_oldest(runner, db_path, monkeypatch):
    """With two brews logged, no-ID update targets the latest one."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner, date="2026-02-18T08:00:00Z")   # brew #1 — older
    _add_brew(runner, date="2026-02-20T08:00:00Z")   # brew #2 — newer

    result = runner.invoke(cli, ["update", "--overall", "3"])
    assert result.exit_code == 0
    assert "Brew #2 updated." in result.output

    conn = db_module.get_connection(db_path=db_path)
    try:
        row1 = db_module.get_brew(1, conn)
        row2 = db_module.get_brew(2, conn)
        assert row1["result_ratings"] is None    # oldest untouched
        ratings2 = json.loads(row2["result_ratings"])
        assert ratings2["overall"] == 3           # latest updated
    finally:
        conn.close()


def test_update_coffee_fields(runner, db_path, monkeypatch):
    """roast-date and varietal are stored correctly."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, [
        "update", "--roast-date", "2026-01-15", "--varietal", "Gesha",
    ])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["coffee_roast_date"] == "2026-01-15"
        assert row["coffee_varietal"] == "Gesha"
    finally:
        conn.close()


def test_update_water_ppm(runner, db_path, monkeypatch):
    """--water-ppm flag stores correctly."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--water-ppm", "75.5"])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["water_ppm"] == 75.5
    finally:
        conn.close()


def test_update_equipment_fields(runner, db_path, monkeypatch):
    """--grinder and --brewer flags store correctly."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, [
        "update", "--grinder", "Niche Zero", "--brewer", "Hario V60",
    ])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["equipment_grinder"] == "Niche Zero"
        assert row["equipment_brewer"] == "Hario V60"
    finally:
        conn.close()


def test_update_result_tds(runner, db_path, monkeypatch):
    """--tds flag updates result_tds column."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--tds", "1.42"])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["result_tds"] == 1.42
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_update_no_flags_errors(runner):
    """No flags provided -> exit 1 with helpful message."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update"])
    assert result.exit_code == 1
    assert "at least one" in result.output.lower() or "no fields" in result.output.lower()


def test_update_id_not_found(runner):
    """Explicit ID that doesn't exist -> exit 1."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "999", "--overall", "3"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "999" in result.output


def test_update_no_brews(runner):
    """Empty DB, no ID supplied -> exit 1."""
    result = runner.invoke(cli, ["update", "--overall", "4"])
    assert result.exit_code == 1
    assert "no brews" in result.output.lower() or "empty" in result.output.lower()


def test_update_invalid_overall(runner):
    """overall=6 -> exit 1."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--overall", "6"])
    assert result.exit_code == 1
    assert "overall" in result.output.lower() or "rating" in result.output.lower()


def test_update_invalid_temp(runner):
    """temp=101 -> exit 1."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--temp", "101"])
    assert result.exit_code == 1
    assert "temp" in result.output.lower() or "100" in result.output


def test_update_invalid_duration(runner):
    """duration=0 -> exit 1."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--duration", "0"])
    assert result.exit_code == 1
    assert "duration" in result.output.lower() or "0" in result.output


def test_update_invalid_tds(runner):
    """tds=-1 -> exit 1."""
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--tds", "-1"])
    assert result.exit_code == 1
    assert "tds" in result.output.lower()
