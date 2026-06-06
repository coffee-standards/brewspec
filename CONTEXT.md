# CONTEXT.md

Agent-facing context for **BrewSpec**. `README.md` is for humans; this is for agents. Read it first. The guidance files (skills, agents, commands) are universal and point here for everything repo-specific.

```yaml
profile: standard
visibility: local          # public repo — only this CONTEXT.md is committed; guidance internals are bootstrapped locally
repo:
  name: brewspec
  linear: none             # EXCEPTION: not on Linear yet — manifest.yaml is the local task record (see "Tracking work")
layers:
  linear: false            # the standard is Linear; brewspec is the exception until it goes active
  design_system: false
  feature_specs: true      # canonical record is the spec doc + schema + specs/products/
stack:
  language: Python 3.11
  framework: none for the spec (JSON Schema + pytest); brewlog uses Click + Pydantic v2
commands:
  install: "pip install -r requirements.txt"        # brewlog: pip install -e brewlog
  lint:    "none configured"
  typecheck: "none configured"
  test:    "pytest tests/"                            # validates schema + every example
  test_one: "pytest tests/test_brewspec_schema.py::<test_name>"
  test_brewlog: "cd brewlog && pytest"                # the CLI has its own suite
  run:     "brewlog"                                  # the reference CLI, after pip install -e brewlog
branches:
  integration: main        # CI (pytest) runs on PRs to main
  release: main            # site/ deploys to GitHub Pages from main (deploy-site.yml, CNAME)
tools:
  linear_cli: "none — not on Linear; edit manifest.yaml directly; process roadmap.md ideas into manifest tasks"
paths:
  spec: brewspec-v1.0.md          # human-readable standard
  schema: brewspec.schema.json     # the machine contract (also bundled in brewlog as package-data)
  examples: examples/
  versions: versions/              # released spec snapshots
  source: brewlog/src/             # the reference CLI
  tests: tests/                    # schema + example validation
  brewlog_tests: brewlog/tests/
  feature_specs: specs/products/
  decisions: specs/decisions/
  principles: specs/principles.md
  strategy: specs/strategy.md
  manifest: manifest.yaml
  roadmap: roadmap.md
env:
  file: none
```

## What this repo is

BrewSpec is an **open standard** for describing coffee brews: a human-readable spec (`brewspec-v1.0.md`), a published JSON Schema (`brewspec.schema.json`), validation tests, versioned releases, and a docs site. Plus `brewlog/`, a reference CLI that proves the spec works end-to-end. The mission (see `specs/principles.md`) is an open, interoperable data backbone for coffee — the spec stays free forever; products come second.

## Architecture

Three deliverables in one repo:

- **The spec.** `brewspec-v1.0.md` (prose) is the human contract; `brewspec.schema.json` is the machine contract. `examples/` holds sample brews; `versions/` holds released snapshots. `tests/test_brewspec_schema.py` validates the schema and every example against it — that test suite is the gate.
- **brewlog/.** A standalone Python package (Click CLI + Pydantic v2 models) that reads and writes BrewSpec files. It has its own `pyproject.toml`, its own tests, and **bundles a copy of `brewspec.schema.json`** as package data — that copy must stay in sync with the root schema.
- **site/.** The docs site, deployed to GitHub Pages from `main` (`.github/workflows/deploy-site.yml`, `CNAME`).

Planning layer (prior-art shaped, already here): `specs/` holds `arch/`, `decisions/` (ADRs), `designs/`, `products/`, `principles.md`, `strategy.md`, `templates/`. `manifest.yaml` is in-flight work; `roadmap.md` is the freeform ideation backlog.

## Repo-specific principles

The product principles are in [`specs/principles.md`](specs/principles.md) — read them; they govern direction (open by default, earn complexity, interoperability over features, privacy in aggregation). They extend the universal `engineering-principles`.

The spec's own evolution rule is load-bearing: **the schema is a backward-compatible contract.** New versions add fields; they do not remove or repurpose existing ones. A change that breaks an existing valid BrewSpec file needs an ADR and a new version snapshot in `versions/`.

## Tracking work

There is no Linear or external tracker. The `linear-sync` skill's protocol still applies in spirit (a tracked item is the front door, status moves as work progresses), but the "tracker" is `manifest.yaml`, edited directly:

- New work becomes a task entry in `manifest.yaml` (`id`, `name`, `type`, `level`, `status`).
- Status flows `todo → in_progress → ready_for_review → ready_for_deploy → done` (the existing convention in the file's history).
- `roadmap.md` is the idea inbox; ideas are processed into manifest tasks deliberately, not auto-promoted.

When the guidance says "open the ticket" or "set In Review", read and update the `manifest.yaml` entry instead.

## Decisions index

Full text in `specs/decisions/`.

- **ADR-001** — ratings scale: CVA hedonic.
- **ADR-002** — recipe/result field symmetry (two-phase result field delivery).
- **ADR-003** — notes field differentiation.

## Where deeper truth lives

- **What the format is** → `brewspec-v1.0.md` + `brewspec.schema.json`
- **Why things are the way they are** → `specs/decisions/`
- **In-flight work** → `manifest.yaml` · **Ideas** → `roadmap.md`
- **Direction** → `specs/principles.md`, `specs/strategy.md`

## Gotchas

- **Keep the two schema copies in sync.** Editing `brewspec.schema.json` at the root means updating the bundled copy in `brewlog/` (package data), or the CLI validates against a stale contract.
- **Two test suites.** Root `pytest tests/` validates the schema and examples; `cd brewlog && pytest` tests the CLI. A schema change should pass both.
- **Backward compatibility is a hard rule** (see principles above) — adding fields is safe; changing or removing them is a versioned, ADR-level decision.
- **History committed straight to `main`.** Going forward, feature work should branch into a worktree (`worktree-isolation`); CI runs `pytest` only on PRs to `main`.

---
*Profile note: BrewSpec is a "standard + reference tooling" repo — not a typical consumer product, not the pipeline harness. The `standard` profile is the closest fit and works, but the imperfect match is itself a useful signal (a candidate `library`/`standard` profile). Raise it via `/assess harness`.*
