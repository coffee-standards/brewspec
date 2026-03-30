"""
Tests for BrewSpec v0.8 BrewLog CLI adoption.

Covers:
- Pydantic model validation: roaster, roast_level, elevation_masl, water_temp_c precision
- DB migration: coffee_roaster and coffee_roast_level columns
- insert_brew() and insert_brew_dict() with new fields
- Serialise: export includes roaster, roast_level; BREWSPEC_VERSION is "0.9" (updated in CLI v0.8)
- Import: v0.9 documents accepted, v0.7 documents rejected with updated message
- add command: --roaster, --roast-level, --elevation-masl flags
- update command: --roaster, --roast-level flags
- show command: roaster and roast_level displayed in Coffee section

TDD: tests written before implementation.
"""

from __future__ import annotations

import json
import sqlite3

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import CoffeeInput, OriginInput, BrewInput
from brewlog.serialise import row_to_brew_dict, rows_to_brewspec_document, BREWSPEC_VERSION


# ---------------------------------------------------------------------------
# Note on stderr / stdout mixing
# ---------------------------------------------------------------------------
# Click's CliRunner mixes stderr into stdout by default (mix_stderr defaults
# to True in Click 8).  As a result, assertions against result.output capture
# both stdout and stderr output — error messages emitted via click.echo(...,
# err=True) or sys.stderr are visible in result.output without any extra
# configuration.  Tests below rely on this default behaviour.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Pydantic model: CoffeeInput.roaster validation
# ---------------------------------------------------------------------------

def test_coffee_input_roaster_valid_accepted():
    """roaster = 'Onyx' is accepted."""
    c = CoffeeInput(roaster="Onyx")
    assert c.roaster == "Onyx"


def test_coffee_input_roaster_none_accepted():
    """roaster = None (omitted) is accepted."""
    c = CoffeeInput()
    assert c.roaster is None


def test_coffee_input_roaster_empty_string_rejected():
    """roaster = '' raises ValidationError (minLength 1)."""
    with pytest.raises(ValidationError):
        CoffeeInput(roaster="")


def test_coffee_input_roaster_whitespace_only_rejected():
    """roaster = '   ' raises ValidationError (no content)."""
    with pytest.raises(ValidationError):
        CoffeeInput(roaster="   ")


def test_coffee_input_roaster_101_chars_rejected():
    """roaster longer than 100 characters raises ValidationError."""
    with pytest.raises(ValidationError):
        CoffeeInput(roaster="x" * 101)


def test_coffee_input_roaster_100_chars_accepted():
    """roaster exactly 100 characters is accepted."""
    c = CoffeeInput(roaster="x" * 100)
    assert len(c.roaster) == 100


# ---------------------------------------------------------------------------
# Pydantic model: CoffeeInput.roast_level validation
# ---------------------------------------------------------------------------

def test_coffee_input_roast_level_light_accepted():
    """roast_level = 'light' is accepted."""
    c = CoffeeInput(roast_level="light")
    assert c.roast_level == "light"


def test_coffee_input_roast_level_medium_accepted():
    """roast_level = 'medium' is accepted."""
    c = CoffeeInput(roast_level="medium")
    assert c.roast_level == "medium"


def test_coffee_input_roast_level_dark_accepted():
    """roast_level = 'dark' is accepted."""
    c = CoffeeInput(roast_level="dark")
    assert c.roast_level == "dark"


def test_coffee_input_roast_level_none_accepted():
    """roast_level = None is accepted."""
    c = CoffeeInput()
    assert c.roast_level is None


def test_coffee_input_roast_level_invalid_rejected():
    """roast_level = 'extra_dark' raises ValidationError."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_level="extra_dark")


def test_coffee_input_roast_level_case_sensitive_rejected():
    """roast_level = 'Light' (wrong case) raises ValidationError."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_level="Light")


# ---------------------------------------------------------------------------
# Pydantic model: OriginInput.elevation_masl validation
# ---------------------------------------------------------------------------

def test_origin_input_elevation_masl_positive_accepted():
    """elevation_masl = 1950 is accepted."""
    o = OriginInput(elevation_masl=1950)
    assert o.elevation_masl == 1950


def test_origin_input_elevation_masl_none_accepted():
    """elevation_masl = None is accepted."""
    o = OriginInput()
    assert o.elevation_masl is None


def test_origin_input_elevation_masl_zero_rejected():
    """elevation_masl = 0 raises ValidationError (must be > 0)."""
    with pytest.raises(ValidationError):
        OriginInput(elevation_masl=0)


def test_origin_input_elevation_masl_negative_rejected():
    """elevation_masl = -100 raises ValidationError."""
    with pytest.raises(ValidationError):
        OriginInput(elevation_masl=-100)


def test_origin_input_elevation_masl_one_accepted():
    """elevation_masl = 1 is accepted (smallest valid positive int)."""
    o = OriginInput(elevation_masl=1)
    assert o.elevation_masl == 1


# ---------------------------------------------------------------------------
# Pydantic model: BrewInput.water_temp_c precision validation
# ---------------------------------------------------------------------------

def test_brew_input_water_temp_one_decimal_accepted():
    """water_temp_c = 96.1 (1 decimal place) is accepted."""
    b = BrewInput(water_temp_c=96.1)
    assert b.water_temp_c == 96.1


def test_brew_input_water_temp_integer_accepted():
    """water_temp_c = 96 (integer, 0 decimal places) is accepted."""
    b = BrewInput(water_temp_c=96)
    assert b.water_temp_c == 96


def test_brew_input_water_temp_zero_decimals_accepted():
    """water_temp_c = 100.0 is accepted."""
    b = BrewInput(water_temp_c=100.0)
    assert b.water_temp_c == 100.0


def test_brew_input_water_temp_two_decimal_places_rejected():
    """water_temp_c = 96.15 (2 decimal places) raises ValidationError."""
    with pytest.raises(ValidationError):
        BrewInput(water_temp_c=96.15)


def test_brew_input_water_temp_three_decimal_places_rejected():
    """water_temp_c = 96.123 (3 decimal places) raises ValidationError."""
    with pytest.raises(ValidationError):
        BrewInput(water_temp_c=96.123)


def test_brew_input_water_temp_none_accepted():
    """water_temp_c = None is accepted."""
    b = BrewInput()
    assert b.water_temp_c is None


# ---------------------------------------------------------------------------
# DB migration: coffee_roaster, coffee_roast_level columns
# ---------------------------------------------------------------------------

def test_new_db_has_coffee_roaster_column(tmp_path):
    """Fresh database has coffee_roaster TEXT column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    assert "coffee_roaster" in cols


def test_new_db_has_coffee_roast_level_column(tmp_path):
    """Fresh database has coffee_roast_level TEXT column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    assert "coffee_roast_level" in cols


def test_existing_db_migration_adds_coffee_roaster(tmp_path):
    """Pre-v0.8 database gets coffee_roaster column via migration."""
    db_path = tmp_path / "old.db"

    # Create a DB without the new columns
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE brews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            dose_g REAL,
            water_weight_g REAL,
            coffee_name TEXT
        )
    """)
    conn.commit()
    conn.close()

    conn2 = db_module.get_connection(db_path=db_path)
    cols = {row[1] for row in conn2.execute("PRAGMA table_info(brews)").fetchall()}
    conn2.close()
    assert "coffee_roaster" in cols
    assert "coffee_roast_level" in cols


def test_migration_idempotent_for_v8_columns(tmp_path):
    """Calling get_connection() twice does not error or duplicate v0.8 columns."""
    conn1 = db_module.get_connection(db_path=tmp_path / "test.db")
    conn1.close()
    conn2 = db_module.get_connection(db_path=tmp_path / "test.db")
    cols = [row[1] for row in conn2.execute("PRAGMA table_info(brews)").fetchall()]
    conn2.close()
    assert cols.count("coffee_roaster") == 1
    assert cols.count("coffee_roast_level") == 1


# ---------------------------------------------------------------------------
# DB insert_brew() with new fields
# ---------------------------------------------------------------------------

def test_insert_brew_stores_roaster(tmp_path):
    """insert_brew() stores coffee.roaster in coffee_roaster column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew = BrewInput(
        date="2026-03-19",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
        coffee=CoffeeInput(roaster="Onyx"),
    )
    brew_id = db_module.insert_brew(brew, conn)
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roaster"] == "Onyx"


def test_insert_brew_stores_roast_level(tmp_path):
    """insert_brew() stores coffee.roast_level in coffee_roast_level column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew = BrewInput(
        date="2026-03-19",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
        coffee=CoffeeInput(roast_level="light"),
    )
    brew_id = db_module.insert_brew(brew, conn)
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roast_level"] == "light"


def test_insert_brew_stores_elevation_masl_in_origins_json(tmp_path):
    """insert_brew() stores elevation_masl inside the coffee_origins JSON blob."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew = BrewInput(
        date="2026-03-19",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
        coffee=CoffeeInput(
            origins=[OriginInput(country="Ethiopia", elevation_masl=1950)]
        ),
    )
    brew_id = db_module.insert_brew(brew, conn)
    row = db_module.get_brew(brew_id, conn)
    conn.close()

    origins = json.loads(row["coffee_origins"])
    assert origins[0]["elevation_masl"] == 1950


def test_insert_brew_no_coffee_roaster_and_level_are_null(tmp_path):
    """insert_brew() without coffee stores NULL for coffee_roaster and coffee_roast_level."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew = BrewInput(
        date="2026-03-19",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
    )
    brew_id = db_module.insert_brew(brew, conn)
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roaster"] is None
    assert row["coffee_roast_level"] is None


# ---------------------------------------------------------------------------
# DB insert_brew_dict() with new fields
# ---------------------------------------------------------------------------

def test_insert_brew_dict_stores_roaster(tmp_path):
    """insert_brew_dict() stores coffee.roaster in coffee_roaster column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew_dict = {
        "date": "2026-03-19",
        "type": "pour_over",
        "dose_g": 20.0,
        "water_weight_g": 320.0,
        "coffee": {"roaster": "Tim Wendelboe"},
    }
    brew_id = db_module.insert_brew_dict(brew_dict, conn)
    conn.commit()
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roaster"] == "Tim Wendelboe"


def test_insert_brew_dict_stores_roast_level(tmp_path):
    """insert_brew_dict() stores coffee.roast_level in coffee_roast_level column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew_dict = {
        "date": "2026-03-19",
        "type": "pour_over",
        "dose_g": 20.0,
        "water_weight_g": 320.0,
        "coffee": {"roast_level": "medium"},
    }
    brew_id = db_module.insert_brew_dict(brew_dict, conn)
    conn.commit()
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roast_level"] == "medium"


def test_insert_brew_dict_elevation_masl_in_origins_json(tmp_path):
    """insert_brew_dict() stores elevation_masl inside coffee_origins JSON."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    brew_dict = {
        "date": "2026-03-19",
        "type": "pour_over",
        "dose_g": 20.0,
        "water_weight_g": 320.0,
        "coffee": {
            "origins": [{"country": "Ethiopia", "elevation_masl": 2100}]
        },
    }
    brew_id = db_module.insert_brew_dict(brew_dict, conn)
    conn.commit()
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    origins = json.loads(row["coffee_origins"])
    assert origins[0]["elevation_masl"] == 2100


# ---------------------------------------------------------------------------
# Serialise: BREWSPEC_VERSION is "0.9"
# ---------------------------------------------------------------------------

def test_brewspec_version_constant_is_09():
    """BREWSPEC_VERSION constant in serialise.py is '0.9' (updated in v0.8 CLI)."""
    assert BREWSPEC_VERSION == "0.9"


def test_rows_to_brewspec_document_version_is_09(tmp_path):
    """rows_to_brewspec_document() produces brewspec_version '0.9'."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES (?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    doc = rows_to_brewspec_document(rows)
    assert doc["brewspec_version"] == "0.9"


# ---------------------------------------------------------------------------
# Serialise: row_to_brew_dict() includes roaster and roast_level
# ---------------------------------------------------------------------------

def test_row_to_brew_dict_includes_roaster(tmp_path):
    """row_to_brew_dict() includes coffee.roaster when present."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_roaster)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "George Howell"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    brew_dict = row_to_brew_dict(rows[0])
    assert "coffee" in brew_dict
    assert brew_dict["coffee"]["roaster"] == "George Howell"


def test_row_to_brew_dict_omits_roaster_when_null(tmp_path):
    """row_to_brew_dict() omits coffee.roaster when NULL."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "My Coffee"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    brew_dict = row_to_brew_dict(rows[0])
    assert "coffee" in brew_dict
    assert "roaster" not in brew_dict["coffee"]


def test_row_to_brew_dict_includes_roast_level(tmp_path):
    """row_to_brew_dict() includes coffee.roast_level when present."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_roast_level)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "dark"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    brew_dict = row_to_brew_dict(rows[0])
    assert "coffee" in brew_dict
    assert brew_dict["coffee"]["roast_level"] == "dark"


def test_row_to_brew_dict_omits_roast_level_when_null(tmp_path):
    """row_to_brew_dict() omits coffee.roast_level when NULL."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "My Coffee"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    brew_dict = row_to_brew_dict(rows[0])
    assert "coffee" in brew_dict
    assert "roast_level" not in brew_dict["coffee"]


def test_row_to_brew_dict_elevation_masl_round_trips(tmp_path):
    """elevation_masl round-trips via the coffee_origins JSON blob."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    origins_json = json.dumps([{"country": "Colombia", "elevation_masl": 1800}])
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_origins)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, origins_json))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    brew_dict = row_to_brew_dict(rows[0])
    assert brew_dict["coffee"]["origins"][0]["elevation_masl"] == 1800


# ---------------------------------------------------------------------------
# Bundled schema version
# ---------------------------------------------------------------------------

def test_bundled_schema_is_v09():
    """brewlog/src/brewlog/brewspec.schema.json must declare version 0.9 (updated in CLI v0.8)."""
    import importlib.resources
    import json as json_mod
    with importlib.resources.files("brewlog").joinpath("brewspec.schema.json").open(
        "r", encoding="utf-8"
    ) as f:
        schema = json_mod.load(f)
    assert schema["properties"]["brewspec_version"]["const"] == "0.9"


# ---------------------------------------------------------------------------
# Import: v0.9 document accepted
# ---------------------------------------------------------------------------

def test_import_v09_doc_accepted(tmp_path):
    """Importing a v0.9 document succeeds (CLI v0.8 adopts BrewSpec v0.9)."""
    yaml_content = """
brewspec_version: "0.9"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v09.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output
    assert "1 brews added" in result.output


def test_import_v09_doc_with_roaster_stores_roaster(tmp_path):
    """Importing a v0.9 document with coffee.roaster stores it in DB."""
    yaml_content = """
brewspec_version: "0.9"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
    coffee:
      roaster: "Onyx"
      roast_level: "light"
"""
    doc_path = tmp_path / "v09_roaster.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["coffee_roaster"] == "Onyx"
    assert rows[0]["coffee_roast_level"] == "light"


def test_import_v09_doc_with_elevation_masl_stores_in_origins(tmp_path):
    """Importing a v0.9 document with elevation_masl stores it in origins JSON."""
    yaml_content = """
brewspec_version: "0.9"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
    coffee:
      origins:
        - country: "Ethiopia"
          elevation_masl: 2100
"""
    doc_path = tmp_path / "v09_elevation.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    origins = json.loads(rows[0]["coffee_origins"])
    assert origins[0]["elevation_masl"] == 2100


# ---------------------------------------------------------------------------
# Import: v0.7 document rejected with v0.9 message
# ---------------------------------------------------------------------------

def test_import_v07_file_rejected_with_v09_message(tmp_path):
    """Importing a v0.7 document is rejected with a message referencing v0.9."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v07.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 1
    assert "0.7" in result.output
    assert "0.9" in result.output


def test_import_exact_v07_rejection_message(tmp_path):
    """Exact rejection message for v0.7 file references v0.9 correctly."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v07.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 1
    expected = (
        "Error: This file uses BrewSpec v0.7, which is not supported by BrewLog v0.8.\n"
        "BrewLog v0.8 requires BrewSpec v0.9."
    )
    assert expected in result.output


# ---------------------------------------------------------------------------
# Import round-trip: v0.9 fields survive import → export
# ---------------------------------------------------------------------------

def test_import_export_roundtrip_v09_roaster_and_level(tmp_path):
    """roaster and roast_level survive import → DB → export unchanged (v0.9 doc)."""
    yaml_content = """
brewspec_version: "0.9"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
    coffee:
      roaster: "Onyx"
      roast_level: "light"
"""
    doc_path = tmp_path / "v09.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    doc = rows_to_brewspec_document(rows)
    conn.close()

    assert doc["brewspec_version"] == "0.9"
    brew = doc["brews"][0]
    assert brew["coffee"]["roaster"] == "Onyx"
    assert brew["coffee"]["roast_level"] == "light"


# ---------------------------------------------------------------------------
# add command: --roaster flag
# ---------------------------------------------------------------------------

def test_add_cmd_roaster_flag_stores_roaster(tmp_path):
    """add --roaster 'Onyx' stores roaster in DB."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "add",
        "--date", "2026-03-19",
        "--type", "pour_over",
        "--dose", "20.0",
        "--water", "320.0",
        "--roaster", "Onyx",
    ])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["coffee_roaster"] == "Onyx"


def test_add_cmd_roast_level_flag_stores_level(tmp_path):
    """add --roast-level light stores roast_level in DB."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "add",
        "--date", "2026-03-19",
        "--type", "pour_over",
        "--dose", "20.0",
        "--water", "320.0",
        "--roast-level", "light",
    ])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["coffee_roast_level"] == "light"


def test_add_cmd_invalid_roast_level_rejected(tmp_path):
    """add --roast-level 'extra_dark' exits with error."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "add",
        "--date", "2026-03-19",
        "--type", "pour_over",
        "--dose", "20.0",
        "--water", "320.0",
        "--roast-level", "extra_dark",
    ])
    assert result.exit_code == 1


def test_add_cmd_elevation_masl_stores_in_origins(tmp_path):
    """add --elevation-masl 1950 stores elevation in origins JSON."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "add",
        "--date", "2026-03-19",
        "--type", "pour_over",
        "--dose", "20.0",
        "--water", "320.0",
        "--origin-country", "Ethiopia",
        "--elevation-masl", "1950",
    ])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    origins = json.loads(rows[0]["coffee_origins"])
    assert origins[0]["elevation_masl"] == 1950


def test_add_cmd_elevation_masl_zero_rejected(tmp_path):
    """add --elevation-masl 0 exits with error."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "add",
        "--date", "2026-03-19",
        "--type", "pour_over",
        "--dose", "20.0",
        "--water", "320.0",
        "--origin-country", "Ethiopia",
        "--elevation-masl", "0",
    ])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# update command: --roaster and --roast-level flags
# ---------------------------------------------------------------------------

def test_update_cmd_roaster_flag_updates_column(tmp_path):
    """update --roaster 'Onyx' updates the coffee_roaster column."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES (?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "update", str(brew_id),
        "--roaster", "Onyx",
    ])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roaster"] == "Onyx"


def test_update_cmd_roast_level_flag_updates_column(tmp_path):
    """update --roast-level dark updates the coffee_roast_level column."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES (?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "update", str(brew_id),
        "--roast-level", "dark",
    ])
    assert result.exit_code == 0, result.output

    conn = db_module.get_connection(db_path=db_path)
    row = db_module.get_brew(brew_id, conn)
    conn.close()
    assert row["coffee_roast_level"] == "dark"


def test_update_cmd_invalid_roast_level_rejected(tmp_path):
    """update --roast-level 'blonde' exits with error."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES (?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--db", str(db_path), "update", str(brew_id),
        "--roast-level", "blonde",
    ])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# show command: roaster and roast_level displayed
# ---------------------------------------------------------------------------

def test_show_displays_roaster(tmp_path):
    """show command displays coffee_roaster in Coffee section."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_roaster)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "Tim Wendelboe"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "Tim Wendelboe" in result.output
    assert "Roaster:" in result.output


def test_show_displays_roast_level(tmp_path):
    """show command displays coffee_roast_level in Coffee section."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_roast_level)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "medium"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "medium" in result.output
    assert "Roast Level:" in result.output


def test_show_omits_roaster_when_null(tmp_path):
    """show command omits Roaster line when coffee_roaster is NULL."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, "My Coffee"))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "Roaster:" not in result.output


def test_show_displays_elevation_masl_via_origins(tmp_path):
    """show command displays elevation_masl when present in origins JSON."""
    db_path = tmp_path / "test.db"
    conn = db_module.get_connection(db_path=db_path)
    origins_json = json.dumps([{"country": "Colombia", "elevation_masl": 1800}])
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_origins)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-19", "pour_over", 20.0, 320.0, origins_json))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "1800" in result.output
    assert "Elevation" in result.output
