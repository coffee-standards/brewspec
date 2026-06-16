# CONTEXT.md

Agent-facing context for **BrewSpec**. `README.md` is for humans; this is for agents. Read it first. The guidance files (skills, agents, commands) are universal and point here for everything repo-specific.

```yaml
profile: harness           # the one shared surface (the name is a label, not a repo-type selector); repo-type variation is the layers below
visibility: local          # public repo — only this CONTEXT.md is committed; guidance internals are bootstrapped locally
repo:
  name: brewspec
  linear: none             # not on Linear yet — adopt it when work begins (see "Tracking work")
layers:
  linear: false            # the standard is Linear; brewspec is the exception until it goes active
  design_system: false
  feature_specs: true      # canonical record is specs/features/ (the published doc + schema are the contract artifacts)
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
  linear_cli: "none — not on Linear yet; roadmap.md is the idea inbox until Linear is adopted"
paths:
  spec: brewspec-v1.1.md          # human-readable standard
  schema: brewspec.schema.json     # the machine contract (also bundled in brewlog as package-data)
  examples: examples/
  versions: versions/              # released spec snapshots
  source: brewlog/src/             # the reference CLI
  tests: tests/                    # schema + example validation
  brewlog_tests: brewlog/tests/
  feature_specs: specs/features/         # canonical, as-built feature specs (decisions embedded)
  infrastructure: specs/infrastructure.md
  architecture: specs/arch/principles.md # architecture-principles reference spec
  principles: specs/principles.md         # product principles
  strategy: specs/strategy.md
  roadmap: roadmap.md              # idea inbox (no manifest.yaml — retired with the old process)
env:
  file: none
```

## What this repo is

BrewSpec is an **open standard** for describing coffee brews: a human-readable spec (`brewspec-v1.1.md`), a published JSON Schema (`brewspec.schema.json`), validation tests, versioned releases, and a docs site. Plus `brewlog/`, a reference CLI that proves the spec works end-to-end. The mission (see `specs/principles.md`) is an open, interoperable data backbone for coffee — the spec stays free forever; products come second.

## Architecture

Three deliverables in one repo:

- **The spec.** `brewspec-v1.1.md` (prose) is the human contract; `brewspec.schema.json` is the machine contract. `examples/` holds sample brews; `versions/` holds released snapshots. `tests/test_brewspec_schema.py` validates the schema and every example against it — that test suite is the gate.
- **brewlog/.** A standalone Python package (Click CLI + Pydantic v2 models) that reads and writes BrewSpec files. It has its own `pyproject.toml`, its own tests, and **bundles a copy of `brewspec.schema.json`** as package data — that copy must stay in sync with the root schema.
- **site/.** The docs site, deployed to GitHub Pages from `main` (`.github/workflows/deploy-site.yml`, `CNAME`).

Spec layer (new model — `spec-authoring`): `specs/features/` holds the canonical as-built feature specs (`brewspec.md` for the format, `brewlog.md` for the CLI) with decisions embedded inline. `specs/arch/principles.md` is the architecture-principles reference spec; `specs/infrastructure.md` the infrastructure reference spec; `specs/principles.md` the product principles; `specs/strategy.md` the strategy; `specs/brand/` the brand. `roadmap.md` is the freeform ideation backlog. (The old per-version `products/`/`designs/` trail, the standalone `decisions/` ADRs, and the prior-art `manifest.yaml` are all retired — recoverable via git history.)

## Repo-specific principles

The product principles are in [`specs/principles.md`](specs/principles.md) — read them; they govern direction (open by default, earn complexity, interoperability over features, privacy in aggregation). They extend the universal `engineering-principles`.

The spec's own evolution rule is load-bearing: **the schema is a backward-compatible contract.** New versions add fields; they do not remove or repurpose existing ones. A change that breaks an existing valid BrewSpec file needs a recorded decision (in `specs/features/brewspec.md`) and a new version snapshot in `versions/`.

## Tracking work

brewspec is **not on Linear yet** — it is the rare `linear: false` exception (the standard, and where it is heading when work picks up). There is no `manifest.yaml`; that was a prior-art artifact, now retired.

Until Linear is adopted, `roadmap.md` is the idea inbox — capture ideas there freely. When real work begins, put brewspec on Linear and follow the standard flow (`spec-driven-development`): the Linear issue is the front door and the home of the change spec. Items carried over from the retired manifest are listed at the bottom of `roadmap.md`.

## Where deeper truth lives

- **What the product does today, and why** → `specs/features/` (canonical specs, decisions embedded inline). The published standard is `brewspec-v1.1.md` + `brewspec.schema.json` (the schema is the contract).
- **How the system is built / cross-cutting decisions** → `specs/arch/principles.md`
- **Operational reality** → `specs/infrastructure.md`
- **Ideas / backlog** → `roadmap.md` (no in-flight tracker until Linear is adopted)
- **Direction** → `specs/principles.md`, `specs/strategy.md`

## Gotchas

- **Keep the two schema copies in sync.** Editing `brewspec.schema.json` at the root means updating the bundled copy in `brewlog/` (package data), or the CLI validates against a stale contract.
- **Two test suites.** Root `pytest tests/` validates the schema and examples; `cd brewlog && pytest` tests the CLI. A schema change should pass both.
- **Backward compatibility is a hard rule** (see principles above) — adding fields is safe; changing or removing them is a versioned, decision-level change (recorded in `specs/features/brewspec.md`).
- **History committed straight to `main`.** Going forward, feature work should branch into a worktree (`worktree-isolation`); CI runs `pytest` only on PRs to `main`.

---
*Profile note: the standard-vs-harness profile split is retired — there is now **one** guidance surface, and repo-type variation lives in the `layers:` block above, not in a profile choice. BrewSpec is a "standard + reference tooling" repo: `feature_specs: true` (canonical specs in `specs/features/`), `design_system: false`. The old fit question is now a layers question. BrewSpec carries the full one-surface install: `design-system` is present but dormant (`design_system: false`), and `ux-design` applies to its CLI and docs surface. Raise any remaining gap via `/assess`.*
