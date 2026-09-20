# Daily Tutor

A daily reading recommendation. Each day the site picks one real, human-written
piece — an essay, lecture, or paper by a named author — and says why it is
worth your time. No model-generated article text ever appears on the site.
Deployed at [ericspencer.us/tutor](https://ericspencer.us/tutor) via GitHub
Pages, built on a daily Actions cron.

## How it works

`site/library.json` holds the curated bank: title, author, year, source,
url, topic, estimated reading minutes, and an editor's "why" note per entry.
`site/generate.py` picks the day's piece deterministically from the calendar
date (America/Chicago), rotating through the bank so a piece does not repeat
until every entry has come up once. The page shows that piece's details and
a link out to the real source, plus the last 14 days of picks computed the
same way, so a missed day is recoverable without any state file. Pure
stdlib, no network calls at build time, no API keys.

## Adding an entry

Add an object to the `pieces` array in `site/library.json`: `id` (unique,
kebab-case), `title`, `author`, `year`, `source`, `url`, `topic`, `minutes`,
and `why` (one or two sentences on what the reader gets out of it, written
by a person, not generated). If the canonical host blocks automated readers,
add `fallback_url` with an exact alternate copy; generated pages use that copy
and the link checker retries transient transport/server failures, then tries
the fallback only when the canonical URL still fails. Check the URL actually
loads before adding it.
Run `python3 site/generate.py && open site/dist/index.html` to preview.
