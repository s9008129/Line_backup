# v4 tool self-tests — 16-case matrix for the macOS-Vision route tools

This directory holds the self-test matrix for the v4 route tools introduced by plan Rev21
§21.4 (the v3 verdict logic with the reader layer replaced by the macOS-native Vision
reader). The v3 tool set and its 13-case self-test stay frozen and untouched.

The four tools under test are pinned by relative path, not by an upward search:

- `../../v4/vision_reader.py` — the Vision reader module (helper resolution + word records)
- `../../v4/locate_album_card.py` — album-card metadata locator
- `../../v4/verify_album_open.py` — album-open verifier
- `../../v4/locate_album_ellipsis.py` — album-level ⋮ locator

`run_selftest.py` resolves `TOOLS` as `../../v4` relative to its own `__file__`; the v3
runner's "walk upwards until `locate_album_card.py` is found" convention is deliberately
not reused because it would resolve to the frozen v3 tools.

## Expectation sources (pinned)

- **Cases 1–13** re-express the frozen v3 matrix (`../v3/selftest-summary.json`,
  SHA-256 `17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324`) with the
  same synthetic fixture geometry and the same expected exit code / verdict literals.
  The two ellipsis control cases keep the v3 `click_point [300,47]` with ±2 tolerance.
  The runner re-hashes the v3 summary at run start and after the run; a mismatch is a
  failure (the pinned expectations must come from the frozen summary).
- **Cases 14–16** are the reader-layer cases required by plan Rev21 §21.4:

| # | Case | Expectation |
|---|---|---|
| 14 | `count_normalization` | a card fixture whose 10x count region contains `57張照片` (`digits()` normalizes to `57`) → exit 0, `ELIGIBLE`, `count_text: MATCH`, `count_digits_read` starting with `57` |
| 15 | `helper_unavailable_failclosed` | `VISION_OCR_BIN=/nonexistent/vision_ocr_v4_selftest` on the `card_ok` fixture → documented refusal `TARGET_TITLE_NOT_FOUND` exit 2, no traceback, tool JSON `reader.calls[0].outcome == "binary_missing"`, and no rebuild (fixed build-path binary SHA before == after) |
| 16 | `determinism_5x` | five identical runs of the `card_ok` argv → five byte-identical stdout JSON documents (one SHA-256); the five raw stdout copies are kept in `fixtures_dir` |

## Cases (16)

| Group | Cases |
|---|---|
| album-card locator (v3 literals) | `card_ok` / `card_notitle` / `card_count58` / `card_tight_margins` |
| album-open verifier (v3 literals) | `verify_open` / `verify_no_effect` / `verify_target_mismatch` / `verify_inconclusive` |
| album-level ellipsis locator (v3 literals) | `ellipsis_one_dot_control` / `ellipsis_ocr_derived_title` / `ellipsis_two_in_band` / `ellipsis_group_level_only` / `ellipsis_none` |
| reader layer (new) | `count_normalization` / `helper_unavailable_failclosed` / `determinism_5x` |

## How to re-run

```bash
/opt/homebrew/bin/python3 evidence/20260916-route/tools/selftest/v4/run_selftest.py
```

The runner prints the JSON summary and writes it next to itself (`selftest-summary.json`).
Exit code 0 when every case passes, 1 otherwise; 3 when the v4 tool set is incomplete
(the summary is not written in that case). Every case runs as a subprocess with the same
interpreter that runs the script. `VISION_OCR_BIN` is cleared for the default-path cases
so the v4 reader's own helper resolution is exercised; only the fail-closed case sets it
(to a nonexistent path). `PYTHONDONTWRITEBYTECODE=1` is set for the subprocesses (and the
runner itself does not write bytecode), so running the matrix leaves no `__pycache__`
inside the frozen/versioned tool directories.

## Fixtures

All fixtures are synthetic frames drawn pixel by pixel by `run_selftest.py` into a fresh
temporary directory (`fixtures_dir` in the summary): no screenshot, no GUI, no input
event, no real screen content. The v3 geometry is reused (327x643 window, dark card row
at y≈430 with light text, light dots at x≈300). The count-normalization fixture draws
`57張照片` with a system CJK font (PingFang preferred; on this host PingFang is absent and
`/System/Library/Fonts/Hiragino Sans GB.ttc` is used — recorded in `fixture_notes`); if
no CJK font can be loaded, filled blocks stand in for the CJK glyphs while the digits
`57` stay readable as the count-region prefix.

## Dependencies

- `/opt/homebrew/bin/python3` with Pillow (fixture rendering and the tools themselves).
- The Vision helper binary is resolved by the v4 reader at run time: `$VISION_OCR_BIN` if
  set, else built once from the frozen Swift source `../vision/vision_ocr.swift` with
  `swiftc -O`. No third-party dependency is used and the helper source is never edited.
