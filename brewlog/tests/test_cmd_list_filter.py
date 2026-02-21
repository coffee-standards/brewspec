"""
CLI integration tests for `brewlog list` filtering.
Tests map to AC-18 through AC-24 in brewlog-cli-v0.2 spec.
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


def _insert(db_path, date, brew_type, rating=None, method=None):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date=date,
            type=brew_type,
            dose_g=18.0,
            water_weight_g=280.0,
            rating=rating,
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
# AC-19: --rating filter
# ---------------------------------------------------------------------------

def test_filter_rating_returns_matching(runner, db_path):
    """AC-19: --rating 4 returns only brews with rating 4."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over", rating=4)
    _insert(db_path, "2026-02-02T08:00:00Z", "pour_over", rating=5)
    result = runner.invoke(cli, ["list", "--rating", "4"])
    assert result.exit_code == 0
    # rating 4 row must be present (check for the '4' in the Rating column)
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-" in l]
    assert len(data_lines) == 1


def test_filter_rating_excludes_others(runner, db_path):
    """AC-19: --rating 4 excludes brews with rating 5."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over", rating=4)
    _insert(db_path, "2026-02-02T08:00:00Z", "pour_over", rating=5)
    result = runner.invoke(cli, ["list", "--rating", "4"])
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-02-02" in l]
    assert len(data_lines) == 0, "Rating 5 brew should not appear"


def test_filter_rating_invalid_zero(runner):
    """AC-19: --rating 0 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating", "0"])
    assert result.exit_code == 1


def test_filter_rating_invalid_six(runner):
    """AC-19: --rating 6 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating", "6"])
    assert result.exit_code == 1


def test_filter_rating_invalid_negative(runner):
    """AC-19: --rating -1 -> exit 1."""
    result = runner.invoke(cli, ["list", "--rating", "-1"])
    assert result.exit_code == 1


def test_filter_rating_valid_range(runner, db_path):
    """AC-19: ratings 1-5 are all valid."""
    for i, rating in enumerate(range(1, 6), start=1):
        _insert(db_path, f"2026-02-{i:02d}T08:00:00Z", "pour_over", rating=rating)
    for rating in range(1, 6):
        result = runner.invoke(cli, ["list", "--rating", str(rating)])
        assert result.exit_code == 0, f"--rating {rating} should be valid"


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
    data_lines = [l for l in lines if "2026-" in l]
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

def test_filter_type_and_rating_combined(runner, db_path):
    """AC-21: --type + --rating applied together as AND."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over", rating=4)
    _insert(db_path, "2026-02-02T08:00:00Z", "espresso", rating=4)
    _insert(db_path, "2026-02-03T08:00:00Z", "pour_over", rating=5)
    result = runner.invoke(cli, ["list", "--type", "pour_over", "--rating", "4"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-" in l]
    assert len(data_lines) == 1
    assert "2026-02-01" in result.output


def test_filter_all_three_combined(runner, db_path):
    """AC-21: --type + --rating + --since all applied as AND."""
    _insert(db_path, "2026-01-01T08:00:00Z", "pour_over", rating=4)  # too old
    _insert(db_path, "2026-02-01T08:00:00Z", "espresso", rating=4)   # wrong type
    _insert(db_path, "2026-02-02T08:00:00Z", "pour_over", rating=5)  # wrong rating
    _insert(db_path, "2026-02-03T08:00:00Z", "pour_over", rating=4)  # matches all
    result = runner.invoke(cli, [
        "list", "--type", "pour_over", "--rating", "4", "--since", "2026-02-01"
    ])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-" in l]
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
        _insert(db_path, f"2026-02-{i:02d}T08:00:00Z", "pour_over", rating=4)
    result = runner.invoke(cli, ["list", "--type", "pour_over", "--limit", "3"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-" in l]
    assert len(data_lines) == 3


def test_filter_with_all(runner, db_path):
    """AC-23: --all returns all matching brews, ignoring limit."""
    for i in range(1, 26):
        _insert(db_path, f"2026-01-{i:02d}T08:00:00Z", "espresso")
    result = runner.invoke(cli, ["list", "--type", "espresso", "--all"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    data_lines = [l for l in lines if "2026-" in l]
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
    data_lines = [l for l in lines if "2026-" in l]
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
    data_lines = [l for l in lines if "2026-" in l]
    assert len(data_lines) == 20


def test_no_filters_no_friendly_message(runner, db_path):
    """AC-24: without filter flags and brews present, no 'No brews match' message."""
    _insert(db_path, "2026-02-01T08:00:00Z", "pour_over")
    result = runner.invoke(cli, ["list"])
    assert "No brews match" not in result.output
