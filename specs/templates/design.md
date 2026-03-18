# Design: [Feature Name]

**Feature:** [manifest task id, e.g. brewspec-v0.4]
**Author:** architect
**Created:** [date]
**Input:** [path to product spec, e.g. specs/products/brewspec-v0.4.md]
**Baseline:** [path to previous design if applicable, e.g. specs/designs/brewspec-v0.3.md]
**Status:** Ready for Dev

---

## Overview

One paragraph describing the scope of this design. What is being built or changed, and why. Reference the product spec and any carry-forward context from previous versions. Flag any significant breaking changes upfront.

---

## 1. Changes Required

The bulk of the design. Break this into numbered subsections — one per logical area of change. Each subsection should be specific enough that the developer can implement from it without guessing.

### 1.1 [Area of change]

Describe the change. Include:
- Before/after comparisons where applicable
- Exact field names, types, constraints
- JSON/YAML snippets for schema changes
- SQL DDL for database changes
- Function signatures for code changes

### 1.2 [Area of change]

...

> **Tip**: For BrewSpec schema tasks, structure subsections as: root-level changes → `$defs` changes → new definitions. For BrewLog CLI tasks: database schema → Pydantic models → CLI interface → output format.

---

## 2. Data Models

### 2.1 Pydantic Models

Define or update Pydantic v2 models. Show the complete model, not just the delta — the dev should not need to diff against the previous version.

```python
class ExampleModel(BaseModel):
    field: type
```

### 2.2 SQLite Schema

Define CREATE TABLE statements or ALTER TABLE migrations if the database schema changes. If unchanged, state that explicitly.

```sql
CREATE TABLE example (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
);
```

---

## 3. CLI Interface

*Skip this section for BrewSpec schema-only tasks.*

Document every command affected by this design:

```
brewlog <command> [OPTIONS] [ARGS]

Options:
  --flag TEXT    Description of flag [required/optional]
```

Include:
- New commands
- Modified commands (before/after comparison)
- Output format (example terminal output)
- Exit codes and error messages

---

## 4. Architecture Decision Records

Document significant design trade-offs. Skip if no meaningful trade-offs exist.

### ADR-1: [Decision title]

**Context**: Why this decision needed to be made.
**Options considered**: List the alternatives.
**Decision**: What was chosen.
**Rationale**: Why.
**Consequences**: What this means for future changes.

---

## 5. Public Spec Document

*Required for BrewSpec schema tasks. Skip for BrewLog CLI tasks.*

The dev must produce `brewspec-vX.Y.md` in the public brewspec repo alongside the schema. This section defines the required content.

> Before writing the new spec doc, archive the previous version: copy `brewspec-vX.(Y-1).md` to `versions/brewspec-vX.(Y-1).md`, then overwrite `brewspec-vX.Y.md` at the repo root.

### 5.1 Structure

The spec document must include these sections in order:

1. **Overview** — What BrewSpec is; one paragraph
2. **Field Reference** — Table of all fields with type, required/optional, constraints, description
3. **What Changed in vX.Y** — Bulleted list of additions and breaking changes
4. **Validation** — Guidance that tools should validate at storage time, not just display time
5. **Backward Compatibility** — What breaks from the previous version; migration guide

### 5.2 Field Reference Table Format

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `field_name` | string | Yes | maxLength: 100 | Description |

---

## 6. File Manifest

Complete list of every file the dev must create or modify. Include the repo (calibrate-coffee vs brewspec) and the operation (create / modify / archive).

| File | Repo | Operation | Notes |
|------|------|-----------|-------|
| `brewspec.schema.json` | brewspec | Modify | Schema changes per Section 1 |
| `brewspec-vX.Y.md` | brewspec | Create | Per Section 5 |
| `versions/brewspec-vX.(Y-1).md` | brewspec | Archive | Copy before overwriting root spec |
| `examples/valid/example.yaml` | brewspec | Modify | Update to new version |
| `tests/test_brewspec_schema.py` | brewspec | Modify | Add test cases per Section 7 |

---

## 7. Test Strategy

Enumerate the test cases the dev must write before implementing. Group by acceptance criterion. Every AC must have at least one test case.

### AC-N: [AC description]

| Test | Input | Expected |
|------|-------|----------|
| Valid case | `{field: value}` | passes validation |
| Invalid case | `{field: bad_value}` | fails with error |
| Edge case | `{field: boundary_value}` | passes / fails |

---

## 8. Security Considerations

Address each trust boundary relevant to this design:

- **Input validation**: What user inputs are validated, and how (Pydantic field type, JSON Schema constraint, etc.)
- **File I/O**: Any new file read/write operations and how they're made safe
- **SQL**: Any new queries — confirm parameterized, no f-string interpolation of user data
- **Error messages**: Confirm error messages don't expose internal paths or stack traces
- **Data integrity**: Any new constraints that protect data consistency

---

## 9. TDD Implementation Order

Prescribe the sequence the dev should follow. Tests must be written before implementation code for each step.

1. Write failing tests for [AC group]
2. Implement [change] to make tests pass
3. Write failing tests for [AC group]
4. Implement [change] to make tests pass
5. Run full test suite — confirm all pass
6. Run `ruff check .` — fix any lint errors
