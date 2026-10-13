# Runtime Entry-Point Verification

**Classification: `PRODUCER_OR_BINDING_MISSING`**

This is a bounded, read-only source and artifact-presence review. Inspected source hashes identify the current local working-tree bytes, which differ from the verified b7 evidence branch for several tracked files and include untracked Q files; the branch-base comparison is explicit in the manifest. It did not run the Controller, Harness CLI, task runner, native executable, LINE, CUA, or any GUI action. No screenshot/AX payload, grant contents, token, or private task evidence was interpreted or uploaded. The archived `raw/local-main.swift` source copy was hash-checked only; its contents were not opened for this review.

The accepted Harness v4.8.0 task state remains: `TASK-4acb4326ea2a4c50ace6f333f2de8751`, issue `a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5`, c6 `c6c6b55d-865f-467b-94ba-3fd669df97ec`; c6 consumed count 1 and retries 0; task BLOCKED with no `next_stage`; issue WAIT_HUMAN; 28 original gates; G0 BLOCKED; G1–G3 NOT_RUN. The original issue criterion is pinned by SHA-256 `9b5b171e37e828f325b004b6a8a91d7ceae6ef52b36b2a4270ce6c4f8d4db657` (142 UTF-8 bytes): “Exact current contract/path and full runtime task-module closure agree in JS/Python/Swift, then the original formal build/probe/gates proceed.” This review does not attest that criterion as satisfied.

| Required status | Finding |
|---|---|
| `SOURCE_EXISTS` | YES. The selected local task JavaScript/Python sources and the `rev28` Swift package/source are present. The archived `Q/evidence/.../raw/local-main.swift` copy has the same hash as `rev28/Sources/rev28ctl/main.swift`; the active package source is the latter, not the archived evidence copy. |
| `BUILT_BINARY_EXISTS` | YES, elsewhere. arm64 Mach-O `rev28ctl` files exist in `rev28/.build/.../debug` and in the separate `live-grounding-03` continuation. The expected `minimal-live-08/bin/rev28ctl` is absent. Existing binaries were identified and hashed, never executed. Build provenance tying either binary to the `minimal-live-08` task binding is not established. |
| `RUNTIME_BINDING_VERIFIED` | NO. The selected task-root grant files and `runtime-binding.json` are absent. The existing preflight code requires these artifacts and checks a complete JS/Python/Swift source and binary inventory. |
| `LIVE_PRODUCER_EXECUTED` | NO. No execution or producer receipt was sought or produced in this review. |
| `GUI_AUTHORIZED` | NO. GUI scope for this review was NONE. No live session, app foreground handoff, or current authorization was inspected or invoked. |
| `NOT_VERIFIED` | A live entry caller, genuine CUA app/session injection, current task-root grant, exact bound producer binary, complete runtime closure, producer execution, and original-criterion proof remain unverified. |

## Bounded call-chain trace

The selected task root is `harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/` (abbreviated **Q** below). Its `live_entry.mjs` exports `createLiveEntry`; it is a factory, not a command-line `main`. It accepts an injected `app`, checks exact project/task roots and the expected producer path, requires `app.getAXStateAndScreenshot`, and calls `cli.preflight()` before constructing the producer/analyzer/classifier (`live_entry.mjs:13–40`). Its returned `probe()` snapshots state/ledger hashes around `observer.observe()`, then calls `checks/validate_real_frame.py` and retains a real-link result (`:41–56`). Its returned `runTwoAlbums()` additionally requires explicit LINE foreground handoff and a complete set of injected grounded `liveActions` (`:58–69`). In the bounded search of Q and the checked `scripts/` and `tests/` callers, no production caller invoking `createLiveEntry()` or `runTwoAlbums()` was found; the checked test imports the adapter, not this entry factory. Therefore source composition exists, while the host-to-session caller edge is not evidenced.

`host_io.mjs` provides a Node process wrapper and filesystem RPC (`host_io.mjs:12–31, 52–72`). It delegates `RUN`, `MKDIR`, and `PUBLISH` requests to Q's `tools/host_process.py`; the latter admits only the configured Python executable or the exact Q path `bin/rev28ctl`, uses `shell=False`, and scopes writes to Q evidence/input locations (`host_process.py:27–35, 71–85`). These are source-level controls, not evidence of an OS sandbox or actual host invocation.

The task runner's `createCli()` invokes `python -B -m line_backup_batch.cli` after `runtimeGate()` succeeds (`live_runner.mjs:177–207`). That Python package is the LINE batch transaction CLI and `Service`, not the Universal Harness Controller CLI. Separately, `Q/tools/native_bridge.py` imports `CandidateController` and its `prepare_plan()` allocates/publishes a Harness PLAN (`native_bridge.py:20–24, 60, 119–122`; SHA in the manifest). That is Controller admission/planning tooling; no checked call edge connects it to `createLiveEntry`, CUA capture, or the Swift producer. Do not treat either Python entry as proof that an approved Controller allocated or ran this live producer path.

The Swift package also contains a separate `rev28ctl live-preflight|live-execute` command branch (`main.swift:105–121, 342–378`). The checked branch explicitly refuses `live-execute` as legacy-disabled and requires its own config plus one-shot authorization; `live-preflight` builds a native `LiveCompositionFactory` using that separate authorization/config. The inspected Swift command contains no call to Q's JavaScript classifier and is not a caller for Q's `createLiveEntry()`. The presence of a separate Swift preflight executable therefore does not supply the missing original-task CUA host/session entry or prove original task/module/contract closure. `Package.swift` declares Swift tools 6.3 and macOS 26.0; no build or executable version query was run.

If a genuine app object is supplied, the CUA adapter's `createHostedSession()` requires the documented app capture and input methods (`line_backup_cua_adapter.mjs:111–123`). Its `observe()` calls `app.getAXStateAndScreenshot()` and persists the returned screenshot and AX string before invoking the classifier (`:145–175`). The `createNavigationObserver()` used by `probe()` has the same capture/retain/classify sequence (`line_backup_cua_adapter.mjs:545–597`). `createLiveEntry` wraps it with before/after native-context hooks (`live_entry.mjs:30–40`). The source therefore separates responsibilities: the screenshot/AX frame begins at the injected CUA app API; `rev28ctl native-context` reads native process/window/AX context and may OCR the already-retained supplied image (`main.swift:35–70`; `PassiveContextObservation.swift:145–167, 202–224, 520–554`). The supplementary `frame-support` path obtains a ScreenCaptureKit full-display frame and correlates it with the CUA frame (`main.swift:556–573, 1110, 1226–1260`). It is not the source of the adapter's initial CUA screenshot.

The production JS classifier consumes the CUA capture, retained AX bytes, native analysis, support reference, and session/frame identity before returning its observation (`live_classifier.mjs:48–74, 118–160, 225–242`). These source branches were inspected, not executed; their existence does not establish a live producer receipt or a passing original issue criterion.

## Binding and first G1 gap

The exact task binding predicates are visible in the selected source. `live_entry.mjs` supplies Q's expected `bin/rev28ctl` and grant path, requires an injected app, and stops at `cli.preflight()` before it constructs the analyzer/producer. `live_runner.mjs` then pins Q and the exact contract. The Python runtime validator independently expects the same task-local runtime-binding and producer paths. The Swift supplementary frame-support validator expects a different task/contract pair:

`live_entry.mjs:13–22` (SHA in manifest):

```js
export async function createLiveEntry({app,repoRoot=PROJECT_ROOT,runRoot=TASK_ROOT,pythonBin=PYTHON,
  producerBinary=path.join(TASK_ROOT,'bin/rev28ctl'),authorization=CON+'/live-grant-1.json',
  liveActions=null,foregroundHandoff=null}) {
  need(repoRoot===PROJECT_ROOT&&runRoot===TASK_ROOT&&pythonBin===PYTHON&&producerBinary===path.join(TASK_ROOT,'bin/rev28ctl'),
    'LIVE_ENTRY_ROOT_BINDING');
  need(app&&typeof app.getAXStateAndScreenshot==='function','GENUINE_APP_REQUIRED');
  const config=JSON.parse(await io.readFile(path.join(repoRoot,'config/line_backup_config.json')));
  const retain=createRetain({io,repoRoot});
  const cli=createCli({io,runProcess:supervisedProcess,repoRoot,pythonBin,authorization});
  const authority=await cli.preflight();
```

`live_runner.mjs:75–87` (SHA in manifest):

```js
  need(grant.grant_version==='line-batch-execution-grant-2'&&grant.fixture===false
    &&grant.project_root===repoRoot&&grant.artifact_dir===CON,'GRANT_V2_REQUIRED');
  need(grant.contract_path===contractPath&&grant.contract_sha256===contractSha256
    &&grant.native_binary_sha256===decoderSha256,'GRANT_CONTRACT_BINDING');
  const contractRaw=await readBounded(io,path.join(repoRoot,contractPath));
  need(sha256(contractRaw)===contractSha256,'GRANT_CONTRACT_DRIFT');
  const runtimeRaw=await readVerified(io,repoRoot,grant.runtime_binding,'RUNTIME_BINDING_DRIFT');
  const runtime=JSON.parse(decoder.decode(runtimeRaw));
  need(Object.keys(runtime).sort().join(',')==='contract_path,contract_sha256,files,memberships,project_root,source_sha256,task_id,version'
    &&runtime.version===1&&runtime.task_id===grant.task_id&&runtime.project_root===repoRoot
    &&runtime.contract_path===contractPath&&runtime.contract_sha256===contractSha256
    &&runtime.source_sha256===grant.source_sha256,
    'RUNTIME_BINDING_MISMATCH');
```

`src/line_backup_batch/cli.py:52–70` (SHA in manifest):

```python
def validate_runtime_binding(reader,grant):
    """Verify the complete frozen task source closure before live authority is used."""
    from .observations import artifact
    from .store import SOURCE_PATHS
    ref=grant.get('runtime_binding')
    require(isinstance(ref,dict) and set(ref)=={'path','bytes','sha256'}
        and ref.get('path')==CONTINUATION+'/runtime-binding.json','RUNTIME_BINDING_REQUIRED')
    raw=artifact(reader,ref)
    manifest=strict_json(raw,'INVALID_RUNTIME_BINDING')
    require(isinstance(manifest,dict) and set(manifest)=={'version','task_id','project_root','contract_path',
        'contract_sha256','source_sha256','memberships','files'} and manifest.get('version')==1
        and manifest.get('task_id')==grant['task_id'] and manifest.get('project_root')==grant['project_root']
        and manifest.get('contract_path')==CONTRACT_PATH and manifest.get('contract_sha256')==CONTRACT_SHA256
        and manifest.get('source_sha256')==grant['source_sha256'],'RUNTIME_BINDING_MISMATCH')
    binary=grant.get('producer_binary')
    require(isinstance(binary,dict) and set(binary)=={'path','bytes','sha256'}
        and binary.get('path')==CONTINUATION+'/bin/rev28ctl','PRODUCER_BINARY_BINDING')
    binary_path=Path(reader.root,binary['path']).resolve(strict=True)
    require(binary_path.is_file() and os.access(binary_path,os.X_OK),'PRODUCER_BINARY_UNAVAILABLE')
```

`rev28/Sources/rev28ctl/main.swift:993–1004` (SHA in manifest):

```swift
    let expectedContractPath = "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan-contract.json"
    let expectedContractSHA = "d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219"
    guard Set(grant.keys) == grantKeys,
          grant["grant_version"] as? String == "line-batch-execution-grant-2",
          grant["task_id"] as? String == "TASK-20261010-line-v3-live-e2e",
          grant["project_root"] as? String == root.path, grant["fixture"] as? Bool == false,
          grant["contract_path"] as? String == expectedContractPath,
          grant["contract_sha256"] as? String == expectedContractSHA,
          grant["artifact_dir"] as? String == "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03",
          (grant["operations"] as? [String])?.contains("frame_support") == true else {
        throw FrameSupportCommandError.refused("execution grant is not the frozen v2 authority for frame-support")
    }
```

`line_backup_cua_adapter.mjs:577–596` (SHA in manifest):

```js
    const rawCapture=await app.getAXStateAndScreenshot({emit:false,disableDiffing:true});
    const ended=clock(),requestEndedAtUtc=new Date().toISOString();
    requireFact(Number.isFinite(started)&&Number.isFinite(ended)&&ended>=started&&typeof rawCapture?.state==='string',
      'CAPTURE_INCOMPLETE');
    const screenshot=normalizeScreenshotBytes(rawCapture.screenshot);
    const capture=Object.freeze({...rawCapture,screenshot});
    const frameId=sha(screenshot);
    const monotonicInterval=Object.freeze({start_ms:started,end_ms:ended,duration_ms:ended-started});
    const saved=await retain({screenshot,ax:capture.state,frameId,sessionId,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    verifyFrameReference(saved,frameId,screenshot.byteLength);
    const afterContext=hasCaptureContextHooks?await afterCapture({capture,saved,frameId,sessionId,
      sourceBinding:beforeContext,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,monotonicInterval}):null;
    const sourceBinding=hasCaptureContextHooks?Object.freeze({before:beforeContext,after:afterContext}):null;
    const capturedContext=sourceBinding;
    const observation=await classify({capture,saved,frameId,sessionId,sourceBinding,capturedContext,capturedAt:requestStartedAtUtc,
      requestStartedAtUtc,requestEndedAtUtc,monotonicInterval});
    requireFact(observation.frame_id===frameId&&observation.session_id===sessionId,'CLASSIFIER_FRAME_MISMATCH');
    latest=Object.freeze({started,capturedAt:requestStartedAtUtc,requestStartedAtUtc,requestEndedAtUtc,
      monotonicInterval,frameId,capture,saved,observation});return observation;
```

These are literal source excerpts from the listed local working-tree hashes, not source copies in the evidence branch. The line-numbered paths and hashes above are the verification anchors.

The current task runner pins the plan contract at Q's controller path and SHA-256 `a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc` (`live_runner.mjs:9–14`; the file at that exact path was hash-checked). `runtimeGate()` requires a non-fixture grant with Q as artifact directory, the exact contract path/hash, and the expected decoder hash (`:70–80`). It then reads and validates `runtime_binding`, matches the runtime/task/contract fields, verifies current Python bytes, and requires `grant.producer_binary.path` to equal `Q/bin/rev28ctl` with matching byte length and SHA (`:81–101`). It also compares product/task-module memberships, package manifest, Python path, all Swift source inventory entries and all listed source digests (`:102–169`). The Python batch CLI has corresponding grant and runtime-binding validation (`src/line_backup_batch/cli.py:52–113, 115–161`).

Read-only existence checks found all three expected Q artifacts absent: `live-grant-1.json`, `live-grant-2.json`, `runtime-binding.json`; `Q/bin/rev28ctl` and Q's `bin/` directory are absent. The current contract file itself exists and matches its pinned SHA. The expected `image_decode` binary exists with the hash pinned by the Q runner. The configured Python 3.13 executable exists, resolves to its configured path, and has a measured file hash, but its required runtime-inventory membership/hash cannot be verified without the missing binding. No grant contents or secrets were printed. With no grant, no task runtime binding can be established; with no Q-bound producer executable, the runner's preflight cannot bind the native binary to this task.

There is also a source-level contract mismatch for the supplementary native producer. The Q runner's pinned contract is `a043…dffc` under Q, but the selected `rev28ctl` `frameSupportVerifyGrant` requires a different task ID, `live-grounding-03` artifact directory, and contract path/hash `d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219` (`main.swift:978–1003`). The Q runner passes its same authorization into `frame-support` (`live_runner.mjs:274–286`). Thus moving or rebuilding a binary at Q's expected path alone cannot make the Q grant and this Swift command agree. This static mismatch is an inference from the two independently inspected source predicates; no command was run to reproduce the refusal.

A second source-level incompatibility is in the CUA-frame-to-Swift-native-context edge. `createRetain.publish()` writes every retained byte artifact with a `.bin` suffix (`live_runner.mjs:232–241`). The analyzer passes the just-retained screenshot reference as the `--image` input after capture (`live_analyzer.mjs:35–45`). The inspected `PassiveContextObservation.loadVisual()` accepts only `.png`, `.jpg`, or `.jpeg` paths under Q's evidence directory (`PassiveContextObservation.swift:515–523`). The Swift capture catches a visual-load failure as an incomplete observation (`:220–224`), and `rev28ctl native-context` exits with 77 for incomplete output (`main.swift:54–61`); the JS analyzer requires status zero (`live_analyzer.mjs:38–39`). If the existing executable was built from these inspected local source bytes, the `.bin` path would be rejected before the JS classifier receives a complete paired native context. This is a source inference only: no producer was run, and binary-to-current-source provenance is NOT_VERIFIED.

The exact format predicates are short and directly reviewable:

`live_runner.mjs:237–241` (source SHA in manifest):

```js
    const file=`${frameId.slice(0,16)}-${(++counter).toString(36)}-${randomUUID()}.bin`;
    const rel=`${directory}/${file}`;await io.writeFile(path.join(repoRoot,rel),raw);
    const readback=await io.readFile(path.join(repoRoot,rel));
    need(readback.byteLength===raw.byteLength&&sha256(readback)===sha256(raw),'RETAIN_READBACK');
    return {path:rel,bytes:raw.byteLength,sha256:sha256(raw)};
```

`live_analyzer.mjs:35–39`:

```js
  async function native(image=null) {
    const argv=[binary,'native-context','--bundle-id','jp.naver.line.mac'];
    if(image)argv.push('--image',path.join(repoRoot,image.path),'--image-sha256',image.sha256);
    const result=await runProcess(argv,{timeoutMs:30000,cap:2*1024*1024});
    need(result.status===0&&!result.stop_reason&&result.reaped===true,'NATIVE_CONTEXT_FAILED');
```

`live_analyzer.mjs:44–45`:

```js
  const beforeCapture=()=>native();
  const afterCapture=({saved})=>native(saved);
```

`PassiveContextObservation.swift:515–524`:

```swift
        mutating func loadVisual() throws -> Visual? {
            guard let imageURL, let expected = imageSHA256 else { return nil }
            let standardized = imageURL.standardizedFileURL
            let evidenceRoot = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
                .appendingPathComponent("harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/evidence", isDirectory: true)
                .standardizedFileURL.path + "/"
            guard ["png", "jpg", "jpeg"].contains(standardized.pathExtension.lowercased()),
                  standardized.path.hasPrefix(evidenceRoot) else {
                throw CaptureError.invalidImageBinding
            }
```

`main.swift:54–61`:

```swift
        let observation = try PassiveContextObservation.capture(
            bundleID: bundleID,
            imageURL: imagePath.map { URL(fileURLWithPath: $0) },
            imageSHA256: imageSHA
        )
        FileHandle.standardOutput.write(try EvidenceIO.encodeJSON(observation))
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(observation.complete ? 0 : 77)
```

`live_runner.mjs` requires an explicit 21-entry product-source membership, an exact task-module list, `rev28/Package.swift`, the Python runtime, and producer binary; it walks `rev28/Sources/Rev28Core` and `rev28/Sources/rev28ctl` and requires every discovered Swift source in the runtime file inventory (`:102–169`). `rev28/Package.swift` declares the `rev28ctl` executable target. The manifest needed to prove the full closure is absent, so no JS/Python/Swift equality claim is made. A small archived raw-source copy is not a substitute for the current runtime-binding inventory.

The accepted Controller/task state is **G0 BLOCKED**; this review did not independently reassess its authority rationale. Separately, GUI authority for this review was NONE and no GUI action was attempted. The first technical G1 gap is **no evidenced host/session caller with a valid, mutually consistent task grant, runtime binding, and Q-bound producer**. Exact Q grants/runtime-binding and the expected executable are absent, the live entry is not shown called, and the inspected Swift frame-support authority pins another continuation. The additional `.bin` versus image-extension conflict is an independent source-level blocker before classification if the binary matches the inspected source. An arm64 binary exists elsewhere, but its existence and architecture do not bind it to this task. No build was attempted: an unrelated rebuild would not repair the missing grant, binding, caller, or observed source incompatibilities. The source package and prior binaries are not a live G1 result.

## Decision and next step

`PRODUCER_OR_BINDING_MISSING` is the single classification. The observed host is macOS 27.0.1/arm64 and the Swift package declares macOS 26.0; no build or ABI compatibility was tested. `/Applications/LINE.app` exists, but this establishes only host/app presence, not a usable CUA session, a permission grant, or UI authority. The next useful step is to obtain a separately reviewed, mutually consistent task-root runtime binding and authorized entrypoint for this exact task, with the precise Swift contract and image-format bindings resolved; then a reviewer must decide whether a bounded live read-only producer observation is authorized. Until then, G1 is blocked and G1–G3 remain NOT_RUN. No replan, runtime change, issue transition, retry, or activation is implied by this report.

## Tool and activity provenance

The report was prepared from read-only source views, bounded `rg` searches, file existence checks, `shasum`, `file`, and `lipo -info`. It did not execute project source, the Swift executable, build tooling, tests, Controller/Harness CLI, Python batch operations, or any GUI/producer/session API. No screenshot/AX payload, grant contents, raw task payload, or private absolute workstation path is included. The source identity roster and preservation anchors are in `EVIDENCE_MANIFEST.md`.
