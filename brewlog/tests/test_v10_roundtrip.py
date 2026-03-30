"""
Round-trip tests for BrewLog CLI v1.0.

Tests cover acceptance criteria:
AC-47: export from full v1.0 DB passes v1.0 schema validation
AC-48: export from minimal pre-v1.0 DB passes v1.0 schema validation
AC-57: import → export → validate round-trip preserves all v1.0 fields
AC-64: import a valid v1.0 BrewSpec file, export, assert passes schema validation

TDD: tests written before implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from brewlog import db as db_module, schema as schema_module
from brewlog.cli import cli
from brewlog.models import (
    BrewInput, CoffeeInput, OriginInput, EquipmentInput, ResultInput
)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _insert_brew(db_path, brew: BrewInput) -> int:
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-47: export from full v1.0 DB passes schema validation
# ---------------------------------------------------------------------------

class TestExportFullV10PassesSchema:
    """AC-47: export with all v1.0 fields passes v1.0 JSON Schema validation."""

    def test_export_full_v10_passes_schema(self, runner, db_path, tmp_path):
        """Insert a brew using all new v1.0 fields, export, validate against schema."""
        brew = BrewInput(
            date="2026-03-30",
            type="espresso",
            dose_g=18.0,
            water_g=36.0,
            yield_g=36.0,
            process_notes="Pre-infused 5s at 3 bar",
            coffee=CoffeeInput(
                name="Colombia Huila",
                cupping_notes="Dark chocolate, citrus",
                origins=[
                    OriginInput(
                        country="Colombia",
                        region="Huila",
                        cupping_notes="Bright malic acidity",
                    )
                ],
            ),
            equipment=EquipmentInput(
                grinder="Niche Zero",
                pressure_bar=9.0,
                flow_rate_ml_s=1.3,
            ),
            result=ResultInput(
                yield_g=36.5,
                water_g=35.5,
                tds=9.1,
            ),
        )
        _insert_brew(db_path, brew)

        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0

        doc = yaml.safe_load(Path(export_file).read_text())
        errors = schema_module.validate_document(doc)
        assert errors == [], f"Schema validation errors: {errors}"


# ---------------------------------------------------------------------------
# AC-48: export from minimal pre-v1.0 brew passes schema validation
# ---------------------------------------------------------------------------

class TestExportMinimalPassesSchema:
    """AC-48: export from minimal brew (no new fields) passes v1.0 schema validation."""

    def test_export_minimal_passes_schema(self, runner, db_path, tmp_path):
        """Minimal brew (date, type, dose_g, water_g only) export passes schema."""
        brew = BrewInput(
            date="2026-03-30",
            type="pour_over",
            dose_g=18.0,
            water_g=280.0,
        )
        _insert_brew(db_path, brew)

        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0

        doc = yaml.safe_load(Path(export_file).read_text())
        errors = schema_module.validate_document(doc)
        assert errors == [], f"Schema validation errors: {errors}"


# ---------------------------------------------------------------------------
# AC-57: import → export → validate round-trip (all v1.0 fields)
# ---------------------------------------------------------------------------

class TestV10RoundTrip:
    """AC-57: full round-trip with all v1.0 fields preserved."""

    def test_v10_import_export_roundtrip(self, tmp_path, monkeypatch):
        """Import a v1.0 YAML file, export, validate, assert field values preserved."""
        # Construct a v1.0 BrewSpec document with all new fields
        v10_doc = {
            "brewspec_version": "1.0",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_g": 36.0,
                    "yield_g": 36.0,
                    "process_notes": "Pre-infused 5s",
                    "coffee": {
                        "name": "Colombia Huila",
                        "cupping_notes": "Dark chocolate, citrus",
                        "origins": [
                            {
                                "country": "Colombia",
                                "cupping_notes": "Bright malic acidity",
                            }
                        ],
                    },
                    "equipment": {
                        "grinder": "Niche Zero",
                        "pressure_bar": 9.0,
                        "flow_rate_ml_s": 1.3,
                    },
                    "result": {
                        "yield_g": 36.5,
                        "water_g": 35.5,
                        "tds": 9.1,
                    },
                }
            ],
        }

        import_file = tmp_path / "v10_import.yaml"
        import_file.write_text(yaml.dump(v10_doc))

        src_db = tmp_path / "source.db"
        monkeypatch.setattr(db_module, "DB_PATH", src_db)
        runner = CliRunner()

        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0, result.output

        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0, result.output

        doc = yaml.safe_load(Path(export_file).read_text())
        errors = schema_module.validate_document(doc)
        assert errors == [], f"Schema validation errors: {errors}"

        # Verify field values preserved
        brew = doc["brews"][0]
        assert brew["water_g"] == 36.0
        assert brew["yield_g"] == 36.0
        assert brew["process_notes"] == "Pre-infused 5s"
        assert brew["coffee"]["cupping_notes"] == "Dark chocolate, citrus"
        assert brew["coffee"]["origins"][0]["cupping_notes"] == "Bright malic acidity"
        assert brew["equipment"]["pressure_bar"] == 9.0
        assert brew["equipment"]["flow_rate_ml_s"] == 1.3
        assert brew["result"]["water_g"] == 35.5


# ---------------------------------------------------------------------------
# AC-64: import a valid v1.0 BrewSpec file, export, validate schema
# ---------------------------------------------------------------------------

class TestImportV10ThenExportValidatesSchema:
    """AC-64: import valid v1.0 file, export, assert passes v1.0 schema."""

    def test_import_v10_export_passes_schema(self, tmp_path, monkeypatch):
        """Standard import→export round-trip validates against v1.0 schema."""
        v10_doc = {
            "brewspec_version": "1.0",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_g": 36.0,
                }
            ],
        }

        import_file = tmp_path / "v10.yaml"
        import_file.write_text(yaml.dump(v10_doc))

        db_path = tmp_path / "test.db"
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        runner = CliRunner()

        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0, result.output

        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0, result.output

        doc = yaml.safe_load(Path(export_file).read_text())
        errors = schema_module.validate_document(doc)
        assert errors == [], f"Schema validation errors: {errors}"

    def test_import_v09_document_rejected(self, tmp_path, monkeypatch):
        """AC-49: v0.9 document (water_weight_g) fails v1.0 schema validation and is rejected."""
        v09_doc = {
            "brewspec_version": "0.9",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_weight_g": 36.0,  # old field — rejected in v1.0
                }
            ],
        }

        import_file = tmp_path / "v09.yaml"
        import_file.write_text(yaml.dump(v09_doc))

        db_path = tmp_path / "test.db"
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        runner = CliRunner()

        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1, f"v0.9 document should be rejected: {result.output}"
