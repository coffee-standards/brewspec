"""
CLI integration tests for `brewlog add`.
Tests map to AC-3, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module


@pytest.fixture
def runner_with_db(tmp_path, monkeypatch):
    """CliRunner with a temporary DB path injected."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


# ---------------------------------------------------------------------------
# AC-11: Non-interactive mode (all required flags supplied)
# ---------------------------------------------------------------------------

def test_add_all_flags_no_prompts(runner_with_db):
    """AC-11: all 4 required flags -> no prompts, brew logged."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 0
    assert "logged" in result.output.lower()


def test_add_confirmation_message(runner_with_db):
    """AC-10: output contains 'Brew #1 logged.'"""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


def test_add_second_brew_increments_id(runner_with_db):
    """AC-10: sequential adds produce incrementing IDs."""
    runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-20T08:30:00Z",
        "--type", "immersion",
        "--dose", "20.0",
        "--water", "300.0",
    ])
    assert "Brew #2 logged." in result.output


# ---------------------------------------------------------------------------
# AC-9: Validation of flags
# ---------------------------------------------------------------------------

def test_add_invalid_type_flag(runner_with_db):
    """AC-9: --type invalid -> error, exit 1, no DB write."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "invalid_type",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 1


def test_add_invalid_dose_zero(runner_with_db):
    """AC-9: --dose 0 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "0",
        "--water", "280.0",
    ])
    assert result.exit_code == 1


def test_add_invalid_dose_negative(runner_with_db):
    """AC-9: --dose -5 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "-5",
        "--water", "280.0",
    ])
    assert result.exit_code == 1


def test_add_invalid_temp_out_of_range(runner_with_db):
    """AC-9: --temp 101 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--temp", "101",
    ])
    assert result.exit_code == 1


def test_add_invalid_rating_out_of_range(runner_with_db):
    """AC-9: --rating 6 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--rating", "6",
    ])
    assert result.exit_code == 1


def test_add_invalid_duration_zero(runner_with_db):
    """AC-9: --duration 0 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--duration", "0",
    ])
    assert result.exit_code == 1


def test_add_invalid_roast_date_format(runner_with_db):
    """AC-9: --roast-date 01-20-2026 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--roast-date", "01-20-2026",
    ])
    assert result.exit_code == 1


def test_add_invalid_coffee_type(runner_with_db):
    """AC-9: --coffee-type espresso -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--coffee-type", "espresso",  # not a valid coffee type
    ])
    assert result.exit_code == 1


def test_add_invalid_date_format(runner_with_db):
    """AC-9: --date in wrong format -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19",  # missing time component
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-8: Optional fields stored
# ---------------------------------------------------------------------------

def test_add_origin_multiple(runner_with_db, tmp_path, monkeypatch):
    """AC-8: --origin Ethiopia --origin Colombia stored as list."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--origin", "Ethiopia",
        "--origin", "Colombia",
    ])
    assert result.exit_code == 0

    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        import json
        assert json.loads(row["coffee_origin"]) == ["Ethiopia", "Colombia"]
    finally:
        conn.close()


def test_add_optional_fields_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-8: all optional flags round-trip through DB."""
    import brewlog.db as db_mod
    db_path = tmp_path / "opt_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--method", "Hario V60",
        "--temp", "96.0",
        "--grind", "medium-fine",
        "--duration", "180",
        "--rating", "4",
        "--notes", "Bright acidity",
        "--roast-date", "2026-01-20",
        "--coffee-type", "single_origin",
        "--origin", "Ethiopia",
        "--varietal", "Heirloom",
        "--process", "Washed",
        "--water-ppm", "150.0",
        "--tds", "1.38",
    ])
    assert result.exit_code == 0

    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        assert row["method"] == "Hario V60"
        assert row["water_temp_c"] == 96.0
        assert row["grind"] == "medium-fine"
        assert row["duration_s"] == 180
        assert row["rating"] == 4
        assert row["notes"] == "Bright acidity"
        assert row["coffee_roast_date"] == "2026-01-20"
        assert row["coffee_type"] == "single_origin"
        assert row["coffee_varietal"] == "Heirloom"
        assert row["coffee_process"] == "Washed"
        assert row["water_ppm"] == 150.0
        assert row["tds"] == 1.38
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-3: DB auto-created
# ---------------------------------------------------------------------------

def test_add_db_auto_created(tmp_path, monkeypatch):
    """AC-3: first add creates DB file."""
    import brewlog.db as db_mod
    db_path = tmp_path / "auto" / "brews.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    assert not db_path.exists()
    runner = CliRunner()
    result = runner.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 0
    assert db_path.exists()


# ---------------------------------------------------------------------------
# AC-5, AC-6, AC-7: Interactive prompts
# ---------------------------------------------------------------------------

def test_add_interactive_accepts_default_date(tmp_path, monkeypatch):
    """AC-5, AC-6: empty Enter for date uses current UTC."""
    import brewlog.db as db_mod
    db_path = tmp_path / "interactive.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    # Simulate: press Enter (accept default date), then provide type/dose/water
    result = runner.invoke(cli, ["add"], input="\npour_over\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


def test_add_interactive_shows_date_prompt(tmp_path, monkeypatch):
    """AC-6: date prompt includes 'Date' and shows default."""
    import brewlog.db as db_mod
    db_path = tmp_path / "prompt_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\npour_over\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Date" in result.output


def test_add_interactive_reprompts_invalid_type(tmp_path, monkeypatch):
    """AC-7: invalid type re-prompts with error."""
    import brewlog.db as db_mod
    db_path = tmp_path / "reprompt_type.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    # First provide invalid type 'drip', then valid 'pour_over'
    result = runner.invoke(cli, ["add"], input="\ndrip\npour_over\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output
    # Should show an error message about the invalid type
    assert "immersion" in result.output or "error" in result.output.lower() or "invalid" in result.output.lower()


def test_add_interactive_reprompts_invalid_dose(tmp_path, monkeypatch):
    """AC-7: non-numeric dose re-prompts."""
    import brewlog.db as db_mod
    db_path = tmp_path / "reprompt_dose.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    # Provide: default date, valid type, invalid dose 'abc', then valid dose 18.0
    result = runner.invoke(cli, ["add"], input="\npour_over\nabc\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


# ---------------------------------------------------------------------------
# v0.2: Flag hint in fully-interactive mode
# ---------------------------------------------------------------------------

def test_add_interactive_shows_tip(tmp_path, monkeypatch):
    """v0.2: tip line printed when no required flags are supplied."""
    import brewlog.db as db_mod
    db_path = tmp_path / "tip_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\npour_over\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Tip:" in result.output
    assert "--rating" in result.output


def test_add_with_flags_no_tip(runner_with_db):
    """v0.2: tip NOT shown when required flags are supplied."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 0
    assert "Tip:" not in result.output
