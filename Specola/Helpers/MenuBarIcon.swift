import AppKit

enum MenuBarIcon {

    /// Normal icon: binoculars with optional badge count and sparkline.
    /// - Parameters:
    ///   - badgeCount: Unread count (0 = no badge)
    ///   - sparklineData: Item counts for last 7 entries (newest last). Empty = no sparkline.
    static func image(badgeCount: Int, sparklineData: [Int] = []) -> NSImage {
        let config = NSImage.SymbolConfiguration(pointSize: 16, weight: .regular)
        guard let baseImage = NSImage(systemSymbolName: "binoculars", accessibilityDescription: "Specola")?
            .withSymbolConfiguration(config) else {
            return NSImage()
        }

        let hasSparkline = sparklineData.count >= 2
        let hasBadge = badgeCount > 0

        if !hasBadge && !hasSparkline {
            baseImage.isTemplate = true
            return baseImage
        }

        let sparklineHeight: CGFloat = hasSparkline ? 5 : 0
        let canvasSize = NSSize(width: 24, height: 18 + sparklineHeight)
        let image = NSImage(size: canvasSize, flipped: false) { rect in
            // Draw binoculars
            baseImage.draw(
                in: NSRect(x: 0, y: sparklineHeight, width: 18, height: 18),
                from: .zero,
                operation: .sourceOver,
                fraction: 1.0
            )

            // Badge
            if hasBadge {
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
            }

            // Sparkline (tiny bar chart at the bottom)
            if hasSparkline {
                let data = Array(sparklineData.suffix(7))
                let maxVal = CGFloat(data.max() ?? 1)
                let barWidth: CGFloat = 2
                let gap: CGFloat = 1
                let totalWidth = CGFloat(data.count) * barWidth + CGFloat(data.count - 1) * gap
                let startX = (18 - totalWidth) / 2  // Center under binoculars

                for (i, val) in data.enumerated() {
                    let normalized = maxVal > 0 ? CGFloat(val) / maxVal : 0
                    let barHeight = max(1, normalized * (sparklineHeight - 1))
                    let x = startX + CGFloat(i) * (barWidth + gap)
                    let barRect = NSRect(x: x, y: 0, width: barWidth, height: barHeight)

                    let isLast = i == data.count - 1
                    (isLast ? NSColor.systemRed : NSColor.secondaryLabelColor).setFill()
                    NSBezierPath(roundedRect: barRect, xRadius: 0.5, yRadius: 0.5).fill()
                }
            }

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
