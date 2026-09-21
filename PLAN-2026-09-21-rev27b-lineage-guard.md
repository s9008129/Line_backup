# PLAN — Rev27b: ALBUM_DETAIL_WINDOW_LINEAGE_GUARD + future album-card gate (append-only revision)

PLAN_REVISION: rev27b-1
TASK_CLASS: STANDARD (safety-critical guard design; zero GUI input this round)
REVIEW_REQUIRED: YES (two fresh independent reviews of this exact file's SHA-256)
INDEPENDENT_ACCEPTANCE_REQUIRED: NO for this round (offline replan; verification
  is the deterministic selftest + offline replay in `tools/v7`)
E2E_REQUIRED: NO (no live GUI input is authorized in this revision)
PREPARED: 2026-09-21 (zero GUI input; repo evidence writes only)

## 1. Goal Contract (plain language)

The Rev27 Save All Gate A attempt-03 round exposed a safety gap: the frozen
album-open verifier returned `ALBUM_OPEN_VERIFIED` while the actual surface was
the album-**list** window; no album-detail window existed. The verifier's rules
(target title readable + changed_fraction) are surface-agnostic and can never
stand alone as "the correct album detail is open".

Goal: make "the correct album detail is open" a **composite** condition that
also requires a machine-checkable, fail-closed **lineage guard** over the
current round's AX/window evidence; and define the future album-card reopen
gate that uses it. CORE: the guard + composite rule + tests proving the
attempt-03 path can never pass. SUPPORTING: the future album-card gate runbook
(design only; not executed here). BEST_EFFORT: none. Nothing in this revision
authorizes ellipsis, menu, Save All, chooser or any live GUI input.

## 2. Composite success rule (supersedes "frozen verifier alone")

```
ALBUM_OPEN_VERIFIED_COMPOSITE =
    frozen album-open verifier == ALBUM_OPEN_VERIFIED        (same-round frame pair)
  AND
    album_detail_lineage_guard == ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED
```

The frozen verifier must run on the SAME round's `frame-pre`/`frame-post`
(its own input contract; attempt-03 violated it by passing historical frames —
this is recorded as a contributing cause, not a modified verdict). The guard
additionally requires (when `--frozen-album-open-json` is supplied) that the
frozen artifact's `post_sha256` equals this round's frame sha256, so a verdict
from another round can never compose.

## 3. The guard (implemented: `evidence/20260916-route/tools/v7/album_detail_lineage_guard.py`)

Inputs (same round; each hashed): frozen AX window inventory JSON, CU
**full-tree** AX state text of the focused window, CU window screenshot of that
window, full-screen frame, target album identity (`--expect-start/--expect-end/
--expect-count`), optional frozen verdict artifact.

Checks (all must PASS; fail-closed):
`C0` evidence/schema/frame-scale · `C1` bundle+frontmost+trusted ·
`C2` exactly one AX-focused window AND one main window, same window, not
minimized, `AXWindow/AXStandardWindow` · `C3` no duplicate-geometry ambiguity,
target inside frame · `C4` AX surface class = custom-drawn detail
(standard window + close/minimize chrome, no `列表`/`文字欄位`/rows, focused UI
element is the window) · `C5` frame/window pixel binding at the rect derived
from the current inventory (dims exact, gray MAD <= 12.0) · `C6` detail header
context on the BOUND screenshot via the frozen Vision reader (target title with
bottom <= 30% of window height; `張照片` token whose digits == expected count;
no `相簿`/`記事本` tabs) · `C7` optional composite binding.

Invariants: read-only; zero GUI input; deterministic (byte-identical output for
identical inputs); every rect derived from the current inventory; **no
historical coordinate and no window-position hard-code** (the historical
`[337,30]` remains evidence only); ambiguity, missing/malformed evidence,
wrong/multiple windows, stale/occluded binding, list surfaces, wrong album or
count all refuse. The guard never clicks and never opens anything.

Frozen tools v4/v5/v6 and the frozen album-open verifier are untouched; v7 is a
new append-only version that imports the frozen reader read-only.

## 4. Future album-card reopen gate (design; requires a NEW owner authorization)

Per-gate flow (a fresh owner authorization is required before any of it):

1. fresh read-only album-list identity: fresh frame + frame-SHA-bound geometry
   + frozen v6 album-card locator must be `ELIGIBLE`;
2. owner one-shot **album-card** authorization (this gate only);
3. exactly one album-card left click on the candidate derived from this round's
   frame (no retry, no fallback, no historical candidate);
4. evidence capture for the post-click state: `frame-post`; fresh AX window
   inventory; **full-tree** CU AX state read of the focused window (the CU read
   must be a session-first read; diff/"no change" forms are not acceptable
   evidence and make the guard refuse); CU window screenshot;
5. frozen album-open verifier on `frame-pre`/`frame-post` -> V1;
6. lineage guard on the same-round evidence -> V2;
7. composite decision recorded; then **STOP unconditionally**.

Budgets: album-card click <= 1; ellipsis 0; menu 0; Save All 0; chooser 0;
keyboard 0; scroll 0; AX write 0; bring-to-front 0; download 0; destination
write 0; retry 0. Even when the composite passes, this gate **must not** click
the ellipsis: the ellipsis/menu inspection is a separate, later gate with its
own authorization, and Save All/chooser remain out of scope until separately
planned.

Stop conditions (any -> STOP, no retry): guard refusal of any kind, composite
fail, missing/full-tree-unavailable AX evidence, frame/window binding failure,
ambiguity, surface change versus the album-list identity step, or any deviation
from the budgets.

## 5. Verification obligations for this revision (already executed offline)

- `tools/v7/selftest/run_selftest.py`: 22 deterministic cases, PASS, including
  album-list-with-title, count-57-no-detail, detail-pixels-with-list-controls,
  wrong LINE window, multiple candidates, missing/diff AX tree, stale frame
  binding, occluded detail, malformed evidence, historical-coordinate
  injection, wrong album, wrong count, composite-not-bound;
- determinism: repeated run byte-identical;
- attempt-03 sweep: 5 attempt-03-derived input combinations, none may verify;
- replay record (`evidence/20260921-lineage-guard-replan/replay/`): attempt-12
  pre REFUSED; attempt-12 post strict REFUSED (diff-form AX evidence) and
  VERIFIED+composite PASS via the documented byte-identical-screenshot bridge;
  attempt-13 VERIFIED; attempt-03 REFUSED with its frozen verdict present.

Known evidence-shape limitation recorded for the future gate: attempt-12's
post-click CU state was saved in diff form, so the strict contract cannot
verify it; the bridged replay exists only to demonstrate the positive path on
the byte-identical surface. Future rounds must capture the full-tree form.

## 6. Review checklist (each item must be independently confirmed)

1. the attempt-03 false-positive path is closed (guard refuses; composite can
   never PASS for any attempt-03-derived input set);
2. the frozen album-open verifier is unmodified (sha256 `ffa82aed...`);
3. no historical coordinates and no window-position hard-code anywhere in the
   guard/plan; all rects derive from the current inventory;
4. current-round AX/window evidence is mandatory; ambiguity or missing evidence
   refuses;
5. the album-card click is never merged with an ellipsis/menu step;
6. Save All / chooser / download are not part of this revision.

## 7. Status / handoff

This revision is documentation + offline tooling only: GUI input = 0,
filesystem destination writes = 0, repo evidence writes only. When both fresh
reviews return PLAN_APPROVED for this exact file's SHA-256 and the attempt-03
regression is proven blocked, the project is
`READY_FOR_NEW_ALBUM_REOPEN_AUTHORIZATION` (i.e. an owner may authorize a
future album-card reopen gate under section 4). It is NOT
READY_FOR_ELLIPSIS, NOT READY_FOR_SAVE_ALL and NOT READY_TO_DOWNLOAD.
