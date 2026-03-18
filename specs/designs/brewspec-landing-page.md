# Design: BrewSpec Landing Page (brewspec.coffee)

**Feature:** brewspec-landing-page
**Author:** architect
**Created:** 2026-02-25
**Input:** specs/brand/brewspec/copy/landing-page.md, specs/brand/brewspec/brand-guidelines.md
**Baseline:** n/a — new site
**Status:** Ready for Dev

---

## Overview

This document specifies the complete technical design for the BrewSpec landing page at brewspec.coffee. The site is a static Astro site hosted on GitHub Pages, sourced from the `coffee-standards/brewspec` repository alongside the schema. It has one page (the homepage) plus a served static asset (the JSON Schema file at `brewspec.coffee/schema/v0.4.json`). The landing page enables the schema `$id` to be updated from the GitHub raw URL to a stable, human-readable canonical URL, and gives tool builders and coffee professionals a clear reference point for the spec.

The design is driven directly from the approved copy document (`specs/brand/brewspec/copy/landing-page.md`) and brand guidelines (`specs/brand/brewspec/brand-guidelines.md`). All copy is fixed — no deviation without returning to marketing-comms. The key correction this design addresses: the copy document's Section 3 espresso example omits three SCA rating dimensions (fragrance, aroma, sweetness). The corrected complete example with all 8 dimensions is specified in Section 1.3.

---

## 1. Changes Required

### 1.1 Site Structure

The site is a single-page static site. There are no multi-page routes beyond the root. The router is flat — GitHub Pages serves `index.html` at the root, and the schema JSON file is a static passthrough asset in the `public/` directory.

**Pages and routes:**

| Route | File | Description |
|-------|------|-------------|
| `/` | `src/pages/index.astro` | Landing page — all six sections |
| `/schema/v0.4.json` | `public/schema/v0.4.json` | Schema file — served as static asset |

No 404 page is required for MVP. GitHub Pages provides a default 404.

**Anchor links (in-page navigation):**

| Anchor | Section |
|--------|---------|
| `#what-it-covers` | Section 2: What It Covers |
| `#examples` | Section 3: Examples |
| `#who-its-for` | Section 4: Who It's For |
| `#the-standard` | Section 5: The Standard |

The nav items `Schema`, `Spec`, and `Examples` are deep links or external links (see Section 1.6).

---

### 1.2 Astro Project Layout

The Astro site source lives in a `site/` subdirectory inside the `coffee-standards/brewspec` repo, alongside the schema and spec documents.

```
brewspec/                           ← repo root
├── brewspec.schema.json            ← existing: JSON Schema (current)
├── brewspec-v0.4.md                ← existing: spec document
├── examples/                       ← existing: example YAML files
├── tests/                          ← existing: schema test suite
├── versions/                       ← existing: archived schema versions
├── site/                           ← NEW: Astro site source
│   ├── astro.config.mjs            ← Astro config (base, output, adapter)
│   ├── package.json                ← Node dependencies
│   ├── tsconfig.json               ← TypeScript config (Astro default)
│   ├── .gitignore                  ← node_modules, dist
│   ├── public/                     ← Static assets — copied verbatim to output
│   │   ├── schema/
│   │   │   └── v0.4.json           ← Copy of brewspec.schema.json (with updated $id)
│   │   └── favicon.svg             ← Minimal text-based SVG favicon
│   └── src/
│       ├── layouts/
│       │   └── Base.astro          ← HTML shell, head, meta tags, global CSS import
│       ├── pages/
│       │   └── index.astro         ← Composes all section components
│       ├── components/
│       │   ├── Nav.astro           ← Navigation bar
│       │   ├── Hero.astro          ← Section 1: headline, subheadline, CTAs
│       │   ├── WhatItCovers.astro  ← Section 2: five field groups
│       │   ├── Examples.astro      ← Section 3: two code blocks side-by-side
│       │   ├── CodeBlock.astro     ← Reusable: labelled syntax-highlighted code block
│       │   ├── WhoItsFor.astro     ← Section 4: two audience cards
│       │   ├── AudienceCard.astro  ← Reusable: single audience card
│       │   ├── TheStandard.astro   ← Section 5: stability / license copy
│       │   └── Footer.astro        ← Section 6: footer CTAs and attribution
│       └── styles/
│           └── global.css          ← CSS custom properties, base reset, typography
└── .github/
    └── workflows/
        └── deploy-site.yml         ← NEW: GitHub Actions — build and deploy to Pages
```

**Rationale for `site/` subdirectory:** The schema, spec, and examples must remain at the repo root to preserve existing raw GitHub URLs. The site cannot occupy the root without polluting the schema namespace. A `site/` subdirectory keeps the Astro project self-contained without disturbing existing artifacts.

---

### 1.3 Corrected Espresso YAML Example

The copy document's Section 3 espresso example includes only 5 of 8 SCA rating dimensions under `result.ratings` (fragrance, aroma, and sweetness are missing). The BrewSpec v0.4 schema defines all 8 dimensions. The landing page must display a complete, schema-valid example.

The corrected complete espresso example (to be used in `CodeBlock` and in the copy of `Examples.astro`) is:

```yaml
brewspec_version: "0.4"
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
      origin: ["Colombia"]
      roast_date: "2026-02-10"
      type: "single_origin"
      varietal: "Castillo"
      process: "Washed"
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

All 8 dimensions present: `overall`, `fragrance`, `aroma`, `flavour`, `acidity`, `aftertaste`, `sweetness`, `mouthfeel`. Values are realistic and plausible for a well-pulled espresso. This example is schema-valid against the v0.4 schema.

---

### 1.4 Styling Approach

**Choice: Plain CSS with custom properties.** No Tailwind, no CSS-in-JS framework.

Rationale: Tailwind adds a build-time dependency (PostCSS, the Tailwind CLI or Vite plugin) and a non-trivial `node_modules` footprint for a five-section static page. The brand guidelines specify a small, precise palette and a simple single-column layout. Plain CSS with custom properties is sufficient, produces smaller output, and is readable by any contributor without framework knowledge. It also aligns with the project principle of minimal dependencies.

**CSS custom properties (design tokens):**

```css
:root {
  /* Colours */
  --color-bg:         #F7F5F2;   /* Off-white warm background */
  --color-text:       #1A1814;   /* Near-black warm text */
  --color-text-muted: #6B6560;   /* Secondary text — labels, captions */
  --color-accent:     #C47B2B;   /* Warm ochre — CTAs, active states */
  --color-accent-hover: #A3651F; /* Darkened ochre for hover state */
  --color-border:     #E2DED9;   /* Subtle border — card outlines, dividers */
  --color-code-bg:    #1E1E1E;   /* Dark code block background */
  --color-code-text:  #D4D4D4;   /* Default code text */

  /* Typography */
  --font-sans:   "Inter", "DM Sans", system-ui, sans-serif;
  --font-mono:   "JetBrains Mono", "Fira Code", "Cascadia Code", ui-monospace, monospace;

  --text-base:   1rem;       /* 16px */
  --text-lg:     1.125rem;   /* 18px */
  --text-xl:     1.25rem;    /* 20px */
  --text-2xl:    1.5rem;     /* 24px */
  --text-3xl:    2rem;       /* 32px */
  --text-4xl:    2.75rem;    /* 44px */
  --text-hero:   3.5rem;     /* 56px — headline only */

  --line-height-body: 1.7;
  --line-height-heading: 1.2;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold:   700;

  /* Spacing */
  --space-xs:   0.5rem;
  --space-sm:   1rem;
  --space-md:   1.5rem;
  --space-lg:   2.5rem;
  --space-xl:   4rem;
  --space-2xl:  6rem;

  /* Layout */
  --content-width: 720px;   /* Max width for text content */
  --wide-width:    1100px;  /* Max width for code example columns */
}
```

**Font loading:** Inter is loaded from Google Fonts via a `<link preconnect>` and a single font stylesheet request (weights 400, 500, 700). This is the only external network request on the page. JetBrains Mono is loaded for the code blocks from the same request. Fallback to system fonts if the network request fails — the page remains readable.

**Base reset and global styles:** A minimal custom reset (not `normalize.css`, not a library). Box-sizing, margin reset, body font/background/colour from custom properties.

---

### 1.5 Component Breakdown

Every component is an `.astro` file. Astro components render to static HTML at build time — no client-side JavaScript is shipped unless explicitly opted into. All components are zero-JS by default.

---

**`Base.astro` — Layout wrapper**

Props: `{ title: string, description: string }`

Renders:
- `<!DOCTYPE html>`, `<html lang="en">`, `<head>`, `<body>`
- In `<head>`: charset, viewport, `<title>` (from prop), `<meta name="description">` (from prop), Open Graph tags (`og:title`, `og:description`, `og:type: website`, `og:url`), canonical `<link>`, Google Fonts preconnect + stylesheet, global CSS import
- `<slot />` for page content
- SEO values from copy doc: `<title>BrewSpec — An open format for coffee brews</title>`, meta description from copy doc

---

**`Nav.astro` — Navigation bar**

Props: none (copy is static)

Renders:
- `<header>` / `<nav>` landmark
- Left: BrewSpec wordmark (plain text, links to `#top` / `/`)
- Right: four nav items from copy doc microcopy table:
  - `Schema` → `/schema/v0.4.json` (opens in new tab)
  - `Spec` → link to `brewspec-v0.4.md` in the GitHub repo
  - `Examples` → `#examples` anchor on the page
  - `GitHub` → `https://github.com/coffee-standards/brewspec` (opens in new tab)
- Mobile behaviour: at viewport widths below 640px, nav links collapse behind a hamburger toggle button. The toggle uses minimal inline `<script>` to add/remove a CSS class (`nav--open`) on the `<nav>` element. This is the only JavaScript on the page — approximately 5 lines.
- `<button aria-expanded aria-controls>` pattern for the hamburger. Nav links rendered in `<ul>` with `role="list"`.

---

**`Hero.astro` — Section 1**

Props: none (copy is static)

Renders:
- `<section id="hero">` containing:
- `<h1>` (SEO h1 from copy doc): `An open format for describing a coffee brew`
- Display headline (visually prominent, rendered as `<p class="hero-headline">`): `Coffee brewing, precisely described.`
- Subheadline paragraph: full subheadline copy from copy doc
- Two CTA buttons:
  - Primary: `<a href="/schema/v0.4.json">View the schema</a>` — styled as accent-coloured button
  - Secondary: `<a href="#examples">Browse examples</a>` — styled as outlined/ghost button

Note: The `<h1>` contains the SEO-optimised text. The display headline is a visually prominent paragraph, not a second h1. This preserves semantic correctness (one h1 per page) while matching the copy doc intent.

---

**`WhatItCovers.astro` — Section 2**

Props: none (copy is static)

Renders:
- `<section id="what-it-covers">`
- `<h2>`: `Everything you need to describe a brew.`
- Intro sentence paragraph
- Five field groups, each rendered as `<div class="field-group">` containing:
  - `<h3>` group label (Brew, Coffee, Water, Equipment, Result)
  - `<ul>` list of fields from copy doc
- Closing line paragraph

The five groups are laid out in a single column with generous vertical spacing on mobile and on desktop. The copy doc specifies no two-column grid for this section — single column matches the brand guideline for "constrained single-column for text content."

---

**`Examples.astro` — Section 3**

Props: none (copy is static; code content passed as string literals)

Renders:
- `<section id="examples">`
- `<h2>`: `See what a brew looks like.`
- Intro line paragraph
- Two `<CodeBlock>` components:
  - Left/top: label `Pour over — required fields only`, the minimal pour-over YAML
  - Right/bottom: label `Espresso — full record`, the corrected full espresso YAML (Section 1.3)
- Layout: CSS Grid — two equal columns (`1fr 1fr`) on desktop (viewport >= 768px); single stacked column on mobile

---

**`CodeBlock.astro` — Reusable code block**

Props: `{ label: string, code: string, language: string }`

Renders:
- `<figure>` wrapping `<figcaption>` (the label) and a `<pre><code>` block
- Syntax highlighting applied at build time (see Section 1.7)
- `<figcaption>` uses `--color-text-muted` and small caps / uppercase styling to match the label treatment in the copy doc
- `<pre>` background: `var(--color-code-bg)`, colour: `var(--color-code-text)`
- `overflow-x: auto` on `<pre>` for narrow viewports

---

**`WhoItsFor.astro` — Section 4**

Props: none (copy is static)

Renders:
- `<section id="who-its-for">`
- `<h2>`: `Built for the people who handle brew data.`
- Two `<AudienceCard>` components, side-by-side on desktop (CSS Grid, `1fr 1fr`), stacked on mobile

---

**`AudienceCard.astro` — Reusable audience card**

Props: `{ headline: string, body: string }` — body accepts HTML string for inline links

Renders:
- `<article>` with border (`var(--color-border)`), generous padding, subtle background offset
- `<h3>` headline
- Body copy (rendered via `<Fragment set:html={body} />` to support inline anchor tags)

---

**`TheStandard.astro` — Section 5**

Props: none (copy is static)

Renders:
- `<section id="the-standard">`
- `<h2>`: `Open, versioned, and maintained.`
- Two body paragraphs from copy doc
- Inline link to `github.com/coffee-standards/brewspec` (opens in new tab, `rel="noopener noreferrer"`)

---

**`Footer.astro` — Section 6**

Props: none (copy is static)

Renders:
- `<footer>` landmark
- `<h2>` (visually de-emphasised to not dominate): `Start using BrewSpec.`
- Two CTA elements:
  - Primary: `<a href="/schema/v0.4.json">View the schema</a>` — URL `brewspec.coffee/schema/v0.4.json` displayed as subtext below the button
  - Secondary: `<a href="https://github.com/coffee-standards/brewspec" rel="noopener noreferrer">Try BrewLog</a>` — GitHub URL as subtext
- Attribution paragraph: `BrewSpec is open source software released under the Apache 2.0 License. Schema and spec maintained at github.com/coffee-standards/brewspec.`

---

**`index.astro` — Page composition**

```astro
---
import Base from '../layouts/Base.astro';
import Nav from '../components/Nav.astro';
import Hero from '../components/Hero.astro';
import WhatItCovers from '../components/WhatItCovers.astro';
import Examples from '../components/Examples.astro';
import WhoItsFor from '../components/WhoItsFor.astro';
import TheStandard from '../components/TheStandard.astro';
import Footer from '../components/Footer.astro';
---
<Base
  title="BrewSpec — An open format for coffee brews"
  description="BrewSpec is a free, open data format for describing coffee brews. JSON Schema-validated, Apache 2.0. For tool builders and coffee professionals."
>
  <Nav />
  <main>
    <Hero />
    <WhatItCovers />
    <Examples />
    <WhoItsFor />
    <TheStandard />
  </main>
  <Footer />
</Base>
```

---

### 1.6 Navigation Behaviour

**Nav item link targets:**

| Label | URL | Behaviour |
|-------|-----|-----------|
| Schema | `/schema/v0.4.json` | New tab (`target="_blank"`) — downloads/displays JSON |
| Spec | `https://github.com/coffee-standards/brewspec/blob/main/brewspec-v0.4.md` | New tab |
| Examples | `#examples` | In-page anchor scroll |
| GitHub | `https://github.com/coffee-standards/brewspec` | New tab |

All external links include `rel="noopener noreferrer"`.

**Mobile navigation:**

On viewports narrower than 640px the horizontal nav list is hidden by default. A hamburger button (`☰` / `✕`) is shown. Clicking it toggles a `nav--open` class on the `<nav>` element, revealing the nav list as a stacked vertical menu. The JavaScript required is approximately:

```js
document.querySelector('.nav-toggle').addEventListener('click', () => {
  document.querySelector('.nav').classList.toggle('nav--open');
});
```

This is the only `<script>` tag on the page. It is inlined in `Nav.astro` rather than loaded as a separate file. No framework required.

---

### 1.7 Code Example Rendering — Syntax Highlighting

**Library: Shiki** (bundled with Astro — zero additional dependency).

Astro's built-in `<Code>` component uses Shiki for server-side syntax highlighting at build time. The highlighted HTML is emitted as static markup — no JavaScript is shipped to the browser for highlighting.

**Implementation:**

```astro
---
// In CodeBlock.astro
import { Code } from 'astro:components';
const { label, code, language } = Astro.props;
---
<figure class="code-block">
  <figcaption class="code-label">{label}</figcaption>
  <Code code={code} lang={language} theme="dark-plus" />
</figure>
```

**Theme choice:** `dark-plus` (VS Code dark theme) — consistent with developer expectation, visually close to the `#1E1E1E` background specified in brand guidelines. No custom theme required.

**Language:** `yaml` for both code blocks.

**Desktop layout — side by side:**

```css
.examples-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  max-width: var(--wide-width);
  margin: 0 auto;
}

@media (max-width: 767px) {
  .examples-grid {
    grid-template-columns: 1fr;
  }
}
```

On desktop the two code blocks sit side by side at equal width. On mobile they stack vertically, the minimal example above the full example.

---

### 1.8 Schema `$id` Update and Static Asset Serving

**Current `$id` in `brewspec.schema.json`:**
```json
"$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json"
```

**Target `$id` after landing page deployment:**
```json
"$id": "https://brewspec.coffee/schema/v0.4.json"
```

**How the file is served:**

1. The file `site/public/schema/v0.4.json` is a copy of `brewspec.schema.json` with the `$id` updated to `https://brewspec.coffee/schema/v0.4.json`.
2. Astro copies everything in `public/` verbatim to the build output directory (`dist/`). No processing occurs.
3. GitHub Pages serves the output directory. The file resolves at `https://brewspec.coffee/schema/v0.4.json`.

**Two copies, one source of truth problem:** There will temporarily be two copies of the schema — the repo root `brewspec.schema.json` and `site/public/schema/v0.4.json`. To keep them in sync:
- The GitHub Actions deployment workflow (Section 1.9) copies `brewspec.schema.json` to `site/public/schema/v0.4.json` and patches the `$id` before building, using a `jq` one-liner.
- This means the developer does not manually maintain two copies — the build pipeline generates `site/public/schema/v0.4.json` from the canonical source.
- The `site/public/schema/v0.4.json` file is `.gitignore`d inside `site/` — it is a build artifact, not a committed file.

**`jq` command in the workflow:**
```bash
jq '."$id" = "https://brewspec.coffee/schema/v0.4.json"' \
  brewspec.schema.json > site/public/schema/v0.4.json
```

This runs before `astro build`. The output file is in `public/` so Astro copies it as a static asset.

**MIME type:** GitHub Pages serves `.json` files with `Content-Type: application/json`. No configuration required.

**URL update in copy:** Section 4 (Who It's For, tool builder card) and Section 6 (footer) reference `brewspec.coffee/schema/v0.4.json`. These are hardcoded as text in those components. When the schema advances to v0.5, the copy in those components must be updated. This is not automated — it is a developer task at that point.

---

### 1.9 Build and Deploy — GitHub Actions

**Workflow file:** `.github/workflows/deploy-site.yml` in the `coffee-standards/brewspec` repo.

**Trigger:** Push to `main` branch. The workflow runs only when files under `site/` or `brewspec.schema.json` change (path filter applied), plus manual `workflow_dispatch`.

**GitHub Pages configuration:**
- Source: GitHub Actions (not the legacy `gh-pages` branch approach)
- Pages is enabled on the `coffee-standards/brewspec` repo settings with source set to GitHub Actions
- Custom domain: `brewspec.coffee` — configured via a `CNAME` file in `site/public/CNAME` containing `brewspec.coffee`

**Full workflow:**

```yaml
name: Deploy BrewSpec Site

on:
  push:
    branches: [main]
    paths:
      - 'site/**'
      - 'brewspec.schema.json'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: site/package-lock.json

      - name: Install jq
        run: sudo apt-get install -y jq

      - name: Patch schema $id and copy to public
        run: |
          mkdir -p site/public/schema
          jq '."$id" = "https://brewspec.coffee/schema/v0.4.json"' \
            brewspec.schema.json > site/public/schema/v0.4.json

      - name: Install dependencies
        working-directory: site
        run: npm ci

      - name: Build site
        working-directory: site
        run: npm run build

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Branch strategy:**
- Feature branch: `brewspec-landing-page` — all development happens here
- Pull request from `brewspec-landing-page` → `main`
- GitHub Pages deploys from `main` only
- After merge: delete `brewspec-landing-page` branch per project conventions

**Node version:** 20 LTS. Astro 4.x supports Node 18+; Node 20 is the current LTS.

---

### 1.10 Astro Configuration

```js
// site/astro.config.mjs
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://brewspec.coffee',
  output: 'static',
});
```

No adapter is required — GitHub Pages serves static HTML. `site` is set to the canonical URL so Astro can generate correct canonical links and sitemap entries. No `base` path is set — the site is served at the domain root, not a subpath.

---

## 2. Data Models

This is a static site. There are no Pydantic models, no SQLite schema, and no dynamic data layer. All content is authored directly in `.astro` component files as string literals. This section is intentionally absent.

---

## 3. CLI Interface

Not applicable — this is a web site, not a CLI tool.

---

## 4. Architecture Decision Records

### ADR-1: Plain CSS over Tailwind

**Context:** The brand guidelines specify a small, precise palette and a single-column layout. The architect must choose a styling approach.

**Options considered:**
1. Tailwind CSS — utility-first, popular in Astro projects
2. Plain CSS with custom properties — no framework, just a `global.css` file
3. CSS Modules — scoped styles per component

**Decision:** Plain CSS with custom properties.

**Rationale:** Tailwind adds meaningful build-time complexity (PostCSS plugin, class purging, `tailwind.config.js`) for a five-section single-page site with a fixed palette. CSS custom properties cover 100% of the design token needs. The resulting CSS is fully readable without Tailwind knowledge, which matters for an open source project where community contributors may not know Tailwind. CSS Modules is a reasonable alternative but adds import boilerplate in every component for what amounts to global design tokens — overkill for one page.

**Consequences:** No utility classes — every component owns its structural styles. The `global.css` owns the design tokens and reset. Scoped component styles use `<style>` blocks in `.astro` files (Astro scopes these automatically). No naming convention system needed — component names are the namespace.

---

### ADR-2: Shiki (built-in) over Prism or highlight.js for syntax highlighting

**Context:** The code examples are primary content. Syntax highlighting must work at build time (no runtime JavaScript).

**Options considered:**
1. Shiki via Astro's built-in `<Code>` component — zero additional dependency
2. Prism.js — widely used, requires either a runtime script or a build-time integration
3. highlight.js — similar tradeoff to Prism

**Decision:** Shiki via Astro's built-in `<Code>` component.

**Rationale:** Shiki is already bundled with Astro — adopting it adds zero dependencies. It runs at build time and emits static HTML with inline styles. No JavaScript is shipped to the browser. Prism and highlight.js both require either a runtime script or an additional Astro integration. Shiki's output is also higher quality for YAML specifically — its tokeniser is more accurate than Prism for this language.

**Consequences:** Syntax theme is tied to Shiki's theme library. `dark-plus` closely matches the `#1E1E1E` background intent in the brand guidelines. Changing the theme later is a single prop change in `CodeBlock.astro`.

---

### ADR-3: Single page over multi-page

**Context:** The copy doc defines six sections. These could be implemented as separate routes or a single scrolling page.

**Options considered:**
1. Single-page site — one `index.astro`, all sections on one scroll
2. Multi-page site — separate routes per section

**Decision:** Single page.

**Rationale:** The content volume is small — six sections, no deeply nested content, no user journeys requiring separate URLs. All sections are linked from the nav via anchor tags. A multi-page structure would require additional routing, layout duplication, and page transitions for no user benefit. The brand guidelines describe "a spec reference with a human voice" — a long-form scrolling page is the natural format for this kind of document-centric content.

**Consequences:** All nav anchor links resolve to the same page. In-page navigation uses smooth scroll (CSS `scroll-behavior: smooth` on `<html>`).

---

### ADR-4: Two copies of schema with build-time generation

**Context:** The schema `$id` must be updated to `brewspec.coffee/schema/v0.4.json`, and the file must be served at that URL. The canonical source is `brewspec.schema.json` at the repo root.

**Options considered:**
1. Manually maintain `site/public/schema/v0.4.json` as a committed copy
2. Generate `site/public/schema/v0.4.json` at build time from `brewspec.schema.json`
3. Redirect `brewspec.coffee/schema/v0.4.json` to the GitHub raw URL via a `_redirects` file

**Decision:** Generate at build time using `jq` in the GitHub Actions workflow.

**Rationale:** Option 1 (committed copy) creates a maintenance burden — the two files drift out of sync whenever the schema changes. Option 3 (redirect) keeps the GitHub raw URL as the canonical `$id` and defeats the purpose of the schema URL update. Option 2 ensures a single source of truth (`brewspec.schema.json`), with the `$id` patch applied automatically on every build.

**Consequences:** `site/public/schema/v0.4.json` is a build artifact and must be `.gitignore`d inside `site/`. A developer running `astro build` locally must run the `jq` patch step first, or the schema asset won't be present. This should be documented in the site `README` and can also be wired as a pre-build `npm` script.

---

## 5. Public Spec Document

Not applicable — this task produces a website, not a BrewSpec schema version.

---

## 6. File Manifest

All files are in the `coffee-standards/brewspec` repo on the `brewspec-landing-page` feature branch.

| File | Repo | Operation | Notes |
|------|------|-----------|-------|
| `site/astro.config.mjs` | brewspec | Create | Per Section 1.10 |
| `site/package.json` | brewspec | Create | Astro 4.x, no other dependencies |
| `site/tsconfig.json` | brewspec | Create | Astro default tsconfig |
| `site/.gitignore` | brewspec | Create | `node_modules`, `dist`, `public/schema/v0.4.json` |
| `site/public/CNAME` | brewspec | Create | Contains `brewspec.coffee` |
| `site/public/favicon.svg` | brewspec | Create | Minimal SVG favicon |
| `site/src/layouts/Base.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/pages/index.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/Nav.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/Hero.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/WhatItCovers.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/Examples.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/CodeBlock.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/WhoItsFor.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/AudienceCard.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/TheStandard.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/components/Footer.astro` | brewspec | Create | Per Section 1.5 |
| `site/src/styles/global.css` | brewspec | Create | Per Section 1.4 |
| `.github/workflows/deploy-site.yml` | brewspec | Create | Per Section 1.9 |
| `brewspec.schema.json` | brewspec | Modify | Update `$id` to `https://brewspec.coffee/schema/v0.4.json` |

**Note on `brewspec.schema.json`:** The `$id` must be updated in the canonical schema file at the repo root as well. The build pipeline generates `site/public/schema/v0.4.json` from this file, so the source of truth must already carry the new `$id`. This is a single-field change with no schema logic impact.

---

## 7. Test Strategy

The test strategy for a static site differs from a Python project. There is no Pytest suite. Tests are a combination of build-time validation, automated link checks, and an accessibility audit.

### AC-1: Build succeeds and produces valid HTML

| Test | Method | Expected |
|------|--------|----------|
| `astro build` exits 0 | Run `npm run build` in CI | Build completes without error |
| Output contains `index.html` | Assert `dist/index.html` exists after build | File present |
| Output contains schema asset | Assert `dist/schema/v0.4.json` exists after build | File present |
| HTML is valid | Run `npx html-validate dist/index.html` in CI | Zero validation errors |

### AC-2: Schema asset is valid JSON and carries correct `$id`

| Test | Method | Expected |
|------|--------|----------|
| Schema file is valid JSON | `python3 -c "import json; json.load(open('dist/schema/v0.4.json'))"` | No exception |
| `$id` is correct | `jq '."$id"' dist/schema/v0.4.json` | `"https://brewspec.coffee/schema/v0.4.json"` |
| Schema validates a known-good file | Run existing schema tests from `tests/` against `dist/schema/v0.4.json` | All pass |

### AC-3: Internal anchor links resolve

| Test | Method | Expected |
|------|--------|----------|
| `#what-it-covers` exists | `grep -q 'id="what-it-covers"' dist/index.html` | Match found |
| `#examples` exists | `grep -q 'id="examples"' dist/index.html` | Match found |
| `#who-its-for` exists | `grep -q 'id="who-its-for"' dist/index.html` | Match found |
| `#the-standard` exists | `grep -q 'id="the-standard"' dist/index.html` | Match found |

### AC-4: Copy accuracy — corrected espresso example present

| Test | Method | Expected |
|------|--------|----------|
| All 8 rating dimensions present | `grep -c "fragrance\|aroma\|flavour\|acidity\|aftertaste\|sweetness\|mouthfeel\|overall" dist/index.html` | Count >= 8 |
| Espresso example is schema-valid | Extract YAML block from built HTML, validate against `dist/schema/v0.4.json` | Passes validation |

### AC-5: Accessibility baseline

| Test | Method | Expected |
|------|--------|----------|
| WCAG AA colour contrast (text on background) | `npx @axe-core/cli dist/index.html` or manual check | `#1A1814` on `#F7F5F2` — contrast ratio ~16:1, passes AA |
| Accent on background | Compute contrast `#C47B2B` on `#F7F5F2` | Ratio >= 4.5:1 for AA |
| No images lacking alt text | `npx @axe-core/cli dist/index.html` | Zero alt-text violations |
| Nav toggle has aria-expanded | `grep -q 'aria-expanded' dist/index.html` | Match found |
| Landmarks present (main, nav, footer) | axe check or `grep` | `<main>`, `<nav>`, `<footer>` all present |
| Page title present | `grep -q '<title>BrewSpec' dist/index.html` | Match found |

### AC-6: No JavaScript required for core content

| Test | Method | Expected |
|------|--------|----------|
| Core content readable without JS | Verify all section content is in static HTML, not JS-rendered | All six sections present in `dist/index.html` source |
| Only JS is nav toggle | Count `<script>` tags | At most 1 `<script>` tag (the nav toggle) |

### AC-7: CNAME file present for custom domain

| Test | Method | Expected |
|------|--------|----------|
| CNAME present in output | Assert `dist/CNAME` exists | File present |
| CNAME content correct | `cat dist/CNAME` | `brewspec.coffee` |

---

## 8. Security Considerations

### Input Validation

This is a fully static site. There is no user input, no form submission, no dynamic rendering, and no database. The attack surface is minimal.

- No user-supplied input reaches the server or build pipeline.
- The only dynamic element (nav toggle) is a CSS class toggle on a local DOM element — no network calls, no user data.

### File I/O Safety

- The build pipeline reads one file (`brewspec.schema.json`) and writes one file (`site/public/schema/v0.4.json`) using `jq`. The `jq` command is deterministic and does not execute user input. The output is a static JSON file.
- The GitHub Actions workflow runs in an ephemeral environment with least-privilege permissions: `contents: read`, `pages: write`, `id-token: write`. No secrets are required or used beyond the GitHub-managed OIDC token for Pages deployment.

### Data Integrity

- The schema `$id` update is a single-field JSON patch applied deterministically by `jq`. The rest of the schema content is passed through unmodified.
- The test suite in AC-2 validates that the deployed schema file is valid JSON and validates known-good brew files — this detects any corruption introduced by the `jq` patch step.

### External Links

- All external links use `rel="noopener noreferrer"` — prevents `window.opener` access from linked pages.
- No `<script src>` external dependencies. Google Fonts is the only external resource, loaded via `<link>` (not script execution). The font request cannot execute arbitrary code.

### Content Security

- No user content is ever reflected on the page — all copy is authored at build time.
- No `innerHTML` assignments in JavaScript. The one `<script>` block (nav toggle) only touches CSS class names on a known DOM element.
- No cookies, no local storage, no tracking pixels.

### Trust Boundaries

```
Author (copy doc)  →  Build pipeline (Astro + jq)  →  Static HTML/JSON  →  GitHub Pages CDN  →  Browser
```

The only trust boundary with any sensitivity is the build pipeline's read of `brewspec.schema.json`. This file is version-controlled and reviewed through the normal PR process — no external data ingested at build time.

---

## 9. TDD Implementation Order

For a static site, "TDD" means writing the build and validation checks before writing the component implementations, then confirming each check passes as each component is built.

1. **Set up the project skeleton** — initialise `site/` with `npm create astro@latest`, confirm `astro build` runs and produces a `dist/` directory.
2. **Write AC-1 build test** — add `npm run build` to a local test script; confirm it passes on the empty scaffold.
3. **Write AC-7 test** — assert `dist/CNAME` exists; create `site/public/CNAME`; confirm test passes.
4. **Write AC-2 schema test** — write the `jq` patch command; assert output is valid JSON with correct `$id`; run it and confirm.
5. **Write AC-3 anchor link grep tests** — assert each `id` exists in `dist/index.html`; confirm they fail on the empty page.
6. **Implement `Base.astro` and `index.astro` skeleton** — add landmark elements; confirm AC-1 still passes.
7. **Implement `Nav.astro`** — confirm AC-3 anchor links still fail (sections not yet added); confirm nav toggle `<script>` present.
8. **Implement sections in order** — `Hero.astro`, `WhatItCovers.astro`, `Examples.astro` (with corrected espresso YAML per Section 1.3), `WhoItsFor.astro`, `TheStandard.astro`, `Footer.astro`. After each: run `astro build` and confirm no errors.
9. **Write AC-4 copy accuracy test** — assert all 8 rating dimension names appear in built HTML; confirm pass.
10. **Write AC-5 accessibility checks** — run `@axe-core/cli`; fix any violations before proceeding.
11. **Write AC-6 JS check** — assert `<script>` count; confirm at most 1 tag.
12. **Apply global CSS** — implement `global.css` per Section 1.4 design tokens; visually review.
13. **Wire GitHub Actions workflow** — add `.github/workflows/deploy-site.yml`; validate YAML syntax with `actionlint`.
14. **Full end-to-end check** — run all tests, confirm all pass, run `astro build`, visually inspect `dist/index.html`.
