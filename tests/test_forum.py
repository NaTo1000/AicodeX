"""Standard-library tests for the AicodeX Edition 2 community forum page."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.cob import CobReporter
from edition2.forum import CommunityForum, Discussion

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
FORUM_CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["monitor"]["forum"]


class ForumModelTests(unittest.TestCase):
    def test_public_and_read_only_by_default(self) -> None:
        forum = CommunityForum()
        self.assertTrue(forum.page.public)
        self.assertTrue(forum.page.read_only)
        self.assertTrue(FORUM_CFG["public"])
        self.assertTrue(FORUM_CFG["read_only"])

    def test_live_refresh_interval(self) -> None:
        self.assertEqual(CommunityForum().page.refresh_seconds, 0.5)
        self.assertEqual(FORUM_CFG["refresh_seconds"], 0.5)

    def test_publish_article_and_discussion(self) -> None:
        forum = CommunityForum()
        forum.publish_article("# Report")
        forum.add_discussion(Discussion(title="Feature X", author="alice",
                                        body="Can we add it?"))
        self.assertEqual(len(forum.page.articles), 1)
        self.assertEqual(len(forum.page.discussions), 1)


class ForumRenderTests(unittest.TestCase):
    def test_render_is_public_readonly_live_page(self) -> None:
        forum = CommunityForum()
        page = forum.render()
        self.assertIn("<html", page)
        self.assertIn("AicodeX Community Forum", page)
        self.assertIn("anyone can read", page)
        self.assertIn('http-equiv="refresh"', page)          # live page
        self.assertIn('data-live-refresh-ms="500"', page)    # 0.5s

    def test_render_includes_articles_and_discussions(self) -> None:
        forum = CommunityForum()
        forum.publish_article("# Monday report\nLeaders: ...")
        forum.add_discussion(Discussion(title="Idea", author="bob",
                                        body="Improve caching",
                                        replies=["+1 from carol"]))
        page = forum.render()
        self.assertIn("Monday report", page)
        self.assertIn("Idea", page)
        self.assertIn("Improve caching", page)
        self.assertIn("+1 from carol", page)

    def test_render_escapes_html(self) -> None:
        forum = CommunityForum()
        forum.add_discussion(Discussion(title="<script>alert(1)</script>",
                                        author="eve", body="x"))
        page = forum.render()
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_publish_cob_report(self) -> None:
        reporter = CobReporter()
        reporter.record_score("Claude", "structure", 90.0)
        forum = CommunityForum()
        forum.publish_cob(reporter.build(day="2026-09-04"))
        page = forum.render()
        self.assertIn("AicodeX Daily Build Report — 2026-09-04", page)
        self.assertIn("Claude", page)


class CliTests(unittest.TestCase):
    def test_forum_html_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "forum.html"
            rc = cli_main(["--forum-html", str(out),
                           "--config", str(CONFIG_PATH)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            self.assertIn("AicodeX Community Forum", out.read_text())


if __name__ == "__main__":
    unittest.main()
