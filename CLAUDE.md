# endless_sites — Session Instructions

## Goal
Find local businesses in Columbia, MD with no website, build a polished static demo site for each one, iterate with the human owner until approved, and surface owner contact info once 5 sites reach "approved" status.

## Pipeline States
A business moves through these statuses in order:
`researching` → `prototype` → `in_review` → `approved` | `abandoned`

- **researching** — candidate found, data being gathered, `meta.json` skeleton exists
- **prototype** — `fill-template.py` has run, `index.html` generated
- **in_review** — presented to user, awaiting decision
- **approved** — user confirmed ready to pitch; count toward milestone
- **abandoned** — dropped; immediately begin research on a replacement

## Rules
1. **Never** mark a site `approved` without explicit user confirmation ("Approve").
2. Keep 2–3 sites in `prototype` or `in_review` at all times.
3. When a site is abandoned, start researching a replacement immediately.
4. Run `python3 scripts/check-milestone.py` after every status change.
5. Deploy to Cloudflare Pages before presenting for review so the user has a live URL.

## Milestone
Target: **5 approved sites**. When reached, print the contact sheet (from `check-milestone.py`) and ask the user if they want outreach emails drafted.

## Workflow Steps
1. Search for Columbia, MD businesses (zip 21044, 21045, 21046) with no website
2. Fill `meta.json` with gathered data
3. Run `bash scripts/new-site.sh <slug>` to scaffold the site directory
4. Read the scaffolded `meta.json` before writing it (Write tool requires a prior Read)
5. Fill `meta.json` with complete research data
6. Run `python3 scripts/fill-template.py <slug>` to generate the site
7. Add the new business card to `index.html` (the GitHub Pages portfolio) — use the hero image URL from meta.json at `w=600`. Card format:
   ```html
   <a href="sites/<slug>/index.html" class="card">
     <div class="card__preview" style="background-image: url('<hero_image_url w=600>');"></div>
     <div class="card__body">
       <div class="card__category" style="color: <accent-hex>;">Category Label</div>
       <div class="card__name">Business Name</div>
       <div class="card__address">Street · City, State Zip</div>
       <span class="card__status">Prototype</span>
     </div>
   </a>
   ```
8. Commit and push to dev branch, then push dev→main and dev→staging (see Git section below)
9. Present to user: site summary, file path, GitHub Pages URL
10. Record user decision in `meta.json` `review_log[]`
11. If iterate: edit directly, re-present. If approve: update status, run check-milestone. If abandon: update status, start research.

## Scripts
- `bash scripts/new-site.sh <slug>` — scaffold site directory from template
- `python3 scripts/fill-template.py <slug>` — generate site from meta.json data
- `python3 scripts/check-milestone.py` — show progress, surface contacts at milestone

## Git — Push Protocol
GitHub Pages deploys on push to `main` (the `github-pages` environment only allows the default branch). Always push to dev first, then to both `main` and `staging`. **Never force push.**

```bash
git push -u origin claude/local-business-static-sites-P3Fqm
git push origin claude/local-business-static-sites-P3Fqm:main
git push origin claude/local-business-static-sites-P3Fqm:staging
```

Before pushing dev→main or dev→staging, check for divergence:
```bash
git log HEAD..origin/main --oneline
git log HEAD..origin/staging --oneline
```
If staging has commits not on dev (e.g. workflow tweaks made directly on staging), cherry-pick them to dev first, then push normally. Any file that belongs in the repo long-term (GitHub Actions workflow, `index.html`) must live on the dev branch — never staging-only.

GitHub Pages portfolio URL: `https://rosstastic.github.io/endless_sites/`  
Individual site paths: `sites/<slug>/index.html`

## Photo Sourcing (Unsplash)
Unsplash blocks all server-side fetches (403), so photos cannot be verified programmatically.

**CRITICAL:** Only old-format IDs (`photo-XXXXXXXXXX-XXXXXXXXXXXX`) work as CDN image URLs. New-format slugs (e.g. `ebNZJGWd4zY`) are Unsplash page slugs only — they do NOT work as `images.unsplash.com/{slug}` CDN paths and will show broken images.

To find confirmed old-format IDs:
1. Google: `unsplash "photo-XXXXXXXXXX"` — if the first result is a direct `images.unsplash.com/photo-...` URL, the ID is valid
2. Google: `site:unsplash.com/photos "keyword"` returns new-format slugs — **do not use these as CDN URLs**
3. Confirmed working IDs already in use (safe to reuse in individual site galleries):
   - Food/BBQ: `photo-1555992336-03a23c7b20ee`
   - Food overhead: `photo-1504674900247-0877df9cc836`
   - Tacos: `photo-1565299624946-b28f40a0ae38`
   - Cafe/coffee: `photo-1509042239860-f550ce710b93`
   - Nails: `photo-1604654894610-df63bc536371`

Use as: `https://images.unsplash.com/photo-XXXXXXXXXX-XXXXXXXXXXXX?w=1400&q=80&fit=crop`

## Template Routing
`fill-template.py` picks the template based on the first keyword match in `CATEGORY_TEMPLATES`. The category string in `meta.json` must be set deliberately:
- `"Korean Restaurant"` → restaurant template (dark cinematic)
- `"Salvadoran Cafe"` → cafe template (warm parchment) — use "Cafe" not "Restaurant" to avoid routing to restaurant template
- Check `CATEGORY_TEMPLATES` in `fill-template.py` when adding new cuisine types

## Business Research
Most restaurant/business listing sites (Yelp, Grubhub, DoorDash) return 403 on WebFetch. Use WebSearch instead — search results provide enough data (address, phone, hours, menu items) without needing to load the page directly.

To verify a business has no website: Google `"<business name>" Columbia MD site:` and check for a standalone domain vs. only delivery/aggregator listings.

## Key Files
- `businesses.json` — master registry and milestone counter
- `index.html` — GitHub Pages portfolio (update whenever a new site is added)
- `sites/<slug>/meta.json` — per-business data and workflow status
- `templates/cafe/`, `templates/restaurant/`, `templates/salon/` — the three template families (never edit for a specific site)
- `.github/workflows/deploy-pages.yml` — triggers gh-pages deploy on push to staging
