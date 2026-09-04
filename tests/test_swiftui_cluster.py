"""Static validation of the AicodeX SwiftUI clustered-workspace sources.

Checks the cross-device cluster model, iCloud connectivity, and CI workflows —
including that all four Apple device kinds are covered and no secrets are
hardcoded. Standard library only; runs offline.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPLE = ROOT / "apple"
PACKAGE = APPLE / "Package.swift"
DEVICE = APPLE / "Sources" / "AicodeXCore" / "ClusterDevice.swift"
CORE = APPLE / "Sources" / "AicodeXCore" / "ClusterCore.swift"
STORE = APPLE / "App" / "ClusterStore.swift"
APP = APPLE / "App" / "AicodeXApp.swift"
CONTENT = APPLE / "App" / "ContentView.swift"
SWIFT_TEST = APPLE / "Tests" / "AicodeXAppTests" / "ClusterCoreTests.swift"
CI = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}"),
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


class ClusterModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.device = _read(DEVICE)

    def test_all_four_device_kinds(self) -> None:
        for kind in ("watch", "phone", "iPad", "mac"):
            self.assertIn(f"case {kind}", self.device)

    def test_each_device_has_function(self) -> None:
        # Each device performs a distinct function in the cluster.
        self.assertIn("var function: String", self.device)

    def test_device_is_codable_for_icloud(self) -> None:
        self.assertIn("Codable", self.device)


class ConnectivityTests(unittest.TestCase):
    def test_icloud_key_value_store(self) -> None:
        store = _read(STORE)
        self.assertIn("NSUbiquitousKeyValueStore", store)
        self.assertIn("ubiquityIdentityToken", store)

    def test_combine_observable(self) -> None:
        store = _read(STORE)
        self.assertIn("ObservableObject", store)
        self.assertIn("@Published", store)

    def test_concurrent_distinct_functions(self) -> None:
        content = _read(CONTENT)
        self.assertIn("ClusterStore", content)
        self.assertIn("ProgressView", content)
        # All four device rows rendered.
        self.assertIn("ClusterDevice.Kind.allCases", content)


class SwiftCoreTests(unittest.TestCase):
    def test_core_is_pure_foundation(self) -> None:
        for path in (DEVICE, CORE):
            text = _read(path)
            self.assertNotIn("import SwiftUI", text)
            self.assertNotIn("import Combine", text)

    def test_swift_test_target_present(self) -> None:
        text = _read(SWIFT_TEST)
        self.assertIn("XCTest", text)
        self.assertIn("ClusterCore", text)

    def test_package_defines_core_target(self) -> None:
        text = _read(PACKAGE)
        self.assertIn('name: "AicodeXCore"', text)
        self.assertIn("watchOS(.v9)", text)


class WorkflowTests(unittest.TestCase):
    def test_ci_workflow_jobs(self) -> None:
        ci = _read(CI)
        for job in ("lint:", "test:", "docker:", "swift:", "status:"):
            self.assertIn(job, ci)
        self.assertIn("if: always()", ci)

    def test_ci_least_privilege(self) -> None:
        ci = _read(CI)
        self.assertIn("contents: read", ci)

    def test_release_workflow_push_and_sign(self) -> None:
        rel = _read(RELEASE)
        self.assertIn("buildx bake", rel)
        self.assertIn("--push", rel)
        self.assertIn("cosign sign", rel)

    def test_release_apple_secrets_from_ci(self) -> None:
        rel = _read(RELEASE)
        self.assertIn("secrets.APPLE_DIST_CERT_P12", rel)
        # No hardcoded Apple secrets.
        for pattern in SECRET_PATTERNS:
            self.assertIsNone(pattern.search(rel))


class NoSecretsTests(unittest.TestCase):
    def test_no_secrets_in_swift_or_workflows(self) -> None:
        for path in (DEVICE, CORE, STORE, APP, CONTENT, SWIFT_TEST, CI, RELEASE):
            text = _read(path)
            for pattern in SECRET_PATTERNS:
                self.assertIsNone(pattern.search(text),
                                  f"possible secret in {path.name}")


if __name__ == "__main__":
    unittest.main()
