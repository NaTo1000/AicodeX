"""Bounded offline reference matching and declared model-capability routing.

Snippets are data: this module never executes, translates, or rewrites code.
Models are configuration labels only; no provider is contacted.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Mapping

from .crosscode_catalog import ALGORITHMS, LANGUAGES
from .hive import PerformanceController
from .orchestrator import ConfigError

MAX_REQUESTS = 256
MAX_TEXT = 8192
MAX_LABEL = 128
_DEFAULT = object()


def _text(value, name, limit=MAX_LABEL):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or any(ord(c) < 32 for c in value)):
        raise ConfigError(f"{name} must be nonempty text of at most {limit} characters without controls")
    return value


def _integer(value, name, maximum):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ConfigError(f"{name} must be an integer in [1, {maximum}]")
    return value


def _object(value, name, allowed):
    if not isinstance(value, Mapping) or set(value) - set(allowed):
        raise ConfigError(f"{name} must be an object with only: {', '.join(allowed)}")
    return value


class ReferenceCatalog:
    """Extensible through explicit language aliases and algorithm variants."""

    def __init__(self, languages=None, algorithms=None):
        languages = LANGUAGES if languages is None else languages
        algorithms = ALGORITHMS if algorithms is None else algorithms
        if not isinstance(languages, Mapping) or not languages or len(languages) > MAX_REQUESTS:
            raise ConfigError("languages must be a nonempty mapping of at most 256 entries")
        self._languages = {}
        self._aliases = {}
        for name, aliases in languages.items():
            _text(name, "language")
            if name != name.strip().lower() or name == "all":
                raise ConfigError("canonical languages must be lowercase and cannot be 'all'")
            if not isinstance(aliases, list) or len(aliases) > MAX_REQUESTS:
                raise ConfigError("aliases must be a list of at most 256 labels")
            normal = []
            for alias in [name] + aliases:
                alias = _text(alias, "alias").strip().lower()
                if alias == "all" or alias in self._aliases:
                    raise ConfigError(f"Duplicate or reserved language alias: {alias}")
                self._aliases[alias] = name
                normal.append(alias)
            self._languages[name] = normal[1:]
        if not isinstance(algorithms, Mapping) or len(algorithms) > MAX_REQUESTS:
            raise ConfigError("algorithms must be a mapping of at most 256 entries")
        self._algorithms = {}
        for name, raw in algorithms.items():
            _text(name, "algorithm")
            _object(raw, "algorithm", ("semantics", "variants"))
            semantics = _text(raw.get("semantics"), "semantics", MAX_TEXT)
            variants = raw.get("variants")
            if not isinstance(variants, Mapping):
                raise ConfigError("variants must be a language-to-snippet mapping")
            for language, snippet in variants.items():
                if language not in self._languages:
                    raise ConfigError(f"Variant language must be canonical: {language}")
                if not isinstance(snippet, str) or not snippet.strip() or len(snippet) > MAX_TEXT:
                    raise ConfigError("snippets must be nonempty text of at most 8192 characters")
            self._algorithms[name] = {"semantics": semantics, "variants": dict(variants)}

    def canonical(self, language):
        return self._aliases.get(_text(language, "language").strip().lower())

    def describe(self):
        return {"languages": deepcopy(self._languages),
                "algorithms": deepcopy(self._algorithms)}


@dataclass(frozen=True)
class ModelDeclaration:
    model_id: str
    provider: str
    languages: tuple
    algorithms: tuple
    enabled: bool


@dataclass(frozen=True)
class MatchResult:
    source_lang: str
    target_lang: str
    algorithm: str
    status: str
    reason: str = ""
    source: str = ""
    target: str = ""
    semantics: str = ""
    eligible_models: tuple = ()
    selected_model: str = ""
    provider: str = ""


@dataclass(frozen=True)
class BatchReport:
    results: tuple
    success: int
    unsupported: int
    configured_max_workers: int
    concurrency: int
    elapsed_s: float
    requests_per_second: float

    def as_dict(self):
        return asdict(self)

    def render(self):
        lines = ["Crosscode — offline curated references (model declarations only)"]
        for result in self.results:
            lines.append(f"{result.source_lang} -> {result.target_lang}: "
                         f"{result.algorithm} [{result.status}]")
            if result.status == "unsupported":
                lines.append(f"  {result.reason}")
            else:
                lines.extend([f"  Declared model: {result.selected_model} ({result.provider})",
                              f"  Domain: {result.semantics}",
                              "Source reference:", result.source,
                              "Target reference:", result.target])
        lines.append(f"success={self.success} unsupported={self.unsupported} "
                     f"concurrency={self.concurrency} configured_max_workers={self.configured_max_workers} "
                     f"elapsed_s={self.elapsed_s:.6f} requests_per_second={self.requests_per_second:.1f}")
        return "\n".join(lines)


class CrosscodeMatcher:
    """Validate once, then match batches in stable input order.

    An explicit models list replaces role-derived defaults. At least one enabled
    declaration must cover both languages and the algorithm to match a request.
    """

    def __init__(self, config=_DEFAULT, roles=(), catalog=None):
        config = {} if config is _DEFAULT else config
        _object(config, "crosscode", ("max_workers", "models", "requests"))
        self.catalog = catalog if catalog is not None else ReferenceCatalog()
        self.max_workers = _integer(config.get("max_workers", 4), "max_workers", 32)
        self._performance = PerformanceController(max_workers=self.max_workers)
        models = config.get("models")
        if "models" not in config:
            defaults = {}
            for role in roles:
                if role.model not in defaults:
                    defaults[role.model] = {
                        "model_id": role.model, "provider": "configured-role",
                        "languages": sorted(self.catalog._languages),
                        "algorithms": sorted(self.catalog._algorithms),
                        "enabled": False,
                    }
                defaults[role.model]["enabled"] |= role.enabled
            models = list(defaults.values())
        if not isinstance(models, list) or len(models) > MAX_REQUESTS:
            raise ConfigError("models must be a list of at most 256 declarations")
        self._models = {}
        for raw in models:
            _object(raw, "model", ("model_id", "provider", "languages", "algorithms", "enabled"))
            model_id = _text(raw.get("model_id"), "model_id")
            provider = _text(raw.get("provider"), "provider")
            enabled = raw.get("enabled", True)
            if type(enabled) is not bool:
                raise ConfigError("model enabled must be a boolean")
            capabilities = {}
            for field in ("languages", "algorithms"):
                values = raw.get(field)
                if not isinstance(values, list) or len(values) > MAX_REQUESTS:
                    raise ConfigError(f"model {field} must be a list of at most 256 labels")
                normalized = []
                for value in values:
                    value = _text(value, field)
                    value = self.catalog.canonical(value) if field == "languages" else value
                    known = self.catalog._languages if field == "languages" else self.catalog._algorithms
                    if value not in known:
                        raise ConfigError(f"Unknown model capability in {field}")
                    normalized.append(value)
                capabilities[field] = tuple(sorted(set(normalized)))
            if model_id in self._models:
                raise ConfigError(f"Duplicate model_id: {model_id}")
            self._models[model_id] = ModelDeclaration(
                model_id, provider, capabilities["languages"], capabilities["algorithms"], enabled)
        self.requests = self._expand(config.get("requests", []))

    def describe(self):
        return {**self.catalog.describe(),
                "models": [asdict(self._models[key]) for key in sorted(self._models)],
                "model_status": "configuration declarations, not verified provider availability"}

    def _expand(self, requests):
        if not isinstance(requests, (list, tuple)) or len(requests) > MAX_REQUESTS:
            raise ConfigError("requests must be a list/tuple of at most 256 items")
        expanded = []
        for raw in requests:
            _object(raw, "request", ("source_lang", "target_lang", "algorithm", "model"))
            request = {key: _text(raw.get(key), key)
                       for key in ("source_lang", "target_lang", "algorithm")}
            if "model" in raw:
                request["model"] = _text(raw["model"], "model")
            if request["target_lang"].strip().lower() == "all":
                source = self.catalog.canonical(request["source_lang"])
                targets = sorted(set(self.catalog._languages) - {source})
                expanded.extend(dict(request, target_lang=target) for target in targets)
            else:
                expanded.append(request)
            if len(expanded) > MAX_REQUESTS:
                raise ConfigError("Expanded requests exceed 256 items")
        return expanded

    def _match(self, request):
        source = self.catalog.canonical(request["source_lang"])
        target = self.catalog.canonical(request["target_lang"])
        algorithm = request["algorithm"]
        identity = (source or request["source_lang"], target or request["target_lang"], algorithm)
        def unsupported(reason):
            return MatchResult(*identity, status="unsupported", reason=reason)
        if source is None or target is None:
            return unsupported("Unknown source or target language")
        entry = self.catalog._algorithms.get(algorithm)
        if entry is None:
            return unsupported("Unknown algorithm")
        variants = entry["variants"]
        if source not in variants or target not in variants:
            return unsupported("No curated variant for this language pair")
        eligible = tuple(sorted(
            model.model_id for model in self._models.values()
            if model.enabled and source in model.languages and target in model.languages
            and algorithm in model.algorithms))
        requested = request.get("model")
        if requested is not None and requested not in eligible:
            return unsupported("Requested model is unknown, disabled, or lacks declared capabilities")
        if not eligible:
            return unsupported("No enabled model declaration covers both languages and algorithm")
        selected = requested if requested is not None else eligible[0]
        return MatchResult(*identity, status="success", source=variants[source],
                           target=variants[target], semantics=entry["semantics"],
                           eligible_models=eligible, selected_model=selected,
                           provider=self._models[selected].provider)

    def batch(self, requests, workers=None):
        if workers is not None:
            _integer(workers, "workers", MAX_REQUESTS)
        expanded = self._expand(requests)
        started = perf_counter()
        concurrency = self._performance.effective_workers(len(expanded), workers) if expanded else 0
        if expanded:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                results = tuple(executor.map(self._match, expanded))
        else:
            results = ()
        elapsed = perf_counter() - started
        success = sum(result.status == "success" for result in results)
        return BatchReport(results, success, len(results) - success, self.max_workers,
                           concurrency, elapsed, len(results) / elapsed if elapsed > 0 else 0.0)
