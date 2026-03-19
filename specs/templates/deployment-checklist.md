# Deployment Checklist — brewspec repo

Use this checklist before every deployment to the public `coffee-standards/brewspec` repo.
Complete the relevant section(s) for what is being deployed.

---

## BrewSpec Schema / Spec Document

*Complete for every BrewSpec vX.Y release.*

### Pre-flight

- [ ] Reviewer verdict is **PASS** — never deploy on a FAIL
- [ ] All schema tests pass (`pytest tests/test_brewspec_schema.py`)
- [ ] All brewlog tests pass (`pytest brewlog/tests/`)
- [ ] Ruff is clean (`ruff check .` — zero errors)
- [ ] Feature branch is up to date with `main` (no divergence)

### Schema file

- [ ] `brewspec.schema.json` — `brewspec_version` const updated to `"X.Y"`
- [ ] `brewspec.schema.json` — `title` updated to `"BrewSpec vX.Y"`
- [ ] `brewspec.schema.json` — `$id` is correct (update if canonical URL changed)
- [ ] All new fields are present with correct types, constraints, and descriptions
- [ ] All removed/changed fields are absent or updated
- [ ] `additionalProperties: false` is in place on any new objects

### Examples

- [ ] All existing valid examples updated to `brewspec_version: "X.Y"`
- [ ] Valid examples still pass schema validation after update
- [ ] New valid examples added for new fields or formats (per spec ACs)
- [ ] New invalid examples added for new rejection cases (per spec ACs)
- [ ] No example files contain `brewspec_version: "X.(Y-1)"` or earlier

### Spec document

- [ ] Previous spec doc moved to archive — **move, don't copy:**
  - If `versions/brewspec-vX.(Y-1).md` does **not** exist: `git mv brewspec-vX.(Y-1).md versions/`
  - If `versions/brewspec-vX.(Y-1).md` **already exists** (e.g. pre-archived): `git rm brewspec-vX.(Y-1).md` (the copy in `versions/` is authoritative — no duplicate needed)
  - Verify `brewspec-vX.(Y-1).md` is absent from the repo root after this step
- [ ] New spec doc written to repo root: `brewspec-vX.Y.md`
- [ ] Spec doc contains: Overview, Field Reference, What Changed, Validation, Backward Compatibility
- [ ] Field reference table is complete — every schema field has a row
- [ ] Breaking changes are listed with migration steps
- [ ] Validation section includes storage-time guidance

### README

- [ ] Version badge / current version reference updated to `vX.Y`
- [ ] Changelog or version history entry added for `vX.Y`
- [ ] Any new fields or examples referenced in the README are accurate

### Git

- [ ] All changed files staged and committed on the feature branch
- [ ] Commit message follows convention: `feat(schema): bump to vX.Y — [brief summary]`
- [ ] Feature branch merged to `main`
- [ ] Tag `vX.Y` created on `main` HEAD
- [ ] Tag pushed to remote: `git push origin vX.Y`
- [ ] Feature branch deleted locally: `git branch -d brewspec-vX.Y`
- [ ] Feature branch deleted remotely: `git push origin --delete brewspec-vX.Y`

### Landing page

- [ ] `Nav.astro` Spec link updated to `brewspec-vX.Y.md` (was `brewspec-vX.(Y-1).md`)
- [ ] Any hardcoded schema URL references in components updated to `brewspec.coffee/schema/vX.Y.json`
- [ ] Landing page `astro build` passes after copy changes
- [ ] Changes committed and pushed — GitHub Actions redeploys automatically

### Manifest

- [ ] `manifest.yaml` task `brewspec-vX.Y` status updated to `done`
- [ ] `completed_date` set to today

---

## BrewLog CLI

*Complete for every BrewLog vX.Y release.*

### Pre-flight

- [ ] Reviewer verdict is **PASS** — never deploy on a FAIL
- [ ] All brewlog tests pass (`pytest brewlog/tests/`)
- [ ] All schema tests pass (`pytest tests/test_brewspec_schema.py`)
- [ ] Ruff is clean (`ruff check .` — zero errors)
- [ ] Feature branch is up to date with `main`

### Package

- [ ] Version bumped in `brewlog/pyproject.toml` to `X.Y`
- [ ] Version bumped in `brewlog/src/brewlog/__init--.py` to `X.Y`
- [ ] Version in `pyproject.toml` matches the tag that will be created

### README / Docs

- [ ] `brewlog/README.md` updated if new commands were added
- [ ] New commands documented with usage and flag descriptions
- [ ] Removed or changed commands updated or removed from docs
- [ ] Any new dependencies documented in setup/install instructions

### Git

- [ ] All changed files staged and committed on the feature branch
- [ ] Commit message follows convention: `feat(brewlog): vX.Y — [brief summary]`
- [ ] Feature branch merged to `main`
- [ ] Tag `brewlog-vX.Y` created on `main` HEAD
- [ ] Tag pushed to remote: `git push origin brewlog-vX.Y`
- [ ] Feature branch deleted locally: `git branch -d brewlog-cli-vX.Y`
- [ ] Feature branch deleted remotely: `git push origin --delete brewlog-cli-vX.Y`

### Manifest

- [ ] `manifest.yaml` task `brewlog-cli-vX.Y` status updated to `done`
- [ ] `completed_date` set to today

---

## BrewSpec Landing Page

*Complete for landing page deployments.*

### Pre-flight

- [ ] Copy doc status is **Approved** (user sign-off on all copy)
- [ ] Brand guidelines status is **Approved**
- [ ] Build succeeds locally (`astro build` — no errors)
- [ ] Site renders correctly in browser at local preview URL
- [ ] All links on the page are valid (no 404s)

### Content

- [ ] All copy matches the approved copy doc exactly
- [ ] Version references on the page match the current schema version
- [ ] Schema `$id` URL on the page matches the canonical URL in `brewspec.schema.json`
- [ ] GitHub links point to correct repo and branch

### SEO / Meta

- [ ] `<title>` matches copy doc SEO section
- [ ] Meta description matches copy doc SEO section
- [ ] OG tags present (og:title, og:description, og:url)

### GitHub Pages

- [ ] `astro.config.mjs` site URL is set to `https://brewspec.coffee`
- [ ] GitHub Pages source is set to correct branch/directory in repo settings
- [ ] DNS for `brewspec.coffee` points to GitHub Pages

### Git

- [ ] Feature branch merged to `main`
- [ ] Feature branch deleted locally and remotely
- [ ] No tag required for landing page updates (continuous deployment via GitHub Pages)

---

## Adding new checklist items

When a new artifact is introduced to the brewspec repo (a new file type, new directory,
new convention), add a checklist item here before the next deployment. The reviewer should
flag any new artifact types they encounter that aren't covered by this checklist.
