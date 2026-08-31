#!/usr/bin/env python3
"""Verify every library URL actually serves the document it claims.

A 200 is not enough: a dead deep link often redirects to a site homepage and
returns 200. So we check three things.
  1. the request succeeds
  2. the final URL still has a real path (a redirect to "/" means the document
     is gone)
  3. the body looks like the named work — a PDF magic number, or HTML that
     mentions distinctive words from the title or the author's surname
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
# These hosts return 403 to any scripted request but serve the document
# normally in a browser. Each was checked by hand in a real browser. A 403 from
# one of these is not evidence the document is gone.
BOT_BLOCKED = {
    "www.feynmanlectures.caltech.edu",
    "www.etsy.com",
}

STOP = {"the", "a", "an", "of", "on", "in", "to", "and", "for", "about", "is",
        "it", "be", "as", "at", "by", "from", "with", "more", "than", "what",
        "who", "why", "how", "not", "we", "may", "can", "will", "our", "your"}


def fetch(url):
    """Return (status, final_url, content_type, body_bytes)."""
    out = subprocess.run(
        ["curl", "-sSL", "--max-time", "30", "-A", UA,
         "-w", "\n__META__%{http_code}|%{url_effective}|%{content_type}",
         "--max-filesize", "8000000", url],
        capture_output=True, timeout=60)
    raw = out.stdout
    marker = raw.rfind(b"\n__META__")
    if marker == -1:
        return 0, url, "", b""
    body = raw[:marker]
    meta = raw[marker + 9:].decode("utf-8", "replace")
    parts = meta.split("|")
    status = int(parts[0]) if parts[0].isdigit() else 0
    return status, parts[1] if len(parts) > 1 else url, parts[2] if len(parts) > 2 else "", body


def keywords(piece):
    title = re.sub(r"[^a-z0-9 ]", " ", piece["title"].lower())
    words = [w for w in title.split() if len(w) > 3 and w not in STOP]
    surname = piece["author"].split(" and ")[0].split()[-1].lower()
    return words, surname


def check(piece):
    url = piece["url"]
    try:
        status, final, ctype, body = fetch(url)
    except Exception as e:
        return piece, "ERROR", f"fetch failed: {e}"

    if status == 403 and urlparse(url).netloc in BOT_BLOCKED:
        return piece, "OK", "403 to scripts; browser-verified host"

    if status >= 400 or status == 0:
        return piece, "DEAD", f"HTTP {status}"

    # redirected away from a deep link to a site root
    orig_path = urlparse(url).path.rstrip("/")
    final_path = urlparse(final).path.rstrip("/")
    if orig_path and len(orig_path) > 1 and final_path in ("", "/"):
        return piece, "REDIRECTED", f"-> {final} (homepage)"

    if body.startswith(b"%PDF") or "application/pdf" in ctype:
        # a large PDF may be cut short by --max-filesize; the content-type from
        # the server is authoritative in that case
        return piece, "OK", f"PDF {len(body)//1024}KB"

    if url.lower().endswith(".pdf"):
        return piece, "NOT-PDF", f"served {ctype} at {final}"

    text = body.decode("utf-8", "replace").lower()
    text = re.sub(r"<[^>]+>", " ", text)
    words, surname = keywords(piece)
    hits = sum(1 for w in words if w in text)
    if surname in text or hits >= max(1, len(words) // 2):
        return piece, "OK", f"html, {hits}/{len(words)} title words, author={'y' if surname in text else 'n'}"
    return piece, "SUSPECT", f"content match weak ({hits}/{len(words)} words, no '{surname}') at {final}"


def main():
    lib = json.load(open(sys.argv[1]))
    pieces = lib["pieces"]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(check, pieces))
    bad = []
    for piece, verdict, detail in results:
        if verdict != "OK":
            bad.append((piece, verdict, detail))
        print(f"{verdict:11} {piece['id']:34} {detail}")
    print(f"\n{len(pieces)-len(bad)}/{len(pieces)} verified. {len(bad)} need attention.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
