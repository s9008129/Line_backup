PUBLIC_REVIEW_COPY — REDACTED — NOT_EXECUTABLE — NOT_NATIVE_ADMISSION

# PR9 revision02 — source-backed cap1 sequential design

PUBLIC_PLAN_SHA256=edfba734c7aa1263bdbed3dc3cecea601f0a83985d57d5fc5a76d9b61a6787fb
PUBLIC_CONTRACT_SHA256=f326ab3865c14a2dd40066d6254c66e31f55e9289726945e4b47a7868b3eb30c

Responds to the independent CHANGES_REQUIRED comment https://github.com/s9008129/Line_backup/pull/9#issuecomment-6164378480 on HEAD73987af9e32577644f6f6957a5a92ea62478d9b6. The GitHub comment is external design review evidence, not authenticated native role/admission provenance.

Selected CAP1_SEQUENTIAL: one uninterrupted GUI workflow; TWO genuinely distinct sequential cap1 transactions and owners; shared global23 input ledger/slots and aggregate2 original intents. No config cap change. Source-supported A VERIFIED/read-back/lease close → stop → release → fresh B owner begin → automatic return/real bounded scroll/new complete card → B transaction. The same product gates, duplicate protection, no-human-intervention and independent Acceptance remain.

Current production blockers are explicit: ML08-pinned grants; full-catalog admit despite bounded pilot; missing-ledger auto-init and lack of per-action slot enforcement; owner/session coupling; in-pair SCK capture/receipt2 versus accepted no-I/O policy. Proposed narrow edits are cli/service/store/adapter and affected existing tests, all NOT_IMPLEMENTED. Scoped receipt3 preserves pre-intent SCK calibration/closure and fresh anchor, removes in-pair I/O without fabricating an in-pair SCK guard, and binds stable observation identity separately from fresh owner. Old receipts/history remain unchanged.

Validation actually run:10 existing Python tests PASS;10 selected Node tests=9 PASS/1 FAIL (SCROLL_NO_VISUAL_CHANGE from repeated synthetic fixture image); isolated fixture actual finalize-stop-release-fresh-owner begin PASS; actual cross-owner/run global23 pool and UNKNOWN/no-refund PASS; missing-ledger reset behavior CONFIRMED GAP; six synthetic scroll comparison assertions PASS. No source/test repaired to hide failure. These do not prove proposed receipt3/slots/bounded manifest, current hosted native delivery or real LINE E2E. The unrelated-to-live fixture failure is retained as evidence; it is not converted into a product PASS.

B03=BLOCKED; B05=BLOCKED; NATIVE_ADMISSION=NOT_GRANTED; GUI_CONSENT=NOT_GRANTED; LINE_ACTIONS=0. Authentic scope/root-budget eligibility, actual manual-review acceptance, supported runtime/private binding/accounting, private reviewer access and fresh Owner consent are hard pre-execution gates. No original ML08/c6/28-gate reset, new Task/Issue, Luna, Harness change or production edit. Hidden original bindings remain PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED.

Review request: APPROVE | CHANGES_REQUIRED | REJECT on the source-backed A/B comparison, four-file minimum production delta, global23 slot/ledger ownership across fresh cap1 owners, actual scroll link, receipt3 semantics and truthfully unresolved admission. No self-review or Luna reviewer. Public review cannot certify hidden target/source/config values or native admission. Existing repository privacy exposure remains a separate finding.

## Complete PUBLIC revision02 Plan

````markdown
PUBLIC_REVIEW_COPY — REDACTED — NOT_EXECUTABLE — NOT_NATIVE_ADMISSION

PUBLIC_DESIGN_REVISION=02_CAP1_SEQUENTIAL

This is a semantically revised copy of the separately versioned PRIVATE revision02 candidate, not a changed copy pretending to match the original frozen revision01 bytes. All original revision01 artifacts remain unchanged and local. No implementation/admission/GUI authority follows. Hidden identity, canonical config/state/source/build/private-evidence bindings are PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED; public JSON syntax is not production/native schema validity. Source excerpt hashes below bind locally inspected code, not independently rehashed full hidden sources or platform attestations.

Stable aliases: GROUP_PRIVATE_01, VERIFIED_ALBUM_01, VERIFIED_ALBUM_02, NEW_ALBUM_A, NEW_ALBUM_B. Existing cryptographically random opaque correlation references/mapping are preserved privately, not unkeyed hashes of guessable tuples.

- VERIFIED_ALBUM_01: OPAQUE_FP_6b27490d9210bc6a0c7a9bf9049a5c0a2d901061d77a24e8697ec29a28ac11a0
- VERIFIED_ALBUM_02: OPAQUE_FP_0a26366c9663e2bb14ee8d4a4a55d4404a8b30fc3d7c4af4838a2e5a2354e2a8

# Continuous two NEW LINE albums — PRIVATE candidate revision 02 (CAP1_SEQUENTIAL)

Status: AWAITING_EXTERNAL_REVIEW; NOT_NATIVE_ADMITTED; NO_GUI_CONSENT. This isolated proposal allocates no Task/run/Issue and changes no production configuration or state. It does not amend PR #8. This revision supersedes the earlier cap2 preference for DESIGN REVIEW ONLY; it does not rewrite any frozen source artifact. The companion `plan-contract.public-review.json` is a candidate scope contract, not a native v3 Task or Controller receipt. The review packet binds the exact bytes of both files.

## 1. Outcome, roles and fixed baseline

One initially authorized, uninterrupted macOS foreground Computer Use workflow must back up TWO different NEW eligible albums: A VERIFIED → return to the same group list → actual bounded scroll with ordered complete-card overlap and a new complete card → B detail MATCH → B VERIFIED. No Owner calibration, selection, screenshot, click or foreground recovery between A and B. Historical single-album success is provenance, not this test's PASS.

Project root is exactly `<PRIVATE_PROJECT_ROOT>`. Config identity is `GROUP_PRIVATE_01`; preserve the exact private Unicode sequence; never substitute visually similar code points (PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED). Fingerprint is `(group_key, ISO start_date, ISO end_date, expected_images)`, not count alone. Preserve original visible labels separately; OCR variation cannot establish a different group is equivalent.

Verified baseline: state schema 3/revision 35, active_batch/active_writer_id/context_lock null; two terminal VERIFIED runs and retry=false intents. Protect:

| Exact date range | Count | Bytes | Existing destination leaf |
|---|---:|---:|---|
| VERIFIED_ALBUM_01 | 57 | 17,924,900 | `<PRIVATE_DESTINATION_VERIFIED_ALBUM_01>` |
| VERIFIED_ALBUM_02 | 182 | 38,045,847 | `<PRIVATE_DESTINATION_VERIFIED_ALBUM_02>` |

Both have retained scoped independent A1 PASS. The 57 closure explicitly says native Controller admission was unavailable; the 182 acceptance explicitly describes human-assisted single-album calibration. Neither proves uninterrupted two-album automation. Never open/download either fingerprint again.

Sol authors/orchestrates only. Luna/high implements only after legitimate admission. An independent ChatGPT/other high-reasoning reviewer performs Plan Review and later independent Acceptance; no contributor reviews its own artifact, and Luna cannot review. Owner manually transfers exact artifacts and returns the actual review verbatim. Risk is CRITICAL because real private-photo downloads and persistent transaction authority/state are involved. Independent Plan Review and Acceptance are required; deterministic Handoff must copy the finally reviewed native contract exactly. No separate Handoff model is proposed. No helpers/writers/delegation are proposed.

## 2. Architecture decision — compare exactly two options

SELECTED_TRANSACTION_MODEL=CAP1_SEQUENTIAL. Product continuity means one uninterrupted foreground/app observation workflow, not one batch ID. Current config remains max_albums_per_run=1; no cap amendment is proposed. Each of two explicitly preauthorized NEW album transactions uses a separate cap=1 canonical service lifecycle (Service.begin mode=backup_batch, limit=1), distinct owner/run/action/lease/destination, and the SAME global task-scoped GUI budget and stable GUI observation identity. This is two independently scoped one-album transactions, not a backup_batch skill call pretending its effective cap exceeds one. Aggregate product scope is exactly two original intents; no third lifecycle/attempt is authorized.

| Actual source question | Option A: two cap=1 lifecycles | Option B: one cap=2 batch |
|---|---|---|
| API support | finalize → stop(CAP1_COMPLETE) → release → new owner's begin(limit=1); existing methods, no catalog needed for stop/release | begin(limit=2) can represent it only after config cap2; A finalize clears album ownership but retains batch; B prepare needs another manifest identity |
| First current admission blocker | cli.py authorize pins artifact_dir/contract/GUI ledger to exhausted ML08 and requires old waiver/owners/cap1000; no current new-scope production grant | Same grant blocker; additionally config cap1 makes second prepare/intent LIMIT_REACHED |
| Inter-album state | A VERIFIED/read-back/lease-close; owner/context null; active_batch still RUNNING, so direct B begin is BATCH_BUSY. stop after successful A changes only the empty lifecycle; release requires terminal lifecycle, no current album, null owner/context and all barriers resolved. Then fresh B owner begins. | A finalize leaves the parent batch and increments index; B acquires a new album lease inside that batch after A release |
| Catalog | Current admit requires TOP/BOTTOM for both options. Proposed single-candidate manifest per lifecycle reuses frame/card_target and reports bounded coverage only; no full-list finish or claim ALL_COMPLETE | Needs the same bounded-discovery adaptation PLUS a way to admit/append later B to the already-frozen manifest safely |
| Minimum delta | cli/service/store/adapter plus focused existing tests. Config/schema/observations stay unchanged. Single-candidate manifests are immutable per lifecycle; existing stop/release closes each | Same shared grant/ledger/menu work, config1→2 and incremental same-batch manifest/index handling; adds a protected config decision without improving the product oracle |
| Accounting/history | One product Implement scope, two distinct original album intents. Store.enforce_grant_quota counts persisted intents across lifecycles; no budget refill. Failure stops the whole pilot and requires honest native accounting | Same accounting/history constraints; increasing batch cap does not solve B03/B05 |

Option A is not invalid as a transaction model: its supported terminal lifecycle API was exercised in isolated fixtures, including fresh-owner begin only AFTER release. The first CURRENT production-route blocker is cli.py:127–128 GRANT_SCOPE, then150–152 GRANT_LIVE_BINDING_REQUIRED; these must be legitimately rebound for a distinct scope, not bypassed. An implementation that starts B before A lifecycle release is invalid (Service.begin:65 BATCH_BUSY). Source excerpts/hashes and actual check limitations are in the companion review packet.

Minimum future implementation delta — NOT applied:
1. src/line_backup_batch/cli.py: a narrowly bound new reviewed product scope, two authorized transaction owners, lifecycle limit1, aggregate album/Save All/chooser quota2, one fixed GUI ledger/cap23 and source/config/contract bindings. Keep old exhausted bindings closed; do not impersonate the old waiver or reviewer. Actual manual-review acceptance remains B05 BLOCKED.
2. src/line_backup_batch/service.py: explicitly versioned single-candidate manifest (BOUNDED_CANDIDATE_ONLY), validated using existing frame/card_target; never call catalog or set fake top/bottom for this branch. Each immutable manifest contains exactly one eligible target, stable GUI observation identity and, for B, the retained verified return/scroll link. Reuse existing finalize/stop/release; no generic writer or new state schema. Add the scoped calibrated atomic receipt described below, separating transaction owner from GUI observation identity; old receipt meanings remain unchanged.
3. src/line_backup_batch/store.py: reuse the shared lock, fsync/atomic ledger/read-back and all-entry count. For the new scope require the existing once-initialized fixed ledger, no implicit reinitialization, and 23 unique reviewed action-slot keys; RESERVED/UNKNOWN count forever. No historic quota/reset logic change.
4. scripts/line_backup_cua_adapter.mjs: separate fresh transactionOwner/transaction label from stable GUI observation session ID while reusing the same CUA App/foreground workflow; supply exact action slots; recheck original frame age after reservation I/O. Align the new scope's final pair and receipt with RC2 no-I/O policy. Do not build a new executor or local process framework.
5. Existing tests/test_batch_authority.py, tests/test_batch_lifecycle.py and tests/test_cua_adapter.mjs: only affected ledger/refusal/owner-seam/receipt/no-replay and scroll-evidence cases. The existing positive scroll fixture fails because it returns an unchanged image; preserve the negative no-effect check and provide actual distinct synthetic frames/ordered overlap for that unit case, not a production workaround. No new test framework.

There are still hard entry barriers: authentic independent review of final bytes and source; genuine scope/root-budget eligibility; B03 actual hosted/native guarantee or competent applicable acceptance of its actual level; B05 lawful manual-review acceptance/admission; supported private capture/retention/geometry bridge and Mac permissions; honest non-PASS accounting; independent Acceptance access to private evidence; fresh specific Owner foreground/GUI consent. A GitHub verdict is not a native receipt. No new Task or imported result is authorized here.

Atomic-menu compatibility is currently BLOCKED, not silently waived. Existing adapter:294–335 really captures/guards SCK AFTER ellipsis and BEFORE Save All. Service receipt2:306–418 requires that exact SCK_MENU_GUARD_PASS, popup/support/point binding, event order and reservations. RC2 ui-procedure Final atomic dispatch prohibits that intervening I/O. This revision preserves the accepted no-I/O policy and proposes one scoped receipt3 CALIBRATED_NO_IO_PAIR; it is NOT implemented or approved. Retain affirmative SCK/visual guard during pre-intent menu calibration, safe closure and a fresh matching detail/ellipsis anchor. Receipt3 must bind calibration/menu/support/guard/closure references and original intent frame, but must not claim the CLOSED calibration popup is a current in-pair popup or fabricate SCK_MENU_GUARD_PASS. Its final chain is exactly ellipsis → bounded wait → Save All with logical invocation bookkeeping only. The receipt event order removes only the in-pair SCK event; it retains truthful errors, the two-input reservation, all actual chooser-phase/path/confirmation/download proofs, and owner/run/action/frame/source binding. Its session_id compares to the manifest's stable observation identity; execution_id/chooser owner compare to the fresh current transaction owner. Existing receipt1/2 validation is not rewritten. Independent CRITICAL review of this source/receipt change and acceptance is required before any native Save All. If calibration cannot safely cover replay geometry, STOP; no fallback to formula or old guarded receipt under the new mode.

This proposal adds no Harness/reviewer platform, provider migration, config change, schema migration, new native executor, allocation, Issue or GUI action. No implementation is authorized by publication of this candidate.

## 3. Reuse and literal scope

Use the October task-local operators only as audited algorithm references: nofollow root/destination checks, shared exclusive-lock compare-and-commit, exact revision/owner/run/outcome checks at commit, atomic replace/read-back, append-only evidence, combined VERIFIED/registry/ownership-release commit. Their constants and imports make them invalid new-album executables. Use the current canonical v3 Store/Service after lawful scope binding, not a competing writer.

Reuse `src/line_backup_acceptance/project_binding.py` history/duplicate rules and verify-only functions, and `src/line_backup_batch/content.py` stable-inventory/hash/full-decode logic. The existing GENERIC 182 ImageIO binary takes `<destination> <expected-count>` and may be reused after exact hash verification; the historical 57 decoder has a fixed-count scope and is not the new pilot decoder. No Pillow/NumPy install. Required existing runtime: supported macOS CUA; Python 3.13 plus existing pinned jsonschema/referencing dependencies for state validation; Python standard library; existing ImageIO decoder; existing screenshot/OCR sources where needed. Swift compilation is not required merely to reuse that decoder.

Permitted future non-GUI adoption scope is limited to existing project `src/line_backup_batch/{cli.py,service.py,store.py}`, `scripts/line_backup_cua_adapter.mjs`, the three targeted existing tests named in §2, and pilot-local binding/retention instructions. Production config, state schema, observations and legacy common guards remain unchanged. The scoped Store ledger change is required by the demonstrated missing-ledger/per-action enforcement gaps. No source change is made now. Existing dirty work in these files belongs to the Owner; any later implementation must preserve it and bind its actual bytes, not reset or overwrite it.

Future data writes, only after review/admission/consent: `state/backup_state.json`, append-only `state/run_log.md`, existing shared project-state lock and same-filesystem temporary commit files; two newly created exact empty leaf directories below `backups/GROUP_PRIVATE_01/`; pilot-local evidence/intent/GUI-budget records below `<PRIVATE_EXECUTION_SCOPE_REVISION02>/evidence/`. Resolve all paths by components/realpath/nofollow. No existing photo, historical run, registry entry, source receipt, native Task/Issue, c6, 28 gates, or PR8 contract mutation. Control temp paths must be included literally by final admission, not guessed at runtime.

Retain raw screenshot/AX/full-display/OCR/inventory locally only: private directories 0700, files 0600, task-local `.gitignore` `/private/`, verify `git check-ignore` before capture and confirm admitted evidence paths do not overlap Controller-protected paths. No raw content in reviewable reports. Before any future commit/push inspect staged/index names and contents; never force-add private files. Public/shareable metadata is limited to permitted redacted identities, hashes, dispositions and local references. No commit/push is authorized by this Plan preparation.

## 4. Supported CUA calls and evidence handling

Current runtime documentation was read without acquiring LINE. Supported macOS entry is `await cua.getApp("jp.naver.line.mac")`; it may launch an absent app, so live preflight must first establish LINE already running normally. Normal observation is `await line.getAXStateAndScreenshot({emit:false, disableDiffing:true})`, which returns full state and screenshot bytes. Missing screenshot, incomplete AX or retention failure is UNKNOWN, never synthetic evidence. Fresh AX-only read is `line.getAXState({emit:false, disableDiffing:true})`.

Supported actions: `line.click(freshPoint,{mouseButton:"left",clickCount:1})`; `line.scroll(freshViewportTarget,"down",0.25)` (macOS page units); `line.pressKey("super+shift+g")`, `line.setValue(freshPathFieldIndex, exactDestination)`, `line.pressKey("Return")`; `line.pressKey("Escape")` only for an affirmatively identified safe calibration menu. Do not invent `scrollDown`, use Linux pixel options on Mac, or infer exactly 0.25 physical movement from the requested page parameter. Verify actual list movement and overlap after each request.

After every action, obtain current AX before making another decision, and a fresh paired image wherever identity/geometry/effect is required. Exceptions: no observation within the final atomic pair; refresh AX and observe immediately after it. Persist raw bytes/state with capture start/end times, hash, provider, window geometry/scale, native process/session lineage and action relation. Never reset age after OCR/persistence. Existing adapter observation/retention callbacks and historical `host_io.mjs` describe reusable algorithms, but the latter is ML08-path-bound and its local-process availability in today's hosted kernel is not proven by JavaScript syntax. Verify a supported filesystem-only bridge using non-GUI preflight before adopting it; no unsupported process spawn or silent executor replacement.

If CUA omits the menu, obtain a fresh privately retained full-display screenshot using an existing explicitly admitted read-only source. `/usr/sbin/screencapture -x -m <private-new.png>` is a real installed, noninteractive main-display capture interface; it is ONLY a proposed read-only capture permission after explicit full-display consent, never a GUI input workaround. It is suitable only when LINE and its popup are affirmatively on that display. Existing `rev28ctl album-support` is a SCK/OCR support producer requiring actual PID/window/display/scale, retained pair frame, bounds and hashes; it is not a dispatcher or independently validated current build. Use it only with a matching admitted binary/source closure and supported bridge. Do not fabricate its claims or reuse its old grant. Existing OCR is supporting evidence; AX absence does not prove Save All absent. If fresh popup ownership, unobstructed row or coordinate mapping cannot be proven automatically, STOP instead of asking for mid-run calibration.

No live CUA, AX, SCK, screenshot or permission prompts are executed during planning. Current Screen Recording/Accessibility permission and complete capture/retention bridge readiness are UNTESTED for this scope; software installation is not proof of permission. Lack of supported retention/geometry/producer is a pre-GUI blocker, not a reason for a new framework.

## 5. Reviewed proposed budgets

| Operation | Maximum logical invocations | Preconditions |
|---|---:|---|
| App acquisition | 3 total | Initial LINE binding plus at most one fresh detail-window binding per album if needed; no launch/recovery loop |
| Fresh paired screenshot/AX | 80 total, at most 2 per required observation checkpoint | Initial attempt + at most one read-only recapture; no input retry; no capture inside atomic pair |
| Additional AX-only refresh | 23 total | Post-action current semantics; not repeated to simulate effect |
| Full-display popup observation | 4 total, at most 2 per album | Pre-intent calibration only; explicit private full-display consent |
| Album metadata click | 1 per NEW album, 2 total | Same-frame persisted binding and duplicate/destination gates |
| Calibration menu open/dismiss | 1 open + 1 safe dismiss per album | Fresh actual menu; no menu-item activation; no retry |
| Atomic dispatch | 1 pair per album: ellipsis1 + SaveAll1; 2 pairs total | Durable read-back intent, fresh proven calibration, uninterrupted owner |
| Chooser | 4 per album: GoToFolder1, setValue1, Return1, confirm1 | Fresh identified path field, exact full path and leaf, no fallback/reconfirmation |
| Return to list | 1 total after A | Fresh safe Back/close-detail control with verified source-list relationship |
| Scroll | 4 total; reserve at least1 after A | Each is one 0.25-page down request, separate pre/post observations; before A at most3 |

Total GUI method cap is 23: two albums ×9 + return1 + scroll4. Acquisition/observation are separate. Every invocation/uncertain reservation consumes its slot; no refund. These are proposed ceilings, not existing authority. Any input failure/no effect/UNKNOWN stops that action and the pilot; no click, key, Save All or scroll redispatch, transport fallback, Page Down, blind Escape or generic focus click. Read-only recapture may resolve an input UNKNOWN, but cannot rearm its permission. File polling is separate: 5-second minimum interval, 3 identical full inventories, 600-second maximum wait per album. Capture budgets do not reset between albums or across interruptions.

Final atomic menu wait proposal is bounded 1200 ms within the existing adapter's 800–1500 ms range, subject to review and current calibration applicability. Historical 1200 ms is not a readiness guarantee; stale/different menu/version/layout or inadequate safe margin means no dispatch. No per-row formula/historical coordinate is admitted.

## 6. Phase A — admission and preflight, then initial handoff

Before GUI: verify authentic independent verdict on final exact hashes; legitimate workflow acceptance/native admission (or an explicitly lawful alternative without claiming native admission); exact Task/source/contract/config bindings; independent root-issue eligibility; required truthful non-PASS accounting; deterministic Handoff; Luna Implementer role; all entry barriers above. The old conditional one-Issue decision is for TASK-55518bd9640d4ea59ab3a6414a171795 only and does not transfer. Do not suppress failure import, fake PASS or create an Issue now. If the new scope lacks lawful accounting, stop before execution.

Read canonical config/state from the selected root only. Current state schema3/revision35, config cap1 and both historical VERIFIED fingerprints remain unchanged. Revalidate history/duplicates/unresolved intents and same-date changed-count collisions, all permitted destinations, null owner/context/active_batch and no pending writes. Missing/changed authority, source, lock or state blocks, never repair by guessing. Validate private path containment/no symlinks/modes/ignore protection and the supported actual capture/retention/geometry bridge; source code does not demonstrate current hosted process-spawn or Mac permissions.

Before any input, initialize ONE new admitted task-scoped ledger cap23 exactly once using exclusive creation, serialize its initialization under the existing shared guard and verify read-back. Bind both legitimate owner grants to that SAME path/task/cap/slot map and aggregate quota2, lifecycle limit1. Store references to this original ledger in the private workflow record; no new path/task/ledger or refill on owner/run/lifecycle change. After initialization any missing/malformed/replaced/drifted ledger means STOP, never automatically create another. No old ML08 ledger or c6 record is reused or reset.

Use the existing ledger algorithm with a proposed scope-specific version2 entry action_keys: each key is unique across every entry, including RESERVED/UNKNOWN; count equals key count; sum(count)≤23. Existing top-level task/cap binding and shared-lock read-back remain. Fixed slots:
A: CARD, CAL_OPEN, CAL_DISMISS, ATOMIC_ELLIPSIS, SAVE_ALL, GO_TO_FOLDER, SET_PATH, PATH_RETURN, CHOOSER_CONFIRM (9).
B: the same nine B-prefixed slots (9).
Transition: RETURN_A_TO_LIST (1), SCROLL_1..SCROLL_4 (4).
Atomic pair reserves its two slots before ellipsis; chooser reserves four before its first input; calibration reserves two. Unused reserved slots remain spent after error/crash. No slot may be reused by another owner/run. Pre-A scrolls≤3; ≥1 post-A scroll is required, so discovery cannot spend all four before A. A global total cap alone does not prove these per-action limits; the new slot checks and phase prerequisites are part of the proposed minimal Store/adapter delta, not existing enforcement.

Owner_A and Owner_B are genuine new transaction-ownership bindings under one admitted product workflow, not invented platform sessions. Stable observation identity S is local CUA continuity metadata, not backend attestation; app/process/window/group continuity must have fresh native/image/AX evidence. Current adapter/service couple owner with session_id; the scoped receipt/service/adapter adjustment separates them without permitting foreign owners.

Only after all non-GUI prerequisites actually PASS report READY_FOR_FOREGROUND_HANDOFF. Ask Owner to display the configured group's Albums list with visible context/complete cards, unlocked normal LINE and no menu/dialog/viewer, then grant fresh explicit consent for TWO independently authorized cap1 new-album transactions under one uninterrupted workflow;≤23 input calls including≤4 individually observed0.25-page scrolls; private capture/full-display scope; exact new empty project-local destinations, verification and atomic state writes. No consent exists now. No Owner album selection/calibration is required between A and B.

After handoff, retain one CUA App/foreground workflow. Begin only lifecycle A with Owner_A, mode=backup_batch, limit=1 under its specific grant; manifest is a bounded eligible single-candidate representation, not whole-list coverage. Do not begin B until A's exact VERIFIED/read-back/lease-close, successful stop/release and null ownership/active_batch are proven. Shared GUI budget and aggregate persisted intent quota survive that boundary.

## 7. Phase B — NEW_ALBUM_A transaction

1. Fresh-observe canonical group + Albums + full unique cards. Identify complete date/count identity with canonical Unicode group carried through verified navigation context. Skip both protected fingerprints and every registry/history/download/unresolved/active candidate; no invented year, partial card or same-date changed-count candidate. Select the first affirmative eligible complete candidate. If none is visible, use at most3 individually budgeted/observed scrolls under Phase C rules, preserving at least1 for the A→B transition. Exhaustion means NO_ELIGIBLE_TARGET_OBSERVED_WITHIN_BUDGET, not global absence.
2. Under admitted current v3 transaction authority, bind A's run, owner, canonical fingerprint and exact destination `backups/<canonical-group>/<start>_<end>_<count>張`. Inspect every path component/nofollow; reject any existing leaf, symlink, nonempty directory or unassociated downloaded content rather than overwriting/reusing it. Create the new empty leaf once, inspect it and record directory identity. Reject uncertainty and preserve any prepared directory.
3. Fresh dedicated same-frame target binding: full card bounds, safe non-thumbnail metadata subregion, observed adjacent separation, actual mapping uncertainty, window geometry/scale, capture ID/hash/time, PID/application identity/session. Persist/read back exact click point and affirmative empty intervening-action trace. All geometry/identity comes from this one current observation. If time/layout changes while persistence completes, read-only rebind within budget; never renew old frame age.
4. Consume/reserve the sole card-click slot durably before one `line.click` call. Fresh AX/image must show A's complete date range/count and detail context MATCH. Opening may create a NEW detail window while the source list remains: require same verified LINE app/process/session and defensible source-list→detail relation, not equal pre/post IDs/size. Use visual/OCR when AX is chrome-only. Dates/count alone do not prove group. MISMATCH or unresolved UNKNOWN is terminal; no second card click or Back-and-repair.
5. Freshly identify ellipsis, open calibration menu once, acquire automatic visual menu evidence (full-display if needed). Affirmatively identify 儲存全部 row, menu ownership, adjacent Rename/Delete boundaries, unobstructed safe center and point mapping. Derive margins from current geometry/uncertainty, not a fixed pixel/row formula. Dismiss safely once; verify closed/no command/no chooser/no download. Freshly rebind detail/ellipsis and calibration applicability; drift/unsafe closure aborts.
6. Recheck history, owner/run, empty destination and identity. Commit a unique durable Save All intent and exhausted original-input reservation through shared CAS; bind calibration/frame/source/config/destination/action, retry=false. Read back exact bytes/revision. Only the uninterrupted caller that committed this new intent may use its sole original permission. Loaded intent, new run or changed destination cannot authorize dispatch.
7. In ONE sequential CUA call, invoke ellipsis once → bounded menu wait → mark logical Save All invocation in memory → Save All click once. No capture/I/O/persistence/keyboard/reacquisition/app switch inside the pair. If first click errors or freshness breaks, do not issue second. Persist exact original return/error and invocation boundary afterward; missing boundary proof is UNKNOWN, never zero. Logical RETURNED is not physical delivery or correct activation. An unmistakable matching native folder chooser must affirm the trigger; wrong row/unknown modal stops permanently for the intent.
8. In the matching chooser, one GoToFolder → fresh AX/image → setValue on currently identified PathTextField to the exact recorded absolute path → fresh full-path proof → one Return → fresh exact leaf/breadcrumb/destination proof → one newly bound confirm click. Check empty directory identity again before confirmation. No paste fallback, stale AX index, parent-folder click, folder creation, blind Return, overwrite acceptance or repeated confirm. Preserve original input errors. Uncertain confirmation permits read-only UI/filesystem observation only.
9. Once download starts, cease all LINE input until transaction terminal verification/read-back. Poll only that exact destination. Record all entries including hidden/partial/symlink/subdirectories; do not delete or filter anomalies. Require expected recognized image count, nonzero bytes, valid MIME/content, no unknown/partial entries, at least3 identical name/size/mtime/hash inventories separated by≥5s, full ImageIO pixel decode with exact names/SHA-256 and unchanged postdecode inventory. No UI-completion inference; timeout/extra files/decode mismatch stops the batch.
10. Atomically commit A verification evidence + correct fingerprint registry addition + VERIFIED + cleared album writer/context in one revision under latest CAS; read back exact committed contents, directory inventory and closed album lease. Retain terminal current_run_id if valid. Filesystem PASS with failed state finalization remains PARTIAL and cannot start B. Never reopen or reset A's intent/owner.

## 8. Phase C — mandatory autonomous return and real scroll

After A's VERIFIED commit and exact read-back, verify lease-close=CLOSED and settle pending writes. Active album writer/context are null but the cap1 service lifecycle is still RUNNING; a direct next begin would BATCH_BUSY. Call existing Service.stop with reason AUTHORIZED_CAP1_COMPLETE only when current_album_run_id is null and A is genuinely VERIFIED; it must leave A's terminal run/evidence/intent unchanged. Then Service.release requires terminal batch, null current album/writer/context and no unresolved barriers; read back active_batch=null. This is honest successful cap1 termination, not pretending a failed album passed or declaring the entire collection complete.

Begin lifecycle B with fresh Owner_B, limit1 and the same global ledger/aggregate quota before the return/scroll navigation. Initially it has no candidate/album writer/context. Navigation evidence is appended to authorized workflow/B-lifecycle evidence, never A's retired events. Keep stable GUI observation identity S and the same CUA App/foreground session. No repeated generic approval or Plan Review is required between A and B if the finally admitted whole workflow and all gates permit it.

Identify one unmistakable safe Back/close-detail control and its actual source-list relationship from fresh A detail evidence; invoke it once. Freshly verify the original same-group Albums list and current LINE application/process/session/window/layout continuity. No assumed focus switch or generic Escape. Unknown return/list identity ends the pilot.

Perform at least ONE real down scroll even if another eligible card was previously visible. Each of the≤4 total scrolls must: retain fresh pre-frame/AX and ordered full unique card fingerprints; validate safe unobstructed viewport/no editing/menu/modal; persist/read back action intent and consume one slot; call `line.scroll(freshTarget,"down",0.25)` once; immediately fresh-observe; prove same group/surface/session/PID/list-window/layout, affirmative movement, at least1 unique complete shared neighboring card in unchanged order and at least1 newly visible complete card with dates/count. Reuse existing `verifyAlbumScroll` only as a checker of actual retained observations; its result does not create evidence. A gap, no effect, UNKNOWN or geometry change means STOP, no bridging/back-scroll/fallback in this pilot.

Choose B only from a complete NEW card affirmatively exposed by this successful post-A scroll chain. Compare its full canonical fingerprint with A, both historical albums, all existing destinations/history and unresolved intents again. Ordered overlap alone does not prove whole-list coverage. If no eligible B is found within remaining scroll budget, report ALBUM_A_VERIFIED_WITHOUT_ELIGIBLE_B_OBSERVED; if authoritative complete coverage actually proves fewer than2, report that separately. Never fabricate absence from a partial scan or redownload A/57/182.

## 9. Phase D — NEW_ALBUM_B transaction and unconditional stop

Acquire B's fresh independent album run/lease/intent within the already-begun cap1 lifecycle B only after A is VERIFIED/read-back exact/lease closed, A lifecycle released, linking return/scroll PASS and B duplicate checks PASS. Bind the immutable bounded B candidate manifest to the actual post-scroll observation and its retained C1 link; no whole-catalog/top/bottom or ALL_COMPLETE claim. B's fingerprint/destination/action differs from A, both historical protected fingerprints and every unresolved intent. Aggregate quota2 and the original global ledger remain unchanged. Do not precommit B's intent while A runs.

Repeat Phase B steps2–10 using ONLY B's new observations/geometry/calibration, its own safe empty destination, one card-click slot, one Save All intent/pair and one chooser confirmation. A's menu calibration, coordinates, permits or owner cannot authorize B. Require B actual detail MATCH to the post-scroll candidate. Both photo sets must be independently verified and safely committed. After B VERIFIED/read-back/lease-close, terminate/release its cap1 lifecycle through the same honest stop/release procedure; read back active_batch/writer/context null; no third album, further return/scroll, canary or extra GUI action. Preserve both historical and both new records.

Any interruption, Owner intervention, unexpected modal, state conflict or uncertain side effect ends further input. Persist append-only original errors/UNKNOWN under existing valid authority and honestly finalize SAFE_ABORT/batch stop when supported. Failed/uncertain persistence authorizes no fallback overwrite. No automatic cleanup, continuation, replay or rearm. A consumed intent/reservation is never evidence of physical dispatch. If interruption occurs during a native held mouse event, no new click/down may be sent; only a separately supported neutral button-release safety action could be considered under explicit actuation policy, otherwise preserve UNKNOWN and stop. CUA documents click as one call and exposes no separately proven release control, so do not invent one.

## 10. Real acceptance gates and reporting

| Gate | Required evidence and PASS condition | Evidence owner |
|---|---|---|
| P0 | Independent final Plan Review, authentic lawful scope/admission, exact deterministic Handoff/source/config binding, accounting and consent; none currently PASS | Independent Reviewer / admission authority / Owner |
| T0 | Current valid schema/history, duplicate safeguards, no conflicting owner/batch, supported private capture/retention and transaction route, source/build/dependency checks | Implementer tools |
| A1 | Fresh eligible A same-frame target → actual distinct detail MATCH with app/window lineage and group context | Implementer, private visual + AX + trace |
| A2 | Real identified menu, safe closure, intent/read-back, sole original Save All, exact chooser/path/one confirmation | Implementer, private visual + dispatch/transaction evidence |
| A3 | Actual A file inventory/stability/hash/full decode/source join; atomic VERIFIED/registry/release/read-back | Implementer tools |
| C1 | A→same list, real post-A bounded scroll, same session, ordered complete unique overlap AND new full card, eligible distinct B binding | Implementer, real private pre/post frames/AX/trace |
| B1 | Fresh B same-frame target → detail MATCH to post-scroll fingerprint, separate menu/intent/sole Save All/exact chooser | Implementer, private visual + trace/transaction evidence |
| B2 | Actual B inventory/stability/hash/full decode/source join; atomic VERIFIED/registry/read-back, lease close and cap1 lifecycle stop/release | Implementer tools |
| X1 | Independent review of BOTH actual transactions AND connecting C1, no Owner intervention, exact budgets/no replay, all prior data/history preserved | Independent Acceptance Reviewer |

All are REQUIRED closure gates; P0/X1 independent; product gates are GOAL_CRITICAL, implementation tools/actual observed visuals retain their proper evidence labels. Human visual attestations remain OBSERVED, not tool PASS. Neither synthetic fixtures, CI, schema validity, source hashes nor historical success may pass a fresh product gate. No gate passes by inference from another.

Overall `UNATTENDED_TWO_ALBUM_PASS` requires every applicable gate's own actual evidence and independent Acceptance, two different NEW fingerprints with complete verified photos, valid separate intents and the uninterrupted observed connecting scroll, no Owner intervention and no protected changes. Otherwise name first FAILED/UNKNOWN/NOT_RUN gate, preserve filesystem/transaction successes and report PARTIAL/BLOCKED/ASSISTED_PARTIAL accurately. Keep PRIMARY_OUTCOME_STATUS, IMPLEMENTATION_STATUS, CORE_ACCEPTANCE_STATUS, REQUIRED_VERIFICATION_STATUS, INDEPENDENT_ACCEPTANCE_STATUS and TASK_CLOSURE_STATUS separate.

Write one transaction report per album and one pilot `E2E測試報告.md` under the admitted private evidence scope, with actual tool events, original uncertainties, GOAL_GATE_DELTA, INFORMATION_GAIN and NEXT_AUTHORIZED_REAL_STEP. Reviewable summaries contain only permitted metadata/hashes/local references. Independent Acceptance must inspect original local evidence on the Mac through an authorized read-only path; manual transfer of raw private images to external/public services is not implied. Missing reviewer access is an Acceptance blocker, not invented inspection. Native failure imports/Issues require the actual admitted scope's supported accounting; no fake PASS or silent skip.

## 11. External review decision

Please return APPROVE / CHANGES_REQUIRED / REJECT with evidence-based findings on this exact Plan/contract scope, proposed budgets, source-backed cap1-versus-cap2 decision and minimum measured project-compatibility changes, logical-vs-native B03 disposition, manual-review/admission authority, private evidence and independent final Acceptance. APPROVE is the external decision only; it cannot create native authentication/admission, authorize unreviewed future source, reset exhausted history or grant foreground/GUI consent.

This planning turn ends with the frozen packet. No Task/run/Issue is created, no production cap/state/source is changed, no Luna starts, and LINE captures/inputs/downloads remain zero.
````

## Complete PUBLIC revision02 contract

````json
{
  "artifact_kind": "EXTERNAL_REVIEW_CANDIDATE_CONTRACT",
  "contract_revision": "line-two-album-review-candidate-2-cap1-sequential",
  "native_task_format_version": null,
  "native_task_id": null,
  "native_run_id": null,
  "native_schema_validation": "NOT_APPLICABLE_TO_UNALLOCATED_CANDIDATE",
  "publication_status": "LOCAL_CANDIDATE_ONLY_NOT_CONTROLLER_PUBLISHED",
  "goal": "One continuous authorized macOS LINE CUA workflow backs up two distinct NEW eligible albums, with NEW_ALBUM_A VERIFIED then automatic return to the same list, real bounded scroll/ordered overlap/new complete card, NEW_ALBUM_B detail MATCH, second Save All and NEW_ALBUM_B VERIFIED, followed by independent Acceptance.",
  "project_root": "<PRIVATE_PROJECT_ROOT>",
  "group_key": "GROUP_PRIVATE_01",
  "group_name": "GROUP_PRIVATE_01",
  "task_class": "CRITICAL",
  "workflow_policy": {
    "plan_review_required": true,
    "independent_acceptance_required": true,
    "handoff_review_required": false,
    "deterministic_handoff_exact_contract_copy": true
  },
  "role_policy": {
    "planner": "SOL_XHIGH_PLANNER_ONLY",
    "implementer": "LUNA_HIGH_IMPLEMENTER_ONLY",
    "plan_reviewer": "OWNER_MANUALLY_TRANSFERRED_EXTERNAL_INDEPENDENT_HIGH_REASONING_REVIEWER",
    "acceptance_reviewer": "EXTERNAL_INDEPENDENT_HIGH_REASONING_REVIEWER",
    "sol_self_review": false,
    "luna_review": false,
    "max_parallel_read_only_helpers": 0,
    "max_parallel_writers": 0
  },
  "current_turn_authority": {
    "planning_files_only": true,
    "production_edits": false,
    "native_allocations_or_imports": false,
    "gui_capture": false,
    "gui_input": false
  },
  "reference_pr": {
    "number": 8,
    "url": "https://github.com/s9008129/Line_backup/pull/8",
    "head": "8141a12925f58ee675d446033ed5b804ba66efd6",
    "frozen_scope_reused": false
  },
  "baseline": {
    "root": "<PRIVATE_PROJECT_ROOT>",
    "state_schema": 3,
    "state_revision": 35,
    "verified_album_protection": [
      {
        "alias": "VERIFIED_ALBUM_01",
        "opaque_fingerprint_reference": "OPAQUE_FP_6b27490d9210bc6a0c7a9bf9049a5c0a2d901061d77a24e8697ec29a28ac11a0",
        "group_reference": "GROUP_PRIVATE_01",
        "expected_images": 57,
        "status": "VERIFIED",
        "exact_binding": "PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED"
      },
      {
        "alias": "VERIFIED_ALBUM_02",
        "opaque_fingerprint_reference": "OPAQUE_FP_0a26366c9663e2bb14ee8d4a4a55d4404a8b30fc3d7c4af4838a2e5a2354e2a8",
        "group_reference": "GROUP_PRIVATE_01",
        "expected_images": 182,
        "status": "VERIFIED",
        "exact_binding": "PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED"
      }
    ],
    "active_batch": null,
    "active_writer_id": null,
    "context_lock": null,
    "source_build_and_git_identity": "PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED",
    "dispatch_authorized": false
  },
  "transaction_model": {
    "selected": "CAP1_SEQUENTIAL",
    "current_configured_cap": 1,
    "current_state_schema": 3,
    "lifecycle_service_mode": "backup_batch",
    "lifecycle_authorized_limit": 1,
    "configured_cap_unchanged": 1,
    "continuous_gui_workflows": 1,
    "distinct_cap1_lifecycles": 2,
    "aggregate_original_intent_quota": 2,
    "aggregate_save_all_quota": 2,
    "aggregate_chooser_quota": 2,
    "separate_run_action_owner_lease_destination": true,
    "stable_gui_observation_session_not_platform_attestation": true,
    "a_terminal_boundary": [
      "VERIFIED_AND_READBACK",
      "LEASE_CLOSED",
      "OWNER_CONTEXT_NULL",
      "STOP_AUTHORIZED_CAP1_COMPLETE_WITH_NO_CURRENT_ALBUM",
      "RELEASE",
      "ACTIVE_BATCH_NULL"
    ],
    "b_begin_before_return_scroll": true,
    "b_candidate_admitted_only_after_real_c1": true,
    "manifest_mode_proposed": "BOUNDED_SINGLE_CANDIDATE_V2_NOT_COMPLETE_CATALOG",
    "existing_terminal_apis": [
      "Service.finalize",
      "Service.stop",
      "Service.release",
      "Service.begin"
    ],
    "first_current_admission_blocker": "cli.py:127-128 GRANT_SCOPE;150-152 GRANT_LIVE_BINDING_REQUIRED binds exhausted ML08",
    "model_specific_premature_begin_blocker": "Service.begin:65 BATCH_BUSY until stop/release",
    "config_change_proposed": false,
    "production_route_status": "NOT_IMPLEMENTED_NOT_ADMITTED",
    "option_b_not_selected": "Requires config cap2 and incremental same-batch manifest/index change; adds delta without changing product oracle"
  },
  "scope": {
    "planning_write_paths": [
      "<PRIVATE_EXECUTION_SCOPE_REVISION02>/plan.md",
      "<PRIVATE_EXECUTION_SCOPE_REVISION02>/plan-contract.json",
      "<PRIVATE_EXECUTION_SCOPE_REVISION02>/review-packet.md"
    ],
    "proposed_adoption_write_paths": [
      "src/line_backup_batch/cli.py",
      "src/line_backup_batch/service.py",
      "src/line_backup_batch/store.py",
      "scripts/line_backup_cua_adapter.mjs",
      "tests/test_batch_authority.py",
      "tests/test_batch_lifecycle.py",
      "tests/test_cua_adapter.mjs",
      "<PRIVATE_EXECUTION_SCOPE_REVISION02>"
    ],
    "proposed_runtime_write_paths": [
      "state/backup_state.json",
      "state/run_log.md",
      "state/.line-backup-state.lock",
      "state/.line-backup-v3.tmp",
      "<PRIVATE_EXECUTION_SCOPE_REVISION02>/evidence"
    ],
    "destinations": {
      "root": "<PRIVATE_BACKUP_ROOT>",
      "template": "<PRIVATE_BACKUP_ROOT>/<PRIVATE_CANONICAL_GROUP_DIRECTORY>/<CANONICAL_START_END_COUNT_DERIVED_NEW_EMPTY_LEAF>",
      "max_new_empty_leaf_directories": 2,
      "existing_leaf_reuse": false,
      "overwrite": false,
      "symlinks": false
    },
    "forbidden": [
      "pinned Harness V4.8.0 edits",
      "original ML08 Task/Issue/c6/28 gates edits",
      "PR8 native state/Plan/contract edits",
      "old photo or terminal intent edits",
      "test-mode production writes",
      "unsupported native receipt import",
      "new generic executor/reviewer/migration framework",
      "third album",
      "input redispatch",
      "Save All replay",
      "mid-run Owner assistance for unattended PASS"
    ]
  },
  "privacy": {
    "private_path": "<PRIVATE_EXECUTION_SCOPE_REVISION02>/evidence",
    "directory_mode": "0700",
    "file_mode": "0600",
    "ignore_rule": "/private/",
    "git_check_ignore_before_capture": true,
    "index_content_check_before_any_commit_push": true,
    "force_add": false,
    "raw_evidence_to_public_git": false,
    "raw_evidence_transfer_to_external_reviewer_authorized": false,
    "full_display_capture_requires_fresh_explicit_consent": true,
    "controller_path_check_at_actual_admission": true
  },
  "cua": {
    "documented_entry": "cua.getApp(\"jp.naver.line.mac\")",
    "observation": "app.getAXStateAndScreenshot({emit:false,disableDiffing:true})",
    "scroll": "app.scroll(freshViewportTarget,\"down\",0.25)",
    "scroll_units": "MACOS_PAGES_REQUEST_NOT_PHYSICAL_DISTANCE_PROOF",
    "click": "app.click(freshPoint,{mouseButton:\"left\",clickCount:1})",
    "go_to_folder": "app.pressKey(\"super+shift+g\")",
    "path_input": "app.setValue(freshPathFieldIndex,exactDestination)",
    "key_return": "app.pressKey(\"Return\")",
    "atomic_pair": "PROPOSED_RECEIPT3_CALIBRATED_NO_IO_PAIR: pre-intent SCK calibration/closure; fresh anchor; one sequential ellipsis -> bounded wait -> Save All; no capture/I/O inside pair; not implemented",
    "menu_wait_ms_proposed": 1200,
    "mac_permissions": "UNTESTED_FOR_THIS_SCOPE",
    "hosted_local_process_or_retention_bridge": "NOT_DEMONSTRATED_BY_CUA_DOCUMENTATION",
    "host_transport_automatic_retry": "UNKNOWN",
    "native_duplicate_delivery": "UNKNOWN",
    "native_effect": "REQUIRES_REAL_POST_ACTION_EVIDENCE",
    "observation_identity": "stable local GUI continuity S; fresh owner A/B separately bound; neither is fabricated backend provenance"
  },
  "proposed_budgets": {
    "app_acquisitions": 3,
    "paired_observation_attempts_total": 80,
    "attempts_per_observation_checkpoint": 2,
    "extra_ax_only_refreshes": 23,
    "full_display_popup_observations": 4,
    "full_display_observations_per_album": 2,
    "album_card_clicks_per_album": 1,
    "album_card_clicks_total": 2,
    "calibration_menu_opens_per_album": 1,
    "calibration_safe_dismissals_per_album": 1,
    "atomic_pairs_per_album": 1,
    "save_all_logical_invocations_per_album": 1,
    "save_all_total": 2,
    "chooser_go_to_folder_per_album": 1,
    "chooser_set_value_per_album": 1,
    "chooser_return_per_album": 1,
    "chooser_confirmation_per_album": 1,
    "return_to_list": 1,
    "scroll_total": 4,
    "scroll_before_album_a_max": 3,
    "scroll_after_album_a_min": 1,
    "scroll_page_request": 0.25,
    "total_input_method_invocations": 23,
    "input_retries": 0,
    "input_transport_fallbacks": 0,
    "unknown_effect_redispatch": false,
    "filesystem_poll_min_interval_seconds": 5,
    "stable_identical_inventories_required": 3,
    "download_deadline_per_album_seconds": 600
  },
  "retry_policy": {
    "candidate_read_only_recaptures_per_checkpoint": 1,
    "task_input_retries": 0,
    "save_all_retry_allowed": false,
    "native_v4_8_schema_eligibility": "UNCHANGED; must remain separate from task-level and host-level behavior",
    "no_claim_of_native_or_transport_at_most_once": true,
    "loaded_intent_original_dispatch_authorized": false
  },
  "required_entry_dispositions": [
    "Authentic independent review of final exact bytes, legitimate workflow acceptance and deterministic Handoff",
    "Competent authority confirms authentic manual-review acceptance; no forged native model/session/effort/nonce/invitation/completion",
    "Genuinely independent new product scope and root-issue budget eligibility; no ML08 retry reset",
    "Lawfully reviewed new-scope grants, bounded single-candidate manifests, existing cap1 stop/release boundaries, strict global ledger and scoped receipt3; no exhausted ML08 grant reuse",
    "Binding execution policy accepts stated logical-at-most-once controls or supplies supported native guarantee; UNKNOWN remains explicit",
    "Current hosted capture/retention/geometry and permission readiness without unauthorized LINE preflight",
    "Supported truthful non-PASS accounting for this new scope; old Task555 one-Issue permission does not transfer",
    "Fresh foreground handoff and scoped GUI/private-display/download/state consent immediately before live execution"
  ],
  "protected_history": {
    "original_task": "TASK-4acb4326ea2a4c50ace6f333f2de8751",
    "task_state": "BLOCKED",
    "issue_state": "WAIT_HUMAN",
    "c6_run": "c6c6b55d-865f-467b-94ba-3fd669df97ec",
    "c6_consumed": 1,
    "c6_retries_remaining": 0,
    "original_gate_count": 28,
    "harness_version": "4.8.0_IMMUTABLE"
  },
  "gate_order": [
    {
      "gate_id": "P0",
      "purpose": "AUTHORITY_AND_REVIEW",
      "owner": "INDEPENDENT_REVIEWER_AND_AUTHORITY",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "INDEPENDENT_REVIEWER_AND_AUTHORITY",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "T0",
      "purpose": "PREFLIGHT",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "A1",
      "purpose": "ALBUM_A_CARD_DETAIL",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "A2",
      "purpose": "ALBUM_A_SAVE_ALL_CHOOSER",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "A3",
      "purpose": "ALBUM_A_FILES_COMMIT",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "C1",
      "purpose": "RETURN_SCROLL_NEW_CARD",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "B1",
      "purpose": "ALBUM_B_CARD_DETAIL_DISPATCH",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "B2",
      "purpose": "ALBUM_B_FILES_COMMIT",
      "owner": "IMPLEMENTER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "IMPLEMENTER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    },
    {
      "gate_id": "X1",
      "purpose": "TWO_ALBUM_INDEPENDENT_ACCEPTANCE",
      "owner": "INDEPENDENT_ACCEPTANCE_REVIEWER",
      "required": true,
      "goal_criticality": "GOAL_CRITICAL",
      "evidence_role": "INDEPENDENT_ACCEPTANCE_REVIEWER",
      "closure_gate": true,
      "initial_verdict": "NOT_RUN"
    }
  ],
  "acceptance": {
    "requires_two_new_distinct_fingerprints": true,
    "requires_real_post_a_scroll_and_new_complete_card": true,
    "requires_both_files_decode_hash_and_atomic_verified_readback": true,
    "requires_one_uninterrupted_workflow": true,
    "owner_intervention_means": "ASSISTED_PARTIAL",
    "tool_return_is_semantic_pass": false,
    "human_visual_is": "OBSERVED",
    "independent_acceptance_required": true,
    "scope_completion_label": "UNATTENDED_TWO_ALBUM_PASS_ONLY_WITH_ALL_GATE_EVIDENCE"
  },
  "review_status": "CHANGES_REQUIRED_REVISION02_AWAITING_INDEPENDENT_RE_REVIEW",
  "b03_status": "BLOCKED_HOST_NATIVE_GUARANTEE_UNPROVEN_POLICY_DISPOSITION_REQUIRED",
  "b05_status": "BLOCKED_MANUAL_EXTERNAL_REVIEW_NATIVE_ACCEPTANCE_UNPROVEN",
  "native_admission": "NOT_GRANTED",
  "gui_consent": "NOT_GRANTED",
  "review_basis": {
    "pr_number": 9,
    "reviewed_head": "73987af9e32577644f6f6957a5a92ea62478d9b6",
    "comment": "https://github.com/s9008129/Line_backup/pull/9#issuecomment-6164378480",
    "verdict": "CHANGES_REQUIRED_DESIGN_ONLY_NOT_NATIVE_RECEIPT"
  },
  "global_gui_boundary": {
    "status": "PROPOSED_NOT_IMPLEMENTED",
    "current_source": "Store.reserve_gui uses locked durable all-entry sum; missing ledger currently initializes empty",
    "one_fixed_task_ledger": true,
    "cap": 23,
    "scope_owner_grants_share_path_task_cap": true,
    "slot_keys": [
      "A.CARD",
      "A.CAL_OPEN",
      "A.CAL_DISMISS",
      "A.ATOMIC_ELLIPSIS",
      "A.SAVE_ALL",
      "A.GO_TO_FOLDER",
      "A.SET_PATH",
      "A.PATH_RETURN",
      "A.CHOOSER_CONFIRM",
      "B.CARD",
      "B.CAL_OPEN",
      "B.CAL_DISMISS",
      "B.ATOMIC_ELLIPSIS",
      "B.SAVE_ALL",
      "B.GO_TO_FOLDER",
      "B.SET_PATH",
      "B.PATH_RETURN",
      "B.CHOOSER_CONFIRM",
      "RETURN_A_TO_LIST",
      "SCROLL_1",
      "SCROLL_2",
      "SCROLL_3",
      "SCROLL_4"
    ],
    "init": "one explicit admitted preflight exclusive creation; existing once-initialized ledger required afterward",
    "missing_ledger": "STOP_NO_REINITIALIZATION",
    "unknown_reserved_consumed": "ALL_COUNT_NO_REFUND_NO_REPLAY",
    "slot_uniqueness_global": true,
    "atomic_pair_reserve_count": 2,
    "chooser_reserve_count": 4,
    "calibration_reserve_count": 2,
    "before_a_scroll_limit": 3,
    "post_a_scroll_min": 1,
    "total_scroll_limit": 4,
    "native_delivery_guarantee": "UNKNOWN_B03_BLOCKED"
  },
  "atomic_menu_compatibility": {
    "current": "IN_PAIR_SCK_CAPTURE_GUARD_AND_RECEIPT2_REQUIRED_CONFLICTS_WITH_RC2_NO_IO",
    "proposed": "SCOPED_RECEIPT3_CALIBRATED_NO_IO_PAIR_NOT_IMPLEMENTED",
    "pre_intent_evidence": [
      "affirmative_actual_menu",
      "SCK_support_guard",
      "safe_close_no_activation",
      "fresh_detail_ellipsis_geometry"
    ],
    "receipt_binding": [
      "run",
      "action",
      "fresh_transaction_owner",
      "stable_gui_observation_session",
      "config_source_contract",
      "calibration_menu_support_guard_closure_refs",
      "original_intent_frame",
      "global_slot_reservations",
      "chooser_phases_path_confirmation_download"
    ],
    "forbidden_claim": "NO_FAKE_IN_PAIR_SCK_MENU_GUARD_PASS_OR_CURRENT_POPUP",
    "legacy_receipts_unchanged": true,
    "independent_source_review_and_acceptance_before_native_save_all": true
  },
  "source_inspection": {
    "provenance": "LOCALLY_INSPECTED_CURRENT_MAC_SOURCE_NOT_INDEPENDENT_FULL_SOURCE_REHASH",
    "files": [
      {
        "path": "src/line_backup_batch/cli.py",
        "bytes": 19613,
        "sha256": "f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "bytes": 45295,
        "sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/schema.py",
        "bytes": 2623,
        "sha256": "d400cb0e5cdee4a0f0ce555e3222a590093c2dcaae9f10f464e205b9d1da3302"
      },
      {
        "path": "src/line_backup_batch/observations.py",
        "bytes": 48734,
        "sha256": "db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "bytes": 24794,
        "sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "bytes": 44833,
        "sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      },
      {
        "path": "src/line_backup_acceptance/project_binding.py",
        "bytes": 27866,
        "sha256": "f8894652fc9070416df5544b9573c26cee440300ca8a14f201f654f3886874f8"
      },
      {
        "path": "tests/test_batch_authority.py",
        "bytes": 14930,
        "sha256": "e7adfff030b5105cf342b8f0bc1af72014eb6ab449e1ed600600423450f358e5"
      },
      {
        "path": "tests/test_batch_lifecycle.py",
        "bytes": 2256,
        "sha256": "aeeedbf61bf29a80ee6529628223dce4c1c01783f6da6c64b01e81242f11011b"
      },
      {
        "path": "tests/test_batch_observations.py",
        "bytes": 18502,
        "sha256": "92defeef97b5d27c79c83ad3c9fdbb4c26ddbef55f0f0eb4f6fe4f2b898fb222"
      },
      {
        "path": "tests/test_cua_adapter.mjs",
        "bytes": 18529,
        "sha256": "0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd"
      }
    ],
    "state_revision": 35,
    "current_max_albums_per_run": 1,
    "exact_config_state_git_hashes": "PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED_RETAINED_IN_PRIVATE_CANDIDATE",
    "source_excerpts": [
      {
        "path": "src/line_backup_batch/cli.py",
        "start_line": 127,
        "end_line": 128,
        "excerpt_sha256": "56928af37c8cf27c93117e11893c9ef1a6018c38fa1f6171df1fa6336995aa3e",
        "source_sha256": "f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6"
      },
      {
        "path": "src/line_backup_batch/cli.py",
        "start_line": 150,
        "end_line": 152,
        "excerpt_sha256": "7698c39735afaaec2c03f1176cf8b2df53e3a12fb0f70de62b336bf34e5dad19",
        "source_sha256": "f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6"
      },
      {
        "path": "src/line_backup_batch/cli.py",
        "start_line": 192,
        "end_line": 207,
        "excerpt_sha256": "5ad3faf88c4ff92c64c003a34db33c67204fe0cd0d2b9e8617887491c1e2bae4",
        "source_sha256": "f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 59,
        "end_line": 72,
        "excerpt_sha256": "438d65fbe363ff5e89252775a957bd4844431be4fe03c7f19aeb8119a9f8bb05",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 93,
        "end_line": 98,
        "excerpt_sha256": "bf5344721694cbbf180e267acfadd2292c4b4df90856e314ef6884b60b2a2a6b",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 190,
        "end_line": 205,
        "excerpt_sha256": "8324a1102bb06bf2bb83e9c97dc0870207d4ffe4cc8c5c8c808f79de8c56fa38",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 272,
        "end_line": 289,
        "excerpt_sha256": "235359cf704e897bc9cd982e90812e243cf60e346cdea1e0c386f0bb4020871a",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 306,
        "end_line": 314,
        "excerpt_sha256": "479b1f55f7d97e82ac91fcb2cebbaf64e1cceddd661c7e9b71f4927596346207",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 378,
        "end_line": 390,
        "excerpt_sha256": "ca9219582711a0f379d7e090e7ba2e00f7d8b85710a904002156c56a8da953bf",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 422,
        "end_line": 431,
        "excerpt_sha256": "38b2d67839df9e68ebfe2aeaa78773688ac616ab8abebfce9183afb76d7f5d2e",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 450,
        "end_line": 460,
        "excerpt_sha256": "e2c7cf084b6151e08d8aeecdca97f4f15e734a5ccdd5314d3989acfd9134d405",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 529,
        "end_line": 554,
        "excerpt_sha256": "222d8808d8b78476641d96510d9f2af773ea583a2ca41db5e29d40442e03ddea",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/service.py",
        "start_line": 593,
        "end_line": 603,
        "excerpt_sha256": "84c985349a08beb15921db1c573843e8f095b4d04a704d59e0b0aea591baa68c",
        "source_sha256": "54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "start_line": 129,
        "end_line": 140,
        "excerpt_sha256": "5253063a321341129ac1e3e0df8b7a4ff7993066d664fa2b3bf217998acede4c",
        "source_sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "start_line": 203,
        "end_line": 215,
        "excerpt_sha256": "1fe1550bbf35047e22c49c34f06089353ef7ad1b0abfd47de522e2c3018f2da3",
        "source_sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "start_line": 232,
        "end_line": 238,
        "excerpt_sha256": "8e9d61a6803b8e236ec995512bca9744859b5686251ec27126828245e8a70ee0",
        "source_sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "start_line": 264,
        "end_line": 275,
        "excerpt_sha256": "31b9a0ff3a2c9bf8a2e74854756cdae10d74399be070b8655f9f58f91607975f",
        "source_sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "src/line_backup_batch/store.py",
        "start_line": 353,
        "end_line": 384,
        "excerpt_sha256": "a0e34c660ed48a3c57078ff8b56039039abe1f8e7742bb61c1cef28927ce7a0d",
        "source_sha256": "f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc"
      },
      {
        "path": "src/line_backup_batch/schema.py",
        "start_line": 30,
        "end_line": 34,
        "excerpt_sha256": "a93d21a401543f15a71d0c5ceece1ad71db9bf58b35fb044249db0f90e6455f1",
        "source_sha256": "d400cb0e5cdee4a0f0ce555e3222a590093c2dcaae9f10f464e205b9d1da3302"
      },
      {
        "path": "src/line_backup_batch/observations.py",
        "start_line": 601,
        "end_line": 607,
        "excerpt_sha256": "0fb3a2ebaf4bbbb51c503e061ea0f1564b381c92c65fa459ebafc1b38fac1df0",
        "source_sha256": "db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587"
      },
      {
        "path": "src/line_backup_batch/observations.py",
        "start_line": 629,
        "end_line": 636,
        "excerpt_sha256": "9c5346c6104f72eb4e0b7a0fa0d9281eaae07bc703804ec21b8a437ed2d5b2cd",
        "source_sha256": "db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "start_line": 48,
        "end_line": 76,
        "excerpt_sha256": "8587ba9d5d8ef53d97fd523e76f19d220cbb27908ae8bf0f9d3b585942c71f8e",
        "source_sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "start_line": 130,
        "end_line": 138,
        "excerpt_sha256": "9fdaa09a6c77aa058d6a2e6b5ab5adda390c0de7502182feeededc632a4f52c1",
        "source_sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "start_line": 294,
        "end_line": 313,
        "excerpt_sha256": "a67fb0999c63e877b30c3b3e2447e99204a6b173f9b550500d0ac40336641e38",
        "source_sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "start_line": 319,
        "end_line": 335,
        "excerpt_sha256": "13b1f0a3f6a75a91483b0ab3437f391b3294e215699efe252a5e793786d45b4d",
        "source_sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      },
      {
        "path": "scripts/line_backup_cua_adapter.mjs",
        "start_line": 613,
        "end_line": 628,
        "excerpt_sha256": "2bcada722bedd859c38659478425f675e4d3c31f39c4de57aea58475bf0b64f4",
        "source_sha256": "d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f"
      }
    ],
    "excerpt_text_location": "review-packet.public-review.md; exact line ranges and excerpt hashes match private source"
  },
  "focused_non_gui_validation": {
    "python_existing": {
      "selected": 10,
      "passed": 10,
      "exit_code": 0
    },
    "node_existing": {
      "exit_code": 1,
      "selected": 10,
      "passed": 9,
      "failed": 1,
      "failure_name": "native scroll is limited to one quarter viewport per invocation",
      "failure": "SCROLL_NO_VISUAL_CHANGE",
      "scope": "MOCKED_APP_ONLY_NOT_LINE_PRODUCT_PASS"
    },
    "fixture_terminal_and_global23_cases": {
      "exit_code": 0,
      "output": "CAP1_FINALIZE_STOP_RELEASE_FRESH_OWNER_BEGIN=PASS_FIXTURE_API_ONLY\nGLOBAL23_CROSS_OWNER_RUN_RESERVED_UNKNOWN_NO_REFUND=PASS_FIXTURE_POOL_ONLY_NOT_SLOT_ENFORCEMENT\nCURRENT_MISSING_LEDGER_REINITIALIZATION=CONFIRMED_GAP_NEW_SCOPE_MUST_REFUSE\n"
    },
    "synthetic_scroll_comparison": {
      "exit_code": 0,
      "assertions": 6
    },
    "proposed_new_scope_implementation_checks": "NOT_RUN_NEW_IMPLEMENTATION_PROHIBITED",
    "not_real_line_product_pass": true
  },
  "public_review_copy": {
    "label": "PUBLIC_REVIEW_COPY — REDACTED — NOT_EXECUTABLE — NOT_NATIVE_ADMISSION",
    "private_candidate_revision": "line-two-album-review-candidate-2-cap1-sequential",
    "executable": false,
    "native_admission": false,
    "production_schema_validity": "NOT_ASSERTED_PLACEHOLDERS_AND_REDACTED_PROJECTION",
    "exact_private_binding_validation": "PRIVATE_BINDING_NOT_EXTERNALLY_VERIFIED",
    "review_delivery": "SAME_GITHUB_PR9_INDEPENDENT_RE_REVIEW",
    "original_revision01_unchanged": true
  }
}
````

## Current Mac-local source evidence

These are inspected CURRENT source excerpts, not native/platform attestations or claims that proposed changes exist. Full-file and excerpt SHA-256 bind exact local bytes and line ranges. Existing source is not in this PR HEAD; an independent reviewer can examine these excerpts, but full hidden source/build/config binding is not independently rehashed by a public-copy review.

### src/line_backup_batch/cli.py:127–128

SOURCE_SHA256=f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6
EXCERPT_SHA256=56928af37c8cf27c93117e11893c9ef1a6018c38fa1f6171df1fa6336995aa3e

```python
    else:
        require(grant['artifact_dir']==CONTINUATION,'GRANT_SCOPE')
```

### src/line_backup_batch/cli.py:150–152

SOURCE_SHA256=f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6
EXCERPT_SHA256=7698c39735afaaec2c03f1176cf8b2df53e3a12fb0f70de62b336bf34e5dad19

```python
            require(grant['contract_path']==CONTRACT_PATH and grant['contract_sha256']==CONTRACT_SHA256
                and grant['native_binary_sha256']==NATIVE_BINARY_SHA256 and grant['gui_ledger']==GUI_LEDGER_PATH,
                'GRANT_LIVE_BINDING_REQUIRED')
```

### src/line_backup_batch/cli.py:192–207

SOURCE_SHA256=f8bf0ef25fd5d2d1dbce1de590016aaa383122703048c372db0bb67d5a382ef6
EXCERPT_SHA256=5ad3faf88c4ff92c64c003a34db33c67204fe0cd0d2b9e8617887491c1e2bae4

```python
            grant_slot={CONTINUATION+'/live-grant-1.json':0,CONTINUATION+'/live-grant-2.json':1}.get(path)
            require(grant_slot is not None and grant['owner']==authorization['authorized_owners'][grant_slot],
                'GRANT_OWNER_SLOT_MISMATCH')
            require(authorization.get('decision_code')=='A'
                and authorization.get('plan_review_decision')=='USER_WAIVED_NOT_RUN'
                and authorization.get('sensor_scope')==scope
                and authorization.get('album_quota')==grant['album_quota']
                and authorization.get('save_all_dispatch_cap')==grant['save_all_dispatch_limit']
                and authorization.get('chooser_confirmation_cap')==grant['chooser_confirmation_limit']
                and authorization.get('additional_reversible_gui_invocation_cap')==grant['reversible_gui_invocation_limit']
                and authorization.get('config_albums_per_lifecycle')==grant['lifecycle_album_limit']==1
                and authorization.get('independent_acceptance_required') is True,
                'AUTHORIZATION_SCOPE_MISMATCH')
            require(grant['album_quota']==2 and grant['lifecycle_album_limit']==1 and grant['save_all_dispatch_limit']==2
                and grant['chooser_confirmation_limit']==2 and grant['reversible_gui_invocation_limit']==1000,
                'GRANT_QUOTA_MISMATCH')
```

### src/line_backup_batch/service.py:59–72

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=438d65fbe363ff5e89252775a957bd4844431be4fe03c7f19aeb8119a9f8bb05

```python
    def begin(self,expected,mode,limit):
        require(mode in ('catalog_only','backup_batch') and integer(limit),'INVALID_BATCH_SCOPE')
        require(limit==0 if mode=='catalog_only' else limit>0,'INVALID_BATCH_SCOPE')
        batch_id='BATCH-'+uuid.uuid4().hex
        def acquire(cfg,s):
            require(s['active_batch'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'BATCH_BUSY')
            require(all(r['workflow_outcome']=='VERIFIED' or (r['workflow_outcome']=='SAFE_ABORT' and r['intent'] is None
                and r['manual_reconciliation_required'] is False) for r in s['runs']),'UNRESOLVED_HISTORY')
            s['active_batch']=dict(batch_id=batch_id,owner_execution_id=self.owner,group_key=cfg['group_key'],mode=mode,
                phase='CATALOG',policy_version=POLICY,config_sha256=expected['config_sha256'],source_sha256=expected['source_sha256'],
                created_at=utc_now(),authorized_new_download_limit=limit,configured_new_download_limit=cfg['max_albums_per_run'],
                new_transactions_reserved=0,manifest_reference=None,next_index=0,current_album_run_id=None,stop_reason=None)
            return dict(batch_id=batch_id,status='BATCH_OWNED')
        return self.store._update(expected,acquire,operation='begin')
```

### src/line_backup_batch/service.py:93–98

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=bf5344721694cbbf180e267acfadd2292c4b4df90856e314ef6884b60b2a2a6b

```python
        m=dict(version=1,project_root=self.store.root,group_key=snap['config']['group_key'],config_sha256=expected['config_sha256'],
            source_sha256=expected['source_sha256'],session_id=session,identities=identities,frames=records,policy=POLICY)
        ref=self.publish('catalog-'+uuid.uuid4().hex+'.json',m)
        def admit(cfg,s):
            b=self.batch(s);require(b['phase']=='CATALOG' and b['manifest_reference'] is None,'ALREADY_ADMITTED')
            require(b['config_sha256']==expected['config_sha256'] and b['source_sha256']==expected['source_sha256'],'BATCH_AUTHORITY_DRIFT')
```

### src/line_backup_batch/service.py:190–205

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=8324a1102bb06bf2bb83e9c97dc0870207d4ffe4cc8c5c8c808f79de8c56fa38

```python
    def run(self,s):
        b=self.batch(s);require(b['current_album_run_id'] is not None,'NO_ACTIVE_ALBUM')
        r=next(r for r in s['runs'] if r['run_id']==b['current_album_run_id'])
        require(r['workflow_outcome']=='IN_PROGRESS' and s['active_writer_id']==self.owner,'FOREIGN_ALBUM_OWNER')
        return b,r

    def calibrate(self,expected,detail,calibration,menu,closure):
        reader=ProjectReader(self.store.root)
        try:
            snap=self.store.snapshot();require(snap['receipt']==expected,'STALE_CAS')
            b,r=self.run(snap['state']);m=self.manifest(b,reader,snap['config'])
            require(r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            for record in (detail,closure):
                frame(reader,record,snap['config'],session=m['session_id'])
                require(record['surface']=='ALBUM_DETAIL' and len(record['cards'])==1
                    and record['cards'][0]['fingerprint']==r['fingerprint'],'TARGET_MISMATCH')
```

### src/line_backup_batch/service.py:272–289

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=235359cf704e897bc9cd982e90812e243cf60e346cdea1e0c386f0bb4020871a

```python
        def intent(cfg,s):
            b,r=self.run(s);require(r['phase']=='SAVE_ALL_CALIBRATION' and r['intent'] is None,'LOADED_INTENT_NO_PERMISSION')
            require(b['new_transactions_reserved']<min(b['authorized_new_download_limit'],b['configured_new_download_limit']),'LIMIT_REACHED')
            require(content.inventory(self.store.root,r['destination'])==[],'DESTINATION_NONEMPTY')
            previous=strict_json(r['checkpoint']['evidence'].encode(),'INVALID_CALIBRATION_RECORD')
            require(previous['closure']['layout_key']==fresh['layout_key'] and previous['closure']['pid']==fresh['pid']
                and previous['closure']['window_id']==fresh['window_id'],'CALIBRATION_LAYOUT_DRIFT')
            cal=previous['calibration'];action='ACTION-'+uuid.uuid4().hex
            r['intent']=dict(action_id=action,committed_at=utc_now(),owner_execution_id=self.owner,group_key=cfg['group_key'],
                fingerprint=r['fingerprint'],destination=r['destination'],calibration=cal,save_all_retry_allowed=False,
                dispatch_outcome='NOT_ATTEMPTED',trigger_outcome='NOT_APPLICABLE')
            r['intent_state']='INTENT_COMMITTED';b['new_transactions_reserved']+=1
            self.event(r,'SAVE_ALL_INTENT_COMMITTED',dict(fresh=fresh,action_id=action))
            return dict(status='ORIGINAL_INTENT_COMMITTED',run_id=r['run_id'],action_id=action,owner=self.owner,
                fingerprint=r['fingerprint'],destination=r['destination'],frame_id=fresh['frame_id'],session_id=m['session_id'],
                ellipsis=cal['ellipsis'],save_all=cal['save_all_point'],dispatch_authorized=not self.store.fixture,
                fixture=self.store.fixture)
        result=self.store._update(expected,intent,operation='intent');result['new_intent']=True
```

### src/line_backup_batch/service.py:306–314

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=479b1f55f7d97e82ac91fcb2cebbaf64e1cceddd661c7e9b71f4927596346207

```python
                    require(version=='cua-dispatch-receipt-2' and set(receipt_data)==DISPATCH_RECEIPT_V2_KEYS,
                        'INVALID_DISPATCH_RECEIPT')
                    require(receipt_data['cease_input'] is True and receipt_data['save_all_click_count']==1,
                        'RECEIPT_TRIGGER_UNPROVEN')
                    event_order=DISPATCH_EVENT_ORDER_V2
                    require(self.store.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
                    from .cli import authorize
                    grant=authorize(self.store.root,self.store.authorization_path,False,'dispatch')
                    require(grant['grant_version']=='line-batch-execution-grant-2','LIVE_RECEIPT_V2_REQUIRED')
```

### src/line_backup_batch/service.py:378–390

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=ca9219582711a0f379d7e090e7ba2e00f7d8b85710a904002156c56a8da953bf

```python
                require(receipt_data['run_id'] and receipt_data['action_id'] and receipt_data['execution_id']==self.owner
                    and receipt_data['session_id'],'RECEIPT_IDENTITY')
                support=strict_json(artifact(reader,receipt_data['support']),'INVALID_SCK_SUPPORT')
                require(support.get('frame_id')==receipt_data['pair_frame_id']
                    and support.get('session_id')==receipt_data['session_id'],'RECEIPT_SUPPORT_BINDING')
                popup_raw=artifact(reader,support.get('sck_frame'))
                require(sha(popup_raw)==receipt_data['popup_frame_id']
                    and receipt_data['popup_frame_id']!=receipt_data['pair_frame_id'],'RECEIPT_POPUP_BINDING')
                guard=receipt_data['guard']
                require(isinstance(guard,dict) and guard.get('verdict')=='PASS' and guard.get('provider')=='SCREEN_CAPTURE_KIT'
                    and guard.get('pairFrameId')==receipt_data['pair_frame_id']
                    and guard.get('popupFrameId')==receipt_data['popup_frame_id']
                    and guard.get('supportSha256')==receipt_data['support']['sha256'],'RECEIPT_GUARD_UNPROVEN')
```

### src/line_backup_batch/service.py:422–431

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=38b2d67839df9e68ebfe2aeaa78773688ac616ab8abebfce9183afb76d7f5d2e

```python
        def record(cfg,s):
            b,r=self.run(s);require(r['intent'] is not None and r['dispatch_evidence'] is None,'DISPATCH_ALREADY_RECORDED')
            d=copy.deepcopy(evidence)
            require(d['run_id']==r['run_id'] and d['action_id']==r['intent']['action_id'] and d['execution_id']==self.owner,'DISPATCH_IDENTITY')
            if receipt_data is not None:
                require(receipt_data['run_id']==r['run_id'] and receipt_data['action_id']==r['intent']['action_id']
                    and receipt_data['execution_id']==self.owner and receipt_data['session_id']==b['owner_execution_id'],'RECEIPT_IDENTITY')
                require(json_bytes(receipt_data['chooser'])==json_bytes(chooser),'RECEIPT_CHOOSER_MISMATCH')
                point=receipt_data['guard']['actionPoint']
                require(json_bytes(point)==json_bytes(r['intent']['calibration']['save_all_point']),'RECEIPT_GUARD_POINT')
```

### src/line_backup_batch/service.py:450–460

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=e2c7cf084b6151e08d8aeecdca97f4f15e734a5ccdd5314d3989acfd9134d405

```python
                require(d['download_started'] is True,'DOWNLOAD_START_NOT_OBSERVED')
            r['dispatch_evidence']=copy.deepcopy(d)
            confirmed=(d['save_all_click_count']==1 and d['save_all_invocation_attempted'] is True
                and d['folder_chooser_appeared'] is True and d['download_started'] is True
                and (download_proven if receipt_data and receipt_data['version']=='cua-dispatch-receipt-2' else download_started is True))
            require(chooser['destination']==r['destination'] and chooser['confirmation_attempts']==1
                and chooser['full_path']==r['destination'] and chooser['leaf']==Path(r['destination']).name,'CHOOSER_DESTINATION_MISMATCH')
            require(chooser['action_id']==r['intent']['action_id'] and chooser['session_id']==b['owner_execution_id'],'FOREIGN_CHOOSER')
            r['intent']['dispatch_outcome']='RETURNED' if confirmed else 'UNKNOWN'
            r['intent']['trigger_outcome']='TRIGGER_CONFIRMED' if confirmed else 'UNKNOWN'
            r['intent_state']='TRIGGER_CONFIRMED' if confirmed else 'TRIGGER_UNKNOWN'
```

### src/line_backup_batch/service.py:529–554

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=222d8808d8b78476641d96510d9f2af773ea583a2ca41db5e29d40442e03ddea

```python
            s['active_writer_id']=None;s['context_lock']=None;b['current_album_run_id']=None;b['next_index']+=1
            return dict(status='VERIFIED',run_id=current['run_id'],fingerprint=current['fingerprint'],verification_reference=vref)
        outcome=self.store._update(expected,finish,operation='finalize')
        if fault=='DRIFT_AFTER_COMMIT':
            (Path(r['destination'])/'post-commit-drift.png').write_bytes(b'\x89PNG\r\n\x1a\npost-commit fixture drift')
        try:
            post=content.inventory(self.store.root,r['destination'])
            require(post==verification['inventory'],'FINALIZE_READBACK_UNCERTAIN')
        except Exception as exc:
            failure=getattr(exc,'code',None) or str(exc)
            self.publish('finalize-drift-'+r['run_id']+'.json',dict(version='line-backup-finalize-drift-1',run_id=r['run_id'],
                state_committed=True,state_revision=outcome['receipt']['revision'],
                pre_inventory_sha256=sha(json_bytes(verification['inventory'])),post_inventory_sha256=None,
                at=utc_now(),failure=failure))
            self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
                state='UNVERIFIED',state_revision=outcome['receipt']['revision'],at=utc_now()))
            raise AcceptanceError('FINALIZE_READBACK_UNCERTAIN',str(exc),4) from exc
        self.publish('lease-close-'+r['run_id']+'.json',dict(version='line-backup-lease-close-1',run_id=r['run_id'],
            state='CLOSED',post_inventory_sha256=sha(json_bytes(post)),state_revision=outcome['receipt']['revision'],at=utc_now()))
        return outcome

    def stop(self,expected,reason):
        def stop(cfg,s):
            b=self.batch(s)
            if b['current_album_run_id'] is not None:
                _,r=self.run(s);r['workflow_outcome']='SAFE_ABORT';r['stop_reason']=reason
```

### src/line_backup_batch/service.py:593–603

SOURCE_SHA256=54ec4abbaad139d19a0c3be1fda24427825a84678270289512581e4675535da6
EXCERPT_SHA256=84c985349a08beb15921db1c573843e8f095b4d04a704d59e0b0aea591baa68c

```python
    def release(self,expected):
        def release(cfg,s):
            b=s['active_batch']
            require(b is not None and b['owner_execution_id']==self.owner and b['phase'] in ('STOPPED','COMPLETED'),
                'TERMINAL_BATCH_REQUIRED')
            require(b['current_album_run_id'] is None and s['active_writer_id'] is None and s['context_lock'] is None,'ALBUM_BUSY')
            require(all(run_barrier_ok(r) for r in s['runs']),'UNRESOLVED_BARRIER')
            result=dict(status='BATCH_RELEASED',batch_id=b['batch_id'],prior_phase=b['phase'],stop_reason=b['stop_reason'])
            s['active_batch']=None
            return result
        return self.store._update(expected,release,operation='release')
```

### src/line_backup_batch/store.py:129–140

SOURCE_SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc
EXCERPT_SHA256=5253063a321341129ac1e3e0df8b7a4ff7993066d664fa2b3bf217998acede4c

```python
def enforce_grant_quota(grant,operation,state):
    """Conservatively count persisted original intents across separate lifecycle batches."""
    used=sum(1 for item in state['runs'] if item.get('batch_id') is not None and item.get('intent') is not None)
    allowance=min(grant['album_quota'],grant['save_all_dispatch_limit'],grant['chooser_confirmation_limit'])
    if operation=='begin':
        batch=state['active_batch']
        require(batch is not None and batch.get('owner_execution_id')==grant['owner']
            and batch.get('authorized_new_download_limit',0)<=grant['lifecycle_album_limit']
            and batch.get('authorized_new_download_limit',0)<=max(0,allowance-used),'GRANT_ALBUM_QUOTA')
    if operation=='intent':
        require(used<=allowance,'GRANT_DISPATCH_QUOTA')
    return used
```

### src/line_backup_batch/store.py:203–215

SOURCE_SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc
EXCERPT_SHA256=1fe1550bbf35047e22c49c34f06089353ef7ad1b0abfd47de522e2c3018f2da3

```python
    def _update(self,expected,transform,*,operation=None,migration=False,snapshot_path=None,fault=None):
        """Internal operation-scoped commit primitive; public callers use Service transitions."""
        grant=None
        require(operation in TRANSITION_FIELDS,'OPERATION_REQUIRED')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            require(migration==(operation=='migrate'),'OPERATION_MISMATCH')
            grant=authorize(self.root,self.authorization_path,False,operation)
        with self.guard() as (r,parent,check_lock,lock_identity):
            cfg,before,actual,raw,_=self.load(r)
            require(actual==expected,'STALE_CAS')
            require(before['schema_version']==(2 if migration else 3),'STATE_VERSION_READ_ONLY')
```

### src/line_backup_batch/store.py:232–238

SOURCE_SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc
EXCERPT_SHA256=8e9d61a6803b8e236ec995512bca9744859b5686251ec27126828245e8a70ee0

```python
            validate_nested_delta(before,candidate,operation)
            if grant is not None:
                enforce_grant_quota(grant,operation,candidate)
            candidate['revision']=before['revision']+1
            from line_backup_acceptance.common import validate_state_strict
            validate_state_strict(candidate)
            validate_history(candidate,cfg,r,allow_v3=True)
```

### src/line_backup_batch/store.py:264–275

SOURCE_SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc
EXCERPT_SHA256=31b9a0ff3a2c9bf8a2e74854756cdae10d74399be070b8655f9f58f91607975f

```python
                require(ProjectReader.ident(os.stat('backup_state.json',dir_fd=parent,follow_symlinks=False))==tuple(actual['state_identity']),
                    'STATE_INODE_DRIFT')
                self._require_temp_owner(parent,temporary,owner)
                os.replace(temporary,'backup_state.json',src_dir_fd=parent,dst_dir_fd=parent);replaced=True
                os.fsync(parent)
                if fault=='AFTER_REPLACE':raise AcceptanceError('READBACK_UNCERTAIN','fixture fault',4)
                check_lock()
                back=ProjectReader(self.root)
                try:
                    written,_=back.read(STATE)
                    require(written==body,'READBACK_UNCERTAIN')
                    _,_,receipt,_,_=self.load(back)
```

### src/line_backup_batch/store.py:353–384

SOURCE_SHA256=f7ff0a3a8622d7562935dfd24979fbd0de20a8c58822f6948964bb77dd30ddfc
EXCERPT_SHA256=a0e34c660ed48a3c57078ff8b56039039abe1f8e7742bb61c1cef28927ce7a0d

```python
    def _ledger_open(self,r,grant):
        path=self.ledger_path(grant);cap=grant['reversible_gui_invocation_limit']
        ledger=self._ledger_read(r,path)
        if ledger is None:
            ledger=dict(version=GUI_LEDGER_VERSION,task_id=grant['task_id'],cap=cap,entries=[])
        require(isinstance(ledger,dict) and set(ledger)=={'version','task_id','cap','entries'}
            and ledger['version']==GUI_LEDGER_VERSION and isinstance(ledger['entries'],list)
            and ledger['task_id']==grant['task_id'] and ledger['cap']==cap,'GUI_LEDGER_DRIFT')
        return path,ledger,cap

    def reserve_gui(self,grant,data):
        """Reserve GUI inputs before they happen; reservations are never refunded."""
        kind=data.get('kind');count=data.get('count');run_id=data.get('run_id');owner=data.get('owner')
        require(isinstance(kind,str) and kind in GUI_LEDGER_KINDS,'GUI_LEDGER_KIND')
        require(type(count) is int and count>=1,'GUI_LEDGER_COUNT')
        require(isinstance(owner,str) and owner==grant['owner'],'GUI_LEDGER_OWNER')
        require(run_id is None or isinstance(run_id,str),'GUI_LEDGER_RUN')
        if not self.fixture:
            require(self.authorization_path is not None,'LIVE_AUTHORITY_REQUIRED')
            from .cli import authorize
            live=authorize(self.root,self.authorization_path,False,'gui_reserve')
            require(live==grant,'GRANT_DRIFT')
        with self.guard() as (r,parent,check_lock,lock_identity):
            check_lock()
            path,ledger,cap=self._ledger_open(r,grant)
            used=sum(entry['count'] for entry in ledger['entries'])
            require(used+count<=cap,'GUI_LEDGER_EXHAUSTED')
            entry=dict(seq=len(ledger['entries'])+1,id=uuid.uuid4().hex,kind=kind,count=count,run_id=run_id,
                owner=owner,at=utc_now(),state='RESERVED',outcome=None,consumed_at=None)
            ledger['entries'].append(entry)
            self._ledger_write(r,path,ledger)
            return dict(reservation=dict(id=entry['id'],kind=kind,count=count),used=used+count,cap=cap)
```

### src/line_backup_batch/schema.py:30–34

SOURCE_SHA256=d400cb0e5cdee4a0f0ce555e3222a590093c2dcaae9f10f464e205b9d1da3302
EXCERPT_SHA256=a93d21a401543f15a71d0c5ceece1ad71db9bf58b35fb044249db0f90e6455f1

```python
    require(b['new_transactions_reserved']<=cap,'QUOTA_OVERFLOW')
    require(b['group_key'].startswith('line:jp.naver.line.mac:'),'BATCH_GROUP')
    if b['mode']=='catalog_only':
        require(b['authorized_new_download_limit']==0 and b['new_transactions_reserved']==0
            and b['current_album_run_id'] is None,'CATALOG_DISPATCH_REFUSED')
```

### src/line_backup_batch/observations.py:601–607

SOURCE_SHA256=db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587
EXCERPT_SHA256=0fb3a2ebaf4bbbb51c503e061ea0f1564b381c92c65fa459ebafc1b38fac1df0

```python
def card_target(reader,record,cfg,target,session,*,now=None):
    frame(reader,record,cfg,session=session,now=now)
    require(record['surface']=='ALBUMS','SURFACE_MISMATCH')
    cards=[c for c in record['cards'] if c['fingerprint']==target]
    require(len(cards)==1 and cards[0]['fully_visible'] is True,'CARD_NOT_FULLY_VISIBLE')
    b=cards[0]['safe_metadata_bounds'];p=[b[0]+b[2]/2,b[1]+b[3]/2]
    return point(p,b,record['mapping']['uncertainty'])
```

### src/line_backup_batch/observations.py:629–636

SOURCE_SHA256=db81671826f8d48832034de765b4aa232c51592d97254e84e3e4f249221f7587
EXCERPT_SHA256=9c5346c6104f72eb4e0b7a0fa0d9281eaae07bc703804ec21b8a437ed2d5b2cd

```python
        boundary=record['boundary']
        require(isinstance(boundary,dict) and set(boundary)=={'top','bottom','evidence'},'BOUNDARY_UNKNOWN')
        require(type(boundary['top']) is bool and type(boundary['bottom']) is bool,'BOUNDARY_UNKNOWN')
        artifact(reader,boundary['evidence'])
        if i==0:require(boundary['top'],'TOP_NOT_PROVEN')
        if i==len(records)-1:require(boundary['bottom'],'BOTTOM_NOT_PROVEN')
        prior=keys
    return identities
```

### scripts/line_backup_cua_adapter.mjs:48–76

SOURCE_SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f
EXCERPT_SHA256=8587ba9d5d8ef53d97fd523e76f19d220cbb27908ae8bf0f9d3b585942c71f8e

```javascript
export function verifyAlbumScroll(before, after) {
  requireFact(before?.surface==='ALBUMS' && after?.surface==='ALBUMS'
    && before.session_id===after.session_id && before.group_key===after.group_key
    && before.pid===after.pid && before.window_id===after.window_id
    && before.layout_key===after.layout_key, 'SCROLL_CONTEXT_DRIFT');
  requireFact(hex64(before.frame_id) && hex64(after.frame_id)
    && before.frame_id!==after.frame_id, 'SCROLL_NO_VISUAL_CHANGE');
  requireFact(Array.isArray(before.cards) && Array.isArray(after.cards),
    'SCROLL_CARD_EVIDENCE_REQUIRED');
  const complete = observation => observation.cards.filter(card=>
    card?.fully_visible===true && typeof card?.fingerprint?.start_date==='string'
    && typeof card?.fingerprint?.end_date==='string'
    && Number.isInteger(card?.fingerprint?.expected_images)
    && card.fingerprint.expected_images>0
  ).map(card => JSON.stringify([card.fingerprint.start_date,
    card.fingerprint.end_date, card.fingerprint.expected_images]));
  const previous=complete(before), current=complete(after);
  requireFact(previous.length>0 && current.length>0
    && new Set(previous).size===previous.length
    && new Set(current).size===current.length, 'SCROLL_CARD_EVIDENCE_REQUIRED');
  const previousSet=new Set(previous);
  const shared=current.filter(id=>previousSet.has(id));
  const fresh=current.filter(id=>!previousSet.has(id));
  requireFact(shared.length>0, 'SCROLL_NO_CARD_OVERLAP');
  const indices=shared.map(id=>previous.indexOf(id));
  requireFact(indices.every((value,i)=>i===0||value>indices[i-1]),
    'SCROLL_CARD_ORDER_DRIFT');
  requireFact(fresh.length>0, 'SCROLL_NO_NEW_FULL_CARD');
  return Object.freeze({overlap_count:shared.length,new_full_card_count:fresh.length});
```

### scripts/line_backup_cua_adapter.mjs:130–138

SOURCE_SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f
EXCERPT_SHA256=9fdaa09a6c77aa058d6a2e6b5ab5adda390c0de7502182feeededc632a4f52c1

```javascript
  async function reserveGui(kind,count,runId) {
    requireFact(!stopped,'SESSION_STOPPED');
    requireFact(Number.isInteger(count) && count > 0,'GUI_LEDGER_COUNT');
    const response = await bridge('gui_reserve',{data:{kind,count,run_id:runId,owner:sessionId}});
    const reservation = response?.reservation;
    requireFact(reservation && typeof reservation.id === 'string' && reservation.kind === kind
      && reservation.count === count,'GUI_LEDGER_RESERVE_REFUSED');
    latest = null;
    return Object.freeze({id:reservation.id,kind,count});
```

### scripts/line_backup_cua_adapter.mjs:294–313

SOURCE_SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f
EXCERPT_SHA256=a67fb0999c63e877b30c3b3e2447e99204a6b173f9b550500d0ac40336641e38

```javascript
  async function originalAtomicDispatch(token,{captureMenuSupport,guardMenu}={}) {
    const permit=permits.get(token);requireFact(permit,'NO_ORIGINAL_PERMISSION');
    // Consume before the first call. Throw/timeout/crash never leaves a reusable token.
    permits.delete(token);
    requireFact(typeof captureMenuSupport==='function' && typeof guardMenu==='function','MENU_GUARD_REQUIRED');
    if (requireV2) requireFact(typeof classifyChooser==='function' && chooser,'V2_CHOOSER_REQUIRED');
    fresh(permit.frameId);
    const action=permit.result;
    requireFact(point(action.ellipsis) && point(action.save_all),'INVALID_MENU_POINTS');
    requireFact(clock()-permit.issuedAt<=2000,'PERMIT_EXPIRED');
    const reservation = await reserveGui('dispatch_inputs',2,action.run_id);
    record('ELLIPSIS_INVOCATION',{actionId:action.action_id});
    latest=null;
    let support=null,guard=null;
    try {
      await app.click(action.ellipsis);
      record('ELLIPSIS_RETURNED');
      await wait(menuWaitMs);
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_MENU_CAPTURE');
      support=await captureMenuSupport(Object.freeze({action,pairFrameId:permit.frameId,sessionId,
```

### scripts/line_backup_cua_adapter.mjs:319–335

SOURCE_SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f
EXCERPT_SHA256=13b1f0a3f6a75a91483b0ab3437f391b3294e215699efe252a5e793786d45b4d

```javascript
        && hex64(support.reference.sha256),'SCK_SUPPORT_REQUIRED');
      guard=await guardMenu(Object.freeze({action,support,pairFrameId:permit.frameId,sessionId}));
      requireFact(guard?.verdict==='PASS' && guard?.provider==='SCREEN_CAPTURE_KIT'
        && guard?.pairFrameId===permit.frameId && guard?.popupFrameId===support.popupFrameId
        && guard?.supportSha256===support.reference.sha256
        && Array.isArray(guard?.actionPoint) && guard.actionPoint.length===2
        && guard.actionPoint[0]===action.save_all[0] && guard.actionPoint[1]===action.save_all[1],
        'SCK_MENU_GUARD_REFUSED');
      requireFact(clock()>=permit.issuedAt && clock()<=permit.deadline,'PERMIT_EXPIRED_BEFORE_SAVE_ALL');
      record('SCK_MENU_GUARD_PASS',{support:support.reference,guard});
      record('SAVE_ALL_INVOCATION',{actionId:action.action_id});
      await app.click(action.save_all);
      record('SAVE_ALL_RETURNED');
      await consumeGui(reservation,'RETURNED');
    } catch(error) {
      stopped=true;record('DISPATCH_UNCERTAIN',{message:String(error)});throw error;
    }
```

### scripts/line_backup_cua_adapter.mjs:613–628

SOURCE_SHA256=d9f6a850c6f3181c7a10cac697d1b617d853e677edca22d23e7bc9be0115189f
EXCERPT_SHA256=2bcada722bedd859c38659478425f675e4d3c31f39c4de57aea58475bf0b64f4

```javascript
  async function boundedScroll(before,target,direction,distance) {
    fresh(before.frame_id);requireFact(before.surface==='ALBUMS'&&['up','down'].includes(direction)
      &&point(target)&&Number.isFinite(distance)&&distance>0&&distance<=0.25,'SCROLL_POLICY');
    const reservation=await reserve('scroll',1);record('SCROLL_INVOCATION',{direction,distance});
    try {await app.scroll(target,direction,distance);await app.getAXState({emit:false});}
    catch(error) {closed=true;record('SCROLL_UNCERTAIN');throw error;}
    await consume(reservation);record('SCROLL_RETURNED');
    try {
      const after=await observe();
      const progress=verifyAlbumScroll(before,after);
      record('SCROLL_VERIFIED_NEW_CARD',progress);
      return after;
    } catch(error) {
      closed=true;latest=null;record('SCROLL_UNVERIFIED',{message:String(error)});
      throw error;
    }
```
