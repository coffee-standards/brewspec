"""
CLI integration tests for `brewlog export`.
Tests map to AC-21, AC-22, AC-23, AC-24, AC-25, AC-26, AC-27.
"""

import json
import os
import pytest
import yaml
from pathlib import Path
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module, schema as schema_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput


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
            grind="medium-fine",
            duration_s=180,
            tds=1.38,
            rating=4,
            notes="Bright acidity",
            coffee=CoffeeInput(
                roast_date="2026-01-20",
                type="single_origin",
                origin=["Ethiopia"],
                varietal="Heirloom",
                process="Washed",
            ),
            water=WaterInput(ppm=150.0),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-21: YAML export
# ---------------------------------------------------------------------------

def test_export_yaml_creates_file(runner_with_db, tmp_path):
    """AC-21: file exists at path after export."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    result = runner_with_db.invoke(cli, ["export", out_file])
    assert result.exit_code == 0
    assert Path(out_file).exists()


def test_export_yaml_valid_schema(runner_with_db, tmp_path):
    """AC-21: exported YAML passes validate_document()."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    runner_with_db.invoke(cli, ["export", out_file])
    doc = yaml.safe_load(Path(out_file).read_text())
    errors = schema_module.validate_document(doc)
    assert errors == []


# ---------------------------------------------------------------------------
# AC-22: JSON export
# ---------------------------------------------------------------------------

def test_export_json_creates_file(runner_with_db, tmp_path):
    """AC-22: --format json creates JSON file."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.json")
    result = runner_with_db.invoke(cli, ["export", out_file, "--format", "json"])
    assert result.exit_code == 0
    assert Path(out_file).exists()


def test_export_json_valid_schema(runner_with_db, tmp_path):
    """AC-22: exported JSON passes validate_document()."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.json")
    runner_with_db.invoke(cli, ["export", out_file, "--format", "json"])
    doc = json.loads(Path(out_file).read_text())
    errors = schema_module.validate_document(doc)
    assert errors == []


# ---------------------------------------------------------------------------
# AC-23: Document structure
# ---------------------------------------------------------------------------

def test_export_document_structure(runner_with_db, tmp_path):
    """AC-23: top-level keys: brewspec_version, brews."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    runner_with_db.invoke(cli, ["export", out_file])
    doc = yaml.safe_load(Path(out_file).read_text())
    assert "brewspec_version" in doc
    assert doc["brewspec_version"] == "0.3"
    assert "brews" in doc
    assert isinstance(doc["brews"], list)


# ---------------------------------------------------------------------------
# AC-24: No null values or empty objects
# ---------------------------------------------------------------------------

def _has_null_values(obj) -> bool:
    """Recursively check for None/null values in a dict/list structure."""
    if obj is None:
        return True
    if isinstance(obj, dict):
        return any(_has_null_values(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_null_values(item) for item in obj)
    return False


def _has_empty_objects(obj) -> bool:
    """Recursively check for empty dicts or lists in a dict/list structure."""
    if isinstance(obj, dict):
        if len(obj) == 0:
            return True
        return any(_has_empty_objects(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_empty_objects(item) for item in obj)
    return False


def test_export_no_null_values(runner_with_db, tmp_path):
    """AC-24: no null values in exported YAML."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    runner_with_db.invoke(cli, ["export", out_file])
    doc = yaml.safe_load(Path(out_file).read_text())
    assert not _has_null_values(doc), "Exported YAML must not contain null values"


def test_export_no_empty_objects(runner_with_db, tmp_path):
    """AC-24: empty coffee/water objects absent."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    runner_with_db.invoke(cli, ["export", out_file])
    doc = yaml.safe_load(Path(out_file).read_text())
    brew = doc["brews"][0]
    assert "coffee" not in brew
    assert "water" not in brew


# ---------------------------------------------------------------------------
# AC-25: Empty database
# ---------------------------------------------------------------------------

def test_export_empty_db_exits_clean(runner_with_db, tmp_path):
    """AC-25: No brews to export message, exit 0, no file written."""
    out_file = str(tmp_path / "empty_export.yaml")
    result = runner_with_db.invoke(cli, ["export", out_file])
    assert result.exit_code == 0
    assert "No brews to export" in result.output
    assert not Path(out_file).exists()


# ---------------------------------------------------------------------------
# AC-26: Path validation
# ---------------------------------------------------------------------------

def test_export_path_dotdot_rejected(runner_with_db, tmp_path):
    """AC-26: '../out.yaml' -> error, exit 1."""
    result = runner_with_db.invoke(cli, ["export", "../out.yaml"])
    assert result.exit_code == 1


def test_export_missing_parent_dir(runner_with_db, tmp_path):
    """AC-26: parent dir does not exist -> error, exit 1."""
    out_file = str(tmp_path / "nonexistent_dir" / "out.yaml")
    result = runner_with_db.invoke(cli, ["export", out_file])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-27: Overwrite protection
# ---------------------------------------------------------------------------

def test_export_overwrite_prompts(runner_with_db, tmp_path):
    """AC-27: existing file -> confirmation prompt shown."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    # Create file first
    Path(out_file).write_text("existing content")
    # Invoke without --force; respond 'n' to overwrite prompt
    result = runner_with_db.invoke(cli, ["export", out_file], input="n\n")
    assert result.exit_code == 0
    # Prompt was shown
    assert "already exists" in result.output or "Overwrite" in result.output
    # Content unchanged (rejected overwrite)
    assert Path(out_file).read_text() == "existing content"


def test_export_force_skips_prompt(runner_with_db, tmp_path):
    """AC-27: --force skips overwrite prompt."""
    _insert_minimal(tmp_path / "test.db")
    out_file = str(tmp_path / "export.yaml")
    Path(out_file).write_text("existing content")
    result = runner_with_db.invoke(cli, ["export", out_file, "--force"])
    assert result.exit_code == 0
    # File was overwritten
    assert Path(out_file).read_text() != "existing content"
