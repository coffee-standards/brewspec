# Infrastructure Reference

Operational infrastructure for BrewSpec. Source of truth for domains, hosting, and email — read by agents and humans when making deployment or configuration decisions.

**Last updated:** 2026-03-19

---

## Domain

| Domain | Purpose | DNS provider |
|--------|---------|--------------|
| `brewspec.coffee` | Landing page + spec home | TBD (check registrar) |

---

## Hosting

| Service | Platform | Source | Domain |
|---------|----------|--------|--------|
| Landing page | GitHub Pages | `site/` dir, Astro build | `brewspec.coffee` |

Deployed via GitHub Actions on push to `main`. CNAME record in `site/public/CNAME`.

---

## Repository

| Repo | Visibility | URL |
|------|------------|-----|
| `coffee-standards/brewspec` | Public | github.com/coffee-standards/brewspec |

---

## Email

| Address | Purpose |
|---------|---------|
| `hello@brewspec.coffee` | General contact |

Hosted via **iCloud Custom Email Domain** (Apple iCloud+). MX and TXT records managed in the DNS provider dashboard.
