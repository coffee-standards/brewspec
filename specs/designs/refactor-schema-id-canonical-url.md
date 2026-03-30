# Design: Correct Schema $id to Canonical URL

**Feature:** refactor-schema-id-canonical-url
**Author:** architect
**Created:** 2026-03-31
**Input:** reviews/2026-03-31-system-steward-health-report.yaml (finding DRIFT-1)
**Baseline:** n/a — maintenance refactor
**Status:** Ready for Dev

---

## Overview

The architecture principle at `specs/arch/principles.md` (section "Site") states: "The canonical schema URL lives at brewspec.coffee/schema/. The JSON Schema `$id` references this URL." All three copies of the schema currently set `$id` to the raw GitHub CDN URL (`https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json`). The canonical URL — `https://brewspec.coffee/schema/v1.0.json` — is already served by the site at `site/public/schema/v1.0.json`. This refactor updates `$id` in all three schema copies to match the principle and adds tests that lock the value down.

No schema fields, constraints, or validation behaviour change. This is a single-field metadata correction replicated across three files.

---

## 1. Changes Required

### 1.1 Root schema — `brewspec.schema.json`

**Before:**
```json
"$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json"
```

**After:**
```json
"$id": "https://brewspec.coffee/schema/v1.0.json"
```

This is the authoritative source. The two copies below must always match it.

### 1.2 Site copy — `site/public/schema/v1.0.json`

Same one-line change as 1.1. This file is a verbatim copy of `brewspec.schema.json`. The dev must apply the identical `$id` edit here.

**Before:**
```json
"$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json"
```

**After:**
```json
"$id": "https://brewspec.coffee/schema/v1.0.json"
```

### 1.3 Brewlog bundled schema — `brewlog/src/brewlog/brewspec.schema.json`

Same one-line change. This file is the copy loaded at runtime by `brewlog/src/brewlog/schema.py` via `importlib.resources`. The `$id` value is metadata only — `Draft202012Validator` does not fetch it and no network calls are made — but it must stay in sync with the authoritative copy for correctness and clarity.

**Before:**
```json
"$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json"
```

**After:**
```json
"$id": "https://brewspec.coffee/schema/v1.0.json"
```

### 1.4 Sync process for future version bumps

The three schema copies (`brewspec.schema.json`, `site/public/schema/v1.0.json`, `brewlog/src/brewlog/brewspec.schema.json`) must stay identical. The existing pattern is manual copy-on-release. The tests added in section 7 verify that all three `$id` values match the canonical URL and that all three files are byte-for-byte identical — this will catch any future drift at CI time before it ships.

When a future version (v1.1, v2.0) is released:
- The new canonical URL will be `https://brewspec.coffee/schema/vX.Y.json`
- A new site copy is placed at `site/public/schema/vX.Y.json`
- The brewlog bundled copy is updated to the new version's content
- The `$id` in all three files is updated to the new versioned URL
- The test `CANONICAL_SCHEMA_ID` constant is updated to match

---

## 2. Data Models

Not applicable. No Pydantic models, SQLite schema, or CLI commands are affected. `schema.py` requires no changes — it loads the schema file by path, and `$id` is transparent to the validator.

---

## 3. CLI Interface

Not applicable.

---

## 4. Architecture Decision Records

No new ADR required. The decision is already encoded in `specs/arch/principles.md` (section "Site") and the target URL is recorded in the manifest task under `url_decision`. The only question was whether the site already served the file at the target path — it does (`site/public/schema/v1.0.json` exists). No trade-off to record.

---

## 5. Public Spec Document

Not applicable. This refactor does not change any schema field, constraint, or behaviour. The spec document (`brewspec-v1.0.md`) requires no update.

---

## 6. File Manifest

| File | Operation | Notes |
|------|-----------|-------|
| `brewspec.schema.json` | Modify | Change `$id` value — line 3 only |
| `site/public/schema/v1.0.json` | Modify | Change `$id` value — line 3 only |
| `brewlog/src/brewlog/brewspec.schema.json` | Modify | Change `$id` value — line 3 only |
| `tests/test_brewspec_schema.py` | Modify | Add `test_schema_id_is_canonical_url` (see section 7) |
| `brewlog/tests/test_brewspec_schema.py` | Modify | Add `test_schema_id_is_canonical_url` (see section 7) |

Five files total. Three are single-line edits. Two receive one new test function each.

---

## 7. Test Strategy

### AC-1: `$id` in root schema equals the canonical URL

**File:** `tests/test_brewspec_schema.py`

Add one test function. The `schema` fixture already loads `brewspec.schema.json`; no new fixture is needed.

```python
CANONICAL_SCHEMA_ID = "https://brewspec.coffee/schema/v1.0.json"

def test_schema_id_is_canonical_url(schema):
    """$id must reference the canonical brewspec.coffee URL, not the GitHub CDN URL."""
    assert schema["$id"] == CANONICAL_SCHEMA_ID
```

| Test | Input | Expected |
|------|-------|----------|
| Correct `$id` | `schema["$id"]` after the fix | equals `"https://brewspec.coffee/schema/v1.0.json"` |
| Wrong `$id` (regression) | `schema["$id"]` if reverted to GitHub CDN URL | assertion fails — catches drift |

### AC-2: `$id` in brewlog bundled schema equals the canonical URL

**File:** `brewlog/tests/test_brewspec_schema.py`

Add one test function. The `schema` fixture already loads `brewlog/src/brewlog/brewspec.schema.json`.

```python
CANONICAL_SCHEMA_ID = "https://brewspec.coffee/schema/v1.0.json"

def test_schema_id_is_canonical_url(schema):
    """Bundled schema $id must reference the canonical brewspec.coffee URL."""
    assert schema["$id"] == CANONICAL_SCHEMA_ID
```

| Test | Input | Expected |
|------|-------|----------|
| Correct `$id` | `schema["$id"]` after the fix | equals `"https://brewspec.coffee/schema/v1.0.json"` |
| Bundled copy not updated (regression) | `schema["$id"]` if brewlog copy missed | assertion fails — catches drift |

### AC-3: All three schema copies are identical

**File:** `tests/test_brewspec_schema.py`

Add one test function that reads all three files and asserts they are byte-for-byte equal. This is the cheapest guard against the copies diverging again in future.

```python
def test_schema_copies_are_identical():
    """The root schema, site copy, and brewlog bundled copy must be identical."""
    root = REPO_ROOT / "brewspec.schema.json"
    site_copy = REPO_ROOT / "site" / "public" / "schema" / "v1.0.json"
    brewlog_copy = REPO_ROOT / "brewlog" / "src" / "brewlog" / "brewspec.schema.json"

    root_text = root.read_text(encoding="utf-8")
    assert site_copy.read_text(encoding="utf-8") == root_text, (
        "site/public/schema/v1.0.json differs from brewspec.schema.json"
    )
    assert brewlog_copy.read_text(encoding="utf-8") == root_text, (
        "brewlog/src/brewlog/brewspec.schema.json differs from brewspec.schema.json"
    )
```

| Test | Input | Expected |
|------|-------|----------|
| All three in sync | files identical after the fix | passes |
| Site copy not updated | site copy still has old `$id` | fails with path-specific message |
| Brewlog copy not updated | brewlog copy still has old `$id` | fails with path-specific message |

Note: `REPO_ROOT` is already defined in `tests/test_brewspec_schema.py` as `Path(__file__).parent.parent`. Use it directly.

---

## 8. Security Considerations

- **Input validation**: No user input involved. The `$id` field is schema metadata read at startup; it is not derived from user data.
- **File I/O**: The three files are read-only at runtime (loaded once at import in `schema.py`). No new file write paths are introduced.
- **Network**: `Draft202012Validator` does not resolve `$id` as a network URL. Changing the value to a live domain URL does not introduce any network calls or SSRF surface.
- **Data integrity**: The new identity test in AC-3 provides a CI guard that all three copies remain identical. Drift between copies could cause a user's schema reference to resolve to a different version than the one validating their documents — the test closes this gap.

---

## 9. TDD Implementation Order

1. Write the three failing tests (`test_schema_id_is_canonical_url` in both test files, `test_schema_copies_are_identical` in the root test file) — all three will fail against the current GitHub CDN `$id`.
2. Update `$id` in `brewspec.schema.json` — `test_schema_id_is_canonical_url` in the root suite passes; `test_schema_copies_are_identical` still fails (site and brewlog copies not yet updated).
3. Update `$id` in `site/public/schema/v1.0.json` — `test_schema_copies_are_identical` site assertion passes.
4. Update `$id` in `brewlog/src/brewlog/brewspec.schema.json` — all tests pass, including `test_schema_id_is_canonical_url` in the brewlog suite.
5. Run full root test suite: `pytest tests/` — confirm all pass.
6. Run brewlog test suite: `cd brewlog && pytest tests/` — confirm all pass.
7. Run `ruff check .` from `brewlog/` — confirm no lint errors (no code changes, but run as a habit before handoff).
