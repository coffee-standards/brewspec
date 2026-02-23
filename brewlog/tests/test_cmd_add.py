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


def test_add_invalid_overall_out_of_range(runner_with_db):
    """AC-9/AC-26: --rating-overall 6 -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--rating-overall", "6",
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
    """AC-9: --date in completely wrong format -> error, exit 1."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "not-a-date",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 1


def test_add_date_only_accepted(runner_with_db):
    """AC-v0.4: date-only format YYYY-MM-DD is accepted."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
    ])
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


def test_add_invalid_grind_freeform(runner_with_db):
    """AC-v0.4: freeform grind value rejected."""
    result = runner_with_db.invoke(cli, [
        "add",
        "--date", "2026-02-19T08:30:00Z",
        "--type", "pour_over",
        "--dose", "18.0",
        "--water", "280.0",
        "--grind", "setting 15",
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
        "--grind", "medium_fine",
        "--duration", "180",
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
        assert row["grind"] == "medium_fine"
        assert row["duration_s"] == 180
        assert row["notes"] == "Bright acidity"
        assert row["coffee_roast_date"] == "2026-01-20"
        assert row["coffee_type"] == "single_origin"
        assert row["coffee_varietal"] == "Heirloom"
        assert row["coffee_process"] == "Washed"
        assert row["water_ppm"] == 150.0
        assert row["result_tds"] == 1.38
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
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


def test_add_interactive_shows_date_prompt(tmp_path, monkeypatch):
    """AC-6: date prompt includes 'Date' and shows default."""
    import brewlog.db as db_mod
    db_path = tmp_path / "prompt_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Date" in result.output


def test_add_interactive_reprompts_invalid_type(tmp_path, monkeypatch):
    """AC-7: invalid type re-prompts with error."""
    import brewlog.db as db_mod
    db_path = tmp_path / "reprompt_type.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    # First provide invalid menu choice '9', then valid '4' (pour_over)
    result = runner.invoke(cli, ["add"], input="\n9\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output
    assert "Invalid choice" in result.output


def test_add_interactive_reprompts_invalid_dose(tmp_path, monkeypatch):
    """AC-7: non-numeric dose re-prompts."""
    import brewlog.db as db_mod
    db_path = tmp_path / "reprompt_dose.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    # Provide: default date, valid type (4=pour_over), invalid dose 'abc', then valid
    result = runner.invoke(cli, ["add"], input="\n4\nabc\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Brew #1 logged." in result.output


# ---------------------------------------------------------------------------
# v0.2: Flag hint in fully-interactive mode
# ---------------------------------------------------------------------------

def test_add_interactive_shows_tip(tmp_path, monkeypatch):
    """v0.3: tip line printed when no required flags are supplied."""
    import brewlog.db as db_mod
    db_path = tmp_path / "tip_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Tip:" in result.output
    # v0.3: tip now shows --rating-overall, not --overall
    assert "--rating-overall" in result.output


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


# ---------------------------------------------------------------------------
# v0.2: Numbered brew type menu
# ---------------------------------------------------------------------------

def test_add_interactive_numbered_menu_shown(tmp_path, monkeypatch):
    """AC-10: numbered menu shows all four brew types."""
    import brewlog.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "menu_test.db")
    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "1)" in result.output
    assert "espresso" in result.output
    assert "pour_over" in result.output


def test_add_interactive_type_stored_as_string(tmp_path, monkeypatch):
    """AC-13: selecting option stores enum string, not integer."""
    import brewlog.db as db_mod
    db_path = tmp_path / "string_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner = CliRunner()
    runner.invoke(cli, ["add"], input="\n3\n18.0\n280.0\n")  # 3 = immersion
    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        assert row["type"] == "immersion"
    finally:
        conn.close()


def test_add_interactive_invalid_choice_reprompts(tmp_path, monkeypatch):
    """AC-11: invalid choice re-prompts with error message."""
    import brewlog.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "reprompt_menu.db")
    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n5\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "Invalid choice" in result.output


# ---------------------------------------------------------------------------
# v0.2: --ey, --grinder, --brewer flags on add (AC-14 to AC-17)
# ---------------------------------------------------------------------------

def test_add_ey_flag_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-14: --ey stored in DB (as result_ey)."""
    import brewlog.db as db_mod
    db_path = tmp_path / "ey_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--ey", "22.5",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_ey"] == 22.5
    finally:
        conn.close()


def test_add_ey_invalid_zero(runner_with_db):
    """AC-14: --ey 0 -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--ey", "0",
    ])
    assert result.exit_code == 1


def test_add_ey_invalid_negative(runner_with_db):
    """AC-14: --ey -1 -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--ey", "-1",
    ])
    assert result.exit_code == 1


def test_add_grinder_flag_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-15: --grinder stored in DB."""
    import brewlog.db as db_mod
    db_path = tmp_path / "grinder_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--grinder", "Comandante C40",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["equipment_grinder"] == "Comandante C40"
    finally:
        conn.close()


def test_add_grinder_empty_string(runner_with_db):
    """AC-15: --grinder '' -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--grinder", "",
    ])
    assert result.exit_code == 1


def test_add_brewer_flag_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-16: --brewer stored in DB."""
    import brewlog.db as db_mod
    db_path = tmp_path / "brewer_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--brewer", "Hario V60-02",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["equipment_brewer"] == "Hario V60-02"
    finally:
        conn.close()


def test_add_brewer_empty_string(runner_with_db):
    """AC-16: --brewer '' -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--brewer", "",
    ])
    assert result.exit_code == 1


def test_add_ey_grinder_brewer_together(runner_with_db, tmp_path, monkeypatch):
    """AC-17: all three new flags together stored in single INSERT."""
    import brewlog.db as db_mod
    db_path = tmp_path / "all_three.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-21T08:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
        "--ey", "21.0", "--grinder", "Niche Zero", "--brewer", "Chemex",
    ])
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        assert row["result_ey"] == 21.0
        assert row["equipment_grinder"] == "Niche Zero"
        assert row["equipment_brewer"] == "Chemex"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# v0.3: AC-25, AC-30 — --rating flag retired; tip updated
# ---------------------------------------------------------------------------

def test_add_rating_retired_flag_exits_1(runner_with_db):
    """AC-25: --rating N produces exit 1 (flag retired)."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating", "4",
    ])
    assert result.exit_code == 1


def test_add_rating_retired_message(runner_with_db):
    """AC-25: --rating N error message mentions --rating-overall."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating", "4",
    ])
    assert "--rating-overall" in result.output


def test_add_tip_shows_rating_overall(tmp_path, monkeypatch):
    """AC-30: interactive tip shows --rating-overall, not --rating."""
    import brewlog.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    assert "--rating-overall 4" in result.output


def test_add_tip_does_not_show_bare_rating(tmp_path, monkeypatch):
    """AC-30: interactive tip does not show bare '--rating 4' example."""
    import brewlog.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    runner = CliRunner()
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    # '--rating 4' should not appear (--rating-overall 4 is fine)
    import re
    assert not re.search(r"--rating\s+\d", result.output)


# ---------------------------------------------------------------------------
# v0.3: AC-24, AC-26 — all 8 --rating-* flags on add
# ---------------------------------------------------------------------------

def test_add_rating_overall_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-24, AC-26: --rating-overall stored in result_rating_overall."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-overall", "4",
    ])
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_rating_overall"] == 4
    finally:
        conn.close()


def test_add_rating_fragrance_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-24: --rating-fragrance stored in result_rating_fragrance."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-fragrance", "3",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_rating_fragrance"] == 3
    finally:
        conn.close()


def test_add_rating_aroma_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-24: --rating-aroma stored in result_rating_aroma."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-aroma", "4",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_rating_aroma"] == 4
    finally:
        conn.close()


def test_add_all_8_rating_dimensions_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-24: all 8 --rating-* flags stored in individual DB columns."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
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
    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
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


def test_add_rating_overall_invalid_zero(runner_with_db):
    """AC-26: --rating-overall 0 -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-overall", "0",
    ])
    assert result.exit_code == 1


def test_add_rating_overall_invalid_six(runner_with_db):
    """AC-26: --rating-overall 6 -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-overall", "6",
    ])
    assert result.exit_code == 1


def test_add_rating_overall_invalid_string(runner_with_db):
    """AC-26: --rating-overall abc -> Click rejects it (non-integer)."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--rating-overall", "abc",
    ])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# v0.3: AC-27 — --brix validation
# ---------------------------------------------------------------------------

def test_add_brix_valid_zero(runner_with_db, tmp_path, monkeypatch):
    """AC-27: --brix 0 is valid (0 Brix is physically meaningful)."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--brix", "0",
    ])
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_brix"] == 0.0
    finally:
        conn.close()


def test_add_brix_valid_positive(runner_with_db, tmp_path, monkeypatch):
    """AC-27: --brix 1.5 stored correctly."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--brix", "1.5",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_brix"] == 1.5
    finally:
        conn.close()


def test_add_brix_invalid_negative(runner_with_db):
    """AC-27: --brix -0.1 -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--brix", "-0.1",
    ])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# v0.3: AC-28 — --tasting-notes validation
# ---------------------------------------------------------------------------

def test_add_tasting_notes_stored(runner_with_db, tmp_path, monkeypatch):
    """AC-28: --tasting-notes stored in result_tasting_notes."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
        "--tasting-notes", "Bright acidity",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["result_tasting_notes"] == "Bright acidity"
    finally:
        conn.close()


def test_add_tasting_notes_empty_string_exits_1(runner_with_db):
    """AC-28: --tasting-notes '' -> exit 1."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--tasting-notes", "",
    ])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# v0.3: AC-29 — no result flags -> all result cols NULL
# ---------------------------------------------------------------------------

def test_add_no_result_flags_succeeds(runner_with_db, tmp_path, monkeypatch):
    """AC-29: omitting all result flags -> exit 0, result cols are NULL."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
    ])
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        assert row["result_rating_overall"] is None
        assert row["result_brix"] is None
        assert row["result_tasting_notes"] is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# v0.3: AC-6, AC-7, AC-8, AC-9 — date format UX
# ---------------------------------------------------------------------------

def test_date_prompt_default_is_today_yyyy_mm_dd(tmp_path, monkeypatch):
    """AC-6: interactive date prompt defaults to today in YYYY-MM-DD format."""
    from datetime import date as _date
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner = CliRunner()
    # Press Enter (accept default date), then type, dose, water
    result = runner.invoke(cli, ["add"], input="\n4\n18.0\n280.0\n")
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        row = db_mod.get_brew(1, conn)
        today_str = _date.today().strftime("%Y-%m-%d")
        assert row["date"] == today_str
    finally:
        conn.close()


def test_date_flag_accepts_date_only(runner_with_db, tmp_path, monkeypatch):
    """AC-8: --date YYYY-MM-DD accepted, exit 0."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
    ])
    assert result.exit_code == 0
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["date"] == "2026-02-22"
    finally:
        conn.close()


def test_date_stored_exactly_as_supplied_date_only(runner_with_db, tmp_path, monkeypatch):
    """AC-9: date-only value stored without normalisation."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["date"] == "2026-02-22"
    finally:
        conn.close()


def test_date_stored_exactly_as_supplied_datetime(runner_with_db, tmp_path, monkeypatch):
    """AC-9: full datetime stored without normalisation."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22T09:00:00Z", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0",
    ])
    conn = db_mod.get_connection(db_path=db_path)
    try:
        assert db_mod.get_brew(1, conn)["date"] == "2026-02-22T09:00:00Z"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# v0.3: AC-16, AC-18 — grind enum on add
# ---------------------------------------------------------------------------

def test_grind_all_valid_values_accepted(runner_with_db):
    """AC-16: all 7 grind enum values accepted."""
    for grind in ("turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"):
        result = runner_with_db.invoke(cli, [
            "add", "--date", "2026-02-22", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0", "--grind", grind,
        ])
        assert result.exit_code == 0, f"grind={grind} should be accepted"


def test_grind_hyphenated_rejected(runner_with_db):
    """AC-16: 'medium-fine' (hyphenated) is not a valid enum value."""
    result = runner_with_db.invoke(cli, [
        "add", "--date", "2026-02-22", "--type", "pour_over",
        "--dose", "18.0", "--water", "280.0", "--grind", "medium-fine",
    ])
    assert result.exit_code == 1


def test_grind_help_lists_enum_values(runner_with_db):
    """AC-18: --help lists grind enum values."""
    result = runner_with_db.invoke(cli, ["add", "--help"])
    assert "medium_fine" in result.output
    assert "coarse" in result.output
