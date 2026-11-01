# 計畫草案 v1：Issue #50 記事本派送證據流程

本文件供另一位 Agent 審查，尚未取得計畫或產品 acceptance。角色為 Planner；不啟動實作、修復、實機重測或下一正式角色。Owner 已選定：先建立可靠證據流程，既有 UNKNOWN 無新證據就保留；沿用 CLI，補強 Skill、證據範本與判定案例。

## 1. 決策、目標與基線

- 目標：讓 Agent 清楚判斷什麼證據允許什麼動作，避免把控制定位、輸入回傳、App 接受、下載結果、檔案驗證與 completion 混為一談。成功須有一致的證據矩陣、操作順序、恢復規則與可審閱案例；不以解除既有阻塞作本次成功前提。
- 選定根因 H50-OBS-01：派送可能已發生，但缺少可歸屬且足以判定結果的證據，造成同一列表帳本停止新派送。原始點擊失敗的觸發因素仍 UNKNOWN。
- 分級 STANDARD：本次僅改操作與證據契約，不改程式、事件、公共介面或資料語意。保留人工啟動的計畫與首個實作切片 Simplicity Review；先前記事本功能任務的豁免不自動沿用。
- Repo 為 Line_backup；工作分支 feature/line-notes-media；規劃產品基線 `b3cf231b8159622c5532520cc8b178182c9d37b9`。起始工作樹與暫存區乾淨。既有 worktree、舊任務、私有證據及所有資料保留，不清理或搬移。
- 本次正式交付為 plan.md 與同目錄 handoff.md；原始診斷來源為 `.local/line-backup/tasks/20261101-issue50-high-reasoning-review/issue-analysis.md`。私有調查影格位於 `.local/line-backup/tasks/20261101-issue50-replan/video-cache/`，不提交 Git。

## 2. 研究依據與第一性原理

### 程式事實

在上述基線的 `src/line_backup_batch/notes.py`：

- 297–342：evidence 是非空 regular file 的內容定址保存與 bytes/hash 核對；不解析其 GUI 敘述真實性。
- 1984–2000：沒有 outcome 的結果為 None；已有 UNKNOWN outcome 的結果為 UNKNOWN。兩者需分開說明，均不能由缺少本機 marker 推論尚未派送。
- 2227–2247：同媒體 recovery 需 STOPPED／NOT_SENT、恢復授權及 evidence；其他未完成媒體亦阻擋新 intent。範圍是同一列表帳本，不是所有列表或整台電腦的 mutex。
- 2279–2312：第一筆 outcome 不可重寫；UNKNOWN 已可 reconcile 至 UNKNOWN／STOPPED／NOT_SENT／DOWNLOAD_FINISHED。終態後不可再調和。
- 2911–2913：只有 DOWNLOAD_FINISHED 才可 verify。

因此不新增退出轉移、不宣稱 mutex 死鎖，也不縮小 blocker。CLI 接受某結果只能證明結構及保存符合檢查，不能替 Agent 判斷外部證據是否足夠。

### 影片與 Issue 比對

Owner 提供的是 2026-10-26 示範影片，並非 2026-11-01 失敗當次。ffprobe 顯示約 124.256667 秒、2294×1490、H.264、單一影像串流、無音訊串流；SHA-256 前後一致，且與舊交接相符：

```text
54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6
```

本輪全片分段取樣並加密檢視關鍵區間，不宣稱逐一檢視全部 5504 個影格。下表採來源影格 PTS；初始等間隔重採樣預覽不作精確時間證據。影格中的現象記 OBSERVED，不代表當前 LINE E2E。

| 時間（秒，約值） | 錄影可見事實 | 可支持的規劃結論 |
|---|---|---|
| 5.97 → 6.22 | 同一照片 viewer 由未呈現工具列變成呈現工具列 | 開啟 viewer 不等於控制已可定位；無法判定是等待、移鼠或點擊觸發 |
| 31.38、40.40、46.39 | 照片儲存返回後有「下載完畢」提示 | 可作正面 UI 結果證據，仍需來源、目的地及檔案驗證 |
| 102.64 → 104.17 | 影片 viewer 先黑畫面與載入，後出現內容、時長及播放進度 | 載入中的缺少訊號不足以直接判 PHOTO |
| 105.69 → 106.70 | 下載圖示附近有另存提示，後出現 chooser | 控制定位與 App 階段性回應應分開保存 |
| 108.47 之後 | chooser 關閉後顯示「重播」，播放進度到結尾 | 這是播放狀態，不能當下載完成證據 |

已唯讀比對 Issue 原始截圖：成功第 2 項與失敗第 3 項的保存控制圖都未呈現工具列；成功第 2 項另有 chooser 圖。因此「保存圖沒有工具列」不足以區分成功與失敗，不支持原 click 瞬間必定未命中。成功第 1 項的控制圖則有工具列。截圖來源、範圍、時間與實際輸入必須分別核對，檔名本身不證明內容。

影片的照片與影片來自不同貼文，未建立同篇混合附件的完整覆蓋；也不能由示範片替 Issue 中 19 項重新分類。儲存期限、summary EAGAIN、錯誤 hash 引用、輸出覆寫及未完成盤點仍保留為其他未結案項，本次不修復或關閉整個 Issue。

### 官方最佳實務與能力界限

- [Apple AXUIElementPerformAction](https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction?language=objc)：modal callback 未及回應可能回傳 kAXErrorCannotComplete，並不必然代表 action 失敗；不能直接據此判 NOT_SENT。
- [Apple hit-test](https://developer.apple.com/documentation/applicationservices/1462077-axuielementcopyelementatposition?language=objc)：查詢當時螢幕位置的 AX object，受 z-order 影響。文件未提供截圖→hit-test→後續 click 的原子交易契約；保留其間 UI 改變風險是本案推論。
- [AWS timeout 與重試](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)及[冪等設計](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)：timeout 不排除副作用；安全重試依賴服務接受的 request ID 與去重契約。將此原則套用 GUI 是本案推論；本機 attempt ID、新目錄或增加等待不等於 LINE 冪等。

Apple 頁面直接 open 僅取得 JavaScript 外殼，正文以官方網域搜尋索引核對；AWS 正文直接讀取。沒有證明 LINE/CUA 支援 AXPress、hit-test、panel observer 或可排除副作用的 receipt。不得因官方 API 存在而要求 Agent 使用未提供能力、補猜時間或新增控制器。

## 3. 證據與允許行為矩陣

| 證據來源 | 能證明的命題 | 允許行為／仍未知時行為 |
|---|---|---|
| intent、空目錄、save_all_count=0 | 本機前置紀錄已建立 | 不能證明未派送；維持禁止重送 |
| 當次控制可見、作用與映射明確 | 具備單次輸入的定位依據 | 不推論已命中或 App 接受 |
| input API 成功／錯誤 | 工具回傳該結果 | 未有排除副作用保證時，不推 NOT_SENT |
| 可歸屬同 viewer／attempt 的 chooser | App 有階段性回應 | 核對精確目的地；尚不能 DOWNLOAD_FINISHED |
| timeout、畫面未變、空目錄、缺少 marker | 尚無足夠結果證據 | UNKNOWN；無新資訊不重複查證或追加相同調和 |
| 可歸屬的下載終結訊號與穩定結果檔 | 可進入檔案驗證 | DOWNLOAD_FINISHED → verify；不等於檔案完整或 completion 已保存 |
| 可歸屬、明確未派送／停止，且足以排除原操作稍後繼續的證據 | 可安全終結原 attempt | 才可 NOT_SENT／STOPPED；目前取得此證據的能力 UNKNOWN，不啟用猜測性的自動終態判定 |
| 完整檔案核驗與 completion 讀回 | 指定檔案與帳本完成條件成立 | 才計完成；仍不證明服務端原始位元相等或外部副本完整 |

Owner 無證據簽名、關閉 viewer、重開 App、換目錄或缺少本機 dispatch marker，都不能替代終態事實。既有 UNKNOWN 沒有可歸屬新證據就保留；未來流程改善不回填舊事實。

## 4. 最小實作範圍與首個切片

後續 Implementer 的可寫範圍：`.agents/skills/line-notes-agent-cua/SKILL.md`、該 Skill 的 references，以及本計畫目錄內的案例與角色交付文件。操作順序唯一維護在 download-and-ledger，GUI reference 維護定位與觀察，verification reference 維護結果與驗證界限；主 Skill 只摘要並連結，避免另造互相衝突的順序。

首個可驗證切片就是完整文件候選：

1. 在 intent 前預檢資格、來源及當次控制定位，避免明知無可靠目標仍建立 attempt；intent 保存讀回後，在輸入前再次核對當次目標。若此時失去定位，停止輸入並保留可能已派送的保護，不以 marker 缺席解鎖。
2. 將下載控制與 chooser 確認分開記錄，各自最多一次；保存真實工具回傳、觀察與結果。已派送但結果不明時，不重開或再點下載控制查證。
3. 主視窗來源未涵蓋 popup 時，僅用當次授權且工具文件支援的觀察範圍補查；圖中未呈現與 App 不存在該控制分開表述。不猜全域座標、不盲用相簿入口。
4. 補證據範本：三層 key、attempt、原目的地、畫面來源與範圍／尺寸、可取得的時間及時鐘來源、座標空間與映射、控制可見性、input 原始回傳、chooser 與檔案歸屬。缺值寫 UNKNOWN；引用 hash 由工具計算及核對，輸出用唯一檔名。只使用任務所需私有區域，不外傳影像。
5. 明確區分 intent 後無 outcome 與已有 UNKNOWN outcome：前者保存第一筆真實結果，後者用 reconcile 追加新證據。未收斂不得 verify、建新 attempt 或派送下一項；沒有新資訊就停止相同查證。
6. 補判定案例，每例包含前提、觀察、可支持命題、允許動作、禁止推論及所缺證據。範本沿用現有 --evidence FILE，不增 schema、parser 或語意感測宣稱。

保持 notes.py、狀態機、事件格式、CLI、列表級 blocker、相簿 daily／decoder 及既有測試不變。不新增 observer、GUI controller、結構化校驗器或 attempts 查詢；這些不是本次必要前提。文件契約的代價是無法自動驗證 evidence 語意，也不保證任意模糊結果後仍可自動前進。

## 5. 驗證、owner 與通過條件

| 檢查 | Owner | 通過證據 | 停止條件 |
|---|---|---|---|
| 計畫 simplicity | 人工啟動的 Simplicity Reviewer | 精確草案版本與有依據的審查報告 | 被拒絕或範圍有實質變更，交人決策 |
| 文件一致性、引用、案例 | Implementer | 逐項對照矩陣、可解析引用、git diff --check exit 0 | 規則衝突、引用缺失或需改公共介面 |
| 指定最小回歸 | Implementer | 下列命令的實際 exit code 與完整輸出摘要 | 任一失敗保留證據，不自行跨角色修復或豁免 |
| 首個文件候選 simplicity | 人工啟動的 Simplicity Reviewer | 精確候選與實作複雜度審查 | 拒絕就停止；沒有剩餘實作則不重開 Implementer |
| 真實 GUI 能力與後續結果 | Owner 另行指定的實機任務執行者 | 當次授權、前景、來源、逐次觀察與檔案證據 | 缺授權、前景中斷、能力不足或不明派送 |

Implementer 應執行專案指定最小回歸；不新增只比對文件字串的測試：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

判定案例至少涵蓋：控制檢查後隱藏；API error 但 chooser 出現；chooser 延遲或出處不明；晚到結果不可誤歸下一項；播放結束不可當下載完成；無 outcome 的 crash window；UNKNOWN 未收斂；有充分完成／停止證據與證據仍不足。案例驗規則完整性，不宣稱已模擬 LINE。

真實能力驗證與文件接受分層記錄。未來最小診斷先在 Owner 另行指定且有效交接的同一 viewer，觀察控制可見性、來源範圍與座標映射；不按下載、不建 intent、不操作舊 UNKNOWN。需要正常導覽或移鼠輸入時仍須有效任務及前景。真正下載、chooser 歸屬、混合附件與跨 Session 恢復另需具體授權；沒有當次證據維持 NOT_RUN。若需下載測試，不得在原列表 blocker 未解時派送，也不得藉另一列表或空帳冒充原問題已解。

## 6. 風險、停止與交接

不承諾 screenshot／輸入原子性、來源快照、OS 隔離、exactly-once 或外部 writer 不改動。不能以無限重查消除觀察與操作間的時間差。當平台能力不足時保留 UNKNOWN，而非降低證據標準。

以下任一情況停止並交人決策：需縮小 blocker、放寬禁止重送、改事件／公共介面、遷移或改寫帳本、讀 LINE 私有資料、另造輸入控制器、跨列表繞過、發現新根因或缺少必要能力。工具拒絕、寫入衝突、身分歧義、不明派送亦停止依賴該前提的動作。同一根因最多三次有證據嘗試、連續兩次無新資訊就停；原實機嘗試總額不完整，不能宣稱尚餘次數。

本輪實際做了 Git／來源唯讀核對、影片 metadata／hash／取樣影格、Issue 與截圖比對及官方資料研究，沒有重跑產品回歸、操作 LINE 或真實帳本。helper 只做同角色研究，不構成獨立 acceptance。派送參數指定模型不等於 provider 回報的後端身分或用量；不宣稱成本或 token 節省。

下一步由 Owner 在獨立主 Session 啟動計畫 Simplicity Review，攜帶本文件、handoff、原分析、精確文件提交與必要私有證據。審查通過後仍由人決定並啟動 Implementer；此交付不授予實作或 GUI 權限。不得合併 master、改寫歷史或自動關閉 Issue。

本文件落檔時的六狀態如下；Git 提交與遠端精確 HEAD 以實際交付結果為準：

```text
PRIMARY_OUTCOME_STATUS=PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=BLOCKED
REQUIRED_VERIFICATION_STATUS=BLOCKED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=BLOCKED
```

上述 BLOCKED 指原備份／Issue 尚未收斂；不抹除本輪已完成的規劃研究。計畫、文件檢查與 Git 交付不構成產品 PASS。
