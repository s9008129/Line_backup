# PLAN — Save All / chooser / filesystem safety (rev27)

- Plan ID: `PLAN-2026-09-21-rev27-save-all`
- Owner round label: rev27 (Save All / chooser / filesystem safety planning)
- Route lineage: `evidence/20260916-route/` attempts 01–13 (latest: attempt-13, commit `802ee4c`)
- Status: **CANDIDATE — carries no execution authority by itself.**
- GUI authority granted by this plan in its own round: **none** (this was a zero-GUI-input round).
- Execution authority requires: **(1)** two independent reviews of this exact SHA both `PLAN_APPROVED`
  (recorded in this round), and **(2)** a separate owner authorization round accepting the Gate A block in §12.

---

## 1. Goal Contract

Primary outcome (owner): design and review the next **bounded Save-All transaction** that will produce
a real filesystem side effect — without touching the accepted baseline, without any retry, and with an
explicit pre-declared budget for every GUI input.

Success definition (owner-stated, preserved verbatim in intent): success is **not** "the album opens /
downloads"; success is: **if fresh safety conditions do not hold → stop with zero input; if they hold →
dispatch exactly once; then reliably determine what that dispatch actually caused; then stop.**

Load-bearing invariants (CORE, each with its gate):

- **I1 — Baseline read-only.** The accepted 57-file baseline directory is never written, renamed,
  deleted, or used as a download destination.
- **I2 — Save All at-most-once.** Exactly one 「儲存全部」 activation per authorized lineage; a returned
  call proves only that the call returned; any UNKNOWN dispatch forbids retry **forever**.
- **I3 — No historical input.** Every GUI input is pre-declared, budgeted, and derived from the current
  round's fresh frame. `[39,923]`, attempt-13's `[304,50]`/menu bbox, the historical ellipsis points
  `[304,50]`/`[305,50]`, and all formula-derived points are permanently barred as live inputs.
- **I4 — Append-only evidence, immutable frozen tools.** Attempts 10–13 and `tools/v4,v5,v6` are not
  modified; every new round appends a new attempt/section.
- **I5 — No cleanup without authorization.** No photo file or directory is deleted or moved by any
  round of this plan.
- **I6 — No semantic contract changes.** The state contract, engine semantics, and frozen verdict
  vocabularies are used as-is; any change is a replan, not a bounded fix.

Non-goals: general backup automation; keyboard-free chooser automation; registering a second backup
copy of this album; deleting/reorganizing staging after the test.

## 2. Established facts (read-only, this round)

- **F1 — attempt-13 closed as designed.** `ALBUM_OPEN_VERIFIED` → live frozen v5 `ELIGIBLE` → exactly
  one ⋮ click (1) → `MENU_SURFACE_AFFIRMATIVELY_OBSERVED`; menu items read top-to-bottom
  `選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿`; 「儲存全部」affirmatively identified as
  evidence only; menu-item clicks 0; Save All 0; chooser 0; download 0; retry 0; menu left open for the
  owner. Evidence: `evidence/20260916-route/attempt-13/99-scope-status.json`
  (`4188d3d4…f1353a`), `…/s6-menu-observation.json` (`d841b41c…4a3fb2`), `…/run-ledger.json`
  (`d194a21f…6cecb1d0`); full SHA list in `…/00-baseline-audit.json`.
- **F2 — Baseline verified unchanged this round.** `READ_ONLY_ACCEPTED_BASELINE` =
  `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`:
  57 regular `.jpg` files, 17,924,900 bytes, no symlinks/temp/hidden entries, directory mtime
  `2026-09-07 15:53:46`; fresh manifest digest
  `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd`; compared against the frozen
  `evidence/20260916-baseline/attempt-01/baseline-pre.json` (`ab6747f2…5b5`): 0 missing / 0 extra /
  0 size / 0 sha256 / 0 mtime_ns mismatches.
- **F3 — Historical successful route exists for this exact album.** `RUN-20260907-154331-01`
  (state rev 39): Save All dispatch → "expected macOS 打開 folder chooser" → Go to Folder with the exact
  destination → leaf folder confirmed → one confirmation → `正在下載... 0/57` → filesystem VERIFIED
  (57 `image/jpeg`, 17,924,900 bytes). Also documented: a chooser clipboard timeout recovered via AX
  `setValue` on the identified path field; and a long zero-byte placeholder phase (24 stable 0-byte
  samples) before completion.
- **F4 — Historical failure/uncertainty modes.** `RUN-20260908-124357-01`: Save-All invocation returned,
  **no chooser**, `TRIGGER_UNKNOWN`, SAFE_ABORT, destination stayed empty, manual reconciliation
  required, no retry. `RUN-20260907-101314-01`: same shape with an owner attestation that the click
  missed Save All. `RUN-20260907-132845-01`: calibration attempt entered `已選擇0個項目` selection mode;
  the later dispatch died on the first click (`noWindowsAvailable`).
- **F5 — Engine at-most-once semantics exist and stay canonical.** `transaction.py`
  (`save_all_retry_allowed=false` forever; `_dispatch_complete()` requires `save_all_click_count == 1`,
  `save_all_invocation_attempted`, `failure_boundary NONE`); duplicate gate refuses a second backup of a
  VERIFIED fingerprint to a new destination (`CONFLICT_DUPLICATE_FINGERPRINT` / `SKIP_DUPLICATE`);
  `state-contract.md` TRIGGER_CONFIRMED = expected chooser observed; UNKNOWN → barrier + manual
  reconciliation, never retry.
- **F6 — Verifier primitives exist and stay canonical.** `verifier.py` `PARTIAL_SUFFIXES`
  (`.part .partial .tmp .temp .download .crdownload .incomplete .filepart`), deterministic structural
  JPEG/PNG decode, `stable_samples=3`, `poll_interval_seconds=5`, zero-byte/other-entry/subdirectory
  checks.
- **F7 — Proven GUI input path.** The only click path proven in this route lineage is
  `sky.click(app=jp.naver.line.mac, x, y)` in **app-local pt** (attempt-13: window-local `(304,50)`).
  No proven **screen-space** click path is recorded. This constrains Gate A candidate derivation
  (§5.3) and is a hard fail-closed condition, not a tuning problem.

## 3. Transaction model: three independent gates

One album route test, three owner authorizations, strictly sequential, each terminal on its own:

| Gate | Purpose | Inputs allowed | Ends in |
|---|---|---|---|
| **A — Save All dispatch observation** | prove what activating 「儲存全部」 actually produces | exactly 1 menu-item click; ≥0 read-only captures | chooser observed / no new surface / UNKNOWN — then STOP |
| **B — chooser destination selection** | drive the already-open chooser to the frozen staging folder and confirm once | explicit keyboard + entry + 1 confirm budget (only if Gate A proved a chooser) | download started / UNKNOWN — then STOP |
| **C — filesystem completion & verification** | file-system-only verdict under the completion definition (§8) | read-only sampling | VERIFIED-equivalent duplicate-content confirmation / NOT_COMPLETE class — no GUI |

Rules that bind all gates: no retry of any consumed input; no gate inherits another gate's unused
budget; every gate revalidates its own fresh preconditions; a gate that cannot prove its preconditions
runs **zero** inputs.

## 4. Staging destination (owner §C)

- Root: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/`
- Run ID: `RUN-YYYYMMDD-HHMMSS-01`, generated fresh at Gate A execution; frozen into the path.
- Path: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<run_id>/`
- Rationale: inside the configured `backup_root` (the authority rule requires destinations to be
  inside `backup_root` realpath), distinct from the accepted baseline, unique per run, never reused.
- Creation: Gate A preflight performs **exactly one** `mkdir` of the frozen path — plus, only if
  `staging/` itself is machine-proven absent, exactly one `mkdir` of `staging/` (`staging/`'s own
  parent must already exist and be proven). Both directories are empty; both are read back and proven.
  These are the only permitted filesystem writes in Gate A/B outside evidence, and both must be listed
  in the authorization (`staging_setup_mkdir ≤ 2`, empty directories only).
- **Preflight (fail-closed; any failure → STOP with `gui_input = 0`):**
  1. lexical equality: `realpath(path) == abspath(path)`; no symlink in any component;
  2. parent `staging/` exists, is a real directory, `realpath(staging/)` is within
     `realpath(backup_root)`, and is owner-writable;
  3. target did not exist before the single `mkdir`;
  4. after `mkdir`: 0 entries, 0 regular files, 0 bytes, not a symlink, not a mount point;
  5. exclusion: staging path ≠ baseline path; baseline is not an ancestor/descendant of staging;
  6. name matches the frozen `RUN-…` pattern; the run_id does not appear in any prior attempt ledger.
- After the test: **PRESERVE** (quarantine). No automated cleanup; deletion only under a separate
  explicit owner authorization (§9).

## 5. Gate A — Save All dispatch observation (owner §F)

### 5.1 Fresh preconditions (all required, all in the same Gate A round)

1. LINE frontmost: AX read shows `jp.naver.line.mac`, the exact target window, position/size read
   cleanly, and no occluding window over the menu/ellipsis region.
2. Fresh album-open verification: frozen `v5/verify_album_open.py`
   (`ffa82aed…3cf58`) on a fresh live frame → formal `ALBUM_OPEN_VERIFIED` (both the window pair and the
   screen supporting pair), title `2024/05/13～05/17`, count `57`.
3. Fresh menu surface:
   - **If attempt-13's menu is still open:** capture a fresh full-screen frame; run the frozen
     `tools/detect_menu_popup.py` (`6ae9c250…f740bc`) with `pre = evidence/20260916-route/attempt-13/frame-menu-pre.png`
     (`0118b12f…0fb6`, menu-absent reference) and `post = fresh frame`, **only after** a frame↔window
     binding check proves the pre-frame's window region still binds to the fresh frame (same procedure
     as attempts 10–13; MAD ≤ 12) → require `MENU_DETECTED` on the fresh frame with a fresh bbox.
   - **If the menu is not present (binding fails, `NOT_DETECTED`, or the owner reports it closed):**
     STOP immediately and report
     `MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`. **Never reopen the ellipsis.**
4. Fresh menu-item identification for 「儲存全部」 by the **new frozen locator (§5.3)** → `ELIGIBLE`
   with a single fresh candidate. Any other verdict → STOP.
5. Staging preflight (§4) PASS, including the single `mkdir` and its read-back proof.
6. Baseline tripwire: fresh baseline manifest digest `== b7debe92…` (read-only recomputation).
7. Intent record written and read back before dispatch (§7.1).
8. Final freshness gate, ≤ 15 s before dispatch, with the dispatch call as the **very next action**
   (no intervening operations): re-capture a frame; require LINE still frontmost, `ALBUM_OPEN_VERIFIED`
   still binding, menu still detected, identified row unchanged. Otherwise STOP
   (`ABORTED_BEFORE_DISPATCH`, zero input). This tight bound minimizes (it cannot fully eliminate) the
   residual risk that the menu auto-closes between the last check and the click; see §5.4 for the
   miss-classification rule.

### 5.2 The single input

- Exactly **one** left click at the fresh candidate, app-local pt space, via the proven
  `sky.click` path (app `jp.naver.line.mac`), `click_count = 1`. No double click, no second click,
  no keyboard, no scroll, no AX write.
- Dispatch boundary recorded per §7.2, with timestamps, candidate, frame SHA, tool SHA, run_id.
- Budget: `save_all_menu_item_click = 1`, `retry = 0` forever, `ellipsis = 0`, `album_card = 0`,
  `chooser = 0`, `keyboard = 0` (Escape included), `scroll = 0`, `AX_write = 0`,
  `app_acquisition = 0`, `bring_to_front = 0`, `download = 0`, `cleanup = 0`, `formal_state_write = 0`.

### 5.3 Candidate derivation — requirements for the new frozen locator (v7 class)

The locator must be **created, self-tested, frozen (SHA-256), and independently reviewed (a separate
review pass recorded in that round's evidence) within the Gate A round before any click**; it is
read-only and fail-closed. Required properties:

1. Inputs: the fresh frame (SHA), the fresh menu bbox from the frozen detector, and the fresh window
   geometry bound to that frame (SHA). The report must carry all three.
2. Text-first identification: tesseract word boxes within the menu bbox (`chi_tra+eng`, same
   preprocessing family as the frozen tools); match `儲存全部` (allow the observed multi-glyph splits);
   exactly one matching row → else `NOT_FOUND` / `AMBIGUOUS` → STOP.
3. Cross-check, not computation: the observed item rows must agree with the recorded reference order
   (`選擇項目 / 修改相簿名稱 / 儲存全部 / 刪除相簿 / 分享相簿`) and the identified row must be uniquely
   placed; a contradicting row set → `MENU_CONTENT_UNEXPECTED` → STOP. The reference order may only be
   *checked against* the observation; it may never be used to compute a row position.
4. Candidate: `x = midpoint of (identified text box x-range ∩ addressable input region x-range)`;
   `y = vertical center of the identified text box`; require the intersection width ≥ 20 px
   (≈10 pt), the candidate inside the menu bbox, inside the addressable region, and within the
   identified row's vertical extent. Otherwise `NOT_ADDRESSABLE` → STOP.
5. Output spaces: frame px (screen), screen pt (= px/2), app-local pt (= screen pt − window origin pt).
   The app-local form is the dispatch form; if it cannot be computed from the round's own bound
   geometry → `NOT_ADDRESSABLE` → STOP.
6. Hard prohibitions: no literal coordinates, no row-index arithmetic, no formula rows, no reuse of any
   attempt-13 number may appear in the tool or its inputs. (Feasibility note only — the geometry of
   attempt-13's frame is discussed in `01-save-all-flow-evidence.md`; it confers no authority.)

### 5.4 Post-dispatch observation (read-only, immediate)

- Capture post frames (≈0.4 s and ≈2.2 s) + AX state; run the frozen detector on the fresh pair.
- Classify the resulting surface, fail-closed:
  - `SAVE_ALL_TRIGGER_CONFIRMED` — an unmistakable macOS folder chooser is affirmatively observed
    (fresh evidence; the historical expected form is the 打開 panel);
  - `SAVE_ALL_TRIGGER_NOT_OBSERVED` — the round's own observation proves no new surface (e.g., the
    album view is unchanged and no chooser exists);
  - `SAVE_ALL_TRIGGER_UNKNOWN` — anything else, including an unclassifiable dialog or ambiguous frame.
- Miss-classification rule (menu auto-closed between the final gate and the click, so the click landed
  on whatever is behind the menu — expected worst cases: a photo-grid cell opening the photo viewer, an
  album-list card, or no change): record `SAVE_ALL_TRIGGER_NOT_OBSERVED` plus an explicit
  `UNINTENDED_CLICK_OUTCOME` note, capture the resulting surface as evidence, stop, and report. Such a
  miss is expected to have **no data-side effect** (LINE viewers are read-only), but it must be reported
  precisely; the round must not attempt to repair or re-run anything.
- Re-run the baseline tripwire digest (read-only) to prove the click wrote nothing into the baseline.
- **STOP.** No chooser interaction, no Escape (keyboard), no click anywhere, no second ellipsis click,
  no menu navigation. Whatever surface resulted (chooser open / menu still open / unchanged album
  view) is left exactly as-is for the owner.
- Owner hand-off note (residual risk, accepted for Gate A): a chooser left open could in principle be
  confirmed by an accidental keystroke outside this route, which would start a download to an unknown
  default folder. Mitigations: (a) the round's report must tell the owner to keep hands off the
  keyboard/pointer until the next authorized round; (b) the post-dispatch baseline tripwire (§5.4) is
  mandatory and reported; (c) Gate B, if authorized, always navigates explicitly to the frozen staging
  path and never accepts a default. No input is used to "clean up" the open surface.

### 5.5 Gate A authorization request (exact block for the owner, §12)

## 6. Gate B — chooser destination selection (design only; separate authorization)

Activation precondition: Gate A ended `SAVE_ALL_TRIGGER_CONFIRMED`, the chooser is still identified
fresh, and staging is still proven empty. If any of those fail → STOP, no input.

Budget (must be granted explicitly; each item is a separate line):

| Item | Budget | Notes |
|---|---|---|
| fresh chooser identification (read-only) | — | unmistakable macOS folder chooser required |
| Go to Folder chord (`super+shift+g`) | 1 | keyboard input — only if listed in the authorization |
| path entry | 1 | typed text, clipboard paste, or AX `setValue`; the chosen method must be enumerated |
| clipboard write (only if paste is the chosen method) | ≤1 | system-side, not a filesystem write |
| AX write (only if `setValue` is the chosen method) | ≤1 | historically used fallback; must be enumerated or it stays forbidden |
| path commit (Return) | 1 | |
| destination confirmation | 1 | only after the leaf folder is positively observed |
| retry / second confirm / folder creation inside chooser | 0 | never |

AX `setValue` (and clipboard paste) are Gate B-only options; neither is ever part of Gate A.
Required evidence chain before the single confirmation: chooser identity → path-entry UI observed →
absolute staging path entered → breadcrumb/path observed → the exact leaf `RUN-…` folder observed →
then confirm once. Any uncertainty or unexpected surface (overwrite/conflict prompt, wrong folder,
different chooser type) → STOP + observe-only reconciliation. After confirmation → STOP; Gate C
begins without further GUI input.

## 7. Transaction semantics (owner §G)

### 7.1 Before dispatch

Route-ledger intent record (append-only, under the attempt dir) containing at least: `run_id`, `gate`,
group, fingerprint `{2024-05-13, 2024-05-17, 57}`, staging path, fresh frame SHA, detector SHA,
locator SHA, candidate in all three spaces, budgets, `dispatch_state = NOT_ATTEMPTED`,
`save_all_retry_allowed = false`, timestamp. Written atomically and read back **before** the click.

### 7.2 Dispatch boundary

`SAVE_ALL_DISPATCH_ATTEMPTED` is recorded immediately **before** the click call (atomic write +
read-back). The call's invocation is the boundary: a returned call proves only that the call returned.
If the call throws or its result is ambiguous → `dispatch_state = UNKNOWN` and the click is **never
re-invoked**. `save_all_click_count = 1`; dispatch timestamps recorded.

### 7.3 After dispatch

State vocabulary (contract-compatible):
`dispatch_state ∈ {NOT_ATTEMPTED, SAVE_ALL_ATTEMPTED, SAVE_ALL_RETURNED, UNKNOWN}`,
surface observation `∈ {TRIGGER_CONFIRMED, TRIGGER_NOT_OBSERVED, UNKNOWN}`.
- `ABORTED_BEFORE_DISPATCH` may be recorded only with proof the click was never invoked.
- Manual reconciliation is required unless the run reaches a verified completion; an UNKNOWN dispatch
  keeps a permanent barrier and forbids any later Save All by the same lineage.

### 7.4 Live-state integration — explicit decision

Gate A/B/C **do not write** the live `backup_state.json`. Rationale:
1. This fingerprint is already `VERIFIED` with the accepted baseline; the engine's duplicate gate
   would (correctly) refuse a second destination (`CONFLICT_DUPLICATE_FINGERPRINT`), and a route test
   must not masquerade as a backup or release a fingerprint barrier.
2. `prepare` models the historical atomic "ellipsis + Save All" chain with a dispatcher adapter; the
   authorized route is a different chain (menu pre-opened; fresh identification; one activation).
   Forcing it would require new semantics — a replan, not a bounded fix.
3. A live intent would create a blocking record whose later release is not justified by a
   duplicate-content test.

Compensating controls: the route ledger is the durable, append-only record (committed); it must state
the at-most-once and no-retry semantics explicitly; and a future formal backup of this fingerprint is
already impossible (VERIFIED duplicate), so no untracked-dispatch exposure remains for this album.
Recording an additional reconciliation note in live state is deferred as owner decision **OD-1**
(default: no; requires separate explicit authorization). If the owner instead prefers the engine's
`prepare`-style live intent as the substrate for Gate A, that is a replan (new plan revision + new
reviews + a dispatcher adapter and calibration design) — not a bounded execution change.

### 7.5 Engine command usage

Only read-only/evaluation forms that do not mutate `backup_state.json` may ever be used (e.g., a
verify-only inspection writing evidence into the attempt directory). No `prepare / commit / finalize /
resume` state mutations, and no `duplicate_check` state-adjacent runs, without a separate explicit
authorization. The `.line-backup-state.lock` sidecar counts as a state-dir write and must be listed if
any engine command is used.

## 8. Completion definition (owner §H)

Gate C is filesystem-only. Its verdict, bound to `run_id` + staging path:

- **Sampling:** ≥3 complete inventories at ≥5 s intervals (engine `stable_samples=3`,
  `poll_interval_seconds=5`). Gate C observes for a bounded window — default **600 s** wall clock
  (the engine's `max_wait_seconds`); on expiry the verdict is `INCOMPLETE_QUIESCENT` (no criteria
  relaxation, no GUI action, no retry).
- **C1** exactly 57 regular files; 0 subdirectories; 0 symlinks; 0 other entries.
- **C2** no filename ends with any `PARTIAL_SUFFIXES` member; no hidden temp patterns.
- **C3** zero-byte count = 0.
- **C4** every file structurally decodable as JPEG or PNG (deterministic structural decode).
- **C5** total bytes stable across the final samples, > 0.
- **C6** manifest generated: sorted `relative_path \t size \t sha256` lines + trailing `\n`;
  manifest file and digest recorded.
- **C7** duplicate confirmation: the **multiset of per-file SHA-256** equals the accepted baseline's
  multiset → `DUPLICATE_CONTENT_CONFIRMED`; filename differences (LINE rename behavior) are reported
  explicitly and do not affect the verdict, which is content-based.
- **C8** quiescence: no size/mtime changes across the final two samples.
- **57-count alone is explicitly insufficient** — the historical zero-byte phase (F3) proves a stable
  57-file, 0-byte state is a possible intermediate.
- Failure classes: `INCOMPLETE_QUIESCENT` (stalled), `INCOMPLETE_GROWING` (still writing),
  `ANOMALY` (extra entries / partials / zero-byte / undecodable / unexpected names) → all STOP or
  RECONCILE; never a GUI retry; never deletion.
- Terminal handling: the run is **not** registered as a second VERIFIED destination, and nothing is
  copied into the formal backup.

## 9. Duplicate protection (owner §I)

- Layer 1 — before Save All: the album fingerprint is already `VERIFIED` with the accepted baseline;
  this is recorded as the duplicate baseline for the test, and the test proceeds only as a
  duplicate-content route test into fresh staging.
- Layer 2 — after Gate C: compare staging's content-hash multiset against the baseline digest
  `b7debe92…`. Identical → `DUPLICATE_CONTENT_CONFIRMED` (end-to-end route test success; **not** a new
  backup). Different → `DIFFERENT_CONTENT`; stop, report, and require an owner decision before any
  further action; never write into the baseline.
- Staging disposition: `PRESERVE` (quarantine as evidence). No deletion, move, or automated cleanup
  without a separate explicit owner authorization (**OD-3**, default: preserve).

## 10. Failure matrix (owner §J) — every row is fail-closed

| # | Condition | Class | Rule |
|---|---|---|---|
| 1 | menu disappeared before Gate A | STOP | `MENU_NOT_PRESENT_REQUIRES_NEW_ELLIPSIS_AUTHORIZATION`; never reopen ellipsis |
| 2 | 「儲存全部」 text no longer readable | STOP | locator `NOT_FOUND`; zero input |
| 3 | wrong menu item geometry / identification ambiguous | STOP | locator `AMBIGUOUS`/`MENU_CONTENT_UNEXPECTED`; zero input |
| 4 | menu moved / bbox changed vs fresh frame | STOP | re-run fresh detection; if not freshly detected → STOP |
| 5 | Save All click call returns unknown / throws | RECONCILE | `dispatch_state=UNKNOWN`; no retry ever; manual reconciliation |
| 6 | chooser does not appear | RECONCILE | `TRIGGER_UNKNOWN` or `TRIGGER_NOT_OBSERVED`; stop, report, no retry |
| 7 | unexpected chooser type / unknown dialog | STOP | identity unknown ≠ identity proved; observe only |
| 8 | chooser destination defaults near baseline | STOP | never accept default; Gate B navigates explicitly or stops |
| 9 | staging not fresh (non-empty / symlink / wrong owner) | STOP | preflight fails; `gui_input = 0` |
| 10 | keyboard/navigation method unavailable | FUTURE_REVISION | Gate B cannot proceed; chooser left open; new authorization needed |
| 11 | chooser confirm uncertain | RECONCILE | observe only until positively identified; never repeat confirmation |
| 12 | download starts but stalls | RECONCILE | Gate C classifies `INCOMPLETE_QUIESCENT`; no GUI action |
| 13 | fewer than 57 files | RECONCILE | `NOT_COMPLETE`; report; owner decision; no retry |
| 14 | more than 57 files (extra/renamed/duplicate names) | RECONCILE | `ANOMALY`; report; content-hash multiset decides duplicates |
| 15 | corrupt image / undecodable file | RECONCILE | `ANOMALY`; preserve file as evidence; no deletion |
| 16 | duplicate filename / LINE rename behavior | RECONCILE | content-based comparison (C7); filename deltas reported |
| 17 | permission failure on staging | STOP | no GUI escalation; report |
| 18 | LINE closes / restarts mid-flow | RECONCILE | surface gone ⇒ stop; never re-dispatch; fresh authorization required |
| 19 | chooser closes unexpectedly | RECONCILE | observe only; no re-click of anything |
| 20 | process crash / machine restart boundary | RECONCILE | ledger + state vocabulary determine dispatch certainty; UNKNOWN stays UNKNOWN |

No row ever permits: an automatic retry, a second Save All, a second ellipsis click, or a baseline
write.

## 11. Budgets

| Budget | This round (executed) | Gate A (requested) | Gate B (future) | Gate C |
|---|---|---|---|---|
| GUI input | 0 | 1 (Save All only) | enumerated per §6 | 0 |
| ellipsis click | 0 | 0 | 0 | 0 |
| album-card click | 0 | 0 | 0 | 0 |
| menu-item click | 0 | 1 | 0 | 0 |
| chooser interaction | 0 | 0 | 1 confirm (+ entry budget) | 0 |
| keyboard | 0 | 0 (Escape included) | enumerated per §6 | 0 |
| download | 0 | 0 | starts as a side effect | 0 |
| destination write | 0 | 1 empty staging `mkdir` | writes via download | 0 |
| cleanup/delete | 0 | 0 | 0 | 0 |
| formal state write | 0 | 0 (§7.4) | 0 | 0 |

## 12. Gate A authorization block (for the owner to grant verbatim)

> I authorize the Gate A round as specified in `PLAN-2026-09-21-rev27-save-all.md` at SHA-256
> `<plan-sha>`: fresh read-only revalidation (LINE frontmost, `ALBUM_OPEN_VERIFIED`, fresh menu
> detection, fresh frozen locator `ELIGIBLE`, staging preflight, baseline tripwire, intent record),
> then exactly one left click on the fresh 「儲存全部」 candidate if and only if every precondition
> holds, then immediate read-only observation and unconditional stop. Budget: `save_all_menu_item_click = 1`,
> `staging_setup_mkdir = 1` (empty directory only), everything else 0 — no chooser interaction, no
> keyboard, no Escape, no download, no cleanup, no formal state writes. No retry ever. If the menu is
> not present, the round stops and asks for a new ellipsis authorization.
>
> (Instantiate `<plan-sha>` with this document's recorded SHA-256 and a frozen execution-round date;
> any later edit to this plan invalidates the authorization and requires new reviews.)

## 13. Evidence, ledger, git (future rounds)

Each future gate appends `evidence/<YYYYMMDD>-rev27-save-all/attempt-NN/` with: fresh frames + SHAs,
tool SHAs, verdict JSONs, dispatch ledger, surface classification, and a closing scope-status file
following the attempt-13 pattern. No frozen tool or historical attempt is modified. Commits stay
local; no push.

## 14. Review record (this round)

Both reviews bind this document's exact SHA-256 and are stored in
`evidence/20260921-rev27-save-all/attempt-01/`:
- `review-01-top-down.md` — transaction / data-integrity review
- `review-02-adversarial-gui-filesystem.md` — adversarial GUI / filesystem side-effect review

Gate A authorization may be requested only if both are `PLAN_APPROVED` for this exact SHA.
