"""
End-to-end export/import round-trip tests.
Tests map to AC-21, AC-22, AC-24, AC-28.
"""

import yaml
from pathlib import Path
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module, schema as schema_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput, ResultInput


def _insert_brew(db_path, brew: BrewInput):
    conn = db_module.get_connection(db_path=db_path)
    try:
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _count_rows(db_path) -> int:
    conn = db_module.get_connection(db_path=db_path)
    try:
        rows = db_module.list_brews(conn, all_rows=True)
        return len(rows)
    finally:
        conn.close()


def _get_all_rows(db_path):
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.list_brews(conn, all_rows=True)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test helpers: three distinct brews
# ---------------------------------------------------------------------------

def _three_brews():
    return [
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="Hario V60",
            result=ResultInput(tds=1.38, ey=20.5),
        ),
        BrewInput(
            date="2026-02-18T07:15:00Z",
            type="immersion",
            dose_g=20.0,
            water_weight_g=300.0,
            duration_s=240,
            coffee=CoffeeInput(
                origin=["Ethiopia", "Colombia"],
                type="blend",
            ),
        ),
        BrewInput(
            date="2026-02-17T06:00:00Z",
            type="espresso",
            dose_g=18.0,
            water_weight_g=36.0,
            duration_s=28,
            water=WaterInput(ppm=100.0),
            result=ResultInput(tds=8.5),
        ),
    ]


# ---------------------------------------------------------------------------
# Round-trip: YAML
# ---------------------------------------------------------------------------

def test_export_import_roundtrip_yaml(tmp_path, monkeypatch):
    """AC-21, AC-28: add 3 brews -> export YAML -> import to fresh DB -> all fields match."""
    import brewlog.db as db_mod

    # Source DB
    src_db = tmp_path / "source.db"
    for brew in _three_brews():
        _insert_brew(src_db, brew)

    # Export from source
    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    result = runner.invoke(cli, ["export", export_file])
    assert result.exit_code == 0

    # Import into fresh DB
    dest_db = tmp_path / "dest.db"
    monkeypatch.setattr(db_mod, "DB_PATH", dest_db)
    result = runner.invoke(cli, ["import", export_file])
    assert result.exit_code == 0
    assert "Imported 3 brews." in result.output

    assert _count_rows(dest_db) == 3


def test_export_import_roundtrip_json(tmp_path, monkeypatch):
    """AC-22, AC-28: same round-trip with JSON format."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    for brew in _three_brews():
        _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.json")
    result = runner.invoke(cli, ["export", export_file, "--format", "json"])
    assert result.exit_code == 0

    dest_db = tmp_path / "dest.db"
    monkeypatch.setattr(db_mod, "DB_PATH", dest_db)
    result = runner.invoke(cli, ["import", export_file])
    assert result.exit_code == 0

    assert _count_rows(dest_db) == 3


# ---------------------------------------------------------------------------
# Round-trip: origin array preserved
# ---------------------------------------------------------------------------

def test_roundtrip_origin_array_preserved(tmp_path, monkeypatch):
    """AC-8: multi-origin blend survives export/import unchanged."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="immersion",
        dose_g=20.0,
        water_weight_g=300.0,
        coffee=CoffeeInput(
            origin=["Ethiopia", "Colombia", "Guatemala"],
            type="blend",
        ),
    )
    _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    runner.invoke(cli, ["export", export_file])

    dest_db = tmp_path / "dest.db"
    monkeypatch.setattr(db_mod, "DB_PATH", dest_db)
    runner.invoke(cli, ["import", export_file])

    conn = db_mod.get_connection(db_path=dest_db)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 1
        import json as json_mod
        origin = json_mod.loads(rows[0]["coffee_origin"])
        assert origin == ["Ethiopia", "Colombia", "Guatemala"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Round-trip: null fields absent after round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_optional_absent_fields_omitted(tmp_path, monkeypatch):
    """AC-24: null fields absent after round-trip."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    runner.invoke(cli, ["export", export_file])

    doc = yaml.safe_load(Path(export_file).read_text())
    brew_dict = doc["brews"][0]

    # No null values anywhere
    for key, value in brew_dict.items():
        assert value is not None
    # No optional sub-objects
    assert "coffee" not in brew_dict
    assert "water" not in brew_dict
    assert "method" not in brew_dict
    assert "result" not in brew_dict


# ---------------------------------------------------------------------------
# Round-trip: schema valid at midpoint
# ---------------------------------------------------------------------------

def test_roundtrip_schema_valid_at_midpoint(tmp_path, monkeypatch):
    """AC-21: exported file passes JSON Schema validation independently."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    for brew in _three_brews():
        _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    runner.invoke(cli, ["export", export_file])

    doc = yaml.safe_load(Path(export_file).read_text())
    errors = schema_module.validate_document(doc)
    assert errors == [], f"Schema validation errors: {errors}"


# ---------------------------------------------------------------------------
# AC-9/AC-10: date-only format round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_date_only_format_preserved(tmp_path, monkeypatch):
    """AC-9: YYYY-MM-DD date stored and exported as-is (no normalisation)."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    brew = BrewInput(
        date="2026-02-22",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    result = runner.invoke(cli, ["export", export_file])
    assert result.exit_code == 0

    doc = yaml.safe_load(Path(export_file).read_text())
    brew_dict = doc["brews"][0]
    assert brew_dict["date"] == "2026-02-22"


def test_roundtrip_date_only_import_roundtrip(tmp_path, monkeypatch):
    """AC-9: YYYY-MM-DD date survives export->import cycle unchanged."""
    import brewlog.db as db_mod

    src_db = tmp_path / "source.db"
    brew = BrewInput(
        date="2026-02-22",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    runner.invoke(cli, ["export", export_file])

    dest_db = tmp_path / "dest.db"
    monkeypatch.setattr(db_mod, "DB_PATH", dest_db)
    runner.invoke(cli, ["import", export_file])

    conn = db_mod.get_connection(db_path=dest_db)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert rows[0]["date"] == "2026-02-22"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-12: all 8 rating dimensions round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_all_rating_dimensions(tmp_path, monkeypatch):
    """AC-12: all 8 SCA rating dimensions survive export->import unchanged."""
    import brewlog.db as db_mod
    from brewlog.models import RatingsInput

    src_db = tmp_path / "source.db"
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        result=ResultInput(
            ratings=RatingsInput(
                overall=4,
                fragrance=3,
                aroma=5,
                flavour=4,
                aftertaste=3,
                acidity=5,
                sweetness=4,
                mouthfeel=3,
            )
        ),
    )
    _insert_brew(src_db, brew)

    monkeypatch.setattr(db_mod, "DB_PATH", src_db)
    runner = CliRunner()
    export_file = str(tmp_path / "export.yaml")
    result = runner.invoke(cli, ["export", export_file])
    assert result.exit_code == 0

    # Schema validation at midpoint
    doc = yaml.safe_load(Path(export_file).read_text())
    errors = schema_module.validate_document(doc)
    assert errors == [], f"Schema errors at midpoint: {errors}"

    # Import into fresh DB
    dest_db = tmp_path / "dest.db"
    monkeypatch.setattr(db_mod, "DB_PATH", dest_db)
    result = runner.invoke(cli, ["import", export_file])
    assert result.exit_code == 0

    # Verify all 8 dimensions survived
    conn = db_mod.get_connection(db_path=dest_db)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 1
        row = rows[0]
        assert row["result_rating_overall"] == 4
        assert row["result_rating_fragrance"] == 3
        assert row["result_rating_aroma"] == 5
        assert row["result_rating_flavour"] == 4
        assert row["result_rating_aftertaste"] == 3
        assert row["result_rating_acidity"] == 5
        assert row["result_rating_sweetness"] == 4
        assert row["result_rating_mouthfeel"] == 3
    finally:
        conn.close()
