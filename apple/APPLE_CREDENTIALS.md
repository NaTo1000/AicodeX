# Apple Credentials & App Store Release

AicodeX's Apple build/sign/release pipeline is driven **entirely by CI secrets**.
No certificates, private keys, provisioning profiles, or App Store Connect API keys
are ever committed to this repository.

## Required GitHub Actions secrets

| Secret | Purpose |
|--------|---------|
| `APPLE_TEAM_ID` | Apple Developer Team ID |
| `APPLE_BUNDLE_ID` | App bundle identifier (e.g. `com.aicodex.app`) |
| `ASC_KEY_ID` | App Store Connect API key ID |
| `ASC_ISSUER_ID` | App Store Connect API issuer ID |
| `ASC_PRIVATE_KEY` | App Store Connect API private key (`.p8` contents) |
| `MACOS_CERTIFICATE_P12` | Base64-encoded distribution certificate (`.p12`) |
| `MACOS_CERTIFICATE_PASSWORD` | Password for the `.p12` |
| `MACOS_PROVISION_PROFILE` | Base64-encoded provisioning profile (if used) |

## Release flow

1. CI builds the Swift package (`swift build`, `swift test`) on macOS.
2. The Xcode app target (`apple/App`) is archived with `xcodebuild -archivePath`.
3. The archive is exported/uploaded with `ExportOptions.plist` (`method: app-store`,
   `destination: upload`) using the App Store Connect API key from secrets.
4. Credentials are injected at runtime from secrets and never persisted to disk in the repo.

## Local development

Open `apple/Package.swift` in Xcode for the core library, or create an Xcode project
that includes the `apple/App` sources and asset catalog, links `AicodeXCore`, and
points at `apple/App/Resources/Info.plist` + `AicodeX.entitlements`.
