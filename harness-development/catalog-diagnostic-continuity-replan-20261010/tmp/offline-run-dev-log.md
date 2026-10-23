# Offline runner development log (setup failures, not method attempts)

These were candidate wiring/typing defects found while building the offline runner.
They are recorded so the single authorized method verification is not confused
with harness plumbing. The OCR method itself (profiles, ROI, parser, thresholds,
movement policy) was never changed after the first full method run.

1. run 1: `decide_frame` compared `binding["list_viewport"]` as a dict and the
   indicator spec as raw dicts -> TypeError. Fixed by normalizing rects in the
   evaluator (no semantics change: same rectangles, dict-or-tuple accepted).
2. run 2: the R06 in-memory live fixture omitted `frame["rgba"]["source_sha256"]`
   -> KeyError. Fixed by adding the real `source_sha256` field to the fixture.
3. run 3 (authorized fixed method verification): see offline-validation/results.json.

Each run regenerated OCR because the runner is atomic; the OCR method outputs are
compared across runs via `ocr/*/*.sha256` recorded hashes to show the method was
not tuned.
