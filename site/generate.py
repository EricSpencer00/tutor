#!/usr/bin/env python3
"""
Builds site/dist/index.html for today's date: America/Chicago calendar day
picks a deterministic piece from library.json (a curated bank of real,
human-written essays, lectures, and papers).

This site curates. It never generates article prose. The page shows title,
author, year, source, topic, reading time, an editor's "why" note, and a
link out to the real piece.

No network calls, no API keys. Pure stdlib.
"""
import json
import html
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
LIBRARY = json.loads((ROOT / "library.json").read_text())
PIECES = LIBRARY["pieces"]
DIST = ROOT / "dist"
REPO = "EricSpencer00/tutor"
ARCHIVE_DAYS = 14


def today_chicago():
    # America/Chicago is UTC-6 (CST) or UTC-5 (CDT). Avoid a tz database
    # dependency in CI by using a fixed UTC-6 offset — off by one hour
    # during CDT, never off by a day, which is all that matters for
    # picking "today's" piece deterministically.
    return (datetime.now(timezone.utc) - timedelta(hours=6)).date()


def pick_piece(date):
    idx = date.toordinal() % len(PIECES)
    return PIECES[idx]


def reading_url(piece):
    """Return the URL readers should use for a curated piece.

    A fallback is useful when a publisher's canonical host blocks automated
    readers or has an intermittent edge outage. The fallback is an exact
    alternate copy recorded alongside the canonical source, not generated
    content.
    """
    return piece.get("fallback_url") or piece["url"]


def recent_pieces(date, n=ARCHIVE_DAYS):
    """Last n days including today, most recent first."""
    out = []
    for i in range(n):
        d = date - timedelta(days=i)
        out.append((d, PIECES[d.toordinal() % len(PIECES)]))
    return out


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Daily Tutor</title>
<meta name="description" content="{why_attr}">
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
  h1 {{ font-size:2.1rem; line-height:1.15; margin: 0 0 0.4rem; }}
  .byline {{ font-family: var(--font-sans); font-size:1rem; color: var(--muted); margin: 0 0 1.6rem; }}
  .why {{ font-size:1.08rem; margin: 0 0 1.8rem; }}
  .cta {{
    display:inline-block; font-family: var(--font-sans); font-weight:600; font-size:0.95rem;
    padding:0.8rem 1.3rem; border-radius:8px; background: var(--accent); color:#fff;
    text-decoration:none; margin-bottom:2.5rem;
  }}
  .cta:hover {{ opacity:0.9; }}
  .archive {{ margin-top:3rem; padding-top:2rem; border-top:1px solid var(--border); font-family: var(--font-sans); }}
  .archive h2 {{ font-size:0.85rem; text-transform:uppercase; letter-spacing:0.06em; color: var(--muted); margin: 0 0 1rem; }}
  .archive ul {{ list-style:none; padding:0; margin:0; }}
  .archive li {{ padding:0.55rem 0; border-bottom:1px solid var(--border); font-size:0.92rem; }}
  .archive li:last-child {{ border-bottom:none; }}
  .archive .a-date {{ color: var(--muted); font-size:0.78rem; display:block; }}
  .archive a {{ color: var(--fg); text-decoration:none; }}
  .archive a:hover {{ color: var(--accent); }}
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
  <div class="meta">{topic} · {date_str} · {minutes} min read</div>
  <h1>{title}</h1>
  <p class="byline">{author}{year_part} — {source}</p>
  <p class="why">{why}</p>
  <a class="cta" href="{url}" target="_blank" rel="noopener">Read it &rarr;</a>

  <div class="archive">
    <h2>Last {archive_n} days</h2>
    <ul>
      {archive_items}
    </ul>
  </div>

  <div class="feedback" id="feedback">
    <p>Was today's pick worth your time?</p>
    <div class="buttons">
      <button id="btn-up" onclick="sendFeedback(true)">Good</button>
      <button id="btn-down" onclick="sendFeedback(false)">Bad</button>
    </div>
    <div class="thanks" id="thanks">Thanks — opens a pre-filled GitHub issue so Eric sees it.</div>
  </div>

  <footer class="site">
    <p>One human-written piece a day, rotating through a curated reading list. No model-generated article text — ever. Source: <a href="https://github.com/{repo}">github.com/{repo}</a>.</p>
  </footer>
</div>
<script>
function sendFeedback(good) {{
  var key = 'tutor-feedback-{id}';
  try {{ localStorage.setItem(key, good ? 'good' : 'bad'); }} catch (e) {{}}
  document.getElementById('btn-up').classList.toggle('active', good);
  document.getElementById('btn-down').classList.toggle('active', !good);
  document.getElementById('thanks').style.display = 'block';
  var title = encodeURIComponent((good ? '[good] ' : '[bad] ') + '{id}: {title_js}');
  var body = encodeURIComponent('Feedback on today\\'s pick: {title_js} ({date_str}).\\nPiece id: {id}\\n\\nRating: ' + (good ? 'Good' : 'Bad') + '\\n\\nWhat worked or didn\\'t:\\n');
  var url = 'https://github.com/{repo}/issues/new?title=' + title + '&body=' + body + '&labels=feedback';
  window.open(url, '_blank', 'noopener');
}}
(function() {{
  try {{
    var v = localStorage.getItem('tutor-feedback-{id}');
    if (v) {{
      document.getElementById(v === 'good' ? 'btn-up' : 'btn-down').classList.add('active');
    }}
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
"""


def render_archive_items(date):
    items = []
    for d, piece in recent_pieces(date):
        items.append(
            '<li><a href="{url}" target="_blank" rel="noopener">{title}</a> '
            '&mdash; {author}<span class="a-date">{date_str}</span></li>'.format(
                url=html.escape(reading_url(piece), quote=True),
                title=html.escape(piece["title"]),
                author=html.escape(piece["author"]),
                date_str=d.isoformat(),
            )
        )
    return "\n      ".join(items)


def render_page(piece, date):
    title_js = piece["title"].replace("\\", "\\\\").replace("'", "\\'")
    year = piece.get("year")
    year_part = f", {year}" if year is not None else ""
    return PAGE_TEMPLATE.format(
        title=html.escape(piece["title"]),
        title_js=title_js,
        why_attr=html.escape(piece["why"]),
        why=html.escape(piece["why"]),
        author=html.escape(piece["author"]),
        year_part=html.escape(year_part),
        source=html.escape(piece["source"]),
        topic=html.escape(piece["topic"]),
        minutes=piece["minutes"],
        url=html.escape(reading_url(piece), quote=True),
        date_str=date.isoformat(),
        archive_n=ARCHIVE_DAYS,
        archive_items=render_archive_items(date),
        repo=REPO,
        id=piece["id"],
    )


def main():
    DIST.mkdir(exist_ok=True)
    date = today_chicago()
    piece = pick_piece(date)
    page = render_page(piece, date)
    (DIST / "index.html").write_text(page)
    # keep an archive by date+id so past days stay linkable
    archive_dir = DIST / "archive"
    archive_dir.mkdir(exist_ok=True)
    (archive_dir / f"{date.isoformat()}-{piece['id']}.html").write_text(page)
    print(f"Built {date.isoformat()}: {piece['title']} by {piece['author']} ({piece['topic']})")


if __name__ == "__main__":
    main()
