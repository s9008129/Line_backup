# Rev25 Phase 2 — S5 NO_EFFECT 假說矩陣

`GUI_INPUT_COUNT: 0`. Every row has exactly one of `SUPPORTED`, `REJECTED`, or `UNKNOWN`; no unproven cause is promoted.

| 假說 | Status | Evidence / boundary |
|---|---|---|
| px→Retina→pt 的算術映射錯誤 | **REJECTED** | Historical screen was 2294×1490 @2x; WIN1 origin `(0,54)` px; `[42,895]` maps to `[21,447.5]` pt and emitted `[21,448]`, matching the recorded conversion. |
| System Events 需要 window-local 而非 global coordinates | **REJECTED** | `System Events.sdef` defines process `click at` as global coordinates; the historical command used global `[21,448]`. |
| 0.5pt y-rounding 造成 miss | **UNKNOWN** | Exact y is `447.5`, emitted y is `448`; no UI hitbox or event-target trace exists to distinguish rounding behavior. |
| click point 確實落在 OCR title/text band | **SUPPORTED** | `[42,895]` is inside S3 title bbox `[30,883,257,907]`, by the recorded derivation `left+12`, vertical centre. |
| title/text band 不是 album-card hitbox | **UNKNOWN** | The point is visibly/textually in the title band, but no AX hitbox or LINE control geometry proves the card's interactive region. |
| 歷史 click 被其他 app / wrong z-order 攔截 | **REJECTED** | Historical evidence recorded LINE frontmost; S4 returned `window 1 of application process LINE`; no bring-to-front was needed. |
| LINE 內部 focus / event consumption 仍有問題 | **UNKNOWN** | Frontmost/window return is not an event-consumption trace; current LINE is unavailable, and no AX focus/event target was recorded. |
| shell `osascript` semantics 與原 CUA click semantics 不同 | **UNKNOWN** | Runtime actually had no CUA executor and used `screencapture -x` + System Events; sdef confirms coordinate semantics, but no proof exists that LINE handled the event identically to CUA. |
| single click 不足，需 double/另一個 card region/hover | **UNKNOWN** | Only one click was authorized and the route closed at S5; no retry, hover, or alternate gesture was tested. |
| post capture 太早 | **UNKNOWN** | S5 was about five seconds after S4, but no timing sweep or later live observation was authorized. |
| pre frame stale / mismatch caused NO_EFFECT | **REJECTED** | Supporting fresh-pre re-run also returned `NO_EFFECT` (`0.014715`); the official pre/post pair was recorded as fresh and Stage05 replay matched. |
| verifier 的 frozen numeric threshold 造成 NO_EFFECT | **SUPPORTED** | Recorded `161820/(2294×1490)` rounds to `0.047343 < 0.05`; the offline threshold sweep confirms lower thresholds would pass the numeric gate. |
| lowering threshold alone would prove album open | **REJECTED** | The verifier's changed bbox is `[676,14,2261,978]` in the right-side terminal area; title/count remained the album-list surface. Numeric passage is not semantic proof. |
| S5 changed surface came from the LINE card | **REJECTED** | Frozen evidence attributes the changed bbox to the right-side terminal area, while the LINE title/count remain readable at the same bbox. |
| v4 reader failed, so NO_EFFECT is a reader artifact | **REJECTED** | S5 carries a healthy v4 reader block; title and count `57` were read; reader calls were `ok`/exit 0. |

## Diagnostic conclusion

The strongest supported statement is narrow: the event was mathematically converted and dispatched to the frontmost LINE window, but its screen point was derived from the title/text band, while the S5 verifier stopped on a deterministic numeric threshold whose changed pixels were outside the LINE card. The actual card hitbox/event-consumption cause remains **UNKNOWN**. Therefore this diagnosis does **not** justify a v6 card-point correction.
