import SwiftUI

@main
struct SpecolaApp: App {
    @State private var appState: AppState
    @State private var scheduler: SchedulerService
    @State private var animationFrame: Int = 0
    @State private var animationTimer: Timer?

    var body: some Scene {
        MenuBarExtra {
            MenuBarView()
                .environment(appState)
                .modifier(FirstLaunchModifier())
        } label: {
            if appState.isGenerating {
                Image(nsImage: MenuBarIcon.generatingImage(frame: animationFrame))
            } else {
                Image(nsImage: MenuBarIcon.image(badgeCount: appState.unreadCount))
            }
        }
        .menuBarExtraStyle(.window)
        .onChange(of: appState.isGenerating) { _, isGenerating in
            if isGenerating {
                startIconAnimation()
            } else {
                stopIconAnimation()
            }
        }

        Settings {
            SettingsView()
                .environment(appState)
        }
    }

    init() {
        // Setup notifications with delegate for foreground display
        NotificationService.setup()

        let state = AppState()
        state.loadHistory()
        _appState = State(initialValue: state)

        Task {
            await setupEngineIfNeeded()
        }

        let schedulerInstance = SchedulerService()
        schedulerInstance.start {
            guard !state.isGenerating, !state.hasGeneratedToday else { return }
            guard SpecolaSettings.autoGenerate else { return }
            triggerGeneration(appState: state)
        }
        _scheduler = State(initialValue: schedulerInstance)
    }

    private func startIconAnimation() {
        animationTimer?.invalidate()
        animationFrame = 0
        let timer = Timer.scheduledTimer(withTimeInterval: 0.4, repeats: true) { _ in
            Task { @MainActor [self] in
                self.animationFrame = (self.animationFrame + 1) % 3
            }
        }
        animationTimer = timer
    }

    private func stopIconAnimation() {
        animationTimer?.invalidate()
        animationTimer = nil
        animationFrame = 0
    }
}

private struct FirstLaunchModifier: ViewModifier {
    @Environment(\.openSettings) private var openSettings

    func body(content: Content) -> some View {
        content
            .task {
                if !SpecolaSettings.hasCompletedSetup {
                    openSettings()
                    SpecolaSettings.hasCompletedSetup = true
                }
            }
    }
}

private func setupEngineIfNeeded() async {
    let engineDir = SpecolaSettings.engineDir
    let venvPath = engineDir.appendingPathComponent(".venv/bin/python")

    guard !FileManager.default.fileExists(atPath: venvPath.path) else { return }

    guard let bundledEngine = Bundle.main.resourceURL?.appendingPathComponent("engine") else { return }
    guard FileManager.default.fileExists(atPath: bundledEngine.path) else { return }

    try? FileManager.default.removeItem(at: engineDir)
    try? FileManager.default.copyItem(at: bundledEngine, to: engineDir)

    let setupScript = engineDir.appendingPathComponent("setup_engine.sh")
    guard FileManager.default.fileExists(atPath: setupScript.path) else { return }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/bin/bash")
    process.arguments = [setupScript.path]
    process.currentDirectoryURL = engineDir
    try? process.run()
    process.waitUntilExit()
}

private func triggerGeneration(appState: AppState) {
    guard appState.canGenerate else { return }

    appState.isGenerating = true
    appState.lastError = nil

    Task {
        do {
            let result = try await EngineService.run()
            let dateId = {
                let fmt = DateFormatter()
                fmt.dateFormat = "yyyy-MM-dd_HHmm"
                return fmt.string(from: Date())
            }()

            let entry = SpecolaEntry(
                id: dateId,
                date: Date(),
                path: result.outputPath ?? "",
                htmlPath: result.htmlPath ?? "",
                feedCount: result.feedCount,
                itemCount: result.itemCount,
                highlights: result.highlights,
                read: false
            )

            await MainActor.run {
                appState.addEntry(entry)
                appState.isGenerating = false
            }

            if let path = result.outputPath {
                NotificationService.notifySuccess(
                    date: dateId,
                    itemCount: result.itemCount,
                    docxPath: path
                )
            }
        } catch {
            await MainActor.run {
                appState.isGenerating = false
                appState.lastError = error.localizedDescription
            }
            NotificationService.notifyError(message: error.localizedDescription)
        }
    }
}
