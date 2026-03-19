# BUG-001: Favicon not showing on brewspec.coffee

**Status:** in_progress
**Severity:** low
**Product area:** frontend
**Date filed:** 2026-03-18
**Filed by:** user

---

## Description

The brewspec.coffee site no longer displays a favicon in the browser tab. Favicon asset files exist in `site/public/` and are referenced correctly in the `<head>` of `site/src/layouts/Base.astro`, so the issue is likely related to deployment, asset paths, or the build pipeline.

## Steps to reproduce

1. Navigate to https://brewspec.coffee in a browser
2. Observe the browser tab — no favicon is displayed

## Expected behaviour

The BrewSpec favicon should appear in the browser tab.

## Actual behaviour

Browser displays a generic cube icon instead of the BrewSpec favicon.

## Environment

- **URL:** https://brewspec.coffee
- **Screen / flow:** Any page
- **Auth state:** n/a (public site)
- **Browser:** All
- **Device:** All

## Affected spec

- Spec file: `specs/products/brewspec.md`
- Section / AC: n/a — no specific AC covers favicon presence

---

## Investigation notes

- Favicon files exist in `site/public/`: `favicon.ico`, `favicon.svg`, `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`
- `<link>` tags in `site/src/layouts/Base.astro` lines 33–38 reference these files correctly
- Possible causes: Astro build not copying public assets, GitHub Pages base path mismatch, or caching issue

---

## Resolution

### Root cause

The favicon SVG redesigned in commit `d553afa` used concentric thin rings (#1A1814, 28px and 20px stroke) on a cream background (#F7F5F2). At 16x16 and 32x32 pixels the rings became invisible, and the cream background blended with browser chrome — making the favicon effectively transparent. The browser fell back to the generic cube icon.

### Fix summary

Redesigned favicon SVG with high-contrast approach: dark rounded square background (#1A1814) with bold accent ring and centre dot (#C47B2B, 80px stroke). Regenerated all raster variants (16x16, 32x32 PNG, ICO, apple-touch-icon, android-chrome sizes) from the new SVG.

- PR / commit: `fix(site): redesign favicon for visibility at small sizes`

### Regression test added

- **Added:** no — favicon rendering is a visual/browser concern not testable in the current test suite
- **Test file:** n/a
- **Test name:** n/a

### Spec / AC updated

- **Updated:** not applicable
- **File + section:** n/a
- **Change:** n/a

### Architectural implication

- **ADR impact:** none
- **Summary:** n/a
