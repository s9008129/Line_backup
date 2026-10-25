# Rev28 macOS Capability Matrix

This matrix separates **real-Mac production authority** from **GitHub-hosted pre-live evidence**.

Updated 2026-10-04: the table below describes historical observations, not a new
probe of current permissions, LINE, hosted runners or baseline data. The current
local repair's build/test/replay evidence lives in
`harness-development/rev28-fresh-repair/TASK-d34338d2680f4814aabd6841ef094c14`.
Native composition is implemented and reachable by both CLI commands. Missing
current calibration and popup/occlusion proof still block production eligibility.

| Capability | Historical user Mac evidence | Historical GitHub `xcode-27` evidence | Authority / treatment |
|---|---|---|---|
| macOS | macOS 27.0 | macOS 27.0 (26A428) | both relevant |
| Swift/Xcode | Swift 6.3.3 / Xcode-provided SDK | Swift 6.4 / Xcode 27.0 (27A266a) / macOS 27 SDK | CI adds portability coverage |
| Accessibility trust | PASS | `AXIsProcessTrusted=true` | required for headed harness |
| Screen capture permission | PASS | `CGPreflightScreenCaptureAccess=true` | required for headed harness |
| Quartz post-event permission | PASS | `CGPreflightPostEventAccess=true` | required for headed harness |
| ScreenCaptureKit inventory | PASS | PASS, hosted run observed 5 windows / 1 display | pre-live capable |
| ScreenCaptureKit capture geometry | W2 calibrated/frozen | build/contracts exercised; SCK available | historical calibration is not bound to the current composer; Phase A v2 reports UNKNOWN |
| Vision modern OCR | PASS: exact `儲存全部` and `57張照片` | FAIL: `unknownError` | real Mac remains production authority |
| Vision legacy parity | diagnostic only | FAIL: same `unknownError` | supports hosted-runtime limitation classification |
| Quartz event construction/routing | W2 PASS | TCC + deterministic/harness coverage | final LINE routing only real Mac |
| Native NSOpenPanel | W2 chooser PASS | PASS | hosted headed environment usable |
| W2 postcondition item 5 | formerly PARTIAL locally | PASS on native NSOpenPanel | closes synthetic timing blocker; retain real-Mac live verification |
| Postcondition outcomes | contract exists | `within=chooserVerified`; `timeout=noChooserObserved`; `late=chooserObservedAfterWindow`; zero monitor posts | CI evidence |
| 20-sample panel latency | local partial history | PASS; hosted max observed ~59.09 ms in successful run | supports reviewed 8 s / 15 s bounds; does not widen them |
| Structural locators | historical Python v5-v8 | native Swift album/detail/ellipsis/Save-All contracts + replay | live candidates always fresh-frame bound |
| Historical replay | historical artifacts | 20 reviewed fixtures SHA-bound, run twice, byte-identical | deterministic pre-live gate |
| Transaction state/budgets | scaffolding | Swift policy + regression tests | pre-live gate |
| Hash-chained crash resume | W2 fixture PASS | regression coverage | stable goal slot/run/source bindings preserved; verified continuation re-observes current state |
| Staging exact verifier | historical scripts | native Swift exact predicate + named terminal states | final data only real Mac |
| G01-G22 + X01-X03 | planned | 25/25 tests, run twice on successful macOS 27 CI | pre-live gate |
| Real LINE account/session | available only on user Mac | unavailable | **real Mac only** |
| Target group/album current state | real Mac only | unavailable | **real Mac only** |
| Actual LINE Save All semantics | real Mac only | synthetic NSOpenPanel only | **real Mac only** |
| Actual 57-file download | real Mac only | not reproducible | **real Mac only** |
| Accepted baseline path + mtimes + digests | real Mac filesystem | unavailable | **real Mac only** |
| Stage-05 disk recomputation | after live transaction | unavailable | **real Mac only** |

## Hosted Vision limitation

In the recorded GitHub-hosted macOS 27 run, the same synthetic OCR fixtures failed with `unknownError` using both:

- production Swift `RecognizeTextRequest`, and
- diagnostic legacy `VNRecognizeTextRequest`.

The capability probe simultaneously reports Accessibility, screen capture, post-event and ScreenCaptureKit success. Therefore the CI workflow treats Vision as a separately reported runtime limitation and does **not** skip or weaken the production OCR contract. The real Mac's executable-context Vision evidence remains required for production.

## CI evidence discipline

CI copies reviewed frozen harness inputs into `$RUNNER_TEMP`, writes all new calibration output into an ephemeral evidence root and uploads it as an Actions artifact. It never rewrites canonical repository evidence.

Deterministic replay output contains no wall-clock or workspace-specific paths, allowing byte-for-byte rerun comparison.

## Current production conclusion

The fresh local identity repair rechecks process/signing/AX facts after capture,
retains one explicit session CG snapshot for both identity and bundle, and
rejects conflicting or invalid SCK/CG target geometry. Target signing lookup
failure is unknown; caller signing information is never a substitute. Local
regressions exercise these boundaries without LINE interaction. Existing AX
matching has its own CG reads, so this does not claim one total OS inventory read
or atomic native acquisition. New logs and independent local Acceptance belong
to the fresh task; historical capability observations are not re-certified.

The hosted environment is strong enough to carry the bulk of W2-W5 pre-live engineering. It is not a substitute for the real LINE app/session and filesystem acceptance path. No CI result alone may produce `DUPLICATE_CONTENT_CONFIRMED`.

`live-preflight` can navigate reversibly and retains fresh session evidence;
it does not consume Save All authority. A published report with FAIL/UNKNOWN is
blocked and returns nonzero. Current native calibration, exact visible
group/date/count, popup ownership and lack of occlusion, independently reviewed
source/binary eligibility, and actual chooser/filesystem observations remain
required. A new runID cannot bypass a pre-existing goal slot; recovery or source
authorization migration requires a separately reviewed decision.

### Passive native diagnostic collection

| Capability | Current boundary |
| --- | --- |
| Reusable passive CLI | `capture-diagnostic`, LINE-only fresh PID binding, explicit project root, existing empty output under `harness-development/native-diagnostics` |
| Native observation retention | Default primary-window PNG (v1); explicit optional child-union PNG (v2), full raw native bundle, OCR, SCK/CG/AX/process identities, rulebook and actual source/executable hashes |
| Packet verification | External manifest SHA required; matching record/manifest version and profile, retained-file hashes, actual PNG bundle validation and independently recomputed geometry/scale |
| Child diagnostic boundary | Affirmative same-process on-screen intersecting children; exact selected snapshot agreement across settling samples, session inventories and included set; recomputed union; no automatic fallback |
| Output safety | Symlink/traversal/nonempty/reuse refusal, exclusive claim/files, partial output retained, no overwrite |
| Application input | No activation, permission request, transaction owner or actuator in this command |
| Calibration / occlusion / current composer / Phase B | `UNKNOWN`; passive collection cannot authorize live backup or claim native E2E acceptance |
| OS attestation | `UNKNOWN`; source and binary hashes are observed file provenance |

Local fake-boundary regressions verify packet and refusal behavior. Actual LINE collection and native end-to-end acceptance are separate required observations and have not been established by these tests.

Passive source initialization is descriptor-bound and noncreating, including the assertion-to-constructor gap. Deterministic filesystem-only tests cover deletion, symlink and ancestor replacement, descriptor ownership and persistent epoch floors; these tests run no native capture or GUI input.

Version 2 snapshot agreement does not establish AX parentage, menu ownership, topmost status or occlusion. The existing live engine still uses its original capture configuration and permission gates. Local child-profile tests and backwards loading of an actual version 1 packet cannot certify current LINE child-window capture or native backup completion.
# Explicit LINE diagnostic profile (v3)

| Capability | Local implementation boundary | Actual native status |
|---|---|---|
| Exact LINE window group | Explicit IDs/handles, fresh facts, one containing zero-origin display, no implicit child additions | Unverified |
| Crop and scale evidence | Actual full union crop, filter content rectangle/scale, selected display/backing-scale match | Unverified renderer behavior |
| Successful session binding | Shared request/settling/effective/witness validator before return/count and final deadline check | Offline synthetic evidence only |
| Strict packet v3 | Same validator at reconstruct/load with external anchor; legacy v1/v2 remain separate | No real v3 packet |
| Production eligibility | New diagnostic kind refused before composition construction | No Phase B permit |

V3 implementation or synthetic success leaves calibration, ownership, occlusion,
current composer and the reusable native workflow UNKNOWN/not achieved. The
historical production 3/3 budget and two consumed child observations remain;
this profile supplies no new native grant and no download authorization.

| Project inspection foundation | Capability | Limit |
| --- | --- | --- |
| Python `project-preflight` | Canonical project snapshot, target/history decisions, source digests | Read-only; no writer, state change, native observation or dispatch |
| Swift `ProjectBackupBinding.inspect` | Strict byte-bound inspection consumer; recomputes authority/history | `canDispatch=false`; no native permit or ownership |
| Verified target | Always skipped when project is healthy | No photo rescan or second download |
| Unverified historical intent | Conservatively blocked, including purported releases | Future release adoption needs separate evidence and design |
| Destination proposal | Existing safe directory entries or absent path observation | Not a reservation or a freshness guarantee |
| Full native integration | Pending | Shared writer boundary, target continuity and readiness remain required |
