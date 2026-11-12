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

`--asset` 可重複；role 限 `screenshot`、`ax`、`input_receipt`、`command_stdout`、`command_stderr`、`observation`。statement 與畫面／AX 不可空；`command_stdout`／`command_stderr` 可為零 bytes。貼文層另加 `--post-key "$POST_KEY"`；媒體層再加 `--media-key "$MEDIA_KEY"` 及適用的 `--attempt-id "$ATTEMPT_ID"`／`--scan-id "$SCAN_ID"`。Owner 不需要提供 JSON、UUID、key、路徑或 hash。

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

## CUA 觀察原件落地

CUA 的觀察結果不會自動成為專案檔案。使用同一次 `getAXStateAndScreenshot` 取得完整 AX 與截圖，再從 CUA 的 Node runtime 直接寫入已存在的專案私有 task directory；不要從聊天摘要重建原件，也不要把 CUA 回傳貼進手寫 JSON。

先在終端機確認 `TASK_PRIVATE_DIR` 是本次任務在 `.local/line-backup/tasks/` 下的 canonical 私有目錄，建立尚不存在的 `OBSERVATION_DIR`，並產生只含英數、點、底線或連字號的唯一 `OBSERVATION_ID`。三個值都要代入絕對路徑；範例會再核對兩者是 canonical 路徑，且 observation directory 位於 task directory 下。檔名碰撞不是重試訊號；改用新的 observation ID。

下列第一段只在 CUA Node runtime 定義工具，第二段才實際取得並保存同一次回傳。`util.types.isUint8Array` 可接受真正的 Buffer／Uint8Array，包括 CUA 跨 realm 回傳值；`instanceof`、constructor 名稱或任意 array-like 都不是型別證明。副本只取 view 的 `byteLength`，不會把整個 backing buffer 當成影像。兩段之間不要另做 capture，也不要用 statement 或聊天摘要重建原件。

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
      ready_for_bind: false,
    };
    const setStage = (name, status, detail) => {
      metadata.stages[name] = Object.assign({ status }, detail || {});
    };
    const result = (blockers) => Object.assign({
      ready_for_bind: false,
      blockers,
      observation_id: options.observationId,
      files: metadata.files,
    }, metadata);

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
    if (capture && typeof capture.state === 'string' && capture.state.length > 0) {
      axBytes = Buffer.from(capture.state, 'utf8');
      setStage('AX', 'OK', { utf8_bytes: axBytes.length });
    } else if (capture && typeof capture.state === 'string') {
      setStage('AX', 'EMPTY');
      blockers.push('AX:EMPTY');
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

    const output = result(blockers);
    output.metadata_persistence = diagnostic;
    output.ready_for_bind = blockers.length === 0;
    return output;
  }

  async function captureAndPersist(options) {
    let capture = null;
    let captureError = null;
    try {
      const app = await cua.getApp('jp.naver.line.mac');
      capture = await app.getAXStateAndScreenshot({
        disableDiffing: true,
        emit: false,
      });
    } catch (error) {
      captureError = describeError(error);
    }
    return persistObservation(Object.assign({}, options, { capture, captureError }));
  }

  return {
    captureAndPersist,
    copyExactUint8Array,
    describeError,
    persistObservation,
    readbackExact,
    sha256,
    writeExclusive,
  };
})();
```
<!-- cua-evidence-tools:end -->

```js
const OBSERVATION = await evidenceTools.captureAndPersist({
  taskDir: '/ABS/TASK_PRIVATE_DIR',
  observationDir: '/ABS/OBSERVATION_DIR',
  observationId: 'UNIQUE_OBSERVATION_ID',
});
nodeRepl.write(JSON.stringify(OBSERVATION, null, 2));
if (!OBSERVATION.ready_for_bind) {
  throw new Error('CUA_RAW_OBSERVATION_INCOMPLETE: ' + OBSERVATION.blockers.join(', '));
}
```

`stages` 會分別留下 `CAPTURE`、`CAPTURE_SHAPE`、`AX`、`SCREENSHOT_TYPE`、`SCREENSHOT_LENGTH` 與各 asset 的 `*_PERSISTENCE`；`assets` 另記實際路徑、長度、SHA-256、寫入與讀回，`metadata_persistence` 則記 diagnostic 的寫入與讀回。只有 AX 與非空截圖都存在、兩者都以 `wx` 寫入並逐 bytes 讀回 MATCH，且 diagnostic 也寫入／讀回 MATCH，runtime 輸出的 `ready_for_bind` 才會是 `true`。AX 合格但截圖型別錯、空值或寫入失敗時，合格 AX 仍會保存；反向情況亦同。這些部分原件可用於唯讀診斷，但 blocker 未消除前不得 bind。

`CUA_RAW_OBSERVATION_INCOMPLETE` 是本地保存 gate，不是 CUA 沒有回傳或不支援該 API；依 `blockers`、`stages` 與部分 asset 判斷是缺值、型別、權限、碰撞或讀回問題。沒有新 bytes 時不要重作 GUI 輸入或猜測補值；若回傳 `regions` 等未實測形狀，保留可保存的部分與 `UNSUPPORTED_REGIONS`，交回精確範圍決策。

這段只保存 CUA 回傳的 bytes，不代表畫面真實、列表身分已確認或 GUI 權限成立。statement 另記實際 app／window、API、範圍與時間來源；未知值照實填 `UNKNOWN`。以剛保存的路徑作 `--asset ax` 與 `--asset screenshot` 執行既有 `evidence-pack`，再把 CLI 回傳的 bundle path 傳給 `bind --observation`／`--handoff`。兩個命題只有在同一原件確實支持且 context 相同時才共用 bundle；否則各自封裝適用原件，不複製或擴張原件能證明的範圍。

## 必錄欄位

| 區塊 | 欄位／內容 | 最低要求 |
|---|---|---|
| 身分 | `list_key`、`post_key`、`media_key`、`source_order` | key 以 notes CLI 產生／讀回值為準；任一層不能唯一對應就記 `UNKNOWN`，不得以顯示名稱、日期、張數、序號或單一 hash 代替 |
| Attempt | `attempt_id`、`intent_event_ref`、`outcome_event_ref`、`reconcile_event_refs`、`recovery_of`、`recovery_evidence_ref` | `attempt_id` 以 CLI 結果為準。現行 CLI 的 intent／outcome／reconcile 回傳 payload 不直接提供 event sequence；event ref 由唯讀核對 `events/%08d.json`（例如 `00000001.json`）、記錄 sequence 與該檔 SHA-256 讀回建立。同一 attempt 可多次 reconcile；每次都要新增一筆 `reconcile_event_refs`，保留全部 sequence／event SHA-256 與結果，不用最後一筆覆寫先前歷史。沒有 reconcile 記 `NOT_APPLICABLE`；任何一次無法唯一核對時，該次記 `UNKNOWN`，不得由資料夾、檔名或媒體 hash 反推 |
| Restart 批次 | `restart_id`、`generation`、`confirmation_ref`、`scope_digest`、`version_directory`、`owner_consent_ref`、`recovery_scan_id`、`prior_attempt_ref`、`activation_ref` | 只在精確 `restart preview`／Owner 明示同意／`restart confirm`／confirm 後完整 recovery scan 路徑使用。`confirmation_ref`、`generation`、`scope_digest`、`version_directory` 與新 attempt 必須對應同一個已確認批次；`owner_consent_ref` 指向當次可核對的 Owner 明示回覆，不能以 Prompt 本身、沉默、逾時或一般「繼續」代替。一般 attempt 或未使用欄位記 `NOT_APPLICABLE`；無法唯一讀回才記 `UNKNOWN`，不得由路徑或檔名猜值。此區塊是私有 statement 欄位，不是新的 CLI schema；傳給 CLI 的仍是既有 v2 `bundle_path` |
| 目的地 | `original_destination`、`destination_event_refs`、`observed_destination` | 原目的地以 intent 讀回值為準。目的地相關事件可能是 `created`（初始 root）、`destination`（追加 root）或 `intent`（attempt 目的地），各自以事件檔與讀回 hash 引用；`binding` 事件不含目的地。chooser 顯示或實際落點另記，不得反寫原目的地 |
| 觀察來源 | `observation_id`、`source_kind`、`tool`、`api_scope`、`app_window_binding`、`role_children_ref`、`raw_return_ref`、`scope`、`capture_rect`、`raw_rect`、`image_pixels`、`window_frame`、`window_points`、`scale_factor`、`popup_covered` | 記 AX／app-bound 截圖／桌面局部截圖／Computer Use 回傳／真人觀察，並分開 AX client／API scope、app／window 綁定與 role／children 來源；範圍、原始矩形、實際像素、點數與縮放分開，來源未涵蓋 popup 時不可推論不存在。同一 viewer 的 AX 相同不得推定工具列未變，截圖與 AX 也不能互相補值 |
| 時間 | `observed_at`、`input_at`、`clock_source`、`timezone`、`precision` | 每個時間都要有來源；不可取得工具時間或可信時鐘時寫 `UNKNOWN`，不以 mtime 冒充操作時間。capture label／sequence 只能支持相對先後；不能證明是否在輸入前時，`observation_order=UNKNOWN`，不得把檔名或 label 寫成已證實的 pre-click |
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
  observed_at: UNKNOWN
  clock_source: UNKNOWN
  timezone: UNKNOWN
  precision: UNKNOWN
  evidence_bundle_path: UNKNOWN
  evidence_bundle_sha256: UNKNOWN
  evidence_pack_command_ref: UNKNOWN

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

- 使用可避免覆寫的唯一檔名，例如 `<attempt_id>__<phase>__<sequence>__<source_kind>.<ext>`；不得因同名而覆寫先前證據。`evidence-pack` 會自行計算並核對原件 hash；不要手填或改寫 bundle 內部 hash。
- 保存 `evidence-pack` 的完整命令、exit code、stdout 與 stderr；用回傳的 `bundle_path`、outer SHA-256 及 context 作引用。hash 只證明 bundle／子 blob 的位元組與 context，不證明畫面真實、媒體身分、控制命中或下載完成。
- 檔名、相同 basename、隱藏副檔名、修改時間、hash、畫面出現順序與鄰近時間都不能單獨建立 attempt／chooser／檔案歸屬；每個 attempt 仍用獨立空白目的地，metadata 不足記 `UNKNOWN`，不新增全域改名器。

## 使用界限

- 主視窗截圖／AX 未涵蓋獨立 popup 或 chooser 時，控制可見性記 `UNKNOWN`；只有充分涵蓋的來源才可記 `NOT_OBSERVED`。不要猜全域座標或改用相簿流程。
- 同一「下載完畢」提示在截圖可見但 AX 不含時，只記截圖來源與當次範圍，不把 AX 記成看見；反之亦然。瞬態時間／涵蓋範圍不可得就寫 `UNKNOWN`，不為取得提示重新下載。
- input 原始成功／錯誤只證明工具回傳，不是 App 接受；chooser 只證明階段性回應，不是下載完成；終結訊號不等於檔案驗證；completion 也不等於外部副本或服務端原始位元相同。
- `intent` 已保存但沒有 outcome 時，第一筆真實結果用 `outcome`（可為 `UNKNOWN`）；只有已有 `outcome=UNKNOWN` 才用 `reconcile`。未收斂不得 verify、建立新 attempt、重下或派下一項。
- 本範本與填入內容都不是 GUI 授權、實機結果、E2E PASS 或獨立驗收。相關案例見 [證據判定案例](evidence-decision-cases.md)。
