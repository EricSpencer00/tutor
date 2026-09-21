#!/usr/bin/env python3
"""Validate the shape and editorial minimums of the curated library."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "id", "title", "author", "year", "source", "url", "topic", "minutes", "why"
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEXT_FIELDS = {"title", "author", "source", "topic", "why"}


def validate(path):
    data = json.loads(Path(path).read_text())
    pieces = data.get("pieces") if isinstance(data, dict) else None
    errors = []

    if not isinstance(pieces, list) or not pieces:
        return ["top-level 'pieces' must be a non-empty array"]

    ids = set()
    urls = set()
    for index, piece in enumerate(pieces, start=1):
        label = f"entry {index}"
        if not isinstance(piece, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = REQUIRED - piece.keys()
        if missing:
            errors.append(f"{label} missing: {', '.join(sorted(missing))}")

        for field in TEXT_FIELDS:
            value = piece.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} {field} must be a non-empty string")

        entry_id = piece.get("id")
        if not isinstance(entry_id, str) or not ID_PATTERN.fullmatch(entry_id):
            errors.append(f"{label} id must be kebab-case lowercase text")
        elif entry_id in ids:
            errors.append(f"{label} duplicates id '{entry_id}'")
        else:
            ids.add(entry_id)

        url = piece.get("url")
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label} url must be an absolute http(s) URL")
        elif url in urls:
            errors.append(f"{label} duplicates url '{url}'")
        else:
            urls.add(url)

        year = piece.get("year")
        if isinstance(year, bool) or not isinstance(year, int):
            errors.append(f"{label} year must be an integer")

        minutes = piece.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, int) or not 1 <= minutes <= 240:
            errors.append(f"{label} minutes must be an integer from 1 to 240")

        why = piece.get("why")
        if isinstance(why, str) and len(why.strip()) < 80:
            errors.append(f"{label} why note must be at least 80 characters")

    return errors


def main():
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} LIBRARY.json", file=sys.stderr)
        return 2
    errors = validate(sys.argv[1])
    if errors:
        print("Library validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    with Path(sys.argv[1]).open() as handle:
        count = len(json.load(handle)["pieces"])
    print(f"Validated {count} library entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
