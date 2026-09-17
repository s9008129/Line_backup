# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 31
- REVIEWED_PLAN_REVISION: 21
- REVIEWED_PLAN_SHA256: 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190 (1,877 lines; verified before and after reading; snapshot byte-identical)
- PLAN_SNAPSHOT_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-31/plan_snapshot.md
- Repository anchor observed: branch master, HEAD 4b01522, working tree clean at review start; plan.md frozen during review (post-read SHA re-check = same)
- Reviewer runtime/model: Codex CLI agent (independent context; no Planner transcript loaded; informational only)
- Review inputs (order): H3.0 handoff + GOAL-vision-agent-next-conversation.md → independent GOAL_BASELINE → plan.md Rev21 (§21.1–§21.9 + prior sections) → focused read-only verification (v3 tool sources, Phase 0 baseline, frozen frames, v3 self-test runner, prior review attempts 28/29)

## OWNER_VERDICT
- 這版要做什麼：把「看圖讀字」的引擎從舊的 tesseract 換成 macOS 內建的 Vision（做成新的一整套 v4 工具），並用一個「不會亂跑、可重跑」的離線測試（C1–C5，四個已保存的畫面）證明原本卡住的 57 被讀成 75 的問題會消失。
- 真正必要的（CORE）：v4 讀取器＋三支新版工具、v4 自測矩陣、四個凍結畫面的 C1–C5（含 5 次重跑一致）、失敗 5 次即停；舊 v3/v2 工具、舊證據、57 張照片、正式資料全部不准動。
- 支撐性、不擋結案：建置紀錄、v4 說明文件、「即時看螢幕」那層明確不做（可能跳系統權限視窗、對證明沒幫助）。
- 什麼會卡住整套：只有上面 CORE 失敗才會卡；另外路線 attempt-05 的收尾（A 結案／B 再授權一次「⋮ 只觀察」）還是您未決的事，這版沒有偷做、也沒有替您決定。
- 設計是否過度：沒有。做法是「新目錄 v4＝舊 v3 邏輯＋只換讀取器，舊檔一字不動」，最安全也最可追；沒有新增第三方依賴。
- 最大風險：v4 自測只有 16 個合成案例（13 個舊案例＋3 個讀取器案例），證明「只有讀取器被換掉」的說法還缺一個「v4 與 v3 差異只落在讀取器」的稽核紀錄；另外「累計失敗 5 次」的計數規則、Phase 0 基線的一處數據小錯、測試輸出是否位元一致這幾點需要在交接/實作時寫精確。這些都不影響方向，屬於可修的收尾項。

## GOAL_BASELINE
Reconstructed from H3.0 + the command file before reading any Rev21 rationale (full text: `goal-baseline.md`, SHA-256 `93afcdf24f0304c04a9a5444fffb0331f69209b8cffac73ea2442e6b7e9d216f`):
- PRIMARY_OUTCOME (this wave): (G1) the official route-verification chain's OCR reader becomes macOS-native Vision (system frameworks only), delivered as a new versioned tool set that supersedes the v3 reader role while every v3 byte stays frozen; (G2) a bounded, offline, re-runnable agent acceptance test (C1–C5) proves Vision reads the key fields and that replaying the frozen S5 logic with Vision removes the attempt-05 `75≠57` blocker, with append-only JSON+SHA evidence and a 5-cumulative-failure stop.
- SUCCESS_EVIDENCE: C1–C5 green on the four durable frozen frames with raw readings and hashes; C2 deterministic repeats; C4 `DEMONSTRATION_ONLY`; v3 13-case matrix re-expressed green; helper-unavailable fail-closed exercised; no v3/v2 byte changed; route verdict untouched.
- MUST_NOT_BREAK: zero GUI input this wave; at-most-once + zero retry + no menu item (Save All) + no chooser/keyboard/AX write if ever authorized; zero images in conversation; destination/formal config/state/run-log read-only; 57 photos never re-downloaded; `禎` U+798E / `楨` U+6968 never merged; no historical coordinates; supplementary evidence never overturns frozen verdicts.
- OWNER-RESERVED: route attempt-05 closure (A `ROUTE_NOT_NEEDED` / B new revision + new one-shot ⋮ gate); agent must not act.
- NON_GOALS: GUI input, menu items, download/Save-All, route continuation under Rev21, live screen-capture layer, scope beyond the one album.
- CRITICAL_PATH: Phase 0 baseline (done, `adf1829`) → Rev21 plan → fresh double review → Stage 03 handoff binding v4 as official + frame SHAs + C1–C5 + stop rule + DEMONSTRATION_ONLY + route reservation → Stage 04 v4 tools/self-test/C1–C5 → Stage 05 independent re-run (INTEGRATION level, never live E2E).

## GOAL_ALIGNMENT
- PASS (verified). The wave's CORE items trace 1:1 to the owner's two goals. `REQ-VR-1/REQ-VR-2` = G1; `REQ-VR-3/REQ-VR-4` + `NFR-VR-1` = G2 plus the hard boundaries; `OOS-VR-1..4` mirror H3.0 §9's prohibitions and the owner-reserved route. `NFR-VR-2` (build record) and the v4 docs are correctly SUPPORTING/non-gating; the deferred live-capture layer is BEST_EFFORT with a recorded safety rationale (OS permission prompt) and cannot block closure.
- The wave is honestly scoped inside `PRIMARY_OUTCOME`: §21.1 states the album-data result (result ①) is not advanced; §21.6 keeps the two results separate; §21.7 tells the owner which item is still waiting on them. No supporting detail (helper build, README, live capture) has been promoted to the de-facto goal.
- No pre-claiming: the header's overall status block is the accepted prior-wave record, the Rev19 Stage-04 facts are explicitly labelled "not independently verified", and the Rev21 wave line is `UNKNOWN/NOT_STARTED/NOT_RUN/NOT_RUN/PENDING/IN_PROGRESS` with "never assumed here". Nothing in §21.1–§21.9 reports a result that does not yet exist.

## NECESSITY_AND_TRACEABILITY
| Element | Goal/decision contribution | Criticality | Veto | Missing/failure behavior | Rationale |
|---|---|---|---|---|---|
| `v4/vision_reader.py` + 3 v4 tools | G1 replacement | CORE | HARD_CLEAN | no wave acceptance | H3.0 §1/§6 |
| v4 self-test 16 cases | proves refusal matrix + reader-layer cases | CORE | HARD_CLEAN | wave not accepted | H3.0 §6 (13 cases), plan §21.4 |
| C1–C5 runner + append-only attempts | G2 proof | CORE | HARD_CLEAN | wave not accepted | H3.0 §8.1–§8.3 |
| 5-failure stop | owner bound | CORE (MUST_NOT_BREAK) | HARD_CLEAN | owner notification | H3.0 §8.2 |
| build record, v4 README | operability/reproducibility | SUPPORTING | NON_GATING | local degradation | §21.4/§21.6 |
| live capture layer | possible extra evidence | BEST_EFFORT | NON_GATING | deferred with rationale | §21.5, H3.0 §8.1 |

Every material new artifact maps to a goal or invariant; the deletion test removes nothing that acceptance needs. C4's `DEMONSTRATION_ONLY` label is necessary and present, so no frozen verdict is rewritten.

## GATE_AND_VETO_AUDIT
- All Rev21 global gates are CORE-by-construction (they gate the wave's own acceptance) and each failure mode is semantic: v4 toolchain presence/self-test, the C1–C5 acceptance, the helper-unavailable refusal path, and the v3-frozen-evidence check. None is a schema-completeness veto; none is waivable by an agent (`WAIVER_ALLOWED: NO`).
- `VISION_READER_FAILCLOSED_MATRIX` covers the one reader-specific safety risk this wave introduces (a new external process boundary: the helper binary). Its failure classification ("crash or guessed value is TASK_REGRESSION") is correct and independently motivated.
- Independence: C4 cannot flip any frozen verdict, cannot set `CUA_ROUTE_DECISION`, and cannot authorize the ⋮ input (§21.6). The route gate remains owner-reserved; Rev21 grants nothing over it (verified in §21.1/§21.6/§21.7 and the matrix row text).
- No supporting/best-effort element carries a global veto. `BASELINE_REGRESSION_DELTA` is HARD_CLEAN but its scope is "prior artifact signatures unchanged", which is a MUST_NOT_BREAK obligation, not a completeness gate.

## COUPLING_AND_FAILURE_CONTAINMENT
- The single intentional coupling is the one the owner asked for: v4 shares the v3 rule code and differs only in the reader (the count-region geometry derives from the OCR title bbox, so title-read and count-read are chained — this is exactly the v3 rule, and my independent replay of the frozen rules against Vision's line-level output confirms it holds on all four durable frames: post title + `57張照片` conf 1.00, pre title + count region read `57`, C4 replay verdict `ALBUM_OPEN_VERIFIED`).
- Failure containment: helper missing/failing degrades locally to empty words → frozen refusal paths (`TARGET_TITLE_NOT_FOUND(2)` / `INCONCLUSIVE(5)` / recorded `UNREADABLE`), never a guessed value and never a global stop of unrelated subjects. The route and the album-data result are untouched by any Rev21 failure path (separate status tuples).
- The 5-failure stop is the correct containment for the bounded loop; the loop has no model calls, so retries are only meaningful for process-level flakiness — see RV-31-1 for the counting precision.

## DESIGN_ECONOMY
- New moving parts: one reader module, three v4 tools (copies of v3 logic with the reader swapped), one v4 self-test, one agent-e2e runner + per-attempt evidence dirs. Each pays rent: the v4 copies preserve frozen-v3 reproducibility (the alternative, in-place editing v3, would break every recorded verdict binding), and the runner is the G2 deliverable itself. No new dependency, no new state machine, no service.
- Rejected alternatives are recorded (`DEC-VR-1`), and the deferred live-capture layer is explicitly excluded rather than half-built. The deletion test fails for nothing in the CORE set. Complexity verdict: minimal and repository-consistent.

## CRITICAL_PATH_AND_PRIORITY
- §Critical path items 8–9 put the reader/toolchain first, then the bounded agent test, then Stage 05 re-run — correct order (CORE first, no polish work ahead of it).
- The v4 self-test is a prerequisite to the wave acceptance (it is the refusal matrix proof), not a supporting extra; the agent test does not wait on the deferred live-capture layer. No priority inversion found. The route question is parked (owner-reserved) rather than silently worked around.

## REQUIREMENT_FIDELITY
- `REQ-VR-1` (new versioned tool set, system frameworks only, v3 bytes frozen): matches H3.0 §1/§6 and the command file's 「正式」 definition (the three v3 tools). The v2 side tools (`detect_menu_popup.py`, `locate_card_ellipsis.py`) are correctly left out of the official chain and untouched.
- `REQ-VR-2` (v4 preserves every v3 gating rule/verdict/exit code/geometric parameter; only the reader changes): the plan's description of v3 semantics is accurate against the actual sources (count classification `MATCH/MISMATCH/AMBIGUOUS_READ/UNREADABLE`, exit codes 2/4/5/6 and 0/3/4/5/6, conf never a gate, `禎/楨` preserved). See RV-31-2 for the missing audit of "only the reader changed".
- `REQ-VR-3/REQ-VR-4`: C1–C5 match H3.0 §8.1's C1–C5 one-for-one (count 57, ≥5 deterministic repeats, title on pre+post, frozen S5 replay, s1/s2 count) and the bounded loop matches §8.2. `NFR-VR-2` correctly makes the build record non-gating (binary bytes are measured non-reproducible: my own rebuild produced a third distinct binary SHA whose stdout on the frozen frames is still byte-identical — independent confirmation of the Phase 0 equivalence method).

## GROUNDING_AND_DRIFT
- Verified against the repository, not just asserted: plan SHA matches the brief; the four durable frames hash to the cross-check values; v3 tool SHAs + v3 self-test summary SHA match H3.0 §3; `attempt-05/album-open-verify.json` really does record `count_digits_read: "75"` / `TARGET_MISMATCH` with the same pre/post frame SHAs; the Phase 0 baseline is committed in `adf1829` with 15/15 handoff anchors matching; `agent-e2e/` and `tools/v4/` do not exist yet (append-only creation is a real add).
- Load-bearing claims I independently re-derived (not merely re-read): Vision helper rebuild + post-frame stdout byte-identical to the recorded raw stdout SHA; v4-shaped title/count rules on 3x line-level Vision output for pre/post/s1/s2; count-region reads at the v4-derived 10x count box (`57張照片` conf 1.00 post; `57` pre); frozen-rule replay verdict `ALBUM_OPEN_VERIFIED` exit 0; synthetic v3 self-test fixtures readable by Vision (card_ok title + count, album_ok title).
- See RV-31-3 (Phase 0 data error), RV-31-4 (Phase 0 "C1/C3/C5" are raw readings, not tool-level checks), RV-31-5 (baseline comparison key is the volatile /tmp path).

## ARCHITECTURE_AND_CONTRACTS
- Reader contract is well-defined: token unit = Vision observation line box (no re-tokenization), v3-shaped `{text, conf, x, y, w, h}` records divided by the scale, same scales/geometry as v3, conf recorded but never gated. The frozen rules consume this shape; the token-granularity difference vs tesseract is disclosed and was measured on all four frames.
- Interface edges: helper resolution order (`$VISION_OCR_BIN` → temp build → build from frozen source) needs one clarification for the set-but-invalid case (RV-31-7); the v4 `vision_reader.py` is a new module beyond v3's two-module layout — structurally additive, not a v3 rule change.
- Versioning: v4 delivered as new artifacts, v3 untouched; the Stage-03 handoff is the binding point that makes v4 the official reader, and any future route run needs a new revision + gate (owner-reserved). No migration, no compatibility break for frozen evidence.

## DATA_SECURITY_RELIABILITY
- No formal-data writes, no destination touch, no re-download; the only new writes are repo evidence artifacts. The helper is a local binary built from a frozen 1,070-byte source; no third-party dependency; no network.
- Fail-closed semantics are correctly inherited from v3 and stated: helper missing/unbuildable/non-zero/unparsable → empty words → documented refusal paths, never a guessed value. One pre-existing (v3-inherited) edge: an unreadable/corrupt frame file crashes with a Python traceback instead of a refusal path (independently reproduced on v3, exit 1 traceback). That is outside Rev21's reader-only scope — residual note only.
- Determinism: helper stdout byte-stable per input (Phase 0 5×; independently reproduced), v4 tool JSON contains no timestamp by design. Security/privacy: zero images in conversation, paths + SHA only; `禎`/`楨` never normalized.

## IMPLEMENTATION_SEQUENCE
- Stage 03 → 04 → 05 sequencing is correct and the wave-specific bindings for the handoff are named (v4 official reader, four frame SHAs, C1–C5, 5-failure stop, C4 label, route reservation, INTEGRATION mode, next unused e2e attempt number). Stage 05 is required to re-run the same frozen inputs rather than trust the Stage 04 summary.
- `E2E_REQUIRED: NO` with the INTEGRATION rationale is honest and matches H3.0 §10's "離線重跑屬 integration/contract 等級，不得冒充 live E2E". No Stage 04/05 state leaves a legal status combination uncovered: wave CORE fail → result ② open (FIX_REQUIRED-style routing via the canonical contract), acceptance-side blockage → scoped blockers, prior-wave facts preserved.

## TESTABILITY_AND_ACCEPTANCE
- C1–C5 are executable, judgment-pinned (tool-level rules, not raw conf), and all four inputs are durable and hashed at test start (mismatch = immediate stop). I independently executed the equivalent pipeline and reproduced the intended verdicts, so the acceptance target is reachable, not aspirational.
- The v4 self-test target (16 cases, `cases_failed: 0`) re-expresses the frozen 13-case matrix and adds the reader-layer cases; the one gap is the preservation audit (RV-31-2). The attempt-summary schema (`inputs_sent: 0`, `ui_interaction: none`, per-check raw command/exit/verdict, artifact SHAs, `failures_total`, `stop_reason`) is auditable and append-only.
- Minor precision gaps: C2's tool-JSON claim is not yet measured (RV-31-6), the summary-vs-raw determinism boundary needs one clarifying sentence (RV-31-6), and the selftest case list is named but not pinned by exact expectations (RV-31-9).

## SCOPE_AND_COMPLEXITY
- Scope stays inside the owner's one-album fence: no route continuation, no GUI, no download, no formal data, no v3/v2 edits, no new dependency, no bridge/service work. The only additive surface is evidence/artifact creation plus the v4 tool set. Complexity is proportionate; the alternative (in-place v3 edit) was explicitly rejected with a reproducible-evidence rationale.

## FINDINGS
- ID: RV-31-1 | Severity: MINOR | Category: TEST
  - Affected: §21.5 bounded loop / §21.6 / `REQ-VR-4`.
  - Evidence: [VERIFIED] by text; the plan says "the runner attempts each check once per attempt; cumulative failures are counted… at 5 cumulative failures the loop stops" but does not define whether the counter increments per failed check or per failed attempt, whether prior attempts' totals persist across separate runner invocations, or that checks are not re-run within an attempt.
  - Failure mechanism: a misread either stops the loop after one bad attempt (premature owner notification, wave stalled) or lets repeated invocations exceed the owner's 5-failure budget (violates the bounded-loop instruction).
  - Smallest correction: one sentence pinning `failures_total` = sum of failed check results across attempts (persisted by reading prior attempt summaries), no intra-attempt retry, stop evaluated before starting a new attempt.
- ID: RV-31-2 | Severity: MINOR | Category: TEST
  - Affected: §21.4 `REQ-VR-2` claim ("v4 preserves every v3 gating rule, verdict, exit code, refusal path and geometric parameter; the only semantic delta is the reader layer").
  - Evidence: [VERIFIED] the plan pins the 16-case matrix but no mechanism that verifies "only the reader changed"; the matrix covers behavioral paths, not code equality.
  - Failure mechanism: Stage 04 could silently alter a geometry constant or rule line while the 13 behavior fixtures still pass, producing a future route-run acceptance change that no Rev21 check detects.
  - Smallest correction: require Stage 04 to record a v4-vs-v3 structural diff audit (per tool: only the reader path/lines differ) into the v4 self-test evidence, and to re-express the 13 v3 expectations as the pinned literals unchanged.
- ID: RV-31-3 | Severity: MINOR | Category: DATA
  - Affected: §21.2 (Phase 0 baseline description).
  - Evidence: [VERIFIED] `evidence/20260917-vision-reader/phase0/baseline.json` → `helper_rebuild.byte_identical_to_recorded: true` while the same object records different binary SHAs (`ad140ef7…` vs `f54628e8…`) and the note/commit/plan text correctly say the binary is not byte-identical (equivalence is via stdout).
  - Failure mechanism: a later consumer reading that field could wrongly conclude the binary is byte-reproducible and re-run a binary-identity check that fails, or question the evidence record.
  - Smallest correction: record a one-line correction (baseline is frozen; note the field as an evidence-data error and rely on `raw_stdout_sha256` equivalence) in the Stage-03 handoff or a non-destructive addendum artifact.
- ID: RV-31-4 | Severity: MINOR | Category: GROUNDING
  - Affected: §21.2's "C1/C3/C5 sanity readings reproduce" vs §21.5's judgment column ("tool-level rule, unchanged from v3").
  - Evidence: [VERIFIED] Phase 0 reproduced raw readings; the plan's C1/C3/C5 are tool-level rules whose title/count/geometry path was not run in Phase 0. I independently executed the frozen rules against Vision's line-level output on all four durable frames and they do produce the intended outcomes, so the claim is reachable — but Phase 0 itself did not demonstrate it.
  - Failure mechanism: Stage 04/05 could cite Phase 0 as if it were a tool-level check, overstating pre-verification.
  - Smallest correction: state in the plan/handoff that Phase 0 reproduced raw readings only, and that the tool-level C1–C5 evidence is produced in Stage 04/05.
- ID: RV-31-5 | Severity: MINOR | Category: GROUNDING
  - Affected: §21.4 `BASELINE_REGRESSION_DELTA` ("post-change run must show UNCHANGED for every prior signature").
  - Evidence: [VERIFIED] the Phase 0 pre-change record keys per-frame results to `/tmp` paths (`frozen_frames_tmp`); those copies are volatile after reboot, and the post-change comparison must use the durable preservation copies (`evidence/20260917-vision-reader/frames/`).
  - Failure mechanism: after a reboot the baseline's comparison key is unavailable and the delta check degrades to partial/ambiguous.
  - Smallest correction: one sentence fixing the comparison key to the durable frame copies by SHA-256.
- ID: RV-31-6 | Severity: MINOR | Category: TEST
  - Affected: §21.3 determinism paragraph / §21.5 C2.
  - Evidence: [VERIFIED] the paragraph states the v4 tools' JSON "must also be byte-identical" (a requirement, fine) while C2's row describes both stdout and JSON checks; the tool-JSON half is not yet measured anywhere; the summary file itself contains a timestamp and runner argv, so "byte-identical" cannot apply to it.
  - Failure mechanism: ambiguity invites either an unverifiable claim or a false failure if the summary is included in the determinism comparison.
  - Smallest correction: state that C2 covers helper stdout + per-tool JSON only, and that the attempt summary is intentionally not part of the byte-identity comparison; mark the tool-JSON result as first measured at Stage 04.
- ID: RV-31-7 | Severity: MINOR | Category: SEMANTIC_CONTRACT
  - Affected: §21.3 helper resolution order / §21.4 helper-unavailable case.
  - Evidence: [VERIFIED] by text: if `$VISION_OCR_BIN` is set but nonexistent, the plan does not say whether the reader falls back to a temp-directory build or refuses; the self-test case must not silently rebuild and pass for a different reason.
  - Failure mechanism: the helper-unavailable test could exercise the build path instead of the refusal path, weakening the fail-closed proof.
  - Smallest correction: pin "set-but-invalid `$VISION_OCR_BIN` = no rebuild = empty words/refusal; `$VISION_OCR_BIN` unset may build once."
- ID: RV-31-8 | Severity: MINOR | Category: TEST
  - Affected: §21.3 fail-closed paragraph (reader failure classes).
  - Evidence: [VERIFIED] the paragraph lists helper missing/unbuildable/non-zero/load-failure/timeout/unparsable; for load failure (helper exit 3) the plan does not say the reader must record the helper's exit code/stderr into evidence before degrading to empty words, so a real Vision load failure would be indistinguishable from an empty read.
  - Failure mechanism: acceptance evidence loses the distinction between "reader failed" and "no text", which matters for Stage 04 debugging and for Stage 05 auditing.
  - Smallest correction: require the reader to return an outcome record (`ok | binary_missing | build_failed | nonzero_exit | unparsable | timeout`) with exit code/stderr path recorded in the tool JSON.
- ID: RV-31-9 | Severity: MINOR | Category: TEST
  - Affected: §21.4 v4 self-test strategy.
  - Evidence: [VERIFIED] the case list is named but the expected exit codes/verdicts per case are not pinned in the plan; only the v3 run_selftest source and summary hold the literals.
  - Failure mechanism: an implementer fighting a failing case could quietly adjust its expected value instead of treating it as a defect.
  - Smallest correction: cite the v3 pinned literals/summary SHA as the expectation source and state that v4 expectations equal them (reader-layer cases' new expectations stated explicitly).

No BLOCKER findings.

## REQUIRED_PLAN_CHANGES
None required for approval. RV-31-1…9 are non-gating precision/audit items; they should be absorbed into the Stage-03 handoff instructions (smallest path, no plan edit) so the implementer and Stage 05 get the exact semantics without a Plan revision. If the planner prefers, they may be folded into a later revision; none of them changes goal alignment, gating meaning, safety, compatibility, or acceptance.

## RESIDUAL_MINOR_NOTES
- Pre-existing (v3-inherited) crash edge, out of Rev21 scope: a corrupt/unreadable frame file produces a Python traceback (exit 1) rather than `BAD_FRAME(6)`; v4 must preserve v3 behavior, and this is a candidate for a future revision, not this wave.
- The header's overall `INDEPENDENT_ACCEPTANCE_STATUS: PASS` belongs to the e2e/attempt-05 (Rev18-era) acceptance; the Rev19 Stage-04 facts and the Rev20/attempt-05 route evidence carry no independent acceptance and are labelled as such. The Rev21 wave line correctly re-derives its own tuple; Stage 03 may want one explicit sentence that Stage 05's independent acceptance covers the then-current state including these prior-wave artifacts.
- The plan's "append-only" phrasing for new artifacts is accurate for edits/overwrites; Stage 04 must not treat "append-only" as forbidding the creation of new files, and must not run any in-place mutation of `evidence/20260916-route/tools/` (copy only).
- `evidence/20260916-route/tools/vision/` exists; `tools/v4/` and `agent-e2e/` do not yet exist — Stage 04 creates them, and the v4 file set must be SHA-pinned into its execution record (the plan pins the v3 frozen set but not the new v4 hashes).

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Stage 03 Handoff compiling handoff.md bound to TASK_ID T20260916-0102-01-line-backup-acceptance, PLAN_REVISION 21, SHA-256 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190 (this approval is invalidated by any later plan edit), carrying RV-31-1…9 as non-gating implementer/Stage-05 instructions and preserving the owner-reserved route decision.
