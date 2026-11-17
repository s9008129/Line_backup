# GUI 導覽與盤點

本文件說明在 Owner 已授權且前景交接有效時，如何用當次原生 Mac Computer Use 判讀 LINE 記事本列表、貼文及媒體。它是觀察與導覽方法，不是 GUI 授權、實機 PASS 或自動控制器；未實際執行的畫面與流程一律 `NOT_RUN`。

## 入口判定

1. Owner 先人工開啟指定記事本列表；Agent 交接後以當次 AX／截圖／可見畫面核對頁面角色、焦點、列表標題脈絡及連續性。口頭稱為「列表」不能代替畫面證據。若 Owner 稱目前是 viewer、實見卻是列表，先在有效前景唯讀核對 app／window、AX 與截圖來源，以及列表到貼文的連續性並保存原件；未確認前不點卡片、不捲動、不建 intent。確認為指定列表且前景有效後，列表就是正常入口，依既有盤點與導覽自行繼續，不逐點請示；真正前景中斷即停止輸入，仍有歧義只問一項具體缺口。
2. 名稱可作顯示、目錄及回報；不得用中文名稱／OCR 搜尋、選擇、核准列表，也不得只憑名稱認定是前次帳本。疑似另一個列表、聊天、相簿或出處不明頁面時，停止整份新派送並先唯讀釐清。
3. 若目前是貼文詳細頁、媒體 viewer、下載選單或 chooser，先確認它的原操作與出處。只有找到當次可靠返回控制項，或已證實且符合目前角色／焦點的快捷鍵，才返回一次並重新核對；不得猜 Escape、Command-W、關閉或取消。前景中斷時停止所有 GUI 輸入。
4. 入口未確認前不捲動、不盤點、不開啟下載控制。控制未見時依[導覽與輸入紀律](#導覽與輸入紀律)做有限查證。記事本與相簿不是同一操作；不要沿用相簿的入口、選單、按鈕或歷史狀態。

## 三層身分

身分固定為「列表 → 貼文 → 媒體」。Agent 只保存當次觀察與真實來源；notes CLI 產生可持久化的 key，Owner 不填內部 JSON。任何單一名稱、文字、日期、張數、序號或 hash 都不足以認領歷史。

### 列表

- 可靠依據：本次連續入口、當次畫面／AX 的列表角色、前後導覽連續性，以及相符的本地帳本／觀察 evidence。
- 不足依據：群組或列表的顯示名稱、中文 OCR、貼文文字、相同日期、相同媒體張數、相同封面。
- 疑似另一個列表或無法證明連續性時，不以「看起來一樣」合併；保留斷點，重新交接或問 Owner 具體是哪一份列表。

### 貼文

- 可靠依據：卡片在連續清單中的位置、與前後卡片的共同錨點、日期、可見文字脈絡、媒體縮圖排列及更多指示的交叉。
- 不足依據：單一日期、單一摘要、單一縮圖、總媒體數、畫面序號或貼文顯示名稱。貼文內容被編輯、卡片重排或刪除時都不能自動認領舊完成。
- Agent 保存貼文層觀察，讓 CLI 產生 `post_key`；`post_key` 不是中文標題或畫面序號。來源順序是另一個可更新欄位，不能把順序變動當成新貼文。

### 媒體

- 可靠依據：所屬貼文身分、媒體在貼文中的實際排列、縮圖及 viewer 的前後文；下載後只做基本檔案檢查，不為來源種類播放或檢視內容。
- 不足依據：只看媒體縮圖、只記 `n/N`、只比檔案 hash、只比檔名或只比下載順序。相同外觀或相同內容可能是不同來源項，必須各自保存，不能自動去重。
- Agent 保存媒體觀察，讓 CLI 產生 `media_key`；`source_order` 可因新增／重排更新，但舊完成檔名不變。新增媒體只取該貼文目前最大編號加一。

### 變動與隔離

- 同日期、同張數、同文字或同 hash 不能跨列表合併；每個列表使用獨立 `local_list_id` 與帳本。
- 貼文被編輯時，舊媒體完成事實保留，更新文字／來源順序索引；只追加可唯一辨識的新媒體。若新增、刪除與既有媒體的對應有歧義，保護該篇並停止該篇新派送。
- 列表重排不重命名舊檔；列表新增貼文先補盤點再排程；列表級身分或覆蓋不明時停止整份，而不是只猜一個候選。

## 從頂端到底端盤點

每次只做一個小步，輸入後重新取得 AX／截圖並核對位移、焦點與共同錨點。位移依可唯一連接的卡片邊界、作者列／日期／互動列相對 viewport 的變化判斷；媒體播放／輪播、PNG hash 或單一 AX 數字變化不能單獨證明列表前進。不得連續盲捲、用舊 scrollbar 數值推算總數或把工具沒有反應直接當成邊界。

1. **建立頂端起點。** 從目前位置向上小步移動；以清楚可見的頂端邊界，以及同一首卡再次向上無位移，交叉確認頂端。沒有可靠起點就記盤點未完成。
2. **記錄每個畫面。** 依當次列表順序記下可見貼文卡片的日期／文字脈絡、媒體縮圖、更多指示、部分可見狀態及觀察來源。部分卡片先標待確認，不直接計入新貼文，也不漏記。
3. **有序重疊。** 下一畫面必須與上一畫面共享至少一個可證明是同一張的卡片，且上一頁後段與下一頁前段的順序一致。用共同卡片、日期脈絡和縮圖排列交叉，不用相似外觀拼接。
4. **補缺頁。** 失去重疊時保留缺頁紀錄，以較小步距向回核對，接回最後已證明的畫面；仍無法接回就重建本輪盤點或停止。不得以「看起來差不多」補齊。
5. **確認底端。** 末頁穩定後，先依下方輸入紀律確認當次目標，再向下小步移動；核對同一末卡、同一列表、卡片順序及可靠位置／視覺量測均不變，並指出原件中的終止線索（如容器終點、貼近軌道下緣的捲軸滑塊或結束標記），且沒有未解的下一卡片段或待載入線索。AX 沒有 max 欄位時可用可靠圖片量測，不拿單一數值當最大值。合法輸入後沒有位移，可能是真正底端，也可能是輸入未生效或載入未定；先核對已有原件，無足夠證據就保留未完成並依停止限制結束查證，不反覆換按鍵、座標或單位試到有反應。
6. **完成前覆蓋與歷史對帳。** 先依下方來源卡片到 page 的對帳，確認本輪每張可區分卡片都有來源與 rows 對應；再將本次貼文清單與既有帳本、completion、排除、先前未完成、UNKNOWN、受保護歷史及本機檔案可用性比對。舊證據不足先保護，不因缺少標記就重下。

盤點要保存：當次列表／任務識別、頂底與每頁重疊 evidence、貼文順序、逐篇狀態、純文字篇及待下載順序。只有頂底、覆蓋、篇數及身分都成立，才可聲稱列表已完整盤點；逐篇媒體仍可各自有未解缺項。

## 來源卡片到 page 的覆蓋對帳

### 來源卡片台帳

每次小步移動後先保存當次 AX／截圖與引用，再依畫面由上而下列出**所有可區分的完整及部分卡片**；此時不從預定貼文、`post_key`、總數或既有 rows 回填來源。每張卡片至少記：觀察引用及可定位區域、完整／上段／中段／下段、可見邊界線索、前後卡片、已知對應或待解問題。局部代號只供同次對帳，不是貼文身分、跨 Session 認領鍵或 Owner 必填資料。

相同時間的兩個作者列／卡片邊界仍是兩個候選，分別核對，不因顯示時間相同合併。部分卡片一律留在台帳；用小步補觀察把同一卡片的不同片段接到同一貼文。高卡片跨多個 viewport 時，須以內容延續、邊界及相鄰卡片證明連接；不能只用「畫面相似」拼接，也不能因片段不另計新篇就略去。無法唯一分辨延續或新卡片時，保留待解並停止依賴該頁的提交。

### page 前雙向對帳

原則上一個已對帳 viewport 對應一個 page。只有為解開部分／高卡片的連續補充 viewport，才可共用同一 page；須逐一保存觀察順序、全部卡片、片段連結及 page 的有序聯集，不得把已越過多張新完整卡片的多次捲動事後併成模糊 page。

先保存來源卡片台帳，再產生 CLI 支援的 rows。呼叫 `page` 前逐一核對兩個方向：

- **來源→rows：**每張完整卡片及每個片段都有唯一貼文對應；待解數為零；每個來源新卡片都在該 page rows，已見卡片以既有相鄰 overlap 表達。
- **rows→來源：**每個 row 都能回到至少一個本頁原件區域；不同卡片不被合併，同一卡片不因片段重複計新篇；順序與原畫面相符。

核對紀錄至少包含：觀察引用／卡片區域／完整或部分／前後脈絡／對應身分或 `post_key`／所在 page row／待解與處置。提交前 `page_gate` 只依上述雙向對帳成立與待解為零判定，不以尚未發生的 page 讀回為前置。`page` 成功後，把回傳 key 與事件讀回引用附到同一份紀錄；只有讀回與提交成員及來源對應一致，才可繼續下一頁。讀回若有差異，立即停止後續 page、`scan finish`、新 intent 與下載，不以 `evidence-correct` 改寫 page 成員。頁證據與實際 posts 輸入留在同一 page 的 statement／assets。

任一方向有缺口或未解片段時，不呼叫 `page`／`scan finish`，也不開始新的 intent／下載。原件可區分 A、B、C 三卡而擬提交 `[A,C]` 時，即使 A／C 可接前後頁且頂底重疊成立，B 的來源→row 缺口仍阻止提交；B 只有不下載的附件也不能省略。

### finish 前原件重核與來源變動

最後一次補觀察完成後，直接重新讀本輪來源原件的卡片邊界，與已提交各 page 的讀回 rows 逐頁核對；不是只重讀自行整理的清單，也不以固定重掃或兩次總數相同代替。完成前須同時成立：

1. 當次列表身分及入口連續，頂端／底端有原件與有效邊界觀察。
2. 每頁來源卡片與 rows 雙向對應，部分片段均已解，頁內順序及跨頁尾→頭 overlap 成立。
3. 所有 page 的有序去重聯集與擬 finish 清單相同；每個 key 有來源，不漏卡、不重複計新篇。總數只是對帳結果，不是外部真實總數 oracle。
4. 無未解來源片段、缺頁、page 讀回差異、列表變動或身分歧義；完成 statement 指向逐頁證據及核對結果。

任一條件失敗時，不呼叫 `finish`、不宣稱完整、不開始新下載。已見卡片被新增、刪除、重排、編輯，或原件／rows 無法唯一對應時，保留變動前後證據，將本輪覆蓋視為未成立並停止 finish／新派送；不得以剩餘卡片數相同、改 key 或自稱「已更新」掩蓋。若發現本輪已提交頁內漏登，停在原 scan 與原證據，交 Owner 決定；`evidence-correct` 只修引用，不能補成員，也不得自行再建 scan 覆蓋錯誤。

## 逐篇媒體盤點與交叉核對

先在貼文卡片的可區分區域開啟貼文，避免只點到單一縮圖而誤認整篇內容。若當次卡片已是同一貼文的已展開狀態，可直接以「已展開卡片 → 縮圖 → viewer」連續交叉核對；不為尋找獨立詳情頁而點文字，也不假定所有版本都有詳情頁。來源或覆蓋不明時仍保留待盤，不泛稱所有版本相同。每篇至少交叉以下來源：

1. **貼文網格。** 觀察所有可見縮圖、排列、空白位置、影片指示及「更多」覆蓋。可見縮圖數不是總媒體數。
2. **更多指示。** 若畫面有 `+N`、更多、展開或其他批次入口，記錄其顯示數量與位置；它只作候選訊號，不單獨證明 viewer 總數。
3. **媒體 viewer。** 開啟後記錄首張／目前序號、所屬貼文標題或日期脈絡、相鄰媒體及可用的下載控制。前後移動一次後重新觀察，確認 viewer 仍屬同一貼文及同一媒體序列。
4. **回到貼文。** 只有當次可靠返回控制項或已證實的角色／焦點快捷鍵可用時才返回，並重新核對貼文網格。不要用 viewer 的 `n/N` 自稱整篇已盤點；viewer 可能只涵蓋部分媒體、重新排序或顯示延遲。
5. **逐項建檔。** 對每個可區分媒體保存順序、縮圖／viewer 歸屬觀察及來源引用；種類不明的新媒體使用 `UNCLASSIFIED`，既有媒體沿用原 key／identity，讓 CLI 建 `media_key`。重複外觀仍逐項記錄；不能因為 hash、檔名或縮圖相同就少建一項。

### 目標與下載控制就緒（B1）

本節是 reveal discovery、有限 re-arm、action-on-positive 與 intent 後延後候選／封鎖的唯一決策本文；其他文件只記證據、交易或投影，不另定候選次數，也不改變既有 `STOPPED`／`NOT_SENT` 精確恢復與 restart 規則。可執行 composition `persistRevealWithDirectAfter` 見 [單次輸入與直接 after 觀察](evidence-template.md#單次輸入與直接-after-觀察)；範例只實作本節，不複製或擴張 helper、次數與停止條件。

- **先備妥非 GUI 前置。** 在任何 reveal 前，先完成歷史／資格／完整盤點與目標媒體細盤核對、viewer 三層身分、實際 entry anchor 與 `expected_return_role`，並解析帳本、照片 root、notes CLI、私有 task／證據父目錄、本候選唯一 input／after observation 目錄、statement 骨架與精確 `intent` argv／讀回欄位。所有目錄都要在任何 reveal 前建立；不能在 input 後另開 shell 建目錄。`intent` 與其空白 staging 只能在 `TOOLBAR_VISIBLE` 後由 CLI 建立；不得預先建 staging、猜 key 或先寫事件。
- **固定額度。** 以 `list_key + post_key + media_key` 為 reveal scope；每個 scope 最多派送兩個候選，`candidate_ordinal=1`（初次）及至多 `candidate_ordinal=2`（一次 re-arm），總計最多兩個已派送候選。任何已送出的 hover／pointer move 或 `NAVIGATION` 均計數，包括 timeout、error 或結果 `UNKNOWN`；單純未通過前置而沒有輸入則不計。viewer 重開、返回、換頁、新 Session、新目錄與新 capture 都不重置。此每媒體兩次上限不取代一般同根因最多三次；兩者同時適用，連續兩次沒有新資訊即停止相同方法。
- **候選前稽核。** 每次輸入前保存並讀回 `candidate_ordinal`（`1`／`2`）、`prior_candidate_refs`（候選 1 為 `NONE`；候選 2 必須是同一 scope 的候選 1 持久引用）、`budget_before`（此前已派送候選累計數，只能為 `0`／`1`；未知不得當 0）、target、mapping 與 input request；輸入後保存 `budget_after`（`1`／`2`）。`budget_before=0` 只可在完整查得同一 scope 無先前候選時使用；先前 refs 缺失、不可讀或歧義時停止。`candidate_ordinal=2` 不得重播舊點、舊 mapping 或同一 candidate，且只在 `budget_before=1` 時可評估。
- **候選共同前置。** 授權、有效前景、同一列表／貼文／媒體／viewer、來源、可歸屬返回控制、當次座標映射均成立，且無 chooser、無未解輸入／下載或身分漂移；一般候選另須無 intent，唯一例外是本節下述「intent 後延後第二候選」的完整前置。方法另須各自安全證據：click 僅可用已選 filmstrip 縮圖的非播放安全邊緣；文件支持的 hover 則須有該 hover 自身可歸屬作用區、非播放安全區與映射，不要求 filmstrip 或同一邊緣。幾何只作當次候選的來源與安全證據；不得把曾成功的位置泛化為任意縮圖邊緣、固定左上／右上熱點或跨 Session 座標。當次安全作用區或映射不足就停；API 能力仍依當次工具文件。任一不足就停在輸入前；不點主內容、播放／暫停、時間軸、工具列或其他縮圖，也不以 body click、次要 click、快捷鍵或猜測 API 尋找控制。
- **Hover 能力。** 只有當次工具文件明確支持無點擊移鼠時才可使用；能力未查明記 `UNKNOWN`，明確不支援記 `NOT_AVAILABLE`。不得把 `click` 說成 hover，也不因 hover 可用而增加候選額度；hover 的安全區證據不能借用 click 的 filmstrip 條件。
- **同次輸入與 after 時序。** 每個候選只呼叫一次已核對 input。request 寫入且讀回 `MATCH` 後，在 `persistSingleInput` 的 `invoke` callback 內用已讀回的 target 呼叫一次當次文件支持且已核對的 reveal input（一般為 `app.click`；無點擊移鼠只在文件支持時使用）；原生回傳後，不結束 callback、不開新 shell，也不插入模型回合、固定等待、再取 app 或寫檔，直接對同一 app 取得 after（當次支持時為 `getAXStateAndScreenshot`）。這是兩個相依 API，不是 atomic、0–1 秒或固定秒數保證；after API 的內部等待只沿用其當次文件語意，不能補成事件命中、toolbar 存活時間或精確時間。記憶體分開保留 input 回傳、after 回傳與 after error；callback 原樣回傳 input 回傳（含 typed `undefined`），不得把 after 失敗冒充 input 未送出。記錄 host 層 input call 前／回傳與 after call 前／回傳時間、相對序號；來源未提供 OS event 或個別 capture 時間就記 `UNKNOWN`，不以檔案 mtime 冒充。callback 返回後才由既有 helper 保存 input raw／diagnostic，並以 `persistObservation` 保存剛才取得的同一份 after bytes，不重新 capture。
- **保存缺口不授予重送。** request 寫入／讀回未 `MATCH` 時不得呼叫 input，也不 capture。若 input 已送出而 after capture error、callback 中斷、程序 crash，或 input raw／diagnostic／after bytes 未完成持久化與讀回，保留 request、可得的 input 回傳／error、已取得 bytes 與停止原因，候選額度照算；capture error、空 after、缺 raw、無 after 或重啟都不等於 `NOT_SENT`，不得為補證再點、再 capture、re-arm、建 intent 或新 attempt。只有成功的 input receipt 與保存的同一份 after 足以按 B1 判斷狀態；證據仍不足就停在 discovery blocker。
- **Action-on-positive。** 同一充分範圍的最新正面觀察同時顯示工具列，且下載控制可見、歸屬、啟用與映射成立時，記 `TOOLBAR_VISIBLE`。該觀察就是 action window；保存其 bytes／hash 與映射後，立即執行已備妥的 `intent`，不得插入固定等待或只為確認「穩定」而再捕捉一次；不能宣稱 atomic／immediate。若首次 after 的範圍、AX 或映射不足以完成 gate，可用小步唯讀觀察補足缺口；這不是 stability capture，也不是新的候選，不授予 re-arm，補足後仍須有正面控制證據才可建立 intent。
- **有限 re-arm。** `TOOLBAR_NOT_SHOWN` 只表示該候選後最新、充分且可保存的 bounded observation 未見工具列；它不證明觀察期間從未短暫出現，也不證明 LINE 失敗，尤其不能由單一 after 畫面排除 capture 漏過 transient。`REVEAL_TRANSIENT` 則表示 intent 前曾在有效觀察中正面看見工具列，之後在有效觀察中消失；它不是永久封鎖理由。兩者都只有在仍有 `REARM_1` 額度，且有新的充分觀察證明同一三層身分／有效前景、無 intent／chooser／未解輸入，並具決策相關新證據時，才可進入一次 `REARM_1`。新證據須改變 gate，例如先前遮擋／範圍不足已消除、選取或幾何有可核對變化、或新觀察正當建立該方法的另一個安全作用區；單純再拍一張、時間流逝、只有「換點看看」、底層身分漂移或舊點失效都不是新證據。`REVEAL_TRANSIENT` 後若沒有相關新證據仍停止，不建 intent／outcome；`REARM_1` 後仍無正面控制即記 discovery blocker，不稱 LINE 下載失敗。
- **不可或不必 re-arm 的狀態。** 導覽 `UNKNOWN`、capture／AX／截圖範圍不足、輸入結果不明、播放開始、索引／媒體／viewer／列表或返回錨點漂移、幾何／映射失效、出現 chooser 或任何未解輸入時，先停止依賴輸入；可做小步唯讀補觀察，但未達充分 `TOOLBAR_NOT_SHOWN`／`REVEAL_TRANSIENT` 與新證據前不得進候選 2。前後原件、`budget_after`、`prior_candidate_refs` 與停止原因全留。
- **intent 後延後第二候選。** 這是對原封鎖的窄例外，使用同一 list/post/media scope 原有的 `candidate_ordinal=2`，不增加第三候選。只適用於當次新建立並讀回的 intent、同一 Session／連續有效前景、同一 viewer 與三層身分；原第一候選及其 request／raw／after 均已保存讀回且額度確定為 `budget_before=1`。intent 前仍須正面 `TOOLBAR_VISIBLE`；intent 後最新充分原件證明同一控制由可見轉為隱藏，才是本例外的具體新 gate 證據，不以時間流逝或新 capture 本身授予候選。
  - **intent 前準備。** 若預計可能使用延後候選，在建立 intent 前先保存其方法、安全作用區、原 before 引用、候選 1 完整 receipt、剩餘額度與 request 骨架；尚無 attempt ID 的欄位等 CLI 成功與事件唯讀核對後填入，不預建 staging。沒有這份原 task 的前置準備，不在 intent 後臨時創建新探索方案。
  - **先核對連續性。** 以完整連續輸入原件與持久 intent 讀回正面核對：本 attempt 尚未呼叫下載控制、尚無 outcome，亦無 chooser、活動下載、pending naming、其他未解 attempt 或未解輸入。零計數、空 staging、缺檔或缺 receipt 都不能單獨證明未呼叫。已有 `UNKNOWN`、舊無 outcome 的 crash window、程序／前景中斷、新 Session、候選額度或輸入歷史不明都禁止此例外；原 attempt 繼續依結果／reconcile 分流。
  - **方法與單次保存。** 重新核對當次方法的安全作用區與映射：文件支持的無點擊 hover，或已選 filmstrip 縮圖的非播放安全邊緣 click。後者是真實 `NAVIGATION`，不是 hover；當次工具只有 click 時也只能使用已證明安全的該區域，沒有區域就停。不得點主內容、下載圖示來叫出工具列、播放／時間軸、其他縮圖、返回或 reopen。依[單次保留](evidence-template.md#intent-後延後候選的單次保留)在輸入前保存並讀回 intent／attempt、prior refs、`candidate_ordinal=2` 與 budget 1→2，沿用原 task 的固定 input slot；不得換 ID／目錄／Session 重置。只送一次 input→直接 after，input error／timeout、capture／保存缺口或 crash 也耗額並停止，不補送。
  - **after 與一次下載。** Agent 依同次已保存 after 重新核對三層身分、viewer／返回、未播放、下載控制可見／歸屬／啟用與映射；全部成立才把最新原件及 mapping 交既有 `persistGroundedDownloadClick`。helper 不做視覺判斷或授權。若控制仍缺席或再消失、身分／幾何／前景漂移、任何證據不全就停，不重播第二候選、不沿用舊下載點、不建另一 intent。第一筆 outcome 依真實證據，不足為 `UNKNOWN`；工具列重新出現不等於下載成功、未派送證明或 completion。此序列不是 atomic，無固定延遲或成功保證。
- **其餘 intent 後封鎖。** 一旦開始或建立本 attempt 的 intent，除上述完整成立的一次延後第二候選外，不得再 hover／pointer move 或 `NAVIGATION`，亦不得返回、reopen、新 viewer 或新 Session 重開 discovery。intent 讀回後對當次重新定位的下載控制最多一次；下載呼叫一旦開始或結果不明，即永久關閉該 attempt 的延後候選窗口。控制消失本身不能證明 `NOT_SENT`，保留原 intent 並依 outcome／reconcile 處理。既有 `STOPPED`／`NOT_SENT` 精確恢復與 restart 仍循原授權，不能用來重置本 scope 額度。
- **狀態真值。** `TOOLBAR_VISIBLE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT` 與導覽 `UNKNOWN` 是 statement 結論，不是六類業務狀態；intent 前媒體仍為 `PENDING`。AX 未列控制不能否定充分涵蓋的截圖，截圖也不能替 AX 補成節點。只有 `TOOLBAR_VISIBLE` 可接續 intent；其餘 intent 前狀態不得建立 outcome；已建立 intent 的延後候選則依既有交易規則記第一筆真實結果，不足為 `UNKNOWN`。
- **下載控制定位。** 若以座標點擊，必須使用 [單次 CUA 輸入保存 helper](evidence-template.md#單次-cua-輸入保存-helper) 的 `persistGroundedDownloadClick`。Agent 仍自行判讀控制區域、歸屬、候選點、映射與下一步；helper 只驗證並保存 request，再以持久讀回的 target 呼叫 `app.click([x, y])`，不負責找控制、不提供 native hit-test／receipt。普通導覽、返回與 chooser 不經此 helper；helper 不可用、欄位缺失或讀回不符時停在輸入前，不得改用任意 invoke、手動 app.click 或舊點擊入口。
- 目標或下載控制仍無法可靠定位時，記具體阻塞，不猜點、不重新下載。歷史成功僅為關聯；其他 viewer 有效性與 toggle／timeout／capture race 仍 `NOT_RUN`／觀察未知。

若貼文只有文字而沒有任何照片／影片，標記貼文層 `NO_MEDIA`，不做下載 attempt，也不計入六類媒體完成。若看不到完整媒體、viewer 總數與貼文數量矛盾、更多指示無法展開或返回後網格變動，保留該篇待確認；只有列表級覆蓋仍成立時，保護該篇並可繼續其他已核對篇。

### restart 確認後的來源重核

- `restart confirm` 後不得沿用確認前的 page rows、cursor、舊 scan 或舊 viewer 當作新 attempt 的來源證據。必須從頂端到底端重新觀察同一個已確認列表，完成新的完整 recovery scan，才可逐項建立 restart intent。
- 精確 `restart confirm` 前的既有 `UNKNOWN`，可在 confirm 後由 scope 的第一個新 v3 attempt 首次替代；confirm 後同批次任何新增 v3 attempt 尚無 outcome 或結果 `UNKNOWN`（含後來被 supersede 的舊版）時，停止新 intent 與 activation，先依既有命令查原 attempt；若現行 latest-only `reconcile` 無法處理已被 supersede 的舊版，保留證據、回報具體資料阻塞，不反覆呼叫或擴寫更正入口。`STOPPED`／`NOT_SENT` 依既有授權恢復；`DOWNLOAD_FINISHED` 用原 attempt 基本檢查，不能被這項 scope gate 誤擋。
- 新 attempt 仍要當次列表→貼文→viewer→下載控制→chooser→精確 raw 目的地的連續證據；使用新的空白 staging、當次 viewer／chooser 與重新取得的定位。舊 handle、舊路徑、舊座標或舊 chooser 都不得重用。
- 取消或關閉舊 chooser 只代表該次取消輸入；不證明先前的下載、寫入或晚到輸入已停止。舊 raw／舊版本可能仍有晚到 bytes，保留在原區並記錄，不合併到新 candidate，也不據此改寫新版本。
- 再次中斷後從 `OPEN_BATCH` 找回同一批次時，已驗證 candidate 與歷史仍保留；只對未完成或結果不確定的項目，依上述 scope gate 處理。scope、來源身分、目的地或版本策略改變時，停止並重新預覽、取得新的 Owner 明示同意。

## 導覽與輸入紀律

- 每次輸入前確認授權、有效前景、頁面角色、焦點、目標控制項及預期結果；輸入後重新觀察，不以 API 回傳、OS 慣例或舊座標代替畫面證據。
- **先判讀索引，再輸入。** 先讀最新完整 AX，或能由該完整樹連續還原的最新 diff，才選定元素；在當次操作紀錄連同原件引用記下「索引→目前角色／所屬列表→預期效果」。捲動前反查該索引仍是當前列表或其捲軸，不能只因前一次數字可用就沿用；若已變成視窗按鈕等其他角色，該目標不可用。不要把取得新 AX 與使用尚未核對的舊索引輸入合併成一次預寫呼叫。screenshot-only 或映射失效後，先依當次工具文件重取完整 AX，再使用元素索引。
- 捲動的方法與單位依當次工具文件；macOS native scroll 使用 page count，不從型別範例猜 pixels、捲軸值或未支援按鍵。原始輸入回傳與事後畫面一併保存；工具拒絕或角色不符的呼叫不算有效邊界探測，停止依賴該前提的操作，不換入口繞過。
- 座標、AX 元素與快捷鍵只在當次映射成立時使用。視窗移動、縮放、換頁、popup 重開、前景中斷或觀察來源變化都會使舊定位失效。
- 主視窗截圖／AX 可能漏掉獨立 popup 或 chooser；這不代表控制項沒有出現。必要時依當次 Owner 授權與平台能力使用指定區域的唯讀截圖，只保存任務需要的私有區域，不上傳外部服務。
- Viewer 已就緒且媒體身分成立、仍未見控制時，先查當次工具文件與 API scope。工具不支援第二觀察來源時，來源對照標 `NOT_RUN`；無點擊移鼠能力未查明記 `UNKNOWN`、明確不支援記 `NOT_AVAILABLE`，不得猜 API。是否可使用 selected-filmstrip 候選、何時可 re-arm、額度與 action window 只依 [B1](#目標與下載控制就緒b1)；能力不足不代表控制不存在或 LINE 失敗。
- 對可用來源，在同一媒體、同一幾何下做最小對照並保存各自原件。記錄來源、觀察時間、焦點、hover／其他輸入、幾何及變化／漂移；不同來源不是原子快照，須保留時間差並核對媒體與視窗連續性。需要比較狀態時，保留等時長靜置對照。只有文件明確支援無點擊移鼠，且安全作用區域及當次座標映射均有據時，才可移鼠一次並立即重觀察；未控制其他變項時不得宣稱 hover 因果或已驗證修復。
- 除 [B1](#目標與下載控制就緒b1) 明列的 hover 與 selected-filmstrip `NAVIGATION` 候選外，不可額外 click 探索，且候選不是 hover 或下載控制。不得切換五格反覆查找；控制歸屬、作用或定位未證明，不建 intent。不得重播 intent、使用舊點位、以固定等待當成修復，或把 fresh capture 本身當成 re-arm 的新證據。
- 任何下載控制、chooser 與「確認」都是獨立輸入；不要用反覆點選、猜 Return 或重開選單查證。下載派送限制與 notes CLI 交易見 [下載與 notes CLI](download-and-ledger.md)。
- 一般查證維持同一根因最多三次有證據嘗試，連續兩次沒有新資訊就停止相同方法；B1 的每媒體最多兩次已派送 reveal 候選同樣不可被其他查證次數擴充。更換觀察來源只有在帶來決策相關新資訊時才可支持下一步，不得改下載入口、跨列表或繞過工具拒絕。

## 返回契約與有限恢復

本節是 viewer 返回與入口恢復的唯一決策本文。Skill 只保留摘要與連結。

### 進入 viewer 前先保存錨點

開啟 viewer 前，保存當次 observation、列表／貼文身分、來源卡片或媒體縮圖區域、`entry_page_role`、entry anchor 與 `expected_return_role`。`expected_return_role` 必須由當次可引用原件的實際進入角色建立，直接記該 entry role；不得預填 `LIST`、`POST_DETAIL` 或其他期待值，也不把任一角色當常見預設。`LIST` 與 `POST_DETAIL` 等都是合法角色，只有原件支持的入口角色可供返回後核對。錨點供返回後核對，不是可重用座標或點擊指令。

不要求進入 viewer 前已看見返回控制。進入 viewer 後，先觀察 app／window、頁面角色、焦點及控制歸屬。確認返回控制屬目前 viewer、其語意與 entry anchor 相符且定位有效後，才建立下載 intent 或開始下載交易；實際是否回到 `expected_return_role` 只能在返回後判讀。單獨的「關閉按鈕」標籤不足以證明控制歸屬或作用。

### 返回一次並重新觀察

輸入前保存 viewer observation、控制所屬視窗／區域、AX role 與父層，或視覺控制區域、焦點、座標空間及當次映射。實際 target 必須與映射後的候選點一致。這些證據只能支持一次輸入的定位依據，不證明 OS hit-test 或 LINE 已接受。

只送出一次已證明的返回輸入，隨即唯讀觀察。核對頁面角色、列表／貼文身分與來源錨點，並分開判讀：

頁面角色須由當次可引用原件正面支持。長貼文占滿 viewport、搜尋列／卡片標頭／返回控制不可見，均不足以判 `POST_DETAIL`，也不證明返回控制不存在。同一 app／window、與入口相符的可捲動 List／多 row 結構、可核對同一 scroll 位置及卡片 anchor／前後卡片連續，且沒有相反正面角色轉換證據時，判 `LIST`；hash、row 結構或單一 scroll 數字均不能單獨決定角色，scroll 變動也不單獨證明角色轉換。`POST_DETAIL` 須有當次原件正面支持，不要求另開視窗，也不假定所有 LINE 版本有固定詳情頁 UI；即使同一視窗也可能有正面角色轉換，須照實記錄。證據不足或矛盾時記 `page_role=UNKNOWN`、`return_result=RETURN_NOT_OBSERVED`；若已正面觀察仍是 viewer，保留 `page_role=VIEWER` 並記 `RETURN_NOT_OBSERVED`，不把已知角色洗成 `UNKNOWN`。

- `RETURNED`：符合 `expected_return_role`，且 entry anchor／來源連續性成立。一次返回符合時即完成這一層判定，不為尋找虛構的第二層再關閉。
- `RETURN_NOT_OBSERVED`：最新畫面仍是 viewer、頁面未變，或觀察不足以判斷一次返回是否生效。這不是 `ENTRY_LOST`，不得據此宣稱入口已遺失。
- `ENTRY_LOST`：充分觀察正面顯示頁面角色或身分已失去，例如變成聊天、另一個列表／貼文，或 entry anchor 已不可連續核對。`INPUT_UNAVAILABLE` 另記，可與上述狀態同時成立。

每次只返回一層；上述任一未達 `RETURNED` 即停止原方法，不得連按 Escape、Command-W、關閉或取消，也不得換猜測鍵、舊座標或相簿入口。

### 分開記錄頁面、前景與能力

| 欄位 | 值 | 證據 |
|---|---|---|
| `page_role` | `LIST`、`POST_DETAIL`、`VIEWER`、`CHAT`、`UNKNOWN` | 當次可引用 AX／畫面正面支持的角色；充分截圖可作直接證據。hash、row 結構、scroll 或單一缺項不能單獨決定；矛盾或不足記 `UNKNOWN`。 |
| `foreground` | `VALID`、`INTERRUPTED`、`UNKNOWN` | app／window 綁定、交接及連續性 |
| `observe_capability` | `AVAILABLE`、`UNAVAILABLE`、`UNKNOWN` | AX／截圖的當次可用性與範圍 |
| `input_capability` | `AVAILABLE`、`UNAVAILABLE`、`UNKNOWN` | 工具文件支持的輸入能力與原始回傳 |

`ENTRY_LOST` 表示頁面角色或指定列表連續性失去；`INPUT_UNAVAILABLE` 表示輸入通道不可用。兩者可同時成立，分開記錄。`noWindowsAvailable` 只記實際錯誤欄位；底層原因維持 `UNKNOWN`。

### 有界恢復階梯

1. 若觀察能力可用，保存當次 AX／截圖、app／window 綁定與錯誤原件；先不輸入。
2. 若前景有效、來源仍可證明是同一指定列表所屬聊天、輸入通道可用，且 Notes 控制在當次可唯一辨識與定位，可用該控制導覽一次。AX 缺失時，必須有足夠的視覺歸屬、控制區域與座標映射；不得搜尋或選擇其他聊天室。
3. 若輸入通道失效，只使用當次工具文件支援的唯讀 app／window 列舉與 handle 重新取得。這是 CUA reacquire；不等同 notes `bind`，也不證明輸入能力已恢復。
4. 每一步後重新觀察 app／window、前景、頁面角色、觀察及輸入能力。只有新證據顯示輸入能力恢復，才可考慮下一步；重新映射後才可定位控制。
5. 沒有新證據不重試。同根因最多三次有證據嘗試；連續兩次沒有新資訊即停止。不得用換 API、全螢幕切換、測試按鍵、舊座標或反覆 reset 繞過失效通道。
6. 無法恢復時進入 `HANDOFF_REQUIRED`，停止 GUI 輸入，只請 Owner 把同一指定記事本列表帶回前景並交接。

### 重新交接與帳本 Session

同一有效前景內重新取得 CUA app／window handle，沿用目前 notes 帳本 Session，不重跑 `bind`。前景中斷後由 Owner 重新交接，必須建立新的 notes 帳本 Session ID，即使仍是同一對話或 app；取得新 observation 並重新核對列表身分。

新 `bind` 不會自動中斷舊 open scan。新 Session 先唯讀查歷史並核對當次新前景與列表，成功 `bind` 後才收斂舊 attempt 與命名交易；若仍有 open scan，再明確 `scan interrupt`，然後以普通 `scan start` 重新完成卡片覆蓋。不得以 restart 或 recovery scan 繞過普通入口阻塞，也不得用新 scan 解鎖 UNKNOWN。保留帳本中實際的完成、ACTIVE 與待細盤分類；待盤貼文不得改成 `NO_MEDIA` 或宣稱完成。

同一有效前景的 reacquire、viewer reopen 與新 notes Session 都不重置同一 `list_key + post_key + media_key` 的 reveal 候選額度。新 Session 必須先找回該媒體的 `candidate_ordinal`、`prior_candidate_refs` 與 `budget_after`；查不到或互相矛盾時停止，不假設額度為 0。


## 觀察與命題分界

GUI 觀察只保存當次真正取得的來源，不用事後推測補齊。每次與下載控制、chooser 或檔案歸屬有關的觀察，都要依 [證據範本](evidence-template.md) 記下來源、範圍與未知值：

- **來源與範圍。** 記明是 AX、app-bound／桌面截圖、Computer Use 原始回傳或真人觀察，以及工具名稱；另記 AX／CUA client、API scope、app／window 綁定、role／children 來源、觀察涵蓋的視窗／區域、影像像素尺寸與實際可視範圍。來源邊界不是畫面全貌。同一 viewer 的多次 AX 輸出相同，不得推定工具列或其他控制未變；截圖與 AX 的差異只支持各自來源，不能互相補成存在或不存在；缺 client／綁定／原始來源時記 `UNKNOWN`／`BLOCKED`，不預填 G0 的範圍對照。
- **popup／chooser 的缺席。** 只有當觀察範圍足以涵蓋該 popup／chooser 時，才可記 `NOT_OBSERVED`；範圍不足、視窗被遮擋或來源不合成獨立 popup 時記 `UNKNOWN`。截圖中看不到不等於 App 沒有該控制，也不證明它存在。
- **時間與時鐘。** 記可取得的觀察／輸入時間、時鐘來源與時區；沒有工具時間或可信時鐘來源時記 `UNKNOWN`，不以檔案 mtime 冒充操作時間。
- **座標空間與映射。** 分別記截圖像素、視窗點數、螢幕座標、視窗位置、縮放與映射識別；確認從原始座標到當次輸入位置的轉換。任一項缺失或畫面狀態改變就失效，不輸入、不猜全域座標。
- **控制可見性。** 記頁面角色、焦點、控制所屬流程／物件、可見與可用狀態。只有當次範圍與映射都成立才可說 `VISIBLE`；即使可見，也只支持一次輸入的定位依據，不證明命中、App 接受或派送。
- **原始輸入回傳。** 下載控制、路徑輸入與 chooser 最終確認各自保存工具、動作、目標及原始成功／錯誤／逾時回傳。錯誤不證明未送出，成功也不證明 App 接受或下載完成。
- **chooser／檔案歸屬。** chooser 的延遲出現不證明不存在；只有視窗／process、來源 viewer 與 attempt 能唯一對應時才可使用。檔案必須能歸屬同一 attempt 與原目的地；名稱、出現順序、單一 hash 或相鄰時間都不能單獨建立歸屬。

定位、input receipt、App acknowledgement、下載結果、檔案驗證與 completion 的允許行為見 [證據與允許行為矩陣](verification-and-recovery.md#證據與允許行為矩陣)；下載控制與 chooser 的次數及停止順序只依 [下載與 notes CLI](download-and-ledger.md)。

## 證據界限

本文件描述的是待驗證／可重用的操作規則。沒有本次正式記事本 GUI 任務、有效前景、逐次觀察與檔案證據時，入口、捲動、viewer、混合附件、chooser 及跨 Session 恢復全部 `NOT_RUN`；不得引用相簿的成功案例或錄影觀察宣稱記事本 E2E 已通過。
