"""Static validation of the AicodeX build/packaging infrastructure.

Checks the hardened Dockerfile, the buildx bake targets, and the SwiftUI/Xcode
build files — including that no secrets are hardcoded. Standard library only;
runs offline (does not require Docker or Xcode).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = ROOT / "Dockerfile"
BAKE = ROOT / "docker" / "docker-bake.hcl"
ENTRYPOINT = ROOT / "docker" / "entrypoint.sh"
PACKAGE = ROOT / "apple" / "Package.swift"
APP_SWIFT = ROOT / "apple" / "Sources" / "AicodeXApp" / "AicodeXApp.swift"
CONTENT_SWIFT = ROOT / "apple" / "Sources" / "AicodeXApp" / "ContentView.swift"
EXPORT_PLIST = ROOT / "apple" / "ExportOptions.plist"
CREDS_MD = ROOT / "apple" / "APPLE_CREDENTIALS.md"

# Simple secret-shaped patterns that must never appear in build files.
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]{10,}"),
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


class DockerfileHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _read(DOCKERFILE)

    def test_multistage_build(self) -> None:
        self.assertGreaterEqual(self.text.count("FROM "), 2)
        self.assertIn("AS builder", self.text)
        self.assertIn("AS runtime", self.text)

    def test_runs_as_non_root(self) -> None:
        self.assertRegex(self.text, r"(?m)^USER\s+(?!root\b)\S+")

    def test_uses_slim_base(self) -> None:
        self.assertIn("python:3.11-slim", self.text)

    def test_no_secrets_copied(self) -> None:
        self.assertNotIn(".env", self.text)
        for pattern in SECRET_PATTERNS:
            self.assertIsNone(pattern.search(self.text),
                              f"possible secret in Dockerfile: {pattern.pattern}")

    def test_has_entrypoint(self) -> None:
        self.assertIn("ENTRYPOINT", self.text)


class BakeTargetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _read(BAKE)

    def test_cross_platform_targets(self) -> None:
        for target in ("linux", "windows", "android"):
            self.assertIn(f'target "{target}"', self.text)

    def test_platforms(self) -> None:
        for platform in ("linux/amd64", "linux/arm64", "windows/amd64"):
            self.assertIn(platform, self.text)

    def test_push_group(self) -> None:
        self.assertIn('group "push"', self.text)

    def test_registry_from_env_not_hardcoded(self) -> None:
        self.assertIn('variable "REGISTRY"', self.text)
        # Real image tags must come from the REGISTRY variable, not a hardcoded
        # host. Strip comment lines before checking for hardcoded registries.
        code = "\n".join(line for line in self.text.splitlines()
                         if not line.lstrip().startswith("#"))
        self.assertNotRegex(code, r"tags\s*=\s*\[\s*\"(ghcr|docker|index\.docker)")
        self.assertIn('"${REGISTRY}/aicodex-', code)

    def test_hardening_label(self) -> None:
        self.assertIn("aicodex.hardened", self.text)

    def test_no_secrets(self) -> None:
        for pattern in SECRET_PATTERNS:
            self.assertIsNone(pattern.search(self.text))


class EntrypointTests(unittest.TestCase):
    def test_detects_all_platforms(self) -> None:
        text = _read(ENTRYPOINT)
        for platform in ("android", "linux", "windows", "macos"):
            self.assertIn(platform, text)


class AppleBuildTests(unittest.TestCase):
    def test_package_swift(self) -> None:
        text = _read(PACKAGE)
        self.assertIn("name: \"AicodeX\"", text)
        self.assertIn(".iOS(.v16)", text)
        self.assertIn(".macOS(.v13)", text)
        self.assertIn('name: "AicodeXApp"', text)

    def test_swiftui_app_entry(self) -> None:
        text = _read(APP_SWIFT)
        self.assertIn("@main", text)
        self.assertIn("import SwiftUI", text)
        self.assertIn("WindowGroup", text)

    def test_content_view_is_swiftui(self) -> None:
        text = _read(CONTENT_SWIFT)
        self.assertIn("struct ContentView: View", text)
        self.assertIn("var body: some View", text)

    def test_export_options_plist(self) -> None:
        text = _read(EXPORT_PLIST)
        self.assertIn("<key>method</key>", text)
        self.assertIn("app-store", text)
        self.assertIn("$(APPLE_TEAM_ID)", text)

    def test_credentials_doc_lists_env_vars(self) -> None:
        text = _read(CREDS_MD)
        for var in ("APPLE_TEAM_ID", "APPSTORE_KEY_ID", "APPSTORE_PRIVATE_KEY"):
            self.assertIn(var, text)

    def test_no_real_apple_secrets(self) -> None:
        for path in (EXPORT_PLIST, CREDS_MD, PACKAGE, APP_SWIFT, CONTENT_SWIFT):
            text = _read(path)
            for pattern in SECRET_PATTERNS:
                self.assertIsNone(pattern.search(text),
                                  f"possible secret in {path.name}")


if __name__ == "__main__":
    unittest.main()
