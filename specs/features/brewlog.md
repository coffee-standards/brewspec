---
feature: brewlog-cli
status: implemented        # implemented | partial | planned
last_updated: 2026-06-06
linear: []
---

# BrewLog CLI

> A local command-line brew tracker that stores brews using the BrewSpec format — the reference implementation that proves the spec works end to end. Free and open source.

## Behaviour

`brewlog` is a single-user, local CLI (Click) over a local SQLite database. It logs, edits, and analyses brews, and imports/exports them as BrewSpec documents. Every stored brew round-trips losslessly to and from BrewSpec.

### Commands

| Command | Does |
|---|---|
| `brewlog add` | Log a new brew — flags (`--date`, `--type`, `--dose`, `--water`, …) or interactive prompts. |
| `brewlog list` | List brews. Filters: `--limit`/`--all`, `--type`, `--since`/`--until`, `--rating-min`/`--rating-max`. |
| `brewlog show <id>` | Show one brew in full. |
| `brewlog update <id>` | Edit an existing brew. |
| `brewlog delete <id>` | Delete a brew. |
| `brewlog import <file>` | Import brews from a BrewSpec file (validated against the schema). |
| `brewlog export [file]` | Export brews as a BrewSpec document. |
| `brewlog stats` | Aggregate statistics over the log. |
| `brewlog search` | Search brews. |

The user-facing reference (flags, examples) lives in `brewlog/README.md`.

## Data model

Brews persist in a local **SQLite** database (`db.py`). In memory they are **Pydantic** models (`models.py`); `serialise.py` converts them to and from BrewSpec, and `schema.py` validates against the bundled schema. The canonical interchange shape is BrewSpec (`specs/features/brewspec.md`).

## Interface surface

A local CLI — no network, no server, single user. The interop boundary is `import` / `export` (BrewSpec files), which is what makes a user's data portable: log here, export, take it elsewhere.

## Known limitations

Local, single-user only — no sync or multi-device. This is deliberate (local-first, the precondition for trust before any hosted product). Multi-device sync is future, not deferred debt.

## Decisions

### Decision: Bundle the BrewSpec schema as package data

*Decided 2026.*

**Context.** `brewlog import` validates BrewSpec files and must do so offline, without fetching the schema over the network.

**Decision.** Bundle a copy of `brewspec.schema.json` inside the package (`brewlog` package-data) and validate against it.

**Alternatives.** Fetch the schema from the repo/site at runtime (adds a network dependency; breaks offline); reimplement validation in code (drifts from the canonical schema).

**Consequences.** Offline-capable validation. The bundled copy and the root `brewspec.schema.json` **must be kept in sync** — a schema change updates both, or the CLI validates against a stale contract (see `CONTEXT.md` gotchas).

## Cross-references

- `specs/features/brewspec.md` — the format BrewLog stores and round-trips
- `brewlog/` — the package (`src/`, `tests/`)
- `brewlog/README.md` — user-facing command reference
