# Plan Review Report

## REVIEW_METADATA
- TASK_ID: T20260916-0102-01-line-backup-acceptance
- REVIEW_ATTEMPT: 30 (fresh independent Stage-02 review; attempt-31 is a parallel reviewer's directory and was neither read nor touched)
- REVIEWED_PLAN_REVISION: 21
- REVIEWED_PLAN_SHA256: 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190 (1,877 lines / 260,774 bytes; recomputed from `plan.md` before the full read and re-verified byte-for-byte after writing this report; identical to the task-provided hash)
- PLAN_SNAPSHOT_PATH: `.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-30/plan_snapshot.md` (byte-exact copy; snapshot SHA-256 re-verified = `466bda4a…`)
- Reviewer-derived goal baseline: `.agent/tasks/T20260916-0102-01-line-backup-acceptance/review/attempt-30/goal-baseline.md` (written before reading the Rev21 rationale; SHA-256 `1ada100e…`)
- Repository anchor observed: branch `master`, HEAD `4b01522`, worktree clean apart from the untracked `review/attempt-30/` and `review/attempt-31/` directories
- Reviewer runtime/model: fresh Codex CLI Stage-02 session (model identity not exposed to this session; informational only)
- Read-only honored: no GUI input of any kind, no network use, no product code / tool / evidence / `plan.md` mutation, no commit; writes confined to `review/attempt-30/` (`goal-baseline.md`, `plan_snapshot.md`, `review_report.md`)

## OWNER_VERDICT
（白話）你要的兩件事都對上了：把正式驗證鏈的讀字引擎由 tesseract 換成 macOS 內建 Vision，並且加一個「不會亂跑、可以重複驗證」的 AI Agent 離線測試，證明 attempt-05 卡住的「57 被讀成 75」是舊引擎的問題、不是資料問題。這版唯一會擋結案的是 CORE：新版 v4 工具組＋16 案自測全綠，以及四個已凍結畫面（點擊前、點擊後、兩張裁切）上的 C1–C5 全部通過。不擋結案的：建置紀錄、說明文件、以及「即時看目前螢幕」那一層（明確延後，理由：可能跳出系統權限視窗、且對證明沒幫助）。失敗累計 5 次就停、留證據、通知你；不會無限重試。這版刻意不做：任何點擊（含 ⋮）、任何選單、鍵盤、AX 寫入、下載；不碰 57 張與正式資料；不改舊版工具、舊自測與任何舊證據。路線 attempt-05 的收尾（A 結案「不需要」／B 再開一次 ⋮ 觀察）仍然保留給你，這版沒有替你決定。審查結論：方向正確、設計最小（只換讀取器一層、其餘規則原封不動）、gating 誠實（INTEGRATION 等級、不冒充 live E2E、C4 標示 DEMONSTRATION_ONLY）；沒有 BLOCKER／MAJOR，只有 6 條不影響安全與驗收的 MINOR（見 FINDINGS），不需要再改計畫就能交付 Handoff。

## GOAL_BASELINE
Independent reconstruction from the authoritative owner sources (H3.0 §1/§8.1/§9/§11, the `GOAL-vision-agent-next-conversation.md` 【任務】【範圍】【硬性禁令】【路線待決】), written before adopting the Plan's framing; full text in `review/attempt-30/goal-baseline.md`. In brief:
1. PRIMARY_OUTCOME (two mandatory owner objectives): (a) replace the tesseract reading role used by the three frozen v3 tools with macOS-native Vision (`VNRecognizeTextRequest`) — explicitly a semantic change on the full CRITICAL path; (b) build a bounded, re-runnable, append-only AI-agent test proving the Vision reader is more reliable on the key fields (date title, photo count, group name) and that the frozen "75≠57" blocker disappears offline on the frozen frames (formal acceptance semantics defined by Rev21; C1–C5 as the starting point).
2. Success evidence: C1/C5 count = 57 where tesseract read 75/27/5; C2 determinism (N≥5 identical); C3 title `2024/05/13~05/17` on pre and post; C4 frozen S5 replay reaches `ALBUM_OPEN_VERIFIED`, marked DEMONSTRATION_ONLY; Stage-05 independent acceptance; INTEGRATION-level offline replay never passed off as live E2E; three results reported separately (album data / reusable capability / closure).
3. Must-not-break: fail-closed semantics and frozen verdicts (attempt-05 `TARGET_MISMATCH` never overturned by supplementary evidence); 57 files and formal config/state/run-log read-only; zero GUI input without a new explicit owner gate (at-most-once, zero retry; never a menu item, especially Save All; no chooser/keyboard/AX write); zero conversation images (paths + SHA-256 only); `禎` U+798E never merged with `楨` U+6968; no historical coordinates; no third-party dependencies; append-only evidence.
4. Owner-reserved: the route closure choice A/B — not to be taken by any agent. Scope fence: one album only; album-card GUI budget spent (1/1); ⋮ unspent but precondition unmet.
5. Bounded autonomy: 5 cumulative failures → stop, record, notify; escalate on semantic overreach / self-verification concerns / same root cause failing twice / any new GUI need / any thought of touching the 57 files.

## GOAL_ALIGNMENT
- A1 (intent): Rev21 is exactly the owner's two objectives, delivered as a new wave on the same TASK_ID. `PRIMARY_OUTCOME` is explicitly unchanged; the wave adds CORE only for the **reusable-capability** result (result ②) and states honestly that the album-data result (result ①) is not advanced (§21.1). No supporting detail has become the de facto goal. [VERIFIED against H3.0 §1 and the plan's own goal contract]
- A2 (acceptance proves outcome, not completeness): C1/C5 assert the count where the frozen tesseract failed (`75`/`27`/`5`); C3 asserts the title on both frames; C4 replays the frozen S5 logic and reaches `ALBUM_OPEN_VERIFIED` (labelled DEMONSTRATION_ONLY, never flipping the frozen verdict or `CUA_ROUTE_DECISION`); C2 measures byte-identity. The v4 16-case self-test proves rule preservation rather than mere presence. [VERIFIED]
- A3 (truthfulness of the blocker premise): the "reader artifact, not data" claim is durably grounded: on the same frozen post frame, `album-open-verify.json` records `count_digits_read: "75"`, `verdict: TARGET_MISMATCH`, while the frozen-source helper reads `57張照片` conf 1.00 (Phase 0 `readings/post.txt`, SHA equal to the recorded stdout). [VERIFIED]
- A4 (no scope drift): OOS-VR-1..4 (GUI/menu/chooser/keyboard/AX/download; v2/v3 modification; route closure; live capture) match H3.0 §9 and the owner's command file verbatim; the route stays stopped and owner-reserved. [VERIFIED]

## NECESSITY_AND_TRACEABILITY
| Wave element | Trace | Class |
|---|---|---|
| v4 tool set (`vision_reader.py` + three tools) replacing only the reader layer | REQ-VR-1; H3.0 §1 objective one; §6 call-point inventory | CORE / OUTCOME |
| preservation of every v3 gating rule, verdict, exit code, refusal path, geometric parameter | REQ-VR-2; H3.0 §5.3 ("no ad-hoc threshold relaxation") | CORE / MUST_NOT_BREAK |
| bounded agent-e2e runner + C1–C5 + append-only attempts (JSON+SHA, `SHA256SUMS`) | REQ-VR-3; H3.0 §8.1/§8.3; GOAL 【任務】 objective two | CORE / OUTCOME |
| 5-cumulative-failure stop + stop evidence + owner notification; no long retry | REQ-VR-4; H3.0 §8.2; GOAL 【任務】 | CORE / MUST_NOT_BREAK |
| v4 self-test: 13-case v3 matrix re-expressed + normalization, helper-unavailable fail-closed, determinism probe (16 cases) | REQ-VR-2 + §21.3 fail-closed contract; H3.0 §6 (self-test must be re-run after a reader change) | CORE |
| Phase 0 committed baseline + four durable frame copies | makes C1–C5 re-runnable after a reboot (H3.0 §8.1 "可在隔離環境重跑") | CORE (evidence substrate) |
| v4 README + helper build record | NFR-VR-2 | SUPPORTING (explicitly non-gating) |
| live screen-capture layer | OOS-VR-4, deferred with recorded rationale (possible OS permission prompt; no evidential value; route stopped) | OOS / non-gating |
Nothing material is untraceable; nothing in the CORE set lacks an owner/safety trace. [VERIFIED]

## GATE_AND_VETO_AUDIT
- The four new Status-Contract rows (`VISION_READER_TOOLCHAIN_V4`, `VISION_AGENT_E2E_C1_C5`, `VISION_READER_FAILCLOSED_MATRIX`, `V3_FROZEN_EVIDENCE_UNCHANGED`) are CORE with `WAIVER_ALLOWED: NO`, `WAIVER_AUTHORITY: NONE`, `CLOSURE_GATE: HARD_CLEAN`, and explicit failure-classification rules; they follow the v4.2 matrix schema and admit no self-waiver. [VERIFIED]
- Gate proportionality: the two OUTCOME gates exist because the wave's deliverable **is** the reader replacement and its proof; the two MUST_NOT_BREAK gates protect the frozen chain (any byte change to v2/v3 artifacts, or a crash/guessed value on reader failure, invalidates reproducibility or fail-closed semantics). No low-value supporting item holds a veto. [VERIFIED]
- No new global veto: `NFR-VR-2`, the v4 docs and the deferred live-capture layer are explicitly non-gating, and no supporting failure may mask a CORE failure (§21.6). [VERIFIED]
- C4 containment: DEMONSTRATION_ONLY — cannot set `CUA_ROUTE_DECISION`, cannot authorize the ⋮, cannot change §20.3 routing; the route remains stopped with `owner_decision_required: true`. [VERIFIED]
- Honest acceptance mode: `E2E_REQUIRED: NO` unchanged for the primary object; the wave is `ACCEPTANCE_MODE: INTEGRATION` (offline replay over durable frozen artifacts) and §21.5/§21.6 plus the Runtime-route section (plan.md:1735) all say it is never reported as live E2E. [VERIFIED]
- Bounded loop is CORE (REQ-VR-4) — correct, since unbounded autonomy is the very thing the owner forbade. [VERIFIED]

## COUPLING_AND_FAILURE_CONTAINMENT
- Reader failure is contained at the narrowest safe boundary: helper missing/unbuildable, non-zero exit, load failure, timeout, or unparsable output yields no words / an empty region read and then follows the frozen refusal paths (`TARGET_TITLE_NOT_FOUND(2)`, `BAD_FRAME(6)`, or a recorded `UNREADABLE` count that never refuses) — never a crash, never a guessed value; mirrored by a v4 self-test case and the fail-closed status row. [VERIFIED design]
- The v4 set is self-contained (sibling-loading inside `v4/`; never imports v3), so no cross-version coupling; the v3 files stay byte-identical history. [VERIFIED plan text]
- Result subjects stay separated: a wave CORE failure keeps result ② open and never rewrites result ① facts. [VERIFIED]
- Baseline guard: the wave's pre-change baseline is the committed Phase 0 `baseline.json` + four frame SHAs; the post-change run must show `UNCHANGED` for every prior signature (v3 tool SHAs, v3 self-test summary, route evidence SHAs) and may not silently omit any. Note `plan.md` itself legitimately changed (Rev20 `4919d871…` → Rev21 `466bda4a…`) and is correctly excluded from the UNCHANGED set. [VERIFIED]

## DESIGN_ECONOMY
- Exactly one semantic delta (which reader produces the token stream); everything downstream is frozen. [VERIFIED]
- v4-as-copy rather than in-place v3 edit preserves the reproducibility of every recorded frozen verdict and the append-only rule; the rejected alternative is recorded (`DEC-VR-1`). This is the minimal safe way to keep v3 SHA-bound. [VERIFIED]
- Reusing the already-frozen Swift helper (rather than writing a second helper) keeps the measured artifact identical to the one in the durable crosscheck and avoids a new third-party-free-but-unmeasured component; the Python layer does only scaling + parsing. [VERIFIED]
- Each of the three added reader-layer self-test cases maps to a distinct claim that needs proof (normalization, fail-closed, determinism); the 13-case re-expression is the cheapest proof of rule preservation. [VERIFIED]
- Deferred live capture costs nothing (it could not add evidence for C1–C5 claims and risks an unbidden OS prompt). [VERIFIED]

## CRITICAL_PATH_AND_PRIORITY
- Critical-path items 8-9 put the reader swap + v4 self-test first, then the bounded agent acceptance; no supporting item precedes or blocks a CORE item. [VERIFIED]
- Phase 0 (read-only baseline) is complete and committed (`adf1829`); this review independently re-ran the essential checks (see GROUNDING_AND_DRIFT) — the CORE path starts from verified ground. [VERIFIED]
- No priority inversion: docs/build record/live capture are non-gating; the route closure is frozen and out of scope until the owner answers. [VERIFIED]

## REQUIREMENT_FIDELITY
- `REQ-VR-1..4`, `NFR-VR-1..2`, `OOS-VR-1..4` map 1:1 onto the owner direction; class labels match real gating. [VERIFIED]
- H3.0 §9's prohibitions are carried into OOS-VR-1/2 and the §21.3 reader contract (no case folding, no width normalization, no `禎`/`楨` merge, no historical coordinates; zero images in the conversation). [VERIFIED]
- C1–C5 match H3.0 §8.1's suggested criteria with the promised Rev21 refinements: C2 defines determinism strictly (helper stdout bytes + v4 tool JSON bytes identical across 5 repeats; no conf-jitter allowance) and records conf as evidence only, never as a gate; C3 keeps a digit-token rule with bbox recorded. [VERIFIED]
- The v4 self-test target (`16` cases, `cases_failed: 0`) is an explicit superset of the frozen 13-case matrix; no frozen rule is loosened or tightened. [VERIFIED]
- Coverage note (RV-30-3): H3.0 §1's reliability claim names three key fields (title, count, group name); C1–C5 cover title/count only — faithful to H3.0 §8.1, and no frozen gating rule consumes the group name, but the gap deserves one clarifying sentence.

## GROUNDING_AND_DRIFT
Independent read-only re-verification performed by this review:
- `plan.md` SHA-256 before and after the full read = `466bda4a…` (unchanged); snapshot byte-identical. [VERIFIED]
- Phase 0 `baseline.json`: `handoff_sha_table` has 16 rows, 14 with a recorded SHA-256, and `handoff_sha_mismatches: []` — all 14 recorded anchors matched at recording time; re-hashed now, 13 still byte-identical and the 14th is `plan.md` itself (legitimately advanced to Rev21). The header/§21.2/requirement-table figure "15/15" does not reconcile with any defensible count → RV-30-1. [VERIFIED]
- Frozen frames: all four committed copies re-hashed = recorded values; `manifest.json` matches; baseline records 5 identical runs per frame with per-run stdout SHA equal to the recorded crosscheck stdout SHAs (post `5c86dda8…`, pre `07e3e156…`, s1 `561bb131…`, s2 `abf9d75e…`), and each frame's recorded SHA matches the attempt-05 crosscheck values. [VERIFIED]
- The §21.3 claim "measured conf 1.00 at 3x/6x/10x on the post frame": this review rebuilt the helper from the frozen Swift source and re-ran the post frame at 3x/6x/10x — `57張照片` conf 1.00 at all three (title also conf 1.00). The claim is true but is not itself durably recorded → RV-30-4. [VERIFIED by reviewer re-run]
- Frozen S5 blocker: `album-open-verify.json` records `count_digits_read: "75"`, `count_box [9,109,177,139]`, `verdict: TARGET_MISMATCH`; `run-ledger.json` records `STOPPED_AT_S5_TARGET_MISMATCH`, `CLOSED_AFTER_INPUT_1`, `owner_decision_required: true`, and its `handoff_sha256` equals the Stage-03 handoff `ab88e496…`. [VERIFIED]
- `vision-ocr-crosscheck.json` stays `SUPPLEMENTARY_NON_AUTHORITATIVE`; nothing in Rev21 promotes it, and C4 keeps the frozen v3 verdict intact. [VERIFIED]
- Rev20 approvals: `review/attempt-28` and `review/attempt-29` both end `PLAN_APPROVED` bound to `4919d871…`; the header records exactly this and states no approval exists for Rev21. [VERIFIED]
- `phase0/baseline.json` `helper_rebuild.byte_identical_to_recorded: true` is computed by `phase0_baseline.py` as `sha256(/tmp/vision_ocr) == f54628e8…` — a survival check of the **recorded volatile binary**, not a claim that the **rebuilt** binary (`ad140ef7…`) is byte-identical. The plan's prose is correct (rebuild is not byte-identical; equivalence established via recorded stdout bytes); the field name invites misreading → RV-30-6. [VERIFIED]
- Stale numbering literals: lines 257/259/270/278/334/380/389/403/417 still bind the (never-executed, owner-reserved) route-closure re-derivation to "Stage 05 attempt-06", while §21.6 assigns `e2e/attempt-06` to this wave's Stage 05 and "the number after it" to a later route closure → RV-30-2. [VERIFIED]

## ARCHITECTURE_AND_CONTRACTS
- The reader contract is precise and implementation-ready: v3-shaped word records `{text, conf, x, y, w, h}` in original-frame coordinates (pixel values divided by scale), line-level token unit with no re-tokenization; scales/geometry pinned (frame reads 3x LANCZOS, count region 10x — verified as the v3 `ocr_words(scale=3)` / `ocr_digits_region(scale=10)` parameters); helper resolution order pinned (`$VISION_OCR_BIN` → temp build path → build-once from the frozen Swift source with path/size/SHA recorded in the emitted result). [VERIFIED]
- Fail-closed contract enumerates the exact frozen refusal codes. [VERIFIED]
- Backward compatibility: no v2/v3 byte touched; the official chain is redefined to v4 from Rev21 onward via the Stage-03 handoff, and any future route run must use v4 under a new gate (`DEC-VR-1` rationale). No schema/migration/contract consumed outside this repository. [VERIFIED]

## DATA_SECURITY_RELIABILITY
- Zero formal-data writes; zero GUI input; zero third-party dependency (system frameworks only); zero conversation images (paths and SHA-256 only); no network requirement. [VERIFIED as plan contract]
- Append-only evidence (per-attempt directories with `summary.json`, `raw/*`, `SHA256SUMS`; never rewritten or deleted), bounded loop with stop evidence, immediate stop on input-hash mismatch at test start. [VERIFIED]
- `禎`/`楨` never merged; no width/case normalization; no historical coordinates. [VERIFIED]
- Determinism is measured (C2) rather than assumed; `conf` is recorded evidence and never a gate. [VERIFIED]
- Residual reliability detail: C2's byte-identity requirement vs volatile fields in the emitted tool JSON (helper build path, temp PNG path) — implementable, but should be pinned in words → RV-30-5.

## IMPLEMENTATION_SEQUENCE
- Stage 03 must compile a fresh handoff bound to TASK_ID + Rev21 + approved SHA carrying, additionally, the v4-as-official-reader definition, the four frame SHAs, C1–C5, the 5-failure rule, the C4 DEMONSTRATION_ONLY label, and the owner-reserved route decision — all recorded in §Closure and sequencing. [VERIFIED]
- Stage 04 order (build v4 set → v4 self-test green → agent-e2e attempts → `execution.md` statuses) is CORE-first and executable; Stage 05 independently re-runs the same frozen inputs and consumes the next unused task e2e attempt (06). [VERIFIED]
- The only sequencing wrinkle is the stale route-closure attempt-06 literals (RV-30-2); this wave's own number is unambiguous (§21.6).

## TESTABILITY_AND_ACCEPTANCE
- Every CORE claim has an observable, tool-level check with raw evidence + SHA table: C1/C5 (digit read contains `57` where the frozen tesseract read `75`/`27`/`5`), C3 (title rule on both frames, bbox recorded), C2 (5 repeats: helper stdout bytes identical and v4 tool JSON bytes identical per input), C4 (frozen S5 replay → `ALBUM_OPEN_VERIFIED` exit 0, recorded next to the frozen `TARGET_MISMATCH`), v4 self-test (16 cases, `result: PASS`, `cases_failed: 0`). Inputs are re-hashed at test start with immediate stop on mismatch. [VERIFIED design]
- Acceptance = one all-five-PASS agent attempt + green v4 matrix; Stage 05 independently re-derives the tuple — appropriate for `ACCEPTANCE_MODE: INTEGRATION`, truthfully labelled and never presented as live E2E. [VERIFIED]
- Residual test-design details: C2 byte-identity wording (RV-30-5) and the group-name coverage note (RV-30-3, non-gating).

## SCOPE_AND_COMPLEXITY
- Scope fence holds: one album; toolchain-only change; destination read-only; no download; no third-party dependency; new-versioned-artifacts-only. [VERIFIED]
- Deletion test: removing any of the four v4 tools, any of the three added self-test cases, or any C1–C5 check would remove a CORE proof; nothing else is built. No over-engineering found. [VERIFIED]

## FINDINGS
All findings are MINOR, non-gating, and none affects goal alignment, implementation feasibility, safety, compatibility, rollback or acceptance.

- `RV-30-1` — [MINOR][GROUNDING] Anchor-count figure "15/15" (plan.md header line 22, §21.2 first bullet, §Requirement table row 1543). Evidence: committed `phase0/baseline.json` `handoff_sha_table` contains 16 rows of which **14** carry a recorded SHA-256, all matching, `handoff_sha_mismatches: []` (plus 2 informational rows with `recorded_sha256: null`); no defensible reading of H3.0 §3+§6 yields 15. Mechanism: the most-read lines state an unreconcilable number, inviting doubt in otherwise-solid baseline evidence and a mismatch when Stage 05 re-derives the count. Smallest correction: read "14/14 recorded SHA-256 anchors" (or "all recorded §3 anchors, zero mismatches") in those three places.
- `RV-30-2` — [MINOR][SEQUENCING] Stale numbering literals for the route closure: plan.md lines 257/259/270/278/334/380/389/403/417 still say the (never-executed, owner-reserved) route-closure re-derivation happens at "Stage 05 attempt-06", while §21.6 now assigns `e2e/attempt-06` to **this wave's** Stage 05 and "the number after it" to a later route-closure acceptance. Mechanism: after this wave uses 06, a future authorized route-closure revision could follow the older literal and collide, or a reader could hesitate between the two rules. §21.6's next-unused rule is explicit and governs, so this is documentary. Smallest correction: one supersession sentence (e.g., in §21.6 or §21.8) that every earlier "Stage 05 attempt-06" reference is superseded by the next-unused rule (route closure, if ever authorized under a new revision, takes 07).
- `RV-30-3` — [MINOR][TEST] Key-field coverage: H3.0 §1's reliability claim names three fields (date title, photo count, **group name**); C1–C5 (faithful to H3.0 §8.1's suggested list) cover title and count only, and Phase 0 records the group-name readings (native 1x misread `旻議…` at conf 0.50 vs `旻謙…` at s1/s2) without elevating them to a check. Mechanism: the owner-visible claim (a) "more reliable on the key fields" is only partially proven by the wave's acceptance; a later owner question could bounce. No frozen gating rule in the three v3 tools consumes the group name, so the tool-level acceptance is not wrong. Smallest correction: one §21.5 sentence stating the group-name field is recorded as supplementary raw evidence (non-gating), or explicitly why it is excluded.
- `RV-30-4` — [MINOR][GROUNDING] §21.3 parenthetical "measured conf 1.00 at 3x/6x/10x on the post frame" has no durably committed measurement (Phase 0 records the helper at native scale plus 5x determinism; the crosscheck records native reads). This review rebuilt the helper from the frozen Swift source and re-ran the post frame at 3x/6x/10x: `57張照片` conf 1.00 at all three — the claim is true, unrecorded. Mechanism: an "measured" claim without traceable evidence weakens otherwise-exact grounding. Smallest correction: record such a sweep in the Stage-04/05 C1 raw evidence, or rephrase to the recorded readings (native conf 1.00; tool scales 3x frame / 10x count region).
- `RV-30-5` — [MINOR][TEST] §21.3 justifies C2's byte-identity with "the v4 tools' JSON output contains no timestamps", but the same contract has the tool emit the helper build path/size/SHA and render temp PNGs under the process temp directory. If any process-unique path is emitted, C2's "v4 tool JSON bytes identical" across repeats fails for a non-Vision reason, wasting a bounded attempt or tempting a loosened C2. Mechanism: determinism failure caused by the wrapper, not the reader. Smallest correction: pin in §21.3 that the emitted result contains no timestamp and no process-unique path (or that the runner reuses one helper/work path per input).
- `RV-30-6` — [MINOR][GROUNDING] `phase0/baseline.json` `helper_rebuild.byte_identical_to_recorded: true` is ambiguous: it is computed as `sha256(/tmp/vision_ocr) == f54628e8…` (the recorded volatile binary still matches its own recorded SHA), while the rebuilt binary is `ad140ef7…` and is **not** byte-identical (swiftc non-determinism; the plan's prose and the field's note say so correctly). Mechanism: a future reader (including Stage 05) could cite the field as "rebuild byte-identical" and either overclaim or flag a false inconsistency. Smallest correction: one clarifying sentence in the v4 README or Stage-04 notes (do not rewrite the committed baseline; append-only).

## REQUIRED_PLAN_CHANGES
None. No unresolved BLOCKER or MAJOR capable of invalidating goal alignment, implementation, safety, compatibility, rollback or acceptance was found. The six MINOR findings above are non-gating: RV-30-1…RV-30-6 may be folded into the next in-place plan touch (Rev21 remains approvable as-is), and none requires a revision before Stage 03.

## RESIDUAL_MINOR_NOTES
- `plan.md`'s own anchor: Phase 0 recorded Rev20 `4919d871…`; the file now legitimately hashes `466bda4a…` (Rev21). `PRIOR_REVIEW_GATE` records the Rev20 hash and §21.4's UNCHANGED set correctly excludes `plan.md`; any future re-run must not treat this delta as a regression.
- Task e2e attempts 02–05 exist; "06" follows the max+1 monotonic convention required by §12/§21.6 (the absent 01 is historical and never reused).
- The `review/attempt-31/` directory is a parallel reviewer's; it was neither read nor modified.
- All six findings are non-gating; no hidden blocker or unverified load-bearing claim remains.

FINAL_STATUS: PLAN_APPROVED
NEXT_ACTION: Stage 03 Handoff compiling `handoff.md` bound to TASK_ID T20260916-0102-01-line-backup-acceptance, PLAN_REVISION 21, SHA-256 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190, carrying RV-30-1…6 as non-gating residual notes; do not edit `plan.md` for this approval (any later edit invalidates it).
