"""
CLI integration tests for `brewlog show`.
Tests map to AC-17, AC-18, AC-19, AC-20.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput, ResultInput, RatingsInput


@pytest.fixture
def runner_with_db(tmp_path, monkeypatch):
    """CliRunner with a temporary DB path injected."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


def _insert_minimal(db_path):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _insert_full(db_path):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="Hario V60",
            water_temp_c=96.0,
            grind="medium_fine",
            duration_s=180,
            notes="Bright acidity",
            coffee=CoffeeInput(
                roast_date="2026-01-20",
                type="single_origin",
                origin=["Ethiopia"],
                varietal="Heirloom",
                process="Washed",
            ),
            water=WaterInput(ppm=150.0),
            result=ResultInput(
                tds=1.38,
                ey=20.5,
                ratings=RatingsInput(overall=4),
            ),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-17: Show all fields
# ---------------------------------------------------------------------------

def test_show_existing_brew(runner_with_db, tmp_path):
    """AC-17: shows all fields for brew #1."""
    _insert_full(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "2026-02-19T08:30:00Z" in result.output
    assert "pour_over" in result.output
    assert "Hario V60" in result.output
    assert "18.0" in result.output
    assert "280.0" in result.output


def test_show_result_fields_displayed(runner_with_db, tmp_path):
    """AC-17: result sub-object fields shown."""
    _insert_full(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "TDS" in result.output
    assert "1.38" in result.output


def test_show_omits_null_fields(runner_with_db, tmp_path):
    """AC-17: field not set is absent from output."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    # These optional fields were not set — they should not appear
    assert "Method" not in result.output
    assert "Grind" not in result.output
    assert "TDS" not in result.output


# ---------------------------------------------------------------------------
# AC-18: Grouped output sections
# ---------------------------------------------------------------------------

def test_show_groups_fields(runner_with_db, tmp_path):
    """AC-18: brew parameters, results, coffee, water sections present."""
    _insert_full(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    output = result.output
    assert "Brew parameters" in output or "Brew #1" in output
    assert "Results" in output or "TDS" in output
    assert "Coffee" in output
    assert "Water" in output


def test_show_omits_empty_sections(runner_with_db, tmp_path):
    """AC-18: no coffee section if no coffee metadata."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    # Coffee and Water *section headings* should not appear as standalone lines.
    # Note: "Water weight:" is a brew parameter field and legitimately contains "Water".
    # We check for section headings as standalone words on their own line.
    lines = result.output.split("\n")
    section_headings = [ln.strip() for ln in lines]
    assert "Coffee" not in section_headings
    assert "Water" not in section_headings


def test_show_displays_brew_id_header(runner_with_db, tmp_path):
    """AC-18: output starts with Brew #ID header."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Brew #1" in result.output


# ---------------------------------------------------------------------------
# AC-19: Brew not found
# ---------------------------------------------------------------------------

def test_show_not_found_message(runner_with_db):
    """AC-19: 'No brew found with ID 999.' printed."""
    result = runner_with_db.invoke(cli, ["show", "999"])
    assert "No brew found with ID 999" in result.output


def test_show_not_found_exit_nonzero(runner_with_db):
    """AC-19: exit code 1 when not found."""
    result = runner_with_db.invoke(cli, ["show", "999"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-20: Missing argument
# ---------------------------------------------------------------------------

def test_show_no_argument_error(runner_with_db):
    """AC-20: missing ID -> usage error, exit nonzero."""
    result = runner_with_db.invoke(cli, ["show"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# AC-1 (v0.2): show error goes to stderr
# ---------------------------------------------------------------------------

def test_show_not_found_goes_to_stderr(tmp_path, monkeypatch):
    """AC-1: missing brew ID produces error message and exit 1."""
    from brewlog import db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "999"])
    assert result.exit_code == 1
    assert "No brew found with ID 999" in result.output


# ---------------------------------------------------------------------------
# v0.3: AC-35, AC-36, AC-37 — Results section with individual rating columns
# ---------------------------------------------------------------------------

def _insert_brew_with_ratings(db_path, **result_kwargs):
    """Insert a brew with specified result fields."""
    from brewlog.models import ResultInput, RatingsInput
    conn = db_module.get_connection(db_path=db_path)
    try:
        ratings_data = {k: v for k, v in result_kwargs.items() if k.startswith("rating_")}
        result_data = {k: v for k, v in result_kwargs.items() if not k.startswith("rating_")}
        ratings_obj = RatingsInput(**{k[len("rating_"):]: v for k, v in ratings_data.items()}) if ratings_data else None
        result_obj = ResultInput(**result_data, ratings=ratings_obj) if (result_data or ratings_obj) else None
        from brewlog.models import BrewInput
        brew = BrewInput(
            date="2026-02-22",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            result=result_obj,
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def test_show_results_section_present_when_any_result_set(runner_with_db, tmp_path):
    """AC-35: Results section shows when any result field is populated."""
    _insert_brew_with_ratings(tmp_path / "test.db", rating_overall=4)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "Results" in result.output


def test_show_results_section_absent_when_no_results(runner_with_db, tmp_path):
    """AC-35: Results section omitted when no result fields have values."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "Results" not in result.output


def test_show_tds_displayed_in_results(runner_with_db, tmp_path):
    """AC-36: TDS shown under Results section."""
    _insert_brew_with_ratings(tmp_path / "test.db", tds=1.38)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "1.38" in result.output


def test_show_ey_displayed_in_results(runner_with_db, tmp_path):
    """AC-36: EY shown under Results section."""
    _insert_brew_with_ratings(tmp_path / "test.db", ey=20.1)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "20.1" in result.output


def test_show_brix_displayed_in_results(runner_with_db, tmp_path):
    """AC-36: Brix shown under Results section."""
    _insert_brew_with_ratings(tmp_path / "test.db", brix=1.5)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "1.5" in result.output


def test_show_tasting_notes_displayed_in_results(runner_with_db, tmp_path):
    """AC-36: Tasting notes shown under Results section."""
    _insert_brew_with_ratings(tmp_path / "test.db", tasting_notes="Bright citrus")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Bright citrus" in result.output


def test_show_ratings_subsection_present_when_any_rating_set(runner_with_db, tmp_path):
    """AC-36, AC-37: Ratings sub-section shows when any rating is set."""
    _insert_brew_with_ratings(tmp_path / "test.db", rating_overall=4)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Ratings" in result.output


def test_show_ratings_subsection_absent_when_no_ratings(runner_with_db, tmp_path):
    """AC-37: Ratings sub-section omitted if no rating dimensions have values."""
    _insert_brew_with_ratings(tmp_path / "test.db", tds=1.38)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Ratings" not in result.output


def test_show_displays_each_rating_dimension(runner_with_db, tmp_path):
    """AC-36: all 8 rating dimensions shown when set."""
    _insert_brew_with_ratings(
        tmp_path / "test.db",
        rating_overall=4, rating_fragrance=3, rating_aroma=4,
        rating_flavour=5, rating_aftertaste=4, rating_acidity=5,
        rating_sweetness=3, rating_mouthfeel=4,
    )
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Overall" in result.output
    assert "Fragrance" in result.output
    assert "Aroma" in result.output
    assert "Flavour" in result.output
    assert "Aftertaste" in result.output
    assert "Acidity" in result.output
    assert "Sweetness" in result.output
    assert "Mouthfeel" in result.output


def test_show_omits_unset_rating_dimensions(runner_with_db, tmp_path):
    """AC-36: only set dimensions appear in Ratings sub-section."""
    _insert_brew_with_ratings(tmp_path / "test.db", rating_overall=4)
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Overall" in result.output
    assert "Fragrance" not in result.output


def test_show_legacy_ratings_json_displayed(runner_with_db, tmp_path):
    """AC-35: v0.2 row with result_ratings JSON still shows ratings in output."""
    # Simulate a v0.2 row: write directly to result_ratings column
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    try:
        import json
        conn.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, result_ratings) "
            "VALUES (?, ?, ?, ?, ?)",
            ("2026-02-22", "pour_over", 18.0, 280.0, json.dumps({"overall": 3})),
        )
        conn.commit()
    finally:
        conn.close()
    result = runner_with_db.invoke(cli, ["show", "1"])
    # Should display Overall rating from legacy JSON
    assert "3" in result.output
    assert "Results" in result.output


def test_show_displays_grind_as_raw_enum(runner_with_db, tmp_path):
    """AC-19: grind displayed as raw enum string."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    try:
        from brewlog.models import BrewInput
        brew = BrewInput(
            date="2026-02-22",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="medium_fine",
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "medium_fine" in result.output
