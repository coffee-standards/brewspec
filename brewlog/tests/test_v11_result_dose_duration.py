"""
Tests for BrewSpec v1.0 result.dose_g and result.duration_s fields.

Covers:
- DB migration: result_dose_g and result_duration_s columns exist after migration
- Pydantic model: dose_g and duration_s are optional float fields on BrewResult (ResultInput)
- CLI add: --actual-dose and --actual-duration flags accepted and stored correctly
- CLI update: same flags accepted and stored correctly
- Export: fields appear in YAML output when set
- Import: fields round-trip correctly

TDD: tests written before implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import ResultInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_column_names(db_path: Path) -> set[str]:
    """Return the set of column names in the brews table."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    return cols


def _get_row(db_path: Path, brew_id: int = 1):
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.get_brew(brew_id, conn)
    finally:
        conn.close()


def _add_minimal(runner, db_path=None, **extra_flags):
    """Invoke add with minimal required flags plus any extras."""
    flags = [
        "add",
        "--date", "2026-03-30",
        "--type", "espresso",
        "--dose", "18.0",
        "--water", "36.0",
    ]
    for k, v in extra_flags.items():
        flags.extend([k, str(v)])
    if db_path is not None:
        return runner.invoke(cli, ["--db", str(db_path)] + flags[1:])
    return runner.invoke(cli, flags)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


@pytest.fixture
def runner_with_path(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner(), db_path


# ---------------------------------------------------------------------------
# DB migration: new columns exist after migration
# ---------------------------------------------------------------------------

class TestV11MigrationColumns:
    """New columns result_dose_g and result_duration_s exist after migration."""

    def test_result_dose_g_column_exists_on_fresh_db(self, tmp_path):
        """Fresh DB has result_dose_g column."""
        db_path = tmp_path / "fresh.db"
        conn = db_module.get_connection(db_path=db_path)
        conn.close()
        cols = _get_column_names(db_path)
        assert "result_dose_g" in cols, "result_dose_g column must be present after migration"

    def test_result_duration_s_column_exists_on_fresh_db(self, tmp_path):
        """Fresh DB has result_duration_s column."""
        db_path = tmp_path / "fresh.db"
        conn = db_module.get_connection(db_path=db_path)
        conn.close()
        cols = _get_column_names(db_path)
        assert "result_duration_s" in cols, "result_duration_s column must be present after migration"

    def test_new_columns_null_by_default(self, tmp_path):
        """Pre-existing rows have NULL for new columns after migration."""
        import sqlite3
        db_path = tmp_path / "old.db"
        # Create a DB that looks like a pre-v11 database (no result_dose_g / result_duration_s)
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE brews (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                date                      TEXT,
                type                      TEXT,
                method                    TEXT,
                dose_g                    REAL,
                water_g                   REAL,
                brew_ratio                REAL,
                water_volume_ml           REAL,
                water_temp_c              REAL,
                grind                     TEXT,
                duration_s                INTEGER,
                process_notes             TEXT,
                coffee_roast_date         TEXT,
                coffee_type               TEXT,
                coffee_name               TEXT,
                coffee_origins            TEXT,
                coffee_origin             TEXT,
                coffee_varietal           TEXT,
                coffee_process            TEXT,
                water_ppm                 REAL,
                equipment_grinder         TEXT,
                equipment_brewer          TEXT,
                equipment_grinder_setting REAL,
                equipment_notes           TEXT,
                result_tds                REAL,
                result_ey                 REAL,
                result_brix               REAL,
                result_yield_g            REAL,
                result_tasting_notes      TEXT,
                result_ratings            TEXT,
                result_rating_overall     INTEGER,
                result_rating_fragrance   INTEGER,
                result_rating_aroma       INTEGER,
                result_rating_flavour     INTEGER,
                result_rating_aftertaste  INTEGER,
                result_rating_acidity     INTEGER,
                result_rating_sweetness   INTEGER,
                result_rating_mouthfeel   INTEGER,
                coffee_roaster            TEXT,
                coffee_roast_level        TEXT,
                yield_g                   REAL,
                result_water_g            REAL,
                coffee_cupping_notes      TEXT,
                equipment_pressure_bar    REAL,
                equipment_flow_rate_ml_s  REAL
            )
        """)
        conn.execute(
            "INSERT INTO brews (date, type, dose_g, water_g) VALUES (?, ?, ?, ?)",
            ("2026-01-15", "espresso", 18.0, 36.0),
        )
        conn.commit()
        conn.close()

        # Run migration
        conn2 = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn2)
            assert row["result_dose_g"] is None
            assert row["result_duration_s"] is None
        finally:
            conn2.close()

    def test_migration_idempotent(self, tmp_path):
        """Calling get_connection twice on a migrated DB raises no error."""
        db_path = tmp_path / "idem.db"
        conn1 = db_module.get_connection(db_path=db_path)
        conn1.close()
        conn2 = db_module.get_connection(db_path=db_path)
        conn2.close()


# ---------------------------------------------------------------------------
# Pydantic model: dose_g and duration_s on ResultInput
# ---------------------------------------------------------------------------

class TestResultInputModel:
    """ResultInput has optional dose_g and duration_s float fields."""

    def test_result_input_dose_g_accepted(self):
        """ResultInput accepts dose_g as a positive float."""
        r = ResultInput(dose_g=18.5)
        assert r.dose_g == 18.5

    def test_result_input_duration_s_accepted(self):
        """ResultInput accepts duration_s as a positive float."""
        r = ResultInput(duration_s=25.0)
        assert r.duration_s == 25.0

    def test_result_input_both_fields_accepted(self):
        """ResultInput accepts both dose_g and duration_s together."""
        r = ResultInput(dose_g=18.0, duration_s=30.0)
        assert r.dose_g == 18.0
        assert r.duration_s == 30.0

    def test_result_input_dose_g_defaults_to_none(self):
        """dose_g defaults to None when not provided."""
        r = ResultInput()
        assert r.dose_g is None

    def test_result_input_duration_s_defaults_to_none(self):
        """duration_s defaults to None when not provided."""
        r = ResultInput()
        assert r.duration_s is None

    def test_result_input_dose_g_zero_rejected(self):
        """dose_g of 0 is rejected (exclusiveMinimum: 0)."""
        import pytest as _pytest
        from pydantic import ValidationError
        with _pytest.raises(ValidationError):
            ResultInput(dose_g=0)

    def test_result_input_dose_g_negative_rejected(self):
        """Negative dose_g is rejected."""
        import pytest as _pytest
        from pydantic import ValidationError
        with _pytest.raises(ValidationError):
            ResultInput(dose_g=-1.0)

    def test_result_input_duration_s_zero_rejected(self):
        """duration_s of 0 is rejected (exclusiveMinimum: 0)."""
        import pytest as _pytest
        from pydantic import ValidationError
        with _pytest.raises(ValidationError):
            ResultInput(duration_s=0)

    def test_result_input_duration_s_negative_rejected(self):
        """Negative duration_s is rejected."""
        import pytest as _pytest
        from pydantic import ValidationError
        with _pytest.raises(ValidationError):
            ResultInput(duration_s=-5.0)


# ---------------------------------------------------------------------------
# CLI add: --actual-dose and --actual-duration flags
# ---------------------------------------------------------------------------

class TestAddActualDose:
    """--actual-dose flag stores result_dose_g in DB."""

    def test_add_actual_dose_stored(self, runner_with_path):
        """--actual-dose 17.5 writes to result_dose_g column."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-dose", "17.5",
        ])
        assert result.exit_code == 0, result.output
        row = _get_row(db_path)
        assert row["result_dose_g"] == 17.5

    def test_add_actual_dose_zero_rejected(self, runner):
        """--actual-dose 0 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-dose", "0",
        ])
        assert result.exit_code == 1

    def test_add_actual_dose_negative_rejected(self, runner):
        """--actual-dose -1 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-dose", "-1",
        ])
        assert result.exit_code == 1

    def test_add_actual_dose_not_provided_is_null(self, runner_with_path):
        """When --actual-dose is omitted, result_dose_g is NULL."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["result_dose_g"] is None


class TestAddActualDuration:
    """--actual-duration flag stores result_duration_s in DB."""

    def test_add_actual_duration_stored(self, runner_with_path):
        """--actual-duration 28.0 writes to result_duration_s column."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-duration", "28.0",
        ])
        assert result.exit_code == 0, result.output
        row = _get_row(db_path)
        assert row["result_duration_s"] == 28.0

    def test_add_actual_duration_zero_rejected(self, runner):
        """--actual-duration 0 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-duration", "0",
        ])
        assert result.exit_code == 1

    def test_add_actual_duration_negative_rejected(self, runner):
        """--actual-duration -5 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-duration", "-5",
        ])
        assert result.exit_code == 1

    def test_add_actual_duration_not_provided_is_null(self, runner_with_path):
        """When --actual-duration is omitted, result_duration_s is NULL."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["result_duration_s"] is None


# ---------------------------------------------------------------------------
# CLI update: --actual-dose and --actual-duration flags
# ---------------------------------------------------------------------------

class TestUpdateActualDose:
    """--actual-dose flag on update stores result_dose_g in DB."""

    def test_update_actual_dose_stored(self, runner_with_path):
        """--actual-dose 17.5 on update writes to result_dose_g column."""
        runner, db_path = runner_with_path
        # Add a brew first
        add_result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        assert add_result.exit_code == 0
        # Now update it
        result = runner.invoke(cli, [
            "update", "1", "--actual-dose", "17.5",
        ])
        assert result.exit_code == 0, result.output
        row = _get_row(db_path)
        assert row["result_dose_g"] == 17.5

    def test_update_actual_dose_zero_rejected(self, runner_with_path):
        """--actual-dose 0 on update is rejected."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        result = runner.invoke(cli, ["update", "1", "--actual-dose", "0"])
        assert result.exit_code == 1

    def test_update_actual_dose_negative_rejected(self, runner_with_path):
        """--actual-dose -1 on update is rejected."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        result = runner.invoke(cli, ["update", "1", "--actual-dose", "-1"])
        assert result.exit_code == 1


class TestUpdateActualDuration:
    """--actual-duration flag on update stores result_duration_s in DB."""

    def test_update_actual_duration_stored(self, runner_with_path):
        """--actual-duration 30 on update writes to result_duration_s column."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        result = runner.invoke(cli, ["update", "1", "--actual-duration", "30"])
        assert result.exit_code == 0, result.output
        row = _get_row(db_path)
        assert row["result_duration_s"] == 30.0

    def test_update_actual_duration_zero_rejected(self, runner_with_path):
        """--actual-duration 0 on update is rejected."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        result = runner.invoke(cli, ["update", "1", "--actual-duration", "0"])
        assert result.exit_code == 1

    def test_update_actual_duration_negative_rejected(self, runner_with_path):
        """--actual-duration -3 on update is rejected."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        result = runner.invoke(cli, ["update", "1", "--actual-duration", "-3"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Export: fields appear in YAML output when set
# ---------------------------------------------------------------------------

class TestExportResultDoseDuration:
    """result.dose_g and result.duration_s appear in export when set."""

    def test_export_includes_result_dose_g(self, runner_with_path, tmp_path):
        """When result_dose_g is set, it appears as result.dose_g in YAML export."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-dose", "17.5",
        ])
        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0, result.output

        doc = yaml.safe_load(Path(export_file).read_text())
        brew = doc["brews"][0]
        assert "result" in brew
        assert brew["result"]["dose_g"] == 17.5

    def test_export_includes_result_duration_s(self, runner_with_path, tmp_path):
        """When result_duration_s is set, it appears as result.duration_s in YAML export."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-duration", "28.0",
        ])
        export_file = str(tmp_path / "export.yaml")
        result = runner.invoke(cli, ["export", export_file])
        assert result.exit_code == 0, result.output

        doc = yaml.safe_load(Path(export_file).read_text())
        brew = doc["brews"][0]
        assert "result" in brew
        assert brew["result"]["duration_s"] == 28.0

    def test_export_omits_result_dose_g_when_null(self, runner_with_path, tmp_path):
        """result.dose_g is absent from export when not set."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        export_file = str(tmp_path / "export.yaml")
        runner.invoke(cli, ["export", export_file])

        doc = yaml.safe_load(Path(export_file).read_text())
        brew = doc["brews"][0]
        result_block = brew.get("result", {})
        assert "dose_g" not in result_block

    def test_export_omits_result_duration_s_when_null(self, runner_with_path, tmp_path):
        """result.duration_s is absent from export when not set."""
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
        ])
        export_file = str(tmp_path / "export.yaml")
        runner.invoke(cli, ["export", export_file])

        doc = yaml.safe_load(Path(export_file).read_text())
        brew = doc["brews"][0]
        result_block = brew.get("result", {})
        assert "duration_s" not in result_block

    def test_export_schema_valid_with_result_dose_duration(self, runner_with_path, tmp_path):
        """Export with result.dose_g and result.duration_s passes schema validation."""
        from brewlog import schema as schema_module
        runner, db_path = runner_with_path
        runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-dose", "17.5",
            "--actual-duration", "28.0",
        ])
        export_file = str(tmp_path / "export.yaml")
        runner.invoke(cli, ["export", export_file])

        doc = yaml.safe_load(Path(export_file).read_text())
        errors = schema_module.validate_document(doc)
        assert errors == [], f"Schema validation errors: {errors}"


# ---------------------------------------------------------------------------
# Import: fields round-trip correctly
# ---------------------------------------------------------------------------

class TestImportResultDoseDuration:
    """result.dose_g and result.duration_s round-trip through import."""

    def test_import_result_dose_g_roundtrip(self, tmp_path, monkeypatch):
        """Import a file with result.dose_g, export, assert value preserved."""
        v10_doc = {
            "brewspec_version": "1.0",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_g": 36.0,
                    "result": {
                        "dose_g": 17.5,
                    },
                }
            ],
        }

        import_file = tmp_path / "v10_dose.yaml"
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
        brew = doc["brews"][0]
        assert brew["result"]["dose_g"] == 17.5

    def test_import_result_duration_s_roundtrip(self, tmp_path, monkeypatch):
        """Import a file with result.duration_s, export, assert value preserved."""
        v10_doc = {
            "brewspec_version": "1.0",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_g": 36.0,
                    "result": {
                        "duration_s": 28.5,
                    },
                }
            ],
        }

        import_file = tmp_path / "v10_duration.yaml"
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
        brew = doc["brews"][0]
        assert brew["result"]["duration_s"] == 28.5

    def test_import_both_fields_roundtrip(self, tmp_path, monkeypatch):
        """Import a file with both result.dose_g and result.duration_s, export, assert both preserved."""
        v10_doc = {
            "brewspec_version": "1.0",
            "brews": [
                {
                    "date": "2026-03-30",
                    "type": "espresso",
                    "dose_g": 18.0,
                    "water_g": 36.0,
                    "result": {
                        "dose_g": 17.5,
                        "duration_s": 28.5,
                    },
                }
            ],
        }

        import_file = tmp_path / "v10_both.yaml"
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
        brew = doc["brews"][0]
        assert brew["result"]["dose_g"] == 17.5
        assert brew["result"]["duration_s"] == 28.5
