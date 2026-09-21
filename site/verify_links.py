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
import time
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
FETCH_ATTEMPTS = 2
RETRYABLE_STATUSES = {0, 408, 425, 429, 500, 502, 503, 504}


def fetch(url):
    """Return (status, final_url, content_type, body_bytes)."""
    command = [
        "curl", "-sSL", "--max-time", "30", "-A", UA,
        "-w", "\n__META__%{http_code}|%{url_effective}|%{content_type}",
        "--max-filesize", "8000000", url,
    ]
    result = (0, url, "", b"")
    for attempt in range(FETCH_ATTEMPTS):
        try:
            out = subprocess.run(command, capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            out = None

        if out is None:
            result = (0, url, "", b"")
        else:
            raw = out.stdout
            marker = raw.rfind(b"\n__META__")
            if marker == -1:
                result = (0, url, "", b"")
            else:
                body = raw[:marker]
                meta = raw[marker + 9:].decode("utf-8", "replace")
                parts = meta.split("|")
                status = int(parts[0]) if parts[0].isdigit() else 0
                result = (status, parts[1] if len(parts) > 1 else url,
                          parts[2] if len(parts) > 2 else "", body)

        if result[0] not in RETRYABLE_STATUSES or attempt == FETCH_ATTEMPTS - 1:
            return result
        time.sleep(0.25)

    return result


def keywords(piece):
    title = re.sub(r"[^a-z0-9 ]", " ", piece["title"].lower())
    words = [w for w in title.split() if len(w) > 3 and w not in STOP]
    surname = piece["author"].split(" and ")[0].split()[-1].lower()
    return words, surname


def check_url(piece, url):
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


def source_urls(piece):
    """Return the canonical source followed by an optional exact fallback."""
    urls = [piece["url"]]
    fallback = piece.get("fallback_url")
    if fallback and fallback not in urls:
        urls.append(fallback)
    return urls


def check(piece):
    """Check the canonical source, then fall back only after it fails."""
    attempts = []
    for url in source_urls(piece):
        _, verdict, detail = check_url(piece, url)
        if verdict == "OK":
            if attempts:
                previous = "; ".join(f"{url}: {verdict} ({detail})" for url, verdict, detail in attempts)
                return piece, "OK", f"fallback verified after {previous}; {detail}"
            return piece, "OK", detail
        attempts.append((url, verdict, detail))

    details = "; ".join(f"{url}: {verdict} ({detail})" for url, verdict, detail in attempts)
    verdict = attempts[-1][1] if attempts else "ERROR"
    return piece, verdict, f"all sources failed: {details}"


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
