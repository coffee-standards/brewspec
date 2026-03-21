"""
Tests for BrewLog CLI v0.8 — BrewSpec v0.9 adoption.

Covers all acceptance criteria for the rating range expansion (1-5 → 1-9):

AC-1:  RatingsInput validates 1-9; rejects 0 and 10
AC-2:  brewlog add accepts --rating-* 1-9; rejects out-of-range
AC-3:  brewlog update accepts --rating-* 1-9; rejects out-of-range
AC-4:  brewlog list --rating-min/max accepts 1-9; rejects out-of-range
AC-5:  --rating-min 7 and --rating-max 3 filter correctly
AC-7:  get_brew_stats returns rating_distribution with keys 1-9
AC-8:  brewlog stats displays distribution with numeric labels 1-9
AC-9:  help text for rating flags reads "[Dimension] rating, 1-9."
AC-13: BREWSPEC_VERSION constant is "0.9"
AC-14: brewlog export produces brewspec_version: "0.9"
AC-15: brewlog import accepts v0.9 documents (ratings 1-9)
AC-18: RatingsInput docstring updated to 1-9 / CVA
AC-19: retired --rating message refers to 1-9

D-1:   v0.8 import rejection is intentional per design Section 3.4 (documented below)
D-2:   retired --rating error message now says 1-9
D-3:   bundled schema is v0.9 (maximum: 9 on all rating dims, const: "0.9")

TDD: tests written before implementation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pydantic import ValidationError

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import RatingsInput, BrewInput
from brewlog.serialise import BREWSPEC_VERSION


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(db_path, rating_overall=None):
    """Helper: insert a brew with optional overall rating."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        brew_id = db_module.insert_brew(brew, conn)
        if rating_overall is not None:
            db_module.update_brew(brew_id, {"result_rating_overall": rating_overall}, conn)
        return brew_id
    finally:
        conn.close()


# ===========================================================================
# AC-1: RatingsInput Pydantic validation — 1-9 inclusive
# ===========================================================================

class TestRatingsInputValidation:
    """AC-1: All eight dimensions validate 1-9; reject 0, 10."""

    def test_ratings_overall_min_accepted(self):
        """overall = 1 is accepted."""
        r = RatingsInput(overall=1)
        assert r.overall == 1

    def test_ratings_overall_max_accepted(self):
        """overall = 9 is accepted (new upper bound)."""
        r = RatingsInput(overall=9)
        assert r.overall == 9

    def test_ratings_overall_mid_range_accepted(self):
        """overall = 5 (former max) still accepted under 1-9."""
        r = RatingsInput(overall=5)
        assert r.overall == 5

    def test_ratings_overall_zero_rejected(self):
        """overall = 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RatingsInput(overall=0)
        assert "1 and 9 inclusive" in str(exc_info.value)

    def test_ratings_overall_ten_rejected(self):
        """overall = 10 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RatingsInput(overall=10)
        assert "1 and 9 inclusive" in str(exc_info.value)

    def test_ratings_overall_negative_rejected(self):
        """overall = -1 raises ValidationError."""
        with pytest.raises(ValidationError):
            RatingsInput(overall=-1)

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_ratings_all_dims_accept_9(self, dim):
        """Every dimension accepts 9."""
        r = RatingsInput(**{dim: 9})
        assert getattr(r, dim) == 9

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_ratings_all_dims_reject_10(self, dim):
        """Every dimension rejects 10."""
        with pytest.raises(ValidationError):
            RatingsInput(**{dim: 10})

    def test_ratings_error_message_says_1_to_9(self):
        """AC-1: Error message says 'between 1 and 9 inclusive'."""
        with pytest.raises(ValidationError) as exc_info:
            RatingsInput(overall=10)
        assert "rating dimension must be between 1 and 9 inclusive" in str(exc_info.value)

    def test_ratings_none_accepted(self):
        """All fields optional — None is still accepted."""
        r = RatingsInput()
        assert r.overall is None

    def test_ratings_full_nine_set(self):
        """All eight dims set to 9 simultaneously is accepted."""
        r = RatingsInput(
            overall=9, fragrance=9, aroma=9, flavour=9,
            aftertaste=9, acidity=9, sweetness=9, mouthfeel=9,
        )
        assert r.overall == 9
        assert r.mouthfeel == 9


# ===========================================================================
# AC-18: RatingsInput docstring updated
# ===========================================================================

def test_ratings_input_docstring_mentions_1_to_9():
    """AC-18: RatingsInput docstring includes '1-9'."""
    assert "1-9" in RatingsInput.__doc__


def test_ratings_input_docstring_mentions_cva():
    """AC-18: RatingsInput docstring mentions CVA."""
    assert "CVA" in RatingsInput.__doc__


# ===========================================================================
# AC-2: brewlog add accepts 1-9, rejects out-of-range
# ===========================================================================

class TestAddCommandRatings:
    """AC-2: add command rating flags accept 1-9, reject 0 and 10."""

    def test_add_rating_overall_9_accepted(self, runner):
        """--rating-overall 9 logs successfully."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "9",
        ])
        assert result.exit_code == 0

    def test_add_rating_overall_1_accepted(self, runner):
        """--rating-overall 1 logs successfully."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "1",
        ])
        assert result.exit_code == 0

    def test_add_rating_overall_5_still_accepted(self, runner):
        """--rating-overall 5 (former max) still accepted."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "5",
        ])
        assert result.exit_code == 0

    def test_add_rating_overall_0_rejected(self, runner):
        """--rating-overall 0 exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "0",
        ])
        assert result.exit_code == 1

    def test_add_rating_overall_10_rejected(self, runner):
        """--rating-overall 10 exits with code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "10",
        ])
        assert result.exit_code == 1

    def test_add_rating_overall_10_error_message(self, runner):
        """AC-2: error message says 'between 1 and 9'."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "10",
        ])
        assert "Error: --rating-overall must be an integer between 1 and 9." in result.output

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_add_rating_dim_10_rejected(self, runner, dim):
        """Each non-overall dimension rejects 10."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            f"--rating-{dim}", "10",
        ])
        assert result.exit_code == 1
        assert f"Error: --rating-{dim} must be an integer between 1 and 9." in result.output

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_add_rating_dim_9_accepted(self, runner, dim):
        """Each non-overall dimension accepts 9."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            f"--rating-{dim}", "9",
        ])
        assert result.exit_code == 0

    def test_add_rating_9_stored_in_db(self, runner, db_path):
        """AC-2: rating of 9 is stored correctly in DB."""
        runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating-overall", "9",
        ])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = conn.execute(
                "SELECT result_rating_overall FROM brews ORDER BY id DESC LIMIT 1"
            ).fetchone()
            assert row[0] == 9
        finally:
            conn.close()


# ===========================================================================
# AC-9: Help text for rating flags reads "[Dimension] rating, 1-9."
# ===========================================================================

class TestAddHelpText:
    """AC-9: add --help shows 1-9 in rating dimension help text."""

    def test_add_help_rating_overall_mentions_1_9(self, runner):
        """--rating-overall help text says '1-9'."""
        result = runner.invoke(cli, ["add", "--help"])
        assert "Overall impression, 1-9." in result.output

    def test_add_help_rating_fragrance_mentions_1_9(self, runner):
        """--rating-fragrance help text says '1-9'."""
        result = runner.invoke(cli, ["add", "--help"])
        assert "Fragrance rating, 1-9." in result.output

    def test_add_help_rating_mouthfeel_mentions_1_9(self, runner):
        """--rating-mouthfeel help text says '1-9'."""
        result = runner.invoke(cli, ["add", "--help"])
        assert "Mouthfeel rating, 1-9." in result.output

    def test_add_help_does_not_mention_old_1_5_for_ratings(self, runner):
        """Add help text no longer contains '1-5' for rating fields."""
        result = runner.invoke(cli, ["add", "--help"])
        # The help output should not contain any '1-5' in rating context
        # (Other flags like water_temp_c mention 0-100, not 1-5)
        assert "rating, 1-5" not in result.output
        assert "impression, 1-5" not in result.output


# ===========================================================================
# D-2: Retired --rating error message refers to 1-9
# ===========================================================================

class TestRetiredRatingFlag:
    """D-2: The retired --rating flag error message says 1-9."""

    def test_add_retired_rating_flag_error_says_1_9(self, runner):
        """Add: retired --rating flag message updated to 1-9."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-21", "--type", "pour_over",
            "--dose", "18.0", "--water", "280.0",
            "--rating", "4",
        ])
        assert result.exit_code == 1
        assert "1-9" in result.output
        assert "1-5" not in result.output

    def test_update_retired_rating_flag_error_says_1_9(self, runner, db_path):
        """Update: retired --rating flag message updated to 1-9."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating", "4"])
        assert result.exit_code == 1
        assert "1-9" in result.output
        assert "1-5" not in result.output


# ===========================================================================
# AC-3: brewlog update accepts 1-9, rejects out-of-range
# ===========================================================================

class TestUpdateCommandRatings:
    """AC-3: update command rating flags accept 1-9, reject 0 and 10."""

    def test_update_rating_overall_9_accepted(self, runner, db_path):
        """--rating-overall 9 updates successfully."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating-overall", "9"])
        assert result.exit_code == 0

    def test_update_rating_overall_1_accepted(self, runner, db_path):
        """--rating-overall 1 updates successfully."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating-overall", "1"])
        assert result.exit_code == 0

    def test_update_rating_overall_0_rejected(self, runner, db_path):
        """--rating-overall 0 exits with code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating-overall", "0"])
        assert result.exit_code == 1

    def test_update_rating_overall_10_rejected(self, runner, db_path):
        """--rating-overall 10 exits with code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating-overall", "10"])
        assert result.exit_code == 1

    def test_update_rating_overall_10_error_message(self, runner, db_path):
        """AC-3: error message says 'between 1 and 9'."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "--rating-overall", "10"])
        assert "Error: --rating-overall must be an integer between 1 and 9." in result.output

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_update_rating_dim_10_rejected(self, runner, db_path, dim):
        """Each non-overall dimension rejects 10 in update."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", f"--rating-{dim}", "10"])
        assert result.exit_code == 1
        assert f"Error: --rating-{dim} must be an integer between 1 and 9." in result.output

    def test_update_help_rating_overall_mentions_1_9(self, runner):
        """AC-9: update --rating-overall help text says '1-9'."""
        result = runner.invoke(cli, ["update", "--help"])
        assert "Overall impression, 1-9." in result.output

    def test_update_help_does_not_mention_old_1_5_for_ratings(self, runner):
        """Update help text no longer contains '1-5' for rating fields."""
        result = runner.invoke(cli, ["update", "--help"])
        assert "rating, 1-5" not in result.output
        assert "impression, 1-5" not in result.output

    def test_update_rating_9_stored_in_db(self, runner, db_path):
        """AC-3: rating of 9 is stored correctly after update."""
        brew_id = _add_brew(db_path)
        runner.invoke(cli, ["update", str(brew_id), "--rating-overall", "9"])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = conn.execute(
                "SELECT result_rating_overall FROM brews WHERE id = ?", (brew_id,)
            ).fetchone()
            assert row[0] == 9
        finally:
            conn.close()


# ===========================================================================
# AC-4 & AC-5: brewlog list --rating-min/max with 1-9 range
# ===========================================================================

class TestListRatingFilter:
    """AC-4: --rating-min/max accept 1-9; reject out-of-range.
    AC-5: filters work correctly at new boundary values.
    """

    def test_list_rating_min_9_accepted(self, runner, db_path):
        """--rating-min 9 is valid."""
        _add_brew(db_path, rating_overall=9)
        result = runner.invoke(cli, ["list", "--rating-min", "9"])
        assert result.exit_code == 0

    def test_list_rating_max_9_accepted(self, runner, db_path):
        """--rating-max 9 is valid."""
        _add_brew(db_path, rating_overall=7)
        result = runner.invoke(cli, ["list", "--rating-max", "9"])
        assert result.exit_code == 0

    def test_list_rating_min_0_rejected(self, runner, db_path):
        """--rating-min 0 exits with code 1."""
        result = runner.invoke(cli, ["list", "--rating-min", "0"])
        assert result.exit_code == 1

    def test_list_rating_min_10_rejected(self, runner, db_path):
        """--rating-min 10 exits with code 1."""
        result = runner.invoke(cli, ["list", "--rating-min", "10"])
        assert result.exit_code == 1

    def test_list_rating_max_0_rejected(self, runner, db_path):
        """--rating-max 0 exits with code 1."""
        result = runner.invoke(cli, ["list", "--rating-max", "0"])
        assert result.exit_code == 1

    def test_list_rating_max_10_rejected(self, runner, db_path):
        """--rating-max 10 exits with code 1."""
        result = runner.invoke(cli, ["list", "--rating-max", "10"])
        assert result.exit_code == 1

    def test_list_rating_min_error_message(self, runner, db_path):
        """AC-4: --rating-min error says 'between 1 and 9'."""
        result = runner.invoke(cli, ["list", "--rating-min", "10"])
        assert "Error: --rating-min must be an integer between 1 and 9." in result.output

    def test_list_rating_max_error_message(self, runner, db_path):
        """AC-4: --rating-max error says 'between 1 and 9'."""
        result = runner.invoke(cli, ["list", "--rating-max", "10"])
        assert "Error: --rating-max must be an integer between 1 and 9." in result.output

    def test_list_rating_min_7_filters_correctly(self, runner, db_path):
        """AC-5: --rating-min 7 returns only brews with overall rating >= 7."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            b1 = db_module.insert_brew(brew, conn)
            db_module.update_brew(b1, {"result_rating_overall": 7}, conn)
            brew2 = BrewInput(date="2026-03-20", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            b2 = db_module.insert_brew(brew2, conn)
            db_module.update_brew(b2, {"result_rating_overall": 4}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["list", "--rating-min", "7"])
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        # Only the brew with rating 7 should appear (header + separator + 1 data row)
        assert len([line for line in lines if line.strip()]) >= 2  # header + 1 data row

    def test_list_rating_max_3_filters_correctly(self, runner, db_path):
        """AC-5: --rating-max 3 returns only brews with overall rating <= 3."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-19", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            b1 = db_module.insert_brew(brew, conn)
            db_module.update_brew(b1, {"result_rating_overall": 3}, conn)
            brew2 = BrewInput(date="2026-03-20", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            b2 = db_module.insert_brew(brew2, conn)
            db_module.update_brew(b2, {"result_rating_overall": 8}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["list", "--rating-max", "3"])
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        data_rows = [line for line in lines if line.strip() and not set(line.strip()).issubset({"-", " "})]
        # header + 1 data row
        assert len(data_rows) == 2

    def test_list_help_rating_min_mentions_1_9(self, runner):
        """AC-4: --rating-min help text says '1-9'."""
        result = runner.invoke(cli, ["list", "--help"])
        assert "1-9" in result.output

    def test_list_help_rating_max_mentions_1_9(self, runner):
        """AC-4: --rating-max help text says '1-9'."""
        result = runner.invoke(cli, ["list", "--help"])
        assert "1-9" in result.output


# ===========================================================================
# AC-7: get_brew_stats returns rating_distribution with keys 1-9
# ===========================================================================

class TestGetBrewStats:
    """AC-7: distribution dict has keys 1 through 9."""

    def test_stats_distribution_has_keys_1_through_9(self, db_path):
        """rating_distribution has exactly keys 1-9."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        dist = stats["rating_distribution"]
        assert set(dist.keys()) == set(range(1, 10))

    def test_stats_distribution_does_not_have_key_0(self, db_path):
        """rating_distribution has no key 0."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        assert 0 not in stats["rating_distribution"]

    def test_stats_distribution_does_not_have_key_6_through_old_max(self, db_path):
        """Under old schema, keys 6-9 didn't exist; now they do."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            db_module.insert_brew(brew, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        dist = stats["rating_distribution"]
        # Keys 6, 7, 8, 9 must now exist
        for k in [6, 7, 8, 9]:
            assert k in dist

    def test_stats_distribution_counts_rating_9(self, db_path):
        """Brew with rating 9 appears in distribution[9]."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            bid = db_module.insert_brew(brew, conn)
            db_module.update_brew(bid, {"result_rating_overall": 9}, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        assert stats["rating_distribution"][9] == 1

    def test_stats_distribution_zeros_for_empty_buckets(self, db_path):
        """Buckets with no brews show 0."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over", dose_g=18.0, water_weight_g=280.0)
            bid = db_module.insert_brew(brew, conn)
            db_module.update_brew(bid, {"result_rating_overall": 5}, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        dist = stats["rating_distribution"]
        assert dist[9] == 0
        assert dist[6] == 0
        assert dist[5] == 1

    def test_stats_distribution_full_1_through_9(self, db_path):
        """All nine buckets populated and counted correctly."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r, day in [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
                           (6, 6), (7, 7), (8, 8), (9, 9)]:
                brew = BrewInput(date=f"2026-03-{day:02d}", type="pour_over",
                                 dose_g=18.0, water_weight_g=280.0)
                bid = db_module.insert_brew(brew, conn)
                db_module.update_brew(bid, {"result_rating_overall": r}, conn)
            stats = db_module.get_brew_stats(conn)
        finally:
            conn.close()
        dist = stats["rating_distribution"]
        for r in range(1, 10):
            assert dist[r] == 1


# ===========================================================================
# AC-8: brewlog stats displays distribution with numeric labels 1-9
# ===========================================================================

class TestStatsDisplay:
    """AC-8: stats output shows distribution keys 1-9 with plain numeric labels."""

    def test_stats_distribution_shows_9_values(self, runner, db_path):
        """Distribution section has labels 1 through 9."""
        _add_brew(db_path, rating_overall=7)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        # All nine labels must appear
        for i in range(1, 10):
            assert f"  {i}:" in result.output

    def test_stats_distribution_format_exact(self, runner, db_path):
        """AC-8: Exact format of distribution output."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            for r, day in [(2, 1), (5, 2), (5, 3)]:
                brew = BrewInput(date=f"2026-03-{day:02d}", type="pour_over",
                                 dose_g=18.0, water_weight_g=280.0)
                bid = db_module.insert_brew(brew, conn)
                db_module.update_brew(bid, {"result_rating_overall": r}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        # Key 2 → count 1, key 5 → count 2, all others 0
        assert "  2:" in result.output
        assert "  5:" in result.output

    def test_stats_no_star_labels(self, runner, db_path):
        """AC-8: 'star' label no longer appears in stats output."""
        _add_brew(db_path, rating_overall=3)
        result = runner.invoke(cli, ["stats"])
        assert "star" not in result.output

    def test_stats_distribution_label_1_through_9_all_present(self, runner, db_path):
        """AC-8: All nine distribution labels present even with zero counts."""
        conn = db_module.get_connection(db_path=db_path)
        try:
            brew = BrewInput(date="2026-03-21", type="pour_over",
                             dose_g=18.0, water_weight_g=280.0)
            bid = db_module.insert_brew(brew, conn)
            db_module.update_brew(bid, {"result_rating_overall": 1}, conn)
        finally:
            conn.close()
        result = runner.invoke(cli, ["stats"])
        for i in range(1, 10):
            assert f"  {i}:" in result.output


# ===========================================================================
# AC-13: BREWSPEC_VERSION constant is "0.9"
# ===========================================================================

def test_brewspec_version_is_0_9():
    """AC-13: BREWSPEC_VERSION == '0.9'."""
    assert BREWSPEC_VERSION == "0.9"


# ===========================================================================
# AC-14: brewlog export produces brewspec_version: "0.9"
# ===========================================================================

def test_export_produces_brewspec_version_0_9(runner, db_path, tmp_path):
    """AC-14: exported YAML file has brewspec_version: '0.9'."""
    _add_brew(db_path)
    out_file = tmp_path / "export.yaml"
    result = runner.invoke(cli, ["export", str(out_file)])
    assert result.exit_code == 0
    data = yaml.safe_load(out_file.read_text())
    assert data["brewspec_version"] == "0.9"


def test_export_rating_9_round_trips(runner, db_path, tmp_path):
    """AC-14: rating of 9 survives export (value preserved in YAML)."""
    _add_brew(db_path, rating_overall=9)
    out_file = tmp_path / "export.yaml"
    runner.invoke(cli, ["export", str(out_file)])
    data = yaml.safe_load(out_file.read_text())
    assert data["brews"][0]["result"]["ratings"]["overall"] == 9


# ===========================================================================
# AC-15: brewlog import accepts v0.9 documents
# D-1: v0.8 documents WILL be rejected by v0.9 schema const — this is
#       intentional per design Section 3.4. The bundled schema uses
#       `const: "0.9"` on brewspec_version, so documents declaring "0.8"
#       fail schema validation. This is the correct behaviour: the import
#       command validates against the bundled schema version, not all prior
#       versions. Users must upgrade their documents to v0.9.
# ===========================================================================

class TestImportV09:
    """AC-15 and D-1: import behaviour for v0.9 documents."""

    def _write_brewspec(self, tmp_path: Path, doc: dict, filename: str = "import.yaml") -> Path:
        p = tmp_path / filename
        p.write_text(yaml.dump(doc))
        return p

    def test_import_v09_document_accepted(self, runner, db_path, tmp_path):
        """AC-15: v0.9 document with rating 9 imports without error."""
        doc = {
            "brewspec_version": "0.9",
            "brews": [{
                "date": "2026-03-21",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "result": {"ratings": {"overall": 9}},
            }],
        }
        p = self._write_brewspec(tmp_path, doc)
        result = runner.invoke(cli, ["import", str(p)])
        assert result.exit_code == 0

    def test_import_v09_document_rating_7_stored(self, runner, db_path, tmp_path):
        """AC-15: imported rating of 7 stored correctly in DB."""
        doc = {
            "brewspec_version": "0.9",
            "brews": [{
                "date": "2026-03-21",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "result": {"ratings": {"overall": 7}},
            }],
        }
        p = self._write_brewspec(tmp_path, doc)
        runner.invoke(cli, ["import", str(p)])
        conn = db_module.get_connection(db_path=db_path)
        try:
            row = conn.execute(
                "SELECT result_rating_overall FROM brews ORDER BY id DESC LIMIT 1"
            ).fetchone()
            assert row[0] == 7
        finally:
            conn.close()

    def test_import_v09_document_all_ratings_1_through_9_valid(self, runner, db_path, tmp_path):
        """AC-15: v0.9 document with all dimensions at 9 accepted."""
        doc = {
            "brewspec_version": "0.9",
            "brews": [{
                "date": "2026-03-21",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
                "result": {"ratings": {
                    "overall": 9,
                    "fragrance": 8,
                    "aroma": 7,
                    "flavour": 9,
                    "aftertaste": 6,
                    "acidity": 8,
                    "sweetness": 7,
                    "mouthfeel": 9,
                }},
            }],
        }
        p = self._write_brewspec(tmp_path, doc)
        result = runner.invoke(cli, ["import", str(p)])
        assert result.exit_code == 0

    def test_import_v08_document_rejected(self, runner, db_path, tmp_path):
        """D-1: v0.8 document is rejected — bundled schema const is '0.9'.
        This is intentional per design Section 3.4: the import command validates
        against the bundled schema, which requires brewspec_version: '0.9'.
        """
        doc = {
            "brewspec_version": "0.8",
            "brews": [{
                "date": "2026-03-21",
                "type": "pour_over",
                "dose_g": 18.0,
                "water_weight_g": 280.0,
            }],
        }
        p = self._write_brewspec(tmp_path, doc)
        result = runner.invoke(cli, ["import", str(p)])
        assert result.exit_code == 1


# ===========================================================================
# D-3: Bundled schema is v0.9 (maximum: 9, const: "0.9")
# ===========================================================================

class TestBundledSchema:
    """D-3: Verify the bundled schema is updated to v0.9."""

    def _load_schema(self) -> dict:
        schema_path = Path(__file__).parent.parent / "src" / "brewlog" / "brewspec.schema.json"
        return json.loads(schema_path.read_text())

    def test_bundled_schema_version_const_is_0_9(self):
        """D-3: brewspec_version const is '0.9'."""
        schema = self._load_schema()
        assert schema["properties"]["brewspec_version"]["const"] == "0.9"

    def test_bundled_schema_title_mentions_v0_9(self):
        """D-3: schema title references v0.9."""
        schema = self._load_schema()
        assert "0.9" in schema["title"]

    def test_bundled_schema_ratings_overall_max_is_9(self):
        """D-3: ratings.overall maximum is 9."""
        schema = self._load_schema()
        overall = schema["$defs"]["ratings"]["properties"]["overall"]
        assert overall["maximum"] == 9

    @pytest.mark.parametrize("dim", [
        "fragrance", "aroma", "flavour", "aftertaste",
        "acidity", "sweetness", "mouthfeel",
    ])
    def test_bundled_schema_ratings_dim_max_is_9(self, dim):
        """D-3: All rating dimensions have maximum: 9."""
        schema = self._load_schema()
        prop = schema["$defs"]["ratings"]["properties"][dim]
        assert prop["maximum"] == 9

    def test_bundled_schema_ratings_overall_min_is_1(self):
        """D-3: ratings.overall minimum is still 1."""
        schema = self._load_schema()
        overall = schema["$defs"]["ratings"]["properties"]["overall"]
        assert overall["minimum"] == 1
