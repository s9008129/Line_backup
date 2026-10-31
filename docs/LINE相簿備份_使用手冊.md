# 用 Prompt 啟動 LINE 相簿與記事本備份

本手冊有兩條互相獨立的日常流程。第 1～4 節是 LINE 相簿照片備份；第 5 節是 LINE 記事本貼文內照片與影片備份。Owner 每次只選其中一條，先開好正確頁面，再提交該流程的正式 Prompt。相簿與記事本的授權、Skill、工具、目的地、帳本及操作入口不互通，也不得用一條流程的狀態解鎖另一條流程。

本次記事本新功能只在 `feature/line-notes-media` 開發。Owner 實機測試通過前不合併 `master`，既有主分支相簿流程維持不變。真實記事本 GUI、混合照片／影片 chooser、跨 Session 接續與恢復目前均為 `NOT_RUN`，不得把文件或離線測試寫成實機 PASS。

先在具有原生 Mac Computer Use 的本專案 Agent Session 中，人工登入 LINE 並開好指定相簿列表，再貼上下方 Prompt；提交即完成正式授權與當次前景交接。Agent 應先確認入口、自行查舊進度、盤點、逐本執行「儲存全部」、驗證及保存紀錄，直到這份列表的合格相簿完成；不需要逐本下令或在盤點後再說「開始下載」。

相簿章節的共用 Prompt 用於日常正式下載。Owner 親自試用、確認下載結果，也使用同一份 Prompt；不必啟動 v4.9.0 Harness 的 Independent Acceptance、選擇 Git 候選或先跑開發測試。正式角色驗收只適用另行明示交辦的開發驗收，不是日常備份的前置流程。

`Line_backup` 是唯一核心目錄。照片預設在 `backup/`，永久紀錄分開放 `backup-records/<列表 UUID>/`；Agent 自行查全部帳本，不只記得最近一組。開發歷程留在 Git，不是備份記憶，也不要求保留外層舊資料。

## 1. 填寫 Prompt

| 欄位 | 怎麼填 |
|---|---|
| `BACKUP_ROOT` | 可留空，預設使用目前專案根目錄的 `backup/`；要用其他專案內位置時填完整絕對路徑。此欄只指定照片區，永久紀錄由 Agent 自動管理。 |
| `EXCLUSIONS` | 沒有新增排除就填 `[]`；需要排除時，描述相簿日期、張數及可區分的封面／內容，歧義由 Agent 再核對。`[]` 不解除既有排除，也不允許重下已完成相簿。 |

本手冊以 `$PROJECT` 代表本專案根目錄；相簿預設照片位置是 `$PROJECT/backup/`，記事本預設是 `$PROJECT/backup/記事本/`。不需要提供群組中文名稱、座標、API、UUID 或內部 JSON。Agent 核對當前列表與永久帳本後使用此位置；照片區刪除後，下次可再建立新一批目的地，舊完成紀錄保留。整個專案搬移若出現舊路徑／身分歧義，才先安全對帳，不手改歷史或重新下載。

### 可直接貼用的啟動 Prompt

首次與下次啟動都使用這一份 Prompt。提交它代表授權所述備份工作；只討論或修改範本不代表執行。

```text
BACKUP_ROOT=
EXCLUSIONS=[]

【日常正式備份與當次交接】
請使用本專案 $line-album-agent-cua 及現有工具，實際執行 LINE 相簿備份。
本次是日常下載任務；我會自行確認結果，不啟動 Harness 的
Independent Acceptance 或其他開發角色，也不以 Git 候選版本、
開發測試或獨立驗收報告作為開始下載的前置條件。
我已人工開好指定相簿列表；提交本訊息即交出前景。
請先核對實際畫面與列表身分，再開始操作。

【目標與範圍】
目標是將這一個連續列表中所有合格相簿的全部照片備份到本機。
已完成的依永久紀錄保留並跳過，即使整本本機照片已搬走；
仍在本機但部分缺檔或異常的依 Skill 保護，不重下補帳。
其餘未備份、未排除且符合資格的相簿逐本下載，不操作其他列表。
BACKUP_ROOT 留空時使用目前專案根目錄的 backup/；
其他位置僅限工具支援的專案內絕對路徑。
EXCLUSIONS=[] 表示沒有新增排除，不解除既有排除或歷史保護。
每次啟動自行查全部永久帳本，再核對當前列表與本機照片可用性，
不把缺紀錄或照片區刪除當成空帳；不要求外接硬碟在線或歸檔登記。

【一次授權與自主調整】
我授權你在上述範圍內自主觀察、導覽、盤點、補接缺頁、
重新定位，依 Skill 執行「⋯ → 儲存全部」、選擇本本新空白
目的地、下載、持久命名、本機驗證及保存進度。
觀察包含唯讀 AX、LINE／popup 截圖及相關影像的本機離線 OCR。
必要且平台允許時，可擷取當前桌面補看 LINE popup；可能暫含
其他可見視窗，僅保留本任務所需區域於專案私有證據，不主動
開啟或辨識其他應用內容，不上傳外部 OCR／雲端服務。
可依當次畫面與工具文件調整已支援的方法，不必逐本請示，
也不要在盤點完成後等待我另下開始指令。

本次亦授權相簿級恢復：確認先前已停止且未完成時，
保留原檔，依 Skill 在另一個新空白目錄恢復。
已完成的跳過；仍在下載的觀察；待驗證的先驗證；
派送結果未知的不重送。

【邊界與例外】
只使用 Skill 支援的下載入口。不得發訊息、刪除、分享、
覆寫舊照片、改寫既有完成或 UNKNOWN 事實、跨列表操作，
也不得現場修改產品程式或紀錄規則以繞過拒絕。
本任務不包含 commit、push、merge 或雲端 CI。

執行期間我會保持前景，不中途接管；需要使用電腦時會先請你暫停。
前景中斷即停止 GUI 輸入並保存進度。
遇到異常，先在授權內查證；仍無法安全處理時，
保留原件，回報具體阻塞與需要我處理的一件事。
授權只限本次任務，撤回即停止。

【交付】
依 Skill 回報入口核對、完整盤點、逐本結果及最終對帳。
僅個別舊證據不足的歷史受保護項可保留並跳過，繼續其他合格項；
活動下載、UNKNOWN／未解派送及未完成命名交易不可跳過另送。
人工備份依 Skill 的六類規則歸類，不另增計數或當成排除。
有未解項就明列，不宣稱整份列表全部完成。
分開說明 GUI 觀察、照片驗證、完成紀錄與未驗證能力。
```

## 2. 貼上即交接

主要流程是「先開好正確列表，再提交上方 Prompt」，不用再發第二則開始或交接訊息。僅閱讀、引用或修改範本不是正式提交；Agent 仍須核對當次真實畫面，不能把交接聲明當成列表身分證明。尚未準備好畫面時，先完成準備再提交，不要先貼含有已交接聲明的範本。

LINE 應已登入，當次原生 Computer Use、輔助使用及螢幕擷取權限須可用，目的地須有足夠空間及寫入權限。Agent 在操作前核對可觀察的條件，不以首次工具呼叫代替人工開啟或交接。交接後讓 Agent 使用前景；需要使用電腦時，先請它停止新增操作並保存進度。

不是已確認列表、疑似另一列表或前景中斷時，依 Skill 保留原視窗並查證；仍無法解決才提出具體問題。不能靠猜返回快捷鍵或搜尋群組恢復。重新交回前景只恢復操作前提，不代表重新授權下載，也不解除 UNKNOWN。

### 你親自確認備份結果時

先開好指定列表，再提交上方日常 Prompt，Agent 就實際備份並回報結果；你的人工試用不必另用正式角色驗收 Prompt，也沒有至少兩本才能開始的限制。備份中的數量、非空、穩定性、SHA-256、完整解碼與完成紀錄讀回仍照 Skill 執行，這些是備份品質檢查。

Agent 依真實語意與證據核對任務授權、當次畫面、目的地及排除，不要求逐字口令；只討論範本或只說「畫面在前景」仍不等於正式下載任務。BACKUP_ROOT 留空與 EXCLUSIONS=[] 都是有效預設，不需要為開始下載另外填非預設值。若另行明示委託正式 Independent Acceptance，才適用那次角色交辦的版本與驗收條件。

永久紀錄依列表 UUID 分開，照片目的地不再決定紀錄身分。Agent 先查所有已登錄帳本並核對當前連續列表，不可覆寫 group.json、換 ID 或把新列表假綁為舊列表；名稱相同或不同都不能單獨證明列表身分。

## 3. 下次啟動仍使用同一份 Prompt

重新啟動本專案 Agent，先開好原列表，再貼同一份 Prompt。使用預設位置時 BACKUP_ROOT 留空；不需填 RESUME、回想進度或判斷下載結果。Agent 自行查全部永久帳本，核對列表身分、歷史及本機照片可用性；需要新一批照片區時追加目的地綁定，不改寫舊完成路徑。

完成的跳過、仍下載的觀察、待驗證的先驗證、確認停止且未完成的依原授權恢復。新 Session 使用新交接與新 scan／畫面，不沿用舊座標或畫面游標。Skill 不會自行喚醒已結束的 Agent 程序。

### 照片搬到外接硬碟後

舊照片樹內的紀錄先由 Agent 在已授權維護中遷入專案永久 `backup-records/` 並讀回；完成遷移後，您可以自行複製照片到外接硬碟，再刪掉本機整個 `backup/`。保留專案根目錄的 `backup-records/` 與 `.local/line-backup/`，它們不是照片暫存區。

下次仍貼同一份 Prompt，不需接硬碟、提供歸檔路徑或多填欄位。整本完成照片目錄缺席時，Agent 仍跳過它，另說明本機不可用；這不代表已驗證硬碟上的副本。仍存在的目錄若部分缺檔或異常，Agent 會保護原件並停止新派送。UNKNOWN 與未完成命名交易不因刪除照片解鎖，Agent 也不會替您刪照片。

## 4. 名稱校正與命名中斷

新備份會放在 `BACKUP_ROOT/<相簿目錄名>/`，照片為 `<相簿目錄名>_001.<原副檔名>`。名稱只供顯示及路徑使用；同一列表與相簿仍以本地身分和視覺證據判定。同名不同實體會使用 ` (2)`、` (3)`，恢復使用 ` (恢復 N)`；既有 `albums/<UUID>` 與舊照片不遷移。名稱完全讀不到時 Agent 才問你，不能默默建立舊格式新備份。

扁平布局 `FLAT_V1` 目前不支援完成後的名稱校正，工具會以 `FLAT_NAME_CORRECTION_NOT_SUPPORTED` 拒絕；不要自己在 Finder 改名。以下校正工具適用既有 `GROUPED_V1` 群組分層布局。Agent 先用 `memory` 找到 `album_key`，再以單本 `correct-album-name` 同步修改資料夾與照片前綴；群組錯字用 `correct-group-name` 涵蓋該組已完成的新格式相簿。群組內仍有未完成、未知、舊格式或外來項目、相簿內有額外檔案、符號連結，或來源檔案在計畫後變動時，工具會停止，不會只改一部分或覆寫目標。整個命名與校正流程都使用 direct CLI 參數，不需要你提供或編輯 JSON。若命名或校正中斷，Agent 執行 `resume-naming` 並重驗，不重送下載：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily resume-naming \
  --records-root "$RECORDS_ROOT" --root "$BACKUP_ROOT" --decoder "$DECODER" --decoder-sha256 "$DECODER_SHA256"
```

所有 daily CLI 的業務層成功以 exit 0、業務拒絕以 exit 4 回傳 JSON 簿記結果，固定包含 `dispatch_authorized=false`，不授予 LINE GUI 或 Save All 權限；參數語法／必填欄位錯誤會在執行前以 exit 2 拒絕，不產生 JSON 或紀錄變更。實際下載仍須符合本次任務授權及前景交接。

## 相簿 Prompt 的授權與完成界限

這份 Prompt 已涵蓋儲存全部與相簿級恢復；你的必要輸入是指定對象、必要時指定非預設保存位置、排除要求及有效前景交接。Agent 負責清單、定位、操作、驗證及狀態判斷。更長的 Prompt 無法補足工具缺少的畫面、座標映射或紀錄提交能力。

現有工具若已寫入明確 `UNKNOWN`，即使後來照片通過唯讀驗證，也可能無法提交完成紀錄。Agent 必須如實回報這兩種結果，不以再次授權、改寫歷史或重新下載解鎖。

2026-10-30 的特定 macOS CUA Session 已完成四本／141 張及獨立 E2E PASS，涵蓋逐本 popup 觀察、映射、chooser、命名及檔案／完成紀錄驗證；跨 Session 接續、中斷恢復與名稱校正仍未測。既有 PASS 不自動涵蓋後續修改；工具簿記欄位與獨立驗收分開報告。完整操作方法見 [專案 Skill](../.agents/skills/line-album-agent-cua/SKILL.md)，記憶位置與驗證界限見 [結構化備份記憶](結構化備份記憶.md)。日常備份結果不等於舊正式 AUTO 或獨立 E2E 驗收。

## 5. LINE 記事本照片與影片備份

記事本是與相簿不同的產品物件。此流程只備份 Owner 已開好的單一記事本列表中，各貼文內的照片與影片；貼文文字只作索引，留言、貼圖、連結及其他聊天內容不納入。Agent 使用[記事本 Skill](../.agents/skills/line-notes-agent-cua/SKILL.md) 與 notes CLI，自動查歷史、初始化或綁定列表、完整盤點、逐貼文逐媒體下載、驗證及恢復。Owner 不需要選擇盤點／接續模式、逐項下令，或填寫 UUID、內部 key、JSON、座標。

### 使用方式

1. 在具有原生 Mac Computer Use 的本專案 Agent Session 中登入 LINE。
2. 人工開啟指定的**單一記事本列表**，確認畫面就是本次要備份的列表。
3. 保持該畫面在前景，填入下方 `NOTES_BACKUP_ROOT` 後提交整份 Prompt。提交即同時授權本次備份與交接當次前景，不需要再發第二則開始指令。
4. Agent 會先核對真實畫面、入口及列表身分；尚未確認前不會開始新派送。前景中斷時，Agent 停止 GUI 輸入並保存進度。

`NOTES_BACKUP_ROOT` 可留空，Agent 會在初始化或追加目的地時使用目前專案根目錄的 `backup/記事本/`。若要指定其他工具支援的專案內位置，填完整絕對路徑。`backup/記事本/` 是 Agent 層預設，不是 CLI 的全域預設：`init`／`destination` 實際都要求明確傳入 `--photo-root`。此欄只指定照片／影片區；永久紀錄由 Agent 自動管理，不要手動搬移、改名或刪除內部帳本。

### 可直接貼用的啟動 Prompt

首次與下次啟動都使用這一份記事本 Prompt。請只在正確列表已在前景時提交；只討論、引用或修改範本不代表授權執行。

```text
NOTES_BACKUP_ROOT=

【日常正式備份與當次交接】
請使用本專案 $line-notes-agent-cua 與現有 notes 工具，
實際執行 LINE 記事本照片與影片備份。
我已人工開好指定的單一記事本列表；提交本訊息即授權本次任務，
並交接當次前景。請先核對實際畫面、入口與列表身分，再開始操作。
不需要我另外下令或再次交接。

【目標與範圍】
目標是完整保存這一個列表內所有貼文的照片與影片。
貼文文字只作索引；留言、貼圖、連結及其他聊天內容不納入。
NOTES_BACKUP_ROOT 留空時使用目前專案根目錄的 backup/記事本/；
其他位置僅限工具支援的專案內絕對路徑。
只操作這一個列表，不合併其他記事本、相簿或舊列表的狀態。
自行查全部 notes 永久帳本與 active 定位；
新列表在無缺損歷史或候選歧義時自動初始化，既有列表綁定原帳本。
不要求我提供 UUID、內部 key、JSON、座標或逐項下載指令。

【盤點、下載與恢復】
我先授權你完整盤點這一個列表的貼文，再逐篇交叉核對媒體，
不需要在盤點後等我另說「開始下載」。
一次只處理一個媒體 attempt；下載前先持久保存並讀回 intent、
新空白目的地與禁止重送紀錄，確認下載控制及 chooser 後，
每個 attempt 的記事本當次下載控制最多派送一次；
若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不沿用相簿入口。
下載後先保存第一筆 outcome；只有確認下載完成才驗證檔案。
結果未知先查證與調和，不直接 verify、不建立新 intent、不重送。

本次亦授權恢復：確認先前已停止且未完成時，保留原檔，
依 Skill 建立新的空白恢復 attempt；已完成項跳過，
待驗證項先驗證，命名交易中斷接續原交易而不重下。
已完成的事實不因新 Session、重排、圖片搬走或新目的地而改寫。
純文字貼文記貼文層 NO_MEDIA，不建立下載 intent，
也不是第七類媒體狀態或下載完成，最後須另列篇數。
貼文重排、編輯或新增時保留舊完成，只補可唯一識別的新媒體；
局部歧義保護該篇並繼續其他已核對項，列表身分或覆蓋不明則停止整份。

【邊界與資料保護】
只使用記事本 Skill 支援的下載入口；不得把相簿的
「⋯ → 儲存全部」、相簿選單、按鈕、chooser 或座標當成記事本 fallback。
不得發訊息、刪除、分享、覆寫照片或影片、改寫既有完成／UNKNOWN 事實、
跨列表操作，也不得為繞過拒絕而修改產品程式或紀錄規則。
記事本永久紀錄與相簿 backup-records/ 必須分開，不得混帳。
已完成的整篇目錄缺席時標 LOCAL_MISSING，保留完成且禁止重下；
目錄仍存在但缺檔、有額外檔、hash／身分漂移或 symlink 時，
標 LOCAL_CHANGED、保護原件並停止依賴該篇的新派送。
UNKNOWN、活動下載及未完成命名交易不因照片缺席或新目錄解鎖。
本任務不包含 commit、push、merge、改寫 Git 或雲端 CI。

執行期間我會保持前景，不中途接管；需要使用電腦時會先請你暫停。
前景中斷即停止 GUI 輸入並保存進度。遇到異常先在授權內查證；
仍無法安全處理時，保留原件，回報具體阻塞與需要我處理的一件事。
授權只限本次任務，撤回即停止。

【交付】
依 Skill 回報入口核對、完整盤點、逐篇／逐媒體結果及最終對帳。
列出貼文總數、NO_MEDIA 篇數、六類媒體狀態、已驗證照片與影片數、
本機不可用或內容異常項，以及尚待處理的缺項。
有未解項就明列，不宣稱整份列表全部完成。
分開說明 GUI 觀察、notes CLI 簿記、照片／影片解碼與 completion 讀回；
未實際執行的真實 E2E、跨 Session、混合附件 chooser 或恢復標 NOT_RUN。
```

### 貼上後如何運作

Agent 先依當次畫面與 AX 脈絡核對列表入口，不以中文標題或 OCR 單獨認定身分。身分依序為列表→貼文→媒體；貼文重排只更新來源順序，不重新命名舊完成檔。新媒體只補可唯一識別者，編號取該貼文目前最大編號加一。相簿與記事本、同日期貼文、相同張數或相同檔案 hash 都不能跨列表合併。

每個媒體下載都遵守一次一項。intent 一旦持久保存就按「可能已派送」處理；沒有正面證據不得因工具逾時、畫面未變或舊計數為零就重送。成功 intent 的 `status=UNKNOWN` 只是派送前初始狀態，不表示已下載。`memory`／`summary` 只供摘要投影，不提供完整 attempt、staging 目的地或 completion manifest；交易細節以該次 `intent`／`verify` JSON 及帳本追加事件為準。`UNKNOWN` 必須先以原事件、目的地與當次檔案查證；未收斂前不能直接驗證、建立新 attempt 或改用新目錄解鎖。只有確認先前已停止／未派送、保留原檔且原任務涵蓋恢復時，才可建立新的空白恢復 attempt。

六類媒體業務狀態是 `COMPLETED`、`EXCLUDED`、`PENDING`、`PREVIOUSLY_INCOMPLETE`、`UNKNOWN`、`PROTECTED_HISTORY`。`NO_MEDIA` 是貼文層標記，不是第七類，也不能計入下載完成。人工備份聲明只是來源註記，不能單獨升格為工具認定的完成。

記事本永久記憶在 `notes-backup-records/<local_list_id>/`，內含列表、store、追加式 `events/`、`evidence/` 與鎖定檔；`notes-backup-records/index.json` 只登錄位置。`.local/line-backup/active-notes-task.json` 只協助定位最近任務，遺失它不代表沒有歷史。照片／影片區可依 Owner 決定搬移或刪除，但不要刪除上述永久紀錄與證據；整篇目錄缺席只代表本機不可用，不代表外部副本已驗證。

### CLI、驗證與分支界限

本 feature branch 的工作樹已提供 notes CLI；這些變更尚未合併到 `master`。入口為：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
```

notes CLI 的業務成功以 exit 0、已列業務拒絕以 exit 4 回傳 JSON 簿記結果，這兩種 JSON 固定包含 `dispatch_authorized=false`；參數語法或必填欄位錯誤以 exit 2 拒絕，只在 stderr 顯示錯誤且不改紀錄，不輸出 JSON；未預期內部錯誤以 exit 70 回傳 `status=INTERNAL_ERROR`、`reason=UNEXPECTED_EXCEPTION`、`dispatch_authorized=false`。exit 70 不是可重試業務拒絕，不得據此重送、改寫 ledger、建立新 attempt、換目的地或換入口繞過；應停止並保留現場、原始輸出與證據後回報。`dispatch_authorized=false` 只表示工具不授予 GUI，不能當成下載授權、實機 PASS 或獨立驗收。實際下載仍只能發生在本次任務授權與有效前景交接內。

新列表流程是 `init` → `bind` → `scan start` → `page`… → `scan finish` → `post`／`media`；既有列表是 `bind` → `scan start` → 後續同一盤點流程。`lists`／`init` 使用 collection；除 `lists`、`init` 外，所有帳本命令都要 `--records-root`。`init`／`destination` 另要求 `--photo-root`。完整參數矩陣見[記事本下載與 notes CLI](../.agents/skills/line-notes-agent-cua/references/download-and-ledger.md)；照片 `verify` 必須成對傳 `--decoder` 與 `--decoder-sha256`，影片則不傳該照片 decoder 組合。

相簿、記事本摘要及個別媒體是三個不同層級的完成訊號，不能互換：

- 相簿 `daily summary` 的 `ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS` 只表示相簿簿記覆蓋完整。
- 記事本 `notes summary` 的 `all_known_media_complete=true` 只表示該帳本的已知貼文與媒體覆蓋完整，且沒有 summary 所列阻塞。
- 個別媒體 `verify` 結果的 `verdict=PASS` 只表示該次指定檔案的驗證通過。

上述任一項都不是 GUI 畫面、真實 LINE E2E 或獨立驗收 PASS；`PROTECTED_HISTORY`、`LOCAL_MISSING`、`UNKNOWN` 等仍須依各自規則明列。

照片驗證沿用 ImageIO 完整像素解碼；`--decoder` 由呼叫端提供，實作者須核對其建置來源（例如是否由 repo 的 `src/line_backup_batch/image_decode.swift` 建置），工具只核對呼叫端提供的 SHA-256 與執行前後 binary 穩定性，不能證明 provenance。目前嚴格照片驗證只接受 `.jpg`／`.jpeg`／`.png`，且檔案大小必須小於 512 MiB（等於 512 MiB 也拒絕）。HEIC／HEIF、WebP、TIFF、GIF 等其他格式或超限檔案會保留原檔，但因驗證器不支援而不降格判為完成，仍列未驗證。影片驗證只接受 `.mp4`、`.mov`、`.m4v`、`.avi`、`.mkv` suffix，且 `ffprobe format_name` 必須符合對應 container alias；完整映射見[驗證與恢復](../.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md)。影片使用成對的 Homebrew `/opt/homebrew/bin/ffmpeg` 與 `/opt/homebrew/bin/ffprobe`，先確認有非 `attached_pic` 的有效影像串流，再完整解碼影像與音訊至 EOF。非零退出、截斷、解碼錯誤、覆蓋不足或工具版本不一致都不能完成。成功解碼不證明與 LINE 服務端原始位元完全相同。`notes summary` 的 `local_counts` 固定包含 `VERIFIED_PRESENT`、`LOCAL_MISSING`、`LOCAL_CHANGED`、`NOT_APPLICABLE` 四類，回報時不得只列前兩類或把它們混成六類業務狀態。

本次記事本功能在 `feature/line-notes-media` 開發與測試；在 Owner 測試通過並明確同意合併前，不合併到 `master`。目前可確認的是文件與離線合成測試範圍，不代表 master 已包含此功能。真實記事本下載、照片／影片混合附件 chooser、跨 Session 接續、真實中斷恢復與人眼驗收仍為 `NOT_RUN`；必須另有一次正式任務與有效前景才能驗證。
