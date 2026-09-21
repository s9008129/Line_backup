# Review 1 — top-down state/surface-identity review

- Reviewed artifact: `PLAN-2026-09-21-rev27b-lineage-guard.md`
- Reviewed SHA-256: `7a179d15f61033611dec333d246b6d8c590901c06c182628533e442feae10a7c`
  (recomputed from disk by the reviewer: `shasum -a 256 …`; mtime `19:52:02`, unchanged)
- Lens: top-down — goal alignment, necessity, critical path, gate/veto proportionality, failure
  containment, coupling, design economy; then bottom-up — repository grounding, contracts, sequencing,
  verification.
- Date: 2026-09-21 (read-only; zero GUI input; no repo writes made during review)
- This review binds **only** the SHA above. Any later edit invalidates this review.

## Goal baseline reconstructed from the authoritative owner instruction

Close the Rev27 Save All Gate A attempt-03 safety gap without any GUI input this round: the frozen
album-open verifier returned `ALBUM_OPEN_VERIFIED` while the actual surface was the album-list window;
"frozen verifier alone" must never again be sufficient evidence of an open album detail. Deliver an
append-only, fail-closed lineage guard + composite rule + deterministic tests + offline replay showing
the attempt-03 path can never composite-PASS, plus a future album-card reopen gate design in which the
album-card click is never merged with an ellipsis/menu step and Save All stays out of scope. Frozen
v4/v5/v6, historical attempts, accepted baseline and the Rev27 plan/reviews must remain untouched.

## Pass 1 — top-down

1. **Goal alignment.** CONFIRMED. The root cause recorded on disk
   (`attempt-03/s3-album-open-verify-window.json`: `verdict ALBUM_OPEN_VERIFIED`, `changed_fraction
   0.530517`, title bbox `[15,449,…]` = list-surface geometry) matches the plan's framing. The plan's
   composite rule (frozen `ALBUM_OPEN_VERIFIED` AND guard `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED`)
   closes it, and C7 additionally binds the frozen artifact's `post_sha256` to this round's frame
   sha256 so cross-round verdicts cannot compose.
2. **Read-only / deterministic / no hard-codes.** CONFIRMED. The guard's only write path is the
   optional `--out` (not passed). No coordinate literals: `337` appears only in selftest fixtures and
   plan text (inventories carry it as data). The attempt-13 rect `[337,30,327,643]` matches
   `attempt-13/s1-ax-pre.json` window 0 exactly. Reviewer's live run (no `--out`) returned
   `ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED`, exit 0, C4 full-tree chrome-only, C5 `mad_mean 2.259`,
   C6 title y-frac `0.1726`, `57張照片`. Two runs → byte-identical output.
3. **Attempt-03 regression.** CONFIRMED. Six independent recombinations, all `REFUSED`, none reaching
   C7/composite: (a) a03 native → `SURFACE_HAS_LIST_CONTROLS` / `…ROWS` / `FOCUSED_ELEMENT_NOT_WINDOW`;
   (b) + a12 frame; (c) + a12 window shot; (d) a13 inventory/state + a03 frame → `BINDING_FAILED`;
   (e) a13 evidence + a12 shot → `BINDING_FAILED`; (f) a03 inventory with injected `[337,30]` copy in
   `/tmp` (not repo) → still `SURFACE_HAS_LIST_CONTROLS`; plus frame swapped to the window shot →
   `EVIDENCE_MALFORMED:frame_scale`. All runs had attempt-03's own frozen artifact supplied; the
   composite can never be reached, let alone PASS.
4. **Frozen verifier unmodified.** CONFIRMED. `tools/v4/verify_album_open.py` and
   `tools/v5/verify_album_open.py` both hash `ffa82aed789f9e752c26cc3ae1380c69b8cfe8badbf2567c0ac36693a373cf58`.
5. **Ambiguity / missing / wrong windows.** CONFIRMED. C0 missing/malformed → exit 6; C2 multiple
   focused/main → `TARGET_AMBIGUOUS`; C3 duplicate geometry; C4 diff/empty AX → refuse. `results.json`
   negatives (`neg-multiple-focused-windows`, `neg-two-main-windows`, `neg-missing-ax-tree-diff-form`,
   `neg-empty-ax-tree`, `neg-attempt-03-regression-frozen-verdict`) all pass; `22/22`, repeat
   byte-identical; `replay-record.json` `REPLAY_PASS`.
6. **Separation / scope.** CONFIRMED. Plan §1/§4: the album-card click is its own future gate behind a
   new owner authorization; "must not click the ellipsis"; budgets ellipsis/menu/Save All/chooser/
   keyboard/scroll/download = 0; §7 states NOT READY_FOR_ELLIPSIS / SAVE_ALL / DOWNLOAD. This revision
   = GUI 0.

## Pass 2 — bottom-up

1. **Repository grounding.** PASS. Attempt-03 artifact values, attempt-13 window geometry and frozen
   tool hashes were re-read from the repo during review; nothing in `evidence/` was newer than
   pre-review authoring (latest 19:51:45).
2. **Contracts.** PASS. The guard imports the frozen Vision reader read-only from the v5 default
   `--reader-dir`; no frozen file is written or patched.
3. **Sequencing.** PASS. Plan §4 orders list-identity → album-card click → evidence capture → frozen
   verifier → lineage guard → composite → unconditional STOP.
4. **Verification plan.** PASS. Selftest 22 deterministic cases + determinism rerun + attempt-03 sweep
   (5 combinations, none verify) + offline replay record; the attempt-12 diff-form evidence-shape
   limitation is explicitly recorded rather than papered over.

## Non-blocking observations

- Reviewer did not re-execute `run_selftest.py` (it writes into the repo); `results.json`
  (`affb3602…`) was read and the guard executed live instead.
- Reviewer spot-verified key evidence hashes, not all 20/33/34 rehash entries.
- The CU AX-state text is bound to the screenshot only by runbook contract (not cryptographically
  tied); C5 pixel binding + C6 OCR still enforce the detail surface.
- Vision-OCR cross-OS determinism remains a recorded UNKNOWN.
- attempt-12's bridged replay stays a documented evidence-shape limitation.

## Verdict

**PLAN_APPROVED** for plan SHA-256
`7a179d15f61033611dec333d246b6d8c590901c06c182628533e442feae10a7c`.
