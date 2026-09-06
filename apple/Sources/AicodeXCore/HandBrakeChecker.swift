import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// A release of HandBrake, with download metadata and integrity checksum.
public struct HandBrakeRelease: Codable, Equatable, Sendable {
    public let version: String
    public let downloadURL: URL
    public let sha256: String

    public init(version: String, downloadURL: URL, sha256: String) {
        self.version = version
        self.downloadURL = downloadURL
        self.sha256 = sha256
    }
}

/// Swift port of the Python `HandBrakeChecker` utility.
///
/// Network and hashing are injected so the type is deterministic and testable offline.
public struct HandBrakeChecker {
    /// The pinned release mirrored from the Python implementation.
    public static let latestRelease = HandBrakeRelease(
        version: "1.10.2",
        downloadURL: URL(string: "https://github.com/HandBrake/HandBrake/releases/download/1.10.2/HandBrake-1.10.2-x86_64-Win_GUI.exe")!,
        sha256: "ff868bb43c19a4fd8bec8f4b9d83a756f6818cf4b229012715f35eb2416673cd"
    )

    /// Closure that fetches the bytes for a release. Injectable for tests.
    public var fetchData: @Sendable (HandBrakeRelease) async throws -> Data

    public init(fetchData: @escaping @Sendable (HandBrakeRelease) async throws -> Data = HandBrakeChecker.defaultFetch) {
        self.fetchData = fetchData
    }

    /// Human-readable version summary (parity with Python `check_version`).
    public func versionSummary(for release: HandBrakeRelease = HandBrakeChecker.latestRelease) -> String {
        "Latest HandBrake version: \(release.version)\nDownload URL: \(release.downloadURL.absoluteString)"
    }

    /// Metadata dictionary (parity with Python `get_info`).
    public func info(for release: HandBrakeRelease = HandBrakeChecker.latestRelease) -> [String: String] {
        [
            "version": release.version,
            "download_url": release.downloadURL.absoluteString,
            "sha256": release.sha256
        ]
    }

    /// Download and verify a release's SHA-256 checksum. Returns the verified bytes.
    /// - Throws: `HandBrakeError.checksumMismatch` when integrity verification fails.
    @discardableResult
    public func downloadAndVerify(_ release: HandBrakeRelease = HandBrakeChecker.latestRelease) async throws -> Data {
        let data = try await fetchData(release)
        guard Self.sha256Hex(data).caseInsensitiveCompare(release.sha256) == .orderedSame else {
            throw HandBrakeError.checksumMismatch(expected: release.sha256, actual: Self.sha256Hex(data))
        }
        return data
    }

    /// Verify already-downloaded bytes against a release checksum.
    public func verify(data: Data, for release: HandBrakeRelease = HandBrakeChecker.latestRelease) -> Bool {
        Self.sha256Hex(data).caseInsensitiveCompare(release.sha256) == .orderedSame
    }

    // MARK: - Helpers

    public enum HandBrakeError: Error, Equatable {
        case checksumMismatch(expected: String, actual: String)
    }

    /// Lowercase hex SHA-256 for the given bytes (dependency-free, FIPS 180-4).
    public static func sha256Hex(_ data: Data) -> String {
        SHA256Digest.hex(data)
    }

    @Sendable
    public static func defaultFetch(_ release: HandBrakeRelease) async throws -> Data {
        #if canImport(FoundationNetworking)
        // Linux: use a simple synchronous download shim.
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global().async {
                do {
                    let data = try Data(contentsOf: release.downloadURL)
                    continuation.resume(returning: data)
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
        #else
        let (data, _) = try await URLSession.shared.data(from: release.downloadURL)
        return data
        #endif
    }
}
