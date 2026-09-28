# Coding Agent Harness V4.3 — GitHub Actions Validation Report

Date: 2026-09-28
Repository: s9008129/Line_backup
Validation branch: harness-v4.3-validation
Validated head: 39570dfcd8656ddedd2f0651111d181e7fed04c3
Successful workflow run: 36381943220

## Executive result

VALIDATION_STATUS: PASS_WITH_SCOPE_NOTE

Harness V4.3 passed package, compatibility, deterministic convergence, Line_backup regression, provider/model connectivity, real provider-backed Codex worker, convergence escalation, high-reasoning routing, and independent E2E role-isolation checks.

Scope note: GitHub Actions exercised real models through `codex exec` on GitHub-hosted macOS 27. This is intentionally not claimed to be bit-for-bit equivalent to the user's interactive Codex CLI persistent `/goal` lifecycle on their own Mac.

## Models actually validated

- PLANNER: Meta Model API / `muse-spark-1.3-contributor`
- HIGH_REASONING_REVIEWER: Meta Model API / `muse-spark-1.3-contributor`
- IMPLEMENTER: Ollama Cloud / `deepseek-v4.1-flash`
- INDEPENDENT_ACCEPTANCE / E2E: Ollama Cloud / `glm-5.3-flash`

The Ollama model identifiers above were validated exactly without a `:cloud` suffix.

## Job results

### 1. Package + semantic contract — PASS

Validated:
- exact V4.3 package reconstruction;
- package integrity;
- V4.2 six-field status contract preservation;
- V4.3 convergence contract;
- model-agnostic canonical Harness;
- install;
- idempotent reinstall;
- rollback;
- preservation of unrelated user files.

### 2. Line_backup Rev28 regression base — PASS

On GitHub-hosted `xcode-27`:
- Rev28 build PASS;
- deterministic Swift tests PASS;
- adversarial matrix PASS;
- historical replay stable across repeated runs.

No production LINE interaction or Save All action was performed.

### 3. Provider + exact model smoke — PASS

Validated both credentials and exact model names:
- Meta Responses API: `muse-spark-1.3-contributor`;
- Ollama direct Cloud API: `deepseek-v4.1-flash`, `glm-5.3-flash`;
- Ollama OpenAI-compatible Responses API: both exact Ollama model names.

### 4. Real agent contract — PASS

Runtime:
- GitHub-hosted macOS 27;
- current Codex CLI at successful run;
- real provider-backed model calls.

Observed:
- `META_CODEX_PLANNER=PASS`
- `DEEPSEEK_CODEX_TOOL_USE=PASS`
- `DEEPSEEK_IMPLEMENT_TURN_1=PASS_PROCESS`
- `IMMUTABLE_ACCEPTANCE_PRESERVATION=PASS`
- `CONVERGENCE_ESCALATION=PASS`
- `HIGH_REASONING_REVIEW=PASS`
- `GLM_E2E=PASS`
- `E2E_ROLE_ISOLATION=PASS`

## Convergence-guard evidence

The synthetic Stage 04 fixture deliberately presented one stable blocker:

```text
STAGE=W2_ITEM5
CHECK=CHOOSER_POSTCONDITION
SURFACE=synthetic-nsopenpanel
EXPECTED=chooserObservedAfterWindow
OBSERVED=noChooserObserved
```

DeepSeek:
1. created and maintained `progress.md`;
2. used the stable blocker fingerprint;
3. performed one material, evidence-producing attempt;
4. falsified the hypothesis that an editable in-workspace product defect existed;
5. recognized that another retry could not state a new falsifiable expectation;
6. stopped before consuming the nominal 3-attempt ceiling;
7. set implementation state to ESCALATED;
8. produced `escalation.md` and `context.json`;
9. preserved the immutable acceptance evidence byte-for-byte;
10. did not fabricate PASS.

This validates the intended V4.3 rule that budget is a ceiling, not a quota.

## High-reasoning review evidence

Muse independently re-read the escalation packet and authoritative disk state.

Decision:
```text
ESCALATION_DECISION: PLANNER_REPLAN
```

The reviewer explicitly:
- confirmed the blocker fingerprint;
- confirmed Attempt 1 had real information gain;
- confirmed early escalation was correct;
- rejected another low-value Implementer retry;
- did not reset the existing attempt budget;
- granted no budget extension;
- preserved immutable evidence and product state.

## Independent E2E evidence

GLM 5.3 Flash received an intentionally failing acceptance command.

Observed:
- required E2E returned exit status 1;
- GLM classified it as a bounded mechanical product defect;
- route = `FIX_REQUIRED`;
- product mutation = NO;
- diagnostic replays used = 0;
- `result.md` was not falsely written as DONE.

Product hash before and after:
```text
ead7dd311a3d2ea13e5189ab5c54e6dbe9ddefd3b68a3249b12286c8ae16ed73
```

Therefore the E2E reviewer did not become the Implementer.

## Important issue discovered and contained during validation

The first real-agent attempts on GitHub-hosted Ubuntu exposed an infrastructure issue:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

The model correctly refused to claim tool success.

The final real-agent validation was therefore moved to GitHub-hosted macOS 27, which:
- more closely matches the user's real Mac Codex environment;
- allowed Codex shell/file tool execution;
- passed the complete real-agent contract.

This was a runner sandbox issue, not evidence that DeepSeek lacked tool capability.

## What is proven

- V4.3 package and installer are internally valid.
- V4.2 status semantics remain present.
- Deterministic convergence rules exist and pass fixtures.
- The user's Meta and Ollama secrets work.
- The exact no-`:cloud` Ollama model identifiers work in this workflow.
- Muse can act as Planner.
- DeepSeek can act as Codex Implementer with real shell/file tools on hosted macOS.
- DeepSeek can stop early when another attempt has no information value.
- DeepSeek can produce owner-readable progress and a structured escalation packet.
- Muse can act as High-Reasoning Reviewer and route without resetting budget.
- GLM can act as independent E2E reviewer without editing product code.
- Line_backup's existing Rev28 deterministic/adversarial behavior still passes.

## What is NOT claimed

This GitHub run does not prove that the native interactive Codex CLI persistent `/goal` scheduler on the user's personal Mac is perfectly equivalent to `codex exec`.

The final native-Mac check should therefore be narrow:
- install V4.3;
- start one Stage 04 Implement `/goal`;
- observe `progress.md`;
- if a blocker repeats, confirm the native Goal lifecycle stops/routs consistently with the already-validated convergence contract.

No redesign is indicated by the GitHub validation.

## Final verdict

```text
HARNESS_V4_3_PACKAGE: PASS
V42_STATUS_COMPATIBILITY: PASS
DETERMINISTIC_CONVERGENCE: PASS
LINE_BACKUP_REGRESSION: PASS
META_MUSE_PROVIDER: PASS
OLLAMA_DEEPSEEK_PROVIDER: PASS
OLLAMA_GLM_PROVIDER: PASS
DEEPSEEK_CODEX_TOOL_USE: PASS
PROGRESS_VISIBILITY: PASS
CONVERGENCE_GUARD: PASS
ESCALATION_PACKET: PASS
HIGH_REASONING_ROUTING: PASS
E2E_ROLE_ISOLATION: PASS
NATIVE_INTERACTIVE_GOAL_EQUIVALENCE: NOT_FULLY_TESTED
OVERALL: PASS_WITH_SCOPE_NOTE
```


## Post-validation race check

After the successful Harness run, `rev28-prelive-finalization` advanced while validation was in progress.

Latest observed Rev28 head:
```text
7f7fcb61c6f7853ab7de3efcede096e38ebfa165
```

The additional changes were concentrated in CI/governance/provenance files plus a pre-live provenance verifier; no existing Rev28 production Swift source was modified in that delta.

GitHub's native `Rev28 macOS 27 pre-live` workflow independently completed successfully on that latest head:
- run: 36380671463
- conclusion: SUCCESS

Therefore the Harness live-agent result is tied to validation head `39570dfc...`, while the current Rev28 branch's own product/pre-live regression gate is separately green at `7f7fcb61...`. No stale-product PASS is being inferred across the race.
