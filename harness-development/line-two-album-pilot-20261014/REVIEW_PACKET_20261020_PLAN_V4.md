# REVIEW PACKET 2026-10-20 — Plan v4 送 External Plan Review

```text
TASK_ID        = LINE_TWO_ALBUM_PILOT/1
ROLE_TARGET    = EXTERNAL_PLAN_REVIEWER (Owner 指定的雲端 ChatGPT)
PLAN_REVISION  = v4
PACKET_BASE    = ca4462ff25cd5f043336f7c1d2c4856a2a5d29c9
PRODUCT_SOURCE = PR #10 pilot HEAD 516932dfcee94b662082b909b7980fc2483ab9c0
DELIVERY       = Owner 轉貼本文件或對應 PR 留言給雲端 Reviewer
DECISION_NEEDED= APPROVE_PLAN | CHANGES_REQUIRED
```

本文件是**唯讀交接物**。它不建立 grant、不改 ledger／state、不授權任何 GUI 或 Save All。

## 1. 受審文件

| 文件 | 內容 |
|---|---|
| `PLAN-20261020-manual-archive-exclusion.md` | Plan v4：§1–§8 原始設計、§9 hash 修正與 AC8、§10 eligible 相簿更正、§11 單日相簿缺口 |
| `COVERAGE_AUDIT_20261020.md` | 唯讀對帳：state／backups／hash／eligible 清單／單日解析實測 |
| `E2E測試報告.md` | §14／§14.1：覆蓋率對帳與更正紀錄 |

## 2. Owner 決策（2026-10-20）

1. 採 **Option A**：`MANUAL_DIAGNOSTIC` 明確排除清單；**不冒充 VERIFIED、不偽造 AUTO 派送紀錄**。
2. 同意使用另外兩本相簿：**A = `2024/04/22～04/26`（45 張）**、**B = `2024/4/21`（78 張）**。
3. 允許修 Python 環境（已用隔離 venv，未動系統／global runtime）。
4. 走**正式路**，不以手動 Save All 取代。

## 3. 已完成的真實驗證

| 項目 | 實測結果 |
|---|---|
| 正式 state | `revision 35`，SHA-256 `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`，**未變** |
| `verified_albums` | `2024-05-06..05-10`(182)、`2024-05-13..05-17`(57) → 合計 **239** |
| manual 已下載 | `05-27..05-31`(56，18,117,492 B)、`05-20..05-24`(53，17,095,114 B) → 合計 **109** |
| 排除相簿 | `2024-06-02..06-07`(65)，目錄檔案數 **0**，本輪未觸碰 |
| Python 環境 | 隔離 venv（Python 3.13.11、jsonschema 4.26.0、rpds-py 2026.9.1），可執行 |
| authorizer | `exit 4` / `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED` / `dispatch_authorized=false`（拒絕仍有效） |
| manifest／verification | A56 manifest `99c903e9…e976`、B53 manifest `e2da806c…bd36`、B53 verification `49881e79…229c` |

GUI 0、Save All 0、下載 0、state 寫入 0。

## 4. 三個新發現

### 4.1 registry hash 抄到「已遮蔽版」（Plan §9.1 已修）

`a56-verification.json` 在 PR 分支為 `a67e8207…a38a`，在 Owner 本機 canonical 為 `9381d72a…2a38`；唯一差異是 `destination_workspace_relative` 的群組名。照原 Plan 實作，loader 必然 fail closed 成 `MANUAL_ARCHIVE_REGISTRY_INVALID`。

→ 修正：registry 的 hash **只能對「實際會被讀取的路徑」即時計算**，不得手抄；並補一條「遮蔽版必須 fail closed」的測試。

### 4.2 「eligible = 0」是推論錯誤（Plan §10 已更正）

先前把 `backups/` 的 5 個目錄當成「總共只有 5 本」。Owner 授權前景後實際向下捲動（click 0）：

| 排名（新→舊） | 日期 | 張數 | 既有備份 |
|---|---|---|---|
| 1 | `2024/04/22～04/26` | 45 | 無 |
| 2 | `2024/4/21`（單日） | 78 | 無 |
| 3 | `2024/04/08～04/12` | 77 | 無 |
| 4 | `2024/04/01～04/03` | 42 | 無 |
| 5 | `2024/03/25～03/29` | 87 | 無 |

列表在 `03/25～03/29` 之下尚未到底，總數 UNKNOWN。私有截圖含兒童照片，**未上傳**。

### 4.3 單日相簿 `2024/4/21` 目前不可解析（Plan §11，待裁決）

以 PR #10 `ocr_date_identity()` 實跑：

```text
'2024/04/22～04/26'  -> {'start_date':'2024-04-22','end_date':'2024-04-26'}
'2024/4/21'          -> None     <- 畫面實際文字
'2024/04/21'         -> None
'2024/04/21～04/21'  -> {'start_date':'2024-04-21','end_date':'2024-04-21'}
```

根因：`observations.py:42` regex 強制兩位數 + 區間；`:494` 標題期望固定為 `YYYY/MM/DD～MM/DD`。產品「新→舊」掃描的第二順位就是 `04/21`，因此 **B 現階段選不到**。與 grant／CUA／Save All 無關。

## 5. Plan v4 實作範圍（核准後才動工）

**新增**
- `src/line_backup_acceptance/manual_archive.py`：fail-closed loader
- `tests/test_manual_archive_registry.py`：8 個聚焦案例
- `state/manual_archives.json`（local／untracked，不含群組名／照片／絕對路徑）

**修改**
- `project_binding.history_decision()`：新增 `SKIP_MANUAL_DIAGNOSTIC`（優先序 `PROJECT_BUSY → SKIP_VERIFIED → SKIP_MANUAL_DIAGNOSTIC → AMBIGUOUS → BLOCKED_UNRESOLVED → ELIGIBLE`）
- `service.py`：`eligible` / `prepare` skip 分支 / `admit_bounded`
- `store.py`：lazy `manual_fingerprints()`
- `cli.py`：`inspect` 排除 + `--record-manual-archive`（即時計算 hash）
- 若採「甲」：`observations.py` 的 `ocr_date_identity` 與標題期望支援單日

**明確不改**
`state_v3.schema.json`、grant、ledger、`line_backup_cua_adapter.mjs`、dispatch／intent／at-most-once 語意、`verified_albums`。

## 6. Acceptance Criteria

| AC | 內容 |
|---|---|
| AC1 | registry 具 `provenance=MANUAL_DIAGNOSTIC`、fingerprint、manifest／verification 路徑與 SHA-256、檔數、bytes |
| AC2 | 任一不符（缺檔／hash／count／bytes／provenance／app／group／schema）→ `MANUAL_ARCHIVE_REGISTRY_INVALID`，不得靜默忽略 |
| AC3 | 精確 fingerprint 命中回 `SKIP_MANUAL_DIAGNOSTIC`；同時為正式 VERIFIED 時 `SKIP_VERIFIED` 優先 |
| AC4 | `admit_bounded()` 對 manual 命中回 `BOUNDED_TARGET_INELIGIBLE`，不開 detail、不派送 |
| AC5 | `inspect` 的 eligible 清單排除 manual 命中 |
| AC6 | 不寫 `verified_albums`、不改 revision、不產生 run／intent／dispatch receipt |
| AC7 | 239 VERIFIED、109 manual、65 排除相簿、`2/2` 配額全部不變 |
| AC8 | eligible < 2 → `NO_ELIGIBLE_TARGET`，零派送、零副作用（現為安全網） |
| AC9 | （若採甲）單日解析正確，且不得誤解析非法日期 |

## 7. 需要 Reviewer 裁決

1. 對 Plan v4（§9／§10／§11）回 `APPROVE_PLAN` 或 `CHANGES_REQUIRED`？
2. 單日相簿採 **(甲) 擴充支援**（建議）或 **(乙) 換 B 為 `04/08～04/12` 並定義安全略過**？
3. eligible>0 之後，AC8 是否仍保留為硬性安全網？（建議保留）
4. `MANUAL_DIAGNOSTIC` registry 設計與 fail-closed 強度是否足夠？AC1–AC7 是否需增刪？
5. 核准後關卡順序是否確認為：實作 → 聚焦測試 → External Code Review → quota-2 grant → Owner 啟動獨立 `deepseek-v4.1-flash:1017` Session？在那之前 Owner 還需先提供什麼？

## 8. 狀態

```text
PLAN_STATUS=PENDING_EXTERNAL_PLAN_REVIEW (v4)
PRODUCT_CODE_CHANGED=NO   TESTS_ADDED=NO
GUI=0  SAVE_ALL=0  DOWNLOADS=0  STATE_WRITES=0
STATE_REV=35  STATE_SHA256=4550501…8ee6
A56_SAVE_ALL=PASS_EXISTING_NOT_RERUN   B53_SAVE_ALL=PASS_EXISTING_NOT_RERUN
NEW_A_SAVE_ALL=NOT_RUN   NEW_B_SAVE_ALL=NOT_RUN   TWO_ALBUM_AUTO=NOT_RUN
AUTHORIZER=exit4 PROJECT_IMPLEMENTATION_REVIEW_REQUIRED
BLOCKER=NEED_PLAN_APPROVAL_BEFORE_ANY_IMPLEMENTATION
```
