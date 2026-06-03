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
4. Fill `meta.json` with complete research data
5. Run `python3 scripts/fill-template.py <slug>` to generate the site
6. Deploy: `wrangler pages deploy sites/<slug>/ --project-name=endless-<slug>`
7. Present to user: site summary, file path, live URL
8. Record user decision in `meta.json` `review_log[]`
9. If iterate: edit directly, re-present. If approve: update status, run check-milestone. If abandon: update status, start research.

## Scripts
- `bash scripts/new-site.sh <slug>` — scaffold site directory from template
- `python3 scripts/fill-template.py <slug>` — generate site from meta.json data
- `python3 scripts/check-milestone.py` — show progress, surface contacts at milestone

## Cloudflare Deploy
```
wrangler pages deploy sites/<slug>/ --project-name=endless-<slug>
```
URL pattern: `https://endless-<slug>.pages.dev`

## Key Files
- `businesses.json` — master registry and milestone counter
- `sites/<slug>/meta.json` — per-business data and workflow status
- `templates/business/index.html` — master template (never edit for a specific site)
- `templates/business/style.css` — shared stylesheet (copied to each site)
- `templates/business/script.js` — shared JS (copied to each site)
