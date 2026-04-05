import SwiftUI

@main
struct SpecolaApp: App {
    var body: some Scene {
        MenuBarExtra("Specola", systemImage: "binoculars") {
            Text("Specola is running")
                .padding()
        }
        .menuBarExtraStyle(.window)
    }
}
