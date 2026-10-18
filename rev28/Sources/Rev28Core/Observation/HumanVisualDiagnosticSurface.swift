import CoreFoundation
import Foundation

public enum HumanVisualDiagnosticSurface: String, Codable, CaseIterable, Equatable, Sendable {
    case albums = "ALBUMS"
    case albumDetail = "ALBUM_DETAIL"
    case folderChooser = "FOLDER_CHOOSER"
}

public enum HumanVisualDiagnosticExecutionMode: String, Codable, Equatable, Sendable {
    case humanAssisted = "HUMAN_ASSISTED"
}

public enum HumanVisualDiagnosticEvidenceTag: String, Codable, Equatable, Sendable {
    case humanObservation = "HUMAN_OBSERVATION"
}

public enum HumanVisualDiagnosticSurfaceError: Error, Equatable, CustomStringConvertible, Sendable {
    case conflictingArgument(String)
    case duplicateArgument(String)
    case missingArgumentValue(String)
    case malformedArgument(String)
    case invalidJSON
    case missingField(String)
    case malformedField(String)
    case unknownField(String)
    case forbiddenEvidenceField(String)
    case invalidVersion(Int)
    case invalidKind(String)
    case invalidExecutionMode(String)
    case mixedExecutionMode(String)
    case invalidEvidenceTag(String)
    case mixedEvidenceTag(String)
    case invalidSurface(String)
    case actionableNotAllowed

    public var description: String {
        switch self {
        case .conflictingArgument(let name):
            return "human-visual-surface.conflictingArgument(\(name))"
        case .duplicateArgument(let name):
            return "human-visual-surface.duplicateArgument(\(name))"
        case .missingArgumentValue(let name):
            return "human-visual-surface.missingArgumentValue(\(name))"
        case .malformedArgument(let name):
            return "human-visual-surface.malformedArgument(\(name))"
        case .invalidJSON:
            return "human-visual-surface.invalidJSON"
        case .missingField(let name):
            return "human-visual-surface.missingField(\(name))"
        case .malformedField(let name):
            return "human-visual-surface.malformedField(\(name))"
        case .unknownField(let name):
            return "human-visual-surface.unknownField(\(name))"
        case .forbiddenEvidenceField(let name):
            return "human-visual-surface.forbiddenEvidenceField(\(name))"
        case .invalidVersion(let version):
            return "human-visual-surface.invalidVersion(\(version))"
        case .invalidKind(let kind):
            return "human-visual-surface.invalidKind(\(kind))"
        case .invalidExecutionMode(let mode):
            return "human-visual-surface.invalidExecutionMode(\(mode))"
        case .mixedExecutionMode(let mode):
            return "human-visual-surface.mixedExecutionMode(\(mode))"
        case .invalidEvidenceTag(let tag):
            return "human-visual-surface.invalidEvidenceTag(\(tag))"
        case .mixedEvidenceTag(let tag):
            return "human-visual-surface.mixedEvidenceTag(\(tag))"
        case .invalidSurface(let surface):
            return "human-visual-surface.invalidSurface(\(surface))"
        case .actionableNotAllowed:
            return "human-visual-surface.actionableNotAllowed"
        }
    }
}

/// Strict, read-only metadata for a HUMAN_ASSISTED visual diagnostic capture.
/// This type never grants capture or input authority and is deliberately
/// separate from AUTOMATIC frame-support/classifier evidence.
public struct HumanVisualDiagnosticSurfaceRequest: Codable, Equatable, Sendable {
    public static let version = 1
    public static let kind = "human-visual-diagnostic-surface-1"

    public let version: Int
    public let kind: String
    public let executionMode: HumanVisualDiagnosticExecutionMode
    public let evidenceTag: HumanVisualDiagnosticEvidenceTag
    public let requestedSurface: HumanVisualDiagnosticSurface
    public let actionable: Bool

    private enum CodingKeys: String, CodingKey {
        case version
        case kind
        case executionMode = "execution_mode"
        case evidenceTag = "evidence_tag"
        case requestedSurface = "requested_surface"
        case actionable
    }

    private struct AnyCodingKey: CodingKey {
        let stringValue: String

        init?(stringValue: String) {
            self.stringValue = stringValue
        }

        var intValue: Int? { nil }

        init?(intValue: Int) {
            return nil
        }
    }

    fileprivate init(version: Int, kind: String,
                     executionMode: HumanVisualDiagnosticExecutionMode,
                     evidenceTag: HumanVisualDiagnosticEvidenceTag,
                     requestedSurface: HumanVisualDiagnosticSurface,
                     actionable: Bool) {
        self.version = version
        self.kind = kind
        self.executionMode = executionMode
        self.evidenceTag = evidenceTag
        self.requestedSurface = requestedSurface
        self.actionable = actionable
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: AnyCodingKey.self)
        try HumanVisualDiagnosticSurfaceParser.validateFieldNames(
            Set(container.allKeys.map(\.stringValue)))

        let version: Int = try Self.decode("version", from: container)
        let kind: String = try Self.decode("kind", from: container)
        let executionMode: String = try Self.decode("execution_mode", from: container)
        let evidenceTag: String = try Self.decode("evidence_tag", from: container)
        let requestedSurface: String = try Self.decode("requested_surface", from: container)
        let actionable: Bool = try Self.decode("actionable", from: container)
        self = try HumanVisualDiagnosticSurfaceParser.validated(
            version: version, kind: kind, executionMode: executionMode,
            evidenceTag: evidenceTag, requestedSurface: requestedSurface,
            actionable: actionable)
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(version, forKey: .version)
        try container.encode(kind, forKey: .kind)
        try container.encode(executionMode, forKey: .executionMode)
        try container.encode(evidenceTag, forKey: .evidenceTag)
        try container.encode(requestedSurface, forKey: .requestedSurface)
        try container.encode(actionable, forKey: .actionable)
    }

    private static func decode<T: Decodable>(
        _ field: String, from container: KeyedDecodingContainer<AnyCodingKey>
    ) throws -> T {
        guard let key = AnyCodingKey(stringValue: field), container.contains(key) else {
            throw HumanVisualDiagnosticSurfaceError.missingField(field)
        }
        do {
            return try container.decode(T.self, forKey: key)
        } catch {
            throw HumanVisualDiagnosticSurfaceError.malformedField(field)
        }
    }
}

public enum HumanVisualDiagnosticSurfaceParser {
    public static let argument = "--human-visual-diagnostic-surface-json"

    private static let allowedFields: Set<String> = [
        "version", "kind", "execution_mode", "evidence_tag", "requested_surface", "actionable"
    ]

    private static let fieldOrder = [
        "version", "kind", "execution_mode", "evidence_tag", "requested_surface", "actionable"
    ]

    private static let reservedArguments: Set<String> = [
        "--execution-mode", "--requested-surface", "--surface", "--evidence-tag", "--actionable"
    ]

    private static let forbiddenArgumentFragments: Set<String> = [
        "frame-support", "frame_support", "framesupport",
        "classifier", "native-precision", "native_precision", "nativeprecision",
        "cua-returned", "cua_returned", "cuareturned", "e2e-pass", "e2e_pass", "e2epass"
    ]

    private static let forbiddenEvidenceFields: Set<String> = [
        "frame_support", "frame_support_pass", "frame_support_status",
        "frame-support", "frame-support-pass", "frame-support-status",
        "classifier", "classifier_pass", "classifier_status",
        "classifier-pass", "classifier-status",
        "native_precision", "native_precision_pass", "native_precision_status",
        "native-precision", "native-precision-pass", "native-precision-status",
        "precision", "confidence", "click", "clicks", "input", "gui_input",
        "action", "actionable_click", "cua", "cua_returned", "cua-returned",
        "status", "result", "e2e", "e2e_pass", "e2e-pass", "e2e_status"
    ]

    /// Returns nil only for the legacy AUTOMATIC call shape. Any HUMAN surface
    /// arguments must use the single strict JSON argument below.
    public static func parse(arguments: [String]) throws -> HumanVisualDiagnosticSurfaceRequest? {
        if arguments.contains(where: { $0.hasPrefix(argument + "=") }) {
            throw HumanVisualDiagnosticSurfaceError.malformedArgument(argument)
        }
        let indexes = arguments.indices.filter { arguments[$0] == argument }
        guard !indexes.isEmpty else { return nil }
        if let forbidden = arguments.first(where: {
            guard $0.hasPrefix("--") else { return false }
            let lowered = $0.lowercased()
            return forbiddenArgumentFragments.contains(where: lowered.contains)
        }) {
            throw HumanVisualDiagnosticSurfaceError.conflictingArgument(forbidden)
        }
        if let conflicting = arguments.first(where: { reservedArguments.contains($0) }) {
            throw HumanVisualDiagnosticSurfaceError.conflictingArgument(conflicting)
        }
        guard indexes.count == 1 else {
            throw HumanVisualDiagnosticSurfaceError.duplicateArgument(argument)
        }
        let index = indexes[0]
        guard index + 1 < arguments.count, !arguments[index + 1].isEmpty,
              !arguments[index + 1].hasPrefix("--") else {
            throw HumanVisualDiagnosticSurfaceError.missingArgumentValue(argument)
        }
        return try parse(json: arguments[index + 1])
    }

    public static func parse(json: String) throws -> HumanVisualDiagnosticSurfaceRequest {
        guard let data = json.data(using: .utf8) else {
            throw HumanVisualDiagnosticSurfaceError.invalidJSON
        }
        return try parse(json: data)
    }

    public static func parse(json data: Data) throws -> HumanVisualDiagnosticSurfaceRequest {
        let raw: Any
        do {
            raw = try JSONSerialization.jsonObject(with: data, options: [])
        } catch {
            throw HumanVisualDiagnosticSurfaceError.invalidJSON
        }
        guard let object = raw as? [String: Any] else {
            throw HumanVisualDiagnosticSurfaceError.invalidJSON
        }

        try validateFieldNames(Set(object.keys))

        guard let version = integer(object["version"]) else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("version")
        }
        guard let kind = object["kind"] as? String else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("kind")
        }
        guard let modeValue = object["execution_mode"] as? String else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("execution_mode")
        }
        guard let tagValue = object["evidence_tag"] as? String else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("evidence_tag")
        }
        guard let surfaceValue = object["requested_surface"] as? String else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("requested_surface")
        }
        guard let actionableValue = object["actionable"], isBoolean(actionableValue),
              let actionable = actionableValue as? Bool else {
            throw HumanVisualDiagnosticSurfaceError.malformedField("actionable")
        }

        return try validated(version: version, kind: kind, executionMode: modeValue,
            evidenceTag: tagValue, requestedSurface: surfaceValue, actionable: actionable)
    }

    fileprivate static func validateFieldNames(_ keys: Set<String>) throws {
        if let forbidden = keys.intersection(forbiddenEvidenceFields).sorted().first {
            throw HumanVisualDiagnosticSurfaceError.forbiddenEvidenceField(forbidden)
        }
        if let unknown = keys.subtracting(allowedFields).sorted().first {
            throw HumanVisualDiagnosticSurfaceError.unknownField(unknown)
        }
        for field in fieldOrder where !keys.contains(field) {
            throw HumanVisualDiagnosticSurfaceError.missingField(field)
        }
    }

    fileprivate static func validated(
        version: Int, kind: String, executionMode modeValue: String,
        evidenceTag tagValue: String, requestedSurface surfaceValue: String,
        actionable: Bool
    ) throws -> HumanVisualDiagnosticSurfaceRequest {
        guard version == HumanVisualDiagnosticSurfaceRequest.version else {
            throw HumanVisualDiagnosticSurfaceError.invalidVersion(version)
        }

        guard kind == HumanVisualDiagnosticSurfaceRequest.kind else {
            throw HumanVisualDiagnosticSurfaceError.invalidKind(kind)
        }

        guard let mode = HumanVisualDiagnosticExecutionMode(rawValue: modeValue) else {
            if modeValue == "AUTO" {
                throw HumanVisualDiagnosticSurfaceError.mixedExecutionMode(modeValue)
            }
            throw HumanVisualDiagnosticSurfaceError.invalidExecutionMode(modeValue)
        }

        guard let tag = HumanVisualDiagnosticEvidenceTag(rawValue: tagValue) else {
            if tagValue.contains("AUTO") {
                throw HumanVisualDiagnosticSurfaceError.mixedEvidenceTag(tagValue)
            }
            throw HumanVisualDiagnosticSurfaceError.invalidEvidenceTag(tagValue)
        }

        guard let surface = HumanVisualDiagnosticSurface(rawValue: surfaceValue) else {
            throw HumanVisualDiagnosticSurfaceError.invalidSurface(surfaceValue)
        }

        guard !actionable else {
            throw HumanVisualDiagnosticSurfaceError.actionableNotAllowed
        }

        return HumanVisualDiagnosticSurfaceRequest(version: version, kind: kind,
            executionMode: mode, evidenceTag: tag, requestedSurface: surface, actionable: false)
    }

    private static func integer(_ value: Any?) -> Int? {
        guard let number = value as? NSNumber, !isBoolean(number),
              !CFNumberIsFloatType(number) else { return nil }
        return Int(number.stringValue)
    }

    private static func isBoolean(_ value: Any?) -> Bool {
        guard let value else { return false }
        return CFGetTypeID(value as CFTypeRef) == CFBooleanGetTypeID()
    }
}
