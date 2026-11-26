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

- 可靠依據：本次連續入口、當次畫面／AX 的列表角色、前後導覽連續性。既有列表另以相符的本地帳本為佐證；**相符既有帳本不是新列表的前置**，新列表由當次連續入口、已落地觀察 evidence 與全部 N 份已註冊候選之正面排除成立。
- 不足依據：群組或列表的顯示名稱、中文 OCR、貼文文字、相同日期、相同媒體張數、相同封面。
- 顯示名稱限制：**`display_name`／中文標題既不得單獨認領既有帳本，也不得作為必要匹配門檻或過濾鍵**；查無同名帳本（「零同名候選」）不等於身分不符或候選歧義，不得據此停止或要求重新交接，仍須完成全候選 `identity`／`posts` 核對後依[三路列表判定契約](download-and-ledger.md#候選帳本展開唯讀)處理。
- AX 標題限制：macOS LINE Desktop 的 AX Window title 常為空字串，列表節點也常是泛用元素；這是可存取性資訊有限，不是工具錯誤，也不阻止列表核對。須以已落地讀回的同次截圖＋AX（視窗頁首視覺脈絡、記事本分頁、首屏多張可見貼文卡片的順序／日期／摘要脈絡／媒體縮圖排列）與全部候選帳本之 `identity`／`posts` 錨點（必要時既有事件 `statement`）交叉核對；新列表於 AX 標題空白時如實記 `ax_window_title=EMPTY`，仍不得單憑中文名稱、OCR、單一日期或單一張數認領。候選展開與三路判定見[啟動與帳本對帳](download-and-ledger.md#候選帳本展開唯讀)。
- 疑似另一個列表或無法證明連續性時，不以「看起來一樣」合併；保留斷點，重新交接或問 Owner 具體是哪一份列表。

### 貼文

- 可靠依據：卡片在連續清單中的位置、與前後卡片的共同錨點、日期、可見文字脈絡、媒體縮圖排列及更多指示的交叉。
- 不足依據：單一日期、單一摘要、單一縮圖、總媒體數、畫面序號或貼文顯示名稱。貼文內容被編輯、卡片重排或刪除時都不能自動認領舊完成。
- Agent 保存貼文層觀察，讓 CLI 產生 `post_key`；`post_key` 不是中文標題或畫面序號。來源順序是另一個可更新欄位，不能把順序變動當成新貼文。
- 當次多訊號觀察正面確認某張來源卡對應既有帳本中未變動之歷史貼文時，必須以程式從獨立核對過的最新完成掃描（`scan COMPLETE` 事件）或既有歷史事件**原樣抽取**該篇穩定 `identity` 物件與預期 `post_key`；禁止人工轉錄、摘要、截斷或重寫 `visual_key`／`signals.text_anchor`，並於 `page` 提交時以 `--assert-post-keys` 宣告。進行中或曾中斷掃描的混合 `summary` 僅供定位候選；對帳失敗頁或未收尾中斷頁的 row 不得作為既有歷史 `identity` 或預期鍵來源。
- **跨輪文字編輯：** 若編輯發生在新一輪掃描開始前，且當次多訊號觀察能唯一確認是同一篇歷史貼文，本輪 `page` 首次出現時仍原樣沿用該篇既有穩定 `identity`，並以 `--assert-post-keys` 斷言原 `post_key`；實際文字變更另記於當次新觀察與既有 `post` 細盤欄位（`--text-sha256`／`--date-summary`／statement），不掩蓋變更，也不為更新文字重寫身分或放任 `media_key` 漂移。
- **無法唯一核對或媒體對應歧義：** 不得硬套舊 `identity` 或自動認領舊完成；依[變動與隔離](#變動與隔離)保護該篇並停止該篇新派送，其他已核對且無列表級歧義的貼文仍可繼續。
- **本輪掃描進行中覆蓋漂移：** 若相對本輪已提交頁發生新增、刪除、重排或編輯，依[finish 前原件重核與來源變動](#finish-前原件重核與來源變動)保留前後證據並停止 finish／新派送，不以舊 identity 吸收當輪變動。

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

在產生 `--posts` 後、呼叫 `notes page` 前，先留存本次提交前最後一次序列讀回 `summary` 的 `expected_tip` 基準。overlap 列須以前一頁成功讀回的本輪 `page` row 原樣取值；既知歷史貼文列（未變或已唯一確認為同一篇之跨輪文字編輯）須從獨立核對過的完成掃描／既有歷史事件原樣取值，排除失敗頁／未收尾頁 row；僅確實新發現貼文建立新 `identity` 並於對應槽位填 `null`。呼叫 `page` 時傳入與 `--posts` 等長的 `--assert-post-keys`，依序宣告每列預期 `post_key`（或 `null`），由 CLI 在寫入永久事件前 fail-closed 攔截漂移。遇 `PAGE_POST_KEY_MISMATCH`／`INVALID_ASSERT_POST_KEYS` 拒絕，一律依 [下載與 notes CLI](download-and-ledger.md#cli-共同契約) 的統一拒絕與重試證據契約處理，本節不重複細節。

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

本節是穩定前置、當次方法與可核對額度、既有 intent 邊界、intent 後單一路徑、同次 after 與一次 guarded click 的唯一決策本文；其他文件只記證據、交易或投影，不另定候選次數，也不改變既有 `STOPPED`／`NOT_SENT` 精確恢復與 restart 規則。B1 判讀完成後，必須再以當次已讀回 observation、app／window binding 與 decision 呼叫 [Intent 前下載就緒 gate](evidence-template.md#intent-前下載就緒-gate) 的 `notesIntentDispatch.checkDownloadReadiness({app, observation, windowBinding, branch, decision})`。控制可見時先以 `DIRECT` 檢查一次；另有可獨立稽核的當次安全 reveal 時，再以 `REVEAL` 檢查一次。`REVEAL` 的 `STOP` 不會抹除合格的 `DIRECT`；控制未見時則以 `REVEAL READY` 為進入 intent 的必要條件。兩者即使都 READY，也只建立一次 intent，並保留成功的 `REVEAL` READY 結果供本輪 intent 後使用，不因備選而送出 preflight input、capture、固定 slot 或候選 request。兩項皆不足時保留該項與 `blockers`，不建立 intent／attempt、不送 reveal、不改寫 outcome、也不消耗 v5；READY 仍只是 intent 前置，不是 GUI 派送授權。可執行 composition `persistRevealWithDirectAfter` 見 [單次輸入與直接 after 觀察](evidence-template.md#單次輸入與直接-after-觀察)。目前範本的 reveal 只支援已選縮圖的安全邊緣。即使當次工具文件支持無點擊 hover，也須有能維持同次 input → after 的既有可執行途徑。若當次方法無法通過就緒檢查，保留具體阻塞。

- **AX 與充分視覺分開但仍 fail-closed。** 下載控制可由當次 AX 節點或充分視覺映射定位；AX 缺節點不否決充分視覺，截圖也不得補成 AX 節點。無論使用哪一來源，都須由當次原件正面核對目標 viewer／選中媒體涵蓋、控制可見與啟用、流程／物件歸屬、選取、幾何、像素／點數／螢幕座標／視窗位置／縮放／映射識別及狀態仍有效；舊座標、過期截圖、只見箭頭或外觀就猜點仍不成立。這種定位只支持一次輸入，不證明命中、App 接受或派送。
- **播放三維分開判定。** Agent 的播放輸入恆為 `NONE`：不播放／暫停、不拖曳時間軸、不切換倍速、不以點擊內容切換播放控制、不檢視內容，也不為種類或播放狀態取證而操作 viewer。來源播放狀態只由當次已有、可引用的 AX／視覺觀察正面記為 `NOT_PLAYING`、`AUTOPLAYING` 或 `UNKNOWN`；不為確認狀態新增輸入，且不得把 `UNKNOWN` 當成 `NOT_PLAYING`；此處 `UNKNOWN` 只指播放觀察，不是六類業務狀態或派送 outcome。來源為 `AUTOPLAYING` 或 `UNKNOWN` 時，以 B1 已保存的本次 before 或前次有效觀察，和當次原件正面比對同一 viewer 的來源、選取、viewer 區域邊界、視窗位置、縮放及映射。只有比對一致才能續用 B1；僅未見漂移不足以通過。沿用 intent 前後的取證順序，不額外擷取畫面追查播放。來源切換、選取改變、幾何／映射漂移、控制被播放 UI 遮住或證據不足時立即停止該項輸入並如實記漂移／證據不足；不追認舊 attempt，也不把自動播放、播放結束或內容畫面當成派送、完成或來源種類證據。
- **先核對穩定前置。** 在 intent 前完成歷史／資格／完整盤點與目標媒體細盤核對、viewer 三層身分、實際 entry anchor 與 `expected_return_role`、同一有效前景、可歸屬返回控制、當次座標映射，並排除 chooser、活動下載、舊無 outcome／未解輸入、其他未有效隔離的未決 attempt、pending naming、來源／選取／幾何／映射漂移或任何非 `NONE` 的播放輸入。舊 `UNKNOWN` 或舊無 outcome 必須先依 Skill「結果不明的單次恢復」分流；只有該媒體已持久隔離、目前 Session 已完成新的普通完整掃描與細盤，才可對新空白 attempt 套用 B1。精確 restart 的 Owner 明示同意、scope、confirm 後新 recovery scan 與舊歷史保留規則照舊，不能由本節解鎖或重置額度。
- **intent 前的方法與額度分流。** 最新充分觀察正面支持記事本下載控制可見、歸屬、啟用與映射時，`DIRECT READY` 即可備妥 intent，之後仍須在 intent 後重取一份當次畫面；同一份可見 evidence 若另有同一 viewer／選中項的安全 reveal、完整額度與下一個 ordinal 可用候選，也可獨立取得 `REVEAL READY` 備用。備用的 reveal 檢查失敗只保留其 blockers，不使可見的 `DIRECT` 失效。工具列未見時，只有 `REVEAL READY` 才可建立 intent。方法與安全區只以當次唯讀觀察建立，不為通過此 gate 先送 reveal；無安全方法、無可用候選、額度不明、選取或歸屬不明，且沒有合格 DIRECT 時，應在 intent 前停止，不得先用 hover／click 探索，也不得預建任何未派送的候選或 input request。即使 DIRECT 與 REVEAL 都 READY，仍只可寫一次 intent。控制可見分支若在 intent 後轉為隱藏，而 intent 前沒有已稽核的 `REVEAL READY`，仍在該處停止。上述語意判讀後才呼叫本節開頭的 `checkDownloadReadiness`；符合當次可見／隱藏條件的 READY 才可進既有 intent，全部 STOP 依下一條局部與全域規則處理。
- **局部 B1 阻塞與其他合格項。** 若某媒體在 intent 前因直接控制、隱藏方法、額度、歸屬、映射或 `checkDownloadReadiness=STOP` 而未成立安全建立 intent 的 gate，不建立 intent、不送 reveal，保留該項未完成與具體阻塞；不得因此建立或改寫下載 attempt 的 `UNKNOWN`／`NOT_SENT`、不消耗該媒體的 v5 額度，也不記排除或完成。沒有全域 blocker，且進入 viewer 前保存的 entry anchor／`expected_return_role` 與當次可歸屬返回控制支持一次一層的可靠返回時，可回到已核對列表，重新核對後一次一項處理其他合格項。未隔離 `UNKNOWN`／無 outcome、活動下載、pending naming、`LOCAL_CHANGED`、列表覆蓋或身分不明、前景中斷或返回契約歧義，仍是停止所有新派送的條件，不以排程跳過或解鎖；其他項的 readiness 為 `READY` 也不能解除這些全域 blocker。
- **固定額度與候選前稽核。** 以 `list_key + post_key + media_key` 為 reveal scope；同一 scope 跨 viewer、reopen、Session 與 restart 累計最多兩個已派送 reveal 候選，attempt 內至多一個。輸入前保存並讀回 `candidate_ordinal`、`prior_candidate_refs`、`budget_before`、本次方法、安全作用區、選取、before 原件、映射與 input request；輸入後保存 `budget_after`。已送出 `0` 次且同一 scope 完整查無先前已派送候選，只可用 `candidate_ordinal=1`、`budget_before=0`；已送出 `1` 次時，只有原候選 request／raw／after 完整、未決為零、連續性成立，且有改變既有決策 gate 的相關新證據，才可用 `candidate_ordinal=2`、`budget_before=1`。已送出 `2` 次或計數不明者沒有 reveal 路徑；目前控制直接可見且其他 gate 成立時，仍可走直接路徑。任何開始送出的 hover／pointer move 或 `NAVIGATION` 均耗額，error、timeout、crash、缺 receipt 或結果不明也照算，不能以缺證退回較低計數。候選 2 的新證據及排除條件見下一段。
- **候選 2 新證據的例示。** 可接受的是當次工具文件正面證明原本未查明的無點擊 hover（不帶 click）能力，且同一 viewer／選中項有可歸屬、非播放的安全作用區與完整當次映射，因而實際改變 reveal 方法或映射 gate；這仍只讓符合原條件的 `candidate_ordinal=2` 可被評估，不保證舊項恢復。不可接受的是單純有新文件存在、fresh capture／reopen、時間流逝、只換點、事後補 request，或重述舊 refs／舊 capture 而沒有改變方法或映射。任何新證據都不豁免完整 prior refs、未決為零、安全隔離、同一 scope 累計額度與 intent gate；無合格新證據就保留該項未完成。
- **用既有 CLI 保留本項。** intent 前先解析帳本、照片 root、notes CLI、私有 task／證據父目錄、兩條路徑所需的 statement 與 helper 呼叫架構及精確 argv，並完成上述 B1 語意判讀與 `checkDownloadReadiness`。只有 helper 回 `READY` 才可執行一次既有 `intent`；`STOP` 不呼叫 CLI，保留該項與 blockers。成功後讀回唯一 attempt、原 event、三層身分、Session、新空白 staging 的精確路徑及身分、`save_all_limit=1`、`save_all_count=0` 與禁止重送紀錄。這仍是一筆 `status=UNKNOWN`、`dispatch_authorized=false` 的既有 intent，不是新 ledger 狀態、新事件、新授權或「prepared 可恢復」語意；intent 本身不證明控制已按、下載已開始或已送出。CLI／讀回失敗、衝突或前景中斷時零 GUI 輸入，保留可得證據並依既有規則停止。
- **intent 後先取一份 fresh observation，再只選一條路徑。** 讀回成功後只取得一次最新的同一 app AX／截圖原件，重新核對有效前景、同一列表／貼文／媒體／viewer、返回控制、播放輸入仍為 `NONE`、來源播放狀態已按上列記錄且無漂移、無 chooser／活動下載／未解輸入，以及 intent 的三層身分與原 staging。控制正面可定位、歸屬、啟用且映射成立時，走直接路徑，不再 reveal；不得只因備選 REVEAL 曾 READY 就改走 reveal。唯有在充分涵蓋的 fresh observation 中確定控制未見，且事前 `REVEAL READY` 仍存在、fresh observation 與事前原件不同、window binding 未變、scope／候選 id／ordinal／budget／選取仍一致、無 chooser／活動下載／未解輸入、額度仍成立，並由 Agent 正面確認同一 viewer／三層身分／前景與映射無漂移時，才把這份 fresh observation 交作 reveal 的 before。控制有歧義、映射不足、最新欄位不足、已有下載控制呼叫或 outcome 時停止，不可換路。不得返回、reopen、換 viewer、重新 discovery、換 Session 或為尋找控制而新增輸入。
- **單次 reveal 與同一份 after。** reveal 只可在上述同一新 attempt 內送一次。以 `persistReveal({preIntentReveal, beforeObservation, windowBinding, ...原參數})` 呼叫：`preIntentReveal` 是 intent 前的 REVEAL READY 結果，`beforeObservation` 是 intent 後唯一的 fresh 原件，`windowBinding` 屬於該原件。helper 先用原 `checkDownloadReadiness` 重核 fresh before 的截圖、AX、定位引用、座標空間、有限安全區與嚴格內點，並機械比對事前結果、兩次 observation、window binding 及 request 的 scope／候選 id／ordinal／budget；任一缺失、相同 observation、binding 改變或 request 漂移都零 input 拒絕。request 仍須關聯 attempt／intent event、prior refs、ordinal／budget、before、選取、安全區與映射。通過後使用固定 slot `notes-reveal-c2-<attempt_id>`：`c2` 是固定檔名，實際 `candidate_ordinal` 只能寫在 request，不得改成以 ordinal 命名的另一個 slot；沿用本 attempt 的 task／input 目錄，由 `persistRevealWithDirectAfter` 內的 `persistSingleInput` 以獨占方式建立並逐 bytes 讀回 request，再呼叫一次當次工具文件支持的無點擊 hover，或已選 filmstrip 縮圖的非播放安全邊緣 `NAVIGATION`。input 後不離開同一 callback，不開新 shell、不插入模型回合或固定等待，直接對同一 app 取得 after，保存 input raw／diagnostic 與同一份 after bytes，並保留現有 `fail_closed`／`afterObservation` 回傳。這是兩個相依 API，不保證 atomic、固定完成時間、原生 hit-test 或工具列壽命；input error／timeout、after error、缺 raw／after、保存失敗或 crash 都算該次已派送並立即停止，不得重拍、重送、換 slot 或建新 attempt。
- **同次正面 after 才送出一次下載。** 直接路徑使用 intent 後最新的當次原件；reveal 路徑只使用剛才同一次 invocation 保存的 after，不得重取、補拍或混用舊 after。Agent 在該份原件上正面確認控制可見、歸屬、啟用、映射、viewer、三層身分、前景、播放輸入仍為 `NONE`、來源播放狀態已按上列記錄且無漂移，全部成立才組出下載 request，連同該份原件與 live handle 立即呼叫既有 `persistGroundedDownloadClick` 一次；由 helper 以 `wx` 獨占建立並逐 bytes 讀回固定 `notes-download-<attempt_id>` slot，讀回成功後才依該 target 呼叫。Agent 不得先手動建立該固定檔或先寫 request，否則 helper 的獨占建立會拒絕。helper 不選控制，也不提供 native hit-test／receipt；Agent 判讀仍需模型時間，因此不承諾跨越該段時間的固定時效。任何下載 helper 呼叫一旦開始、API error／timeout、結果不明或 chooser 出現，即永久關閉本 attempt 的 reveal 與後續控制；不得再做第二個下載控制、重播 reveal 或換入口。
- **其餘 intent 後封鎖與結束。** intent 讀回後不得再建立另一個 attempt、重跑 discovery、返回／reopen、用新 Session 接續同一 attempt 或把舊點位當本次定位。每個 scope 的兩次 reveal 上限不可被一般查證次數、fresh capture、restart 或新 Session 擴充；既有 `STOPPED`／`NOT_SENT` 精確恢復與精確 restart 仍循原授權，但舊 `UNKNOWN`、舊無 outcome crash window 或額度不明不因此解鎖。第一筆 outcome 仍依真實結果，證據不足為 `UNKNOWN`；已有 outcome 才可依原規則 reconcile，不以控制缺席、零計數、空 staging 或缺 marker 改寫成 `NOT_SENT`。
- **狀態真值。** `TOOLBAR_VISIBLE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT` 與導覽 `UNKNOWN` 是 statement 結論，不是六類業務狀態；intent 前媒體仍為 `PENDING`，intent 後的結果仍按 outcome／reconcile。`TOOLBAR_VISIBLE` 支持當次直接定位；`TOOLBAR_NOT_SHOWN` 只表示該 bounded observation 未見，不證明 transient 從未出現或 LINE 失敗；`REVEAL_TRANSIENT` 只描述曾見後又消失。隱藏分支是否可進 intent 完全依本節的方法與額度 gate；控制缺席本身不是 `EXCLUDED`、`NO_MEDIA`、下載失敗或 `NOT_SENT`。
- **下載控制定位。** 若以座標點擊，必須使用 [單次 CUA 輸入保存 helper](evidence-template.md#單次-cua-輸入保存-helper) 的 `persistGroundedDownloadClick`，並使用本 attempt 唯一的 `notes-download-<attempt_id>` slot。Agent 仍自行判讀控制區域、歸屬、候選點、映射與下一步；helper 以 `wx` 獨占建立並逐 bytes 讀回 request，再以持久讀回的 target 呼叫 `app.click([x, y])`，不負責找控制、不提供 native hit-test／receipt。普通導覽、返回與 chooser 不經此 helper；helper 不可用、欄位缺失、slot 已存在、讀回不符或回傳 blocker 時停在輸入前，不得改用任意 invoke、手動 app.click、舊點擊入口或另一個 slot。

若貼文只有文字而沒有任何照片／影片，標記貼文層 `NO_MEDIA`，不做下載 attempt，也不計入六類媒體完成。若看不到完整媒體、viewer 總數與貼文數量矛盾、更多指示無法展開或返回後網格變動，保留該篇待確認；只有列表級覆蓋仍成立時，保護該篇並可繼續其他已核對篇。

### restart 確認後的來源重核

- `restart confirm` 後不得沿用確認前的 page rows、cursor、舊 scan 或舊 viewer 當作新 attempt 的來源證據。必須從頂端到底端重新觀察同一個已確認列表，完成新的完整 recovery scan，才可逐項建立 restart intent。
- 精確 `restart confirm` 前的既有 `UNKNOWN`，可在 confirm 後由 scope 的第一個新 v3 attempt 首次替代；confirm 後同批次任何新增 v3 attempt 尚無 outcome 或結果 `UNKNOWN`（含後來被 supersede 的舊版）時，停止新 intent 與 activation，先依既有命令查原 attempt；若現行 latest-only `reconcile` 無法處理已被 supersede 的舊版，保留證據、回報具體資料阻塞，不反覆呼叫或擴寫更正入口。`STOPPED`／`NOT_SENT` 依既有授權恢復；`DOWNLOAD_FINISHED` 用原 attempt 基本檢查，不能被這項 scope gate 誤擋。
- 新 attempt 仍要當次列表→貼文→viewer→下載控制→chooser→精確 raw 目的地的連續證據；使用新的空白 staging、當次 viewer／chooser 與重新取得的定位。舊 handle、舊路徑、舊座標或舊 chooser 都不得重用。
- 取消或關閉舊 chooser 只代表該次取消輸入；不證明先前的下載、寫入或晚到輸入已停止。舊 raw／舊版本可能仍有晚到 bytes，保留在原區並記錄，不合併到新 candidate，也不據此改寫新版本。
- 再次中斷後從 `OPEN_BATCH` 找回同一批次時，已驗證 candidate 與歷史仍保留；只對未完成或結果不確定的項目，依上述 scope gate 處理。scope、來源身分、目的地或版本策略改變時，停止並重新預覽、取得新的 Owner 明示同意。

## 導覽與輸入紀律

- 每次輸入前確認授權、有效前景、頁面角色、焦點、目標控制項及預期結果；輸入後重新觀察，不以 API 回傳、OS 慣例或舊座標代替畫面證據。
- **先判讀定位來源，再輸入。** 使用 AX 元素索引時，先讀最新完整 AX，或能由該完整樹連續還原的最新 diff，才選定元素；在當次操作紀錄連同原件引用記下「索引→目前角色／所屬列表→預期效果」。捲動前反查該索引仍是當前列表或其捲軸，不能只因前一次數字可用就沿用；若已變成視窗按鈕等其他角色，該目標不可用。不要把取得新 AX 與使用尚未核對的舊索引輸入合併成一次預寫呼叫。AX 回傳 `AX:DIFF_NO_CHANGE`（`full_tree=false`、`diff_only=true`）只代表變更通知，不是完整目前樹；不得據此選定索引或沿用舊索引，須依[證據範本](evidence-template.md#cua-觀察原件落地)重取完整 AX。充分視覺定位不要求 AX 節點，截圖也不得補成 AX 節點；視覺路徑仍須有當次原件、viewer／控制歸屬、啟用、選取、幾何與完整座標映射全部成立。AX 索引失效時重取完整 AX；視覺映射失效時重取當次視覺原件並重建映射，不沿用舊座標。
- 捲動的方法與單位依當次工具文件；macOS native scroll 使用 page count，不從型別範例猜 pixels、捲軸值或未支援按鍵。原始輸入回傳與事後畫面一併保存；工具拒絕或角色不符的呼叫不算有效邊界探測，停止依賴該前提的操作，不換入口繞過。
- 座標、AX 元素與快捷鍵只在當次映射成立時使用。視窗移動、縮放、換頁、popup 重開、前景中斷或觀察來源變化都會使舊定位失效。
- 主視窗截圖／AX 可能漏掉獨立 popup 或 chooser；這不代表控制項沒有出現。必要時依當次 Owner 授權與平台能力使用指定區域的唯讀截圖，只保存任務需要的私有區域，不上傳外部服務。
- Viewer 已就緒且媒體身分成立、控制未見時，先依 [B1](#目標與下載控制就緒b1) 檢查 intent 前的隱藏分支：只有當次安全方法已歸屬同一 viewer／選中項，且 ordinal／前次引用／新證據條件與 reveal 額度均成立，才可進既有 intent；否則停在 intent 前。無點擊移鼠能力未查明記 `UNKNOWN`、明確不支援記 `NOT_AVAILABLE`，不得猜 API。不得在任何 intent 前先送 hover／click，也不把能力不足說成控制不存在或 LINE 失敗。
- 對可用來源，在同一媒體、同一幾何下做最小對照並保存各自原件。記錄來源、觀察時間、焦點、hover／其他輸入、幾何及變化／漂移；不同來源不是原子快照，須保留時間差並核對媒體與視窗連續性。需要比較狀態時，保留等時長靜置對照；這種唯讀對照不授予 reveal 或額度。任何 hover／pointer move 與 selected-filmstrip `NAVIGATION` 都只在 B1 的 intent 後單一路徑送出，不能提前探測。
- 除 [B1](#目標與下載控制就緒b1) 明列的 intent 後單次 hover 與 selected-filmstrip `NAVIGATION` 外，不可額外 click 探索，且候選不是 hover 或下載控制。不得切換五格反覆查找；控制歸屬、作用或下載映射未證明時不得按下載控制，但工具列隱藏分支仍只有在 B1 的安全方法與額度均成立時才可進 intent。不得重播 reveal／intent、使用舊點位、以固定等待當成修復，或把 fresh capture 本身當成新證據。
- 任何下載控制、chooser 與「確認」都是獨立輸入；不要用反覆點選、猜 Return 或重開選單查證。下載派送限制與 notes CLI 交易見 [下載與 notes CLI](download-and-ledger.md)。
- 一般查證維持同一根因最多三次有證據嘗試，連續兩次沒有新資訊就停止相同方法；B1 的每個 `list_key + post_key + media_key` 最多兩次已派送 reveal 候選，跨 viewer、reopen、Session 與 restart 累計，不可被其他查證次數擴充。更換觀察來源只有在帶來決策相關新資訊時才可支持下一步，不得改下載入口、跨列表或繞過工具拒絕。同一 `-10005 noWindowsAvailable` 錯誤下輪換截圖像素／螢幕點／視窗相對座標空間不是新方法或新證據，也不是有效映射修正；兩次無新資訊即停（見[有界恢復階梯](#有界恢復階梯)）。

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
| `foreground` | `VALID`、`INTERRUPTED`、`UNKNOWN` | app／window 綁定、交接及連續性；`VALID` 僅覆蓋綁定與交接，不代表頁面角色為 `LIST`、入口仍可用或控制可達，可與 `ENTRY_LOST` 同時成立。 |
| `observe_capability` | `AVAILABLE`、`UNAVAILABLE`、`UNKNOWN` | AX／截圖的當次可用性與範圍 |
| `input_capability` | `AVAILABLE`、`UNAVAILABLE`、`PARTIAL_AX_ONLY`、`UNKNOWN` | 工具文件支持的輸入能力與原始回傳；`PARTIAL_AX_ONLY` 表示 AX 元素／選單輸入可用但 pointer 座標通道不可用，僅視覺可見且須座標點擊的控制不得當 `AVAILABLE`，該路徑按 `INPUT_UNAVAILABLE` 處理。 |

`ENTRY_LOST` 表示頁面角色或指定列表連續性失去；`INPUT_UNAVAILABLE` 表示輸入通道不可用。兩者可同時成立，分開記錄。`noWindowsAvailable` 只記實際錯誤欄位；底層原因維持 `UNKNOWN`。`foreground=VALID` 只證明 app／window 綁定與交接仍有效，不能單獨支持入口可用；`PARTIAL_AX_ONLY` 也不是完整輸入能力。

### 有界恢復階梯

1. 若觀察能力可用，保存當次 AX／截圖、app／window 綁定與錯誤原件；先不輸入。
2. 若前景有效、來源仍可證明是同一指定列表所屬聊天、輸入通道可用，且 Notes 控制在當次可唯一辨識與定位，可用該控制導覽一次。`PARTIAL_AX_ONLY` 不算輸入通道可用；AX 缺失時，視覺路徑另需可送出的 pointer 通道，且必須有足夠的視覺歸屬、控制區域與座標映射；不得搜尋或選擇其他聊天室。
3. 若輸入通道失效，只使用當次 CUA 工具文件支援的唯讀 app／window 列舉與 handle 重新取得；只可呼叫文件明載的形狀，未記載的參數形狀（例如 `getApp({windowId})`）不得試探。這是 CUA reacquire；不等同 notes `bind`，也不證明輸入能力已恢復。`osascript`／System Events／外部 CGWindow 查詢不是 CUA reacquire，不得作為前景／handle 恢復或座標輸入依據，只能標為非 CUA OS 唯讀診斷。
4. 每一步後重新觀察 app／window、前景、頁面角色、觀察及輸入能力。只有新證據顯示輸入能力恢復，才可考慮下一步；重新映射後才可定位控制。
5. 沒有新證據不重試。同根因最多三次有證據嘗試；連續兩次沒有新資訊即停止。連續 `-10005 noWindowsAvailable` 下輪換截圖像素／螢幕點／視窗相對座標空間不計新方法或新證據，也不是映射修正；兩次無新資訊即停並依步驟 6 進 `HANDOFF_REQUIRED`。不得用換 API、全螢幕切換、測試按鍵、舊座標或反覆 reset 繞過失效通道。
6. 若當次 CUA 工具文件支援的唯讀 app/window 列舉與 handle reacquire 取得同一已授權列表，並以當次證據核對身分與有效前景，則恢復操作；無法安全取得時進入 `HANDOFF_REQUIRED`，停止 GUI 輸入並回報具體全域阻塞。重新取得同一授權前景後仍須重新核對入口，再從既有入口接續。

所有入口恢復之 pointer／導覽嘗試與 CUA handle reacquire 呼叫，均須透過 `evidenceTools.persistSingleInput` 保存原始 request／raw／diagnostic（見[單次 CUA 輸入保存 helper](evidence-template.md#單次-cua-輸入保存-helper)），不得僅留手寫 curated 摘要。

### 重新交接與帳本 Session

同一有效前景內重新取得 CUA app／window handle，沿用目前 notes 帳本 Session，不重跑 `bind`；此沿用只影響帳本綁定，不代表入口仍可用，仍須經 `captureAndPersist` 取得 `CAPTURE_BOUNDARY=RECORDED` 之新觀察（不得以 bare `persistObservation` 充當新觀察；`CAPTURE_BOUNDARY=MISSING` 不可採信，合併相同 bytes 時標 `STALE_CAPTURE_SUSPECTED` 並停止消費），重新核對頁面角色與入口連續性，`ENTRY_LOST` 仍停止派送。前景中斷後由 Owner 重新交接，必須建立新的 notes 帳本 Session ID，即使仍是同一對話或 app；取得新 observation 並重新核對列表身分。

新 `bind` 不會自動中斷舊 open scan。新 Session 先唯讀查歷史並核對當次新前景與列表，成功 `bind` 後才收斂舊 attempt 與命名交易；若仍有 open scan，再明確 `scan interrupt`，然後以普通 `scan start` 重新完成卡片覆蓋。不得以 restart 或 recovery scan 繞過普通入口阻塞；新 scan 本身不解鎖 UNKNOWN，只有同一媒體的安全隔離事件持久讀回後，才可由目前 Session 以新的普通完整掃描接續一次補下載。保留帳本中實際的完成、ACTIVE 與待細盤分類；待盤貼文不得改成 `NO_MEDIA` 或宣稱完成。

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
