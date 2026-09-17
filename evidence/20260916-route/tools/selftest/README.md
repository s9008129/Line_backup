# Menu-popup detector self-tests (frozen before the attempt-04 click)

This directory holds the frozen self-test matrix for
`evidence/20260916-route/tools/detect_menu_popup.py` (SHA-256
`6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc`), the read-only
analysis tool that must decide "a popup/menu appeared" for route attempt-04. It is the
machine-observable evidence path required by plan §19.2: `AFFIRMATIVE` needs either new AX
menu elements or this detector returning `MENU_DETECTED` (new rectangular region absent from
the pre capture **plus** at least two transcribed menu strings inside it). OCR alone or a
human report alone can never yield `AFFIRMATIVE`.

All fixtures are synthetic (drawn by `make_fixtures.py`); no GUI, no screenshots, no input
events are involved in these tests.

## How to re-run

```bash
cd evidence/20260916-route/tools/selftest
python3 selftest_menu_popup.py      # needs Pillow + tesseract with chi_tra+eng
```

Expected: every case `ok`, final line `ALL_OK`, exit 0; it rewrites `selftest-summary.json`
(frozen result: 2,946 bytes, SHA-256
`d8ffc1290347da13816f988adbe47656d42c60041ef701bf159b9d4c52a76557`). The frozen summary was
regenerated at this exact location and is byte-identical to the pre-verified copy from the
build directory.

## Case matrix (expected)

| case | args (pre, post) | exit | verdict | ocr_status |
|---|---|---|---|---|
| positive | `fixture-base.png` vs `fixture-post-menu.png` | 0 | `MENU_DETECTED` | `OK` |
| neg_hover | `fixture-base.png` vs `fixture-post-hover.png` | 3 | `NOT_DETECTED` | — |
| neg_identical | `fixture-base.png` vs `fixture-base.png` | 3 | `NOT_DETECTED` | — |
| fail_closed_no_ocr | `fixture-base.png` vs `fixture-post-menu.png`, `PATH=/nonexistent` | 3 | `NOT_DETECTED` | `OCR_FAILED` |
| bad_input_missing | missing pre file | 6 | `BAD_INPUT` | — |
| bad_input_size | pre/post size mismatch | 6 | `BAD_INPUT` | — |

Exit-code contract: `0` menu_detected true; `3` not detected (also used, fail-closed, when
OCR cannot run: `ocr_status=OCR_FAILED`, never a crash); `6` bad input. The tool never sends
input and never writes anything except its optional `--out` JSON.

## Frozen-layout note

The frozen `selftest_menu_popup.py` is byte-identical to the pre-verified build copy
(`e5f444e722053ddf455030551551f9ec6be930eeba89b2558b0a4965673b85aa`) except for one path
constant: `TOOL` points one directory up (`../detect_menu_popup.py`), because the frozen
layout keeps the tool in `tools/` and these materials in `tools/selftest/`. No logic was
changed. The other files (`make_fixtures.py`, the three fixture PNGs) are byte-identical
copies of the pre-verified versions.

## Environment trap fixed here: tesseract cannot read files under /tmp

**This environment's tesseract cannot open image files located under `/tmp`** — it fails with
`Error in fopenReadStream: failed to open locally with tail <name> for filename /tmp/...`
(plus `Leptonica Error in findFileFormat`), for both `/tmp/foo.png` and `/tmp/subdir/foo.png`,
with a zero exit code but no usable transcription. Verified directly:

```bash
tesseract /tmp/ocr_root_probe.png stdout -l chi_tra+eng --psm 6 tsv   # fopenReadStream error
tesseract fixture-post-menu.png stdout -l chi_tra+eng --psm 6 tsv     # works
```

The first implementation wrote a temporary PNG under `/tmp` and passed its path to
tesseract, so the positive self-test failed even though the fixture was valid. The fix (now
frozen) feeds the upscaled crop to the OCR engine through **stdin/stdout** instead:
`tesseract - stdout -l chi_tra+eng --psm 6 tsv`, with the PNG bytes piped in memory — no
temporary file is ever written to disk. Any future re-implementation must keep the
stdin/stdout mode, otherwise it will silently lose the OCR leg of the detection rule.

Note for Stage 05: the detector itself reads captures with Pillow, which *can* read `/tmp`
files (the attempt frames live in `/tmp`); only the tesseract file-path invocation is
affected, and the frozen tool never uses it.
