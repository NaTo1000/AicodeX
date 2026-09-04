"""Metrics panel and usage control deck for AicodeX Edition 2.

The metrics panel sits on top of the compute-backend links and lets a user
*click into* the parameters/usage **control deck** to monitor:

- **token usage per model output** (tokens and cost per output),
- **cost per token** for each model, and
- **better-model swap suggestions** — when a model provides the same or more
  value (tokens delivered) at a lower cost per token than a more expensive one.

Usage rolls up into a **platform-wide total** across all users, and
:func:`render_page` renders a self-contained HTML **metrics web page** so other
users can see the current value trend per model and an overall report on the
value each model provided from actual build-performance analysis.

Standard library only; deterministic; no network access.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


@dataclass
class UsageRecord:
    """A single model output's measured token usage.

    Attributes
    ----------
    model:
        The model that produced the output.
    tokens:
        Number of tokens in the output.
    user:
        The user that triggered the output (for platform-wide aggregation).
    cost_usd:
        Optional explicit cost. When omitted it is derived from the model's
        configured cost per token.
    """

    model: str
    tokens: int
    user: str = "local"
    cost_usd: Optional[float] = None


@dataclass
class ModelStats:
    """Aggregated statistics for one model."""

    model: str
    outputs: int = 0
    tokens: int = 0
    cost_usd: float = 0.0
    users: set = field(default_factory=set)

    @property
    def cost_per_token(self) -> float:
        return self.cost_usd / self.tokens if self.tokens else 0.0

    @property
    def tokens_per_output(self) -> float:
        return self.tokens / self.outputs if self.outputs else 0.0


class MetricsPanel:
    """The usage control deck: records usage and computes value metrics."""

    def __init__(self, cost_per_token: Optional[Mapping[str, float]] = None) -> None:
        # Configured cost per token (USD) per model; used when a UsageRecord
        # does not carry an explicit cost.
        self._cost_per_token: Dict[str, float] = {
            str(k): float(v) for k, v in (cost_per_token or {}).items()}
        self._records: List[UsageRecord] = []

    # -- recording ---------------------------------------------------------

    def record(self, record: UsageRecord) -> None:
        """Add a usage record, deriving cost when not explicitly provided."""
        if record.tokens < 0:
            raise ValueError("tokens must be >= 0")
        if record.cost_usd is None:
            rate = self._cost_per_token.get(record.model, 0.0)
            record.cost_usd = round(rate * record.tokens, 6)
        self._records.append(record)

    def record_output(self, model: str, tokens: int, user: str = "local",
                      cost_usd: Optional[float] = None) -> UsageRecord:
        """Convenience wrapper to record a single model output."""
        record = UsageRecord(model=model, tokens=tokens, user=user,
                             cost_usd=cost_usd)
        self.record(record)
        return record

    # -- aggregation --------------------------------------------------------

    def per_model(self) -> Dict[str, ModelStats]:
        """Aggregate statistics per model across all users."""
        stats: Dict[str, ModelStats] = {}
        for record in self._records:
            model_stats = stats.setdefault(record.model, ModelStats(model=record.model))
            model_stats.outputs += 1
            model_stats.tokens += record.tokens
            model_stats.cost_usd += record.cost_usd or 0.0
            model_stats.users.add(record.user)
        return stats

    def totals(self) -> ModelStats:
        """Platform-wide totals across all users and models."""
        total = ModelStats(model="__platform__")
        users: set = set()
        for model_stats in self.per_model().values():
            total.outputs += model_stats.outputs
            total.tokens += model_stats.tokens
            total.cost_usd += model_stats.cost_usd
            users |= model_stats.users
        total.users = users
        return total

    # -- recommendations -----------------------------------------------------

    def swap_suggestions(self) -> List[str]:
        """Suggest cheaper models that deliver equal-or-more value.

        A model ``B`` is a candidate swap for a more expensive model ``A`` when
        ``B``'s cost per token is strictly lower and its tokens-per-output (a
        proxy for delivered value) is at least ``A``'s.
        """
        stats = list(self.per_model().values())
        suggestions: List[str] = []
        for expensive in stats:
            for cheaper in stats:
                if cheaper is expensive:
                    continue
                if (cheaper.cost_per_token < expensive.cost_per_token
                        and cheaper.tokens_per_output >= expensive.tokens_per_output
                        and cheaper.tokens_per_output > 0):
                    suggestions.append(
                        f"Consider swapping {expensive.model} -> {cheaper.model}: "
                        f"lower cost/token "
                        f"({cheaper.cost_per_token:.6f} vs {expensive.cost_per_token:.6f} USD) "
                        f"with >= value "
                        f"({cheaper.tokens_per_output:.1f} vs {expensive.tokens_per_output:.1f} tokens/output)")
                    break
        return suggestions

    # -- reporting -----------------------------------------------------------

    def render_text(self) -> str:
        """Render the control-deck summary as aligned plain text."""
        lines = ["AicodeX Edition 2 — Metrics Control Deck", "=" * 60,
                 f"{'model':<10} {'outputs':>7} {'tokens':>10} "
                 f"{'cost USD':>10} {'USD/token':>10} {'tok/out':>8}"]
        for model_stats in sorted(self.per_model().values(),
                                  key=lambda s: s.cost_per_token):
            lines.append(
                f"{model_stats.model:<10} {model_stats.outputs:>7} "
                f"{model_stats.tokens:>10} {model_stats.cost_usd:>10.4f} "
                f"{model_stats.cost_per_token:>10.6f} "
                f"{model_stats.tokens_per_output:>8.1f}")
        total = self.totals()
        lines.append("-" * 60)
        lines.append(f"{'TOTAL':<10} {total.outputs:>7} {total.tokens:>10} "
                     f"{total.cost_usd:>10.4f} {'':>10} "
                     f"{total.tokens_per_output:>8.1f}  users={len(total.users)}")
        suggestions = self.swap_suggestions()
        if suggestions:
            lines.append("")
            lines.append("Better-model swap suggestions:")
            lines.extend(f"  - {s}" for s in suggestions)
        return "\n".join(lines)

    def render_page(self) -> str:
        """Render a self-contained HTML metrics web page.

        Shows the per-model value trend and the platform-wide total so other
        users can see the value each model provided. All dynamic text is
        HTML-escaped.
        """
        esc = html.escape
        rows = []
        for model_stats in sorted(self.per_model().values(),
                                  key=lambda s: s.cost_per_token):
            rows.append(
                "<tr>"
                f"<td>{esc(model_stats.model)}</td>"
                f"<td>{model_stats.outputs}</td>"
                f"<td>{model_stats.tokens}</td>"
                f"<td>{model_stats.cost_usd:.4f}</td>"
                f"<td>{model_stats.cost_per_token:.6f}</td>"
                f"<td>{model_stats.tokens_per_output:.1f}</td>"
                f"<td>{len(model_stats.users)}</td>"
                "</tr>")
        total = self.totals()
        suggestions = "".join(
            f"<li>{esc(s)}</li>" for s in self.swap_suggestions()) or \
            "<li>No swap suggestions — current selection is cost-efficient.</li>"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AicodeX Edition 2 — Model Value Metrics</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
 h1 {{ font-size: 1.4rem; }}
 table {{ border-collapse: collapse; min-width: 40rem; }}
 th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.7rem; text-align: right; }}
 th {{ background: #f2f2f2; }}
 td:first-child, th:first-child {{ text-align: left; }}
 .total {{ font-weight: bold; background: #eef; }}
</style>
</head>
<body>
<h1>AicodeX Edition 2 — Model Value Metrics</h1>
<p>Platform-wide token usage and value per model, aggregated across all users.</p>
<table>
 <thead><tr>
  <th>Model</th><th>Outputs</th><th>Tokens</th><th>Cost (USD)</th>
  <th>USD / token</th><th>Tokens / output</th><th>Users</th>
 </tr></thead>
 <tbody>
  {''.join(rows)}
  <tr class="total"><td>TOTAL</td><td>{total.outputs}</td>
   <td>{total.tokens}</td><td>{total.cost_usd:.4f}</td><td></td>
   <td>{total.tokens_per_output:.1f}</td><td>{len(total.users)}</td></tr>
 </tbody>
</table>
<h2>Better-model swap suggestions</h2>
<ul>{suggestions}</ul>
</body>
</html>
"""
