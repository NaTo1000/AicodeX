"""Static validation of the AicodeX build/packaging infrastructure.

Checks the hardened Dockerfile, the buildx bake targets, and the SwiftUI/Xcode
build files — including that no secrets are hardcoded. Standard library only;
runs offline (does not require Docker or Xcode).
"""

from __future__ import annotations

import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = ROOT / "Dockerfile"
BAKE = ROOT / "docker" / "docker-bake.hcl"
ENTRYPOINT = ROOT / "docker" / "entrypoint.sh"
PACKAGE = ROOT / "apple" / "Package.swift"
APP_SWIFT = ROOT / "apple" / "Sources" / "AicodeXApp" / "AicodeXApp.swift"
CONTENT_SWIFT = ROOT / "apple" / "Sources" / "AicodeXApp" / "ContentView.swift"
CORE_DEVICE = ROOT / "apple" / "Sources" / "AicodeXCore" / "ClusterDevice.swift"
CORE_CORE = ROOT / "apple" / "Sources" / "AicodeXCore" / "ClusterCore.swift"
EXPORT_PLIST = ROOT / "apple" / "ExportOptions.plist"
CREDS_MD = ROOT / "apple" / "APPLE_CREDENTIALS.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yaml"

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
        self.assertIn('name: "AicodeXCore"', text)

    def test_swiftui_app_entry(self) -> None:
        text = _read(APP_SWIFT)
        self.assertIn("@main", text)
        self.assertIn("import SwiftUI", text)
        self.assertIn("WindowGroup", text)

    def test_content_view_is_swiftui(self) -> None:
        text = _read(CONTENT_SWIFT)
        self.assertIn("struct ContentView: View", text)
        self.assertIn("var body: some View", text)

    def test_content_view_has_tabs_with_icons(self) -> None:
        text = _read(CONTENT_SWIFT)
        self.assertIn("TabView", text)
        # One .tabItem per app tab, each bound to an AppTab icon.
        self.assertGreaterEqual(text.count(".tabItem"), 4)
        for tab in ("cluster", "devices", "display", "settings"):
            self.assertIn(f"AppTab.{tab}", text)

    def test_content_view_has_hd_3d_display(self) -> None:
        text = _read(CONTENT_SWIFT)
        self.assertIn("DeviceDisplayCard", text)
        self.assertIn("supports3D", text)
        self.assertIn("rotation3DEffect", text)
        self.assertIn("hdLabel", text)

    def test_core_covers_new_devices_and_display(self) -> None:
        text = _read(CORE_DEVICE)
        for case in ("macBook", "macBookPro", "arGlasses"):
            self.assertIn(f"case {case}", text)
        self.assertIn("struct DisplayProfile", text)
        self.assertIn("supports3D", text)
        # Device icons for the new kinds.
        for icon in ("macbook.gen1", "macbook.gen2", "visionpro"):
            self.assertIn(icon, text)

    def test_core_defines_app_tabs(self) -> None:
        text = _read(CORE_CORE)
        self.assertIn("enum AppTab", text)
        for tab in ("cluster", "devices", "display", "settings"):
            self.assertIn(f"case {tab}", text)

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


class XcodeVersionChannelTests(unittest.TestCase):
    """CI selects installed toolchains and propagates required job failures."""

    def setUp(self) -> None:
        self.text = _read(CI_WORKFLOW)

    def test_xcode_matrix_channels(self) -> None:
        self.assertIn("xcode: [latest-stable, latest]", self.text)

    def test_channels_use_supported_action_inputs(self) -> None:
        self.assertIn("maxim-lobanov/setup-xcode@v1.6.0", self.text)
        self.assertIn("xcode-version: ${{ matrix.xcode }}", self.text)
        self.assertNotIn("RobotsAndPencils/xcodes-action", self.text)
        self.assertNotIn("include-prereleases:", self.text)

    def test_checks_run_for_nonstandard_pr_base(self) -> None:
        self.assertRegex(self.text, r"(?m)^  pull_request:\s*\n  workflow_dispatch:")

    def test_package_build_is_not_masked(self) -> None:
        self.assertIn("swift build\n", self.text)
        self.assertIn("swift test\n", self.text)
        self.assertNotIn('|| echo "xcodebuild', self.text)

    @unittest.skipUnless(os.name == "posix", "CI status step uses a POSIX shell")
    def test_status_fails_unless_every_required_job_succeeds(self) -> None:
        status_step = self.text.split("- name: Report job states\n", 1)[1]
        script = status_step.split("        run: |\n", 1)[1]
        variables = ("LINT_RESULT", "TEST_RESULT", "DOCKER_RESULT", "SWIFT_RESULT")
        success = dict.fromkeys(variables, "success")
        cases = [success]
        for variable in variables:
            for result in ("failure", "cancelled", "skipped"):
                cases.append({**success, variable: result})
        for results in cases:
            with self.subTest(results=results):
                completed = subprocess.run(
                    ["sh", "-c", script], env={**os.environ, **results},
                    capture_output=True, text=True, check=False)
                expected = 0 if all(r == "success" for r in results.values()) else 1
                self.assertEqual(completed.returncode, expected, completed.stderr)

    def test_credentials_doc_covers_beta_xcode(self) -> None:
        text = _read(CREDS_MD)
        self.assertIn("Xcode beta & developer versions", text)
        self.assertIn("--latest-beta", text)
        # App Store uploads must still come from a release Xcode.
        self.assertIn("non-beta", text)


class AppleRegistrationComplianceTests(unittest.TestCase):
    """Product registration + compliance requirements must stay documented."""

    def setUp(self) -> None:
        self.text = _read(CREDS_MD)

    def test_product_registration_section(self) -> None:
        self.assertIn("## Product registration", self.text)
        # Explicit App ID + bundle identifier registration.
        self.assertIn("explicit", self.text)
        self.assertIn("AICODEX_BUNDLE_ID", self.text)

    def test_capabilities_registered(self) -> None:
        for capability in ("Key-Value Storage", "App Groups",
                           "Sign In with Apple"):
            self.assertIn(capability, self.text,
                          f"capability '{capability}' must be registered")

    def test_per_platform_provisioning(self) -> None:
        for platform in ("iOS", "macOS", "watchOS"):
            self.assertIn(platform, self.text,
                          f"provisioning profile for {platform} required")

    def test_app_store_connect_record(self) -> None:
        self.assertIn("APPSTORE_APP_ID", self.text)
        self.assertIn("App Store Connect app record", self.text)

    def test_compliance_section(self) -> None:
        self.assertIn("## Compliance requirements", self.text)

    def test_export_compliance_declared(self) -> None:
        # Apple-provided crypto only → non-exempt-encryption key stays false.
        self.assertIn("ITSAppUsesNonExemptEncryption", self.text)
        self.assertIn("`false`", self.text)

    def test_privacy_manifest_required(self) -> None:
        self.assertIn("PrivacyInfo.xcprivacy", self.text)

    def test_notarization_documented(self) -> None:
        self.assertIn("Notarization", self.text)

    def test_export_options_notes_compliance(self) -> None:
        text = _read(EXPORT_PLIST)
        self.assertIn("ITSAppUsesNonExemptEncryption", text)
        self.assertIn("PrivacyInfo.xcprivacy", text)


if __name__ == "__main__":
    unittest.main()
