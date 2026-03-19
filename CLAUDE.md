# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mission:** Make the coffee industry more sustainable by providing tools that help businesses and individuals operate better and make better decisions.

Two products in this repo:
1. **BrewSpec** — An open source standard for describing coffee brews (JSON Schema, YAML/JSON documents)
2. **BrewLog CLI** — An open source local CLI tool for logging and tracking brews using the BrewSpec format

Both are free and open source forever. They are the trust anchor — commercial products (managed in a separate repo) build on top of the open standard.

Strategy in `specs/strategy.md`. Principles in `specs/principles.md`.

## Repo Structure

```
brewspec.schema.json       # Current JSON Schema (source of truth)
brewspec-v0.7.md           # Current spec document (living)
versions/                  # Archived previous spec versions
examples/
  valid/                   # Valid BrewSpec example files
  invalid/                 # Invalid examples (test schema rejection)
tests/                     # Root-level schema validation tests
brewlog/                   # BrewLog CLI (Python package)
  src/brewlog/             # Source code
  tests/                   # CLI test suite
  pyproject.toml           # Package config
site/                      # Landing page (Astro → GitHub Pages)
specs/                     # Product specs, designs, brand, templates
reviews/                   # Agent review artifacts
bugs/                      # Bug tracker
manifest.yaml              # Task backlog and coordination
```

## Tech Stack

### BrewSpec Schema
- **Format**: JSON Schema (Draft 2020-12)
- **Documents**: YAML and JSON
- **Validation**: jsonschema (Python), plus any JSON Schema-compliant validator
- **Testing**: pytest (validates schema against example files)

### BrewLog CLI
- **Language**: Python 3.11+
- **Database**: SQLite (local, zero-config)
- **CLI**: Click
- **Validation**: Pydantic + JSON Schema
- **Data format**: YAML/JSON (BrewSpec)
- **Linting**: Ruff
- **Dependencies**: pyyaml, pydantic, click, jsonschema (keep minimal)

### Landing Page (brewspec.coffee)
- **Framework**: Astro
- **Hosting**: GitHub Pages
- **Domain**: brewspec.coffee (CNAME in site/public/)

## Setup

### BrewLog CLI

```bash
cd brewlog
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

> **Note:** Use `venv` (no dot prefix). macOS automatically applies the `UF_HIDDEN` filesystem flag to dot-prefixed directories, which causes Python's `site.py` to skip `.pth` files inside them — breaking editable installs. A plain `venv` name avoids this.

### Landing Page

```bash
cd site
npm install
npm run dev     # local dev server
npm run build   # production build → site/dist/
```

## Testing

### Schema Tests (root level)

```bash
pip install -r requirements.txt
pytest tests/
```

Validates the JSON Schema against all example files in `examples/valid/` and `examples/invalid/`.

### BrewLog CLI Tests

```bash
cd brewlog
source venv/bin/activate
pytest tests/               # run full suite
pytest tests/ -k "name"     # filter by test name
pytest tests/test_cmd_add.py  # single file
```

Run lint and tests together before handoff:

```bash
cd brewlog
ruff check .
pytest tests/
```

Both must pass. Fix lint errors before running tests — a lint failure is a blocker.

## Conventions

- Python 3.11+
- Test-driven development: tests first, then implementation
- Open source: everything is public, no secrets in the repo
- Atomic commits: each commit leaves the project in a working state
- Lint clean: all code must pass `ruff check .` before handoff to reviewer
- **Commit message format:** `type(scope): description`
  - Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
  - Scopes: `brewspec`, `brewlog`, `site`
  - Manifest-only commits use: `manifest: <description>`
  - Examples: `feat(brewspec): add result.yield_g field`, `fix(brewlog): correct import error message`

## Spec-Driven Development Lifecycle

Every task flows through the agent team in order:

```
strategist → product-manager → architect → backend-dev → reviewer → deployment-manager
   (why)         (what)          (how)     (build + test)  (verify)      (ship it)
```

1. **Strategy** — `strategist` defines principles, objectives, and which problems to solve next. Pauses for user input on priorities and positioning.
2. **Spec** — `product-manager` writes a product spec in `specs/products/` using the template. Defines user stories, acceptance criteria, scope, and security requirements. Pauses for user input on stories, ACs, and scope.
3. **Design** — `architect` reads the product spec and produces data models, CLI interface design, schema definitions, test strategy, and security considerations.
4. **Build + Test** — `backend-dev` follows TDD: write tests for each acceptance criterion first, then implement to make tests pass. Run `ruff check .` alongside tests. All code must be lint-clean and test-passing before signaling ready for review.
5. **Verify** — `reviewer` validates the implementation against the spec, checks security, confirms TDD was followed, and runs the test suite. Any non-blocking issues found during review are recorded as `review_carry_forward` items on the **next** version's backlog task in `manifest.yaml` — not on the completed task.
6. **Deploy** — `deployment-manager` runs only after a reviewer PASS. Commits with a structured message, creates a version tag, and pushes. Updates the manifest to `done`. Never deploys on a FAIL verdict.

### Pipeline Tiers

Every task runs one of three pipelines. The `tier` field in `manifest.yaml` controls routing; it defaults to `standard` if absent.

**Express** — carry-forward fixes and fully-specified patches
- **Eligible:** items where every step is already described in `review_carry_forward`, or single-behaviour bug fixes with no design ambiguity
- **Gate:** *Could a dev implement this from the manifest description alone, with zero ambiguity?* If yes, Express. If no, Standard.
- **Pipeline:** `backend-dev → reviewer → deploy` — no spec, no design, no self-reviews

**Standard** — new features, schema changes, anything requiring design judgment
- **Eligible:** everything not clearly Express
- **Pipeline:** full `strategist → product-manager → architect → backend-dev → reviewer → deploy`

**Discovery** — exploratory spikes, proof-of-concept work
- **Eligible:** work to validate a direction before committing to building it
- **Pipeline:** `backend-dev` only — output may not ship

### Bug Tracking

Bugs are tracked in `bugs/` as individual files — **not** in `manifest.yaml`. The manifest is for features and chores; bugs are high-volume and need their own space.

**Creating a bug:**
1. Copy `specs/templates/bug-report.md` to `bugs/BUG-NNN-short-slug.md` (next sequential number)
2. Fill in description, steps to reproduce, expected/actual behaviour, environment, and affected spec
3. Add a row to the index table in `bugs/README.md`

**Fix requirements — a bug fix PR is not complete unless all four are done:**
1. **Regression test** — a test that would have caught this bug
2. **Spec / AC updated** — if the bug revealed a missing or wrong acceptance criterion
3. **ADR updated** — if the bug revealed a design decision that should be standardised
4. **Bug file Resolution section filled in** — root cause, fix summary, and confirmation of the above

### Security Throughout

Security is embedded in every stage, even for local tools:
- **Product Manager**: Includes data sensitivity and validation requirements in specs
- **Architect**: Designs input validation rules and data integrity constraints
- **Dev**: Validates all inputs via Pydantic, parameterizes queries, no secrets in code
- **Reviewer**: Checks for injection, data exposure, and validates security requirements

### Using Agents

Agents are invoked via natural language in Claude Code conversations:

- **strategist** — Define product direction, principles, and feature priorities
- **product-manager** — Write product specs, acceptance criteria, and manage the backlog
- **architect** — Design data models, CLI interfaces, and schema structures before implementation
- **backend-dev** — Build Python code with TDD. Runs `ruff check .` alongside tests; code must be lint-clean before handoff
- **reviewer** — Final gate: spec compliance, security review, TDD verification, and test execution
- **deployment-manager** — Runs after reviewer PASS only. Commits, tags, pushes, and marks the task done
- **system-steward** — On-demand health monitor. Checks architecture principles, ADR staleness, design-to-code gaps, dependency health, and test health

### Deployment Rules

| Product | Strategy | Tag format |
|---|---|---|
| BrewSpec schema/spec | Feature branch → merge to `main` → delete branch | `vX.Y` |
| BrewLog CLI | Feature branch → merge to `main` → delete branch | `brewlog-vX.Y` |
| BrewSpec site | Push to `main` → GitHub Actions deploys to GitHub Pages | — |

## Orchestrator (Claude Code Main)

Claude Code (the main session) is the orchestrator. It manages the pipeline, mediates the PM conversation, tracks state via the manifest, and decides when to pause for user input.

### When to pause for user input

Pause **only** when:
1. **PM scoping** — the product-manager has produced a scope proposal. Present it to the user, relay their response back to the PM, repeat until scope is agreed. Then proceed autonomously.
2. **Repeated reviewer FAIL** — reviewer fails a second time after a dev fix attempt. Stop and present the full list of blocking issues.
3. **Agent escalation** — any agent explicitly flags a decision it cannot make autonomously.

Everything else runs through without interruption. Do not ask for approval between stages.

### Pipeline execution

Read `manifest.yaml` to determine where a task is and where to start. Never redo a completed stage — resume from the current status.

Update the manifest status at each handoff. The manifest is the source of truth — if a pipeline breaks and restarts, read it and continue from where it stopped.

### Reviewer FAIL logic

1. **First FAIL** — send the full list of blocking issues back to backend-dev. Re-run the reviewer.
2. **Second FAIL** — stop. Present the blocking issues to the user and wait for direction.

## Document Hierarchy

```
specs/
  strategy.md              # Business & product strategy
  principles.md            # Product and engineering principles
  infrastructure.md        # Domains, hosting, email — operational reference
  arch/
    principles.md          # Architecture principles — technical decisions, system design
  decisions/               # Architecture Decision Records (ADRs)
    ADR-NNN-title.md
  products/                # Product specs — one per version
    brewspec.md
    brewspec-v0.3.md
    brewlog.md
  designs/                 # Technical designs — architect output per task
    brewspec-v0.1.md
    brewlog-cli-v0.1.md
  brand/                   # Brand artifacts
    brewspec/
      brand-guidelines.md
      copy/
        landing-page.md
  templates/               # Source-of-truth templates

manifest.yaml              # Task backlog and coordination
reviews/                   # Agent review artifacts
bugs/                      # Bug tracker
```

### How documents flow

| Document | Purpose | Owner |
|----------|---------|-------|
| `specs/strategy.md` | Why we're building, what products, for whom | strategist |
| `specs/principles.md` | Overarching decision-making principles | strategist + architect |
| `specs/infrastructure.md` | Domains, hosting, email — operational reference | orchestrator |
| `specs/products/*.md` | What to build — user stories, ACs, scope | product-manager |
| `specs/arch/principles.md` | How we build — technical principles | architect |
| `specs/decisions/ADR-*.md` | Why we built it this way | architect |
| `specs/designs/*.md` | How to build this task — schemas, models, test strategy | architect |
| `manifest.yaml` | Task backlog — status, assignments, artifacts | all agents |
| `bugs/BUG-NNN-*.md` | Bug reports | dev + reviewer |

## Parallel Build Streams (Worktrees)

To run multiple pipeline tasks simultaneously without file conflicts, use **git worktrees**. Each stream gets an isolated working directory on its own branch, sharing the same git history.

### Starting a parallel stream

```bash
git worktree add .worktrees/<task-name> -b <task-name>
```

### Rules for parallel streams

- Each stream must target a **different manifest task**
- The **manifest** (`manifest.yaml`) is the only shared file that parallel streams touch
- Worktree directories live in `.worktrees/` (gitignored)
- Branch names should match the task slug from the manifest
- **Manifest updates must be committed separately** from code changes

## Cross-Repo Dependencies

BrewSpec and BrewLog are open source tools. A commercial product (Calibrate Coffee, managed in a separate private repo) uses BrewSpec as its data interchange format.

**When a downstream product needs a schema change:**
- File a task in this manifest with a description of the requirement
- Evaluate the change on its merits as a spec improvement — not as a product accommodation
- The spec leads, products follow

**When a spec change affects downstream products:**
- Note the breaking change in the spec document and manifest task
- Downstream products are responsible for adopting the new version on their own timeline

## Key Dependencies

- **pyyaml** — YAML parsing for BrewSpec files
- **pydantic** — Data validation and modeling
- **click** — CLI framework
- **jsonschema** — BrewSpec validation
