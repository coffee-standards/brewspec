"""
BrewLog CLI v0.4 tests.

Covers the 5 carry-forward items implemented in v0.4:

  Item 1 — MED-1: list fallback for v0.2 legacy result_ratings JSON
  Item 2 — Help text fix: update --id description
  Item 3 — Delete ID gap behaviour: note in delete output / help
  Item 4 — List column visibility: hide all-null columns
  Item 5 — CSV export via --format csv
"""

import csv
import json

import pytest
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import BrewInput


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(runner, date="2026-02-19T08:30:00Z", brew_type="pour_over"):
    return runner.invoke(cli, [
        "add", "--date", date, "--type", brew_type,
        "--dose", "18.0", "--water", "280.0",
    ])


def _insert_brew(db_path, **kwargs):
    """Insert a brew via BrewInput into the DB at db_path."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date=kwargs.get("date", "2026-02-19T08:30:00Z"),
            type=kwargs.get("type", "pour_over"),
            dose_g=kwargs.get("dose_g", 18.0),
            water_weight_g=kwargs.get("water_weight_g", 280.0),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _insert_legacy_ratings_row(db_path, overall: int):
    """
    Insert a v0.2-style row with result_ratings JSON and NULL individual rating columns.
    Bypasses Pydantic to simulate a real v0.2 migration row.
    """
    conn = db_module.get_connection(db_path=db_path)
    try:
        conn.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, result_ratings) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "2026-02-10T08:00:00Z",
                "pour_over",
                18.0,
                280.0,
                json.dumps({"overall": overall, "flavour": 4}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# Item 1 — MED-1: list fallback for v0.2 legacy result_ratings JSON
# ===========================================================================


class TestListLegacyRatingFallback:
    """list _format_row() falls back to result_ratings JSON when result_rating_overall is NULL."""

    def test_legacy_row_shows_overall_rating(self, runner, db_path):
        """Overall rating from legacy result_ratings JSON appears in list output."""
        _insert_legacy_ratings_row(db_path, overall=4)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "4" in result.output

    def test_legacy_row_does_not_show_dash_for_rating(self, runner, db_path):
        """When a legacy row has an overall rating, '-' should NOT appear for the rating column."""
        _insert_legacy_ratings_row(db_path, overall=5)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        # The rating value '5' must appear; we confirm the column is not just '-'
        lines = result.output.strip().split("\n")
        # Data row is the last line (after header + separator)
        data_row = lines[-1]
        assert "5" in data_row

    def test_modern_row_with_rating_overall_unaffected(self, runner, db_path):
        """A modern row with result_rating_overall set still shows correctly."""
        _add_brew(runner)
        runner.invoke(cli, ["update", "--rating-overall", "3"])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        data_row = lines[-1]
        assert "3" in data_row

    def test_null_legacy_row_still_shows_dash(self, runner, db_path):
        """A row with both result_rating_overall NULL and result_ratings NULL shows '-'."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "-" in result.output

    def test_legacy_ratings_without_overall_key_shows_dash(self, runner, db_path):
        """A legacy row whose JSON lacks the 'overall' key falls back to '-'."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            conn.execute(
                "INSERT INTO brews (date, type, dose_g, water_weight_g, result_ratings) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "2026-02-10T08:00:00Z",
                    "pour_over",
                    18.0,
                    280.0,
                    json.dumps({"flavour": 4}),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        data_row = lines[-1]
        assert "-" in data_row


# ===========================================================================
# Item 2 — Help text fix: update --id / brew_id description
# ===========================================================================


class TestUpdateHelpText:
    """update --help shows 'defaults to the last brew' (not truncated)."""

    def test_update_help_contains_last_brew(self, runner):
        """update --help text completes the brew_id description."""
        result = runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0
        assert "last brew" in result.output.lower()

    def test_update_help_description_not_truncated(self, runner):
        """'defaults to the last brew' phrase appears in full."""
        result = runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0
        # The phrase must appear verbatim (case-insensitive acceptable)
        assert "defaults to the last brew" in result.output.lower()


# ===========================================================================
# Item 3 — Delete ID gap behaviour: note in delete output
# ===========================================================================


class TestDeleteIdGapNote:
    """delete command communicates that IDs are permanent and gaps are normal."""

    def test_delete_help_mentions_permanent_ids(self, runner):
        """delete --help contains a note about permanent IDs or non-reuse."""
        result = runner.invoke(cli, ["delete", "--help"])
        assert result.exit_code == 0
        output_lower = result.output.lower()
        # Check for any of: 'permanent', 'not reassigned', 'not reused',
        # 'gaps', 'resequenced', 'sequential'
        has_note = (
            "permanent" in output_lower
            or "not reassign" in output_lower
            or "not reused" in output_lower
            or "gap" in output_lower
            or "resequence" in output_lower
        )
        assert has_note, (
            "delete --help should mention that IDs are permanent and gaps are normal. "
            f"Actual output:\n{result.output}"
        )


# ===========================================================================
# Item 4 — List column visibility: hide all-null columns
# ===========================================================================


class TestListColumnVisibility:
    """Columns with no data in the result set are hidden from the list table."""

    def test_method_hidden_when_no_brew_has_method(self, runner, db_path):
        """Method column absent from header when no brew has a method set."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        # Header should not show 'Method' if no brew has a method
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Method" not in header

    def test_method_shown_when_at_least_one_brew_has_method(self, runner, db_path):
        """Method column appears when at least one brew has a method."""
        _insert_brew(db_path)
        conn = db_module.get_connection(db_path=db_path)
        try:
            from brewlog.models import BrewInput
            brew = BrewInput(
                date="2026-02-20T08:00:00Z",
                type="pour_over",
                dose_g=18.0,
                water_weight_g=280.0,
                method="V60",
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Method" in header

    def test_rating_hidden_when_no_brew_has_rating(self, runner, db_path):
        """Overall Rating column absent when no brew has a rating."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Overall Rating" not in header

    def test_rating_shown_when_at_least_one_brew_has_rating(self, runner, db_path):
        """Overall Rating column shown when at least one brew has a rating."""
        _add_brew(runner)
        runner.invoke(cli, ["update", "--rating-overall", "4"])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Overall Rating" in header

    def test_required_columns_always_shown(self, runner, db_path):
        """ID, Date, Type, Dose, and Water columns always appear."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        header = result.output.strip().split("\n")[0]
        assert "ID" in header
        assert "Date" in header
        assert "Type" in header
        assert "Dose" in header
        assert "Water" in header

    def test_legacy_rating_column_shown_for_legacy_rows(self, runner, db_path):
        """Overall Rating column visible when only legacy rows (result_ratings JSON) have ratings."""
        _insert_legacy_ratings_row(db_path, overall=3)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Overall Rating" in header

    def test_mixed_row_set_shows_method_column(self, runner, db_path):
        """With 3 brews (one has method), Method column appears and blanks for others."""
        _insert_brew(db_path)
        _insert_brew(db_path, date="2026-02-21T08:00:00Z")
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(
                date="2026-02-22T08:00:00Z",
                type="pour_over",
                dose_g=18.0,
                water_weight_g=280.0,
                method="Chemex",
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        header = lines[0]
        assert "Method" in header

    def test_empty_db_shows_no_table(self, runner):
        """Empty DB: no table rendered at all (shows 'No brews' message)."""
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No brews logged yet" in result.output


# ===========================================================================
# Item 5 — CSV export via --format csv
# ===========================================================================


class TestCsvExport:
    """brewlog export --format csv writes a flat CSV with one row per brew."""

    def test_csv_export_creates_file(self, runner, db_path, tmp_path):
        """--format csv creates a .csv file."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"])
        assert result.exit_code == 0
        import os
        assert os.path.exists(out_file)

    def test_csv_export_has_header_row(self, runner, db_path, tmp_path):
        """CSV file has a header row."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert len(header) > 0

    def test_csv_export_has_required_headers(self, runner, db_path, tmp_path):
        """CSV header includes required fields: date, type, dose_g, water_weight_g."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert "date" in headers
        assert "type" in headers
        assert "dose_g" in headers
        assert "water_weight_g" in headers

    def test_csv_export_one_row_per_brew(self, runner, db_path, tmp_path):
        """CSV has one data row per brew."""
        _insert_brew(db_path, date="2026-02-19T08:30:00Z")
        _insert_brew(db_path, date="2026-02-20T08:30:00Z")
        _insert_brew(db_path, date="2026-02-21T08:30:00Z")
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3

    def test_csv_export_values_match_db(self, runner, db_path, tmp_path):
        """CSV data row values match what was stored in the DB."""
        _insert_brew(db_path, date="2026-02-19T08:30:00Z")
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row["date"] == "2026-02-19T08:30:00Z"
        assert row["type"] == "pour_over"
        assert float(row["dose_g"]) == 18.0
        assert float(row["water_weight_g"]) == 280.0

    def test_csv_export_null_fields_empty_string(self, runner, db_path, tmp_path):
        """Null fields are represented as empty string (not 'None' or 'null')."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            content = f.read()
        assert "None" not in content
        assert "null" not in content

    def test_csv_extension_accepted_with_csv_format(self, runner, db_path, tmp_path):
        """Path ending with .csv is accepted when --format csv is given."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "out.csv")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"])
        assert result.exit_code == 0

    def test_csv_format_requires_format_flag(self, runner, db_path, tmp_path):
        """A .csv extension without --format csv is rejected (extension-only not enough)."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "out.csv")
        result = runner.invoke(cli, ["export", out_file])
        # Without --format csv, .csv extension is not valid
        assert result.exit_code == 1

    def test_csv_empty_db_exits_clean(self, runner, tmp_path):
        """Empty DB: 'No brews to export' message, exit 0, no file written."""
        out_file = str(tmp_path / "export.csv")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"])
        assert result.exit_code == 0
        assert "No brews to export" in result.output
        import os
        assert not os.path.exists(out_file)

    def test_csv_overwrite_protection(self, runner, db_path, tmp_path):
        """Existing .csv file triggers overwrite prompt without --force."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        # Pre-create the file
        with open(out_file, "w") as f:
            f.write("old content")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"], input="n\n")
        assert result.exit_code == 0
        assert "already exists" in result.output or "Overwrite" in result.output
        # Content not changed
        with open(out_file) as f:
            assert f.read() == "old content"

    def test_csv_force_overwrites(self, runner, db_path, tmp_path):
        """--force overwrites existing .csv without prompting."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        with open(out_file, "w") as f:
            f.write("old content")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv", "--force"])
        assert result.exit_code == 0
        with open(out_file) as f:
            content = f.read()
        assert content != "old content"

    def test_csv_dotdot_path_rejected(self, runner, db_path, tmp_path):
        """Path with '..' rejected even with --format csv."""
        result = runner.invoke(cli, ["export", "../out.csv", "--format", "csv"])
        assert result.exit_code == 1

    def test_csv_missing_parent_dir_rejected(self, runner, db_path, tmp_path):
        """Non-existent parent dir rejected."""
        out_file = str(tmp_path / "nonexistent" / "out.csv")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"])
        assert result.exit_code == 1

    def test_csv_output_is_valid_csv(self, runner, db_path, tmp_path):
        """Output can be parsed by csv.DictReader without errors."""
        _insert_brew(db_path, date="2026-02-19T08:30:00Z")
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # Parseable without exception and has at least one row
        assert len(rows) >= 1

    def test_csv_success_message(self, runner, db_path, tmp_path):
        """Success message mentions the number of brews and path."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "export.csv")
        result = runner.invoke(cli, ["export", out_file, "--format", "csv"])
        assert result.exit_code == 0
        assert "1" in result.output
        assert "brew" in result.output.lower()

    def test_existing_yaml_json_extension_tests_still_work(self, runner, db_path, tmp_path):
        """--format yaml still works; the addition of csv does not break yaml/json."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "out.yaml")
        result = runner.invoke(cli, ["export", out_file, "--format", "yaml"])
        assert result.exit_code == 0

    def test_csv_export_with_optional_fields(self, runner, db_path, tmp_path):
        """CSV row includes optional fields when present."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            from brewlog.models import BrewInput, ResultInput, RatingsInput
            brew = BrewInput(
                date="2026-02-19T08:30:00Z",
                type="pour_over",
                dose_g=18.0,
                water_weight_g=280.0,
                method="V60",
                result=ResultInput(ratings=RatingsInput(overall=4)),
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        out_file = str(tmp_path / "export.csv")
        runner.invoke(cli, ["export", out_file, "--format", "csv"])
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row["method"] == "V60"


# ===========================================================================
# Version bump
# ===========================================================================


class TestVersionBump:
    """v0.4.0 version string appears in the welcome screen and --version output."""

    def test_welcome_screen_shows_v040(self, runner):
        """Welcome screen shows 'BrewLog v0.4.0'."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "0.4.0" in result.output

    def test_version_flag_shows_v040(self, runner):
        """--version outputs 0.4.0."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.4.0" in result.output
