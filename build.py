"""Build the static Narrative Science site with Python 3."""
from html import escape, unescape
import json
from pathlib import Path
import re
import shutil

PROJECT = Path(__file__).resolve().parent
OUTPUT = PROJECT / "dist" / "NarrativeScience"
CANONICAL_ROOT = "https://agist.org/NarrativeScience/"
CONTENT = json.loads((PROJECT / "content.json").read_text(encoding="utf-8"))
SECTIONS = CONTENT["sections"]
JOURNAL = CONTENT["journal"]
TAGLINE = CONTENT["tagline"]
CONTACT_EMAIL = escape(CONTENT["contact_email"])
JOURNAL_STATUS = "In preparation"
COMING_SOON = "Coming soon"

ROUTES = {
    "home": "",
    "about": "about/",
    "explore": "explore/",
    "themes": "research-themes/",
    "applications": "engineering-applications/",
    "resources": "academic-resources/",
    "authors": "for-authors/",
    "contact": "contact/",
}
LABELS = {
    "home": "Overview",
    "about": "About",
    "explore": "Explore Content",
    "themes": "Research Themes",
    "applications": "Engineering Applications",
    "resources": "Academic Resources",
    "authors": "For Authors",
    "contact": "Contact",
}
EXPLORE = ("themes", "applications", "resources")


def heading_and_body(fragment, level):
    match = re.fullmatch(rf"<h{level}>(.*?)</h{level}>(.*)", fragment, re.S)
    if match is None:
        raise ValueError(f"Missing leading h{level} in content fragment")
    return match.groups()


def heading_groups(fragment, level):
    starts = list(re.finditer(rf"<h{level}>", fragment))
    if not starts:
        return fragment, []
    groups = [
        heading_and_body(
            fragment[match.start():starts[index + 1].start() if index + 1 < len(starts) else len(fragment)],
            level,
        )
        for index, match in enumerate(starts)
    ]
    return fragment[:starts[0].start()], groups


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def plain_text(markup):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def first_paragraph(markup):
    return re.search(r"<p>(.*?)</p>", markup, re.S)[1]


def page_url(base, key):
    return base + ROUTES[key]


def navigation(key, base):
    def group(destination, items):
        direct_current = ' aria-current="page"' if key == destination else ""
        current_group = key == destination or any(key == item[0] for item in items)
        current_class = ' is-current' if current_group else ""
        links = []
        for route, label, fragment in items:
            current = ' aria-current="page"' if key == route and key != destination and not fragment else ""
            links.append(f'<a href="{page_url(base, route)}{fragment}"{current}>{label}</a>')
        return f"""
    <div class="nav-group{current_class}">
      <a href="{page_url(base, destination)}"{direct_current}>{LABELS[destination]}</a>
      <details class="nav-menu">
        <summary><span class="visually-hidden">{LABELS[destination]} menu</span></summary>
        <div class="nav-panel">{"".join(links)}</div>
      </details>
    </div>"""

    about_items = (
        ("about", "About Narrative Science", ""),
        ("about", "Our Perspective", "#our-perspective"),
        ("about", "Focus and Scope", "#focus-and-scope"),
        ("about", "Article Types", "#article-types"),
        ("about", "Editorial Principles", "#editorial-principles"),
    )
    explore_items = tuple((item, LABELS[item], "") for item in EXPLORE)
    author_items = (
        ("authors", "Prepare Your Materials", "#prepare-your-materials"),
        ("contact", "Contact the Journal", ""),
    )
    overview_current = ' aria-current="page"' if key == "home" else ""
    return f"""
<nav class="site-nav" aria-label="Journal navigation">
  <div class="shell nav-inner">
    <a class="nav-cta" href="{page_url(base, "authors")}">Submission information</a>
    <a href="{base}"{overview_current}>{LABELS["home"]}</a>
    {group("about", about_items)}
    {group("explore", explore_items)}
    {group("authors", author_items)}
  </div>
</nav>"""


def masthead(key, title, base):
    journal_name = (
        f'<h1 class="journal-name">{JOURNAL}</h1>' if key == "home"
        else f'<a class="journal-name" href="{base}">{JOURNAL}</a>'
    )
    return f"""
<div class="journal-masthead">
  <div class="shell masthead-inner">
    {breadcrumbs(key, title, base)}
    <div class="journal-heading">
      {journal_name}
      <span class="journal-status">{JOURNAL_STATUS}</span>
    </div>
    <p class="journal-tagline">{TAGLINE}</p>
  </div>
</div>"""


def page_shell(key, title, main, description):
    base = "./" if key == "home" else "../"
    document_title = JOURNAL if key == "home" else f"{title} — {JOURNAL}"
    contact_current = ' aria-current="page"' if key == "contact" else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(document_title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{CANONICAL_ROOT}{ROUTES[key]}">
  <link rel="icon" href="{base}assets/agist.ico">
  <link rel="stylesheet" href="{base}assets/site.css">
  <script defer src="{base}assets/site.js"></script>
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header>
  <div class="site-top">
    <div class="shell">
      <a class="site-brand" href="https://agist.org/">
        <span class="brand-image"><img src="{base}assets/agist-logo.webp" alt="AGIST" width="1561" height="729"></span>
      </a>
      <a class="site-utility" href="{page_url(base, "contact")}"{contact_current}>Contact</a>
    </div>
  </div>
  {masthead(key, title, base)}
  {navigation(key, base)}
</header>
{main}
<footer class="site-footer">
  <div class="shell footer-inner">
    <div class="footer-identity">{CONTENT["footer"]}</div>
    <div class="footer-links">
      <a href="{page_url(base, "authors")}">For Authors</a>
      <a href="mailto:{CONTACT_EMAIL}">Email the Journal</a>
    </div>
  </div>
</footer>
</body>
</html>
"""


def browse_content(base, show_heading=True):
    title = '<h2 class="section-title" id="browse-title">Explore Content</h2>' if show_heading else ""
    tabs = []
    panels = []
    for key in EXPLORE:
        label = LABELS[key]
        panel_id = f"browse-{ROUTES[key].rstrip('/')}"
        tab_id = f"tab-{key}"
        tabs.append(f'<a href="#{panel_id}" id="{tab_id}">{label}</a>')
        _, body = heading_and_body(SECTIONS[key], 2)
        _, groups = section_groups(key, body)
        entries = []
        for entry_title, entry_body in groups:
            url = f"{page_url(base, key)}#{slug(entry_title)}"
            preview = f"<p>{escape(plain_text(first_paragraph(entry_body)))}</p>" if "<p>" in entry_body else ""
            entries.append(f'<li class="browse-item"><h4><a href="{url}">{entry_title}</a></h4>{preview}</li>')
        panels.append(f"""
  <section class="browse-panel" id="{panel_id}" aria-labelledby="{panel_id}-title">
    <h3 class="browse-panel-title" id="{panel_id}-title">{label}</h3>
    <ul class="browse-list">{"".join(entries)}</ul>
    <a class="browse-more" href="{page_url(base, key)}">View all {label} <span aria-hidden="true">→</span></a>
  </section>""")
    return f"""
<section class="explore-section" data-browse aria-labelledby="browse-title">
  {title}
  <div class="browse-tabs">{"".join(tabs)}</div>
  {"".join(panels)}
</section>"""


def quick_links(base):
    return f"""
<aside class="quick-links" aria-labelledby="quick-title">
  <h3 id="quick-title">For Authors</h3>
  <a href="{page_url(base, "authors")}#prepare-your-materials">Prepare Your Materials <span aria-hidden="true">→</span></a>
  <a href="{page_url(base, "about")}#article-types">Article Types <span aria-hidden="true">→</span></a>
  <a href="{page_url(base, "contact")}">Contact the Journal <span aria-hidden="true">→</span></a>
</aside>"""


def breadcrumbs(key, title, base):
    items = ['<li><a href="https://agist.org/">AGIST</a></li>']
    if key != "home":
        items.append(f'<li><a href="{base}">{JOURNAL}</a></li>')
    if key in EXPLORE:
        items.append(f'<li><a href="{page_url(base, "explore")}">Explore Content</a></li>')
    items.append(f'<li aria-current="page">{title}</li>')
    return f"""
<nav class="breadcrumbs" aria-label="Breadcrumb">
  <ol>{"".join(items)}</ol>
</nav>"""


def render_home():
    _, groups = heading_groups(SECTIONS["home"], 2)
    title, body = groups[0]
    return f"""
<main class="shell home-main" id="main-content" tabindex="-1" data-home>
  <section class="journal-overview" aria-labelledby="overview-title">
    <h2 class="section-title" id="overview-title">Overview</h2>
    <div class="overview-layout">
      <div class="overview-content">
        <h3>{title}</h3>
        {body}
        <div class="overview-links">
          <a class="text-link" href="./about/#focus-and-scope">Focus and Scope <span aria-hidden="true">→</span></a>
          <a class="text-link" href="./about/#editorial-principles">Editorial Principles <span aria-hidden="true">→</span></a>
        </div>
        <dl class="launch-statuses">
          <div><dt>Submissions</dt><dd>{COMING_SOON}</dd></div>
          <div><dt>First issue</dt><dd>{COMING_SOON}</dd></div>
        </dl>
      </div>
      {quick_links("./")}
    </div>
  </section>
  {browse_content("./")}
</main>"""


def render_explore():
    return f"""
<main class="shell page-main" id="main-content" tabindex="-1">
  <h1 class="section-title page-title" id="browse-title">{LABELS["explore"]}</h1>
  {browse_content("../", show_heading=False)}
</main>"""


def subsection(title, body, class_name="content-section"):
    return f'<section class="{class_name}" id="{slug(title)}"><h2>{title}</h2>{body}</section>'


def section_groups(key, body):
    if key != "resources":
        return heading_groups(body, 3)
    sections = re.findall(r'<div class="resource">(.*?)</div>', body, re.S)
    intro = body.split('<div class="resource">', 1)[0]
    return intro, [heading_and_body(item, 3) for item in sections]


def render_content(key, title, body):
    intro, groups = section_groups(key, body)
    if key == "about":
        intro += f"""
      <div class="journal-statement">
        <h2>{CONTENT["hero_title"]}</h2>
        <p>{CONTENT["hero_intro"]}</p>
      </div>"""
        _, home_groups = heading_groups(SECTIONS["home"], 2)
        groups = home_groups[1:] + groups

    if key == "authors":
        intro = f"""
      <section class="status-notice" aria-labelledby="submissions-title">
        <h2 id="submissions-title">Submissions</h2>
        <p><strong>{COMING_SOON}.</strong> Submission instructions will be posted here when submissions open.</p>
      </section>{intro}"""
    if key == "contact":
        intro = f"""
      <p class="journal-contact"><strong>Official journal email</strong><br>
        <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      </p>{intro}"""

    group_class = "resource content-section" if key == "resources" else "content-section"
    blocks = "".join(subsection(heading, section, group_class) for heading, section in groups)
    sidebar = ""
    if len(groups) > 1:
        links = "".join(f'<li><a href="#{slug(heading)}">{heading}</a></li>' for heading, _ in groups)
        sidebar = f"""
<aside class="page-sidebar">
  <nav class="on-this-page" aria-labelledby="contents-title">
    <h2 id="contents-title">On this page</h2>
    <ul>{links}</ul>
  </nav>
</aside>"""
    return f"""
<main class="shell page-main" id="main-content" tabindex="-1">
  <h1 class="section-title page-title">{title}</h1>
  <div class="content-layout">
    <article class="page-content">
      {intro}
      {blocks}
    </article>
    {sidebar}
  </div>
</main>"""


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PROJECT / "assets", OUTPUT / "assets", dirs_exist_ok=True)
    for key, route in ROUTES.items():
        if key == "home":
            title, main, description = JOURNAL, render_home(), TAGLINE
        elif key == "explore":
            title, main, description = LABELS[key], render_explore(), TAGLINE
        else:
            title, body = heading_and_body(SECTIONS[key], 2)
            main = render_content(key, title, body)
            description = plain_text(first_paragraph(body)) if "<p>" in body else TAGLINE
        destination = OUTPUT / route / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page_shell(key, title, main, description), encoding="utf-8")
    print(f"Built {len(ROUTES)} pages in {OUTPUT}")


if __name__ == "__main__":
    build()
