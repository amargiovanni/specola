import SwiftUI
import UniformTypeIdentifiers

struct OnboardingView: View {
    var onComplete: () -> Void = {}
    @State private var currentStep = 0
    @State private var profileText = ""
    @State private var opmlImported = false
    @State private var opmlInfo = ""

    var body: some View {
        VStack(spacing: 0) {
            // Progress dots
            HStack(spacing: 8) {
                ForEach(0..<3) { i in
                    Circle()
                        .fill(i <= currentStep ? Color.accentColor : Color.secondary.opacity(0.3))
                        .frame(width: 8, height: 8)
                        .animation(.easeInOut, value: currentStep)
                }
            }
            .padding(.top, 24)
            .padding(.bottom, 16)

            // Step content
            TabView(selection: $currentStep) {
                welcomeStep.tag(0)
                feedsStep.tag(1)
                profileStep.tag(2)
            }
            .tabViewStyle(.automatic)
            .frame(maxHeight: .infinity)

            // Navigation
            HStack {
                if currentStep > 0 {
                    Button("Indietro") { withAnimation { currentStep -= 1 } }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if currentStep < 2 {
                    Button("Avanti") { withAnimation { currentStep += 1 } }
                        .buttonStyle(.borderedProminent)
                        .disabled(currentStep == 1 && !opmlImported)
                } else {
                    Button("Inizia") {
                        saveProfile()
                        SpecolaSettings.hasCompletedSetup = true
                        onComplete()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(profileText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
            .padding(24)
        }
        .frame(width: 520, height: 460)
    }

    // MARK: - Step 1: Welcome

    private var welcomeStep: some View {
        VStack(spacing: 16) {
            Image(systemName: "binoculars.fill")
                .font(.system(size: 48))
                .foregroundStyle(.tint)
                .padding(.bottom, 8)

            Text("Benvenuto in Specola")
                .font(.title)
                .fontWeight(.bold)

            Text("La tua specola personale sulle notizie.\nOgni giorno, un briefing su misura.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 360)

            VStack(alignment: .leading, spacing: 12) {
                featureRow(icon: "newspaper", text: "Importa i tuoi feed RSS")
                featureRow(icon: "person.text.rectangle", text: "Descrivi il tuo profilo professionale")
                featureRow(icon: "doc.richtext", text: "Ricevi briefing DOCX, PDF o EPUB")
            }
            .padding(.top, 12)
        }
        .padding(24)
    }

    private func featureRow(icon: String, text: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.tint)
                .frame(width: 28)
            Text(text)
                .font(.subheadline)
        }
    }

    // MARK: - Step 2: Feed import

    private var feedsStep: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text")
                .font(.system(size: 36))
                .foregroundStyle(.tint)

            Text("Importa i tuoi feed")
                .font(.title2)
                .fontWeight(.bold)

            Text("Scegli un file OPML esportato dal tuo feed reader (Feedly, NetNewsWire, Inoreader...)")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 380)

            if opmlImported {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Text(opmlInfo)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 8)
            }

            Button(opmlImported ? "Cambia file OPML..." : "Scegli file OPML...") {
                chooseOPML()
            }
            .buttonStyle(.bordered)
        }
        .padding(24)
    }

    // MARK: - Step 3: Profile

    private var profileStep: some View {
        VStack(spacing: 12) {
            Image(systemName: "person.text.rectangle")
                .font(.system(size: 36))
                .foregroundStyle(.tint)

            Text("Il tuo profilo")
                .font(.title2)
                .fontWeight(.bold)

            Text("Descrivi ruolo, stack, interessi e progetti.\nPiu dettagli dai, migliore sara il briefing.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 380)

            TextEditor(text: $profileText)
                .font(.body)
                .frame(minHeight: 140)
                .padding(4)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.secondary.opacity(0.2))
                )
                .overlay(
                    Group {
                        if profileText.isEmpty {
                            Text("Es: Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS. Mi interessa: regolamentazione EU, sicurezza API, trend VC europeo...")
                                .foregroundStyle(.tertiary)
                                .padding(8)
                                .allowsHitTesting(false)
                        }
                    },
                    alignment: .topLeading
                )
                .padding(.horizontal, 8)
        }
        .padding(24)
    }

    // MARK: - Actions

    private func chooseOPML() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [
            UTType(filenameExtension: "opml") ?? .xml,
            .xml,
        ]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let dest = SpecolaSettings.opmlPath
        try? FileManager.default.removeItem(at: dest)
        try? FileManager.default.copyItem(at: url, to: dest)
        opmlImported = true
        refreshOPMLInfo()
    }

    private func refreshOPMLInfo() {
        guard SpecolaSettings.hasOPML else { opmlInfo = ""; return }
        do {
            let data = try Data(contentsOf: SpecolaSettings.opmlPath)
            let xml = try XMLDocument(data: data)
            let categories = try xml.nodes(forXPath: "/opml/body/outline")
            let feeds = try xml.nodes(forXPath: "//outline[@type='rss']")
            opmlInfo = "\(categories.count) categorie, \(feeds.count) feed importati"
        } catch {
            opmlInfo = "File importato"
        }
    }

    private func saveProfile() {
        let trimmed = profileText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        try? trimmed.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}
