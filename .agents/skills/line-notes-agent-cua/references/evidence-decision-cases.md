# 證據判定案例

本檔用固定案例檢查 [B1](gui-inventory.md#目標與下載控制就緒b1)、[證據與允許行為矩陣](verification-and-recovery.md#證據與允許行為矩陣)、[下載與 notes CLI](download-and-ledger.md) 與 [證據範本](evidence-template.md) 的判斷是否一致。全部案例都是文件規則的假設情境，不是本次 LINE 操作、真實停止 receipt、實機 `OBSERVED` 或 E2E PASS；案例中的時間、視窗與回傳若未由當次工具提供，實際紀錄必須寫 `UNKNOWN`。

## C1 intent 後控制才消失

- **前提：** 新 attempt 的 `intent` 已保存並讀回，尚未有下載控制呼叫或 outcome。intent 前依 B1 走可見控制分支，或已稽核同一 scope 的當次安全 reveal 方法與 `0`／`1` 額度；沒有 chooser、未解輸入或前景中斷。
- **觀察（假設）：** intent 後最新的同一 viewer 原件未見控制。若 intent 前只有控制可見而沒有稽核 reveal 方法／額度，這裡沒有可用的隱藏分支；若有稽核且方法／額度仍成立，才可評估一次 reveal。
- **可支持命題：** 只支持當下 bounded observation 未見控制與舊定位失效；不能證明未輸入、未派送、App 拒絕或控制不存在。只有 intent 前已完整稽核的方法／額度仍成立時，才有本 attempt 的一次 reveal 路徑。
- **允許動作：** 先停止任何下載輸入。隱藏分支的 intent 前稽核完整且仍成立時，使用 `notes-reveal-c2-<attempt_id>` 送一次 reveal、保存同一份 after；after 正面才把該份原件交給下載 helper 一次。方法／額度不明、intent 前沒有稽核、after 失敗或控制再消失就停止；第一筆 outcome 依實際證據，不足為 `UNKNOWN`，已有 outcome 才 reconcile。
- **禁止推論：** 控制隱藏自動授予或重置候選；intent 前先送 reveal；已有 UNKNOWN／crash 可用新例外；控制隱藏等於未命中／未派送；沿用舊座標；重開 viewer 或換相簿入口。
- **缺少證據：** 真正的 input 原始回傳、attempt／viewer 歸屬、chooser／進度、檔案或可歸屬終結訊號。

## C2 API error 但 chooser 出現

- **前提：** `intent` 已建立，下載控制只呼叫一次。
- **觀察（假設）：** input API 回傳 error；同一 viewer／attempt 隨後出現 chooser，且能讀回視窗／process、來源及精確暫存目的地。
- **可支持命題：** API error 只證明工具回傳；可歸屬 chooser 只證明 App 有階段性回應，仍不是下載完成。
- **允許動作：** 保存原始 error 與 chooser 證據；歸屬及目的地明確時，依固定順序輸入路徑並讀回，最終確認至多一次；之後等待可歸屬終結訊號與穩定檔集。
- **禁止推論：** error 必然代表未送出；chooser 出現即下載完成；因 error 再點下載控制；確認出處不明的 chooser。
- **缺少證據：** 下載終結訊號、穩定結果檔、檔案驗證與 completion；error 成因本身也可能仍未知。

## C3 Chooser 延遲或出處不明

- **前提：** `intent` 已存在，可能已有一次下載控制呼叫；尚無 outcome。
- **觀察（假設）：** chooser 在等待後才出現，卻無法可靠連回同一 viewer、attempt 或來源 process，目的地也不確定。
- **可支持命題：** 只支持某個來源出現了 chooser；不能支持它屬於本次 attempt，也不能支持下載開始或完成。
- **允許動作：** 不輸入路徑、不確認；保存畫面、來源、時間與未知值後停止。首次結果記 `UNKNOWN`；已有 `UNKNOWN` 才可 reconcile。
- **禁止推論：** 延遲出現就是本次 chooser；沿用上一 attempt 路徑；猜資料列或按 Return；把 chooser 當下載結果；截圖沒看到就說不存在。
- **缺少證據：** chooser 的 viewer／attempt／process 歸屬、精確目的地與欄位讀回、可信時間、終結訊號。

## C4 晚到結果不可誤歸下一項

- **前提：** attempt A 已有 `UNKNOWN`；下一項 B 尚未建立 intent。
- **觀察（假設）：** A 初次等待後又出現 chooser、進度或檔案，可能屬於 A，但尚未完成歸屬核對。
- **可支持命題：** 晚到證據只能先回到 A；出現時間本身不能指定所有權，也不能證明下載完成。
- **允許動作：** 先暫停 B；以 A 的原事件、原 viewer、原目的地 reconcile。若正面完成證據成立才可 `DOWNLOAD_FINISHED` 並 `download-check`；仍不明時只有 A 符合安全隔離，才可先保留 A，且只有後續 v5 intent append 才消耗一次額度，再處理 B。晚到 A 檔只留 A 的舊 staging，不變成 B 的結果。
- **禁止推論：** 晚到結果算成 B；重設 A；看到檔案就直接 `download-check`；未隔離 A 就為 B 建 intent；晚到檔可發布、清理或併入新 attempt。
- **缺少證據：** attempt／viewer／目的地歸屬、終結訊號、穩定檔集；若檔案存在，還缺基本檔案檢查與 completion。

## C5 播放不是操作步驟或取證來源

日常 Agent 不播放／暫停、拖時間、調倍速或檢視媒體內容，也不為證明來源種類操作 viewer；不可點內容切換播放控制。只可移入游標或使用明確工具列控制顯示下載工具列。若歷史資料中已有播放觀察，不將它用作下載完成或來源種類證據。

## C6 無 outcome 的 crash window

- **前提：** `intent` 已保存並讀回，可能已輸入；程序在第一筆 outcome 前 crash 或重啟。
- **觀察（假設）：** ledger 有 intent、沒有 outcome；重啟後沒有可歸屬 chooser／進度／檔案，暫存目錄可能為空。
- **可支持命題：** 只支持存在 crash window 與可能已派送；缺少資料不是空帳，也不是未派送證明。
- **允許動作：** 找回原 attempt；用 `outcome` 記第一筆真實結果，證據不足就記 `UNKNOWN`。之後可做一次唯讀 reconcile；仍不明且安全隔離條件成立時，依 CLI 追加零消耗隔離，完成隔離後新完整 scan／細盤再以 v5 intent 消耗一次額度；否則停止新派送、檔案檢查與下一項。
- **禁止推論：** 沒有 outcome 就是未送出；空目錄等於 `NOT_SENT`；先呼叫 reconcile；建立新空白 attempt 或重建 ledger。
- **缺少證據：** 是否真正送出、原 viewer／chooser／進度、原目的地檔案、可歸屬終結或停止證據。

## C7 UNKNOWN 未收斂：安全隔離或停止

- **前提：** attempt 已有 `UNKNOWN`，並已依原事件、原 viewer、原目的地調和。
- **觀察（假設）：** 只有 timeout、畫面未變、空目錄或缺 marker；相同查證方法連續兩次沒有新資訊。
- **可支持命題：** 只支持尚未收斂；隔離事件只記錄舊 attempt 的處置，本身零消耗，不證明 `NOT_SENT`、停止或完成。
- **允許動作：** 保留 `UNKNOWN`，停止相同查證。同一媒體、有效前景、舊 staging 符合空目錄或單一穩定普通媒體檔的隔離條件、無 chooser／活動下載／命名／異常／開放 restart 且 CLI 支援時，可由追加隔離事件保留舊 attempt；完成隔離後才開始的新完整掃描與該篇細盤，再由一次 v5 intent append 消耗額度並建立一次新空白補下載。否則保存證據並停止。
- **禁止推論：** 換目錄、重置 ledger、換列表或相簿入口可解鎖；缺 marker 可改寫成 `NOT_SENT`；隔離等於舊操作停止或可無限重送。
- **缺少證據：** 可歸屬終結訊號，或足以安全支持 `STOPPED`／`NOT_SENT` 且排除晚到作用的停止 receipt；自動單次路徑只接受隔離與新 attempt 證據，不能補成停止。

## C8 完成證據：充分與不足

- **前提：** 同一 attempt 已有 outcome，準備判斷能否執行日常 `download-check` 與計完成。
- **觀察（假設對照）：** 充分的下載終結候選是可歸屬原 attempt／viewer／原目的地的正面終結訊號，加上原目的地的穩定結果檔；充分的日常完成證據再加入 magic MIME／suffix 分類、非空穩定檔案、SHA-256、防覆寫、身分核對、發布與 completion 讀回全部成立。不足組合是只有 chooser、API 成功、播放結束、照片 toast 單獨一項、空目錄、部分檔案、名稱／hash 相同，或 completion 未讀回。照片的「下載完畢」提示可作可能的終結觀察之一；影片不要求同一 toast，但必須有自己的可歸屬正面終結證據。
- **可支持命題：** 下載終結候選支持 `DOWNLOAD_FINISHED` 與進入日常 `download-check`；只有基本檔案檢查及 completion 讀回支持 `DOWNLOAD_ONLY`。不足觀察只支持進一步查證或 `UNKNOWN`。
- **允許動作：** 已有 `outcome=UNKNOWN` 且下載終結候選成立時，以 `reconcile` 追加新證據；若既有 outcome 已是 `DOWNLOAD_FINISHED`，直接 `download-check`。只有最終為 `DOWNLOAD_FINISHED` 才可執行基本檢查，再讀回 completion。尚未有 outcome 的 crash window 依 C6 處理，不把本案例當成第一筆 outcome 的替代。不足時停在上一個已證明層次，不重下補帳。
- **禁止推論：** 終結訊號單獨就是 completion；chooser／播放結束／照片 toast 是所有媒體的必要條件；本機驗證等於服務端原始位元或外部副本完整。
- **缺少證據：** 充分組合仍缺真實 LINE 執行與當次工具輸出；本文件案例不能填補該缺項。

## C9 停止證據：充分與不足

- **前提：** 原 attempt 未確認下載完成，評估是否能終結為 `STOPPED`／`NOT_SENT` 或建立恢復 attempt。
- **觀察（假設對照）：** 充分的觀察是有可歸屬原 attempt、足以正面排除原操作稍後繼續的明確停止／未派送 receipt，且原任務授權涵蓋恢復；不足的觀察只有 timeout、API error、控制隱藏、空目錄、缺少 marker、舊計數為零、播放結束或 Owner 口頭聲明。
- **可支持命題：** 充分 receipt 才可能支持終態；不足觀察只支持 `UNKNOWN`。本文件沒有取得任何真實充分 receipt。
- **允許動作：** 充分、授權且帳本已持久化 `recovery_authorized=true` 時，保留原檔並依下載文件以 `intent --recovery-evidence` 建立另一個新空白恢復目錄；授權未持久化或證據不足時停止。不足時保留 `UNKNOWN`，不做檔案檢查、不建新 attempt、不重下、不派下一項。
- **禁止推論：** 假設 receipt 已被本次工具取得；缺 marker 等於停止；新目錄／新 Session 可解鎖；可用相簿控制替代記事本流程。
- **缺少證據：** 真實平台是否能提供足以排除副作用的停止證據仍 `UNKNOWN`；未提供能力不得由案例補齊。

## C10 Go to Folder 預填值不是 panel 目的地

- **前提：** `intent` 已保存並讀回，chooser 可唯一歸屬同一 viewer／attempt；本次目的地應是該 intent 建立的新空白目錄。
- **觀察（假設）：** Go to Folder 的 PathTextField 留著上一次路徑，panel 的 where／current directory 尚未可靠讀回；目前資料夾與預填文字不同，intent staging 仍為空。
- **可支持命題：** 只支持 PathTextField 顯示舊字串；不能證明 panel 已切到舊位置，也不能證明目前位置或 intent staging 正確。
- **允許動作：** 分開記錄 PathTextField、where／current directory 與 intent staging；輸入或覆寫為本次精確新空白絕對路徑後讀回欄位與目前位置。三者一致且來源貼文／attempt 可歸屬時，才可確認一次；任一不符或 `UNKNOWN` 就停止。
- **禁止推論：** PathTextField 預填值等於 panel current directory；舊路徑可當本次目的地；空 staging 等於 chooser 未顯示或尚未輸入；同名檔案可建立 attempt 歸屬。
- **缺少證據：** panel current directory、where 值、PathTextField 真正讀回、intent staging 空白狀態、attempt／viewer 歸屬與確認原始回傳。

## C11 Restart preview 不是 Owner 批次同意

- **前提：** 已有一份完整盤點；帳本含 UNKNOWN、無 outcome、pending 或 `LOCAL_CHANGED`，且 `restart preview` 回報 `RESTART_REQUIRED`。Owner 可能只回「繼續」、沉默或逾時。
- **觀察（假設）：** preview 列出精確列表、受影響貼文／媒體、已完成 sibling、舊版本位置、新 `versions/gNNNNNNNN/` 目錄、額外空間、缺項與保留項；尚未取得針對這批 scope 的明示同意。
- **可支持命題：** 只支持存在待確認批次；Prompt 本身、沉默、逾時與一般「繼續」都不是批次同意。沒有確認時舊 UNKNOWN／pending／LOCAL_CHANGED 的保護不變。
- **允許動作：** 保存 preview 與白話摘要，等待 Owner 對這批範圍明示回覆；同意後以既有 v2 `evidence-pack` bundle（context 為 `list_key` 加 preview 的 `scope.scan_id`）在同一 session 執行 `restart confirm`。confirm 後再完成新的完整 recovery scan，才可逐項 `intent --restart-id`。不新增或手寫 schema。
- **禁止推論：** 一般「繼續」等於同意；`recovery_authorized`、`dispatch_authorized` 或工具成功等於同意；可以順便擴到另一個列表、貼文、媒體、舊版本或不同目的地；confirm 後可直接重用 confirmation 前的 page rows／舊 scan。
- **缺少證據：** 當次可核對的 Owner 明示同意引用，以及 confirm 時仍相符的 expected tip／scope digest；沒有這些證據就沒有 restart 授權。

## C12 同一批次再次中斷、範圍漂移與晚到結果

- **前提：** 一個已確認 restart 批次尚未 activation；部分 candidate 已驗證，另有 UNKNOWN／無 outcome 項，或流程中再次失去前景。重新查詢可能得到同一 `restart_id` 的 `OPEN_BATCH`。
- **觀察（假設）：** 舊 confirmation、candidate、activation、completion 與 UNKNOWN 歷史仍在；新 Session 看見新的 viewer／chooser，舊 chooser 仍可能存在或已被取消；舊 raw 路徑稍後出現寫入。
- **可支持命題：** 同一已確認 scope 在完成前再次中斷可用 `OPEN_BATCH` 找回，只處理未完成或結果仍不確定的項目。舊歷史不被新結果取代，新 candidate 必須是獨立版本目錄；晚到結果只能回到原 attempt，不能歸給新 attempt。取消舊 chooser 不證明舊寫入已停止。
- **允許動作：** 依同批 `restart_id` 接續；先確認目前是否有完整 recovery scan，缺失或中斷時依規則重新中斷／盤點。只對未完成項以新 viewer／chooser／空白 staging 建立新 attempt，逐項最多一次派送；全部 candidate 通過後才一次 activation。若 scope、身分、目的地或版本策略改變，停止並重新 preview、取得新的 Owner 明示同意。
- **禁止推論：** 已確認一次就可無限重送或擴及其他項；再次中斷自動代表舊 UNKNOWN 已停止；取消舊 chooser 等於舊操作終止；晚到檔案屬新 attempt；可重用舊路徑、舊座標或把舊 history 改寫成新版本。
- **缺少證據：** 真實 GUI 的晚到輸入／chooser、舊寫入停止證據、新 viewer 與 staging 的連續歸屬，以及跨 Session 的實際恢復結果仍 `NOT_RUN`；文件案例不能補成 E2E PASS。

## C13 V1／V2 的 intent 前隱藏控制差異

- **前提（假設）：** 同一 viewer 的最新 bounded observation 未見控制；三層身分、有效前景、返回控制與所有非 GUI 前置成立，當次 selected-filmstrip 安全方法可歸屬，且同一 scope 完整查得已送出 `0` 次 reveal、無 chooser／未解輸入／舊 UNKNOWN／舊無 outcome。尚未建立 intent，也尚未送出任何 reveal。
- **觀察（假設）：** 這正是 V1 與 V2 的差異點；工具列仍隱藏，沒有新的可見控制。
- **可支持命題：** V1 要求工具列先可見才能建立 intent，因此同一輸入在 V1 會停在 intent 前。V2 允許以「當次安全方法＋可核對的 `0`／`1` 額度」作為隱藏分支前置，可建立既有 intent；但這不是 reveal 授權，intent 前仍不得送出任何 GUI 輸入，intent 後控制仍隱藏才可送一次。
- **允許動作：** V2 保存方法、安全區、選取、mapping、額度與非 GUI 前置後，建立並讀回 intent；最新原件仍隱藏時才依 C15 走一次 fixed-slot reveal。V1 只可停下並記錄缺可見控制，不得改寫成已 intent。
- **停止反例：** 無當次安全方法、方法不能歸屬同一 viewer／選中項、已用兩次、額度不明、舊 UNKNOWN／舊無 outcome、前景中斷或任何未決；任一成立都在 intent 前停止。V2 也不能用 intent 前 reveal、舊骨架、猜 hover、固定等待或 fresh capture 補條件。
- **缺少證據：** V1／V2 的真實 GUI 差異與 V2 隱藏分支成效仍 `NOT_RUN`；本案例不是實機結果。

## C14 intent 後最新控制可見的直接路徑

- **前提（假設）：** B1 前置成立，既有 intent 已保存並讀回；intent 後最新的同一 viewer 原件正面顯示記事本下載控制可見、歸屬、啟用與映射成立，且無 chooser／未解輸入。
- **可支持命題：** 這份 intent 後原件支持直接下載定位，不需要也不得再送 reveal。intent 前的可見觀察不能用來跳過 intent 後重核。
- **允許動作：** 保存原件與映射，組出 request 並連同同一份原件交 `persistGroundedDownloadClick` 一次；由 helper 以 `wx` 獨占建立並讀回 `notes-download-<attempt_id>` 後才 click。直接路徑不消耗 reveal 額度；其後 chooser 仍依既有至多一次確認。
- **禁止推論：** intent 後不重取即可沿用舊點；固定等待可保證工具列存續；helper 呼叫等於 native hit-test、App 接受或下載成功；控制一旦可見就能重播或再按一次。
- **缺少證據：** 真實控制時序、native hit-test、chooser 與下載終結仍 `NOT_RUN`／`UNKNOWN`。

## C15 隱藏分支的 0→1 與固定 reveal slot

- **前提（假設）：** 新 attempt 的 intent 已讀回；intent 前完整查得同一 scope 已送出 `0` 次，當次安全方法仍在最新原件可歸屬，沒有 chooser、下載控制呼叫或 outcome。
- **觀察（假設）：** intent 後最新原件仍隱藏控制；這是一般 V2 hidden branch，不是額外候選或另一次嘗試。
- **可支持命題：** 只可在同一 attempt 使用一次 `candidate_ordinal=1`、`budget_before=0`；送出後 `budget_after` 為 `1`，不論 error、timeout、crash 或缺 receipt 都耗額。
- **允許動作：** 組出 request 交 `persistRevealWithDirectAfter`；由其內部的 `persistSingleInput` 以 `wx` 建立並逐 bytes 讀回 `notes-reveal-c2-<attempt_id>`，`c2` 是固定檔名，ordinal `1` 只寫在 request。同一次 callback 送一次安全 reveal 並保存同一份 after；after 正面才交給下載 helper 一次。
- **停止反例：** slot 已存在、並行競爭、讀回不符、request 保存失敗、方法／mapping 失效或 after 缺口時零額外 input並停止；不得改 ordinal 命名、換 slot、重送或建新 attempt。
- **缺少證據：** 真實工具列的顯示／消失與 reveal 成效仍 `NOT_RUN`；本案例不證明工具列會出現。

## C16 同次 reveal input → after 的保存順序

- **前提（假設）：** 既有 intent 已建立並讀回；B1 的 intent 前方法／額度 gate、當次安全作用區與映射均成立；input／after observation 目錄事先備妥；`notes-reveal-c2-<attempt_id>` request 已保存並讀回 `MATCH`；當次工具文件支持對同一 app 依序執行一次 input 與 observation。
- **觀察（假設）：** callback 內只送出一次已核對 input；原生回傳後不離開 callback，直接取得同一 app 的 after；input 回傳、after 回傳／error 在記憶體分開保留，input raw 與 after bytes 在 callback 返回後才持久化。
- **可支持命題：** after 來自同一次 runtime invocation，且位於一次 input 之後；這是兩個相依 API，不是 atomic 或固定秒數保證。工具回報的內部等待只能按其文件語意記錄，不能補成 OS event 命中、精確 capture 時間或 toolbar 保證存續。
- **允許動作：** callback 原樣回傳 input 回傳；返回後先保存 input raw／diagnostic，再用 `persistObservation` 保存剛才取得的同一份 after bytes，不重新 capture。記錄 host 層 call 前／回傳時間與相對序號；缺少 OS event 或個別 capture 時間就記 `UNKNOWN`。保存骨架見 [單次輸入與直接 after 觀察](evidence-template.md#單次輸入與直接-after-觀察) 的 `persistRevealWithDirectAfter`。
- **禁止推論：** 在 input 後另開 shell、插入模型回合或固定等待；把兩個 API 說成 atomic／固定秒數完成；用 after 成功反推 input 命中；以 mtime 冒充精確時間；保存後再 capture 一次；以任意縮圖邊緣或固定左上／右上熱點代替當次安全區。
- **缺少證據：** OS event trace、native hit-test、個別 capture 的精確時間、真實 GUI 的 toolbar 存續與 C 類實機結果仍 `NOT_RUN`／`UNKNOWN`。

## C17 intent 後 reveal 已送出但 after 或保存缺口

- **前提（假設）：** 既有 intent 已讀回；hidden branch 已稽核；`notes-reveal-c2-<attempt_id>` request 已保存並讀回 `MATCH`，候選已送出一次 input；之後 after API error、callback 中斷或程序 crash，input raw／diagnostic／after bytes 至少一項未完成持久化與讀回。
- **觀察（假設）：** request 可能仍在，記憶體可能有部分 input 回傳或 bytes，但缺少完整 receipt 或同一份 after；無法證明 input 未送出、控制命中、toolbar 曾顯示或下載開始。
- **可支持命題：** 只能支持一次候選已派送但證據保存不完整；capture error、空 after、缺 raw、無 after 或重啟都不是 `NOT_SENT`，且候選額度已消耗。
- **允許動作：** 立即停止；保存仍可得的 request、input 回傳／error、部分 bytes 與停止原因，`budget_after` 照算。只有原 callback 已取得的同一份 after bytes 可補做原保存；不得重新取得。證據不足時保留原 intent，依實際結果記第一次 outcome 或保留 `UNKNOWN`，之後才可 reconcile。
- **禁止推論：** capture error 等於未輸入；缺 raw／after 可重拍或重送；用新 viewer、Session、目錄、另一個 slot 或第二次 reveal 解鎖；把 partial persistence 當成控制可見或交易資格；以另一次 input 查證。
- **缺少證據：** 完整 input receipt、同一份 after bytes、OS event／hit-test、chooser／進度／檔案與可歸屬終結訊號。

## C18 跨 Session 的 1→2 與新證據

- **前提（假設）：** 同一三層身分在不同 notes Session 查回已送出 `1` 次；原候選 request／raw／after 完整、未決為零、同一 viewer／前景連續，且有改變既有決策 gate 的相關新證據；新 attempt 的 intent 已讀回且最新控制仍隱藏。
- **觀察（假設）：** 跨 Session 沒有重置額度；新的 attempt 或 fresh capture 本身不是新證據，只有例如舊遮罩／範圍不足已消除、或新安全作用區被當次原件重新建立，才可能改變 gate。
- **可支持命題：** 只有完整稽核為 `budget_before=1` 且上述新證據成立，才可用 `candidate_ordinal=2`；否則一律沒有 reveal 路徑。直接控制可見仍可依直接路徑下載，但不消耗 reveal 額度。
- **允許動作：** 使用同一固定 `notes-reveal-c2-<attempt_id>` slot，ordinal `2` 只寫在 request；同次 input→after 後，正面才交給下載 helper一次。任何跨 Session 查不到先前引用、額度矛盾或新證據不足就停在輸入前。
- **禁止推論：** 新 Session／reopen／restart 可重置為 ordinal 1；第三候選；舊點位或舊 mapping 可重播；新 attempt 自動等於新證據；直接可見路徑可用以掩蓋 reveal 額度不明。
- **缺少證據：** 跨 Session 實際查回、新證據是否足以改變 gate 與 GUI 結果仍 `NOT_RUN`。

## C19 固定 slot 衝突、並行與下載關閉

- **前提（假設）：** 新 attempt 的 intent 已讀回，B1 允許一次 reveal 或直接下載；同一 attempt 的 `notes-reveal-c2-<attempt_id>` 或 `notes-download-<attempt_id>` 已被建立，或其 `wx` 寫入遇到並行競爭／逐 bytes 讀回不符。
- **觀察（假設）：** 檔案存在但內容不屬本 attempt，或另一次同 attempt 呼叫正在建立相同 slot；沒有任何新的 input receipt。
- **可支持命題：** 固定 slot 是持久獨占邊界；碰撞只支持「不能用這個 slot 送出此步」，不證明輸入已送出或可改 ordinal／換目錄重開。
- **允許動作：** 零 input、零下載控制呼叫；保存碰撞／讀回錯誤與原 intent，停止本 attempt 的新輸入，依既有 outcome／reconcile 與人工程序處理。不得改 `notes-reveal-c2` 的 `c2`、以 ordinal 改名、換 taskDir／inputDir／Session、重播或建立替代 attempt。
- **禁止推論：** 刪除或覆寫 slot 可安全重試；下載 helper 呼叫前失敗等於未派送；下載控制一旦開始後仍可回 reveal；slot 成功建立就等於 App 接受或下載開始。
- **缺少證據：** 真實並行競爭、slot 修復與 GUI 行為仍 `NOT_RUN`。

## C20 舊 UNKNOWN／無 outcome：單次自動恢復與 exact restart

- **前提（假設）：** 同一媒體已有舊 `UNKNOWN`，或 intent 後 crash 且尚無 outcome；目前工具列可能隱藏或可見，但沒有新的精確 restart 授權。
- **觀察（假設）：** 舊 intent／crash window 與舊歷史仍存在；最新畫面或空 staging 不足以證明舊操作未送出。
- **可支持命題：** 新 Session、fresh capture、控制重新出現、零計數與空 staging 單獨都不解鎖。舊 `UNKNOWN` 可在同一媒體安全隔離與跨 Session 一次額度成立時建立一個新空白補下載；隔離零消耗，只有其後 v5 intent 消耗額度。批次 scope、`LOCAL_CHANGED`、既有完成或其他版本策略仍只能走 fresh `restart preview`、Owner 明示同意、`restart confirm` 與新 recovery scan。
- **允許動作：** 先以有限 AX／截圖核對舊目標與前景；未有 outcome 時記第一筆真實結果，已有 `UNKNOWN` 才 reconcile。符合單次路徑時追加隔離、完成隔離後才開始的新普通完整 scan／細盤，再由一次 v5 intent 消耗額度並補下載；符合 exact restart 時保留舊歷史，使用新 generation／staging。B1 額度仍跨 Session 累計且不自動重置；新 attempt 的方法／額度仍要在 intent 前稽核。
- **禁止推論：** 舊 UNKNOWN 已停止或可清除；單次自動恢復可取代 restart 批次或無限重送；restart 自動提供 reveal 額度；新 attempt 可重用舊 viewer／chooser／座標；一般「繼續」或 `dispatch_authorized=false` 等於 restart 同意。
- **缺少證據：** 真實舊 UNKNOWN 收斂、隔離後跨 Session 一次額度、restart 後額度查回與實機結果仍 `NOT_RUN`。

## C21 intent 後前景或身分中斷

- **前提（假設）：** 新 attempt 的 intent 已讀回，尚未送 reveal 或下載；Owner 將前景交給其他 app，或最新原件顯示 viewer／列表／貼文／媒體／返回錨點已漂移。
- **觀察（假設）：** 舊 viewer 與 mapping 不再有效；可能有未完成 input 或尚未送出的 slot。
- **可支持命題：** 只支持目前不能安全輸入；有效前景與連續性消失，不得用新 Session、reopen、舊座標或另一個 attempt 接續同一未決 attempt。
- **允許動作：** 零後續 GUI 輸入，保存最新原件、停止原因與原 intent；若此前已有 input，依 input receipt／候選額度與既有 outcome／reconcile 處理。前景恢復後仍要重新核對列表與歷史；舊 attempt 不會因新交接自動解鎖。
- **禁止推論：** 新 Session 重置額度；可由另一 viewer 完成同 attempt；控制重新出現即可重按；未見 chooser 或空 staging 等於未送出。
- **缺少證據：** 真實中斷、跨 Session 交接與恢復結果仍 `NOT_RUN`。

## C22 AX 缺控制節點但充分視覺與映射成立

- **前提（假設）：** 新 attempt 的 `intent` 已保存並讀回；最新 observation 仍屬於同一 app／window、同一列表／貼文／媒體／viewer，沒有 chooser、活動下載、未解輸入或前景中斷。Agent 的播放輸入為 `NONE`；來源播放狀態已正面記錄，來源、選取、幾何與映射沒有漂移。
- **觀察（假設）：** 完整 AX 沒有下載控制節點，但同一份當次截圖充分涵蓋目標 viewer，控制可見、歸屬、啟用與作用區成立；截圖像素、視窗點數、螢幕座標、視窗位置、縮放與 mapping 識別均完整，且該份原件仍是 intent 後的最新狀態。
- **可支持命題：** AX 缺少節點只表示該次 AX capture 沒有列出該節點，不能據此宣稱控制不存在；當次充分視覺與完整映射可以支持 B1 的直接定位，但不證明 native hit-test、App 接受或下載結果。
- **允許動作：** 保存截圖、AX、視窗綁定、控制區域、候選 target 與映射，並以該份 intent 後原件準備一次直接路徑；不得另補 AX 節點、重送 reveal 或改走新的 GUI 方法。
- **禁止推論：** AX 沒有節點就否定充分視覺；截圖存在只憑圖示、箭頭或近似位置就等於映射成立；可用截圖補造 AX 節點；helper 接受 request 就等於控制命中或下載開始。
- **缺少證據：** 真實 OS hit-test、控制命中、chooser、下載終結與檔案結果仍 `NOT_RUN`／`UNKNOWN`；本案例是文件假設，不是實機 `OBSERVED`。

## C23 AX 缺節點且視覺／映射不足

- **前提（假設）：** 同一目標尚未建立新 attempt，或既有 intent 已讀回但還沒有下載控制 outcome。有效前景存在，但沒有新的全域 blocker。
- **觀察（假設對照）：** AX 沒有控制節點；當次截圖只顯示局部 viewer、箭頭或未歸屬圖示，目標 viewer 覆蓋、控制歸屬／啟用、視窗位置、縮放或座標映射至少一項缺失、過期或 `UNKNOWN`。沒有可用的新方法或正向 mapping 證據。
- **可支持命題：** 只支持目前無法安全定位控制與需要保留該項；AX 缺席本身仍不是控制不存在的證據，局部圖示也不是可點區。
- **允許動作：** 補足證據僅限 intent 前的唯讀觀察。若真正補足 viewer 覆蓋、控制歸屬、啟用與映射，才可依 B1 備妥直接路徑。若仍不足，保留本項；只有無全域 blocker 且可靠返回契約成立時，才依 C26 排程。intent 已讀回時，直接路徑只用讀回後取得的那份原件，reveal 路徑只用原先已稽核方法的同次 after。任一路徑所需證據不足就停止該路徑，兩條路徑都不成立時依既有 outcome／`UNKNOWN` 分流；不得另外重拍、重開 viewer 或重新尋找控制。既有 intent 未收斂且未安全隔離時，不派送下一項。
- **禁止推論：** 看見箭頭或相似圖示即可猜點；缺欄位可自行補值；把新 capture、重開 viewer 或換 Session 的行為本身當成映射證據；截圖不足可改寫成 `NOT_SENT`。
- **缺少證據：** 充分 viewer 覆蓋、控制歸屬／啟用、完整座標映射與當次原件仍缺；真實控制作用與下載結果 `NOT_RUN`。

## C24 來源自動播放的三個維度

- **前提（假設）：** 同一 viewer／媒體尚未送出下載控制；Agent 的播放、暫停、拖曳、倍速、點內容切換與內容分析輸入均為 `NONE`。來源可能自行播放，畫面上可見的控制狀態仍在當次 observation 範圍內。
- **觀察（假設對照）：** 分開記錄三個維度：`Agent 播放輸入=NONE`；`來源播放狀態=NOT_PLAYING／AUTOPLAYING／UNKNOWN`；以及來源、選取、幾何、映射或控制遮蔽是否漂移。案例一是來源 `AUTOPLAYING` 且無漂移，控制可見、歸屬、啟用與映射完整；案例二是自動播放伴隨 viewer／選取／幾何／映射改變或控制被遮蔽；案例三是播放狀態 `UNKNOWN`。以本次已保存的 before 或前次有效觀察比對當次原件，正面核對同一 viewer 的來源、選取、viewer 區域邊界、視窗位置、縮放與映射均一致。
- **可支持命題：** 來源自動播放本身不是 Agent 播放違規，也不單獨阻擋 B1；只有在上述維度均可正面核對、沒有漂移且其他 B1 前置成立時，才有繼續路徑。漂移或控制遮蔽只支持停止與證據不足，不能記成 Agent 播放。
- **允許動作：** 按 B1 記錄播放狀態、觀察範圍、時間與映射。案例一及案例三須依既有原件完成明確比對，且其餘 B1 前置成立，才能依當次路徑處理。案例二、缺比對原件或無法證實一致時，停止該項輸入並保留證據。不得為確認狀態新增播放、暫停、拖曳、倍速或內容點擊。
- **禁止推論：** `Agent 播放輸入=NONE` 就等於畫面靜止；`AUTOPLAYING` 一定是 Agent 造成；`UNKNOWN` 或僅未看見變化即可證明無漂移；`UNKNOWN` 可猜成 `NOT_PLAYING`；播放造成漂移仍可沿用舊選取或舊映射；播放狀態會重置候選或交易限制。
- **缺少證據：** 真實自動播放的時序、漂移範圍與跨版本行為 `NOT_RUN`；本案例不追認任何舊 attempt 的播放證據。

## C25 Candidate 2 的正面新證據與僅新 capture

- **前提（假設）：** 同一三層身分跨 Session 查回已送出 `1` 次 reveal；前次 `candidate_refs`、request／raw／after 完整，沒有未決 input、chooser、活動下載、pending naming、隔離或額度矛盾；新 attempt 的 `intent` 已讀回且控制仍隱藏。此路徑只適用 hidden branch；控制可直接定位時走直接路徑，不需要 candidate 2。
- **觀察（假設對照）：** 正面新證據是當次工具文件現在證明先前未查明的無點擊方法，且當次原件能歸屬該方法的安全區與映射，因而確實改變既有方法／映射 gate；或當次原件正面重建先前缺失、且可安全執行同一 reveal 的安全區與映射。僅新 capture、重開 viewer／new Session、時間流逝、只換一個點、事後補 request，或只有文件存在而未改變方法／映射，都不是新證據。
- **可支持命題：** 前者才可能支持 `candidate_ordinal=2`，但仍須完整 `prior refs`、`budget_before=1`、同一固定 reveal slot、最新 intent 與所有 B1 gate；後者只保留該項未完成，不能解鎖。
- **允許動作：** 新證據成立且 gate 完整時，使用同一 attempt 的 `notes-reveal-c2-<attempt_id>`，ordinal `2` 只寫在 request，同次 input→after 保存；若沒有新證據或任何 gate 不明，停在輸入前並保留原狀態。
- **禁止推論：** 新文件存在、fresh capture、重開、換 Session、換點或新 attempt 自動等於新證據；ordinal 可改回 1 或建立第三候選；候選 2 一定成功；以直接路徑名義再送額度不明的 reveal；控制確實直接可見且其他 gate 成立時，仍依 B1 走直接路徑，不要求 reveal 額度可用。
- **缺少證據：** 跨 Session 的完整額度查回、真正新證據的 GUI 效果與結果仍 `NOT_RUN`；不保證舊項可恢復。

## C26 局部 B1 阻塞、可靠返回與其他合格項

- **前提（假設）：** 完整列表覆蓋與身分已核對；目標項在 intent 前因 B1 控制映射不足而局部阻塞，沒有未隔離 `UNKNOWN`、無 outcome、活動下載、pending naming、`LOCAL_CHANGED`、列表覆蓋或身分歧義等全域 blocker。當次前景仍有效，且 entry anchor、`expected_return_role`、一次一層的可歸屬返回控制與返回後可核對的來源身分都成立。
- **觀察（假設）：** 目標項沒有安全定位或 input；其他合格項已有新的 B1 前置與 intent 資格。返回契約在當次 observation 可正面核對，而不是只看到一個未歸屬的箭頭或沿用舊座標。
- **可支持命題：** 局部 B1 阻塞不等於全域停止，也不等於該項已下載失敗；可在不擴張授權的前提下保留該項，依可靠返回契約回到入口，再逐項重過 B1、返回與 intent gate 處理其他合格項。`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 是項目級未完成狀態，不單獨構成全域阻擋，但仍保留欠件、不計完成。
- **允許動作：** 記錄目標項的 blockers 與證據，執行一次契約內返回，重新核對列表／貼文／媒體與前景；之後一次一項處理其他合格項。清單摘要仍須標示原目標未完成，不得宣稱整份列表完成。
- **停止反例：** 返回控制、entry anchor、返回角色或前景任一 `UNKNOWN`／不符；目標已有未隔離 intent 或 input；出現全域 blocker；需要第二次猜返回或改用另一入口時停下，不跳過。
- **禁止推論：** 局部阻塞可用來跳過全域 `UNKNOWN`；返回成功等於下載成功；處理其他項可平行派送或改變原目標歷史；`REDOWNLOAD_REQUIRED` 可直接清除。
- **缺少證據：** 真實返回控制命中、排程順序與跨篇 GUI 行為仍 `NOT_RUN`。

## C27 全域 UNKNOWN 不可由排程或 Session 跳過

- **前提（假設）：** 列表完整覆蓋尚可核對，但存在未隔離 `UNKNOWN`、無 outcome、活動下載、pending naming、`LOCAL_CHANGED`、列表覆蓋缺口或身分歧義等任一全域 blocker；另有一項表面合格的媒體，當次前景與返回契約可能成立。
- **觀察（假設）：** 另一個項目看似可派送，或新 Session／重開 viewer／空 staging／零計數提供了新的畫面，但沒有收斂原 blocker 的正面證據。
- **可支持命題：** 全域 blocker 仍阻止新的 intent、下載與排程跳過；其他項目的 B1 合格或返回成功不能解除它。沒有新的結果證據時，`UNKNOWN` 只維持未知，不能改寫成 `NOT_SENT`、`STOPPED` 或完成。
- **允許動作：** 保存全部原件、blocker 與原 attempt，停止依賴該前提的新派送；只有符合既有安全隔離、精確 restart 或正式恢復路徑時，才依各自 gate 另案處理。
- **禁止推論：** 換 Session、重開、重新掃描、空目錄、控制重新出現或另一項可下載即可繞過；`UNKNOWN` 可因等待或截圖未見檔而改寫 `NOT_SENT`；可以平行建立新 attempt。
- **缺少證據：** 可歸屬且排除晚到作用的停止 receipt，或安全隔離／正式 restart 的完整證據；沒有時保留 `UNKNOWN`，真實恢復結果 `NOT_RUN`。

## D1 Viewer 返回契約在進入後核對

- **前提：** 目標貼文／媒體已核對，尚未建立下載 intent，Agent 準備開啟 viewer。
- **觀察（假設）：** 貼文詳細頁來源 observation 與貼文錨點已保存；viewer 尚未進入，因此尚無 viewer 返回控制。
- **可支持命題：** 可用來源錨點與預期返回角色核對稍後返回；`expected_return_role` 由實際 entry anchor 的當次角色決定，`LIST` 與 `POST_DETAIL` 都是合法結果，不得預設其一；入口角色沒有充分原件時記 `UNKNOWN`。進入前看不到返回控制是正常資訊缺口，不代表禁止進入；進入 viewer 後才核對控制歸屬與角色，實際返回結果仍須在輸入後判讀。
- **允許動作：** 依有效前景及當次映射開啟目標 viewer；進入後先觀察控制所屬 app／window、角色、焦點與歸屬。確認返回控制與 entry anchor／預期角色相符且定位有效後才建立下載 intent；實際返回結果仍須在輸入後判讀。
- **禁止推論：** 進入前不存在返回按鈕；單獨標為「關閉」的按鈕必定回到來源貼文；舊 viewer 座標可重用。
- **缺少證據：** viewer 內返回控制的歸屬與作用須由進入後的新 observation 判斷；本案例不是實機結果。

## D2 返回後頁面偏離預期

- **前提：** 已從 viewer 送出一次有證據的返回輸入。
- **觀察（假設）：** 新 observation 顯示畫面仍是 viewer、已變成聊天，或無法連回來源貼文錨點。
- **可支持命題：** 頁面未變或觀察不足時只記 `RETURN_NOT_OBSERVED`，不能宣稱 `ENTRY_LOST`；只有充分觀察正面顯示頁面角色／身分或 entry 連續性已失去，才記 `ENTRY_LOST`。
- **允許動作：** 停止原返回方法，保存前後 observation 與輸入 receipt；分開記錄頁面角色、前景、觀察及輸入能力。
- **禁止推論：** 再按一次 Escape／Command-W、改猜關閉鍵或沿用舊座標可安全退一層。
- **缺少證據：** 真實返回控制命中、後續 GUI 行為與 LINE E2E 均 `NOT_RUN`。

以下五列均為 **假設文件案例、非實機驗證**；不引用真實列表、截圖、key 或交易結果。

| 案例 | 證據 | 正確判斷／禁止動作 |
|---|---|---|
| **長卡正例**（假設文件案例、非實機驗證） | LIST 入口；同 app／window 的可捲動 List／多 row；scroll、entry anchor 與相鄰卡片連續；viewer 已離開；沒有角色轉換證據。 | 判 `page_role=LIST`。只有 `expected_return_role` 與 anchor／身分都吻合才記 `RETURNED`；不因長卡再找第二層返回或重複關閉。 |
| **長卡資訊不足**（假設文件案例、非實機驗證） | 只有長卡，或只有單一 hash／scroll，缺列表身分或 anchor；沒有正面角色／導覽證據。 | 記 `UNKNOWN`／`RETURN_NOT_OBSERVED`；若已正面觀察仍在 viewer，保留 `page_role=VIEWER` 並記 `RETURN_NOT_OBSERVED`，不洗成 `UNKNOWN`。不得因看不到搜尋列、卡頭或返回控制就猜 `POST_DETAIL`，也不得猜第二次 close。 |
| **真實詳情頁**（假設文件案例、非實機驗證） | 當次可引用原件正面支持詳情頁角色或導覽轉換；可位於同一 app／window，不要求另開視窗。 | 可判 `page_role=POST_DETAIL`；返回結果依實際 `expected_return_role` 與 anchor／身分判讀，不強制 `LIST`。不得因長卡反例否定真實詳情頁。 |
| **正面偏離**（假設文件案例、非實機驗證） | 充分觀察正面顯示變成其他列表／聊天／貼文，或來源 anchor 與連續身分已失去。 | 保留 `ENTRY_LOST`；長卡不等於 `POST_DETAIL` 的反例不能豁免正面偏離證據。 |
| **摘要待盤**（假設文件案例、非實機驗證） | 其他貼文為 `DETAIL_PENDING`，但目標貼文細盤合格；另有 notes 摘要 blocker。 | `POST_DETAIL_PENDING` 只是列表級摘要狀態，不得映射成 GUI `page_role=POST_DETAIL`。整份列表仍未完成，也不自動授予派送；不可當成目標 viewer 返回失敗或下載授權。 |

## D3 AX 沒有 Notes 控制但視覺可見

- **前提：** 指定記事本入口遺失；前景與輸入通道仍可用，來源仍能證明是同一指定列表所屬聊天。
- **觀察（假設）：** 完整 AX 未列 Notes 控制，但當次截圖可辨識候選控制及其視窗區域。
- **可支持命題：** 僅在當次視覺歸屬、控制作用區、座標空間及映射都充分，且候選點位於已核對控制區內時，才支持一次導覽輸入。
- **允許動作：** 保存 screenshot／window 綁定、控制區域、候選 target 與映射；最多用該當次可靠 Notes 控制一次，之後重新觀察。
- **禁止推論：** 看見圖示就代表 AX target 存在、OS hit-test 會命中、列表身分已恢復；不得搜尋其他聊天室。
- **缺少證據：** 視覺控制的實際作用及輸入結果須當次觀察；本案例不證明跨版本支援。

## D4 輸入失效但唯讀觀察可用

- **前提：** CUA 輸入回傳錯誤，AX／截圖仍可讀。
- **觀察（假設）：** 工具原始錯誤含 `noWindowsAvailable`；app／window 綁定或輸入能力尚未恢復。
- **可支持命題：** 只證明這次輸入回傳錯誤；`ENTRY_LOST` 與 `INPUT_UNAVAILABLE` 可同時成立。底層原因仍為 `UNKNOWN`。
- **允許動作：** 依當次工具文件唯讀列舉 app／window 並重新取得 handle；每步後重新觀察。只有新證據顯示通道恢復才考慮一次有證據輸入。
- **禁止推論：** 換 API、全螢幕切換、測試按鍵、重複 reset 或同一錯誤重試能恢復通道。
- **缺少證據：** 真實 `noWindowsAvailable` 根因與可恢復條件仍 `UNKNOWN`。

## D5 同前景 reacquire 與新 Session 交接

- **前提：** 重新取得 CUA app／window handle，或 Owner 將中斷的指定列表重新帶回前景。
- **觀察（假設）：** 前者仍是同一有效前景；後者是新的正式前景交接，可能仍在相同對話。
- **可支持命題：** 同一有效前景內的平台 reacquire 沿用 notes Session，不重跑 `bind`。真正中斷後重新交接須使用新 notes Session ID；新 Session、reopen 或新目錄都不重置同一媒體的 reveal 額度。
- **允許動作：** 新 Session 保存新 observation、核對列表，先處理舊交易，再顯式 interrupt 舊 open scan，之後以普通完整 scan 接續。
- **禁止推論：** `bind` 會替舊 scan interrupt；新 scan 可解鎖 UNKNOWN；一般入口恢復可使用 restart／recovery scan；帳本內既有完成或待盤狀態可改寫。本匿名事故案例的兩項 ACTIVE 與 49 篇 `DETAIL_PENDING` 是案例事實，不是所有列表的固定數值。
- **缺少證據：** 跨 Session 真實恢復及完整 51 篇 E2E 仍 `NOT_RUN`。

## D6 多候選帳本、已註冊他帳本 active_hint 與 AX 標題空白

- **前提：** 完整 `lists` capture 已 exit 0、receipt `COMPLETE` 且 `stdout.bin` 無截斷；同次 CUA 截圖與完整 AX 已落地並讀回。`lists` 有多份名稱相近的已註冊候選，或畫面顯示標題在 `lists` 中零同名候選（`display_name` 完全相符為 0）；macOS AX Window title 為空字串、列表節點泛用，`active_hint` 的 `records_root` 與 `local_list_id` 精確指向其中另一份已註冊帳本，或 `active_hint` 為 `none`。
- **觀察（假設）：** 全部 N 份候選的 `identity` 與前 5 篇 `posts` 錨點已展開；當次首屏卡片順序、日期、摘要脈絡與媒體縮圖排列恰與其中一份吻合，或全部 N 份均以具體差異正面排除；`active_hint` 命中的是另一份帳本或為 `none`，且沒有任何 hint 指向未註冊位置。
- **可支持命題：** `active_hint` 只證明前次曾操作該已註冊帳本，是切換列表的日常常態，不是缺損歷史阻塞；AX 標題空白只表示可存取性資訊有限，不是工具錯誤，也不阻止以同次截圖＋AX 與帳本 `identity`／`posts` 錨點交叉核對。單一中文名稱、OCR、單一日期或單一張數仍不足以認領列表。
- **允許動作：** 依[啟動與帳本對帳](download-and-ledger.md#啟動與帳本對帳)的三路契約處理：A 恰有一份交叉吻合且其餘 N−1 份有具體差異 → `bind`；B 全部 N 份均以具體差異正面排除、hint 已核對且無未註冊／損壞歷史 → `list-key` → `evidence-pack`（statement 明列全部 N 份排除依據）→ `init`（正式日常 Prompt 涵蓋恢復授權時加 `--recovery-authorized`）→ 讀回 `list_key` → `bind`；C 完成全核對仍有 `>= 2` 份無法區分或歷史異常 → 停在 `init`／`bind` 前，零寫入零輸入，保留已落地原件與 capture receipt，回報去識別化摘要與單一具體釐清動作（須附具體未成立的身分證據、衝突候選之去識別化 ID 與 `identity`／`posts` 差異；不得以「名稱不符」代替）。
- **禁止推論：** `lists` 終端截斷或名稱相近可以作為提前停在 `bind` 前的理由；以 `display_name == 畫面標題` 過濾候選；把「零同名候選」（`matches: []`）升格為身分不符／候選歧義或直接認定新列表；Route C 僅憑「名稱不符」要求重新交接；已註冊他帳本的 `active_hint` 等於歷史缺損；AX 標題空白等於工具故障或無法核對；中文標題、OCR、單一日期、單一張數或 hint 可以單獨認領列表或改綁他帳本。
- **缺少證據：** 真實 LINE GUI 的多候選消歧、`bind` 與後續下載均 `NOT_RUN`；本案例是假設文件案例，不引用真實列表、key 或交易結果。

## D7 CUA 原件落地：未執行 helper、真實失敗與工具撤除

- **前提：** 新 Session 需在 `bind` 前把同次截圖與完整 AX 落地；canonical `TASK_PRIVATE_DIR` 與 `OBSERVATION_DIR` 已建立，尚未或剛要於 CUA Node runtime 呼叫 `evidenceTools.captureAndPersist`。
- **觀察（假設）：** 三種互斥情境之一：(a) Agent 只在對話介面看到截圖／AX 就判定無法寫入檔案系統，或未先載入 `cua-evidence-tools` 定義區塊而僅測得 `typeof evidenceTools === "undefined"`（或直接觸發 `CUA_EVIDENCE_TOOLS_NOT_LOADED`）即宣稱 runtime 缺少 `captureAndPersist`；(b) 實際呼叫 helper 後回傳 `ready_for_bind=false`，或拋出含 `error`、`stages`、`blockers` 的失敗；(c) 任務中途 CUA 工具 namespace 被撤除。
- **可支持命題：** (a) 屬 `NOT_RUN`／Agent 未執行或 helper 未載入，不是環境或工具不支援，也不證明 helper 無法落地；(b) 才是實證阻塞，須保留真實 `error`（`name`／`code`／`message`）與 `stages`／`blockers`；(c) 只證明工具可用性變動，應停止且不得以對話摘要重建 AX 或截圖原件。
- **允許動作：** (a) 先建好私有目錄，先於同一個 Node runtime 載入 `cua-evidence-tools` 定義區塊，再實際呼叫 `evidenceTools.captureAndPersist`，讀回同一份 bytes 並核對後才封裝 bundle／`bind`；(b) 保留完整失敗輸出，只修正可歸因的路徑或權限問題後重跑一次，仍失敗就停在 `bind` 前；(c) 保存已落地原件與進度，停止依賴 CUA 的步驟並回報工具不可用。
- **禁止推論：** 對話介面可見截圖等於已落地；未執行 helper 或只測得 `typeof evidenceTools === "undefined"`／觸發 `CUA_EVIDENCE_TOOLS_NOT_LOADED` 等於環境不支援或 runtime 缺少 `captureAndPersist`；改跑裸 `lineApp.getAXStateAndScreenshot()` 後可宣稱 helper 不可用；工具撤除後可用對話摘要補造 AX／截圖；helper 失敗可用檔案名稱或猜測補值。
- **缺少證據：** 真實 CUA runtime 的落地讀回、namespace 撤除情境與 LINE E2E 均 `NOT_RUN`；本案例是假設文件案例。
