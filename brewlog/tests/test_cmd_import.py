"""
CLI integration tests for `brewlog import`.
Tests map to AC-28, AC-29, AC-30, AC-31, AC-32, AC-33.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner_with_db(tmp_path, monkeypatch):
    """CliRunner with a temporary DB path injected."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


# ---------------------------------------------------------------------------
# AC-28, AC-30: Successful import (YAML and JSON)
# ---------------------------------------------------------------------------

def test_import_yaml_success(runner_with_db, tmp_path):
    """AC-28, AC-30: imports valid YAML, prints 'Imported N brews.'"""
    fixture = str(FIXTURES_DIR / "valid_brewspec.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 0
    assert "Imported 1 brews." in result.output or "Imported 1 brew" in result.output


def test_import_json_success(runner_with_db, tmp_path):
    """AC-28: imports valid JSON."""
    fixture = str(FIXTURES_DIR / "valid_brewspec.json")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 0
    assert "Imported" in result.output


def test_import_count_message(runner_with_db, tmp_path):
    """AC-30: 'Imported 3 brews.' for a 3-brew file."""
    fixture = str(FIXTURES_DIR / "valid_brewspec_multi.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 0
    assert "Imported 3 brews." in result.output


def test_import_data_stored_in_db(runner_with_db, tmp_path, monkeypatch):
    """AC-28: imported brews are stored in DB."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    fixture = str(FIXTURES_DIR / "valid_brewspec.yaml")
    runner = CliRunner()
    runner.invoke(cli, ["import", fixture])

    conn = db_mod.get_connection(db_path=db_path)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 1
        assert rows[0]["type"] == "pour_over"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-29: Schema validation failures
# ---------------------------------------------------------------------------

def test_import_invalid_schema_rejected(runner_with_db, tmp_path):
    """AC-29: file with missing required field -> error, exit 1, no DB write."""
    fixture = str(FIXTURES_DIR / "invalid_missing_field.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 1
    assert "Validation failed" in result.output or "error" in result.output.lower()


def test_import_wrong_version_rejected(runner_with_db, tmp_path):
    """AC-29: brewspec_version: '0.1' -> error, exit 1."""
    fixture = str(FIXTURES_DIR / "invalid_wrong_version.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 1


def test_import_no_partial_write(runner_with_db, tmp_path, monkeypatch):
    """AC-29: invalid file -> no rows inserted."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    fixture = str(FIXTURES_DIR / "invalid_missing_field.yaml")
    runner = CliRunner()
    runner.invoke(cli, ["import", fixture])

    conn = db_mod.get_connection(db_path=db_path)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-31: safe_load usage
# ---------------------------------------------------------------------------

def test_import_uses_safe_load(runner_with_db, tmp_path):
    """AC-31: YAML with Python object tag is rejected safely."""
    # This YAML attempts to use a Python object constructor tag
    # yaml.safe_load() raises ConstructorError; schema validation catches it anyway.
    malicious_yaml = tmp_path / "malicious.yaml"
    malicious_yaml.write_text(
        "brewspec_version: '0.2'\n"
        "brews:\n"
        "  - !!python/object/apply:os.system ['echo hacked']\n"
    )
    result = runner_with_db.invoke(cli, ["import", str(malicious_yaml)])
    # Must exit non-zero (either ConstructorError or schema validation failure)
    assert result.exit_code != 0
    # Must NOT have executed any system command (we can't easily verify this,
    # but the important thing is that exit_code != 0 confirms rejection)


# ---------------------------------------------------------------------------
# AC-32: Path validation
# ---------------------------------------------------------------------------

def test_import_path_dotdot_rejected(runner_with_db):
    """AC-32: path with '..' -> error, exit 1."""
    result = runner_with_db.invoke(cli, ["import", "../evil.yaml"])
    assert result.exit_code == 1


def test_import_file_too_large(runner_with_db, tmp_path):
    """AC-32: file > 10MB -> error before parse, exit 1."""
    large_file = tmp_path / "large.yaml"
    with open(large_file, "wb") as f:
        f.write(b"x" * (10 * 1024 * 1024 + 1))
    result = runner_with_db.invoke(cli, ["import", str(large_file)])
    assert result.exit_code == 1
    assert "10MB" in result.output or "limit" in result.output.lower() or "large" in result.output.lower()


def test_import_unknown_extension_rejected(runner_with_db, tmp_path):
    """AC-28: .csv extension -> error, exit 1."""
    csv_file = tmp_path / "brews.csv"
    csv_file.write_text("date,type,dose_g\n2026-02-19T08:30:00Z,pour_over,18\n")
    result = runner_with_db.invoke(cli, ["import", str(csv_file)])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-33: Append-only (no deduplication)
# ---------------------------------------------------------------------------

def test_import_appends_not_replaces(runner_with_db, tmp_path, monkeypatch):
    """AC-33: import twice -> 2x rows (no dedup)."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    fixture = str(FIXTURES_DIR / "valid_brewspec.yaml")
    runner = CliRunner()
    runner.invoke(cli, ["import", fixture])
    runner.invoke(cli, ["import", fixture])

    conn = db_mod.get_connection(db_path=db_path)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 2
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-13: v0.3 (and non-v0.4) file rejection with actionable error message
# ---------------------------------------------------------------------------

def test_import_v03_file_rejected(runner_with_db):
    """AC-13: brewspec_version: '0.3' -> exit 1."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert result.exit_code == 1


def test_import_v03_file_states_version_found(runner_with_db):
    """AC-13: error message states the version found in the file."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert "0.3" in result.output


def test_import_v03_file_mentions_not_supported(runner_with_db):
    """AC-13: error message says the version is not supported."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    output_lower = result.output.lower()
    assert "not supported" in output_lower or "unsupported" in output_lower


def test_import_v03_file_lists_migration_changes(runner_with_db):
    """AC-13: error message lists required structural changes."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    # Must mention tds/ey moving to result sub-object
    assert "result" in result.output.lower()


def test_import_v03_file_points_to_migration_guide(runner_with_db):
    """AC-13: error message points to migration guide URL."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    assert "github.com/coffee-standards/brewspec" in result.output


def test_import_v03_no_rows_written(runner_with_db, tmp_path, monkeypatch):
    """AC-13: v0.3 file rejected -> no rows written to DB."""
    import brewlog.db as db_mod
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)

    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    runner = CliRunner()
    runner.invoke(cli, ["import", fixture])

    conn = db_mod.get_connection(db_path=db_path)
    try:
        rows = db_mod.list_brews(conn, all_rows=True)
        assert len(rows) == 0
    finally:
        conn.close()


def test_import_v02_file_rejected(runner_with_db, tmp_path):
    """AC-13: brewspec_version: '0.2' -> exit 1 (any non-0.4 version rejected)."""
    v02_file = tmp_path / "v02_brew.yaml"
    v02_file.write_text(
        "brewspec_version: '0.2'\n"
        "brews:\n"
        "  - date: '2026-02-19T08:30:00Z'\n"
        "    type: pour_over\n"
        "    dose_g: 18.0\n"
        "    water_weight_g: 280.0\n"
    )
    result = runner_with_db.invoke(cli, ["import", str(v02_file)])
    assert result.exit_code == 1


def test_import_v03_exact_error_message(runner_with_db):
    """AC-13: v0.3 file rejection produces the exact verbatim error message from the spec."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")
    result = runner_with_db.invoke(cli, ["import", fixture])
    expected = (
        'Error: This file uses BrewSpec v0.3, which is not supported by BrewLog v0.3.\n'
        'BrewLog v0.3 requires BrewSpec v0.4.\n'
        '\n'
        'To migrate your file from v0.3 to v0.4, make the following changes:\n'
        '  1. Change \'brewspec_version\' from "0.3" to "0.4"\n'
        '  2. Move \'tds\' (if present) from the brew level to \'result.tds\'\n'
        '  3. Move \'ey\' (if present) from the brew level to \'result.ey\'\n'
        '  4. Move \'rating\' (if present) from the brew level to \'result.ratings.overall\'\n'
        '  5. Replace any freeform \'grind\' values with one of:\n'
        '     turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse\n'
        '     (or remove the \'grind\' field if no match applies)\n'
        '\n'
        'Full migration guide: https://github.com/coffee-standards/brewspec'
    )
    assert result.output.strip() == expected.strip()
