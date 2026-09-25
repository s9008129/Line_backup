import XCTest
@testable import Rev28Core

final class ExecutionPolicyTests: XCTestCase {
    func testStateMachineOnlyAllowsNextReviewedTransition() throws {
        XCTAssertNoThrow(try ExecutionStateMachine.validateTransition(from: .appReady, to: .groupReady))
        XCTAssertThrowsError(try ExecutionStateMachine.validateTransition(from: .appReady, to: .albumDetailVerified))
    }

    func testSaveAllAndConfirmationAreExactlyOnce() throws {
        var budget = LiveDispatchBudget()
        try budget.consumeSaveAll()
        try budget.consumeDestinationConfirmation()
        XCTAssertEqual(budget.saveAllDispatches, 1)
        XCTAssertEqual(budget.destinationConfirmations, 1)
        XCTAssertThrowsError(try budget.consumeSaveAll()) { XCTAssertEqual($0 as? ExecutionPolicyError, .saveAllAlreadyDispatched) }
        XCTAssertThrowsError(try budget.consumeDestinationConfirmation()) { XCTAssertEqual($0 as? ExecutionPolicyError, .destinationAlreadyConfirmed) }
    }

    func testGlobalReversibleBudgetStopsThirteenthDispatch() throws {
        var budget = LiveDispatchBudget()
        for _ in 0..<12 { try budget.consumeReversible() }
        XCTAssertThrowsError(try budget.consumeReversible()) { XCTAssertEqual($0 as? ExecutionPolicyError, .reversibleBudgetExhausted) }
    }

    func testIdenticalBlockerStopsFourthRecovery() throws {
        var budget = LiveDispatchBudget()
        for _ in 0..<3 { try budget.consumeReversible(blockerKey: "same") }
        XCTAssertThrowsError(try budget.consumeReversible(blockerKey: "same")) {
            XCTAssertEqual($0 as? ExecutionPolicyError, .identicalBlockerBudgetExhausted)
        }
    }

    func testTwoConsecutiveRevalidationFailuresAbort() throws {
        var budget = LiveDispatchBudget()
        try budget.recordCandidateRevalidation(false)
        XCTAssertThrowsError(try budget.recordCandidateRevalidation(false)) {
            XCTAssertEqual($0 as? ExecutionPolicyError, .candidateRevalidationExhausted)
        }
    }

    func testSuccessfulRevalidationResetsFailureCount() throws {
        var budget = LiveDispatchBudget()
        try budget.recordCandidateRevalidation(false)
        try budget.recordCandidateRevalidation(true)
        try budget.recordCandidateRevalidation(false)
        XCTAssertEqual(budget.consecutiveCandidateRevalidationFailures, 1)
    }
}
