# v3 tool self-tests (frozen before any attempt-05 input)

This directory holds the frozen self-test matrix for the three v3 route tools introduced by
Rev20 §20.2 for the corrected route (open the target album, then the album-level ⋮):

- `../../locate_album_card.py` — album-card metadata locator (attempt-05 S3)
- `../../verify_album_open.py` — album-open verifier (S5)
- `../../locate_album_ellipsis.py` — album-level ⋮ locator (S6)

All fixtures are synthetic frames drawn pixel by pixel by `run_selftest.py`; no screenshot,
no GUI and no input event is involved. The synthetic geometry mirrors the real attempt-04
window frame (327x643, dark card row around y=430 with light text, three light dots at
x≈300) so the frozen parameters are exercised on realistic scales.

## How to re-run

```bash
/opt/homebrew/bin/python3 selftest/v3/run_selftest.py     # from evidence/20260916-route/tools/
```

Needs Pillow and tesseract with `chi_tra+eng`. The script renders into a temporary directory,
runs every case as a subprocess with the same interpreter, prints the JSON summary and writes
it next to itself (`selftest-summary.json`). Exit code 0 when every case passes, 1 otherwise.

## Cases (13)

| Group | Cases |
|---|---|
| album-card locator | eligible / no target title / readable count 58 / unsafe margins |
| album-open verifier | verified / no effect / target mismatch (non-target date) / inconclusive (changed surface, no readable title) |
| album-level ellipsis locator | one control in the album-title row band (click point [300, 47]) / title re-derived by OCR instead of the S5 bbox / two controls in the band / group-level only / none found |

The punctuation-only-token rule is exercised by the eligible cases: the control's own dots are
recognized by OCR as a colon-like token, which must never block the candidate; a readable
multi-character alphanumeric OCR word overlapping the middle dot does block it.
