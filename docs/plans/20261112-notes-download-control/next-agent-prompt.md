# 歷史參考：有界控制可觀察性診斷（非下載診斷）

下方 fenced Prompt 僅保留為歷史記錄，包含舊 HEAD 與當時「不下載」的診斷授權；不得作為日常啟動指示，也不得將其中舊 HEAD 當成現行版本 gate。記事本日常備份唯一入口是[使用手冊附錄 C：記事本正式 Prompt](../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt)。未來若另需診斷，須由 Owner 指定當次 candidate、範圍與前景交接；日常使用者不需攜帶開發檔，亦不新增另一份 Prompt。

```text
你是本次「有界診斷執行 Agent」，執行 TARGETED_DIAGNOSTIC。只診斷記事本下載控制的可觀察性，不下載、不修改產品，也不啟動其他正式角色。

專案：/Users/hsiaojohnny/dev/Line_backup
分支：feature/line-notes-media
基準 HEAD：23e98bcc718859cca5c583a9255262e9ce1f9794
交接文件：docs/plans/20261112-notes-download-control/issue-analysis.md

我已手動開啟同一篇記事本的媒體 viewer。本訊息授權你帶回 LINE 前景，執行下述非下載觀察，以及工具明確支援的一次無點擊移鼠。這不是下載授權。若前景中斷，停止 GUI 輸入。

開始前：
1. 核對 Git root、branch、HEAD、status，保留既有 dirty／untracked。基準不符時停止回報，不自行 checkout、reset 或修正。
2. 閱讀 AGENTS.md、記事本 Skill，以及 issue-analysis.md，尤其第 3、5、7 節。這是事故診斷，不是 Skill 文件審查或備份驗收。
3. 允許唯讀檢查報告明確引用的事發 AX、截圖、輸入紀錄與收據，以核對當前 viewer。不得廣搜私人資料、讀寫真實帳本或存取 LINE 內部資料庫。

已知事實：
五個媒體仍 PENDING，沒有 intent 或下載成果。五份事發 AX 的非視窗元素列相同，但首張截圖有標題列，後四張沒有同樣可見的標題列。這不證明 hover、LINE 缺陷或 Agent 違規。

執行順序：
1. 先讀當次原生 Mac Computer Use 工具文件，記錄可用的 AX、app-bound 截圖、局部桌面截圖、window frame、無點擊移鼠能力。不猜 API，不用其他執行器繞過限制。
2. 核對當前 viewer 與交接來源。固定目前這一個媒體，保存原始 AX、截圖、焦點、觀察範圍、幾何、時間及已知指標狀態；未知值寫 UNKNOWN。不要重新切換五張媒體。
3. 先不輸入，取得工具允許的 app-bound／最小局部畫面來源對照。記錄時間差及狀態漂移，不假裝它們是原子快照。只有一種來源時，將來源對照標 NOT_RUN。
4. 若仍未辨識控制，且工具明確支援無點擊移鼠、當次目標區域與映射可靠，才在非下載／分享控制的 viewer 區域移鼠一次，立即取得新觀察。保持同一媒體與幾何，記錄其他變項是否改變。無此能力就停止該方法，不以 click、drag、右鍵或快捷鍵模擬。
5. 看見候選控制也不要點擊。保存其 LINE／Notes 歸屬、作用依據、可見／可用狀態與定位證據，然後停止實驗。只有圖示、作用不明時仍為 UNKNOWN。

禁止：
不建 intent、不執行 notes 寫入命令、不下載、不開 chooser、不分享、不猜關閉或返回、不換其他頁面／列表、不修改 Skill／程式／歷史資料。不用重跑盤點、summary 或相同截圖充當新資訊。

停止：
前景中斷、身分／作用／映射不明、工具拒絕、來源變動、非預期 chooser 或不明派送，立即停止依賴該前提的動作。沿用同根因嘗試歷史；最多三次有證據嘗試，連續兩次沒有新資訊就停止，不因換 Session 重置。

交付：
- 新增 docs/plans/20261112-notes-download-control/control-observation-report.md；若已存在，使用新版本檔名，保留原件。
- 原始證據與過程紀錄放專案 .local/line-backup/tasks/ 下的新私有目錄；公開報告只保留遮蔽結論、技術引用及 hashes。
- 清楚區分直接觀察、推論、未知、工具能力不足。列出實際工具呼叫與回傳、變項對照、新取得的區辨證據及未執行項。
- 分別報告六項狀態；不得將控制出現寫成下載完成，也不得宣稱未實證的根因已確認。
- 最後明確告訴我：下一步應交給哪個角色、提供哪些精確文件、需要什麼授權。只建議，不自行派送。

允許將本次遮蔽診斷報告及來源 metadata 逐檔 add、commit、push 至目前分支。提交訊息須包含意圖、做了什麼、下一步的建議、驗證與結果；讀回 message body 並核對遠端精確 HEAD。不要提交私人原件、夾帶既有工作、merge 或 force-push。
```
