# Bug Tracker

Bugs live here as individual files, separate from the feature manifest.
This directory is the source of truth for bug status, reproduction steps, fix details, and regression notes.

## Naming convention

```
BUG-NNN-short-slug.md
```

- `NNN` is a zero-padded sequential number (001, 002, ...)
- `short-slug` is a 2–4 word kebab-case description of the symptom
- Example: `BUG-001-import-rejects-valid-file.md`

## Severity definitions

| Severity | Meaning |
|---|---|
| `critical` | Schema or CLI is broken for all users. Fix before next deploy. |
| `high` | Core workflow is broken or significantly degraded. Fix in the next deploy. |
| `medium` | Non-critical feature is broken or UX is noticeably wrong. Can batch with next release. |
| `low` | Minor cosmetic or edge case. Fix when convenient. |

## Status lifecycle

```
open → in_progress → fixed → closed
             ↓
          wont_fix
```

- **open** — filed, not yet assigned
- **in_progress** — a dev is working on it
- **fixed** — fix is deployed; regression test and doc updates complete
- **closed** — confirmed fixed in production
- **wont_fix** — acknowledged but not going to fix (add a reason)

## Fix requirements

A bug fix PR is not complete unless:

1. **Regression test** — a test exists that would have caught this bug. No exceptions unless the bug is untestable (explain why in the bug file).
2. **Spec updated** — if the bug revealed a gap in the product spec or acceptance criteria, that AC must be added or corrected in `specs/products/`.
3. **ADR updated** — if the bug revealed a design decision that should be standardised or a constraint that should be recorded, amend or create an ADR in `specs/decisions/`.
4. **Bug file updated** — fill in the Resolution section before the PR is merged.

## Template

Copy `specs/templates/bug-report.md` to start a new bug file.

## Index

| ID | Slug | Severity | Status | Area |
|---|---|---|---|---|
| BUG-001 | site-favicon-missing | low | in_progress | frontend |

*Update this table when adding or closing a bug.*
