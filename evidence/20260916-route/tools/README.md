# Route tools (frozen) — v2 reused + v3 for the corrected route

Read-only, fail-closed analysis tools used by the route observations. None of these tools
sends input; the clicks themselves are executed by the runbook (attempt-04 v2 runbook for
the card control, attempt-05 v3 runbook for the corrected route) at points derived from the
current frame only.

## Tools

| Tool | Used at | Purpose | Verdicts (exit code) |
|---|---|---|---|
| `locate_card_ellipsis.py` (v2, reused unchanged) | attempt-04 | card-level ⋮ locator; in attempt-05 only corroborating | `ELIGIBLE(0)`, `TARGET_TITLE_NOT_FOUND(2)`, `NO_ELLIPSIS_FOUND(3)`, `AMBIGUOUS_ELLIPSIS(4)`, `BAD_FRAME(6)` |
| `detect_menu_popup.py` (v2, reused unchanged) | attempt-03/04/05 | pre/post image diff plus OCR strings to decide a popup rendered | `MENU_DETECTED(0)`, `NOT_DETECTED(3)`, `BAD_INPUT(6)` |
| `locate_album_card.py` (v3) | attempt-05 S3 | locate the target album card's metadata click point: title date tokens, same-frame margin rule against the bright content bands, best-effort count read | `ELIGIBLE(0)`, `TARGET_TITLE_NOT_FOUND(2)`, `UNSAFE_MARGINS(4)`, `TARGET_COUNT_MISMATCH(5)`, `BAD_FRAME(6)` |
| `verify_album_open.py` (v3) | attempt-05 S5 | decide whether the single album-card click actually opened the target album: target title readable in the post frame AND changed-pixel fraction >= 5% | `ALBUM_OPEN_VERIFIED(0)`, `NO_EFFECT(3)`, `TARGET_MISMATCH(4)`, `INCONCLUSIVE(5)`, `BAD_INPUT(6)` |
| `locate_album_ellipsis.py` (v3) | attempt-05 S6 | locate the album-level ⋮ inside the opened album: whole-frame vertical three-dot census, eligibility restricted to the album title row band right of the title, group-title row band never eligible | `ELIGIBLE(0)`, `TARGET_TITLE_NOT_FOUND(2)`, `NO_ELLIPSIS_FOUND(3)`, `AMBIGUOUS_ELLIPSIS(4)`, `GROUP_LEVEL_ONLY(5)`, `BAD_FRAME(6)` |

## Running

```
/opt/homebrew/bin/python3 <tool>.py <frame> [--options] [--out report.json]
```

- Interpreter: `/opt/homebrew/bin/python3` (3.14, Pillow). The v3 tools load
  `locate_album_card.py` from their own directory for the shared OCR/title reader, so the
  tools must stay together in one directory.
- OCR: `tesseract - stdout -l chi_tra+eng --psm 6 tsv` via stdin/stdout. This environment's
  tesseract cannot open files under `/tmp` (`Error in fopenReadStream`), so no tool writes an
  image for OCR.
- Refusal is fail-closed: every tool exits non-zero and reports `verdict` instead of guessing;
  a non-`ELIGIBLE`/non-`ALBUM_OPEN_VERIFIED`/non-`MENU_DETECTED` verdict means the run stops
  before the next input.

## Frozen self-test

```
/opt/homebrew/bin/python3 selftest/run_selftest.py [--out selftest-summary.json]
```

Renders deterministic synthetic frames that mirror the geometry observed on the real
attempt-04 window frame (327x643, dark card row around y=430 with light text, three light
dots at x≈300) and asserts the documented verdict and exit code of every refusal path of the
three v3 tools, plus the click point of the eligible case:

13 cases — card: eligible / no title / count 58 / unsafe margins; album-open: verified /
no effect / target mismatch / inconclusive; album-level ellipsis: one control / title derived
by OCR / two controls in band / group-level only / none.

The self-test never uses real screen content: fixtures are drawn pixel by pixel and written to
a temporary directory.
