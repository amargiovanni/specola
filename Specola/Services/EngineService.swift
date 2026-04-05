import Foundation

struct EngineResult {
    let outputPath: String?
    let feedCount: Int
    let itemCount: Int
}

enum EngineError: LocalizedError {
    case engineNotFound
    case pythonNotFound
    case executionFailed(String)

    var errorDescription: String? {
        switch self {
        case .engineNotFound: return "Motore Python non trovato"
        case .pythonNotFound: return "Python venv non trovato"
        case .executionFailed(let msg): return msg
        }
    }
}

enum EngineService {
    static func run() async throws -> EngineResult {
        let pythonPath = SpecolaSettings.pythonPath
        let engineDir = SpecolaSettings.engineDir
        let enginePath = engineDir.appendingPathComponent("specola_engine.py")

        guard FileManager.default.fileExists(atPath: enginePath.path) else {
            throw EngineError.engineNotFound
        }
        guard FileManager.default.fileExists(atPath: pythonPath.path) else {
            throw EngineError.pythonNotFound
        }

        let process = Process()
        process.executableURL = pythonPath
        process.arguments = [
            enginePath.path, "run",
            "--opml", SpecolaSettings.opmlPath.path,
            "--profile", SpecolaSettings.profilePath.path,
            "--output-dir", SpecolaSettings.outputDir,
            "--hours", String(SpecolaSettings.hours),
            "--language", SpecolaSettings.language,
        ]
        process.currentDirectoryURL = engineDir

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        try process.run()
        process.waitUntilExit()

        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

        guard let outputString = String(data: outputData, encoding: .utf8),
              !outputString.isEmpty else {
            let errorString = String(data: errorData, encoding: .utf8) ?? "Unknown error"
            throw EngineError.executionFailed(errorString)
        }

        return try parseOutput(outputString)
    }

    static func parseOutput(_ json: String) throws -> EngineResult {
        guard let data = json.data(using: .utf8) else {
            throw EngineError.executionFailed("Invalid output encoding")
        }
        let parsed = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let parsed else {
            throw EngineError.executionFailed("Invalid JSON output")
        }
        guard let status = parsed["status"] as? String else {
            throw EngineError.executionFailed("Missing status in output")
        }
        if status == "error" {
            let message = parsed["message"] as? String ?? "Errore sconosciuto"
            throw EngineError.executionFailed(message)
        }
        return EngineResult(
            outputPath: parsed["output_path"] as? String,
            feedCount: parsed["feed_count"] as? Int ?? 0,
            itemCount: parsed["item_count"] as? Int ?? 0
        )
    }
}
