# 記事本 evidence-pack statement 範本

本範本是 Agent 撰寫 `notes evidence-pack --statement FILE` 的人工紀錄內容，不是可直接傳給事件 evidence 參數的自由文字檔，也不是 CLI schema、parser 或語意驗證器。Agent 把這份 statement 與當次截圖／AX／input receipt／command stdout／stderr 等原件用 `evidence-pack` 封裝；成功後只把回傳的 `bundle_path` 傳給 `--evidence`、`--binding-evidence`、`--observation` 或其他證據參數。CLI 核對 v2 bundle 的結構、context 與保存子 blob 的 bytes／SHA-256，但不解析欄位語意，也不知道欄位是否真實、畫面是否屬於該 attempt，或證據是否足以判完成。

每次下載控制、chooser 確認、outcome、reconcile、更正與恢復前，先建立這份私有 statement，再用 `evidence-pack` 產生 bundle。context 只填該命令唯一主體的已知 ID；適用 ID 不可留 `UNKNOWN` 或誤填另一主體，未分配／不適用的欄位才由 `evidence-pack` 保持 `UNKNOWN`。`intent` 沒有一般 evidence 參數，其預檢與讀回證據留在私有任務區。無法取得的欄位寫 `UNKNOWN` 並說明原因；不要用空白、猜測、檔名或另一個畫面補值。原始證據留在專案任務所需的私有區域，不外傳。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes evidence-pack \
  --statement STATEMENT_FILE \
  --asset screenshot PRIVATE_SCREENSHOT \
  --asset ax PRIVATE_AX_CAPTURE \
  --output-dir .local/line-backup/tasks/TASK_ID/evidence/NEW_UUID \
  --list-key LIST_KEY [--post-key POST_KEY] [--media-key MEDIA_KEY] \
  [--attempt-id ATTEMPT_ID] [--scan-id SCAN_ID]
```

`--asset` 可重複；role 限 `screenshot`、`ax`、`input_receipt`、`command_stdout`、`command_stderr`、`observation`。statement 與畫面／AX 不可空；`command_stdout`／`command_stderr` 可為零 bytes。`--output-dir` 必須在 `.local/line-backup/tasks/` 下、尚不存在且不可用既有目錄代替；不要手動命名或覆寫 hash。Owner 不需要提供 JSON、UUID、key 或 hash。

## 必錄欄位

| 區塊 | 欄位／內容 | 最低要求 |
|---|---|---|
| 身分 | `list_key`、`post_key`、`media_key`、`source_order` | key 以 notes CLI 產生／讀回值為準；任一層不能唯一對應就記 `UNKNOWN`，不得以顯示名稱、日期、張數、序號或單一 hash 代替 |
| Attempt | `attempt_id`、`intent_event_ref`、`outcome_event_ref`、`reconcile_event_refs`、`recovery_of`、`recovery_evidence_ref` | `attempt_id` 以 CLI 結果為準。現行 CLI 的 intent／outcome／reconcile 回傳 payload 不直接提供 event sequence；event ref 由唯讀核對 `events/%08d.json`（例如 `00000001.json`）、記錄 sequence 與該檔 SHA-256 讀回建立。同一 attempt 可多次 reconcile；每次都要新增一筆 `reconcile_event_refs`，保留全部 sequence／event SHA-256 與結果，不用最後一筆覆寫先前歷史。沒有 reconcile 記 `NOT_APPLICABLE`；任何一次無法唯一核對時，該次記 `UNKNOWN`，不得由資料夾、檔名或媒體 hash 反推 |
| 目的地 | `original_destination`、`destination_event_refs`、`observed_destination` | 原目的地以 intent 讀回值為準。目的地相關事件可能是 `created`（初始 root）、`destination`（追加 root）或 `intent`（attempt 目的地），各自以事件檔與讀回 hash 引用；`binding` 事件不含目的地。chooser 顯示或實際落點另記，不得反寫原目的地 |
| 觀察來源 | `observation_id`、`source_kind`、`tool`、`scope`、`capture_rect`、`raw_rect`、`image_pixels`、`window_frame`、`window_points`、`scale_factor`、`popup_covered` | 記 AX／app-bound 截圖／桌面局部截圖／Computer Use 回傳／真人觀察；範圍、原始矩形、實際像素、點數與縮放分開，來源未涵蓋 popup 時不可推論不存在 |
| 時間 | `observed_at`、`input_at`、`clock_source`、`timezone`、`precision` | 每個時間都要有來源；不可取得工具時間或可信時鐘時寫 `UNKNOWN`，不以 mtime 冒充操作時間 |
| 定位 | `page_role`、`focus_state`、`control_owner`、`control_visibility`、`enabled_state`、`raw_coord_space`、`mapped_screen_point`、`mapping_id`、`mapping_valid_at` | 控制可見性只在充分範圍成立時記 `VISIBLE`／`NOT_OBSERVED`；座標映射失效或缺失時記 `UNKNOWN`，不得輸入 |
| 輸入 | `input_phase`、`action`、`target_ref`、`input_tool`、`input_api`、`raw_tool_return`、`error_raw`、`download_control_call_count`、`chooser_confirm_call_count` | `input_phase` 至少區分 `DOWNLOAD_CONTROL`、`CHOOSER_PATH`、`CHOOSER_CONFIRM`；記工具／API 及原始成功／錯誤／逾時，並分別累計兩個至多一次的呼叫。失敗、逾時與未知也計入 |
| Chooser | `appeared`、`attribution_basis`、`chooser_window_process`、`source_viewer_ref`、`attempt_link`、`path_field_readback`、`destination_check`、`confirm_raw_return` | 只有來源 viewer／attempt、視窗／process 與目的地能唯一對應才可確認；延遲出現仍不是下載完成 |
| 結果 | `terminal_signal`、`terminal_source_ref`、`candidate_file_refs`、`stability_ref`、`file_attribution_basis` | 終結訊號與穩定檔集都要可歸屬原 attempt；空目錄、timeout、畫面未變或單一提示不足 |
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

observation:
  source_kind: UNKNOWN
  tool: UNKNOWN
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
  raw_coord_space: UNKNOWN
  mapped_screen_point: UNKNOWN
  mapping_id: UNKNOWN
  mapping_valid_at: UNKNOWN

input:
  input_phase: UNKNOWN
  action: UNKNOWN
  target_ref: UNKNOWN
  input_tool: UNKNOWN
  input_api: UNKNOWN
  input_at: UNKNOWN
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
  destination_check: UNKNOWN
  confirm_raw_return: UNKNOWN

result:
  terminal_signal: UNKNOWN
  terminal_source_ref: UNKNOWN
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

## 引用檔名與 hash

- 使用可避免覆寫的唯一檔名，例如 `<attempt_id>__<phase>__<sequence>__<source_kind>.<ext>`；不得因同名而覆寫先前證據。`evidence-pack` 會自行計算並核對原件 hash；不要手填或改寫 bundle 內部 hash。
- 保存 `evidence-pack` 的完整命令、exit code、stdout 與 stderr；用回傳的 `bundle_path`、outer SHA-256 及 context 作引用。hash 只證明 bundle／子 blob 的位元組與 context，不證明畫面真實、媒體身分、控制命中或下載完成。
- 檔名、修改時間、hash、畫面出現順序與鄰近時間都不能單獨建立 attempt／chooser／檔案歸屬；關聯不足就寫 `UNKNOWN`。

## 使用界限

- 主視窗截圖／AX 未涵蓋獨立 popup 或 chooser 時，控制可見性記 `UNKNOWN`；只有充分涵蓋的來源才可記 `NOT_OBSERVED`。不要猜全域座標或改用相簿流程。
- input 原始成功／錯誤只證明工具回傳，不是 App 接受；chooser 只證明階段性回應，不是下載完成；終結訊號不等於檔案驗證；completion 也不等於外部副本或服務端原始位元相同。
- `intent` 已保存但沒有 outcome 時，第一筆真實結果用 `outcome`（可為 `UNKNOWN`）；只有已有 `outcome=UNKNOWN` 才用 `reconcile`。未收斂不得 verify、建立新 attempt、重下或派下一項。
- 本範本與填入內容都不是 GUI 授權、實機結果、E2E PASS 或獨立驗收。相關案例見 [證據判定案例](evidence-decision-cases.md)。
