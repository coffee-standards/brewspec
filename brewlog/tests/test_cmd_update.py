"""
CLI integration tests for `brewlog update`.
Tests map to BrewLog v0.2 + v0.3 update command acceptance criteria.

v0.3 changes:
- --overall flag retired; replaced by --rating-overall (and 7 other dimensions)
- All rating dimensions stored in individual DB columns (not JSON)
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

def test_update_rating_overall_on_latest(runner, db_path, monkeypatch):
    """v0.3: No ID arg — updates the latest brew's overall rating via --rating-overall."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, ["update", "--rating-overall", "4"])
    assert result.exit_code == 0
    assert "Brew #1 updated." in result.output

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["result_rating_overall"] == 4
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
    """Sets rating-overall, method, and grind in one call."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, [
        "update", "--rating-overall", "5", "--method", "Chemex", "--grind", "medium_coarse",
    ])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["result_rating_overall"] == 5
        assert row["method"] == "Chemex"
        assert row["grind"] == "medium_coarse"
    finally:
        conn.close()


def test_update_defaults_to_latest_not_oldest(runner, db_path, monkeypatch):
    """With two brews logged, no-ID update targets the latest one."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner, date="2026-02-18T08:00:00Z")   # brew #1 — older
    _add_brew(runner, date="2026-02-20T08:00:00Z")   # brew #2 — newer

    result = runner.invoke(cli, ["update", "--rating-overall", "3"])
    assert result.exit_code == 0
    assert "Brew #2 updated." in result.output

    conn = db_module.get_connection(db_path=db_path)
    try:
        row1 = db_module.get_brew(1, conn)
        row2 = db_module.get_brew(2, conn)
        assert row1["result_rating_overall"] is None    # oldest untouched
        assert row2["result_rating_overall"] == 3       # latest updated
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
# Error cases (existing)
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

    result = runner.invoke(cli, ["update", "999", "--rating-overall", "3"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "999" in result.output


def test_update_no_brews(runner):
    """Empty DB, no ID supplied -> exit 1."""
    result = runner.invoke(cli, ["update", "--rating-overall", "4"])
    assert result.exit_code == 1
    assert "no brews" in result.output.lower() or "empty" in result.output.lower()


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


# ---------------------------------------------------------------------------
# v0.3: AC-32 — --rating flag retired on update
# ---------------------------------------------------------------------------

def test_update_rating_retired_flag_exits_1(runner):
    """AC-32: --rating N on update produces exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--rating", "4"])
    assert result.exit_code == 1


def test_update_rating_retired_message(runner):
    """AC-32: --rating N on update shows message mentioning --rating-overall."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--rating", "4"])
    assert "--rating-overall" in result.output


# ---------------------------------------------------------------------------
# v0.3: AC-31, AC-33 — all 8 --rating-* dimension flags on update
# ---------------------------------------------------------------------------

def test_update_all_rating_dimensions_stored(runner, db_path, monkeypatch):
    """AC-31, AC-33: all 8 --rating-* flags stored in individual columns."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)

    result = runner.invoke(cli, [
        "update",
        "--rating-overall", "4",
        "--rating-fragrance", "3",
        "--rating-aroma", "4",
        "--rating-flavour", "5",
        "--rating-aftertaste", "4",
        "--rating-acidity", "5",
        "--rating-sweetness", "3",
        "--rating-mouthfeel", "4",
    ])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        assert row["result_rating_overall"] == 4
        assert row["result_rating_fragrance"] == 3
        assert row["result_rating_aroma"] == 4
        assert row["result_rating_flavour"] == 5
        assert row["result_rating_aftertaste"] == 4
        assert row["result_rating_acidity"] == 5
        assert row["result_rating_sweetness"] == 3
        assert row["result_rating_mouthfeel"] == 4
    finally:
        conn.close()


def test_update_rating_invalid_exits_1(runner):
    """AC-33: --rating-overall 6 -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--rating-overall", "6"])
    assert result.exit_code == 1


def test_update_rating_zero_exits_1(runner):
    """AC-33: --rating-overall 0 -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--rating-overall", "0"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# v0.3: AC-33 — --brix and --tasting-notes on update
# ---------------------------------------------------------------------------

def test_update_brix_valid(runner, db_path, monkeypatch):
    """AC-33: --brix 1.5 stored correctly."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--brix", "1.5"])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn)["result_brix"] == 1.5
    finally:
        conn.close()


def test_update_brix_negative_exits_1(runner):
    """AC-33: --brix -1 -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--brix", "-1"])
    assert result.exit_code == 1


def test_update_tasting_notes_stored(runner, db_path, monkeypatch):
    """AC-33: --tasting-notes stored in result_tasting_notes."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--tasting-notes", "Caramel finish"])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn)["result_tasting_notes"] == "Caramel finish"
    finally:
        conn.close()


def test_update_tasting_notes_empty_exits_1(runner):
    """AC-33: --tasting-notes '' -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--tasting-notes", ""])
    assert result.exit_code == 1


def test_update_does_not_write_result_ratings_column(runner, db_path, monkeypatch):
    """AC-31: updating rating-overall does not touch result_ratings JSON column."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)
    runner.invoke(cli, ["update", "--rating-overall", "4"])

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = db_module.get_brew(1, conn)
        # result_ratings should still be NULL (we never wrote to it)
        assert row["result_ratings"] is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# v0.3: AC-17 — grind enum on update
# ---------------------------------------------------------------------------

def test_update_grind_valid(runner, db_path, monkeypatch):
    """AC-17: --grind coarse stored correctly."""
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--grind", "coarse"])
    assert result.exit_code == 0

    conn = db_module.get_connection(db_path=db_path)
    try:
        assert db_module.get_brew(1, conn)["grind"] == "coarse"
    finally:
        conn.close()


def test_update_grind_invalid(runner):
    """AC-17: --grind 'light' (not in enum) -> exit 1."""
    _add_brew(runner)
    result = runner.invoke(cli, ["update", "--grind", "light"])
    assert result.exit_code == 1
