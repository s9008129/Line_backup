# Computer Use from Codex CLI — user-requested live proof (2026-09-16)

Purpose: answer the user's question "can Codex CLI actually use Computer Use?" with direct,
reproducible evidence, and record exactly which GUI actions were consumed while doing it.

This file is an evidence record, not a production authorization and not a Stage-03 handoff.

## Environment at the time of the proof

| Item | Value |
|---|---|
| Harness | Codex CLI (TUI), `cli_version 0.154.0`, interactive session PID 23438, started `Wed Sep 16 14:12:00 2026` |
| Model | `deepseek-v4.1-flash` (BYOK) |
| Provider | `ollama_cloud` (`https://ollama.com/v1`, `wire_api = "responses"`, `env_key = "OLLAMA_API_KEY"`, `requires_openai_auth = false`) |
| Reasoning | `model_reasoning_effort = "max"` |
| Computer Use | plugin `unified-computer-use@openai-bundled` version `26.908.70816`, MCP server `cua_repl`, `enabled: true` |
| Target app | LINE, bundle id `jp.naver.line.mac` |

The BYOK flags were passed on the CLI command line (`-m` + `-c` overrides); `~/.codex/config.toml`
still defaults to `model = "gpt-5.6-luna"` and contains no `[model_providers.*]` section.

## Actions actually performed (complete list)

1. `await cua.rewriteDocumentation()` — read the runtime API documentation (no UI effect).
2. `const line = await cua.getApp("jp.naver.line.mac")` — bound the LINE window and read its
   accessibility state (read-only).
3. `await line.performSecondaryAction(0, "Raise")` — **one** accessibility "Raise" action on the
   window element, to bring the LINE window to the foreground. This is the only state-changing GUI
   action used. "Raise" is an action the element itself exposes (`0 標準視窗 LINE, Secondary Actions: Raise`).
4. `await line.getScreenshot({ emit: false })` — **one** window screenshot, saved to disk and also
   emitted into the conversation so the user can see it.
5. Local image processing only (copy/rename/upscale/crop with `sips` and `ffmpeg`).

Not performed: no click, no typing, no keyboard shortcut, no context-menu/ellipsis input, no
"Save All", no download chooser, no LINE state change, no product config/state/run-log write,
no download, no re-download. The album Save-All transaction was never entered.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `line-window-raised-20260916T1839+0800.jpg` (original capture; the CUA runtime returns JPEG bytes) | 113927 | `9e6aeaf01161faad3effc7eb400bf9589f7e3fc2437c5d06f5b751a3b2e565b0` |
| `line-window-raised-2x.jpg` (2x upscale, for readability) | 253822 | `8fc55aa08faeaeb53b7336b2fced6ef99809aa864d5b9f7c83ac49e4bd8038b3` |
| `crop-header-3x.jpg` (chat header, 3x) | 15117 | `04b35c35ddf0286f0f41fd9ff07c5450c30f10798a5376e8fb60bbd06abaa41f` |
| `crop-sidebar-3x.jpg` (chat-list row, 3x) | 15534 | `80f44aa733e3fdbf67d3060763e699e113ca64b1e0cfdea8d9ecf7c0d577b919` |
| `byok-image-path-probe.log` (isolation probe, copied from `/tmp/byok-image-probe/probe.log`) | 20595 | `1b7d4716e9e0f480df438b8f71b972eaa1d9820b0d52df84c4e6156da63d35a3` |
| `byok-image-path-rollout-extract.txt` | 3175 | `27a421465efb3ab238330c78c149cf870bccb05d240ea56396d10e42c6d025a9` |

## What this proves

1. **Computer Use works from Codex CLI, including on a BYOK model.** In this session the model is
   `deepseek-v4.1-flash` served through Ollama Cloud, and CUA calls returned `status: "completed"`
   (`getApp` read the real LINE accessibility tree; `performSecondaryAction("Raise")` and
   `getScreenshot()` both succeeded and produced the image above).
2. **The screenshot path reaches the model provider.** Images produced by an MCP tool are sent as
   Responses-API `input_image` content items (base64 data URL). An isolated probe on the same
   provider concluded `IMAGE_PATH_WORKS`: after both a `view_image` result and a
   `node_repl.emitImage` result were materialized as `input_image` items, every following upstream
   request completed (model reasoning continued, token accounting continued, 0 error events,
   0 aborted turns). Residual uncertainty: provider-side raw wire logs were not inspected, so
   "accepted" means "not rejected and the conversation continued"; whether the provider truly
   parsed the pixels is UNKNOWN.
3. **The real model-side gate is model metadata, not the provider name.** No model/provider gate
   exists in the plugin config or the CLI binary; the relevant gates are the model's
   `input_modalities` (an image-unsupported model gets `<image content omitted because you do not
   support image input>`) and `node_repl_disabled`. Unknown/BYOK models fall back to fallback model
   metadata; every catalog present on this machine (`~/.codex/models_cache.json`, bundled catalog)
   declares `text,image`.

## Observation worth preserving (NOT an identity proof)

The captured window shows the LINE group title rendered as **旻謙允禎成長日記 (3)** — i.e. the
character **禎** (U+798E), which matches the user's requested string and differs from the persisted
formal config/state key **旻謙允楨成長日記** (**楨**, U+6968). See `crop-header-3x.jpg` and
`crop-sidebar-3x.jpg`.

Status: `[OBSERVED]` visual text only. Per the skill/plan trust model this is *supporting* evidence,
not an authoritative exact source join, and it must not be used to merge, normalise or rewrite the
two strings. It becomes usable only together with one precise preserved user fact (exact question,
exact answer, who/when, and this evidence's SHA-256).

## Privacy

These files contain private LINE conversation content from the user's own machine. They are kept
locally under the work repository only, and were emitted to the model provider in use for this
session (Ollama Cloud) as part of the user-requested demonstration.
