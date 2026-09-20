import json
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

    def test_dyson_entry_declares_the_verified_snapshot_fallback(self):
        piece = next(piece for piece in self.library["pieces"] if piece["id"] == "dyson-birds-frogs")
        self.assertEqual(generate.reading_url(piece), piece["fallback_url"])
        self.assertIn(piece["fallback_url"], verify_links.source_urls(piece))


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
