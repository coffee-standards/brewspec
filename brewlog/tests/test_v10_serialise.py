"""
Serialisation tests for BrewLog CLI v1.0.

Tests cover acceptance criteria for serialise.py and insert_brew_dict:
AC-1:  BREWSPEC_VERSION is "1.0"
AC-40: row_to_brew_dict reads water_g (not water_weight_g)
AC-41: row_to_brew_dict reads process_notes (not notes)
AC-42: row_to_brew_dict includes brew-level yield_g when present
AC-43: row_to_brew_dict includes result_water_g as result.water_g
AC-44: row_to_brew_dict includes coffee_cupping_notes as coffee.cupping_notes
AC-45: row_to_brew_dict includes origin cupping_notes from coffee_origins JSON
AC-46: row_to_brew_dict includes equipment_pressure_bar and equipment_flow_rate_ml_s
AC-50: insert_brew_dict reads water_g (not water_weight_g)
AC-51: insert_brew_dict reads process_notes (not notes)
AC-52: insert_brew_dict reads brew-level yield_g
AC-53: insert_brew_dict reads result.water_g -> result_water_g
AC-54: insert_brew_dict reads coffee.cupping_notes -> coffee_cupping_notes
AC-55: insert_brew_dict reads first origin cupping_notes into coffee_origins JSON
AC-56: insert_brew_dict reads equipment.pressure_bar and flow_rate_ml_s

TDD: tests written before implementation.
"""

from __future__ import annotations

import json


from brewlog import db as db_module
from brewlog import serialise
from brewlog.serialise import BREWSPEC_VERSION


# ---------------------------------------------------------------------------
# AC-1: BREWSPEC_VERSION is "1.0"
# ---------------------------------------------------------------------------

class TestBrewspecVersion:
    """AC-1: BREWSPEC_VERSION constant is "1.0"."""

    def test_brewspec_version_is_1_0(self):
        """BREWSPEC_VERSION must be '1.0'."""
        assert BREWSPEC_VERSION == "1.0"

    def test_exported_document_has_version_1_0(self, tmp_db):
        """rows_to_brewspec_document includes brewspec_version: "1.0"."""
        db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
        }, tmp_db)
        tmp_db.commit()
        rows = db_module.get_all_brews(tmp_db)
        doc = serialise.rows_to_brewspec_document(rows)
        assert doc["brewspec_version"] == "1.0"


# ---------------------------------------------------------------------------
# Helper: build a v1.0 dict and return DB row
# ---------------------------------------------------------------------------

def _insert_v10_dict(tmp_db, extra: dict = None) -> object:
    """Insert a v1.0 brew dict and return the resulting row."""
    brew_dict = {
        "date": "2026-03-30",
        "type": "espresso",
        "dose_g": 18.0,
        "water_g": 36.0,
    }
    if extra:
        brew_dict.update(extra)
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    return db_module.get_brew(brew_id, tmp_db)


# ---------------------------------------------------------------------------
# AC-40: row_to_brew_dict reads water_g
# ---------------------------------------------------------------------------

class TestRowToBrewDictWaterG:
    """AC-40: row_to_brew_dict emits water_g (not water_weight_g)."""

    def test_water_g_in_output(self, tmp_db):
        """Output dict has water_g key."""
        row = _insert_v10_dict(tmp_db)
        result = serialise.row_to_brew_dict(row)
        assert "water_g" in result
        assert result["water_g"] == 36.0

    def test_water_weight_g_not_in_output(self, tmp_db):
        """Output dict must NOT have water_weight_g key."""
        row = _insert_v10_dict(tmp_db)
        result = serialise.row_to_brew_dict(row)
        assert "water_weight_g" not in result


# ---------------------------------------------------------------------------
# AC-41: row_to_brew_dict reads process_notes
# ---------------------------------------------------------------------------

class TestRowToBrewDictProcessNotes:
    """AC-41: row_to_brew_dict emits process_notes (not notes)."""

    def test_process_notes_in_output(self, tmp_db):
        """Output dict has process_notes key when set."""
        row = _insert_v10_dict(tmp_db, {"process_notes": "Pre-infused 5s"})
        result = serialise.row_to_brew_dict(row)
        assert "process_notes" in result
        assert result["process_notes"] == "Pre-infused 5s"

    def test_notes_not_in_output(self, tmp_db):
        """Output dict must NOT have notes key."""
        row = _insert_v10_dict(tmp_db, {"process_notes": "Pre-infused 5s"})
        result = serialise.row_to_brew_dict(row)
        assert "notes" not in result

    def test_process_notes_absent_when_null(self, tmp_db):
        """process_notes absent from output when NULL."""
        row = _insert_v10_dict(tmp_db)
        result = serialise.row_to_brew_dict(row)
        assert "process_notes" not in result


# ---------------------------------------------------------------------------
# AC-42: row_to_brew_dict includes brew-level yield_g
# ---------------------------------------------------------------------------

class TestRowToBrewDictYieldG:
    """AC-42: row_to_brew_dict includes brew-level yield_g when present."""

    def test_brew_yield_g_in_output(self, tmp_db):
        """Brew-level yield_g appears in output dict when set."""
        row = _insert_v10_dict(tmp_db, {"yield_g": 36.0})
        result = serialise.row_to_brew_dict(row)
        assert result.get("yield_g") == 36.0

    def test_brew_yield_g_absent_when_null(self, tmp_db):
        """Brew-level yield_g absent from output when NULL."""
        row = _insert_v10_dict(tmp_db)
        result = serialise.row_to_brew_dict(row)
        assert "yield_g" not in result


# ---------------------------------------------------------------------------
# AC-43: row_to_brew_dict includes result_water_g as result.water_g
# ---------------------------------------------------------------------------

class TestRowToBrewDictResultWaterG:
    """AC-43: result_water_g column maps to result.water_g in output."""

    def test_result_water_g_in_result_sub_object(self, tmp_db):
        """result.water_g present when result_water_g set."""
        row = _insert_v10_dict(tmp_db, {
            "result": {"yield_g": 36.0, "water_g": 35.5},
        })
        result = serialise.row_to_brew_dict(row)
        assert "result" in result
        assert result["result"]["water_g"] == 35.5

    def test_result_water_g_absent_when_null(self, tmp_db):
        """result.water_g absent from result when result_water_g is NULL."""
        row = _insert_v10_dict(tmp_db, {"result": {"yield_g": 36.0}})
        result = serialise.row_to_brew_dict(row)
        if "result" in result:
            assert "water_g" not in result["result"]


# ---------------------------------------------------------------------------
# AC-44: row_to_brew_dict includes coffee.cupping_notes
# ---------------------------------------------------------------------------

class TestRowToBrewDictCoffeeCuppingNotes:
    """AC-44: coffee_cupping_notes maps to coffee.cupping_notes in output."""

    def test_coffee_cupping_notes_in_coffee_sub_object(self, tmp_db):
        """coffee.cupping_notes present when coffee_cupping_notes set."""
        row = _insert_v10_dict(tmp_db, {
            "coffee": {
                "name": "Colombia Huila",
                "cupping_notes": "Dark chocolate, citrus",
            },
        })
        result = serialise.row_to_brew_dict(row)
        assert "coffee" in result
        assert result["coffee"]["cupping_notes"] == "Dark chocolate, citrus"

    def test_coffee_cupping_notes_absent_when_null(self, tmp_db):
        """coffee.cupping_notes absent from coffee when NULL."""
        row = _insert_v10_dict(tmp_db, {"coffee": {"name": "Colombia"}})
        result = serialise.row_to_brew_dict(row)
        if "coffee" in result:
            assert "cupping_notes" not in result["coffee"]


# ---------------------------------------------------------------------------
# AC-45: origin cupping_notes embedded in coffee_origins JSON
# ---------------------------------------------------------------------------

class TestRowToBrewDictOriginCuppingNotes:
    """AC-45: origin cupping_notes flows through coffee_origins JSON."""

    def test_origin_cupping_notes_in_origins_json(self, tmp_db):
        """When first origin has cupping_notes, it appears in exported origins."""
        row = _insert_v10_dict(tmp_db, {
            "coffee": {
                "origins": [
                    {"country": "Colombia", "cupping_notes": "Bright malic acidity"},
                ],
            },
        })
        result = serialise.row_to_brew_dict(row)
        assert "coffee" in result
        assert "origins" in result["coffee"]
        assert result["coffee"]["origins"][0]["cupping_notes"] == "Bright malic acidity"

    def test_origin_cupping_notes_absent_when_not_set(self, tmp_db):
        """When origin has no cupping_notes, key absent in exported origins."""
        row = _insert_v10_dict(tmp_db, {
            "coffee": {
                "origins": [{"country": "Colombia"}],
            },
        })
        result = serialise.row_to_brew_dict(row)
        if "coffee" in result and "origins" in result["coffee"]:
            assert "cupping_notes" not in result["coffee"]["origins"][0]


# ---------------------------------------------------------------------------
# AC-46: row_to_brew_dict includes equipment_pressure_bar and flow_rate_ml_s
# ---------------------------------------------------------------------------

class TestRowToBrewDictEquipmentFields:
    """AC-46: equipment_pressure_bar and equipment_flow_rate_ml_s map to equipment sub-object."""

    def test_pressure_bar_in_equipment(self, tmp_db):
        """equipment.pressure_bar present when equipment_pressure_bar set."""
        row = _insert_v10_dict(tmp_db, {
            "equipment": {"grinder": "Niche Zero", "pressure_bar": 9.0},
        })
        result = serialise.row_to_brew_dict(row)
        assert "equipment" in result
        assert result["equipment"]["pressure_bar"] == 9.0

    def test_flow_rate_in_equipment(self, tmp_db):
        """equipment.flow_rate_ml_s present when equipment_flow_rate_ml_s set."""
        row = _insert_v10_dict(tmp_db, {
            "equipment": {"grinder": "Niche Zero", "flow_rate_ml_s": 1.3},
        })
        result = serialise.row_to_brew_dict(row)
        assert "equipment" in result
        assert result["equipment"]["flow_rate_ml_s"] == 1.3

    def test_pressure_bar_absent_when_null(self, tmp_db):
        """pressure_bar absent from equipment when NULL."""
        row = _insert_v10_dict(tmp_db, {"equipment": {"grinder": "Niche"}})
        result = serialise.row_to_brew_dict(row)
        if "equipment" in result:
            assert "pressure_bar" not in result["equipment"]

    def test_flow_rate_absent_when_null(self, tmp_db):
        """flow_rate_ml_s absent from equipment when NULL."""
        row = _insert_v10_dict(tmp_db, {"equipment": {"grinder": "Niche"}})
        result = serialise.row_to_brew_dict(row)
        if "equipment" in result:
            assert "flow_rate_ml_s" not in result["equipment"]


# ---------------------------------------------------------------------------
# AC-50: insert_brew_dict reads water_g
# ---------------------------------------------------------------------------

class TestInsertBrewDictWaterG:
    """AC-50: insert_brew_dict writes water_g to the water_g DB column."""

    def test_insert_water_g_stored_correctly(self, tmp_db):
        """water_g in brew_dict is written to water_g column."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["water_g"] == 36.0

    def test_insert_water_weight_g_not_written(self, tmp_db):
        """water_weight_g in brew_dict is ignored (not written to water_g)."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_weight_g": 36.0,  # old field — must be ignored
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["water_g"] is None


# ---------------------------------------------------------------------------
# AC-51: insert_brew_dict reads process_notes
# ---------------------------------------------------------------------------

class TestInsertBrewDictProcessNotes:
    """AC-51: insert_brew_dict writes process_notes to process_notes column."""

    def test_insert_process_notes_stored_correctly(self, tmp_db):
        """process_notes in brew_dict is written to process_notes column."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "process_notes": "Rinsed filter first",
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["process_notes"] == "Rinsed filter first"

    def test_insert_notes_field_ignored(self, tmp_db):
        """notes in brew_dict (old field) is not written to process_notes."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "notes": "Old notes field",  # old field — must be ignored
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["process_notes"] is None


# ---------------------------------------------------------------------------
# AC-52: insert_brew_dict reads brew-level yield_g
# ---------------------------------------------------------------------------

class TestInsertBrewDictYieldG:
    """AC-52: insert_brew_dict writes brew-level yield_g to yield_g column."""

    def test_insert_brew_yield_g(self, tmp_db):
        """Brew-level yield_g written to yield_g DB column."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "yield_g": 36.0,
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["yield_g"] == 36.0


# ---------------------------------------------------------------------------
# AC-53: insert_brew_dict reads result.water_g -> result_water_g
# ---------------------------------------------------------------------------

class TestInsertBrewDictResultWaterG:
    """AC-53: result.water_g written to result_water_g column."""

    def test_insert_result_water_g(self, tmp_db):
        """result.water_g written to result_water_g."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "result": {"water_g": 35.5, "yield_g": 36.0},
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["result_water_g"] == 35.5


# ---------------------------------------------------------------------------
# AC-54: insert_brew_dict reads coffee.cupping_notes -> coffee_cupping_notes
# ---------------------------------------------------------------------------

class TestInsertBrewDictCoffeeCuppingNotes:
    """AC-54: coffee.cupping_notes written to coffee_cupping_notes column."""

    def test_insert_coffee_cupping_notes(self, tmp_db):
        """coffee.cupping_notes written to coffee_cupping_notes."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "coffee": {
                "name": "Colombia Huila",
                "cupping_notes": "Dark chocolate, citrus",
            },
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["coffee_cupping_notes"] == "Dark chocolate, citrus"


# ---------------------------------------------------------------------------
# AC-55: insert_brew_dict reads first origin cupping_notes into JSON
# ---------------------------------------------------------------------------

class TestInsertBrewDictOriginCuppingNotes:
    """AC-55: first origin cupping_notes preserved in coffee_origins JSON."""

    def test_insert_origin_cupping_notes_in_json(self, tmp_db):
        """First origin cupping_notes stored inside coffee_origins JSON."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "coffee": {
                "origins": [
                    {"country": "Colombia", "cupping_notes": "Bright malic acidity"},
                ],
            },
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        origins = json.loads(row["coffee_origins"])
        assert origins[0]["cupping_notes"] == "Bright malic acidity"


# ---------------------------------------------------------------------------
# AC-56: insert_brew_dict reads equipment.pressure_bar and flow_rate_ml_s
# ---------------------------------------------------------------------------

class TestInsertBrewDictEquipmentFields:
    """AC-56: equipment.pressure_bar and flow_rate_ml_s written to DB columns."""

    def test_insert_pressure_bar(self, tmp_db):
        """equipment.pressure_bar written to equipment_pressure_bar."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "equipment": {"grinder": "Niche Zero", "pressure_bar": 9.0},
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["equipment_pressure_bar"] == 9.0

    def test_insert_flow_rate_ml_s(self, tmp_db):
        """equipment.flow_rate_ml_s written to equipment_flow_rate_ml_s."""
        brew_id = db_module.insert_brew_dict({
            "date": "2026-03-30",
            "type": "espresso",
            "dose_g": 18.0,
            "water_g": 36.0,
            "equipment": {"grinder": "Niche Zero", "flow_rate_ml_s": 1.3},
        }, tmp_db)
        tmp_db.commit()
        row = db_module.get_brew(brew_id, tmp_db)
        assert row["equipment_flow_rate_ml_s"] == 1.3
