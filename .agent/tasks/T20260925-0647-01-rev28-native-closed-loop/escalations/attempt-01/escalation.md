# Stage 04 convergence escalation — PRIMARY_NATIVE_COMPOSITION

TASK_ID: T20260925-0647-01-rev28-native-closed-loop  
AB_MODE: AB_IMPLEMENTATION_EVALUATION_OFFLINE_ONLY  
STAGE: 04  
STATE: ESCALATED  
BLOCKER_FINGERPRINT: The exact `PRIMARY_NATIVE_COMPOSITION` fingerprint in `progress.md`; expected one reachable native path binding fresh observation, actual adapters, common engine, durable owner, chooser and filesystem proof; observed CLI refuses because no reviewed native frame+structural-candidate session provider is configured.  
ATTEMPTS: 3/3 task-scoped attempts: prior same-task composition attempt on `v43-ab/codex-rev28` (`c7eb3f99f5fd3ce3bcdad4ae44ca5a677e48ac1c`); retained-image-to-OCR link (current attempt 02); source-contract composition feasibility trace (current attempt 03).  

## Attempt history and new evidence

The prior same-task attempt assembled a preflight composition but still left live execution fail-closed before dispatch. Current attempt 02 closed and tested the retained-image-to-OCR identity handoff. Final attempt 03 traced whether the planned small factory/phase-aware composition could satisfy the approved criterion without a semantic change. It could not: `LiveExecutionAdapter.establish` returns a raw `String` digest; `LiveExecutionEngine.run()` starts only from empty state and proceeds through Save All and destination confirmation; `rev28ctl` has no native observation/session provider and refuses `live-execute` before constructing or invoking the engine. Thus a factory alone would be either unreachable or would preserve the plan-forbidden ability for adapter-returned digest strings to assert state.

Evidence locations and source references:

- `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift:54` — state establishment returns `String`.
- `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift:93-150` — one `run()` executes pre-Save-All states and then Save All, chooser, destination confirmation and later steps.
- `rev28/Sources/rev28ctl/main.swift:105-108` — live execution refuses before engine construction because no native provider is configured.
- `rev28/Sources/Rev28Core/Transaction/PersistentTransactionOwner.swift:239,263,318` — owner exposes irreversible reservation/chooser methods, but their existence alone does not provide typed native evidence or phase control.
- Current bounded implementation and verification evidence is recorded in `progress.md`, including attempt 02 and the earlier deterministic gates.

## Eliminated and remaining uncertainty

Eliminated: A retained image can be carried through OCR with its epoch/image identity intact and tested offline.

Eliminated: Adding a factory around the current engine and adapter contracts is sufficient to establish the approved native composition.

Remaining: the coherent design and implementation sequence for typed run-bound state evidence, phase-aware common orchestration, persistent goal-slot/ledger/anchor authority, same-session native observation, guarded actuation, strict actual chooser binding and filesystem proof through the existing common engine.

Another local retry has low information value because the budget is exhausted, and the source trace shows that a facade-only retry cannot meet the acceptance condition. Coordinated work across the existing engine, owner, phase controller and native adapters requires high-reasoning review before further edits.

## MUST_NOT_BREAK

- Owner + IntentLedger remain sole transaction/state authority; persistent goal slot and independent anchor/checkpoint survive run/session/path/token changes.
- Phase A leaves all Save All and destination-confirmation intent/attempt counts at zero and does not consume/rename the one-shot entitlement.
- No caller-asserted freshness or arbitrary digest string may authorize a transition. Same retained pixels and identity/provenance bind OCR, structure and readiness.
- Common engine semantics and owner gates are shared by injected and production paths. No parallel engine or semantic bypass.
- After any irreversible intent/attempt, all restarts are observe-only; unknown effects never permit retry or replacement.
- Preserve frozen identity, geometry, chooser timing/predicate, exact destination, tripwire, baseline, stable-content and refusal requirements in handoff C2–C7.
- No real LINE, GUI, `live-preflight`, `live-execute`, Phase A or Phase B in this offline A/B evaluation.

## Precise question for Stage 06 HIGH_REASONING_REVIEWER

Given the current `LiveExecutionAdapter` string-digest API, the all-phases `LiveExecutionEngine.run()` sequence, and the absent native observation provider, what is the smallest coherent decomposition of the approved C2–C7 contract that preserves one common state/evidence/intent authority and keeps `live-preflight` reversible/unconsumed? Specify the typed evidence, phase entrypoints/controller, owner persistence/eligibility interfaces, injected OS boundaries and test order needed before a reachable native path can be considered safe. If that decomposition changes reviewed semantics, identify the exact Plan elements requiring Stage 01 replanning.

## Statuses

```text
PRIMARY_OUTCOME_STATUS: NOT_ACHIEVED
IMPLEMENTATION_STATUS: ESCALATED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: INCOMPLETE
INDEPENDENT_ACCEPTANCE_STATUS: PENDING
TASK_CLOSURE_STATUS: HIGH_REASONING_REVIEW_REQUIRED
PHASE_A_STATUS: NOT_STARTED
PHASE_B_STATUS: FORBIDDEN_AB_EVALUATION
NEXT_STAGE: STAGE_06_HIGH_REASONING_REVIEW
```

No real LINE interaction, GUI operation, production authorization/ledger, Save All dispatch, destination confirmation or Phase A/B action occurred. No product source was changed for attempt 03; no tests were run for that read-only feasibility trace.
