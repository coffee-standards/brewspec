# Brand Guidelines: BrewSpec

**Product:** BrewSpec
**Author:** marketing-comms
**Created:** 2026-02-25
**Status:** Approved
**Approved by:** Scott Luengen — 2026-02-25

---

## Audience

### Primary Audience

**Who they are:** Tool builders — developers building coffee apps, brew trackers, roasting software, or recipe platforms who need a schema to build against rather than invent one. They read JSON Schema. They care about versioning, documented breaking changes, and a stable canonical URL.

**What they want:** A well-maintained, correctly designed data format they can adopt as a dependency without worrying it will be abandoned or arbitrarily changed.

**What they're not:** Casual home brewers who have never heard of a schema. That's Calibrate Coffee's audience. BrewSpec.org does not explain what a data format is.

### Secondary Audience

**Who they are:** Coffee professionals and serious home brewers who are brew-literate — baristas, roasters, home enthusiasts who understand dose, grind, extraction yield, and method, even if they've never opened a terminal. They can read a YAML file describing a coffee brew and immediately recognise what's being represented.

**What they want:** Confidence that the tools they use are built on something portable — that their data isn't trapped in a proprietary format that will disappear.

**What they're not:** Technically disinterested. They understand the brew entities. They don't need to understand JSON Schema to get value from the page.

---

## Positioning

### One-Line Positioning Statement

> BrewSpec is an open data format for describing coffee brews — a shared schema that lets tools exchange, store, and analyse brew data without building their own from scratch.

### Elevator Pitch

BrewSpec is an open, versioned data format for describing a coffee brew — method, dose, water, grind, duration, extraction, result. It's free, Apache 2.0, and built on JSON Schema. If you're building a tool that handles brew data, this is a shared format your data can travel in.

### Core Value Props

Ranked by importance to the primary audience:

1. **A stable schema to build against** — Version-controlled, JSON Schema-validated, with a documented migration path between versions. Not a napkin spec someone posted to a forum.
2. **Interoperability by design** — Data written in BrewSpec works across any tool that adopts the format. The schema is the contract.
3. **Open and permanently free** — Apache 2.0. No licensing fee, no governance fee. The spec is yours to use in commercial and open source projects.
4. **Grounded in how coffee actually works** — Covers method, dose, water, grind, TDS, extraction yield, SCA-aligned tasting dimensions. Not a generic activity-log schema with a coffee theme.

---

## Voice and Tone

### Voice (consistent across all copy)

Voice is who we are. It doesn't change based on context.

The BrewSpec voice is the voice of a confident, technically fluent practitioner — someone who makes very good espresso and also writes software. They write clearly, cite specifics, and have no patience for marketing language. They respect the reader's time and intelligence. A person wrote this; it doesn't read like a committee spec or a startup pitch.

| We are | We are not |
|--------|------------|
| Direct — say the thing plainly | Hedging — "may potentially help with..." |
| Technically fluent — assume the reader knows coffee | Jargon-heavy — acronym soup without context |
| Human — a person wrote this | Corporate — "solutions", "platforms", "leverage" |
| Specific — field names, version numbers, concrete examples | Generic — "track everything", "manage your data" |
| Confident without hype — let the spec speak | Superlative-laden — "world-class", "powerful", "revolutionary" |
| Community-minded — this is infrastructure others build on | Promotional — we're not selling; we're publishing |

### Tone (adjusts by context)

Tone is how we express our voice in a given situation.

| Context | Tone adjustment |
|---------|-----------------|
| Hero headline | Confident and precise — a strong claim at large type, no exclamation marks |
| Value props / feature descriptions | Specific and factual — reads like a thoughtful changelog entry, not an ad |
| Code examples | Neutral and realistic — real field names, plausible values, no toy data |
| Documentation / spec reference | Precise and technical — facts, not persuasion |
| CTA buttons | Plain and action-oriented — "View the schema", "Browse examples" |
| GitHub / community context | Collegial — contributor-to-contributor, not brand-to-user |

---

## Language

### Use These Words

Words and phrases that feel native to our voice and audience:

- "open format" / "open standard" — it's what it is; the audience understands these terms
- "schema" — the primary audience knows this word; use it without qualification
- "BrewSpec-compliant" — for tools that adopt the format
- "validate" / "validation" — specific and meaningful; use it when describing JSON Schema behaviour
- "portable" — captures the data-freedom value in one word
- "tool builders" — more precise than "developers" for this audience
- "interoperable" — one word that replaces a sentence
- "extraction yield", "TDS", "dose", "grind setting" — use the words coffee people actually use; do not genericise them
- "brew record" — the concrete thing a BrewSpec file contains; prefer over "data" or "log entry"
- "migration path" — the correct term for version upgrade documentation; use it

### Avoid These Words

| Avoid | Use instead | Why |
|-------|-------------|-----|
| "Elevate" | Say the specific thing | Vague and overused |
| "Unlock" | Say the specific thing | Gamification language; not fitting here |
| "Seamless" | "Works without modification" or be specific | Says nothing |
| "Powerful" | Cite the specific capability | Unearned modifier |
| "Journey" | Drop it | Not a journey |
| "Platform" | "Standard", "format", "spec" | Platform implies a product; this is a spec |
| "Revolutionise" | Drop it | Overpromises |
| "Coffee lover" | "Home brewer", "barista", "tool builder" | Vague; the audience has a name |
| "Modern" | Drop it or be specific | Filler word |
| "The open data standard" | "An open data format" | Adoption will determine whether it becomes the standard — the page cannot claim that |
| "World-class" | Drop it | Unearned claim |
| "Game-changing" | Drop it | Startup cliche |
| "Ecosystem" | "The tools that use BrewSpec" or be specific | Jargon when used loosely |

### Vocabulary Reference

Key terms and how we use them — consistency across all copy:

| Term | How we use it | Notes |
|------|---------------|-------|
| BrewSpec | Always capitalised as written — "BrewSpec" | Never "Brew Spec" (two words) or "brewspec" in prose |
| brew record | A single brew entry in a BrewSpec file | Prefer over "log entry" or "data point" |
| schema | The JSON Schema file that defines valid BrewSpec documents | Lowercase in prose; use with the version when specific: "the v0.4 schema" |
| spec | The specification document describing the format | Lowercase; "the spec" is fine in prose |
| tool builder | A developer building a coffee tool that handles brew data | Preferred over "developer" when the audience is specifically people building on BrewSpec |
| BrewLog | The reference CLI implementation of BrewSpec | Always "BrewLog" — capitalised as written |
| Apache 2.0 | The license | Full name on first mention; "Apache 2.0" thereafter |
| JSON Schema | The validation framework | Always "JSON Schema" — capitalised as written |

---

## Visual Language Direction

> Note: The Colour Direction subsection reflects the live implemented palette — these are authoritative values, not direction. Typography, spacing, and imagery subsections define intent and constraints for visual design decisions not yet fully resolved in implementation.

### Colour Direction

**Feel:** Clean and modern with warmth. Not clinical white, not dark mode by default, not styled like a coffee-shop menu. The spec is a precise technical artifact; the site should feel like someone took the time to present it well.

These are the live palette values from the implemented site — not aspirational direction. Use them exactly.

**Palette:**

| Role | Hex | Notes |
|------|-----|-------|
| Background | `#F7F5F2` | Off-white with warmth — not pure white. Clean and readable. |
| Text (primary) | `#1A1814` | Near-black with warmth — not pure black. Readable without harshness. |
| Text (muted) | `#6B6460` | Secondary text, metadata, captions. |
| Accent / CTA | `#C47B2B` | Warm ochre — used for buttons and active states. References extraction colour without being literal. One accent only; do not introduce a second. |
| Border | `#E8E4E0` | Subtle dividers and component boundaries. |
| Code block background | `#1E1E1E` | Standard dark background with syntax highlighting. Developer convention — do not fight it. |

### Typography Direction

**Feel:** Clean and readable — function over decoration.

- Headings: Strong, clean sans-serif at weight. Inter, DM Sans, or equivalent. No display fonts, no artisanal serifs.
- Body: Highly readable at 16–18px. Generous line height (1.6–1.7). This page has substantive prose; legibility is not optional.
- Code / schema examples: Monospace, properly syntax-highlighted. Code samples are primary content on this page — not appendix material.

### Spacing and Layout

- Generous whitespace throughout. The page breathes. Dense pages signal noise; a lean, well-spaced page signals confidence.
- Constrained single-column for text content — this is not a features grid. It is a spec reference with a human voice.
- Code examples are visually prominent — full width or near-full width on desktop. The examples are proof of concept; do not squeeze them into a sidebar or secondary column.
- Mobile must work. Primary audience is likely on desktop but the page is not desktop-only.

### Imagery Direction

- No stock photography.
- No illustrations.
- If any imagery is used: genuine coffee photography that looks like it was taken by someone who actually brews. Process-oriented — the act of brewing, not the finished cup in flatlay.
- Default preference: no imagery. Strong typography and well-presented code samples say more than a photo of a V60.

---

## Do / Don't Examples

Short copy examples showing the guidelines in action.

### Headlines

| Don't | Do |
|-------|----|
| "Elevate your coffee data experience" | "Coffee brewing, precisely described." |
| "The world's most seamless brew tracking standard" | "Every brew, recorded. Every detail, portable." |
| "Unlock the power of your brew data" | "Log the brew. Keep the data." |

### Value prop / feature descriptions

| Don't | Do |
|-------|----|
| "Powerful schema covering all your brewing needs" | "Covers method, dose, water, grind, TDS, and extraction yield. Validates against JSON Schema." |
| "Seamlessly integrate with any tool" | "Any tool that reads BrewSpec can consume your data. No custom parsers." |
| "A revolutionary open format for the modern barista" | "Apache 2.0. Version-controlled. Breaking changes follow a documented migration path." |

### CTA buttons

| Don't | Do |
|-------|----|
| "Get started today!" | "View the schema" |
| "Unlock BrewSpec" | "Read the spec" |
| "Join the revolution" | "Browse examples" |

### Describing the standard

| Don't | Do |
|-------|----|
| "BrewSpec is the open data standard for coffee" | "BrewSpec is an open data format for coffee brews" |
| "The world's leading coffee schema" | "Free, versioned, and Apache 2.0" |

---

## Open Questions

All questions resolved. Guidelines approved 2026-02-25.
