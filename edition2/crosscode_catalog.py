"""Curated integer-algorithm references, not a general-purpose translator."""

LANGUAGES = {
    "python": ["py", "python3"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "swift": [],
    "rust": ["rs"],
    "go": ["golang"],
    "java": [],
    "c": [],
    "cpp": ["c++", "cplusplus"],
    "csharp": ["c#", "cs"],
    "kotlin": ["kt"],
    "ruby": ["rb"],
}

DOMAIN = (
    "Finite, dense sequences of signed integers only; no booleans, nulls, "
    "fractional/nonfinite values, overloaded equality, or concurrent mutation. "
    "Values and every intermediate sum must be exactly representable in both "
    "languages' chosen numeric types (JS/TS: safe integers; C: long long; "
    "C++/Rust/Go: signed 64-bit; Java/C#/Kotlin: long/Long; Swift: Int). "
    "Lengths and indices must fit both index types; C length must be valid "
    "and nonnegative. Python/Ruby arbitrary precision does not remove the "
    "target's overflow limits. No overflow or coercion equivalence is claimed."
)

ALGORITHMS = {
    "integer_sum": {
        "semantics": DOMAIN + " Add left to right; empty input returns 0.",
        "variants": {
            "python": "def integer_sum(items):\n    total = 0\n    for value in items:\n        total += value\n    return total",
            "javascript": "function integerSum(items) {\n  let total = 0;\n  for (const value of items) total += value;\n  return total;\n}",
            "typescript": "function integerSum(items: number[]): number {\n  let total = 0;\n  for (const value of items) total += value;\n  return total;\n}",
            "swift": "func integerSum(_ items: [Int]) -> Int {\n    var total = 0\n    for value in items { total += value }\n    return total\n}",
            "rust": "fn integer_sum(items: &[i64]) -> i64 {\n    let mut total: i64 = 0;\n    for &value in items { total += value; }\n    total\n}",
            "go": "func integerSum(items []int64) int64 {\n    var total int64\n    for _, value := range items { total += value }\n    return total\n}",
            "java": "class IntegerSum {\n    static long integerSum(long[] items) {\n        long total = 0;\n        for (long value : items) total += value;\n        return total;\n    }\n}",
            "c": "long long integer_sum(const long long *items, int length) {\n    long long total = 0;\n    for (int i = 0; i < length; ++i) total += items[i];\n    return total;\n}",
            "cpp": "#include <cstdint>\n#include <vector>\nstd::int64_t integer_sum(const std::vector<std::int64_t>& items) {\n    std::int64_t total = 0;\n    for (auto value : items) total += value;\n    return total;\n}",
            "csharp": "public static class IntegerSum {\n    public static long Sum(long[] items) {\n        long total = 0;\n        foreach (long value in items) total += value;\n        return total;\n    }\n}",
            "kotlin": "fun integerSum(items: LongArray): Long {\n    var total = 0L\n    for (value in items) total += value\n    return total\n}",
            "ruby": "def integer_sum(items)\n  total = 0\n  items.each { |value| total += value }\n  total\nend",
        },
    },
    "linear_search": {
        "semantics": DOMAIN + (
            " Scan left to right using exact integer equality; return the "
            "zero-based first matching index, or -1 for absent/empty input. "
            "Rust/C++ lengths must fit the signed return index."
        ),
        "variants": {
            "python": "def linear_search(items, target):\n    for index, value in enumerate(items):\n        if value == target:\n            return index\n    return -1",
            "javascript": "function linearSearch(items, target) {\n  for (let i = 0; i < items.length; i++) {\n    if (items[i] === target) return i;\n  }\n  return -1;\n}",
            "typescript": "function linearSearch(items: number[], target: number): number {\n  for (let i = 0; i < items.length; i++) {\n    if (items[i] === target) return i;\n  }\n  return -1;\n}",
            "swift": "func linearSearch(_ items: [Int], _ target: Int) -> Int {\n    for (index, value) in items.enumerated() {\n        if value == target { return index }\n    }\n    return -1\n}",
            "rust": "fn linear_search(items: &[i64], target: i64) -> isize {\n    for (index, &value) in items.iter().enumerate() {\n        if value == target { return index as isize; }\n    }\n    -1\n}",
            "go": "func linearSearch(items []int64, target int64) int {\n    for index, value := range items {\n        if value == target { return index }\n    }\n    return -1\n}",
            "java": "class LinearSearch {\n    static int linearSearch(long[] items, long target) {\n        for (int i = 0; i < items.length; i++) {\n            if (items[i] == target) return i;\n        }\n        return -1;\n    }\n}",
            "c": "int linear_search(const long long *items, int length, long long target) {\n    for (int i = 0; i < length; ++i) {\n        if (items[i] == target) return i;\n    }\n    return -1;\n}",
            "cpp": "#include <cstddef>\n#include <cstdint>\n#include <vector>\nstd::ptrdiff_t linear_search(const std::vector<std::int64_t>& items, std::int64_t target) {\n    for (std::size_t i = 0; i < items.size(); ++i) {\n        if (items[i] == target) return static_cast<std::ptrdiff_t>(i);\n    }\n    return -1;\n}",
            "csharp": "public static class LinearSearch {\n    public static int Find(long[] items, long target) {\n        for (int i = 0; i < items.Length; i++) {\n            if (items[i] == target) return i;\n        }\n        return -1;\n    }\n}",
            "kotlin": "fun linearSearch(items: LongArray, target: Long): Int {\n    for (i in items.indices) {\n        if (items[i] == target) return i\n    }\n    return -1\n}",
            "ruby": "def linear_search(items, target)\n  items.each_with_index { |value, index| return index if value == target }\n  -1\nend",
        },
    },
}
