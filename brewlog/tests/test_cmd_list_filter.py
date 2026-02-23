"""
CLI integration tests for `brewlog list` filtering.
Tests map to AC-18 through AC-24 in brewlog-cli-v0.2 spec.

Note: --rating filter removed in v0.4 (rating moved to result.ratings sub-object).
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module
from brewlog.models import BrewInput


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


def _insert(db_path, date, brew_type, method=None):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date=date,
            type=brew_type,
            dose_g=18.0,
            water_weight_g=280.0,
            method=method,
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-18: --type filter
# ---------------------------------------------------------------------------

def test_filter_type_returns_matching(runner, db_path):
    """AC-18: --type espresso returns only espresso brews."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    _insert(db_path, "2026-02-02T08:00:00Z", "espresso")
    result = runner.invoke(cli, ["list", "--type", "espresso"])
    assert result.exit_code == 0
    assert "espresso" in result.output


def test_filter_type_excludes_others(runner, db_path):
    """AC-18: --type espresso excludes non-espresso brews."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    _insert(db_path, "2026-02-02T08:00:00Z", "espresso")
    result = runner.invoke(cli, ["list", "--type", "espresso"])
    assert result.exit_code == 0
    assert "pour_over" not in result.output


def test_filter_type_invalid_exits_1(runner):
    """AC-18: invalid type value -> exit 1."""
    result = runner.invoke(cli, ["list", "--type", "drip"])
    assert result.exit_code == 1


def test_filter_type_invalid_message(runner):
    """AC-18: invalid type value -> error message shown."""
    result = runner.invoke(cli, ["list", "--type", "drip"])
    assert "drip" in result.output or "type" in result.output.lower() or "invalid" in result.output.lower()


def test_filter_type_all_valid_values(runner, db_path):
    """AC-18: all four valid type values are accepted."""
    for brew_type in ("immersion", "pour_over", "espresso", "hybrid"):
        _insert(db_path, "2026-02-01T08:00:00Z", brew_type)
    for brew_type in ("immersion", "pour_over", "espresso", "hybrid"):
        result = runner.invoke(cli, ["list", "--type", brew_type])
        assert result.exit_code == 0, f"--type {brew_type} should be valid"


# ---------------------------------------------------------------------------
# AC-20: --since filter
# ---------------------------------------------------------------------------

def test_filter_since_returns_matching(runner, db_path):
    """AC-20: --since excludes brews before the date."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over")  # old
    _insert(db_path, "2026-02-15T08:00:00Z", "pour_over")  # new
    result = runner.invoke(cli, ["list", "--since", "2026-02-01"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 1
    assert "2026-02-15" in result.output


def test_filter_since_excludes_before(runner, db_path):
    """AC-20: brews before --since date are excluded."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over")
    _insert(db_path, "2026-02-15T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--since", "2026-02-01"])
    assert "2026-01-01" not in result.output


def test_filter_since_same_date_included(runner, db_path):
    """AC-20: brew on the --since date itself is included."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--since", "2026-02-01"])
    assert result.exit_code == 0
    assert "2026-02-01" in result.output


def test_filter_since_invalid_format(runner):
    """AC-20: non-YYYY-MM-DD format -> exit 1."""
    result = runner.invoke(cli, ["list", "--since", "February 20"])
    assert result.exit_code == 1


def test_filter_since_invalid_date(runner):
    """AC-20: valid format but invalid date -> exit 1."""
    result = runner.invoke(cli, ["list", "--since", "2026-13-01"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-21: Filters are combinable (AND logic)
# ---------------------------------------------------------------------------

def test_filter_type_and_since_combined(runner, db_path):
    """AC-21: --type + --since applied together as AND."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over")  # too old
    _insert(db_path, "2026-02-01T08:00:00Z", "espresso")   # wrong type
    _insert(db_path, "2026-02-03T08:00:00Z", "pour_over")  # matches all
    result = runner.invoke(cli, ["list", "--type", "pour_over", "--since", "2026-02-01"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 1
    assert "2026-02-03" in result.output


# ---------------------------------------------------------------------------
# AC-22: No matches -> friendly message, exit 0
# ---------------------------------------------------------------------------

def test_filter_no_matches_message(runner, db_path):
    """AC-22: friendly message when filters match nothing."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--type", "espresso"])
    assert result.exit_code == 0
    assert "No brews match" in result.output


def test_filter_no_matches_no_table(runner, db_path):
    """AC-22: no table header when filters match nothing."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--type", "espresso"])
    # Should not print the table header
    assert "----" not in result.output


# ---------------------------------------------------------------------------
# AC-23: Filter interacts with --limit and --all
# ---------------------------------------------------------------------------

def test_filter_with_limit(runner, db_path):
    """AC-23: --limit applies to filtered result set."""
    for i in range(1, 6):
        _insert(db_path, f"2026-02-{i:02d}T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--type", "pour_over", "--limit", "3"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 3


def test_filter_with_all(runner, db_path):
    """AC-23: --all returns all matching brews, ignoring limit."""
    for i in range(1, 26):
        _insert(db_path, f"2026-01-{i:02d}T08:00:00Z", "espresso")
    result = runner.invoke(cli, ["list", "--type", "espresso", "--all"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 25


def test_filter_limit_applies_after_filter(runner, db_path):
    """AC-23: limit is applied to filtered set, not the full DB."""
    # 5 espresso + 10 pour_over; limit 3 on espresso should give 3, not 3 from mixed
    for i in range(1, 6):
        _insert(db_path, f"2026-02-{i:02d}T08:00:00Z", "espresso")
    for i in range(6, 16):
        _insert(db_path, f"2026-02-{i:02d}T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--type", "espresso", "--limit", "3"])
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 3
    assert "pour_over" not in result.output


# ---------------------------------------------------------------------------
# AC-24: No filter flags -> identical to v0.1.1 behaviour
# ---------------------------------------------------------------------------

def test_no_filters_default_limit_20(runner, db_path):
    """AC-24: without filter flags, default limit of 20 applies."""
    for i in range(1, 26):
        _insert(db_path, f"2026-01-{i:02d}T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 20


def test_no_filters_no_friendly_message(runner, db_path):
    """AC-24: without filter flags and brews present, no 'No brews match' message."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list"])
    assert "No brews match" not in result.output


# ---------------------------------------------------------------------------
# AC-39: --until filter
# ---------------------------------------------------------------------------

def test_filter_until_returns_matching(runner, db_path):
    """AC-39: --until excludes brews after the date."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over")  # before
    _insert(db_path, "2026-02-28T08:00:00Z", "pour_over")  # after
    result = runner.invoke(cli, ["list", "--until", "2026-02-01"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 1
    assert "2026-01-01" in result.output


def test_filter_until_excludes_after(runner, db_path):
    """AC-39: brews after --until date are excluded."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over")
    _insert(db_path, "2026-02-28T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--until", "2026-02-01"])
    assert "2026-02-28" not in result.output


def test_filter_until_same_date_included(runner, db_path):
    """AC-39: brew on the --until date itself is included."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--until", "2026-02-01"])
    assert result.exit_code == 0
    assert "2026-02-01" in result.output


def test_filter_until_date_only_included(runner, db_path):
    """AC-10: brew stored as date-only is included by --until on same day."""
    _insert(db_path, "2026-02-01", "pour_over")
    result = runner.invoke(cli, ["list", "--until", "2026-02-01"])
    assert result.exit_code == 0
    assert "2026-02-01" in result.output


def test_filter_until_invalid_format(runner):
    """AC-39: non-YYYY-MM-DD format -> exit 1."""
    result = runner.invoke(cli, ["list", "--until", "February 1"])
    assert result.exit_code == 1


def test_filter_until_invalid_date(runner):
    """AC-39: valid format but invalid date -> exit 1."""
    result = runner.invoke(cli, ["list", "--until", "2026-13-01"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-40: --since + --until combined
# ---------------------------------------------------------------------------

def test_filter_since_and_until_combined(runner, db_path):
    """AC-40: --since + --until returns brews within the range."""
    _insert(db_path, "2026-01-15T08:00:00Z", "pour_over")  # too old
    _insert(db_path, "2026-02-05T08:00:00Z", "pour_over")  # in range
    _insert(db_path, "2026-02-20T08:00:00Z", "pour_over")  # too new
    result = runner.invoke(cli, ["list", "--since", "2026-02-01", "--until", "2026-02-10"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 1
    assert "2026-02-05" in result.output


def test_filter_since_after_until_exits_1(runner, db_path):
    """AC-40: --since later than --until -> exit 1."""
    _insert(db_path, "2026-02-05T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--since", "2026-02-10", "--until", "2026-02-01"])
    assert result.exit_code == 1


def test_filter_since_after_until_message(runner, db_path):
    """AC-40: --since later than --until -> meaningful error message."""
    _insert(db_path, "2026-02-05T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list", "--since", "2026-02-10", "--until", "2026-02-01"])
    assert "since" in result.output.lower() or "until" in result.output.lower()


# ---------------------------------------------------------------------------
# AC-2/AC-3: --rating-min and --rating-max
# ---------------------------------------------------------------------------

def _insert_with_rating(db_path, date, overall_rating):
    """Insert a brew with a specific overall rating."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        from brewlog.models import BrewInput, ResultInput, RatingsInput
        brew = BrewInput(
            date=date,
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            result=ResultInput(ratings=RatingsInput(overall=overall_rating)),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def test_filter_rating_min_returns_matching(runner, db_path):
    """AC-2: --rating-min 4 returns only brews with overall >= 4."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 3)
    _insert_with_rating(db_path, "2026-02-02T08:00:00Z", 4)
    _insert_with_rating(db_path, "2026-02-03T08:00:00Z", 5)
    result = runner.invoke(cli, ["list", "--rating-min", "4"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 2


def test_filter_rating_min_excludes_below(runner, db_path):
    """AC-2: --rating-min 4 excludes brews with overall < 4."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 3)
    _insert_with_rating(db_path, "2026-02-02T08:00:00Z", 4)
    result = runner.invoke(cli, ["list", "--rating-min", "4"])
    assert "2026-02-01" not in result.output
    assert "2026-02-02" in result.output


def test_filter_rating_max_returns_matching(runner, db_path):
    """AC-3: --rating-max 3 returns only brews with overall <= 3."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 2)
    _insert_with_rating(db_path, "2026-02-02T08:00:00Z", 3)
    _insert_with_rating(db_path, "2026-02-03T08:00:00Z", 4)
    result = runner.invoke(cli, ["list", "--rating-max", "3"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 2


def test_filter_rating_max_excludes_above(runner, db_path):
    """AC-3: --rating-max 3 excludes brews with overall > 3."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 3)
    _insert_with_rating(db_path, "2026-02-02T08:00:00Z", 4)
    result = runner.invoke(cli, ["list", "--rating-max", "3"])
    assert "2026-02-02" not in result.output
    assert "2026-02-01" in result.output


def test_filter_rating_min_invalid_zero(runner):
    """AC-2: --rating-min 0 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating-min", "0"])
    assert result.exit_code == 1


def test_filter_rating_min_invalid_high(runner):
    """AC-2: --rating-min 6 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating-min", "6"])
    assert result.exit_code == 1


def test_filter_rating_max_invalid_zero(runner):
    """AC-3: --rating-max 0 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating-max", "0"])
    assert result.exit_code == 1


def test_filter_rating_max_invalid_high(runner):
    """AC-3: --rating-max 6 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating-max", "6"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-4: --rating-min and --rating-max combined
# ---------------------------------------------------------------------------

def test_filter_rating_range_combined(runner, db_path):
    """AC-4: --rating-min 3 --rating-max 4 returns brews with 3 <= overall <= 4."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 2)
    _insert_with_rating(db_path, "2026-02-02T08:00:00Z", 3)
    _insert_with_rating(db_path, "2026-02-03T08:00:00Z", 4)
    _insert_with_rating(db_path, "2026-02-04T08:00:00Z", 5)
    result = runner.invoke(cli, ["list", "--rating-min", "3", "--rating-max", "4"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 2


def test_filter_rating_min_exceeds_max_exits_1(runner, db_path):
    """AC-4: --rating-min 4 --rating-max 3 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating-min", "4", "--rating-max", "3"])
    assert result.exit_code == 1


def test_filter_rating_min_exceeds_max_message(runner, db_path):
    """AC-4: --rating-min > --rating-max -> meaningful error."""
    result = runner.invoke(cli, ["list", "--rating-min", "4", "--rating-max", "3"])
    assert "rating" in result.output.lower() or "min" in result.output.lower()


# ---------------------------------------------------------------------------
# AC-5: --rating-min/--rating-max combinable with other filters
# ---------------------------------------------------------------------------

def test_filter_rating_min_with_type(runner, db_path):
    """AC-5: --rating-min combined with --type."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 4)
    conn = db_module.get_connection(db_path=db_path)
    try:
        from brewlog.models import BrewInput, ResultInput, RatingsInput
        brew = BrewInput(
            date="2026-02-02T08:00:00Z",
            type="espresso",
            dose_g=18.0,
            water_weight_g=36.0,
            result=ResultInput(ratings=RatingsInput(overall=4)),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()
    result = runner.invoke(cli, ["list", "--type", "pour_over", "--rating-min", "4"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 1


def test_filter_rating_no_matches_friendly_message(runner, db_path):
    """AC-41: no brews match rating filter -> friendly message, exit 0."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 2)
    result = runner.invoke(cli, ["list", "--rating-min", "4"])
    assert result.exit_code == 0
    assert "No brews match" in result.output


def test_filter_rating_excludes_brews_without_rating(runner, db_path):
    """AC-2: brews with no overall rating are excluded by --rating-min."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")  # no rating
    result = runner.invoke(cli, ["list", "--rating-min", "1"])
    # Brew with no rating should not show up
    lines = result.output.strip().split("\n")
    data_lines = [ln for ln in lines if "2026-" in ln]
    assert len(data_lines) == 0


# ---------------------------------------------------------------------------
# AC-38: Overall Rating column in list
# ---------------------------------------------------------------------------

def test_filter_overall_rating_column_shows_value(runner, db_path):
    """AC-38: Overall Rating column shows the rating value when set."""
    _insert_with_rating(db_path, "2026-02-01T08:00:00Z", 4)
    result = runner.invoke(cli, ["list"])
    assert "4" in result.output
    assert "Overall Rating" in result.output
