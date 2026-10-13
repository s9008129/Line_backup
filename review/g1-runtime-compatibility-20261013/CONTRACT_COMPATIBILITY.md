# Contract Compatibility

`frameSupportVerifyGrant` chooses one of two compile-time identity profiles by exact equality over task ID, contract path, contract SHA-256, and artifact directory. The profile constructor is private; the selector and read-only fields expose only the two reviewed identities. No grant payload can add a profile or provide its own expected values.

| Profile | Task ID | Contract SHA-256 | Artifact directory | Task modules |
|---|---|---|---|---:|
| Legacy live-grounding-03 | `TASK-20261010-line-v3-live-e2e` | `d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219` | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03` | 4 |
| Original minimal-live-08 | `TASK-4acb4326ea2a4c50ace6f333f2de8751` | `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc` | `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08` | 10 |

The legacy profile preserves the existing task/contract/artifact binding and the pre-existing safe `harness-development/` grant-path acceptance; it is not narrowed to two filenames. The prior legacy authorization and runtime checks remain in that branch. The legacy path does not acquire a new mandatory exact `task_modules` membership check.

The ML08 identity recognizes only `live-grant-1.json` and `live-grant-2.json`, then refuses with `minimal-live-08 authority is unbound` before applying legacy authorization rules. The existing canonical authorization and CRITICAL Plan Review evidence binding for the original Task have not been verified, and no authorization file path is guessed. The source patch therefore records the exact identity but does not admit an ML08 grant. It does not relax required grant keys, non-fixture/runtime/binary/sensor checks for the legacy branch.

No grant or runtime binding was created, edited, read as an authority record, or supplied to the candidate. No canonical Q authorization evidence was validated. The existing Q runner’s static runtime gate independently requires exactly its ten task modules; the legacy runner requires its four. The code change does not loosen those lists, derive module membership from an arbitrary artifact directory, or authorize fixture mode.

The `FrameSupportGrantProfileTests` cover each exact tuple, safe legacy task-local paths, exact ML08 grant filenames, and cross-mixed/unlisted tuples. They did not run: the single isolated Swift build/test failed in unrelated copied native-observation code before test execution. The final helper and CLI changes are uncompiled.

| Status | Result |
|---|---|
| `CODE_PATCHED` | YES — isolated candidate only |
| `SOURCE_VALIDATED` | PARTIAL — source identity and bounded diff checked; Swift integration uncompiled |
| `OFFLINE_BUILD_PASS` | NO — the sole authorized build failed before tests |
| `RUNTIME_BOUND` | NO |
| `LIVE_PRODUCER_PASS` | NO |
| `GUI_AUTHORIZED` | NO |
