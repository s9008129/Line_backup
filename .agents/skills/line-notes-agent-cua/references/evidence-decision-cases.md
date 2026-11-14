# 證據判定案例

本檔用固定案例檢查 [證據與允許行為矩陣](verification-and-recovery.md#證據與允許行為矩陣)、[下載與 notes CLI](download-and-ledger.md) 與 [證據範本](evidence-template.md) 的判斷是否一致。全部案例都是文件規則的假設情境，不是本次 LINE 操作、真實停止 receipt、實機 `OBSERVED` 或 E2E PASS；案例中的時間、視窗與回傳若未由當次工具提供，實際紀錄必須寫 `UNKNOWN`。

## C1 控制檢查後隱藏

- **前提：** `intent` 已保存並讀回，尚未有 outcome；下載控制曾在同一 viewer 可見且映射明確。
- **觀察（假設）：** 最後一次輸入前核對時控制消失，沒有可歸屬 chooser、進度或終結訊號。
- **可支持命題：** 只支持當下未見控制與舊定位失效；不能證明未輸入、未派送、App 拒絕或控制不存在。
- **允許動作：** 停止輸入並重新定位；若沒有正面終態證據，按可能已派送保護，第一筆 outcome 記 `UNKNOWN`，之後只以新證據 reconcile。
- **禁止推論：** 控制隱藏等於未命中／未派送；沿用舊座標；用第二次點擊查證；換相簿入口。
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
- **允許動作：** 暫停 B；以 A 的原事件、原 viewer、原目的地 reconcile。若正面完成證據成立才可 `DOWNLOAD_FINISHED` 並 `download-check`；否則維持 `UNKNOWN`。
- **禁止推論：** 晚到結果算成 B；重設 A；看到檔案就直接 `download-check`；為 B 建 intent 或重送。
- **缺少證據：** attempt／viewer／目的地歸屬、終結訊號、穩定檔集；若檔案存在，還缺基本檔案檢查與 completion。

## C5 播放不是操作步驟或取證來源

日常 Agent 不播放／暫停、拖時間、調倍速或檢視媒體內容，也不為證明來源種類操作 viewer；不可點內容切換播放控制。只可移入游標或使用明確工具列控制顯示下載工具列。若歷史資料中已有播放觀察，不將它用作下載完成或來源種類證據。

## C6 無 outcome 的 crash window

- **前提：** `intent` 已保存並讀回，可能已輸入；程序在第一筆 outcome 前 crash 或重啟。
- **觀察（假設）：** ledger 有 intent、沒有 outcome；重啟後沒有可歸屬 chooser／進度／檔案，暫存目錄可能為空。
- **可支持命題：** 只支持存在 crash window 與可能已派送；缺少資料不是空帳，也不是未派送證明。
- **允許動作：** 找回原 attempt；用 `outcome` 記第一筆真實結果，證據不足就記 `UNKNOWN`；有後續新證據才可 reconcile。停止新派送、檔案檢查與下一項。
- **禁止推論：** 沒有 outcome 就是未送出；空目錄等於 `NOT_SENT`；先呼叫 reconcile；建立新空白 attempt 或重建 ledger。
- **缺少證據：** 是否真正送出、原 viewer／chooser／進度、原目的地檔案、可歸屬終結或停止證據。

## C7 UNKNOWN 未收斂

- **前提：** attempt 已有 `UNKNOWN`，並已依原事件、原 viewer、原目的地調和。
- **觀察（假設）：** 只有 timeout、畫面未變、空目錄或缺 marker；相同查證方法連續兩次沒有新資訊。
- **可支持命題：** 只支持尚未收斂；這是同一列表帳本的 blocker，不是 `NOT_SENT` 或完成。
- **允許動作：** 保留 `UNKNOWN`，停止相同查證，保存證據並提出最小具體問題。
- **禁止推論：** Owner 口頭聲明、換目錄、重置 ledger、換列表或相簿入口可解鎖；缺 marker 可改寫成 `NOT_SENT`。
- **缺少證據：** 可歸屬終結訊號，或足以安全支持 `STOPPED`／`NOT_SENT` 且排除晚到作用的停止 receipt；目前能力仍 `UNKNOWN`。

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

## D1 Viewer 返回契約在進入後核對

- **前提：** 目標貼文／媒體已核對，尚未建立下載 intent，Agent 準備開啟 viewer。
- **觀察（假設）：** 貼文詳細頁來源 observation 與貼文錨點已保存；viewer 尚未進入，因此尚無 viewer 返回控制。
- **可支持命題：** 可用來源錨點與預期返回角色核對稍後返回。進入前看不到返回控制是正常資訊缺口，不代表禁止進入。
- **允許動作：** 依有效前景及當次映射開啟目標 viewer；進入後先觀察控制所屬 app／window、角色、焦點與歸屬。確認可返回預期角色後才建立下載 intent。
- **禁止推論：** 進入前不存在返回按鈕；單獨標為「關閉」的按鈕必定回到來源貼文；舊 viewer 座標可重用。
- **缺少證據：** viewer 內返回控制的歸屬與作用須由進入後的新 observation 判斷；本案例不是實機結果。

## D2 返回後頁面偏離預期

- **前提：** 已從 viewer 送出一次有證據的返回輸入。
- **觀察（假設）：** 新 observation 顯示畫面仍是 viewer、已變成聊天，或無法連回來源貼文錨點。
- **可支持命題：** 返回未得到預期的 `POST_DETAIL`；若列表連續性也消失，記 `ENTRY_LOST`。
- **允許動作：** 停止原返回方法，保存前後 observation 與輸入 receipt；分開記錄頁面角色、前景、觀察及輸入能力。
- **禁止推論：** 再按一次 Escape／Command-W、改猜關閉鍵或沿用舊座標可安全退一層。
- **缺少證據：** 真實返回控制命中、後續 GUI 行為與 LINE E2E 均 `NOT_RUN`。

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
- **可支持命題：** 同一有效前景內的平台 reacquire 沿用 notes Session，不重跑 `bind`。真正中斷後重新交接須使用新 notes Session ID。
- **允許動作：** 新 Session 保存新 observation、核對列表，先處理舊交易，再顯式 interrupt 舊 open scan，之後以普通完整 scan 接續。
- **禁止推論：** `bind` 會替舊 scan interrupt；新 scan 可解鎖 UNKNOWN；一般入口恢復可使用 restart／recovery scan；帳本內既有完成或待盤狀態可改寫。本匿名事故案例的兩項 ACTIVE 與 49 篇 `DETAIL_PENDING` 是案例事實，不是所有列表的固定數值。
- **缺少證據：** 跨 Session 真實恢復及完整 51 篇 E2E 仍 `NOT_RUN`。
