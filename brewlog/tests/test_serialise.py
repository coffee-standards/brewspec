"""
Unit tests for serialisation/deserialisation in brewlog.serialise.
Tests map to AC-24 (null omission), Section 6.1 (row_to_brew_dict),
and security path validation (AC-26, AC-32).
"""

import pytest

from brewlog import db as db_module
from brewlog import serialise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(tmp_db, brew_dict: dict):
    """Insert a brew_dict and return the raw sqlite3.Row."""
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    return db_module.get_brew(brew_id, tmp_db)


def _minimal_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
    }


def _full_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
        "method": "Hario V60",
        "water_temp_c": 96.0,
        "grind": "medium_fine",
        "duration_s": 180,
        "notes": "Bright acidity",
        "coffee": {
            "roast_date": "2026-01-20",
            "type": "single_origin",
            "origin": ["Ethiopia"],
            "varietal": "Heirloom",
            "process": "Washed",
        },
        "water": {"ppm": 150.0},
        "result": {
            "tds": 1.38,
            "ey": 20.5,
        },
    }


# ---------------------------------------------------------------------------
# row_to_brew_dict
# ---------------------------------------------------------------------------

def test_row_to_brew_dict_minimal(tmp_db):
    """AC-24: required fields present; no null values in output."""
    row = _make_row(tmp_db, _minimal_dict())
    result = serialise.row_to_brew_dict(row)
    assert result["date"] == "2026-02-19T08:30:00Z"
    assert result["type"] == "pour_over"
    assert result["dose_g"] == 18.0
    assert result["water_weight_g"] == 280.0


def test_row_to_brew_dict_no_nulls(tmp_db):
    """AC-24: NULL columns absent from output dict entirely."""
    row = _make_row(tmp_db, _minimal_dict())
    result = serialise.row_to_brew_dict(row)
    # No key should have a None value
    for key, value in result.items():
        assert value is not None, f"Field '{key}' should be absent, not None"
    # Optional fields should not be present at all
    assert "method" not in result
    assert "grind" not in result
    assert "notes" not in result
    assert "water_temp_c" not in result
    assert "coffee" not in result
    assert "water" not in result


def test_row_to_brew_dict_coffee_object_included(tmp_db):
    """Section 6.1: coffee dict included when at least one field set."""
    row = _make_row(tmp_db, _full_dict())
    result = serialise.row_to_brew_dict(row)
    assert "coffee" in result
    assert result["coffee"]["type"] == "single_origin"


def test_row_to_brew_dict_coffee_object_omitted(tmp_db):
    """AC-24: coffee dict absent when all coffee fields NULL."""
    row = _make_row(tmp_db, _minimal_dict())
    result = serialise.row_to_brew_dict(row)
    assert "coffee" not in result


def test_row_to_brew_dict_water_object_included(tmp_db):
    """Section 6.1: water dict included when ppm set."""
    row = _make_row(tmp_db, _full_dict())
    result = serialise.row_to_brew_dict(row)
    assert "water" in result
    assert result["water"]["ppm"] == 150.0


def test_row_to_brew_dict_water_object_omitted(tmp_db):
    """AC-24: water dict absent when ppm NULL."""
    row = _make_row(tmp_db, _minimal_dict())
    result = serialise.row_to_brew_dict(row)
    assert "water" not in result


def test_row_to_brew_dict_result_object_included(tmp_db):
    """Section 6.1: result dict included when tds set."""
    row = _make_row(tmp_db, _full_dict())
    result = serialise.row_to_brew_dict(row)
    assert "result" in result
    assert result["result"]["tds"] == 1.38
    assert result["result"]["ey"] == 20.5


def test_row_to_brew_dict_result_object_omitted(tmp_db):
    """AC-24: result dict absent when all result fields NULL."""
    row = _make_row(tmp_db, _minimal_dict())
    result = serialise.row_to_brew_dict(row)
    assert "result" not in result


def test_row_to_brew_dict_origin_deserialised(tmp_db):
    """Section 6.1: JSON string '["Ethiopia"]' becomes ["Ethiopia"]."""
    brew_dict = {**_minimal_dict(), "coffee": {"origin": ["Ethiopia"]}}
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    assert result["coffee"]["origin"] == ["Ethiopia"]
    assert isinstance(result["coffee"]["origin"], list)


def test_row_to_brew_dict_origin_multi(tmp_db):
    """AC-8: multi-origin blend round-trips correctly."""
    brew_dict = {**_minimal_dict(), "coffee": {"origin": ["Ethiopia", "Colombia"]}}
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    assert result["coffee"]["origin"] == ["Ethiopia", "Colombia"]


# ---------------------------------------------------------------------------
# rows_to_brewspec_document
# ---------------------------------------------------------------------------

def test_rows_to_brewspec_document_structure(tmp_db):
    """AC-23: top-level keys are 'brewspec_version' and 'brews'."""
    db_module.insert_brew_dict(_minimal_dict(), tmp_db)
    tmp_db.commit()
    rows = db_module.get_all_brews(tmp_db)
    doc = serialise.rows_to_brewspec_document(rows)
    assert "brewspec_version" in doc
    assert doc["brewspec_version"] == "0.4"
    assert "brews" in doc
    assert isinstance(doc["brews"], list)
    assert len(doc["brews"]) == 1


def test_rows_to_brewspec_document_multiple_rows(tmp_db):
    """rows_to_brewspec_document returns all rows."""
    for i in range(3):
        d = _minimal_dict()
        d["date"] = f"2026-02-{i + 1:02d}T08:30:00Z"
        db_module.insert_brew_dict(d, tmp_db)
    tmp_db.commit()
    rows = db_module.get_all_brews(tmp_db)
    doc = serialise.rows_to_brewspec_document(rows)
    assert len(doc["brews"]) == 3


# ---------------------------------------------------------------------------
# validate_export_path
# ---------------------------------------------------------------------------

def test_validate_export_path_rejects_dotdot(tmp_path):
    """AC-26: '../evil' rejected."""
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_export_path("../evil.yaml")
    assert exc_info.value.code == 1


def test_validate_export_path_rejects_embedded_dotdot(tmp_path):
    """AC-26: 'foo/../bar' rejected."""
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_export_path("foo/../bar.yaml")
    assert exc_info.value.code == 1


def test_validate_export_path_rejects_missing_parent(tmp_path):
    """AC-26: parent dir does not exist -> error."""
    nonexistent = str(tmp_path / "nonexistent_dir" / "out.yaml")
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_export_path(nonexistent)
    assert exc_info.value.code == 1


def test_validate_export_path_accepts_valid(tmp_path):
    """validate_export_path accepts a valid path in an existing directory."""
    valid_path = str(tmp_path / "out.yaml")
    result = serialise.validate_export_path(valid_path)
    assert result is not None


# ---------------------------------------------------------------------------
# validate_import_path
# ---------------------------------------------------------------------------

def test_validate_import_path_rejects_dotdot(tmp_path):
    """AC-32: '../evil.yaml' rejected."""
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_import_path("../evil.yaml")
    assert exc_info.value.code == 1


def test_validate_import_path_rejects_missing_file(tmp_path):
    """AC-28: non-existent path rejected."""
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_import_path(str(tmp_path / "nonexistent.yaml"))
    assert exc_info.value.code == 1


def test_validate_import_path_rejects_oversized(tmp_path):
    """AC-32: file > 10MB rejected before parse."""
    large_file = tmp_path / "large.yaml"
    # Write just over 10MB
    with open(large_file, "wb") as f:
        f.write(b"x" * (10 * 1024 * 1024 + 1))
    with pytest.raises(SystemExit) as exc_info:
        serialise.validate_import_path(str(large_file))
    assert exc_info.value.code == 1


def test_validate_import_path_accepts_valid(tmp_path):
    """validate_import_path accepts a valid existing file."""
    valid_file = tmp_path / "test.yaml"
    valid_file.write_text("brewspec_version: '0.4'\n")
    result = serialise.validate_import_path(str(valid_file))
    assert result is not None
