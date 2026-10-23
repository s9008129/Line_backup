# Stage 06 — High-Reasoning Review of `PRIMARY_NATIVE_COMPOSITION` (escalation attempt-01)

- **TASK_ID**: `T20260925-0647-01-rev28-native-closed-loop` (task class CRITICAL)
- **Stage / role**: HIGH_REASONING_REVIEW / HIGH_REASONING_REVIEWER
- **Escalation reviewed**: `escalations/attempt-01/escalation.md` (SHA-256 `5bcbd72c718384d96fab9d69a4d272bf4c6bb210ba56a3e5ba7513063060a367`) + `context.json` (`ae2081adb327c90fb421c1855cc65468c23f22848ad5bf979f03d2f40a69b8b1`)
  - origin copy: worktree `Line_backup-ab-luna`, branch `v43-ab/luna-rev28`, HEAD `9cbaa1141595acb538d4672066072d2b8ffb7065` (untracked files, written 2026-09-29T08:56:32+0800 — observed by mtime; both hashes match the handoff §16 values)
  - durable mirror + this decision: this directory (see `PROVENANCE.md`)
- **Worktree / branch of record for this review**: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`, branch `v43-ab/codex-rev28`, HEAD `5ed71064a9f93d4abc27eecc857e3584a1b2a2ae` (read-only review; HEAD unchanged)
- **Reviewed contract SHAs**: `plan.md` `05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b`; `handoff.md` `67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33`
- **Date**: 2026-09-29 (Asia/Taipei)
- **Read-only statement**: no product edit, no build/test execution, no `rev28ctl` product invocation, no LINE.app interaction, no OS events, no `live-preflight`/`live-execute`, no git write to any product tree, no worktree change. Zero irreversible throughout: Save All dispatches 0, destination confirmations 0, irreversible intents 0. `PHASE_B_STATUS`: `FORBIDDEN_AB_EVALUATION`.

```text
ESCALATION_DECISION: IMPLEMENTER_FIX
```

## 1. Expected vs observed (reconstructed)

The escalation's failing acceptance condition was:

```text
STAGE=04  CHECK=PRIMARY_NATIVE_COMPOSITION
EXPECTED=One reachable native path binds fresh observation, actual adapters, common engine, durable owner, chooser, and filesystem proof
OBSERVED=CLI refuses because no reviewed native frame+structural-candidate session provider is configured
```

Source re-read (read-only) shows this EXPECTED/OBSERVED pair is **branch-local to the luna worktree at checkpoint `9cbaa11`**, and is **falsified on the same `TASK_ID`'s newer lineage** (`v43-ab/codex-rev28`, 24 commits after `c7eb3f99`, HEAD `5ed7106`). The three cited root causes no longer hold there:

| Escalation citation (luna tree @ `9cbaa11`) | Observed on `v43-ab/codex-rev28` @ `5ed7106` | Verdict |
|---|---|---|
| `LiveExecutionEngine.swift:54` `establish(...) -> String` | `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift:84` `func establish(state:owner:) async throws -> EstablishedStateEvidence` (typed run-bound evidence; introduced `c441477` 05:30) | FALSIFIED |
| one all-phases `run()` (`:93-150`) with no reversible/irreversible split | `LiveExecutionEngine.swift:229` `establishPreSaveStates()`; `:264` `runPreflight() -> LivePreflightOutcome` (zero-irreversible preflight; `preflightRequiresZeroIrreversibleRecords`; entitlement state observed from the durable goal slot); introduced `947db18` 05:42 | FALSIFIED |
| `rev28ctl/main.swift:105-108` refusal "no reviewed native frame+structural-candidate session provider was configured" (`git show 9cbaa11:…/main.swift` confirms this exact text on the luna tree, which has **no** `Rev28Core/Composition/` directory) | `rev28ctl/main.swift:282-317` builds `LiveCompositionFactory.make(...)` with `ProductionObservationSource`, `ComposedNativeAdapter`, `NativeObservationSession`, `PersistentTransactionOwner`, `GatedQuartzActuator` and calls `composition.engine.runPreflight()`; composition assembled `c7eb3f99` 05:51, Phase B eligibility arming `8528ce5`, post-Save-All composition `e407565` 06:06, Phase A publisher `0d1cdb5` 06:28 | FALSIFIED |

The composition is not merely present as a facade: it was hardened by three completed fresh-review rounds on this lineage — V-09 attempt-01 (8 MAJOR findings → in-contract repairs), attempt-02 (4 MAJOR + 2 actionable MINOR → repairs), attempt-03 (**0 MAJOR**; M-1 margin repair `cf39fdcc` + record fix `3d74248b`). Offline evidence on the repaired tree is bound and was re-verified during this review: digest `6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686` (48 paths; independently recomputed, Python replica identical to `a49`), frozen artifacts 9/9 re-hashed PASS, replay `a52`/`a53` byte-identical `81f6da94…7261`, adversarial 27/27 ×2, CLI-refusal fixture 77/77/77/64/77 with zero side effects, provenance PASS.

## 2. Identity reconciliation (decisive finding)

At the moment the escalation was written (2026-09-29T08:56+0800), the authoritative lineage already carried: the full composition (since 06:28), V-09 attempt-01/02/03 reviews and repairs, M-1 at `cf39fdcc` (08:06), the attempt-04 `bindings.json` (08:08) and the attempt-04 `03-transaction-history.md` (08:14). The escalation therefore describes a **stale tree slice** (the checkpoint `9cbaa11`, which is an ancestor of the escalating branch but predates the composition work), not the task's latest durable state.

```text
STATE_RECONCILIATION_REQUIRED → RESOLVED (recording, no git surgery):
  task_id      = T20260925-0647-01-rev28-native-closed-loop   (one task, three worktrees)
  escalations  = only in Line_backup-ab-luna (untracked), HEAD 9cbaa11; mirrored here byte-identical
  authority    = Line_backup (v43-ab/codex-rev28) HEAD 5ed7106; 9cbaa11 and c7eb3f99 are ancestors
  controller   = no ~/.codex/task-orchestrator state for this legacy TASK_ID → STATE_RECONCILIATION_REQUIRED (no new task started: a new TASK_ID would fragment identity)
```

Root cause (first principles, two layers):

1. **Contract layer (genuine, now closed).** At the checkpoint, a string-digest adapter contract, a single all-phases engine entry, and the absence of a reviewed native observation/session provider genuinely could not satisfy `PRIMARY_NATIVE_COMPOSITION` without changing semantics. The newer lineage closed exactly these three gaps *inside* C2–C7 (typed evidence, phase entrypoint, composition factory), so the load-bearing plan semantics did **not** need to change.
2. **Process layer (the real stall cause).** Durable state was fragmented across three worktrees with no single controller state, so an escalation for a blocker that was already being closed on a sibling branch could still be produced, and local attempts on the stale slice could not see the landed contracts. This is an identity-discipline defect, not an architecture defect.

## 3. Falsified hypotheses and information value

| Hypothesis | Verdict |
|---|---|
| H1 "A factory seam alone suffices" (escalation attempt-03) | TRUE for the luna tree (no typed evidence contract there) and IRRELEVANT now: the newer lineage did not settle for a facade; it built typed evidence + phase entrypoint + provider and passed three review rounds |
| H2 "C2–C7 must be replanned" | FALSIFIED — the composition was implemented and reviewed against the unchanged `plan.md`/`handoff.md`; every V-09 finding was a plan-conformance defect, i.e. an in-contract repair |
| H3 "`PRIMARY_NATIVE_COMPOSITION` is still blocked, 3/3" | FALSIFIED — the failing condition ("CLI refuses … no provider") does not exist on the authority tree; the CLI refusal fixture now exercises deliberate fail-closed refusals (77/77/77/64/77) rather than a missing composition |
| H4 "Another local composition attempt has information value" | FALSIFIED — no composition failing condition remains offline; the next falsifiable test is a real Phase A preflight, which is externally blocked (LINE signed out; no target album surface) |

Budget discipline: `PRIMARY_NATIVE_COMPOSITION` stays **3/3 exhausted** and is now closed as `RESOLVED_BY_SUPERSEDING_LINEAGE`. This decision does **not** reset it and authorizes **no** further composition implementation. The extension below is scoped to a **distinct** fingerprint with a different surface and different acceptance.

## 4. New distinct blocker (not a rename)

```text
BLOCKER_FINGERPRINT: V09_A4_FRESH_VERIFICATION_INCOMPLETE
STAGE=04
CHECK=V09_ATTEMPT_04_REVIEW_SET
SURFACE=.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/v09/attempt-04 (fresh reviewer contexts vs bindings head cf39fdcc / digest 6734dda5…a686)
EXPECTED=three fresh read-only reviewer contexts (01-perception-geometry, 02-timing-automation, 03-transaction-history) complete on the repaired tree; every M-1 repair claim and every in-force VERIFIED claim re-derived at cf39fdcc / 6734dda5…a686 (no attempt-01/02/03 evidence reused as proof); 0 MAJOR after disposition; attempt-04 record written to progress.md + execution.md and committed
OBSERVED=v09/attempt-04/bindings.json (committed 5ed7106) and 03-transaction-history.md (untracked) exist; 01-perception-geometry.md and 02-timing-automation.md are absent; no attempt-04 record in progress.md / execution.md
```

Why it is not a rename: the old failing condition was *composition reachability* (a missing native session provider). The new one is *verification close-out of the repaired tree* (missing reviewer reports over an existing, reviewed composition). Different failing surface, different acceptance, different evidence class; the composition itself is not re-attempted.

## 5. Budget extension

```text
BUDGET_EXTENSION: +2
EXTENSION_SCOPE: V09_A4_FRESH_VERIFICATION_INCOMPLETE (PRIMARY_NATIVE_COMPOSITION remains 3/3 exhausted; no composition implementation is authorized)
NEW_INFORMATION_SOURCE: superseding lineage state on the same TASK_ID — typed-evidence contract c441477, per-state native adapter + runPreflight 947db18, live composition wired into rev28ctl c7eb3f99, Phase B eligibility arming 8528ce5, post-Save-All composition e407565, Phase A publisher 0d1cdb5; V-09 attempt-03 0-MAJOR reviews; M-1 repair cf39fdcc with digest 6734dda5…a686 (48 paths); v09/attempt-04/bindings.json bound to that tree; the landed attempt-04 03 report
STOP_AFTER: attempt-04's three reports complete, any fresh MAJOR dispositioned under the convergence policy, the attempt-04 record written to progress.md + execution.md and committed — then stop. The only remaining real-world gate is the external Phase A prerequisite (user logs into LINE and opens 旻謙允禎成長日記 — 禎 U+798E — at 2024/05/13～05/17), which is a separate EXTERNAL_BLOCKER route and must not be pre-empted by polling, retrying, or GUI prepositioning.
```

## 6. Why not the other routes

- `PLANNER_REPLAN` — rejected: no load-bearing C2–C7 semantic change is implied; the composition already conforms to the unchanged plan and passed review rounds.
- `TARGETED_DIAGNOSTIC` — rejected: no distinguishing experiment is needed; the missing information is the completion of the already-bound verification round, not a new measurement.
- `EXTERNAL_BLOCKER` — not yet: the immediate next step is machine work (attempt-04 close-out). The external LINE-login gate becomes the correct route only after STOP_AFTER is met.

## 7. Not done by this review

No fourth composition implementation attempt; no product edits; no real LINE interaction; no album-list prepositioning; no Phase A; no Phase B; no `live-preflight`/`live-execute`; no Save All; no destination confirmation; no budget reset; no worktree/git surgery.
