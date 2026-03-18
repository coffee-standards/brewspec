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
- [ ] Manifest changes committed to `main` in calibrate-coffee

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
- [ ] Manifest changes committed to `main` in calibrate-coffee

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

## Calibrate Coffee Backend

*Complete for every Calibrate Coffee FastAPI backend deployment.*

### Pre-flight

- [ ] Reviewer verdict is **PASS** — never deploy on a FAIL
- [ ] All tests pass (`pytest` — zero failures)
- [ ] Ruff is clean (`ruff check .` — zero errors)
- [ ] Feature branch is up to date with `main`

### Code

- [ ] New routers registered in `app/main.py` (`app.include_router(...)`)
- [ ] New schema changes have an Alembic migration file — **never modify the DB without a migration**
- [ ] Migrations run via FastAPI lifespan (`alembic_command.upgrade(cfg, "head")` in `lifespan()`) — do not add migrate steps to Dockerfile or railway.json
- [ ] No secrets or credentials in committed code

### Railway environment variables

Verify these are set in the Railway app service before deploying a change that touches auth, database, or CORS:

- [ ] `DATABASE_URL` — must be a **reference to the Railway Postgres service** (not a hardcoded sqlite:/// URL)
- [ ] `CLERK_JWKS_URL` — format: `https://<slug>.clerk.accounts.dev/.well-known/jwks.json` (no trailing slash)
- [ ] `CLERK_ISSUER` — format: `https://<slug>.clerk.accounts.dev` (**no trailing slash** — a trailing slash causes all JWT verifications to fail with 401)
- [ ] `FRONTEND_ORIGIN` — exact Vercel URL with no trailing slash (e.g. `https://calibrate-drab.vercel.app`). Update this whenever the frontend URL changes.
- [ ] `ENVIRONMENT=production`

### Deployment

- [ ] Railway deploys via **Dockerfile** — do not add a Procfile or startCommand in railway.json (see ADR-006)
- [ ] `railway.json` contains only health check config — no `startCommand` or `preDeployCommand`
- [ ] Health check endpoint `GET /healthz` returns `{"status": "ok"}` with HTTP 200
- [ ] After deploy, confirm Railway shows the service as **healthy** (green) and linked to the Postgres service

### Post-deploy verification

- [ ] `GET https://<railway-url>/healthz` returns 200
- [ ] Railway Postgres `users` and `brews` tables exist (migrations ran on startup)
- [ ] Sign in via the frontend and log a test brew — confirm it appears in the Railway Postgres `brews` table

### Git

- [ ] All changed files staged and committed on the feature branch
- [ ] Commit message follows convention: `feat(calibrate-backend): [brief summary]`
- [ ] Pull request created — **do not merge to `main` without user review**
- [ ] PR linked to the relevant manifest task

### Manifest

- [ ] `manifest.yaml` task status updated to `done`
- [ ] `completed_date` set to today
- [ ] Manifest changes committed to `main` in calibrate-coffee

---

## Calibrate Coffee Frontend

*Complete for every Calibrate Coffee React frontend deployment.*

### Pre-flight

- [ ] Reviewer verdict is **PASS** — never deploy on a FAIL
- [ ] All tests pass (`npm test` or `npx vitest run` — zero failures)
- [ ] TypeScript build is clean (`npm run build` — zero errors, zero type errors)
- [ ] Feature branch is up to date with `main`

### Code

- [ ] `@clerk/react` is used — **not** the deprecated `@clerk/clerk-react`
- [ ] Every authenticated API call passes a JWT: `const token = await getToken(); api(token)`
- [ ] `VITE_API_BASE_URL` is the env var name for the backend URL — **not** `VITE_API_URL`
- [ ] No secrets or API keys hardcoded in source
- [ ] `vercel.json` SPA rewrite rule is present (redirects all paths to `index.html`)

### Vercel environment variables

Verify these are set in the Vercel project settings before deploying:

- [ ] `VITE_CLERK_PUBLISHABLE_KEY` — `pk_test_...` for dev, `pk_live_...` for production
- [ ] `VITE_API_BASE_URL` — Railway backend URL, e.g. `https://calibrate-coffee-production.up.railway.app` (no trailing slash)
- [ ] After changing any env var in Vercel, trigger a **manual redeploy** — env var changes do not auto-redeploy

### Clerk configuration

- [ ] Vercel deployment URL is added to Clerk → **Configure → Paths → Application Paths** as an allowed redirect URL
- [ ] `FRONTEND_ORIGIN` in Railway is updated to match the Vercel URL (no trailing slash)
- [ ] If using a custom JWT template, confirm `getToken({ template: '...' })` matches the template name in Clerk

### Deployment

- [ ] Vercel root directory is set to `frontend/` in project settings
- [ ] Vercel detects the Vite framework automatically — no custom build command needed
- [ ] Deploy triggers automatically on push to `main`

### Post-deploy verification

- [ ] App loads at the Vercel URL without console errors
- [ ] Sign-in flow opens Clerk modal — user can sign in successfully
- [ ] Log a brew as a signed-in user — toast shows green "Brew logged"
- [ ] Navigate to History — the logged brew appears
- [ ] Click the brew in History — detail panel opens (desktop) or navigates to detail screen (mobile)
- [ ] Error states show in **ember red** (not bloom green)

### Git

- [ ] All changed files staged and committed on the feature branch
- [ ] Commit message follows convention: `feat(calibrate-frontend): [brief summary]`
- [ ] Pull request created — **do not merge to `main` without user review**
- [ ] PR linked to the relevant manifest task

### Manifest

- [ ] `manifest.yaml` task status updated to `done`
- [ ] `deployed_url` set to the Vercel URL
- [ ] `deployed_date` set to today
- [ ] Manifest changes committed to `main` in calibrate-coffee

---

## Adding new checklist items

When a new artifact is introduced to the brewspec repo (a new file type, new directory,
new convention), add a checklist item here before the next deployment. The reviewer should
flag any new artifact types they encounter that aren't covered by this checklist.
