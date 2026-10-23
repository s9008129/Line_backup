# candidate/ — LINE album catalog diagnostic (fixed offline method)

Task: `TASK-20261010-catalog-diagnostic-continuity-replan`
Scope: everything here is task-local, read-only with respect to the OS. It never
captures the screen, never sends input and never downloads. All outputs use
exclusive creation; reruns need a new directory.

## Dependencies
- macOS with the system Swift toolchain (`swiftc`), Foundation, Vision, ImageIO,
  CoreGraphics.
- Python 3 standard library only (no Pillow/OpenCV, no pip installs).
- No network access is used.

## Build (task-local)

```
cd harness-development/catalog-diagnostic-continuity-replan-20261010
TMPDIR=$PWD/tmp swiftc -parse-as-library -O \
  -module-cache-path $PWD/module-cache \
  -o offline-validation/offline_vision candidate/offline_vision.swift
```

`run_offline_once.py` performs the same build itself into its run directory and
stores stdout/stderr under `offline-validation/logs/`.

## Commands

```
python3 -B candidate/catalog_diagnostic.py prepare-replay --source harness-development/catalog-diagnostic-20261010 --out harness-development/catalog-diagnostic-continuity-replan-20261010/replay
python3 -B candidate/catalog_diagnostic.py verify-packet --packet-root harness-development/catalog-diagnostic-continuity-replan-20261010 --out harness-development/catalog-diagnostic-continuity-replan-20261010/tmp/verify-packet-01
python3 -B candidate/catalog_diagnostic.py evaluate --mode replay --binding FILE --frame-manifest FILE --modern FILE --legacy FILE --previous FILE_OR_NONE --out NEW_DIRECTORY
python3 -B candidate/run_offline_once.py --task-root harness-development/catalog-diagnostic-continuity-replan-20261010
python3 -B -m unittest discover -s harness-development/catalog-diagnostic-continuity-replan-20261010/candidate -p 'test_catalog_diagnostic.py'
```

Swift subcommands:

```
offline_vision decode --input IMAGE --out NEW_DIRECTORY
offline_vision recognize --input IMAGE --profile PROFILE_JSON --profile-name NAME --roi ROI_JSON --out NEW_DIRECTORY
offline_vision check-fixture --input PNG --expect EXPECT_JSON
```

## What was actually run and observed

- `prepare-replay`: 43 byte-exact copies, source/copy hashes equal, no source drift.
- `verify-packet`: 63 records PASS, `plan-contract.json` == `handoff.json` bytes,
  handoff/spec/plan/review hash bindings PASS. This is byte binding only, not
  controller schema VALID (no applicable stage packet exists).
- `run_offline_once.py`: four-frame replay + R01-R19 in
  `offline-validation/` — see `offline-validation/results.json` for the recorded
  expected/actual/verdict of every case. R20 (six real live steps) is `NOT_RUN`:
  no live session was started because the same-candidate pre-live independent review
  had not passed and no fresh user-coordinated LINE foreground existed (the host CUA
  surface itself is available; see ../live/README.md).
- unittest: 29 stdlib unittest cases PASS (R02-R19 fixtures; fixtures are
  in-memory mutations only and never touch original images).

## Binding / frame manifest schemas (for `evaluate`)

`binding` (JSON):
- `mode`, `run_id`, `observation_id`, `width`, `height`
- `text_slot_guard` {x0,y0,x1,y1} — full text slots compared exactly (RGBA)
- `text_slots` (title / album_tab / notes_tab rects), `exclusions` (non-text rects)
- `indicator` { region, album_region, notes_region, album_tab_horizontal,
  notes_tab_horizontal, baseline_bbox, baseline_mask_sha256 }
- `list_viewport`, `candidate_hash`, `profile_hashes`, `decoder_hash`, `binding_hash`

`frame-manifest` (JSON):
- `mode`, `frame_id`, `run_id`, `observation_id`, `previous_frame_id`
- `source_artifact_sha256`, `width`, `height`
- `rgba` { path, decoded_rgba_sha256, source_sha256 }
- optional `capture_age_seconds` (live only; input eligibility requires <= 5),
  `safety_observation` (live only), `metadata` (previous-frame rows/qualified ids)

The decoded RGBA is produced by `offline_vision decode` so both the evaluator and
the OCR helper share one canonical RGBA8 sRGB top-left decode.

## Fixed OCR profiles (`profiles.json`)

| profile | api | correction | custom words | purpose |
|---|---|---|---|---|
| fixed-label-live | modern | true | 相簿, 記事本 | fixed tab-label profile |
| fixed-label-offline-comparison | modern | false | — | one declared offline comparison |
| identity-header-metadata | modern | false | — | identity/date/count main results |
| identity-header-metadata-legacy | legacy | false | — | diagnostic API comparison |

All profiles use `accurate`, `["zh-Hant","en-US"]`, automatic language detection
off, top 3 candidates requested. Missing candidates stay UNKNOWN; nothing is
invented, and no 相溥→相簿 substitution or confidence threshold is applied.

## Constraints (frozen by the reviewed plan)

- Historic three method attempts are preserved; the authorized additional slot is
  recorded in `results/attempt-ledger.json` and was consumed once.
- No live input is allowed from this candidate until an independent same-candidate
  pre-live review PASS (`results/pre-live-review.result.json`, currently
  `PENDING_INDEPENDENT_REVIEW` because this host has no native delegation).
- `full_collection_coverage` is always `NOT_ESTABLISHED`.
