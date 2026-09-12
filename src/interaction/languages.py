"""World languages, code variants, and file/serialisation formats catalog.

A small, dependency-free catalog the prediction engine uses to recognise what a
piece of submitted code is (language + variant) and which formats are available
for it. Kept intentionally declarative so new languages/variants/formats can be
added as data.
"""

from __future__ import annotations

from typing import Dict, List, Optional


class CodeLanguage:
    """A world programming/markup language with variants and formats."""

    def __init__(
        self,
        name: str,
        variants: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        extensions: Optional[List[str]] = None,
    ) -> None:
        self.name = str(name)
        self.variants = list(variants or [])
        self.formats = list(formats or [])
        self.extensions = [e.lower() for e in (extensions or [])]

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "variants": list(self.variants),
            "formats": self.formats,
            "extensions": list(self.extensions),
        }


#: The available serialisation / interchange formats referenced across the catalog.
FORMATS: List[str] = [
    "json", "yaml", "toml", "xml", "csv", "markdown", "html", "sql", "shell",
    "source", "text",
]


def _default_languages() -> List[CodeLanguage]:
    return [
        CodeLanguage("python", variants=["cpython", "pypy", "micropython"], formats=["source", "json"], extensions=["py"]),
        CodeLanguage("javascript", variants=["node", "es2023", "typescript"], formats=["source", "json", "html"], extensions=["js", "mjs", "jsx"]),
        CodeLanguage("typescript", variants=["es2023", "deno"], formats=["source", "json"], extensions=["ts", "tsx"]),
        CodeLanguage("swift", variants=["swiftui", "uikit", "swift5", "swift6"], formats=["source"], extensions=["swift"]),
        CodeLanguage("rust", variants=["edition2021", "nightly"], formats=["source", "toml"], extensions=["rs"]),
        CodeLanguage("go", variants=["go1.x"], formats=["source"], extensions=["go"]),
        CodeLanguage("java", variants=["se", "android"], formats=["source", "xml"], extensions=["java"]),
        CodeLanguage("kotlin", variants=["jvm", "android", "multiplatform"], formats=["source", "xml"], extensions=["kt", "kts"]),
        CodeLanguage("c", variants=["c11", "c17"], formats=["source"], extensions=["c", "h"]),
        CodeLanguage("cpp", variants=["c++17", "c++20", "c++23"], formats=["source"], extensions=["cpp", "cc", "hpp", "hh"]),
        CodeLanguage("csharp", variants=["dotnet", "unity"], formats=["source", "xml", "json"], extensions=["cs"]),
        CodeLanguage("ruby", variants=["rails"], formats=["source", "yaml"], extensions=["rb"]),
        CodeLanguage("php", variants=["php8"], formats=["source", "html"], extensions=["php"]),
        CodeLanguage("r", variants=["tidyverse"], formats=["source", "csv"], extensions=["r"]),
        CodeLanguage("scala", variants=["scala3"], formats=["source"], extensions=["scala", "sc"]),
        CodeLanguage("haskell", variants=["ghc"], formats=["source"], extensions=["hs"]),
        CodeLanguage("lua", variants=["luajit"], formats=["source"], extensions=["lua"]),
        CodeLanguage("perl", variants=["perl5"], formats=["source"], extensions=["pl", "pm"]),
        CodeLanguage("sql", variants=["postgres", "mysql", "sqlite", "tsql"], formats=["sql"], extensions=["sql"]),
        CodeLanguage("shell", variants=["bash", "zsh", "posix", "powershell"], formats=["shell"], extensions=["sh", "bash", "zsh", "ps1"]),
        CodeLanguage("html", variants=["html5"], formats=["html"], extensions=["html", "htm"]),
        CodeLanguage("css", variants=["css3", "scss", "sass"], formats=["source"], extensions=["css", "scss", "sass"]),
        CodeLanguage("dart", variants=["flutter"], formats=["source", "yaml"], extensions=["dart"]),
        CodeLanguage("objectivec", variants=["objc2"], formats=["source"], extensions=["m", "mm"]),
        CodeLanguage("julia", variants=["julia1"], formats=["source"], extensions=["jl"]),
    ]


class LanguageCatalog:
    """Lookup over the known languages, their variants, and formats."""

    def __init__(self, languages: Optional[List[CodeLanguage]] = None) -> None:
        self._languages: Dict[str, CodeLanguage] = {}
        for lang in languages or _default_languages():
            self._languages[lang.name.lower()] = lang

    def names(self) -> List[str]:
        return sorted(self._languages.keys())

    def get(self, name: str) -> Optional[CodeLanguage]:
        return self._languages.get(str(name).lower())

    def by_extension(self, ext: str) -> Optional[CodeLanguage]:
        e = str(ext).lower().lstrip(".")
        for lang in self._languages.values():
            if e in lang.extensions:
                return lang
        return None

    def variants(self, name: str) -> List[str]:
        lang = self.get(name)
        return list(lang.variants) if lang else []

    def formats(self, name: str) -> List[str]:
        lang = self.get(name)
        return list(lang.formats) if lang else []

    def as_dict(self) -> Dict[str, object]:
        return {name: lang.as_dict() for name, lang in sorted(self._languages.items())}
