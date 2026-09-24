import Foundation

// rev28probe — capability probe CLI (V-01).
// Records, in the built binary's own process context: TCC/AX preflight results,
// Quartz event-construction smoke, ScreenCaptureKit enumeration, and Vision OCR
// availability, plus the exact SDK path used for the build. Writes one structured
// JSON record (atomic temp+rename) into the evidence directory given as argv[1].
// A false trust result is a hard gate failure: it is recorded and surfaced, never
// worked around.

let exitCode = CapabilityProbeCLI.run(arguments: CommandLine.arguments)
exit(exitCode)
