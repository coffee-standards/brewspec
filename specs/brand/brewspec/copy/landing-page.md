# Copy: BrewSpec — Landing Page

**Product:** BrewSpec
**Surface:** Landing page — brewspec.coffee
**Author:** marketing-comms
**Created:** 2026-02-25
**Brand guidelines:** specs/brand/brewspec/brand-guidelines.md
**Status:** Approved
**Approved by:** Scott Luengen — 2026-02-25

> **Note for architect**: Copy is approved. Use this document for layout and component design.
> Do not alter copy without returning to marketing-comms.

---

## Surface Brief

**Goal of this surface:** A visitor should leave knowing what BrewSpec is, what it covers, why it exists, and where to go next — whether they are a tool builder evaluating it as a dependency or a coffee professional trying to understand what their tools are built on.

**Primary CTA:** View the schema

**Secondary CTA:** Browse examples

**Audience entering this surface:** Direct navigation, GitHub referrals, and word-of-mouth from the developer and specialty coffee communities. Both tool builders and brew-literate coffee professionals land here.

---

## Copy by Section

---

### Section 1: Hero

**Purpose:** State clearly what BrewSpec is. Earn a scroll from both a developer scanning for "what is this" and a barista trying to understand if this is relevant to them.

**Headline:**
> Coffee brewing, precisely described.

**Subheadline:**
> BrewSpec is a free, versioned data format for coffee brew records — method, dose, water, grind, extraction, result. Build on it. Log with it. Export from one tool, import into another.

**CTA button — primary:**
> View the schema

**CTA button — secondary:**
> Browse examples

**Notes:** "Coffee brewing, precisely described." carries weight at headline scale — "precisely" signals a schema with real structure, not a loose notes format, and the phrase works for both the barista and the developer. The subheadline gives both audiences what they need: brew-literate people see familiar entities (dose, water, grind, extraction, result); builders see the technical framing (versioned, free, format). The two CTAs split the audience naturally — builders go to the schema; curious coffee people go to examples. "An open format" in the subheadline rather than "the open format" is intentional — adoption will determine whether BrewSpec becomes the standard; the page does not claim that.

---

### Section 2: What It Covers

**Purpose:** Show the scope of the spec concretely. Both the barista and the tool builder should read this and know exactly what's described. The five-group structure mirrors how any barista thinks about a brew session.

**Section headline:**
> Everything you need to describe a brew.

**Intro sentence:**
> BrewSpec covers the full record — what went in, what the setup was, and what came out.

**Five field groups (presented as labelled lists):**

---

**Brew**
- Brew date (date-only or full datetime)
- Brew type (espresso, pour over, immersion, hybrid)
- Dose (g)
- Water weight (g) and temperature (°C)
- Brew method (freeform — "Hario V60", "AeroPress")
- Grind setting (espresso through coarse)
- Duration (seconds)
- Brew-process notes

**Coffee**
- Origin
- Roast date
- Type (single origin, blend)
- Varietal
- Process (washed, natural, honey, etc.)

**Water**
- Dissolved solids (ppm)

**Equipment**
- Grinder model
- Brewer model

**Result**
- TDS and extraction yield
- Brix
- Tasting notes (sensory description — kept separate from process notes)
- Ratings: overall, fragrance, aroma, flavour, acidity, aftertaste, sweetness, mouthfeel — aligned to SCA cupping dimensions

---

**Closing line:**
> All fields optional except date, type, dose, and water weight. Record what you measure. Leave the rest blank.

**Notes:** The five-group layout separates inputs from outputs — a structure any barista will recognise from dial-in sheets. The closing line matters: it signals to both audiences that you don't need a refractometer to use this. Tool builders need to know which fields are required; home brewers need to know the schema won't demand measurements they can't take.

---

### Section 3: Examples

**Purpose:** Show the spec in action. The two examples together show the full range — a builder or barista can read both and immediately understand what BrewSpec looks like in practice. The code samples are the proof of concept.

**Section headline:**
> See what a brew looks like.

**Intro line:**
> A minimal record with just the required fields. A full record with everything populated.

---

**Code block — left/top**

Label:
> Pour over — required fields only

```yaml
brewspec_version: "0.6"
brews:
  - date: "2026-02-25"
    type: "pour_over"
    dose_g: 18
    water_weight_g: 280
```

---

**Code block — right/bottom**

Label:
> Espresso — full record

```yaml
brewspec_version: "0.6"
brews:
  - date: "2026-02-25T08:30:00Z"
    type: "espresso"
    dose_g: 18
    water_weight_g: 36
    water_temp_c: 94
    grind: "espresso"
    duration_s: 28
    method: "La Marzocco Linea Mini"
    notes: "Re-calibrated grinder after three weeks"
    coffee:
      name: "El Paraiso Washed Castillo"
      roast_date: "2026-02-10"
      type: "single_origin"
      origins:
        - country: "Colombia"
          region: "Huila"
          varietal: "Castillo"
    water:
      ppm: 120
    equipment:
      grinder: "Niche Zero"
      brewer: "La Marzocco Linea Mini"
    result:
      tds: 9.2
      ey: 19.8
      brix: 4.6
      tasting_notes: "Dark chocolate, orange peel, long clean finish"
      ratings:
        overall: 4
        fragrance: 4
        aroma: 4
        flavour: 5
        acidity: 4
        aftertaste: 4
        sweetness: 3
        mouthfeel: 3
```

**Notes:** The pour over uses date-only format — the more natural input for most users and the format BrewLog defaults to. The espresso uses full datetime, showing the alternative. Both use realistic field values, not toy placeholders. The minimal example makes the barrier to entry obvious: four fields. The espresso example is rich but not intimidating — any working barista will recognise every field. Side-by-side layout on desktop; stacked on mobile.

---

### Section 4: Who It's For

**Purpose:** Make both audiences feel explicitly seen. Use their real vocabulary and describe their actual situation — not a generic "coffee enthusiast" or "developer" framing.

**Section headline:**
> Built for the people who handle brew data.

---

**Card — For tool builders**

**Card headline:**
> For tool builders

**Card body:**
> Building a brew logger, a roasting app, or a recipe platform? BrewSpec is a shared format you can build against instead of defining your own. JSON Schema-validated. Version-controlled with documented migration paths between versions. Apache 2.0 — use it in anything.
>
> The schema lives at brewspec.coffee/schema/v0.6.json. The spec document covers every field, validation rules, and the expected validation pipeline.

---

**Card — For coffee professionals and home brewers**

**Card headline:**
> For coffee professionals and home brewers

**Card body:**
> If you log brews — on paper, in a spreadsheet, in an app — BrewSpec is the format your data can travel in. Export from one tool, import into another. No locked-in proprietary format.
>
> BrewLog is the reference CLI implementation. Free, local, no account required. Log a brew in under a minute. Your data is yours.

**Notes:** The tool builder card is more technical because that's the right register for that audience. The coffee professional card is warmer and focuses on outcome (portability, no lock-in). BrewLog is mentioned once in the second card as the concrete "try it" path — grounding the standard in something you can actually run. Neither card uses enthusiasm language ("you'll love it") — they state what the thing does.

---

### Section 5: The Standard

**Purpose:** Address the "should I trust this?" question directly. This is the stability signal developers need before committing to a dependency. Keep it short — the copy answers the questions without selling.

**Section headline:**
> Open, versioned, and maintained.

**Body:**
> BrewSpec is Apache 2.0. Free to use in commercial and open source projects. The schema is JSON Schema (Draft 2020-12), hosted at a stable URL, and versioned with a `brewspec_version` const inside every brew file.
>
> Breaking changes follow a documented migration path. Every schema version is archived. A brew file tells you exactly which version of the spec it was written against — there's no guessing.

**Inline link:**
> github.com/coffee-standards/brewspec

**Notes:** Short by design. Answers license, versioning, and stability in four sentences. The GitHub link signals openness — read the source, file issues, submit PRs. This is for the developer who has been scanning the page and now wants to know if it's worth adopting. Do not add more copy to this section.

---

### Section 6: Footer / CTA

**Purpose:** Close the page with clear next steps. One action for builders, one for users.

**Footer headline:**
> Start using BrewSpec.

**CTA — primary:**
> View the schema
> brewspec.coffee/schema/v0.6.json

**CTA — secondary:**
> Try BrewLog
> github.com/coffee-standards/brewspec

**Footer attribution line:**
> BrewSpec is open source software released under the Apache 2.0 License.
> Schema and spec maintained at github.com/coffee-standards/brewspec.

---

## Microcopy

| Element | Copy |
|---------|------|
| Nav — schema link | Schema |
| Nav — spec link | Spec |
| Nav — examples link | Examples |
| Nav — GitHub link | GitHub |
| Hero CTA — primary | View the schema |
| Hero CTA — secondary | Browse examples |
| Code block label — minimal | Pour over — required fields only |
| Code block label — full | Espresso — full record |
| Footer CTA — builder | View the schema |
| Footer CTA — user | Try BrewLog |
| Footer attribution | BrewSpec is open source software released under the Apache 2.0 License. |

---

## SEO

| Element | Copy |
|---------|------|
| `<title>` | BrewSpec — An open format for coffee brews |
| Meta description | BrewSpec is a free, open data format for describing coffee brews. JSON Schema-validated, Apache 2.0. For tool builders and coffee professionals. |
| H1 (may differ from display headline) | An open format for describing a coffee brew |
| Primary keyword | open coffee data format |
| Secondary keywords | coffee brew schema, BrewSpec, coffee JSON schema, brew data standard, coffee tool interoperability |

---

## Open Questions

All questions resolved. Copy approved 2026-02-25.
