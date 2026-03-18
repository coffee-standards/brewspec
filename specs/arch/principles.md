# Architecture Principles

**Last Updated:** 2026-03-18
**Status:** Active

These principles govern technical and system design decisions for BrewSpec and BrewLog. They are distinct from the product principles in `specs/principles.md` — those define what we build and why; these define how we build it. All architecture decisions (recorded in `specs/decisions/`) should be traceable to one or more of these principles.

---

## Data

**BrewSpec is the canonical data interchange format.**
The JSON Schema is the single source of truth for what a valid brew document looks like. The CLI, the landing site, examples, and any downstream consumers all derive from this schema. If there's a conflict between documentation and the schema, the schema wins.

**User data portability is a hard constraint, not a feature.**
A user must always be able to export all of their data in a standard, open format and take it elsewhere. This is not something we add later — it is a precondition for trust in this industry. No design decision should make full data export impractical. If a design makes portability hard, change the design.
*Derived from: product principle "Build trust before asking for commitment"; principles "Interoperability over features"*

**The spec leads, products follow.**
When a downstream product (e.g. a commercial brew tracker) needs a schema change, that change is evaluated on its merits as a spec improvement — not as a product accommodation. Changes must make the spec better for all consumers, not just one. Breaking changes require a version bump and migration guidance.

---

## Schema Design

**Additive changes are preferred over breaking changes.**
New optional fields are always safe. Removing fields, changing types, or altering required constraints are breaking changes that force all consumers to update. Breaking changes are acceptable when they improve the spec — but they must be versioned, documented, and carry migration guidance.

**Validate at every system boundary.**
All inputs are untrusted until validated. This applies to: BrewSpec documents during import, CLI user input, and any data that crosses a process boundary. The CLI established this pattern with Pydantic at every input — maintain it.
*Derived from: principles "Secure by habit"*

**Schema constraints should be enforceable.**
Every constraint in the JSON Schema should be testable with a valid and invalid example. If a constraint can't be demonstrated with an example file, it may be too subtle to enforce reliably.

---

## CLI Design

**Offline-first, zero infrastructure.**
BrewLog runs locally with SQLite. No network calls, no accounts, no cloud dependency. A user's data lives on their machine and they own it completely.

**Python-only stack.**
The CLI is Python 3.11+. Adding a second language adds operational overhead that a solo operation cannot sustain. Default to Python unless there is a strong, specific reason not to.

**Minimal dependencies.**
Every library we add is a dependency we own. Prefer fewer, better dependencies over many convenient ones. The standard library is often enough. Before adopting a dependency: Is it actively maintained? Is the license compatible with Apache 2.0? Does it do one thing well?
*Derived from: principles "Every dependency is a future obligation"*

---

## Site (brewspec.coffee)

**Static, no runtime dependencies.**
The landing page is a static Astro site deployed to GitHub Pages. No server, no database, no API calls. Content changes require a code push, not a database update.

**Schema is served from the site.**
The canonical schema URL lives at brewspec.coffee/schema/. The JSON Schema `$id` references this URL, making it the stable, human-readable location for the schema.

---

## Operations

**Every system must be solo-operable.**
If understanding, deploying, or debugging a component requires more than one person's knowledge, it's too complex for this stage. This applies to: the CLI (pip install), the site (git push → GitHub Pages), and the schema (JSON file in the repo).
*Derived from: operating principle "Respect the constraint. This is a one-person operation"*

---

## Security

**Secure by habit.**
Even local tools handle personal data. Validate inputs. Don't log sensitive info. Parameterize queries (no f-string SQL). Build the muscle memory now so it's automatic when the ecosystem grows.

**Input validation is mandatory, not optional.**
Every CLI command that accepts user input validates it before storage. Every import pipeline validates against the JSON Schema before processing. Defence in depth — don't assume the data is clean just because it came from a trusted source.
