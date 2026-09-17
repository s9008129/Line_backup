# execution-rev21.md — Stage 04 execution record (Rev21: macOS Vision reader wave)

Stage-04 execution record for the Rev21 Vision wave (`REQ-VR-1..4`, result ②
reusable-capability subject). Append-only. Contains **no image data**: paths and
SHA-256 values only. No GUI input, no screen capture, no formal-data write, no
production download was performed anywhere in this wave.

## 0. Record identity and binding

- TASK_ID: T20260916-0102-01-line-backup-acceptance
- PLAN_REVISION: 21
- PLAN_SHA256: 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190 (1,877 lines / 260,774 bytes; re-verified at Stage-04 start)
- HANDOFF_SHA256: df595831eab25bb405d1f084f1113963ce911713515c4c31faaf34e9362f0888 (STATUS: READY_FOR_IMPLEMENTATION, NEXT_STAGE: 04_IMPLEMENT; re-verified against Rev21)
- PRIOR_WAVE_APPROVALS: review/attempt-30 (92d5be16a…, PLAN_APPROVED) + review/attempt-31 (c80a14da…, PLAN_APPROVED), both bound to Rev21 `466bda4a…`
- EXECUTION_TIMESTAMP_LOCAL: 2026-09-17T21:07:54+0800
- EVIDENCE_PATH: .agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev21.md
- Wave artifacts (untracked at write time; committed by this wave's Stage-04 commit): `evidence/20260916-route/tools/v4/` (5 files), `evidence/20260916-route/tools/selftest/v4/` (3 files), `evidence/20260916-route/agent-e2e/` (README + runner + attempt-01).

## 1. Status Contract v2 — six orthogonal statuses (wave-scoped, Stage-04 reported)

Subject: the Rev21 Vision wave (`REQ-VR-1..4`; result ② reusable capability). The
plan (§21.6) requires the wave tuple to be reported as result ② and never mixed
into result ①; Stage 05 re-derives it from fresh evidence and never trusts this
summary.

```
STAGE_04_REPORTED_PRIMARY_OUTCOME_STATUS:        ACHIEVED   # wave-scoped: Vision reader replaced tesseract and the attempt-05 blocker (57 read as 75) is proven a reader artifact with durable, re-runnable evidence
STAGE_04_REPORTED_IMPLEMENTATION_STATUS:         COMPLETE
STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS:        PASS
STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS:  PASS
STAGE_04_REPORTED_INDEPENDENT_ACCEPTANCE_STATUS: PENDING    # Stage 05 (e2e/attempt-06) not yet run
STAGE_04_REPORTED_TASK_CLOSURE_STATUS:           READY_FOR_INDEPENDENT_ACCEPTANCE
```

```
REV21_WAVE_TUPLE (Stage-04 reported): ACHIEVED | COMPLETE | PASS | PASS | PENDING | READY_FOR_INDEPENDENT_ACCEPTANCE
```

No field rewrites another subject. `PRIMARY_OUTCOME_STATUS` here is **wave-scoped
(result ②)**; it does not and cannot rewrite result ① (see §2). `CORE_ACCEPTANCE_STATUS: PASS`
rests on §21.5's acceptance rule: one attempt with all five checks PASS plus the
16-case v4 self-test matrix green. `REQUIRED_VERIFICATION_STATUS: PASS` rests on
the frozen re-check (§9), `baseline_delta=UNCHANGED`, and the Status-Contract
compliance of this record. Independent acceptance stays PENDING.

## 2. Preserved facts — result ① and prior scoped blockers (NOT re-derived, NOT touched by this wave)

- Result ① album-data (prior verified snapshot, preserved verbatim):
  `PRIMARY UNKNOWN | IMPLEMENTATION COMPLETE | CORE BLOCKED | REQUIRED_VERIFICATION PASS | INDEPENDENT_ACCEPTANCE PASS | CLOSURE CORE_ACCEPTANCE_BLOCKED`.
  The Rev21 wave adds no album-data evidence and changes none of these values.
- SOURCE_CORRESPONDENCE: `UNRESOLVED` — scoped CORE blocker for result ①, evidence-bound
  (exact source namespace/provenance was never captured). Preserved fact; this wave
  neither resolves nor worsens it.
- CUA_ROUTE_DECISION: scoped CORE blocker, **owner-reserved**. The route remains
  stopped with `owner_decision_required: true` (owner chooses A `ROUTE_NOT_NEEDED`
  or B a new one-shot ⋮ gate). Rev21 grants nothing over the route; C4 is
  `DEMONSTRATION_ONLY` and can never set this field or flip attempt-05's frozen verdict.
- attempt-05 frozen route artifacts are unchanged: `run-ledger.json` `17b17203…`,
  `album-open-verify.json` `ffa5d963…` (verdict `TARGET_MISMATCH`, exit 4, `count_digits_read: "75"`),
  `vision-ocr-crosscheck.json` `d3ebbaed…` (`SUPPLEMENTARY_NON_AUTHORITATIVE`, never promoted).

## 3. Stage-04 snapshot fields (for Stage 05)

```
TASK_ID:                                T20260916-0102-01-line-backup-acceptance
PLAN_REVISION:                          21
PLAN_SHA256:                            466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190
HANDOFF_SHA256:                         df595831eab25bb405d1f084f1113963ce911713515c4c31faaf34e9362f0888
STAGE_04_REPORTED_IMPLEMENTATION_STATUS:         COMPLETE
STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS:        PASS
STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS:  PASS
STAGE_04_EXECUTION_ARTIFACT_SHA256:     self-reference not embedded (hashing this file changes it); the value is reported in the Stage-04 hand-off message and re-hashed independently by Stage 05
EVIDENCE_PATH:                          .agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev21.md
```

## 4. Check matrix (wave-active rows; canonical per-check fields)

Fields per the plan's authoritative table (plan.md §Canonical Status Contract v2):
CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY | CHECK_RESULT | WAIVER_STATUS.

| CHECK_ID | Criticality | Evidence role | Gate | Baseline | Failure routing | Waiver allowed | Authority | Check result | Waiver status |
|---|---|---|---|---|---|---|---|---|---|
| VISION_READER_TOOLCHAIN_V4 | CORE | OUTCOME | HARD_CLEAN | YES | reader-layer regression changing a verdict/exit code = TASK_REGRESSION | NO | NONE | PASS | NOT_ALLOWED |
| VISION_AGENT_E2E_C1_C5 | CORE | OUTCOME | HARD_CLEAN | YES | failed/absent check or non-append-only attempt invalidates wave CORE acceptance; C4 stays DEMONSTRATION_ONLY | NO | NONE | PASS | NOT_ALLOWED |
| VISION_READER_FAILCLOSED_MATRIX | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | helper-unavailable/unparsable input must reach a documented refusal path with non-zero exit; crash or guessed value = TASK_REGRESSION | NO | NONE | PASS | NOT_ALLOWED |
| V3_FROZEN_EVIDENCE_UNCHANGED | CORE | MUST_NOT_BREAK | HARD_CLEAN | YES | any byte change to v2/v3 tool, v3 self-test summary, route ledger/artifact or attempt-05 frames = TASK_REGRESSION (stop the wave) | NO | NONE | PASS | NOT_ALLOWED |
| BASELINE_REGRESSION_DELTA | CORE | MUST_NOT_BREAK | BASELINE_DELTA | YES | new/worsened signature, or an old signature silently omitted, = TASK_REGRESSION | NO | NONE | PASS (baseline_delta=UNCHANGED) | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | illegal enum/routing/self-waiver = TASK_REGRESSION | NO | NONE | PASS (this record uses the canonical enums; no self-waiver) | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | missing independent result stays PENDING/BLOCKED | NO | NONE | PENDING (Stage 05 e2e/attempt-06) | NOT_ALLOWED |

### 4.1 Carried-forward prior CORE checks (freshness contract)

Prior checks carry forward with freshness; Stage 05 re-derives them with fresh
evidence and may not silently omit any. This wave did not re-run them and does
not claim them as fresh results: `VERIFIER_FALSE_POSITIVE_REPRO`,
`VERIFY_REAL_DESTINATION`, `VERIFY_NEGATIVE_FIXTURES`, `TRANSACTION_RESUME_CORE`,
`TRANSACTION_COMMIT_CORE`, `FORMAL_STATE_READONLY_RECONCILIATION`,
`SOURCE_CORRESPONDENCE` (scope: result ①; UNRESOLVED preserved), `CUA_ROUTE_DECISION`
(owner-reserved preserved). Their underlying artifacts were re-hashed in §9 and are
byte-identical, so no prior signature regressed.

## 5. Scoped blockers

| Blocker | Scope/subject | Class | Authority | Status | Effect on this wave |
|---|---|---|---|---|---|
| (none new) | Rev21 Vision wave | — | — | no wave blocker | none |
| SOURCE_CORRESPONDENCE | result ① exact source correspondence | UNRESOLVED (evidence-bound) | owner / exact-join evidence (Rev16 §16.4) | preserved, untouched | none (never promoted to closure; never inferred) |
| CUA_ROUTE_DECISION | route attempt-05 closure | owner-reserved; route stopped, `owner_decision_required: true` | project owner (A/B decision) | preserved, untouched | none; C4 cannot set it (§7.4) |

No agent approves its own waiver; no waiver is requested or granted here.

## 6. W6-V4-TOOLCHAIN evidence — v4 artifacts, self-test, helper build record, probes

### 6.1 Delivered v4 tool set (5 files, landed byte-identical to the Phase-1 drafts)

| Path | SHA-256 | Bytes |
|---|---|---|
| evidence/20260916-route/tools/v4/vision_reader.py | 22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8 | 8,369 |
| evidence/20260916-route/tools/v4/locate_album_card.py | bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162 | 7,025 |
| evidence/20260916-route/tools/v4/verify_album_open.py | ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58 | 6,981 |
| evidence/20260916-route/tools/v4/locate_album_ellipsis.py | b77e3d51d43e6cb4a0a1b7bf2e9e1179a2718d7867ac01b5344fbcd07cef96c4 | 11,436 |
| evidence/20260916-route/tools/v4/README.md | ed3ebf0aad53024f3e4fe7d4886faa9b37c048e2fdf95513ab3bc7bafe677f23 | 8,052 |

The README carries the three handoff-required notes: (a) tool JSON contains no
timestamp and no process-unique path; (b) `byte_identical_to_recorded` clarification
(Phase-0 baseline is append-only committed evidence, never rewritten; the field
referred to the that-day `/tmp` originals, and future re-verification keys on the
durable frame copies under `evidence/20260917-vision-reader/frames/` + `manifest.json`);
(c) helper resolution order (`$VISION_OCR_BIN`, else the fixed build path) plus the
six-outcome record, and the "v4 = v3 logic + reader layer" diff note with rerun commands.

### 6.2 v4 self-test matrix (`tools/selftest/v4/`, author: Harvey)

- `selftest-summary.json` **5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d** (final)
  — `result: PASS`, `cases_total: 16`, `cases_failed: 0`; the matrix was re-run twice, green both times.
- `run_selftest.py` `7182d5760821b0e3464316722a20fc1af9cfedddf374f0509c65b7a95299f690`; `README.md` `1c2f3d7a5fc5de3ff99c87645d1723a4c15c137115b2ceba097398c038639c9f`.
- TOOLS is pinned to `../../v4` resolved from the runner's own `__file__` (never v3).
- Expectations pinned to the frozen v3 literals: v3 summary `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324`,
  re-hashed at run start and after the run, unchanged; cases 1–13 carry the frozen
  v3 `expect_exit`/`expect_verdict` verbatim — **zero mismatches**; the two ellipsis
  control cases keep the v3 `click_point [300,47]` with ±2 tolerance.
- New reader-layer cases (14–16): `count_normalization` (10x count region `57張照片`
  → exit 0 / ELIGIBLE / MATCH with digits `57`), `helper_unavailable_failclosed`
  (`VISION_OCR_BIN=/nonexistent/vision_ocr_v4_selftest` → documented refusal
  `TARGET_TITLE_NOT_FOUND` exit 2, no traceback, `reader.calls[0].outcome == "binary_missing"`,
  fixed build-path binary SHA unchanged before/after = no rebuild), `determinism_5x`
  (5 repeats: stdout bytes all equal).
- `tool_shas`: before == after == the landed hashes in §6.1 (`stable_during_run: true`).
- `fixture_notes`: all fixtures synthetic/pixel-drawn, no real screen content; PingFang
  not available on this host, so the CJK fixture font is `/System/Library/Fonts/Hiragino Sans GB.ttc`
  (font substitution recorded; `pingfang_available: false`).

### 6.3 Helper build record (frozen source, built exactly once, reused)

- Source: `evidence/20260916-route/tools/vision/vision_ocr.swift` SHA-256 `4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32` (never edited; re-verified in §9).
- Built exactly once (Phase 1) with `swiftc -O` into the fixed deterministic path
  `/var/folders/0r/r3qmjfbn0z57mtmdxmnp60c80000gn/T/vision_ocr_v4_build/vision_ocr`
  (atomic `vision_ocr.tmp<pid>` + `os.replace`; sidecar `source.sha256` = `4fc9fa2b…`).
- Binary: 67,200 bytes, SHA-256 `c7087d98a1035db39b39906b8da995fa41e3ed52ac4b34481d1213d4fe6eb0b5`;
  mtime 2026-09-17 20:47:54 +0800 — unchanged by every Phase-2 run (reuse, no rebuild).
- `VISION_OCR_BIN` was unset for all normal runs; an invalid value never triggers a rebuild
  (verified: binary mtime unchanged, `resolved_from: "env"`, `outcome: "binary_missing"`).

### 6.4 Stage-04 probes (own runs, `/opt/homebrew/bin/python3`, `PYTHONDONTWRITEBYTECODE=1`)

| Probe | Exit | Key facts | stdout SHA-256 (bytes) |
|---|---|---|---|
| card post | 4 `UNSAFE_MARGINS` | count `57` MATCH; count_box [7,113,175,143]; title bbox [15,83,204,111]; `margin_above_px: null`, `margin_below_px: 129` | 179af9b19b103ef4b61fa26b3649ab9f307a105f8037f3f876fff37fe516a2d6 (1,745) |
| card pre | 0 `ELIGIBLE` | count `57` MATCH; title bbox [15,449,129,462]; margins 22/52 | 120582377191556218c1b18a65fb71dfbae9d6e6b6abb603845a90147363191f (1,775) |
| card s1 | 0 `ELIGIBLE` | count `57` MATCH; title bbox [15,449,128,462]; margins 22/52 | 184cab605df1f0488c633da41db1e19d70feaee94abef87cfdec32844eccbdb5 (1,779) |
| card s2 | 0 `ELIGIBLE` | count `57` MATCH; title bbox [30,899,256,923]; margins 44/103 | 153dd6ee713d22b2f3cab3e6f1f1c5f4f73108c84ea1f53866645d4e4d342b07 (1,776) |
| verify (pre,post) | 0 `ALBUM_OPEN_VERIFIED` | `changed_fraction 0.646749`; count `57` MATCH; post title `2024/05/13~05/17` | a9de4661399b9d848ea200ebc358592050f057509c281689fef2ccd793893810 (3,135) |
| ellipsis pre (extra smoke) | 0 `ELIGIBLE` | single 3x reader call, 7 lines | ae9ac08c11e0e27745f9e471fa9849f9c31b714e6557d0e4e8559f1a7b714d86 (5,131) |
| ellipsis post (extra smoke) | 3 `NO_ELLIPSIS_FOUND` | documented refusal path, 4 lines | b53b9554532e65435db8661bee29f46e7f7a96e4a5948f2bd77304b9132771e8 (8,722) |

All five required probes were run twice; the two runs are byte-identical
(C2 preview). The 10x count-region read for the post frame returns one
line-level observation `57張照片` (conf 1.00), coordinates
x=8.5, y=7.6, w=51.6, h=12.6 in original-frame units.

Scope note: the v4 README also cites the four historical raw-stdout SHAs
(`5c86dda8…` post, `07e3e156…` pre, `561bb131…` s1, `abf9d75e…` s2). Those are the
supplementary attempt-05 native-scale cross-check runs on the same four frozen
frames (`vision-ocr-crosscheck.json`, `SUPPLEMENTARY_NON_AUTHORITATIVE`). They are
historical provenance keys for the durable frames, not the v4 per-call comparison
values above (the v4 calls render a LANCZOS-upscaled PNG and read that instead of
the original file, so byte equality with the cross-check is not expected).

## 7. W6-AGENT-E2E evidence — C1–C5 measured values (author: Boole)

- Location `evidence/20260916-route/agent-e2e/`; attempt-01 is append-only and preserved as produced.
- `attempt-01/summary.json` **0ee83325286ba64a9817b93427a6562e1a4d73c205043103e33f074b68cf8aad**
  — `result: PASS`, `failures_total: 0`, `attempt_failures: 0`, `prior_failures_total: 0`,
  `stop_reason: null` (bounded loop: threshold 5, not reached), `acceptance_mode: INTEGRATION`
  (offline replay over durable frozen frames; never reported as live E2E).
- 38 raw artifacts + `SHA256SUMS` (38 lines); `shasum -c` → all 38 OK
  (SHA256SUMS SHA-256 `0c51198075dfb5ef922e401a0a75e6f7e7b2b90370a5ed8e8ee4b191195078e3`).
- Frames re-hashed at test start: post `4cb8a6b4…`, pre `3d926e7d…`, s1 `aea53a0d…`, s2 `7b9d0a19…` — all match.
- v4 tools pinned by hash in the summary: identical to §6.1.

Measured values:

| ID | Check | Measured result |
|---|---|---|
| C1 | post count read | exit 4 `UNSAFE_MARGINS`; `count_digits_read: "57"`, `count_text: MATCH`; count_box [7,113,175,143]; raw line `57張照片` conf 1.00 |
| C2 | determinism | 5 repeats × 4 inputs: v4 tool JSON bytes identical; helper stdout bytes identical per call (`reader.calls[].stdout_sha256` equal across repeats) |
| C3 | title on pre and post | both frames read `2024/05/13~05/17` (pre bbox [15,449,129,462]; post bbox [15,83,204,111]) |
| C4 | frozen S5 replay (`DEMONSTRATION_ONLY`) | v4 `verify_album_open` (pre,post) → exit 0 `ALBUM_OPEN_VERIFIED`, `changed_fraction 0.646749`, count `57` MATCH; recorded next to the frozen v3 result `TARGET_MISMATCH` exit 4 / count read `75` (`attempt-05/album-open-verify.json` `ffa5d963…`) |
| C5 | s1/s2 crop counts | both read `57` (frozen locator historically read `27` / `5`) |
| RV-30-4 | count-scale sweep | full-frame reads at 3x/6x/10x → `57張照片` conf 1.00 each; count-region reads at 3x/6x/10x → `57`; official count-region read `57` |

**C4 declaration:** C4 is `DEMONSTRATION_ONLY`. It never flips attempt-05's frozen
verdict (`TARGET_MISMATCH`/exit 4/`75` stays the recorded route outcome), never
sets `CUA_ROUTE_DECISION`, never authorizes ⋮ input, and never changes §20.3's
routing. The route remains stopped with `owner_decision_required: true`. Rev21
grants nothing over the route.

### 7.1 Provenance notes (recorded as facts)

1. **Runner v1.0.0 → v1.1.0:** attempt-01 was produced by runner v1.0.0
   (`2225e3a7eee135c3a714e62fde026f92d4b5648590e5ffec79f564b761704819`, recorded verbatim in
   `attempt-01/summary.json`). The committed runner file is v1.1.0
   (`cd0aa1511ae45af32cb4497ddc0a7532053a4ebfd13fdaea55f451e13f06c93c`); its changes are
   bookkeeping-only (shared raw registry, helper values read from tool JSON,
   `sys.dont_write_bytecode`) and it was validated end-to-end in `/tmp` scratch. attempt-01 is
   preserved as-is (append-only; a later run would take `attempt-02`).
2. **`helper_from_tool_json`:** attempt-01's top-level `helper` object is `null` because the v1.0.0
   preflight resolved the helper before the tool JSONs existed. The authoritative values are in the
   same file under `helper_from_tool_json` and in each raw tool JSON's `reader.helper`:
   `resolved_from: "build_path"`, `binary_path: …/T/vision_ocr_v4_build/vision_ocr`,
   `binary_sha256: c7087d98…`, `binary_bytes: 67200`, `source_sha256: 4fc9fa2b…`.
3. **post `UNSAFE_MARGINS` is v3 geometry as-is:** on the post frame the v3 bright-band rule finds
   no bright row above the title (`band_top_bright_row: null` → `margin_above_px: null < 10`), so the
   frozen verdict is `UNSAFE_MARGINS` / exit 4. This is the untouched v3 rule; it is recorded as-is
   and is explicitly **not** a defect to fix. C1's judgement is the count read (`57` / MATCH), which
   passes.
4. **CJK fixture font substitution:** PingFang is unavailable on this host, so the v4 self-test
   fixtures use `/System/Library/Fonts/Hiragino Sans GB.ttc`; this is recorded in the summary's
   `fixture_notes` (`pingfang_available: false`, `cjk_font_fallback_blocks: false`). Fixtures are
   synthetic and pixel-drawn only.
5. **Self-test summary supersession:** `selftest-summary.json` was regenerated by a peer re-run
   (`44979637…` → `5ad2be10…`); the final `5ad2be10…` version is authoritative and both runs were green.
6. **Determinism scope (C2):** helper stdout bytes + v4 tool JSON bytes. The agent-attempt
   `summary.json` is out of C2 scope (it records timestamps/argv by design). The v4 tool JSON
   contains no timestamp and no process-unique path (verified by scan); `resolved_from` is only
   `env` or `build_path`.
7. **No rebuild anywhere in Phase 2:** the fixed-path helper was reused in every run, including the
   e2e attempt (same path/SHA), with the sidecar `source.sha256` present.

## 8. VISION_READER_FAILCLOSED_MATRIX evidence — all six outcomes exercised

| Outcome | Trigger used | Observed |
|---|---|---|
| ok | normal runs (helper at fixed build path) | words parsed; `exit_code: 0`; `lines_parsed` 4–7 per frame read |
| binary_missing | `VISION_OCR_BIN=/nonexistent/vision_ocr` | `resolved_from: "env"`; stderr excerpt `helper binary missing: /nonexistent/vision_ocr`; empty words → card refusal `TARGET_TITLE_NOT_FOUND` exit 2; helper binary mtime unchanged (no rebuild). Self-test case 15 records the same on its fixture |
| build_failed | in-process probe: fresh build dir + missing frozen source | `outcome: "build_failed"`; reason `frozen source missing: /nonexistent/vision_ocr.swift`; empty words; `find_title` → None → documented exit 2 |
| nonzero_exit | synthetic helper printing to stderr and exiting 2 | `outcome: "nonzero_exit"`, `exit_code: 2`, stderr excerpt `synthetic helper failure` → card exit 2 (`TARGET_TITLE_NOT_FOUND`) |
| unparsable | synthetic helper printing a non-matching line, exit 0 | `outcome: "unparsable"`, `exit_code: 0`, empty words → card exit 2 |
| timeout | synthetic helper sleeping 5 s with `TIMEOUT_S` patched to 1 s | `outcome: "timeout"`, elapsed 1.03 s (kill+wait), empty words |

No failure mode crashes the tool and none yields a guessed value: every case ends
in a documented refusal path (`TARGET_TITLE_NOT_FOUND` 2, `BAD_FRAME` 6, or a
recorded `UNREADABLE` count that never refuses). `BAD_FRAME` emits
`"reader": {"helper": null, "calls": []}` (exit 6) before any read.

## 9. W6-DELTA-RECORD — frozen re-check (`baseline_delta=UNCHANGED`)

Comparison key: durable in-repo artifacts (durable frame copies, committed tools
and evidence). Every anchor re-hashed:

| Anchor | SHA-256 | Bytes | Result |
|---|---|---|---|
| v2 `detect_menu_popup.py` | 6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc | 6,339 | UNCHANGED |
| v2 `locate_card_ellipsis.py` | 8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e | 8,943 | UNCHANGED |
| v2 self-test summary (`tools/selftest/selftest-summary.json`) | d8ffc1290347da13816f988adbe47656d42c60041ef701bf159b9d4c52a76557 | 2,946 | UNCHANGED |
| v3 `locate_album_card.py` | 500fcadbe8cb47f1cd22f0d247ad7d7d65c84baef4000f2239e1872e340e98e4 | 7,389 | UNCHANGED |
| v3 `verify_album_open.py` | 80504262025cf10202c8938612b5be73f91809578f1317f36733f52b513fa74b | 6,818 | UNCHANGED |
| v3 `locate_album_ellipsis.py` | 60e3120abb312f189f785f12ee4047f4365028a8759ae88874eebb06046a7deb | 11,273 | UNCHANGED |
| v3 self-test summary | 17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324 | 4,250 | UNCHANGED |
| v3 self-test runner | 94a41092e2c72a95bf833fea64f7c607979512133034c43abeaa0aedf9f0bf13 | 10,777 | UNCHANGED |
| v3 self-test README | 76bda610f255340eecf4bbeeef205ba4b4d81740557ddf63d4883a2d17898736 | 1,937 | UNCHANGED |
| frozen helper source `vision/vision_ocr.swift` | 4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32 | 1,070 | UNCHANGED |
| attempt-05 `run-ledger.json` | 17b172031a38ea6b5c66ebfedacf748aa1f08b12d572263d13eef02f54465218 | 29,772 | UNCHANGED |
| attempt-05 `album-open-verify.json` | ffa5d9633804f819473674f57a9979d56e849882f32dfcfa4a2b5b1326083a9b | 2,249 | UNCHANGED |
| attempt-05 `vision-ocr-crosscheck.json` | d3ebbaed3db446cfbecd01d74d132764b6a675232b9db9edd2d1af3071dd6d5b | 10,707 | UNCHANGED |
| frame post | 4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3 | 66,686 | UNCHANGED |
| frame pre | 3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531 | 63,914 | UNCHANGED |
| frame s1 | aea53a0df8c4ef20488446dbccc42fa84ecd72c36aad71d42199f20b9e30f5c3 | 87,400 | UNCHANGED |
| frame s2 | 7b9d0a19323e0f7341d2ee9722415251195531dc067b773f231676729c63721b | 248,922 | UNCHANGED |
| plan.md | 466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190 | 260,774 | UNCHANGED |
| handoff.md | df595831eab25bb405d1f084f1113963ce911713515c4c31faaf34e9362f0888 | 37,807 | UNCHANGED |
| `execution.md` (untouched) | d54011483e597bc572930b03fef7536a0743f8fb9d23744078b3b75953eb0242 | 33,676 | UNCHANGED |
| `execution-rev19.md` (untouched) | 8302005a03261747bd25fc21e823937a70389b940a50019b0437d8ff4c38cbfa | 15,174 | UNCHANGED |

`git diff HEAD --stat` at re-check time: empty (no tracked modification). No prior
signature is silently omitted and no new/worsened signature exists.

**`baseline_delta=UNCHANGED`** — no WORSENED condition; the wave may continue.

## 10. RV-31-2 diff audit — v4 vs frozen v3 (full unified diffs + per-hunk explanations)

Method: `diff -u` of each v4 tool against its frozen v3 counterpart; the two new
files (`vision_reader.py`, `README.md`) appear as new-file diffs. Machine proof of
"only the reader layer changed": **reverse-mask audit** — applying exactly the
declared seam edits in reverse to each v4 file reproduces the frozen v3 file
**byte-for-byte** (`reverse-mask -> byte-identical to frozen v3 = True` for all
three tools; `AUDIT: PASS`). No verdict, threshold, exit code, refusal path or
geometry line is touched.

### 10.1 Per-hunk explanations

- `card.diff` H1 `@@ -17,18 +17,30 @@` — docstring +1 v4 note line; imports
  `io`→`importlib.util`, drop `subprocess`; add `_load_sibling()` (own-directory
  path loader) + module-level `vision_reader = _load_sibling("vision_reader")`
  (required so the tool loads the v4 reader from its own directory; never v3).
- `card.diff` H2 `@@ -38,39 +50,15 @@` — `_tsv_rows` body: the frozen tesseract
  stdin/stdout TSV subprocess call becomes `vision_reader.read_words(image, scale)`;
  `ocr_words` no longer upscales — the LANCZOS 3x upscale moved into the reader
  (call site passes the unscaled image; `or []` unchanged).
- `card.diff` H3 `@@ -131,12 +119,12 @@` — `ocr_digits_region`: the 10x LANCZOS
  upscale moved into the reader; `emit()` adds `result["reader"] = vision_reader.record()`
  before serialization. Nothing else in the file changed.
- `verify.diff` H1 `@@ -28,6 +28,8 @@` — docstring +1 v4 note line.
- `verify.diff` H2 `@@ -52,6 +54,7 @@` — `emit()` adds
  `result["reader"] = card.vision_reader.record()`; the v3 `_load_sibling` convention
  (already present in v3) now resolves the sibling card module inside `tools/v4/`.
- `ellipsis.diff` H1 `@@ -30,6 +30,8 @@` — docstring +1 v4 note line.
- `ellipsis.diff` H2 `@@ -51,6 +53,7 @@` — `emit()` adds
  `result["reader"] = card.vision_reader.record()` (same sibling-loading convention).
- `vision_reader.diff` (new file, 232 diff lines) — the reader module: helper
  resolution/atomic one-time build, `read_words()` (LANCZOS upscale, temp PNG,
  helper invocation, `split("\t", 2)` line parsing, int→float ÷ scale), the outcome
  record, fail-closed handling.
- `README.diff` (new file, 143 diff lines) — usage, reader contract, outcome record,
  fail-closed semantics, C2 scope, v4=v3 diff note, `byte_identical_to_recorded` semantics.

### 10.2 Full unified diffs

#### locate_album_card.py (v3 → v4)

```diff
--- evidence/20260916-route/tools/locate_album_card.py	2026-09-17 17:01:01
+++ evidence/20260916-route/tools/v4/locate_album_card.py	2026-09-17 20:54:28
@@ -17,18 +17,30 @@
 Refusals (non-zero exit): 2 TARGET_TITLE_NOT_FOUND, 4 UNSAFE_MARGINS,
 5 TARGET_COUNT_MISMATCH, 6 BAD_FRAME. Historical coordinates are never used:
 every run must be given the frame captured for the current surface.
+
+v4 (Rev21): the reader layer is macOS Vision (sibling vision_reader module); all v3 rules above are unchanged.
 """
 import argparse
 import hashlib
-import io
+import importlib.util
 import json
 import os
 import re
-import subprocess
 
 from PIL import Image
 
 
+def _load_sibling(name):
+    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
+    spec = importlib.util.spec_from_file_location(name, path)
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+vision_reader = _load_sibling("vision_reader")
+
+
 def sha256_file(path):
     h = hashlib.sha256()
     with open(path, "rb") as f:
@@ -38,39 +50,15 @@
 
 
 def _tsv_rows(image, psm, scale):
-    buf = io.BytesIO()
-    image.save(buf, format="PNG")
-    proc = subprocess.run(
-        ["tesseract", "-", "stdout", "-l", "chi_tra+eng", "--psm", str(psm), "tsv"],
-        input=buf.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
-    if proc.returncode != 0:
-        return None
-    words = []
-    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
-        parts = line.rstrip("\n").split("\t")
-        if len(parts) < 12 or parts[0] == "level":
-            continue
-        text = parts[11].strip()
-        if not text:
-            continue
-        try:
-            conf = float(parts[10])
-        except ValueError:
-            conf = -1.0
-        words.append({
-            "text": text,
-            "conf": conf,
-            "x": int(parts[6]) / float(scale),
-            "y": int(parts[7]) / float(scale),
-            "w": int(parts[8]) / float(scale),
-            "h": int(parts[9]) / float(scale),
-        })
-    return words
+    """v4 reader seam: the frozen tesseract TSV call became the Vision reader.
 
+    `image` is the unscaled image; vision_reader applies the LANCZOS upscale
+    (`scale`) and returns v3-shaped records (psm has no Vision equivalent)."""
+    return vision_reader.read_words(image, scale)
 
+
 def ocr_words(im, scale=3, psm=6):
-    up = im.resize((im.size[0] * scale, im.size[1] * scale), Image.LANCZOS)
-    return _tsv_rows(up, psm, scale) or []
+    return _tsv_rows(im, psm, scale) or []
 
 
 def digits(text):
@@ -131,12 +119,12 @@
     crop = im.crop(box)
     if crop.size[0] <= 0 or crop.size[1] <= 0:
         return ""
-    up = crop.resize((crop.size[0] * scale, crop.size[1] * scale), Image.LANCZOS)
-    words = _tsv_rows(up, psm, scale) or []
+    words = _tsv_rows(crop, psm, scale) or []
     return digits("".join(w["text"] for w in words))
 
 
 def emit(result, out_path):
+    result["reader"] = vision_reader.record()
     payload = json.dumps(result, ensure_ascii=False, indent=1)
     print(payload)
     if out_path:
```

#### verify_album_open.py (v3 → v4)

```diff
--- evidence/20260916-route/tools/verify_album_open.py	2026-09-17 17:01:01
+++ evidence/20260916-route/tools/v4/verify_album_open.py	2026-09-17 20:54:28
@@ -28,6 +28,8 @@
 Exit codes: 0 ALBUM_OPEN_VERIFIED, 3 NO_EFFECT, 4 TARGET_MISMATCH, 5 INCONCLUSIVE,
 6 BAD_INPUT. Historical frames are never used: both frames must be the ones captured
 for this run.
+
+v4 (Rev21): the reader layer is macOS Vision (sibling vision_reader module); all v3 rules above are unchanged.
 """
 import argparse
 import importlib.util
@@ -52,6 +54,7 @@
 
 
 def emit(result, out_path):
+    result["reader"] = card.vision_reader.record()
     payload = json.dumps(result, ensure_ascii=False, indent=1)
     print(payload)
     if out_path:
```

#### locate_album_ellipsis.py (v3 → v4)

```diff
--- evidence/20260916-route/tools/locate_album_ellipsis.py	2026-09-17 17:01:01
+++ evidence/20260916-route/tools/v4/locate_album_ellipsis.py	2026-09-17 20:54:28
@@ -30,6 +30,8 @@
 Exit codes: 0 ELIGIBLE, 2 TARGET_TITLE_NOT_FOUND, 3 NO_ELLIPSIS_FOUND,
 4 AMBIGUOUS_ELLIPSIS, 5 GROUP_LEVEL_ONLY, 6 BAD_FRAME. Historical coordinates are
 never used: every run must be given the frame captured for the current surface.
+
+v4 (Rev21): the reader layer is macOS Vision (sibling vision_reader module); all v3 rules above are unchanged.
 """
 import argparse
 import importlib.util
@@ -51,6 +53,7 @@
 
 
 def emit(result, out_path):
+    result["reader"] = card.vision_reader.record()
     payload = json.dumps(result, ensure_ascii=False, indent=1)
     print(payload)
     if out_path:
```

#### vision_reader.py (new file)

```diff
--- /dev/null	2026-09-17 20:58:02
+++ evidence/20260916-route/tools/v4/vision_reader.py	2026-09-17 20:54:28
@@ -0,0 +1,229 @@
+#!/usr/bin/env python3
+"""macOS Vision reader for the v4 route tools (Rev21 REQ-VR-1 / REQ-VR-2).
+
+Given a PIL image, this module renders the requested LANCZOS upscale to a
+temporary PNG, runs the frozen Vision helper (source SHA-256 4fc9fa2b…,
+`VNRecognizeTextRequest`) and returns the v3-shaped word records
+`{text, conf, x, y, w, h}` in original-frame coordinates: x=x0/scale,
+y=y0/scale, w=(x1-x0)/scale, h=(y1-y0)/scale. Vision observations are
+line-level; the helper's own line boxes are the token unit and no
+re-tokenization is performed. TEXT is never rewritten: no case folding, no
+width normalization, no merge of 禎 (U+798E) and 楨 (U+6968).
+
+Helper resolution: `$VISION_OCR_BIN` when set (used as-is; an invalid value is
+never rebuilt), else `<tempdir>/vision_ocr_v4_build/vision_ocr`, built exactly
+once from the frozen Swift source with `swiftc -O` when the binary or its
+`source.sha256` sidecar is missing/stale. Builds are atomic (build to
+`vision_ocr.tmp<pid>`, then `os.replace`).
+
+Fail-closed: every helper failure (missing binary, build failure, non-zero
+exit, timeout, unparsable stdout) yields empty words and one recorded call;
+the caller then follows the frozen v3 refusal paths. The module never crashes
+and never guesses a value. The record carries no timestamps and no
+process-unique paths, so repeated runs on the same input are byte-identical.
+"""
+import hashlib
+import os
+import re
+import subprocess
+import tempfile
+
+from PIL import Image
+
+SOURCE_SHA256 = "4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32"
+BUILD_DIR_NAME = "vision_ocr_v4_build"
+BUILD_NAME = "vision_ocr"
+TIMEOUT_S = 60
+EXCERPT_LIMIT = 200
+
+_PX = re.compile(r"^px\[(-?\d+),(-?\d+),(-?\d+),(-?\d+)\]$")
+_CONF = re.compile(r"^conf=(\d+(?:\.\d+)?)$")
+
+_STATE = {"helper": None, "usable": False, "reason": "", "calls": []}
+
+
+def sha256_bytes(data):
+    return hashlib.sha256(data).hexdigest()
+
+
+def sha256_file(path):
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(1 << 20), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def _excerpt(data):
+    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
+    return text.strip()[:EXCERPT_LIMIT]
+
+
+def _build_dir():
+    return os.path.join(tempfile.gettempdir(), BUILD_DIR_NAME)
+
+
+def _build_binary():
+    return os.path.join(_build_dir(), BUILD_NAME)
+
+
+def _sidecar():
+    return os.path.join(_build_dir(), "source.sha256")
+
+
+def _frozen_source():
+    here = os.path.dirname(os.path.abspath(__file__))
+    return os.path.normpath(os.path.join(here, os.pardir, "vision", "vision_ocr.swift"))
+
+
+def _file_fields(path):
+    if os.path.isfile(path):
+        return sha256_file(path), os.path.getsize(path)
+    return None, None
+
+
+def _sidecar_matches():
+    try:
+        with open(_sidecar(), "r", encoding="utf-8") as f:
+            return f.read().strip() == SOURCE_SHA256
+    except OSError:
+        return False
+
+
+def _build_once():
+    """Build the helper at the fixed path when needed; returns (usable, reason)."""
+    binary = _build_binary()
+    if os.path.isfile(binary) and _sidecar_matches():
+        return True, ""
+    source = _frozen_source()
+    if not os.path.isfile(source):
+        return False, "frozen source missing: " + source
+    if sha256_file(source) != SOURCE_SHA256:
+        return False, "frozen source sha256 mismatch: " + source
+    try:
+        os.makedirs(_build_dir(), exist_ok=True)
+    except OSError as exc:
+        return False, "build dir error: %s" % exc
+    tmp = binary + ".tmp%d" % os.getpid()
+    try:
+        proc = subprocess.run(["swiftc", "-O", source, "-o", tmp],
+                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
+    except OSError as exc:
+        return False, "swiftc error: %s" % exc
+    if proc.returncode != 0 or not os.path.isfile(tmp):
+        try:
+            os.remove(tmp)
+        except OSError:
+            pass
+        return False, _excerpt(proc.stderr) or ("swiftc exit %d" % proc.returncode)
+    os.replace(tmp, binary)
+    try:
+        with open(_sidecar(), "w", encoding="utf-8") as f:
+            f.write(SOURCE_SHA256 + "\n")
+    except OSError as exc:
+        return False, "sidecar write error: %s" % exc
+    return True, ""
+
+
+def _resolve_helper():
+    """Resolve the helper once per process and cache it for the run."""
+    if _STATE["helper"] is not None:
+        return
+    env = os.environ.get("VISION_OCR_BIN")
+    if env:
+        helper = {"resolved_from": "env", "binary_path": env}
+        usable = os.path.isfile(env)
+        reason = "" if usable else "helper binary missing: " + env
+    else:
+        helper = {"resolved_from": "build_path", "binary_path": _build_binary()}
+        usable, reason = _build_once()
+    helper["binary_sha256"], helper["binary_bytes"] = _file_fields(helper["binary_path"])
+    helper["source_sha256"] = SOURCE_SHA256
+    _STATE["helper"] = helper
+    _STATE["usable"] = usable
+    _STATE["reason"] = reason
+
+
+def read_words(image, scale):
+    """Upscale `image` by `scale` (LANCZOS), read it with the Vision helper and
+    return v3-shaped word records in original-frame coordinates.
+
+    Any failure returns an empty list; the call outcome is recorded either way."""
+    _resolve_helper()
+    call = {"scale": scale, "outcome": None, "exit_code": None, "stderr_excerpt": "",
+            "stdout_sha256": sha256_bytes(b""), "stdout_bytes": 0, "lines_parsed": 0}
+    _STATE["calls"].append(call)
+    if not _STATE["usable"]:
+        call["outcome"] = ("binary_missing" if _STATE["helper"]["resolved_from"] == "env"
+                           else "build_failed")
+        call["stderr_excerpt"] = _excerpt(_STATE["reason"])
+        return []
+    try:
+        with tempfile.TemporaryDirectory(prefix="vision_ocr_v4_") as tmpdir:
+            png = os.path.join(tmpdir, "frame.png")
+            up = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)),
+                              Image.LANCZOS)
+            up.save(png, format="PNG")
+            try:
+                proc = subprocess.Popen([_STATE["helper"]["binary_path"], png],
+                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
+            except OSError as exc:
+                call["outcome"] = "binary_missing"
+                call["stderr_excerpt"] = _excerpt("exec error: %s" % exc)
+                return []
+            try:
+                out, err = proc.communicate(timeout=TIMEOUT_S)
+            except subprocess.TimeoutExpired:
+                proc.kill()
+                proc.wait()
+                out, err = b"", b""
+                call["outcome"] = "timeout"
+                call["stderr_excerpt"] = ""
+                return []
+    except OSError as exc:
+        call["outcome"] = "unparsable"
+        call["stderr_excerpt"] = _excerpt("render error: %s" % exc)
+        return []
+    call["exit_code"] = proc.returncode
+    call["stdout_sha256"] = sha256_bytes(out)
+    call["stdout_bytes"] = len(out)
+    if proc.returncode != 0:
+        call["outcome"] = "nonzero_exit"
+        call["stderr_excerpt"] = _excerpt(err)
+        return []
+    if not out:
+        call["outcome"] = "ok"
+        return []
+    words = []
+    for line in out.decode("utf-8", errors="replace").splitlines():
+        parts = line.split("\t", 2)
+        if len(parts) != 3:
+            continue
+        px = _PX.match(parts[0])
+        conf = _CONF.match(parts[1])
+        if not px or not conf or not parts[2]:
+            continue
+        x0, y0, x1, y1 = (int(px.group(i)) for i in range(1, 5))
+        words.append({
+            "text": parts[2],
+            "conf": float(conf.group(1)),
+            "x": x0 / float(scale),
+            "y": y0 / float(scale),
+            "w": (x1 - x0) / float(scale),
+            "h": (y1 - y0) / float(scale),
+        })
+    call["lines_parsed"] = len(words)
+    if not words:
+        call["outcome"] = "unparsable"
+        call["stderr_excerpt"] = _excerpt(err)
+        return []
+    call["outcome"] = "ok"
+    return words
+
+
+def record():
+    """Reader outcome record for the tool JSON (`"reader"`): helper resolution
+    plus one call entry per read, in call order."""
+    helper = _STATE["helper"]
+    return {"helper": dict(helper) if helper is not None else None,
+            "calls": [dict(call) for call in _STATE["calls"]]}
```

#### README.md (new file)

```diff
--- /dev/null	2026-09-17 20:58:02
+++ evidence/20260916-route/tools/v4/README.md	2026-09-17 20:54:28
@@ -0,0 +1,140 @@
+# v4 route tools — macOS Vision reader (Rev21)
+
+Read-only route-verification tools whose OCR reader is the macOS-native Vision
+framework (`VNRecognizeTextRequest`). For Rev21 and after, this set is the official
+reader of the official chain; the frozen v3 files (`../locate_album_card.py`
+`500fcadb…`, `../verify_album_open.py` `80504262…`, `../locate_album_ellipsis.py`
+`60e3120a…`) remain byte-identical history. The v4 set is self-contained and never
+imports a v3 module.
+
+| File | Role |
+|---|---|
+| `vision_reader.py` | Vision reader module (no CLI): image → v3-shaped word records + outcome record |
+| `locate_album_card.py` | album-card metadata locator (S3): v3 logic + Vision reader |
+| `verify_album_open.py` | album-open verifier (S5): v3 logic + Vision reader |
+| `locate_album_ellipsis.py` | album-level ⋮ locator (S6): v3 logic + Vision reader |
+
+## Usage
+
+Same CLI, verdicts and exit codes as the v3 tools; each tool's JSON (stdout and
+`--out`) additionally carries one `"reader"` field.
+
+```bash
+/opt/homebrew/bin/python3 v4/locate_album_card.py <frame> \
+    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 [--out x.json]
+/opt/homebrew/bin/python3 v4/verify_album_open.py <pre> <post> \
+    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 [--out x.json]
+/opt/homebrew/bin/python3 v4/locate_album_ellipsis.py <frame> \
+    --expect-start 2024/05/13 --expect-end 2024/05/17 [--title-bbox x0,y0,x1,y1] [--out x.json]
+```
+
+Interpreter: `/opt/homebrew/bin/python3` (Pillow required; `/usr/bin/python3` has no
+PIL). Read-only analysis: no GUI input, no menu item, no chooser, no keyboard/AX
+write, no capture, no download, no formal config/state/run-log/photos write.
+
+## Reader contract
+
+- Input: a PIL image plus a scale. The reader applies the `Image.LANCZOS` upscale by
+  that scale to a temporary PNG under the process temporary directory and feeds that
+  file to the helper. Scales are unchanged from v3: 3x for frame reads, 10x for the
+  count region. The temporary render path never appears in any JSON.
+- Helper resolution: `$VISION_OCR_BIN` when set — used as-is, **never rebuilt even
+  when invalid**; otherwise `<tempdir>/vision_ocr_v4_build/vision_ocr`, built exactly
+  once from the frozen Swift source `../vision/vision_ocr.swift` (SHA-256
+  `4fc9fa2b…`) with `swiftc -O` when the binary or its `source.sha256` sidecar is
+  missing/stale. The build is atomic (`vision_ocr.tmp<pid>` → `os.replace`) and the
+  sidecar contains the frozen source SHA; an existing binary with a matching sidecar
+  is reused unmodified.
+- Parse: stdout carries one line per observation,
+  `px[x0,y0,x1,y1]\tconf=NN\tTEXT`, split with `split("\t", 2)`; TEXT is kept
+  verbatim (interior spaces/tabs preserved). Vision observations are line-level: the
+  helper's own line boxes are the token unit and no re-tokenization is performed.
+  Text is never rewritten — no case folding, no width normalization, and 禎 (U+798E)
+  / 楨 (U+6968) are never merged.
+- Output: v3-shaped records `{text, conf, x, y, w, h}` in original-frame pixels:
+  `x=x0/scale`, `y=y0/scale`, `w=(x1-x0)/scale`, `h=(y1-y0)/scale` (same formula as
+  v3). `conf` is recorded evidence and is never a gate.
+- `psm` is accepted for v3 signature parity in `_tsv_rows`/`ocr_words`/
+  `ocr_digits_region` and has no Vision equivalent (unused).
+
+## Helper outcome record (`"reader"`)
+
+```json
+"reader": {
+ "helper": {"resolved_from": "env"|"build_path", "binary_path": "…",
+            "binary_sha256": "…"|null, "binary_bytes": n|null,
+            "source_sha256": "4fc9fa2b…"},
+ "calls": [{"scale": n, "outcome": "…", "exit_code": n|null,
+            "stderr_excerpt": "…", "stdout_sha256": "…",
+            "stdout_bytes": n, "lines_parsed": n}, …]
+}
+```
+
+`calls` is appended in call order (frame read then, when the title was found, the
+count-region read). `helper` is `null` and `calls` empty when a run refused before
+any OCR (missing frame, size mismatch). `resolved_from` is only `env` or
+`build_path` — never `built`/`cached` — so the record is identical on the first
+(building) and every later run.
+
+Parse order and the fail-closed outcomes (any failure returns empty words, and the
+tool then follows its frozen v3 refusal path — never a crash, never a guessed value):
+
+| Outcome | Condition |
+|---|---|
+| `ok` | helper exit 0; at least one valid line parsed. Empty stdout is also `ok` with 0 words |
+| `binary_missing` | resolved helper missing or not executable (`$VISION_OCR_BIN` invalid → no rebuild) |
+| `build_failed` | fixed-path build was needed and failed (frozen source missing/sha mismatch, swiftc error, sidecar write error) |
+| `nonzero_exit` | helper exit ≠ 0 (2 usage, 3 image load failure, 4 recognition failure) |
+| `unparsable` | helper exit 0, stdout non-empty, no valid `px[…]` + `conf=…` line with non-empty TEXT |
+| `timeout` | no exit within 60 s → kill (no pipe drain; a helper grandchild cannot stall the reader); `exit_code` null |
+
+Exit 2/3/4 or a missing helper = failure; empty stdout = success with 0 words; a
+line yields a word only when `px[x0,y0,x1,y1]` and `conf=NN` parse and TEXT is
+non-empty. `stderr_excerpt` is `""` on success and ≤200 chars otherwise; for
+`binary_missing`/`build_failed` it carries the reader's short reason (there is no
+process stderr), and `timeout` records `""` because the pipes are not drained. A
+render-stage `OSError` (e.g. temporary-file failure) is recorded as `unparsable`
+with a `render error: …` excerpt; it never raises out of the reader.
+
+## Determinism (C2) scope
+
+- In scope: for a given input, the helper's stdout bytes and the v4 tools' JSON
+  bytes must be identical across repeats. The `"reader"` field is part of that
+  identity (no timestamps, no process-unique render paths; the only path recorded is
+  the env value or the fixed build path).
+- Out of scope: the agent-attempt `summary.json` (it records timestamps/argv by
+  design), and the helper binary's own bytes (`swiftc` output is not
+  byte-deterministic; equivalence is shown by identical stdout on the same input).
+
+## v4 = v3 logic + reader layer only
+
+Diffing v4 against the frozen v3 files shows exactly these hunks (nothing else):
+
+- `locate_album_card.py`: docstring +1 line; tesseract-only imports (`io`,
+  `subprocess`) dropped and `importlib.util` added for the sibling loader;
+  `_load_sibling` + `vision_reader = _load_sibling("vision_reader")` added;
+  `_tsv_rows` body = `return vision_reader.read_words(image, scale)`;
+  `ocr_words`/`ocr_digits_region` call `_tsv_rows` with the unscaled/cropped image
+  (the LANCZOS upscale moved into the reader; call sites and `or []` unchanged);
+  `emit` +1 line (`result["reader"] = vision_reader.record()`).
+- `verify_album_open.py` / `locate_album_ellipsis.py`: docstring +1 line;
+  `emit` +1 line (`result["reader"] = card.vision_reader.record()`).
+  Everything else is byte-identical, including `_load_sibling`, the sibling
+  `locate_album_card` load, every threshold, verdict, exit code, refusal path and
+  geometric parameter.
+
+Known seam notes: `_tsv_rows` now receives the unscaled image (the 3x/10x LANCZOS
+factors are unchanged) and returns `[]` instead of `None` on failure — the callers'
+`or []` makes both identical.
+
+## Phase 0 baseline field `byte_identical_to_recorded` (semantics)
+
+`evidence/20260917-vision-reader/phase0/baseline.json` is append-only committed
+evidence (commit `adf1829`) and is never rewritten. Its
+`helper_rebuild.byte_identical_to_recorded` recorded a *that-day* observation:
+`sha256(/tmp/vision_ocr)` equalled the historical volatile-binary SHA `f54628e8…`.
+It is not a reproducibility claim: `swiftc` output is not byte-deterministic, and
+the helper binary is not the acceptance key. Later re-verification keys on the
+durable frame copies (`evidence/20260917-vision-reader/frames/` + `manifest.json`)
+and the recorded raw-stdout SHAs (post `5c86dda8…`, pre `07e3e156…`, s1
+`561bb131…`, s2 `abf9d75e…`) — never on volatile `/tmp` content.
```

## 11. Artifact hashes (consolidated)

### 11.1 This wave's new artifacts

| Artifact | SHA-256 |
|---|---|
| tools/v4/vision_reader.py | 22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8 |
| tools/v4/locate_album_card.py | bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162 |
| tools/v4/verify_album_open.py | ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58 |
| tools/v4/locate_album_ellipsis.py | b77e3d51d43e6cb4a0a1b7bf2e9e1179a2718d7867ac01b5344fbcd07cef96c4 |
| tools/v4/README.md | ed3ebf0aad53024f3e4fe7d4886faa9b37c048e2fdf95513ab3bc7bafe677f23 |
| selftest/v4/selftest-summary.json | 5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d |
| selftest/v4/run_selftest.py | 7182d5760821b0e3464316722a20fc1af9cfedddf374f0509c65b7a95299f690 |
| selftest/v4/README.md | 1c2f3d7a5fc5de3ff99c87645d1723a4c15c137115b2ceba097398c038639c9f |
| agent-e2e/attempt-01/summary.json | 0ee83325286ba64a9817b93427a6562e1a4d73c205043103e33f074b68cf8aad |
| agent-e2e/attempt-01/SHA256SUMS | 0c51198075dfb5ef922e401a0a75e6f7e7b2b90370a5ed8e8ee4b191195078e3 (38 lines, 38/38 verified OK) |
| agent-e2e/runner/run_agent_e2e.py (v1.1.0) | cd0aa1511ae45af32cb4497ddc0a7532053a4ebfd13fdaea55f451e13f06c93c |
| agent-e2e/README.md | 59edb445ea3a83497518cfe74868338a476466be9e688f53ee0882b3d6cf70e2 |
| execution-rev21.md (this file) | self-hash not embedded; reported in the Stage-04 message and re-hashed by Stage 05 |

### 11.2 Helper binary

| Artifact | Value |
|---|---|
| helper binary path (fixed, deterministic) | /var/folders/0r/r3qmjfbn0z57mtmdxmnp60c80000gn/T/vision_ocr_v4_build/vision_ocr |
| helper binary SHA-256 / bytes | c7087d98a1035db39b39906b8da995fa41e3ed52ac4b34481d1213d4fe6eb0b5 / 67,200 |
| helper source SHA-256 (`vision_ocr.swift`) | 4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32 |

### 11.3 Frozen anchors (re-verified §9)

v2 tools `6ae9c250…`, `8c8b6fc7…`; v2 self-test summary `d8ffc129…`;
v3 tools `500fcadb…`, `80504262…`, `60e3120a…`; v3 self-test summary `17840e91…`,
runner `94a41092…`, README `76bda610…`; helper source `4fc9fa2b…`;
attempt-05 `run-ledger.json` `17b17203…`, `album-open-verify.json` `ffa5d963…`,
`vision-ocr-crosscheck.json` `d3ebbaed…`; frames `4cb8a6b4…`, `3d926e7d…`,
`aea53a0d…`, `7b9d0a19…`; plan `466bda4a…`; handoff `df595831…`;
`execution.md` `d5401148…`; `execution-rev19.md` `8302005a…`.

## 12. No-side-effect declarations

Own Stage-04 runs and the agent-e2e attempt: GUI inputs 0, screen captures 0,
model/API calls 0 in the runner loop, formal-data writes 0, downloads 0,
v2/v3/frozen/plan/handoff files untouched. No image data appears in this record.
`inputs_sent: 0`, `ui_interaction: none` are recorded in `attempt-01/summary.json`.

## 13. Deviations

- None material. A transient `tools/v4/__pycache__` created by a parallel teammate's
  imports was removed before the commit; no tracked file was modified and no pinned
  artifact changed. The `post` frame's `UNSAFE_MARGINS`/exit 4 is the untouched v3
  geometry rule recorded as-is (§7.1 note 3), not a deviation.

## 14. Stage-05 hand-off

Stage 05 binds to the approved Rev21 hash `466bda4a…`, consumes the next unused
`.agent/tasks/<TASK_ID>/e2e/attempt-NN/` (06 at this writing), re-runs the same frozen
inputs, independently re-derives the tuple, and must not trust this summary.
`ACCEPTANCE_MODE: INTEGRATION` — offline replay over durable artifacts; never
reported as live E2E.
