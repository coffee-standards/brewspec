"""
Shared fixtures for BrewLog CLI tests.
"""

import pytest
from click.testing import CliRunner

from brewlog import db as db_module


@pytest.fixture
def runner():
    """Click CliRunner with isolated filesystem support."""
    return CliRunner()


@pytest.fixture
def tmp_db(tmp_path):
    """Return a fresh sqlite3.Connection to a tmp db file."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    yield conn
    conn.close()


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a Path for a fresh test database (not yet connected)."""
    return tmp_path / "test.db"


@pytest.fixture
def minimal_brew_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
    }


@pytest.fixture
def full_brew_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
        "method": "Hario V60",
        "water_temp_c": 96.0,
        "grind": "medium_fine",
        "duration_s": 180,
        "notes": "Bright acidity",
        "coffee": {
            "roast_date": "2026-01-20",
            "type": "single_origin",
            "origin": ["Ethiopia"],
            "varietal": "Heirloom",
            "process": "Washed",
        },
        "water": {"ppm": 150.0},
        "result": {
            "tds": 1.38,
            "ey": 20.5,
        },
    }


@pytest.fixture
def env_with_tmp_db(tmp_path, monkeypatch):
    """
    Monkeypatch DB_PATH so CLI commands use a temp database.
    Returns the tmp db path.
    """
    import brewlog.db as db_mod
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)
    return db_file
