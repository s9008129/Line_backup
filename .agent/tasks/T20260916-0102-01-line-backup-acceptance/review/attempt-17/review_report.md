# Stage 02 Independent Plan Review — attempt-17

- TASK_ID: `T20260916-0102-01-line-backup-acceptance`
- Reviewed artifact: `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`
- PLAN_REVISION: **14 (CANDIDATE)**
- PLAN_BYTES: **123211**
- PLAN_SHA256 (self-computed): **bbedee40f0c6619cb662fe9dd54911d7bbb2d3f0a76f3954bb0c64f65a5aa97f**
- Snapshot: `review/attempt-17/plan-snapshot.md` (identical byte length and SHA-256; copied 2026-09-16T12:17:18Z, hash re-verified 2026-09-16T12:51Z before this report was written)
- Review time: 2026-09-16T12:51Z
- READ_ONLY: **YES**. No product CLI or test driver was executed. No reviewed artifact was modified (`plan.md`, `src/**`, `tests/**`, `evidence/**`, `handoff.md` untouched; `review/attempt-01..16/` untouched). Only file written: this report.
- GATE: **PLAN_REVISION_REQUIRED**

---

## Goal Baseline (reconstructed from authoritative sources, before reading the plan's framing)

Sources: user `/goal` (`~/.codex/attachments/210176d8-3c5b-4400-8443-d74a5ffcaa65/pasted-text-1.txt`), `handoff.md` H2.1 (§0–§14), `evidence/20260916-user-fact/source-identity-user-fact.json`, and direct read-back of `evidence/20260916-auto-verification/attempt-01/`.

1. **Primary owner outcome**: LINE macOS album backup should become fully automatic; this milestone is to make the **automation verification** real — reproduce handoff §7 R1–R7 through the real entry (no predictive fault flags manufacturing safety), fix them, and leave rerunnable, independently re-readable evidence. Do not add PASS numbers or documentation instead. (handoff.md:19–22; /goal 【任務】)
2. **Scope**: exactly one album — app `jp.naver.line.mac`, group 「旻謙允禎成長日記」(禎 U+798E), album 2024/05/13–05/17, 57 images. If the existing 57 files are valid, use verify-only; **never redownload for a test**. Formal config/state/run-log and the 57 photos are read-only absent a new explicit gate. (/goal 【範圍】; handoff.md:22, §3)
3. **Two scoped blockers, only two legal resolutions**: (B1) source identity — the request uses 禎 (U+798E) while formal config/state use 楨 (U+6968); merge/normalization/inference from equal date/count/hash is forbidden; resolution is an authoritative exact source join or one precisely preserved user fact (original question, answer, supplier/time, evidence SHA-256). (B2) GUI observation gate — after all non-GUI work, **one** precise gate permitting exactly one current-target ellipsis observation with immediate post-evidence; it authorizes no menu item, Save All, chooser, shortcut, state write, or download; historical ellipsis credit is exhausted. (/goal 【兩個 blocker】; handoff.md:106–134)
4. **R1–R7 are the CORE gap list** to reproduce and repair through the real entry, with external oracles; fixes touching safety/persistence/success semantics must go through CRITICAL (Rev increments, fresh independent review, recompiled handoff, fresh implementer). Old approvals (Rev13, review/attempt-16) do not carry over. (/goal 【怎麼做】/【範圍】; handoff.md:165–189)
5. **Hard rules**: no admin/sudo/TCC-triggering commands; no AXPress/AX-write/guessed coordinates/OCR-only PASS/sandbox workaround; never overwrite evidence/attempt/result.md (append-only, keep failures); never repeat Save All when dispatch outcome is unknown; `/private/tmp` is not durable storage; every attempt keeps argv/env (secrets removed), stdout/stderr/exit, program hashes, independent side-effect counters, before/after state and SHA-256+bytes manifests, all independently re-readable. (/goal 【硬性禁令】【證據規則】; handoff.md:293–316)
6. **Three separately reported results**: (1) album data result, (2) reusable automation capability, (3) overall closure; `complete` only when 1 and 2 hold; offline/fixture PASS must never masquerade as GUI end-to-end success. (handoff.md:24–28; /goal 【三個結果分開報告】)
7. **Verification truthfulness**: fake adapters may replace external I/O only; they must not manufacture VERIFIED; Phase 2 reproduction must state claim / tested entry / external oracle / how the result changes the next step; no expectation relaxation or authority widening to pass a test. (/goal 【怎麼做】Phase 2/4/5; handoff.md:220–259)

**Baseline conclusion:** Rev14's job is a truthful F1–F7 fix contract for R1–R7 executable at the real operator boundary, a deterministic acceptance matrix whose oracles are computed before product output, one exact GUI gate, and three-result closure semantics. Any design that cannot be grounded in the versioned skill schema/state contract, or that changes the accepted expected behavior only in test code, fails this baseline.

## Method

- Top-down pass: goal alignment, necessity (CORE/SUPPORTING/BEST_EFFORT), critical-path ordering, gate/veto proportionality, failure containment, coupling, design economy.
- Bottom-up pass: repository grounding against `schemas/schemas.json`, `references/state-contract.md`, `references/verification.md`, `SKILL.md`, current product source (`src/line_backup_acceptance/*.py`), current test drivers, and direct read-back of `evidence/20260916-auto-verification/attempt-01/`.
- Adversarial checks specifically requested for Rev14 (F1–F7 vs R1–R7, source-join binding, F5, F6, verification sufficiency, R5(c) variance, human gate, over/under-scope) are folded into the findings below.

Evidence read back directly (not just trusted from prose):

- `readback-verification.json`: 84 manifests, 4859 artifacts, 0 problems, 0 uncovered files, verdict PASS.
- `baseline-pre.json`: 19005 bytes, SHA-256 `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5` (matches handoff §11).
- `phase2-r1/observation.json`: kill-after-dispatch then fresh resume dispatched again; independent counter 1→2; `REPRODUCED_DUPLICATE_DISPATCH`.
- `phase2-r2/observation.json`: `prepare` then fresh-process `resume` dispatched once (`DISPATCH_RETURNED`); `--no-dispatch` probe performed 0 side effects.
- `phase2-r6-ownership/observation.json`: both `authority_negative_driver.py` and `test_transaction_core.py` destroyed all twelve shared `/private/tmp/line-backup-acceptance-case-01..12` roots.
- `phase2-r7/observation.json`: `integration_closed=false`, duplicate bypass after terminal, verify-only did not close the loop.
- Program hashes in phase-2 records equal handoff §4 values (`transaction.py c486edbe…`, `verifier.py b38ee6d5…`, `status.py 20a95f7c…`, `authority.py a98964e3…`, `cli.py a5bbbbf6…`, `common.py 59a85c47…`).

---

## Top-down review

### Goal alignment

- F1–F7 trace one-to-one to R1–R7 (plan.md:29–47 → plan.md:54–148); no orphan fix and no unfixed gap. The two blockers stay scoped: source identity is handled by the recorded user fact / join requirement (F3/F4), and the GUI gate is exactly one message that authorizes one ellipsis observation only (plan.md:171–184), matching /goal and handoff §5/§6.
- Three-result closure is present and orthogonal (plan.md:186–202), including "offline/fixture PASS is never reported as GUI E2E" and "Done means overall closure only".
- The plan's own guard against test-passing behavior exists (plan.md:52: "No fix may change an expectation, relax an authority allowlist, or add a fixture-only back door in order to pass a test") — see Finding F-1 for where Rev14 currently violates its own guard.

### Necessity, critical path, gate proportionality, design economy

- **F1 core design is the minimal contract-enforcing repair, not an overreach.** state-contract REQUIRED #3 (references/state-contract.md:90) and SKILL.md step 6 both require the *same uninterrupted execution* that just persisted/read back the intent to perform the one dispatch, and forbid a loaded intent from granting a fresh action. Because the accepted harness runs `prepare` and `resume` as separate processes, dispatch cannot legally remain in `resume`; moving it into `prepare`'s process is both minimal and necessary. No smaller equivalent design was found: an in-resume continuity token would still cross a process boundary, which is exactly the reproduced R2 gap.
- **F2 is proportionate**: one shared precondition evaluator reused by `duplicate-check`/`prepare`, refusal-before-write, and no new state. The `--source-evidence` requirement is the direct minimal answer to R3(e)'s fabricated `[1,1]`/HIGH/"test fixture" calibration.
- **F4's decode hardening is proportionate to a reproduced false PASS**: PNG CRC+zlib/IEND and JPEG marker/EOI checks are the minimum deterministic tests that reject the reproduced truncated-PNG PASS; fail-closed for other image types is honest. The residual "structurally closed but corrupted JPEG body" limitation is disclosed (plan.md:122).
- **Gate/veto proportionality**: supporting items (bridge/service diagnosis) remain explicitly non-gating (plan.md:184 "not proof that any bridge is necessary"; handoff §1 SUPPORTING/BEST_EFFORT rules), and R5(c) degradation is stated as a misclassification-vs-false-PASS distinction rather than silently upgrading the fix claim (plan.md:42, 114–116). This is honest and correct.
- **Over-scope check**: F3's "binding artifact lives under the selected project root, written atomically by prepare" is the one real scope growth — it introduces a new persisted artifact without declaring it inside the contract's authorized write set or the versioned schema (Finding F-2). F5's added output field is trivial and fixture-compatible (positive below). Everything else stays inside "one album, verify-only, formal read-only".
- **Primary risk**: the plan simultaneously holds two sources of truth for accepted behavior — the Rev14 fix contract and the still-live Rev13 deterministic case matrix/grammar. Findings F-1/F-6 make that split explicit.

---

## Bottom-up review (repository grounding)

- **Schema grounding (blocking).** `schemas/schemas.json` `$defs/run` and `$defs/intent` are `additionalProperties:false`; neither declares `source_provenance` (run also lacks `owner_id`). Current product `transaction.py:16` writes `source_provenance` and `owner_id`, so the existing run object is already schema-invalid — the same class of defect R4 recorded for the registry entry. Rev14 F3 fixes only the registry entry shape and *requires* the run to keep carrying `source_provenance`, so it does not resolve R4's "schema forbids extra properties" root cause.
- **Authorized write set.** state-contract.md:37 restricts writes to (A) contract-permitted control/state paths from X and (B) backup_root + destination, with verify_only an empty write set; no new artifact path is declared anywhere in the skill contract. F3's project-root binding artifact therefore has no declared authority base, and a second artifact file beside `state/backup_state.json` risks becoming a second authority (state-contract.md:11 "State is the authoritative machine registry").
- **Current verifier confirms the R4 defect.** `verifier.py:172` computes `source_proof` from `exact[0].get("source_authority")`, a field the registry schema forbids; F4's `verified_run_id`-resolution design is the right direction but its storage location is unresolved (F-2).
- **Case protocol grounding (blocking).** The literal argv/revision oracles in plan.md:480–487 and 510–518 still encode the pre-F1 protocol (dispatch on `resume`, barrier committed before the adapter side effect, cases 01/02/03/04/09 passing `--dispatcher`/`--dispatch-counter`/`--dispatcher-outcome` to `resume`). They directly contradict F1 at plan.md:57–65. Stage 04/05 cannot satisfy both. The same applies to the "Transaction subprocess entry point" literal at plan.md:305, the resume grammar at plan.md:311, and the restart bullet at plan.md:476.
- **Authority-flag precedence is unspecified.** plan.md:313 promises authority validation is the first *filesystem* operation after argument parsing, while F1 (plan.md:61) rejects adapter flags with `INVALID_INPUT` "in every mode". The eleven authority rows at plan.md:445 (row 2, row 6) and plan.md:447 (row 2) feed resume commands *with* dispatcher flags and require `INVALID_AUTHORITY` with a JSON error artifact. If flag rejection happens at parse time or before `validate_transaction`, those rows lose their class/evidence; if it happens after, the row still passes. This must be pinned in the plan (Finding F-1d).
- **Resume behavior is under-specified beyond one case.** F1 defines reconciliation only for a loaded non-terminal `INTENT_COMMITTED` intent. Undefined: a loaded `TRIGGER_UNKNOWN`/manually-reconciled intent (repeat resume), or a `SAVE_ALL_DISPATCH_ATTEMPTED` non-terminal state after the post-dispatch commit. Since the matrix asserts exact revisions, repeated-resume idempotence must be specified (Finding F-1e).
- **F5 compatibility verified (positive).** `tests/status_fixture_driver.py:136–160` compares only the six status fields, `blocker`, `checks`, `baseline_delta`, `failure_class`, `waiver`, plus stdout==output-file JSON, so adding `evidence_basis` to the product output does not break any existing fixture oracle. Caveat: no oracle asserts the new field, so F5's requirement can regress silently (Finding F-4e).
- **F6's rule is right but its fix list is incomplete.** `tests/acceptance_case_driver.py:83` unconditionally `rmtree`s the whole case root; `tests/verifier_fixture_driver.py:114,138`, `tests/automation_verification/run_phase2_r1:41`, `r2:31`, `r3:64,311,416`, `r4:85`, `r5:141,306,309`, `r6:226`, `r7:73,142`, `fixtures.py:55`, `harness.py:185`, and `tests/legacy_false_positive_repro.py:30,71` also remove roots/evidence — several on the shared literal case-01..12 roots used by the acceptance matrix. Fixing only the two drivers F6 names (plan.md:135) cannot make "any order or parallel re-run" true.
- **Safety and evidence discipline check (positive).** Formal root stays read-only; fixture writes stay under literal `/private/tmp/line-backup-acceptance-*` roots; the human gate authorizes no download/menu/chooser/shortcut/state write; evidence attempts are append-only and the wave's own read-back verifier passed (84 manifests / 4859 artifacts / 0 problems). The plan also keeps DONE gated on `CONFIRMED` source correspondence and refuses to promote `UNRESOLVED`/`LEGACY_PROVENANCE_LIMITED` (plan.md:665–667).
- **Under-scope check**: no R1–R7 gap is left without a fix mapping; the gaps are in verifiability (matrix rows) and grounding, not in R-coverage.

---

## Findings

### F-1 (BLOCKING) — F1 contradicts the plan's own deterministic case matrix, CLI grammar, and authority rows; Stage 04 cannot implement both

Evidence: plan.md:54–67 (F1) vs plan.md:305, 311, 316, 326, 476, 480–483, 486–487, 510–513, 518, 445(2), 445(6), 447(2).

1. Case 01's literal prepare argv (plan.md:481) carries no adapter flags, and its resume argv (plan.md:480) carries `--dispatcher … --dispatcher-outcome RETURNED --test-mode` with `--expected-revision 1`, expecting revisions 1→2→3→4 (plan.md:510). Under F1, `prepare` must carry the dispatcher flags and perform the dispatch (revision 1→2), and the same resume argv must be rejected with `INVALID_INPUT`. The literal protocol and revision oracle are invalid.
2. Cases 02/03 (plan.md:511–512) inject the crash on `resume` and require the ambiguity barrier to be durably committed **before** the adapter side effect at revision 2, then a second resume with dispatcher flags at `--expected-revision 2`. F1 instead moves dispatch into `prepare`, commits the post-dispatch record **after** the side effect, and only commits the ambiguity barrier when a later `resume` loads the still-`INTENT_COMMITTED` intent. The state at the crash (revision 1, `INTENT_COMMITTED`), the expected revisions, and the second command's argv all change; neither is written down.
3. Case 04 (plan.md:513) and Case 09 (plan.md:518) expect a post-terminal `resume` — carrying `--dispatcher` and `--dispatcher-outcome RETURNED` (case 04) / `--dispatcher … --no-dispatch` (case 09) — to return `SKIP_TERMINAL` exit 0. F1 says adapter flags are rejected with `INVALID_INPUT` in every mode. The precedence between `SKIP_TERMINAL` and flag rejection is unspecified.
4. The authority rows plan.md:445 row 2, row 6, and plan.md:447 row 2 pass adapter flags to `resume` and require `INVALID_AUTHORITY` plus a retained JSON error artifact. If F1 removes those options from the resume parser (argparse-level), the rows degrade to a plain usage error with no JSON result; if rejection runs before `validate_transaction`, the class changes. The plan must keep the parser surface and pin the order: authority validation → adapter-flag semantic rejection → operation logic.
5. F1 defines reconciliation only for a loaded `INTENT_COMMITTED` intent. Repeat `resume` after the barrier is committed, or a loaded non-terminal post-dispatch state (`intent_state=SAVE_ALL_DISPATCH_ATTEMPTED`), has no specified result/revision delta. The deterministic matrix asserts exact revisions, so this is load-bearing.
6. F1 lists `--dispatcher-outcome` as a prepare adapter flag without the test-mode restriction that plan.md:326/336 requires for fault flags, and does not say where the test-mode crash injection for the new in-`prepare` dispatch window lives. Case 02/03 fault injection has no valid surface after F1.
7. Field mapping is loose: "commits `SAVE_ALL_DISPATCH_ATTEMPTED`/`SAVE_ALL_RETURNED`" mixes an `intent_state` value with a `dispatch_state` value (schemas.json `$defs/run`), while the reproduced R1 state shows the actual mapping (`intent_state=SAVE_ALL_DISPATCH_ATTEMPTED`, `dispatch_state=SAVE_ALL_RETURNED`). Case 01's new oracle needs the exact fields, including `intent.dispatch_outcome` and the written `dispatch_evidence`.

Why it matters: this is exactly the "tests changed to pass" hazard — Stage 04 could quietly rewrite case expectations to match F1 without an approved protocol, or Stage 05 would fail on oracles that no longer describe intended behavior. Both are prohibited (plan.md:52; handoff Phase 4).

### F-2 (BLOCKING for grounding) — The F3/F4 source-join binding has no schema-legal location, no declared write authority, and a self-certification loop

Evidence: plan.md:98–104, 106–113; `schemas/schemas.json` (`$defs/run`, `$defs/intent` `additionalProperties:false`, no `source_provenance`; `verified_albums` item allows exactly `{group_key, fingerprint, verified_run_id, destinations, source_kind, evidence}` with `evidence` a string); `src/line_backup_acceptance/transaction.py:16`; `src/line_backup_acceptance/verifier.py:172`; `references/state-contract.md:11,37`; user-fact artifact path `evidence/20260916-user-fact/source-identity-user-fact.json`.

1. Plan says "For VERIFIED the **run** must carry … `source_provenance = "join:<relative path>:<sha256>"`". No versioned schema location accepts that field; the only schema-legal free string near the registry entry is `verified_albums[].evidence` (and checkpoint/event `evidence` strings inside runs). Either the plan names a schema-legal location or it must declare a versioned schema extension — and state-contract.md:47 warns schema/safety changes require review. It cannot do neither and still claim "schema-conformant shape".
2. The `<relative path>` base is undefined, and the authoritative user fact lives in this repo's evidence tree, not under any project root, so `user_fact:<relpath>` as written cannot point at it.
3. "The binding artifact lives under the selected project root, is written atomically by prepare" adds a persisted artifact with no declared membership in the contract-permitted control/state write set (state-contract.md:37). A separate artifact read by the verifier also risks becoming a second authority beside `backup_state.json`.
4. Self-certification: F4 re-reads and re-hashes the artifact that `prepare` itself wrote from the operator's `--source-evidence` input. Nothing in F4 requires re-hashing the **external** evidence artifact recorded in `evidence_artifacts[{path,bytes,sha256}]` at its original location. As written, "hash-matching" can be satisfied entirely by product-authored bytes, which the plan's own R6/F5 reasoning (self-certifying inputs) and plan.md:52 forbid. The verification plan (plan.md:150–168) adds only "a valid join binding verifies" as a negative control — no forged/product-authored binding that must fail, and no deleted/mutated external artifact case.

### F-3 (MAJOR) — F2's `--source-evidence` cannot legally build the intent (no calibration) and is missing from the grammar; new refusal classes have no matrix rows

Evidence: plan.md:82–90, 310–316, 408–439; `schemas/schemas.json` `$defs/calibration` (requires `observed_at`, `screenshot_width`, `screenshot_height`, `ellipsis`, `dot_spacing`, `save_all_point`, `confidence` const `HIGH`, `evidence`); `references/state-contract.md:75–81`.

1. `--source-evidence` is not added to the production grammar (plan.md:311) or the authority paragraph (plan.md:310–316)/call graph, so its authority, canonicality and test-mode status are undefined.
2. The listed record fields contain no calibration geometry, yet F2 says "The intent's calibration … [is] taken from that record", and forbids fabricating `[1,1]`/HIGH. Production `prepare` must therefore either accept a complete schema-shaped `calibration` block inside the record (with validation and mismatch refusal) or refuse — this must be written down, because F1's in-`prepare` dispatch needs a bound calibration and `$defs/intent.calibration` is mandatory.
3. The deterministic matrix (plan.md:408–439) has no rows for the new F2 refusals (`MISSING_SOURCE_EVIDENCE`, `INVALID_SOURCE_EVIDENCE`, `CONFLICT_DUPLICATE`, `CONFLICT_DUPLICATE_FINGERPRINT`, `AMBIGUOUS_FINGERPRINT`, `NEEDS_RECONCILIATION`), and the verifier fixture manifest row list (plan.md:437–440) does not include them. The plan elsewhere treats that matrix as the acceptance oracle ("A product PASS line is never an oracle", plan.md:529-area), so the new behavior is currently unverifiable by design.

### F-4 (MAJOR) — F4/F5 verification coverage gaps in the deterministic matrix/manifest

Evidence: plan.md:106–124, 150–168, 410–441, 437–440; `tests/status_fixture_driver.py:136–160`; `phase2-r5` observation (`REPRODUCED_WITH_VARIANCE`).

1. No matrix row or fixture ID for the F4 structural-decode failures: truncated PNG (reproduced as a false PASS), JPEG missing EOI, and non-JPEG/PNG recognized image type fail-closed. The post-fix plan only asserts these as expectations (plan.md:154–155), not as deterministic rows with independent oracles; the fixture manifest claims to enumerate "every matrix row" (plan.md:437–440).
2. No row for the R5(c) variance itself — a read error in samples 1–2 with a clean sample 0 — even though that is the recorded reproduction and the exact behavior F4's any-sample rule changes (plan.md:42, 114–116). Rows `unreadable-file`/`file-command-error` cover only a permanently failing read.
3. No rows for dangling `verified_run_id`, SAFE_ABORT-linked `verified_run_id`, wrong-group link, or legacy entry without binding (row plan.md:435 covers "legacy record" only for missing `contract_revision`/formula calibration, and its oracle values must be updated to F4's binding rule).
4. Row plan.md:435 lists Registry = `EXACT`, a State-axis value, contradicting the plan's own result-schema rule (plan.md:441: "rejects any value from another subject enum, such as … EXACT in the Filesystem axis"). Registry values are PASS/FAIL.
5. F5 requires the product to emit `evidence_basis: scenario_table_non_acceptance` (plan.md:126–131), but no oracle checks it; the status driver would pass unchanged if the field disappeared.

### F-5 (MAJOR) — F6 fixes only two of the drivers that delete shared roots; "any order or parallel re-run" is not achievable as written

Evidence: plan.md:133–140; `tests/acceptance_case_driver.py:83`; `tests/verifier_fixture_driver.py:114,138`; `tests/automation_verification/run_phase2_r1:41`, `r2:31`, `r3:64,311,416`, `r4:85`, `r5:141,306,309`, `r6:226`, `r7:73,142`; `tests/automation_verification/fixtures.py:55`; `tests/automation_verification/harness.py:185`; `tests/legacy_false_positive_repro.py:30,71`.

The reproduced R6(b) destruction came from two drivers, but the invariant F6 states ("No test or driver may delete or overwrite another test's root or evidence … any order or parallel re-run must leave every manifest independently readable") applies to every driver above. Several of them delete the same literal `/private/tmp/line-backup-acceptance-case-01..12` roots used by the acceptance matrix. Fixing only the two named drivers leaves the invariant false and Stage 05's "re-run in any order" check failing.

### F-6 (MINOR, but a harness stop condition) — Stale Rev13 self-references break Stage 03/04 handoff binding

Evidence: plan.md:341 ("After Rev13 approval"), plan.md:655–659 ("Stage 03 must create a fresh handoff bound to TASK_ID, PLAN_REVISION=13"; "Stage 02 must independently review this Revision 13"). The reviewed plan is Rev14, and Rev14 itself says "Any earlier approval (including Rev13 + review/attempt-16) is not valid for this revision" (plan.md:27). A Stage 03 handoff compiled to Rev13 would be stale at Stage 04 startup (handoff↔plan mismatch is a stop condition), so these must be updated to the actual revision before Stage 03.

### F-7 (MINOR) — Part-1 user-fact wording overclaims same-source determination

Evidence: plan.md:188–194; `evidence/20260916-user-fact/source-identity-user-fact.json` (`answer.addresses: part_1`, `answer.part_2: UNANSWERED`, `source_correspondence_result_at_recording: UNRESOLVED`, "第 2 問未答前不得推定", `merge_prohibited: true`).

The user fact establishes only which character the visible group uses (禎) and that strings must never be merged/normalized. It does not establish that the 57 destination files correspond to the 禎-named album, nor that the 楨-keyed formal namespace is the same source. The sentence "With part 1 … the group-identity question (禎 ≡ 楨 as the same source …) is determinable by this plan" reads as if same-source identity were settled; the outcome fields (LEGACY_PROVENANCE_LIMITED, item 1 not complete) are correct, but the wording must be tightened to "part 1 resolves the visible-title character; same-source correspondence for the 57 files remains UNRESOLVED until part 2 or an authoritative machine join".

### F-8 (MINOR, fold into F-1) — Authority-row and grammar count/consistency checks

- The plan's statement "These eleven authority rows" (plan.md:447) must remain consistent with F1's new surface: if resume no longer accepts adapter flags, rows plan.md:445(2), 445(6), 447(2) need either the retained-parser-plus-precedence rule (preferred, minimal) or explicit replacement argv.
- plan.md:316 ("No production command accepts test-only fault/dispatcher flags") is ambiguous about production `--dispatcher`/`--dispatch-counter` on `prepare`, which F1 now requires. Reword to distinguish the production adapter interface (allowed on `prepare`) from test-only fault injection (`--dispatcher-outcome`, `--crash-after-dispatch`, `--pause-at`, `--storage-fault`; `--test-mode` only).

---

## Positive findings (verified, to preserve in the next revision)

- Evidence discipline is real: append-only attempt-01 with 84 manifests / 4859 artifacts independently read back (0 problems), program hashes matching handoff §4, and R1/R2/R6/R7 read back as recorded; R5's variance and R3(e)/R4/R7 fixtures are honestly labelled fixtures, not E2E.
- F1's core invariant (loaded intent never dispatches; only the same uninterrupted caller that just persisted/read back its intent dispatches once) exactly matches state-contract.md:90 and SKILL.md step 6, and is the minimal enforceable design at this process boundary.
- F2's shared-precondition precedence (`SKIP_DUPLICATE`/`SKIP_TERMINAL`, historical-intent scan, count-change reconciliation, refusal-before-write) is consistent with state-contract.md:55–57.
- F4's "any-sample read error → UNKNOWN, exit 1, never INPUT_NEGATIVE/PASS" is the correct minimal repair for the R5(c) misclassification; the PNG/JPEG structural decode is proportionate; the residual limitation is disclosed.
- F5's `evidence_basis` output field is compatible with the existing status fixture oracle (no fixture semantics broken).
- The human gate (plan.md:171–184) is exactly one message, precise, asks the open part-2 question with 「不知道」 allowed, and authorizes no menu selection, Save All, chooser, shortcut, state write, download, or production transaction; historical ellipsis credit exhaustion is stated.
- Three-result reporting and Status v2 orthogonality (plan.md:186–202, 663–667) match the harness closure semantics; `Done` remains overall closure only; fixture PASS cannot impersonate GUI E2E.
- The formal root remains read-only in this wave, `/private/tmp` is treated as working space only, and bridge work stays non-gating.

---

## Gate

**PLAN_REVISION_REQUIRED**

### Minimal necessary fixes for the next revision (PLAN_REVISION 15)

1. **Reconcile F1 with the accepted protocol (F-1, F-8).** Specify the new call surface exactly: `prepare` carries `--dispatcher`/`--dispatch-counter` (production + test) and the test-mode-only fault flags (`--dispatcher-outcome`, `--crash-after-dispatch`) for the in-process dispatch window; `resume` is reconciliation-only with adapter flags rejected after authority validation; keep the resume parser options so existing no-write authority rows still produce `INVALID_AUTHORITY` JSON artifacts; pin precedence (authority → flag semantics → operation). Rewrite the literal case 01/02/03/04/09 argv, revision deltas and state-field oracles (crash injected on `prepare`; crash-window state revision 1 `INTENT_COMMITTED`; fresh resume commits the ambiguity barrier once and reports `RECOVERY_NO_DISPATCH`), define resume behavior for every loadable non-terminal state and repeat-resume idempotence, spell out the exact post-dispatch fields (`intent_state`, `dispatch_state`, `intent.dispatch_outcome`, `trigger_outcome`, `save_all_retry_allowed`, `dispatch_evidence`), and update plan.md:305/311/316/326/476.
2. **Ground the F3/F4 binding (F-2).** Name the schema-legal storage location for `join:`/`user_fact:` provenance (e.g. `verified_albums[].evidence` plus a checkpoint/event evidence string in the run) or declare a reviewed schema extension; define the relpath base; name the binding artifact's exact path and show it is within the authorized write set (or store it in state); require the verifier to re-hash the **external** evidence artifact at its recorded path; add negative controls: forged/product-authored binding never CONFIRMs, and a deleted/mutated external artifact → UNRESOLVED.
3. **Complete F2 (F-3).** Add `--source-evidence` to the production grammar/authority paragraph/call graph; define the record schema including a complete schema-shaped `calibration` block and evidence-artifact path/hash rules, with missing/mismatched → refusal before any write; add deterministic matrix rows for the new refusal classes.
4. **Extend the verification matrix (F-4).** Add rows/IDs and independent oracles for truncated PNG, JPEG missing EOI, non-JPEG/PNG fail-closed, any-sample read-error variance, dangling/SAFE_ABORT-linked `verified_run_id`, wrong-group link, and legacy-without-binding; fix row plan.md:435 Registry value to PASS/FAIL; add an oracle assertion for F5's `evidence_basis`.
5. **Complete F6's scope (F-5).** Enumerate every driver/script that creates or removes shared roots and apply the ownership-marker/no-default-removal protocol (or isolate roots per driver) so the "any order/parallel re-run" claim is machine-checked by the read-back verifier in both orders.
6. **Update revision self-references (F-6).** plan.md:341, 655–659 (and any other "Rev13" self-references meaning "this revision") must read 14/15 consistently so Stage 03 compiles a handoff bound to the approved revision and Stage 04 has no handoff↔plan mismatch.
7. **Tighten the part-1 wording (F-7).** State that part 1 resolves the visible-title character only; same-source correspondence for the 57 files stays `UNRESOLVED` until part 2 or an authoritative machine join.

No waiver is available for items 1–5: they change accepted expectations, authority semantics, or verification oracles, and are therefore non-waivable per the plan's own rules (plan.md:52, 653) and the /goal Phase 3/4 requirements.
