---
feature: brewlog-cli
status: implemented        # implemented | partial | planned
last_updated: 2026-10-14
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

The user-facing reference is the root `README.md` → *BrewLog CLI* section, which lists the commands and gives examples. Each command's flags are documented only by its `--help`; the README carries no flag table, because the hand-copied one drifted (it still listed 1–5 ratings at v0.6). `brewlog --help` and `brewlog export --help` name the BrewSpec version export writes, and a test pins that to v1.2.

## Data model

Brews persist in a local **SQLite** database (`db.py`). In memory they are **Pydantic** models (`models.py`); `serialise.py` converts them to and from BrewSpec, and `schema.py` validates against the bundled schema. The canonical interchange shape is BrewSpec (`specs/features/brewspec.md`).

## Interface surface

A local CLI — no network, no server, single user. The interop boundary is `import` / `export` (BrewSpec files), which is what makes a user's data portable: log here, export, take it elsewhere.

**Version.** `export` writes, and `import` accepts, exactly the BrewSpec version in `serialise.BREWSPEC_VERSION`, which is `"1.2"`. `import` reads that constant rather than a second literal. A file of any other version is refused before schema validation, with a message naming the required version and the migration: from v1.0 or v1.1, change `brewspec_version` only; from v0.9, also rename `water_weight_g` to `water_g` and `notes` to `process_notes`. A test pins `BREWSPEC_VERSION` to the bundled schema's `brewspec_version` const. Until CAL-2301 the two had drifted (`"1.0"` against `"1.1"`), so every export failed its own schema check and every import was refused.

**Fields import drops.** `import` validates the whole document against the bundled schema, then stores only the fields BrewLog models. It drops v1.1's `water.type`, `water.notes`, `equipment.burr_set` and `equipment.rpm`, and v1.2's `brew.brewed_at`, `brew.servings` and `coffee.caffeine_level`. A file using them imports, and those values are not stored or exported again.

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
- `README.md` → *BrewLog CLI* — user-facing command reference; flags are under each command's `--help`
