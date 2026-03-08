"""
Tests for brewlog stats command (AC-1 through AC-5).

These tests are extracted for clarity but also covered in test_cmd_v05.py.
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


class TestStatsCommand:
    """Full stats command coverage."""

    def test_stats_command_exists(self, runner):
        """AC-1: stats is a top-level command."""
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0

    def test_stats_empty_db_exit_0(self, runner):
        """AC-4: Empty DB exits with code 0."""
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0

    def test_stats_empty_db_message(self, runner):
        """AC-4: Empty DB prints friendly message."""
        result = runner.invoke(cli, ["stats"])
        assert "No brews logged yet. Run 'brewlog add' to log your first brew." in result.output

    def test_stats_with_one_brew(self, runner, db_path):
        """AC-1: stats with one brew returns exit 0."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0

    def test_stats_total_count(self, runner, db_path):
        """AC-2: Total count matches number of brews."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for i in range(5):
                brew = BrewInput(
                    date=f"2026-02-{19+i:02d}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0
                )
                db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "5" in result.output

    def test_stats_most_common_type_single(self, runner, db_path):
        """AC-2: Most common type when clear winner exists."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for brew_type, count in [("pour_over", 3), ("espresso", 1)]:
                for i in range(count):
                    brew = BrewInput(
                        date=f"2026-02-{19+i:02d}", type=brew_type,
                        dose_g=18.0, water_weight_g=280.0
                    )
                    db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "pour_over" in result.output

    def test_stats_average_rating_no_ratings(self, runner, db_path):
        """AC-2: No ratings shows 'No ratings logged'."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "No ratings logged" in result.output

    def test_stats_average_rating_with_ratings(self, runner, db_path):
        """AC-2: Average rating computed correctly."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r, day in [(4, 19), (5, 20), (3, 21)]:
                brew = BrewInput(
                    date=f"2026-02-{day}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0
                )
                brew_id = db_module.insert_brew(brew, conn)
                db_module.update_brew(brew_id, {"result_rating_overall": r}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        # Average of 4, 5, 3 = 4.0
        assert "4.0" in result.output

    def test_stats_rating_distribution_all_stars(self, runner, db_path):
        """AC-2: Distribution shows all 5 star levels."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r, day in [(1, 19), (2, 20), (3, 21), (4, 22), (5, 23)]:
                brew = BrewInput(
                    date=f"2026-02-{day}", type="pour_over",
                    dose_g=18.0, water_weight_g=280.0
                )
                brew_id = db_module.insert_brew(brew, conn)
                db_module.update_brew(brew_id, {"result_rating_overall": r}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        for star in ["1 star", "2 star", "3 star", "4 star", "5 star"]:
            assert star in result.output

    def test_stats_brew_summary_section(self, runner, db_path):
        """AC-3: Output has 'Brew Summary' section header."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "Brew Summary" in result.output
        assert "============" in result.output

    def test_stats_ratings_section(self, runner, db_path):
        """AC-3: Output has 'Ratings' section."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "Ratings" in result.output
        assert "-------" in result.output

    def test_stats_total_brews_label(self, runner, db_path):
        """AC-3: 'Total brews:' label present."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "Total brews:" in result.output

    def test_stats_most_common_type_label(self, runner, db_path):
        """AC-3: 'Most common type:' label present."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "Most common type:" in result.output

    def test_stats_distribution_label(self, runner, db_path):
        """AC-3: 'Distribution:' label present."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_module.insert_brew(brew, conn)
            db_module.update_brew(brew_id, {"result_rating_overall": 4}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert "Distribution:" in result.output

    def test_stats_get_brew_stats_function(self, db_path):
        """stats queries are available as get_brew_stats() in db module."""
        from brewlog import db as db_mod
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-02-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            brew_id = db_mod.insert_brew(brew, conn)
            db_mod.update_brew(brew_id, {"result_rating_overall": 4}, conn)
            stats = db_mod.get_brew_stats(conn)
            assert stats["total"] == 1
            assert stats["most_common_type"] == "pour_over"
            assert stats["avg_overall_rating"] == pytest.approx(4.0)
            assert stats["rating_distribution"][4] == 1
            assert stats["rating_distribution"][1] == 0
        finally:
            conn.close()

    def test_stats_get_brew_stats_empty(self, db_path):
        """get_brew_stats() on empty DB returns correct defaults."""
        from brewlog import db as db_mod
        conn = db_module.get_connection(db_path=db_path)
        try:
            stats = db_mod.get_brew_stats(conn)
            assert stats["total"] == 0
            assert stats["most_common_type"] is None
            assert stats["avg_overall_rating"] is None
        finally:
            conn.close()
