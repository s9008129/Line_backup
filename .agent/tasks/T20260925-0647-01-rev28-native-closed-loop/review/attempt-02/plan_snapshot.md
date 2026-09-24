# Rev28 — Native macOS sensing/actuation closed-loop LINE album backup

## META

- Plan status: `READY_FOR_REVIEW`
- TASK_ID: `T20260925-0647-01-rev28-native-closed-loop`
- PLAN_REVISION: `1`
- TASK_CLASS: `CRITICAL`
- GOAL_ID: `REV28-MACOS27-NATIVE-CLOSED-LOOP-LINE-BACKUP`
- AUTHORIZATION_TYPE: `AUTONOMOUS_ARCHITECTURE_RESEARCH_IMPLEMENT_TEST_AND_BOUNDED_LIVE_EXECUTION`
- REVIEW_REQUIRED: `YES`
- INDEPENDENT_ACCEPTANCE_REQUIRED: `YES`
- E2E_REQUIRED: `YES` (true user-journey live run, strictly conditional on every preceding gate; if gates do not pass, the task ends in a scoped blocked/partial state and the live run does not execute)
- ACCEPTANCE_MODE: Stage-02 independent plan reviews → synthetic AppKit calibration → offline replay → adversarial suite → seven pre-live implementation reviews → single bounded production run → filesystem/content verification → independent E2E acceptance.
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
| R6 | Visual stability/registration using Vision-native capabilities; frame SHA for provenance, registered/normalized structural evidence for semantic state | SUPPORTING | registration tests on jitter fixtures |
| R7 | Foundation Models may be a diagnostic assistant only, never production click authority | SUPPORTING | design + usage log (diagnostics only) |
| R8 | Native Quartz actuator: `CGPreflightPostEventAccess`/`CGRequestPostEventAccess`, `CGEventCreateMouseEvent`+`CGEventPost`, screen-global points, `mouseMoved`→revalidate→`leftMouseDown`→`leftMouseUp` | CORE | actuator tests against harness + live evidence |
| R9 | One canonical coordinate-transform component; explicit transform record (window origin, content rect, content scale/backing scale, capture dims); no implicit 2x assumptions | CORE | transform tests incl. wrong-Retina adversarial |
| R10 | Synthetic AppKit harness proving capture (occlusion-surviving, stable coordinates, Retina scale, child/popup identification), Vision localization, transforms, Quartz routing to topmost popup, postcondition detection, AX chooser observation | CORE | harness evidence bundle |
| R11 | AX plane: semantic inspection (role/subrole/title/children/actions/focused element/window ownership); prefer exact `AXPress` when unambiguous; never AX-write to ambiguous elements | CORE | AX tests incl. ambiguity refusal |
| R12 | App activation/focus handling with post-activation verification (isActive, AX focused/main window, SCWindow identity); focus theft is a recoverable pre-irreversible condition | CORE | focus-theft adversarial tests |
| R13 | Persistent execution state machine owning recovery (states APP_READY…FINALIZED), each transition with fresh precondition, action, direct postcondition, timeout, bounded recovery, evidence | CORE | state-machine tests + live ledger |
| R14 | Action risk classes REVERSIBLE_NAVIGATION / PRE_SIDE_EFFECT_ACTION / IRREVERSIBLE_SIDE_EFFECT defined, reviewed, and applied; Save All empirically classified, never inferred from label | CORE | risk classification artifact + review |
| R15 | Save All postcondition: bounded high-frequency observation (SC + AX + window inventory + filesystem tripwire); success requires directly observed chooser; logs/panel-service presence are supporting only; no blind retry | CORE | postcondition tests + live evidence |
| R16 | File chooser via native AX semantics first; destination `…/staging/<UNIQUE-RUN-ID>/`; fresh unique run, canonicalized, inside approved root, empty at start, not baseline, no symlink escape; keyboard/Go-to-Folder only after fresh chooser identity verification; exactly-once confirmation with durable intent | CORE | chooser tests + live evidence |
| R17 | Filesystem completion: exactly 57 completed images, no subdirs/partials/zero-byte, decodable, stable across repeated samples, quiescence, manifest SHA-256, content multiset vs baseline | CORE | staging verifier tests + live verification |
| R18 | Transactional safety: fresh preconditions, durable intent, single dispatch, postcondition observation, filesystem verification, append-only ledger; unknown irreversible dispatch never blindly retried | CORE | ledger tests + adversarial |
| R19 | Bounded autonomy: identical live-state blocker ≤3 autonomous recovery cycles; implementation failures may continue while hypotheses differ; 3 consecutive reviews on the same unresolved dependency → `BLOCKED_WITH_ROOT_CAUSE`; never weaken safety invariants for approval | CORE | run ledger + review artifacts |
| R20 | Reviews: 7 named pre-live reviews + adversarial review of 23 named scenarios before production; production only if all required reviews approve the exact frozen implementation | CORE | review artifacts bound to SHAs |
| R21 | Single production run for exactly `旻謙允禎成長日記 / 2024/05/13～05/17 / 57`; destination confirmation max 1; side-effecting ops max 1; fresh coordinates only; no historical coordinate reuse | CORE | live-run ledger |
| R22 | Success condition incl. baseline unchanged, registry/evidence updated consistently, no unexplained side effect; `DUPLICATE_CONTENT_CONFIRMED` route; never claim BACKUP_COMPLETE from click/menu/chooser/count alone | CORE | final acceptance |
| R23 | Deliverables: architecture doc, capability matrix, Swift engine, harness, Vision locator tests, transform tests, actuator tests, postcondition tests, historical replay results, adversarial tests, review artifacts, live-run evidence (if authorized), filesystem manifest, transaction ledger, handoff doc, local commits | SUPPORTING | deliverable manifest |
| R24 | Reconciliation-barrier supersession argument reviewed before any new Save All | CORE | barrier section + review |
| R25 | Historical artifacts preserved byte-identical; no pycache; no push | CORE | diff/manifest audit |

## CRITICAL_PATH (smallest safe path to the primary outcome)

1. **Capability + harness first** (R2, R10): prove ScreenCaptureKit capture semantics, Vision localization, the coordinate transform, and Quartz routing in a synthetic AppKit environment before any LINE interaction.
2. **Engine core** (R3, R4, R5, R8, R9, R11, R13, R18): implement the Swift engine with deterministic pure cores and thin OS edges.
3. **Offline validation** (R5, R6, R23): unit/integration tests + replay of historical frames through the Rev28 locators (no live input).
4. **Adversarial hardening** (R10, R12, R14, R18): the 23-scenario matrix in the harness, including fake-chooser and partial-download attacks.
5. **Independent reviews** (R14, R15, R16, R18, R20, R24): seven pre-live topics, all bound to frozen SHAs; repair and re-review until approved.
6. **Live run** (R1, R8, R15, R16, R17, R21): navigate LINE from `APP_READY` to the exact album, one ellipsis, one Save All, direct chooser observation, one confirmation into a unique staging run, download.
7. **Filesystem + content verification** (R17, R22): 57 stable decodable files; multiset equal to baseline → `DUPLICATE_CONTENT_CONFIRMED`; baseline unchanged.
8. **Closeout** (R22, R23): ledger, manifests, handoff, final report, local commits.

Ordering rule: any step that cannot proceed does NOT block unrelated steps; only the irreversible production step has a hard prerequisite chain (steps 1–5).

## VERIFIED_REPOSITORY_FACTS (this round, read-only)

- HEAD `766b22c4f8bf29b9d0a46049c75309c70593d66d` = `origin/master`; ahead 0. Working tree: no tracked modifications; untracked Rev27e WIP + prior evidence preserved.
- Issue SHA-256 verified as above.
- Accepted baseline `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to-2024-05-17_57`: 57 files, 17,924,900 bytes; manifest digest recomputed on disk this round = `b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd` (method: sorted `relpath\tsize\tsha256` lines, SHA-256 of the concatenation) = MATCH. READ-ONLY.
- Staging `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260923-111908-01/`: exists, 0 entries, 0 bytes. PRESERVE (no cleanup without separate authorization).
- Historical classification remains `SAVE_ALL_SEMANTIC_EFFECT_INDETERMINATE`; reconciliation barrier remains open until a reviewed Rev28 supersession passes.
- Historical success RUN-20260907-154331-01: Save All → macOS **folder chooser** appeared → Go to Folder with exact destination → one confirmation → download `0/57` → 57 files. Historical failure precedents: click missed Save All; returned-without-chooser (2025-09-08, same shape as attempt-07); wrong-row activation (Rename). No historical coordinate may ever be reused.
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
| `SCScreenshotManager.captureScreenshot` + `SCScreenshotConfiguration` (macOS 26 API) | works; `includeChildWindows=false` → px = frame×scale exactly; `includeChildWindows=true` → px = union(frame, child windows)×scale | probe output (2294×1366 vs 2294×1438) |
| `SCScreenshotManager.captureImage` + `SCStreamConfiguration` (legacy) | works but default size is 1920×1080; explicit dimensions required | probe output |
| Tool-process GUI context | `SCScreenshotManager` requires `NSApplication.shared` + run loop, else `CGS_REQUIRE_INIT` assertion crash | probe output |
| Display | single 1147×745 pt @ 2.0 | NSScreen + CGDisplay |
| Vision Swift API | `RecognizeTextRequest`, `DetectRectanglesRequest`, `GenerateImageFeaturePrintRequest`, `RecognizeDocumentsRequest`, registration requests present in SDK interface | SDK `.swiftinterface` |
| AX / CGEvent APIs | `AXUIElement`, `AXActionConstants`, `CGEventCreateMouseEvent`, `CGEventPost`, preflight APIs present | SDK headers |
| LINE app | 26.0.2, installed; not running at probe | Info.plist |

Open capability questions to be resolved empirically (they are CORE gates for the harness, not assumptions):
- exact meaning of `SCWindow.frame` vs captured image bounds for LINE's window kinds (main, popup, panel) on this machine;
- whether LINE's popup/menu is a separate SCWindow, a child window, or drawn inside the main window surface;
- whether AX exposes the album ellipsis / popup / Save All rows (historically mostly custom-drawn);
- AX surface of the native folder chooser on macOS 27 (roles, subroles, the Go-to-folder affordance, default button);
- behavior of `AXIsProcessTrusted` inside a compiled SwiftPM executable vs the current privileged shell (probe used the shell's trust context).

## SOURCE_OF_TRUTH

1. Current user goal text (this plan's contract) and the verified repository/issue anchors.
2. Live macOS/SDK behavior demonstrated by capability probes and harness tests on this machine.
3. Repository evidence for historical facts (labeled `[HISTORICAL]`), never as live coordinates.
4. Reviewed Rev28 implementation and its frozen SHAs.
5. Anything unproven is labeled `[UNVERIFIED]` and fails closed at gate level.

## CONSTRAINTS_NON_GOALS_AND_DO_NOT_TOUCH

- Non-goals: no changes to the accepted baseline; no second accepted production copy; no cleanup/deletion of staging or baseline without separate authorization; no push; no `__pycache__`/`*.pyc` additions; no modification of other agents'/owner's unrelated work; no reclassification of attempt-07; no claim of BACKUP_COMPLETE without the full chain.
- Do-not-touch (byte-identical): `evidence/20260916-route/attempt-07/**`, Rev27d reconciliation artifacts, cycle-3 frozen reviewed snapshot + reviews, `ISSUE-2026-09-24-rev27e4-r2-ownership-provenance.md`, revoked/old plans, frozen tools v4–v8, the accepted baseline, `staging/RUN-20260923-111908-01/**`, all Rev27e WIP not owned by this task.
- LINE-internal inference (unified logs, panel-service presence, click-return codes) may never be the primary success condition. It may be supporting/forensic evidence only.
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
    rev28ctl/                (orchestrator CLI: probe|replay|harness|live subcommands)
  Tests/Rev28CoreTests/      (unit + harness integration tests)
```

Design rules: pure functions for geometry/matching/locators/verifiers (deterministic, testable without a GUI); thin OS edges behind protocols so the harness can substitute fakes; every OS observation produces a structured evidence record with SHA-256 and timestamps; every write is atomic (temp+rename) and append-only where it is evidence.

## ARCHITECTURE

### 1. Sensor plane (ScreenCaptureKit)

- Enumerate with `SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)`.
- Select the LINE main window by: bundle `jp.naver.line.mac`, owning pid == the target process instance, window layer == 0, on-screen, and a frame that matches the live AX main-window geometry within tolerance. Never select by windowID alone; a windowID is only valid inside one capture epoch.
- Primary capture: `SCContentFilter(desktopIndependentWindow:)` + `SCScreenshotConfiguration` with `includeChildWindows=false`, `showsCursor=false`. Primary image space = window-local points × `pointPixelScale` px, origin at `filter.contentRect.origin`.
- Popup/child/sheet observation: `includeChildWindows=true` (child windows are included by default on macOS 26+) and/or an app-level/independent-window filter for the popup's own SCWindow when it is a separate window. Every capture records which windows were included; the expected bounding box is the union of those windows' frames, and the produced image must satisfy `image.px == bbox.size × scale` (±0.5 px) or the frame is INVALID (fail-closed).
- Fullscreen/display captures (`captureImage(in:)`/display filter) are permitted only for corroboration, occlusion investigation, and actuation verification.
- Each `CapturedFrame` records: capture kind, filter description, included windowIDs, frame/bbox (pt), scale, image dims (px), monotonic epoch + wall time, SHA-256 of the PNG/raw bytes, and the bound `WindowIdentity`.

### 2. Window identity

`WindowIdentity` = {bundleID, pid, process start time (`proc_pidinfo(PROC_PIDTBSDINFO)`), windowID, window frame (pt), AX role/subrole/title (read-only), CGWindowList entry (id/frame/layer/owner), capture epoch, capture SHA-256}. Cross-checks: NSRunningApplication for activation state; AX for main/focused; CG list for frame/ordering. Identity rules:
- A perception result is only valid for the epoch it was captured in.
- Before every dispatch, re-enumerate and re-derive the target window; if windowID changed, the candidate is invalid (re-locate, do not reuse coordinates).
- Multi-display: transforms bind to the display containing the window; the harness proves behavior with a moved window; a second display is `[UNVERIFIED]` on this machine and must fail closed if a window moves outside the captured display.

### 3. Perception plane (Vision)

- OCR: `RecognizeTextRequest` (Swift) with `recognitionLevel = .accurate`, `recognitionLanguages = ["zh-Hant", "en-US"]`, `usesLanguageCorrection = false`; a `VNRecognizeTextRequest` wrapper exists for parity; both are tested on the same fixtures. Exact identity strings are compared with NFC-exact matching; `禎 U+798E` and `楨 U+6968` are never normalized or merged.
- The OCR layer returns `(text, quad, confidence)` in capture px, transformed to window-local pt by the canonical transform.
- **Separation rule:** OCR establishes *identity* (album title, `57張照片`, menu item name, chooser labels). *Geometry* for clicks comes from structural rules over OCR boxes + surface structure (row bands, safe interior, addressable rect), never from a raw character box.
- Structural locators (each fail-closed with a distinct verdict): album list surface + target card, album detail surface, count text `57張照片` (digits == 57), album-level ellipsis, popup/menu surface, `儲存全部` row (v8 invariants ported), chooser presence. Multiple matches → AMBIGUOUS (refuse).
- Registration/stability: `GenerateImageFeaturePrintRequest` distance and/or rectangle-based registration to compare surfaces across redraws/cursor changes/minor motion; frame SHA stays provenance-only. Beta APIs never become the sole production gate.

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

**Save All classification policy for THIS run:** the goal requires empirical classification and explicitly permits PRE_SIDE_EFFECT *only if proven*; at plan time it is NOT proven (historically indeterminate). Therefore Rev28 executes Save All under `IRREVERSIBLE_SIDE_EFFECT` semantics: exactly one dispatch, no retry, direct postcondition observation. The run's evidence then records the empirical classification for future runs. This is conservative in the direction of safety, and matches the authorization envelope (Save All: 1).

### 10. Save All postcondition

After the single dispatch, a bounded high-frequency observation window (cadence ≤150 ms, total ≤8.0 s, plus one late sample at ~12 s for the ledger only):
- SC captures (LINE window; full display for corroboration),
- AX window inventory for LINE pid and any panel-service pids (including a pre-dispatch census),
- `CGWindowListCopyWindowInfo` inventory,
- filesystem tripwire: any creation/modification under the staging run dir and under `~/Downloads` (read-only observation; no writes by the monitor).
Affirmative evidence = directly observed expected chooser (AX sheet/window bound to the panel-service process whose identity is established by the fresh census + timing, corroborated by SC/CG window inventory). `SAVE_ALL_POSTCONDITION_CONFIRMED` requires the direct observation; unified logs / panel-service presence / menu disappearance / click-returned are never sufficient. No affirmative within the window → `NO_CHOOSER_OBSERVED` → scoped indeterminate; **no retry** (budget consumed).

### 11. Chooser automation

- Verify chooser identity first (fresh): AX window/sheet with panel ownership pid in the freshly established panel-service set; present in CG/SC inventories; role/subrole consistent with a native open/save panel. Fake or ambiguous surfaces → refusal.
- Write durable intent (ledger, fsync) BEFORE the confirmation.
- Destination: `/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/<UNIQUE-RUN-ID>/` where `UNIQUE-RUN-ID = RUN-<yyyyMMdd-HHmmss>-<4 hex>`. Preflight: `realpath` canonicalization; must be inside the approved root; must not exist or must be empty; must not equal/contain/be-contained-by the accepted baseline; symlink components rejected.
- Navigation: AX first (locate the panel's Go-to-folder affordance, its path field, and the default button; verify values after each step). If AX cannot safely drive it: keyboard path (⇧⌘G + Unicode text entry via `CGEventKeyboardSetUnicodeString` + Return) only after fresh chooser identity verification; a clipboard-based path is NOT used unless AX and keyboard both fail under review.
- Confirmation exactly once (AXPress on the unambiguous default button; else Return key). Then verify the direct postcondition: chooser closes / download begins (filesystem tripwire).
- All chooser actions are logged with pre/post evidence and consume the single confirmation budget.

### 12. Filesystem completion

- Monitor the unique staging dir at ≥1 s cadence: file count, names, sizes, mtimes; detect partial suffixes (`.part .partial .tmp .temp .download .crdownload .incomplete .filepart`), zero-byte files, subdirectories.
- Require: exactly 57 image files; no subdirs; none zero-byte at settle; all structurally decodable (JPEG/PNG structural checks ported from the repo verifier); sizes+mtimes stable across ≥3 samples spanning ≥4 s with a quiescence interval ≥5 s after the last change; then compute the sorted manifest digest and the SHA-256 multiset.
- Compare multiset vs the accepted baseline (57 files / 17,924,900 bytes / digest `b7debe92…`). Equal multiset → `DUPLICATE_CONTENT_CONFIRMED` (success). Never copy staging into the accepted baseline.

### 13. Transactional safety

Append-only JSONL ledger `evidence/20260925-rev28-native-closed-loop/live-run/ledger.jsonl` with hash-chaining (`prev` field), one entry per observation/decision/dispatch/intent, fsync on critical entries; intent records precede irreversible actions; every artifact named in the ledger by path+SHA-256. No implicit state in memory across restarts: the state machine persists `state.json` atomically and can resume in a read-only "observe" mode after a crash, never re-dispatching an irreversible action without a fresh reviewed decision.

## COORDINATE_TRANSFORM_MODEL

Spaces: window-local points (origin = window frame top-left), screen-global points (top-left origin, points; same as CGWindow bounds / `CGEvent` coordinates), capture pixels.

Given `binding` (window frame `W`, content rect `C` == `W` for the stable main window, scale `S = pointPixelScale`), and capture bbox `B` (the union actually captured), the canonical transform is:

```
screenPt   = windowLocalPt + W.origin
capPx      = (screenPt − B.origin) × S
windowLocalPt = screenPt − W.origin
capturePx→screenPt = B.origin + capPx / S
```

Invariants checked at frame creation and before every dispatch:
1. `image.px == round(B.size × S)` (±0.5 px) — otherwise INVALID frame.
2. `B == W` when `includeChildWindows=false` (main window path).
3. `W.origin` and `B` derive from the same enumeration epoch as the frame (`windowID` + frame re-read).
4. No implicit 2×: every conversion carries its `S` and `B`; mixed-scale usage is a type-level impossibility (distinct structs for each space).
5. Rounding: dispatch points are computed in points; pixel conversions are for evidence only. If a click point falls within 1 pt of a safe-interior boundary, it is refused (re-locate).

## SYNTHETIC_HARNESS_CALIBRATION_PLAN

`rev28harness` is an AppKit app (own window hierarchy, controllable by a test driver over a local unix socket / stdio protocol):
- main window (known geometry, known internal markers, Retina-scaled content);
- a target "row" surface and a custom popup (child window) above it;
- a scenario mode that (a) moves the window, (b) opens a popup at controlled offsets, (c) brings a second NSWindow (occluder) fully over the main window, (d) presents a real `NSOpenPanel` in directory mode (chooser emulation), (e) presents a fake chooser-like window (look-alike), (f) steals focus to another app/process, (g) writes files into a temp destination (download simulation incl. zero-byte placeholders, partial suffixes, slow growth).

The harness must prove (evidence bundle with SHAs):
1. **Capture semantics**: `includeChildWindows=false/true` bbox rule (px == union×scale); capture survives full occlusion by another window; coordinates stable across captures; Retina scale reported correctly; child/popup windows identifiable either as separate SCWindows or via union bbox.
2. **Vision localization**: OCR reads the synthetic labels (`儲存全部` row inside a 5-row menu, `57張照片`, album title strings incl. `禎/楨` discrimination fixture); locators return the same safe-interior point for repeated captures; ambiguity fixtures refuse.
3. **Coordinate transforms**: window moved (± dx/dy), scale 2.0 on this machine; local→screen→px→local round-trips; wrong-scale injection is detected by invariant #1.
4. **Quartz routing**: a posted click at the popup row's screen point hits the popup (not the main window beneath), proved by the harness recording the hit-test result (popup receives the event and responds; main window must not receive it); including when the occluder is present but the popup is topmost.
5. **Postcondition detection**: chooser detector affirms the real `NSOpenPanel`, refuses the fake look-alike; postcondition timeout path produces `NO_CHOOSER_OBSERVED` without retry.
6. **AX chooser observation**: AX read of the harness `NSOpenPanel` (roles/subroles/titles/buttons), AXPress confirm path, keyboard Go-to-folder path, and post-confirmation destination verification — plus an ambiguity fixture that must refuse.
7. **Focus theft recovery**: harness steals focus; engine re-verifies before dispatch and (in test) aborts or recovers per policy without ever dispatching against the wrong window.

## HISTORICAL_REPLAY_PLAN

Offline only, using already-retained frames (attempt-07 frames/AX JSON, attempt-12/13/14/16 window frames, attempt-07 menu evidence) replayed through the Rev28 Swift locators/transform (fixtures copied read-only into the new evidence dir with SHAs):
- album list card candidate vs v6 output (agreement or documented divergence),
- album detail surface + `57張照片` identity,
- ellipsis location vs v5 output,
- popup menu + Save All row vs v8 output (candidate point within v8 `x_safe/y_safe`).
Divergences are recorded, not "fixed" by threshold tweaks; each divergence gets a hypothesis and a test.

## ADVERSARIAL_TEST_MATRIX (harness + offline)

wrong window · wrong bundle · stale windowID · wrong Retina transform · occluding app · window movement · popup movement · wrong row · duplicate target OCR · OCR corruption (single-glyph substitution) · whole-screen false positive (fake `儲存全部` elsewhere) · click outside popup · click on neighboring row · focus theft · postcondition timeout · fake chooser-like surface · unexpected filesystem write (tripwire must notice) · zero-byte burst · partial download (partial suffixes / stalled growth) · duplicate files (58th file / duplicate SHA) · process restart (state machine resume in observe-only mode) · multi-display transform (fail-closed on this single-display machine) · plus: stale AX element after re-layout, popup drawn inside main window vs separate window, and event posted while target window is inactive.

Each scenario has: fixture/scenario id, expected verdict, fail-closed behavior, evidence path. The suite must be deterministic across two runs (semantic equality).

## REVIEW_PLAN

Stage-02 plan review (this plan; fresh context) → then, after implementation and calibration, before the live run, fresh independent reviews (each with frozen SHA bindings):
1. sensor/perception design (R2, R4, R5, R6),
2. coordinate transform model (R9),
3. Quartz actuator (R8),
4. postcondition model (R15),
5. action-risk classification (R14),
6. chooser automation (R16),
7. transaction/recovery policy (R18, R13),
plus 8. the adversarial matrix results (R10/R12) and 9. the reconciliation-barrier supersession argument (R24).
Production execution is permitted only if all required reviews approve the exact frozen implementation (SHAs recorded in each review artifact). Reviews that find issues → repair → re-review (no invariant weakening). Three consecutive reviews identifying the same unresolved architectural dependency → `BLOCKED_WITH_ROOT_CAUSE` with the exact external dependency named.

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

Applies only after gates: (a) capability probe PASS, (b) harness calibration PASS, (c) replay complete, (d) adversarial suite PASS, (e) all seven topic reviews + adversarial review APPROVED on frozen SHAs, (f) live preflight (LINE launchable, baseline unchanged, staging run created empty, ledger armed, TCC grants re-verified).

Counters (all others zero): Save All dispatch = 1; chooser confirmation = 1; ellipsis open = 1 (recovery ≤3 within policy); irreversible side-effecting ops = 1; destination = 1; no retry of any irreversible op; no historical coordinates.

Abort conditions (stop immediately, zero further input): wrong album/group identity at any gate; baseline digest change; staging precondition failure; identity/transform invariant failure; chooser not observed within the postcondition window; any unexpected filesystem write outside staging; focus/identity state that cannot be freshly verified; two consecutive failed revalidations of the same candidate.

On abort: preserve all evidence, write the scoped terminal state (`INDETERMINATE_*`/`ABORTED_*`), do not retry irreversible ops, report honestly.

## IMPLEMENTATION_WAVES

1. **W1 (CORE, no GUI):** package skeleton, capability probe CLI, coordinate transform + tests, OCR engine wrapper + fixtures, capture layer + bbox invariants, identity binding + tests.
2. **W2 (CORE, harness):** synthetic harness app + driver; prove capture semantics, transforms, Vision localization, Quartz routing, postcondition detection, AX chooser observation, focus theft.
3. **W3 (CORE, offline):** structural locators (album/detail/count/ellipsis/menu/Save All/chooser) + historical replay + registration/stability + unit tests.
4. **W4 (CORE, policy):** state machine, risk classes, ledger, staging verifier, chooser driver, postcondition monitor + tests.
5. **W5 (CORE, hardening):** adversarial matrix end-to-end in harness + deterministic reruns + defect repair.
6. **W6 (SUPPORTING):** architecture doc, capability matrix, replay report, deliverable manifest, handoff.
7. **W7 (CORE, conditional):** live run under the envelope; then filesystem/content verification; final report; local commits.

## CHANGE_MAP

Added: `rev28/**` (Swift package), `evidence/20260925-rev28-native-closed-loop/**`, this task dir. Modified: none outside these (`.gitignore` gets one line for `rev28/.build/`). Untouched: everything listed in DO_NOT_TOUCH.

## VERIFICATION_AND_ACCEPTANCE

- Unit: geometry, identity, locators, verifier, ledger, risk classes, state machine (deterministic, no GUI).
- Integration: harness scenarios (above) with SHA-bound evidence bundles.
- Offline replay: documented above.
- Live: the run ledger + captures + AX reads + filesystem manifest + content comparison.
- Independent acceptance (Stage 05): verify CORE acceptance first — correct album identity, reviewed actuation, chooser postcondition observed, unique staging, exactly-57 stable decodable files, content equal to baseline → `DUPLICATE_CONTENT_CONFIRMED`, baseline unchanged, no unexplained side effect. Verifier modifies nothing.

## DEGRADATION_AND_GATE_BEHAVIOR

- Optional components (Foundation Models diagnostics, registration-based comparison, AX chooser path) degrade to deterministic-only behavior without blocking the core path.
- If AX chooser navigation proves unsafe/unavailable, the keyboard path is used only after fresh identity verification and only if its reviewed test passes; otherwise the run stops at `CHOOSER_VERIFIED` with zero confirmation.
- If the postcondition window shows no chooser, the run stops as indeterminate (no retry) — this is a permitted, non-successful, honest terminal state.
- Waivers: none available to the agent; every gate is explicit and reviewed.

## RISKS

1. LINE UI differences on macOS 27 / LINE 26.0.2 vs historical evidence (popup as separate window, album-list navigation path). Mitigation: fresh observation + harness + fail-closed locators.
2. Screen/popups may be custom-drawn with no AX exposure. Mitigation: Vision + Quartz primary for LINE surfaces; AX where real.
3. Another agent session on this machine (observed: a second Terminal/Codex window) may steal focus or occlude. Mitigation: pre-dispatch activation + revalidation; focus-theft recovery; harness-tested.
4. The single live Save All may produce no chooser again (attempt-07 shape). Consequence: indeterminate terminal state, budget consumed, no retry. This is accepted and pre-declared; it does not justify weakening the postcondition rule.
5. LINE launch may require user interaction (session/login). If so, this is a genuine external dependency → report `BLOCKED_WITH_ROOT_CAUSE` (after 3-cycle audit) rather than asking the owner casually.
6. Download may take long or LINE may throttle; verifier waits with bounded patience and reports indeterminate rather than declaring success.

## DEFINITION_OF_DONE

Primary outcome: the Rev28 route either (a) completes the live run and proves `DUPLICATE_CONTENT_CONFIRMED` with baseline unchanged and no unexplained side effect → `REV28_END_TO_END_LINE_ALBUM_BACKUP_VERIFIED`, or (b) reaches a scoped, honestly-reported terminal state (`BLOCKED_WITH_ROOT_CAUSE` only after the audit threshold; otherwise a scoped indeterminate/partial state) with all evidence preserved.
Task closure additionally requires: frozen-SHA reviews, deliverable manifest, replay results, adversarial results, ledger, handoff, local commits (no push), and the closeout audit per the v4.2 status contract.

## STATUS_SEMANTICS_AND_CLOSURE_ROUTING

Per the harness status contract: PRIMARY_OUTCOME (Rev28 verified route), IMPLEMENTATION (engine + harness), CORE_ACCEPTANCE, REQUIRED_VERIFICATION, INDEPENDENT_ACCEPTANCE, TASK_CLOSURE are tracked as separate subjects. A passed synthetic suite never implies a live result; a live run without the filesystem/content proof never implies BACKUP_COMPLETE/duplicate-confirmed. `IMPLEMENTATION_BLOCKED` is reserved for unfinished product implementation that cannot safely continue.

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
