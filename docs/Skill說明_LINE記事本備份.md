# LINE 記事本照片與影片備份 Skill 說明

> **這是技術背景與操作規則，不是日常啟動入口。** 第一次使用請先讀[白話使用手冊](LINE相簿備份_使用手冊.md)。

> **一句話：** 這是一份給 AI Agent 的獨立工作手冊，讓它在 macOS 上盤點你已打開的 LINE 記事本列表，只下載貼文內的照片與影片，以基本檔案檢查確認下載結果並保存可跨 Session 查詢的永久紀錄；中斷接續仍以當次紀錄與已驗證範圍為限。

## 1. 先認識這個 Skill

`line-notes-agent-cua` 是一套以 Skill 為核心的 Agent 工作流程，不是背景 App，也不是 LINE 官方匯出工具。Agent 讀取 Skill 後，使用 macOS Computer Use 觀察與操作 LINE；本專案的 `notes.py` 等工具只負責交易、去重、證據、檔案驗證與紀錄，不會自己點擊 LINE。

它和相簿備份看起來都在「下載媒體」，但實際上是兩條完全獨立的流程：

| 項目 | 相簿備份 | 記事本備份 |
|---|---|---|
| Skill | `line-album-agent-cua` | `line-notes-agent-cua` |
| 入口 | 一個群組相簿列表 | 一個記事本列表 |
| 下載單位 | 一本相簿使用 `儲存全部` | 一則貼文中的一個照片或影片 |
| 預設媒體區 | `backup/<相簿目錄>/` | `backup/記事本/` |
| 永久紀錄 | `backup-records/` | `notes-backup-records/` |

相簿與記事本的 Skill、Prompt、下載入口、目的地、狀態與帳本都不能互換。記事本不得把相簿的 `⋯ → 儲存全部`、選單、按鈕、chooser 或座標當成 fallback。

## 2. 真正的意圖

這個 Skill 的目標是完成**一個指定記事本列表內已知貼文的照片與影片備份**，同時維持三層身分與交易一致性：

1. 先完整盤點列表中的貼文，再辨識每篇貼文內的照片、影片與純文字貼文。
2. 一次只處理一個貼文／媒體 attempt，不平行派送下載。
3. 每個 attempt 先保存並讀回 intent、新空白目的地與禁止重送紀錄。
4. 記事本自己的下載控制與 chooser 最終確認各最多一次。
5. 日常以 `download-check` 檢查 magic MIME 與副檔名分類、非空穩定檔案、SHA-256、防覆寫及身分一致性；不做 ImageIO／ffmpeg 完整解碼。
6. 只有下載結果通過上述基本檢查才保存 completion，assurance 為 `DOWNLOAD_ONLY`；不證明來源原件或內容完整。舊完成事實不能被新 Session 覆寫。
7. 中斷、未知結果或本機檔案異常時，保留原檔與證據，不以重下或改紀錄解鎖。

它追求的是**可解釋、可恢復、資料不被重複派送的工作流程**，不是「看到圖片就全部按下去」。

## 3. 會備份與不會備份的內容

### 會備份

- 貼文內的照片：下載後依 magic MIME 與副檔名分類，並檢查非空、穩定性與 SHA-256。
- 貼文內的影片：依下載檔案 magic MIME 與副檔名分類；不要求檢查影像串流或完整解碼。
- 純文字貼文的「目前沒有照片或影片」事實：只有在 Skill 的盤點證據足以確認時，才記在貼文層 `NO_MEDIA`，不做下載 attempt。若貼文只有 PDF／Word 等非備份附件，Agent 必須另外說明附件不在範圍，不能把整篇描述成純文字。

### 不會備份

- 貼文的文字本身。
- 留言、回覆、貼圖、表情符號與連結。
- PDF、Word、網頁文件、壓縮檔或其他非照片／影片附件。
- 其他記事本列表或相簿中的內容。

`NO_MEDIA` 是**貼文層標記**，不是第七類下載完成。看到它不代表影片或照片成功下載；它只表示這篇貼文在當次盤點中沒有照片或影片。若貼文只有非照片／影片附件，請把附件種類另列為「不在備份範圍」，不要把它誤寫成純文字貼文。

## 4. 適合與不適合的情況

### 適合

- 你使用 macOS，且 Agent 具備原生 Computer Use、螢幕擷取與輔助使用能力。
- 你已人工打開**一個記事本列表**，並在任務期間把 LINE 前景交給 Agent。
- 你要備份貼文中的照片與影片，且接受留言、貼圖與文件附件不在範圍內。
- 你需要跨 Session 找回完成紀錄，或希望 Agent 依紀錄嘗試接續中斷的工作。

### 不適合

- 想匯出整個 LINE 帳號、聊天室或所有附件。
- 想下載記事本中的 PDF、Word、網頁文件或其他檔案。
- 只打開單一貼文中的單張圖片，卻期待 Agent 自動知道整個列表。
- 沒有有效前景交接，或希望 Agent 在背景自行監看 LINE。
- 想用相簿流程代替記事本流程，或把兩邊的 ledger 混在一起。

## 5. 你、Agent 與工具的分工

| 角色 | 白話工作 |
|---|---|
| 你 | 打開正確的單一記事本列表；提交正式 Prompt，授權本次備份並交接前景。 |
| Agent | 讀 Skill、核對入口、完整盤點、選擇下一個合格媒體、操作 LINE、保存證據與回報。 |
| Computer Use | 觀察 AX／畫面、捲動、開啟貼文、操作下載控制與 chooser。 |
| `notes.py` | 保存列表、貼文、媒體、intent、outcome、completion 與恢復狀態；不操作 LINE。 |
| `notes_evidence.py` | 建立不可覆寫的證據 bundle，核對證據 bytes、hash 與 context。 |
| `notes_capture.py` | 包裝一次 notes CLI child 呼叫，以暫存檔、fsync、獨占連結與讀回方式保存 stdout、stderr、退出碼與 signal；不保存也不證明 GUI 輸入。 |
| `download-check` | 日常檢查下載結果的 MIME／suffix 分類、穩定性、SHA-256、防覆寫與身分。 |

你不需要手填 UUID、`list_key`、內部 JSON、貼文序號或 attempt id。Agent 會從當次畫面與工具輸出自行整理，並保存真實依據。

## 6. 核心技術與工具

### 原生 macOS Computer Use

Agent 以當次 AX 與畫面觀察確認入口、列表、貼文、媒體 viewer、下載控制與 chooser。每次輸入前都要重新定位；視窗移動、縮放、換頁、popup 重開或來源內容改變，都可能讓舊座標與舊 mapping 失效。

截圖與 AX 都只是觀察來源。若缺少某個 popup、按鈕標籤或可見元素，不能直接推論「沒有下載授權」或「沒有下載成功」；必須依 Skill 的證據規則區分「沒看到」、「可能已送出」與「已完成」。

### `notes.py`：獨立記事本帳本

記事本使用自己的 CLI 與永久紀錄，主要流程包括：

- `lists`、`memory`：查全部記事本帳本與單一帳本摘要。
- `list-key`、`init`：在沒有既有帳本時，先建立一致的列表身分。
- `bind`：綁定當次有效前景與 Session。
- `scan`、`page`：從列表頂端到底端盤點，保存每頁覆蓋。
- `post`、`media`：保存貼文層清單、`NO_MEDIA`、媒體種類與來源順序。
- `intent`：在下載前保存 attempt、新空白暫存目錄與禁止重送狀態。
- `outcome`：保存第一個可觀察到的下載結果。
- `reconcile`：在已有 `outcome=UNKNOWN` 時，追加新證據來釐清。
- `download-check`：日常對具備明確下載終結結果的 attempt 做基本檔案檢查與發布。舊 `verify` 僅供 legacy 相容。若 `summary`／`resume` 保留 legacy `VERIFY_REQUIRED` 標記，日常按待 `download-check` 處理，不啟動舊 `verify` 或來源種類取證。
- `resume`：接續中斷的命名／發布交易，不會重新下載。
- `restart`、`reattest`：處理精確範圍的受控重建與 list directory 裝置轉接。
- `summary`：投影目前狀態；它不是 GUI 或 E2E 的替代品。

所有成功輸出的 JSON 都包含 `dispatch_authorized=false`。這個欄位只是「CLI 沒有授予 GUI 權限」的簿記聲明，不是你的同意、工具操作成功、下載 PASS 或獨立驗收。

### 證據與交易技術

- 事件以追加方式保存，不靠覆寫最後一筆來說明歷史。
- v2 evidence bundle 會保存 context、子 blob、bytes 與 SHA-256，並拒絕父／子漂移。
- 檔案寫入使用暫存檔、`O_EXCL`、`fsync`、獨占連結／原子替換與讀回。
- 發布使用暫名到正式名稱的受控交易；中斷時用 `resume` 接續同一交易。
- 本機帳本有鎖定與一致性檢查；這能降低競態與部分寫入風險，但不是 OS sandbox、網路隔離或「點擊恰好一次」的硬體保證。

### 日常下載檢查

`download-check --records-root ... --session-id ... --attempt-id ...` 依檔案 magic MIME 與 suffix 分類，檢查非空穩定 SHA-256、防覆寫及身分一致性。明確為 `text/plain`、`text/html`、`application/pdf`、`application/zip` 時追加 exclusion、保留 staging、不寫 completion，也不宣稱來源原件不是媒體；未知 MIME、`application/octet-stream` 或 MIME／suffix 不符時保持 pending 並拒絕完成。其他通過項的 assurance 為 `DOWNLOAD_ONLY`；不執行 ImageIO／ffmpeg 完整解碼，不證明來源原件或內容完整。舊 `verify` 僅供既有嚴格帳本相容，不是日常入口。若 `summary`／`resume` 保留 legacy `VERIFY_REQUIRED` 標記，日常按待 `download-check` 處理，不啟動舊 `verify` 或來源種類取證。

### 操作邊界

Agent 只下載，不播放／暫停、拖時間、調倍速、檢視內容或為種類取證；不可點媒體內容切換播放控制。可移入游標或使用明確工具列控制顯示下載工具列。真正新媒體種類未知時可標 `identity.kind=UNCLASSIFIED`；既有媒體沿用原 identity 與 key，不因種類未明改 key。

### 證據 bundle 與 capture

`notes_evidence.py` 只核對 bundle 結構、context、bytes 與 hash，不替 Agent 判斷畫面語意或真實性。`notes_capture.py` 保存 child CLI 的 stdout、stderr、退出碼與 signal，讓「下載控制已派送但結果未知」不會被安靜地當成沒發生；capture receipt 不是 GUI／Computer Use 原始回傳，也不證明實際點擊或輸入。

## 7. 三層身分：列表 → 貼文 → 媒體

記事本備份最重要的安全觀念是「三層身分」：

```text
列表身分
  └─ 貼文身分（日期、卡片位置、相鄰貼文、內容脈絡）
       └─ 媒體身分（所屬貼文、媒體順序、縮圖、viewer 脈絡）
```

以下任何一項都不能單獨認領另一個項目：

- 記事本或群組的中文名稱。
- 日期、張數、總數或序號。
- 相同檔名、相同外觀或相同內容 hash。
- 目前畫面上剛好看到的一張縮圖。

即使兩個檔案內容相同，也可能是不同貼文、不同媒體或不同歷史來源；不能自動跨列表或跨貼文去重。列表重排、貼文編輯或新增媒體時，舊完成事實仍保留，只追加可唯一辨識的新項目。局部貼文有歧義時，保護該篇並繼續其他已核對項；如果列表覆蓋或身分整體不明，才停止整份新派送。

## 8. 完整流程

```text
你打開一個記事本列表並提交正式 Prompt
        ↓
Agent 查全部記事本帳本、active-notes-task 與相符記憶
        ↓
核對入口與有效前景 → bind
        ↓
scan start → 從頂端到底端頁面盤點 → page 雙向對帳 → scan finish
        ↓
逐篇 post／media 盤點，純文字記 NO_MEDIA
        ↓
每個合格媒體：intent → 新空白 staging → 下載控制一次 → chooser 確認一次
        ↓
第一筆 outcome → UNKNOWN 先 reconcile → 只有 DOWNLOAD_FINISHED 才 download-check
        ↓
基本檢查、發布、completion 讀回 → 下一項 → 最終 summary 與畫面交叉對帳
```

### 步驟 1：找回前次任務

先跑 `lists` 查全部記事本帳本，再讀 `active-notes-task.json` 與相符帳本。索引只登錄位置，active 檔只是最近任務書籤，不能取代完整歷史。缺帳本、索引毀損或出現多個列表候選時，不得開空帳或猜配。

### 步驟 2：核對入口並綁定前景

入口必須是記事本列表，不是相簿、聊天室、單一貼文 viewer 或不相關畫面。Agent 先用當次 AX／畫面確認，再在有效前景下 `bind`。入口未確認前不捲動、不盤點、不下載。

### 步驟 3：完整盤點列表

Agent 從頂端到底端，以有序重疊與來源逐卡紀錄避免漏篇。`page` 前要先完成來源卡片與 page rows 的雙向對帳；讀回不一致時停止後續 page、scan finish 與新下載，不用 correction 偷偷改掉 page 成員。

### 步驟 4：逐篇辨識貼文與媒體

每篇貼文要交叉核對卡片位置、日期、相鄰貼文、媒體排列與 viewer 脈絡。純文字貼文記 `NO_MEDIA`；真正新媒體種類未知時可用 `identity.kind=UNCLASSIFIED`；既有媒體沿用原 identity 與 key，不因種類未明改 key。Agent 不播放／暫停、拖時間、調倍速、檢視內容或為種類取證；可移入游標或使用明確工具列控制顯示下載工具列，不點媒體內容切換播放控制。

### 步驟 5：一次只做一個 attempt

每個合格媒體都先建立並讀回 intent。intent 會保存 attempt、暫存目的地與「可能已派送、禁止重送」的初始狀態；其中的 `save_all_count=0` 只是 ledger 初始值，不是實際點擊次數。讀回後要在輸入前再次定位同一列表、貼文、媒體、viewer 與控制項。

### 步驟 6：下載控制與 chooser

每個 attempt 的記事本下載控制最多呼叫一次；chooser 最終確認也最多一次，兩者是分開的計數。失敗、逾時、呼叫成功但結果不明，全部算使用過一次；重開選單、移動滑鼠或重新輸入路徑都不會把次數歸零。若 UI 顯示 `Save All`，必須先證明它是這個記事本自己的控制，不能把相簿的 `⋯ → 儲存全部`、舊按鈕或舊座標拿來沿用。

chooser 可能延遲出現。只有視窗／process、來源 viewer 與 attempt 都能唯一歸屬，而且 PathTextField、where／current directory 與 intent staging 三者一致指向新空白目錄時，才可以確認一次。`Go to Folder` 裡的預填字串只證明欄位文字，不證明目前資料夾或下載目的地。

### 步驟 7：結果、未知與驗證

先查該 attempt 是否已有 outcome，不要從 `memory` 顯示的 `UNKNOWN` 猜測。沒有 outcome 時只記錄一次第一筆真實結果，且第一筆結果不能任意改寫；若只有逾時、畫面沒變、進度未結束或歸屬不足，就記 `UNKNOWN`。

只有已經有 `outcome=UNKNOWN`，且取得新證據時，才使用 `reconcile`。`reconcile` 不是重送，也不是把未知硬改成成功。只有最終結果是 `DOWNLOAD_FINISHED`，才可進入日常 `download-check`；未收斂前不得 download-check、建立新 intent、重下或派下一項。舊 `verify` 與種類更正命令僅供 legacy 相容，不屬日常步驟。



### 步驟 8：發布、completion 與下一項

`download-check --records-root ... --session-id ... --attempt-id ...` 會核對 magic MIME 與 suffix 分類、非空穩定檔案、SHA-256、防覆寫及身分一致性；通過後保存 completion，assurance 為 `DOWNLOAD_ONLY`。命名交易中斷時用 `resume` 接續；`resume` 不會觸發下載。完成後重新觀察原貼文／列表，再定位下一個合格項。

### 步驟 9：最終對帳

先重讀本輪來源原件，核對各 page 讀回、貼文總數、`NO_MEDIA` 篇數、六類媒體狀態與下載排程。`summary` 只能輔助核對簿記，不能取代當次 GUI 覆蓋。只有覆蓋完整且沒有未解的 dispatch blocker，才能說已知媒體都已處理；仍要另列 `PROTECTED_HISTORY`、`LOCAL_MISSING`、來源到期或其他未解項。

## 9. 下載、結果與驗證的關鍵字

| 名稱 | 白話意思 | 重要限制 |
|---|---|---|
| `intent` | 下載前的交易預告。 | 寫入後就按「可能已派送」對待；不是 GUI 授權。 |
| `outcome` | 第一個觀察到的下載結果。 | 同一 attempt 不任意改寫；不確定就記 `UNKNOWN`。 |
| `reconcile` | 用新證據釐清既有 UNKNOWN。 | 只處理已存在的 UNKNOWN，不是重送。 |
| `download-check` | 下載完成後檢查檔案並保存 completion。 | 基本檢查；不作完整解碼或來源種類證明。 |
| `DOWNLOAD_FINISHED` | 有可歸屬的下載終結結果。 | 只代表可以進入 `download-check`，還不代表檔案完成。 |
| `verify` | 舊流程嚴格驗證。 | 僅 legacy 相容，不是日常命令。 |
| `resume` | 接續中斷的命名／發布交易。 | 不會重新下載。 |
| `UNKNOWN` | 可能已送出，但無法確認成功或失敗。 | 不重送、不建新 attempt、不換入口解鎖。 |

## 10. 六類狀態與本機可用性

### 六類業務狀態

| 狀態 | 白話意思 |
|---|---|
| `COMPLETED` | 下載、檔案驗證、發布與 completion 讀回都成立。 |
| `EXCLUDED` | 已依證據明確排除。 |
| `PENDING` | 已盤點，尚未完成處理。 |
| `PREVIOUSLY_INCOMPLETE` | 以前開始但沒有完成，需要受控恢復。 |
| `UNKNOWN` | 可能已派送，結果尚未確認。 |
| `PROTECTED_HISTORY` | 舊資料證據不足或來源不明，先保護，不升格成完成。 |

純文字貼文的 `NO_MEDIA` 不屬於這六類下載狀態，也不是第七類。

### 本機可用性

- `VERIFIED_PRESENT`：本機檔案目前存在，且與對應完成紀錄的檔名、大小、時間戳與 hash 相符；這是可用性核對，不是本次重新下載或重新執行一次完整解碼驗證。
- `LOCAL_MISSING`：完成紀錄仍在，但整篇本機目錄目前不見；保留完成、禁止重下，外部副本未經驗證。
- `LOCAL_CHANGED`：目錄還在，但有缺檔、非屬合格環境附屬項的額外檔、hash／身分漂移或 symlink；保護原檔，停止未經確認的新派送。目錄讀取權限異常或只能看到部分內容時，也不能自動當成整篇目錄不見。
- `NOT_APPLICABLE`：這項沒有可套用的本機媒體狀態。

本機可用性不是第七類業務狀態。`UNKNOWN`、活動下載與未完成命名交易，不會因為照片區不見、換新目錄或使用者說「繼續」而自動解除。

## 11. 什麼是精確 restart，什麼不是普通重試

當工具回報 `RESTART_REQUIRED`／`OPEN_BATCH` 時，Agent 不能直接重下。它必須先做 `restart preview`，用白話列出：

- 精確的列表、貼文與媒體 scope。
- 哪個 attempt、generation 與版本策略會受影響。
- 舊位置、新 `versions/gNNNNNNNN/` 目錄與需要的額外空間。
- 哪些項目要重建、哪些保留；`UNKNOWN` 與 `LOCAL_MISSING` 等未解項要獨立列出，不能被包進重建 scope 假裝已解決。

`restart preview` 會區分 `RESTART_REQUIRED`（需要新的精確確認）、`OPEN_BATCH`（已有未完成批次）與 `NO_RESTART_REQUIRED`（不需要建立批次）。只有新的待確認批次才需要你對精確 scope 明示同意；已完成項只作 scope 脈絡列出，不代表會重新下載。

只有你對這份精確 scope 明示同意後，才執行 `restart confirm`；一般「繼續」、沉默、逾時或原本的日常 Prompt 都不算批次同意。confirm 後必須完成新的完整 `scan start --recovery`，才能逐項 `intent --restart-id`。舊 confirmation、candidate、activation、completion 與 UNKNOWN 歷史全部保留，新 attempt 使用新的空白 staging。`restart verify` 會把候選檔複製到新的版本目錄，不是用改名或 hard link 假裝完成；日常以 `restart resume --download-only` 執行候選基本檢查；scope 內若出現明確非媒體，回報 `RESTART_SCOPE_NON_MEDIA` 並停止，不自動改 scope。全部候選通過後才做 activation，activation 不會按 GUI、下載或重送。

這不是無限重送：scope、身分、目的地或版本策略改變就要重新預覽與確認。`LOCAL_MISSING`、scope 外的異常、`EXCLUDED` 與 `PROTECTED_HISTORY` 不會因批次同意而解除。

### list directory 裝置轉接（reattest）

若既有 `OPEN_BATCH` 的 list directory 路徑與 inode 相同，但 device 改變，Agent 可先做唯讀的 `reattest preview`。`NO_CHANGE` 表示不需要確認；只有 `CONFIRMATION_REQUIRED`、完整 witness、舊／新 binding、scope 剩餘風險都可解釋，且你對該 preview 另行明示同意時，才可 `reattest confirm`。成功後仍要完成新的完整 recovery scan。每個帳本最多一次；再次漂移、`REATTEST_CURRENT_BINDING_CHANGED` 或任何拒絕就停止，不換目的地或重送。

## 12. 退出碼與錯誤處理

| 退出碼 | 意思 | 你應該怎麼做 |
|---|---|---|
| `0` | 命令成功完成。 | 仍要讀輸出，確認是否只是簿記成功。 |
| `2` | argparse／必填參數錯誤。 | 修正輸入；不要把它當成下載結果。 |
| `4` | 已列出的業務拒絕，例如保護、重送或證據不符。 | 依 Skill 查證；不要繞過拒絕。 |
| `70` | 未預期內部錯誤，輸出含 `status=INTERNAL_ERROR`、`reason=UNEXPECTED_EXCEPTION`、`dispatch_authorized=false`。 | **停止**，保留命令輸出、畫面與紀錄，交給維護者；不重送、不改 ledger、不建新 attempt、不換目的地。 |

`dispatch_authorized=false` 不是 GUI grant；它只說明 CLI 沒有授予操作權限。退出碼 70 更不是可重試的業務拒絕。

目前實作仍有一項待修落差：部分 `OSError`／`SubprocessError`（例如檔案系統或子程序失敗）可能也被包成退出碼 4。若輸出沒有指出明確的已列業務拒絕，請按未預期錯誤停止並交給維護者，不要因為看到 4 就重試。

`evidence-audit` 若回報 `integrity_ok=false`，會以 exit 4 結束並設定 `business_projection_omitted=true`，不能使用它的局部業務結果。`notes_capture` 是保存 child 命令輸出的 wrapper，不是 GUI 授權；capture 自身失敗通常是 70，child 正常結束時則保留 child 的退出碼。

## 13. 永久紀錄與檔案位置

| 位置 | 用途 | 注意事項 |
|---|---|---|
| `backup/記事本/` 底下的列表／貼文子目錄 | 照片與影片預設媒體區。 | `backup/` 是相簿與記事本共用的父目錄，不要整包刪除；只在確認某個列表／貼文子目錄已有可讀副本後整理它，且不要在交易中移動。 |
| `notes-backup-records/<列表識別>/` | 列表、貼文、媒體、intent、outcome、completion 與恢復事件。 | **不要刪除、手改或搬到相簿帳本。** |
| `.local/line-backup/active-notes-task.json` | 最近記事本任務書籤。 | 只協助定位，不是唯一歷史。 |
| 專案私有證據區 | 工具原始回傳、截圖／AX 引用與驗證證據。 | 保留必要證據；不要用範例或推測補造。 |

舊完成事實只追加、不覆寫。若你刪除 `backup/記事本/` 的媒體，`notes-backup-records/` 仍會保留完成與禁止重下的依據；這不代表外部硬碟副本已被驗證。

## 14. 驗證邊界與目前證據

請分開理解四個層次：

1. **GUI 觀察**：Agent 當次看到什麼、操作什麼；真人觀察應標 `OBSERVED`。
2. **notes CLI 簿記**：事件與 summary 投影一致，不代表 LINE UI 已完成。
3. **日常檔案檢查**：`download-check` 只證明指定本機下載結果通過 magic MIME／suffix、非空穩定、SHA-256、防覆寫及身分檢查；ImageIO／ffmpeg 完整解碼只適用舊 `verify` 相容流程。
4. **真實 E2E**：只覆蓋當次環境、版本、Session 與情境，不能外推到所有使用者。

目前已知：個別照片與小型照片列表有完成紀錄；但完整列表 GUI E2E、影片、混合照片／影片附件、即時 chooser、跨 Session 接續與恢復仍維持 `NOT_RUN`。合成 fixture 測試 PASS 只證明實作在該測試矩陣下的簿記與檔案行為，不能補成真實 LINE GUI PASS。

`summary` 的 `all_known_media_complete=true` 只表示已知貼文／媒體的簿記與覆蓋資料一致，沒有 dispatch blocker；它不是 GUI、個別檔案或完整 E2E 的獨立驗收。`LOCAL_MISSING` 仍可與這項 true 並存；`LOCAL_CHANGED` 或個別 `PROTECTED_HISTORY` 會使整體不能宣稱全部完成。

### 已知實作落差（待程式修正）

- **active candidate 單檔消失：** 精確 restart 的版本目錄仍存在、但 active candidate 檔案消失時，目前工具可能把該項投影成 `LOCAL_MISSING`，而 `all_known_media_complete` 仍可能為 true。這不代表整篇目錄安全缺席；遇到時必須停止、保留現場與證據，交由維護者處理，不能重下或宣稱全部檔案存在。
- **退出碼分類：** 如上一節所述，部分系統／子程序錯誤可能被包成 4；沒有明確業務拒絕原因時，按未預期錯誤處理。
- **restart preview 的保留清單：** 目前 preview 未必會把所有 `LOCAL_MISSING` 自動列進 scope；Agent 必須另外從 summary／事件列出，並讓它們保持保留狀態，不得因批次同意而解鎖。

## 15. 安全邊界

這個 Skill 不會因為你提交一次備份 Prompt，就取得其他操作權限。正常流程不包含：

- 發訊息、刪除貼文、分享內容或修改 LINE 設定。
- 備份留言、貼圖、連結、PDF、Word、網頁文件或其他附件。
- 覆寫舊照片／影片、改寫既有完成或把 UNKNOWN 清空。
- 操作其他列表、相簿流程或其他群組。
- 修改產品程式、Skill、測試或紀錄規則來繞過阻塞。

Agent 遇到工具拒絕、身分歧義、證據漂移、寫入衝突或不明派送時，應停止依賴該前提的動作，保留原狀並回報；不能換入口、換資料夾或重貼 Prompt 當作解鎖。

## 16. 什麼時候應該停止並交還給你

- 列表／貼文／媒體身分或完整覆蓋無法確認。
- `UNKNOWN`、活動下載或未完成命名交易尚未收斂。
- chooser 無法唯一歸屬，或目的地不是本 attempt 的新空白目錄。
- 本機目錄有缺檔、非屬合格環境附屬項的額外檔、hash／身分漂移或 symlink。
- legacy strict verifier 的影片工具版本、binary hash、影像串流或完整解碼不符。
- 工具退出碼為 70，或出現 `INTERNAL_ERROR`／`UNEXPECTED_EXCEPTION`。
- Agent 想使用相簿的 `儲存全部`、舊座標、第二個 chooser 或其他列表的歷史來繞過阻塞。

停止並保留證據，是這個 Skill 的正式安全行為，不是流程失敗。

## 17. 相關文件

- [LINE 相簿與記事本備份使用手冊](LINE相簿備份_使用手冊.md)：日常入口與正式 Prompt。
- [記事本 Skill 的完整操作規則](../.agents/skills/line-notes-agent-cua/SKILL.md)：Agent 的正式工作規格。
- [下載與 ledger](../.agents/skills/line-notes-agent-cua/references/download-and-ledger.md)：CLI、intent、下載控制與 chooser。
- [驗證與恢復](../.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md)：六類狀態、本機可用性與 restart。
- [GUI 導覽與盤點](../.agents/skills/line-notes-agent-cua/references/gui-inventory.md)：三層身分與列表覆蓋。
- [日常備份的結構化記憶](結構化備份記憶.md)：相簿永久紀錄的背景；記事本帳本仍與它分開。
