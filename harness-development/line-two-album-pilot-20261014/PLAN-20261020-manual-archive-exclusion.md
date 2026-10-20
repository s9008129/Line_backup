# PLAN：MANUAL_DIAGNOSTIC 已下載排除機制（Option A）

- 狀態：`PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`
- Owner 已決定：採 **Option A**（明確排除清單，不冒充 VERIFIED）、同意用另外兩本相簿、允許修 Python 環境
- 本 Plan 不建立 grant、不改 ledger／state、不操作 LINE
- 實作必須在外部 Plan Reviewer 回 `APPROVE_PLAN` 後才開始

## 1. 問題與目標

A56（56 張）與 B53（53 張）已於 manual diagnostic 完成 Save All、下載與逐檔驗證，但正式 state revision 35 沒有它們的紀錄。`history_decision()` 只看 `runs`／`verified_albums`，因此正式 `runTwoAlbumPilot()` 會把 A56／B53 當成 eligible，存在重複下載風險。

目標：讓正式產品在**不偽造 AUTO 派送、不冒充 VERIFIED**的前提下，知道「這兩本已手動下載，必須跳過」，並讓新的雙相簿 grant 只能選到其他 eligible 相簿。

## 2. Acceptance Criteria

- **AC1**：存在一份 local registry，entries 帶 `provenance=MANUAL_DIAGNOSTIC`、fingerprint、manifest/verification 路徑與 SHA-256、檔數、bytes。
- **AC2**：loader 會重新 hash manifest 與 verification JSON；任一不符、缺檔、group 不符、schema 不符都 fail closed，不得靜默忽略。
- **AC3**：`history_decision()` 對 registry 精確命中的 fingerprint 回 `SKIP_MANUAL_DIAGNOSTIC`；若同時是正式 VERIFIED，仍以 `SKIP_VERIFIED` 優先。
- **AC4**：`admit_bounded()` 對 manual 命中的 target 回 `BOUNDED_TARGET_INELIGIBLE`，讓 `runTwoAlbumPilot()` 跳過並找下一張卡；不得開啟 detail、不得派送。
- **AC5**：`inspect` 的 `eligible_candidates` 不包含 manual 命中的 fingerprint。
- **AC6**：手動 registry **不**寫入 `verified_albums`、不改 state revision、不產生 run／intent／dispatch receipt。
- **AC7**：既有 verified 歷史、A56／B53 實體檔案、65 張排除相簿與 `2/2` 配額全部不變。

## 3. 設計

### 3.1 Registry 檔案（local、untracked）

位置：`<PROJECT_ROOT>/state/manual_archives.json`。這是 local runtime artifact，不放進 git；格式由本 Plan 與 committed example 固定。

```json
{
  "schema_version": 1,
  "kind": "manual_archive_registry",
  "app_identifier": "jp.naver.line.mac",
  "group_key": "line:jp.naver.line.mac:<sha256>",
  "entries": [
    {
      "fingerprint": {
        "start_date": "2024-05-27",
        "end_date": "2024-05-31",
        "expected_images": 56
      },
      "provenance": "MANUAL_DIAGNOSTIC",
      "recorded_at": "2026-10-20T21:57:16+08:00",
      "manifest_path": "harness-development/line-two-album-pilot-20261014/public/manual-diagnostic-20261020-a56/a56-sha256.txt",
      "manifest_sha256": "99c903e91415f6dff275668c5794390e581fa42764912eda9c63a038b45ce976",
      "verification_path": "harness-development/line-two-album-pilot-20261014/public/manual-diagnostic-20261020-a56/a56-verification.json",
      "verification_sha256": "a67e82078e08a3eed480844b3248ef6e345e6d55b388ec98954d10208af7a38a",
      "file_count": 56,
      "total_bytes": 18117492
    }
  ]
}
```

B53 以同樣格式加入（53 檔、17,095,114 bytes、manifest `e2da806c…bd36`、verification `49881e79…229c`）。registry 不含群組名稱、照片、人名或絕對路徑。

### 3.2 Loader

新增 `src/line_backup_acceptance/manual_archive.py`：

```python
def load_manual_archives(reader, *, app_identifier, group_key) -> frozenset[tuple[str, str, int]]
```

行為：

1. `state/manual_archives.json` 不存在 → 回空集合（不是錯誤）。
2. 以 `ProjectReader` 讀取，禁止 symlink 逃逸。
3. 嚴格檢查 keys／型別／`schema_version=1`／`kind=manual_archive_registry`／app／group。
4. `provenance` 必須等於 `MANUAL_DIAGNOSTIC`。
5. 重新 hash `manifest_path` 與 `verification_path`，必須等於宣告值。
6. verification JSON 的 `files.count`／`files.total_bytes` 必須等於 entry；manifest 行數必須等於 `file_count`。
7. fingerprint 日期格式與 `expected_images>0` 必須有效。
8. 任一失敗 → `AcceptanceError("MANUAL_ARCHIVE_REGISTRY_INVALID", detail, 4)`。

### 3.3 Decision precedence

`project_binding.history_decision(state, target, by_id, manual=frozenset())`：

```text
PROJECT_BUSY
→ SKIP_VERIFIED
→ SKIP_MANUAL_DIAGNOSTIC   # 新增，僅精確 fingerprint
→ AMBIGUOUS_FINGERPRINT
→ BLOCKED_UNRESOLVED
→ PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION
```

`facts` 增加 `manual_archive_match` 與 `destination_status="MANUAL_ARCHIVE_RECORDED"`。

### 3.4 Service 接線

- `Service.eligible(s, target, manual=None)` 保持 static，增加 optional `manual`。
- `Store` 增加 lazy `manual_fingerprints()`，以 config 的 app／group 載入並 cache；載入失敗即 fail closed。
- 呼叫點：`admit_bounded`、`prepare`、`Service.eligible` in `cli.py inspect`。
- `prepare` 的 skip 分支改為 `decision in {"SKIP_VERIFIED", "SKIP_MANUAL_DIAGNOSTIC"}`，只遞增 `next_index`，不建立 destination／run。
- 不在 state 寫任何 manual 欄位，避免 schema／CAS 變更。

### 3.5 為什麼不放进 `verified_albums`

`verified_albums` 的 `source_kind` 只允許 `filesystem_verification`／`user_attestation`，且 entry 必須有 `verified_run_id`。把 manual 放進去會混淆「已驗證」與「已手動下載」，也會影響 `verified_count`／未來的 duplicate 語意。獨立 registry 只影響 eligibility，方向永遠是「少下載」，安全。

## 4. 變更檔案（實作階段）

- `src/line_backup_acceptance/manual_archive.py`（新增 loader）
- `src/line_backup_acceptance/project_binding.py`（`history_decision` optional manual）
- `src/line_backup_batch/service.py`（`eligible`、`prepare` skip 分支）
- `src/line_backup_batch/store.py`（`manual_fingerprints()` lazy loader）
- `src/line_backup_batch/cli.py`（`inspect` 傳 manual set）
- `tests/test_manual_archive_registry.py`（新增）
- `tests/test_batch_authority.py`／`tests/test_project_binding.py`（回歸）
- `harness-development/line-two-album-pilot-20261014/config/manual_archives.example.json`（格式範例，placeholder）
- 不改 `state_v3.schema.json`、不改 grant／ledger、不改 JS CUA adapter

## 5. 測試計畫（無 GUI）

使用隔離 venv：`/private/tmp/lb-authorizer-20261020/.venv/bin/python`（Python 3.13.11 + jsonschema 4.26.0）。

新增測試案例：

1. 合法 registry → A56/B53 回 `SKIP_MANUAL_DIAGNOSTIC`。
2. manifest SHA 被改 → `MANUAL_ARCHIVE_REGISTRY_INVALID`。
3. verification count／bytes 不符 → fail closed。
4. 缺 manifest／verification 檔 → fail closed。
5. 非 `MANUAL_DIAGNOSTIC` provenance → fail closed。
6. 同時正式 VERIFIED → `SKIP_VERIFIED` 優先。
7. 未列出的 fingerprint → 維持 eligible。
8. `admit_bounded` 對 manual target 回 `BOUNDED_TARGET_INELIGIBLE`，且沒有 run／destination 副作用。

指令：

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_manual_archive_registry -v
PYTHONPATH=src .venv/bin/python -m unittest tests.test_batch_authority tests.test_project_binding -v
```

## 6. 新雙相簿 grant（不是本 Plan 實作）

實作與外部 Code Review 完成後，才建立新 bundle：

- `entry_method=runTwoAlbumPilot`
- `no_second_album=false`
- `album_quota=2`、`lifecycle_album_limit=2`
- `save_all_dispatch_limit=2`、`chooser_confirmation_limit=2`
- `implementation_head`＝實作後精確 commit
- `source_sha256`／entry binding／runtime binding 全部重算
- `implementation-review.json` 為真實 `APPROVE_IMPLEMENTATION`，`approved_operations` 完整
- target 必須是兩本**不同、未在 verified 或 manual registry**的 eligible 相簿
- 不重用 ONE56 grant、不改 `2/2`、不重送 A56／B53

## 7. 風險與回復

- **Registry 被誤加條目** → 只會造成「少下載」，且報告會顯示 skip；每次 review 都重新 hash evidence。
- **Registry 被刪除** → A56/B53 會回到 eligible；執行前必須先驗證 registry 存在且兩筆 entry PASS，否則不啟動正式 E2E。
- **Loader 效能** → 每次 CLI 只 hash 兩份小 manifest／JSON（<10 KB），可忽略。
- **回復**：移除 registry 與 loader 呼叫即可回到原行為；不改 state，所以沒有資料遷移。

## 8. 審查與下一步

1. External Plan Reviewer 對此 Plan 回 `APPROVE_PLAN` 或 `CHANGES_REQUIRED`。
2. 核准後由 Implementer 做上述最小 diff + 聚焦測試。
3. 固定 commit，送 External Code Review。
4. 建立新的雙相簿 grant，Owner 做當次 LINE 前景交接。
5. 新的獨立 `deepseek-v4.1-flash:1017` Session 對兩本其他相簿跑正式 E2E；A56／B53 只做唯讀核對。

## 9. 2026-10-20 唯讀對帳後的兩個必要修正

來源：`COVERAGE_AUDIT_20261020.md`（同目錄，唯讀、無 GUI、無 state 寫入）。

### 9.1 修正 A — registry 的 hash 必須「即時計算」，不得手寫

§3.1 範例中的 `verification_sha256: a67e8207…a38a` 是 **PR 分支上已遮蔽版** 的 hash；執行時 loader 讀到的是 Owner 本機 canonical 版 `9381d72a…2a38`（唯一差異是 `destination_workspace_relative` 的群組名）。若照抄範例，loader 必定 fail closed 並拋 `MANUAL_ARCHIVE_REGISTRY_INVALID` —— 表面上「有做」，實際上整個排除機制永遠無法通過。

因此實作階段新增硬性要求：

- registry **不得由人手抄寫 hash**；必須用同一個 loader 的 reader／hash 函式，對「即將被讀取的那個路徑」即時計算後寫入。
- 提供 `--record-manual-archive`（唯讀計算 + 寫 registry，不碰 state／grant／ledger）或等价的測試 helper；寫入後立即重新載入驗證。
- 新增測試：同內容但 `destination_workspace_relative` 被遮蔽 → 必須 `MANUAL_ARCHIVE_REGISTRY_INVALID`（證明 fail closed 有效）。

### 9.2 修正 B — 本群組 eligible 相簿數量為 0（`NO_ELIGIBLE_TARGET`）

唯讀對帳結果（`backups/<REDACTED_GROUP>/`，5 本全部已有歸屬）：

| 相簿 | 檔案數 | 歸屬 |
|---|---|---|
| 2024-05-06…05-10 | 182 | 正式 `VERIFIED` |
| 2024-05-13…05-17 | 57 | 正式 `VERIFIED` |
| 2024-05-20…05-24 | 53 | manual（B53） |
| 2024-05-27…05-31 | 56 | manual（A56） |
| 2024-06-02…06-07 | 0 | Owner 排除（空目錄，從未下載） |

182 + 57 = 239（歷史 VERIFIED 總數）、56 + 53 = 109（manual 總數），完全吻合，沒有第 6 本。

**結論**：§6 要求的「兩本不同、未備份的 eligible 相簿」在**目前群組內不存在**。這不是程式 bug，也不是 grant 缺失。

因此新增前置條件（在建立 grant 之前）：

1. **AC8**：`runTwoAlbumPilot()` 在 eligible < 2 時必須回 `NO_ELIGIBLE_TARGET` 並零派送、零副作用（不得為了湊數重開已備份相簿）。
2. 若要繼續 TWO_ALBUM_AUTO，Owner 需擇一：
   - **(i)** 指定**另一個 LINE 群組／對話**的相簿作為 A/B（需該群組的真實列表證據）；
   - **(ii)** 確認本群組在目前可見的 5 本之外還有更早／更晚的相簿（需真機列表 + 實際捲動證據，不得用推測補位）。
3. 在 (i)／(ii) 取得之前，**不得**建立 `album_quota=2` 的 grant，也不得用 A56／B53／65 張相簿湊數。

### 9.3 不受影響的部分

§2 的 AC1–AC7、§3.2–3.5 的 loader／precedence／service 接線設計、§4 變更檔案清單（除 9.1 新增的 `--record-manual-archive` 與其測試）、§5 測試計畫 1–8 全部維持。9.1／9.2 是增補，不是重寫。

## 10. 2026-10-20 修正 — §9.2 的前提不成立（eligible 相簿存在）

Owner 授權當次 LINE 前景後，對相簿列表做了一次可逆捲動（click 0、Save All 0、下載 0、state 寫入 0）。實測結果：`2024/05/06` 之後還有更多相簿，且以下 5 本**不在任何既有備份**中：

| 排名（新→舊） | 日期 | 張數 |
|---|---|---|
| 1 | `2024/04/22～04/26` | 45 |
| 2 | `2024/4/21`（單日） | 78 |
| 3 | `2024/04/08～04/12` | 77 |
| 4 | `2024/04/01～04/03` | 42 |
| 5 | `2024/03/25～03/29` | 87 |

因此：

- **§9.2 的「eligible = 0」與「Owner 需換群組」作廢**；這是「已下載 5 本 = 總共 5 本」的推論錯誤，證據見 `COVERAGE_AUDIT_20261020.md` 的 CORRECTION 區塊。
- **§9.2 的 AC8 仍然保留**：`runTwoAlbumPilot()` 在 eligible < 2 時必須回 `NO_ELIGIBLE_TARGET` 且零副作用。它現在是安全網，不是現況描述。
- 建議的正式 E2E 目標（由產品依「新→舊」自然選取，不需硬編碼）：
  - **A = `2024/04/22～04/26`，45 張**
  - **B = `2024/4/21`，78 張**
- 注意 `2024/4/21` 是**單日相簿**（無前導零、無區間），fingerprint/OCR 需支援此格式；`04/08` 與 `03/25` 兩張卡帶有綠色未讀小點，該標記不得進入 fingerprint。
- 列表在 `2024/03/25～03/29` 之下尚未到底，總數仍為 UNKNOWN；正式執行只需前兩本，不要求完整覆蓋。
