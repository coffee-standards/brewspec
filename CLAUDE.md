# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It defines the spec-driven development pipeline, agent coordination, and operational rules.

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
brewspec-v0.8.md           # Current spec document (living)
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

## Parallel Build Streams (Worktrees)

Use git worktrees to run multiple pipeline tasks simultaneously. Each stream gets an isolated working directory on its own branch.

### Rules

- Each stream targets a **different manifest task** — never work on the same task in two streams
- The **manifest** is the only shared file; read it at stream start, update only your own task
- Worktree directories live in `.worktrees/` (gitignored)
- Branch names match the task slug from the manifest
- **Manifest updates must be committed separately** from code/spec/design changes — keeps merge conflicts isolated from implementation history

### Git safety

- **All work must be on a branch.** Never leave implementation changes uncommitted on `main`.
- **Never assume uncommitted changes or stashes are stale.** Always show the user what's in them before dropping. Other sessions may be active.
- **If `git pull` is blocked**, stash to proceed but do NOT drop without user approval.
- **Sync regularly** — after merging a PR or before starting a new task, pull main and rebase active worktrees.

## Document Hierarchy

| Document | Purpose | Owner |
|----------|---------|-------|
| `specs/strategy.md` | Why we're building, what products, for whom | strategist |
| `specs/principles.md` | Overarching decision-making principles | strategist + architect |
| `specs/infrastructure.md` | Domains, hosting, email — operational reference | orchestrator |
| `specs/products/*.md` | What to build — user stories, ACs, scope | product-manager |
| `specs/arch/principles.md` | How we build — technical principles governing all design decisions | architect |
| `specs/arch/escalation-levels.md` | When to pause — L0–L3 autonomy scale for agent and orchestrator actions | architect |
| `specs/arch/pipeline.md` | Full pipeline reference — tiers, task types, bug tracking, reviewer/deploy rules | architect |
| `specs/decisions/ADR-*.md` | Why we built it this way — record of significant architectural decisions | architect |
| `specs/designs/*.md` | How to build this task — schemas, models, test strategy | architect |
| `specs/brand/brewspec/` | Brand guidelines and copy | marketing-comms |
| `roadmap.md` | Ideation backlog — loose product ideas, feature thoughts, sequencing intuitions | user |
| `context/anti-patterns.md` | What failed and why — mistakes to avoid repeating | all agents |
| `manifest.yaml` | Task backlog — status, assignments, artifacts | all agents |
| `bugs/BUG-NNN-*.md` | Bug reports — reproduction, root cause, fix, regression test, spec/ADR impact | dev + reviewer |

## Spec-Driven Development Pipeline

Full reference: `specs/arch/pipeline.md`. Summary below.

```
Backend:   strategist → PM → architect → backend-dev → reviewer → deploy
Frontend:  strategist → PM → marketing-comms → architect → frontend-dev → reviewer → deploy
Full-stack: both dev agents run in parallel worktrees after architect
```

Each stage in plain language:

1. **Strategy** — `strategist` defines principles, objectives, and which problems to solve next. Pauses for user input on priorities and positioning.
2. **Spec** — `product-manager` writes a product spec in `specs/products/` using the template. Defines user stories, acceptance criteria, scope, and security requirements. Pauses for user input on stories, ACs, and scope.
3. **Brand/copy** (frontend tasks only) — `marketing-comms` produces copy and messaging before the architect designs the UI. Pauses at every direction checkpoint and final copy sign-off.
4. **Design** — `architect` reads the product spec and produces data models, CLI interface design, schema definitions, test strategy, and security considerations.
5. **Build + Test** — `backend-dev` (CLI/schema) or `frontend-dev` (site) follows TDD: write tests for each acceptance criterion first, then implement to make tests pass. Run `ruff check .` alongside tests. All code must be lint-clean and test-passing before signalling ready for review.
6. **Verify** — `reviewer` validates the implementation against the spec, checks security, confirms TDD was followed, and runs the test suite. Any non-blocking issues found during review are recorded as `review_carry_forward` items on the **next** version's backlog task in `manifest.yaml` — not on the completed task.
7. **Deploy** — `deployment-manager` runs only after a reviewer PASS. Commits with a structured message, creates a version tag, and pushes. Updates the manifest to `done`. Never deploys on a FAIL verdict.

### Pipeline Tiers

Every task runs one of three pipelines. The `tier` field in `manifest.yaml` controls routing; it defaults to `standard` if absent.

| Tier | Pipeline | When |
|---|---|---|
| `standard` | Full pipeline | New features, schema changes, design judgment needed |
| `express` | `dev → reviewer → deploy` | Carry-forwards, unambiguous bug fixes |
| `discovery` | `dev` only | Spikes, proof-of-concept (output may not ship) |

**Express** gate: *Could a dev implement this from the manifest description alone, with zero ambiguity?* If yes, Express. If no, Standard.

**Discovery** exit: promote to Standard (write a spec from what was learned) or discard.

### Task Types

The `type` field classifies tasks in `manifest.yaml`. Feature and chore tasks live in the `tasks:` section; bugs and refactors live in the `maintenance:` section.

| Type | Section | Default tier | Pipeline |
|---|---|---|---|
| `feature` (default) | `tasks:` | standard | Full pipeline or as specified by `tier` |
| `bug` | `maintenance:` | express | dev → reviewer → deploy |
| `refactor` | `maintenance:` | steward-sourced | steward → dev → reviewer (or + architect) |
| `chore` | `tasks:` | n/a | Human-driven, no agent pipeline |

**When to create a `type: bug` maintenance item:**
- A reviewer records a non-blocking finding and there is no upcoming feature version to bundle it into
- A defect or usability issue is found during real use that can be fixed independently
- A carry-forward item on a completed task was not absorbed into the next scheduled version

Use `source_task` to link a maintenance item back to the task where it was originally surfaced.

### Agent Isolation — Worktrees Required

When the orchestrator launches any agent that modifies files (backend-dev, frontend-dev, reviewer, deployment-manager), it **must** use `isolation: "worktree"` on the Agent tool call. This gives the agent its own copy of the repo so it cannot conflict with the orchestrator's working directory or with other agents running in parallel.

Branches alone are not sufficient — two sessions on the same working directory will still clobber each other's uncommitted files, stashes, and untracked artifacts. Worktrees provide true filesystem isolation.

Read-only agents (strategist, product-manager, architect, marketing-comms, system-steward, harness-reviewer) do not require worktree isolation since they do not write to the repo.

### Using Agents

All agents use the L0–L3 escalation scale (`specs/arch/escalation-levels.md`).

| Agent | Role | L2 checkpoints? |
|---|---|---|
| **strategist** | Product direction, principles, priorities | Yes — priorities, principles, personas, positioning |
| **product-manager** | Product specs, ACs, backlog | Yes — stories, ACs, scope, domain assumptions |
| **marketing-comms** | Brand, voice, copy, messaging for landing page and releases | Yes — every direction + final copy sign-off |
| **architect** | Data models, CLI interfaces, schema definitions, test strategy | No |
| **backend-dev** | Python TDD, lint-clean before handoff | No |
| **frontend-dev** | Astro/TS TDD, design system enforcement for the landing page | No |
| **reviewer** | Two-stage review: spec compliance then code quality | No |
| **deployment-manager** | PR creation after reviewer PASS only | No |
| **system-steward** | Health checks, refactor recommendations — run via `/system-health` | No |
| **harness-reviewer** | Harness coherence audits (MECE, Lean, Correct) — run via `/harness-review` | No |

### Skills

Skills are behavioural knowledge that agents load and follow. They live in `.claude/skills/` and are referenced by agent definitions — they apply automatically, not via explicit invocation.

| Skill | File | Used by | Purpose |
|-------|------|---------|---------|
| TDD | `.claude/skills/test-driven-development.md` | backend-dev, frontend-dev | Red-green-refactor methodology, rationalisation rejection, restart triggers |
| Systematic Debugging | `.claude/skills/systematic-debugging.md` | backend-dev, frontend-dev | 4-phase root cause analysis, 3-strikes escalation rule |
| Verification Before Completion | `.claude/skills/verification-before-completion.md` | All agents | Fresh verification evidence required before any completion claim |
| Code Review | `.claude/skills/code-review.md` | reviewer, self-review | Two-stage review methodology, severity levels, verdict criteria |
| Writing Quality | `.claude/skills/writing-quality.md` | marketing-comms, product-manager, strategist, architect | AI slop elimination — banned phrases, structural anti-patterns, sentence-level rules |
| Design System | `.claude/skills/design-system.md` | frontend-dev, reviewer | Brand tokens, visual craft, component specs, animation, elevation, responsive, dark mode |
| UX Design | `.claude/skills/ux-design.md` | frontend-dev, reviewer, architect | User psychology, flow design, information architecture, cognitive load, accessibility |
| Notion Sync | `.claude/skills/notion-sync.md` | frontend-dev, reviewer, marketing-comms, orchestrator | Bidirectional Notion ↔ code sync for app copy and rich docs |

Dev agents read these at the start of every task. The reviewer enforces compliance — skipping TDD or claiming "done" without verification evidence is a FAIL.

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

### Slash Commands

| Command | Purpose | When to use |
|---|---|---|
| `/start-task` | Begin a manifest task — reads manifest, selects pipeline, starts execution | Starting any new task from the backlog |
| `/pipeline-status` | Show current status of all active tasks; archives stale completed tasks | Checking what's in flight |
| `/self-review` | Structured review of a spec or design doc before handoff to the next agent | Standard tier: after PM spec, after design |
| `/release-notes` | Generate formatted release notes for a completed task | After a task reaches `done` — for GitHub releases |
| `/bug` | File a new bug report from the template | When a defect is found during use or review |
| `/system-health` | Run the system-steward health check | On-demand or periodic (weekly/fortnightly) |
| `/harness-review` | Audit the harness itself for coherence (MECE, Lean, Correct) | When pipeline docs or agent definitions have drifted |
| `/forensics` | Deep-dive root cause analysis on a past failure or regression | After a second reviewer FAIL or a production incident |
| `/pause-work` | Safely checkpoint in-progress work before ending a session at critical context | When context monitor fires at critical level |

## Permissions and Safety Model

**Permissions posture:** `Bash(*)` allowed, with a deny list for destructive operations (force push, hard reset, PR merge, direct merge to main). The safety boundary is **branch and worktree isolation**, not permission prompts. See ADR-009.

**Deny list** (in `.claude/settings.json`): force push, force-with-lease, hard reset, merge to main, PR merge. These are never auto-allowed.

**Agent secret access:** Agents must not access, store, or transmit secrets (API keys, tokens, credentials). If a task requires secret access, escalate to L3. Secrets are injected at deploy time, not during development.

### Hooks

Three hooks run automatically (registered in `.claude/settings.json`):

| Hook | Type | Trigger | Purpose |
|------|------|---------|---------|
| `hooks/context-monitor.js` | PostToolUse | Every tool call | Warns at 35% (warning) and 25% (critical) remaining context. Debounced to every 5 tool uses. |
| `hooks/prompt-guard.js` | PreToolUse | Write, Edit | Scans content for prompt injection patterns (instruction override, role play, system markers, invisible Unicode). Advisory only. |
| `hooks/workflow-guard.js` | PreToolUse | Write, Edit | Warns when editing source code on main outside a pipeline task. Advisory only. |

All hooks are advisory — they inject context messages but never block execution. If the context monitor fires at critical level, run `/pause-work` before the session ends.

## Orchestrator (Claude Code Main)

Claude Code (the main session) is the orchestrator. It manages the pipeline, mediates the PM conversation, tracks state via the manifest, and decides when to pause for user input. These rules govern how it runs.

### Escalation levels

All agents and the orchestrator use a shared 4-level scale defined in `specs/arch/escalation-levels.md`. Read that file for the full table of actions per level.

| Level | Rule | Orchestrator behaviour |
|---|---|---|
| **L0 — Autonomous** | Read-only, reversible, or pipeline-authorised | Proceed without notification |
| **L1 — Inform** | Safe, localised changes | Proceed, mention in handoff summary |
| **L2 — Propose** | API/schema/scope/brand changes, 5+ files, new deps | Present options, wait for "go ahead" |
| **L3 — Stop** | Deploys, security, irreversible ops, reviewer FAIL ×2 | Halt, explain, wait for explicit instruction |

### When to pause for user input

The orchestrator pauses **only** at L2+ moments:

1. **PM scoping (L2)** — the product-manager has produced a scope proposal. Present it, relay user feedback, repeat until agreed. Then proceed autonomously.
2. **Brand/copy sign-off (L2)** — marketing-comms requires explicit approval at each checkpoint before handing off to architect.
3. **Repeated reviewer FAIL (L3)** — reviewer fails a second time after a dev fix attempt. Stop and present the full list of blocking issues.
4. **Agent escalation (L2/L3)** — any agent explicitly flags a decision it cannot make autonomously, stating the level.

Everything at L0–L1 runs through without interruption. Do not ask for approval between pipeline stages unless an agent raises an L2+ escalation.

### Pipeline execution

Read `manifest.yaml` to determine where a task is and where to start. Never redo a completed stage — resume from the current status. Check both `tasks:` and `maintenance:` sections when scanning for work.

**Quick reference:** manifest status → next action:
- `backlog` → wait | `ready_for_spec` → PM | `ready_for_design` → marketing-comms (frontend) or self-review + architect (backend) | `ready_for_dev` → self-review + dev | `ready_for_review` → reviewer | `ready_for_deploy` → deployment-manager | `done` → nothing
- Express tier skips spec/design/self-review. Discovery tier is dev-only.

**Standard tier — full status table:**

| Manifest status | Orchestrator action |
|---|---|
| `backlog` | Not ready — wait for strategist to prioritise |
| `ready_for_spec` | Invoke product-manager (with PM conversation loop) |
| `ready_for_design` | **Frontend tasks:** invoke marketing-comms (L2 sign-off loop) → self-review → architect. **Backend/schema tasks:** self-review on product spec → invoke architect |
| `ready_for_dev` | Run `/self-review` on the design doc → invoke backend-dev or frontend-dev |
| `ready_for_review` | Invoke reviewer |
| `ready_for_deploy` | Invoke deployment-manager |
| `done` | Nothing to do |

**Express tier** (`tier: express`): `ready_for_dev` → backend-dev directly (no self-review) → reviewer → deployment-manager.

**Discovery tier** (`tier: discovery`): `ready_for_dev` → backend-dev → close out or promote to Standard.

**Maintenance items:** `type: bug` defaults to express; `type: refactor` follows steward → dev → reviewer. Can run independently or bundle into the next feature version — use judgement based on priority and whether a related feature task is in flight.

**Reviewer FAIL logic:**
1. First FAIL → send full list of blocking issues back to backend-dev. Re-run reviewer.
2. Second FAIL → L3 stop. Present blocking issues to user and wait for direction.

**Deployment:** branch + PR only. PRs require user review before merge — deployment-manager creates the PR but does not merge it.

## Conventions

- Python 3.11+
- Test-driven development: tests first, then implementation
- Open source: everything is public, no secrets in the repo
- Atomic commits: each commit leaves the project in a working state
- Lint clean: all code must pass `ruff check .` before handoff to reviewer

**Commit message format:** `type(scope): description`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
- Scopes: `brewspec`, `brewlog`, `site`
- Manifest-only commits use: `manifest: <description>` (no scope, no type prefix)
- Examples: `feat(brewspec): add result.yield_g field`, `fix(brewlog): correct import error message`

**Pull request format:**
- Title: `type(scope): description` — same as commit format, under 70 characters
- Body: summary bullets + test plan checklist
- PRs require user review before merge — deployment-manager creates the PR but does not merge it

## Deployment Rules

| Product | Strategy | Tag format |
|---|---|---|
| BrewSpec schema/spec | Feature branch → merge to `main` → delete branch | `vX.Y` |
| BrewLog CLI | Feature branch → merge to `main` → delete branch | `brewlog-vX.Y` |
| BrewSpec site | Push to `main` → GitHub Actions deploys to GitHub Pages | — |

## Cross-Repo Dependencies

BrewSpec and BrewLog are open source tools. Downstream products (managed in separate repos) may use BrewSpec as their data interchange format.

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
