# Rev25 Phase 1 — 零 GUI 基線完整性

- **Status:** PASS
- **GUI_INPUT_COUNT:** `0`
- **Scope:** fresh read-only recomputation only; no LINE GUI, no formal-state write, no destination write.

## Frozen source and baseline

- Source record: v1.1 exact match `True`; legacy v1 exact match `False`.
- Requested group: `旻謙允禎成長日記`; codepoint `U+798E` present and `U+6968` absent; normalization `NONE`.
- Destination: `57` regular files, `17,924,900` bytes.
- Current baseline: `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5` (`19,005` bytes).
- Frozen baseline: same SHA and size; result `UNCHANGED`.

## Tool and replay checks

- Fresh v5 selftest: `21` cases, `0` failed, `PASS`.
- Frozen frame: `route5r_frame_post.jpg`, SHA-256 `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3`.
- Fresh v5 replay: `ELIGIBLE`, dots `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]`, click `[304,50]`.
- Fresh v4 same-frame replay: `NO_ELLIPSIS_FOUND` (exit `3`).
- Stage05 attempt-08 fresh internal consistency: `PASS`; its recorded end state has `gui_inputs: 0`, and its 15/15 anchor rehash has `mismatches: 0`.

## Evidence files

- `current.json` and `current-summary.json` are the fresh baseline readback.
- `source-fact-rederive.json` is the fresh exact-equality source check.
- `stage05-consistency.json` is the fresh consistency check over the historical Stage05 evidence.
- `v5-selftest.json`, `v5-offline-replay.json`, and `v4-same-frame-replay.json` are fresh outputs in this append-only attempt root.
