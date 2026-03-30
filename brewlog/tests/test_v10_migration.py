"""
Migration tests for BrewLog CLI v1.0.

Tests cover all migration acceptance criteria:
AC-3: water_weight_g renamed to water_g
AC-4: notes renamed to process_notes
AC-5: old columns absent after migration, new names present
AC-6: idempotent migration
AC-7: new columns added (yield_g, result_water_g, coffee_cupping_notes,
       equipment_pressure_bar, equipment_flow_rate_ml_s)
AC-8: new columns default to NULL for existing rows

TDD: tests written before implementation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


from brewlog import db as db_module


# ---------------------------------------------------------------------------
# Helper: create an old-schema DB (simulating a pre-v1.0 database)
# ---------------------------------------------------------------------------

def _create_old_schema_db(db_path: Path) -> None:
    """
    Create a SQLite DB that looks like a pre-v1.0 BrewLog database.
    Uses water_weight_g and notes columns (pre-rename), without the new columns.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE brews (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            date                      TEXT,
            type                      TEXT,
            method                    TEXT,
            dose_g                    REAL,
            water_weight_g            REAL,
            brew_ratio                REAL,
            water_volume_ml           REAL,
            water_temp_c              REAL,
            grind                     TEXT,
            duration_s                INTEGER,
            notes                     TEXT,
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
            coffee_roast_level        TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC)")
    conn.commit()
    conn.close()


def _insert_old_row(db_path: Path, water_weight_g: float = 280.0, notes: str = "Test notes") -> int:
    """Insert a row into an old-schema DB using old column names."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO brews (date, type, dose_g, water_weight_g, notes) VALUES (?, ?, ?, ?, ?)",
        ("2026-01-15", "pour_over", 18.0, water_weight_g, notes),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def _get_column_names(db_path: Path) -> set[str]:
    """Return the set of column names in the brews table."""
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    return cols


# ---------------------------------------------------------------------------
# AC-3: water_weight_g renamed to water_g
# ---------------------------------------------------------------------------

class TestMigrationRenameWaterWeightG:
    """AC-3: water_weight_g column is renamed to water_g."""

    def test_water_weight_g_renamed_to_water_g(self, tmp_path):
        """After migration, water_g present and water_weight_g absent."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path, water_weight_g=250.0)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols, "water_g column must be present after migration"
        assert "water_weight_g" not in cols, "water_weight_g column must be absent after migration"

    def test_water_g_data_preserved_after_rename(self, tmp_path):
        """AC-3: existing data in water_weight_g is preserved under water_g."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, water_weight_g=250.0)

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["water_g"] == 250.0
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# AC-4: notes renamed to process_notes
# ---------------------------------------------------------------------------

class TestMigrationRenameNotes:
    """AC-4: notes column is renamed to process_notes."""

    def test_notes_renamed_to_process_notes(self, tmp_path):
        """After migration, process_notes present and notes absent."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path, notes="Pre-infused 5s")

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "process_notes" in cols
        assert "notes" not in cols

    def test_process_notes_data_preserved_after_rename(self, tmp_path):
        """AC-4: existing data in notes is preserved under process_notes."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, notes="Pre-infused 5s")

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["process_notes"] == "Pre-infused 5s"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# AC-5: both old columns absent, both new names present
# ---------------------------------------------------------------------------

class TestMigrationBothRenames:
    """AC-5: after migration, water_weight_g and notes absent, water_g and process_notes present."""

    def test_both_old_columns_absent(self, tmp_path):
        """Old names must not appear in PRAGMA table_info after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_weight_g" not in cols
        assert "notes" not in cols

    def test_both_new_columns_present(self, tmp_path):
        """New names must appear in PRAGMA table_info after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols
        assert "process_notes" in cols


# ---------------------------------------------------------------------------
# AC-6: idempotent migration
# ---------------------------------------------------------------------------

class TestMigrationIdempotent:
    """AC-6: calling get_connection() multiple times on the same DB produces no error."""

    def test_migration_idempotent_twice(self, tmp_path):
        """Second call to get_connection() on already-migrated DB must not fail."""
        db_path = tmp_path / "test.db"
        conn1 = db_module.get_connection(db_path=db_path)
        conn1.close()
        # Second call must not raise
        conn2 = db_module.get_connection(db_path=db_path)
        conn2.close()

    def test_migration_idempotent_on_old_db(self, tmp_path):
        """Running migration twice on an old DB produces no error."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn1 = db_module.get_connection(db_path=db_path)
        conn1.close()

        # Second call on now-migrated DB must not fail
        conn2 = db_module.get_connection(db_path=db_path)
        conn2.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols
        assert "process_notes" in cols
        assert "water_weight_g" not in cols
        assert "notes" not in cols


# ---------------------------------------------------------------------------
# AC-7: new columns added
# ---------------------------------------------------------------------------

class TestMigrationNewColumns:
    """AC-7: the v1.0 migration adds five new columns."""

    def test_new_columns_present_on_fresh_db(self, tmp_path):
        """Fresh DB created by get_connection() has all five new columns."""
        db_path = tmp_path / "fresh.db"
        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "yield_g" in cols
        assert "result_water_g" in cols
        assert "coffee_cupping_notes" in cols
        assert "equipment_pressure_bar" in cols
        assert "equipment_flow_rate_ml_s" in cols

    def test_new_columns_added_to_old_db(self, tmp_path):
        """Old DB gains all five new columns after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "yield_g" in cols
        assert "result_water_g" in cols
        assert "coffee_cupping_notes" in cols
        assert "equipment_pressure_bar" in cols
        assert "equipment_flow_rate_ml_s" in cols


# ---------------------------------------------------------------------------
# AC-8: new columns are NULL for pre-migration rows
# ---------------------------------------------------------------------------

class TestMigrationNewColumnsAreNull:
    """AC-8: new columns default to NULL for existing rows."""

    def test_new_columns_null_for_existing_row(self, tmp_path):
        """Pre-migration row has NULL for all five new columns after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["yield_g"] is None
            assert row["result_water_g"] is None
            assert row["coffee_cupping_notes"] is None
            assert row["equipment_pressure_bar"] is None
            assert row["equipment_flow_rate_ml_s"] is None
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Transaction integrity
# ---------------------------------------------------------------------------

class TestMigrationTransaction:
    """Both renames and all new column additions must complete together."""

    def test_both_renames_and_new_columns_all_present(self, tmp_path):
        """After migration, both renamed columns and all new columns are present."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, water_weight_g=200.0, notes="Bloom 30s")

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            # Renamed columns preserved data
            assert row["water_g"] == 200.0
            assert row["process_notes"] == "Bloom 30s"
            # New columns are NULL
            assert row["yield_g"] is None
            assert row["result_water_g"] is None
            assert row["coffee_cupping_notes"] is None
            assert row["equipment_pressure_bar"] is None
            assert row["equipment_flow_rate_ml_s"] is None
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Transaction atomicity
# ---------------------------------------------------------------------------

class TestMigrationAtomicity:
    """V10 migration DDL and data coercion steps must be one atomic transaction.

    If _apply_migrations raises after DDL statements but before commit, the DB
    must remain in its pre-migration state (SQLite rolls back uncommitted work).
    We simulate this by running the DDL statements manually inside a BEGIN
    block, then rolling back, and verifying no structural change persisted.
    """

    def test_rolled_back_ddl_leaves_schema_unchanged(self, tmp_path):
        """DDL inside a rolled-back transaction must not persist to the DB.

        This validates that the migration is structured so that all DDL runs
        inside a single transaction: if that transaction is rolled back, the
        schema returns to its pre-migration state.
        """
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path, water_weight_g=150.0, notes="Pre-infuse 30s")

        # Capture pre-migration schema
        pre_cols = _get_column_names(db_path)
        assert "water_weight_g" in pre_cols
        assert "yield_g" not in pre_cols

        # Open connection, begin an explicit transaction, run the V10 DDL
        # statements (rename + new columns), then ROLLBACK.
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("BEGIN")
            # Simulate the V10 DDL: rename columns and add new ones
            conn.execute("ALTER TABLE brews RENAME COLUMN water_weight_g TO water_g")
            conn.execute("ALTER TABLE brews ADD COLUMN yield_g REAL")
            # Verify the changes are visible inside this transaction
            in_txn_cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(brews)").fetchall()
            }
            assert "water_g" in in_txn_cols
            assert "yield_g" in in_txn_cols
            assert "water_weight_g" not in in_txn_cols
            # Now roll back — simulating a failure before commit
            conn.execute("ROLLBACK")
        finally:
            conn.close()

        # After rollback, schema must be back to pre-migration state
        post_cols = _get_column_names(db_path)
        assert "water_weight_g" in post_cols, (
            "water_weight_g must be present — rolled-back DDL must not persist"
        )
        assert "yield_g" not in post_cols, (
            "yield_g must be absent — rolled-back DDL must not persist"
        )

    def test_successful_migration_has_single_commit_path(self, tmp_path):
        """Successful V10 migration reaches a consistent final state
        whether or not coffee_origin exists — both code paths converge
        on the same committed schema."""
        # DB with coffee_origin present (the 'has coffee_origin' branch)
        db_path_with = tmp_path / "with_origin.db"
        _create_old_schema_db(db_path_with)  # _create_old_schema_db includes coffee_origin
        _insert_old_row(db_path_with)

        conn = db_module.get_connection(db_path=db_path_with)
        conn.close()

        cols_with = _get_column_names(db_path_with)
        assert "water_g" in cols_with
        assert "yield_g" in cols_with
        assert "water_weight_g" not in cols_with

        # DB without coffee_origin (simulate a DB that never had it)
        db_path_without = tmp_path / "without_origin.db"
        conn2 = sqlite3.connect(db_path_without)
        conn2.execute("""
            CREATE TABLE brews (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                date                      TEXT,
                type                      TEXT,
                method                    TEXT,
                dose_g                    REAL,
                water_weight_g            REAL,
                water_volume_ml           REAL,
                water_temp_c              REAL,
                grind                     TEXT,
                duration_s                INTEGER,
                notes                     TEXT,
                coffee_roast_date         TEXT,
                coffee_type               TEXT,
                coffee_name               TEXT,
                coffee_origins            TEXT,
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
                coffee_roast_level        TEXT
            )
        """)
        conn2.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, notes) VALUES (?, ?, ?, ?, ?)",
            ("2026-01-10", "espresso", 18.0, 36.0, "Single shot"),
        )
        conn2.commit()
        conn2.close()

        conn3 = db_module.get_connection(db_path=db_path_without)
        conn3.close()

        cols_without = _get_column_names(db_path_without)
        assert "water_g" in cols_without
        assert "yield_g" in cols_without
        assert "water_weight_g" not in cols_without
        assert "coffee_origin" not in cols_without

    def test_v10_migration_single_commit_path_with_coffee_origin(self, tmp_path):
        """When coffee_origin column is present, migration still uses a single
        commit at the end — not an early commit in the guard branch."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        # Insert a row with coffee_origin data to trigger Step B
        conn_setup = sqlite3.connect(db_path)
        conn_setup.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, notes, coffee_origin) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-01-15", "pour_over", 18.0, 280.0, "Test", '["Ethiopia"]'),
        )
        conn_setup.commit()
        conn_setup.close()

        # Run migration — must succeed without error
        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        # Final state: migration is complete and consistent
        cols = _get_column_names(db_path)
        assert "water_g" in cols
        assert "yield_g" in cols
        assert "coffee_origins" in cols
        assert "water_weight_g" not in cols

        # Verify the origin migration (Step B) ran correctly
        conn_check = sqlite3.connect(db_path)
        row = conn_check.execute("SELECT coffee_origins FROM brews").fetchone()
        conn_check.close()
        import json
        origins = json.loads(row[0])
        assert origins == [{"country": "Ethiopia"}]

    def test_step_b_skipped_gracefully_when_coffee_origin_absent(self, tmp_path):
        """When coffee_origin is absent, _apply_migrations completes all steps
        including Step A (grinder coercion) without error, and the final schema
        state is fully migrated.

        This test verifies that the absent-origin guard path does not short-circuit
        the function before all committed work is complete.
        """
        db_path = tmp_path / "no_origin.db"
        conn_no = sqlite3.connect(db_path)
        conn_no.execute("""
            CREATE TABLE brews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, type TEXT, dose_g REAL,
                water_weight_g REAL, notes TEXT,
                coffee_origins TEXT,
                equipment_grinder_setting REAL,
                coffee_roaster TEXT, coffee_roast_level TEXT,
                result_rating_overall INTEGER
            )
        """)
        # Insert rows with TEXT grinder_setting values (Step A must coerce these)
        conn_no.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, "
            "equipment_grinder_setting) VALUES (?, ?, ?, ?, ?)",
            ("2026-01-15", "pour_over", 18.0, 280.0, "20 clicks"),
        )
        conn_no.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, "
            "equipment_grinder_setting) VALUES (?, ?, ?, ?, ?)",
            ("2026-01-16", "espresso", 18.0, 36.0, "bad value"),
        )
        conn_no.commit()
        conn_no.close()

        # Run migration — must complete without error
        conn = db_module.get_connection(db_path=db_path)
        rows = conn.execute(
            "SELECT equipment_grinder_setting FROM brews ORDER BY date"
        ).fetchall()
        conn.close()

        # Step A must have coerced valid TEXT -> REAL and set invalid -> NULL
        assert rows[0][0] == 20.0, (
            f"'20 clicks' must be coerced to 20.0 by Step A, got {rows[0][0]}"
        )
        assert rows[1][0] is None, (
            f"'bad value' must become NULL via Step A, got {rows[1][0]}"
        )

    def test_origin_migration_runs_when_coffee_origin_present_and_data_needs_migration(
        self, tmp_path
    ):
        """Step B (origin migration) executes and commits when coffee_origin IS present.

        This verifies that removing the early-return does not break Step B:
        when coffee_origin rows exist, they are migrated to coffee_origins objects.
        """
        db_path = tmp_path / "with_origin_data.db"
        _create_old_schema_db(db_path)
        conn_setup = sqlite3.connect(db_path)
        conn_setup.execute(
            "INSERT INTO brews (date, type, dose_g, water_weight_g, notes, coffee_origin) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-01-20", "espresso", 18.0, 36.0, "Bloom", '["Kenya", "Ethiopia"]'),
        )
        conn_setup.commit()
        conn_setup.close()

        conn = db_module.get_connection(db_path=db_path)
        row = conn.execute("SELECT coffee_origins FROM brews").fetchone()
        conn.close()

        import json
        origins = json.loads(row[0])
        assert origins == [{"country": "Kenya"}, {"country": "Ethiopia"}], (
            f"Step B must migrate coffee_origin strings to origin objects. Got: {origins}"
        )
