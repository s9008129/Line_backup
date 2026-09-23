# Supplemental test - historical-coordinate injection (attempt-05 negative matrix)

Role: **supplemental, offline, zero-GUI** negative test that keeps a direct
fixture for the negative-matrix item *historical-coordinate injection* while
leaving the reviewed v8 selftest binding byte-exact.

Context: case `c19-historical-coordinate-injection` was authored pre-freeze in
`tools/v8/selftest/run_selftest.py`, then withdrawn before freeze so that the
frozen script/results bytes equal exactly what the Rev27c plan and the two
fresh reviews bind (`run_selftest.py` sha `c94fc407...`, `results.json` sha
`943f2939...`, 43 cases). Its fixture
`tools/v8/selftest/fixtures/geo-a05-injected-history.json` (sha `842cb933...`)
was left on disk (zero-cleanup rule) and is reused by this supplemental case.
The withdrawn case's scratch output `tools/v8/selftest/out/c19-historical-coordinate-injection.json`
(sha `ab4c577a...`) was likewise left in place; note that its bytes are exactly
what this supplemental case reproduces as `out/injected-run-1.json`
(`ab4c577a...`), so the frozen selftest directory stays internally consistent
without any deletion. The clean control run `out/clean-control.json` is
byte-identical to the reviewed selftest's `c01` stdout (`c92f4151...`).

What it does: runs the frozen v8 CLI (sha `c5ad4686...`) on the attempt-05 menu
frame

1. with the clean geometry fixture `geo-a05.json` (control), and
2. twice with the decoy-injected geometry fixture
   `geo-a05-injected-history.json` (historical v5 ellipsis window-local point
   `[304, 50]`, historical v7 candidate frame px `[1313.5, 332.333]`,
   app-local fallback `[42, 988]`),

then asserts: ELIGIBLE with exactly one candidate, the candidate is identical
to the clean-fixture decision, equals the current-frame-derived expectation
`frame px [1297.333, 351.5] / screen pt [648.667, 175.75] / app-local
[319.667, 134.75]`, differs from every decoy value, and the injected run is
deterministic (x2 byte-identical stdout).

Boundary: this artifact is **not** part of the reviewed binding; it cannot
approve, weaken or replace any gate, and an ELIGIBLE verdict here is not a
live click authorization. No GUI input, no LINE interaction, no downloads, no
staging, no destination writes.

Run: `/opt/homebrew/bin/python3 run_injection_case.py` (writes `out/` and
`results.json`).
