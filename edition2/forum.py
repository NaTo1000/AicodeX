"""Public community forum page for AicodeX Edition 2.

The forum is a **link off the app but wholly connected to it** — a live web
page that **non-members can access and read**. It hosts the daily COB article,
discussions, and allocated voice-message / email improvement requests.

The page rendered by :func:`render_forum_page` is read-only for the public:
visitors can read everything, but posting is reserved for members inside the
app. All dynamic text is HTML-escaped. Standard library only; deterministic
(the page timestamp and live-refresh interval are injectable).
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import List, Optional

from .cob import CobReport


@dataclass
class Discussion:
    """A forum discussion thread."""

    title: str
    author: str
    body: str
    replies: List[str] = field(default_factory=list)


@dataclass
class ForumPage:
    """The community forum page model."""

    title: str = "AicodeX Community Forum"
    public: bool = True          # non-members can access and read
    read_only: bool = True       # visitors read; members post via the app
    refresh_seconds: float = 0.5  # live-page refresh cadence
    articles: List[str] = field(default_factory=list)   # daily COB articles
    discussions: List[Discussion] = field(default_factory=list)


class CommunityForum:
    """Builds the public, read-only community forum page."""

    def __init__(self, refresh_seconds: float = 0.5) -> None:
        self.page = ForumPage(refresh_seconds=float(refresh_seconds))

    # -- content ------------------------------------------------------------

    def publish_article(self, article_markdown: str) -> None:
        self.page.articles.append(article_markdown)

    def publish_cob(self, report: CobReport) -> None:
        """Publish a COB report's daily article to the forum."""
        self.page.articles.append(report.render_text())

    def add_discussion(self, discussion: Discussion) -> None:
        self.page.discussions.append(discussion)

    # -- rendering ------------------------------------------------------------

    def render(self) -> str:
        """Render the live, public, read-only forum page as HTML."""
        esc = html.escape
        page = self.page

        articles_html = "".join(
            f"<article><pre>{esc(a)}</pre></article>" for a in page.articles) \
            or "<p>No reports published yet.</p>"

        discussions_html = ""
        for d in page.discussions:
            replies = "".join(f"<li>{esc(r)}</li>" for r in d.replies)
            discussions_html += (
                f"<section class='thread'><h3>{esc(d.title)}</h3>"
                f"<p class='by'>by {esc(d.author)}</p>"
                f"<p>{esc(d.body)}</p>"
                f"<ul>{replies}</ul></section>")
        if not discussions_html:
            discussions_html = "<p>No discussions yet.</p>"

        access = ("Public — anyone can read. Posting is for members via the app."
                  if page.public and page.read_only else "Members only.")
        refresh_ms = int(page.refresh_seconds * 1000)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="{page.refresh_seconds}">
<title>{esc(page.title)}</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
 h1 {{ font-size: 1.5rem; }}
 .access {{ color: #555; font-style: italic; }}
 article pre {{ background: #f6f8fa; padding: 1rem; white-space: pre-wrap; }}
 .thread {{ border-top: 1px solid #ddd; padding-top: 0.5rem; }}
 .by {{ color: #777; font-size: 0.85rem; }}
</style>
</head>
<body data-live-refresh-ms="{refresh_ms}">
<h1>{esc(page.title)}</h1>
<p class="access">{esc(access)} Live page — refreshes every {page.refresh_seconds}s.</p>
<h2>Daily Reports</h2>
{articles_html}
<h2>Discussions &amp; Improvement Requests</h2>
{discussions_html}
</body>
</html>
"""
