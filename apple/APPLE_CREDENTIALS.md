# Apple Developer Credentials — Preparation Guide

AicodeX's Apple build requires Apple Developer credentials. **No certificates,
private keys, provisioning profiles, or passwords are ever committed to this
repository.** Provide them at build time via environment variables or CI
secrets.

## Required credentials

| Item | Env var / secret | Notes |
|------|------------------|-------|
| Apple Team ID | `APPLE_TEAM_ID` | 10-char team identifier |
| App Store Connect API Key ID | `APPSTORE_KEY_ID` | For notarization/upload |
| App Store Connect API Issuer ID | `APPSTORE_ISSUER_ID` | UUID from App Store Connect |
| App Store Connect API private key | `APPSTORE_PRIVATE_KEY` | `.p8` contents (secret) |
| Distribution certificate | `APPLE_DIST_CERT_P12` | base64 `.p12` (secret) |
| Distribution certificate password | `APPLE_DIST_CERT_PASSWORD` | secret |
| Provisioning profile | `APPLE_PROVISION_PROFILE` | base64 `.mobileprovision` (secret) |
| Bundle ID | `AICODEX_BUNDLE_ID` | e.g. `com.aicodex.app` |

## Setup steps

1. **Enroll** in the Apple Developer Program and note your **Team ID**.
2. **App Store Connect API key:** App Store Connect → Users and Access → Keys
   → create a key with the *App Manager* role. Download the `.p8` (shown once)
   and record the **Key ID** and **Issuer ID**.
3. **Distribution certificate:** create an *Apple Distribution* certificate in
   the developer portal, export as `.p12`, and base64-encode it for CI.
4. **Provisioning profile:** create an App Store profile for the bundle ID and
   base64-encode it for CI.
5. **Store everything in CI secrets** (never in the repo). `ExportOptions.plist`
   references `$(APPLE_TEAM_ID)` only.

## Local build (after credentials are in your keychain)

```bash
# Build the Swift package / open in Xcode
cd apple
swift build                 # or: open Package.swift in Xcode

# Archive & export (uses your keychain credentials)
xcodebuild -scheme AicodeXApp -archivePath build/AicodeX.xcarchive archive
xcodebuild -exportArchive -archivePath build/AicodeX.xcarchive \
  -exportOptionsPlist ExportOptions.plist -exportPath build/export
```
