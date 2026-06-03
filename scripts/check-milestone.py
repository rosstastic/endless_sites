#!/usr/bin/env python3
"""check-milestone.py
Reports pipeline progress and surfaces owner contact info at 5 approved sites.
Run after every status change.
"""

import json
import os
import sys
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_registry():
    path = os.path.join(REPO_ROOT, "businesses.json")
    with open(path) as f:
        return json.load(f), path


def sync_counts(reg):
    counts = {"researching": 0, "prototype": 0, "in_review": 0, "approved": 0, "abandoned": 0}
    for b in reg["businesses"]:
        counts[b.get("status", "researching")] += 1

    reg["milestone"]["approved"]    = counts["approved"]
    reg["milestone"]["in_progress"] = counts["researching"] + counts["prototype"] + counts["in_review"]
    reg["milestone"]["abandoned"]   = counts["abandoned"]
    reg["milestone"]["last_updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return counts


def progress_bar(approved, target):
    filled = min(approved, target)
    bar = "█" * filled + "░" * (target - filled)
    return f"[{bar}] {approved}/{target} approved"


def load_meta(slug):
    path = os.path.join(REPO_ROOT, "sites", slug, "meta.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def print_contact_sheet(approved_slugs):
    print()
    print("=" * 60)
    print("  MILESTONE REACHED: 5 sites approved and ready to pitch!")
    print("=" * 60)
    print()
    for i, slug in enumerate(approved_slugs, 1):
        meta = load_meta(slug)
        if not meta:
            continue
        biz   = meta.get("business", {})
        owner = meta.get("owner", {})
        deploy = meta.get("deploy", {})
        url = deploy.get("last_deployed_url") or f"https://endless-{slug}.pages.dev"

        print(f"  {i}. {biz.get('name', slug)}")
        print(f"     Address: {biz.get('address', 'N/A')}")
        print(f"     Owner:   {owner.get('name', 'Unknown')}")
        print(f"     Phone:   {owner.get('contact_phone', biz.get('phone', 'N/A'))}")
        if owner.get("contact_email"):
            print(f"     Email:   {owner['contact_email']}")
        print(f"     Site:    {url}")
        if owner.get("contact_source"):
            print(f"     Source:  {owner['contact_source']}")
        print()
    print("=" * 60)
    print()
    print("Suggested next step: draft outreach emails for each owner above.")
    print()


def main():
    reg, reg_path = load_registry()
    counts = sync_counts(reg)
    target = reg["milestone"].get("target", 5)

    # Save updated counts
    with open(reg_path, "w") as f:
        json.dump(reg, f, indent=2)
        f.write("\n")

    # Print summary
    print()
    print("  Pipeline Status")
    print("  " + "─" * 40)
    print(f"  {progress_bar(counts['approved'], target)}")
    print()
    statuses = [
        ("In progress",  counts["researching"] + counts["prototype"] + counts["in_review"]),
        ("  Researching",counts["researching"]),
        ("  Prototype",  counts["prototype"]),
        ("  In review",  counts["in_review"]),
        ("Approved",     counts["approved"]),
        ("Abandoned",    counts["abandoned"]),
    ]
    for label, n in statuses:
        if n > 0:
            print(f"  {label:<20} {n}")
    print()

    # List each business with status
    if reg["businesses"]:
        print("  Businesses:")
        for b in reg["businesses"]:
            status_icon = {
                "researching": "🔍",
                "prototype":   "🔨",
                "in_review":   "👁️ ",
                "approved":    "✅",
                "abandoned":   "❌",
            }.get(b.get("status",""), "·")
            name = b.get("name") or b["slug"]
            print(f"    {status_icon}  {name} ({b.get('status','')})")
        print()

    # Milestone surface
    approved_slugs = [b["slug"] for b in reg["businesses"] if b.get("status") == "approved"]
    if len(approved_slugs) >= target:
        print_contact_sheet(approved_slugs[:target])
        return 0

    remaining = target - counts["approved"]
    print(f"  {remaining} more approval{'s' if remaining != 1 else ''} needed to reach the milestone.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
