#!/usr/bin/env bash
# new-site.sh <slug>
# Scaffolds sites/<slug>/ from the template and registers the business.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="${1:-}"

if [[ -z "$SLUG" ]]; then
  echo "Usage: bash scripts/new-site.sh <slug>" >&2
  exit 1
fi

if [[ ! "$SLUG" =~ ^[a-z0-9-]+$ ]]; then
  echo "Error: slug must be lowercase letters, numbers, and hyphens only." >&2
  exit 1
fi

SITE_DIR="$REPO_ROOT/sites/$SLUG"
TEMPLATE_DIR="$REPO_ROOT/templates/business"

if [[ -d "$SITE_DIR" ]]; then
  echo "Error: sites/$SLUG already exists." >&2
  exit 1
fi

echo "→ Creating sites/$SLUG/ ..."
mkdir -p "$SITE_DIR/assets"

echo "→ Copying template files ..."
cp "$TEMPLATE_DIR/index.html"  "$SITE_DIR/index.html"
cp "$TEMPLATE_DIR/style.css"   "$SITE_DIR/style.css"
cp "$TEMPLATE_DIR/script.js"   "$SITE_DIR/script.js"
cp "$TEMPLATE_DIR/assets/placeholder-hero.svg"  "$SITE_DIR/assets/placeholder-hero.svg"
cp "$TEMPLATE_DIR/assets/placeholder-logo.svg"  "$SITE_DIR/assets/placeholder-logo.svg"

echo "→ Writing wrangler.toml ..."
cat > "$SITE_DIR/wrangler.toml" << EOF
name = "endless-$SLUG"
compatibility_date = "2025-01-01"

# Deploy command (run from repo root):
#   wrangler pages deploy sites/$SLUG/ --project-name=endless-$SLUG
# Live URL: https://endless-$SLUG.pages.dev
EOF

echo "→ Writing skeleton meta.json ..."
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
cat > "$SITE_DIR/meta.json" << EOF
{
  "slug": "$SLUG",
  "status": "researching",
  "business": {
    "name": "",
    "tagline": "",
    "description": "",
    "category": "",
    "address": "",
    "phone": "",
    "email": null,
    "year_founded": null,
    "hours": {
      "monday":    "",
      "tuesday":   "",
      "wednesday": "",
      "thursday":  "",
      "friday":    "",
      "saturday":  "",
      "sunday":    ""
    },
    "services_or_menu": [],
    "google_maps_embed_url": "",
    "yelp_url": "",
    "photos_found": []
  },
  "owner": {
    "name": "",
    "contact_phone": "",
    "contact_email": "",
    "contact_source": ""
  },
  "research": {
    "sources_checked": [],
    "has_existing_website": false,
    "website_check_notes": "",
    "researched_at": "$TIMESTAMP"
  },
  "review_log": [],
  "deploy": {
    "cloudflare_project_name": "endless-$SLUG",
    "last_deployed_url": null,
    "deployed_at": null
  }
}
EOF

echo "→ Registering in businesses.json ..."
python3 - << PYEOF
import json, datetime, sys

path = "$REPO_ROOT/businesses.json"
with open(path) as f:
    data = json.load(f)

# Check for duplicate
for b in data["businesses"]:
    if b["slug"] == "$SLUG":
        print("Warning: $SLUG already in businesses.json — skipping registration.", file=sys.stderr)
        sys.exit(0)

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
data["businesses"].append({
    "slug": "$SLUG",
    "name": "",
    "status": "researching",
    "site_path": "sites/$SLUG/",
    "added_at": now,
    "updated_at": now
})
data["updated_at"] = now
data["milestone"]["in_progress"] = sum(
    1 for b in data["businesses"]
    if b["status"] in ("researching", "prototype", "in_review")
)

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF

echo ""
echo "✓ Scaffold complete: sites/$SLUG/"
echo ""
echo "Next steps:"
echo "  1. Fill in sites/$SLUG/meta.json with business data"
echo "  2. python3 scripts/fill-template.py $SLUG"
echo "  3. wrangler pages deploy sites/$SLUG/ --project-name=endless-$SLUG"
