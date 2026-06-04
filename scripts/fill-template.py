#!/usr/bin/env python3
"""fill-template.py <slug>
Reads sites/<slug>/meta.json and generates a finished index.html
by substituting all {{TOKEN}} placeholders in the category-specific template.
Updates status to 'prototype' in meta.json and businesses.json.
"""

import json
import sys
import os
import re as _re
import datetime
import html as html_lib
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORY_COLORS = {
    "restaurant":   ("#111111", "#e67e22"),
    "bar":          ("#1A1A2E", "#C0392B"),
    "cafe":         ("#3e2723", "#d4a853"),
    "bakery":       ("#4A235A", "#E8A87C"),
    "deli":         ("#3e2723", "#d4a853"),
    "coffee":       ("#3e2723", "#d4a853"),
    "salon":        ("#4a235a", "#F8C8D4"),
    "nail":         ("#4a235a", "#F8C8D4"),
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

CATEGORY_TEMPLATES = {
    "korean":     "restaurant",
    "japanese":   "restaurant",
    "chinese":    "restaurant",
    "thai":       "restaurant",
    "vietnamese": "restaurant",
    "restaurant": "restaurant",
    "bar":        "restaurant",
    "food":       "restaurant",
    "salvadoran": "cafe",
    "mexican":    "cafe",
    "latin":      "cafe",
    "caribbean":  "restaurant",
    "cafe":       "cafe",
    "bakery":     "cafe",
    "deli":       "cafe",
    "coffee":     "cafe",
    "nail":       "salon",
    "salon":      "salon",
    "spa":        "salon",
}

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
DAY_SHORT = {
    "monday":"Mon","tuesday":"Tue","wednesday":"Wed",
    "thursday":"Thu","friday":"Fri","saturday":"Sat","sunday":"Sun"
}


def esc(s):
    return html_lib.escape(str(s)) if s else ""


def get_colors(category):
    cat = (category or "").lower()
    for key, colors in CATEGORY_COLORS.items():
        if key in cat:
            return colors
    return DEFAULT_COLORS


def get_template_dir(category):
    cat = (category or "").lower()
    for key, tmpl in CATEGORY_TEMPLATES.items():
        if key in cat:
            return os.path.join(REPO_ROOT, "templates", tmpl)
    return os.path.join(REPO_ROOT, "templates", "business")


def render_hours_table(hours):
    rows = []
    for day in DAY_ORDER:
        val = hours.get(day, "Closed") or "Closed"
        rows.append(
            f'<tr><td>{DAY_DISPLAY[day]}</td><td>{esc(val)}</td></tr>'
        )
    return "\n            ".join(rows)


def render_hours_row(hours):
    """Renders hours as horizontal pill badges (restaurant template)."""
    pills = []
    for day in DAY_ORDER:
        val = hours.get(day, "Closed") or "Closed"
        is_closed = val.strip().lower() == "closed"
        cls = "hours__pill closed" if is_closed else "hours__pill open"
        pills.append(
            f'<div class="{cls}">'
            f'<span class="hours__pill__day">{DAY_SHORT[day]}</span>'
            f'<span class="hours__pill__time">{esc(val)}</span>'
            f'</div>'
        )
    return "\n".join(pills)


def render_favorites_html(services, photos):
    """Cafe-specific: renders 'Today's Favorites' image cards."""
    if not services:
        return ""
    cards = []
    for i, section in enumerate(services[:3]):
        items = section.get("items", [])
        section_name = section.get("section", "")
        if items:
            item = items[0]
            if isinstance(item, dict):
                name = item.get("name", section_name)
                desc = item.get("description", "")
            else:
                name = str(item)
                desc = ""
        else:
            name = section_name
            desc = ""

        bg = photos[i] if i < len(photos) else (photos[0] if photos else "")
        bg_style = f'style="background-image:url(\'{esc(bg)}\')"' if bg else ""
        desc_html = f'<p class="fav-card__desc">{esc(desc)}</p>' if desc else ""

        cards.append(
            f'<div class="fav-card" {bg_style}>'
            f'<div class="fav-card__overlay"></div>'
            f'<div class="fav-card__body">'
            f'<p class="fav-card__cat">{esc(section_name)}</p>'
            f'<h3 class="fav-card__name">{esc(name)}</h3>'
            f'{desc_html}'
            f'</div></div>'
        )
    if not cards:
        return ""
    return '<div class="favorites__grid">' + "\n".join(cards) + "</div>"


def render_services_html(services_or_menu, category):
    if not services_or_menu:
        return '<p style="color:var(--color-text-muted)">Details coming soon.</p>'

    cat = (category or "").lower()
    is_restaurant = any(k in cat for k in ("restaurant","bar","cafe","bakery","food","deli"))

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
                desc_html  = f'<p class="menu-item__desc">{desc}</p>' if desc else ""
                items_html.append(
                    f'<div class="menu-item">'
                    f'<span class="menu-item__name">{name}</span>'
                    f'{price_html}'
                    f'</div>'
                    + (f'<div class="menu-item__desc-row">{desc_html}</div>' if desc else "")
                )
            else:
                text = str(item)
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
                        f'<div class="menu-item">'
                        f'<span class="menu-item__name">{esc(text)}</span>'
                        f'</div>'
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

        if not items and title:
            cards.append(
                f'<div class="service-card">'
                f'<div class="service-card__icon">{icon}</div>'
                f'<div class="service-card__title">{esc(title)}</div>'
                f'</div>'
            )

    if not cards:
        return '<p style="color:var(--color-text-muted)">Services available — call for details.</p>'

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
        return '<p style="color:var(--color-text-muted)">Find us on Google Maps.</p>'
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

    if not os.path.isdir(site_dir):
        print(f"Error: sites/{slug}/ does not exist. Run new-site.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(meta_path) as f:
        meta = json.load(f)

    biz = meta["business"]
    cat = biz.get("category", "")

    # Routing: pick the right template dir
    template_dir = get_template_dir(cat)
    template_html_path = os.path.join(template_dir, "index.html")
    if not os.path.exists(template_html_path):
        template_dir = os.path.join(REPO_ROOT, "templates", "business")
        template_html_path = os.path.join(template_dir, "index.html")

    html_path = os.path.join(site_dir, "index.html")

    # Colors
    color_primary, color_accent = get_colors(cat)

    # Services nav label
    cat_lower = cat.lower()
    if any(k in cat_lower for k in ("restaurant","bar","cafe","bakery","food","deli")):
        services_nav_label = "Menu"
        services_heading   = "Our Menu"
    else:
        services_nav_label = "Services"
        services_heading   = "What We Offer"

    # Hero image: prefer meta hero_image_url, then local file, then placeholder
    photos = biz.get("photos_found", [])
    hero_url = biz.get("hero_image_url", "")
    if not hero_url:
        if os.path.exists(os.path.join(site_dir, "assets", "hero.jpg")):
            hero_url = "assets/hero.jpg"
        else:
            hero_url = "assets/placeholder-hero.svg"

    # About image: use second photo if available, else hero
    about_url = photos[1] if len(photos) > 1 else hero_url

    # Hours JSON for JS
    hours_json = json.dumps(biz.get("hours", {}))

    phone_raw = biz.get("phone", "")
    phone_href = _re.sub(r"[^\d+]", "", phone_raw)

    # Optional fields with defaults
    pull_quote = biz.get("pull_quote", "Come taste the difference.")
    testimonial_quote = biz.get("testimonial_quote", "A neighborhood gem that feels like home.")
    testimonial_author = biz.get("testimonial_author", "— Happy Customer")
    owner_name = meta.get("owner", {}).get("name", "")

    substitutions = {
        "{{BUSINESS_NAME}}":         esc(biz.get("name", "")),
        "{{TAGLINE}}":               esc(biz.get("tagline", "")),
        "{{DESCRIPTION}}":           esc(biz.get("description", "")),
        "{{CATEGORY}}":              esc(cat),
        "{{PHONE}}":                 phone_href,
        "{{PHONE_DISPLAY}}":         esc(phone_raw),
        "{{ADDRESS}}":               esc(biz.get("address", "")).replace(",", ",<br>"),
        "{{HERO_IMAGE_URL}}":        esc(hero_url),
        "{{ABOUT_IMAGE_URL}}":       esc(about_url),
        "{{COLOR_PRIMARY}}":         color_primary,
        "{{COLOR_ACCENT}}":          color_accent,
        "{{SERVICES_NAV_LABEL}}":    services_nav_label,
        "{{SERVICES_HEADING}}":      services_heading,
        "{{HOURS_TABLE_HTML}}":      render_hours_table(biz.get("hours", {})),
        "{{HOURS_ROW_HTML}}":        render_hours_row(biz.get("hours", {})),
        "{{HOURS_JSON}}":            hours_json,
        "{{SERVICES_HTML}}":         render_services_html(biz.get("services_or_menu", []), cat),
        "{{FAVORITES_HTML}}":        render_favorites_html(biz.get("services_or_menu", []), photos),
        "{{GALLERY_SECTION_HTML}}":  render_gallery(photos),
        "{{GOOGLE_MAPS_EMBED_HTML}}": render_google_maps(biz.get("google_maps_embed_url", "")),
        "{{EMAIL_HTML}}":            render_email_html(biz.get("email")),
        "{{CONTACT_FORM_HTML}}":     render_contact_form(""),
        "{{FOUNDED_BADGE_HTML}}":    render_founded_badge(biz.get("year_founded")),
        "{{PULL_QUOTE}}":            esc(pull_quote),
        "{{TESTIMONIAL_QUOTE}}":     esc(testimonial_quote),
        "{{TESTIMONIAL_AUTHOR}}":    esc(testimonial_author),
        "{{OWNER_NAME}}":            esc(owner_name),
        "{{YEAR}}":                  str(datetime.date.today().year),
    }

    with open(template_html_path) as f:
        content = f.read()

    for token, value in substitutions.items():
        content = content.replace(token, value)

    with open(html_path, "w") as f:
        f.write(content)

    # Copy CSS (and script.js if present) from template dir to site dir
    for fname in ("style.css", "script.js"):
        src = os.path.join(template_dir, fname)
        dst = os.path.join(site_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)

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

    tmpl_name = os.path.basename(template_dir)
    print(f"✓ Generated sites/{slug}/index.html  [template: {tmpl_name}]")
    print(f"  Status: prototype")
    print(f"\nNext: deploy and review")
    print(f"  wrangler pages deploy sites/{slug}/ --project-name=endless-{slug}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fill-template.py <slug>", file=sys.stderr)
        sys.exit(1)
    fill(sys.argv[1])
