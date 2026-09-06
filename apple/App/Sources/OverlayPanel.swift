#if os(macOS)
import SwiftUI
import AppKit
import AicodeXCore

/// A borderless, always-on-top, semi-transparent overlay panel for macOS.
/// Mirrors the Python `-topmost` / `-alpha` overlay behaviour.
final class OverlayPanel: NSPanel {
    init(settings: WindowSettings, content: () -> some View) {
        super.init(
            contentRect: NSRect(
                x: settings.xPosition,
                y: settings.yPosition,
                width: settings.width,
                height: settings.height
            ),
            styleMask: [.nonactivatingPanel, .titled, .closable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        isFloatingPanel = true
        level = .floating
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        titleVisibility = .hidden
        titlebarAppearsTransparent = true
        isMovableByWindowBackground = true
        alphaValue = CGFloat(WindowSettings.clampOpacity(settings.opacity))
        isOpaque = false
        backgroundColor = .clear
        contentView = NSHostingView(rootView: content())
    }

    func setOpacity(_ value: Double) {
        alphaValue = CGFloat(WindowSettings.clampOpacity(value))
    }
}
#endif
