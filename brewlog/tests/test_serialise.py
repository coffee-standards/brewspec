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


# ---------------------------------------------------------------------------
# AC-15: SCHEMA_RESOURCE_NAME constant in schema.py
# ---------------------------------------------------------------------------

def test_schema_resource_name_constant_exists():
    """AC-15: SCHEMA_RESOURCE_NAME constant is defined in schema module."""
    from brewlog import schema as schema_module
    assert hasattr(schema_module, "SCHEMA_RESOURCE_NAME")


def test_schema_resource_name_value():
    """AC-15: SCHEMA_RESOURCE_NAME equals 'brewspec.schema.json'."""
    from brewlog import schema as schema_module
    assert schema_module.SCHEMA_RESOURCE_NAME == "brewspec.schema.json"


# ---------------------------------------------------------------------------
# AC-11/AC-12: serialise reads from individual rating columns, not JSON
# ---------------------------------------------------------------------------

def test_row_to_brew_dict_ratings_from_individual_columns(tmp_db):
    """AC-12: ratings serialised from individual result_rating_* columns."""
    brew_dict = {
        **_minimal_dict(),
        "result": {
            "ratings": {
                "overall": 4,
                "fragrance": 3,
                "aroma": 5,
            },
        },
    }
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    assert "result" in result
    assert "ratings" in result["result"]
    assert result["result"]["ratings"]["overall"] == 4
    assert result["result"]["ratings"]["fragrance"] == 3
    assert result["result"]["ratings"]["aroma"] == 5


def test_row_to_brew_dict_ratings_omits_null_dimensions(tmp_db):
    """AC-12: rating dimensions not set are absent from exported ratings dict."""
    brew_dict = {
        **_minimal_dict(),
        "result": {"ratings": {"overall": 4}},
    }
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    ratings = result["result"]["ratings"]
    # Only 'overall' was set; others should be absent
    assert "overall" in ratings
    assert "fragrance" not in ratings
    assert "aroma" not in ratings


def test_row_to_brew_dict_no_ratings_key_when_all_null(tmp_db):
    """AC-12: ratings key absent from result when no rating dimensions set."""
    brew_dict = {**_minimal_dict(), "result": {"tds": 1.38}}
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    # result present (tds set) but ratings absent
    assert "result" in result
    assert "ratings" not in result["result"]


def test_row_to_brew_dict_all_eight_rating_dims(tmp_db):
    """AC-12: all 8 SCA dimensions round-trip correctly."""
    brew_dict = {
        **_minimal_dict(),
        "result": {
            "ratings": {
                "overall": 4,
                "fragrance": 3,
                "aroma": 5,
                "flavour": 4,
                "aftertaste": 3,
                "acidity": 5,
                "sweetness": 4,
                "mouthfeel": 3,
            }
        },
    }
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    ratings = result["result"]["ratings"]
    assert ratings["overall"] == 4
    assert ratings["fragrance"] == 3
    assert ratings["aroma"] == 5
    assert ratings["flavour"] == 4
    assert ratings["aftertaste"] == 3
    assert ratings["acidity"] == 5
    assert ratings["sweetness"] == 4
    assert ratings["mouthfeel"] == 3


# ---------------------------------------------------------------------------
# AC-11: GRIND_ENUM constant and invalid grind sentinel
# ---------------------------------------------------------------------------

def test_grind_enum_constant_exists():
    """AC-11: GRIND_ENUM constant defined in serialise module."""
    assert hasattr(serialise, "GRIND_ENUM")


def test_grind_enum_has_seven_values():
    """AC-11: GRIND_ENUM has exactly 7 values."""
    assert len(serialise.GRIND_ENUM) == 7


def test_grind_enum_contains_all_values():
    """AC-11: GRIND_ENUM contains all 7 v0.4 enum members."""
    expected = {"turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"}
    assert serialise.GRIND_ENUM == expected


def test_row_to_brew_dict_valid_grind_included(tmp_db):
    """AC-11: valid enum grind value included in output."""
    brew_dict = {**_minimal_dict(), "grind": "medium_fine"}
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    assert result.get("grind") == "medium_fine"


def test_row_to_brew_dict_invalid_grind_omitted(tmp_db):
    """AC-11: freeform grind not in enum is omitted from main output."""
    # Directly insert a row with a non-enum grind value via raw SQL
    tmp_db.execute(
        "INSERT INTO brews (date, type, dose_g, water_weight_g, grind) "
        "VALUES (?, ?, ?, ?, ?)",
        ("2026-02-19T08:30:00Z", "pour_over", 18.0, 280.0, "setting 15"),
    )
    tmp_db.commit()
    row = tmp_db.execute("SELECT * FROM brews ORDER BY id DESC LIMIT 1").fetchone()
    result = serialise.row_to_brew_dict(row)
    # grind should not be in main output
    assert "grind" not in result


def test_row_to_brew_dict_invalid_grind_sentinel_set(tmp_db):
    """AC-11: _invalid_grind sentinel key set when grind is non-enum."""
    tmp_db.execute(
        "INSERT INTO brews (date, type, dose_g, water_weight_g, grind) "
        "VALUES (?, ?, ?, ?, ?)",
        ("2026-02-19T08:30:00Z", "pour_over", 18.0, 280.0, "medium-fine"),
    )
    tmp_db.commit()
    row = tmp_db.execute("SELECT * FROM brews ORDER BY id DESC LIMIT 1").fetchone()
    result = serialise.row_to_brew_dict(row)
    assert "_invalid_grind" in result
    assert result["_invalid_grind"] == "medium-fine"


def test_row_to_brew_dict_valid_grind_no_sentinel(tmp_db):
    """AC-11: no _invalid_grind sentinel when grind is valid enum member."""
    brew_dict = {**_minimal_dict(), "grind": "coarse"}
    row = _make_row(tmp_db, brew_dict)
    result = serialise.row_to_brew_dict(row)
    assert "_invalid_grind" not in result
