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
| App Store Connect App ID | `APPSTORE_APP_ID` | Numeric ID of the app record |

## Product registration

Register the product across Apple's surfaces before the first archive. All of
these live in the developer portal / App Store Connect — **nothing registrable
is committed to this repository**.

1. **App ID (bundle identifier):** Developer portal → Identifiers → register an
   *explicit* App ID matching `AICODEX_BUNDLE_ID` (e.g. `com.aicodex.app`).
   Wildcard App IDs cannot use the capabilities below.
2. **Capabilities:** on the App ID, enable the capabilities the cluster uses —
   **iCloud ▸ Key-Value Storage** (cross-device sync), **App Groups** (shared
   state between watch/phone/iPad/Mac), and **Sign In with Apple** if account
   sign-in ships. Re-create provisioning profiles after changing capabilities.
3. **Per-platform provisioning profiles:** create an App Store profile per
   shipped platform — iOS, macOS, and watchOS (the watch app is bundled in the
   iOS archive). Base64-encode each as `APPLE_PROVISION_PROFILE` for CI.
4. **App Store Connect app record:** create the app (App Store Connect → My
   Apps → +) bound to the registered bundle ID; record its numeric
   **App ID** as `APPSTORE_APP_ID` for upload/notarization calls.
5. **Agreements:** keep the *Paid Apps* agreement, banking/tax forms, and the
   latest license agreements accepted in App Store Connect — uploads fail with
   a compliance error when any agreement lapses.

## Compliance requirements

Shipping on Apple platforms carries standing compliance obligations:

- **Export compliance (encryption):** the app uses only Apple-provided
  cryptography (iCloud sync, TLS), which qualifies for the standard exemption.
  Declare it once by setting **`ITSAppUsesNonExemptEncryption` = `false`** in
  the app `Info.plist` so App Store Connect stops prompting for export
  compliance on every build. If non-exempt crypto is ever added, file an ERN
  and flip the key.
- **Privacy manifest:** include **`PrivacyInfo.xcprivacy`** declaring required
  reason APIs, collected data types, and third-party SDK domains. This is
  mandatory for App Store submission.
- **App privacy details (nutrition labels):** keep the data-collection
  declarations in App Store Connect in sync with the manifest.
- **Age rating & content rights:** complete the age-rating questionnaire and
  content-rights declaration for the app record; review them whenever features
  change.
- **Notarization (macOS):** archive builds distributed outside the App Store
  must be notarized with the App Store Connect API key
  (`APPSTORE_KEY_ID`/`APPSTORE_ISSUER_ID`/`APPSTORE_PRIVATE_KEY`).
- **Beta distribution:** TestFlight builds require *Export Compliance* and
  *Beta App Review* approval before external testers; internal testers only
  need the export declaration above.

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

## Xcode beta & developer versions

CI builds the Swift package across three Xcode channels — **stable** (runner
default), **latest-beta**, and the latest **developer/seed** build (via
[`RobotsAndPencils/xcodes-action`](https://github.com/RobotsAndPencils/xcodes-action)).
To work against a beta or developer Xcode locally:

```bash
# Install the newest beta (or: xcodes install --latest-prerelease)
xcodes install --latest-beta
sudo xcode-select -s /Applications/Xcode-beta.app
xcodebuild -version         # confirm the beta/developer toolchain
```

Credentials are identical across channels — point the same keychain/CI
secrets at whichever Xcode is selected. Note: **App Store uploads still
require a release (non-beta) Xcode**; use the beta/developer channels for
development and pre-release validation only.
