---
name: line-album-agent-cua
description: 在 macOS LINE 以目前前景相簿列表進行 Agent 備份、完整盤點與相簿級中斷恢復；使用原生 Computer Use，保護既有照片及完成紀錄。
---

# LINE 前景相簿備份

使用者把正確群組的「相簿列表」放到前景並指定儲存位置即可；**不要求輸入 GROUP_NAME，不以群組名稱或其中文 OCR（包括模糊比對）辨識、選擇或核准備份對象**。Agent 根據最新畫面、AX、視覺脈絡及必要 OCR 判斷卡片／控制項；Computer Use 執行輸入，程式守住紀錄、去重與檔案安全。不新增 GUI 框架、不重用舊座標。

## 依情境讀取

- 完整盤點是必備能力：先讀 [完整盤點與下載清單](references/inventory.md)。每次新備份須先完成此流程；只盤點不開選單、不派送 Save All。
- 實機導覽／選單：先讀 [已驗證經驗](references/verified-experience.md)，使用 PR28 metadata strip → 詳細頁核對 → fresh menu 的方法，及 PR32 過期 AX 重新觀察／重疊捲動經驗。
- 完整列表、跨群組紀錄或中斷恢復：讀 [日常備份與恢復](references/daily-backup.md)，使用現有 `src/line_backup_batch/daily.py` 輔助記錄及 `image_decode.swift` 驗證；輔助 CLI 不操作 LINE、不簽發 grant。
- 首次使用、交接給一般使用者：讀 [使用手冊](../../../docs/LINE相簿備份_使用手冊.md)。

## 執行迴圈

先確認本次模式：`REVIEW`（離線檢查 Skill）、`INVENTORY_ONLY`（只盤點）、`BACKUP`（盤點完成後依授權下載）、`RESUME`（查舊結果後接續）。討論、審查或修改 Skill 不構成 GUI 授權；盤點授權也不構成下載授權。用途不明先問，不自行升級模式。前景由 Owner 人工開啟正確列表並交接，Agent 不依群組名稱搜尋或選擇另一列表。

1. 先讀根目錄 `AGENTS.md` 及當次授權。核對原生 Mac 工具、LINE 與當次前景交接；Owner 正在使用電腦時先做離線工作，真正需要前景才提出交接。登入畫面、前景中斷或對象不明時停止 GUI 輸入。
2. **前景是對象，目的地是紀錄邊界。** 唯讀查正式 state、manual archive、私有 completion／intent、最新 batch summary 及排除清單；只使用已確認屬於當前群組的紀錄。目的地綁定持久本地 UUID；LINE 若有可靠 opaque ID 可輔助，名稱／路徑名稱／一字 OCR 差異都不決定群組身分。新 Session 以新畫面重核群組與 UUID 對應，有歧義才請 Owner 確認，不自動跨群組套用舊紀錄。
3. **先完整盤點，再下載。** 依 inventory 參考從頂端到末端逐卡記錄；每次捲動保留有序重疊與前後證據，日期／張數相同仍須視覺識別。確認底端及逐本去重後，先保存總本數、完成／排除／待下載／未完成／未知／受保護歷史數量與有序下載清單。總數未對上、缺頁或身份未釐清，不進入下載。AX 子項數不是總本數。舊格式／不完整來源保留為 `PROTECTED_HISTORY`：不重下載，也不當完成或排除。`INVENTORY_ONLY` 到此結束；不可繼續下列下載步驟。
4. 點卡片 metadata strip；在詳細頁重新核對日期、張數及可區分的視覺脈絡，再看 fresh `⋯` 選單。主視窗看不到 popup 時，先沿用現有 native window list／指定 popup screenshot／OCR 方法觀察，不盲點。每次動作後重新觀察 AX／畫面。
5. Save All 前須有有效 L2、受審且綁定的 runtime、正式交易 gate、去重、持久 intent、唯一選單和新空白目的地。**本 Skill、Owner 日常 Prompt、本地紀錄或 request JSON 都不是 runtime grant。** 不改 `gui_authorized_by_this_profile`、不偽造 consent／review、不重開 closed grant、不重置 ledger。未合法成立就停在 Save All 前。
6. 單次派送 → chooser 核對新空白目錄 → 觀察下載結束與穩定 → 張數／非空檔／逐檔 SHA-256／既有 ImageIO 完整像素解碼 → 寫後讀回。相同 SHA-256 的不同照片檔允許保留。日常完成標 `MANUAL_DIAGNOSTIC`、`formal_auto_verified=false`，不改正式 VERIFIED。
7. 返回列表繼續逐本對帳。只有覆蓋從頂到底、所有卡片已完成或明確排除、`PROTECTED_HISTORY=0`、`INCOMPLETE=0` 且 `UNKNOWN=0` 才可報日常列表簿記完整。`daily summary` 明示 `evidence_role=AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED`；它只投影 Agent 提交的證據參照與狀態，不是 sensor/tool PASS 或實機驗收。此結論不能升格正式 AUTO。

## 正式恢復基準

`RECOVERY_STRATEGY=ALBUM_LEVEL`；`PHOTO_LEVEL_RESUME=FUTURE_RESEARCH`。

- COMPLETED／FILES_VERIFIED／VERIFIED 與已人工完成相簿永不重下載；遺失或改動則停止核對，不能自動補下。
- 中斷保留全部部分檔案與 intent；明確 `UNKNOWN` outcome 不可由普通 outcome 改成 STOPPED／NOT_SENT，也禁止自動重送。只有 intent 尚無 outcome 時，才可記錄第一個實際已知結果。
- 前次派送狀態明確、已確認終止、取得**該群組／該本／該次**恢復授權後，才建立另一個新空白目錄及新 intent。原目錄不覆寫、不刪除，另通過有效 L2／交易 gate。
- 照片級／LINE 原生 resume 尚未實證；不把它當目前產品完成的前置條件。

## 回報

記錄 GUI／選單／Save All／取消的實際次數、下載與解碼張數、列表覆蓋、四種相簿狀態、受保護資料差異及唯一下一步；未實測標 `NOT_TESTED`。實機證據、原始檔名及家庭照片保留本機私有位置。更新當輪 `E2E測試報告.md`；人工觀察記 `OBSERVED`，不寫成工具或正式 AUTO PASS。
