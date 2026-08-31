# Daily Tutor

A daily-article teaching site. A new topic every day, from a broad subject
bank — math, science, computing, finance, humanities, music theory, low-level
architecture, economics, linguistics, engineering, history. Deployed at
[ericspencer.us/tutor](https://ericspencer.us/tutor) via GitHub Pages.

## How it works

- `.github/workflows/daily-tutor.yml` runs on a daily cron (06:00 America/Chicago),
  builds the page, and deploys it to GitHub Pages.
- `site/generate.py` deterministically picks the day's topic from
  `site/topics.json` by calendar date, no randomness, no network calls, no API
  keys.
- If `site/articles/<slug>.md` exists for that topic, the full written
  article renders. Otherwise a study-outline page renders instead, so every
  topic in the bank always has something live.

## Adding articles

Write ~500-700 words in `site/articles/<slug>.md`:

```
---
title: Article Title
category: Category Name
summary: One sentence, shown as the meta description and outline blurb.
---

Body text. Paragraphs separated by blank lines. Supports **bold**,
*italic*, and `## headers`.
```

Add a matching entry to `site/topics.json` for any new topic (slug, title,
category, summary). **Claude sessions: feel free to append new articles here
over time** — the bank is meant to grow.

## Feedback

Good/Bad buttons on each page save a rating to `localStorage` and open a
pre-filled GitHub issue (`labels=feedback`) — no backend required.

## Local test

```bash
python3 site/generate.py && open site/dist/index.html
```

## Origin

Seeded from the daily-lesson tutor app at
[EricSpencer00/reading-room-tutor](https://github.com/EricSpencer00/reading-room-tutor)
(private) — that repo's local interactive tutor and this static daily-article
site are independent products sharing a topic bank.
