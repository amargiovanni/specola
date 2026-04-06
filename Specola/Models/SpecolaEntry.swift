import Foundation

struct SpecolaEntry: Codable, Identifiable, Equatable {
    let id: String
    let date: Date
    let path: String
    let htmlPath: String
    let feedCount: Int
    let itemCount: Int
    let highlights: [String]
    var read: Bool

    enum CodingKeys: String, CodingKey {
        case id, date, path, htmlPath, feedCount, itemCount, highlights, read
    }

    init(
        id: String, date: Date, path: String, htmlPath: String = "",
        feedCount: Int, itemCount: Int, highlights: [String] = [], read: Bool
    ) {
        self.id = id
        self.date = date
        self.path = path
        self.htmlPath = htmlPath
        self.feedCount = feedCount
        self.itemCount = itemCount
        self.highlights = highlights
        self.read = read
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        date = try c.decode(Date.self, forKey: .date)
        path = try c.decode(String.self, forKey: .path)
        htmlPath = try c.decodeIfPresent(String.self, forKey: .htmlPath) ?? ""
        feedCount = try c.decode(Int.self, forKey: .feedCount)
        itemCount = try c.decode(Int.self, forKey: .itemCount)
        highlights = try c.decodeIfPresent([String].self, forKey: .highlights) ?? []
        read = try c.decode(Bool.self, forKey: .read)
    }
}
