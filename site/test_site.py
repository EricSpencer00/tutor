import json
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import call, patch


SITE_DIR = Path(__file__).parent
sys.path.insert(0, str(SITE_DIR))

import generate  # noqa: E402
import verify_links  # noqa: E402


class LibraryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = json.loads((SITE_DIR / "library.json").read_text())

    def test_every_piece_has_unique_curated_fields(self):
        pieces = self.library["pieces"]
        ids = [piece["id"] for piece in pieces]
        self.assertEqual(len(ids), len(set(ids)))
        for piece in pieces:
            for field in ("id", "title", "author", "source", "url", "topic", "minutes", "why"):
                self.assertTrue(piece.get(field), f"{piece.get('id')} missing {field}")
            self.assertTrue(piece["url"].startswith(("http://", "https://")))
            if "fallback_url" in piece:
                self.assertTrue(piece["fallback_url"].startswith("https://"))
                self.assertNotEqual(piece["url"], piece["fallback_url"])

    def test_blocked_sources_declare_verified_fallbacks(self):
        expected = {
            "dyson-birds-frogs": "https://web.archive.org/web/20110304104413/http://www.ams.org/notices/200902/rtx090200212p.pdf",
            "gowers-two-cultures": "https://www.maths.tcd.ie/~bnick/Gowers.pdf",
        }
        pieces = {piece["id"]: piece for piece in self.library["pieces"]}
        for piece_id, fallback in expected.items():
            piece = pieces[piece_id]
            self.assertEqual(generate.reading_url(piece), fallback)
            self.assertIn(fallback, verify_links.source_urls(piece))


class FetchRetryTests(unittest.TestCase):
    def test_transient_transport_failure_is_retried(self):
        success = b"%PDF-1.7\n__META__200|https://example.test/work.pdf|application/pdf"
        failed = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        recovered = subprocess.CompletedProcess([], 0, stdout=success, stderr=b"")
        with patch.object(
            verify_links.subprocess,
            "run",
            side_effect=[failed, recovered],
        ) as run, patch.object(verify_links.time, "sleep") as sleep:
            result = verify_links.fetch("https://example.test/work.pdf")

        self.assertEqual(result, (200, "https://example.test/work.pdf", "application/pdf", b"%PDF-1.7"))
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(0.25)

    def test_permanent_not_found_is_not_retried(self):
        response = b"not found\n__META__404|https://example.test/work|text/html"
        completed = subprocess.CompletedProcess([], 0, stdout=response, stderr=b"")
        with patch.object(verify_links.subprocess, "run", return_value=completed) as run:
            result = verify_links.fetch("https://example.test/work")

        self.assertEqual(result, (404, "https://example.test/work", "text/html", b"not found"))
        run.assert_called_once()


class SourceFallbackTests(unittest.TestCase):
    def setUp(self):
        self.piece = {
            "id": "example",
            "title": "Example Work",
            "author": "Ada Example",
            "url": "https://canonical.example/work.pdf",
            "fallback_url": "https://archive.example/work.pdf",
        }

    def test_healthy_canonical_source_stays_preferred(self):
        with patch.object(
            verify_links,
            "fetch",
            return_value=(200, self.piece["url"], "application/pdf", b"%PDF-1.7"),
        ) as fetch:
            _, verdict, detail = verify_links.check(self.piece)

        self.assertEqual(verdict, "OK")
        self.assertNotIn("fallback", detail)
        self.assertEqual(fetch.call_args_list, [call(self.piece["url"])])

    def test_failed_canonical_source_uses_fallback(self):
        def fake_fetch(url):
            if url == self.piece["url"]:
                return 403, url, "text/html", b"blocked"
            return 200, url, "application/pdf", b"%PDF-1.7"

        with patch.object(verify_links, "fetch", side_effect=fake_fetch) as fetch:
            _, verdict, detail = verify_links.check(self.piece)

        self.assertEqual(verdict, "OK")
        self.assertIn("fallback verified", detail)
        self.assertEqual(
            fetch.call_args_list,
            [call(self.piece["url"]), call(self.piece["fallback_url"])],
        )

    def test_failed_sources_remain_a_failure(self):
        with patch.object(
            verify_links,
            "fetch",
            return_value=(404, self.piece["url"], "text/html", b"not found"),
        ):
            _, verdict, detail = verify_links.check(self.piece)

        self.assertEqual(verdict, "DEAD")
        self.assertIn("all sources failed", detail)


class GeneratedPageTests(unittest.TestCase):
    def test_fallback_is_used_in_the_generated_reader_link(self):
        piece = next(piece for piece in generate.PIECES if piece["id"] == "dyson-birds-frogs")
        page = generate.render_page(piece, date(2026, 9, 20))

        self.assertIn(f'href="{piece["fallback_url"]}"', page)
        self.assertNotIn(f'href="{piece["url"]}"', page)

    def test_archive_keeps_fourteen_deterministic_entries(self):
        entries = generate.recent_pieces(date(2026, 9, 20))
        self.assertEqual(len(entries), generate.ARCHIVE_DAYS)
        self.assertEqual(entries, generate.recent_pieces(date(2026, 9, 20)))


if __name__ == "__main__":
    unittest.main()
