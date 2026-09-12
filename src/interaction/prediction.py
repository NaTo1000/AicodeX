"""HiAi + PECs code prediction engine.

:class:`CodePredictor` analyses a submitted snippet and **predicts** its:

* **language** — via keyword/construct signatures (the predetermined
  algorithms), file-extension hints, and the user's coding *style*;
* **algorithmic family** — sorting, searching, dynamic programming,
  graph traversal, recursion, parsing, concurrency, I/O, etc.; and
* **format** — the serialisation/interchange format the code reads/writes.

The prediction fuses several signals (this is the **HiAi** heuristic layer) and
normalises the snippet through the PECs **term-control** system
(:class:`~assistant.router.TermControl`) so decisions are made over controlled
terms and recorded in retention for history-aware priors. Every prediction
carries a confidence and a rationale so the user can see *why*.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .languages import LanguageCatalog

# Predetermined keyword signatures per language. Tokens are matched
# case-insensitively as whole words / substrings against the snippet.
_LANGUAGE_SIGNATURES: Dict[str, Tuple[str, ...]] = {
    "python": ("def ", "import ", "print(", "self", "elif", "lambda ", ":", "None", "True", "__init__"),
    "javascript": ("function ", "const ", "let ", "var ", "=>", "console.log", "require(", "module.exports"),
    "typescript": ("interface ", ": string", ": number", "const ", "implements ", "enum ", "readonly "),
    "swift": ("func ", "let ", "var ", "guard ", "struct ", "import Foundation", "@State", "some View"),
    "rust": ("fn ", "let mut", "impl ", "match ", "println!", "-> ", "&str", "pub "),
    "go": ("func ", "package ", "import (", ":=", "fmt.", "go func", "chan "),
    "java": ("public class", "public static void main", "System.out.println", "private ", "new ", ";"),
    "kotlin": ("fun ", "val ", "var ", "data class", "println(", ": String"),
    "c": ("#include", "int main", "printf(", "malloc(", "->", ";"),
    "cpp": ("#include <", "std::", "cout", "int main", "template <", "::", "nullptr"),
    "csharp": ("using System", "public class", "Console.WriteLine", "namespace ", "var ", "{ get;"),
    "ruby": ("def ", "end", "puts ", "require ", "@", "do |"),
    "php": ("<?php", "$", "echo ", "function ", "->"),
    "r": ("<-", "library(", "data.frame", "ggplot", "function("),
    "scala": ("def ", "val ", "var ", "object ", "extends ", "case class"),
    "haskell": ("::", "->", "where", "let ", "data ", "module "),
    "lua": ("function ", "local ", "end", "then", "require "),
    "perl": ("use strict", "my $", "sub ", "print ", "@_"),
    "sql": ("select ", "from ", "where ", "insert into", "create table", "join "),
    "shell": ("#!/bin", "echo ", "$", "fi", "then", "#!/usr/bin/env", "function "),
    "html": ("<html", "<div", "<!doctype", "<script", "<body", "<span", "<p>", "<head"),
    "css": ("color:", "margin:", "padding:", "@media", "font-size", "background:", "display:", "#"),
    "dart": ("void main", "Widget ", "build(", "import 'package:", "final "),
    "objectivec": ("#import", "@interface", "@implementation", "NSLog", "@end"),
    "julia": ("function ", "end", "println(", "::", "using "),
}

# Format signatures — what the code reads/writes. Tokens are deliberately
# distinctive (no bare "{" / "," / "=") so format detection is meaningful.
_FORMAT_SIGNATURES: Dict[str, Tuple[str, ...]] = {
    "json": ("json.", "json.loads", "json.dumps", "json.load(", "json.dump(", "tojson", "jsonencoder", "stringify(", "json.parse"),
    "yaml": ("yaml.", "yaml.safe_load", "yaml.load", "safe_load(", ".yml", ".yaml"),
    "toml": ("toml.", "toml.load", "toml.parse", "# toml", "pyproject.toml"),
    "xml": ("<?xml", "etree", "elementtree", "xml.dom", "xml.sax", "tostring(", "<rss", "lxml"),
    "csv": ("csv.", "csv.reader", "csv.writer", "dictreader", "dictwriter", "read_csv"),
    "markdown": ("## ", "- [", "](", "```", "__bold__", "**bold**"),
    "html": ("<html", "<div", "<!doctype", "<body", "<script", "beautifulsoup"),
    "sql": ("select ", "insert into", "create table", "execute(", "alter table", "drop table"),
    "shell": ("#!/bin", "#!/usr/bin/env", "echo ", "subprocess"),
}

# Algorithmic-family signatures.
_ALGORITHM_SIGNATURES: Dict[str, Tuple[str, ...]] = {
    "sorting": ("sort(", "sorted(", "quicksort", "mergesort", "bubble", "order by", "heapify"),
    "searching": ("binary_search", "indexof", "find(", "search(", "contains(", "lookup"),
    "dynamic_programming": ("dp[", "memo", "cache", "fibonacci", "knapsack", "lcs"),
    "graph": ("dfs", "bfs", "graph", "node", "edge", "adjacency", "dijkstra", "topological"),
    "recursion": ("recursion", "recursive", "return ", "base case"),
    "parsing": ("parse(", "tokenize", "lexer", "ast", "regex", "split("),
    "concurrency": ("thread", "async", "await", "goroutine", "lock", "mutex", "parallel", "spawn"),
    "io": ("open(", "read(", "write(", "file", "socket", "request", "input"),
    "math": ("sqrt", "pow(", "factorial", "gcd", "prime", "mod"),
    "ml": ("model", "train(", "predict(", "tensor", "epoch", "loss", "neural"),
}

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class StyleFingerprint:
    """A light-weight coding-style fingerprint used as a prediction signal."""

    def __init__(self, indent: int = 4, uses_tabs: bool = False, quote: str = "double", brace_same_line: bool = True) -> None:
        self.indent = int(indent)
        self.uses_tabs = bool(uses_tabs)
        self.quote = quote
        self.brace_same_line = bool(brace_same_line)

    @classmethod
    def from_code(cls, code: str) -> "StyleFingerprint":
        lines = code.splitlines()
        indent = 4
        uses_tabs = any(l.startswith("\t") for l in lines)
        # Detect a common indent width from leading spaces.
        for l in lines:
            stripped = l.lstrip(" ")
            if stripped and l[: len(l) - len(stripped)]:
                indent = max(1, len(l) - len(stripped))
                break
        single = code.count("'")
        double = code.count('"')
        quote = "single" if single > double else "double"
        brace_same_line = "{\n" not in code and "{" in code
        return cls(indent=indent, uses_tabs=uses_tabs, quote=quote, brace_same_line=brace_same_line)

    def as_dict(self) -> Dict[str, object]:
        return {
            "indent": self.indent,
            "uses_tabs": self.uses_tabs,
            "quote": self.quote,
            "brace_same_line": self.brace_same_line,
        }


class Prediction:
    """The result of predicting a snippet's language/algorithm/format."""

    def __init__(
        self,
        language: str,
        language_confidence: float,
        variant: str,
        fmt: str,
        format_confidence: float,
        algorithm: str,
        algorithm_confidence: float,
        terms: List[str],
        rationale: str,
        candidates: List[Tuple[str, float]],
    ) -> None:
        self.language = language
        self.language_confidence = float(language_confidence)
        self.variant = variant
        self.format = fmt
        self.format_confidence = float(format_confidence)
        self.algorithm = algorithm
        self.algorithm_confidence = float(algorithm_confidence)
        self.terms = list(terms)
        self.rationale = rationale
        self.candidates = list(candidates)

    def as_dict(self) -> Dict[str, object]:
        return {
            "language": self.language,
            "language_confidence": round(self.language_confidence, 4),
            "variant": self.variant,
            "format": self.format,
            "format_confidence": round(self.format_confidence, 4),
            "algorithm": self.algorithm,
            "algorithm_confidence": round(self.algorithm_confidence, 4),
            "terms": self.terms,
            "rationale": self.rationale,
            "candidates": [(k, round(v, 4)) for k, v in self.candidates],
        }

    def summary(self) -> str:
        return (
            f"Language: {self.language} ({self.variant}) conf={self.language_confidence:.2f}\n"
            f"Format: {self.format} conf={self.format_confidence:.2f}\n"
            f"Algorithm: {self.algorithm} conf={self.algorithm_confidence:.2f}\n"
            f"Why: {self.rationale}"
        )


class CodePredictor:
    """HiAi heuristic predictor with PECs term-control over a language catalog."""

    def __init__(self, catalog: Optional[LanguageCatalog] = None, term_control=None) -> None:
        self.catalog = catalog or LanguageCatalog()
        # PECs term-control: reuse the assistant's TermControl when available.
        if term_control is None:
            try:
                from ..assistant.router import TermControl  # type: ignore
                term_control = TermControl()
            except Exception:  # pragma: no cover - fallback when assistant absent
                term_control = None
        self.term_control = term_control

    # -- signal scorers ----------------------------------------------------
    def _score(self, code: str, signatures: Dict[str, Tuple[str, ...]]) -> Dict[str, float]:
        lowered = code.lower()
        scores: Dict[str, float] = {}
        for key, sigs in signatures.items():
            hits = sum(1 for s in sigs if s.lower() in lowered)
            scores[key] = hits / float(len(sigs)) if sigs else 0.0
        return scores

    def _terms(self, code: str) -> List[str]:
        if self.term_control is not None:
            return self.term_control.controlled_terms(code)
        return list(dict.fromkeys(_WORD_RE.findall(code.lower())))[:12]

    def _top(self, scores: Dict[str, float]) -> Tuple[str, float, List[Tuple[str, float]]]:
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if not ranked or ranked[0][1] <= 0.0:
            return "unknown", 0.0, ranked[:3]
        # Confidence = top score, dampened by how close the runner-up is.
        top, top_score = ranked[0]
        runner = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = max(0.0, top_score - runner)
        confidence = min(1.0, top_score * 0.8 + margin * 0.2)
        return top, confidence, ranked[:3]

    def _pick_variant(self, language: str, code: str) -> str:
        variants = self.catalog.variants(language)
        if not variants:
            return "standard"
        lowered = code.lower()
        for v in variants:
            if v.lower() in lowered:
                return v
        # Language-specific heuristics for a sensible default variant.
        if language == "python" and "asyncio" in lowered:
            return "cpython"
        if language == "swift" and ("swiftui" in lowered or "some view" in lowered):
            return "swiftui"
        return variants[0]

    # -- main entry --------------------------------------------------------
    def predict(self, code: object, filename: Optional[str] = None) -> Prediction:
        text = code if isinstance(code, str) else str(code or "")
        if not text.strip():
            return Prediction(
                "unknown", 0.0, "standard", "text", 0.0, "unknown", 0.0, [],
                "Empty submission — nothing to analyse.", [],
            )

        terms = self._terms(text)
        style = StyleFingerprint.from_code(text)

        lang_scores = self._score(text, _LANGUAGE_SIGNATURES)
        # Extension hint boosts the matching language.
        ext_lang = None
        if filename and "." in filename:
            ext_lang = self.catalog.by_extension(filename.rsplit(".", 1)[1])
            if ext_lang is not None:
                lang_scores[ext_lang.name] = lang_scores.get(ext_lang.name, 0.0) + 0.15

        # Style nudge: heavy brace usage with same-line braces leans C-family.
        if "{" in text and style.brace_same_line:
            for c_family in ("c", "cpp", "csharp", "java", "javascript", "typescript", "go", "rust"):
                lang_scores[c_family] = lang_scores.get(c_family, 0.0) + 0.03

        language, lang_conf, candidates = self._top(lang_scores)
        fmt, fmt_conf, _ = self._top(self._score(text, _FORMAT_SIGNATURES))
        algorithm, algo_conf, _ = self._top(self._score(text, _ALGORITHM_SIGNATURES))
        variant = self._pick_variant(language, text)

        if ext_lang is not None and language == ext_lang.name:
            rationale = (
                f"Extension '.{filename.rsplit('.', 1)[1]}' and construct signatures agree on "
                f"'{language}'."
            )
        elif language != "unknown":
            top_sigs = ", ".join(t for t in terms[:4]) or "n/a"
            rationale = (
                f"Construct signatures point to '{language}' (key terms: {top_sigs}); "
                f"variant '{variant}' inferred from style/usage."
            )
        else:
            rationale = "No strong language signature matched; providing a filename hint would help."

        return Prediction(
            language, round(lang_conf, 4), variant, fmt, round(fmt_conf, 4),
            algorithm, round(algo_conf, 4), terms, rationale, candidates,
        )
