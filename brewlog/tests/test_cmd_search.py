"""
Tests for brewlog search command (AC-6 through AC-14).
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import BrewInput


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


class TestSearchCommand:
    """Full search command coverage."""

    def test_search_command_exists(self, runner):
        """AC-6: search is a top-level command."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0

    def test_search_requires_query(self, runner):
        """AC-6: QUERY is required."""
        result = runner.invoke(cli, ["search"])
        assert result.exit_code != 0

    def test_search_matches_notes_field(self, runner, db_path):
        """AC-6/AC-7: notes field is searched."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(
                date="2026-02-19", type="pour_over",
                dose_g=18.0, water_weight_g=280.0,
                notes="Ethiopia Yirgacheffe washed"
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "yirgacheffe"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_tasting_notes_field(self, runner, db_path):
        """AC-6/AC-7: result_tasting_notes field is searched."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(brew_id, {"result_tasting_notes": "jasmine and bergamot"}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "bergamot"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_coffee_name_field(self, runner, db_path):
        """AC-6/AC-7: coffee_name field is searched."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(brew_id, {"coffee_name": "Gesha Village Honey Process"}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "gesha"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_coffee_origins_field(self, runner, db_path):
        """AC-6/AC-7: coffee_origins JSON field is searched."""
        import json
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(
                brew_id,
                {"coffee_origins": json.dumps([{"country": "Kenya", "region": "Kirinyaga"}])},
                conn
            )
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "kirinyaga"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_matches_legacy_coffee_origin(self, runner, db_path):
        """AC-7: Legacy coffee_origin column is searched."""
        import json
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            # coffee_origin is not in UPDATABLE_COLUMNS; insert directly
            conn.execute(
                "UPDATE brews SET coffee_origin = ? WHERE id = ?",
                (json.dumps(["Guatemala"]), brew_id)
            )
            conn.commit()
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "guatemala"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_case_insensitive_upper(self, runner, db_path):
        """AC-9: Uppercase query matches lowercase data."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="colombia huila washed")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "COLOMBIA"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_case_insensitive_mixed(self, runner, db_path):
        """AC-9: Mixed case query matches."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="Colombia Huila")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "cOlOmBiA"])
        assert result.exit_code == 0
        assert "pour_over" in result.output

    def test_search_no_results(self, runner, db_path):
        """AC-10: No match returns friendly message and exit 0."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "xyznosuchthing123"])
        assert result.exit_code == 0
        assert 'No brews found matching "xyznosuchthing123".' in result.output

    def test_search_empty_string_error(self, runner):
        """AC-11: Empty query string errors with exit 1."""
        result = runner.invoke(cli, ["search", ""])
        assert result.exit_code == 1

    def test_search_whitespace_only_error(self, runner):
        """AC-11: Whitespace-only query errors with exit 1."""
        result = runner.invoke(cli, ["search", "   "])
        assert result.exit_code == 1

    def test_search_empty_error_message(self, runner):
        """AC-11: Error message for empty query mentions 'empty'."""
        result = runner.invoke(cli, ["search", ""])
        assert result.exit_code == 1
        assert "empty" in result.output.lower() or "Error" in result.output

    def test_search_limit_caps_results(self, runner, db_path):
        """AC-12: --limit N limits results to N."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for i in range(10):
                brew = BrewInput(
                    date=f"2026-02-{10+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0,
                    notes="match text here"
                )
                db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "match", "--limit", "4"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.strip().split("\n") if ln.strip()]
        # header + separator = 2 lines, then 4 data lines
        data_lines = lines[2:]
        assert len(data_lines) == 4

    def test_search_no_limit_returns_all(self, runner, db_path):
        """AC-12: No limit returns all matches."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for i in range(7):
                brew = BrewInput(
                    date=f"2026-02-{10+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0,
                    notes="all match"
                )
                db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "all match"])
        assert result.exit_code == 0
        lines = [ln for ln in result.output.strip().split("\n") if ln.strip()]
        data_lines = lines[2:]
        assert len(data_lines) == 7

    def test_search_sql_injection_safe(self, runner, db_path):
        """AC-13: SQL injection characters in query don't cause errors."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        # Various SQL injection patterns
        for query in ["'; DROP TABLE brews; --", "' OR '1'='1", "% (wildcard)", "1; SELECT *"]:
            result = runner.invoke(cli, ["search", query])
            assert result.exit_code == 0  # should not crash

    def test_search_output_has_table_headers(self, runner, db_path):
        """AC-8: Output has same table headers as list (ID, Date, Type, Dose, Water)."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="findme")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["search", "findme"])
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Date" in result.output
        assert "Type" in result.output
        assert "Dose" in result.output
        assert "Water" in result.output

    def test_search_brews_function_in_db(self, db_path):
        """AC-13: search_brews() function exists in db module with parameterised queries."""
        from brewlog import db as db_mod
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0,
                             water_weight_g=280.0, notes="unique test phrase")
            db_mod.insert_brew(brew, conn)
            rows = db_mod.search_brews(conn, "unique test phrase")
            assert len(rows) == 1
        finally:
            conn.close()

    def test_search_brews_function_limit(self, db_path):
        """AC-12: search_brews() respects limit parameter."""
        from brewlog import db as db_mod
        conn = db_module.get_connection(db_path=db_path)
        try:
            for i in range(5):
                brew = BrewInput(
                    date=f"2026-02-{19+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0,
                    notes="limited search"
                )
                db_mod.insert_brew(brew, conn)
            rows = db_mod.search_brews(conn, "limited search", limit=3)
            assert len(rows) == 3
        finally:
            conn.close()

    def test_search_with_db_flag(self, tmp_path):
        """AC-14: --db PATH works with search command."""
        runner = CliRunner()
        custom_db = tmp_path / "custom.db"
        conn = db_module.get_connection(db_path=custom_db)
        try:
            brew = BrewInput(date="2026-02-19", type="espresso", dose_g=18.0,
                             water_weight_g=36.0, notes="ristretto pull")
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["--db", str(custom_db), "search", "ristretto"])
        assert result.exit_code == 0
        assert "espresso" in result.output

    def test_search_does_not_match_non_searched_fields(self, runner, db_path):
        """AC-6: Fields not in search scope (e.g., method, grind) are not searched."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(
                date="2026-02-19", type="pour_over",
                dose_g=18.0, water_weight_g=280.0,
                method="Hario V60",
                grind="coarse",
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        # Searching by method value — should not match
        result = runner.invoke(cli, ["search", "Hario V60"])
        assert result.exit_code == 0
        assert "No brews found" in result.output
