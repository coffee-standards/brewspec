# Product Roadmap

This is the ideation backlog — a loose, human-written space for capturing product ideas, feature thoughts, and sequencing intuitions. It is not the manifest. Ideas here are inputs, not commitments.

**How this works:**
- Write freely. No YAML, no acceptance criteria required.
- Organise by product, then by rough theme or area.
- When an idea is ready, ask the PM to "process the roadmap" — it will read this file, propose manifest tasks, and check with you before writing anything.
- The PM will note which items it has processed so you know what's been picked up.

---

## BrewSpec Schema

### Schema Evolution
- **Next Steps
	- Temperature is a float, which is correct. Can we specify that maximum precision is really 1 decimal place? _(unclear if addressed in brewspec-v0.7 — verify before deleting)_
	- Coffee object needs a roaster field, can have the same origins roasted by different companies and blend names are tied to roasters
- **Longer-term**
	- Consider a `source` or `provenance` field to track whether a brew was logged by a CLI tool, a mobile app, a cafe POS, etc. Useful for data quality signals in aggregation.

### Landing Page
- 

### Adoption and ecosystem

- **Example library (ON HOLD)** — a richer set of example BrewSpec files covering edge cases: minimal valid brews, all-optional-fields populated, every brew type, every grind enum value. Makes it easier for tool builders to test against real-world variation.
- **Validator playground (ON HOLD)** — a simple web UI (could be static, no backend) where you paste a BrewSpec YAML and see validation results in real time. Lowers the barrier for tool builders evaluating adoption.
- **Registry of tools (ON HOLD)** — a simple list in the repo (or brewspec.coffee) of tools that support BrewSpec. Purely social/discovery, no infrastructure.

---

## BrewLog CLI
### Feedback
- 
### Core experience

- 
### Usability

- 

### Data management

- 