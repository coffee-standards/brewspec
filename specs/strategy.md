# BrewSpec & BrewLog Strategy

**Version:** 1.0
**Status:** Active
**Owner:** Scott Luengen
**Last Updated:** 2026-03-18
**Repository:** github.com/coffee-standards/brewspec

---

## Mission

Make the coffee industry more sustainable by providing the data backbone that helps businesses and individuals operate better and make smarter decisions.

## Vision

The coffee supply chain is full of small businesses that don't make a lot of money. They can't afford large solutions with high implementation costs. They're lumped in with all of hospitality and underserviced by tech as a result. No single business has the data to drive deep analysis or insights — the data gravity just isn't there.

We change that by starting at the cup and working backward up the supply chain.

First, we establish trust through an open source brew specification and a free tool that proves it works. The open source phase isn't charity. It's how you earn trust in an industry where businesses can't afford to get locked into proprietary apps and have data they rely on taken away.

BrewSpec and BrewLog are the trust anchor. They stay free and open source permanently. Commercial products (managed separately) build on top of the open standard — they don't replace it.

---

## Industry Context

**Small businesses, thin margins.** From farmers to roasters to cafes, the coffee supply chain is composed of small operators. They can't absorb the cost of enterprise software or failed technology bets.

**No data gravity.** A single cafe's brew data is noise. A single roaster's sales data is a sliver. No individual business has enough data to drive meaningful analysis or predictions. Value comes from aggregation.

**Underserviced by tech.** Coffee gets lumped into "hospitality" by most software vendors. The result: generic POS systems, no industry-specific tooling, and data silos everywhere. Every coffee app, spreadsheet template, and roaster portal invents its own schema.

**Trust deficit.** The industry has seen tools come and go. Businesses that invested time in data entry lost that data when apps shut down or changed pricing. Open source is not just a philosophy — it's a go-to-market requirement.

---

## Products

### BrewSpec

An open source standard for describing coffee brews (JSON/YAML). Like BeerXML, but for coffee.

**Purpose:** Establish an open, portable data format so that brew data can move freely between tools and never be locked into a single vendor's platform.

**Free forever.** The spec stays open source permanently. It's the trust anchor that everything else — our tools and third-party tools — builds on.

### BrewLog CLI

A minimal command-line tool to log and view brews locally using the BrewSpec format.

**Purpose:** Prove the spec works end-to-end. Give early adopters a real tool, not just a schema.

**Intentionally basic.** The CLI validates the spec but won't meet the needs of power users. That's by design — it drives adoption of the format while more sophisticated tools (ours or others') build on top.

### BrewSpec Landing Page (brewspec.coffee)

Public website describing BrewSpec, linking to the repo and schema, and giving tool builders a canonical URL to reference.

---

## Strategic Purpose

1. **Build trust.** Plant a flag: our data format is open, portable, and yours. Coffee businesses see we're not building a lock-in play.
2. **Move fast and learn.** Ship quickly, see how people use it, discover what matters before committing to polish.
3. **Enable the ecosystem.** BrewSpec is designed to be adopted by any coffee tool. If other apps adopt the format, that's a win — ecosystem adoption validates the standard.

**Downstream consumers:** Commercial products may use BrewSpec as their data interchange format. Requirements from those products may drive schema changes, which are evaluated and implemented here on their merits as spec improvements — not as product-specific features.

---

## Target Users

### The Early Adopter

- Home brewers and coffee enthusiasts who log brews
- Comfortable with a terminal (or willing to try)
- Current workaround: notes app, spreadsheet, memory
- **What we learn from them:** Do people log brews consistently? What fields matter? What's missing?

### The Tool Builder

- Developers building coffee-related software
- Want a spec to build against instead of inventing a schema
- Ecosystem adoption of BrewSpec validates the standard

---

## Business Model

**No revenue.** BrewSpec and BrewLog are open source. Build trust and validate assumptions.

**The trust anchor:** The spec and CLI remain free and open source forever. They establish the data layer that commercial products can build on.

---

## Success Metrics

**Output metrics:**
- Spec published and usable (someone outside the project can validate a brew file against it)
- At least 3 example files covering different brew methods
- JSON Schema passes validation against all examples
- A user can install BrewLog, log a brew, and view history in under 2 minutes
- Works on macOS, Linux, and Windows (Python 3.11+)

**Learning metrics:**
- Do people log brews consistently over weeks/months?
- What fields do they actually use vs. skip?
- Do coffee professionals express interest when shown the spec and tool?
- What conversations happen when we use this as a talking point with roasters?

---

## Technical Constraints

- Solo developer — every decision must optimize for one person's bandwidth
- Zero infrastructure cost — no servers, no databases, no hosting (except GitHub Pages for the site)
- Python-only — leverage existing dependencies, avoid adding new languages
- Offline-first — everything runs locally, network is never required
- Open source — spec and tooling are public from day one

---

## Assumptions & Risks

**Assumptions:**
- An open brew spec doesn't already exist (needs verification — research BeerXML adaptations, SCA standards, existing coffee data formats)
- Home brewers who use the terminal are a viable audience for initial validation
- Starting with a CLI doesn't limit future growth (the spec is the real asset, not the tool)
- YAML/JSON is the right format (vs. XML like BeerXML)
- Coffee professionals will engage with tooling built on an open standard they trust

**Risks:**
- **Spec design is hard** — getting the fields right on the first try is unlikely
  - Mitigation: Ship v0.1 fast, iterate based on real usage, keep backward compatibility simple
- **Audience too narrow** — terminal-only users are a small market
  - Mitigation: The CLI is for learning, not market capture. The spec is the real product.
- **Scope creep** — temptation to add commercial features or jump to cloud before the spec is validated
  - Mitigation: This repo stays focused on the open standard and CLI. Commercial features live elsewhere.

---

## Competitive Landscape

**Open standards:**
- **BeerXML** — Open spec for beer recipes. Widely adopted. Proves the model works. Coffee has no equivalent.
- **SCA Protocols** — Specialty Coffee Association has brewing standards but no open data format.

**Coffee tools:**
- **Beanconqueror** — Open source, feature-rich, but complex. No open data spec. If they adopted BrewSpec, that's a win (ecosystem adoption), not a threat.
- **Various timer/tracking apps** — Proprietary, single-platform, no data export. Exactly the lock-in problem we solve.

**Our position:**
- **Open standard.** No one else is building this. The spec is our moat — if it becomes the way coffee data is described, everything built on top has a structural advantage.
- **Ecosystem play.** We don't need to build every tool. We need to build the data layer that every tool uses.

**Founder advantage:** Barista experience + tech consulting = the intersection of domain knowledge and technical execution that this market needs.
