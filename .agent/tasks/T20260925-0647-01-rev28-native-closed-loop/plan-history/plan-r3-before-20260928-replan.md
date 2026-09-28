# Rev28 — Native macOS sensing/actuation closed-loop LINE album backup

## META

- Plan status: `READY_FOR_REVIEW`
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- PLAN_REVISION: `3`
- PLAN_REVISION_BASIS: revision 3 applies the Stage-02 reviews of revision 2 (SHA-256 `84b65bc9eebb763d9ea3839db1ecfafa7f181b7fa6be92cf4216e2befceba1ed`): review attempt-03 (report SHA-256 `6e6602a940c8bc1f078ee8cf289bc2cc778c829d90d58244f0ecf238bd480025`, `PLAN_REVISION_REQUIRED`) and review attempt-04 (report SHA-256 `7d28aef2a5e45ae66eb469e09c6c99c426a4cdc821327a6180e2f332059e1c09`, `PLAN_REVISION_REQUIRED`) — both independently found the accepted-baseline path literal wrong (`_to-…` vs the on-disk/JSON `_to_…`) plus wording/contract clarifications. Revision 2 applies revision 1's review results (attempt-02 SHA-256 `025c74cb61ee067b49a4f6347b74d9764fb68596e8e9932e9e7e7202ded0360e`, `PLAN_REVISION_REQUIRED`; attempt-01 SHA-256 `2ad96474f9f9274405b45bbe9e338f3491ae35006d95a35866d4a719c10b2b98`, `PLAN_APPROVED`). All prior revisions and review attempt dirs are preserved unchanged; no gate is weakened (attempt-03/04 both re-verified that independently).
- TASK_CLASS: `CRITICAL`
- GOAL_ID: `REV28-MACOS27-NATIVE-CLOSED-LOOP-LINE-BACKUP`
- AUTHORIZATION_TYPE: `AUTONOMOUS_ARCHITECTURE_RESEARCH_IMPLEMENT_TEST_AND_BOUNDED_LIVE_EXECUTION`
- REVIEW_REQUIRED: `YES`
- INDEPENDENT_ACCEPTANCE_REQUIRED: `YES`
- E2E_REQUIRED: `YES` (true user-journey live run, strictly conditional on every preceding gate; if gates do not pass, the task ends in a scoped blocked/partial state and the live run does not execute)
- ACCEPTANCE_MODE: Stage-02 independent plan reviews → synthetic AppKit calibration (with W2-frozen rules) → offline replay → adversarial suite → seven pre-live implementation reviews → read-only LINE reconnaissance → single bounded production run → filesystem/content verification → independent E2E acceptance.
- Repository: `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`
- Anchor at plan authoring: HEAD `766b22c4f8bf29b9d0a46049c75309c70593d66d`, `origin/master` identical, ahead 0; working tree has only untracked Rev27e WIP (preserved, never staged or modified).
- Issue anchor: `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md`, SHA-256 `0b3c9efab209bcb4c8c9b5dcaa5fa1ca6279234df0ee3cc0984da829ead67a2d` (verified on disk this round).
- Planning context: this is a NEW architecture (Rev28). Historical Rev27c/d/e artifacts, attempt-07, the frozen v4–v8 tools, the accepted baseline, and the existing staging run are read-only inputs. Uncommitted Rev27e drafts are WIP evidence, not authoritative production code.

## GOAL_CONTRACT (plain language)

The owner wants the LINE group album `2024/05/13～05/17` of group `旻謙允禎成長日記` (57 photos) backed up again through a *new* automation architecture that does not depend on invisible LINE-internal event inference. The new architecture must:

1. see the real LINE window with macOS 27 native APIs (ScreenCaptureKit),
2. read identity/labels with Apple Vision,
3. click with a real system-level pointer event (Quartz `CGEvent`) derived from freshly observed geometry,
4. directly observe the *resulting* UI state (the native chooser) instead of guessing from a returned click,
5. drive the chooser to a fresh unique staging folder exactly once,
6. prove on the filesystem that 57 complete, stable, decodable images arrived, and compare their content against the already accepted 57-photo baseline, and
7. change nothing else.

Because a complete accepted baseline already exists, success is proven by `DUPLICATE_CONTENT_CONFIRMED` (identical content in a fresh staging run), not by creating a second accepted copy.

The owner explicitly authorizes autonomous research/implementation/testing and, after all gates pass, exactly one new production Save All run for exactly the named album. The owner does NOT want to be asked to resolve problems the agent can solve from repository evidence, SDK inspection, offline tests, synthetic tests, or fresh read-only observation. Human input is reserved for genuinely external requirements.

## REQUIREMENTS_AND_CRITICALITY

Derived from the goal text; each requirement is labeled `CORE` (blocks the primary outcome), `SUPPORTING` (required evidence/completeness that must not be silently dropped), or `BEST_EFFORT` (nice-to-have, non-gating).

| # | Requirement | Class | Verification |
|---|---|---|---|
| R1 | Closed-loop contract OBSERVE→LOCATE→ACT→OBSERVE POSTCONDITION→VERIFY FS; primary Save All acknowledgement is the directly observed chooser | CORE | engine design + postcondition monitor tests + live evidence |
| R2 | Native Swift/macOS 27 ScreenCaptureKit sensor layer; `SCContentFilter(desktopIndependentWindow:)` for the stable LINE window; no fullscreen as primary localization source | CORE | capability matrix + harness proof + live capture records |
| R3 | Window identity binding (bundle, pid/process instance, windowID, frame, capture epoch, capture SHA-256) with cross-checks; stale windowID invalidates | CORE | identity tests (incl. adversarial stale-ID) |
| R4 | Apple Vision OCR (accurate, zh-Hant + en-US, no language correction) as authoritative text identity; text identity and click geometry separated | CORE | Vision locator tests + replay |
| R5 | Structural locators: album card/list, album detail, `57張照片`, album ellipsis, popup/menu, `儲存全部`, chooser presence; v6/v7/v8 invariants ported where useful | CORE | locator unit tests + historical replay |
| R6 | Visual stability/registration using Vision-native capabilities: image registration, rectangle detection, **rectangle tracking** (`TrackRectangleRequest` present in the SDK), feature-print similarity; frame SHA for provenance, registered/normalized structural evidence for semantic state | SUPPORTING | registration/tracking tests on jitter fixtures |
| R7 | Foundation Models may be a diagnostic assistant only, never production click authority | SUPPORTING | design + usage log (diagnostics only) |
| R8 | Native Quartz actuator: `CGPreflightPostEventAccess`/`CGRequestPostEventAccess`, `CGEventCreateMouseEvent`+`CGEventPost`, screen-global points, `mouseMoved`→revalidate→`leftMouseDown`→`leftMouseUp` | CORE | actuator tests against harness + live evidence |
| R9 | One canonical coordinate-transform component; explicit transform record (window frame, recorded capture bbox origin/size, `pointPixelScale` + independently checked `NSScreen.backingScaleFactor`, capture dims); validated-tolerance capture rule (no exact-equality assumption); no implicit 2x assumptions | CORE | transform tests incl. wrong-Retina adversarial |
| R10 | Synthetic AppKit harness proving capture (occlusion-surviving, stable coordinates, Retina scale, child/popup identification), Vision localization, transforms, Quartz routing to topmost popup, postcondition detection, AX chooser observation | CORE | harness evidence bundle |
| R11 | AX plane: semantic inspection (role/subrole/title/children/actions/focused element/window ownership); prefer exact `AXPress` when unambiguous; never AX-write to ambiguous elements | CORE | AX tests incl. ambiguity refusal |
| R12 | App activation/focus handling with post-activation verification (isActive, AX focused/main window, SCWindow identity); focus theft is a recoverable pre-irreversible condition | CORE | focus-theft adversarial tests |
| R13 | Persistent execution state machine owning recovery (states APP_READY…FINALIZED), each transition with fresh precondition, action, direct postcondition, timeout, bounded recovery, evidence | CORE | state-machine tests + live ledger |
| R14 | Action risk classes REVERSIBLE_NAVIGATION / PRE_SIDE_EFFECT_ACTION / IRREVERSIBLE_SIDE_EFFECT defined, reviewed, and applied; Save All empirically classified, never inferred from label | CORE | risk classification artifact + review |
| R15 | Save All postcondition: bounded high-frequency observation (SC + AX + window inventory + filesystem tripwire) at one evidence standard with a hard cap; success requires the directly observed chooser inside the window; late affirmative has its own named terminal state; logs/panel-process presence are supporting only; no blind retry | CORE | postcondition tests + latency calibration + live evidence |
| R16 | File chooser via native AX semantics first; destination `…/staging/<UNIQUE-RUN-ID>/`; fresh unique run, canonicalized, inside approved root, empty at start, not baseline, no symlink escape; keyboard/Go-to-Folder only after fresh chooser identity verification; exactly-once confirmation with durable intent (one chosen confirmation action, never both AXPress and Return) | CORE | chooser tests + live evidence |
| R17 | Filesystem completion: exactly 57 completed images, no subdirs/partials/zero-byte, decodable, stable across repeated samples, quiescence, total bytes 17,924,900, and the exact `DUPLICATE_CONTENT_CONFIRMED` predicate = name-excluded sorted SHA-256 content-multiset equality against the recorded baseline reference | CORE | staging verifier tests + live verification |
| R18 | Transactional safety: fresh preconditions, durable intent, single dispatch, postcondition observation, filesystem verification, append-only ledger; unknown irreversible dispatch never blindly retried | CORE | ledger tests + adversarial |
| R19 | Bounded autonomy: identical live-state blocker ≤3 autonomous recovery cycles; implementation failures may continue while hypotheses differ; 3 consecutive reviews on the same unresolved dependency → `BLOCKED_WITH_ROOT_CAUSE`; never weaken safety invariants for approval | CORE | run ledger + review artifacts |
| R20 | Reviews: 7 named pre-live reviews + adversarial review of the 25-scenario matrix (22 goal-mandated G01–G22 + 3 labeled extensions X01–X03) before production; production only if all required reviews approve the exact frozen implementation | CORE | review artifacts bound to SHAs |
| R21 | Single production run for exactly `旻謙允禎成長日記 / 2024/05/13～05/17 / 57`; each side-effecting/irreversible operation type max 1 (Save All dispatch = 1, destination confirmation = 1); fresh coordinates only; no historical coordinate reuse | CORE | live-run ledger |
| R22 | Success condition incl. baseline unchanged, registry/evidence updated consistently, no unexplained side effect; `DUPLICATE_CONTENT_CONFIRMED` route; never claim BACKUP_COMPLETE from click/menu/chooser/count alone | CORE | final acceptance |
| R23 | Deliverables: architecture doc, capability matrix, Swift engine, harness, Vision locator tests, transform tests, actuator tests, postcondition tests, historical replay results, adversarial tests, review artifacts, live-run evidence (if authorized), filesystem manifest, transaction ledger, handoff doc, local commits | SUPPORTING | deliverable manifest |
| R24 | Reconciliation-barrier supersession argument reviewed before any new Save All | CORE | barrier section + review |
| R25 | Historical artifacts preserved byte-identical; no pycache; no push | CORE | diff/manifest audit |

## CRITICAL_PATH (smallest safe path to the primary outcome)

1. **Capability + harness first** (R2, R10): prove ScreenCaptureKit capture semantics, Vision localization, the coordinate transform, and Quartz routing in a synthetic AppKit environment before any LINE interaction.
2. **Engine core** (R3, R4, R5, R8, R9, R11, R13, R18): implement the Swift engine with deterministic pure cores and thin OS edges.
3. **Offline validation** (R5, R6, R23): unit/integration tests + replay of historical frames through the Rev28 locators (no live input).
4. **Adversarial hardening** (R10, R12, R14, R18): the 25-scenario matrix (22 goal-mandated G01–G22 + 3 labeled extensions X01–X03, §ADVERSARIAL_TEST_MATRIX) in the harness, including fake-chooser and partial-download attacks.
5. **Independent reviews** (R14, R15, R16, R18, R20, R24): seven pre-live topics, all bound to frozen SHAs, plus the frozen W2 artifacts (capture per-state rule, postcondition bounds, chooser predicate, tripwire attribution) they review; repair and re-review until approved.
6. **Read-only LINE reconnaissance** (R1, R3, R4, R5): reversible-only navigation to the exact album surface with the frozen locators; resolves the LINE-specific open questions (popup kind, AX exposure, live geometry) with zero side-effecting dispatches and no Save All.
7. **Live run** (R1, R8, R15, R16, R17, R21): navigate LINE from `APP_READY` to the exact album, one ellipsis, one Save All, direct chooser observation, one confirmation into a unique staging run, download.
8. **Filesystem + content verification** (R17, R22): 57 stable decodable files, 17,924,900 bytes, name-excluded content-multiset equality with the recorded baseline reference → `DUPLICATE_CONTENT_CONFIRMED`; baseline unchanged.
9. **Closeout** (R22, R23): ledger, manifests, handoff, final report, local commits.

Ordering rule: any step that cannot proceed does NOT block unrelated steps; only the irreversible production step has a hard prerequisite chain (steps 1–5).

## VERIFIED_REPOSITORY_FACTS (this round, read-only)

- HEAD `766b22c4f8bf29b9d0a46049c75309c70593d66d` = `origin/master`; ahead 0. Working tree: no tracked modifications; untracked Rev27e WIP + prior evidence preserved.
- Issue SHA-256 verified as above.
- Accepted baseline `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` (spelling copied verbatim from `baseline-content-multiset.json.source_dir`; the revision-1/2 literal `…_to-…` was a typo — corrected in revision 3): 57 files, 17,924,900 bytes; **name-inclusive manifest digest** recomputed on disk this round = `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` (method: the lines `relpath\tsize\tsha256`, sorted lexicographically, joined with `\n` **plus a trailing newline**, then SHA-256; verified by both revision-2 reviewers, including the negative control that the no-trailing-newline variant does not match) = MATCH. READ-ONLY. This digest is the baseline's identity/manifest artifact and a tripwire only — never the `DUPLICATE_CONTENT_CONFIRMED` comparison predicate (baseline filenames embed the per-download date token `LINE_ALBUM_20240513～0517_260907_*.jpg`; a fresh download must carry a new token).
- **Baseline resolution is a hard precondition (fail-closed):** the canonical baseline path is the one recorded in `baseline-content-multiset.json.source_dir`; live preflight gate (f) and Stage 05 must, before anything else, (1) `realpath`-resolve that path, (2) assert it is a directory of 57 files / 17,924,900 bytes, (3) recompute the name-inclusive manifest digest == `b7debe92…`, and (4) recompute the content-multiset reference == `ee958e64…`. Any failure to resolve/read the baseline or its reference → `CHECK_RESULT: BLOCKED`; the tripwire is never skipped, the comparison is never degraded, and the live run does not proceed.
- Baseline **content-multiset reference** (read-only, computed this round): `evidence/20260925-rev28-native-closed-loop/baseline-content-multiset.json` SHA-256 `3c932d8ccb9f4d2a7945463861fb4ebae066eadb59b8ff2702767b3a9f851bc2`; 57 unique content SHA-256 values; reference digest `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf` = SHA-256 of the sorted (lexicographic) list of the 57 file hashes joined with `\n`, **no trailing newline** (filenames excluded); the JSON also carries the 57 values so the digest is reproducible independently. This is the RV-02 predicate reference.
- Staging `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260923-111908-01/`: exists, 0 entries, 0 bytes. PRESERVE (no cleanup without separate authorization).
- Historical classification remains `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE`; reconciliation barrier remains open until a reviewed Rev28 supersession passes.
- Historical success RUN-20260907-154331-01: Save All → macOS **folder chooser** appeared → Go to Folder with exact destination → one confirmation → download `0/57` → 57 files. Historical failure precedents: click missed Save All; returned-without-chooser (`RUN-20260908-124357-01`, 2026-09-08, same shape as attempt-07); wrong-row activation (Rename). No historical coordinate may ever be reused.
- v8 Save All locator invariants (ported): popup-shape plausibility; exact `儲存全部` single-row match; menu reference order `選擇項目/修改相簿名稱/儲存全部/刪除相簿/分享相簿` with ≤1 substituted glyph on non-target rows; row-band geometry safety; `x_safe` = row band ∩ window rect with ≥20 px overlap and 2 px margin; `y_safe` = `[max(band.top+edge, above.bottom+12), min(band.bottom−edge, below.top−12)]`, `edge = max(6, 0.15×band_h)`; read-only, deterministic.
- LINE installed: 26.0.2 (3828). LINE not running at probe time. Historical LINE windows observed: main chat window 327×643 pt at (0,33) plus a `LINE`-titled window 1147×699; the album-list surface (AX list + search field) was previously the 327×643 window's content.

## ENVIRONMENT_AND_CAPABILITY_MATRIX (probe evidence: `evidence/20260925-rev28-native-closed-loop/capability-probe/`)

| Capability | Status | Evidence |
|---|---|---|
| macOS | 27.0 (26A428) | `sw_vers`, SystemVersion.plist |
| Xcode / SDK | 26.6 (17F113) / `MacOSX26.5.sdk` (SDK 26.5) | `xcrun --show-sdk-path`, SDKSettings |
| Swift | 6.3.3 | `swift --version` |
| Screen Recording TCC | allowed | `CGPreflightScreenCaptureAccess()` = true |
| Post-event TCC | allowed | `CGPreflightPostEventAccess()` = true |
| Accessibility TCC | trusted | `AXIsProcessTrusted()` = true |
| `SCShareableContent.excludingDesktopWindows` | works (6–8 windows, 1 display) | probe output |
| `SCContentFilter(desktopIndependentWindow:)` | works; `contentRect` == window frame; `pointPixelScale` = 2.0 | probe output |
| `SCScreenshotManager.captureScreenshot` + `SCScreenshotConfiguration` (macOS 26 API) | works; `includeChildWindows=false` → px = frame×scale exactly (round 0, Terminal 1147×683 pt → 2294×1366); `includeChildWindows=true` → px = union(frame, child windows)×scale | probe output (2294×1366 vs 2294×1438) |
| Capture bbox vs `SCWindow.frame` (round 1/2) | **Not guaranteed equal.** `includeChildWindows=true` = union of window + child SCWindow frames, ±padding (round 1: 1038×796 px ≈ union 517×396 pt + ~1 pt/side; round 2 with `ignoreShadows=true`: 1040×798 px = 520×399 pt exactly). `includeChildWindows=false` round 1: 792×660 px vs SC frame 394×326 pt (+~1–2 pt/side); round 2 with `ignoreShadows=true`: 800×664 px = frame×2 exactly. Round-2 default (shadows rendered): 1024×952 px for a 400×364 pt frame, i.e. ~56 pt/side of shadow inflation → shadow-bearing captures are **never geometry-bearing** | `prototype-round1-findings.md` (`43998519…`), `prototype-round2-outputs.txt` (`afd6c26d…`) |
| `SCWindow.frame` stability (round 1 P6) | unstable vs AppKit frame in unsettled states (uniform 3 pt inset shortly after creation/activation); exact when settled | `prototype-round1-findings.md` P3/P6 |
| `sourceRect` semantics (round 1 P5) | window-local, not display-global; origin outside the window → `SCStreamErrorDomain -3811`; partial overlap → in-bounds region + black | `prototype-round1-findings.md` P5 |
| `SCScreenshotManager.captureImage` + `SCStreamConfiguration` (legacy) | works but default size is 1920×1080; explicit dimensions required | probe output |
| Goal-named `contentScale` / `scaleFactor` | **No SDK symbol with either name exists** (checked both SDKs' interfaces); the scale source is `pointPixelScale` (window/content space) and `NSScreen.backingScaleFactor` (display); both are recorded per capture and cross-checked | SDK `.swiftinterface` + `probe-metadata.json` |
| Tool-process GUI context | `SCScreenshotManager` requires `NSApplication.shared` + run loop, else `CGS_REQUIRE_INIT` assertion crash | probe output |
| Display | single 1147×745 pt @ 2.0 | NSScreen + CGDisplay |
| Vision Swift API | `RecognizeTextRequest`, `DetectRectanglesRequest`, `GenerateImageFeaturePrintRequest`, `RecognizeDocumentsRequest`, registration requests present in SDK interface | SDK `.swiftinterface` |
| AX / CGEvent APIs | `AXUIElement`, `AXActionConstants`, `CGEventCreateMouseEvent`, `CGEventPost`, preflight APIs present | SDK headers |
| LINE app | 26.0.2, installed; not running at probe | Info.plist |
| Build-SDK pinning | bare `xcrun --show-sdk-path` = CLT `MacOSX27.0.sdk`; `xcrun --sdk macosx --show-sdk-path` = Xcode `MacOSX26.5.sdk`; both contain every required API. Each build records its exact SDK path in the build/evidence log | SDKSettings + review attempt-02 residual |

Open capability questions to be resolved empirically — each names its **resolving evidence class** (harness = synthetic AppKit calibration on this machine; reconnaissance = fresh read-only LINE observation; both are pre-live gates, never assumptions):
- per-state capture bbox rule (settled/unsettled × activated/deactivated × shadows on/off × includeChildWindows on/off) → **harness** (W2 freezes the rule and tolerance; RV-01);
- whether LINE's popup/menu is a separate SCWindow, a child window, or drawn inside the main window surface → **reconnaissance** (read-only popup open + Escape dismissal; no row activation);
- whether AX exposes the album ellipsis / popup / Save All rows (historically mostly custom-drawn) → **reconnaissance** (read-only AX reads only);
- AX surface + hosting shape of the native folder chooser on macOS 27 (roles, subroles, Go-to-folder affordance, default button, owning process) → **harness** with a real `NSOpenPanel` (W2 freezes the chooser-affirmation predicate; RV-09) plus post-dispatch observation;
- behavior of `AXIsProcessTrusted`/`CGPreflight*` inside a compiled SwiftPM executable vs the current privileged shell (probe used the shell's trust context) → **harness/CLI probe** (first W1 run records the executable-context result; a false result is a hard gate failure, not a workaround);
- panel-appearance latency for the postcondition bounds → **harness** (≥20 real-panel runs; bounds re-frozen by review 4; RV-03).

## SOURCE_OF_TRUTH

1. Current user goal text (this plan's contract) and the verified repository/issue anchors.
2. Live macOS/SDK behavior demonstrated by capability probes and harness tests on this machine.
3. Repository evidence for historical facts (labeled `[HISTORICAL]`), never as live coordinates.
4. Reviewed Rev28 implementation and its frozen SHAs.
5. Anything unproven is labeled `[UNVERIFIED]` and fails closed at gate level.

## CONSTRAINTS_NON_GOALS_AND_DO_NOT_TOUCH

- Non-goals: no changes to the accepted baseline; no second accepted production copy; no cleanup/deletion of staging or baseline without separate authorization; no push; no `__pycache__`/`*.pyc` additions; no modification of other agents'/owner's unrelated work; no reclassification of attempt-07; no claim of BACKUP_COMPLETE without the full chain.
- Do-not-touch (byte-identical): `evidence/20260916-route/attempt-07/**`, Rev27d reconciliation artifacts, cycle-3 frozen reviewed snapshot + reviews, `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md`, revoked/old plans, frozen tools v4–v8, the accepted baseline, `staging/RUN-20260923-111908-01/**`, all Rev27e WIP not owned by this task.
- LINE-internal inference (unified logs, panel-process presence, click-return codes) may never be the primary success condition. It may be supporting/forensic evidence only.
- Zero side-effecting dispatches before `SAVE_ALL_LOCATED`: reconnaissance and all navigation are reversible-only; no menu row is ever activated during reconnaissance.
- Live-run captures/OCR extracts remain in the untracked evidence directory and are never pushed; no accepted second production copy is ever created.
- No AX write or click against an element whose identity is ambiguous or unbound to the freshly verified surface.
- No historical coordinates; every live coordinate must be freshly derived from the current frame and revalidated immediately before dispatch.

## SYSTEM_BOUNDARY_AND_MODULE_MAP

New SwiftPM package `rev28/` (product code) + append-only evidence `evidence/20260925-rev28-native-closed-loop/`.

```
rev28/
  Package.swift
  ARCHITECTURE.md            (deliverable)
  CAPABILITY-MATRIX.md       (deliverable)
  Sources/
    Rev28Core/               (library; deterministic cores + OS edges)
      Geometry/Coordinates.swift
      Sensor/WindowSensor.swift
      Sensor/FrameCapture.swift
      Identity/WindowIdentity.swift
      Perception/OcrEngine.swift
      Perception/Registration.swift
      Perception/Locators.swift
      Actuation/QuartzActuator.swift
      Actuation/AXDriver.swift
      Postcondition/PostconditionMonitor.swift
      Chooser/FolderChooserDriver.swift
      State/BackupStateMachine.swift
      Transaction/IntentLedger.swift
      Verify/StagingVerifier.swift
      Risk/ActionRisk.swift
      Diagnostics/DiagnosticHooks.swift
    rev28probe/              (capability probe CLI)
    rev28harness/            (synthetic AppKit harness app + scenario driver)
    rev28occluder/           (separate-process occluder helper used by the harness)
    rev28ctl/                (orchestrator CLI: probe|replay|harness|live subcommands)
  Tests/Rev28CoreTests/      (unit + harness integration tests)
```

Design rules: pure functions for geometry/matching/locators/verifiers (deterministic, testable without a GUI); thin OS edges behind protocols so the harness can substitute fakes; every OS observation produces a structured evidence record with SHA-256 and timestamps; every write is atomic (temp+rename) and append-only where it is evidence.

## ARCHITECTURE

### 1. Sensor plane (ScreenCaptureKit)

- Enumerate with `SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)`.
- Select the LINE main window by: bundle `jp.naver.line.mac`, owning pid == the target process instance, window layer == 0, on-screen, and a frame that matches the live AX main-window geometry within tolerance. Never select by windowID alone; a windowID is only valid inside one capture epoch.
- Capture configuration is explicit and recorded per capture; nothing relies on defaults: `showsCursor=false`; geometry-bearing captures use `ignoreShadows=true` (round-2 probe: the shadow-bearing default inflates the image by up to ~56 pt/side and shifts its origin → shadow-bearing captures can never be geometry-bearing); `ignoreClipping` and `includeChildWindows` are recorded flags.
- Primary capture: `SCContentFilter(desktopIndependentWindow:)` + `SCScreenshotConfiguration` with `includeChildWindows=false`. Expected image = the included window's freshly read `SCWindow.frame` × `pointPixelScale`; the **actual capture bbox (origin + size, pt)** is recorded per frame and used by the canonical transform. A residual delta between expected and actual geometry is permitted only inside the W2-frozen per-state rule/tolerance (§COORDINATE_TRANSFORM_MODEL invariant 1); anything else → INVALID (fail-closed). Primary image space = window-local points × scale, origin at the window frame top-left (round-1 P4: the captured surface includes the title bar).
- Popup/child/sheet observation: `includeChildWindows=true` and/or an app-level/independent-window filter for the popup's own SCWindow when it is a separate window. The expected bbox is the **union of the included windows' freshly read SCWindow frames**; the same validated-tolerance rule applies, and the recorded bbox — not the main window frame — drives the transform for these captures. Round-1/round-2 evidence: with `ignoreShadows=true` the union rule was exact (1040×798 px = 520×399 pt for the observed borderless-window + child union).
- `SCWindow.frame` is unstable in unsettled states (round-1 P6: uniform 3 pt inset shortly after creation/activation; exact when settled) → never assume equality; re-read per capture epoch (§2).
- `sourceRect` is window-local (round-1 P5): a rect whose origin lies outside the window fails with `SCStreamErrorDomain -3811`; a partial overlap returns the in-bounds region with the rest black. `sourceRect` is never used to reach beyond a window surface; popups/sheets that are separate windows get their own filter.
- Fullscreen/display captures (`captureImage(in:)`/display filter) are permitted only for corroboration, occlusion investigation, and actuation verification.
- Each `CapturedFrame` records: capture kind; the full configuration (includeChildWindows, ignoreShadows, ignoreClipping, showsCursor, sourceRect if any); included windowIDs + their freshly read SCWindow frames; expected bbox; actual image dims (px) and derived actual bbox (pt); per-side residual; scale + independent scale source (`pointPixelScale` vs `NSScreen.backingScaleFactor`); monotonic epoch + wall time; SHA-256 of the PNG/raw bytes; and the bound `WindowIdentity`. Invariant failures emit an INVALID frame record carrying the raw numbers — never a silent clamp or a retry with looser numbers.

### 2. Window identity

`WindowIdentity` = {bundleID, pid, process start time (`proc_pidinfo(PROC_PIDTBSDINFO)`), windowID, window frame (pt), AX role/subrole/title (read-only), CGWindowList entry (id/frame/layer/owner), capture epoch, capture SHA-256}. Cross-checks: NSRunningApplication for activation state; AX for main/focused; CG list for frame/ordering. Identity rules:
- A perception result is only valid for the epoch it was captured in.
- Before every dispatch, re-enumerate and re-derive the target window; if windowID changed, the candidate is invalid (re-locate, do not reuse coordinates).
- Multi-display: transforms bind to the display containing the window; the harness proves behavior with a moved window; a second display is `[UNVERIFIED]` on this machine and must fail closed if a window moves outside the captured display.

### 3. Perception plane (Vision)

- OCR: `RecognizeTextRequest` (Swift) with `recognitionLevel = .accurate`, `recognitionLanguages = ["zh-Hant", "en-US"]`, `usesLanguageCorrection = false`; an optional `VNRecognizeTextRequest` parity wrapper (BEST_EFFORT, non-gating) may exist for cross-checking on the same fixtures; the production path is the Swift request. Exact identity strings are compared with NFC-exact matching; `禎 U+798E` and `楨 U+6968` are never normalized or merged.
- The OCR layer returns `(text, quad, confidence)` in capture px, transformed to window-local pt by the canonical transform.
- **Separation rule:** OCR establishes *identity* (album title, `57張照片`, menu item name, chooser labels). *Geometry* for clicks comes from structural rules over OCR boxes + surface structure (row bands, safe interior, addressable rect), never from a raw character box.
- Structural locators (each fail-closed with a distinct verdict): album list surface + target card, album detail surface, count text `57張照片` (digits == 57), album-level ellipsis, popup/menu surface, `儲存全部` row (v8 invariants ported), chooser presence. Multiple matches → AMBIGUOUS (refuse).
- Registration/stability: `GenerateImageFeaturePrintRequest` distance, rectangle detection, and rectangle tracking (`TrackRectangleRequest`), and/or registration requests to compare surfaces across redraws/cursor changes/minor motion; frame SHA stays provenance-only. Beta APIs never become the sole production gate.

### 4. Foundation Models role

Optional diagnostic assistant: may inspect failed frames and propose classifications/ROIs/hypotheses or generate offline tests. It may not authorize clicks, override a refusal, relax identity rules, or invent production coordinates. All FM output is recorded as `diagnostic` evidence.

### 5. Actuator (Quartz)

- Preflight `CGPreflightPostEventAccess()`; request only if needed (`CGRequestPostEventAccess()`).
- Sequence per dispatch: (1) activate/verify target app state; (2) capture a fresh frame; (3) re-derive the target candidate on that frame; (4) compute screen-global point via the canonical transform; (5) `mouseMoved` to the point; (6) assert target window still frontmost/active and the candidate still valid; (7) `leftMouseDown`; (8) short inter-event delay; (9) `leftMouseUp`; (10) record a `DispatchRecord` (screen pt, window-local pt, capture px, windowID, epoch, frame SHA, candidate SHA, risk class, ledger id).
- One actuator code path only; no window-relative abstraction, no app-specific magic.
- Clicks land on the topmost window at that point (verified in harness with a popup above the main window).

### 6. Accessibility plane

- AX reads: role, subrole, title, children, actions, focused element, window ownership (pid of element).
- Prefer a semantic `AXPress` for an action when: the element identity is unambiguous (single match), the element belongs to the freshly verified surface, and the action is exactly the intended one. Otherwise use Quartz coordinates.
- For LINE custom-drawn surfaces: Vision + Quartz.
- AX writes are attempted only against a uniquely identified element bound to the verified surface; ambiguity → refusal.

### 7. App activation / focus

- Activation via `NSRunningApplication.activate(options:)` and (if needed) `NSWorkspace.openApplication` for launch; then verify `isActive`, AX focused/main window identity, and the SCWindow identity. Activation is not assumed to be immediate (poll with bounded timeout).
- Focus theft before an irreversible action is a recoverable condition under the reviewed recovery policy; the engine re-verifies preconditions and re-derives the candidate.

### 8. State machine

States: `APP_READY → GROUP_READY → ALBUM_LIST_READY → TARGET_ALBUM_LOCATED → ALBUM_DETAIL_VERIFIED → ELLIPSIS_LOCATED → MENU_VERIFIED → SAVE_ALL_LOCATED → CHOOSER_VERIFIED → DESTINATION_PREPARED → DOWNLOAD_CONFIRMED → DOWNLOAD_IN_PROGRESS → FILESYSTEM_STABLE → CONTENT_VERIFIED → FINALIZED`, plus terminal scoped states (`ABORTED_<REASON>`, `INDETERMINATE_<REASON>`). Every transition carries {fresh precondition, action, direct observable postcondition, timeout, bounded recovery policy, evidence record}. Recovery is owned by the state machine (persistent), not by conversation continuity.

### 9. Action risk classes (pre-registered; refined only by evidence)

- `REVERSIBLE_NAVIGATION`: LINE launch/activation, chat/group selection, opening the album list, opening an album card, scrolling, opening the ellipsis popup, dismissing a popup without selection. Bounded recovery ≤3 attempts per identical blocker with fresh preconditions; never at a point where a side-effect could already have occurred.
- `PRE_SIDE_EFFECT_ACTION`: an action empirically proven to only open a chooser/sheet before any filesystem write, with a reviewed bounded-recovery policy.
- `IRREVERSIBLE_SIDE_EFFECT`: destination confirmation, download commit, and any action whose filesystem effect is unproven. Exactly-once: durable intent, single dispatch, no blind retry.

**Save All classification policy for THIS run:** the goal requires empirical classification and explicitly permits PRE_SIDE_EFFECT *only if proven*; at plan time it is NOT proven (historically indeterminate). Therefore Rev28 executes Save All under `IRREVERSIBLE_SIDE_EFFECT` semantics: exactly one dispatch, no retry, direct postcondition observation. The run's evidence then records the empirical classification for future runs. This is conservative in the direction of safety, and matches the authorization envelope (Save All: 1). The ledger names that classification record explicitly (`saveAllEmpiricalClassRecord`, with the postcondition + tripwire evidence it is derived from) so any future bounded-recovery decision has a reviewed basis; `PRE_SIDE_EFFECT_ACTION` stays defined and reviewed even if unused this round.

**Recovery-budget interplay (deliberate cap interaction):** revalidation failures are not navigation blockers. `REVERSIBLE_NAVIGATION` allows ≤3 attempts per identical blocker with fresh preconditions, while the abort rule stops at two consecutive failed revalidations of the same candidate; the stricter revalidation cap wins whenever both could apply, and the ledger records which class each stop belongs to.

### 10. Save All postcondition

After the single dispatch, one bounded observation window at a single evidence standard — every sample carries the same identity binding and is verdict-eligible — with cadence ≤150 ms for the first 8.0 s and then ≤500 ms up to the hard cap 15.0 s, observing:
- SC captures (LINE window; full display for corroboration),
- AX window inventory for the LINE pid and for panel-process candidates (with a pre-dispatch census of processes hosting panel-like windows),
- `CGWindowListCopyWindowInfo` inventory,
- filesystem tripwire: creations/modifications under the staging run dir and under `~/Downloads` (read-only observation; no writes by the monitor), under the attribution rule below.

Affirmative evidence (`SAVE_ALL_POSTCONDITION_CONFIRMED`) = a chooser surface satisfying the frozen chooser-affirmation predicate (§11) directly observed inside the bounded window, with its capture/AX/CG records. Unified logs / panel-process presence / menu disappearance / click-returned are never sufficient.

Terminal semantics (no contradiction allowed between state name and evidence):
- affirmative inside the window → `CHOOSER_VERIFIED` (proceed to chooser automation);
- affirmative first observed only after the hard cap (the monitor keeps one late ledger sample at ~30 s for forensics) → `CHOOSER_OBSERVED_AFTER_WINDOW` (indeterminate-with-cause; zero further input; disclosed in the final report);
- no affirmative by the hard cap → `NO_CHOOSER_OBSERVED` (scoped indeterminate; **no retry**; budget consumed).

Plan-time bounds are re-frozen by W2 calibration: the harness measures real panel-appearance latency (real `NSOpenPanel`, ≥20 runs) and review 4 binds the frozen cadence/bounds with that evidence and margin. If calibration shows the hard cap is insufficient, that is a replan — never a silent extension.

Filesystem-tripwire attribution — explicit three-level scope ladder (RV-02 of review attempt-03): the monitoring scope is `L1 = the unique staging run dir` ⊆ `L2 = the approved root /Users/hsiaojohnny/Downloads/LINE-Backup-PoC/` ⊆ `L3 = ~/Downloads`; classification after dispatch is level-specific:
- `L1` — writes here are the expected primary chooser-effect signal, attributable to the download flow (never abort on them; they are the evidence).
- `L2` — writes here (including the accepted baseline, which must stay byte-identical) are attributed via {process census diff (target app / panel processes / engine), path pattern, FSEvents timing, the engine's own pre-declared writes}; attributable-but-unexpected → record `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED` (non-fatal; disclosed in the ledger and final report as a side-effect observation); unattributable → `ABORTED_UNATTRIBUTED_FILESYSTEM_WRITE` (fail closed, no retry); any modification of the accepted baseline → immediate abort regardless of attribution.
- `L3` (outside the approved root) — environmental observation only: attributable-to-this-run writes outside the approved root are a scope violation → `ABORTED_WRITE_OUTSIDE_APPROVED_ROOT`; unattributable activity is recorded as environmental context (concurrent-machine-activity caveat disclosed in the ledger) and does not abort by itself.
Pre-dispatch environmental activity is recorded as context and never aborts by itself: while the run sits at `SAVE_ALL_LOCATED`, the monitor records a ≥10 s pre-dispatch environmental baseline (FSEvents) for exactly this attribution.

### 11. Chooser automation

- Verify chooser identity first against the **frozen chooser-affirmation predicate** (W2 freezes it before the seven reviews; the hosting shape comes from harness calibration, never from assumption):
  1. a window/sheet that is new relative to the pre-dispatch inventory, on-screen, present in the fresh SC and CG inventories;
  2. whose AX surface matches native open/save-panel semantics — role/subrole, a path affordance, default/cancel buttons — as calibrated against a real `NSOpenPanel` on macOS 27;
  3. with unambiguous ownership: the owning pid is bound to the freshly established panel-process set — pre-dispatch census (target app pid + any process hosting a panel-like window in the observed recent past) plus post-dispatch census; the specific instance is authenticated by bundle identifier / code-signing identity + process start time (pid reuse rejected); an empty or indeterminate pre-census set is allowed as an observation, but it **widens the refusal requirement rather than relaxing the predicate**: ownership evidence is then strictly weaker, so any residual ambiguity in (1) or (2) must be refused (no benefit of the doubt), and the harness fixture for this case includes a same-process look-alike that must be refused;
  4. observed inside the bounded postcondition window with full capture/AX/CG evidence.
  Panel-process membership is one ingredient, never the sole gate; the predicate explicitly permits whichever hosting shape (separate panel service, in-process, or other) the harness proves on this macOS version, and that resolved shape is recorded in the frozen review set. Fake, look-alike, ambiguous, or predicate-mismatching surfaces → refusal, recorded as `INDETERMINATE_CHOOSER_REFUSED` with a cause enum that includes `frozen_predicate_mismatch` (the frozen native-panel-shaped predicate was calibrated on a real `NSOpenPanel`; LINE's actual chooser shape cannot be pre-validated in Phase A without consuming the Save All budget, so a mismatch must be reported with that cause and must not trigger an ad-hoc predicate loosening).
- Write durable intent (ledger, fsync) BEFORE the confirmation.
- Destination: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<UNIQUE-RUN-ID>/` where `UNIQUE-RUN-ID = RUN-<yyyyMMdd-HHmmss>-<4 hex>`. Preflight: `realpath` canonicalization; must be inside the approved root; must not exist or must be empty; must not equal/contain/be-contained-by the accepted baseline; symlink components rejected.
- Navigation: AX first (locate the panel's Go-to-folder affordance, its path field, and the default button; verify values after each step). If AX cannot safely drive it: keyboard path (⇧⌘G + Unicode text entry via `CGEventKeyboardSetUnicodeString` + Return) only after fresh chooser identity verification; a clipboard-based path is NOT used unless AX and keyboard both fail under review.
- Confirmation exactly once: exactly one confirmation action is chosen before dispatch — `AXPress` on the unambiguous default button, else `Return` — and recorded; the two are never both used, and a non-effect consumes the single confirmation budget. Then verify the direct postcondition: chooser closes / download begins (filesystem tripwire).
- Only the one chosen confirmation action consumes the single confirmation budget; destination navigation/preparation steps (Go-to-folder, path entry, field verification) are logged with pre/post evidence and are reversibly navigable, but are never themselves a confirmation and never consume the budget.

### 12. Filesystem completion and the exact duplicate-content predicate

- Monitor the unique staging dir at ≥1 s cadence: file count, names, sizes, mtimes; detect partial suffixes (`.part .partial .tmp .temp .download .crdownload .incomplete .filepart`), zero-byte files, subdirectories.
- Require: exactly 57 image files; no subdirs; none zero-byte at settle; all structurally decodable (JPEG/PNG structural checks ported from the repo verifier); total bytes == 17,924,900; sizes+mtimes stable across ≥3 samples spanning ≥4 s with a quiescence interval ≥5 s after the last change; then compute the sorted content multiset.
- **`DUPLICATE_CONTENT_CONFIRMED` predicate (exact, RV-02):** staging has exactly 57 image files, no subdirs/partials/zero-byte, all decodable and stable, total bytes 17,924,900, and `SHA-256(sort(values).joined("\n"))` (no trailing newline) == `ee958e6467676506a1c7aaf237a4376ecc5e5083fd94aa6fd0d56d376cacdaaf` (baseline reference in `baseline-content-multiset.json`, file SHA-256 `3c932d8c…`, 57 unique content hashes). Filenames are excluded by design; the name-inclusive digest `b7debe92…` is the baseline's identity/manifest artifact and a tripwire only.
- **Mismatch reporting (no improvised verdicts):** any failure of the predicate above produces a scoped, non-success terminal with a forensic report distinguishing route-level defect from album-content change: `STAGING_INCOMPLETE` (<57 files / partial / zero-byte / unstable), `STAGING_EXTRA_FILES` (>57 or non-image entries), `STAGING_DUPLICATE_CONTENT` (same hash twice inside staging), `CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE` (57 stable decodable files whose multiset differs — report the symmetric difference; separate hypothesis (a) route-level content defect vs (b) album legitimately changed since the baseline, using the OCR/identity evidence of the album at capture time). No accepted-copy creation, ever; never copy staging into the accepted baseline.
- Baseline side is resolved, never guessed: the comparison target is the directory named by `baseline-content-multiset.json.source_dir` (with the file's own SHA-256 `3c932d8c…` checked first); the name-inclusive tripwire digest uses the trailing-newline method above; an unresolvable/unreadable baseline or reference mismatch → `CHECK_RESULT: BLOCKED` (no degraded comparison, no skipped tripwire).
- Stage 05 recomputes the staging multiset and both baseline digests (name-excluded reference and name-inclusive tripwire) from disk itself; it never trusts Stage-04 claims.

### 13. Transactional safety

Append-only JSONL ledger `evidence/20260925-rev28-native-closed-loop/live-run/ledger.jsonl` with hash-chaining (`prev` field), one entry per observation/decision/dispatch/intent, fsync on critical entries; intent records precede irreversible actions; every artifact named in the ledger by path+SHA-256. No implicit state in memory across restarts: the state machine persists `state.json` atomically and can resume in a read-only "observe" mode after a crash, never re-dispatching an irreversible action without a fresh reviewed decision.

## COORDINATE_TRANSFORM_MODEL

Spaces: window-local points (origin = window frame top-left), screen-global points (top-left origin, points; same as CGWindow bounds / `CGEvent` coordinates), capture pixels.

Given `binding` (window frame `W` and capture scale `S = pointPixelScale`, cross-checked against `NSScreen.backingScaleFactor` of the display containing the window) and the **recorded actual capture bbox `B`** (origin + size in pt, recorded per frame with its configuration flags), the canonical transform is:

```
screenPt   = windowLocalPt + W.origin
capPx      = (screenPt − B.origin) × S
windowLocalPt = screenPt − W.origin
capturePx→screenPt = B.origin + capPx / S
```

Invariants checked at frame creation and before every dispatch:
1. **Validated capture geometry, not exact equality** (RV-01): with the W2-frozen configuration, `image.size.px` must be within the W2-frozen per-state bound of `round(expectedBBox.size × S)`, where `expectedBBox` = the union of the freshly read `SCWindow.frame`s of the included windows. Round-1/round-2 evidence for the bound: shadow-free settled captures were exact or ≤ ~1 pt/side (`includeChildWindows=false` 800×664 px = 400×332 pt ×2; union case 1040×798 px = 520×399 pt ×2); shadow-bearing captures were inflated by up to ~56 pt/side and are barred from geometry. W2 resolves and freezes the exact per-state rule (settled/unsettled × activated/deactivated × shadows on/off × child-windows on/off) with this machine's measurements before the seven reviews; a state without a frozen rule, or a delta beyond the frozen bound, is INVALID (fail-closed). No tolerance exists without a recorded rule; post-freeze rule changes are semantic changes → replan.
2. **Origin consistency:** the transform uses the *recorded* `B`. In the frozen settled shadow-free state `B.origin == W.origin` exactly (or `W.origin − p` with a frozen symmetric padding `p ≤ bound`); any unexplained origin deviation → INVALID. `W.origin`/`B` derive from the same enumeration epoch as the frame (`windowID` + frame re-read); a window that moved between enumeration and capture invalidates the frame.
3. **Independent scale check:** `pointPixelScale` must equal `NSScreen.backingScaleFactor` for the display containing the window, else INVALID — wrong-scale detection is anchored to this independent source, not to the size check alone.
4. No implicit 2×: every conversion carries its `S` and `B`; mixed-scale usage is a type-level impossibility (distinct structs for each space).
5. Rounding: dispatch points are computed in points; pixel conversions are for evidence only. If a click point falls within 1 pt of a safe-interior boundary, it is refused (re-locate).

## SYNTHETIC_HARNESS_CALIBRATION_PLAN

`rev28harness` is an AppKit app + a tiny separate helper process (own window hierarchy, controllable by a test driver over a local unix socket / stdio protocol):
- main window (known geometry, known internal markers, Retina-scaled content);
- a target "row" surface and a custom popup (child window) above it;
- a separate helper process `rev28occluder` that can place its own window fully over the main window (OS-level occluding app, not a same-process NSWindow) — RV-08;
- a scenario mode that (a) moves the window, (b) opens a popup at controlled offsets, (c) covers the main window with the separate-process occluder, (d) presents a real `NSOpenPanel` in directory mode (chooser emulation), (e) presents a fake chooser-like window (look-alike), (f) steals focus to another app/process, (g) writes files into a temp destination (download simulation incl. zero-byte placeholders, partial suffixes, slow growth), (h) simulates an unrelated writer process writing outside the staging dir (tripwire-attribution fixture), (i) crash-injection: `rev28ctl` can `SIGKILL` itself at scripted points (after intent fsync, after dispatch, mid-postcondition, mid-download) so restart behavior is exercised deterministically — RV-08.

The harness must prove (evidence bundle with SHAs):
1. **Capture semantics + per-state rule freeze (RV-01)**: a matrix of {settled/unsettled} × {activated/deactivated} × {shadows on/off} × {includeChildWindows on/off} records actual bbox and per-side residual vs the SCWindow union; the result freezes the exact per-state rule + numeric tolerance that production uses, and proves the shadow-free geometry path; capture survives full occlusion by the **separate-process** occluder; coordinates stable across captures; Retina scale reported correctly and cross-checked against `NSScreen.backingScaleFactor`; child/popup windows identifiable either as separate SCWindows or via union bbox.
2. **Vision localization**: OCR reads the synthetic labels (`儲存全部` row inside a 5-row menu, `57張照片`, album title strings incl. `禎/楨` discrimination fixture); locators return the same safe-interior point for repeated captures; ambiguity fixtures refuse.
3. **Coordinate transforms**: window moved (± dx/dy), scale 2.0 on this machine; local→screen→px→local round-trips; wrong-scale injection is detected by invariant #1.
4. **Quartz routing**: a posted click at the popup row's screen point hits the popup (not the main window beneath), proved by the harness recording the hit-test result (popup receives the event and responds; main window must not receive it); including when the occluder is present but the popup is topmost.
5. **Postcondition detection + bounds freeze (RV-03)**: chooser detector affirms the real `NSOpenPanel`, refuses the fake look-alike; the harness measures real panel-appearance latency over ≥20 runs and the frozen cadence/bounds (≤150 ms/8.0 s then ≤500 ms to hard cap 15.0 s) are recorded with that evidence; postcondition timeout path produces `NO_CHOOSER_OBSERVED` without retry; late-affirmative path produces `CHOOSER_OBSERVED_AFTER_WINDOW` with zero further input.
6. **AX chooser observation + predicate freeze (RV-09)**: AX read of the harness `NSOpenPanel` (roles/subroles/titles/buttons/path affordance), AXPress confirm path, keyboard Go-to-folder path, post-confirmation destination verification, ownership/pid-reuse semantics (bundle/signing identity + process start time; pre/post census, empty-set case) — all frozen into the chooser-affirmation predicate — plus an ambiguity fixture that must refuse, a look-alike owned by a different process that must refuse, and an empty-census fixture in which a same-process look-alike must also be refused (the empty census widens refusal).
7. **Focus theft recovery**: harness steals focus; engine re-verifies before dispatch and (in test) aborts or recovers per policy without ever dispatching against the wrong window.
8. **Tripwire attribution (RV-07)**: the harness writes inside the staging dir (attributable) and, via the unrelated-writer fixture, outside it (unattributable); the engine classifies correctly, records attribution evidence, and only the unattributable case fails closed.
9. **Restart/observe-only fixture (RV-08)**: `rev28ctl` is killed at the scripted points; on resume it must enter observe-only mode, preserve ledger hash-chain continuity, and perform zero irreversible re-dispatches (asserted from the ledger).

## HISTORICAL_REPLAY_PLAN

Offline only. Fixtures are read-only, copied into the new evidence dir at first use, and bound by SHA-256 (recomputed when copied; any mismatch → STOP, the fixture is not what this plan reviewed) — RV-10 disambiguates the two `attempt-07` trees explicitly:

| Fixture (repository-relative, read-only) | SHA-256 | Replay purpose |
|---|---|---|
| `evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-frame.png` | `d545043d…` | full pre-click frame, last frozen Save-All attempt (menu path) |
| `evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-ax.json` | `668bed55…` | AX state at pre-click |
| `evidence/20260921-rev27-save-all/attempt-07/s11e-menu-detect.json` | `009c705f…` | menu detection record (v8 path) |
| `evidence/20260921-rev27-save-all/attempt-07/s11e-menu-frame-geometry.json` | `8f236eba…` | menu frame geometry vs locator bands |
| `evidence/20260921-rev27-save-all/attempt-07/s11e-v8-locate-save-all.json` | `5f5ba237…` | v8 `儲存全部` locator output (x_safe/y_safe) |
| `evidence/20260921-rev27-save-all/attempt-07/s11e-final-gate.json` | `fd44018d…` | pre-click gate decision |
| `evidence/20260916-route/attempt-07/v5-offline-replay.json` | `5ad6aa01…` | v5 ellipsis locator baseline |
| `evidence/20260916-route/attempt-07/v4-baseline-replay.json` | `126b3c92…` | v4 baseline locator outputs |
| `evidence/20260916-route/attempt-07/album-card-locate.json` | `94694c92…` | album card locator output |
| `evidence/20260916-route/attempt-07/album-open-verify.json` | `aa0a2161…` | album-detail verify record |
| `evidence/20260916-route/attempt-07/screen-probe.json` | `38130a6a…` | historical window geometry |
| `evidence/20260916-route/attempt-12/frame-pre.png` | `b88f7e09…` | album-list frame |
| `evidence/20260916-route/attempt-12/album-card-locate-v6.json` | `05bcea90…` | v6 album-card locator output |
| `evidence/20260916-route/attempt-12/live-window-geometry.json` | `fdd68d75…` | live window geometry binding |
| `evidence/20260916-route/attempt-12/s1-ax-pre.json` | `fe5f3d68…` | AX state, album-list surface |
| `evidence/20260916-route/attempt-13/frame-menu-pre.png` | `0118b12f…` | pre-menu frame (attempt-13) |
| `evidence/20260916-route/attempt-13/geometry-binding-preclick.json` | `288dba46…` | geometry binding at pre-click |
| `evidence/20260916-route/attempt-14/frame-pre.png` | `7e16ddff…` | album-list frame (attempt-14) |
| `evidence/20260916-route/attempt-16/frame-s1.png` | `d0581391…` | s1 surface frame |
| `evidence/20260916-route/attempt-16/s1-window-ocr.json` | `ddf202f0…` | OCR output on s1 |

(Full hashes were computed at plan-revision time and are recorded in `evidence/20260925-rev28-native-closed-loop/replay/fixture-manifest.json` at W3, together with the copy SHA-256; abbreviated forms above are display-only.) Replay checks:
- album list card candidate vs v6 output (agreement or documented divergence),
- album detail surface + `57張照片` identity,
- ellipsis location vs v5 output,
- popup menu + Save All row vs v8 output (candidate point within v8 `x_safe/y_safe`).
Divergences are recorded, not "fixed" by threshold tweaks; each divergence gets a hypothesis and a test.

## ADVERSARIAL_TEST_MATRIX (harness + offline)

Canonical numbering: the goal's 22 scenarios in goal order (`G01`–`G22`) plus 3 explicitly labeled extensions (`X01`–`X03`) = **25**.

- `G01` wrong window · `G02` wrong bundle · `G03` stale windowID · `G04` wrong Retina transform · `G05` occluding app (**separate-process** occluder) · `G06` window movement · `G07` popup movement · `G08` wrong row · `G09` duplicate target OCR · `G10` OCR corruption (single-glyph substitution) · `G11` whole-screen false positive (fake `儲存全部` elsewhere) · `G12` click outside popup · `G13` click on neighboring row · `G14` focus theft · `G15` postcondition timeout · `G16` fake chooser-like surface · `G17` unexpected filesystem write (attribution fixture) · `G18` zero-byte burst · `G19` partial download (partial suffixes / stalled growth) · `G20` duplicate files (58th file / duplicate SHA) · `G21` process restart (crash-injection → resume in observe-only mode) · `G22` multi-display transform (fail-closed on this single-display machine).
- Extensions: `X01` stale AX element after re-layout · `X02` popup drawn inside main window vs separate window · `X03` event posted while target window is inactive.

Each scenario has: fixture/scenario id, expected verdict, fail-closed behavior, evidence path. The suite must be deterministic across two runs (semantic equality).

## REVIEW_PLAN

Stage-02 plan review (this plan; fresh context) → then, after implementation and calibration, before the live run, fresh independent reviews (each with frozen SHA bindings). The W2-frozen artifacts are mandatory review inputs: (a) the capture per-state rule + tolerance, (b) postcondition cadence/bounds with the measured panel latency, (c) the chooser-affirmation predicate incl. resolved hosting shape and ownership/pid-reuse semantics, (d) the tripwire-attribution rule, (e) the restart fixture definition; fresh read-only LINE reconnaissance results feed reviews 1, 4 and 6 where applicable. Reviews:
1. sensor/perception design (R2, R4, R5, R6),
2. coordinate transform model (R9),
3. Quartz actuator (R8),
4. postcondition model (R15),
5. action-risk classification (R14),
6. chooser automation (R16),
7. transaction/recovery policy (R18, R13),
plus 8. the adversarial matrix results (R10/R12) and 9. the reconciliation-barrier supersession argument (R24).
Production execution is permitted only if all required reviews approve the exact frozen implementation (SHAs recorded in each review artifact). Reviews that find issues → repair → re-review (no invariant weakening). Three consecutive reviews identifying the same unresolved architectural dependency → `BLOCKED_WITH_ROOT_CAUSE` with the exact external dependency named. A change to any frozen W2 rule after review approval is a semantic change → replan + fresh review, never an implementer edit.

## RECONCILIATION_BARRIER_SUPERSESSION

The Rev27d barrier exists because the attempt-07 Save All dispatch had no observable postcondition and no affirmative non-activation proof; the old actuation path (`sky.click`, window-relative coordinates, compiled native service) could not establish whether the event reached the target row.

Rev28 supersedes it by changing the actuation architecture itself, not by reinterpreting the old evidence:
- coordinates are freshly derived from the current frame and transformed by one reviewed component with an explicit scale/bbox record;
- the event is a real Quartz system event at screen-global coordinates, with a pre/post revalidation and a physical hit-test proof in the synthetic harness;
- the success acknowledgement is the directly observed chooser, not a click return;
- the production run has a fresh, goal-scoped authorization for exactly one Save All on exactly this album, and it consumes no historical budget (the historical Save All budget stays consumed for the old path).
- The attempt-07 classification `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE` is preserved and not reinterpreted; its forensic value (the old path's behavior) is explicitly the reason a new path is required.

This argument is reviewed (Review 9) before any live dispatch. If the review does not approve, no live Save All occurs.

## LIVE_RUN_ENVELOPE

Applies only after gates (a)–(f): (a) capability probe PASS, (b) harness calibration PASS, (c) replay complete, (d) adversarial suite PASS, (e) all seven topic reviews + adversarial review APPROVED on frozen SHAs, (f) live preflight (LINE launchable; the accepted baseline path resolves, matches `baseline-content-multiset.json.source_dir`, and both baseline digests recompute to `b7debe92…`/`ee958e64…`; staging run created empty; ledger armed; TCC grants re-verified in the executable context). Phase A below then produces gate (g) — the reconnaissance gate — which must PASS before Phase B.

**Phase A — read-only LINE reconnaissance (before the production phase; zero side-effecting dispatches):** launch/activate LINE and navigate with the frozen locators only up to `ALBUM_DETAIL_VERIFIED`; optionally open the album ellipsis popup and dismiss it with Escape (never activate a row); record window inventory, popup kind, AX exposure, OCR labels, fresh geometry. It resolves the LINE-specific open questions (§ENVIRONMENT_AND_CAPABILITY_MATRIX) and its evidence is bound by SHA. Any failure here is a normal pre-live gate result (repair/replan), not a consumed live budget.

**Phase B — production run.** Counters are per operation type (all other operations zero): Save All dispatch = 1; destination confirmation = 1 — these are the run's only two irreversible dispatches, each exactly once and never retried; no historical coordinates. Reversible navigation (incl. ellipsis/menu re-open) follows `REVERSIBLE_NAVIGATION`: ≤3 attempts per identical blocker with fresh preconditions, global reversible-dispatch ceiling = 12 for the run (ledger-counted), whichever binds first — exceeding the ceiling → `ABORTED_REVERSIBLE_BUDGET_EXHAUSTED`. All live captures/OCR extracts stay in the untracked evidence dir and are never pushed.

Abort conditions (stop immediately, zero further input): wrong album/group identity at any gate; baseline digest change; staging precondition failure; identity/transform invariant failure; chooser not observed within the postcondition window; an **unattributable** post-dispatch filesystem write outside staging (§10 attribution rule); focus/identity state that cannot be freshly verified; two consecutive failed revalidations of the same candidate.

On abort: preserve all evidence, write the scoped terminal state (`INDETERMINATE_*`/`ABORTED_*`), do not retry irreversible ops, report honestly.

## IMPLEMENTATION_WAVES

1. **W1 (CORE, no GUI):** package skeleton, capability probe CLI, coordinate transform + tests (validated-tolerance capture rule from RV-01, never exact equality), OCR engine wrapper + fixtures, capture layer + bbox/config records, identity binding + tests.
2. **W2 (CORE, harness):** synthetic harness app + separate-process occluder helper + driver; prove the capture per-state matrix and **freeze its rule/tolerance**, transforms, Vision localization, Quartz routing, postcondition detection + **latency/bounds freeze**, AX chooser observation + **affirmation-predicate freeze**, focus theft, tripwire attribution, restart/observe-only fixture. The frozen artifacts are review inputs.
3. **W3 (CORE, offline):** structural locators (album/detail/count/ellipsis/menu/Save All/chooser) + historical replay (fixture manifest with SHAs) + registration/stability incl. rectangle tracking + unit tests.
4. **W4 (CORE, policy):** state machine, risk classes, ledger (incl. `saveAllEmpiricalClassRecord`), staging verifier with the exact RV-02 predicate and the named mismatch classes, chooser driver, postcondition monitor + tests.
5. **W5 (CORE, hardening):** adversarial matrix (G01–G22 + X01–X03) end-to-end in harness + deterministic reruns + defect repair.
6. **W6 (SUPPORTING):** architecture doc, capability matrix, replay report, deliverable manifest, handoff.
7. **W7 (CORE, conditional):** Phase A reconnaissance gate → Phase B single live run under the envelope; then filesystem/content verification; final report; local commits.

## CHANGE_MAP

Added: `rev28/**` (Swift package), `evidence/20260925-rev28-native-closed-loop/**`, this task dir. Modified: none outside these (`.gitignore` gets one line for `rev28/.build/`). Untouched: everything listed in DO_NOT_TOUCH.

## VERIFICATION_AND_ACCEPTANCE

- Unit: geometry, identity, locators, verifier, ledger, risk classes, state machine (deterministic, no GUI).
- Integration: harness scenarios (above) with SHA-bound evidence bundles.
- Offline replay: documented above.
- Live: the run ledger + captures + AX reads + filesystem manifest + content comparison.
- Independent acceptance (Stage 05): verify CORE acceptance first — correct album identity, reviewed actuation, chooser postcondition observed, unique staging, exactly-57 stable decodable files, content equal to the recorded baseline reference → `DUPLICATE_CONTENT_CONFIRMED`, baseline unchanged, no unexplained side effect. The verifier recomputes the staging multiset and both baseline digests (name-excluded reference and name-inclusive tripwire) from disk itself and modifies nothing.

### Verification-item schema (v4.2 §7.3, committed at plan level)

No broad repository-wide gates are planned: every check below is bespoke. `BASELINE_REQUIRED: NO` and `CLOSURE_GATE ≠ BASELINE_DELTA` for every item (no pre-change broad-gate baseline is used; the baseline comparison is itself the success predicate and is tracked as its own subject). `WAIVER_ALLOWED: NO` / `WAIVER_AUTHORITY: NONE` for every item at plan time (only the owner could define a waiver before mutation, and none is planned), so the default `WAIVER_STATUS` is `NOT_ALLOWED`.

`CLOSURE_GATE` uses the canonical §7.3 enum (`HARD_CLEAN | BASELINE_DELTA | NON_GATING`) and describes whether the item by itself must be clean for `TASK_CLOSURE`; `LIVE_RUN_INTERLOCK` is this plan's own extra column and describes whether the item must pass before the irreversible Phase B may start (a safety interlock, not a closure claim). The two are independent and neither changes `GOAL_CRITICALITY`; a `NON_GATING` item may still be a hard interlock (e.g. the adversarial suite), which is deliberate — such items protect the one-shot run without inflating closure semantics.

| CHECK_ID | Check | GOAL_CRITICALITY | EVIDENCE_ROLE | CLOSURE_GATE | BASELINE_REQUIRED | LIVE_RUN_INTERLOCK | FAILURE_CLASSIFICATION_RULE |
|---|---|---|---|---|---|---|---|
| `V-01` | Capability probe: executable-context trust (TCC/AX in the built binary) + SC/Vision/Quartz APIs | CORE | DIAGNOSTIC | NON_GATING | NO | YES | `NOT_RUN` → pending (no Phase B); `FAIL` → replan/blocked |
| `V-02` | Harness calibration incl. frozen per-state capture rule | CORE | DIAGNOSTIC | NON_GATING | NO | YES | `FAIL` → repair/replan (semantic change) |
| `V-03` | Capture-geometry invariants honored in live frames | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | YES | any unexplained INVALID frame → abort |
| `V-04` | Postcondition direct observation (frozen predicate, bounded window) | CORE | OUTCOME | HARD_CLEAN | NO | YES | `SAVE_ALL_POSTCONDITION_CONFIRMED`, `NO_CHOOSER_OBSERVED`, or `CHOOSER_OBSERVED_AFTER_WINDOW` per §10 |
| `V-05` | Chooser identity + exactly-once confirmation | CORE | OUTCOME | HARD_CLEAN | NO | YES | refusal → `INDETERMINATE_CHOOSER_REFUSED` (cause enum incl. `frozen_predicate_mismatch`) |
| `V-06` | Staging predicate (57 / stable / decodable / 17,924,900 B / multiset) | CORE | OUTCOME | HARD_CLEAN | NO | YES | named mismatch classes (§12) |
| `V-07` | Baseline unchanged: path resolution + both digests + mtimes | CORE | MUST_NOT_BREAK | HARD_CLEAN | NO | YES | unresolvable/mismatch → `CHECK_RESULT: BLOCKED`; delta → abort + report |
| `V-08` | Replay + adversarial suites (G01–G22, X01–X03) | SUPPORTING | DIAGNOSTIC | NON_GATING | NO | YES | failure → repair before Phase B |
| `V-09` | Reviews: 7 topics + adversarial + barrier supersession | CORE | DIAGNOSTIC | HARD_CLEAN | NO | YES | `REVISION_REQUIRED` → repair + re-review |
| `V-10` | Stage-05 independent acceptance (recompute from disk) | CORE | OUTCOME | HARD_CLEAN | NO | NO (gates closure itself) | recompute-from-disk mismatch → fail/replan |
| `V-11` | Preservation audit (do-not-touch, no pycache, no push) | SUPPORTING | REPOSITORY_HEALTH | NON_GATING | NO | NO | violation → stop + report |

`CHECK_RESULT` defaults to `NOT_RUN` at plan level and is recorded per item in `execution.md` (Stage 04) and the Stage-05 report; the final report carries the v4.2 subjects separately (PRIMARY_OUTCOME / IMPLEMENTATION / CORE_ACCEPTANCE / REQUIRED_VERIFICATION / INDEPENDENT_ACCEPTANCE / TASK_CLOSURE) with scoped blockers, never a naked `BLOCKED` and never `DONE` from synthetic evidence.

## DEGRADATION_AND_GATE_BEHAVIOR

- Optional components (Foundation Models diagnostics, registration-based comparison, the `VNRecognizeTextRequest` parity wrapper, rectangle-tracking evidence) degrade to deterministic-only behavior without blocking the core path; the production OCR path is the Swift `RecognizeTextRequest`.
- If AX chooser navigation proves unsafe/unavailable, the keyboard path is used only after fresh identity verification and only if its reviewed test passes; otherwise the run stops at `CHOOSER_VERIFIED` with zero confirmation.
- If the postcondition window shows no chooser, the run stops as indeterminate (no retry); if the chooser is first seen after the hard cap, it stops as `CHOOSER_OBSERVED_AFTER_WINDOW` — both are permitted, non-successful, honest terminal states.
- If staging content differs from the accepted baseline, the run stops as `CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE` with the route-defect-vs-album-changed forensic split — never a success label, never a second accepted copy.
- If a frozen rule (capture tolerance, postcondition bounds, chooser predicate, attribution) would have to change to proceed, that is a replan + fresh review, not a degradation.
- Waivers: none available to the agent; every gate is explicit and reviewed (`WAIVER_ALLOWED: NO`).

## RISKS

1. LINE UI differences on macOS 27 / LINE 26.0.2 vs historical evidence (popup as separate window, album-list navigation path). Mitigation: fresh observation + harness + fail-closed locators.
2. Screen/popups may be custom-drawn with no AX exposure. Mitigation: Vision + Quartz primary for LINE surfaces; AX where real.
3. Another agent session on this machine (observed: a second Terminal/Codex window) may steal focus or occlude. Mitigation: pre-dispatch activation + revalidation; focus-theft recovery; harness-tested.
4. The single live Save All may produce no chooser again (attempt-07 shape). Consequence: indeterminate terminal state, budget consumed, no retry. This is accepted and pre-declared; it does not justify weakening the postcondition rule.
5. LINE launch may require user interaction (session/login). If so, this is a genuine external dependency → report `BLOCKED_WITH_ROOT_CAUSE` (after 3-cycle audit) rather than asking the owner casually.
6. Download may take long or LINE may throttle; verifier waits with bounded patience and reports indeterminate rather than declaring success.
7. Capture geometry: shadow-bearing/default configurations inflate the image up to ~56 pt/side (round 2) and `SCWindow.frame` is unstable in unsettled states (round 1 P6). Mitigation: explicit `ignoreShadows=true` for geometry, recorded per-capture bbox, W2-frozen per-state rule, fail-closed on unexplained deltas.
8. LINE reconnaissance may find a popup/locator shape not covered by a frozen branch (e.g. in-window drawing, no AX exposure). Mitigation: reconnaissance is a pre-live gate with its own repair/replan loop — it cannot consume the single production Save All budget.
9. Concurrent machine activity (another agent/session observed at probe time) may occlude or steal focus, or write under `~/Downloads`. Mitigation: separate-process occluder + focus-theft harness proofs; pre-dispatch revalidation; §10 attribution rule with a pre-dispatch environmental baseline; fail-closed only for unattributable writes.

## ACCEPTED_TERMINAL_STATES_AND_CLOSURE

Accepted terminal states of the Rev28 route:
(a) the live run completes and proves `DUPLICATE_CONTENT_CONFIRMED` with baseline unchanged and no unexplained side effect → `REV28_END_TO_END_LINE_ALBUM_BACKUP_VERIFIED`;
(b) a scoped, honestly-reported terminal state — `CHOOSER_OBSERVED_AFTER_WINDOW`, `NO_CHOOSER_OBSERVED`, `INDETERMINATE_CHOOSER_REFUSED` (cause enum incl. `frozen_predicate_mismatch`), `CONTENT_MISMATCH_AGAINST_ACCEPTED_BASELINE`, `STAGING_INCOMPLETE`/`STAGING_EXTRA_FILES`/`STAGING_DUPLICATE_CONTENT`/`STAGING_UNSTABLE`, `ABORTED_*` (incl. `ABORTED_UNATTRIBUTED_FILESYSTEM_WRITE`, `ABORTED_WRITE_OUTSIDE_APPROVED_ROOT`, `ABORTED_REVERSIBLE_BUDGET_EXHAUSTED`), `INDETERMINATE_*`, or `BLOCKED_WITH_ROOT_CAUSE` (only after the audit threshold) — with all evidence preserved. A run that records `ATTRIBUTED_EXTERNAL_WRITE_OBSERVED` may still succeed only if the write is disclosed as a side-effect observation in the ledger and the final report (never silently absorbed).

Case (b) is an accepted terminal state, **never "Done"**: `PRIMARY_OUTCOME_STATUS` is NOT_ACHIEVED (or UNKNOWN where evidence is incomplete) and `TASK_CLOSURE_STATUS` follows the v4.2 §7.7/§7.8 routing; `DONE` requires primary-outcome achievement per §7.10.

Task closure additionally requires: frozen-SHA reviews, deliverable manifest, replay results, adversarial results, ledger, handoff, local commits (no push), and the closeout audit per the v4.2 status contract.

## STATUS_SEMANTICS_AND_CLOSURE_ROUTING

Per the harness status contract: PRIMARY_OUTCOME (Rev28 verified route), IMPLEMENTATION (engine + harness), CORE_ACCEPTANCE, REQUIRED_VERIFICATION, INDEPENDENT_ACCEPTANCE, TASK_CLOSURE are tracked as separate subjects. A passed synthetic suite never implies a live result; a live run without the filesystem/content proof never implies BACKUP_COMPLETE/duplicate-confirmed. `IMPLEMENTATION_BLOCKED` is reserved for unfinished product implementation that cannot safely continue; blocked results always name scope/subject.

The final report additionally states, per the goal: which sensing API was used; which visual API was used; which actuation API was used; why the event reaches the intended window; how the coordinate transforms were proved; how chooser success was directly observed; how filesystem completion was proved; whether the production run completed; whether content matched the accepted baseline; and whether any ambiguity remains.

## DELIVERABLES_MAP (goal → artifact)

- Rev28 architecture document → `rev28/ARCHITECTURE.md`
- macOS 27 capability matrix → `rev28/CAPABILITY-MATRIX.md` + probe evidence
- native Swift automation engine → `rev28/Sources/Rev28Core/**` + `rev28ctl`
- synthetic AppKit harness → `rev28/Sources/rev28harness/**` + evidence bundles
- Vision locator tests, coordinate-transform tests, Quartz actuator tests, postcondition tests → `rev28/Tests/**` + evidence
- historical replay results → `evidence/20260925-rev28-native-closed-loop/replay/**`
- adversarial tests → `evidence/20260925-rev28-native-closed-loop/adversarial/**`
- review artifacts → `evidence/20260925-rev28-native-closed-loop/reviews/**`
- live-run evidence (if authorized gates pass) → `evidence/20260925-rev28-native-closed-loop/live-run/**`
- filesystem manifest + transaction/reconciliation ledger → same dir
- handoff document → task dir `handoff.md`
- final local commits → repo commits (no push)
