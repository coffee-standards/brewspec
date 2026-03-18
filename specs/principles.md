# Principles

**Last Updated:** 2026-02-28

---

## Mission

Make the coffee industry more sustainable by providing the data backbone that helps businesses and individuals operate better and make smarter decisions.

---

## Product Principles

**Open by default.** The coffee industry runs on small businesses with thin margins. Technology adoption starts with free, interoperable tools — not vendor lock-in. We build open standards first, products second. The spec stays free forever.

**Build trust before asking for commitment.** Small businesses can't afford lock-in. Individuals won't invest time in data entry without portability guarantees. We start open source not out of ideology — it's how you earn trust in a low-margin, underserviced industry. Trust first, then product, then revenue.

**Start where people are.** Home brewers use notebooks, phone timers, and spreadsheets. Cafes use paper logs and proprietary POS exports. Meet them there. Don't ask them to change their workflow — make their existing one better, then give them a reason to upgrade.

**Earn complexity.** Every feature starts as the simplest version that's useful. Add sophistication only when real usage demands it. A plain text log beats a fancy dashboard nobody opens. A free CLI beats a polished app nobody trusts.

**Interoperability over features.** A standardized brew format that any tool can read is more valuable than a proprietary app with more buttons. Build for the ecosystem, not just our users.

**Enter downstream, expand upstream.** The supply chain runs from farm to cup. We enter at the cup (brewing), where data exhaust reveals consumer behaviour. Then work backward: cafes, roasters, eventually sourcing. Each step is unlocked by the data and trust built at the step before it.

**Aggregate data creates value no one has alone.** A single cafe's brew data is noise. Thousands of data points become signal — predictions, trends, insights. Design for this from the start, and never compromise on privacy or data ownership. Aggregate analysis of unidentifiable brew data is what makes the product valuable — without it there is no product. Only unidentifiable brew data is used in aggregation; identifying information is never included. Users are informed when aggregate analysis goes live. We are not selling user data or running ads — we are building the data backbone of the coffee supply chain.

---

## Building Principles

**Simplicity scales.** Every dependency, every service, every abstraction must justify its existence. If it doesn't make things simpler, it makes things harder.

**Atomic increments.** Ship small, ship often. A working CLI that logs brews beats a half-built web app. Every commit should leave the project in a better, working state.

**Iterate to learn.** The first version of anything can be free, rough, and wrong. The point is to get it into hands and learn. We don't know what we'll discover when we see how people use this. Speed of learning beats perfection of output.

**Scale with needs.** Start free. Start local. Start simple. SQLite before Postgres. Files before databases. Local before cloud. Move up the cost and complexity curve only when the current approach breaks under real usage.

**Tests prove the spec.** We practice test-driven development. Write the test for the acceptance criterion, then write the code. If you can't write a test for it, the spec isn't clear enough.

**Secure by habit.** Even local tools handle personal data. Validate inputs. Don't log sensitive info. Build the muscle memory now so it's automatic when we scale.

**Adopt open source for commodity work.** Don't build what already exists and works. YAML parsers, CLI frameworks, JSON Schema validators, test runners — these are solved problems. Use well-maintained open source libraries for anything that isn't core differentiation and spend build energy on what only we can build.

**Vet dependencies before adopting them.** Every library we add is a dependency we own. Before adopting, check: Is it actively maintained? Does it have a healthy community? Is the license compatible with Apache 2.0? Does it do one thing well without pulling in a chain of transitive dependencies? A dependency that fails these checks is technical debt with no owner.

**Every dependency is a future obligation.** As a single-founder operation, every library we adopt is something we'll eventually have to debug, upgrade, or replace ourselves. Prefer fewer, better dependencies over many convenient ones. When in doubt, the standard library is enough.

**Design for agent collaboration.** LLM agents excel with structured specs, explicit acceptance criteria, and machine-readable formats. Give them JSON schemas, clear templates, and TDD feedback loops. The spec-driven development lifecycle isn't just for humans — it's how agents ship working code without hallucinating.

---

## Operating Principles

**Apply what we preach.** We're building SPC and Lean tooling for the coffee industry. We run our own business the same way — using Profound Knowledge, reducing variation, focusing on systems over blame. If we can't apply these ideas to our own work, we have no business selling them to others.

**Measure what matters.** Vanity metrics don't drive decisions. In Phase 1, learning metrics (do people log consistently? what fields get skipped?) matter more than download counts. Measure the thing that tells you what to do next.

**Respect the constraint.** This is a one-person operation building with AI agents. Every decision optimizes for that reality. Don't plan for a team we don't have. Don't build infrastructure we don't need. The constraint is a feature — it forces focus.
