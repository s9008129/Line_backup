# Stage 04 execution record — LINE album acceptance (Rev19 wave)

`workflow-routing` §7.11 durable execution record for the Rev19 wave (W-USER-FACT-V1.1, W-ROUTE-PREFREEZE,
W-ROUTE-ATTEMPT-04, W-DELTA-RECORD). The frozen Rev18-wave record `execution.md` is preserved untouched; this file is
the Rev19 record and must not be read as an amendment of it.

IDENTITY
- TASK_ID: `T20260916-0102-01-line-backup-acceptance`
- PLAN_REVISION: `19`
- PLAN_SHA256: `10ec0f032788982bb9cb270918829ca4b30fdcfbf156b82ac442df29fca07aff` (1,600 lines / 217,588 bytes; re-verified at wave start)
- HANDOFF_SHA256: `361d4b274be61921db63b99d8f7e09c743a158a53c704dc81dd015a9a4534e3b` (134 lines / 28,104 bytes; Rev19-bound; old Rev18 handoff archived at `handoff-history/handoff-plan-r18-20260917-154007.md`, `9cf01d4e…`)
- PLAN_APPROVAL: `review/attempt-26/review_report.md` FINAL_STATUS `PLAN_APPROVED` + `review/attempt-27/review_report.md` FINAL_STATUS `PLAN_APPROVED` (dual fresh review bound to Rev19 at the SHA above)
- IMPLEMENTATION_MODE: `FRESH_STAGE_04`, orchestrator-run. This wave sent exactly ONE authorized GUI input (the §19.2 one-shot ⋮ click, attempt-04); every other action was read-only. No product code, fixture, config, state or run-log edit.
- STAGE_04_ANCHOR_HEAD: `2983f44` (W1–W3 commit: v1.1 record + attempt-04 pre-freeze artifacts). This record and the attempt-04 post-run artifacts are the wave's W4 commit.
- EXECUTION_DATE: `2026-09-17`; local timezone `+0800`
- WAVE COMMITS: `2983f44` (W1–W3), plus this commit (W4: route result, ledger finalization, manifest, execution record)

## 1. Result first — six orthogonal statuses (Status Contract v2)

Snapshot taken by the implementer at the end of the wave; it pre-claims nothing about independent acceptance.

| Subject | Status | Basis |
|---|---|---|
| PRIMARY_OUTCOME_STATUS | `UNKNOWN` | Unchanged by this wave and deliberately not promoted by Stage 04. Result (1) album data: task-level source correspondence now has its basis (v1.1 record passes §16.4) but the promotion to ACHIEVED is a Stage 05 act; result (2) reusable capability: proven (carry-forward). The route experiment returned AFFIRMATIVE for the control it was authorized to test, while the album's own download ⋮ (owner-identified in the same session) remains unobserved — see §5. |
| IMPLEMENTATION_STATUS | `COMPLETE` | All four Rev19 wave deliverables exist with evidence: corrected record v1.1 + authoring note + §16.4 re-run; frozen gate/runbook/tools; the attempt-04 run and its six artifacts; this record. No implementation work remains inside Rev19. |
| CORE_ACCEPTANCE_STATUS | `PASS` (scoped) | All 11 CORE checks carry verified results: the six long-standing checks carry forward from Stage-04/05 attempts with unchanged artifacts; `FORMAL_STATE_READONLY_RECONCILIATION` re-verified (baseline byte-identical); `SOURCE_CORRESPONDENCE` now PASS at task level via the §19.1 v1.1 record (§16.4: 16/16 assertions, matcher true; v1 false for reference) with the product-level Source axis explicitly staying `UNRESOLVED`; `CUA_ROUTE_DECISION` PASS as the frozen §19.2 question ("does one authorized ⋮ input yield a machine-observable menu") answered AFFIRMATIVE, with the scope limitation recorded (album-list card menu; no download item exercised). `INDEPENDENT_ACCEPTANCE` remains the one open CORE item (NOT_RUN — see §5). |
| REQUIRED_VERIFICATION_STATUS | `PASS` | No verification debt: baseline re-run with the plan's literal argv is byte-identical (`baseline_delta=UNCHANGED`); every artifact has bytes/SHA-256 recorded; the attempt-04 ledger closes with 9 events and matching counts; no check is silently omitted. |
| INDEPENDENT_ACCEPTANCE_STATUS | `PENDING` | Stage 05 attempt-06 has not run. Deferred by design, not blocked — see §5 (a new revision would void this handoff, so the acceptance wave must bind to the then-current revision; plan.md:1584-1592). |
| TASK_CLOSURE_STATUS | `READY_FOR_INDEPENDENT_ACCEPTANCE` | Scoped CORE blockers of attempt-05 are closed by this wave's evidence; the only remaining act is independent acceptance, whose timing is sequenced in §5. |
| BASELINE_REGRESSION_DELTA (check) | `UNCHANGED` | Named subject `AUTHORITATIVE_INPUT_AND_EXISTING_DESTINATION_INTEGRITY`: `tests/authority_baseline.py` re-run after the wave produced a byte-identical snapshot (`ab6747f2…85b5`, 19,005 bytes) — formal config/state/run-log and all 57 files unchanged; the GUI input wrote nothing. |

Plain-language owner view: the two things that were stuck are both unstuck. (1) The 57 files can now be attributed to
the requested album through the corrected confirmation record (the format error is fixed in a *new* file; your original
answer file was never touched). (2) The automatic ⋮ click was proven to really open a menu — we captured it five times
and read its items. But you then told us the ⋮ we clicked is the one on the album *list*, and that the ⋮ you actually
need is *inside* the album; that is a new instruction for a new one-shot attempt, which needs your authorization again
(§5). Nothing was clicked beyond that single ⋮, no download, no delete, no state change; the menu itself was left open
for you to close.

## 2. Check matrix — authoritative 13 rows (plan.md:1505-1519) with this wave's results

Policy columns are the plan's table; `CHECK_RESULT`/`WAIVER_STATUS` are the observed results at the end of this wave.

| CHECK_ID | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_RULE | FAILURE_ROUTING | WAIVER_ALLOWED | WAIVER_AUTHORITY | CHECK_RESULT | WAIVER_STATUS |
|---|---|---|---|---|---|---|---|---|---|
| VERIFIER_FALSE_POSITIVE_REPRO | CORE | OUTCOME | HARD_CLEAN | REQUIRED | old false acceptance not reproduced invalidates baseline | NO | NONE | `PASS` (carry-forward; artifacts unchanged) | NOT_ALLOWED |
| VERIFY_REAL_DESTINATION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | incorrect axis/exit/artifact or false acceptance is TASK_REGRESSION | NO | NONE | `PASS` (carry-forward; destination byte-identical) | NOT_ALLOWED |
| VERIFY_NEGATIVE_FIXTURES | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | malformed/unsafe acceptance or axis conflation is TASK_REGRESSION | NO | NONE | `PASS` (carry-forward) | NOT_ALLOWED |
| TRANSACTION_RESUME_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | repeat dispatch or barrier bypass is TASK_REGRESSION | NO | NONE | `PASS` (carry-forward) | NOT_ALLOWED |
| TRANSACTION_COMMIT_CORE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | stale/split/uncertain commit or false terminality is TASK_REGRESSION | NO | NONE | `PASS` (carry-forward) | NOT_ALLOWED |
| FORMAL_STATE_READONLY_RECONCILIATION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | formal mutation or contradiction is TASK_REGRESSION/BLOCKED | NO | NONE | `PASS` (fresh baseline re-run; byte-identical) | NOT_ALLOWED |
| SOURCE_CORRESPONDENCE | CORE | OUTCOME | HARD_CLEAN | REQUIRED | missing authority is scoped BLOCKED/UNRESOLVED; contradiction is FAIL | NO | NONE | `PASS` (task level, v1.1 §16.4 16/16 + matcher true; product Source axis stays UNRESOLVED) | NOT_ALLOWED |
| CUA_ROUTE_DECISION | CORE | OUTCOME | HARD_CLEAN | REQUIRED | missing/ambiguous route evidence is scoped BLOCKED/UNKNOWN; no dispatch | NO | NONE | `PASS` (scoped: AFFIRMATIVE on machine-observable menu evidence for the authorized input; album-download route still unobserved, routed to a later revision) | NOT_ALLOWED |
| STATUS_CLOSURE_CONTRACT | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | illegal enum/routing/self-waiver is TASK_REGRESSION | NO | NONE | `PASS` (canonical vocabulary used; no self-waiver; new owner evidence routed to a later revision, never improvised into this wave) | NOT_ALLOWED |
| INDEPENDENT_ACCEPTANCE | CORE | MUST_NOT_BREAK | HARD_CLEAN | NONE | missing independent result remains PENDING/BLOCKED | NO | NONE | `NOT_RUN` (Stage 05 attempt-06 PENDING; sequencing in §5) | NOT_ALLOWED |
| BASELINE_REGRESSION_DELTA | CORE | MUST_NOT_BREAK | BASELINE_DELTA | REQUIRED | new/worsened signature or silently omitted old signature | NO | NONE | `PASS` (`UNCHANGED`) | NOT_ALLOWED |
| BRIDGE_READINESS | SUPPORTING | DIAGNOSTIC | NON_GATING | NONE | non-gating unless route-specific necessity is proved | YES | Project owner, exact scope | `NOT_RUN` (non-gating; still no necessity proof) | NOT_REQUESTED |
| DOCUMENTATION_RETENTION_HEALTH | SUPPORTING | REPOSITORY_HEALTH | HARD_CLEAN | NONE | within task-evidence scope, missing raw records/read-back makes acceptance non-reproducible | YES | Project owner, exact scope | `PASS` (all raw records, argv, outputs, bytes/SHA-256 present; frozen Rev18 `execution.md` preserved) | NOT_REQUESTED |

## 3. Per-deliverable commands, results, evidence

1. W-USER-FACT-V1.1 (CORE; plan.md:30-71) — `PASS`
   - Construction: deterministic re-authoring of `evidence/20260916-user-fact/source-identity-user-fact.confirmed.v1.1.json` from the frozen v1 via `build-user-fact-v1.1.py` (5,336 B, `669240f7…`), asserting 1,741 bytes + SHA-256 `a8c1055137d14026f7ecbc15b4f06ee540b56114af3276b081a0be72d195c263` before writing.
   - Observed: v1.1 = 1,741 B / `a8c10551…`; exactly one changed line (line 30, `answer.part_2.confirmed_album` = `2024/05/13～05/17`, U+FF5E); key sets equal to v1 at top level and inside `answer`/`answer.part_2`; `record_version` stays `"1.0"`; no other leaf drift; v1 (1,746 B / `2cd7eccd…`) and the gate artifact (1,438 B / `03ffff57…`) byte-identical.
   - §16.4 re-run (`PYTHONPATH=src /usr/bin/python3` + `line_backup_acceptance.common.user_fact_v1_matches`, common.py:533): 15/15 in-script conditions true, `matcher_result=true`, `v1_matcher_result_for_reference=false`, `CHECK_RESULT: ALL_TRUE` (16 of 16 overall boolean assertions).
   - Evidence: `source-identity-user-fact.confirmed.v1.1-authoring-note.md` (11,789 B / `1fbddc4b…`), the record itself, the build script.
   - Scope: task-level acceptance basis only; the product CLI's Source axis for the real destination stays `UNRESOLVED` and is never reported as CONFIRMED.

2. W-ROUTE-PREFREEZE (CORE; plan.md:72-112) — `PASS`
   - `gate-2-authorization.json` (3,821 B / `f3d17790…`) records the owner's verbatim `2.要，授權給你` (2026-09-17T14:59:40.847+0800, transcript line 5091) and the auxiliary menu question as `UNANSWERED`.
   - Frozen before any click: `route-runbook.md` v2 (7,101 B / `30253892…`), `detect_menu_popup.py` (6,339 B / `6ae9c250…`) with self-tests (summary 2,946 B / `d8ffc129…`), `locate_card_ellipsis.py` (8,943 B / `8c8b6fc7…`), `run-ledger.json` parent chain (`77c4f86c…`).

3. W-ROUTE-ATTEMPT-04 (CORE; plan.md:72-112, 1475-1490) — executed exactly once, `AFFIRMATIVE`
   - One left click at window-relative `[304,446]` (current-frame-derived; identical from the pre-frame and probe-crop locator runs), click_count=1, zero retries, zero conversation images, at ~2026-09-17T15:57:37.6+0800.
   - Screen-scope probe accepted at scale 1 (frozen locator ELIGIBLE on the s1 AX-window crop; `PERMISSION_PROMPT_OBSERVED=false`).
   - Post observation: window frame + AX (AX byte-identical, no menu element), then five screen captures at +488…+940 ms.
   - Frozen detector: window-scoped `NOT_DETECTED` (only a 21×24 halo on the control, 306 changed px); screen-scoped `MENU_DETECTED 5/5`, chosen bbox `[20,72,254,312]` identical in all five, region pixel-stable across the burst (0 changed px cap1↔cap5).
   - Menu transcription (per-row OCR, capture 1): `上傳項目 / 修改相簿名稱 / 分享相簿 / 刪除相簿` — album-management items with no download/Save-All entry; the menu was left open and untouched.
   - Evidence: `attempt-04/{route-result,run-ledger,manifest,screen-probe,menu-analysis,ellipsis-locate}.json`; route-result `6f71c5e7…` (15,747 B), ledger final `df0e9c44…` (11,463 B), menu-analysis `81d430bd…` (11,910 B), screen-probe `912e962b…` (5,243 B).
   - Zero side effects: no menu item, no Save All, no chooser, no keyboard input, no navigation/scroll, no state/config/run-log write, no re-download; frames not committed (bytes/size/SHA-256 only).

4. W-DELTA-RECORD (CORE deliverable) — `PASS`
   - All six attempt-04 artifacts written; ledger finalized with 9 events, `final_counts.ellipsis_inputs=1`, `route_result_sha256` bound; manifest lists every artifact, tool and /tmp observation with bytes/SHA-256; this execution record written; the frozen Rev18 `execution.md` untouched; prior attempts (01–03) untouched.

## 4. Stage 05 snapshot fields (for attempt-06 to read before accepting)

- TASK_ID: `T20260916-0102-01-line-backup-acceptance`
- PLAN_REVISION: `19`; PLAN_SHA256: `10ec0f03…`; HANDOFF_SHA256: `361d4b27…`
- STAGE_04_EXECUTION_ARTIFACT: `.agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev19.md` (this file; hash recorded in the wave commit)
- STAGE_04_REPORTED_IMPLEMENTATION_STATUS: `COMPLETE`
- STAGE_04_REPORTED_CORE_ACCEPTANCE_STATUS: `PASS` (scoped; `INDEPENDENT_ACCEPTANCE` NOT_RUN)
- STAGE_04_REPORTED_REQUIRED_VERIFICATION_STATUS: `PASS`
- STAGE_04_REPORTED_PRIMARY_OUTCOME_STATUS: `UNKNOWN` (not promoted by Stage 04)
- EXECUTION_TIMESTAMP: `2026-09-17` (wave run 15:45–16:2x +0800)
- EVIDENCE_PATHS: `evidence/20260916-user-fact/*v1.1*`, `evidence/20260916-route/attempt-04/*`, `evidence/20260916-baseline/attempt-02/baseline-pre.json`, `.agent/tasks/.../review/attempt-26|27/*`, `.agent/tasks/.../plan.md`, `.agent/tasks/.../handoff.md`

## 5. Scoped items carried forward (nothing hidden)

1. **Stage 05 attempt-06 is deferred, not blocked.** The owner's post-run messages (2026-09-17T16:00:03 and 16:01:49,
   verbatim in `route-result.json:supplemental_owner_observations`) direct a corrected route — first open the album, then
   use the ⋮ inside it. Any GUI input beyond the consumed one-shot needs a new gate + a new `PLAN_REVISION` + fresh review
   (plan.md:72-112, 1584-1592), and a new revision voids this handoff and any approval bound to it; Stage 05 must
   therefore accept the then-current revision, so the acceptance wave runs after the route question settles instead of
   being wasted on a stale revision.
2. **Intended album-download route remains unobserved.** `CUA_ROUTE_DECISION` is PASS only for the scoped experiment
   (machine-observable menu for the authorized ⋮ input). The album's in-album ⋮ / download menu was never observed; no
   download/Save-All route is established, and production Save-All stays outside every wave (plan.md:1485-1490).
3. **The observed menu's anchor is unexplained.** It rendered at the window's upper-left rather than at the input point;
   mechanism unobservable (menu-analysis.json:menu_identity.anchoring). Recorded so the next wave's runbook can account
   for how the runtime delivers clicks and where popups render.
4. **Disclosed axis facts, unchanged:** Registry=`FAIL`, State=`LEGACY_PROVENANCE_LIMITED`, product Source=`UNRESOLVED`
   for the real destination; these are axis facts, never to be reported as contradictions or as CONFIRMED.
5. **Owner action pending from the run:** close the ⋮ menu that was intentionally left open (no key or click was sent by
   this wave).
