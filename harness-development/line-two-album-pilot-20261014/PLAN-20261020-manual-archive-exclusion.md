# PLAN v4.1：MANUAL_DIAGNOSTIC 已下載排除機制（Option A）

- 狀態：`PROPOSED_PENDING_EXTERNAL_FAST_REREVIEW`
- 版本：v4.1（2026-10-20）；v4 外部審查 [`pullrequestreview-5586830157`](https://github.com/s9008129/Line_backup/pull/21#pullrequestreview-5586830157) 為 `CHANGES_REQUIRED`，本版只處理 P0-A～P0-F、AC8 與 Coverage Audit 狀態，不展開新架構。
- Owner 已決定：採 **Option A**（明確排除清單，不冒充 VERIFIED）；本次唯一合法雙相簿目標為 **A45／B78**；單日相簿採 **方案甲**。
- 本輪只修文件：不改產品程式、不操作 LINE、不建立 grant、不改 ledger／state、不新增測試框架。
- 實作必須在外部 Plan Reviewer 回 `APPROVE_PLAN` 後才開始。

## 1. 問題與目標

A56（56 張）與 B53（53 張）已於 manual diagnostic 完成 Save All、下載與逐檔驗證，但正式 state revision 35 沒有它們的紀錄。`history_decision()` 只看 `runs`／`verified_albums`，因此正式 `runTwoAlbumPilot()` 會把 A56／B53 當成 eligible，存在重複下載風險。

目標：讓正式產品在**不偽造 AUTO 派送、不冒充 VERIFIED**的前提下，知道「這兩本已手動下載，必須跳過」，並讓新的雙相簿 grant 只能選到其他 eligible 相簿。

## 2. Acceptance Criteria

- **AC1**：存在一份 local registry，entries 帶 `provenance=MANUAL_DIAGNOSTIC`、fingerprint、manifest/verification 路徑與 SHA-256、檔數、bytes。
- **AC2**：loader 會重新 hash 實際讀取的 manifest 與 verification JSON；任一不符、缺檔、group 不符、schema 不符都 fail closed，不得靜默忽略。**本次 Owner 宣告的 A56／B53 scope**，registry 遺失或損壞必須在 live `gui_initialize`／`begin` 前停止，並在 admission 再檢查一次，不得 fallback 成 eligible；沒有 manual archive 的一般新群組不必被全域封鎖。
- **AC3**：`history_decision()` 的優先序必須保留未結交易與 UNKNOWN：`PROJECT_BUSY → SKIP_VERIFIED → AMBIGUOUS_FINGERPRINT → BLOCKED_UNRESOLVED → SKIP_MANUAL_DIAGNOSTIC → ELIGIBLE`。manual skip 不得掩蓋同 fingerprint 的 ambiguous／unresolved 狀態。
- **AC4**：`admit_bounded()` 對 manual 命中的 target 回 `BOUNDED_TARGET_INELIGIBLE`，讓 `runTwoAlbumPilot()` 跳過並找下一張卡；不得開啟 detail、不得派送。
- **AC5**：`inspect` 的 `eligible_candidates` 不包含 manual 命中的 fingerprint，且只接受 Owner 指定的 A45／B78。
- **AC6**：手動 registry **不**寫入 `verified_albums`、不改 state revision、不產生 run／intent／dispatch receipt。
- **AC7**：既有 verified 歷史、A56／B53 實體檔案、65 張排除相簿與 `2/2` 配額全部不變。
- **AC8（stage-aware）**：若 **A 尚未派送**即找不到合格目標，回 `NO_ELIGIBLE_TARGET`，不得派送任何新 Save All，也不得用已備份相簿湊數；若 **A 已合法 VERIFIED** 而 B 找不到，回 `PARTIAL_A_VERIFIED_B_NOT_RUN`，保留 A 的 VERIFIED 狀態，B 派送數為 0，停止即可，不得回滾 A，也不得承諾這種情況完全沒有 state 寫入。
- **AC9（方案甲）**：單日 `2024/4/21` 在 Python 與既有 JS 辨識鏈都必須正規化為 `2024-04-21..2024-04-21`；畫面 OCR 標題仍是 `2024/4/21`；保留兩位數區間、跨年 rollover、`(1/N)` viewer 拒絕與非法日期 `2024/2/30 → None`。不得改 Save All／dispatch／at-most-once 語意。
- **AC10**：新增的 `src/line_backup_acceptance/manual_archive.py` 必須列入 `src/line_backup_batch/store.py:SOURCE_PATHS`，並在實作後重算 `source_sha256`／runtime binding；未進入正式 Source Closure 不得跑正式 E2E。
- **AC11**：正式雙相簿入口以 Owner-bound 小型白名單限制 A=`2024-04-22..2024-04-26,45`、B=`2024-04-21..2024-04-21,78`；`2024-06-02..2024-06-07,65` 永久排除。`inspect` 與 `admit_bounded` 都必須拒絕白名單外目標；65 張相簿不得標成 `MANUAL_DIAGNOSTIC`。

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
      "manifest_path": "<owner-local-canonical-path>/a56-sha256.txt",
      "manifest_sha256": "<computed-from-exact-local-file>",
      "verification_path": "<owner-local-canonical-path>/a56-verification.json",
      "verification_sha256": "<computed-from-exact-local-file>",
      "file_count": 56,
      "total_bytes": 18117492
    }
  ]
}
```

B53 以同樣格式加入（53 檔、17,095,114 bytes）。registry 不含群組名稱、照片、人名或絕對路徑；registry 本身是 local、untracked runtime artifact。

**v4.1 hash 規則：** example 不再放入任何可被人手抄用的 verification hash。`--record-manual-archive` 必須要求 A56 的 56 個與 B53 的 53 個實際本地檔案都存在，逐檔核對 index／count／bytes／content SHA 與各自 manifest，並對「即將被讀取的實際 canonical 路徑」即時計算 manifest／verification SHA；不得把 PR 上已遮蔽版 JSON 的 hash 當成 canonical。讀取時用同一路徑重算，任何不一致即 fail closed。

### 3.2 Loader

新增 `src/line_backup_acceptance/manual_archive.py`：

```python
def load_manual_archives(reader, *, app_identifier, group_key, required=False) -> frozenset[tuple[str, str, int]]
```

行為：

1. `state/manual_archives.json` 不存在 → generic loader 可回空集合；但本次 Owner 宣告的 A56／B53 scope 以 `required=True` 呼叫，必須在 live `gui_initialize`／`begin` 前回 `MANUAL_ARCHIVE_REGISTRY_REQUIRED`，不得靜默視為 eligible。一般新群組可在沒有 manual archive 時使用空集合。
2. 以 `ProjectReader` 讀取，禁止 symlink 逃逸。
3. 嚴格檢查 keys／型別／`schema_version=1`／`kind=manual_archive_registry`／app／group。
4. `provenance` 必須等於 `MANUAL_DIAGNOSTIC`。
5. 重新 hash `manifest_path` 與 `verification_path`，必須等於宣告值。
6. verification JSON 的 `files.count`／`files.total_bytes` 必須等於 entry；manifest 行數必須等於 `file_count`。
7. fingerprint 日期格式與 `expected_images>0` 必須有效；A56／B53 必須與 Owner 宣告的 canonical group／fingerprint 一致。
8. `--record-manual-archive` 寫入前與寫入後都要重新載入；record 成功不得產生 state／grant／ledger 變更。
9. 任一失敗 → `AcceptanceError("MANUAL_ARCHIVE_REGISTRY_INVALID", detail, 4)`；缺 registry 的本次 scope 使用 `MANUAL_ARCHIVE_REGISTRY_REQUIRED`。

### 3.3 Decision precedence

`project_binding.history_decision(state, target, by_id, manual=frozenset())`：

```text
PROJECT_BUSY
→ SKIP_VERIFIED
→ AMBIGUOUS_FINGERPRINT
→ BLOCKED_UNRESOLVED
→ SKIP_MANUAL_DIAGNOSTIC   # 新增，僅精確 fingerprint，且不得高於 ambiguous／UNKNOWN
→ PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION
```

`facts` 增加 `manual_archive_match` 與 `destination_status="MANUAL_ARCHIVE_RECORDED"`。

### 3.4 Service 接線

- `Service.eligible(s, target, manual=None)` 保持 static，增加 optional `manual`。
- `Store` 增加 lazy `manual_fingerprints(required=False)`，以 config 的 app／group 載入並 cache；本次 Owner 宣告 scope 的入口傳 `required=True`，載入失敗即 fail closed。
- 呼叫點：`admit_bounded`、`prepare`、`Service.eligible` in `cli.py inspect`；本次 scope 在 live `gui_initialize`／`begin` 前先驗證一次，admission 再驗證一次。
- `prepare` 的 skip 分支改為 `decision in {"SKIP_VERIFIED", "SKIP_MANUAL_DIAGNOSTIC"}`，只遞增 `next_index`，不建立 destination／run。
- 不在 state 寫任何 manual 欄位，避免 schema／CAS 變更。

### 3.5 為什麼不放进 `verified_albums`

`verified_albums` 的 `source_kind` 只允許 `filesystem_verification`／`user_attestation`，且 entry 必須有 `verified_run_id`。把 manual 放進去會混淆「已驗證」與「已手動下載」，也會影響 `verified_count`／未來的 duplicate 語意。獨立 registry 只影響 eligibility，方向永遠是「少下載」，安全。

### 3.6 Owner-bound 雙目標與 65 張排除

這是本次 run 的小型明確限制，不是通用 registry 框架：

- 允許的正式目標只有 A=`2024-04-22..2024-04-26,45` 與 B=`2024-04-21..2024-04-21,78`；不依賴畫面座標硬編碼。
- `2024-06-02..2024-06-07,65` 永久排除，既不進 manual registry，也不得被當成 manual skip；它沒有被下載，只是 Owner 指定不可選。
- `inspect` 與 `admit_bounded` 都必須驗證精確 fingerprint；任何白名單外或 65 張目標都回 `BOUNDED_TARGET_INELIGIBLE`，不得進 detail／menu／Save All。
- 產品仍按「新→舊」自然掃描；A45 必須先完成，之後才可找 B78。不得為湊數重開 A56／B53 或歷史 239 張 VERIFIED。

## 4. 變更檔案（實作階段）

- `src/line_backup_acceptance/manual_archive.py`（新增 loader）
- `src/line_backup_acceptance/project_binding.py`（`history_decision` optional manual）
- `src/line_backup_batch/service.py`（`eligible`、`prepare` skip 分支）
- `src/line_backup_batch/store.py`（`manual_fingerprints()` lazy loader；把 `manual_archive.py` 加入 `SOURCE_PATHS`）
- `src/line_backup_batch/cli.py`（`inspect` 傳 manual set、`--record-manual-archive`、本次 scope 的 fail-closed 入口）
- `src/line_backup_batch/observations.py`（單日 `ocr_date_identity` 與詳情標題期望）
- `harness-development/line-two-album-pilot-20261014/mac/analyzer.mjs`（`completeDateTitle()` 接受單日格式）
- `harness-development/line-two-album-pilot-20261014/mac/classifier.mjs`（既有標題比對接受單日與區間）
- `tests/test_manual_archive_registry.py`（新增）
- `tests/test_batch_authority.py`／`tests/test_project_binding.py`／`tests/test_batch_observations.py`（回歸）
- `tests/test_detail_grid_name_target.mjs`／`tests/test_cua_adapter.mjs`（既有 JS 測試，聚焦單日／區間標題）
- `harness-development/line-two-album-pilot-20261014/config/manual_archives.example.json`（格式範例，placeholder）
- 重算並更新既有 source／runtime manifest：`manual_archive.py` 必須加入 `SOURCE_PATHS`；`observations.py` 已在 Source Closure 內；analyzer／classifier 由既有 entry binding 覆蓋，變更後必須重算對應 entry／runtime binding。這是實作階段的必要交付，不是本輪文件修訂。
- 不改 `state_v3.schema.json`、不改 grant／ledger、不改 Save All／dispatch／at-most-once 語意、不改 JS CUA adapter 的派送路徑

## 5. 測試計畫（無 GUI）

使用隔離 venv：`/private/tmp/lb-authorizer-20261020/.venv/bin/python`（Python 3.13.11 + jsonschema 4.26.0）。

新增測試案例：

1. 合法 registry → A56/B53 回 `SKIP_MANUAL_DIAGNOSTIC`。
2. manifest SHA 被改 → `MANUAL_ARCHIVE_REGISTRY_INVALID`。
3. verification count／bytes 不符 → fail closed。
4. 缺 manifest／verification 檔 → fail closed。
5. 非 `MANUAL_DIAGNOSTIC` provenance → fail closed。
6. 同時正式 VERIFIED → `SKIP_VERIFIED` 優先。
7. 未列出的 fingerprint → 維持 eligible（但仍受 A45／B78 白名單限制）。
8. `admit_bounded` 對 manual target 回 `BOUNDED_TARGET_INELIGIBLE`，且沒有 run／destination 副作用。
9. 本次 A56／B53 scope 缺 registry／缺 backing file／hash 不符 → 在 live `gui_initialize`／`begin` 前 fail closed；admission 重讀仍要 fail closed。
10. 65 張指紋與非 A45／B78 指紋 → `inspect` 及 `admit_bounded` 都拒絕；不得標成 manual。
11. 同 fingerprint 同時有 ambiguous／unresolved 與 manual entry → ambiguous／`BLOCKED_UNRESOLVED` 優先，manual skip 不得掩蓋。
12. 單日 `2024/4/21` → start=end=`2024-04-21`；`2024/4/21～4/21`、`2024/04/21～04/21` 與既有 `YYYY/MM/DD～MM/DD` 行為保持；非法日期仍拒絕。
13. 既有 analyzer／classifier 的 interval、cross-year、viewer `(1/N)` 拒絕案例保持；以已捕捉的真實畫面文字作聚焦 fixture，不建立新框架。

指令：

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_manual_archive_registry -v
PYTHONPATH=src .venv/bin/python -m unittest tests.test_batch_authority tests.test_project_binding tests.test_batch_observations -v
node --test tests/test_detail_grid_name_target.mjs tests/test_cua_adapter.mjs
```

## 6. 新雙相簿 grant（不是本 Plan 實作）

實作與外部 Code Review 完成後，才建立新 bundle：

- `entry_method=runTwoAlbumPilot`
- `no_second_album=false`
- **Grant tuple 必須精確為 `(2,1,2,2,23)`**：`album_quota=2`、`lifecycle_album_limit=1`、`save_all_dispatch_limit=2`、`chooser_confirmation_limit=2`、`reversible_gui_invocation_limit=23`。
- `lifecycle_album_limit=1` 表示 A、B 各自獨立的單相簿 lifecycle，`two_album_entry.mjs` 對 A 與 B 分別 `begin(limit=1)`；不為此改產品參數。
- `implementation_head`＝實作後精確 commit
- `source_sha256`／entry binding／runtime binding 全部重算
- `implementation-review.json` 為真實 `APPROVE_IMPLEMENTATION`，`approved_operations` 完整
- target 必須精確是 A45／B78 兩本不同、未在 verified 或 manual registry 的 eligible 相簿；65 張永久排除
- 不重用 ONE56 grant、不改 `2/2`、不重送 A56／B53

## 7. 風險與回復

- **Registry 被誤加條目** → 只會造成「少下載」，且報告會顯示 skip；每次 review 都重新 hash evidence。
- **Registry 被刪除** → 本次 A56／B53 scope 必須 fail closed；執行前必須先驗證 registry 存在且兩筆 entry PASS，否則不啟動正式 E2E。一般新群組的空白 manual scope 不受此全域限制。
- **Loader 效能** → 每次 CLI 只 hash 兩份小 manifest／JSON（<10 KB），可忽略。
- **回復**：移除 registry 與 loader 呼叫即可回到原行為；不改 state，所以沒有資料遷移。

## 8. 審查與下一步

1. External Plan Reviewer 對 v4.1 精確 HEAD 做一次快速複審。
2. 核准後直接由 Implementer 在 **PR #10 pilot 的 `516932d` 基礎**做最小 diff + 聚焦 Python／Node 測試；不在此分支直接拿舊 baseline 當產品來源。
3. 實作後把 `manual_archive.py` 納入 `SOURCE_PATHS`，重算 source／runtime binding，固定新 commit，送 External Code Review。
4. 建立 `(2,1,2,2,23)` 的雙相簿 grant，Owner 做當次 LINE 前景交接。
5. 新的獨立 `deepseek-v4.1-flash:1017` Session 只對 A45 → 真實捲動 → B78 跑正式 E2E；A56／B53 只做唯讀核對，65 張永久不選。

## 9. 2026-10-20 唯讀對帳後的兩個必要修正

來源：`COVERAGE_AUDIT_20261020.md`（同目錄，唯讀、無 GUI、無 state 寫入）。

### 9.1 修正 A — registry 的 hash 必須「即時計算」，不得手寫（歷史紀錄；v4.1 已修正 example）

審查當時 §3.1 範例曾引用 `verification_sha256: a67e8207…a38a`，那是 **PR 分支上已遮蔽版** 的 hash；執行時 loader 讀到的是 Owner 本機 canonical 版 `9381d72a…2a38`（唯一差異是 `destination_workspace_relative` 的群組名）。若照抄該值，loader 必定 fail closed 並拋 `MANUAL_ARCHIVE_REGISTRY_INVALID` —— 表面上「有做」，實際上整個排除機制永遠無法通過。v4.1 已改用 placeholder，並要求由實際讀取路徑即時計算。

因此實作階段新增硬性要求：

- registry **不得由人手抄寫 hash**；必須用同一個 loader 的 reader／hash 函式，對「即將被讀取的那個路徑」即時計算後寫入。
- 提供 `--record-manual-archive`（唯讀計算 + 寫 registry，不碰 state／grant／ledger）或等价的測試 helper；寫入後立即重新載入驗證。
- 新增測試：同內容但 `destination_workspace_relative` 被遮蔽 → 必須 `MANUAL_ARCHIVE_REGISTRY_INVALID`（證明 fail closed 有效）。

### 9.2 修正 B — 本群組 eligible 相簿數量為 0（歷史錯誤推論；已被 §10 推翻）

> **歷史保留：** 本節的「eligible=0」與「Owner 需換群組」是根據 `backups/` 目錄作出的錯誤推論。其後的真實 LINE 捲動證據見 §10 與 `COVERAGE_AUDIT_20261020.md` 的 CORRECTION；不要用本節當現況。

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

1. **AC8（本段原稿；已由 §2 的 stage-aware 版本取代）**：`runTwoAlbumPilot()` 在 eligible < 2 時必須回 `NO_ELIGIBLE_TARGET` 且不得為了湊數重開已備份相簿。A 已 VERIFIED 而 B 不足時另見 `PARTIAL_A_VERIFIED_B_NOT_RUN`。
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
- **§9.2 的 AC8 仍然保留**：`runTwoAlbumPilot()` 在 **A 尚未派送**且找不到合格目標時必須回 `NO_ELIGIBLE_TARGET`，不得派送新 Save All；若 A 已 VERIFIED 而 B 找不到，則回 `PARTIAL_A_VERIFIED_B_NOT_RUN`，保留 A 的狀態且 B 派送為 0。它現在是安全網，不是現況描述。
- 建議的正式 E2E 目標（由產品依「新→舊」自然選取，不需硬編碼）：
  - **A = `2024/04/22～04/26`，45 張**
  - **B = `2024/4/21`，78 張**
- 注意 `2024/4/21` 是**單日相簿**（無前導零、無區間），fingerprint/OCR 需支援此格式；`04/08` 與 `03/25` 兩張卡帶有綠色未讀小點，該標記不得進入 fingerprint。
- 列表在 `2024/03/25～03/29` 之下尚未到底，總數仍為 UNKNOWN；正式執行只需前兩本，不要求完整覆蓋。

## 11. 2026-10-20 追加 — 單日相簿解析缺口（方案甲已由外部審查採納）

以 PR #10 pilot HEAD `516932d` 實跑 `ocr_date_identity()`，畫面文字 `2024/4/21` 回傳 `None`（regex 於 `observations.py:42` 強制兩位數 + 區間；`:494` 的標題期望固定為 `YYYY/MM/DD～MM/DD`）。

因為產品「新→舊」掃描的第二順位就是 `2024/4/21`，**B 目前不可達**；這與 grant／CUA／Save All 無關，屬純解析層缺口，可在零 GUI、零 state 寫入下重現。

本 Plan 追加 **AC9（方案甲）**：

- `ocr_date_identity('2024/4/21')` → `{'start_date':'2024-04-21','end_date':'2024-04-21'}`
- 不得把 `2024/4/21` 誤解析為其他年份／月日；非法日期（`2024/2/30`）仍回 `None`
- `:494` 的標題期望需同時接受「單日」與「區間」兩種畫面格式
- 此修正**不得**改動 `dispatch`／`intent`／at-most-once 或 any save-all gate；只影響 identity 解析
- (乙) 不採用；不得改用 `2024/04/08～04/12` 當 B。

變更範圍（方案甲）：`src/line_backup_batch/observations.py`（僅 `ocr_date_identity` 與標題期望）、`mac/analyzer.mjs`（`completeDateTitle()`）、`mac/classifier.mjs`（既有標題比對）＋既有 Python／Node 測試；不新增檔案、不動 schema、不動 Save All／dispatch／at-most-once。

## 12. v4.1 審查對照（P0-A～P0-F）

| 項目 | v4.1 處理 |
|---|---|
| P0-A | §6 改為精確 grant tuple `(2,1,2,2,23)`；A／B 各自 `begin(limit=1)`。 |
| P0-B | §4 將 `manual_archive.py` 納入 `store.py:SOURCE_PATHS`，並要求重算 source／runtime binding。 |
| P0-C | §3.6 以 Owner-bound 白名單限制 A45／B78，65 張永久排除；`inspect` 與 `admit_bounded` 都檢查。 |
| P0-D | §3.1／§3.2／§3.4 要求本次 scope 的 registry、backing files 與 SHA fail closed，於 live 入口及 admission 各檢查一次；hash 取實際讀取路徑。 |
| P0-E | §3.3 將 `AMBIGUOUS_FINGERPRINT`／`BLOCKED_UNRESOLVED` 放在 manual skip 之前。 |
| P0-F | §4／§11 將方案甲擴及 Python 與既有 JS analyzer／classifier，不改派送語意。 |

本表只記錄 v4.1 文件修訂；不代表 Plan 已核准、實作已完成或 Save All 已授權。
