# Rev25 route attempt-08 — gate-6 runbook

## Binding

- App: `jp.naver.line.mac`
- Group: `旻謙允禎成長日記` (`禎` U+798E; never merge with `楨` U+6968)
- Album: `2024/05/13～05/17`, count `57`
- Authorization: `gate-6-authorization.json`
- Parent route ledger: attempt-07 FINAL SHA `7c8ea39a391617f3276b4e3e40043086317c73719baf3b51bdf3d356ea2f032f`
- Runtime: documented CUA app binding for observations and click inputs; frozen offline tools for evidence-only decisions.

## At-most-once sequence

1. **S1 binding read:** fresh LINE AX state and screenshot; record current app/window, frame bytes/dimensions/SHA, and zero inputs.
2. **S2 read-only surface check:** confirm LINE is the current target surface, the target group/albums list is visible, the target card is fully visible, and no permission/unknown overlay is present. No scroll, activation, or AX write.
3. **S3 current-frame locator:** capture a fresh frame for the frozen v4 card locator. Require exact date/count `ELIGIBLE`; derive the click point from this frame only. If not affirmative, stop with zero input.
4. **S4 input #1:** exactly one normal left click on the current-frame-derived safe album-card metadata point. No retry/double click.
5. **S5 post verification:** fresh post screenshot and frozen v4 semantic verifier. Continue only on `ALBUM_OPEN_VERIFIED`; otherwise close with ellipsis `0/1`.
6. **S6 live v5 locator:** on the immediate live album frame, use only frozen v5 ellipsis locator. Require `ELIGIBLE` and a v4-reader block; no v4 fallback.
7. **S7 input #2:** exactly one normal left click at the live v5-derived ellipsis point.
8. **S8 menu observation:** read-only screenshot/AX state and frozen detector; identify menu/Save All text if possible. Do not click any menu item or close the menu if that requires input.
9. **S9 final ledger:** record all hashes, verdicts, budgets, `SAVE_ALL_DISPATCH_ATTEMPTED=NO`, and no formal-state/destination writes.

Any non-affirmative precondition is a fail-closed stop. Historical coordinates are evidence only, never live input.
