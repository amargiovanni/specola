#!/usr/bin/env swift
import AppKit

let outputDir = CommandLine.arguments.count > 1
    ? CommandLine.arguments[1]
    : "Specola/Assets.xcassets/AppIcon.appiconset"

func generateIcon(size: Int) -> NSImage {
    let s = CGFloat(size)
    let image = NSImage(size: NSSize(width: s, height: s))
    image.lockFocus()

    // Background — navy gradient
    let bg1 = NSColor(red: 0.102, green: 0.102, blue: 0.180, alpha: 1.0) // #1a1a2e
    let bg2 = NSColor(red: 0.059, green: 0.082, blue: 0.165, alpha: 1.0) // #0f152a
    let gradient = NSGradient(starting: bg1, ending: bg2)!
    gradient.draw(in: NSRect(x: 0, y: 0, width: s, height: s), angle: -45)

    // Red accent bar at bottom
    let accentColor = NSColor(red: 0.914, green: 0.271, blue: 0.376, alpha: 1.0) // #e94560
    accentColor.setFill()
    let barHeight = s * 0.035
    let barWidth = s * 0.5
    let barX = (s - barWidth) / 2
    let barY = s * 0.12
    let barRect = NSRect(x: barX, y: barY, width: barWidth, height: barHeight)
    NSBezierPath(roundedRect: barRect, xRadius: barHeight / 2, yRadius: barHeight / 2).fill()

    // Binoculars symbol — white
    let pointSize = s * 0.42
    let config = NSImage.SymbolConfiguration(pointSize: pointSize, weight: .medium)
    if let symbol = NSImage(systemSymbolName: "binoculars.fill", accessibilityDescription: nil)?
        .withSymbolConfiguration(config) {

        let symSize = symbol.size
        let symRect = NSRect(origin: .zero, size: symSize)

        // Create white-tinted version
        let tinted = NSImage(size: symSize)
        tinted.lockFocus()
        symbol.draw(in: symRect)
        NSColor.white.setFill()
        symRect.fill(using: .sourceAtop)
        tinted.unlockFocus()

        let x = (s - symSize.width) / 2
        let y = (s - symSize.height) / 2 + s * 0.04
        tinted.draw(
            in: NSRect(x: x, y: y, width: symSize.width, height: symSize.height),
            from: .zero, operation: .sourceOver, fraction: 0.95
        )
    }

    image.unlockFocus()
    return image
}

func savePNG(_ image: NSImage, to path: String, pixelSize: Int) {
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: pixelSize, pixelsHigh: pixelSize,
        bitsPerSample: 8, samplesPerPixel: 4,
        hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0, bitsPerPixel: 0
    )!
    rep.size = NSSize(width: pixelSize, height: pixelSize)

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    image.draw(in: NSRect(x: 0, y: 0, width: pixelSize, height: pixelSize))
    NSGraphicsContext.restoreGraphicsState()

    let data = rep.representation(using: .png, properties: [:])!
    try! data.write(to: URL(fileURLWithPath: path))
}

// Generate all required sizes
let sizes: [(name: String, pixels: Int, scale: String, size: String)] = [
    ("icon_16x16",      16,  "1x", "16x16"),
    ("icon_16x16@2x",   32,  "2x", "16x16"),
    ("icon_32x32",      32,  "1x", "32x32"),
    ("icon_32x32@2x",   64,  "2x", "32x32"),
    ("icon_128x128",    128, "1x", "128x128"),
    ("icon_128x128@2x", 256, "2x", "128x128"),
    ("icon_256x256",    256, "1x", "256x256"),
    ("icon_256x256@2x", 512, "2x", "256x256"),
    ("icon_512x512",    512, "1x", "512x512"),
    ("icon_512x512@2x", 1024,"2x", "512x512"),
]

// Create output directory
let fm = FileManager.default
try? fm.createDirectory(atPath: outputDir, withIntermediateDirectories: true)

// Generate icon at a large size and scale down
let masterIcon = generateIcon(size: 1024)

for entry in sizes {
    let path = "\(outputDir)/\(entry.name).png"
    savePNG(masterIcon, to: path, pixelSize: entry.pixels)
    print("Generated \(entry.name).png (\(entry.pixels)px)")
}

// Write Contents.json
let images = sizes.map { entry in
    """
        {
          "filename" : "\(entry.name).png",
          "idiom" : "mac",
          "scale" : "\(entry.scale)",
          "size" : "\(entry.size)"
        }
    """
}.joined(separator: ",\n")

let contentsJSON = """
{
  "images" : [
\(images)
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}
"""

try! contentsJSON.write(toFile: "\(outputDir)/Contents.json", atomically: true, encoding: .utf8)
print("Generated Contents.json")
print("Done!")
