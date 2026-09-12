import Foundation

/// A world programming/markup language with variants and formats.
public struct CodeLanguage: Codable, Equatable, Identifiable {
    public var id: String { name }
    public var name: String
    public var variants: [String]
    public var formats: [String]
    public var extensions: [String]

    public init(name: String, variants: [String] = [], formats: [String] = [], extensions: [String] = []) {
        self.name = name
        self.variants = variants
        self.formats = formats
        self.extensions = extensions.map { $0.lowercased() }
    }
}

/// Lookup over known languages, their variants, and formats.
public struct LanguageCatalog {
    private var languages: [String: CodeLanguage] = [:]

    public init(languages: [CodeLanguage]? = nil) {
        for lang in languages ?? LanguageCatalog.defaultLanguages {
            self.languages[lang.name.lowercased()] = lang
        }
    }

    public var names: [String] { languages.keys.sorted() }

    public func get(_ name: String) -> CodeLanguage? { languages[name.lowercased()] }

    public func byExtension(_ ext: String) -> CodeLanguage? {
        let e = ext.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "."))
        return languages.values.first { $0.extensions.contains(e) }
    }

    public func variants(_ name: String) -> [String] { get(name)?.variants ?? [] }
    public func formats(_ name: String) -> [String] { get(name)?.formats ?? [] }

    public static let defaultLanguages: [CodeLanguage] = [
        CodeLanguage(name: "python", variants: ["cpython", "pypy", "micropython"], formats: ["source", "json"], extensions: ["py"]),
        CodeLanguage(name: "javascript", variants: ["node", "es2023", "typescript"], formats: ["source", "json", "html"], extensions: ["js", "mjs", "jsx"]),
        CodeLanguage(name: "typescript", variants: ["es2023", "deno"], formats: ["source", "json"], extensions: ["ts", "tsx"]),
        CodeLanguage(name: "swift", variants: ["swiftui", "uikit", "swift5", "swift6"], formats: ["source"], extensions: ["swift"]),
        CodeLanguage(name: "rust", variants: ["edition2021", "nightly"], formats: ["source", "toml"], extensions: ["rs"]),
        CodeLanguage(name: "go", variants: ["go1.x"], formats: ["source"], extensions: ["go"]),
        CodeLanguage(name: "java", variants: ["se", "android"], formats: ["source", "xml"], extensions: ["java"]),
        CodeLanguage(name: "kotlin", variants: ["jvm", "android", "multiplatform"], formats: ["source", "xml"], extensions: ["kt", "kts"]),
        CodeLanguage(name: "c", variants: ["c11", "c17"], formats: ["source"], extensions: ["c", "h"]),
        CodeLanguage(name: "cpp", variants: ["c++17", "c++20", "c++23"], formats: ["source"], extensions: ["cpp", "cc", "hpp", "hh"]),
        CodeLanguage(name: "csharp", variants: ["dotnet", "unity"], formats: ["source", "xml", "json"], extensions: ["cs"]),
        CodeLanguage(name: "ruby", variants: ["rails"], formats: ["source", "yaml"], extensions: ["rb"]),
        CodeLanguage(name: "php", variants: ["php8"], formats: ["source", "html"], extensions: ["php"]),
        CodeLanguage(name: "r", variants: ["tidyverse"], formats: ["source", "csv"], extensions: ["r"]),
        CodeLanguage(name: "scala", variants: ["scala3"], formats: ["source"], extensions: ["scala", "sc"]),
        CodeLanguage(name: "haskell", variants: ["ghc"], formats: ["source"], extensions: ["hs"]),
        CodeLanguage(name: "lua", variants: ["luajit"], formats: ["source"], extensions: ["lua"]),
        CodeLanguage(name: "perl", variants: ["perl5"], formats: ["source"], extensions: ["pl", "pm"]),
        CodeLanguage(name: "sql", variants: ["postgres", "mysql", "sqlite", "tsql"], formats: ["sql"], extensions: ["sql"]),
        CodeLanguage(name: "shell", variants: ["bash", "zsh", "posix", "powershell"], formats: ["shell"], extensions: ["sh", "bash", "zsh", "ps1"]),
        CodeLanguage(name: "html", variants: ["html5"], formats: ["html"], extensions: ["html", "htm"]),
        CodeLanguage(name: "css", variants: ["css3", "scss", "sass"], formats: ["source"], extensions: ["css", "scss", "sass"]),
        CodeLanguage(name: "dart", variants: ["flutter"], formats: ["source", "yaml"], extensions: ["dart"]),
        CodeLanguage(name: "objectivec", variants: ["objc2"], formats: ["source"], extensions: ["m", "mm"]),
        CodeLanguage(name: "julia", variants: ["julia1"], formats: ["source"], extensions: ["jl"]),
    ]
}

/// The result of predicting a snippet's language/algorithm/format.
public struct CodePrediction: Equatable {
    public var language: String
    public var languageConfidence: Double
    public var variant: String
    public var format: String
    public var formatConfidence: Double
    public var algorithm: String
    public var algorithmConfidence: Double
    public var rationale: String
    public var candidates: [(language: String, score: Double)]

    public static func == (lhs: CodePrediction, rhs: CodePrediction) -> Bool {
        lhs.language == rhs.language && lhs.variant == rhs.variant && lhs.format == rhs.format
            && lhs.algorithm == rhs.algorithm
    }
}

/// HiAi heuristic predictor (language/algorithm/format) over a language catalog.
///
/// Pure Foundation so it compiles and tests on Linux. Mirrors the Python
/// ``CodePredictor``: keyword/construct signatures + extension hints + a style
/// nudge, with confidence and a human-readable rationale.
public struct CodePredictor {
    public let catalog: LanguageCatalog

    public init(catalog: LanguageCatalog = LanguageCatalog()) {
        self.catalog = catalog
    }

    private static let languageSignatures: [String: [String]] = [
        "python": ["def ", "import ", "print(", "self", "elif", "lambda ", ":", "none", "true", "__init__"],
        "javascript": ["function ", "const ", "let ", "var ", "=>", "console.log", "require(", "module.exports"],
        "typescript": ["interface ", ": string", ": number", "const ", "implements ", "enum ", "readonly "],
        "swift": ["func ", "let ", "var ", "guard ", "struct ", "import foundation", "@state", "some view"],
        "rust": ["fn ", "let mut", "impl ", "match ", "println!", "-> ", "&str", "pub "],
        "go": ["func ", "package ", "import (", ":=", "fmt.", "go func", "chan "],
        "java": ["public class", "public static void main", "system.out.println", "private ", "new ", ";"],
        "kotlin": ["fun ", "val ", "var ", "data class", "println(", ": string"],
        "c": ["#include", "int main", "printf(", "malloc(", "->", ";"],
        "cpp": ["#include <", "std::", "cout", "int main", "template <", "::", "nullptr"],
        "csharp": ["using system", "public class", "console.writeline", "namespace ", "var ", "{ get;"],
        "ruby": ["def ", "end", "puts ", "require ", "@", "do |"],
        "php": ["<?php", "$", "echo ", "function ", "->"],
        "r": ["<-", "library(", "data.frame", "ggplot", "function("],
        "scala": ["def ", "val ", "var ", "object ", "extends ", "case class"],
        "haskell": ["::", "->", "where", "let ", "data ", "module "],
        "lua": ["function ", "local ", "end", "then", "require "],
        "perl": ["use strict", "my $", "sub ", "print ", "@_"],
        "sql": ["select ", "from ", "where ", "insert into", "create table", "join "],
        "shell": ["#!/bin", "echo ", "$", "fi", "then", "#!/usr/bin/env", "function "],
        "html": ["<html", "<div", "<!doctype", "<script", "<body", "<span", "<p>", "<head"],
        "css": ["color:", "margin:", "padding:", "@media", "font-size", "background:", "display:", "#"],
        "dart": ["void main", "widget ", "build(", "import 'package:", "final "],
        "objectivec": ["#import", "@interface", "@implementation", "nslog", "@end"],
        "julia": ["function ", "end", "println(", "::", "using "],
    ]

    private static let formatSignatures: [String: [String]] = [
        "json": ["json.", "json.loads", "json.dumps", "json.load(", "json.dump(", "tojson", "jsonencoder", "stringify(", "json.parse"],
        "yaml": ["yaml.", "yaml.safe_load", "yaml.load", "safe_load(", ".yml", ".yaml"],
        "toml": ["toml.", "toml.load", "toml.parse", "# toml", "pyproject.toml"],
        "xml": ["<?xml", "etree", "elementtree", "xml.dom", "xml.sax", "tostring(", "<rss", "lxml"],
        "csv": ["csv.", "csv.reader", "csv.writer", "dictreader", "dictwriter", "read_csv"],
        "markdown": ["## ", "- [", "](", "```", "__bold__", "**bold**"],
        "html": ["<html", "<div", "<!doctype", "<body", "<script", "beautifulsoup"],
        "sql": ["select ", "insert into", "create table", "execute(", "alter table", "drop table"],
        "shell": ["#!/bin", "#!/usr/bin/env", "echo ", "subprocess"],
    ]

    private static let algorithmSignatures: [String: [String]] = [
        "sorting": ["sort(", "sorted(", "quicksort", "mergesort", "bubble", "order by", "heapify"],
        "searching": ["binary_search", "indexof", "find(", "search(", "contains(", "lookup"],
        "dynamic_programming": ["dp[", "memo", "cache", "fibonacci", "knapsack", "lcs"],
        "graph": ["dfs", "bfs", "graph", "node", "edge", "adjacency", "dijkstra", "topological"],
        "recursion": ["recursion", "recursive", "return ", "base case"],
        "parsing": ["parse(", "tokenize", "lexer", "ast", "regex", "split("],
        "concurrency": ["thread", "async", "await", "goroutine", "lock", "mutex", "parallel", "spawn"],
        "io": ["open(", "read(", "write(", "file", "socket", "request", "input"],
        "math": ["sqrt", "pow(", "factorial", "gcd", "prime", "mod"],
        "ml": ["model", "train(", "predict(", "tensor", "epoch", "loss", "neural"],
    ]

    private func score(_ code: String, _ signatures: [String: [String]]) -> [String: Double] {
        let lowered = code.lowercased()
        var scores: [String: Double] = [:]
        for (key, sigs) in signatures {
            let hits = sigs.reduce(0) { $0 + (lowered.contains($1) ? 1 : 0) }
            scores[key] = sigs.isEmpty ? 0.0 : Double(hits) / Double(sigs.count)
        }
        return scores
    }

    private func top(_ scores: [String: Double]) -> (String, Double, [(String, Double)]) {
        let ranked = scores.sorted { $0.value > $1.value }
        guard let first = ranked.first, first.value > 0 else { return ("unknown", 0.0, Array(ranked.prefix(3))) }
        let runner = ranked.count > 1 ? ranked[1].value : 0.0
        let margin = max(0.0, first.value - runner)
        let confidence = min(1.0, first.value * 0.8 + margin * 0.2)
        return (first.key, confidence, Array(ranked.prefix(3)))
    }

    private func pickVariant(_ language: String, _ code: String) -> String {
        let variants = catalog.variants(language)
        guard !variants.isEmpty else { return "standard" }
        let lowered = code.lowercased()
        for v in variants where lowered.contains(v.lowercased()) { return v }
        if language == "swift", lowered.contains("swiftui") || lowered.contains("some view") { return "swiftui" }
        if language == "python", lowered.contains("asyncio") { return "cpython" }
        return variants[0]
    }

    public func predict(_ code: String, filename: String? = nil) -> CodePrediction {
        guard !code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return CodePrediction(language: "unknown", languageConfidence: 0, variant: "standard", format: "text", formatConfidence: 0, algorithm: "unknown", algorithmConfidence: 0, rationale: "Empty submission — nothing to analyse.", candidates: [])
        }

        var langScores = score(code, CodePredictor.languageSignatures)
        var extLang: CodeLanguage? = nil
        if let filename = filename, let dot = filename.lastIndex(of: ".") {
            let ext = String(filename[filename.index(after: dot)...])
            extLang = catalog.byExtension(ext)
            if let lang = extLang {
                langScores[lang.name, default: 0] += 0.15
            }
        }
        // Style nudge: same-line braces lean C-family.
        if code.contains("{") {
            for family in ["c", "cpp", "csharp", "java", "javascript", "typescript", "go", "rust"] {
                langScores[family, default: 0] += 0.03
            }
        }

        let (language, langConf, candidates) = top(langScores)
        let (format, fmtConf, _) = top(score(code, CodePredictor.formatSignatures))
        let (algorithm, algoConf, _) = top(score(code, CodePredictor.algorithmSignatures))
        let variant = pickVariant(language, code)

        let rationale: String
        if let ext = extLang, language == ext.name {
            rationale = "Extension and construct signatures agree on '\(language)'."
        } else if language != "unknown" {
            rationale = "Construct signatures point to '\(language)'; variant '\(variant)' inferred from style/usage."
        } else {
            rationale = "No strong language signature matched; providing a filename hint would help."
        }

        return CodePrediction(
            language: language, languageConfidence: langConf, variant: variant,
            format: format, formatConfidence: fmtConf,
            algorithm: algorithm, algorithmConfidence: algoConf,
            rationale: rationale,
            candidates: candidates.map { ($0.0, $0.1) }
        )
    }
}
