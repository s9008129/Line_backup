# LINE Album Backup — Rev25 Final Automation Test Plan

Date: 2026-09-19  
Repository: `s9008129/Line_backup`  
Plan revision: **25 (final execution plan)**  
Status: **READY_FOR_CODEX_PREFLIGHT; GUI NOT YET AUTHORIZED**  
Supersedes for execution: `GOAL-2026-09-19-rev25-next.md` (historical preliminary goal remains immutable)

## 1. Mission

The purpose of Rev25 is **not** to download the album again. The purpose is to close the current route uncertainty safely:

1. prove the newly repaired acceptance/state machine still fails closed;
2. diagnose why route attempt-07 sent one album-card click but S5 returned `NO_EFFECT`;
3. if the diagnosis supports a safe route correction, build a new append-only locator revision rather than rewriting frozen tools;
4. only after a new owner one-shot authorization, perform one bounded live observation:
   - open the exact target album once;
   - prove that the album really opened;
   - locate the album-level ellipsis on the live frame;
   - click the ellipsis once;
   - observe the menu only;
   - **never activate Save All in Rev25**;
5. run an independent zero-input acceptance replay after the live observation.

Target identity is exact and must never be normalized:

- app: `jp.naver.line.mac`
- group: `旻謙允禎成長日記` — **禎 U+798E**
- album: `2024/05/13～05/17`
- expected images: `57`
- baseline destination: 57 files / 17,924,900 bytes
- frozen baseline SHA-256 prefix: `ab6747f2…`
- `禎 U+798E` and legacy `楨 U+6968` are never merged.

## 2. Mandatory code baseline

The following repair commit must be an ancestor of the execution HEAD:

`8fb622e4f2a25a2b1297894855303fdc671dafd3`

Repairs already committed to `master` before this plan:

- `4e05a31b1df768a52416d8cd47f75ec48b4e7c00` — shared completed-dispatch gate; `finalize --outcome VERIFIED` can no longer bypass unresolved dispatch; reconciliation evidence uses atomic write.
- `007a6c307c3c6ccfa6530b30cf922fefa0822863` — Status Contract generic branch fixes: legal `ESCALATED` enum and `required_verification_status=FAIL -> FIX_REQUIRED`.
- `941e4b83d3070c09b9564eca5ee8d46e0c1ad956` — test-mode lexical + symlink-resolved containment.
- `1aa9ee1aa6aae9015efc0e4fa4beedf0df473926` — production binding workspace defaults to the checked-out repository root; optional `LINE_BACKUP_WORK_ROOT` override.
- `5a23e67990f8734cc47c835c32d2c562cf94f664` — acceptance regressions for direct VERIFIED-finalize refusal from unresolved states.
- `1fd9612b01a79bcbdfc01438461da7323388207c` — core regressions for status routing and symlink escape.
- `8fb622e4f2a25a2b1297894855303fdc671dafd3` — README contract/documentation alignment.

Important: the GitHub connector that authored the repair could read back the source but could not execute the repository test suite. Therefore **Phase 0 dynamic execution is a hard prerequisite**. No GUI input is allowed until Phase 0 is fully green.

## 3. Frozen historical anchors

Historical evidence is append-only. Never edit, replace, regenerate in place, or “correct” any of these:

- `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md` Rev24, SHA-256 `40eb01980c7e11f96b4b12c2db8f53728852f1ab6ca452dfb5e865fd5435a003`
- `evidence/20260916-route/attempt-07/run-ledger.json` FINAL, historical SHA prefix `7c8ea39a…`
- `evidence/20260916-route/attempt-07/gate-5-authorization.json`, SHA-256 `2817b122e17f782f71392d951546aff5f7cee41d9f01f73b7c0a8091f33114a5`
- `evidence/20260916-route/attempt-07/album-card-locate.json`
- `evidence/20260916-route/attempt-07/screen-probe.json`
- `evidence/20260916-route/attempt-07/album-open-verify.json`
- `evidence/20260916-route/attempt-07/v5-offline-replay.json`
- `evidence/20260916-route/attempt-07/v4-baseline-replay.json`
- v1–v5 route tools and their frozen self-tests
- route attempts 01–07
- e2e attempts 02–08
- gates 1–5
- prior result/handoff/history artifacts.

Known Rev24 live result remains immutable:

- S3 target card: `ELIGIBLE`
- one album-card/navigation input sent
- S5: `NO_EFFECT`
- `changed_fraction = 0.047343 < 0.05`
- ellipsis input remained `UNSPENT 0/1`
- S6–S10 never ran
- v5 has offline proof only; **no live v5 proof exists**
- no Save All, chooser, download, or formal state write occurred.

## 4. Global non-negotiable rules

1. Fail closed. “Probably” is not a pass.
2. Frozen evidence stays byte-identical.
3. No historical coordinate may become a live click coordinate.
4. Every live coordinate must be derived from the immediate current frame and current window geometry.
5. No retry after any GUI input.
6. No double click unless a future plan revision explicitly proves and authorizes it; Rev25 does not authorize one.
7. No v5→v4 fallback for ellipsis.
8. No menu-item activation in Rev25, explicitly including Save All.
9. No chooser interaction, keyboard input, AX write action, scrolling, or app-acquisition input.
10. No write to the existing 57-file destination.
11. Formal config/state/run-log remain read-only during route observation.
12. Python runs with `-B` / `PYTHONDONTWRITEBYTECODE=1`.
13. Evidence roots are append-only. If an attempt root exists and is non-empty, allocate the next attempt number; never reuse it.
14. Do not post screenshots into the conversation. Report paths, hashes, sizes, dimensions, and verdicts.
15. A new GUI attempt requires a new owner one-shot authorization artifact. This plan and its GOAL are **not themselves GUI authorization**.

## 5. Phase -1 — local-clone bootstrap (zero GUI; narrowly authorized)

This phase exists only to resolve a stale local clone. It is the **only** pre-Phase-0 write permission and may update only Git remote-tracking refs plus a clean local branch by fast-forward.

Canonical Rev25 plan path after synchronization:

`PLAN-2026-09-19-rev25-final.md`

Do **not** require a copy under `~/Downloads`, and do not treat `PLAN-20260919-rev25-final.md` as the canonical file.

### 5.1 Preconditions

Run:

```bash
git status --porcelain=v1 --branch
git remote get-url origin
git rev-parse HEAD
```

Hard requirements:

- working tree/index are clean;
- current branch is `master`;
- `origin` points to the intended `s9008129/Line_backup` repository.

If any requirement fails, stop. Do not stash, reset, rebase, cherry-pick, force-update, or discard user work.

### 5.2 Read remote state

The following is explicitly authorized:

```bash
git fetch --prune origin master
```

This fetch is not a GUI action and does not authorize any LINE interaction.

After fetch, verify:

```bash
git cat-file -e 8fb622e4f2a25a2b1297894855303fdc671dafd3^{commit}
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 origin/master
git merge-base --is-ancestor HEAD origin/master
```

All three commands must exit 0.

### 5.3 Fast-forward only

If and only if the worktree is still clean and local `HEAD` is an ancestor of `origin/master`, the following branch update is explicitly authorized:

```bash
git merge --ff-only origin/master
```

Equivalent `git pull --ff-only origin master` is acceptable, but do not perform both.

Forbidden recovery paths:

- `git reset` of any kind;
- `git rebase`;
- `git cherry-pick`;
- force push/update;
- deleting or overwriting local files to make the merge work.

If fast-forward cannot be completed exactly, stop and report the divergence.

### 5.4 Bootstrap acceptance

After fast-forward:

```bash
git status --porcelain=v1 --branch
git rev-parse HEAD
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 HEAD
test -f PLAN-2026-09-19-rev25-final.md
test -f GOAL-2026-09-19-rev25-final.md
```

Required:

- clean worktree;
- baseline ancestor check exit 0;
- both canonical Rev25 files exist in the repository root.

Only then proceed to Phase 0.

## 6. Phase 0 — repaired-core dynamic preflight (zero GUI)

### 6.1 Repository gate

Run from the repository root:

```bash
git status --short
git rev-parse HEAD
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 HEAD
```

Acceptance:

- worktree is clean before the run;
- ancestor check exits 0;
- if there are local changes, do not discard them automatically; stop and record them.

### 6.2 Focused regression suite

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/test_transaction_core.py
```

Must exit 0. The following new regressions must be present and pass:

- symlink fixture escape rejected;
- generic missing CORE rationale emits legal `ESCALATED / REPLAN_REQUIRED`;
- generic required-verification FAIL emits `FIX_REQUIRED`.

### 6.3 Full acceptance wave

Use a **new append-only root**, for example:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/run_acceptance_wave.py \
  --attempt-root evidence/20260919-rev25-preflight/attempt-01
```

If that root is non-empty, increment the attempt number. Never delete an old attempt.

Hard pass conditions:

- process exit 0
- `all_safe == true`
- all cases 01–25 safe
- no failed checks
- verifier matrix matches
- status matrix matches
- authority negatives match
- preserved legacy false-positive reproduction matches
- read-back verdict `PASS`
- manifest/read-back report contains no uncovered mutation that violates the harness contract.

Mandatory spot-checks in the generated Case 03 and Case 23 evidence:

- a genuine verify-only chain can have filesystem PASS while dispatch is unresolved;
- direct `finalize --outcome VERIFIED` returns `CONFLICT_UNRESOLVED_DISPATCH`, exit 4;
- state SHA is unchanged;
- `verified_albums` remains unchanged;
- writer ownership remains retained;
- no extra dispatch occurs.

### 6.4 Full automation-verification wave

Use another fresh append-only root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/automation_verification/run_all.py \
  --attempt-root evidence/20260919-rev25-auto-verification/attempt-01
```

Hard pass conditions:

- exit 0
- `all_orders_safe == true`
- both `driver-first` and `ownership-first` orders safe
- each final read-back verdict `PASS`.

### 6.5 Phase 0 stop rule

Any failure in 6.1–6.4 means:

- **no LINE GUI input**
- classify as `TASK_REGRESSION` or evidence/environment failure as supported by the data
- repair with a new commit
- repeat Phase 0 from a new append-only evidence root.

Do not continue by waiving a failed regression.

## 7. Phase 1 — baseline and historical integrity replay (zero GUI)

Recompute, do not trust prose:

- current destination file count = 57
- total bytes = 17,924,900
- frozen baseline digest matches the previously accepted baseline
- source identity v1.1 remains `CONFIRMED`
- legacy v1 remains non-authoritative
- exact `禎 U+798E` / `楨 U+6968` separation remains enforced
- attempt-07 FINAL ledger and gate-5 hashes still match their frozen history
- v5 selftest remains 21 total / 0 failed
- v5 offline replay remains `ELIGIBLE` on the frozen frame
- v4 same-frame baseline remains `NO_ELLIPSIS_FOUND`
- Stage05 e2e/attempt-08 report remains internally consistent.

If any historical artifact changed unexpectedly, stop. Do not “repair” history.

## 8. Phase 2 — S5 NO_EFFECT diagnosis (zero GUI)

Create a new append-only diagnostic directory under:

`evidence/20260919-rev25-s5-diagnostic/attempt-N/`

Required analysis:

### 7.1 Coordinate-space reconstruction

Reconstruct, with equations and evidence references:

- full-screen pixels
- Retina scale
- Cocoa/System Events points
- LINE window origin and size
- card title bbox
- old click derivation `title left edge + 12 px, vertical centre`
- old emitted System Events point `{21,448}`.

The analysis must answer whether the old point was:

- inside the visible target row;
- inside text only;
- plausibly outside the card's clickable hit area;
- affected materially by half-point rounding.

Do not infer hitbox semantics from appearance alone. Mark unsupported conclusions `UNKNOWN`.

### 7.2 Focus / z-order reconstruction

Use only prior logs/evidence and current read-only application/window queries. Determine whether evidence supports:

- LINE frontmost;
- the intended LINE window receiving the event;
- another window/overlay intercepting it.

No clicks are allowed.

### 7.3 Event-semantics review

Review the actual runtime path:

- Rev24 skeleton assumed CUA;
- live attempt used `screencapture -x` + `osascript System Events click at`.

Determine from code/docs/local help, read-only only:

- whether `click at` means one left click at global point;
- whether coordinates are points rather than pixels;
- whether bringing the app frontmost is implicit or not;
- whether any implementation difference from the planned CUA route is material.

### 7.4 S5 threshold sensitivity

Replay the existing pre/post frames offline and report changed fraction under nearby analytical thresholds, but:

- never alter the frozen Rev24 verdict;
- never choose a new threshold merely to convert 0.047343 into PASS;
- semantic album-open evidence remains mandatory.

### 7.5 Hypothesis matrix

Write `s5-hypothesis-matrix.md` with rows such as:

- click point landed in a non-clickable text subregion
- px↔pt transform wrong
- 0.5pt rounding mattered
- LINE focus/z-order issue
- System Events click semantics mismatch
- single click insufficient
- post-capture timing/animation window too short
- S5 visual threshold too strict.

Every row must be one of `SUPPORTED`, `REJECTED`, `UNKNOWN`, with explicit evidence. Do not manufacture a winner.

## 9. Phase 3 — route-tool decision and Rev25 review gate (zero GUI)

### 9.1 Tool immutability

Never modify frozen v4/v5 files.

If Phase 2 produces evidence that the card click-point strategy itself needs correction:

- create **v6** under a new path;
- modify only the minimum required card-locator/click-point derivation;
- add deterministic self-tests;
- replay against frozen historical frames;
- require v6 to preserve identity/count recognition and produce a defensible interior card point;
- keep v5 ellipsis locator unchanged unless a separate evidence-backed defect is found.

If Phase 2 does not justify a tool change, do not create v6 just to make progress.

### 9.2 Fresh review

Before any GUI gate:

- freeze this Rev25 plan content and compute its SHA-256;
- run two fresh independent reviews against the exact same plan SHA;
- both must return `PLAN_APPROVED`;
- reviews must explicitly verify Phase 0 passed and that the proposed S3 click derivation is current-frame based;
- any review rejection requires a new plan content hash and both reviews repeated.

### 9.3 Draft gate-6

Create but do not spend a new gate-6 artifact mirroring gate-5's 17-key top-level schema:

1. `artifact_type`
2. `gate`
3. `session_id`
4. `session_transcript`
5. `prior_gate`
6. `authority_artifact`
7. `plan_binding`
8. `context_authorization`
9. `option_presentation_transcript`
10. `decided_interpretation`
11. `alternative_reading`
12. `scope`
13. `budgets`
14. `not_authorized`
15. `recorded_in`
16. `recorded_at_local`
17. `notes`.

Gate-6 must bind:

- the exact Rev25 plan SHA;
- both fresh review report SHAs;
- the exact parent route attempt-07 FINAL ledger SHA recomputed from disk;
- every live route tool SHA;
- the selected click-point derivation;
- the one-shot budgets below.

### 9.4 Owner authorization hard stop

At this point stop and ask the owner for a **new explicit one-shot authorization**.

Minimum authorized envelope, if the owner chooses to proceed:

- album-card/navigation input: 1
- ellipsis input: 1
- click count per input: 1
- retry: 0
- menu item: 0
- keyboard: 0
- chooser: 0
- app acquisition: 0
- scrolling: 0
- AX write: 0
- Save All: 0.

The current request to author this plan does not consume or grant gate-6.

## 10. Phase 4 — live route attempt-08 (only after owner explicitly authorizes gate-6)

Create a new route directory; do not reuse attempt-07:

`evidence/20260916-route/attempt-08/`

### S1 — Fresh pre-frame

- capture fresh full-screen/window evidence;
- record bytes, dimensions, SHA-256, time, window geometry;
- zero input.

### S2 — Read-only window/screen observations

- inspect current LINE windows/focus/geometry;
- supporting only;
- do not block solely because the old v3 supporting probe is unavailable.

### S3 — Target card locator

- use the approved Rev25 card locator strategy;
- target must be exact album `2024/05/13～05/17`, count 57;
- verdict must be `ELIGIBLE`;
- live point must come from this immediate frame;
- if anything is ambiguous, stop with zero input.

### S4 — Input #1

Exactly one album-card/navigation left click.

No retry, no second click, no double click.

### S5 — Prove album open

Capture an immediate fresh post-frame and run the frozen semantic album-open verifier.

Required verdict: `ALBUM_OPEN_VERIFIED`.

If verdict is anything else, including `NO_EFFECT`, stop immediately:

- no ellipsis click;
- mark ellipsis budget `UNSPENT 0/1`;
- close attempt as fail-closed;
- never adjust threshold or click again.

### S6 — Live v5 ellipsis

Only after S5 passes:

- run the frozen v5 ellipsis locator on the immediate current album frame;
- require `ELIGIBLE`;
- bind the v5 reader block and current frame hash;
- derive the live ellipsis point from this frame;
- **no v4 fallback**.

If S6 is non-affirmative, stop with no second input.

### S7 — Input #2

Exactly one album-level ellipsis left click at the S6 live-derived point.

### S8 — Menu observation only

Capture the menu and run the frozen menu detector/readers.

Record:

- whether a menu surface is affirmatively found;
- menu items that can be machine-read;
- whether `Save All` / localized equivalent can be affirmatively identified.

Do **not** click any menu item. Do not close the menu if closing requires an unauthorized input.

### S9 — Final route ledger

Write a FINAL append-only ledger containing:

- all hashes
- tool bindings
- budgets spent/unspent
- exact inputs
- stop reason or success reason
- runtime/provider truth
- explicit statement: `SAVE_ALL_DISPATCH_ATTEMPTED=NO`.

## 11. Phase 5 — independent acceptance e2e/attempt-09 (zero GUI)

After route attempt-08 closes, create:

`e2e/attempt-09/`

This stage must independently re-read/re-hash/replay. It must not trust the route ledger's conclusions.

Required checks:

- repaired transaction regressions still pass or are referenced from immutable Phase 0 evidence;
- source identity remains confirmed;
- destination baseline remains unchanged;
- all frozen anchors remain intact;
- route input count matches gate-6 exactly;
- S5 verdict recomputes from the fresh frames;
- if S5 passed, live S6 v5 verdict recomputes;
- if S7 occurred, menu observation recomputes;
- no Save All, chooser, download, or formal state write occurred.

## 12. Rev25 success definitions

Keep three results separate.

### A. Existing album data

Expected: still preserved and unchanged.

### B. Reusable automation route capability

Rev25 route capability is successful only if independent acceptance proves:

`TARGET_CARD_ELIGIBLE -> ONE_CARD_CLICK -> ALBUM_OPEN_VERIFIED -> LIVE_V5_ELLIPSIS_ELIGIBLE -> ONE_ELLIPSIS_CLICK -> MENU_SURFACE_AFFIRMATIVELY_OBSERVED`

Anything shorter is not full route success.

### C. Full automatic backup product

Still **not complete** at the end of Rev25, because Rev25 explicitly forbids Save All.

A future revision must separately prove, exactly once:

- Save All activation
- chooser observation/selection
- real new download
- 57-image verification
- terminal state commit
- duplicate/repeat run refusal
- crash/restart recovery
- LINE restart/machine restart behavior.

## 13. Reporting and commits

At each completed phase:

- write append-only evidence;
- commit with a concise Traditional-Chinese four-part message: intent / changes / evidence / next step;
- never rewrite historical evidence;
- report paths + SHA-256, not screenshots.

Final report must state, separately:

1. existing 57-file backup status;
2. reusable route status;
3. full automatic backup-product status;
4. exact scoped blocker if not complete.

