# Agent E2E acceptance test — Rev21 Vision-reader wave (`W6-AGENT-E2E`, plan.md §21.5)

Bounded, offline, re-runnable acceptance test (checks C1-C5) proving that the macOS-Vision
reader used by the v4 tool set is effective on the key fields (date title, photo count) and
that the frozen attempt-05 `75 != 57` blocker was a tesseract reader artifact, not a data
problem. Acceptance mode is **INTEGRATION — offline replay over the durable frozen frames**
(plan.md §21.6); it is never reported as live E2E.

Fences (must never be violated by anything in this directory):

- zero GUI input, zero screen capture, zero keyboard/AX writes, no menu item, no Save All,
  no chooser, no production download, zero formal-data writes;
- zero model/API calls — the runner is a deterministic orchestrator of local CLI tools;
- the four frozen attempt-05 frames and every v2/v3 tool, self-test, ledger and route
  artifact are read-only and byte-identical;
- C4 is `DEMONSTRATION_ONLY`: it never flips the frozen attempt-05 `TARGET_MISMATCH`
  verdict, never sets `CUA_ROUTE_DECISION`, and never authorizes any GUI input; the route
  stays stopped and owner-reserved;
- judgement rules are pinned; a failing result is never re-tagged or relaxed to pass.

## Layout (append-only)

```
evidence/20260916-route/agent-e2e/
  README.md                    this file
  runner/run_agent_e2e.py      the deterministic orchestrator
  attempt-NN/summary.json      one attempt summary (append-only; never rewritten)
  attempt-NN/raw/*             every raw artifact (tool stdout, helper stdout, OCR lines,
                               sweep evidence, preflight pins)
  attempt-NN/SHA256SUMS        `shasum -a 256` lines for every file under raw/, with
                               attempt-directory-relative paths
```

Attempt numbering starts at `attempt-01` for this wave. The runner refuses to open or
overwrite an existing attempt directory (exit 4) and never rewrites a previous attempt.
A failed attempt is preserved; the next run continues at the next unused number.

## Inputs (durable; re-hashed at test start)

| label | path | pinned SHA-256 |
|---|---|---|
| post | `evidence/20260917-vision-reader/frames/route5r_frame_post.jpg` | `4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3` |
| pre | `evidence/20260917-vision-reader/frames/route5r_frame_pre.jpg` | `3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531` |
| s1 | `evidence/20260917-vision-reader/frames/route5r_probe_crop_s1.png` | `aea53a0df8c4ef20488446dbccc42fa84ecd72c36aad71d42199f20b9e30f5c3` |
| s2 | `evidence/20260917-vision-reader/frames/route5r_probe_crop_s2.png` | `7b9d0a19323e0f7341d2ee9722415251195531dc067b773f231676729c63721b` |

A missing frame or a SHA mismatch stops the run immediately with `stop_reason` evidence
(summary written, non-zero exit) — never a silent continue. The same rule applies to the
plan pin (`plan.md` must hash to `466bda4a…`) and to a byte change of the frozen v3
`attempt-05/album-open-verify.json` (`ffa5d963…`).

## Checks (plan.md §21.5)

| ID | Check | Judgement (pinned; never relaxed) |
|---|---|---|
| C1 | post frame count read | v4 `locate_album_card` `count_digits_read` contains `57` (raw line + conf + bbox recorded) |
| C2 | determinism | per input, 5 repeats: v4 `locate_album_card` stdout JSON bytes identical (SHA-256) and helper stdout identical within the repeats |
| C3 | date title | v4 `locate_album_card` `title` is non-null on **both** pre and post frames (texts + bbox recorded) |
| C4 | frozen S5 replay (`DEMONSTRATION_ONLY`) | v4 `verify_album_open` on (pre, post) → `ALBUM_OPEN_VERIFIED`, exit 0, listed next to the frozen v3 result (`TARGET_MISMATCH`, exit 4, count read `75`) |
| C5 | s1/s2 crops | same rule as C1 on both crops |

Fixed arguments for every card-tool invocation: `--expect-start 2024/05/13
--expect-end 2024/05/17 --expect-count 57` (identical path strings across repeats).

C2 helper-stdout evidence uses, in priority order, the tool JSON's
`reader.calls[].stdout_sha256` sequences (the v4 reader's own calls) when present; when
they are absent the runner performs its own 5x direct helper invocation on the same input
(rendered at the reader's frame scale) and stores the raw stdout of each call. The runner
never assumes the `reader` field exists — absence is recorded, not fatal by itself.

**RV-30-4** — as part of the C1 evidence the runner stores a 3x/6x/10x **count sweep**
(full frame and count region; read value + confidence per scale; `ocr_digits_region` at
10x recorded as well), preferring the v4 reader's calls and falling back to the runner's
direct helper.

## Bounded loop (`REQ-VR-4`)

- Each check runs **exactly once per attempt**; the runner never retries a check inside an
  attempt.
- `failures_total` continues across attempts: the runner reads the newest prior
  `attempt-NN/summary.json` and carries its counter forward (attempt-01 starts at 0).
- At **5 cumulative failures** the loop stops: if the threshold was already reached before
  the attempt, the runner writes a stop-only attempt record (summary with
  `stop_reason = FAILURE_THRESHOLD_REACHED`, no check executed) and exits 3; if it is
  reached during the attempt, the remaining checks are recorded `NOT_RUN` and the same
  `stop_reason` is written. The owner is notified; no long retry.
- Every check result carries `CHECK_RESULT` (= its `status`) and the stop semantics are
  reported through `stop_reason` / `stop_phase` / `failures_total`.

## CLI

```
python3 runner/run_agent_e2e.py [--attempt NN] [--out DIR]
```

- `--attempt` accepts `01`, `1` or `attempt-01`; default is the next unused number.
- `--out` overrides the base directory (default: this directory).
- Exit codes: `0` PASS · `1` attempt executed, FAIL · `2` preflight stop (plan/frame/tool
  pin) · `3` bounded-loop stop · `4` usage error / attempt directory already exists.
- Run it with the interpreter that has Pillow 12.3.0 (`/opt/homebrew/bin/python3` here);
  all tool subprocesses are spawned with the same interpreter. The runner sends no input,
  makes no network/model call, and writes only inside the new attempt directory
  (plus transient helper builds/renders under the process temp directory).

## `summary.json` (required fields)

attempt id, timestamp, runner argv, python version, helper binary path/size/SHA (from the
v4 tool JSON's `reader.helper` record — the authoritative binary the tools used — when
present, else from the runner's own helper resolution), per check the raw command,
exit code and parsed verdict, the SHA-256 of every raw artifact, `failures_total`,
`stop_reason`, `inputs_sent: 0`, `ui_interaction: "none"`, the four frame SHAs used, and
the overall `result` (`PASS`/`FAIL`). C2 does not require the summary itself to be
byte-identical across runs (per handoff).

`SHA256SUMS` lists every file under `raw/` in `shasum -a 256` format with
attempt-directory-relative paths (e.g. `raw/c1_post_stdout.json`).

## Reproduce (Stage 05)

Stage 05 (fresh, `ACCEPTANCE_MODE=INTEGRATION`) consumes the next unused
`.agent/tasks/<TASK_ID>/e2e/attempt-NN/` and independently re-runs the same frozen inputs
with this runner (its own attempt slot, e.g. via `--out`; do not reuse an existing
attempt directory):

```
/opt/homebrew/bin/python3 evidence/20260916-route/agent-e2e/runner/run_agent_e2e.py
```

It then re-derives the tuple from the new `attempt-NN/summary.json` + `raw/` +
`SHA256SUMS` instead of trusting this directory's summary. A re-run must produce its own
new attempt directory; nothing in an existing attempt is ever edited.
