"""Close-of-Business (COB) daily reporting for AicodeX Edition 2.

At the end of each day the monitor's metrics are rolled into a COB report:

- **who is the best at what job** — the top performer per job/metric,
- a **daily article** summarising the day for the public forum page, and
- **allocation of user-wanted improvements** to a discussion channel
  (voice message or email).

Standard library only; deterministic (the report date is injectable).
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Mapping, Optional, Sequence


@dataclass
class JobScore:
    """A component's score on a job/metric for the day."""

    component: str
    job: str
    score: float


@dataclass
class ImprovementRequest:
    """A user-wanted improvement, allocated to a contact channel."""

    title: str
    requested_by: str
    channel: str = "forum"     # forum | voice | email
    contact: Optional[str] = None  # email address or voice thread ref

    def channel_label(self) -> str:
        return {"voice": "voice message", "email": "email"}.get(
            self.channel, self.channel)


@dataclass
class CobReport:
    """The close-of-business daily report."""

    day: str
    best_per_job: Dict[str, JobScore] = field(default_factory=dict)
    improvements: List[ImprovementRequest] = field(default_factory=list)

    def article_title(self) -> str:
        return f"AicodeX Daily Build Report — {self.day}"

    def render_text(self) -> str:
        lines = [self.article_title(), "=" * 55,
                 "Best at each job:"]
        if self.best_per_job:
            for job in sorted(self.best_per_job):
                score = self.best_per_job[job]
                lines.append(f"  {job:<24} -> {score.component} "
                             f"({score.score:.1f})")
        else:
            lines.append("  (no job scores recorded today)")
        lines.append("")
        lines.append(f"User-wanted improvements: {len(self.improvements)}")
        for req in self.improvements:
            contact = f" <{req.contact}>" if req.contact else ""
            lines.append(f"  - {req.title} (by {req.requested_by}) "
                         f"[{req.channel_label()}{contact}]")
        return "\n".join(lines)


class CobReporter:
    """Aggregates daily job scores and improvement requests into a report."""

    def __init__(self, jobs: Optional[Sequence[str]] = None) -> None:
        self._jobs = list(jobs or [])
        self._scores: List[JobScore] = []
        self._improvements: List[ImprovementRequest] = []

    def record_score(self, component: str, job: str, score: float) -> JobScore:
        entry = JobScore(component=component, job=job, score=float(score))
        self._scores.append(entry)
        return entry

    def add_improvement(self, title: str, requested_by: str,
                        channel: str = "forum",
                        contact: Optional[str] = None) -> ImprovementRequest:
        if channel not in ("forum", "voice", "email"):
            raise ValueError("channel must be one of forum|voice|email")
        req = ImprovementRequest(title=title, requested_by=requested_by,
                                 channel=channel, contact=contact)
        self._improvements.append(req)
        return req

    def best_per_job(self) -> Dict[str, JobScore]:
        """Return the highest-scoring component for each job."""
        best: Dict[str, JobScore] = {}
        for score in self._scores:
            current = best.get(score.job)
            if current is None or score.score > current.score:
                best[score.job] = score
        return best

    def build(self, day: Optional[str] = None) -> CobReport:
        """Build the COB report for ``day`` (defaults to today, ISO)."""
        report_day = day or date.today().isoformat()
        return CobReport(day=report_day, best_per_job=self.best_per_job(),
                         improvements=list(self._improvements))

    def daily_article(self, day: Optional[str] = None) -> str:
        """Generate the daily article for the public forum page."""
        report = self.build(day)
        esc = html.escape
        parts = [f"# {report.article_title()}", "",
                 "Today's build-performance leaders:"]
        if report.best_per_job:
            for job in sorted(report.best_per_job):
                score = report.best_per_job[job]
                parts.append(f"- **{job}** — {score.component} "
                             f"(score {score.score:.1f})")
        else:
            parts.append("- No job scores recorded today.")
        if report.improvements:
            parts += ["", "Community improvement requests allocated:"]
            for req in report.improvements:
                parts.append(f"- {req.title} — via {req.channel_label()}")
        # The article is markdown text for the forum; escape is applied by the
        # forum renderer, so return raw text here. (esc kept for callers that
        # embed directly.)
        _ = esc
        return "\n".join(parts)
