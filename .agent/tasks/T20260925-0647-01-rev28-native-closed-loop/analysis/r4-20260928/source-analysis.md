# Stage 01 evidence and current-source trace

TASK_ID: T20260925-0647-01-rev28-native-closed-loop  
ROLE: HIGH-REASONING PLANNER, not Implementer  
ANALYSIS_BOUND_HEAD: 67c4fad9f2dded272cc9720100b1a6958fe352da  
BRANCH: rev28-prelive-finalization  
DATE: 2026-09-28, Asia/Taipei

## 1. Authority and diagnostic limits

The first command sequence was pwd, short status, branch, fetch origin --prune, local HEAD, remote branch HEAD, log -15. Initial worktree was clean; both HEADs were the SHA above. No merge was needed. Current source, tests and this exact HEAD govern this analysis. Historical reports retain their original meaning and do not prove current readiness.

Read the installed ~/.codex/AGENTS.md, prompts/01b_debug_plan_prompt.md and policies workflow-routing, convergence-escalation, plan-review-gate, testing-verification, debugging-recovery, git-change-hygiene, high-risk-change and model-routing. Routing is CRITICAL. Stage 02 and Stage 05 independent review are mandatory. The line-album-backup skill was consulted for preservation/unknown-result constraints; its legacy visual execution procedure does not override this native Rev28 planning request.

Read R3 plan, current handoff/execution, six review attempts and their revision evidence, three handoff-history records, ARCHITECTURE.md and the source/test/tool/workflow paths below. R1 snapshots 01/02 are identical, R2 snapshots 03/04 identical, R3 snapshots 05/06 identical to the original canonical plan. Historical revision deltas are preserved in historical-plan-deltas.diff. There was no pre-existing progress.md, e2e/, escalations/, context.json or decision.md under this task at analysis start. No prior V4.3 attempt counters can be inferred from their absence.

This turn did not run live-preflight, live-execute, launch/activate LINE, send GUI input, request TCC, create a production transaction or alter baseline/staging. Native LINE observations remain future Phase A work. Filesystem reads establish baseline count/bytes/hashes/mtimes, not a new decoded or downloaded backup. Temporary Swift probes linked the current built Rev28Core objects; probe source is stored as .swift.txt outside the package. No product or test repair was made.

## 2. Four distinct subjects and causal evidence

| Subject | Exact conclusion | Evidence |
|---|---|---|
| SYMPTOM | StructuralLocatorsTests test target compilation fails: non-callable SurfaceBinding; missing ocr; contextual Equatable diagnostic. | test.log; CI failed log |
| ROOT_CAUSE of compile failure | Commit 0d373ae introduced tests that call the computed property binding as binding() and use undeclared ocr helpers instead of the existing item helper interface. | StructuralLocatorsTests.swift:7, helper declarations, new tests at 193/231; git show 0d373ae |
| CURRENT_BLOCKER | Deterministic Swift tests cannot execute at the bound HEAD. Build of product targets alone passes. | local build-result.json exit 0; test-result.json exit 1, no test execution |
| PRIMARY_OUTCOME_GAP | There is no reachable complete native production composition that can produce the required fresh download and filesystem proof. Fixing test helper names cannot connect the missing production path. | rev28ctl/main.swift:50–118; LiveExecutionEngine.swift; only FakeAdapter implementation in tests |

PRIMARY_ROOT_CAUSE is the incomplete integration contract: a native observation/session provider and real adapter have not been composed with the common engine, transaction owner, eligibility gates and final filesystem evidence. This is a source-proven implementation gap, not a claim about how LINE would behave after a real click. The cause of the historical Rev27 indeterminate semantic effect remains unresolved and is not rewritten.

The Equatable diagnostic does not prove a missing refusal enum case. StructuralLocatorRefusal.referenceStructureMismatch exists; the linked stability probe prints that member successfully. The primary compiler errors destroy contextual type inference in the new test expressions.

### Independent secondary defects, before any repair

1. **Date segmentation:** StructuralLocators.segmentAlbumCards -> isDateRangeTitle requires yyyy/mm/dd on both sides. The target's short end date and both new tests use 2024/05/13~05/17. segmentation-result.log shows short-end-date input yields zero card regions and unsafeGeometry; changing only the diagnostic input to a full end year yields two regions and a candidate. This is an additional current product defect, not evidence that the corrected XCTest suite passes.
2. **Stable interval:** StagingVerifier.isStable measures last minus first of the whole history, but compares only the last three signatures. stability-result.log reproduces true for an old different sample at t=0 followed by equal samples at t=10, 10.1, 10.2. The equal samples span 0.2 seconds, below the required 4. This is a false positive in the existing stable predicate; no production filesystem was changed to demonstrate it.

## 3. CI and local evidence

Latest inspected pre-live workflow run: https://github.com/s9008129/Line_backup/actions/runs/36411316643, bound HEAD, completed 2026-09-28T10:45:11Z, FAILURE. Provenance PASS, Rev28 build PASS, deterministic Swift tests FAIL at compilation. Adversarial/replay steps and the dependent headed job were skipped. Therefore there is no current headed Vision PASS or FAIL from this run. Historical hosted Vision unknownError is a separate limitation.

Local macOS 27.0 (26A428), Swift 6.3.3: xcrun swift build --package-path rev28 passed; xcrun swift test --package-path rev28 --filter StructuralLocatorsTests failed at compilation. The filter does not bypass compiling other test sources. Exact commands/times/exit codes are stored beside logs. No full-suite or real-Mac production PASS is claimed.

python3 -B rev28/Tools/verify_pre_live_provenance.py passed. It validates v3 evidence against HarnessCalibration source blob c411011b1b44b1efb614e000f526b2118f45d120 and historical implementation 2ecfeb9c1803d9ab184e69381b0a340e69bd46ea, run 36125874509, 20 latency samples. This is meaningful frozen sampler provenance; it is not validation of the new StrictPostconditionMonitor/native composer. A queried V09 run at e786aad also failed; no exact-current V09 approval has been established by this analysis.

## 4. Actual CLI call graphs

```text
rev28ctl live-preflight OR live-execute
  -> reject CI environment
  -> decode LiveConfig + one-shot authorization
  -> compare run/plan/source digest and installed PID bundle
  -> SCK inventory: exactly one main-window candidate
  -> active/frontmost + CG membership + AX trust
  -> IntentLedger -> PersistentTransactionOwner (no checkpoint URL)
  -> live-execute: unconditional refusal; no engine invocation
  -> live-preflight: rename one-shot to .consumed; output summary
```

The preflight command already creates authorization/ledger state and consumes a one-shot file. Its name is not a guarantee of read-only behavior. It does not capture a frame, run Vision or baseline verification, localize structures, collect a native tripwire journal, or emit a complete Phase A eligibility record. The CLI claims observed facts only at inventory level. This planner did not invoke it.

```text
LiveExecutionEngineTests.FakeAdapter
  -> LiveExecutionEngine.run
  -> eight establish(state) callbacks + owner ledger transitions
  -> actual readiness/Quartz gate with synthetic observations and counting sink
  -> fabricated chooser/tripwire artifacts
  -> prepare callback returning a digest
  -> actual confirmation gate with readiness=true and counting callback
  -> download/stability callbacks returning digests
  -> constructed successful StagingVerification
```

The common engine is real code and exercises parts of transaction policy. The test does not exercise StrictPostconditionMonitor, native chooser navigation, native tripwire collection or StagingVerifier as one composed path. Source search finds no concrete native LiveExecutionAdapter in Sources. Classification of live-execute: **B + C + D**, with **E as a coverage/composition divergence**: only injected tests currently enter the engine; the real entry point stops earlier. There is not a second complete production engine to compare as equivalent.

## 5. Required 34-point trace at the bound HEAD

Paths below are relative to rev28/Sources; line anchors identify current definitions, not comments as proof. “Exists” means a component is present, not that production reaches it.

| # | Surface | Current implementation and unresolved connection |
|---|---|---|
| 1 | Real LINE process | rev28ctl/main.swift:86 validates PID/bundle/active state. Rev28Core/Identity/WindowIdentity.swift ProcessInstanceID.current uses proc_pidinfo. CLI does not bind that full instance into a capture chain. |
| 2 | SCK / CG inventory | Rev28Core/Sensor/WindowSensor.swift:43,116 implement both. childWindows uses same-app overlap, not proven parent ownership. CLI only checks main candidate + CG membership. |
| 3 | Fresh frame | Sensor/FrameCapture.swift:179,196 uses real SCScreenshotManager. Returns CapturedFrameRecord without the retained image/bytes needed for same-frame OCR composition. |
| 4 | Geometry | FrameCapture + Geometry/Coordinates.swift have rulebook, bbox, sourceRect offset, independent scale, per-side residual checks. Actuation captureLive uses a separate unbound capture/configuration path. |
| 5 | Vision OCR | Perception/OcrEngine.swift implements accurate zh-Hant/en-US OCR and exact text. Not called by live CLI. |
| 6 | Group identity | StructuralLocators/engine constants contain exact 旻謙允禎成長日記; no production evidence chain establishes it. 禎/楨 must remain different. |
| 7 | Album identity | Perception/StructuralLocators.swift:150 exact title matching exists. verifyAlbumDetail:208 checks group/count, not date; composer must retain/reconfirm album identity across navigation. |
| 8 | 57 association | locateAlbumCard requires title/count within one supplied card region. It safely over-refuses multiple global matches, but has no native region provider. |
| 9 | Segmentation | StructuralLocators.swift:90/130 derives vertical bands from date anchors; short-end-date failure reproduced. Whole-width midpoint bands do not prove actual card bounds for unknown/multiple-column/truncated layouts. |
| 10 | Cross-card refusal | locateAlbumCard rejects title/count in different supplied regions; new tests fail to compile. Coverage must include actual segmenter and native card boundaries. |
| 11 | Ellipsis | Perception/AlbumEllipsisLocator.swift uses same-image pixels, compact triple/header constraints. No live caller establishes its image/identity association. |
| 12 | Menu / Save All | StructuralLocators.swift:232 requires exact five-row order, neighbor-derived safe region and addressable overlap. Menu bounds/rows are supplied; native extraction, v8 invariant parity and surface ownership are unproved. |
| 13 | ProcessInstanceID | Identity/WindowIdentity.swift implements PID + start seconds/microseconds. Real census must use it throughout, not only PID. |
| 14 | SurfaceBinding | Perception/StructuralLocators.swift binds bundle/process/window/epoch/frame hash. Useful immutable provenance, currently assembled by callers. |
| 15 | Candidate freshness | StructuralLocators.revalidate compares binding; Quartz ReadinessObservation.captureLive:190 independently recaptures, requires old PNG hash and reuses old epoch. Equal hash is not a fresh observation-chain proof. |
| 16 | Quartz | Actuation/QuartzActuator.swift:357 checks permit/process/frontmost before move/down/up. Lines 411–414 have no revalidation between mouseMoved and mouseDown; CG membership alone is not point occlusion/topmost proof. |
| 17 | Permit | DispatchReadinessGate:294 + ReadinessPermit:260 provide one-second single-use consumption. Public synthetic observations can mint permits; gate does not itself require the validated frozen capture record. |
| 18 | Transaction owner | Transaction/PersistentTransactionOwner.swift:131 owns state/intent/reversible records. Production constructor omits mandatory checkpoint policy; state and evidence validation need composition-level enforcement. |
| 19 | IntentLedger | Transaction/IntentLedger.swift provides hash chaining, locking, stale-writer detection, append/fsync and independent head anchors. Generic append is public; sole semantic ownership is not enforced by the type alone. |
| 20 | Save All intent | Owner.reserveSaveAll:239 and markSaveAllAttempted:251 persist before Quartz. Owner does not require saveAllLocated state or Phase B eligibility at reservation. |
| 21 | One Save All | Engine checks count==2 meaning one intent + one attempt, NOT two clicks. Actuator test sees three mouse events for one click. No production dispatch is currently reachable. A goal-level slot must prevent a new runID from resetting budget. |
| 22 | Strict monitor | Postcondition/PostconditionMonitor.swift:235 races sampler vs deadline; no observer error promoted to success. Native sampler absent; journal must be cumulative so overwritten latestTripwire cannot hide an earlier abort. |
| 23 | Chooser affirmation | Chooser/ChooserAffirmationPredicate.swift derives strict production v2 and evaluates SCK/CG/newness/AX/owner facts. Owner rehashes JSON but does not independently reconstruct the native predicate/freshness facts. |
| 24 | Tripwire | Transaction/TripwireAttribution.swift has pure L1/L2/L3 classification; no real filesystem event collector/attribution journal was found. BaselineVerifier exists but CLI/engine do not call it. |
| 25 | Chooser continuity | Predicate evaluates census/start/bundle/signature continuity. rev28ctl/ProcessIdentity.swift has a harness fallback to the driver's signature; production must never substitute that for an unreadable target signature. |
| 26 | Destination preparation | Chooser/FolderChooserDriver.swift:228 guards before/after navigation but reevaluates the same candidate; focused field and reflected path can come from different app windows; one budget record wraps multiple inputs without per-input validation. |
| 27 | Confirmation intent | GatedDestinationConfirmation.perform:76 does check -> reserve -> attempt -> check -> dispatch. Good durable boundary; eligibility, exact panel and destination binding must precede it. |
| 28 | One confirmation | confirmDefaultButton:283 searches first matching button across app windows; uniqueness and exact candidate window/path association are not established. Must choose one AXPress path with no Return fallback in production. |
| 29 | Staging verification | Verification/StagingVerifier.swift:126 checks count/bytes/hash/regular/decodable data. Native engine adapter never invokes it at present. Snapshot reads metadata/hash/decode separately, allowing mixed file generations. |
| 30 | Stability/quiescence | StagingVerifier.isStable:166 has the reproduced interval bug. Production must use stable snapshots rather than verify(single snapshot). |
| 31 | Content multiset | StagingVerifier.contentMultisetDigest:91 implements sorted hash lines without trailing newline. Correct primitive; fake adapter constructs expected output instead of recomputing files. |
| 32 | Crash/restart | Owner nonempty ledger -> observe-only. Checkpoint optional; empty ledger path skips existing anchor verification. CLI preflight creates nonempty state, conflicting with subsequent execution. No goal-wide durable identity binding prevents replacement authorization/run path. |
| 33 | Append-only evidence | BoundEvidenceDigest rehashes run-scoped bytes, ledger anchors exist. Most engine states accept only a syntactically valid SHA string; missing typed raw evidence and no engine finalization/baseline recheck/empirical record invocation. |
| 34 | Independent recomputation | Hash algorithms/reference exist. No complete live run manifest + finalized ledger + independent recomputation tool is composed. Stage 05 cannot accept a fake verdict or prior execution.md claim. |

## 6. Single authority answers

**Transaction authority: partially implemented, not demonstrated end to end.** PersistentTransactionOwner + ledger are the intended common authority. The current CLI never executes the engine, omits anchors, consumes authorization during preflight, and does not enforce an eligibility state. Public ledger mutation/high-level adapter callbacks can bypass semantic evidence checks. LiveDispatchBudget is a separate pure policy model; production must not let it become a second counter authority. Required R4 resolution: one persistent goal slot, one owner/ledger and mandatory independent anchor, all budgets/phase/state/evidence checked there.

**Observation authority: absent as a coherent production session.** WindowSensor, FrameCaptureService, OCR, captureLive and chooser helpers acquire or accept facts independently. There is no retained exact-image observation bundle joining process instance, pre/post inventories, geometry, frame hash, OCR, candidate, AX, tripwire cursor and monotonic deadlines. R4 must define this composition, not approve comments asserting freshness.

## 7. Recent-commit assessment

| Commit/concept | Evidence-based assessment |
|---|---|
| 0d373ae tests; 2419315 segmentation | Intent is useful cross-card safety. Helper mismatch breaks test compile; date parser rejects the intended target representation. No reason to remove the tests or weaken cross-card refusal. |
| 67c4fad destination preparation | Adds a guarded public reversible path. Does not make every inner AX/key operation bound to a newly observed unique chooser; requires integration hardening before production. |
| 335d2f7 engine; e786aad integration tests | Common owner/state orchestration exists, but real CLI never calls it; test success uses synthetic high-level observations. |
| 730e848 persistent transitions | Improves durable state recovery over separate state.json; this is a load-bearing change from R3 and needs explicit authority/anchor/resume semantics. |
| 31f404c readiness exposure | Exposes captureLive/mint seam; does not connect the frozen capture rule to same-frame native OCR/candidates. |
| 8f278b8/f305c23 baseline verifier/tests | Adds correct reusable fail-closed baseline comparison. Still not on live CLI/engine path. |
| 86fe341/953da85/fb6c1e7 evidence layout | Moves evidence outside staging, avoiding extra-file failure. Production must enforce canonical disjoint roots and run binding, not caller convention. |
| 1dec6e5/e003174 derived predicate | Stricter v2 derived from frozen artifacts preserves old files. Exact inputs and derivation must be hash bound; derivation is not real LINE chooser validation. |

## 8. Plan decision and evidence scope

PLAN_REVISION_REQUIRED. R3 product outcome remains correct. Its execution assumptions do not: state.json versus ledger authority, Phase A authorization consumption/resume incompatibility, missing native session, independent readiness captures, and partial high-level engine tests require explicit design decisions. The compile defect alone would not justify revising semantics; these architecture facts do.

The previous handoff is STALE / SUPERSEDED_CANDIDATE for future execution, recorded in decision.md without changing historical bytes. R3 is archived byte-identically in plan-history; original review attempts stay untouched. R4 is an unapproved candidate. Fresh Stage 02 must assess both the new architecture contract and retained outcome constraints before Stage 03 creates a new handoff.

Planner diagnostics establish a shorter route: restore compilation; prove parser/stability repairs; build one native composition with OS-boundary injection; validate authority/observation invariants; Phase A real-Mac evidence; all exact-bound gates; one conditional Phase B; independent filesystem recomputation. “All tests green” alone never closes the primary outcome.
