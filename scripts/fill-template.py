#!/usr/bin/env python3
"""fill-template.py <slug>
Reads sites/<slug>/meta.json and generates a finished index.html
by substituting all {{TOKEN}} placeholders in the template copy.
Updates status to 'prototype' in meta.json and businesses.json.
"""

import json
import sys
import os
import datetime
import html as html_lib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORY_COLORS = {
    "restaurant":   ("#2C3E50", "#E67E22"),
    "bar":          ("#1A1A2E", "#C0392B"),
    "cafe":         ("#3E2723", "#D4A853"),
    "bakery":       ("#4A235A", "#E8A87C"),
    "salon":        ("#6C3483", "#F1948A"),
    "nail":         ("#7D3C98", "#F8C8D4"),
    "spa":          ("#1B4F72", "#A9CCE3"),
    "barbershop":   ("#1A252F", "#2ECC71"),
    "auto":         ("#1A252F", "#2980B9"),
    "repair":       ("#212F3C", "#F39C12"),
    "landscaping":  ("#1E8449", "#F39C12"),
    "lawn":         ("#1E8449", "#F39C12"),
    "cleaning":     ("#1A5276", "#48C9B0"),
    "childcare":    ("#1A5276", "#F7DC6F"),
    "tutoring":     ("#154360", "#2ECC71"),
    "fitness":      ("#1C2833", "#E74C3C"),
    "gym":          ("#1C2833", "#E74C3C"),
}
DEFAULT_COLORS = ("#2C3E50", "#3498DB")

SERVICES_ICONS = {
    "restaurant": "🍽️", "bar": "🍺", "cafe": "☕", "bakery": "🥐",
    "salon": "✂️", "nail": "💅", "spa": "🧖", "barbershop": "💈",
    "auto": "🔧", "repair": "🔨", "landscaping": "🌿", "lawn": "🌱",
    "cleaning": "🧹", "childcare": "🧒", "tutoring": "📚",
    "fitness": "💪", "gym": "🏋️",
}

DAY_ORDER = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
DAY_DISPLAY = {
    "monday":"Monday","tuesday":"Tuesday","wednesday":"Wednesday",
    "thursday":"Thursday","friday":"Friday","saturday":"Saturday","sunday":"Sunday"
}


def esc(s):
    return html_lib.escape(str(s)) if s else ""


def get_colors(category):
    cat = (category or "").lower()
    for key, colors in CATEGORY_COLORS.items():
        if key in cat:
            return colors
    return DEFAULT_COLORS


def render_hours_table(hours):
    rows = []
    for day in DAY_ORDER:
        val = hours.get(day, "Closed") or "Closed"
        rows.append(
            f'<tr><td>{DAY_DISPLAY[day]}</td><td>{esc(val)}</td></tr>'
        )
    return "\n            ".join(rows)


def render_services_html(services_or_menu, category):
    """Renders either menu sections (restaurant) or service cards (other)."""
    if not services_or_menu:
        return '<p style="color:var(--color-text-light)">Details coming soon.</p>'

    cat = (category or "").lower()
    is_restaurant = any(k in cat for k in ("restaurant","bar","cafe","bakery","food"))

    if is_restaurant:
        return render_menu(services_or_menu)
    else:
        return render_service_cards(services_or_menu, category)


def render_menu(sections):
    parts = []
    for section in sections:
        title = esc(section.get("section", ""))
        items_html = []
        for item in section.get("items", []):
            if isinstance(item, dict):
                name  = esc(item.get("name", ""))
                price = esc(item.get("price", ""))
                desc  = esc(item.get("description", ""))
                price_html = f'<span class="menu-item__price">{price}</span>' if price else ""
                desc_html  = f'<span class="menu-item__desc">{desc}</span>' if desc else ""
                items_html.append(
                    f'<div class="menu-item"><span class="menu-item__name">{name}</span>{price_html}</div>'
                    + (f'<div class="menu-item" style="padding-top:0;border:none">{desc_html}</div>' if desc else "")
                )
            else:
                # Simple string like "Fried Chicken ($14)"
                text = str(item)
                # Try to split off trailing price in parens
                if "(" in text and text.endswith(")"):
                    name_part, price_part = text.rsplit("(", 1)
                    price_part = price_part.rstrip(")")
                    items_html.append(
                        f'<div class="menu-item">'
                        f'<span class="menu-item__name">{esc(name_part.strip())}</span>'
                        f'<span class="menu-item__price">{esc(price_part.strip())}</span>'
                        f'</div>'
                    )
                else:
                    items_html.append(
                        f'<div class="menu-item"><span class="menu-item__name">{esc(text)}</span></div>'
                    )
        parts.append(
            f'<div class="menu-section">'
            f'<div class="menu-section__title">{title}</div>'
            + "\n".join(items_html)
            + "</div>"
        )
    return "\n".join(parts)


def render_service_cards(sections, category):
    cat = (category or "").lower()
    icon = next((v for k, v in SERVICES_ICONS.items() if k in cat), "⭐")
    cards = []
    for section in sections:
        title = section.get("section", "")
        items = section.get("items", [])
        for item in items:
            if isinstance(item, dict):
                name  = item.get("name", "")
                price = item.get("price", "")
                desc  = item.get("description", "")
            else:
                name, price, desc = str(item), "", ""
                if "(" in name and name.endswith(")"):
                    name, price = name.rsplit("(", 1)
                    price = price.rstrip(")")
                    name = name.strip()

            price_html = f'<div class="service-card__price">{esc(price)}</div>' if price else ""
            desc_html  = f'<div class="service-card__desc">{esc(desc)}</div>' if desc else ""
            cards.append(
                f'<div class="service-card">'
                f'<div class="service-card__icon">{icon}</div>'
                f'<div class="service-card__title">{esc(name)}</div>'
                f'{price_html}{desc_html}'
                f'</div>'
            )

        # If no items, make the section itself a card
        if not items and title:
            cards.append(
                f'<div class="service-card">'
                f'<div class="service-card__icon">{icon}</div>'
                f'<div class="service-card__title">{esc(title)}</div>'
                f'</div>'
            )

    if not cards:
        return '<p style="color:var(--color-text-light)">Services available — call for details.</p>'

    return '<div class="services__grid">' + "\n".join(cards) + "</div>"


def render_gallery(photos):
    if not photos:
        return ""
    count = len(photos)
    grid_class = "single" if count == 1 else ""
    imgs = []
    for i, url in enumerate(photos[:6]):
        alt = f"Photo {i+1}"
        imgs.append(f'<img src="{esc(url)}" alt="{alt}" loading="lazy">')
    grid_html = f'<div class="gallery__grid {grid_class}">' + "\n".join(imgs) + "</div>"
    return (
        '<section class="gallery section" id="gallery">\n'
        '  <div class="container">\n'
        '    <span class="section-label">Gallery</span>\n'
        '    <h2>Take a Look Inside</h2>\n'
        f'    {grid_html}\n'
        '  </div>\n'
        '</section>'
    )


def render_google_maps(embed_url):
    if not embed_url:
        return '<p style="color:var(--color-text-light)">Find us on Google Maps.</p>'
    return f'<iframe src="{esc(embed_url)}" allowfullscreen loading="lazy" title="Map"></iframe>'


def render_email_html(email):
    if not email:
        return ""
    return f'<a href="mailto:{esc(email)}" class="contact__email">{esc(email)}</a>'


def render_contact_form(action_url):
    if not action_url:
        return ""
    return (
        f'<form class="contact-form" action="{esc(action_url)}" method="POST">'
        '<div><label for="cf-name">Name</label>'
        '<input type="text" id="cf-name" name="name" required></div>'
        '<div><label for="cf-email">Email</label>'
        '<input type="email" id="cf-email" name="email" required></div>'
        '<div><label for="cf-msg">Message</label>'
        '<textarea id="cf-msg" name="message" required></textarea></div>'
        '<button type="submit" class="btn btn--accent">Send Message</button>'
        '</form>'
    )


def render_founded_badge(year_founded):
    if not year_founded:
        return ""
    return (
        f'<p><span class="about__badge">Serving Columbia since {esc(str(year_founded))}</span></p>'
    )


def fill(slug):
    site_dir = os.path.join(REPO_ROOT, "sites", slug)
    meta_path = os.path.join(site_dir, "meta.json")
    html_path = os.path.join(site_dir, "index.html")

    if not os.path.isdir(site_dir):
        print(f"Error: sites/{slug}/ does not exist. Run new-site.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(meta_path) as f:
        meta = json.load(f)

    biz = meta["business"]
    cat = biz.get("category", "")

    # Colors
    color_primary, color_accent = get_colors(cat)

    # Services nav label
    cat_lower = cat.lower()
    if any(k in cat_lower for k in ("restaurant","bar","cafe","bakery","food")):
        services_nav_label = "Menu"
        services_heading   = "Our Menu"
    else:
        services_nav_label = "Services"
        services_heading   = "What We Offer"

    # Hero image
    hero_url = "assets/hero.jpg"
    if not os.path.exists(os.path.join(site_dir, "assets", "hero.jpg")):
        hero_url = "assets/placeholder-hero.svg"

    # About image (same as hero by default)
    about_url = hero_url

    # Hours JSON for JS
    hours_json = json.dumps(biz.get("hours", {}))

    # Photos for gallery (exclude hero if same)
    photos = biz.get("photos_found", [])

    import re as _re
    phone_raw = biz.get("phone", "")
    phone_href = _re.sub(r"[^\d+]", "", phone_raw)  # digits only for tel: href

    substitutions = {
        "{{BUSINESS_NAME}}":      esc(biz.get("name", "")),
        "{{TAGLINE}}":            esc(biz.get("tagline", "")),
        "{{DESCRIPTION}}":        esc(biz.get("description", "")),
        "{{CATEGORY}}":           esc(cat),
        "{{PHONE}}":              phone_href,
        "{{PHONE_DISPLAY}}":      esc(phone_raw),
        "{{ADDRESS}}":            esc(biz.get("address", "")).replace(",", ",<br>"),
        "{{HERO_IMAGE_URL}}":     hero_url,
        "{{ABOUT_IMAGE_URL}}":    about_url,
        "{{COLOR_PRIMARY}}":      color_primary,
        "{{COLOR_ACCENT}}":       color_accent,
        "{{SERVICES_NAV_LABEL}}": services_nav_label,
        "{{SERVICES_HEADING}}":   services_heading,
        "{{HOURS_TABLE_HTML}}":   render_hours_table(biz.get("hours", {})),
        "{{HOURS_JSON}}":         hours_json,
        "{{SERVICES_HTML}}":      render_services_html(biz.get("services_or_menu", []), cat),
        "{{GALLERY_SECTION_HTML}}": render_gallery(photos),
        "{{GOOGLE_MAPS_EMBED_HTML}}": render_google_maps(biz.get("google_maps_embed_url", "")),
        "{{EMAIL_HTML}}":         render_email_html(biz.get("email")),
        "{{CONTACT_FORM_HTML}}":  render_contact_form(""),
        "{{FOUNDED_BADGE_HTML}}": render_founded_badge(biz.get("year_founded")),
        "{{YEAR}}":               str(datetime.date.today().year),
    }

    with open(html_path) as f:
        content = f.read()

    for token, value in substitutions.items():
        content = content.replace(token, value)

    with open(html_path, "w") as f:
        f.write(content)

    # Update status in meta.json
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["status"] = "prototype"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    # Update businesses.json
    biz_path = os.path.join(REPO_ROOT, "businesses.json")
    with open(biz_path) as f:
        reg = json.load(f)

    for entry in reg["businesses"]:
        if entry["slug"] == slug:
            entry["status"] = "prototype"
            entry["name"] = biz.get("name", slug)
            entry["updated_at"] = now

    reg["updated_at"] = now
    in_prog = sum(1 for b in reg["businesses"] if b["status"] in ("researching","prototype","in_review"))
    reg["milestone"]["in_progress"] = in_prog

    with open(biz_path, "w") as f:
        json.dump(reg, f, indent=2)
        f.write("\n")

    print(f"✓ Generated sites/{slug}/index.html")
    print(f"  Status set to: prototype")
    print(f"\nNext: deploy and review")
    print(f"  wrangler pages deploy sites/{slug}/ --project-name=endless-{slug}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fill-template.py <slug>", file=sys.stderr)
        sys.exit(1)
    fill(sys.argv[1])
