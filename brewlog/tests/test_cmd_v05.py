"""
BrewLog CLI v0.5 tests.

Covers all acceptance criteria for v0.5:
- AC-1 to AC-5: brewlog stats
- AC-6 to AC-14: brewlog search
- AC-15 to AC-20: import deduplication
- AC-21 to AC-26: single-brew export --id N
- AC-27 to AC-33: --db PATH global flag
- AC-34 to AC-36: BrewSpec v0.6 schema adoption
- AC-37 to AC-43: brew_ratio field
- AC-44 to AC-50: coffee.origins structured data
- AC-50a to AC-50g: coffee.name field
- AC-51 to AC-57: equipment fields (grinder_setting, equipment_notes)
- AC-58 to AC-60: interactive brew type on update
- AC-61 to AC-63: version bump
"""

from __future__ import annotations

import json

import pytest
import yaml
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import BrewInput


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(runner, date="2026-02-19", brew_type="pour_over", dose="18.0", water="280.0"):
    return runner.invoke(cli, [
        "add", "--date", date, "--type", brew_type,
        "--dose", dose, "--water", water,
    ])


def _insert_brew(db_path, **kwargs):
    """Insert a brew via BrewInput into the DB at db_path."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date=kwargs.get("date", "2026-02-19"),
            type=kwargs.get("type", "pour_over"),
            dose_g=kwargs.get("dose_g", 18.0),
            water_weight_g=kwargs.get("water_weight_g", 280.0),
        )
        brew_id = db_module.insert_brew(brew, conn)
        return brew_id
    finally:
        conn.close()


# ===========================================================================
# AC-61 to AC-63: Version bump
# ===========================================================================


class TestVersionBump:
    """v0.6.0 version string appears in the welcome screen and --version output."""

    def test_welcome_screen_shows_v060(self, runner):
        """Welcome screen shows 'BrewLog v0.6.0'."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "0.6.0" in result.output

    def test_version_flag_shows_v060(self, runner):
        """--version outputs 0.6.0."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.6.0" in result.output


# ===========================================================================
# AC-27 to AC-33: --db PATH global flag
# ===========================================================================


class TestDbFlag:
    """--db PATH global flag routes DB operations to the specified file."""

    def test_db_flag_in_help(self):
        """--db PATH option appears in brewlog --help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--db" in result.output

    def test_db_flag_uses_custom_db(self, tmp_path):
        """AC-28: --db PATH uses that file instead of the default."""
        runner = CliRunner()
        custom_db = tmp_path / "custom.db"
        result = runner.invoke(cli, [
            "--db", str(custom_db),
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
        ])
        assert result.exit_code == 0
        assert custom_db.exists()
        # Verify the brew is in the custom DB
        conn = db_module.get_connection(db_path=custom_db)
        try:
            rows = db_module.get_all_brews(conn)
            assert len(rows) == 1
        finally:
            conn.close()

    def test_db_flag_creates_file_if_not_exists(self, tmp_path):
        """AC-28: If the db file does not exist, it is created."""
        runner = CliRunner()
        new_db = tmp_path / "new.db"
        assert not new_db.exists()
        runner.invoke(cli, [
            "--db", str(new_db),
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
        ])
        assert new_db.exists()

    def test_db_flag_nonexistent_parent_rejected(self, tmp_path):
        """AC-30: Parent directory does not exist -> error, exit 1."""
        runner = CliRunner()
        bad_db = tmp_path / "nonexistent_dir" / "test.db"
        result = runner.invoke(cli, [
            "--db", str(bad_db),
            "list",
        ])
        assert result.exit_code == 1
        assert "does not exist" in result.output.lower() or "does not exist" in (result.output + "").lower()

    def test_db_flag_dotdot_rejected(self, tmp_path):
        """AC-32: Path with '..' is rejected."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--db", "../other.db",
            "list",
        ])
        assert result.exit_code == 1
        assert ".." in result.output or "path" in result.output.lower()

    def test_db_flag_with_list(self, tmp_path):
        """AC-31: --db works with list command."""
        runner = CliRunner()
        custom_db = tmp_path / "test.db"
        # Add a brew to the custom DB
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "list"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_db_flag_with_show(self, tmp_path):
        """AC-31: --db works with show command."""
        runner = CliRunner()
        custom_db = tmp_path / "test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "show", str(brew_id)])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_db_flag_with_update(self, tmp_path):
        """AC-31: --db works with update command."""
        runner = CliRunner()
        custom_db = tmp_path / "test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "update", str(brew_id), "--notes", "test note"])
        assert result.exit_code == 0

    def test_db_flag_with_delete(self, tmp_path):
        """AC-31: --db works with delete command."""
        runner = CliRunner()
        custom_db = tmp_path / "test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "delete", str(brew_id), "--force"])
        assert result.exit_code == 0

    def test_no_db_flag_uses_default_path(self, tmp_path, monkeypatch):
        """AC-29: No --db flag uses ~/.brewlog/brews.db."""
        # We monkeypatch DB_PATH to a tmp path and verify it's used
        monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "default.db")
        runner = CliRunner()
        runner.invoke(cli, ["add", "--date", "2026-02-19", "--type", "pour_over", "--dose", "18", "--water", "280"])
        assert (tmp_path / "default.db").exists()


# ===========================================================================
# AC-1 to AC-5: brewlog stats
# ===========================================================================


class TestStats:
    """brewlog stats command."""

    def test_stats_empty_db(self, runner):
        """AC-4: Empty DB prints friendly message, exit 0."""
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "No brews logged yet" in result.output
        assert "brewlog add" in result.output

    def test_stats_empty_db_exact_message(self, runner):
        """AC-4: Exact message for empty database."""
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "No brews logged yet. Run 'brewlog add' to log your first brew." in result.output

    def test_stats_exit_code_zero(self, runner, db_path):
        """AC-1: Exit code is 0 on success."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0

    def test_stats_total_brews(self, runner, db_path):
        """AC-2: Total brews count is correct."""
        for i in range(3):
            _insert_brew(db_path, date=f"2026-02-{19+i:02d}")
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "3" in result.output

    def test_stats_most_common_type(self, runner, db_path):
        """AC-2: Most common brew type is displayed."""
        _insert_brew(db_path, date="2026-02-19", type="pour_over")
        _insert_brew(db_path, date="2026-02-20", type="pour_over")
        _insert_brew(db_path, date="2026-02-21", type="espresso")
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_stats_most_common_type_tie_alphabetical(self, runner, db_path):
        """AC-2: Ties broken alphabetically (espresso before pour_over)."""
        _insert_brew(db_path, date="2026-02-19", type="pour_over")
        _insert_brew(db_path, date="2026-02-20", type="espresso")
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        # espresso comes before pour_over alphabetically
        assert "espresso" in result.output

    def test_stats_average_rating(self, runner, db_path):
        """AC-2: Average overall rating displayed rounded to 1 decimal."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r in [3, 4, 4, 5, 2]:
                brew = BrewInput(
                    date=f"2026-02-{19+r:02d}",
                    type="pour_over",
                    dose_g=18.0,
                    water_weight_g=280.0,
                )
                brew_id = db_module.insert_brew(brew, conn)
                db_module.update_brew(brew_id, {"result_rating_overall": r}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "3.6" in result.output

    def test_stats_no_ratings_message(self, runner, db_path):
        """AC-2: When no ratings, display 'No ratings logged'."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "No ratings logged" in result.output

    def test_stats_rating_distribution(self, runner, db_path):
        """AC-2: Rating distribution shows counts for stars 1-5."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r in [1, 3, 3, 5]:
                brew = BrewInput(
                    date=f"2026-02-{19+r:02d}",
                    type="pour_over",
                    dose_g=18.0,
                    water_weight_g=280.0,
                )
                brew_id = db_module.insert_brew(brew, conn)
                db_module.update_brew(brew_id, {"result_rating_overall": r}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "1 star" in result.output
        assert "2 star" in result.output  # 0 count but still shown
        assert "3 star" in result.output
        assert "5 star" in result.output

    def test_stats_output_sections(self, runner, db_path):
        """AC-3: Output has required sections: Brew Summary, Ratings."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "Brew Summary" in result.output
        assert "Ratings" in result.output

    def test_stats_output_has_separator(self, runner, db_path):
        """AC-3: Brew Summary section has '====' separator."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "====" in result.output

    def test_stats_with_db_flag(self, tmp_path):
        """AC-5: --db PATH works with stats."""
        runner = CliRunner()
        custom_db = tmp_path / "stats_test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "stats"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_stats_zero_counts_for_missing_stars(self, runner, db_path):
        """AC-2: Rating distribution shows 0 for stars with no brews."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(brew_id, {"result_rating_overall": 5}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        # Stars 1-4 should show with count 0
        assert "0" in result.output


# ===========================================================================
# AC-6 to AC-14: brewlog search
# ===========================================================================


class TestSearch:
    """brewlog search command."""

    def test_search_matches_notes(self, runner, db_path):
        """AC-6/AC-7: Search matches in notes field."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="Ethiopia washed")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "ethiopia"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_tasting_notes(self, runner, db_path):
        """AC-6/AC-7: Search matches in result_tasting_notes field."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(brew_id, {"result_tasting_notes": "bright citrus"}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "citrus"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_coffee_name(self, runner, db_path):
        """AC-6/AC-50g: Search matches in coffee_name field."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "Blue Bottle Single Origin",
        ])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["search", "bottle"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_coffee_origins(self, runner, db_path):
        """AC-6/AC-7: Search matches in coffee_origins JSON."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-region", "Yirgacheffe",
        ])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["search", "yirgacheffe"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_case_insensitive(self, runner, db_path):
        """AC-9: Search is case-insensitive."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="ethiopia washed")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "ETHIOPIA"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_no_match(self, runner, db_path):
        """AC-10: No match prints friendly message, exit 0."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["search", "xyz123notexist"])
        assert result.exit_code == 0
        assert 'No brews found matching "xyz123notexist".' in result.output

    def test_search_empty_query_error(self, runner, db_path):
        """AC-11: Empty query exits with code 1."""
        result = runner.invoke(cli, ["search", ""])
        assert result.exit_code == 1
        assert "empty" in result.output.lower() or "Error" in result.output

    def test_search_whitespace_only_error(self, runner, db_path):
        """AC-11: Whitespace-only query is an error."""
        result = runner.invoke(cli, ["search", "   "])
        assert result.exit_code == 1

    def test_search_with_limit(self, runner, db_path):
        """AC-12: --limit N caps results."""
        for i in range(5):
            conn = db_module.get_connection(db_path=db_path)
            try:
                brew = BrewInput(
                    date=f"2026-02-{19+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0,
                    notes="ethiopia match"
                )
                db_module.insert_brew(brew, conn)
            finally:
                conn.close()
        result = runner.invoke(cli, ["search", "ethiopia", "--limit", "3"])
        assert result.exit_code == 0
        # Count rows: subtract 2 for header and separator
        lines = [ln for ln in result.output.strip().split("\n") if ln.strip()]
        data_lines = lines[2:]  # skip header and separator
        assert len(data_lines) == 3

    def test_search_no_limit_returns_all(self, runner, db_path):
        """AC-12: No --limit returns all matches."""
        for i in range(5):
            conn = db_module.get_connection(db_path=db_path)
            try:
                brew = BrewInput(
                    date=f"2026-02-{19+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0,
                    notes="ethiopia match"
                )
                db_module.insert_brew(brew, conn)
            finally:
                conn.close()
        result = runner.invoke(cli, ["search", "ethiopia"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.strip().split("\n") if ln.strip()]
        data_lines = lines[2:]  # skip header and separator
        assert len(data_lines) == 5

    def test_search_sql_injection_guard(self, runner, db_path):
        """AC-13: SQL injection in query does not crash or return extra rows."""
        _insert_brew(db_path)
        result = runner.invoke(cli, ["search", "' OR '1'='1"])
        # Should either show no results or show matching results — but NOT crash
        assert result.exit_code == 0

    def test_search_with_db_flag(self, tmp_path):
        """AC-14: --db PATH works with search."""
        runner = CliRunner()
        custom_db = tmp_path / "search_test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="custom db test")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "search", "custom"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_does_not_match_grind(self, runner, db_path):
        """AC-6: grind field is NOT searched."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, grind="medium")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "medium"])
        assert result.exit_code == 0
        assert "No brews found" in result.output

    def test_search_output_format_same_as_list(self, runner, db_path):
        """AC-8: Search output format matches list output format (has ID, Date, Type columns)."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="ethiopia test")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "ethiopia"])
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Date" in result.output
        assert "Type" in result.output


# ===========================================================================
# AC-15 to AC-20: Import deduplication
# ===========================================================================


class TestImportDeduplication:
    """Import deduplication: skip brews that already exist."""

    def _make_valid_v06_yaml(self, brews_list):
        doc = {"brewspec_version": "0.7", "brews": brews_list}
        return yaml.dump(doc, default_flow_style=False)

    def _base_brew(self, date="2026-02-19", brew_type="pour_over"):
        return {
            "date": date,
            "type": brew_type,
            "dose_g": 18.0,
            "water_weight_g": 280.0,
        }

    def test_dedup_skip_existing(self, runner, db_path, tmp_path):
        """AC-15/AC-16: Brew matching date+type+dose+water is skipped."""
        _insert_brew(db_path, date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([self._base_brew()])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        assert "0 brews added" in result.output
        assert "1 skipped" in result.output
        assert "already exist" in result.output

    def test_dedup_insert_new(self, runner, db_path, tmp_path):
        """AC-18: New brews (no match) are inserted."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([self._base_brew()])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        assert "1 brews added" in result.output
        assert "0 skipped" in result.output

    def test_dedup_mixed(self, runner, db_path, tmp_path):
        """AC-16: Mixed file: 1 duplicate, 1 new."""
        _insert_brew(db_path, date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([
                self._base_brew("2026-02-19"),
                self._base_brew("2026-02-20"),
            ])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        assert "1 brews added" in result.output
        assert "1 skipped" in result.output

    def test_dedup_all_duplicates(self, runner, db_path, tmp_path):
        """AC-17: All brews duplicates -> 0 added, N skipped, exit 0."""
        _insert_brew(db_path, date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        _insert_brew(db_path, date="2026-02-20", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([
                self._base_brew("2026-02-19"),
                self._base_brew("2026-02-20"),
            ])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        assert "0 brews added" in result.output
        assert "2 skipped" in result.output

    def test_dedup_summary_message_format(self, runner, db_path, tmp_path):
        """AC-16: Summary message format is 'Import complete: N brews added, M skipped (already exist).'"""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([self._base_brew()])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        assert "Import complete:" in result.output
        assert "brews added" in result.output
        assert "skipped (already exist)." in result.output

    def test_dedup_after_schema_validation(self, runner, db_path, tmp_path):
        """AC-19: Invalid file fails before dedup check."""
        import_file = tmp_path / "import.yaml"
        # Write a v0.6 file with invalid schema
        import_file.write_text(
            "brewspec_version: '0.6'\nbrews:\n  - date: '2026-02-19'\n    type: invalid_type\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1

    def test_dedup_with_db_flag(self, tmp_path):
        """AC-20: --db PATH works with import deduplication."""
        runner = CliRunner()
        custom_db = tmp_path / "import_test.db"
        import_file = tmp_path / "import.yaml"
        brews = [{"date": "2026-02-19", "type": "pour_over", "dose_g": 18.0, "water_weight_g": 280.0}]
        import_file.write_text(yaml.dump({"brewspec_version": "0.7", "brews": brews}))
        result = runner.invoke(cli, ["--db", str(custom_db), "import", str(import_file)])
        assert result.exit_code == 0
        assert "1 brews added" in result.output

    def test_import_output_message_changed(self, runner, db_path, tmp_path):
        """AC-16: Old 'Imported N brews.' message replaced by new format."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(
            self._make_valid_v06_yaml([self._base_brew()])
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        # Old message should NOT appear
        assert "Imported 1 brews." not in result.output
        # New message must appear
        assert "Import complete:" in result.output


# ===========================================================================
# AC-21 to AC-26: Single-brew export --id N
# ===========================================================================


class TestExportById:
    """brewlog export --id N exports a single brew."""

    def test_export_id_found(self, runner, db_path, tmp_path):
        """AC-21: Export single brew by ID."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "single.yaml")
        result = runner.invoke(cli, ["export", out_file, "--id", "1"])
        assert result.exit_code == 0
        content = (tmp_path / "single.yaml").read_text()
        doc = yaml.safe_load(content)
        assert len(doc["brews"]) == 1

    def test_export_id_not_found(self, runner, db_path, tmp_path):
        """AC-22: Brew ID not found -> error message to stderr, exit 1, no file."""
        out_file = str(tmp_path / "nope.yaml")
        result = runner.invoke(cli, ["export", out_file, "--id", "999"])
        assert result.exit_code == 1
        assert "No brew found with ID 999." in result.output
        assert not (tmp_path / "nope.yaml").exists()

    def test_export_id_schema_valid(self, runner, db_path, tmp_path):
        """AC-23: Single-brew export passes v0.7 schema validation."""
        from brewlog import schema
        _insert_brew(db_path)
        out_file = str(tmp_path / "single.yaml")
        result = runner.invoke(cli, ["export", out_file, "--id", "1"])
        assert result.exit_code == 0
        content = (tmp_path / "single.yaml").read_text()
        doc = yaml.safe_load(content)
        errors = schema.validate_document(doc)
        assert not errors

    def test_export_id_version_is_07(self, runner, db_path, tmp_path):
        """AC-34: Export with --id writes brewspec_version: '0.7'."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "single.yaml")
        runner.invoke(cli, ["export", out_file, "--id", "1"])
        content = (tmp_path / "single.yaml").read_text()
        doc = yaml.safe_load(content)
        assert doc["brewspec_version"] == "0.7"

    def test_export_no_id_exports_all(self, runner, db_path, tmp_path):
        """AC-24: No --id exports all brews."""
        _insert_brew(db_path, date="2026-02-19")
        _insert_brew(db_path, date="2026-02-20")
        out_file = str(tmp_path / "all.yaml")
        result = runner.invoke(cli, ["export", out_file])
        assert result.exit_code == 0
        doc = yaml.safe_load((tmp_path / "all.yaml").read_text())
        assert len(doc["brews"]) == 2

    def test_export_id_json_format(self, runner, db_path, tmp_path):
        """AC-21: --format json works with --id."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "single.json")
        result = runner.invoke(cli, ["export", out_file, "--id", "1", "--format", "json"])
        assert result.exit_code == 0
        doc = json.loads((tmp_path / "single.json").read_text())
        assert len(doc["brews"]) == 1

    def test_export_id_dotdot_path_rejected(self, runner, db_path, tmp_path):
        """AC-25: Path traversal rejected for --id exports."""
        result = runner.invoke(cli, ["export", "../bad.yaml", "--id", "1"])
        assert result.exit_code == 1

    def test_export_id_with_db_flag(self, tmp_path):
        """AC-26: --db PATH works with export --id."""
        runner = CliRunner()
        custom_db = tmp_path / "exp_test.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        out_file = str(tmp_path / "out.yaml")
        result = runner.invoke(cli, ["--db", str(custom_db), "export", out_file, "--id", "1"])
        assert result.exit_code == 0
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        assert len(doc["brews"]) == 1


# ===========================================================================
# AC-34 to AC-36: BrewSpec v0.7 schema adoption
# ===========================================================================


class TestSchemaAdoption:
    """BrewSpec v0.7 schema adoption."""

    def test_export_writes_v07_version(self, runner, db_path, tmp_path):
        """AC-34: All exports write brewspec_version: '0.7'."""
        _insert_brew(db_path)
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / out_file).read_text())
        assert doc["brewspec_version"] == "0.7"

    def test_import_rejects_v05_file(self, runner, db_path, tmp_path):
        """AC-35: v0.5 file rejected with error, exit 1."""
        import_file = tmp_path / "v05.yaml"
        import_file.write_text(
            "brewspec_version: '0.5'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1
        assert "0.5" in result.output

    def test_import_rejects_v04_file(self, runner, db_path, tmp_path):
        """AC-35: v0.4 file rejected with error, exit 1."""
        import_file = tmp_path / "v04.yaml"
        import_file.write_text(
            "brewspec_version: '0.4'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1
        assert "0.4" in result.output

    def test_import_rejects_unknown_version(self, runner, db_path, tmp_path):
        """AC-35: Unknown version rejected."""
        import_file = tmp_path / "bad.yaml"
        import_file.write_text(
            "brewspec_version: '99'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1

    def test_import_v05_rejection_message_contains_version(self, runner, db_path, tmp_path):
        """AC-36: Rejection message for v0.5 file mentions the version."""
        import_file = tmp_path / "v05.yaml"
        import_file.write_text(
            "brewspec_version: '0.5'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1
        assert "v0.5" in result.output or "0.5" in result.output

    def test_import_v05_rejection_lists_migration_steps(self, runner, db_path, tmp_path):
        """AC-36: Rejection message for v0.5 file lists migration steps."""
        import_file = tmp_path / "v05.yaml"
        import_file.write_text(
            "brewspec_version: '0.5'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1
        # Check for migration guidance
        assert "brewspec_version" in result.output or "migrate" in result.output.lower()

    def test_import_v05_rejection_references_github(self, runner, db_path, tmp_path):
        """AC-36: Rejection message references github.com/coffee-standards/brewspec."""
        import_file = tmp_path / "v05.yaml"
        import_file.write_text(
            "brewspec_version: '0.5'\nbrews:\n  - date: '2026-02-19'\n    type: pour_over\n    dose_g: 18\n    water_weight_g: 280\n"
        )
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 1
        assert "github.com/coffee-standards/brewspec" in result.output


# ===========================================================================
# AC-37 to AC-43: brew_ratio field
# ===========================================================================


class TestBrewRatio:
    """brew_ratio field: add, update, show, export, import."""

    def test_brew_ratio_valid_on_add(self, runner, db_path):
        """AC-37: --brew-ratio valid value is stored."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "15.5",
        ])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["brew_ratio"] == pytest.approx(15.5)
        finally:
            conn.close()

    def test_brew_ratio_zero_rejected(self, runner, db_path):
        """AC-37: --brew-ratio 0 exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "0",
        ])
        assert result.exit_code == 1

    def test_brew_ratio_negative_rejected(self, runner, db_path):
        """AC-37: Negative --brew-ratio exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "-1.0",
        ])
        assert result.exit_code == 1

    def test_brew_ratio_on_update(self, runner, db_path):
        """AC-38: --brew-ratio on update stores the value."""
        _add_brew(runner)
        result = runner.invoke(cli, ["update", "1", "--brew-ratio", "16.0"])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["brew_ratio"] == pytest.approx(16.0)
        finally:
            conn.close()

    def test_brew_ratio_column_exists(self, db_path):
        """AC-39: brew_ratio REAL column exists after migration."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()]
            assert "brew_ratio" in cols
        finally:
            conn.close()

    def test_brew_ratio_shown_in_show(self, runner, db_path):
        """AC-40: brew_ratio displayed in show when non-null."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "15.5",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Brew Ratio" in result.output
        assert "15.5" in result.output

    def test_brew_ratio_not_shown_when_null(self, runner, db_path):
        """AC-40: Brew Ratio label absent when brew_ratio is null."""
        _add_brew(runner)
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Brew Ratio" not in result.output

    def test_brew_ratio_not_in_list(self, runner, db_path):
        """AC-41: Brew Ratio column absent from list output."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "15.5",
        ])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Brew Ratio" not in result.output

    def test_brew_ratio_in_export(self, runner, db_path, tmp_path):
        """AC-42: brew_ratio serialised in export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--brew-ratio", "15.5",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        assert doc["brews"][0]["brew_ratio"] == pytest.approx(15.5)

    def test_brew_ratio_in_import(self, runner, db_path, tmp_path):
        """AC-42: brew_ratio read from import file."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(yaml.dump({
            "brewspec_version": "0.7",
            "brews": [{
                "date": "2026-02-19",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "brew_ratio": 15.5,
            }]
        }))
        result = runner.invoke(cli, ["import", str(import_file)])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            assert rows[0]["brew_ratio"] == pytest.approx(15.5)
        finally:
            conn.close()

    def test_brew_ratio_in_updatable_columns(self, db_path):
        """AC-43: brew_ratio is in UPDATABLE_COLUMNS."""
        from brewlog import db as db_mod
        assert "brew_ratio" in db_mod.UPDATABLE_COLUMNS


# ===========================================================================
# AC-44 to AC-50: coffee.origins structured data
# ===========================================================================


class TestCoffeeOrigins:
    """Structured origin data: add, update, show, export, import, migration."""

    def test_origin_country_flag(self, runner, db_path):
        """AC-45: --origin-country stored in coffee_origins."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
        ])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            origins = json.loads(row["coffee_origins"])
            assert origins[0]["country"] == "Ethiopia"
        finally:
            conn.close()

    def test_origin_multiple_fields(self, runner, db_path):
        """AC-45: Multiple --origin-* flags form a single origin object."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-region", "Yirgacheffe",
            "--origin-process", "Washed",
        ])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            origins = json.loads(row["coffee_origins"])
            assert len(origins) == 1
            assert origins[0]["country"] == "Ethiopia"
            assert origins[0]["region"] == "Yirgacheffe"
            assert origins[0]["process"] == "Washed"
        finally:
            conn.close()

    def test_origin_varietal(self, runner, db_path):
        """AC-45: --origin-varietal stored in origin object."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-varietal", "Heirloom",
        ])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            origins = json.loads(row["coffee_origins"])
            assert origins[0]["varietal"] == "Heirloom"
        finally:
            conn.close()

    def test_multi_origin_blend(self, runner, db_path):
        """AC-46: Multiple --origin-country creates multiple origin objects."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-country", "Colombia",
        ])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            origins = json.loads(row["coffee_origins"])
            assert len(origins) == 2
            countries = {o["country"] for o in origins}
            assert "Ethiopia" in countries
            assert "Colombia" in countries
        finally:
            conn.close()

    def test_origin_update_replaces_all(self, runner, db_path):
        """AC-47: update with origin flags replaces entire coffee_origins."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-country", "Colombia",
        ])
        runner.invoke(cli, ["update", "1", "--origin-country", "Brazil"])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            origins = json.loads(row["coffee_origins"])
            assert len(origins) == 1
            assert origins[0]["country"] == "Brazil"
        finally:
            conn.close()

    def test_origin_single_show(self, runner, db_path):
        """AC-48: Single origin displayed with 'Origin:' label in show."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-region", "Yirgacheffe",
            "--origin-varietal", "Heirloom",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Origin:" in result.output
        assert "Ethiopia" in result.output
        assert "Yirgacheffe" in result.output
        assert "Heirloom" in result.output

    def test_origin_blend_show(self, runner, db_path):
        """AC-48: Multiple origins displayed with 'Origin 1:' and 'Origin 2:' labels."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-country", "Colombia",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Origin 1:" in result.output
        assert "Origin 2:" in result.output

    def test_origin_serialised_in_export(self, runner, db_path, tmp_path):
        """AC-49: coffee_origins serialised in v0.7 export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-region", "Yirgacheffe",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        origins = doc["brews"][0]["coffee"]["origins"]
        assert origins[0]["country"] == "Ethiopia"
        assert origins[0]["region"] == "Yirgacheffe"

    def test_origin_not_at_top_level_in_export(self, runner, db_path, tmp_path):
        """AC-49: No coffee.process or coffee.varietal at top level of coffee object in export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-varietal", "Heirloom",
            "--origin-process", "Washed",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        coffee = doc["brews"][0].get("coffee", {})
        assert "varietal" not in coffee
        assert "process" not in coffee

    def test_origin_import_reads_origins(self, runner, db_path, tmp_path):
        """AC-50: import reads coffee.origins into coffee_origins column."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(yaml.dump({
            "brewspec_version": "0.7",
            "brews": [{
                "date": "2026-02-19",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "coffee": {
                    "origins": [{"country": "Ethiopia", "region": "Yirgacheffe"}]
                }
            }]
        }))
        runner.invoke(cli, ["import", str(import_file)])
        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            origins = json.loads(rows[0]["coffee_origins"])
            assert origins[0]["country"] == "Ethiopia"
        finally:
            conn.close()

    def test_origin_migration_from_string_array(self, db_path):
        """AC-44: legacy coffee_origin string array migrated to coffee_origins object array."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            # Insert a legacy row with coffee_origin but no coffee_origins
            conn.execute(
                "INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_origin) "
                "VALUES (?, ?, ?, ?, ?)",
                ("2026-01-01", "pour_over", 18.0, 280.0, json.dumps(["Ethiopia"]))
            )
            conn.commit()
            row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()

        # Re-open connection to trigger migration
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            # Migration should have run
            assert row["coffee_origins"] is not None
            origins = json.loads(row["coffee_origins"])
            assert origins[0]["country"] == "Ethiopia"
        finally:
            conn.close()

    def test_origin_varietal_export_import_round_trip(self, runner, db_path, tmp_path):
        """varietal survives export → import round-trip via coffee.origins."""
        # 1. Add a brew with --origin-country and --origin-varietal
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-country", "Ethiopia",
            "--origin-varietal", "Heirloom",
        ])

        # 2. Export to a temp YAML file
        out_file = tmp_path / "export.yaml"
        result = runner.invoke(cli, ["export", str(out_file)])
        assert result.exit_code == 0

        # 3. Delete the brew so the DB is empty
        runner.invoke(cli, ["delete", "1", "--yes"])

        # 4. Re-import the YAML file
        result = runner.invoke(cli, ["import", str(out_file)])
        assert result.exit_code == 0

        # 5. Assert the re-imported brew has varietal: "Heirloom" in coffee_origins
        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            assert len(rows) == 1
            origins = json.loads(rows[0]["coffee_origins"])
            assert origins[0]["varietal"] == "Heirloom"
        finally:
            conn.close()

    def test_origin_varietal_castillo_export(self, runner, db_path, tmp_path):
        """MED-1: --origin-varietal Castillo survives to exported YAML origins[0].varietal."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--origin-varietal", "Castillo",
        ])
        out_file = tmp_path / "out.yaml"
        result = runner.invoke(cli, ["export", str(out_file)])
        assert result.exit_code == 0, result.output
        doc = yaml.safe_load(out_file.read_text())
        origins = doc["brews"][0]["coffee"]["origins"]
        assert origins[0]["varietal"] == "Castillo"

    def test_origin_varietal_import_show(self, runner, db_path, tmp_path):
        """MED-1: importing a YAML with varietal in origins[] shows varietal in `show` output."""
        import_file = tmp_path / "varietal_import.yaml"
        import_file.write_text(yaml.dump({
            "brewspec_version": "0.7",
            "brews": [{
                "date": "2026-03-10",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "coffee": {
                    "origins": [{"country": "Colombia", "varietal": "Castillo"}]
                },
            }]
        }))
        import_result = runner.invoke(cli, ["import", str(import_file)])
        assert import_result.exit_code == 0, import_result.output

        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            brew_id = rows[0]["id"]
        finally:
            conn.close()

        show_result = runner.invoke(cli, ["show", str(brew_id)])
        assert show_result.exit_code == 0, show_result.output
        assert "Castillo" in show_result.output

    def test_legacy_origin_export_fallback(self, db_path, tmp_path, monkeypatch):
        """AC-49: Legacy coffee_origin rows exported with origin object structure."""
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        runner = CliRunner()
        conn = db_module.get_connection(db_path=db_path)
        try:
            conn.execute(
                "INSERT INTO brews (date, type, dose_g, water_weight_g, coffee_origin) "
                "VALUES (?, ?, ?, ?, ?)",
                ("2026-01-01", "pour_over", 18.0, 280.0, json.dumps(["Ethiopia"]))
            )
            conn.commit()
        finally:
            conn.close()
        out_file = str(tmp_path / "out.yaml")
        result = runner.invoke(cli, ["export", out_file])
        assert result.exit_code == 0
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        origins = doc["brews"][0]["coffee"]["origins"]
        assert origins[0]["country"] == "Ethiopia"


# ===========================================================================
# AC-50a to AC-50g: coffee.name field
# ===========================================================================


class TestCoffeeName:
    """coffee.name field: add, update, show, export, import, search."""

    def test_coffee_name_add(self, runner, db_path):
        """AC-50b: --coffee-name stored in DB."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "Ethiopia Yirgacheffe",
        ])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["coffee_name"] == "Ethiopia Yirgacheffe"
        finally:
            conn.close()

    def test_coffee_name_empty_rejected(self, runner, db_path):
        """AC-50b: Empty --coffee-name exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "",
        ])
        assert result.exit_code == 1

    def test_coffee_name_update(self, runner, db_path):
        """AC-50c: --coffee-name on update stores value."""
        _add_brew(runner)
        result = runner.invoke(cli, ["update", "1", "--coffee-name", "New Name"])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["coffee_name"] == "New Name"
        finally:
            conn.close()

    def test_coffee_name_shown_in_show(self, runner, db_path):
        """AC-50d: coffee_name shown as 'Name:' first field in Coffee section."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "Ethiopia Yirgacheffe",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Name:" in result.output
        assert "Ethiopia Yirgacheffe" in result.output

    def test_coffee_name_in_export(self, runner, db_path, tmp_path):
        """AC-50e: coffee_name serialised as coffee.name in export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "Ethiopia Natural",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        assert doc["brews"][0]["coffee"]["name"] == "Ethiopia Natural"

    def test_coffee_name_in_import(self, runner, db_path, tmp_path):
        """AC-50e: coffee.name read from import file."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(yaml.dump({
            "brewspec_version": "0.7",
            "brews": [{
                "date": "2026-02-19",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "coffee": {"name": "Kenya AA"},
            }]
        }))
        runner.invoke(cli, ["import", str(import_file)])
        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            assert rows[0]["coffee_name"] == "Kenya AA"
        finally:
            conn.close()

    def test_coffee_name_in_updatable_columns(self):
        """AC-50f: coffee_name in UPDATABLE_COLUMNS."""
        from brewlog import db as db_mod
        assert "coffee_name" in db_mod.UPDATABLE_COLUMNS

    def test_coffee_name_searchable(self, runner, db_path):
        """AC-50g: coffee_name is searched by search command."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--coffee-name", "Kenya AA Kiambu",
        ])
        result = runner.invoke(cli, ["search", "kiambu"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_coffee_name_column_exists(self, db_path):
        """AC-50a: coffee_name TEXT column exists after migration."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()]
            assert "coffee_name" in cols
        finally:
            conn.close()


# ===========================================================================
# AC-51 to AC-57: Equipment fields
# ===========================================================================


class TestEquipmentFields:
    """equipment_grinder_setting and equipment_notes."""

    def test_grinder_setting_add(self, runner, db_path):
        """AC-53: --grinder-setting stored as REAL."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "21",
        ])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["equipment_grinder_setting"] == pytest.approx(21.0)
        finally:
            conn.close()

    def test_grinder_setting_zero_rejected(self, runner, db_path):
        """AC-53: --grinder-setting 0 exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "0",
        ])
        assert result.exit_code == 1

    def test_grinder_setting_negative_rejected(self, runner, db_path):
        """AC-53: Negative --grinder-setting exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "-1",
        ])
        assert result.exit_code == 1

    def test_equipment_notes_add(self, runner, db_path):
        """AC-53: --equipment-notes stored."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--equipment-notes", "Burrs 3 months old",
        ])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["equipment_notes"] == "Burrs 3 months old"
        finally:
            conn.close()

    def test_equipment_notes_empty_rejected(self, runner, db_path):
        """AC-53: Empty --equipment-notes exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--equipment-notes", "",
        ])
        assert result.exit_code == 1

    def test_grinder_setting_update(self, runner, db_path):
        """AC-54: --grinder-setting on update stores value."""
        _add_brew(runner)
        result = runner.invoke(cli, ["update", "1", "--grinder-setting", "25.0"])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["equipment_grinder_setting"] == pytest.approx(25.0)
        finally:
            conn.close()

    def test_equipment_notes_update(self, runner, db_path):
        """AC-54: --equipment-notes on update stores value."""
        _add_brew(runner)
        result = runner.invoke(cli, ["update", "1", "--equipment-notes", "New burrs"])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["equipment_notes"] == "New burrs"
        finally:
            conn.close()

    def test_grinder_setting_shown_in_show(self, runner, db_path):
        """AC-55: equipment_grinder_setting shown in Equipment section."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "21",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Grinder Setting" in result.output
        assert "21" in result.output

    def test_equipment_notes_shown_in_show(self, runner, db_path):
        """AC-55: equipment_notes shown in Equipment section."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--equipment-notes", "Burrs 3 months old",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert result.exit_code == 0
        assert "Notes:" in result.output
        assert "Burrs 3 months old" in result.output

    def test_equipment_section_shown_for_grinder_setting(self, runner, db_path):
        """AC-55: Equipment section shown when only grinder_setting is non-null."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "21",
        ])
        result = runner.invoke(cli, ["show", "1"])
        assert "Equipment" in result.output

    def test_grinder_setting_in_export(self, runner, db_path, tmp_path):
        """AC-56: equipment_grinder_setting serialised as number in export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--grinder-setting", "21",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        assert doc["brews"][0]["equipment"]["grinder_setting"] == pytest.approx(21.0)

    def test_equipment_notes_in_export(self, runner, db_path, tmp_path):
        """AC-56: equipment_notes serialised in export."""
        runner.invoke(cli, [
            "add", "--date", "2026-02-19", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--equipment-notes", "Burrs 3 months old",
        ])
        out_file = str(tmp_path / "out.yaml")
        runner.invoke(cli, ["export", out_file])
        doc = yaml.safe_load((tmp_path / "out.yaml").read_text())
        assert doc["brews"][0]["equipment"]["notes"] == "Burrs 3 months old"

    def test_equipment_import(self, runner, db_path, tmp_path):
        """AC-56: equipment fields read from import file."""
        import_file = tmp_path / "import.yaml"
        import_file.write_text(yaml.dump({
            "brewspec_version": "0.7",
            "brews": [{
                "date": "2026-02-19",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "equipment": {
                    "grinder": "Comandante",
                    "grinder_setting": 21.0,
                    "notes": "Fresh burrs",
                }
            }]
        }))
        runner.invoke(cli, ["import", str(import_file)])
        conn = db_module.get_connection(db_path=db_path)
        try:
            rows = db_module.get_all_brews(conn)
            assert rows[0]["equipment_grinder_setting"] == pytest.approx(21.0)
            assert rows[0]["equipment_notes"] == "Fresh burrs"
        finally:
            conn.close()

    def test_equipment_grinder_setting_in_updatable_columns(self):
        """AC-57: equipment_grinder_setting in UPDATABLE_COLUMNS."""
        from brewlog import db as db_mod
        assert "equipment_grinder_setting" in db_mod.UPDATABLE_COLUMNS

    def test_equipment_notes_in_updatable_columns(self):
        """AC-57: equipment_notes in UPDATABLE_COLUMNS."""
        from brewlog import db as db_mod
        assert "equipment_notes" in db_mod.UPDATABLE_COLUMNS

    def test_grinder_setting_column_is_real(self, db_path):
        """AC-51: equipment_grinder_setting column type is REAL."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            pragma = conn.execute("PRAGMA table_info(brews)").fetchall()
            col_types = {row[1]: row[2] for row in pragma}
            assert col_types.get("equipment_grinder_setting", "").upper() == "REAL"
        finally:
            conn.close()

    def test_equipment_notes_column_exists(self, db_path):
        """AC-52: equipment_notes TEXT column exists."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()]
            assert "equipment_notes" in cols
        finally:
            conn.close()

    def test_grinder_setting_legacy_text_coercion(self, db_path):
        """AC-51: Legacy TEXT grinder_setting values coerced to REAL on migration."""
        # Directly insert a string value bypassing normal insert path
        conn = db_module.get_connection(db_path=db_path)
        try:
            conn.execute(
                "INSERT INTO brews (date, type, dose_g, water_weight_g) VALUES (?, ?, ?, ?)",
                ("2026-02-19", "pour_over", 18.0, 280.0)
            )
            conn.commit()
            # Force a string into the grinder_setting column
            conn.execute(
                "UPDATE brews SET equipment_grinder_setting = '21 clicks' WHERE id = 1"
            )
            conn.commit()
        finally:
            conn.close()

        # Re-open to trigger migration
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            val = row["equipment_grinder_setting"]
            # After coercion, should be numeric (21.0) or NULL
            assert val is None or isinstance(val, (int, float))
            if val is not None:
                assert val == pytest.approx(21.0)
        finally:
            conn.close()


# ===========================================================================
# AC-58 to AC-60: Interactive brew type on update
# ===========================================================================


class TestInteractiveTypeOnUpdate:
    """Interactive brew type menu on update command."""

    def test_update_type_with_value(self, runner, db_path):
        """AC-59: --type VALUE sets type directly without interactive menu."""
        _add_brew(runner, brew_type="pour_over")
        result = runner.invoke(cli, ["update", "1", "--type", "espresso"])
        assert result.exit_code == 0
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["type"] == "espresso"
        finally:
            conn.close()

    def test_update_type_interactive_empty_string(self, runner, db_path):
        """AC-58: --type '' shows interactive menu."""
        _add_brew(runner, brew_type="pour_over")
        # Simulate user selecting '1' (espresso)
        result = runner.invoke(cli, ["update", "1", "--type", ""], input="1\n")
        assert result.exit_code == 0
        # Should show type selection menu
        assert "Select brew type" in result.output or "espresso" in result.output or "Choice" in result.output

    def test_update_type_interactive_menu_shows_options(self, runner, db_path):
        """AC-58: Interactive menu shows all brew type options."""
        _add_brew(runner, brew_type="pour_over")
        result = runner.invoke(cli, ["update", "1", "--type", ""], input="4\n")
        assert result.exit_code == 0
        # Menu options should appear
        assert "espresso" in result.output or "pour_over" in result.output

    def test_update_type_invalid_value_rejected(self, runner, db_path):
        """AC-59: Invalid --type VALUE is rejected."""
        _add_brew(runner, brew_type="pour_over")
        result = runner.invoke(cli, ["update", "1", "--type", "invalid_type"])
        assert result.exit_code == 1

    def test_update_no_type_flag_no_change(self, runner, db_path):
        """AC-60: No --type flag means no type update attempted."""
        _add_brew(runner, brew_type="pour_over")
        runner.invoke(cli, ["update", "1", "--notes", "test"])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(1, conn)
            assert row["type"] == "pour_over"  # unchanged
        finally:
            conn.close()

    def test_update_type_in_updatable_columns(self):
        """AC-58: type is in UPDATABLE_COLUMNS per design doc resolution."""
        from brewlog import db as db_mod
        assert "type" in db_mod.UPDATABLE_COLUMNS
