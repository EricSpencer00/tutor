#!/usr/bin/env python3
"""
Builds site/dist/index.html for today's date: America/Chicago calendar day
picks a deterministic topic from topics.json. If site/articles/<slug>.md
exists, render it. Otherwise render a solid outline page (title, category,
summary, and 3-4 study prompts) so every topic in the bank has a page even
before a full article is written for it.

No network calls, no API keys. Pure stdlib.
"""
import json
import html
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
TOPICS = json.loads((ROOT / "topics.json").read_text())
ARTICLES = ROOT / "articles"
DIST = ROOT / "dist"
REPO = "EricSpencer00/tutor"  # already correct: this repo IS EricSpencer00/tutor


def today_chicago():
    # America/Chicago is UTC-6 (CST) or UTC-5 (CDT). Avoid a tz database
    # dependency in CI by using a fixed UTC-6 offset — off by one hour
    # during CDT, never off by a day, which is all that matters for
    # picking "today's" topic deterministically.
    return (datetime.now(timezone.utc) - timedelta(hours=6)).date()


def pick_topic(date):
    idx = date.toordinal() % len(TOPICS)
    return TOPICS[idx]


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, body


def md_to_html(md):
    """Tiny markdown-ish renderer: paragraphs + **bold** + *italic* + headers."""
    out = []
    for block in md.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            out.append(f"<h2>{html.escape(block[3:])}</h2>")
            continue
        if block.startswith("# "):
            out.append(f"<h2>{html.escape(block[2:])}</h2>")
            continue
        text = html.escape(block)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = text.replace("\n", " ")
        out.append(f"<p>{text}</p>")
    return "\n".join(out)


def render_article(topic, date):
    slug = topic["slug"]
    md_path = ARTICLES / f"{slug}.md"
    if md_path.exists():
        fm, body = parse_frontmatter(md_path.read_text())
        title = fm.get("title", topic["title"])
        category = fm.get("category", topic["category"])
        summary = fm.get("summary", topic["summary"])
        content_html = md_to_html(body)
        is_outline = False
    else:
        title = topic["title"]
        category = topic["category"]
        summary = topic["summary"]
        content_html = (
            f"<p>{html.escape(summary)}</p>"
            "<p><em>A full article for this topic hasn't been written yet — "
            "this is a study outline instead. Claude sessions append full "
            "articles to <code>site/articles/</code> over time; see the "
            "README for the format.</em></p>"
            "<h2>Where to start</h2>"
            "<ul>"
            f"<li>Look up the core definition of <strong>{html.escape(title)}</strong> "
            "and restate it in one sentence, no jargon.</li>"
            "<li>Find one concrete example where this shows up outside its "
            "home field.</li>"
            "<li>Find the one place this idea is commonly misunderstood or "
            "oversimplified, and why.</li>"
            "</ul>"
        )
        is_outline = True

    return {
        "title": title,
        "category": category,
        "summary": summary,
        "content_html": content_html,
        "is_outline": is_outline,
        "date": date,
        "slug": slug,
    }


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Daily Tutor</title>
<meta name="description" content="{summary_attr}">
<style>
  :root {{
    --bg: #faf8f4; --fg: #1c1a17; --muted: #6b6558; --accent: #a5432b;
    --card: #ffffff; --border: #e5ded2; --font-serif: Georgia, 'Iowan Old Style', 'Palatino Linotype', serif;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#16140f; --fg:#eee8dc; --muted:#a29c8c; --accent:#e08a6f; --card:#201d17; --border:#332f26; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg); font-family: var(--font-serif);
    line-height: 1.65;
  }}
  .wrap {{ max-width: 680px; margin: 0 auto; padding: 2.5rem 1.25rem 5rem; }}
  header.site {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:2.5rem; font-family: var(--font-sans); }}
  header.site a {{ color: var(--muted); text-decoration:none; font-size:0.85rem; letter-spacing:0.02em; }}
  header.site .brand {{ font-weight:600; color: var(--fg); }}
  .meta {{ font-family: var(--font-sans); font-size:0.8rem; color: var(--muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.6rem; }}
  h1 {{ font-size:2.1rem; line-height:1.15; margin: 0 0 1.4rem; }}
  article p {{ margin: 0 0 1.1rem; font-size:1.08rem; }}
  article h2 {{ font-family: var(--font-sans); font-size:1rem; text-transform:uppercase; letter-spacing:0.06em; color: var(--accent); margin: 2rem 0 0.8rem; }}
  article ul {{ padding-left: 1.3rem; }}
  article li {{ margin-bottom: 0.5rem; }}
  .outline-note {{ background: var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; font-family: var(--font-sans); font-size:0.9rem; color: var(--muted); }}
  .feedback {{ margin-top: 3rem; padding-top: 2rem; border-top:1px solid var(--border); font-family: var(--font-sans); }}
  .feedback p {{ font-size:0.85rem; color: var(--muted); margin: 0 0 0.8rem; }}
  .feedback .buttons {{ display:flex; gap:0.7rem; }}
  .feedback button {{
    font-family: var(--font-sans); font-size:0.95rem; padding:0.6rem 1.1rem; border-radius:8px;
    border:1px solid var(--border); background: var(--card); color: var(--fg); cursor:pointer;
  }}
  .feedback button:hover {{ border-color: var(--accent); }}
  .feedback button.active {{ background: var(--accent); color:#fff; border-color: var(--accent); }}
  .feedback .thanks {{ font-size:0.85rem; color: var(--accent); margin-top:0.7rem; display:none; }}
  footer.site {{ margin-top:3rem; font-family: var(--font-sans); font-size:0.78rem; color: var(--muted); }}
  footer.site a {{ color: var(--muted); }}
</style>
</head>
<body>
<div class="wrap">
  <header class="site">
    <span class="brand">Daily Tutor</span>
    <a href="https://ericspencer.us">ericspencer.us</a>
  </header>
  <div class="meta">{category} · {date_str}{outline_flag}</div>
  <h1>{title}</h1>
  <article>
    {content_html}
  </article>

  <div class="feedback" id="feedback">
    <p>Was this article good?</p>
    <div class="buttons">
      <button id="btn-up" onclick="sendFeedback(true)">Good</button>
      <button id="btn-down" onclick="sendFeedback(false)">Bad</button>
    </div>
    <div class="thanks" id="thanks">Thanks — opens a pre-filled GitHub issue so Eric sees it.</div>
  </div>

  <footer class="site">
    <p>New topic daily, rotating through a growing bank of subjects. Source and article bank: <a href="https://github.com/{repo}">github.com/{repo}</a>.</p>
  </footer>
</div>
<script>
function sendFeedback(good) {{
  var key = 'tutor-feedback-{slug}';
  try {{ localStorage.setItem(key, good ? 'good' : 'bad'); }} catch (e) {{}}
  document.getElementById('btn-up').classList.toggle('active', good);
  document.getElementById('btn-down').classList.toggle('active', !good);
  document.getElementById('thanks').style.display = 'block';
  var title = encodeURIComponent((good ? '[good] ' : '[bad] ') + '{title_js}');
  var body = encodeURIComponent('Feedback on today\\'s article: {title_js} ({date_str}).\\n\\nRating: ' + (good ? 'Good' : 'Bad') + '\\n\\nWhat worked or didn\\'t:\\n');
  var url = 'https://github.com/{repo}/issues/new?title=' + title + '&body=' + body + '&labels=feedback';
  window.open(url, '_blank', 'noopener');
}}
(function() {{
  try {{
    var v = localStorage.getItem('tutor-feedback-{slug}');
    if (v) {{
      document.getElementById(v === 'good' ? 'btn-up' : 'btn-down').classList.add('active');
    }}
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
"""


def render_page(a):
    outline_flag = " · outline" if a["is_outline"] else ""
    title_js = a["title"].replace("\\", "\\\\").replace("'", "\\'")
    return PAGE_TEMPLATE.format(
        title=html.escape(a["title"]),
        title_js=title_js,
        summary_attr=html.escape(a["summary"]),
        category=html.escape(a["category"]),
        date_str=a["date"].isoformat(),
        content_html=a["content_html"],
        outline_flag=outline_flag,
        repo=REPO,
        slug=a["slug"],
    )


INDEX_REDIRECT = """<!doctype html>
<html><head><meta charset="utf-8"><title>Daily Tutor</title></head>
<body>Redirecting…</body></html>
"""


def main():
    DIST.mkdir(exist_ok=True)
    date = today_chicago()
    topic = pick_topic(date)
    article = render_article(topic, date)
    page = render_page(article)
    (DIST / "index.html").write_text(page)
    # keep an archive by date+slug so past days stay linkable
    archive_dir = DIST / "archive"
    archive_dir.mkdir(exist_ok=True)
    (archive_dir / f"{date.isoformat()}-{topic['slug']}.html").write_text(page)
    print(f"Built {date.isoformat()}: {topic['title']} ({topic['category']}) "
          f"[{'outline' if article['is_outline'] else 'full article'}]")


if __name__ == "__main__":
    main()
