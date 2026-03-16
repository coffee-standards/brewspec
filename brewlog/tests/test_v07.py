"""
Tests for BrewSpec v0.7 BrewLog CLI changes.

Covers:
- ResultInput.yield_g Pydantic model validation (AC: yield_g > 0, optional)
- DB migration: result_yield_g REAL column (new DB and existing DB)
- Import/export round-trip with yield_g
- show command display of yield_g

TDD: tests written before implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import ResultInput
from brewlog.serialise import row_to_brew_dict, rows_to_brewspec_document


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Pydantic model: ResultInput.yield_g validation
# ---------------------------------------------------------------------------

def test_result_input_yield_g_positive_accepted():
    """AC: yield_g = 36.5 is accepted."""
    result = ResultInput(yield_g=36.5)
    assert result.yield_g == 36.5


def test_result_input_yield_g_none_accepted():
    """AC: yield_g = None (omitted) is accepted."""
    result = ResultInput()
    assert result.yield_g is None


def test_result_input_yield_g_zero_rejected():
    """AC: yield_g = 0 raises ValidationError (must be > 0)."""
    with pytest.raises(ValidationError):
        ResultInput(yield_g=0)


def test_result_input_yield_g_negative_rejected():
    """AC: yield_g = -1 raises ValidationError."""
    with pytest.raises(ValidationError):
        ResultInput(yield_g=-1)


def test_result_input_yield_g_small_positive_accepted():
    """AC: yield_g = 0.1 is accepted (smallest valid positive)."""
    result = ResultInput(yield_g=0.1)
    assert result.yield_g == 0.1


# ---------------------------------------------------------------------------
# DB migration: result_yield_g column
# ---------------------------------------------------------------------------

def test_new_db_has_result_yield_g_column(tmp_path):
    """AC: fresh database has result_yield_g REAL column."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    assert "result_yield_g" in cols


def test_existing_db_migration_adds_result_yield_g(tmp_path):
    """AC: pre-v0.7 database gets result_yield_g column via migration."""
    import sqlite3
    db_path = tmp_path / "old.db"

    # Create a minimal DB without result_yield_g (simulating pre-v0.7 DB)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE brews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            dose_g REAL NOT NULL,
            water_weight_g REAL NOT NULL,
            result_tds REAL,
            result_ey REAL,
            result_brix REAL,
            result_tasting_notes TEXT
        )
    """)
    conn.commit()
    conn.close()

    # Run get_connection() — should apply migration and add result_yield_g
    conn2 = db_module.get_connection(db_path=db_path)
    cols = {row[1] for row in conn2.execute("PRAGMA table_info(brews)").fetchall()}
    conn2.close()
    assert "result_yield_g" in cols


def test_migration_idempotent(tmp_path):
    """AC: calling get_connection() twice does not error or duplicate column."""
    conn1 = db_module.get_connection(db_path=tmp_path / "test.db")
    conn1.close()
    conn2 = db_module.get_connection(db_path=tmp_path / "test.db")
    cols = [row[1] for row in conn2.execute("PRAGMA table_info(brews)").fetchall()]
    conn2.close()
    # Column should appear exactly once
    assert cols.count("result_yield_g") == 1


# ---------------------------------------------------------------------------
# Import: result.yield_g stored from BrewSpec document
# ---------------------------------------------------------------------------

def test_import_v07_doc_with_yield_stores_result_yield_g(tmp_path):
    """AC: importing a v0.7 document with result.yield_g stores it in DB."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "espresso"
    dose_g: 18.0
    water_weight_g: 36.0
    result:
      yield_g: 36.5
      tds: 9.2
"""
    doc_path = tmp_path / "espresso_yield.yaml"
    doc_path.write_text(yaml_content)

    db_path = tmp_path / "test.db"
    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_mod.get_connection(db_path=db_path)
    rows = db_mod.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["result_yield_g"] == 36.5


def test_import_v07_doc_without_yield_stores_null(tmp_path):
    """AC: importing a v0.7 document without result.yield_g stores NULL."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
    result:
      tds: 1.38
"""
    doc_path = tmp_path / "pour_over.yaml"
    doc_path.write_text(yaml_content)

    db_path = tmp_path / "test.db"
    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_mod.get_connection(db_path=db_path)
    rows = db_mod.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["result_yield_g"] is None


# ---------------------------------------------------------------------------
# Export: result.yield_g included in BrewSpec document
# ---------------------------------------------------------------------------

def test_export_brew_with_yield_includes_yield_g(tmp_path):
    """AC: exporting a row with result_yield_g includes yield_g in result dict."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")

    # Insert a brew with result_yield_g
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, result_yield_g, result_tds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("2026-03-16", "espresso", 18.0, 36.0, 36.5, 9.2))
    conn.commit()

    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    brew_dict = row_to_brew_dict(rows[0])
    assert "result" in brew_dict
    assert brew_dict["result"]["yield_g"] == 36.5


def test_export_brew_without_yield_omits_yield_g(tmp_path):
    """AC: exporting a row with NULL result_yield_g omits yield_g from result."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")

    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, result_tds)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-16", "pour_over", 20.0, 320.0, 1.38))
    conn.commit()

    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    brew_dict = row_to_brew_dict(rows[0])
    assert "result" in brew_dict
    assert "yield_g" not in brew_dict["result"]


def test_export_document_version_is_07(tmp_path):
    """AC: exported document has brewspec_version '0.7'."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES (?, ?, ?, ?)
    """, ("2026-03-16", "pour_over", 20.0, 320.0))
    conn.commit()
    rows = db_module.list_brews(conn, all_rows=True)
    conn.close()

    doc = rows_to_brewspec_document(rows)
    assert doc["brewspec_version"] == "0.7"


# ---------------------------------------------------------------------------
# Round-trip: import then export preserves yield_g
# ---------------------------------------------------------------------------

def test_import_export_roundtrip_with_yield(tmp_path):
    """AC: yield_g survives import → DB → export with same value."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "espresso"
    dose_g: 18.0
    water_weight_g: 36.0
    result:
      yield_g: 36.5
"""
    doc_path = tmp_path / "espresso.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    import brewlog.db as db_mod
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output

    conn = db_mod.get_connection(db_path=db_path)
    rows = db_mod.list_brews(conn, all_rows=True)
    doc = rows_to_brewspec_document(rows)
    conn.close()

    assert doc["brews"][0]["result"]["yield_g"] == 36.5


# ---------------------------------------------------------------------------
# show command: displays Yield when present
# ---------------------------------------------------------------------------

def test_show_brew_with_yield_displays_yield_line(tmp_path):
    """AC: show output contains 'Yield: 36.5g' when result_yield_g is set."""
    db_path = tmp_path / "test.db"
    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, result_yield_g)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-16", "espresso", 18.0, 36.0, 36.5))
    conn.commit()
    rows = db_mod.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "Yield:" in result.output
    assert "36.5g" in result.output


def test_show_brew_without_yield_omits_yield_line(tmp_path):
    """AC: show output contains no 'Yield' line when result_yield_g is NULL."""
    db_path = tmp_path / "test.db"
    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    conn.execute("""
        INSERT INTO brews (date, type, dose_g, water_weight_g, result_tds)
        VALUES (?, ?, ?, ?, ?)
    """, ("2026-03-16", "pour_over", 20.0, 320.0, 1.38))
    conn.commit()
    rows = db_mod.list_brews(conn, all_rows=True)
    brew_id = rows[0]["id"]
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "show", str(brew_id)])
    assert result.exit_code == 0, result.output
    assert "Yield:" not in result.output


# ---------------------------------------------------------------------------
# Import: v0.7 version message updated
# ---------------------------------------------------------------------------

def test_import_v07_file_accepted(tmp_path):
    """AC: importing a file with brewspec_version '0.7' succeeds."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v07.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output
    assert "1 brews added" in result.output


def test_import_v06_file_rejected_with_v07_message(tmp_path):
    """AC: importing a file with brewspec_version '0.6' is rejected with v0.7 error."""
    yaml_content = """
brewspec_version: "0.6"
brews:
  - date: "2026-03-16"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v06.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 1
    assert "0.6" in result.output
    assert "not supported" in result.output.lower() or "v0.7" in result.output


def test_import_exact_v07_rejection_message(tmp_path):
    """AC: v0.6 rejection message is exact and references v0.7."""
    yaml_content = """
brewspec_version: "0.6"
brews:
  - date: "2026-03-16"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 320.0
"""
    doc_path = tmp_path / "v06.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 1
    expected = (
        "Error: This file uses BrewSpec v0.6, which is not supported by BrewLog v0.7.\n"
        "BrewLog v0.7 requires BrewSpec v0.7."
    )
    assert expected in result.output


# ---------------------------------------------------------------------------
# Bundled schema version
# ---------------------------------------------------------------------------

def test_bundled_schema_is_v07():
    """AC: brewlog/src/brewlog/brewspec.schema.json must declare version 0.7."""
    import importlib.resources
    with importlib.resources.files("brewlog").joinpath("brewspec.schema.json").open(
        "r", encoding="utf-8"
    ) as f:
        import json as json_mod
        schema = json_mod.load(f)
    assert schema["properties"]["brewspec_version"]["const"] == "0.7"


# ---------------------------------------------------------------------------
# AC-4: partial v0.7 brew import (no date / type / dose_g / water_weight_g)
# ---------------------------------------------------------------------------

def test_import_minimal_v07_brew_no_required_fields_stores_without_error(tmp_path):
    """AC-4: importing a v0.7 brew with none of the four formerly-required fields
    (date, type, dose_g, water_weight_g) succeeds and stores a row with NULLs."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - notes: "partial brew, no required fields"
"""
    doc_path = tmp_path / "minimal.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert result.exit_code == 0, result.output
    assert "1 brews added" in result.output

    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    rows = db_mod.list_brews(conn, all_rows=True)
    conn.close()

    assert len(rows) == 1
    assert rows[0]["date"] is None
    assert rows[0]["type"] is None
    assert rows[0]["dose_g"] is None
    assert rows[0]["water_weight_g"] is None
    assert rows[0]["notes"] == "partial brew, no required fields"


def test_import_minimal_v07_brew_round_trips(tmp_path):
    """AC-4: partial brew (no date/type/dose_g/water_weight_g) round-trips through
    import → DB → export without error and preserves present fields."""
    yaml_content = """
brewspec_version: "0.7"
brews:
  - notes: "espresso experiment"
    result:
      yield_g: 42.0
"""
    doc_path = tmp_path / "partial.yaml"
    doc_path.write_text(yaml_content)
    db_path = tmp_path / "test.db"

    runner = CliRunner()
    import_result = runner.invoke(cli, ["--db", str(db_path), "import", str(doc_path)])
    assert import_result.exit_code == 0, import_result.output

    import brewlog.db as db_mod
    conn = db_mod.get_connection(db_path=db_path)
    rows = db_mod.list_brews(conn, all_rows=True)
    doc = rows_to_brewspec_document(rows)
    conn.close()

    assert doc["brewspec_version"] == "0.7"
    brew = doc["brews"][0]
    assert brew.get("notes") == "espresso experiment"
    assert brew["result"]["yield_g"] == 42.0
    # These four fields are absent — they should not appear in the export
    assert "date" not in brew
    assert "type" not in brew
    assert "dose_g" not in brew
    assert "water_weight_g" not in brew


def test_existing_db_with_not_null_accepts_partial_brew(tmp_path):
    """AC-4: an existing DB whose brews table has NOT NULL on the four fields
    is migrated (table-rebuild) so that partial brews can be stored."""
    import sqlite3

    db_path = tmp_path / "legacy.db"

    # Simulate a pre-v0.7 database with NOT NULL on the four fields.
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE brews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT    NOT NULL,
            type            TEXT    NOT NULL,
            dose_g          REAL    NOT NULL,
            water_weight_g  REAL    NOT NULL,
            notes           TEXT
        )
    """)
    conn.execute(
        "INSERT INTO brews (date, type, dose_g, water_weight_g, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        ("2026-01-01", "espresso", 18.0, 36.0, "pre-migration brew"),
    )
    conn.commit()
    conn.close()

    # get_connection should detect the NOT NULL constraint and rebuild the table.
    conn2 = db_module.get_connection(db_path=db_path)

    # Existing row should survive the migration.
    rows = db_module.list_brews(conn2, all_rows=True)
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-01-01"
    assert rows[0]["notes"] == "pre-migration brew"

    # Inserting a partial brew (NULL in formerly-required fields) must succeed.
    from brewlog.db import insert_brew_dict
    insert_brew_dict({"notes": "post-migration partial"}, conn2)
    conn2.commit()
    rows2 = db_module.list_brews(conn2, all_rows=True)
    conn2.close()

    partial = next(r for r in rows2 if r["notes"] == "post-migration partial")
    assert partial["date"] is None
    assert partial["type"] is None
    assert partial["dose_g"] is None
    assert partial["water_weight_g"] is None
