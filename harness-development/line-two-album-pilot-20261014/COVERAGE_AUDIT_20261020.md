# COVERAGE AUDIT 2026-10-20 — 本群組是否還有「另外兩本」eligible 相簿？

- 狀態：`READ_ONLY_NO_GUI_NO_STATE_WRITE`
- 目的：在建立新的雙相簿 grant 之前，先確認 Owner 核准的「另外兩本不同相簿」**實際存在且 eligible**
- 方法：只讀 `state/backup_state.json`、`backups/<REDACTED_GROUP>/` 目錄與既有 manifest／verification；**未開 LINE、未寫 state、未 Save All**
- **最新狀態（2026-10-20，Plan v4.1 輸入）**：真實 LINE 已觀察到至少 5 本既有備份之外的 eligible 候選；本次唯一正式目標為 **A45（`2024/04/22～04/26`）與 B78（`2024/4/21` 單日）**，65 張相簿永久排除。下方 §1／§7 的 `ELIGIBLE_ALBUMS_IN_CURRENT_GROUP=0` 是歷史推論，已被 CORRECTION 推翻；不刪除原文。

> ## ⚠️ CORRECTION（2026-10-20 22:38，本節推翻下面 §1 的結論）
>
> 下面的 §1／§2 只根據 `backups/` 目錄推論，犯了**「已下載 5 本」等於「總共只有 5 本」**的錯。Owner 其後授權真機捲動，實測結果是：
>
> - 相簿列表在 `2024/05/06` 之後**還有更多相簿**，一路到 `2024/03/25～03/29` 尚未到底。
> - 新發現、且**不在任何既有備份**中的 eligible 相簿至少 5 本：
>
> | 排名（新→舊） | 日期 | 張數 |
> |---|---|---|
> | 1 | `2024/04/22～04/26` | 45 |
> | 2 | `2024/4/21`（單日） | 78 |
> | 3 | `2024/04/08～04/12` | 77 |
> | 4 | `2024/04/01～04/03` | 42 |
> | 5 | `2024/03/25～03/29` | 87 |
>
> - 因此 **eligible 相簿數量不是 0**；`NO_ELIGIBLE_TARGET` 不成立。§9.2 的 AC8 仍然有效（作為安全網），但「Owner 必須換群組」的結論**作廢**。
> - 證據：`private/album-list-scroll-20261020/`（本機私有，含兒童照片，**未上傳**），`observations.json` + `SHA256SUMS.txt`。公開文件只保留日期／張數。
> - 操作副作用：click 0、Save All 0、下載 0、state 寫入 0；只有滾輪捲動。
>
> 保留 §1–§5 原文不動，作為「錯誤推論如何發生」的可追溯紀錄。

## 1. 結論（**已被上方 CORRECTION 推翻，僅保留作歷史紀錄**）

**本群組目前沒有可下載的 eligible 相簿。**

已對帳的 5 本相簿中，2 本已是正式 `VERIFIED`、2 本已由 manual diagnostic 實體下載完成、1 本是 Owner 指定排除（且目錄為空、從未下載）。
因此「再用另外兩本相簿跑 TWO_ALBUM_AUTO」在**目前這個群組內不可能成立**，不是程式 bug，也不是 grant 問題。

## 2. 對帳表（實體檔案層）

群組目錄：`backups/<REDACTED_GROUP>/`（名稱在公開證據中遮蔽）

| 相簿目錄 | 檔案數 | 狀態來源 | eligibility |
|---|---|---|---|
| `2024-05-06_2024-05-10_182張` | 182 | 正式 `VERIFIED` | `SKIP_VERIFIED` |
| `2024-05-13_2024-05-17_57張` | 57 | 正式 `VERIFIED` | `SKIP_VERIFIED` |
| `2024-05-20_2024-05-24_53張` | 53 | manual diagnostic（B53） | 應為 `SKIP_MANUAL_DIAGNOSTIC`（本輪尚未實作） |
| `2024-05-27_2024-05-31_56張` | 56 | manual diagnostic（A56） | 應為 `SKIP_MANUAL_DIAGNOSTIC`（本輪尚未實作） |
| `2024-06-02_2024-06-07_65張` | **0** | Owner 指定排除 | 永不可選 |

182 + 57 = **239**，正好等於歷史 `VERIFIED` 總數；56 + 53 = **109**，正好等於本輪 manual 下載總數。三者互不重疊。

## 3. 正式 state 對帳（revision 35，未寫入）

- `state/backup_state.json` SHA-256 = `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`（與前一輪一致，未變）
- `revision = 35`、`active_batch = null`、`current_run_id = RUN-20261009-project-album182`（終態）
- `verified_albums` 僅 2 筆：
  - `2024-05-13 .. 2024-05-17`，57 張 → `RUN-20261004-project-album57-45ee0a78`（VERIFIED）
  - `2024-05-06 .. 2024-05-10`，182 張 → `RUN-20261009-project-album182`（VERIFIED）
- `runs` 僅 2 筆，皆 `VERIFIED`
- 56／53 **不在** `verified_albums`，也不在 `runs` → 這是 `history_decision()` 會把它們判成 eligible 的唯一原因

## 4. 第二個發現：A56 verification JSON 有「已遮蔽版」與「本機原版」兩種 hash

| 檔案 | SHA-256 | 說明 |
|---|---|---|
| `a56-sha256.txt` | `99c903e91415f6dff275668c5794390e581fa42764912eda9c63a038b45ce976` | 兩邊一致 |
| `a56-verification.json`（PR 分支上的已遮蔽版） | `a67e82078e08a3eed480844b3248ef6e345e6d55b388ec98954d10208af7a38a` | Plan v4 曾引用；v4.1 已改為實際路徑即時計算 |
| `a56-verification.json`（Owner 本機 canonical 版） | `9381d72a01adf3b65f3738c91c226868e02d18de96453fc91eadc07ff6db2a38` | 實際執行時會被讀到的檔案 |

兩者差異只有一個欄位：

```text
destination_workspace_relative
  committed(redacted) : backups/<REDACTED_GROUP>/2024-05-27_2024-05-31_56張
  canonical(local)    : backups/<真實群組名>/2024-05-27_2024-05-31_56張
```

**影響（Plan 必須修正）**：`PLAN-20261020-manual-archive-exclusion.md` 的 registry 範例把 `verification_sha256` 寫成已遮蔽版的 hash，但 loader 會去讀 canonical 專案根下的本機檔案 → fail-closed 會直接拋 `MANUAL_ARCHIVE_REGISTRY_INVALID`，整個排除機制在真機上必然失效（而且是「看起來有做、其實永遠擋住」的假成功）。

修正原則：**registry 只能宣告「它實際會讀的那個檔案」的 hash**，不得手工抄寫；hash 必須在建立 registry 時由同一條路徑即時計算，並在讀取時重新核對。

## 5. 這對 grant 設計的影響（歷史推論；已被 CORRECTION 與 §8 推翻）

- 原本 Plan §6 要求「target 必須是兩本**不同、未在 verified 或 manual registry** 的 eligible 相簿」。
- 依本節第 2 點的對帳，**本群組內符合條件的相簿數量 = 0**。
- 因此建立新的 `album_quota=2` grant 之前，必須先取得「另一個群組／對話」的相簿清單，或由 Owner 確認本群組在已看到的 5 本之外還有更多相簿（需真機列表演員與捲動證據，不能用推測）。

## 6. 重現方式（全部唯讀）

```bash
cd <PROJECT_ROOT>
shasum -a 256 state/backup_state.json
python3 -c "import json;s=json.load(open('state/backup_state.json'));print(s['revision'],s['verified_albums'])"
ls backups/<REDACTED_GROUP>/
find 'backups/<REDACTED_GROUP>/2024-06-02_2024-06-07_65張' -type f | wc -l   # → 0
shasum -a 256 harness-development/line-two-album-pilot-20261014/public/manual-diagnostic-20261020-a56/a56-verification.json
```

## 7. 狀態總結（歷史快照；`ELIGIBLE_ALBUMS_IN_CURRENT_GROUP=0` 已被上方 CORRECTION 推翻）

> **HISTORICAL / OVERRIDDEN：** 本節保留當初唯讀目錄對帳的快照，不作現況。現況是至少 5 本新候選，正式目標 A45／B78；不需為此再取得新證據。

```text
STATE_WRITES=0
GUI_OPENED=NO
SAVE_ALL=0
A56_BYTES_UNCHANGED=YES
B53_BYTES_UNCHANGED=YES
VERIFIED_TOTAL=239_UNCHANGED
MANUAL_TOTAL=109_ALREADY_BACKED_UP
ELIGIBLE_ALBUMS_IN_CURRENT_GROUP=0
EXCLUDED_65_ALBUM_FILES=0_UNTOUCHED
NEW_FINDING_1=NO_ELIGIBLE_TARGET_IN_CURRENT_GROUP
NEW_FINDING_2=A56_VERIFICATION_REDACTED_VS_LOCAL_HASH_MISMATCH
```

## 8. 現況覆寫（Plan v4.1）

```text
ELIGIBLE_ALBUMS_IN_CURRENT_GROUP=AT_LEAST_5_OBSERVED_IN_REAL_LINE
HISTORICAL_ELIGIBLE_ZERO_STATUS=OVERRIDDEN_BY_CORRECTION
TARGET_A=2024-04-22..2024-04-26_45
TARGET_B=2024-04-21..2024-04-21_78
OWNER_EXCLUDED=2024-06-02..2024-06-07_65_UNTOUCHED
PLAN_REVISION=v4.1_PENDING_FAST_REREVIEW
```

## 9. 追加發現（2026-10-20 22:50）— 單日相簿 `2024/4/21` 目前無法被產品解析

B 目標 `2024/4/21` 是**單日相簿**，畫面文字沒有前導零、也沒有日期區間。以 PR #10 pilot HEAD `516932d` 的實際程式碼執行：

```text
$ PYTHONPATH=src python -c "from line_backup_batch.observations import ocr_date_identity; ..."
'2024/04/22～04/26'   -> {'start_date': '2024-04-22', 'end_date': '2024-04-26'}
'2024/4/21'           -> None      ← 畫面實際文字
'2024/04/21'          -> None
'2024/4/21～4/21'     -> None
'2024/04/21～04/21'   -> {'start_date': '2024-04-21', 'end_date': '2024-04-21'}
'2024/03/25～03/29'   -> {'start_date': '2024-03-25', 'end_date': '2024-03-29'}
```

- 來源：`src/line_backup_batch/observations.py:42`，regex `(\d{4})/(\d{2})/(\d{2})\s*[~～〜]\s*(\d{2})/(\d{2})`，**強制兩位數 + 區間**。
- 另 `observations.py:494` 的標題期望固定為 `start.replace('-','/') + '～' + end[5:]`（例：`2024/04/21～04/21`），與 LINE 實際顯示的 `2024/4/21` 不符。

**影響**：相簿 A（`04/22～04/26`）本身沒問題；但產品是「新→舊」掃描，第二順位就是 `2024/4/21`。它會解析失敗，連帶讓 B 選不到。這**不是** Save All 或 CUA 問題，是純解析層缺口，且可在無 GUI、無 state 寫入下重現。

**兩個處理選項（需 Reviewer 裁決）**：

- **(甲) 擴充單日支援**：`ocr_date_identity` 增加「無區間」分支（`YYYY/M/D` → start = end），並同步修正 `:494` 的標題期望。屬最小解析修正，需聚焦回歸（不得改動 at-most-once／dispatch 行為）。
- **(乙) 換 B**：改用 `2024/04/08～04/12`（77 張）。但產品仍會先遇到 `04/21`，因此仍需定義「無法解析的卡片如何安全略過並留下證據」，否則等於把缺口藏起來。

**建議**：採 (甲)，因為單日相簿是真實存在的資料形態；且必須補上「`2024/4/21` → `2024-04-21..2024-04-21`」與「`2024/4/21` 不得被誤解析成其他日期」兩條測試。
