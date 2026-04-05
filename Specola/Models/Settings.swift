import Foundation

enum SpecolaSettings {
    private static let defaults = UserDefaults.standard

    private enum Key {
        static let scheduleHour = "scheduleHour"
        static let scheduleMinute = "scheduleMinute"
        static let autoGenerate = "autoGenerate"
        static let language = "language"
        static let hours = "hours"
        static let outputDir = "outputDir"
        static let claudePath = "claudePath"
        static let launchAtLogin = "launchAtLogin"
        static let hasCompletedSetup = "hasCompletedSetup"
    }

    static var scheduleHour: Int {
        get { defaults.object(forKey: Key.scheduleHour) as? Int ?? 7 }
        set { defaults.set(newValue, forKey: Key.scheduleHour) }
    }

    static var scheduleMinute: Int {
        get { defaults.object(forKey: Key.scheduleMinute) as? Int ?? 0 }
        set { defaults.set(newValue, forKey: Key.scheduleMinute) }
    }

    static var autoGenerate: Bool {
        get { defaults.object(forKey: Key.autoGenerate) as? Bool ?? true }
        set { defaults.set(newValue, forKey: Key.autoGenerate) }
    }

    static var language: String {
        get { defaults.string(forKey: Key.language) ?? "it" }
        set { defaults.set(newValue, forKey: Key.language) }
    }

    static var hours: Int {
        get {
            let val = defaults.integer(forKey: Key.hours)
            return val > 0 ? val : 24
        }
        set { defaults.set(newValue, forKey: Key.hours) }
    }

    static var outputDir: String {
        get {
            defaults.string(forKey: Key.outputDir)
                ?? NSString("~/Documents/Specola").expandingTildeInPath
        }
        set { defaults.set(newValue, forKey: Key.outputDir) }
    }

    static var claudePath: String {
        get { defaults.string(forKey: Key.claudePath) ?? "" }
        set { defaults.set(newValue, forKey: Key.claudePath) }
    }

    static var launchAtLogin: Bool {
        get { defaults.bool(forKey: Key.launchAtLogin) }
        set { defaults.set(newValue, forKey: Key.launchAtLogin) }
    }

    static var hasCompletedSetup: Bool {
        get { defaults.bool(forKey: Key.hasCompletedSetup) }
        set { defaults.set(newValue, forKey: Key.hasCompletedSetup) }
    }

    static var supportDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = base.appendingPathComponent("Specola")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    static var opmlPath: URL { supportDir.appendingPathComponent("Feeds.opml") }
    static var profilePath: URL { supportDir.appendingPathComponent("profile.md") }
    static var historyPath: URL { supportDir.appendingPathComponent("history.json") }
    static var engineDir: URL { supportDir.appendingPathComponent("engine") }
    static var pythonPath: URL { engineDir.appendingPathComponent(".venv/bin/python") }

    static var hasOPML: Bool {
        FileManager.default.fileExists(atPath: opmlPath.path)
    }
}
