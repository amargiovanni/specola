import Foundation

struct SpecolaEntry: Codable, Identifiable, Equatable {
    let id: String
    let date: Date
    let path: String
    let feedCount: Int
    let itemCount: Int
    var read: Bool
}
