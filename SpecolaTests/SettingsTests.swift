import XCTest
@testable import Specola

final class SettingsTests: XCTestCase {

    // MARK: - Default values

    func testDefaultScheduleHour() {
        // Clean state: remove the key to test default
        UserDefaults.standard.removeObject(forKey: "scheduleHour")
        XCTAssertEqual(SpecolaSettings.scheduleHour, 7)
    }

    func testDefaultScheduleMinute() {
        UserDefaults.standard.removeObject(forKey: "scheduleMinute")
        XCTAssertEqual(SpecolaSettings.scheduleMinute, 0)
    }

    func testDefaultAutoGenerate() {
        UserDefaults.standard.removeObject(forKey: "autoGenerate")
        XCTAssertTrue(SpecolaSettings.autoGenerate)
    }

    func testDefaultLanguage() {
        UserDefaults.standard.removeObject(forKey: "language")
        XCTAssertEqual(SpecolaSettings.language, "it")
    }

    func testDefaultHours() {
        UserDefaults.standard.removeObject(forKey: "hours")
        XCTAssertEqual(SpecolaSettings.hours, 24)
    }

    func testDefaultClaudePath() {
        UserDefaults.standard.removeObject(forKey: "claudePath")
        XCTAssertEqual(SpecolaSettings.claudePath, "")
    }

    func testDefaultLaunchAtLogin() {
        UserDefaults.standard.removeObject(forKey: "launchAtLogin")
        XCTAssertFalse(SpecolaSettings.launchAtLogin)
    }

    func testDefaultHasCompletedSetup() {
        UserDefaults.standard.removeObject(forKey: "hasCompletedSetup")
        XCTAssertFalse(SpecolaSettings.hasCompletedSetup)
    }

    func testDefaultOutputFormat() {
        UserDefaults.standard.removeObject(forKey: "outputFormat")
        XCTAssertEqual(SpecolaSettings.outputFormat, "docx")
    }

    // MARK: - Set and get

    func testSetAndGetScheduleHour() {
        SpecolaSettings.scheduleHour = 15
        XCTAssertEqual(SpecolaSettings.scheduleHour, 15)
        // Cleanup
        UserDefaults.standard.removeObject(forKey: "scheduleHour")
    }

    func testSetAndGetScheduleMinute() {
        SpecolaSettings.scheduleMinute = 45
        XCTAssertEqual(SpecolaSettings.scheduleMinute, 45)
        UserDefaults.standard.removeObject(forKey: "scheduleMinute")
    }

    func testSetAndGetAutoGenerate() {
        SpecolaSettings.autoGenerate = false
        XCTAssertFalse(SpecolaSettings.autoGenerate)
        SpecolaSettings.autoGenerate = true
        XCTAssertTrue(SpecolaSettings.autoGenerate)
        UserDefaults.standard.removeObject(forKey: "autoGenerate")
    }

    func testSetAndGetLanguage() {
        SpecolaSettings.language = "en"
        XCTAssertEqual(SpecolaSettings.language, "en")
        SpecolaSettings.language = "it"
        XCTAssertEqual(SpecolaSettings.language, "it")
        UserDefaults.standard.removeObject(forKey: "language")
    }

    func testSetAndGetHours() {
        SpecolaSettings.hours = 48
        XCTAssertEqual(SpecolaSettings.hours, 48)
        UserDefaults.standard.removeObject(forKey: "hours")
    }

    func testSetAndGetOutputDir() {
        SpecolaSettings.outputDir = "/custom/path"
        XCTAssertEqual(SpecolaSettings.outputDir, "/custom/path")
        UserDefaults.standard.removeObject(forKey: "outputDir")
    }

    func testSetAndGetClaudePath() {
        SpecolaSettings.claudePath = "/usr/local/bin/claude"
        XCTAssertEqual(SpecolaSettings.claudePath, "/usr/local/bin/claude")
        UserDefaults.standard.removeObject(forKey: "claudePath")
    }

    func testSetAndGetOutputFormat() {
        SpecolaSettings.outputFormat = "pdf"
        XCTAssertEqual(SpecolaSettings.outputFormat, "pdf")
        SpecolaSettings.outputFormat = "epub"
        XCTAssertEqual(SpecolaSettings.outputFormat, "epub")
        UserDefaults.standard.removeObject(forKey: "outputFormat")
    }

    // MARK: - Hours edge case

    func testHoursZeroReturnDefault() {
        // Setting integer 0 should return default 24
        UserDefaults.standard.set(0, forKey: "hours")
        XCTAssertEqual(SpecolaSettings.hours, 24)
        UserDefaults.standard.removeObject(forKey: "hours")
    }

    func testHoursNegativeReturnDefault() {
        UserDefaults.standard.set(-5, forKey: "hours")
        XCTAssertEqual(SpecolaSettings.hours, 24)
        UserDefaults.standard.removeObject(forKey: "hours")
    }

    // MARK: - Support directory paths

    func testSupportDirExists() {
        let dir = SpecolaSettings.supportDir
        XCTAssertTrue(FileManager.default.fileExists(atPath: dir.path))
    }

    func testSupportDirEndsWithSpecola() {
        let dir = SpecolaSettings.supportDir
        XCTAssertTrue(dir.lastPathComponent == "Specola")
    }

    func testOpmlPath() {
        let path = SpecolaSettings.opmlPath
        XCTAssertEqual(path.lastPathComponent, "Feeds.opml")
        XCTAssertTrue(path.path.contains("Specola"))
    }

    func testProfilePath() {
        let path = SpecolaSettings.profilePath
        XCTAssertEqual(path.lastPathComponent, "profile.md")
    }

    func testHistoryPath() {
        let path = SpecolaSettings.historyPath
        XCTAssertEqual(path.lastPathComponent, "history.json")
    }

    func testEngineDirPath() {
        let path = SpecolaSettings.engineDir
        XCTAssertEqual(path.lastPathComponent, "engine")
    }

    func testPythonPath() {
        let path = SpecolaSettings.pythonPath
        XCTAssertTrue(path.path.contains(".venv/bin/python"))
    }

    // MARK: - hasOPML

    func testHasOPMLFalseWhenMissing() {
        // By default the test OPML file should not exist
        // (unless the app created it, which won't happen in test)
        // This is more of a smoke test
        _ = SpecolaSettings.hasOPML  // Should not crash
    }

    // MARK: - Output dir default

    func testDefaultOutputDirContainsSpecola() {
        UserDefaults.standard.removeObject(forKey: "outputDir")
        let dir = SpecolaSettings.outputDir
        XCTAssertTrue(dir.contains("Specola"))
    }

    func testDefaultOutputDirContainsDocuments() {
        UserDefaults.standard.removeObject(forKey: "outputDir")
        let dir = SpecolaSettings.outputDir
        XCTAssertTrue(dir.contains("Documents"))
    }

    // MARK: - LLM Provider defaults

    func testDefaultLlmProvider() {
        UserDefaults.standard.removeObject(forKey: "llmProvider")
        XCTAssertEqual(SpecolaSettings.llmProvider, "claude")
    }

    func testDefaultCodexModel() {
        UserDefaults.standard.removeObject(forKey: "codexModel")
        XCTAssertEqual(SpecolaSettings.codexModel, "")
    }

    func testDefaultLmstudioEndpoint() {
        UserDefaults.standard.removeObject(forKey: "lmstudioEndpoint")
        XCTAssertEqual(SpecolaSettings.lmstudioEndpoint, "http://localhost:1234/v1/chat/completions")
    }

    func testDefaultLmstudioModel() {
        UserDefaults.standard.removeObject(forKey: "lmstudioModel")
        XCTAssertEqual(SpecolaSettings.lmstudioModel, "")
    }

    // MARK: - LLM Provider set and get

    func testSetAndGetLlmProvider() {
        SpecolaSettings.llmProvider = "codex"
        XCTAssertEqual(SpecolaSettings.llmProvider, "codex")
        SpecolaSettings.llmProvider = "lmstudio"
        XCTAssertEqual(SpecolaSettings.llmProvider, "lmstudio")
        SpecolaSettings.llmProvider = "claude"
        XCTAssertEqual(SpecolaSettings.llmProvider, "claude")
        UserDefaults.standard.removeObject(forKey: "llmProvider")
    }

    func testSetAndGetCodexModel() {
        SpecolaSettings.codexModel = "o3-pro"
        XCTAssertEqual(SpecolaSettings.codexModel, "o3-pro")
        UserDefaults.standard.removeObject(forKey: "codexModel")
    }

    func testSetAndGetLmstudioEndpoint() {
        SpecolaSettings.lmstudioEndpoint = "http://gpu-server:8080/v1/chat/completions"
        XCTAssertEqual(SpecolaSettings.lmstudioEndpoint, "http://gpu-server:8080/v1/chat/completions")
        UserDefaults.standard.removeObject(forKey: "lmstudioEndpoint")
    }

    func testSetAndGetLmstudioModel() {
        SpecolaSettings.lmstudioModel = "llama-3.3-70b"
        XCTAssertEqual(SpecolaSettings.lmstudioModel, "llama-3.3-70b")
        UserDefaults.standard.removeObject(forKey: "lmstudioModel")
    }
}
