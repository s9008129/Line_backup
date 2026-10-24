# 可重複使用入口與手冊：本機檢查報告

日期：2026-10-24。範圍：文件與既有能力盤點，QUICK，無產品程式修改、無 GUI 輸入、無新下載。沿用 Owner 本輪目標，不變更 Harness、正式驗收或交易政策。序列執行，無代理分工。

## 計畫與結果

1. 唯讀核對工作樹、README、專案 AGENTS、LINE Skill 及 verified-experience。
2. 核對 PR28 本機實機報告、最新私有 batch summary、checkpoint、逐本 completion-record、正式 state 與 manual archive。
3. 確認 CLI、CUA 工具及現有 adapter／ImageIO 來源，整理去識別化手冊與完整 Prompt。
4. 檢查 14 節、必要參數、安全約束、隱私與差異；只提交本輪文件，不 push。

本輪沒有實作控制器、啟動腳本、GUI 框架或自動匯入器。保存位置及紀錄格式為 Agent 操作約定，尚未在新群組實測。一般文件切片不需要以新下載或正式 E2E 證明文件完成。

## 實際觀察與可重現檢查

| 檢查 | 實際結果 |
|---|---|
| `command -v codex`、`codex --version`、`codex --help` | PASS，已安裝 CLI 0.164.0；無子命令可進互動介面 |
| `codex mcp list` | cua_repl enabled；單憑設定不宣稱 GUI PASS |
| `cua.getState()` | PASS，原生 App inventory 包含執行中的 LINE；未取得群組畫面、未派送輸入 |
| README／adapter 原始碼 | acceptance CLI 不派送 Save All；adapter 需真實 CUA App，不是獨立啟動器 |
| 手冊必要章節與參數 | Python assertion：1–14 節、GROUP_NAME、BACKUP_ROOT、EXCLUSIONS、UNKNOWN、ImageIO、MANUAL_DIAGNOSTIC 均存在，PASS |
| 手冊私人群組名與個人路徑檢查 | 本輪對已知私人字串檢查 PASS；文件例子使用佔位文字 |
| `git diff --check` | PASS；提交前再查本輪 staged 差異 |
| 新群組下載／9,306 張重驗／外接硬碟複製 | NOT_RUN |
| 正式 AUTO／獨立 E2E | NOT_RUN，不能從文件或歷史結果升級 |

實際使用 PR28 的 metadata strip、詳細頁雙重核對、選單／下載驗證方法，以及 PR32 的即時捲動與過期 AX 重新觀察方法編寫 Prompt；沒有沿用座標或下載授權。

## 本機證據識別

以下以 repo 相對位置標示；絕對位置可由 `git rev-parse --show-toplevel` 的結果接上該路徑取得。公開文件省略個人路徑、群組／相簿名稱與照片清單，私有來源留在本機，沒有上傳。

- `harness-development/line-five-album-manual-20261022/private/batch-summary-20261024.json`，SHA-256 `1a16956beb3b8669104bff049b4398dfac1b9d3092f0da8a96668fd10be52917`：MANUAL_DIAGNOSTIC，列表到底、新完成 19 本／1,555 張，無重複下載、未修改正式 state；不是全群組總帳。
- 同目錄 `checkpoints.json`，SHA-256 `69d385ac9ccf3f5ba139ca45b6d0412c17499ce9e3e6c44eb50b62cb786f548e`：較早五本紀錄，不能拿來取代最新逐本完成紀錄。
- 同目錄 `candidate-*/completion-record.json`：唯讀發現 89 份，狀態皆為 COMPLETED。它們與正式 state、manual archive 有交集可能，不直接相加推算總本數。本輪未重新審計全部照片。
- `state/backup_state.json`，SHA-256 `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`。
- `state/manual_archives.json`，SHA-256 `efe572afc9da1ae2123b3016430370f9ecd84ffb259f3bf73b0e5d26cd667bc5`。
- `src/line_backup_batch/image_decode.swift`，SHA-256 `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b`：唯讀完整 RGB 解碼及逐檔 SHA；不要求 hash 互異。未重跑歷史照片。
- PR28 必要成功來源：`harness-development/line-five-album-manual-20261022/E2E測試報告.md`；PR32 的本地原始報告路徑本輪不存在，只能引用 Skill 的 verified-experience 摘要，不能宣稱重讀到原始 PR32 證據。

Owner 提供 99 本、完成 98 本／9,306 張、排除 1 本及 INCOMPLETE／UNKNOWN 均零，本輪將其保留為既有成果陳述，未將其提升為正式 AUTO 或本輪逐檔驗證結論。

## 限制與下一步

下一個 CLI Session 的 GUI 權限、跨群組實際下載、保存約定的中斷恢復尚未驗證。舊紀錄仍分散在專案私有目錄；本輪未搬移照片、匯入狀態或更動排除。Prompt 要求每次先讀舊來源；不可因新 BACKUP_ROOT 沒有紀錄而重下載。

PRIMARY_OUTCOME_STATUS=PREPARATION_COMPLETE
IMPLEMENTATION_STATUS=DOCUMENTATION_COMPLETE
CORE_ACCEPTANCE_STATUS=DOCUMENT_CHECKS_PASS
REQUIRED_VERIFICATION_STATUS=LOCAL_CHECKS_PASS
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN_FOR_NEW_GROUP
TASK_CLOSURE_STATUS=PREPARATION_ONLY

下一步：Owner 指定新群組與正式保存目錄，在有原生 Computer Use 的 Session 貼上手冊 Prompt，確認當次前景與下載授權。這次不需要重跑舊照片。若工具或 gate 擋住，回報第一個具體阻塞，不建立空殼入口。本輪沒有修復重試，也未建立或冒稱外部審查結果。
