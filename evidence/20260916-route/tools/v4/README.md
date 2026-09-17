# v4 route tools — macOS Vision reader (Rev21)

Read-only route-verification tools whose OCR reader is the macOS-native Vision
framework (`VNRecognizeTextRequest`). For Rev21 and after, this set is the official
reader of the official chain; the frozen v3 files (`../locate_album_card.py`
`500fcadb…`, `../verify_album_open.py` `80504262…`, `../locate_album_ellipsis.py`
`60e3120a…`) remain byte-identical history. The v4 set is self-contained and never
imports a v3 module.

| File | Role |
|---|---|
| `vision_reader.py` | Vision reader module (no CLI): image → v3-shaped word records + outcome record |
| `locate_album_card.py` | album-card metadata locator (S3): v3 logic + Vision reader |
| `verify_album_open.py` | album-open verifier (S5): v3 logic + Vision reader |
| `locate_album_ellipsis.py` | album-level ⋮ locator (S6): v3 logic + Vision reader |

## Usage

Same CLI, verdicts and exit codes as the v3 tools; each tool's JSON (stdout and
`--out`) additionally carries one `"reader"` field.

```bash
/opt/homebrew/bin/python3 v4/locate_album_card.py <frame> \
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 [--out x.json]
/opt/homebrew/bin/python3 v4/verify_album_open.py <pre> <post> \
    --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 [--out x.json]
/opt/homebrew/bin/python3 v4/locate_album_ellipsis.py <frame> \
    --expect-start 2024/05/13 --expect-end 2024/05/17 [--title-bbox x0,y0,x1,y1] [--out x.json]
```

Interpreter: `/opt/homebrew/bin/python3` (Pillow required; `/usr/bin/python3` has no
PIL). Read-only analysis: no GUI input, no menu item, no chooser, no keyboard/AX
write, no capture, no download, no formal config/state/run-log/photos write.

## Reader contract

- Input: a PIL image plus a scale. The reader applies the `Image.LANCZOS` upscale by
  that scale to a temporary PNG under the process temporary directory and feeds that
  file to the helper. Scales are unchanged from v3: 3x for frame reads, 10x for the
  count region. The temporary render path never appears in any JSON.
- Helper resolution: `$VISION_OCR_BIN` when set — used as-is, **never rebuilt even
  when invalid**; otherwise `<tempdir>/vision_ocr_v4_build/vision_ocr`, built exactly
  once from the frozen Swift source `../vision/vision_ocr.swift` (SHA-256
  `4fc9fa2b…`) with `swiftc -O` when the binary or its `source.sha256` sidecar is
  missing/stale. The build is atomic (`vision_ocr.tmp<pid>` → `os.replace`) and the
  sidecar contains the frozen source SHA; an existing binary with a matching sidecar
  is reused unmodified.
- Parse: stdout carries one line per observation,
  `px[x0,y0,x1,y1]\tconf=NN\tTEXT`, split with `split("\t", 2)`; TEXT is kept
  verbatim (interior spaces/tabs preserved). Vision observations are line-level: the
  helper's own line boxes are the token unit and no re-tokenization is performed.
  Text is never rewritten — no case folding, no width normalization, and 禎 (U+798E)
  / 楨 (U+6968) are never merged.
- Output: v3-shaped records `{text, conf, x, y, w, h}` in original-frame pixels:
  `x=x0/scale`, `y=y0/scale`, `w=(x1-x0)/scale`, `h=(y1-y0)/scale` (same formula as
  v3). `conf` is recorded evidence and is never a gate.
- `psm` is accepted for v3 signature parity in `_tsv_rows`/`ocr_words`/
  `ocr_digits_region` and has no Vision equivalent (unused).

## Helper outcome record (`"reader"`)

```json
"reader": {
 "helper": {"resolved_from": "env"|"build_path", "binary_path": "…",
            "binary_sha256": "…"|null, "binary_bytes": n|null,
            "source_sha256": "4fc9fa2b…"},
 "calls": [{"scale": n, "outcome": "…", "exit_code": n|null,
            "stderr_excerpt": "…", "stdout_sha256": "…",
            "stdout_bytes": n, "lines_parsed": n}, …]
}
```

`calls` is appended in call order (frame read then, when the title was found, the
count-region read). `helper` is `null` and `calls` empty when a run refused before
any OCR (missing frame, size mismatch). `resolved_from` is only `env` or
`build_path` — never `built`/`cached` — so the record is identical on the first
(building) and every later run.

Parse order and the fail-closed outcomes (any failure returns empty words, and the
tool then follows its frozen v3 refusal path — never a crash, never a guessed value):

| Outcome | Condition |
|---|---|
| `ok` | helper exit 0; at least one valid line parsed. Empty stdout is also `ok` with 0 words |
| `binary_missing` | resolved helper missing or not executable (`$VISION_OCR_BIN` invalid → no rebuild) |
| `build_failed` | fixed-path build was needed and failed (frozen source missing/sha mismatch, swiftc error, sidecar write error) |
| `nonzero_exit` | helper exit ≠ 0 (2 usage, 3 image load failure, 4 recognition failure) |
| `unparsable` | helper exit 0, stdout non-empty, no valid `px[…]` + `conf=…` line with non-empty TEXT |
| `timeout` | no exit within 60 s → kill (no pipe drain; a helper grandchild cannot stall the reader); `exit_code` null |

Exit 2/3/4 or a missing helper = failure; empty stdout = success with 0 words; a
line yields a word only when `px[x0,y0,x1,y1]` and `conf=NN` parse and TEXT is
non-empty. `stderr_excerpt` is `""` on success and ≤200 chars otherwise; for
`binary_missing`/`build_failed` it carries the reader's short reason (there is no
process stderr), and `timeout` records `""` because the pipes are not drained. A
render-stage `OSError` (e.g. temporary-file failure) is recorded as `unparsable`
with a `render error: …` excerpt; it never raises out of the reader.

## Determinism (C2) scope

- In scope: for a given input, the helper's stdout bytes and the v4 tools' JSON
  bytes must be identical across repeats. The `"reader"` field is part of that
  identity (no timestamps, no process-unique render paths; the only path recorded is
  the env value or the fixed build path).
- Out of scope: the agent-attempt `summary.json` (it records timestamps/argv by
  design), and the helper binary's own bytes (`swiftc` output is not
  byte-deterministic; equivalence is shown by identical stdout on the same input).

## v4 = v3 logic + reader layer only

Diffing v4 against the frozen v3 files shows exactly these hunks (nothing else):

- `locate_album_card.py`: docstring +1 line; tesseract-only imports (`io`,
  `subprocess`) dropped and `importlib.util` added for the sibling loader;
  `_load_sibling` + `vision_reader = _load_sibling("vision_reader")` added;
  `_tsv_rows` body = `return vision_reader.read_words(image, scale)`;
  `ocr_words`/`ocr_digits_region` call `_tsv_rows` with the unscaled/cropped image
  (the LANCZOS upscale moved into the reader; call sites and `or []` unchanged);
  `emit` +1 line (`result["reader"] = vision_reader.record()`).
- `verify_album_open.py` / `locate_album_ellipsis.py`: docstring +1 line;
  `emit` +1 line (`result["reader"] = card.vision_reader.record()`).
  Everything else is byte-identical, including `_load_sibling`, the sibling
  `locate_album_card` load, every threshold, verdict, exit code, refusal path and
  geometric parameter.

Known seam notes: `_tsv_rows` now receives the unscaled image (the 3x/10x LANCZOS
factors are unchanged) and returns `[]` instead of `None` on failure — the callers'
`or []` makes both identical.

## Phase 0 baseline field `byte_identical_to_recorded` (semantics)

`evidence/20260917-vision-reader/phase0/baseline.json` is append-only committed
evidence (commit `adf1829`) and is never rewritten. Its
`helper_rebuild.byte_identical_to_recorded` recorded a *that-day* observation:
`sha256(/tmp/vision_ocr)` equalled the historical volatile-binary SHA `f54628e8…`.
It is not a reproducibility claim: `swiftc` output is not byte-deterministic, and
the helper binary is not the acceptance key. Later re-verification keys on the
durable frame copies (`evidence/20260917-vision-reader/frames/` + `manifest.json`)
and the recorded raw-stdout SHAs (post `5c86dda8…`, pre `07e3e156…`, s1
`561bb131…`, s2 `abf9d75e…`) — never on volatile `/tmp` content.
