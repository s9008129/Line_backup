# Rev27d root-cause analysis — semantic effect of the single Save All dispatch (attempt-07)

Round: `ZERO_GUI_SAVE_ALL_DISPATCH_RECONCILIATION` / `REV27D-RECONCILE-ATTEMPT07-SAVE-ALL`
Zero GUI input. Read-only forensics + append-only evidence. attempt-07 itself is unmodified (154/154 manifest entries byte-identical).

## 0. What is being reconciled

On 2026-09-23 at 11:29:18.383 +0800 the Rev27c Gate A attempt-07 dispatched exactly one click:

    lineApp.click([320,135], {mouseButton:'left', clickCount:1})

It targeted the fresh 「儲存全部」 row of the freshly observed album-level popup (v8 locator ELIGIBLE, S11e final gate 14/14 PASS at 11:29:06). The recorded dispatch state is `RETURNED`.

`RETURNED` (as recorded in `attempt-07/save-all-dispatch-record.json`) has exactly one meaning: **the CU click API call returned normally** (return value `undefined`). It does not, by itself, establish that the menu item's action executed, and this reconciliation neither upgrades nor downgrades that historical verdict. The question here is only: *what was the semantic effect of that one physical click?*

## 1. Coordinate chain — fully reconstructed (machine evidence)

Chain (details in `coordinate-chain.json`):

| step | space | value |
|---|---|---|
| v8 candidate (S11e, fresh frame) | window-local pt | [319.75, 135.25] |
| rounded dispatch arg | window-local pt (CU click space) | [320, 135] |
| expected physical point | screen pt | [531, 164] |
| expected physical point | frame px (scale 2) | [1062, 328] |

- The click API's documented coordinate space for this binding is the **app-window screenshot space (window-relative)** — `@oai/sky .../types/window/Click.d.ts`: “X coordinate in the app-window screenshot… Y coordinate in the app-window screenshot”; “Click either an indexed element from the latest app state or a coordinate in the app window” (sha256 89ca15e9…). `@oai/sky .../types/window2/Click.d.ts` (sha256 3820ce4d…): “Window-relative X coordinate.”
- The JS wrapper chain passes the pair through with **no conversion**: `lineApp.click([x,y])` → `create_tinysky_alt.js` `click:(e,o)=>t.click({app:i, x:e[0], y:e[1], …})` (sha256 d8c19eb3…) → `targets/mac/click.js` (sha256 02090128…) → `client.js` `click()` builds `{click:{at:{coordinate:{_0:[x,y]}}, clickCount, mouseButton}}` inside a `ComputerUseIPCAppPerformActionRequest` IPC request (sha256 b5addc3c…).
- The app-window screenshot used by this surface is 1:1 with the window in points: `s1-window-cu.jpg` = 327×643 px = exactly the LINE window size 327×643 pt. Window origin at [211,29] pt (AX + CG agree; stable 11:08→11:37).
- The **native translation** (SkyComputerUseService, compiled binary — not source-auditable) was pinned empirically by two independent physical measurements, described next. Conclusion: physical point = window-local pt + window origin, scale 1, i.e. [320,135] → [531,164] pt.

## 2. Physical anchors (independent of the mapping assumption)

1. **Software-cursor overlay window (harness-owned).** `attempt-07/s12-cg-window-list.json` (11:32): window `Software Cursor`, owner `ChatGPT Computer Use`, layer 102, bounds pt (468,101,126×126) → **center (531,164) pt = px (1062,328)** — exactly the reconstructed physical point of the Save All dispatch, and no pointer action occurred after 11:29:18. This window did not exist in the pre-click window lists (`s1-window-zorder.json` 11:09, `s5-preclick-zorder.json` 11:11).
2. **Rendered cursor glyph (double cross-anchor).** Isolating the bright cursor outline in the post-click frames (same method both times) gives: after the ellipsis click (click point px (1030,158)) centroid (1032.6,161.4) px = point + (2.6,3.4) px; after the Save All click (click point px (1062,328)) centroid (1064.4,331.2) px = point + (2.4,3.2) px. The two clicks show the same glyph-to-point offset within 0.2 px — a cross-calibration that ties the Save All physical point to the reconstructed (1062,328) px, given the ellipsis click point is semantically pinned (it opened the popup).
3. **Semantic anchor.** The single ellipsis click at window-local [304,50] opened the album-level popup. Under a screen-global reading the physical point would have been (304,50) pt = window-local (93,21) (title bar) and no menu could have opened; under any other candidate origin the 4×4-ish pt control would have been missed. Hence the native layer demonstrably translated window-local → screen-global with the window origin at the ellipsis dispatch, through the same call path used by the Save All dispatch.

**Falsification table (Save All dispatch):** screen-global interpretation predicts physical px (640,270) (and outside the popup → “outside-click dismissal”); scale-2 error predicts px (1702,598); origin [0,29] predicts px (640,328); origin [−1,35] predicts px (638,318); no-translation predicts px (640,270). **All are refuted by the measured cursor at px (1064,331)/(1062,328), ≥420 px away in x.** The only surviving mapping is window origin +(211,29), scale 1.

## 3. Hit test (verdict: SAVE_ALL_HIT_CONFIRMED)

Under the proven mapping the physical point px (1062,328) = pt (531,164) lies:

- inside the fresh 儲存全部 text band px x[1047,1148.33] y[316.33,340.67] (margins: left 15 px, right 86.3 px, top 11.67 px, bottom 12.67 px; ≥5.8 pt vertically each side),
- inside the v8 safe interior x_safe [1049,1074] / y_safe [322.33,334.67] px,
- inside the popup bbox px [1008,182,1246,485] (margins ≥54 px) and inside the popup AXDialog rect px [988,162,1262,496],
- 33.3 px / 33.0 px away from the neighboring row bands (修改相簿名稱 bottom 294.67 px; 刪除相簿 top 361.0 px),
- within 0.56 px of the row's OCR mean center.

Residuals carried explicitly (details in `hit-test-reconstruction.json`): (i) the native translation is anchored empirically, not source-audited (compiled binary), and (ii) the freshest machine snapshot of the menu is the S11e gate frame 12.4 s before the dispatch (no input and no observed state change in between; the window origin was stable across 11:08→11:37; the dispatch was the very next action). No stale/historical coordinates were used anywhere in the chain.

## 4. The menu-dismissal alternative (Section F of the authorization)

- **Can the physical point have been outside the popup (outside-click dismissal)?** No: under the proven mapping it is inside the popup bbox and inside the target row; every mapping that would place it outside the popup (notably the screen-global one) is physically refuted by the cursor anchors. Outside-click dismissal via a wrong coordinate space is therefore **geometrically excluded**.
- **Could it have fallen on the main LINE window instead of the popup?** The popup's frame covers the point; historically this popup receives and acts on clicks (a prior coordinate dispatch into this menu activated 修改相簿名稱 — capability matrix: “one prior coordinate activated Rename”). No evidence supports the point reaching the album surface beneath.
- **Does menu disappearance distinguish activation from dismissal?** No. The popup is an app-drawn AXDialog-style window (not a native NSMenu whose tracking semantics could be argued from platform behavior alone); dismissal may be followed by action execution or not. Menu disappearance is **not** activation proof.
- **Does the AXDialog's disappearance carry activation meaning?** No. The AX tree never exposed the popup's items (attempt-13 precedent), and the s12 reads show only that the window count returned to the pre-popup set (3 windows). No activation semantics attach to that event.
- **Residual alternative that remains open:** an in-popup dismissal **without** action execution (custom-popup behavior is app-defined and not source-auditable), or an activation whose expected downstream effect (panel creation/display) failed. Neither has affirmative evidence; both remain possible.

## 5. Why no chooser — candidate explanations

No chooser/panel/new window appeared in 4 frames spanning 11:29:34→11:37:23; no new AX window; the CG window set is unchanged except the harness software cursor; baseline and staging untouched; no post-dispatch writes anywhere checked; LINE stayed alive, frontmost, idle. Candidate explanations, all unproven:

- **H2 in-popup dismissal without action** — geometry says the click hit the row interior; if LINE's popup closed on the click without running the action, the observable result is exactly what was observed. No affirmative evidence either way.
- **H3 activation executed but the AppKit save panel never created/displayed** — would require an internal failure; the bounded log window shows no panel-creation attempt, no sandbox denial, no crash, but log coverage is not proof of absence.
- **H4 menu already closed before the click** — no positive support: post-dispatch frames show the window region effectively identical to the pre-ellipsis state (MAD 0.137 over the whole window region) and no selection/viewer artifact from a surface click; but not fully excludable from pixels alone.
- **H6 delivery/handling race** — the log does show LINE performing a trust check of the synthetic-event sender (CUAService) at 11:29:17.913, i.e. event delivery began ~0.5 s before the recorded dispatch completion; no further evidence.

**Excluded:** coordinate-space mismatch / outside-click dismissal (Section 3–4), and any “harness clicked somewhere else” class.

## 6. Root cause statement

**Root cause of the missing chooser: UNDETERMINED.** What is affirmatively established: the single click physically landed inside the fresh 儲存全部 row's safe interior under the documented and physically anchored coordinate semantics; the menu closed; no chooser, panel, file operation, or filesystem write followed; no retry occurred. What cannot be established from machine evidence: whether the menu item's activation handler executed and the panel failed/passed, or whether the popup dismissed without executing the action.

## 7. At-most-once status and retry policy

The historical Save All click budget is consumed (1/1, retry 0). Because activation-vs-non-activation is **not affirmatively resolved**, this round issues **no retry and no retry authorization**; the reconciliation barrier remains (`retry-policy.json`, `semantic-classification.json` = `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE`). Any future retry would require a new reviewed plan, a new owner one-shot authorization, and a fresh full live chain — and is not eligible merely from this analysis.

## 8. Dispatch architecture review (design only, nothing executed)

If a future revision is ever authorized, the strongest next-version design would keep exactly one activation and harden the activation path itself:

1. **Screen-global dispatch path** — compute the expected physical screen point (window origin + fresh candidate) and dispatch in screen space where the harness supports it, removing reliance on the native window-local translation; fail closed if the harness offers no screen-global coordinate path.
2. **Popup-relative candidate derivation** — derive the candidate relative to the fresh popup geometry (AXDialog rect ∩ target row band) and translate via the freshly re-read window origin at dispatch time (same point, more explicitly bound to the popup rather than to the window).
3. **AX menu-item action (AXPress) on the identified item** — only if a fresh read-only verification proves the popup's items are AX-exposed while the menu is open; attempt-13 evidence suggests they are not, so this option needs a zero/low-input revalidation before it can be trusted.
4. **Post-dispatch software-cursor read-back** — this round proved the harness's software cursor is an independent, machine-readable anchor (overlay center == click point). A future dispatch should read the CG window list immediately after the click and assert the overlay center equals the intended point; mismatch ⇒ STOP + classify.
5. **Fresh hit-test immediately before dispatch** — reuse the proven S11e-style gate, but recompute the *screen* point (not only the window-local candidate) and require the window origin and popup bbox to be re-read within the same gate; shrink the gate→dispatch interval where feasible.

Non-negotiables for any such design: current evidence derived; no historical coordinates; at-most-once preserved; exact 「儲存全部」 target with v8-lineage identity preserved; fail-closed on every gate; no change to the accepted baseline.
