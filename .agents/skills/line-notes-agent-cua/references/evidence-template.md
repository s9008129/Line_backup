# 記事本 evidence-pack statement 範本

本範本是 Agent 撰寫 `notes evidence-pack --statement FILE` 的人工紀錄內容，不是可直接傳給事件 evidence 參數的自由文字檔，也不是 CLI schema、parser 或語意驗證器。Agent 把這份 statement 與當次截圖／AX／input receipt／command stdout／stderr 等原件用 `evidence-pack` 封裝；成功後只把回傳的 `bundle_path` 傳給 `--evidence`、`--binding-evidence`、`--observation` 或其他證據參數。CLI 核對 v2 bundle 的結構、context 與保存子 blob 的 bytes／SHA-256，但不解析欄位語意，也不知道欄位是否真實、畫面是否屬於該 attempt，或證據是否足以判完成。

下載控制、chooser 與其原始回傳須在當下即時保存到私有任務區；intent 先持久化並讀回。需要寫入有 evidence 參數的事件前，再建立私有 statement 並封裝適用原件；同一 attempt 與 context 的原件可共用一個 bundle，只有新事實或 context 不同才另建。不要為每個 GUI 階段預先建立 bundle。context 只填該命令唯一主體的已知 ID；適用 ID 不可留 `UNKNOWN` 或誤填另一主體，未分配／不適用的欄位才由 `evidence-pack` 保持 `UNKNOWN`。`intent` 沒有一般 evidence 參數，其預檢與讀回證據留在私有任務區。無法取得的欄位寫 `UNKNOWN` 並說明原因；不要用空白、猜測、檔名或另一個畫面補值。原始證據留在專案任務所需的私有區域，不外傳。

```sh
TASK_PROJECT_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
TASK_PRIVATE_DIR="$TASK_PROJECT_ROOT/.local/line-backup/tasks/CURRENT_TASK"
STATEMENT_FILE="$TASK_PRIVATE_DIR/statement.txt"
PRIVATE_SCREENSHOT="$TASK_PRIVATE_DIR/screenshot.png"
PRIVATE_AX_CAPTURE="$TASK_PRIVATE_DIR/accessibility.json"
EVIDENCE_PARENT="$TASK_PRIVATE_DIR/evidence"
EVIDENCE_OUTPUT="$EVIDENCE_PARENT/NEW_UNIQUE_EVIDENCE_ID"
mkdir -p "$EVIDENCE_PARENT"

PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
  --statement "$STATEMENT_FILE" \
  --asset screenshot "$PRIVATE_SCREENSHOT" \
  --asset ax "$PRIVATE_AX_CAPTURE" \
  --output-dir "$EVIDENCE_OUTPUT" \
  --list-key "$LIST_KEY"
```

`--asset` 可重複，同一 role 也可出現多次；role 限 `screenshot`、`ax`、`input_receipt`、`command_stdout`、`command_stderr`、`observation`。statement 與畫面／AX 不可空；`command_stdout`／`command_stderr` 可為零 bytes。貼文層另加 `--post-key "$POST_KEY"`；媒體層再加 `--media-key "$MEDIA_KEY"` 及適用的 `--attempt-id "$ATTEMPT_ID"`／`--scan-id "$SCAN_ID"`。Owner 不需要提供 JSON、UUID、key、路徑或 hash。

## 路徑與前置條件

- 先確認 repo 的實體根目錄，再以它展開 `TASK_PROJECT_ROOT`；statement、每個 asset、要匯入的 bundle 與 output 都使用絕對路徑。不可把範例中的 `.local/...` 相對字串直接當 argv。
- statement／asset 必須是專案內 canonical regular file，不可為 symlink，且只允許一個 hard link。先由 Agent 取得或建立原件並讀回；不要讓工具自動 resolve 穿過 symlink。
- `EVIDENCE_PARENT` 必須是已存在、位於專案私有 tasks 下的 canonical directory。Agent 只建立這個父目錄；`EVIDENCE_OUTPUT` 必須是它下面尚不存在的子目錄，不可預建、不可指向既有目錄、不可覆寫。
- 以下三種拒絕原因不同，不能互換：
  - statement／asset 相對路徑：`PROJECT_LOCAL_EVIDENCE_REQUIRED`。
  - `--output-dir` 相對路徑：`NEW_EVIDENCE_DIRECTORY_REQUIRED`。
  - output 父目錄不存在：`EVIDENCE_OUTPUT_PARENT_REQUIRED`。
- 其他安全拒絕仍成立：input symlink 為 `EVIDENCE_SYMLINK_REFUSED`、多 hard link 為 `EVIDENCE_SOURCE_CHANGED`、輸出已存在為 `EVIDENCE_OUTPUT_DIRECTORY_EXISTS`、輸出逸出私有 tasks 為 `PROJECT_PRIVATE_EVIDENCE_REQUIRED`。舊紀錄沒有當時 argv 時保留 `UNKNOWN`，不要重跑一次來猜原失敗屬於哪一類。
- 成功後只把 CLI 回傳的絕對 `bundle_path` 作 context 引用。原始 GUI／AX／input receipt 與整理 statement 分開保存；statement 的說明不能冒充工具原始回傳，bundle 只核對 bytes／context，不證明畫面真實或控制命中。

## Viewer 身分與採信 gate

Agent 依當次原件核對後才寫入私有 statement。這個 gate 不是新 CLI schema、controller、GUI sensor，也不是 helper 的圖像辨識。`evidence-pack` 仍只核對 bytes、SHA-256 與命令 context；`identity_match=MATCH` 只表示 Agent 依當次原件完成核對，不表示工具看懂了截圖。

第一次看到 viewer 時，先用中性的唯一 `observation_id` 保存原始 AX／截圖並讀回，不先以 `post`、`media` 或推測的顯示名稱命名。之後從該原件讀出 viewer title 的目前 `n/N`，與既有 `list_key`、已確認的 `post_key`、`media_key`、進入 viewer 前的來源頁／entry anchor，以及任何已宣稱目標的 artifact label／目錄名交叉核對。只有在這些欄位都成立時，才可把後續證據、input 或 bundle 歸屬該 viewer。

gate 本身也要寫入私有 statement／observation 並讀回，記唯一 `identity_gate_id` 與各來源 ref；只在對話記憶或 runtime 變數中完成不算持久 MATCH。每個新的 viewer、頁面切換、媒體切換或擬建立 input／intent 前，都要以當次新原件重做或重新核對，不能沿用已失效 gate。

- `identity_match=MATCH`：三層 keys、viewer `n/N`、entry anchor 與 label 宣告的目標一致；才可保存成該 post／media 的候選證據。
- `identity_match=MISMATCH`：任一可核對欄位矛盾，或 label／目錄名宣稱另一個目標。保留已寫入原件的路徑、bytes 與 SHA-256，記 `accepted=false`、`quarantine_ref` 與差異；不得改名覆寫、重封裝成該 post／media，或傳給 event／attempt。舊 bytes 不改。
- `identity_match=UNKNOWN`：`n/N`、keys、entry anchor 或來源範圍任一不足；`artifact_label_target=NEUTRAL` 的中性唯一 label 不因未宣告 post／media 目標而單獨成為 `UNKNOWN`，若有宣告目標但不足則記 `UNKNOWN`。以中性 observation 保存，不歸屬、不建立 intent；補足新證據後另立 gate。

label 只作唯一標示，即使 `MATCH` 也不能代替 keys。已存在的錯名只需在私有 correction note 追加原路徑、原 hash 與「不作該目標證據」的說明；不得以批次改名器改寫舊 bytes、舊 bundle 或既有正確的 ledger completion。若原件尚可證明屬於另一目標，先保持未採信，待統籌判斷，不由 Agent 自行改掛。

## CUA 觀察原件落地

CUA 的觀察結果不會自動成為專案檔案。使用同一次 `getAXStateAndScreenshot` 取得完整 AX 與截圖，再從 CUA 的 Node runtime 直接寫入已存在的專案私有 task directory；不要從聊天摘要重建原件，也不要把 CUA 回傳貼進手寫 JSON。

先在終端機確認 `TASK_PRIVATE_DIR` 是本次任務在 `.local/line-backup/tasks/` 下的 canonical 私有目錄，建立尚不存在的 `OBSERVATION_DIR`，並產生只含英數、點、底線或連字號的唯一 `OBSERVATION_ID`。三個值都要代入絕對路徑；範例會再核對兩者是 canonical 路徑，且 observation directory 位於 task directory 下。檔名碰撞不是重試訊號；改用新的 observation ID。

實作試跑與歸因紀律：不得僅因對話介面已呈現截圖或 AX，就推斷 CUA 無法橋接至檔案系統。`evidenceTools` 並非 CUA runtime 預先注入的全域物件，而是由本節下方 `cua-evidence-tools` 定義區塊建立；首次使用前必須先於同一 CUA Node runtime（例如 `mcp__cua_repl.js`）按「先定義、後呼叫」順序執行該定義區塊，再執行 `evidenceTools.captureAndPersist`。`bind` 與 `reacquire` 的新觀察一律使用 `evidenceTools.captureAndPersist`，或使用具備同次實時 `hostCalls`、使 `stages.CAPTURE_BOUNDARY.status === 'RECORDED'` 的等價路徑；低階 `persistObservation` 僅用於同次 callback 內已有真實捕捉與 `hostCalls` 的保存（例如 `persistRevealWithDirectAfter`），嚴禁對舊 capture 變數呼叫 bare `persistObservation` 充當新觀察，也不得以手寫 curated diagnostic JSON 取代 helper 落地。僅檢查 `typeof evidenceTools === "undefined"` 只代表尚未載入定義區塊，屬 `NOT_RUN`，不得宣稱環境不支援落地或缺少 helper。Agent 必須先預建 canonical 的 `TASK_PRIVATE_DIR` 與 `OBSERVATION_DIR`，並在同一個 CUA Node runtime 實際執行 `evidenceTools.captureAndPersist`；未實際執行屬 `NOT_RUN`，不得列為環境或工具不支援。只有載入後實跑拋出真實 `error`（例如 `import('node:fs/promises')` 被拒）或回傳 `ready_for_bind=false`（附 `stages`／`blockers`）時，才屬實證保存阻塞，可保留 `error` 的 `name`／`code`／`message` 或 `OBSERVATION.stages`／`blockers`。若 CUA 工具 namespace 於任務中途被撤除，只記錄工具可用性變動並停止，不可用對話摘要重建 AX 或截圖原件。

下列第一段只在 CUA Node runtime 定義工具，第二段才實際取得並保存同一次回傳。`util.types.isUint8Array` 可接受真正的 Buffer／Uint8Array，包括 CUA 跨 realm 回傳值；`instanceof`、constructor 名稱或任意 array-like 都不是型別證明。副本只取 view 的 `byteLength`，不會把整個 backing buffer 當成影像。兩段之間不要另做 capture，也不要用 statement 或聊天摘要重建原件。

同一次 API 呼叫不證明 AX 與截圖是同一瞬間的原子快照。Agent 另記可取得的最早 call 前時間、call 回傳時間，以及 AX／截圖各自可證明的觀察時間與來源；任一時間沒有可信來源就記 `UNKNOWN`，不得用檔案 mtime 或 helper 寫 diagnostic 的 `created_at` 冒充 capture 時間。兩來源狀態不同時分開記錄，不互相補值，也不為把兩者湊成一致而重做 capture。

<!-- cua-evidence-tools:start -->
```js
const evidenceTools = await (async () => {
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const { Buffer } = await import('node:buffer');
  const { createHash } = await import('node:crypto');
  const { types: utilTypes } = await import('node:util');

  function describeError(error) {
    return {
      name: error && typeof error.name === 'string' ? error.name : 'UNKNOWN',
      code: error && typeof error.code === 'string' ? error.code : 'UNKNOWN',
      message: String(error && error.message ? error.message : error).slice(0, 500),
    };
  }

  function sha256(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
  }

  function copyExactUint8Array(value) {
    try {
      if (!utilTypes.isUint8Array(value)) {
        return { ok: false, reason: 'NOT_UINT8ARRAY' };
      }
      const bytes = Buffer.allocUnsafe(value.byteLength);
      bytes.set(new Uint8Array(value.buffer, value.byteOffset, value.byteLength));
      return { ok: true, bytes };
    } catch (error) {
      return { ok: false, reason: 'VIEW_COPY_FAILED', error: describeError(error) };
    }
  }

  function normalizeHostCalls(hostCalls, timeKeys) {
    const value = hostCalls !== null && typeof hostCalls === 'object' ? hostCalls : {};
    const normalized = {};
    for (const key of timeKeys) {
      normalized[key] = typeof value[key] === 'string' ? value[key] : 'NOT_RUN';
    }
    normalized.clock_source = 'HOST_JS_DATE';
    normalized.precision = 'CALL_BOUNDARY_ONLY';
    normalized.os_event_time = 'UNKNOWN';
    return normalized;
  }

  async function writeExclusive(filePath, bytes) {
    try {
      await fs.writeFile(filePath, bytes, { flag: 'wx', mode: 0o600 });
      return { status: 'WRITTEN' };
    } catch (error) {
      return { status: 'FAILED', error: describeError(error) };
    }
  }

  async function readbackExact(filePath, expectedBytes) {
    try {
      const saved = await fs.readFile(filePath);
      const expected_sha256 = sha256(expectedBytes);
      const saved_sha256 = sha256(saved);
      return {
        status: saved.length === expectedBytes.length &&
                saved_sha256 === expected_sha256 ? 'MATCH' : 'MISMATCH',
        expected_bytes: expectedBytes.length,
        saved_bytes: saved.length,
        expected_sha256,
        saved_sha256,
      };
    } catch (error) {
      return {
        status: 'FAILED',
        expected_bytes: expectedBytes.length,
        expected_sha256: sha256(expectedBytes),
        error: describeError(error),
      };
    }
  }

  async function persistAsset(metadata, role, filePath, bytes) {
    const asset = {
      path: filePath,
      bytes: bytes.length,
      sha256: sha256(bytes),
      write: 'NOT_RUN',
      readback: 'NOT_RUN',
    };
    metadata.assets[role] = asset;
    const write = await writeExclusive(filePath, bytes);
    asset.write = write.status;
    if (write.error) asset.write_error = write.error;
    if (write.status !== 'WRITTEN') return false;
    const readback = await readbackExact(filePath, bytes);
    asset.readback = readback.status;
    asset.saved_bytes = readback.saved_bytes;
    asset.saved_sha256 = readback.saved_sha256;
    if (readback.error) asset.readback_error = readback.error;
    return readback.status === 'MATCH';
  }

  async function validatePrivatePaths(taskDir, observationDir) {
    try {
      if (!path.isAbsolute(taskDir) || !path.isAbsolute(observationDir)) {
        return { ok: false, error: { code: 'ABSOLUTE_PATH_REQUIRED' } };
      }
      const taskReal = await fs.realpath(taskDir);
      const observationReal = await fs.realpath(observationDir);
      if (path.resolve(taskDir) !== taskReal ||
          path.resolve(observationDir) !== observationReal) {
        return { ok: false, error: { code: 'CANONICAL_PRIVATE_PATH_REQUIRED' } };
      }
      if (observationReal === taskReal ||
          !observationReal.startsWith(taskReal + path.sep)) {
        return { ok: false, error: { code: 'PRIVATE_TASK_SUBDIRECTORY_REQUIRED' } };
      }
      return { ok: true, task_dir: taskReal, observation_dir: observationReal };
    } catch (error) {
      return { ok: false, error: describeError(error) };
    }
  }

  function isAxNoChangeStub(stateText) {
    if (typeof stateText !== 'string') return false;
    const trimmed = stateText.trim();
    if (!trimmed || trimmed.length > 512) return false;
    const lines = trimmed.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (lines.length === 0 || lines.length > 3) return false;
    if (!/^There has been no change in the accessibility tree\b/i.test(lines[0])) {
      return false;
    }
    return lines.slice(1).every(line => !/^\d+\s+/.test(line));
  }

  async function persistObservation(options) {
    const metadata = {
      schema_version: 1,
      observation_id: options.observationId,
      created_at: {
        value: new Date().toISOString(),
        source: 'CUA Node runtime Date',
      },
      task_dir: options.taskDir,
      observation_dir: options.observationDir,
      files: {
        ax: path.join(options.observationDir, options.observationId + '.ax.txt'),
        screenshot: path.join(options.observationDir,
                              options.observationId + '.screenshot.bin'),
        diagnostic: path.join(options.observationDir,
                              options.observationId + '.diagnostic.json'),
      },
      stages: {},
      assets: {},
      hostCalls: normalizeHostCalls(options.hostCalls, [
        'capture_call_started_at', 'capture_call_returned_at',
      ]),
      ready_for_bind: false,
      blockers: [],
    };
    const setStage = (name, status, detail) => {
      metadata.stages[name] = Object.assign({ status }, detail || {});
    };
    const result = (blockers, readyForBind = false) => Object.assign({
      ready_for_bind: false,
      blockers,
      observation_id: options.observationId,
      files: metadata.files,
    }, metadata, {
      ready_for_bind: readyForBind,
      blockers: [...blockers],
    });

    if (typeof options.observationId !== 'string' ||
        !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(options.observationId)) {
      setStage('OBSERVATION_ID', 'INVALID');
      return result(['OBSERVATION_ID:INVALID']);
    }
    setStage('OBSERVATION_ID', 'OK');

    const paths = await validatePrivatePaths(options.taskDir, options.observationDir);
    if (!paths.ok) {
      setStage('PRIVATE_PATHS', 'FAILED', { error: paths.error });
      return result(['PRIVATE_PATHS:FAILED']);
    }
    setStage('PRIVATE_PATHS', 'OK');

    const hasCaptureBoundary = key => {
      const value = metadata.hostCalls[key];
      return typeof value === 'string' && value.trim().length > 0 &&
        value !== 'NOT_RUN' && value !== 'UNKNOWN';
    };
    setStage(
      'CAPTURE_BOUNDARY',
      hasCaptureBoundary('capture_call_started_at') &&
        hasCaptureBoundary('capture_call_returned_at')
        ? 'RECORDED' : 'MISSING',
    );

    const capture = options.capture;
    const blockers = [];
    if (options.captureError) {
      setStage('CAPTURE', 'FAILED', { error: options.captureError });
      blockers.push('CAPTURE:FAILED');
    } else if (!capture || typeof capture !== 'object' || Array.isArray(capture)) {
      setStage('CAPTURE', 'FAILED', { error: { code: 'CAPTURE_SHAPE_INVALID' } });
      blockers.push('CAPTURE:FAILED');
    } else {
      setStage('CAPTURE', 'OK');
      if (capture.regions !== undefined && capture.regions !== null) {
        setStage('CAPTURE_SHAPE', 'UNSUPPORTED_REGIONS');
        blockers.push('CAPTURE_SHAPE:UNSUPPORTED_REGIONS');
      } else {
        setStage('CAPTURE_SHAPE', 'SUPPORTED_SINGLE_SCREENSHOT');
      }
    }

    let axBytes = null;
    if (capture && typeof capture.state === 'string') {
      if (capture.state.trim().length === 0) {
        setStage('AX', 'EMPTY');
        blockers.push('AX:EMPTY');
      } else if (isAxNoChangeStub(capture.state)) {
        // A no-change line is a diff notification, not a usable tree. Keep the
        // raw bytes for read-only diagnosis but fail closed for bind/download.
        axBytes = Buffer.from(capture.state, 'utf8');
        setStage('AX', 'DIFF_NO_CHANGE', {
          utf8_bytes: axBytes.length,
          full_tree: false,
          diff_only: true,
          stale_index_warning: true,
        });
        blockers.push('AX:DIFF_NO_CHANGE');
      } else {
        axBytes = Buffer.from(capture.state, 'utf8');
        setStage('AX', 'OK', {
          utf8_bytes: axBytes.length,
          full_tree: true,
          diff_only: false,
        });
      }
    } else if (capture) {
      setStage('AX', 'INVALID_TYPE',
               { observed_type: capture.state === null ? 'null' : typeof capture.state });
      blockers.push('AX:INVALID_TYPE');
    } else {
      setStage('AX', 'NOT_AVAILABLE');
    }

    let screenshotBytes = null;
    if (capture) {
      const copied = copyExactUint8Array(capture.screenshot);
      if (!copied.ok && copied.reason === 'NOT_UINT8ARRAY') {
        setStage('SCREENSHOT_TYPE', 'INVALID_TYPE');
        blockers.push('SCREENSHOT_TYPE:INVALID_TYPE');
      } else if (!copied.ok) {
        setStage('SCREENSHOT_TYPE', 'COPY_FAILED', { error: copied.error });
        blockers.push('SCREENSHOT_TYPE:COPY_FAILED');
      } else {
        setStage('SCREENSHOT_TYPE', 'OK');
        if (copied.bytes.length === 0) {
          setStage('SCREENSHOT_LENGTH', 'EMPTY');
          blockers.push('SCREENSHOT_LENGTH:EMPTY');
        } else {
          screenshotBytes = copied.bytes;
          setStage('SCREENSHOT_LENGTH', 'OK',
                   { bytes: screenshotBytes.length });
        }
      }
    } else {
      setStage('SCREENSHOT_TYPE', 'NOT_AVAILABLE');
      setStage('SCREENSHOT_LENGTH', 'NOT_AVAILABLE');
    }

    if (axBytes !== null) {
      if (await persistAsset(metadata, 'ax', metadata.files.ax, axBytes)) {
        setStage('AX_PERSISTENCE', 'MATCH');
      } else {
        setStage('AX_PERSISTENCE', 'FAILED');
        blockers.push('AX_PERSISTENCE:FAILED');
      }
    } else {
      setStage('AX_PERSISTENCE', 'SKIPPED');
    }

    if (screenshotBytes !== null) {
      if (await persistAsset(metadata, 'screenshot', metadata.files.screenshot,
                             screenshotBytes)) {
        setStage('SCREENSHOT_PERSISTENCE', 'MATCH');
      } else {
        setStage('SCREENSHOT_PERSISTENCE', 'FAILED');
        blockers.push('SCREENSHOT_PERSISTENCE:FAILED');
      }
    } else {
      setStage('SCREENSHOT_PERSISTENCE', 'SKIPPED');
    }

    metadata.ready_for_bind = blockers.length === 0;
    metadata.blockers = [...blockers];
    const diagnosticBytes = Buffer.from(JSON.stringify(metadata, null, 2) + '\n', 'utf8');
    const diagnosticWrite = await writeExclusive(metadata.files.diagnostic,
                                                  diagnosticBytes);
    const diagnostic = {
      path: metadata.files.diagnostic,
      bytes: diagnosticBytes.length,
      sha256: sha256(diagnosticBytes),
      write: diagnosticWrite.status,
      readback: 'NOT_RUN',
    };
    if (diagnosticWrite.error) diagnostic.write_error = diagnosticWrite.error;
    if (diagnosticWrite.status === 'WRITTEN') {
      const readback = await readbackExact(metadata.files.diagnostic, diagnosticBytes);
      diagnostic.readback = readback.status;
      diagnostic.saved_bytes = readback.saved_bytes;
      diagnostic.saved_sha256 = readback.saved_sha256;
      if (readback.error) diagnostic.readback_error = readback.error;
    }
    if (diagnostic.write !== 'WRITTEN' || diagnostic.readback !== 'MATCH') {
      blockers.push('DIAGNOSTIC_PERSISTENCE:FAILED');
    }

    const output = result(blockers, blockers.length === 0);
    output.metadata_persistence = diagnostic;
    output.ready_for_bind = blockers.length === 0;
    return output;
  }

  function inputErrorSnapshot(error) {
    const objectLike = error !== null &&
      (typeof error === 'object' || typeof error === 'function');
    const value = objectLike ? error : { value: error };
    const ownFields = Object.create(null);
    let fieldsComplete = true;
    let ownNames = [];
    const fieldGaps = [];
    try {
      ownNames = Object.getOwnPropertyNames(value);
    } catch (captureError) {
      fieldsComplete = false;
      fieldGaps.push('STRING_OWN_KEYS_CAPTURE_FAILED');
    }
    try {
      const ownSymbols = Object.getOwnPropertySymbols(value);
      if (ownSymbols.length > 0) {
        fieldsComplete = false;
        fieldGaps.push('SYMBOL_KEYED_OWN_FIELDS_UNCAPTURED:' + ownSymbols.length);
      }
    } catch (captureError) {
      fieldsComplete = false;
      fieldGaps.push('SYMBOL_OWN_KEYS_CAPTURE_FAILED');
    }
    for (const key of ownNames) {
      try {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (descriptor && Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
          ownFields[key] = descriptor.value;
        } else {
          fieldsComplete = false;
          ownFields[key] = '[ACCESSOR_NOT_CAPTURED]';
        }
      } catch (captureError) {
        fieldsComplete = false;
        ownFields[key] = '[FIELD_CAPTURE_FAILED]';
      }
    }
    let name = 'UNKNOWN';
    let message;
    let code = null;
    try {
      if (typeof value.name === 'string') name = value.name;
      if (typeof value.message === 'string') message = value.message;
      else message = String(error);
      if (value.code !== undefined) code = value.code;
    } catch (captureError) {
      fieldsComplete = false;
      message = '[ERROR_MESSAGE_READ_FAILED]';
    }
    return { name, message, code, own_fields: ownFields,
             fields_complete: fieldsComplete, field_gaps: fieldGaps };
  }

  function inputErrorSummary(snapshot) {
    const code = snapshot.code;
    return {
      name: snapshot.name,
      message: snapshot.message,
      code: code === null || ['string', 'number', 'boolean'].includes(typeof code)
        ? code : '[NON_SCALAR_CODE]',
      own_field_names: Object.keys(snapshot.own_fields || {}),
      fields_complete: snapshot.fields_complete,
      field_gaps: snapshot.field_gaps || [],
    };
  }

  function jsonSerializationGap(value, ancestors = new Set(), location = '$') {
    const kind = typeof value;
    if (value === null || kind === 'string' || kind === 'boolean') return null;
    if (kind === 'number') return Number.isFinite(value) ? null : location + ':NON_FINITE_NUMBER';
    if (kind === 'undefined' || kind === 'function' || kind === 'symbol' || kind === 'bigint') {
      return location + ':UNSUPPORTED_' + kind.toUpperCase();
    }
    if (kind !== 'object') return location + ':UNSUPPORTED_VALUE';
    if (ancestors.has(value)) return location + ':CIRCULAR_REFERENCE';
    const array = Array.isArray(value);
    const prototype = Object.getPrototypeOf(value);
    if (!array && prototype !== Object.prototype && prototype !== null) {
      return location + ':NON_PLAIN_OBJECT';
    }
    ancestors.add(value);
    try {
      for (const key of Reflect.ownKeys(value)) {
        if (typeof key === 'symbol') return location + ':SYMBOL_KEY';
        if (array && key === 'length') continue;
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (!descriptor || !descriptor.enumerable) return location + '.' + key + ':NON_ENUMERABLE';
        if (!Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
          return location + '.' + key + ':ACCESSOR_PROPERTY';
        }
        const gap = jsonSerializationGap(descriptor.value, ancestors, location + '.' + key);
        if (gap) return gap;
      }
      if (array) {
        for (let index = 0; index < value.length; index += 1) {
          if (!Object.prototype.hasOwnProperty.call(value, index)) {
            return location + '[' + index + ']:SPARSE_ARRAY_SLOT';
          }
        }
      }
      return null;
    } finally {
      ancestors.delete(value);
    }
  }

  function snapshotJsonValue(value) {
    try {
      const gap = jsonSerializationGap(value);
      if (gap) {
        return { ok: false, code: 'JSON_COMPLETENESS_REQUIRED', detail: gap };
      }
      const text = JSON.stringify(value);
      if (typeof text !== 'string') {
        return { ok: false, code: 'JSON_SERIALIZATION_FAILED' };
      }
      return { ok: true, value: JSON.parse(text) };
    } catch (error) {
      return {
        ok: false,
        code: 'JSON_SERIALIZATION_FAILED',
        error: inputErrorSnapshot(error),
      };
    }
  }

  const groundedDispatchToken = Object.freeze({});

  function syncGroundedDispatch(output, dispatchContext) {
    if (!dispatchContext || dispatchContext.token !== groundedDispatchToken) {
      return;
    }
    if (dispatchContext.dispatch) {
      output.dispatch_call_target = dispatchContext.dispatch.call_target;
      output.native_return_type = dispatchContext.dispatch.return_type;
    }
    output.native_dispatched_target = 'UNKNOWN';
    output.receipt_target_match = 'UNKNOWN';
    output.receipt_is_os_event_trace = false;
    if (dispatchContext.sourceObservationReadback) {
      output.source_observation_readback =
        dispatchContext.sourceObservationReadback;
    }
    if (dispatchContext.mappingEvidenceReadback) {
      output.mapping_evidence_readback =
        dispatchContext.mappingEvidenceReadback;
    }
    if (dispatchContext.hostCalls) {
      output.hostCalls = normalizeHostCalls(dispatchContext.hostCalls, [
        'dispatch_call_started_at', 'dispatch_call_returned_at',
      ]);
    }
  }

  async function persistSingleInput(options) {
    if (!options || typeof options !== 'object') {
      return {
        schema: 'line-notes-single-input/v1',
        operation_id: 'UNKNOWN',
        status: 'INVALID_HELPER_ARGUMENTS',
        blockers: ['OPTIONS_REQUIRED'],
        request: { status: 'NOT_RUN' },
        raw_return: { status: 'NOT_RUN', complete: false },
        diagnostic: { status: 'NOT_RUN', complete: false },
        files: {},
        receipt_is_os_event_trace: false,
      };
    }
    if (options.request &&
        (options.request.input_phase === 'DOWNLOAD_CONTROL' ||
         options.request.phase === 'DOWNLOAD_CONTROL')) {
      return {
        schema: 'line-notes-single-input/v1',
        operation_id: options.operationId || 'UNKNOWN',
        status: 'DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER',
        blockers: ['DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER'],
        request: { status: 'NOT_RUN' },
        raw_return: { status: 'NOT_RUN', complete: false },
        diagnostic: { status: 'NOT_RUN', complete: false },
        files: {},
        receipt_is_os_event_trace: false,
      };
    }
    return persistSingleInputInternal(options);
  }

  async function persistSingleInputInternal(options, dispatchContext = null) {
    const grounded = Boolean(dispatchContext &&
      dispatchContext.token === groundedDispatchToken);
    const validId = typeof options.operationId === 'string' &&
      /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(options.operationId);
    const output = {
      schema: grounded
        ? 'line-notes-grounded-download-click/v1'
        : 'line-notes-single-input/v1',
      operation_id: options.operationId || 'UNKNOWN',
      status: 'NOT_INVOKED',
      request: { status: 'NOT_RUN' },
      raw_return: { status: 'NOT_RUN', complete: false },
      diagnostic: { status: 'NOT_RUN', complete: false },
      files: {},
      receipt_is_os_event_trace: false,
    };
    if (grounded) {
      output.source_observation_readback = { status: 'NOT_RUN' };
      output.dispatch_call_target = 'NOT_SENT';
      output.native_dispatched_target = 'UNKNOWN';
      output.receipt_target_match = 'UNKNOWN';
      output.native_return_type = 'NOT_APPLICABLE';
    }
    syncGroundedDispatch(output, dispatchContext);
    if (!validId || typeof options.invoke !== 'function') {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = [!validId ? 'INVALID_OPERATION_ID' : 'INVOKE_FUNCTION_REQUIRED'];
      return output;
    }

    const paths = await validatePrivatePaths(options.taskDir, options.inputDir);
    if (!paths.ok) {
      output.status = 'PRIVATE_PATHS_INVALID';
      output.blockers = [paths.error && paths.error.code || 'PRIVATE_PATHS_INVALID'];
      return output;
    }
    const base = path.join(paths.observation_dir, options.operationId + '.input');
    output.files = {
      request: base + '.request.json',
      raw_return: base + '.raw.json',
      diagnostic: base + '.diagnostic.json',
    };

    let requestBytes;
    try {
      const requestEnvelope = {
        schema: output.schema,
        operation_id: options.operationId,
        request: options.request,
      };
      const requestGap = jsonSerializationGap(requestEnvelope);
      if (requestGap) throw new TypeError('REQUEST_NOT_JSON_COMPLETE:' + requestGap);
      const requestText = JSON.stringify(requestEnvelope);
      if (typeof requestText !== 'string') throw new TypeError('REQUEST_NOT_JSON_SERIALIZABLE');
      requestBytes = Buffer.from(requestText + '\n', 'utf8');
    } catch (error) {
      output.status = 'REQUEST_SERIALIZATION_FAILED';
      output.request = { status: 'SERIALIZATION_FAILED', error: inputErrorSnapshot(error) };
      output.blockers = ['REQUEST_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    output.request = {
      status: 'PREPARED',
      bytes: requestBytes.length,
      sha256: sha256(requestBytes),
      write: 'NOT_RUN',
      readback: 'NOT_RUN',
    };
    const requestWrite = await writeExclusive(output.files.request, requestBytes);
    output.request.write = requestWrite.status;
    if (requestWrite.error) output.request.write_error = inputErrorSnapshot(requestWrite.error);
    if (requestWrite.status !== 'WRITTEN') {
      output.status = 'REQUEST_PERSIST_FAILED';
      output.blockers = ['REQUEST_PERSIST_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    const requestReadback = await (options.readbackExact || readbackExact)(
      output.files.request, requestBytes);
    output.request.readback = requestReadback.status;
    output.request.saved_bytes = requestReadback.saved_bytes;
    output.request.saved_sha256 = requestReadback.saved_sha256;
    if (requestReadback.error) output.request.readback_error = inputErrorSnapshot(requestReadback.error);
    if (requestReadback.status !== 'MATCH') {
      output.status = 'REQUEST_READBACK_FAILED';
      output.blockers = ['REQUEST_READBACK_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    let returned;
    let rawEnvelope;
    output.status = 'INVOKED';
    try {
      // Invoke from the bytes that were written and read back. Never pass the
      // caller's mutable object across the persistence boundary.
      const savedEnvelope = JSON.parse(requestBytes.toString('utf8'));
      returned = await options.invoke(savedEnvelope.request);
      output.raw_return.kind = 'RETURN';
      if (returned === undefined) {
        output.raw_return.kind = 'NATIVE_RETURN_UNDEFINED';
        output.raw_return.value_type = 'undefined';
        rawEnvelope = { kind: 'NATIVE_RETURN_UNDEFINED', value_type: 'undefined' };
      } else {
        output.raw_return.value_type = 'VALUE';
        rawEnvelope = { kind: 'RETURN', value: returned };
      }
    } catch (error) {
      const snapshot = inputErrorSnapshot(error);
      output.raw_return.kind = 'ERROR';
      output.raw_return.error_summary = inputErrorSummary(snapshot);
      rawEnvelope = { kind: 'ERROR', error: snapshot };
    }

    let rawBytes;
    try {
      const rawGap = jsonSerializationGap(rawEnvelope);
      if (rawGap) throw new TypeError('RAW_NOT_JSON_COMPLETE:' + rawGap);
      const rawText = JSON.stringify(rawEnvelope);
      if (typeof rawText !== 'string') throw new TypeError('RETURN_NOT_JSON_SERIALIZABLE');
      rawBytes = Buffer.from(rawText + '\n', 'utf8');
    } catch (error) {
      output.status = 'RAW_SERIALIZATION_FAILED';
      output.raw_return.status = 'SERIALIZATION_FAILED';
      output.raw_return.complete = false;
      output.raw_return.gap = '原始回傳含循環或不可 JSON 序列化欄位；未保存為完整 raw。';
      output.raw_return.serialization_error = inputErrorSummary(inputErrorSnapshot(error));
      output.blockers = ['RAW_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    output.raw_return.bytes = rawBytes.length;
    output.raw_return.sha256 = sha256(rawBytes);
    output.raw_return.write = 'NOT_RUN';
    output.raw_return.readback = 'NOT_RUN';
    const rawWrite = await writeExclusive(output.files.raw_return, rawBytes);
    output.raw_return.write = rawWrite.status;
    if (rawWrite.error) output.raw_return.write_error = inputErrorSnapshot(rawWrite.error);
    if (rawWrite.status === 'WRITTEN') {
      const rawReadback = await (options.readbackExact || readbackExact)(
        output.files.raw_return, rawBytes);
      output.raw_return.readback = rawReadback.status;
      output.raw_return.saved_bytes = rawReadback.saved_bytes;
      output.raw_return.saved_sha256 = rawReadback.saved_sha256;
      if (rawReadback.error) output.raw_return.readback_error = inputErrorSnapshot(rawReadback.error);
      output.raw_return.status = rawReadback.status;
      output.raw_return.complete = rawReadback.status === 'MATCH' &&
        (output.raw_return.kind !== 'ERROR' ||
         output.raw_return.error_summary.fields_complete);
      if (!output.raw_return.complete) {
        output.raw_return.gap = '原始回傳寫入／讀回不完整；不得視為完整 raw。';
      }
    } else {
      output.raw_return.status = 'WRITE_FAILED';
      output.raw_return.complete = false;
    }
    if (!output.raw_return.complete) output.blockers = ['RAW_RETURN_INCOMPLETE'];
    await persistInputDiagnostic(output, options, dispatchContext);
    return output;
  }

  function groundedDownloadOutput(operationId) {
    return {
      schema: 'line-notes-grounded-download-click/v1',
      operation_id: typeof operationId === 'string' && operationId
        ? operationId : 'UNKNOWN',
      status: 'NOT_INVOKED',
      blockers: [],
      request: { status: 'NOT_RUN' },
      raw_return: { status: 'NOT_RUN', complete: false },
      diagnostic: { status: 'NOT_RUN', complete: false },
      files: {},
      source_observation_readback: { status: 'NOT_RUN' },
      mapping_evidence_readback: { status: 'NOT_RUN' },
      dispatch_call_target: 'NOT_SENT',
      native_dispatched_target: 'UNKNOWN',
      receipt_target_match: 'UNKNOWN',
      receipt_is_os_event_trace: false,
      native_return_type: 'NOT_APPLICABLE',
      hostCalls: normalizeHostCalls(null, [
        'dispatch_call_started_at', 'dispatch_call_returned_at',
      ]),
    };
  }

  function isPlainObject(value) {
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
      return false;
    }
    try {
      const prototype = Object.getPrototypeOf(value);
      return prototype === Object.prototype || prototype === null;
    } catch (error) {
      return false;
    }
  }

  function isKnownString(value) {
    return typeof value === 'string' && value.length > 0 && value !== 'UNKNOWN';
  }

  function isKnownIdentifier(value) {
    return isKnownString(value) ||
      (Number.isSafeInteger(value) && value >= 0);
  }

  function isFileRef(value) {
    return isPlainObject(value) && isKnownString(value.path) &&
      Number.isSafeInteger(value.bytes) && value.bytes > 0 &&
      typeof value.sha256 === 'string' && /^[0-9a-f]{64}$/.test(value.sha256);
  }

  function sameFileRef(left, right) {
    return isFileRef(left) && isFileRef(right) &&
      left.path === right.path && left.bytes === right.bytes &&
      left.sha256 === right.sha256;
  }

  function groundedWindowBlockers(window) {
    return isPlainObject(window) &&
      window.app_bundle_id === 'jp.naver.line.mac' &&
      isKnownIdentifier(window.window_id)
      ? [] : ['APP_WINDOW_CONTEXT_REQUIRED'];
  }

  function groundedCoordinateBlockers(request, prefix = 'DOWNLOAD_CONTROL',
                                       options = {}) {
    const blockers = [];
    const add = (name, invalid) => {
      if (invalid) blockers.push(prefix + '_' + name);
    };
    add('MAPPING_UNKNOWN', request.mapping_status !== 'MATCH');
    add('OBSERVATION_ORDER_UNKNOWN', request.observation_order !== 'PRE_INPUT');
    add('GROUNDING_NOT_PASS', options.requireGrounding !== false &&
        request.grounding_conclusion !== 'PASS_TO_INPUT');
    add('POINT_RELATION_INVALID', options.requirePointRelation !== false &&
        request.candidate_point_relation !== 'INSIDE');
    add('COORDINATE_SPACE_UNKNOWN', request.coordinate_space_match !== 'MATCH');
    add('TARGET_COORD_SPACE_INVALID',
      !isKnownString(request.control_region_coord_space) ||
      !isKnownString(request.target_coord_space) ||
      request.control_region_coord_space !== request.target_coord_space);
    return blockers;
  }

  function groundedGeometryBlockers(region, point, target, labels = {}) {
    const finitePoint = value => Array.isArray(value) && value.length === 2 &&
      value.every(Number.isFinite);
    const validRegion = Array.isArray(region) && region.length === 4 &&
      region.every(Number.isFinite) && region[2] > region[0] &&
      region[3] > region[1];
    if (!validRegion || !finitePoint(point) || !finitePoint(target)) {
      return [labels.missing || 'DOWNLOAD_CONTROL_GEOMETRY_MISSING_OR_NONFINITE'];
    }
    const blockers = [];
    const strictInterior = point[0] > region[0] && point[0] < region[2] &&
      point[1] > region[1] && point[1] < region[3];
    if (!strictInterior) blockers.push(labels.interior ||
      'DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR');
    if (labels.targetMismatch !== null &&
        (point[0] !== target[0] || point[1] !== target[1])) {
      blockers.push(labels.targetMismatch ||
        'DOWNLOAD_CONTROL_PREPARED_TARGET_MISMATCH');
    }
    return blockers;
  }

  function groundedRequestBlockers(request) {
    const blockers = [];
    const add = code => { if (!blockers.includes(code)) blockers.push(code); };
    if (!isPlainObject(request)) return ['DOWNLOAD_CONTROL_REQUEST_INVALID'];
    const source = request.source_observation;
    if (request.input_phase !== 'DOWNLOAD_CONTROL') {
      add('DOWNLOAD_CONTROL_PHASE_REQUIRED');
    }
    if (!isKnownString(request.attempt_id)) add('ATTEMPT_ID_REQUIRED');
    blockers.push(...groundedWindowBlockers(request.app_window_binding));
    blockers.push(...groundedCoordinateBlockers(request));
    if (!isFileRef(source) ||
        !sameFileRef(source, request.source_observation_ref)) {
      add('DOWNLOAD_CONTROL_SOURCE_REF_MISMATCH');
    }
    if (!isFileRef(request.mapping_evidence_ref)) {
      add('DOWNLOAD_CONTROL_MAPPING_REF_INVALID');
    }
    blockers.push(...groundedGeometryBlockers(
      request.control_region, request.candidate_point, request.prepared_target));
    return blockers;
  }

  async function privateFileReadback(fileRef, taskDir, copied, role) {
    const result = { status: 'NOT_RUN', role };
    const prefix = role === 'MAPPING_EVIDENCE'
      ? 'MAPPING_EVIDENCE' : 'SOURCE_OBSERVATION';
    if (!isFileRef(fileRef)) {
      result.status = 'FAILED';
      result.blocker = prefix + '_REF_REQUIRED';
      return result;
    }
    if (copied) {
      if (!copied.ok) {
        result.status = 'FAILED';
        result.blocker = 'SOURCE_OBSERVATION_BYTES_REQUIRED';
        return result;
      }
      result.expected_bytes = copied.bytes.length;
      result.expected_sha256 = sha256(copied.bytes);
      if (fileRef.bytes !== result.expected_bytes ||
          fileRef.sha256 !== result.expected_sha256) {
        result.status = 'MISMATCH';
        result.blocker = prefix + '_REF_BYTES_MISMATCH';
        return result;
      }
    } else {
      result.expected_bytes = fileRef.bytes;
      result.expected_sha256 = fileRef.sha256;
    }
    result.path = fileRef.path;
    try {
      if (!path.isAbsolute(fileRef.path)) throw new Error('ABSOLUTE_PATH_REQUIRED');
      const taskReal = await fs.realpath(taskDir);
      const real = await fs.realpath(fileRef.path);
      if (path.resolve(fileRef.path) !== real) {
        throw new Error('CANONICAL_SOURCE_REQUIRED');
      }
      if (real !== taskReal && !real.startsWith(taskReal + path.sep)) {
        throw new Error('SOURCE_OUTSIDE_TASK');
      }
      const info = await fs.lstat(real);
      if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1) {
        throw new Error('REGULAR_SINGLE_LINK_SOURCE_REQUIRED');
      }
      const saved = await fs.readFile(real);
      result.saved_bytes = saved.length;
      result.saved_sha256 = sha256(saved);
      result.status = saved.length === result.expected_bytes &&
        result.saved_sha256 === result.expected_sha256 ? 'MATCH' : 'MISMATCH';
      if (result.status !== 'MATCH') {
        result.blocker = prefix + '_READBACK_MISMATCH';
      }
      return result;
    } catch (error) {
      result.status = 'FAILED';
      result.blocker = prefix + '_READBACK_FAILED';
      result.error = describeError(error);
      return result;
    }
  }

  async function persistGroundedDownloadClick(options) {
    const output = groundedDownloadOutput(options && options.operationId);
    const operationId = output.operation_id;
    if (!options || typeof options !== 'object') {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = ['OPTIONS_REQUIRED'];
      return output;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(operationId)) {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = ['INVALID_OPERATION_ID'];
      return output;
    }

    // Snapshot the caller's request and source bytes before the first await.
    // Later path and file reads must never observe mutations to these objects.
    const requestSnapshot = snapshotJsonValue(options.request);
    const sourceCopy = copyExactUint8Array(options.source_observation_bytes);
    const app = options.app;
    const click = app && typeof app.click === 'function'
      ? app.click.bind(app) : null;
    const requestBlockers = requestSnapshot.ok
      ? groundedRequestBlockers(requestSnapshot.value) : [];
    const paths = await validatePrivatePaths(options.taskDir, options.inputDir);
    if (!paths.ok) {
      output.status = 'PRIVATE_PATHS_INVALID';
      output.blockers = [paths.error && paths.error.code || 'PRIVATE_PATHS_INVALID'];
      return output;
    }
    output.files.diagnostic = path.join(
      paths.observation_dir, operationId + '.input.diagnostic.json');
    if (!requestSnapshot.ok) {
      output.status = 'REQUEST_SERIALIZATION_FAILED';
      output.request = {
        status: 'SERIALIZATION_FAILED',
        error: requestSnapshot.error || {
          name: 'TypeError',
          message: requestSnapshot.code + (requestSnapshot.detail
            ? ':' + requestSnapshot.detail : ''),
        },
      };
      output.blockers = ['REQUEST_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const request = requestSnapshot.value;
    if (requestBlockers.length > 0) {
      output.status = 'DOWNLOAD_CONTROL_GROUNDING_INVALID';
      output.blockers = requestBlockers;
      await persistInputDiagnostic(output, {});
      return output;
    }
    if (!sourceCopy.ok) {
      output.status = 'SOURCE_OBSERVATION_BYTES_REQUIRED';
      output.blockers = ['SOURCE_OBSERVATION_BYTES_REQUIRED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const sourceReadback = await privateFileReadback(
      request.source_observation, paths.task_dir, sourceCopy,
      'SOURCE_OBSERVATION');
    output.source_observation_readback = sourceReadback;
    if (sourceReadback.status !== 'MATCH') {
      output.status = 'SOURCE_OBSERVATION_READBACK_FAILED';
      output.blockers = [sourceReadback.blocker || 'SOURCE_OBSERVATION_READBACK_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const mappingReadback = await privateFileReadback(
      request.mapping_evidence_ref, paths.task_dir, null,
      'MAPPING_EVIDENCE');
    output.mapping_evidence_readback = mappingReadback;
    if (mappingReadback.status !== 'MATCH') {
      output.status = 'MAPPING_EVIDENCE_READBACK_FAILED';
      output.blockers = [mappingReadback.blocker || 'MAPPING_EVIDENCE_READBACK_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    if (click === null) {
      output.status = 'APP_CLICK_UNAVAILABLE';
      output.blockers = ['APP_CLICK_UNAVAILABLE'];
      await persistInputDiagnostic(output, {});
      return output;
    }

    const hostCalls = {
      dispatch_call_started_at: 'NOT_RUN',
      dispatch_call_returned_at: 'NOT_RUN',
    };
    const dispatch = {
      call_target: 'NOT_SENT',
      return_type: 'NOT_APPLICABLE',
    };
    const result = await persistSingleInputInternal({
      taskDir: paths.task_dir,
      inputDir: paths.observation_dir,
      operationId,
      request,
      invoke: async saved => {
        const savedPoint = saved.prepared_target;
        const target = [savedPoint[0], savedPoint[1]];
        dispatch.call_target = target;
        try {
          hostCalls.dispatch_call_started_at = new Date().toISOString();
          const returned = await click(target);
          dispatch.return_type = returned === undefined ? 'UNDEFINED' : 'VALUE';
          return returned;
        } catch (error) {
          dispatch.return_type = 'ERROR';
          throw error;
        } finally {
          hostCalls.dispatch_call_returned_at = new Date().toISOString();
        }
      },
    }, {
      token: groundedDispatchToken,
      dispatch,
      hostCalls,
      sourceObservationReadback: sourceReadback,
      mappingEvidenceReadback: mappingReadback,
    });
    return result;
  }

  async function persistInputDiagnostic(output, options, dispatchContext = null) {
    if (!output.files.diagnostic) return;
    if (dispatchContext) syncGroundedDispatch(output, dispatchContext);
    const diagnostic = {
      schema: 'line-notes-single-input-diagnostic/v1',
      operation_id: output.operation_id,
      request: output.request,
      raw_return: output.raw_return,
      status: output.status,
      blockers: output.blockers || [],
      receipt_is_os_event_trace: false,
    };
    for (const key of [
      'source_observation_readback',
      'mapping_evidence_readback',
      'dispatch_call_target',
      'native_dispatched_target',
      'receipt_target_match',
      'native_return_type',
      'hostCalls',
    ]) {
      if (Object.prototype.hasOwnProperty.call(output, key)) {
        diagnostic[key] = output[key];
      }
    }
    let bytes;
    try {
      bytes = Buffer.from(JSON.stringify(diagnostic, null, 2) + '\n', 'utf8');
    } catch (error) {
      output.diagnostic = { status: 'SERIALIZATION_FAILED', complete: false,
                            error: inputErrorSnapshot(error) };
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
      return;
    }
    const written = await writeExclusive(output.files.diagnostic, bytes);
    output.diagnostic = {
      status: written.status,
      complete: false,
      bytes: bytes.length,
      sha256: sha256(bytes),
      readback: 'NOT_RUN',
    };
    if (written.error) output.diagnostic.write_error = inputErrorSnapshot(written.error);
    if (written.status !== 'WRITTEN') {
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
      return;
    }
    const readback = await (options.readbackExact || readbackExact)(
      output.files.diagnostic, bytes);
    output.diagnostic.readback = readback.status;
    output.diagnostic.saved_bytes = readback.saved_bytes;
    output.diagnostic.saved_sha256 = readback.saved_sha256;
    output.diagnostic.complete = readback.status === 'MATCH';
    if (readback.error) output.diagnostic.readback_error = inputErrorSnapshot(readback.error);
    if (!output.diagnostic.complete) {
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
    }
  }

  async function captureAndPersist(options) {
    let capture = null;
    let captureError = null;
    const hostCalls = {
      capture_call_started_at: 'NOT_RUN',
      capture_call_returned_at: 'NOT_RUN',
    };
    try {
      const app = await cua.getApp('jp.naver.line.mac');
      hostCalls.capture_call_started_at = new Date().toISOString();
      try {
        capture = await app.getAXStateAndScreenshot({
          disableDiffing: true,
          emit: false,
        });
      } finally {
        hostCalls.capture_call_returned_at = new Date().toISOString();
      }
    } catch (error) {
      captureError = describeError(error);
    }
    return persistObservation(
      Object.assign({}, options, { capture, captureError, hostCalls }));
  }

  return {
    captureAndPersist,
    copyExactUint8Array,
    describeError,
    groundedCoordinateBlockers,
    groundedGeometryBlockers,
    groundedWindowBlockers,
    persistObservation,
    persistGroundedDownloadClick,
    persistSingleInput,
    readbackExact,
    sha256,
    snapshotJsonValue,
    writeExclusive,
  };
})();
```
<!-- cua-evidence-tools:end -->

<!-- cua-initial-observation:start -->
```js
if (typeof evidenceTools === 'undefined' || !evidenceTools ||
    typeof evidenceTools.captureAndPersist !== 'function') {
  throw new Error(
    'CUA_EVIDENCE_TOOLS_NOT_LOADED: evaluate the cua-evidence-tools ' +
    'block from evidence-template.md in this CUA Node runtime first; ' +
    'typeof evidenceTools === "undefined" is NOT_RUN, not an environment blocker'
  );
}
const OBSERVATION = await evidenceTools.captureAndPersist({
  taskDir: '/ABS/TASK_PRIVATE_DIR',
  observationDir: '/ABS/OBSERVATION_DIR',
  observationId: 'UNIQUE_OBSERVATION_ID',
});
nodeRepl.write(JSON.stringify(OBSERVATION, null, 2));
const captureBoundaryMissing =
  !OBSERVATION.stages ||
  !OBSERVATION.stages.CAPTURE_BOUNDARY ||
  OBSERVATION.stages.CAPTURE_BOUNDARY.status !== 'RECORDED';
if (!OBSERVATION.ready_for_bind || captureBoundaryMissing) {
  const reasons = [...(OBSERVATION.blockers || [])];
  if (captureBoundaryMissing) reasons.push('CAPTURE_BOUNDARY:MISSING');
  throw new Error('CUA_RAW_OBSERVATION_INCOMPLETE: ' + reasons.join(', '));
}
{
  const fs = await import('node:fs/promises');
  const screenshotAsset = OBSERVATION.assets.screenshot;
  const axAsset = OBSERVATION.assets.ax;
  const savedScreenshot = await fs.readFile(screenshotAsset.path);
  const savedAx = await fs.readFile(axAsset.path);
  const readbackMatches =
    savedScreenshot.length === screenshotAsset.bytes &&
    evidenceTools.sha256(savedScreenshot) === screenshotAsset.sha256 &&
    savedAx.length === axAsset.bytes &&
    evidenceTools.sha256(savedAx) === axAsset.sha256;
  if (!readbackMatches) {
    throw new Error('CUA_OBSERVATION_EMIT_READBACK_MISMATCH');
  }
  await nodeRepl.emitImage(new Uint8Array(savedScreenshot));
  nodeRepl.write(savedAx.toString('utf8'));
}
```
<!-- cua-initial-observation:end -->

成功落地後才顯示同一份原件：範例在 `ready_for_bind === true` 時，於獨立區塊作用域內重新讀回已落地的截圖與 AX，以既有 `evidenceTools.sha256` 與位元組長度核對一致，再以 `nodeRepl.emitImage` 與 `nodeRepl.write` 呈現供 Agent 判讀。這是零第二次 capture 的讀回顯示；區塊作用域宣告 `fs` 是為了不與後續 intent 讀回區塊的頂層 `const fs` 衝突。讀回內容與 `OBSERVATION.assets` 不符即拋 `CUA_OBSERVATION_EMIT_READBACK_MISMATCH`，不得改以原始 capture 變數直接顯示。本初始觀察範例要求先於同一 Node runtime 執行 `cua-evidence-tools` 定義區塊；若未先載入（或物件缺少 `captureAndPersist`）即直接執行此範例，會先拋出 `CUA_EVIDENCE_TOOLS_NOT_LOADED`（屬 `NOT_RUN`，非環境不支援），不觸發任何 capture 或 emit；若在同一個 module 內誤把 `const evidenceTools` 定義排於本段之後，則屬拼接順序錯誤。

`stages` 會分別留下 `CAPTURE`、`CAPTURE_SHAPE`、`CAPTURE_BOUNDARY`、`AX`、`SCREENSHOT_TYPE`、`SCREENSHOT_LENGTH` 與各 asset 的 `*_PERSISTENCE`；`assets` 另記實際路徑、長度、SHA-256、寫入與讀回，`metadata_persistence` 則記 diagnostic 的寫入與讀回。寫入 diagnostic 前，helper 先以當次 capture／asset 結果定稿 `metadata.ready_for_bind` 與 `metadata.blockers`；diagnostic 自身的寫入／讀回是外層結果，不要求它記錄自己尚未產生的最終 hash。只有 AX 與非空截圖都存在、兩者都以 `wx` 寫入並逐 bytes 讀回 MATCH，且 diagnostic 的寫入／讀回也 MATCH，runtime 輸出與落地 diagnostic 的 readiness／blockers 才可一致為 `true`／空陣列。若 diagnostic 寫入或讀回失敗，runtime 一律回 `ready_for_bind=false` 並保留 `DIAGNOSTIC_PERSISTENCE:FAILED`，不得消費未驗證的 diagnostic；原檔碰撞時也不覆寫。AX 合格但截圖型別錯、空值或寫入失敗時，合格 AX 仍會保存；反向情況亦同。這些部分原件可用於唯讀診斷，但 blocker 未消除前不得 bind。

`stages.CAPTURE_BOUNDARY` 記 `RECORDED`／`MISSING`：只有 `capture_call_started_at` 與 `capture_call_returned_at` 都是實時 `HOST_JS_DATE` 值才為 `RECORDED`；未傳 `hostCalls`、gate 在呼叫前拒絕或 `getApp` 失敗時為 `MISSING`。`MISSING` 不推入低階 `persistObservation` 的 `blockers`，以維持既有 bare 呼叫契約；但採信任何落地 observation 作為 `bind` 或 `reacquire` 前，必須同時核對 `ready_for_bind === true` 與 `stages.CAPTURE_BOUNDARY.status === 'RECORDED'`，`cua-initial-observation` 入口也對非 `RECORDED` fail-closed 並拋 `CUA_RAW_OBSERVATION_INCOMPLETE`。靜止畫面在 `CAPTURE_BOUNDARY=RECORDED` 下出現相同 bytes、不同 inode 時只記新鮮度註記，不自動阻擋；`CAPTURE_BOUNDARY=MISSING` 一律不得作為新鮮 `bind`／`reacquire` 證據，若同時出現相同 bytes 須標 `STALE_CAPTURE_SUSPECTED` 並停止消費。

`AX` 階段另有 `DIFF_NO_CHANGE`：`getAXState()` 的 no-change 一行輸出只是變更通知，不是可用樹。命中時仍以 `wx` 保存原始 `.ax.txt` 並讀回 `MATCH` 供唯讀診斷，但 `stages.AX` 記 `full_tree: false`、`diff_only: true`、`stale_index_warning: true`，推入 `AX:DIFF_NO_CHANGE` 使 `ready_for_bind=false`，同時阻擋 `cua-initial-observation` emit 與 `checkDownloadReadiness`；純空白 `state` 記 `AX:EMPTY`。判定只接受前綴錨定、長度不超過 512 字元、非空行不超過 3 行且後續行不是編號 AX 節點，避免把內文含該字串的完整樹誤判。`disableDiffing: true` 不是平台絕對保證：若 CUA 回傳「有變更之局部 diff」，helper 仍記 `AX:OK`，Agent 必須自行核對完整樹結構，不可把 `AX:OK`／`full_tree: true` 當成完整樹的絕對證明。

日後讀取落地 diagnostic 時仍要核對其 bytes／SHA-256／原 asset 讀回與適用的 helper `metadata_persistence`，不能只因檔案內寫 `ready_for_bind=true` 就宣稱 bind 成功。這個欄位只表示本地 observation 保存所需檔案完整，不是 GUI 權限、畫面真實、viewer 身分、control 命中或下載成功的證明。

`metadata`、runtime 輸出與落地 diagnostic 另含 `hostCalls`：intent 後唯一 capture 的 `capture_call_started_at`／`capture_call_returned_at`，固定 `clock_source=HOST_JS_DATE`、`precision=CALL_BOUNDARY_ONLY`、`os_event_time=UNKNOWN`。未執行、gate 在呼叫前拒絕或 `getApp` 失敗時，尚未發生的時間維持 `NOT_RUN`；capture 拋錯仍記結束時間。grounded download click 的 receipt／diagnostic 以同一形狀記 `dispatch_call_started_at`／`dispatch_call_returned_at`，只在實際呼叫 `click` 時填入。

### 單次 CUA 輸入保存 helper

只有輸入參數與目標已由當次觀察核對後，才呼叫此 helper。呼叫端提供精確 request 與一個已選定的單次呼叫函式；helper 不尋找控制、不選動作、不導覽、不重試，也不因錯誤再呼叫。

```js
const inputReceipt = await evidenceTools.persistSingleInput({
  taskDir: '/ABS/TASK_PRIVATE_DIR',
  inputDir: '/ABS/EXISTING_PRIVATE_INPUT_DIR',
  operationId: 'UNIQUE_OPERATION_ID',
  request: verifiedInputArguments,
  invoke: async (request) => alreadySelectedSingleCall(request),
});
nodeRepl.write(JSON.stringify(inputReceipt, null, 2));
```

helper 先把 request 以 `wx` 寫入私有目錄，再以既有 hash／readback helper 逐 bytes 核對。只有讀回 `MATCH` 才呼叫一次 `invoke`。結果或錯誤另存 raw 檔；diagnostic 摘要是另一檔。三者都不覆寫。request 寫入／讀回失敗時不呼叫。任何 `persistSingleInput` 的 `invoke` 若回傳頂層 `undefined`，raw 只保存 typed `NATIVE_RETURN_UNDEFINED`／`value_type=undefined`；這只表示回傳型別可無損序列化，不是成功、控制命中或 `NOT_SENT`。巢狀 `undefined`、函式、Symbol、循環或其他不可無損 JSON 保存的欄位仍使 raw 不完整並拒絕完整宣稱。

入口恢復紀律（A12）：所有 entry-recovery 的 CUA pointer／導覽點擊與所有 CUA handle reacquire 呼叫，一律經 `evidenceTools.persistSingleInput` 落地 `.input.request.json`、`.input.raw.json` 與 `.input.diagnostic.json`，不得以手寫 curated blocker JSON 取代原始 receipt。三個操作邊界：(1) 工具若以回傳值而非 throw 回報錯誤，raw 記為 `kind=RETURN`，Agent 仍須依實際內容歸類為錯誤，不得宣稱成功；(2) handle reacquire 若回傳不可序列化之 live handle，須在 `invoke` closure 內暫存該 handle 並回傳純 JSON 投影（例如 `{ ok, bundle_id, window_id, title }`），否則 raw 會因不可序列化欄位而不完整；(3) 入口恢復／reacquire 不得使用 `input_phase: 'DOWNLOAD_CONTROL'`（應標如 `ENTRY_RECOVERY`／`HANDLE_REACQUIRE`），每次重試須使用新的唯一 `operationId` 以遵守 `wx` 不覆寫；需要時間邊界時由 Agent 另以 `HOST_JS_DATE` 記錄並標 `os_event_time=UNKNOWN`。

`persistSingleInput` 是一般輸入 helper；若 request 的 `input_phase` 或 `phase` 是 `DOWNLOAD_CONTROL`，它會直接拒絕，要求改用下列下載控制 wrapper。wrapper 不尋找控制、不選 action、不導覽，也不接受外部 `invoke`／`readbackExact`；它只使用已保存 request 讀回後的 `prepared_target` 呼叫一次已傳入 app handle 的 `click`。

下載控制 request 的最小合法形狀如下。以下路徑、bytes、hash、座標與 ID **全部是合成示意值，不是真實證據，也不得照抄**；每個值都必須由當次畫面觀察、實際私有檔讀回與 attempt context 產生。`source_observation_bytes` 必須是當次剛保存下來的原始 bytes；`source_observation` 與 `source_observation_ref` 必須是同一個 canonical 私有檔案 ref。`mapping_evidence_ref` 可以指向另一個 canonical 私有檔（例如當次 geometry／AX／statement 證據），helper 會讀回它的 bytes／SHA-256，不要求它與 screenshot 同檔。`window_id` 可為已知非 `UNKNOWN` 字串或非負整數。

```js
const sourceObservation = {
  path: '/ABS/SYNTHETIC_TASK/source.bin',
  bytes: 100,
  sha256: '1111111111111111111111111111111111111111111111111111111111111111',
};
const mappingEvidence = {
  path: '/ABS/SYNTHETIC_TASK/mapping-evidence.txt',
  bytes: 50,
  sha256: '2222222222222222222222222222222222222222222222222222222222222222',
};
const request = {
  input_phase: 'DOWNLOAD_CONTROL',
  attempt_id: 'SYNTHETIC_ATTEMPT_ID',
  app_window_binding: {
    app_bundle_id: 'jp.naver.line.mac',
    window_id: 'SYNTHETIC_WINDOW_ID',
  },
  source_observation: sourceObservation,
  source_observation_ref: sourceObservation,
  mapping_evidence_ref: mappingEvidence,
  mapping_status: 'MATCH',
  observation_order: 'PRE_INPUT',
  grounding_conclusion: 'PASS_TO_INPUT',
  candidate_point_relation: 'INSIDE',
  control_region: [10, 20, 50, 60],
  control_region_coord_space: 'APP_BOUND_SCREENSHOT_POINTS',
  target_coord_space: 'APP_BOUND_SCREENSHOT_POINTS',
  coordinate_space_match: 'MATCH',
  candidate_point: [30, 40],
  prepared_target: [30, 40],
};
const receipt = await evidenceTools.persistGroundedDownloadClick({
  taskDir: '/ABS/SYNTHETIC_TASK',
  inputDir: '/ABS/SYNTHETIC_TASK/input',
  operationId: 'SYNTHETIC_DOWNLOAD_CONTROL_ID',
  request,
  source_observation_bytes: sourceBytes,
  app, // 真正 CUA app handle；不可傳 invoke 或 readbackExact。
});
nodeRepl.write(JSON.stringify(receipt, null, 2));
```

這個 wrapper 的 `dispatch_call_target` 是已保存 request 讀回後實際交給 `app.click` 的參數；`native_dispatched_target`、`receipt_target_match` 仍保持 `UNKNOWN`，且 `receipt_is_os_event_trace=false`。若 app 回傳原生 `undefined`，raw 沿用 typed `NATIVE_RETURN_UNDEFINED`，不是成功，也不是 `NOT_SENT`；普通 `persistSingleInput` 的頂層 `undefined` 使用相同 typed 表示，不改變 grounded wrapper 的既有輸出。若呼叫前 request／source／mapping 檢查失敗，則不得呼叫 click。

錯誤 raw 保存完整 `message`、原型可讀的 `name`、原型可讀的 `code` 原型別，以及可忠實序列化的字串自有欄位（含 non-enumerable 欄位）。不使用 `instanceof Error` 判斷跨 realm 錯誤。若偵測到 Symbol 自有欄位，不把 Symbol key 或值轉成替代字串；保留其他可讀欄位與數值 `code`，並以 `field_gaps` 明列未捕獲數及標示 fields/raw 不完整。循環值、accessor、`undefined`、函式、Symbol、BigInt、非有限數字或非純資料物件若無法無損 JSON 保存，raw 標為不完整；diagnostic 只存可序列化的錯誤摘要與缺口。若 diagnostic 自己也無法落地，回傳明確 `complete=false`，不宣稱 raw 完整。

把 raw 檔與 diagnostic 檔分別加入 evidence bundle 的 `input_receipt` 與適用的 `observation` asset，並記各自路徑、bytes、SHA-256、寫入及讀回狀態。input receipt 只記錄保存的呼叫參數與 CUA 回傳；它不是 OS event trace，也不證明事件命中或 App 接受。

`CUA_RAW_OBSERVATION_INCOMPLETE` 是本地保存 gate，不是 CUA 沒有回傳或不支援該 API；依 `blockers`、`stages` 與部分 asset 判斷是缺值、型別、權限、碰撞或讀回問題。沒有新 bytes 時不要重作 GUI 輸入或猜測補值；若回傳 `regions` 等未實測形狀，保留可保存的部分與 `UNSUPPORTED_REGIONS`，交回精確範圍決策。

這段只保存 CUA 回傳的 bytes，不代表畫面真實、列表身分已確認或 GUI 權限成立。statement 另記實際 app／window、API、範圍與時間來源；未知值照實填 `UNKNOWN`。以剛保存的路徑作 `--asset ax` 與 `--asset screenshot` 執行既有 `evidence-pack`，再把 CLI 回傳的 bundle path 傳給 `bind --observation`／`--handoff`。兩個命題只有在同一原件確實支持且 context 相同時才共用 bundle；否則各自封裝適用原件，不複製或擴張原件能證明的範圍。

## Reveal 導覽證據（沿用既有 v2 roles）

本節只定義人工 statement 的欄位與保存順序，不是新的 event、schema、CLI 或 GUI sensor。v2 role 已足夠；本方案無需新增 `navigation_receipt`。`NAVIGATION` 與 `selected-filmstrip-safe-edge` 是 statement 內的 phase／方法名稱，仍使用既有的 `screenshot`、`ax`、`input_receipt`、`observation` roles；同一 role 可重複。

### 本輪 intent 後的單一路徑

- intent 前只依 [GUI 導覽與盤點](gui-inventory.md) 的〈目標與下載控制就緒（B1）〉核對本輪前置：若控制正面可定位，保留直接下載的可能；若控制隱藏，另須有當次可歸屬的 `selected-filmstrip-safe-edge` 安全區、選取狀態、三層身分、映射與明確額度。方法、歸屬或額度任一不足就停在 intent 前，不先送 reveal。
- 每個 attempt 只執行一次既有 `intent` 並讀回 JSON。`attempt_id` 以讀回值為準；`intent_event_ref` 只由 Agent 以唯讀方式核對該 intent 事件檔後記成 `{sequence, event_sha256}`。這個範本不掃描帳本、不重算 event hash、不重驗 schema，也不建立新的持久狀態。
- intent 後只取得一次最新 observation（Block 9 的 `intentObservation`）。控制正面可見且歸屬、啟用、映射成立時走直接路徑，以這份 observation 的定位與截圖 bytes 準備下載；控制不可見時，REVEAL 直接以同一變數作 `beforeObservation`，才可使用一次固定 `notes-reveal-c2-<attempt_id>` 的本輪 reveal。不得再取第二份 intent 後 capture，after 失效也不得重拍。兩條路徑互斥，且共用唯一的 `notes-download-<attempt_id>` 下載 slot。
- 本範本的可執行 reveal 範例只用當次畫面可證的 `selected-filmstrip-safe-edge` click。若當次工具文件沒有明確支持無點擊 hover，不得以 click 冒充 hover，也不得猜測未提供的 API。候選 `candidate_ordinal=1` 對應額度 `0→1`，且 `prior_candidate_refs` 為 `NONE`；只有同一 scope 前一候選 request／raw／after 完整、連續性與相關新證據成立時，才可用 `candidate_ordinal=2` 與額度 `1→2`。已用滿、舊 UNKNOWN、缺 receipt 或額度不明時沒有 reveal 路徑。
- 保存 before 截圖與完整 AX、輸入 request／raw receipt、after 截圖與完整 AX；同一次 observation 的相同 AX bytes 可以被重複引用，但每個 `--asset` ref 與順序都要保留。相同 AX 不代表 toolbar 狀態相同；AX 缺失、未變或沒有該 node 都不是「控制不存在」或「toolbar 未顯示」的反向證明。截圖與 AX 必須分開記錄各自來源、範圍、時間與 hash。

### 單次輸入與直接 after 觀察

只有在 intent 已保存並讀回、B1 的隱藏分支前置成立、input／observation 目錄與唯一 ID 已備妥，且同一個 `app` handle 已取得後，才可經下方 wrapper 呼叫這個 composition。它不改 helper、不改帳本，也不自行授予 `TOOLBAR_VISIBLE`。click 與 capture 必須在同一次 CUA runtime invocation；兩者之間不得跨模型回合，亦不得寫檔、固定等待、重新取得 app 或插入其他輸入。

<!-- notes-reveal-capture:start -->
```js
async function persistRevealWithDirectAfter({
  taskDir, inputDir, observationDir, operationId, observationId, request, app,
}) {
  const hostCalls = {
    input_call_sequence: 1,
    capture_call_sequence: 'NOT_RUN',
    input_call_started_at: 'UNKNOWN',
    input_call_returned_at: 'UNKNOWN',
    capture_call_started_at: 'UNKNOWN',
    capture_call_returned_at: 'UNKNOWN',
    clock_source: 'HOST_JS_DATE',
    precision: 'CALL_BOUNDARY_ONLY',
    os_event_time: 'UNKNOWN',
    ax_observed_at: 'UNKNOWN',
    screenshot_observed_at: 'UNKNOWN',
  };
  let afterCapture = null;
  let afterCaptureError = null;
  const hostNow = () => new Date().toISOString();
  const inputReceipt = await evidenceTools.persistSingleInput({
    taskDir,
    inputDir,
    operationId,
    request,
    invoke: async savedRequest => {
      hostCalls.input_call_started_at = hostNow();
      let inputReturn;
      try {
        inputReturn = await app.click(savedRequest.prepared_target);
      } finally {
        hostCalls.input_call_returned_at = hostNow();
      }
      hostCalls.capture_call_sequence = 2;
      hostCalls.capture_call_started_at = hostNow();
      try {
        afterCapture = await app.getAXStateAndScreenshot({
          emit: false,
          disableDiffing: true,
        });
      } catch (error) {
        afterCaptureError = evidenceTools.describeError(error);
      } finally {
        hostCalls.capture_call_returned_at = hostNow();
      }
      return inputReturn;
    },
  });
  const inputPersisted = inputReceipt.status === 'INVOKED' &&
    inputReceipt.request.readback === 'MATCH' &&
    inputReceipt.raw_return.readback === 'MATCH' &&
    inputReceipt.raw_return.complete === true &&
    inputReceipt.diagnostic.complete === true &&
    !(inputReceipt.blockers || []).length;
  let afterObservation = null;
  if (hostCalls.capture_call_sequence === 2) {
    afterObservation = await evidenceTools.persistObservation({
      taskDir,
      observationDir,
      observationId,
      ...(afterCaptureError
        ? { captureError: afterCaptureError }
        : { capture: afterCapture }),
      hostCalls,
    });
  }
  const failClosed = !(inputPersisted &&
    inputReceipt.raw_return.kind !== 'ERROR' &&
    afterCaptureError === null &&
    afterObservation !== null &&
    afterObservation.ready_for_bind === true);
  return { inputReceipt, afterObservation, hostCalls, fail_closed: failClosed };
}
```
<!-- notes-reveal-capture:end -->

<!-- notes-intent-dispatch:start -->
```js
const notesIntentDispatch = await (async () => {
  const stop = (reason, detail = {}) => ({
    status: 'STOP', reason, blockers: detail.blockers || [reason], ...detail,
  });
  const ready = detail => ({
    status: 'READY', reason: null, blockers: [], ...detail,
  });
  const isObject = value => value !== null && typeof value === 'object' &&
    !Array.isArray(value);
  const isId = value => typeof value === 'string' &&
    /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(value);
  const isKnownString = value => typeof value === 'string' &&
    value.trim().length > 0 && !['UNKNOWN', 'NONE'].includes(value.trim());
  const isReferenceToken = value => isKnownString(value) ||
    (isFileRef(value) && isKnownString(value.path));
  const isEventRef = value => isObject(value) &&
    Object.keys(value).sort().join(',') === 'event_sha256,sequence' &&
    Number.isSafeInteger(value.sequence) && value.sequence >= 1 &&
    typeof value.event_sha256 === 'string' &&
    /^[0-9a-f]{64}$/.test(value.event_sha256);
  const sameEventRef = (left, right) => isEventRef(left) && isEventRef(right) &&
    left.sequence === right.sequence &&
    left.event_sha256 === right.event_sha256;
  const isFileRef = value => isObject(value) &&
    typeof value.path === 'string' && value.path.length > 0 &&
    value.path !== 'UNKNOWN' &&
    Number.isSafeInteger(value.bytes) && value.bytes > 0 &&
    typeof value.sha256 === 'string' && /^[0-9a-f]{64}$/.test(value.sha256);
  const fileRef = value => isFileRef(value)
    ? { path: value.path, bytes: value.bytes, sha256: value.sha256 } : null;
  const sameFileRef = (left, right) => isFileRef(left) && isFileRef(right) &&
    left.path === right.path && left.bytes === right.bytes &&
    left.sha256 === right.sha256;
  const sameReferenceToken = (left, right) => left === right ||
    sameFileRef(left, right);
  const samePriorCandidateRefs = (left, right) => left === right ||
    (Array.isArray(left) && Array.isArray(right) &&
     left.length === right.length &&
     left.every((item, index) => sameReferenceToken(item, right[index])));
  const copyReferenceToken = value => isFileRef(value) ? fileRef(value) : value;
  const matchesObservationAsset = (value, assets) => {
    const ref = fileRef(value);
    return !!ref && (sameFileRef(ref, assets.screenshot) ||
      sameFileRef(ref, assets.ax));
  };
  const appendBlockers = (blockers, checks) => {
    for (const [code, invalid] of checks) {
      if (invalid && !blockers.includes(code)) blockers.push(code);
    }
    return blockers;
  };
  const sameWindowBinding = (left, right) => isObject(left) && isObject(right) &&
    left.app_bundle_id === right.app_bundle_id && left.window_id === right.window_id;

  function checkIntent(options) {
    if (!isObject(options) || !isObject(options.intent) ||
        !isId(options.intent.attempt_id)) {
      return stop('INTENT_READBACK_INVALID');
    }
    if (options.intent.status !== 'UNKNOWN' ||
        options.intent.dispatch_authorized !== false) {
      return stop('INTENT_NOT_DISPATCHABLE');
    }
    if (!isEventRef(options.intentEventRef)) {
      return stop('INTENT_EVENT_REF_INVALID');
    }
    if (!isObject(options.request) ||
        options.request.attempt_id !== options.intent.attempt_id) {
      return stop('INTENT_ATTEMPT_MISMATCH');
    }
    if (!sameEventRef(options.request.intent_event_ref,
                      options.intentEventRef)) {
      return stop('INTENT_EVENT_REF_MISMATCH');
    }
    return ready({
      attempt_id: options.intent.attempt_id,
      intent_event_ref: { sequence: options.intentEventRef.sequence,
                          event_sha256: options.intentEventRef.event_sha256 },
    });
  }

  function revealOrdinalBlocker(request) {
    const ordinal = request.candidate_ordinal;
    const budgetMismatch = ordinal === 1
      ? request.budget_before !== 0 || request.budget_after !== 1 ||
        request.prior_candidate_refs !== 'NONE'
      : ordinal === 2 && (request.budget_before !== 1 ||
        request.budget_after !== 2 || !Array.isArray(request.prior_candidate_refs) ||
        request.prior_candidate_refs.length === 0 ||
        !Array.from(request.prior_candidate_refs).every(isReferenceToken));
    if (budgetMismatch) return 'REVEAL_ORDINAL_BUDGET_MISMATCH';
    return ordinal === 1 || ordinal === 2 ? null : 'REVEAL_ORDINAL_INVALID';
  }

  function checkReveal(options) {
    const gate = checkIntent(options);
    if (gate.status !== 'READY') return gate;
    const request = options.request;
    if (request.input_phase !== 'NAVIGATION') {
      return stop('REVEAL_PHASE_INVALID');
    }
    if (request.navigation_kind !== 'selected-filmstrip-safe-edge') {
      return stop('REVEAL_KIND_UNSUPPORTED');
    }
    const ordinalBlocker = revealOrdinalBlocker(request);
    if (ordinalBlocker) return stop(ordinalBlocker);
    return ready({ ...gate, candidate_ordinal: request.candidate_ordinal });
  }

  function directReadinessBlockers(decision, assets) {
    return appendBlockers([
      ...evidenceTools.groundedCoordinateBlockers(decision),
      ...evidenceTools.groundedGeometryBlockers(
        decision.control_region, decision.candidate_point, decision.prepared_target),
    ], [
      ['DOWNLOAD_CONTROL_VISIBILITY_REQUIRED',
       decision.control_visibility !== 'VISIBLE'],
      ['DOWNLOAD_CONTROL_OWNER_REQUIRED', decision.control_owner !== 'MATCH'],
      ['DOWNLOAD_CONTROL_NOT_ENABLED', decision.enabled_state !== 'ENABLED'],
      ['DOWNLOAD_CONTROL_POSITION_SOURCE_MISMATCH',
       !matchesObservationAsset(decision.position_source_ref, assets)],
    ]);
  }

  function revealReadinessBlockers(decision, assets) {
    const ordinalBlocker = revealOrdinalBlocker(decision);
    return appendBlockers([
      ...evidenceTools.groundedCoordinateBlockers(decision, 'REVEAL',
        {requireGrounding: false, requirePointRelation: false}),
      ...evidenceTools.groundedGeometryBlockers(
        decision.safe_zone, decision.prepared_target, decision.prepared_target,
        {missing: 'REVEAL_SAFE_ZONE_INVALID',
         interior: 'REVEAL_TARGET_NOT_STRICT_INTERIOR', targetMismatch: null}),
    ], [
      ['REVEAL_KIND_UNSUPPORTED',
       decision.navigation_kind !== 'selected-filmstrip-safe-edge'],
      ['REVEAL_CANDIDATE_ID_REQUIRED',
       !isId(decision.reveal_candidate_id) || !isKnownString(decision.reveal_candidate_id)],
      ['REVEAL_SCOPE_REF_REQUIRED', !isReferenceToken(decision.reveal_scope_ref)],
      ['REVEAL_SELECTION_REQUIRED', decision.selected_state_before !== 'SELECTED'],
      ['REVEAL_SELECTED_MEDIA_REF_REQUIRED',
       !isReferenceToken(decision.selected_media_ref)],
      ['REVEAL_BEFORE_SCREENSHOT_MISMATCH',
       !sameFileRef(fileRef(decision.before_screenshot_ref), assets.screenshot)],
      ['REVEAL_BEFORE_AX_MISMATCH',
       !sameFileRef(fileRef(decision.before_ax_ref), assets.ax)],
      ['REVEAL_MAPPING_ID_REQUIRED', !isKnownString(decision.mapping_id)],
      ['REVEAL_MAPPING_TIME_REQUIRED', !isKnownString(decision.mapping_valid_at)],
      ['REVEAL_POSITION_SOURCE_MISMATCH',
       !matchesObservationAsset(decision.position_source_ref, assets)],
      ['REVEAL_SAFE_ZONE_REF_REQUIRED', !isReferenceToken(decision.safe_zone_ref)],
      [ordinalBlocker, !!ordinalBlocker],
      ['REVEAL_REARM_NEW_INFORMATION_REQUIRED',
       decision.candidate_ordinal === 2 &&
       (decision.rearm_new_information_conclusion !== 'PASS' ||
        !isReferenceToken(decision.rearm_preconditions_ref) ||
        !isReferenceToken(decision.rearm_new_information_ref))],
    ]);
  }

  function checkDownloadReadiness(options) {
    const input = isObject(options) ? options : {};
    const app = isObject(input.app) ? input.app : null;
    const assets = observationAssets(input.observation);
    const blockers = [
      ...(!app ? ['APP_HANDLE_REQUIRED'] : []),
      ...(app && typeof app.click !== 'function' ? ['APP_CLICK_UNAVAILABLE'] : []),
      ...(app && typeof app.getAXStateAndScreenshot !== 'function'
        ? ['APP_CAPTURE_UNAVAILABLE'] : []),
      ...evidenceTools.groundedWindowBlockers(input.windowBinding),
      ...(!assets || !isId(input.observation.observation_id)
        ? ['DOWNLOAD_OBSERVATION_INVALID'] : []),
      ...(!isObject(input.decision) ? ['DOWNLOAD_DECISION_REQUIRED'] : []),
      ...(!['DIRECT', 'REVEAL'].includes(input.branch)
        ? ['DOWNLOAD_BRANCH_INVALID'] : []),
    ];
    if (blockers.length) {
      return stop('DOWNLOAD_READINESS_BLOCKED', { blockers });
    }
    const branchBlockers = input.branch === 'DIRECT'
      ? directReadinessBlockers(input.decision, assets)
      : revealReadinessBlockers(input.decision, assets);
    if (branchBlockers.length > 0) {
      return stop('DOWNLOAD_READINESS_BLOCKED', { blockers: branchBlockers });
    }
    const base = {
      branch: input.branch,
      observation_id: input.observation.observation_id,
      window_binding: {
        app_bundle_id: input.windowBinding.app_bundle_id,
        window_id: input.windowBinding.window_id,
      },
      before_observation: assets,
    };
    if (input.branch === 'DIRECT') return ready(base);
    return ready({
      ...base,
      candidate_ordinal: input.decision.candidate_ordinal,
      budget_before: input.decision.budget_before,
      budget_after: input.decision.budget_after,
      reveal_candidate_id: input.decision.reveal_candidate_id,
      reveal_scope_ref: copyReferenceToken(input.decision.reveal_scope_ref),
      prior_candidate_refs: Array.isArray(input.decision.prior_candidate_refs)
        ? input.decision.prior_candidate_refs.map(copyReferenceToken)
        : input.decision.prior_candidate_refs,
    });
  }

  function checkPreIntentReveal(preIntentReveal) {
    if (!isObject(preIntentReveal) ||
        preIntentReveal.status !== 'READY' ||
        preIntentReveal.branch !== 'REVEAL' ||
        !Array.isArray(preIntentReveal.blockers) ||
        preIntentReveal.blockers.length !== 0 ||
        !isId(preIntentReveal.observation_id) ||
        !isObject(preIntentReveal.before_observation) ||
        !isFileRef(preIntentReveal.before_observation.screenshot) ||
        !isFileRef(preIntentReveal.before_observation.ax) ||
        evidenceTools.groundedWindowBlockers(preIntentReveal.window_binding).length) {
      return null;
    }
    const ordinalBlocker = revealOrdinalBlocker(preIntentReveal);
    if (ordinalBlocker ||
        !isId(preIntentReveal.reveal_candidate_id) ||
        !isReferenceToken(preIntentReveal.reveal_scope_ref)) return null;
    return preIntentReveal;
  }

  function checkRevealBefore(options) {
    const preIntentReveal = checkPreIntentReveal(options.preIntentReveal);
    if (!preIntentReveal) return stop('REVEAL_PREFLIGHT_REQUIRED');
    const beforeAssets = observationAssets(options.beforeObservation);
    if (!beforeAssets || !isId(options.beforeObservation.observation_id)) {
      return stop('REVEAL_BEFORE_OBSERVATION_INVALID');
    }
    // A reused path is stale even when its bytes changed; only new files prove
    // that this observation belongs after the intent.
    const reusedAsset = (fresh, prior) => isFileRef(fresh) && isFileRef(prior) &&
      (fresh.path === prior.path || sameFileRef(fresh, prior));
    const priorAssets = preIntentReveal.before_observation;
    if (options.beforeObservation.observation_id === preIntentReveal.observation_id ||
        reusedAsset(beforeAssets.screenshot, priorAssets.screenshot) ||
        reusedAsset(beforeAssets.ax, priorAssets.ax)) {
      return stop('REVEAL_BEFORE_OBSERVATION_NOT_FRESH');
    }
    const windowBlockers = evidenceTools.groundedWindowBlockers(options.windowBinding);
    if (windowBlockers.length) {
      return stop('REVEAL_WINDOW_BINDING_INVALID', { blockers: windowBlockers });
    }
    if (!sameWindowBinding(options.windowBinding, preIntentReveal.window_binding)) {
      return stop('REVEAL_WINDOW_BINDING_CHANGED');
    }
    if (options.request.reveal_candidate_id !== preIntentReveal.reveal_candidate_id ||
        !sameReferenceToken(options.request.reveal_scope_ref,
                            preIntentReveal.reveal_scope_ref) ||
        options.request.candidate_ordinal !== preIntentReveal.candidate_ordinal ||
        options.request.budget_before !== preIntentReveal.budget_before ||
        options.request.budget_after !== preIntentReveal.budget_after ||
        !samePriorCandidateRefs(options.request.prior_candidate_refs,
                                preIntentReveal.prior_candidate_refs)) {
      return stop('REVEAL_REQUEST_DRIFT');
    }
    const fresh = checkDownloadReadiness({
      app: options.app,
      observation: options.beforeObservation,
      windowBinding: options.windowBinding,
      branch: 'REVEAL',
      decision: options.request,
    });
    if (fresh.status !== 'READY') {
      return stop('REVEAL_BEFORE_OBSERVATION_BLOCKED', {
        blockers: fresh.blockers || ['REVEAL_BEFORE_OBSERVATION_BLOCKED'],
      });
    }
    return fresh;
  }

  async function persistReveal(options) {
    if (!isObject(options) || !isObject(options.request)) {
      return stop('REVEAL_REQUEST_REQUIRED');
    }
    const requestSnapshot = evidenceTools.snapshotJsonValue(options.request);
    if (!requestSnapshot.ok) {
      return stop('REVEAL_REQUEST_SERIALIZATION_FAILED', {
        error: requestSnapshot.error || {
          name: 'TypeError',
          message: requestSnapshot.code + (requestSnapshot.detail
            ? ':' + requestSnapshot.detail : ''),
        },
      });
    }
    const request = requestSnapshot.value;
    const gate = checkReveal({ ...options, request });
    if (gate.status !== 'READY') return gate;
    const validatedPreIntentReveal = checkPreIntentReveal(options.preIntentReveal);
    const freshGate = checkRevealBefore({ ...options, request });
    if (freshGate.status !== 'READY') return freshGate;
    const candidateOrdinal = request.candidate_ordinal;
    const preIntentObservationId = validatedPreIntentReveal.observation_id;
    const beforeObservationId = options.beforeObservation.observation_id;
    const operationId = 'notes-reveal-c2-' + gate.attempt_id;
    try {
      const run = await persistRevealWithDirectAfter({
        taskDir: options.taskDir,
        inputDir: options.inputDir,
        observationDir: options.observationDir,
        operationId,
        observationId: operationId + '-after',
        request,
        app: options.app,
      });
      const invoked = run.fail_closed === false;
      return {
        ...gate,
        ...freshGate,
        status: invoked ? 'INVOKED' : 'STOP',
        reason: invoked ? null : 'REVEAL_INPUT_OR_AFTER_INCOMPLETE',
        blockers: invoked ? [] : ['REVEAL_INPUT_OR_AFTER_INCOMPLETE'],
        operation_id: operationId,
        candidate_ordinal: candidateOrdinal,
        pre_intent_observation_id: preIntentObservationId,
        before_observation_id: beforeObservationId,
        run,
        afterObservation: run.afterObservation,
      };
    } catch (error) {
      return stop('REVEAL_WRAPPER_FAILED', {
        operation_id: operationId,
        error: evidenceTools.describeError(error),
      });
    }
  }

  function observationAssets(observation) {
    if (!isObject(observation) || observation.ready_for_bind !== true ||
        !isObject(observation.assets)) return null;
    const screenshot = fileRef(observation.assets.screenshot);
    const ax = fileRef(observation.assets.ax);
    return screenshot && ax ? { screenshot, ax } : null;
  }

  function downloadSource(options, gate) {
    const request = options.request;
    if ((options.reveal === undefined) === (options.observation === undefined)) {
      return stop(options.reveal === undefined
        ? 'DOWNLOAD_OBSERVATION_REQUIRED' : 'DOWNLOAD_OBSERVATION_AMBIGUOUS');
    }
    let mode;
    let assets;
    if (options.reveal !== undefined) {
      const reveal = options.reveal;
      if (!isObject(reveal) || reveal.status !== 'INVOKED' ||
          reveal.attempt_id !== gate.attempt_id ||
          reveal.operation_id !== 'notes-reveal-c2-' + gate.attempt_id ||
          !isObject(reveal.run) || reveal.run.fail_closed !== false) {
        return stop('REVEAL_AFTER_NOT_DISPATCHABLE');
      }
      if (!sameWindowBinding(request.app_window_binding, reveal.window_binding)) {
        return stop('DOWNLOAD_REVEAL_WINDOW_BINDING_MISMATCH');
      }
      assets = observationAssets(reveal.run.afterObservation);
      mode = 'REVEAL_SAME_AFTER';
    } else if (options.observation !== undefined) {
      assets = observationAssets(options.observation);
      mode = 'DIRECT_INTENT_OBSERVATION';
    }
    if (!assets) return stop('DOWNLOAD_OBSERVATION_INVALID');
    if (!sameFileRef(request.source_observation, assets.screenshot) ||
        !sameFileRef(request.mapping_evidence_ref, assets.ax)) {
      return stop('DOWNLOAD_SOURCE_OBSERVATION_MISMATCH');
    }
    return ready({ source_mode: mode,
                   source_observation: assets.screenshot });
  }

  async function persistDownload(options) {
    const gate = checkIntent(options);
    if (gate.status !== 'READY') return gate;
    const source = downloadSource(options, gate);
    if (source.status !== 'READY') return source;
    const operationId = 'notes-download-' + gate.attempt_id;
    try {
      const receipt = await evidenceTools.persistGroundedDownloadClick({
        taskDir: options.taskDir,
        inputDir: options.inputDir,
        operationId,
        request: options.request,
        source_observation_bytes: options.source_observation_bytes,
        app: options.app,
      });
      const invoked = receipt.status === 'INVOKED';
      return {
        ...gate,
        status: invoked ? 'INVOKED' : 'STOP',
        reason: invoked ? null : 'DOWNLOAD_SLOT_OR_HELPER_BLOCKED',
        blockers: invoked ? []
          : (receipt.blockers || ['DOWNLOAD_SLOT_OR_HELPER_BLOCKED']),
        operation_id: operationId,
        source_mode: source.source_mode,
        source_observation: source.source_observation,
        receipt,
      };
    } catch (error) {
      return stop('DOWNLOAD_WRAPPER_FAILED', {
        operation_id: operationId,
        error: evidenceTools.describeError(error),
      });
    }
  }

  return { checkDownloadReadiness, persistDownload, persistReveal };
})();
```
<!-- notes-intent-dispatch:end -->

### Intent 前下載就緒 gate

`notesIntentDispatch.checkDownloadReadiness({app, observation, windowBinding, branch, decision})` 是 intent 前的純同步檢查：只讀 Agent 已呈現、判讀並讀回的同一 `app`／`observation`，加當次 window binding 與 B1 decision；不執行 CLI、click／capture，也不建立 intent／attempt／staging 或固定 slot。輸出只有 `READY`／`STOP`，`STOP.blockers` 保留具體缺口，但不替 Agent 證明歷史、GUI sensor、控制命中或派送授權。

共同條件是同一 live app handle 具備 `click` 與 `getAXStateAndScreenshot`、observation `ready_for_bind=true` 及原始截圖／AX refs，且 binding 為 `jp.naver.line.mac` 加已知非 `UNKNOWN` window id；不足即 `APP_WINDOW_CONTEXT_REQUIRED` 或對應 observation/app blocker。

- `DIRECT`：`VISIBLE`、`MATCH` owner／mapping、`ENABLED`、`PRE_INPUT`、`PASS_TO_INPUT`、`INSIDE`、相同已知座標空間且 `coordinate_space_match=MATCH`；control region／候選點有限，prepared target 相同且為嚴格內點。`position_source_ref` 須是同一 observation 的截圖或 AX ref。
- `REVEAL`：只接受既有 `selected-filmstrip-safe-edge`（其他方法為 `REVEAL_KIND_UNSUPPORTED`）；保留候選 id／scope、已選媒體、同一 before 截圖／AX refs、安全區 ref、有限嚴格內點 target、mapping id／時間／座標空間／position ref，以及 ordinal／budget／prior refs。候選 1 為 `0→1`／`NONE`。候選 2 為 `1→2`，每個 prior ref 都須有實際值。intent 前還須有 `rearm_preconditions_ref`、`rearm_new_information_ref` 與 B1 判定的 `rearm_new_information_conclusion=PASS`。原因、同一媒體連續性及前次 request／raw／after 的完整性由 Agent 依 B1 核對。

`READY` 只允許接既有 intent；仍須完成 B1 判斷，intent 讀回後用當次 observation 或同一 reveal after 重新核對。`STOP` 走 B1 局部停止：不建 intent、不送 reveal、不消耗該媒體 v5；無全域 blocker 且可安全返回時才接續其他合格項。

控制可見時，只有 `controlVisible === true` 才建立 `DIRECT` decision 並求值其欄位；若另有可獨立稽核的 reveal 方法，才在同一 observation 上再建立 `REVEAL` decision 並保留其 `READY`。未啟用分支的 decision 與其 `CURRENT_*` 佔位符保持未宣告、不求值。可見但 `DIRECT` 非 `READY` 時，即使備選 `REVEAL READY` 也停在 intent 前，不先送 reveal。備選 `REVEAL` 的 `STOP` 不抹除合格 `DIRECT`。控制未見時只有 `REVEAL READY` 可進 intent；可見性未明時兩條路徑都不成立。兩者即使都 `READY`，仍只建立一次 intent，選 `DIRECT` 並保留同次備選 `READY`；控制轉為隱藏時才改走 REVEAL。intent 前不得送出 preflight capture、GUI 輸入或建立固定 slot（三者均為零）。

**前置範例。** 沿用本輪已呈現並讀回的 `app`／`observation` 和當次 `windowBinding`。只在充分原件支持控制可見或未見時，將 `controlVisible` 設為 `true` 或 `false`；可見性未明時用 `null`。安全 reveal 方法獨立成立時才把 `revealMethodIndependentlyAuditable` 設為 `true`。`CURRENT_*` 只填由該原件支持的值，且只實例化實際啟用的分支；未啟用分支的 decision 與其佔位符保持未宣告、不求值。控制與 target 使用同一已知座標空間；控制區與安全區須有限，target 須為嚴格內點。reveal 預檢依 `REVEAL_CANDIDATE_ORDINAL` 建立候選 1 或候選 2 的完整 arm；候選 2 的 `prior_candidate_refs` 與三個 rearm 欄位只在 ordinal 2 時求值，intent 後 reveal 路徑沿用同一 ordinal。

<!-- notes-intent-preflight:start -->
```js
const readinessRef = asset => asset && ({
  path: asset.path, bytes: asset.bytes, sha256: asset.sha256,
});
const controlVisible = B1_CONTROL_VISIBLE;
const revealMethodIndependentlyAuditable =
  B1_REVEAL_METHOD_INDEPENDENTLY_AUDITABLE;
const screenshot = readinessRef(observation?.assets?.screenshot);
const ax = readinessRef(observation?.assets?.ax);
const makeCommonDecision = () => ({
  mapping_status: 'MATCH', observation_order: 'PRE_INPUT',
  coordinate_space_match: 'MATCH',
  control_region_coord_space: CURRENT_CONTROL_COORDINATE_SPACE,
  target_coord_space: CURRENT_TARGET_COORDINATE_SPACE,
  position_source_ref: screenshot,
});
const common = {app, observation, windowBinding};
let directReadiness = null;
if (controlVisible === true) {
  const directDecision = {
    ...makeCommonDecision(),
    control_visibility: 'VISIBLE', control_owner: 'MATCH', enabled_state: 'ENABLED',
    grounding_conclusion: 'PASS_TO_INPUT', candidate_point_relation: 'INSIDE',
    control_region: CURRENT_CONTROL_REGION,
    candidate_point: CURRENT_CANDIDATE_POINT,
    prepared_target: CURRENT_VERIFIED_DOWNLOAD_TARGET,
  };
  directReadiness = notesIntentDispatch.checkDownloadReadiness({
    ...common, branch: 'DIRECT', decision: directDecision,
  });
}
let preIntentReveal = null;
if (revealMethodIndependentlyAuditable === true &&
    (controlVisible === true || controlVisible === false)) {
  const revealPreviewArm = REVEAL_CANDIDATE_ORDINAL === 1
    ? {
        candidate_ordinal: 1, prior_candidate_refs: 'NONE',
        budget_before: 0, budget_after: 1,
      }
    : REVEAL_CANDIDATE_ORDINAL === 2
      ? {
          candidate_ordinal: 2, prior_candidate_refs: CURRENT_PRIOR_CANDIDATE_REFS,
          budget_before: 1, budget_after: 2,
          rearm_preconditions_ref: CURRENT_REARM_PRECONDITIONS_REF,
          rearm_new_information_ref: CURRENT_REARM_NEW_INFORMATION_REF,
          rearm_new_information_conclusion:
            CURRENT_B1_REARM_NEW_INFORMATION_CONCLUSION,
        }
      : { candidate_ordinal: REVEAL_CANDIDATE_ORDINAL };
  const revealDecision = {
    ...makeCommonDecision(),
    navigation_kind: 'selected-filmstrip-safe-edge',
    reveal_candidate_id: CURRENT_REVEAL_CANDIDATE_ID,
    reveal_scope_ref: CURRENT_LIST_POST_MEDIA_SCOPE,
    ...revealPreviewArm,
    before_screenshot_ref: screenshot, before_ax_ref: ax,
    selected_state_before: 'SELECTED',
    selected_media_ref: CURRENT_SELECTED_MEDIA_REF,
    safe_zone_ref: CURRENT_SAFE_EDGE_REF,
    safe_zone: CURRENT_VERIFIED_SAFE_EDGE_REGION,
    prepared_target: CURRENT_VERIFIED_SAFE_EDGE_TARGET,
    mapping_id: CURRENT_MAPPING_ID, mapping_valid_at: CURRENT_MAPPING_VALID_AT,
  };
  preIntentReveal = notesIntentDispatch.checkDownloadReadiness({
    ...common, branch: 'REVEAL', decision: revealDecision,
  });
}
const retainedReveal = preIntentReveal?.status === 'READY'
  ? preIntentReveal : null;
const intentReadiness = controlVisible === false ? retainedReveal : directReadiness;
nodeRepl.write(JSON.stringify({
  next_action: intentReadiness?.status === 'READY'
    ? 'RUN_EXISTING_NOTES_INTENT_ONCE' : 'B1_LOCAL_STOP',
  directReadiness, preIntentReveal, retainedReveal,
}, null, 2));
```
<!-- notes-intent-preflight:end -->

只有 `RUN_EXISTING_NOTES_INTENT_ONCE` 才執行一次已解析的既有 notes `intent` CLI 並讀回；`B1_LOCAL_STOP` 保留該項與 blockers，不派送。`next_action` 只依目前可見分支決定：可見時看 `directReadiness`，隱藏時看 `retainedReveal`，所以可見但 `DIRECT` 非 `READY` 時不會被備選 `REVEAL READY` 解鎖。`DIRECT READY` 不因 `preIntentReveal STOP` 失效；`retainedReveal` 只保留同次 `REVEAL READY`，兩者都 READY 時仍選一次 DIRECT，並把備選帶到 intent 後備用。控制轉為隱藏時才改走 REVEAL。本預檢不 capture、不輸入、不建立 slot，也不消耗額度。

### 可直接複製的單一路徑

先保存既有 `intent` CLI 的 JSON，並由 Agent 唯讀核對該 attempt 的事件檔後帶入 `{sequence, event_sha256}`。以下只讀取已保存的 CLI 輸出與私有原件；不掃描事件、不重驗 schema，也不保存額外狀態：

<!-- notes-intent-readback:start -->
```js
const fs = await import('node:fs/promises');
const INTENT_READBACK = JSON.parse(await fs.readFile(
  '/ABS/PRIVATE_TASK/intent-readback.json', 'utf8'));
const asRef = asset => ({path: asset.path, bytes: asset.bytes, sha256: asset.sha256});
const makeIntentEventRef = (sequence, eventSha256) => {
  if (!Number.isSafeInteger(sequence) || sequence < 1 ||
      typeof eventSha256 !== 'string' || !/^[0-9a-f]{64}$/.test(eventSha256)) {
    throw new Error('INTENT_EVENT_REF_INVALID');
  }
  return {sequence, event_sha256: eventSha256};
};
const intentEventRef = makeIntentEventRef(
  Number((await fs.readFile(
    '/ABS/PRIVATE_TASK/intent-event.sequence', 'utf8')).trim()),
  (await fs.readFile(
    '/ABS/PRIVATE_TASK/intent-event.sha256', 'utf8')).trim(),
);
```
<!-- notes-intent-readback:end -->

`intent-readback.json`、`intent-event.sequence` 與 `intent-event.sha256` 是 Agent 對既有 CLI 輸出及同一 intent 事件唯讀核對後保存的輸入；本範本不掃描事件或重算 hash。這兩個事件值不是新的 schema 或持久控制器。

**intent 後唯一 capture。** intent 讀回後只取一次最新觀察（計畫所稱 Block 9）；DIRECT 從這份 `intentObservation` 取得定位與截圖 bytes，REVEAL 也直接以同一變數作 `beforeObservation`。不得再拍第二份 intent 後 capture，after 失敗也不得重拍。先保存並在同一 invocation 呈現這份原件；此時不建立下載 request、不呼叫 click：

<!-- notes-intent-capture:start -->
```js
let intentCapture = null;
let intentCaptureError = null;
const intentCaptureStartedAt = new Date().toISOString();
let intentCaptureReturnedAt = 'NOT_RUN';
try {
  intentCapture = await app.getAXStateAndScreenshot({emit: false, disableDiffing: true});
} catch (error) {
  intentCaptureError = evidenceTools.describeError(error);
} finally {
  intentCaptureReturnedAt = new Date().toISOString();
}
const intentObservation = await evidenceTools.persistObservation({
  taskDir: '/ABS/TASK_PRIVATE_DIR',
  observationDir: '/ABS/EXISTING_PRIVATE_OBSERVATION_DIR',
  observationId: 'INTENT_AFTER_OBSERVATION_ID',
  ...(intentCaptureError
    ? { captureError: intentCaptureError }
    : { capture: intentCapture }),
  hostCalls: {
    capture_call_started_at: intentCaptureStartedAt,
    capture_call_returned_at: intentCaptureReturnedAt,
  },
});
if (intentObservation.ready_for_bind && intentCapture) {
  await nodeRepl.emitImage(intentCapture.screenshot);
  nodeRepl.write(intentCapture.state);
}
nodeRepl.write(JSON.stringify({
  observation_id: intentObservation.observation_id,
  ready_for_bind: intentObservation.ready_for_bind,
  assets: intentObservation.assets,
}, null, 2));
```
<!-- notes-intent-capture:end -->

下列 request 建立器與派送函式同時供 DIRECT 與 REVEAL 兩條路徑使用；未選中的路徑不得執行，呼叫端只能傳入該路徑已核對的 observation 與截圖 bytes。

<!-- notes-download-builder:start -->
```js
const makeDownloadRequest = ({
  attemptId, intentEventRef, observation, windowBinding,
  controlRegion, target, coordinateSpace,
}) => {
  const screenshot = asRef(observation.assets.screenshot);
  return {
    input_phase: 'DOWNLOAD_CONTROL',
    attempt_id: attemptId,
    intent_event_ref: intentEventRef,
    app_window_binding: windowBinding,
    source_observation: screenshot,
    source_observation_ref: {...screenshot},
    mapping_evidence_ref: asRef(observation.assets.ax),
    mapping_status: 'MATCH',
    observation_order: 'PRE_INPUT',
    grounding_conclusion: 'PASS_TO_INPUT',
    candidate_point_relation: 'INSIDE',
    coordinate_space_match: 'MATCH',
    control_region_coord_space: coordinateSpace,
    target_coord_space: coordinateSpace,
    control_region: controlRegion,
    candidate_point: target,
    prepared_target: target,
  };
};

async function dispatchDownload({
  intentEventRef, observation, sourceObservationBytes, windowBinding,
  controlRegion, target, coordinateSpace, app, revealRun,
}) {
  const request = makeDownloadRequest({
    attemptId: INTENT_READBACK.attempt_id,
    intentEventRef,
    observation,
    windowBinding,
    controlRegion,
    target,
    coordinateSpace,
  });
  const source = revealRun === undefined ? {observation} : {reveal: revealRun};
  return notesIntentDispatch.persistDownload({
    taskDir: '/ABS/TASK_PRIVATE_DIR',
    inputDir: '/ABS/EXISTING_PRIVATE_INPUT_DIR',
    intent: INTENT_READBACK,
    intentEventRef,
    request,
    source_observation_bytes: sourceObservationBytes,
    app,
    ...source,
  });
}
```
<!-- notes-download-builder:end -->

**直接派送（步驟二）。** 只有 Agent 對 `intentObservation` 正面判讀控制可見、歸屬、啟用與映射成立後，才以下列四個判讀值呼叫同一個 `dispatchDownload`。`source_observation_bytes` 必須是同一份 `intentCapture.screenshot`；這是共用 capture，不再另拍：

<!-- notes-direct-dispatch:start -->
```js
const directDispatchDecision = {
  windowBinding: DIRECT_WINDOW_BINDING_FROM_OBSERVATION,
  controlRegion: DIRECT_CONTROL_REGION_FROM_OBSERVATION,
  target: DIRECT_DOWNLOAD_TARGET_FROM_OBSERVATION,
  coordinateSpace: DIRECT_COORDINATE_SPACE_FROM_OBSERVATION,
};
const directDownloadReceipt = await dispatchDownload({
  intentEventRef,
  observation: intentObservation,
  sourceObservationBytes: intentCapture.screenshot,
  ...directDispatchDecision,
  app,
});
```
<!-- notes-direct-dispatch:end -->

上例的 `DIRECT_*` 符號是 Agent 判讀後填入的明確輸入，不是可重用的常數；未完成判讀時不得建立 request。`fs` 只用來讀取已保存的 intent／事件核對值與 after 截圖 bytes；直接路徑的 `observation` 是 intent 後唯一 capture 的 `intentObservation`，`sourceObservationBytes` 使用同一份 `intentCapture.screenshot`，沒有額外 capture。

**Reveal 路徑。** 控制隱藏時，只有 B1 的當次安全區、選取、映射與額度都成立才呼叫。REVEAL 仍要求同一 viewer／window、有效前景、選取與三層身分一致、無 chooser／可歸屬活動下載／未決輸入、保留的 `READY` 與原額度；任一不足即沿用原停止規則。`beforeObservation` 直接承接上節唯一的 `intentObservation`，不取得第二份 intent 後 capture；`beforeWindowBinding` 必須屬於該同一原件。`revealCandidateArm` 依 `REVEAL_CANDIDATE_ORDINAL` 只建立一個完整 arm：`1` 為 `prior_candidate_refs='NONE'`、`0→1`；`2` 才填入前次原件的 `prior_candidate_refs`、本次條件的 `rearm_preconditions_ref`、新證據的 `rearm_new_information_ref`，並以這次 B1 正面判讀得到 `rearm_new_information_conclusion='PASS'`，不可沿用舊值或預填。未選中 arm 的 `CURRENT_*` 保持未宣告、不求值。request 帶齊 fresh gate 的映射、先後、座標空間與安全區欄位，並沿用同一固定 slot。

<!-- notes-reveal-path:start -->
```js
const beforeObservation = intentObservation;
const beforeWindowBinding = FRESH_WINDOW_BINDING_FROM_THIS_OBSERVATION;
const beforeScreenshotRef = asRef(beforeObservation.assets.screenshot);
const beforeAxRef = asRef(beforeObservation.assets.ax);
const revealCandidateArm = REVEAL_CANDIDATE_ORDINAL === 1
  ? {
      candidate_ordinal: 1, prior_candidate_refs: 'NONE',
      budget_before: 0, budget_after: 1,
    }
  : {
      candidate_ordinal: 2, prior_candidate_refs: CURRENT_PRIOR_CANDIDATE_REFS,
      budget_before: 1, budget_after: 2,
      rearm_preconditions_ref: CURRENT_REARM_PRECONDITIONS_REF,
      rearm_new_information_ref: CURRENT_REARM_NEW_INFORMATION_REF,
      rearm_new_information_conclusion:
        CURRENT_B1_REARM_NEW_INFORMATION_CONCLUSION,
    };
const revealRequest = {
  input_phase: 'NAVIGATION',
  attempt_id: INTENT_READBACK.attempt_id,
  intent_event_ref: intentEventRef,
  navigation_kind: 'selected-filmstrip-safe-edge',
  reveal_candidate_id: CURRENT_REVEAL_CANDIDATE_ID,
  reveal_scope_ref: CURRENT_LIST_POST_MEDIA_SCOPE,
  ...revealCandidateArm,
  before_screenshot_ref: beforeScreenshotRef,
  before_ax_ref: beforeAxRef,
  selected_state_before: 'SELECTED',
  selected_state_after: 'UNKNOWN',
  selected_media_ref: CURRENT_SELECTED_MEDIA_REF,
  safe_zone_ref: CURRENT_SAFE_EDGE_REF,
  safe_zone: CURRENT_FRESH_VERIFIED_SAFE_EDGE_REGION,
  mapping_status: 'MATCH',
  observation_order: 'PRE_INPUT',
  coordinate_space_match: 'MATCH',
  control_region_coord_space: CURRENT_FRESH_CONTROL_COORDINATE_SPACE,
  target_coord_space: CURRENT_FRESH_TARGET_COORDINATE_SPACE,
  mapping_id: CURRENT_MAPPING_ID,
  mapping_valid_at: CURRENT_MAPPING_VALID_AT,
  position_source_ref: beforeScreenshotRef,
  prepared_target: CURRENT_VERIFIED_SAFE_EDGE_TARGET,
};
const revealRun = await notesIntentDispatch.persistReveal({
  taskDir: '/ABS/TASK_PRIVATE_DIR',
  inputDir: '/ABS/EXISTING_PRIVATE_INPUT_DIR',
  observationDir: '/ABS/EXISTING_PRIVATE_OBSERVATION_DIR',
  intent: INTENT_READBACK,
  intentEventRef,
  request: revealRequest,
  preIntentReveal: retainedReveal,
  beforeObservation,
  windowBinding: beforeWindowBinding,
  app,
});
const revealAfter = revealRun.afterObservation;
const revealAfterBytes = revealRun.status === 'INVOKED' &&
  revealAfter?.ready_for_bind
  ? new Uint8Array(await fs.readFile(revealAfter.assets.screenshot.path))
  : null;
if (revealAfterBytes !== null) {
  await nodeRepl.emitImage(revealAfterBytes);
  nodeRepl.write(await fs.readFile(revealAfter.assets.ax.path, 'utf8'));
}
nodeRepl.write(JSON.stringify(revealRun, null, 2));
```
<!-- notes-reveal-path:end -->

候選 2 不能只改 ordinal／額度／prior refs；必須讓 `REVEAL_CANDIDATE_ORDINAL=2` 建立完整 arm，`rearm_new_information_conclusion` 只有等於 `'PASS'` 才能通過原 gate。

`preIntentReveal` 只接受 intent 前 `REVEAL READY` 的結果；`beforeObservation` 是 intent 後唯一 fresh 原件，`beforeWindowBinding` 必須屬於同一原件，且 window binding 仍與事前相同。fresh 判定同時比對 observation ID 與截圖／AX 各自的 path 或完整 file ref：任一重複即 `REVEAL_BEFORE_OBSERVATION_NOT_FRESH`，即使同一 path 的 bytes／hash 已改變；兩個新 path 可有相同內容 SHA-256。helper 不要求 fresh 的位置、安全區與選取證據 ref 等於 pre-intent 原件；它只比較不變的 scope／候選 id／ordinal／budget／prior refs，再以原 gate 檢查 fresh refs 與 request／observed assets 的配對。選取、三層身分、前景及新資訊真實性仍由 Agent 依當次原件正面判讀。

`persistReveal` 在第一個 `await` 前先要求 request 為物件，缺值回 `REVEAL_REQUEST_REQUIRED`；再以 `evidenceTools.snapshotJsonValue` 建立與呼叫端巢狀物件脫離的私有 JSON 快照，不可完整序列化回 `REVEAL_REQUEST_SERIALIZATION_FAILED`，兩者都在 slot、click 與 after capture 前停止。`checkReveal`、`checkRevealBefore` 與 `persistRevealWithDirectAfter` 都只用該快照；回報的 `candidate_ordinal`、`pre_intent_observation_id` 與 `before_observation_id` 也在同步階段定稿。固定使用 `notes-reveal-c2-<attempt_id>` 與 `<slot>-after`；request 先以 `wx` 保存並讀回，再由讀回值的 `prepared_target` 於同一 callback 送一次 click 並 capture，app handle 的方法接收者不拆開。只有 `revealRun.status=INVOKED`、`run.fail_closed=false` 且 `afterObservation.ready_for_bind=true`，Agent 才正面判讀這份 after 的控制可見、歸屬、啟用、三層身分、前景與映射。任何 input error／timeout、capture error、空 after、再消失或證據不完整都停止；已開始的 input 不得重送，也不得重拍 after。證據不足、已有下載呼叫或 outcome 時沿用原停止規則，不因共用 capture 放寬。

**同一 after 下載。** Agent 正面核對後，以下載 request 的 `source_observation`／`source_observation_ref` 指向同一份 after 截圖，`mapping_evidence_ref` 指向同一 after AX。該原件的 window binding 須與這次 reveal 一致。只使用同一份 after 上重新判定的座標。以已保存的截圖 bytes 呼叫既有 helper；同一份 after 的 capture 邊界留在 `afterObservation.hostCalls`，不另拍。

<!-- notes-reveal-download:start -->
```js
const revealDownloadReceipt = await dispatchDownload({
  intentEventRef,
  observation: revealAfter,
  sourceObservationBytes: revealAfterBytes,
  windowBinding: AFTER_WINDOW_BINDING_FROM_THIS_OBSERVATION,
  controlRegion: AFTER_CONTROL_REGION_FROM_THIS_OBSERVATION,
  target: AFTER_DOWNLOAD_TARGET_FROM_THIS_OBSERVATION,
  coordinateSpace: AFTER_COORDINATE_SPACE_FROM_THIS_OBSERVATION,
  revealRun,
  app,
});
```
<!-- notes-reveal-download:end -->

`persistDownload` 先核對 attempt、event ref，以及 request 是否指向該次 `observation`／`revealRun.afterObservation` 的同一截圖與 AX，再交給原 `persistGroundedDownloadClick`。canonical path、bytes、hash、request 幾何與 schema 仍由該既有 helper 驗證。它固定使用 `notes-download-<attempt_id>`；slot 已存在、並行競爭、讀回失敗或 observation 不符時，原 helper 不呼叫 click。直接與 reveal 兩條路徑只能選一條；direct 與 after 的決策變數不可互相展開或沿用，之後仍由 Agent 正面判讀畫面；wrapper 不是 GUI sensor、controller 或新的驗證層。

每 attempt 仍只有一次 intent、一次 reveal、每媒體兩次 reveal 額度、候選 2 的新證據、固定 slot，以及下載與 chooser 最終確認各一次；這條共用 capture 與 host 邊界記錄不增加 capture、click 或 retry 次數。

### 時序、狀態與停止

前置與停止決策依 [目標與下載控制就緒（B1）](gui-inventory.md#目標與下載控制就緒b1) 的連結摘要：Agent 播放輸入恆為 `NONE`；來源播放狀態與任何來源／選取／幾何／映射漂移分開記錄，是否繼續或停止仍以 B1 為準。索引／來源身分漂移、幾何／映射失效、控制遮蔽或輸入不明時依 B1 停止，且不以返回或 reopen 重設一次額度。

- statement 記錄 `observed_at`、`input_at`、`clock_source`、`timezone`、`precision`、capture／input 的相對序號，以及 `capture_wait_semantics`／`capture_wait_source`。除非當次工具文件或實測能證明，等待能力一律 `UNKNOWN`；不得宣稱 capture 原子、立即或能捕捉點擊瞬間。截圖或 AX 範圍不足、輸入或等待狀態無法從當次原件確認時，相關觀察欄位記 `UNKNOWN`，不自行補值；只有相對序號可支持先後，不能補出點擊與截圖的未證明時間差。
- `TOOLBAR_VISIBLE` 只在 intent 後最新、充分涵蓋的 after 原件正面顯示工具列，且下載控制歸屬、啟用與映射成立時使用；它不是穩定可重播的保證。充分範圍仍看不到 toolbar 記 `TOOLBAR_NOT_SHOWN`；只表示本次 bounded observation 沒有顯示，不能推論控制不存在。若 toolbar 曾出現後在有效觀察中消失，記 `REVEAL_TRANSIENT`。本 attempt 的 reveal 最多一次；已送出、error、timeout、capture 失敗或證據不足都不得再試，也不得跨 attempt 重用舊 after。
- 另記 `stop_reason`（例如 `PRECONDITION_UNPROVEN`、`MAPPING_STALE`、`CAPTURE_INCOMPLETE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT`）。`TOOLBAR_VISIBLE`／`TOOLBAR_NOT_SHOWN`／`REVEAL_TRANSIENT` 是 statement 結論，不是 Notes 六類業務狀態，也不會把未派送媒體改成完成或排除。已派送 input 後依原 attempt 的真實結果分流；證據不足記 `UNKNOWN`，不得預填 outcome 或建立替代 attempt。
- `observation.hostCalls.capture_call_returned_at` 只配對 `receipt.hostCalls.dispatch_call_started_at`：DIRECT 用共用 `intentObservation` 的 capture，REVEAL 用同一次 after capture。gate、request 或 slot 在呼叫前拒絕時，對應時間維持 `NOT_RUN`；缺值、時間來源不可比或時鐘倒退時，延遲記為不可判定。這組證據只界定 host API 呼叫邊界（`HOST_JS_DATE`／`CALL_BOUNDARY_ONLY`），不證明工具列壽命、OS hit-test 或下載結果。

### 永久保存與合法附掛順序

1. **新 scan 的細盤事件尚未寫入。** 先完成該 scan、post 與 media 的合法細盤，並保存細盤當時的非 reveal 盤點原件；在 append 前只把這些當時已存在的盤點證據封裝成 v2 bundle，再把 `bundle_path` 傳給該次 `post` 或 `media` 的 `--evidence`。`post`／`media` event context 均為 `list_key + post_key + scan_id`；`media_key` 只可寫在 statement，不能填入該事件 context。細盤保存後才建立 intent；本 attempt 的 reveal before／input／after 或 direct after 原件不得回填到已 append 的細盤事件，應按合法 outcome context 保存（見下一點）。
2. **post／media 細盤已寫入。** 細盤事件只保存當時的非 reveal 盤點原件；同 scan 的 `post`／`media` 各只能追加一次，沒有「再補 observation」的合法命令。此時 intent 後的 direct／reveal／after 原件與 pre-intent blocker 原件只能留在私有 task 區，尚未進永久帳本。不得為留證另開 scan，不得改用 `bind`、`protect`、`intent` 或 `outcome` 冒充附掛，也不得改寫舊 scan／detail／completion。日後同一個實際 attempt 有合法 outcome 時，才可把仍適用的 direct／reveal／after 原件依該 attempt 的精確 context 重新封裝；不得把沒有 attempt context 的 before-intent bundle 直接冒用為新 attempt 或另一個 context 的證據。新 attempt 需要自己的觀察與 context，舊 blocker 只能作歷史來源引用。
3. `evidence-pack` 本身只建立私有 bundle，不是永久帳本寫入；只有既有 event 成功保存並讀回其 evidence ref 後，才可聲稱已進永久帳本。若沒有可合法承載的既有事件，保留私有原件與 hash，明列「永久帳本未保存」，交回具體缺口；本方案不為補證據擴 schema、CLI 或交易。

## 自動補下載隔離證據

隔離只處置一個已知舊 attempt，不是新媒體認領、GUI 授權、停止證明或下載完成。statement 要能唯讀說明並引用：

- 舊 `list_key + post_key + media_key`、exact `attempt_id`／intent ref、第一筆 `UNKNOWN` outcome ref 與已完成的 reconcile 結果；三者需能唯一回到同一媒體，否則不得隔離。
- 原目的地 binding／staging 精確路徑與身分，以及以相容欄位 `staging_empty_ref` 引用隔離前的舊 staging 觀察：它可證明目錄為空，或只有符合隔離條件的單一穩定媒體檔及合格環境附屬項；此 observation 用來核對舊 attempt 的隔離形狀與原件保留，不證明 `NOT_SENT`。隔離後的新 attempt staging 必須另行核對為新建空目錄。
- 當次有效前景、目標列表／viewer 的 AX／截圖原件與涵蓋範圍；最新觀察是否看到舊 chooser／modal、可歸屬活動下載、來源歧義、pending naming、檔案異常或開放的手動 restart。缺席只在觀察範圍足夠時記 `NOT_OBSERVED`，否則 `UNKNOWN`。
- 隔離事件 ref、`disposition`／`redownload_remaining` 的 CLI 讀回值與衝突／拒絕原因；隔離本身零消耗，後續 v5 intent 才消耗一次額度。隔離 event context 依 CLI 契約綁舊 intent／scan，不借用一個不存在的新 scan 冒充來源。

隔離成功後的新完整掃描、目標細盤、新 empty staging、control／chooser 與結果仍各自需要新的當次證據。舊 attempt 的晚到檔只作舊 staging 的事實，不能附掛成新 attempt 的完成或發布證據。

## 必錄欄位

| 區塊 | 欄位／內容 | 最低要求 |
|---|---|---|
| 身分 | `list_key`、`post_key`、`media_key`、`source_order` | key 以 notes CLI 產生／讀回值為準；任一層不能唯一對應就記 `UNKNOWN`，不得以顯示名稱、日期、張數、序號或單一 hash 代替 |
| Attempt | `attempt_id`、`intent_event_ref`、`outcome_event_ref`、`reconcile_event_refs`、`recovery_of`、`recovery_evidence_ref` | `attempt_id` 以 CLI 結果為準。現行 CLI 的 intent／outcome／reconcile 回傳 payload 不直接提供 event sequence；event ref 由唯讀核對 `events/%08d.json`（例如 `00000001.json`）、記錄 sequence 與該檔 SHA-256 讀回建立。同一 attempt 可多次 reconcile；每次都要新增一筆 `reconcile_event_refs`，保留全部 sequence／event SHA-256 與結果，不用最後一筆覆寫先前歷史。沒有 reconcile 記 `NOT_APPLICABLE`；任何一次無法唯一核對時，該次記 `UNKNOWN`，不得由資料夾、檔名或媒體 hash 反推 |
| 自動恢復隔離 | `isolation_event_ref`、`old_outcome_ref`、`reconcile_refs`、`destination_binding_ref`、`old_staging_ref`、`staging_empty_ref`、`foreground_ref`、`no_chooser_ref`、`no_active_download_ref`、`budget_before`、`budget_after`、`expected_tip` | 只在同一媒體、舊 attempt 已有持久 `UNKNOWN`、安全前提成立時記錄；隔離零消耗，`budget_before`／`budget_after` 應相等，只有其後有效 v5 intent append 才消耗唯一 v5 額度；statement 同時記錄同一 media key 的普通 intent 總額（上限三筆，含 v5）及隔離後的 `next_action`／`attempt_phase`，不得從 v1 disposition 單獨推斷仍可補下載。隔離不是 `STOPPED`／`NOT_SENT`，不得用隔離 statement 補成停止、下載或完成證據。舊 staging 之後出現晚到 bytes 時保留原處並更新事實，不轉正成新 attempt |
| Restart 批次 | `restart_id`、`generation`、`confirmation_ref`、`scope_digest`、`version_directory`、`owner_consent_ref`、`recovery_scan_id`、`prior_attempt_ref`、`activation_ref` | 只在精確 `restart preview`／Owner 明示同意／`restart confirm`／confirm 後完整 recovery scan 路徑使用。`confirmation_ref`、`generation`、`scope_digest`、`version_directory` 與新 attempt 必須對應同一個已確認批次；`owner_consent_ref` 指向當次可核對的 Owner 明示回覆，不能以 Prompt 本身、沉默、逾時或一般「繼續」代替。一般 attempt 或未使用欄位記 `NOT_APPLICABLE`；無法唯一讀回才記 `UNKNOWN`，不得由路徑或檔名猜值。此區塊是私有 statement 欄位，不是新的 CLI schema；傳給 CLI 的仍是既有 v2 `bundle_path` |
| 目的地 | `original_destination`、`destination_event_refs`、`observed_destination` | 原目的地以 intent 讀回值為準。目的地相關事件可能是 `created`（初始 root）、`destination`（追加 root）或 `intent`（attempt 目的地），各自以事件檔與讀回 hash 引用；`binding` 事件不含目的地。chooser 顯示或實際落點另記，不得反寫原目的地 |
| 觀察來源 | `observation_id`、`source_kind`、`tool`、`api_scope`、`app_window_binding`、`role_children_ref`、`raw_return_ref`、`scope`、`capture_rect`、`raw_rect`、`image_pixels`、`window_frame`、`window_points`、`scale_factor`、`popup_covered` | 記 AX／app-bound 截圖／桌面局部截圖／Computer Use 回傳／真人觀察，並分開 AX client／API scope、app／window 綁定與 role／children 來源；範圍、原始矩形、實際像素、點數與縮放分開，來源未涵蓋 popup 時不可推論不存在。同一 viewer 的 AX 相同不得推定工具列未變，截圖與 AX 也不能互相補值 |
| 身分與入口 | `identity_gate_id`、`viewer_title_ref`、`viewer_title_n_of_n`、`list_key`、`post_key`、`media_key`、`entry_anchor_ref`、`artifact_label`、`artifact_label_target`、`identity_match`、`accepted`、`quarantine_ref`、`entry_page_role`、`expected_return_role`、`return_result`、`input_capability_after` | gate 由 Agent 依當次原件持久核對並讀回，不是 helper 圖像辨識；label 不代替 keys。`expected_return_role` 只由當次可引用原件的實際 entry role 決定，不預填 `LIST`、`POST_DETAIL` 或其他期待值。返回後以 `post_input_observation_ref` 指向的原件記錄實際 `page_role` 與文字 basis；角色判定只依[返回契約](gui-inventory.md#返回契約與有限恢復)。角色與來源連續性相符才記 `RETURNED`；長貼文占滿 viewport、搜尋列／卡片標頭／返回控制不可見不足以判 `POST_DETAIL`，也不證明控制不存在。證據不足或矛盾時記 `page_role=UNKNOWN`、`return_result=RETURN_NOT_OBSERVED`；若正面觀察仍是 viewer，保留 `VIEWER` 並記 `RETURN_NOT_OBSERVED`；只有正面顯示角色／身分／錨點失去才記 `ENTRY_LOST`。輸入能力另記且可同時為 `UNAVAILABLE`；此列沿用既有欄位，不新增 schema |
| Reveal 導覽 | `navigation_kind`、`reveal_candidate_id`、`reveal_scope_ref`、`candidate_ordinal`、`prior_candidate_refs`、`budget_before`、`budget_after`、`rearm_preconditions_ref`、`rearm_new_information_ref`、`rearm_new_information_conclusion`、`selected_state_before`、`selected_media_ref`、`safe_zone_ref`、`safe_zone`、`mapping_status`、`observation_order`、`coordinate_space_match`、`control_region_coord_space`、`target_coord_space`、`mapping_id`、`mapping_valid_at`、`before_screenshot_ref`、`before_ax_ref`、`input_phase`、`input_receipt_ref`、`after_screenshot_ref`、`after_ax_ref`、`reveal_state`、`capture_wait_semantics`、`capture_wait_source`、`stop_reason` | 操作契約只依 `gui-inventory.md` 的 B1。每個 attempt 最多一次 intent 後 reveal；`candidate_ordinal=1` 對應 `prior_candidate_refs=NONE`、`budget_before=0`、`budget_after=1`，`candidate_ordinal=2` 對應完整的同一 scope 前次引用、`1`、`2`；候選 2 的 `rearm_new_information_conclusion` 只能由當次 B1 證據得到 `PASS`。`safe_zone`、映射狀態、先後、座標空間與 target 座標空間屬於 fresh gate，必須由同一 before 原件讀回，兩座標空間已知且相同，target 嚴格位於有限安全區內。slot 固定 `notes-reveal-c2-<attempt_id>`，c2 不因 ordinal 改名；本輪 request 以 `wx` 保存並讀回，不能跨 intent 重用舊點。before／input／after 各自保存 bytes／hash；同 AX 可重複但不得合併不同畫面。`TOOLBAR_VISIBLE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT` 是 statement 結論，不是業務狀態；capture 等待能力未證實時記 `UNKNOWN`，不得據 AX 缺失推定不存在 |
| 時間 | `observed_at`、`input_at`、`clock_source`、`timezone`、`precision` | 每個時間都要有來源；不可取得工具時間或可信時鐘時寫 `UNKNOWN`，不以 mtime 冒充操作時間。capture label／sequence 只能支持相對先後；不能證明是否在輸入前時，`observation_order=UNKNOWN`，不得把檔名或 label 寫成已證實的 pre-click |
| 來源與捕捉 | `capture_started_at`、`capture_returned_at`、`ax_observed_at`、`screenshot_observed_at`、`source_time_basis`、`capture_atomicity` | 分別保存 AX／截圖來源、bytes／hash 與可證明的時間；`capture_started_at`／`capture_returned_at` 只界定一次 API 呼叫，不證明兩來源同一瞬間。helper 的 observation diagnostic／下載 receipt 另以 `hostCalls` 記 host API 呼叫邊界，未執行或呼叫前拒絕為 `NOT_RUN`；它不代表工具列壽命、OS hit-test 或下載結果。工具未提供個別時間就記 `UNKNOWN`，不補值；`capture_atomicity=UNVERIFIED`，不得宣稱 atomic／immediate |
| 定位 | `page_role`、`focus_state`、`control_owner`、`control_visibility`、`enabled_state`、`position_source_ref`、`pre_input_observation_ref`、`post_input_observation_ref`、`observation_order`、`control_region`、`control_region_coord_space`、`candidate_point`、`candidate_point_relation`、`raw_coord_space`、`mapped_screen_point`、`coordinate_space_match`、`mapping_id`、`mapping_valid_at`、`grounding_conclusion` | 控制可見性只在充分範圍成立時記 `VISIBLE`／`NOT_OBSERVED`。由同一份當次原件記下控制區域及候選點，兩者使用相同座標空間並讀回；`position_source_ref` 指向截圖／AX 原件與 hash，先後不能判定時明記 `UNKNOWN`。候選點須在可辨識區域內部；區域外、邊界、控制歸屬／映射／先後／區域不明時，`grounding_conclusion=STOP`，不得輸入。`control_region` 是視覺篩選區域，不是原生 hit-test；通過只表示可送入對帳，不表示控制已命中 |
| 輸入 | `input_phase`、`action`、`target_ref`、`prepared_target`、`prepared_target_readback_ref`、`candidate_target_match`、`dispatched_target`、`receipt_target_match`、`input_tool`、`input_api`、`input_receipt_ref`、`raw_tool_return`、`error_raw`、`download_control_call_count`、`chooser_confirm_call_count` | `input_phase` 至少區分 `DOWNLOAD_CONTROL`、`CHOOSER_PATH`、`CHOOSER_CONFIRM`；記工具／API 及原始成功／錯誤／逾時，並分別累計兩個至多一次的呼叫。失敗、逾時與未知也計入。`prepared_target` 是真正要送出的值，須先寫入並讀回，且與 `candidate_point` 比對；不符或無法讀回時不得呼叫。`dispatched_target` 取自實際 input receipt，再與 `prepared_target` 比對；receipt 不符或無法讀回時記 `MISMATCH`／`UNKNOWN`，不得追認為正確定位，也不得據此改寫 `NOT_SENT`。receipt 只證明保存的工具參數，不是 OS event trace 或 LINE hit-test |
| Chooser | `appeared`、`attribution_basis`、`chooser_window_process`、`source_viewer_ref`、`attempt_link`、`path_field_readback`、`panel_current_directory`、`where_value`、`intent_staging_destination`、`destination_agreement`、`destination_check`、`confirm_raw_return` | PathTextField、panel current directory 與 intent staging 分開記錄；只有來源 viewer／attempt、視窗／process 與三者一致的新空白目的地能唯一對應才可確認；延遲出現仍不是下載完成 |
| 結果 | `terminal_signal`、`terminal_source_ref`、`terminal_observed_at`、`candidate_file_refs`、`stability_ref`、`file_attribution_basis` | 終結訊號與穩定檔集都要可歸屬原 attempt；截圖與 AX 的瞬態提示分開其來源／時間／範圍，空目錄、timeout、畫面未變或單一提示不足 |
| 驗證／完成 | `verification_ref`、`file_sha256`、`decode_scope`、`completion_event_ref`、`completion_readback_ref` | 引用 notes 的實際結果與工具輸出；本範本不替代檔案驗證或 completion 讀回 |
| 未知 | `unknowns` | 逐項列缺少的證據、原因及下一步可否安全繼續；不能用 `UNKNOWN` 當成完成或 `NOT_SENT` |

## 可複製骨架

```text
observation_id: UNKNOWN

identity:
  list_key: UNKNOWN
  post_key: UNKNOWN
  media_key: UNKNOWN
  source_order: UNKNOWN
  identity_gate_id: UNKNOWN
  viewer_title_ref: UNKNOWN
  viewer_title_n_of_n: UNKNOWN
  entry_anchor_ref: UNKNOWN
  artifact_label: UNKNOWN
  artifact_label_target: NEUTRAL or UNKNOWN or [declared list/post/media target]
  identity_match: MATCH or MISMATCH or UNKNOWN
  accepted: true or false or UNKNOWN
  mismatch_reason: UNKNOWN
  quarantine_ref: UNKNOWN

entry:
  entry_page_role: UNKNOWN
  expected_return_role: UNKNOWN
  expected_return_basis_ref: UNKNOWN
  return_input_receipt_ref: UNKNOWN
  return_result: RETURNED or RETURN_NOT_OBSERVED or ENTRY_LOST or UNKNOWN
  input_capability_after: AVAILABLE or UNAVAILABLE or UNKNOWN
  return_observation_ref: UNKNOWN

attempt:
  attempt_id: UNKNOWN
  intent_event_ref: UNKNOWN
  outcome_event_ref: UNKNOWN
  reconcile_event_refs: NOT_APPLICABLE or [每一筆 reconcile 的 sequence + event_sha256]
  recovery_of: NOT_APPLICABLE or UNKNOWN
  recovery_evidence_ref: NOT_APPLICABLE or UNKNOWN
  original_destination: UNKNOWN
  destination_event_refs: UNKNOWN

restart:
  restart_id: NOT_APPLICABLE or UNKNOWN
  generation: NOT_APPLICABLE or UNKNOWN
  confirmation_ref: NOT_APPLICABLE or UNKNOWN
  scope_digest: NOT_APPLICABLE or UNKNOWN
  version_directory: NOT_APPLICABLE or UNKNOWN
  owner_consent_ref: NOT_APPLICABLE or UNKNOWN
  recovery_scan_id: NOT_APPLICABLE or UNKNOWN
  prior_attempt_ref: NOT_APPLICABLE or UNKNOWN
  activation_ref: NOT_APPLICABLE or UNKNOWN

observation:
  source_kind: UNKNOWN
  tool: UNKNOWN
  api_scope: UNKNOWN
  app_window_binding: UNKNOWN
  role_children_ref: UNKNOWN
  raw_return_ref: UNKNOWN
  scope: UNKNOWN
  capture_rect: UNKNOWN
  raw_rect: UNKNOWN
  image_pixels: UNKNOWN
  window_frame: UNKNOWN
  window_points: UNKNOWN
  scale_factor: UNKNOWN
  popup_covered: UNKNOWN
  capture_started_at: UNKNOWN
  capture_returned_at: UNKNOWN
  ax_observed_at: UNKNOWN
  screenshot_observed_at: UNKNOWN
  source_time_basis: UNKNOWN
  capture_atomicity: UNVERIFIED
  observed_at: UNKNOWN
  clock_source: UNKNOWN
  timezone: UNKNOWN
  precision: UNKNOWN
  evidence_bundle_path: UNKNOWN
  evidence_bundle_sha256: UNKNOWN
  evidence_pack_command_ref: UNKNOWN

reveal:
  navigation_kind: NOT_APPLICABLE or selected-filmstrip-safe-edge
  reveal_candidate_id: UNKNOWN
  reveal_scope_ref: UNKNOWN
  candidate_ordinal: 1 or 2 or NOT_APPLICABLE or UNKNOWN
  prior_candidate_refs: NONE or [persisted candidate refs] or UNKNOWN
  budget_before: 0 or 1 or UNKNOWN
  budget_after: 1 or 2 or UNKNOWN
  rearm_preconditions_ref: UNKNOWN
  rearm_new_information_ref: UNKNOWN
  selected_state_before: UNKNOWN
  selected_state_after: UNKNOWN
  selected_media_ref: UNKNOWN
  safe_zone_ref: UNKNOWN
  safe_zone: UNKNOWN
  mapping_status: UNKNOWN
  observation_order: UNKNOWN
  coordinate_space_match: UNKNOWN
  control_region_coord_space: UNKNOWN
  target_coord_space: UNKNOWN
  mapping_id: UNKNOWN
  mapping_valid_at: UNKNOWN
  rearm_new_information_conclusion: UNKNOWN
  before_screenshot_ref: UNKNOWN
  before_ax_ref: UNKNOWN
  input_phase: NAVIGATION or NOT_APPLICABLE or UNKNOWN
  input_receipt_ref: UNKNOWN
  after_screenshot_ref: UNKNOWN
  after_ax_ref: UNKNOWN
  reveal_state: TOOLBAR_VISIBLE or TOOLBAR_NOT_SHOWN or REVEAL_TRANSIENT or UNKNOWN
  capture_wait_semantics: UNKNOWN
  capture_wait_source: UNKNOWN
  stop_reason: UNKNOWN

localization:
  page_role: UNKNOWN
  focus_state: UNKNOWN
  control_owner: UNKNOWN
  control_visibility: UNKNOWN
  enabled_state: UNKNOWN
  position_source_ref: UNKNOWN
  pre_input_observation_ref: UNKNOWN
  post_input_observation_ref: UNKNOWN
  observation_order: PRE_INPUT or POST_INPUT or UNKNOWN
  control_region: UNKNOWN
  control_region_coord_space: UNKNOWN
  candidate_point: UNKNOWN
  candidate_point_relation: INSIDE or OUTSIDE or BORDER or UNKNOWN
  raw_coord_space: UNKNOWN
  mapped_screen_point: UNKNOWN
  coordinate_space_match: MATCH or MISMATCH or UNKNOWN
  mapping_id: UNKNOWN
  mapping_valid_at: UNKNOWN
  grounding_conclusion: PASS_TO_INPUT or STOP or UNKNOWN
  # control_region is visual evidence, not a native hit-test target

input:
  input_phase: UNKNOWN
  action: UNKNOWN
  target_ref: UNKNOWN
  prepared_target: UNKNOWN
  prepared_target_readback_ref: UNKNOWN
  candidate_target_match: MATCH or MISMATCH or UNKNOWN
  dispatched_target: UNKNOWN
  receipt_target_match: MATCH or MISMATCH or UNKNOWN
  input_tool: UNKNOWN
  input_api: UNKNOWN
  input_at: UNKNOWN
  input_receipt_ref: UNKNOWN
  raw_tool_return: UNKNOWN
  error_raw: UNKNOWN
  download_control_call_count: UNKNOWN
  chooser_confirm_call_count: UNKNOWN

chooser:
  appeared: UNKNOWN
  attribution_basis: UNKNOWN
  chooser_window_process: UNKNOWN
  source_viewer_ref: UNKNOWN
  attempt_link: UNKNOWN
  observed_destination: UNKNOWN
  path_field_readback: UNKNOWN
  panel_current_directory: UNKNOWN
  where_value: UNKNOWN
  intent_staging_destination: UNKNOWN
  destination_agreement: UNKNOWN
  destination_check: UNKNOWN
  confirm_raw_return: UNKNOWN

result:
  terminal_signal: UNKNOWN
  terminal_source_ref: UNKNOWN
  terminal_observed_at: UNKNOWN
  candidate_file_refs: UNKNOWN
  stability_ref: UNKNOWN
  file_attribution_basis: UNKNOWN

verification:
  verification_ref: UNKNOWN
  file_sha256: UNKNOWN
  decode_scope: UNKNOWN
  completion_event_ref: UNKNOWN
  completion_readback_ref: UNKNOWN

unknowns:
  - UNKNOWN: state what evidence is missing and why the next action is blocked
```

## page／finish 覆蓋紀錄

本節是 [GUI 導覽與盤點](gui-inventory.md) 所要求之來源卡片台帳的私有摘要，**不是新的 CLI schema**；`evidence-pack` 不解析這些欄位，也不能把填表當成視覺完整或 finish 通過。原件、每個 viewport 與事件讀回仍要保存；`UNKNOWN` 不得用預期、總數或 page 回傳 key 回填。page 成功後才把實際 key 與讀回引用附在同一份紀錄。

```text
page_coverage:
  observation_ref: UNKNOWN
  local_card_ref: UNKNOWN
  card_region: UNKNOWN
  part: COMPLETE or TOP or MIDDLE or BOTTOM
  boundary_and_neighbors: UNKNOWN
  resolution: UNKNOWN
  page_index: UNKNOWN
  page_row: UNKNOWN
  readback_ref: UNKNOWN
  unresolved: UNKNOWN
  source_to_rows: UNKNOWN
  rows_to_source: UNKNOWN
  page_gate: UNKNOWN

finish_coverage:
  source_recheck_refs: UNKNOWN
  page_readback_refs: UNKNOWN
  top_bottom_refs: UNKNOWN
  ordered_union: UNKNOWN
  missing_or_duplicate: UNKNOWN
  unresolved_source_cards: UNKNOWN
  source_change: UNKNOWN
  finish_gate: UNKNOWN
```

`page_gate` 是提交前判斷：只有 `source_to_rows` 與 `rows_to_source` 都成立且待解為零時，才可在私有紀錄記為可提交；此時 `readback_ref` 仍為 `UNKNOWN`，不得把尚未發生的 page 讀回列為前置條件。`page` 成功後，才把回傳的實際 key 與事件讀回補到同一份紀錄；讀回若與提交成員或來源對應有差異，立即停止後續 page、finish、新 intent 與下載，且不得以 `evidence-correct` 改寫 page 成員。finish 另須逐頁核對已取得的 page 讀回、以原件重核全部 page、頂底、有序聯集與來源變動，任一缺口都保持停止。這裡的 gate 是 Agent 的人工判斷欄位，不是 CLI 狀態、GUI 授權或獨立驗收。完成 statement 應引用這份逐頁紀錄與原件，而不是只寫「頂底成立，共 N 篇」。

## 引用檔名與 hash

- 使用可避免覆寫的中性唯一檔名，例如 `<attempt_id>__<phase>__<sequence>__<source_kind>.<ext>`；不得因同名而覆寫先前證據。若要使用帶目標語意的 label，必須先通過上一節的 identity gate；label 即使 `MATCH` 也不能單獨建立歸屬。`evidence-pack` 會自行計算並核對原件 hash；不要手填或改寫 bundle 內部 hash。
- 保存 `evidence-pack` 的完整命令、exit code、stdout 與 stderr；用回傳的 `bundle_path`、outer SHA-256 及 context 作引用。hash 只證明 bundle／子 blob 的位元組與 context，不證明畫面真實、媒體身分、控制命中或下載完成。
- 檔名、相同 basename、隱藏副檔名、修改時間、hash、畫面出現順序與鄰近時間都不能單獨建立 attempt／chooser／檔案歸屬；每個 attempt 仍用獨立空白目的地，metadata 不足記 `UNKNOWN`，不新增全域改名器。
- 發現既有 label 與 viewer 身分矛盾時，保留原路徑與 bytes，記 `identity_match=MISMATCH`、`accepted=false`、`quarantine_ref`；不覆寫、不改名、不重封裝，也不拿它作另一 post／media 的證據。只可追加 correction note，舊 bytes 與既有正確 ledger completion 不動。

## 使用界限

- 主視窗截圖／AX 未涵蓋獨立 popup 或 chooser 時，控制可見性記 `UNKNOWN`；只有充分涵蓋的來源才可記 `NOT_OBSERVED`。不要猜全域座標或改用相簿流程。
- 同一「下載完畢」提示在截圖可見但 AX 不含時，只記截圖來源與當次範圍，不把 AX 記成看見；反之亦然。瞬態時間／涵蓋範圍不可得就寫 `UNKNOWN`，不為取得提示重新下載。
- input 原始成功／錯誤只證明工具回傳，不是 App 接受；chooser 只證明階段性回應，不是下載完成；終結訊號不等於檔案驗證；completion 也不等於外部副本或服務端原始位元相同。
- `intent` 已保存但沒有 outcome 時，第一筆真實結果用 `outcome`（可為 `UNKNOWN`）；只有已有 `outcome=UNKNOWN` 才用 `reconcile`。仍不明時，只有同一媒體符合 Skill 的安全隔離條件，才可先追加隔離事件保留舊 attempt；隔離零消耗；只在普通 intent 總額未滿三筆且 v5 未使用時，完成隔離後才開始的新完整掃描與細盤，再由一次 v5 intent append 建立新空白補下載。額度已用盡仍可隔離保留原結果，但不得新建 v5。其他情況不得 verify、建立新 attempt、重下或派下一項。
- 本範本與填入內容都不是 GUI 授權、實機結果、E2E PASS 或獨立驗收。相關案例見 [證據判定案例](evidence-decision-cases.md)。
