import Foundation
import Security

enum ExecutionError: LocalizedError {
    case serverRequired, invalidURL, unavailable(String), tooLarge, unsupportedLanguage(String)
    var errorDescription: String? {
        switch self {
        case .serverRequired: return "Connect a runner in Settings to run this language."
        case .unsupportedLanguage(let language): return "Execution is not enabled for \(language)."
        case .invalidURL: return "Enter an HTTPS runner URL with no query, fragment, or embedded credentials."
        case .unavailable(let message): return message
        case .tooLarge: return "Keep this mobile snippet below 64 KB."
        }
    }
}
struct RunnerRequest: Codable { let language, source, stdin: String }
struct RunnerCapability: Codable, Identifiable { let id, version: String; let packages: [String] }
struct CapabilitiesResponse: Codable { let runtimes: [RunnerCapability] }
struct RemoteExecutionService {
    static func endpoint(base: String, path: String) throws -> URL {
        guard let c = URLComponents(string: base.trimmingCharacters(in: .whitespacesAndNewlines)), c.scheme == "https", c.host != nil, c.user == nil, c.password == nil, c.query == nil, c.fragment == nil, let url = c.url else { throw ExecutionError.invalidURL }
        return url.appendingPathComponent(path)
    }
    func capabilities(base: String) async throws -> [RunnerCapability] {
        let url = try Self.endpoint(base: base, path: "v1/runtimes")
        let (data, response) = try await URLSession.shared.data(for: request(url: url, base: base))
        try check(response, data: data)
        return try Self.decodeCapabilities(data)
    }
    static func decodeCapabilities(_ data: Data) throws -> [RunnerCapability] {
        try JSONDecoder().decode(CapabilitiesResponse.self, from: data).runtimes.filter {
            CodeLanguage(rawValue: $0.id)?.supportsExecution == true
        }
    }
    func run(language: CodeLanguage, source: String, stdin: String, base: String) async throws -> ExecutionResult {
        guard language.supportsExecution else { throw ExecutionError.unsupportedLanguage(language.title) }
        guard !base.isEmpty else { throw ExecutionError.serverRequired }
        guard source.utf8.count <= 65536, stdin.utf8.count <= 8192 else { throw ExecutionError.tooLarge }
        var req = try request(url: Self.endpoint(base: base, path: "v1/execute"), base: base)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(RunnerRequest(language: language.rawValue, source: source, stdin: stdin))
        let (data, response) = try await URLSession.shared.data(for: req)
        try check(response, data: data)
        return try JSONDecoder().decode(ExecutionResult.self, from: data)
    }
    private func request(url: URL, base: String) -> URLRequest {
        var req = URLRequest(url: url); req.timeoutInterval = 35
        if let token = RunnerCredential.read(base: base), !token.isEmpty { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        return req
    }
    private func check(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { throw ExecutionError.unavailable("The runner did not return an HTTP response.") }
        guard (200...299).contains(http.statusCode) else {
            struct Message: Codable { let detail: String }
            let detail = (try? JSONDecoder().decode(Message.self, from: data).detail) ?? "Runner request failed (\(http.statusCode))."
            throw ExecutionError.unavailable(detail)
        }
        guard data.count <= 262144 else { throw ExecutionError.unavailable("The runner returned too much output.") }
    }
}
enum RunnerCredential {
    private static let service = "com.jideoyelayo.CodingTeacher.runner"
    private static func scope(_ base: String) -> String {
        base.trimmingCharacters(in: .whitespacesAndNewlines).trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }
    static func read(base: String) -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: scope(base), kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var value: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &value) == errSecSuccess, let data = value as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    static func save(_ token: String, base: String) throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: scope(base)]
        if token.isEmpty {
            let status = SecItemDelete(query as CFDictionary)
            guard status == errSecSuccess || status == errSecItemNotFound else { throw ExecutionError.unavailable("The saved token could not be cleared.") }
            return
        }
        let data = Data(token.utf8)
        let status = SecItemUpdate(query as CFDictionary, [kSecValueData as String: data] as CFDictionary)
        if status == errSecItemNotFound {
            var item = query; item[kSecValueData as String] = data; item[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
            guard SecItemAdd(item as CFDictionary, nil) == errSecSuccess else { throw ExecutionError.unavailable("The runner token could not be saved securely.") }
        } else if status != errSecSuccess { throw ExecutionError.unavailable("The runner token could not be updated.") }
    }
}
