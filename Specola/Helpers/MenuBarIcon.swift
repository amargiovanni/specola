import AppKit

enum MenuBarIcon {

    /// Normal icon: binoculars with optional badge count.
    static func image(badgeCount: Int) -> NSImage {
        let config = NSImage.SymbolConfiguration(pointSize: 16, weight: .regular)
        guard let baseImage = NSImage(systemSymbolName: "binoculars", accessibilityDescription: "Specola")?
            .withSymbolConfiguration(config) else {
            return NSImage()
        }

        if badgeCount <= 0 {
            baseImage.isTemplate = true
            return baseImage
        }

        let canvasSize = NSSize(width: 24, height: 18)
        let image = NSImage(size: canvasSize, flipped: false) { rect in
            baseImage.draw(
                in: NSRect(x: 0, y: 0, width: 18, height: 18),
                from: .zero,
                operation: .sourceOver,
                fraction: 1.0
            )

            let badgeSize: CGFloat = 10
            let badgeRect = NSRect(
                x: rect.width - badgeSize,
                y: rect.height - badgeSize,
                width: badgeSize,
                height: badgeSize
            )
            NSColor.systemRed.setFill()
            NSBezierPath(ovalIn: badgeRect).fill()

            let text = badgeCount > 9 ? "+" : "\(badgeCount)"
            let attrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.systemFont(ofSize: 7, weight: .bold),
                .foregroundColor: NSColor.white,
            ]
            let textSize = (text as NSString).size(withAttributes: attrs)
            let textPoint = NSPoint(
                x: badgeRect.midX - textSize.width / 2,
                y: badgeRect.midY - textSize.height / 2
            )
            (text as NSString).draw(at: textPoint, withAttributes: attrs)

            return true
        }

        image.isTemplate = false
        return image
    }

    /// Generating icon: cycles between SF Symbols to show activity.
    private static let generatingSymbols = [
        "binoculars",
        "binoculars.circle",
        "binoculars.circle.fill",
        "binoculars.circle",
    ]

    static func generatingImage(frame: Int) -> NSImage {
        let symbolName = generatingSymbols[frame % generatingSymbols.count]
        let config = NSImage.SymbolConfiguration(pointSize: 16, weight: .regular)
        let image = NSImage(systemSymbolName: symbolName, accessibilityDescription: "Generating...")?
            .withSymbolConfiguration(config) ?? NSImage()
        image.isTemplate = true
        return image
    }
}
