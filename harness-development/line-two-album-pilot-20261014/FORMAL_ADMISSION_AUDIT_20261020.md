# 正式 TWO_ALBUM_AUTO 准入稽核（2026-10-20）

- 類型：`READ_ONLY_ADMISSION_AUDIT`（不是 E2E、不是 Save All、不是 VERIFIED）
- 執行時間：2026-10-20 21:5x（Asia/Taipei）
- 依據：External Chief 對 PR #21 的最新審查（review `5585712189`）與 Owner 回報要求
- 本輪 GUI 輸入：**0**
- 本輪 Save All 派送：**0**
- 本輪 state／ledger／grant 寫入：**0**
- 正式狀態：`TWO_ALBUM_AUTO = BLOCKED`、`A/B formal VERIFIED = NOT_RUN`

> 本檔只陳述實際讀取、實際執行與靜態程式路徑；不把 manual 下載冒充正式 AUTO 交易。

## 1. A56／B53 實體檔案唯讀核對

以現有 manifest 對 Mac 上的實體檔案逐檔重算 SHA-256，並比對 verification JSON 的 count／bytes／digest。未修改任何檔案。

| 相簿 | 實體檔數 | 實體 bytes | Manifest 條目 | SHA 不符 | 缺少 | 多出 | 結果 |
|---|---:|---:|---:|---:|---:|---:|---|
| A56 `2024/05/27～05/31` | 56 | 18,117,492 | 56 | 0 | 0 | 0 | **PASS** |
| B53 `2024/05/20～05/24` | 53 | 17,095,114 | 53 | 0 | 0 | 0 | **PASS** |

- 證據：[`public/readonly-inventory-20261020/inventory.json`](./public/readonly-inventory-20261020/inventory.json)（SHA-256 `ec1a41d6…5c610`）
- 重算工具：[`scripts/readonly_inventory_20261020.py`](./scripts/readonly_inventory_20261020.py)
- A manifest：`manual-diagnostic-20261020-a56/a56-sha256.txt`（`99c903e9…e976`）
- A verification：`manual-diagnostic-20261020-a56/a56-verification.json`（`a67e8207…a38a`）
- B manifest：`manual-diagnostic-20261020-b53/b53-sha256.txt`（`e2da806c…bd36`）
- B verification：`manual-diagnostic-20261020-b53/b53-verification.json`（`49881e79…229c`）
- 實體目錄（已去識別）：`<CANONICAL_ROOT>/backups/<REDACTED_GROUP>/2024-05-27_2024-05-31_56張`、`.../2024-05-20_2024-05-24_53張`
- 正式 state：revision **35**、`verified_albums` 仍為既有 2 筆；`state/backup_state.json` SHA-256 `45505011…8ee6`、mtime `2026-10-10T18:00:50+0800`，本輪未變更。

## 2. 現有產品是否能「合法納管」已下載檔案

結論：**沒有既有合法入口**。原因不是文件缺漏，而是交易語意本身要求「同一 run 的真實派送」。

| 檢查點 | 實際程式事實 | 影響 |
|---|---|---|
| `finalize --outcome VERIFIED` | `src/line_backup_acceptance/transaction.py:577` 要求 active run、owner 與 revision；VERIFIED 前必須 `_dispatch_complete(run)`（`:518`） | manual 下載沒有 run／intent／dispatch，直接拒絕 |
| 驗證消費 | `_consume_verification`（`:491`）要求 `verification.run_id == run.run_id`，且 group_key／fingerprint／destination 全部等於該 run | 不能拿 manual 的 verification JSON 掛到任意 run |
| 註冊 verified album | `transaction.py:634` 寫入的 entry 必須帶 `verified_run_id`；`common.py:184` 固定 entry keys | 沒有 run 不能註冊 |
| `source_kind` | `common.py:408` 僅允許 `filesystem_verification`／`user_attestation` | `user_attestation` 是「來源身分確認」，不是「檔案已下載」 |
| user fact 驗證 | `project_binding.py:215` 要求 `source_kind=user_attestation` 且 `run is None`，但內容必須是 confirmed group/album/count 的問答 | 仍不能跳過 dispatch 產生 VERIFIED |
| acceptance CLI | 只有 `project-preflight`、`verify-only`、`transaction {prepare,resume,commit,finalize,duplicate-check}`、`status evaluate` | 沒有 `import`／`adopt`／`reconcile-manual` 指令 |

因此不能把 A56／B53「補登」成 VERIFIED，也不能偽造 AUTO 派送紀錄。這種 import／provenance 機制若要做，屬於 state 語意與資料邊界變更，必須先走 Plan Review 與外部 Code Review，不能由本輪自行實作。

## 3. 正式 `runTwoAlbumPilot()` 的第一個具體阻塞

### 3.1 目前唯一可用的 authority 是「單相簿 ONE56」，且目標就是已下載的 A56

實際讀取 `<CANONICAL_ROOT>/harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-20261017-8bebd23-PENDING-c6147d8f/`：

| 欄位 | 實際值 |
|---|---|
| `project-contract.json: entry_method` | `runSingleAlbumPilot` |
| `project-contract.json: fingerprint` | `2024-05-27`～`2024-05-31`, 56 張（A56） |
| `project-contract.json: no_second_album` | `true` |
| `project-contract.json: lifecycle_limit` | `1` |
| `project-contract.json: authority_status` | `REVIEW_PENDING_NO_LIVE_AUTHORITY` |
| `project-grant.json: single_album_route` | `true` |
| `project-grant.json: album_quota` | `1` |
| `project-grant.json: lifecycle_album_limit` | `1` |
| `project-grant.json: save_all_dispatch_limit` | `1` |
| `implementation-review.json` | `status=PENDING_EXTERNAL_REVIEW`、`approved_operations=[]` |

這是語意層阻塞，不是座標或 GUI 問題：**唯一待審 grant 只允許 A56 一本、一次 Save All；A56 已經 manual 下載完成，依 Owner／Chief 指示禁止再派送。** 即使這份 grant 明天通過，也不能拿來跑 TWO_ALBUM_AUTO，更不能重下 A56。

### 3.2 更嚴重的去重缺口：A56／B53 在正式 state 中仍被視為 eligible

`history_decision`（`src/line_backup_acceptance/project_binding.py:368`）只依 `runs` 與 `verified_albums` 判斷：

- A56、B53 都不在 revision 35 的 `runs`／`verified_albums`。
- 因此 `eligible()` 會回 `PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION`。
- `runTwoAlbumPilot()` 的候選來自畫面上 fully-visible 卡片 fingerprint，沒有「manual 已下載」排除條件。

**風險：若未來以一份 quota 2 的新 grant 直接跑正式 AUTO，產品不知道 A56／B53 已備份，可能再次 Save All 這兩本。** 目前沒有任何合法機制可把它們標記為「已手動下載、不得重送」。這是必須先解決的 state／policy 缺口。

### 3.3 Source／Runtime 綁定現況

| 項目 | 實測值 |
|---|---|
| Canonical repo HEAD | `b7bb666fa78b8e9dfffed8247c4f2a7f869a481b`（工作樹有既有 dirty 變更） |
| Canonical product source closure | `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54` |
| Grant `source_sha256` | `ff717d721c91…ca54`（**與現行安裝來源相符**） |
| Grant `entry_binding` | `726db9a876619aee66df57f0600f3ef07e40910c3f8285b266397800e12895f1`（＝現行安裝 `two_album_entry.mjs`） |
| PR #10 pilot HEAD | `516932dfcee94b662082b909b7980fc2483ab9c0` |
| PR #10 source closure | `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d` |
| PR #10 `two_album_entry.mjs` | `f5981c071709203adc2c1cbbc8d5779a77eb1bc37cf0eb8e0444aa5ee21ab277`（**與 grant 不同**） |

解讀：grant 綁的是「目前安裝的來源」，不是 PR #10 的 `516932d`。因此不能把 PR #10 的 `runTwoAlbumPilot()` 說成已被這份 grant 授權；反之，若照 grant 執行，跑的也不是 PR #10 的雙相簿入口。這是 version binding 的實質阻塞。

### 3.4 本輪實際 authorizer 輸出（環境層）

以 Canonical root 實際執行（唯讀、零 GUI）：

```text
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
/opt/homebrew/opt/python@3.13/bin/python3.13 -B -m line_backup_batch.cli native_authorize \
  --project-root <CANONICAL_ROOT> \
  --authorization harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-20261017-8bebd23-PENDING-c6147d8f/project-grant.json
```

實際結果：`exit 4`

```json
{"status": "REFUSED", "code": "INVALID_REQUEST", "message": "No module named 'jsonschema'", "dispatch_authorized": false}
```

原因：原本固定的 Harness runtime venv 指向已不存在的 Homebrew Python 3.14：

```text
<CODEX_HOME>/harness-runtime/4.7.0/.venv/bin/python3 -> python3.14
-> /opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/bin/python3.14  (MISSING)
```

這是 execution environment 的阻塞，不是產品邏輯錯誤；不能因為它而改產品程式。歷史上同一 authorizer 在 2026-10-18 的可執行環境曾真實回應 `exit 4 / PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`（見 `harness-development/one56-menu-compat-20261017/review/formal-route-preflight-20261018.json`），該拒絕仍然有效，且與本次的 `INVALID_REQUEST` 是兩個不同層級的第一拒絕。

## 4. 狀態總表

| 項目 | 狀態 | 依據 |
|---|---|---|
| A56 實體檔案／manifest 重hash | **PASS** | inventory.json |
| B53 實體檔案／manifest 重hash | **PASS** | inventory.json |
| 現有產品可合法 import manual 檔案 | **NO** | transaction.py / CLI 稽核 |
| 正式 `runTwoAlbumPilot()` 准入 | **BLOCKED** | 單相簿 ONE56 grant、PENDING_EXTERNAL_REVIEW、quota 1 |
| 自動去重排除 A56／B53 | **FAIL（缺口）** | history_decision 只看 state |
| Authorizer 可執行 | **BLOCKED（環境）** | `No module named 'jsonschema'` |
| 本輪 GUI／Save All | **NOT_RUN（0）** | 無前景輸入 |
| 正式 A／B VERIFIED | **NOT_RUN** | state revision 35 未變 |
| Independent DeepSeek 1017 E2E | **NOT_RUN** | 尚未取得合法新 grant |

## 5. 下一步（需 Owner／Reviewer 決策）

1. **不要在目前 grant 上執行任何 LINE 操作。** 它只授權 A56 單本，且 A56 已完成；重用即違反不重下載。
2. **建立新的 bounded 雙相簿 authority bundle**：兩個「不同、未備份」的 fingerprint、`album_quota=2`、`save_all_dispatch_limit=2`、`no_second_album=false`、綁定一個精確 reviewed HEAD（若要用 PR #10，需以 `516932d` 為 implementation head 重新審查 entry hash）。
3. **先補上 manual provenance 的合法表示**，二者擇一並經外部審查：
   - (a) 明確的 `MANUAL_DIAGNOSTIC` registry／exclusion（不冒充 VERIFIED、不建立 dispatch receipt）；或
   - (b) 經核准的 import／adopt 交易，帶 provenance 與 hash，仍不得寫成 AUTO E2E。
4. **修復 pinned Python runtime**（或提供等效且可稽核的 authorizer runtime），讓 `native_authorize` 能再次給出真正的授權判定；這不是程式碼修補。
5. 完成上述准入後，才由 Owner 啟動新的獨立 `deepseek-v4.1-flash:1017` session，以兩本**其他** eligible 相簿跑正式 Save All、逐檔驗證與 VERIFIED。

在上述決策完成前，TWO_ALBUM_AUTO 不能宣稱 PASS，也不應再進行任何 Save All 嘗試。
