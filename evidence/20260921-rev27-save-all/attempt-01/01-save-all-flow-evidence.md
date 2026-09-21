# Save-All flow evidence (Section D) — read-only research, 2026-09-21 (rev27 planning round)

Read-only sources used (nothing was executed against LINE):
- live project state: `/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/`
  (`config/line_backup_config.json`, `state/backup_state.json` rev 39, `state/run_log.md`)
- `evidence/20260915-capability-matrix.md`
- `src/line_backup_acceptance/{transaction,verifier,authority,common}.py`
- `~/.codex/skills/line-album-backup/references/{ui-procedure,state-contract}.md`
- `evidence/20260916-route/attempt-13/*` (attempt-13 evidence, menu observation)
- read-only re-OCR of `evidence/20260916-route/attempt-13/frame-menu-post1.png` (this round)

Labels: CONFIRMED (documented in durable evidence) / UNKNOWN (no evidence; fail closed) / HISTORICAL (evidence exists but from an older version; not current truth).

## Q1. Does clicking 「儲存全部」 always produce a chooser?

EXPECTED — but NOT guaranteed. One confirmed observation, several non-confirmations.

Evidence FOR (chooser appears):
- `RUN-20260907-154331-01` — the run that produced the accepted baseline, same album
  `2024/05/13–05/17` / 57. Event `SAVE_ALL_TRIGGERED`:
  "Atomic dispatch action EAD45337-… returned: ellipsis click once, Save All click once, no errors,
  followed by fresh observation of the expected macOS 打開 folder chooser."
  `intent.trigger_outcome = CHOOSER_CONFIRMED`; then Go to Folder with the exact destination →
  one confirmation → `DOWNLOAD_STARTED`: "正在下載... 0/57".

Evidence AGAINST / uncertainty:
- `RUN-20260908-124357-01` (album 2024/06/02–06/07, 65): one ellipsis click + one Save-All
  coordinate invocation returned without runtime error; NO chooser was observed →
  `TRIGGER_UNKNOWN` → SAFE_ABORT; destination `Stage18` remained a stable empty directory
  (3 samples @ 5 s).
- `RUN-20260907-101314-01`: same shape (`SAVE_ALL_TRIGGERED` then SAFE_ABORT); manual
  reconciliation records owner attestation: "Save All was not triggered", "popup click missed
  Save All", "folder chooser never appeared".
- `RUN-20260907-132845-01`: a calibration attempt entered `已選擇0個項目` selection mode
  (cancelled); the later dispatch failed on the first ellipsis click (`noWindowsAvailable`) →
  `ABORTED_BEFORE_SAVE_ALL_DISPATCH`.

Design consequence: a correctly activated 儲存全部 is expected to raise the macOS 打開 folder
chooser, but a wrong/missed activation can silently do nothing, raise selection mode, or do
something else. "Chooser appears" is the expected-but-not-guaranteed outcome; Gate A exists
exactly to observe the real result freshly. No retry is ever allowed on any outcome.

## Q2. Chooser type

CONFIRMED (2026-09-07, HISTORICAL for current version): macOS **打開 (Open) folder chooser**
panel — state event text "expected macOS 打開 folder chooser"; run_log: "The expected macOS
folder chooser appeared."
Whether the current LINE build presents the same panel: UNKNOWN.
Chooser visibility in the AX tree: NOT VALIDATED — attempt-13's AX reads showed the app AX
tree did not even expose the open menu ("no change in the accessibility tree"); no evidence
shows the chooser or its controls are AX-exposed. UNKNOWN.

## Q3. Default destination of the chooser

UNKNOWN. No evidence records the default folder. The only successful flow never used the
default: it navigated with Go to Folder to the exact absolute destination.
Design rule: never accept the default; always prove the leaf folder; if the chooser evidences
the default = the accepted baseline (or anything outside the frozen staging path), STOP.

## Q4. Is Go to Folder required?

CONFIRMED HISTORICAL: run_log: "Go to Folder was used with the exact absolute destination. The
leaf folder was visually confirmed and the destination was opened once." Capability matrix
notes coordinate/row-index folder selection failed in earlier versions and Go to Folder
succeeded in V4 / ALBUM_VISUAL_003. Current-version revalidation: UNKNOWN.

## Q5. Is keyboard path entry required?

CONFIRMED HISTORICAL: the documented chooser procedure uses the keyboard Go to Folder command
(`super+shift+g`) and then entering the absolute path; the successful run also hit one chooser
clipboard timeout ("Error: Computer Use server error -10005: Timed out waiting for the
application to read the clipboard", `recovered: true`), documented as:
"One chooser clipboard timeout occurred during the first path input; the unchanged field was
re-observed and the same identified path field was completed successfully with `setValue`."
(`setValue` = an AX write into the path field.)
Design consequence: Gate B must enumerate an explicit budget for (a) the chord, (b) the path
entry method (typed vs clipboard paste vs AX `setValue`), (c) the path commit (Return), and
(d) exactly one confirmation. AX write must be listed explicitly if the owner wants the
historical fallback available; otherwise it stays forbidden.

## Q6. Is there a native AX/CUA path that selects the folder without keyboard?

UNKNOWN / NOT VALIDATED. There is no evidence of the chooser, its folder list, or its buttons
being exposed to AX, and the app-window AX tree provably does not expose even the popup menu
(attempt-13 AX affirmation: NEGATIVE). Historical practice is keyboard-based (Go to Folder).
No current evidence supports a keyboard-free folder selection path; the plan must not assume
one.

## Q7. Semantics of the chooser's confirmation

UNKNOWN (exact button label not recorded in durable evidence). What IS confirmed is the
sequence and effect: identify the chooser → Go to Folder → absolute path → observe
path/breadcrumb → observe the exact leaf folder → confirm destination once → LINE begins the
download ("正在下載... 0/57"). Overwrite/conflict behavior when the destination already
contains files: UNKNOWN → staging must be proven empty; any overwrite/conflict prompt → STOP.

## Q8. Save-All dispatch vs chooser acceptance: where is the side-effect boundary?

Two different boundaries, per contract and evidence:
- The **dispatch boundary** = the single 「儲存全部」 activation. Its at-most-once semantics are
  absolute (`save_all_retry_allowed=false` forever; a returned call does not prove a trigger;
  UNKNOWN dispatch ⇒ never retry).
- The **filesystem write boundary** = the chooser confirmation. Evidence shows no files before
  confirmation, and the download starting only after it.
Design: Gate A = dispatch boundary, observation only. Gate B = filesystem side-effect boundary
(exactly one confirmation). Any filesystem change before confirmation = anomaly ⇒ STOP.

## Q9. Can LINE start writing before chooser confirm?

No evidence of any pre-confirmation write: the same run's destination was empty while the
chooser was open, and the download began only after confirmation. Label: not observed;
formally UNKNOWN → any pre-confirmation write is treated as an anomaly (STOP + report).

## Q10. Which cancel/abort stages are safe?

- Before the Save All click (menu open): zero side effects; any stop is safe. (This round ended
  there, with the menu left open for the owner.)
- After the Save All click, chooser open: dismissing (Escape/取消) is plausible macOS behavior
  but LINE-specific behavior is UNKNOWN and it is keyboard input. Plan default: leave the
  chooser open, hands off, no Escape, no clicks.
- After confirmation, download in progress: LINE-side cancel is not authorized; filesystem
  partials → STOP + quarantine (never delete).
- After dispatch with no chooser: stop; manual reconciliation; never retry
  (precedent: RUN-20260908-124357-01).

## Zero-byte hazard (load-bearing for Gate C)

In `RUN-20260907-154331-01`, after confirmation ALL 57 files existed as **zero-byte**
placeholders (`application/octet-stream`); **24 consecutive** read-only samples showed an
identical, stable 0-byte inventory; the download completed later (by 08:04:45 the directory
held 57 `image/jpeg` files, 17,924,900 bytes). Therefore: a 57-count and even sample-to-sample
stability are NOT completion. Completion requires non-zero bytes and structural decodability.

## Menu-item geometry feasibility note (illustrative ONLY — not an input coordinate)

Read-only re-OCR of `evidence/20260916-route/attempt-13/frame-menu-post1.png` (frame
2294×1490 px, 2× ⇒ screen px = 2× screen pt) this round, per-word boxes in frame px:

| item | word boxes (y ranges, px) | row center ≈ |
|---|---|---|
| 選擇項目 | y 210.3–234.7 | 222 |
| 修改相簿名稱 | y 254.3–302.3 | 278 |
| 儲存全部 | 儲存 [1299.0,318.3,1400.7,342.7]; 全 [1357.7,308.3,1381.7,356.3]; 部 [1381.7,308.3,1399.7,356.3] | 332 |
| 刪除相簿 | y 362.3–410.3 | 386 |
| 分享相簿 | y 416.3–464.3 | 440 |

Row step ≈ 54 px ≈ 27 pt. Frozen-detector menu bbox (screen px) [1247,127,1494,478]
≈ screen pt [623.5,63.5,747,239]; LINE window rect px [674,60,1328,1346] (screen pt
[337,30,664,673]).
Consequence: the 儲存全部 text box x-range ∩ the LINE window x-range = [1299,1328] px
(29 px ≈ 14.5 pt wide) — i.e. a click point on the identified row that is addressable in the
proven app-local click space exists (≈ window-local x 312.5–327 pt at row center y ≈ 136 pt
window-local), should the app-local path remain the only proven input path.
This paragraph is a feasibility statement about attempt-13's frame only. Gate A must derive
everything fresh from its own frame; nothing here confers authority or supplies a reusable
coordinate.
