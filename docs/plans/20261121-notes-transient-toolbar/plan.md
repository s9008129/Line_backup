# LINE 記事本短暫工具列與中斷接續修復計畫

## 目標與基準

以同一份正式記事本 Prompt 啟動。Agent 使用既有 Skill 和原生 CUA 核對目標。工具列在 intent 前可見、讀回 intent 後消失時，若已有合格的安全方法，Agent 自行顯示工具列一次。中斷後，Agent 依帳本判定接續原交易、隔離後補下載，或保留欠件。平常無需 Owner 判讀每個媒體。

基準是 `Line_backup` 的 `feature/line-notes-media`，HEAD `a54cf4c`，相對追蹤分支前進一筆。保留既有未追蹤的 `.playwright-mcp/`。這是 STANDARD 變更，派送涉及下載副作用，須有合成安全回歸並區分實機結果。

- 11/19 報告記錄 G 的兩次 `NOT_SENT` 與 Gis 的 `UNKNOWN`。三次都在可見觀察和 intent 讀回後找不到下載控制，未觀察到 chooser 或檔案。空 staging 只描述讀取當時。工具列消失的精確觸發、存活時間及下載命中均未量測。[TOCTOU 提報](../../問題提報單_記事本TOCTOU與reveal派送抽象錯置_20261119.md#4-時間線與證據判讀)
- `65ecad9` 已把正式的下載定位移到 intent 後，但 `checkDownloadReadiness` 的直達分支只檢查直接定位。B1 可在控制消失時使用事前已稽核的 reveal，現行可複製範本只教 Agent 在 intent 前選一個 branch。另有可離線核對的缺口，`persistReveal` 頂層只驗證 intent、操作種類及 ordinal，未用 fresh before 原件再驗證選取、作用區與映射。[B1](../../../.agents/skills/line-notes-agent-cua/references/gui-inventory.md#目標與下載控制就緒b1) [可執行範本](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md#intent-前下載就緒-gate)
- `3bb6fcb` 已實作 `UNKNOWN` 隔離、每媒體單次 v5 補下載及安全耗盡後續行。正式 Prompt 先要求「仍有跨 Session 一次自動額度」才可隔離，稍後又允許額度已用後將補下載的第二筆 `UNKNOWN` 隔離成 `RECOVERY_EXHAUSTED`。應在同一處明示兩條情形，並以對應 CLI phase 決定下一步。[正式 Prompt](../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt) [帳本實作](../../../src/line_backup_batch/notes.py)
- 11/20 另有下載 helper 在呼叫前因 `APP_WINDOW_CONTEXT_REQUIRED` 拒絕。現有就緒 gate 會提早攔缺 ID。現有證據只支持該次未取得 ID，平台能否取得合格 ID、當次是否可用及 hover 是否可用仍待查明。保留原 gate。[11/20 提報](../../../問題提報單.md)

## 切片 A：工具列消失後安全選路

1. 沿用 `checkDownloadReadiness`。intent 前分開評估直接定位和可獨立稽核的安全 reveal。可見時 DIRECT 與 REVEAL 可各自檢查一次，REVEAL 失敗不抹除合格的 DIRECT。隱藏時須 REVEAL 合格。即使同時合格也只寫一次 intent；保留成功的 REVEAL 結果供本輪使用，沒有 preflight input、capture、固定 slot、候選 request 或額度消耗。
2. 讀回 intent 後只取一次目前畫面。控制有效可定位就選 DIRECT；唯有在充分範圍中確定控制未見，而且同一 viewer、有效前景、選取與三層身分仍一致、無 chooser／活動下載／未決輸入、前次證據及額度均仍合格時，才選 REVEAL。控制有歧義、映射不足、漂移或已有下載呼叫／outcome 時停止，無法換路。只有可執行的已選 filmstrip 非播放安全邊緣進現行範本，沒有新 hover API、影像辨識或 native hit-test。
3. 既有 `persistReveal` 以參數 `preIntentReveal`（intent 前 REVEAL 的 READY 結果）、`beforeObservation`（intent 後最新原件）、`windowBinding`（該原件的 binding）加原 `request` 使用原 gate 做機械重核，再使用原固定 slot。沿用 `checkDownloadReadiness` 的 REVEAL 欄位，包含與該原件相符的截圖、AX 與定位引用、座標空間、有限安全區與嚴格內點。若缺少合格事前結果、兩次 observation 相同、window binding 改變、scope／候選 id／ordinal／budget 改變或最新欄位不足，拒絕且零 input。語意、身分連續性與新資訊真實性仍由 Agent 核對。輸入開始即耗原額度，每 attempt 最多一次 reveal，每媒體最多兩次，候選 2 仍須完整前次證據及足以改變方法或映射的新資訊。
4. 既有 reveal input → capture 繼續在同一 callback。呈現同一次 after 給 Agent，只保留必需的控制與映射判讀，接著直接呼叫既有 grounded helper。兩者之間不插入額外 CLI、固定等待或旁支查證，不用舊座標亦不在 after 失效後重拍再點。可執行 helper 不負責語意辨識，該次必要的模型判讀與檔案讀回仍有延遲。範本說明以 host 時間記錄可測的 capture 與 dispatch 邊界，未實測的壽命和點擊命中不作保證。
5. 下載呼叫及 chooser 最終確認各最多一次。工具錯誤、逾時或證據不完整時依原 attempt 調查結果；無正面證據就保持 `UNKNOWN`，無 outcome 時追加第一筆。只有可靠證據排除該次派送才可記 `NOT_SENT`。保留所有原始檔及既有下載驗證、版本、路徑和歷史。

## 切片 B：正式入口的自主接續

1. 以 `unresolved_attempts` 的 `has_outcome`、`last_result`、`attempt_phase` 及原事件辨識待辦。重新取得有效前景及 bind 後讀當次摘要。先依真實證據記第一筆 outcome，已記 `UNKNOWN` 只在新結果證據足夠時 reconcile。原交易已完成下載就用原 `download-check`，待命名走 `resume`。
2. 原結果仍不明時，由 Agent 自行核對同一項、原目的地、舊空 staging、有效前景、持久恢復資格，並排除 chooser、可歸屬活動下載、pending naming、檔案／身分異常及手動 restart。首筆可安全隔離的 `UNKNOWN` 依 `isolate` 的 `RECOVERY_SCAN_REQUIRED`，由目前綁定 Session 完成隔離後新普通掃描與目標細盤，B1 合格後僅一筆 v5 intent。若之後補下載又不明，在相同安全前提下隔離，按 `RECOVERY_EXHAUSTED` 留欠件並自動續做其餘合格項；該次隔離不需剩餘額度，也不建立第三筆自動 attempt。
3. Agent 以各自媒體的持久事件及時序判斷額度，不從列表總覽或其他媒體狀態猜測。摘要只提供既有欄位，不臆造數值。晚到檔留原 staging，未安全隔離的交易仍停止所有新派送。已證實 `STOPPED`／`NOT_SENT` 的精確恢復、restart／reattest、命名及資料異常維持各自現行 gate。前景中斷後須重新取得有效交接；接續的業務判斷由 Agent 依持久紀錄完成。

## 分工與驗證

兩個既有 Worker pane 平行處理。各自先核對 HEAD，回報實際命令、退出碼、修改路徑及未測事項。由 Leader 執行整合檢查。

| 負責 | 寫入範圍 | 合成通過證據 |
|---|---|---|
| Worker1 | `references/gui-inventory.md`、`references/evidence-template.md`（皆在記事本 Skill）、`tests/test_notes_input_helper.py` | 可見直達不耗 reveal。可見變隱藏時，合格事前與 fresh before 各核對一次，原 intent 下只有一次 reveal、一次 capture 與一次有根據的下載呼叫。預檢缺失、錯原件／window／候選、無安全內點及重複 slot 都不派送。既有 after 缺證、映射不符、timeout 及重送回歸維持通過。 |
| Worker2 | 記事本 `SKILL.md`、`references/download-and-ledger.md`、`docs/LINE相簿備份_使用手冊.md` | 沿用現有 phase、帳本與正式入口。對照 `test_notes_unknown_recovery.py` 的既有用例，確認第一筆結果、換 Session、新掃描、逐媒體一次額度、晚到、耗盡與其他項續行。修正文案矛盾，保留相簿段落。 |
| Leader | 本計畫、交接與結果證據 | 核對批准版本與實作差異、兩切片一致、所有 Notes 回歸、CLI help、相簿 records 回歸、差異空白檢查及精確 Git 發布。 |

首個可驗證切片為 A 的腳本與 mock CUA 測試。B 對照 `test_notes_unknown_recovery.py`。整合命令如下。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_input_helper.py'
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_unknown_recovery.py'
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
git diff --check
```

在 Reviewer 計畫通過前不分派實作。此輪不修改 Python CLI、帳本／schema、真實資料、相簿、驗證器、chooser 路徑或工具權限。禁止以未證實的 window id 取代現有安全門檻。缺少當次 LINE 授權與前景，E1（工具列壽命）、E2（intent 後 reveal）、E3（after → click 界限）、實際 chooser、落地、completion 及跨 Session 下載全部記 `NOT_RUN`。後續以相同日常 Prompt 和授權測試媒體驗證，先確認當次原生 CUA 所能提供的 window identity。若工具列在 Agent 必需判讀完成前仍消失，回收時序原件再決定下一個有界修法。
