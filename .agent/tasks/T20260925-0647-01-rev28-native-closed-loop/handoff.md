# Handoff — Rev28 native closed-loop LINE album backup (post-CI pre-live finalization)

## TASK
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- STATUS: `PRE_LIVE_IMPLEMENTATION_READY` (task remains open; no production LINE run has occurred)
- PLAN_PATH: `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/plan.md`
- PLAN_REVISION: `3`
- PLAN_SHA256: `63b25602b215a3e9514fa76db8bd34c097f4bec40f370381d218c57f62745828`
- Stage-02 plan reviews attempt-05 / attempt-06 remain `PLAN_APPROVED` for that exact plan.
- INDEPENDENT_ACCEPTANCE_REQUIRED: YES
- E2E_REQUIRED: YES
- Production success remains `DUPLICATE_CONTENT_CONFIRMED`; CI/synthetic evidence alone can never satisfy it.

## GOAL_ANCHOR
Target: LINE group `旻謙允禎成長日記`, album `2024/05/13～05/17`, 57 photos. A successful production run requires exactly one Save All dispatch, exactly one destination confirmation, a fresh unique staging directory, 57 stable decodable files totaling 17,924,900 bytes, filename-excluded content multiset SHA-256 `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf`, and unchanged baseline tripwire `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`.

## CURRENT IMPLEMENTATION STATE
Branch: `rev28-prelive-finalization`.
Base/merge-base: `master` at `9db32f68d271272fd8ac5a6337522534e88d9ab2`.

### W1 — DONE
Native Swift package, executable-context capability probe, geometry/identity, ScreenCaptureKit, Vision wrapper and Quartz primitives remain intact.

### W2 — SYNTHETIC CALIBRATION COMPLETE
Items 1–4 and 6–9 retain their previously validated/frozen evidence. Item 5 is now closed without changing plan-time bounds.

Validated hosted macOS 27 item-5 freeze:
- GitHub Actions run `36124211295`, headed artifact `10859262043`, artifact digest `sha256:1fcd72a8f16f1e42d60aa190f81eebb4be10b7d098de4dc46bfad6814e29e3f2`.
- Harness run `HARNESS-20260925-103224`.
- `within=chooserVerified`.
- `timeout=noChooserObserved`.
- `late=chooserObservedAfterWindow`, affirmative non-nil.
- `monitorInputPosts=0`.
- 20 native NSOpenPanel latency samples; max 78.634977 ms, median 44.315100 ms, p95 78.634977 ms.
- Frozen bounds remain exactly 150 ms cadence through 8 s, then 500 ms cadence to 15 s hard cap; no bound was widened.
- `postcondition-bounds-v2.json` SHA-256 `14b45107ef9d9df2032575ff161fa08302ce81dd555d09cee9ef3df68ffbb7da`.
- `postcondition-latency-observations-v2.json` SHA-256 `74085354d27abe22f4aee39d92287ff91a589c6ea50007034a9b9371b88dad35`.
- `05-postcondition-proofs.json` SHA-256 `7088ae0021b78f2d3c834ba19e25bf626a9d63e0b1e9b895f51af134821cfc53`.

Root-cause repair: the late-affirmative fixture had placed the panel too close to the one forensic sample and concurrently ran a second diagnostic SCK/AX sampler. The fix preserves production semantics: the late panel is scheduled strictly after the hard cap with settling margin before the forensic sample, and the diagnostic sampler runs only after the monitor completes. No predicate, hard cap, cadence, requiredness, fallback or result meaning changed.

### W3 — IMPLEMENTED AND VERIFIED OFFLINE
- Native structural locators for album/detail/menu/Save All.
- Native album ellipsis locator porting reviewed v5 structural invariants.
- Candidates are bound to window ID + capture epoch + frame SHA; stale candidates refuse.
- Historical replay binds all 20 plan-selected fixtures by SHA-256 and verifies the reviewed album/menu/ellipsis/identity invariants.
- Replay is executed twice in CI and required to be byte-identical.

### W4 — IMPLEMENTED AND VERIFIED
- Persistent execution state transitions and dispatch budgets.
- Exactly-once Save All and destination confirmation.
- Global reversible ceiling 12; identical-blocker ceiling 3; two consecutive candidate-revalidation failures abort.
- Hash-chained intent ledger and observe-only crash recovery.
- Conservative Save All empirical-class evidence.
- Exact staging verifier with named outcomes, stability/quiescence checks, decodability, 57-file / 17,924,900-byte / content-multiset predicate.
- Postcondition monitor checks the monotonic deadline after sampler return so a slow sampler can never promote post-hard-cap evidence to in-window success.

### W5 — IMPLEMENTED AND VERIFIED
Canonical `G01–G22 + X01–X03` adversarial matrix: 25/25 tests PASS and is executed twice per deterministic CI job.

## CI EVIDENCE
Workflow: `.github/workflows/rev28-macos27.yml`, GitHub-hosted `xcode-27`.

Final hardening run `36124211295`: SUCCESS.
- Deterministic Swift contract: SUCCESS.
- Non-Vision deterministic suite: 87 tests / 0 failures.
- Adversarial matrix: 25 / 25, executed twice.
- Historical replay: 20 SHA-bound fixtures, executed twice, byte-identical.
- Headed macOS 27 core: Accessibility=true, ScreenCapture=true, PostEvent=true, ScreenCaptureKit=OK.
- W2 item 5: PASS.
- Hosted Vision remains unavailable with the bounded known `unknownError` signature for both production Swift Vision and the legacy parity diagnostic. CI now fails if the unsupported-Vision signature changes; production OCR requirements are not weakened.
- Earlier finalization run `36123508929` also passed, and its second independent rerun passed; item-5 max latencies were 108.05 ms and 108.36 ms respectively.

## REMAINING GATES
### Non-Mac governance gate
`V-09` still requires genuinely independent review of the exact frozen implementation/evidence (7 topic reviews + adversarial review + reconciliation-barrier supersession). This handoff and the implementing assistant are not claimed to be an independent reviewer. No Phase B may run without the required approval. If Phase A reveals LINE-specific facts that materially affect reviews 1/4/6, update/re-run those reviews before Phase B.

### Real Mac only
1. Reverify real executable-context TCC/AX/ScreenCaptureKit/Vision/Quartz; hosted Vision is not production authority.
2. Recompute accepted baseline path, 57-file count, 17,924,900 bytes, both baseline digests and mtimes; confirm fresh staging is empty/unique and arm the ledger.
3. Phase A read-only LINE reconnaissance using only frozen locators: verify real LINE process/window, group, album, `57張照片`, current geometry, popup/menu structure and chooser assumptions. Zero irreversible input.
4. Only after every interlock/review passes, Phase B: exactly one Save All and exactly one destination confirmation; never blind-retry an unknown irreversible result.
5. Wait for filesystem stability/quiescence and run exact staging/content verification. Only exact content equality may produce `DUPLICATE_CONTENT_CONFIRMED`.
6. Stage-05 independent acceptance recomputes the result from disk and verifies the baseline remained unchanged.

## STATUS
- PRIMARY_OUTCOME_STATUS: `NOT_ACHIEVED`
- IMPLEMENTATION_STATUS: `PRE_LIVE_READY`
- CORE_ACCEPTANCE_STATUS: `NOT_RUN`
- REQUIRED_VERIFICATION_STATUS: `PRE_LIVE_CI_COMPLETE; V-09_AND_LIVE_GATES_PENDING`
- INDEPENDENT_ACCEPTANCE_STATUS: `PENDING`
- TASK_CLOSURE_STATUS: `IN_PROGRESS`

## SAFETY INVARIANTS
No historical coordinate as live input; no fuzzy identity; fresh geometry/identity before dispatch; click return is never success; chooser must be directly affirmed; unknown irreversible outcome is never retried; baseline is read-only; old provisional item-5 v1 evidence remains append-only history and is not overwritten.

## NEXT ACTION
Use the PR exact head for V-09 independent review. After required review approval, move to the user's real Mac for preflight + Phase A. Do not run Phase B until all pre-live and Phase-A gates pass.

TASK_ID: T20260925-0647-01-rev28-native-closed-loop
PLAN_REVISION: 3
NEXT_STAGE: `V-09_REVIEW_THEN_REAL_MAC_PHASE_A`
