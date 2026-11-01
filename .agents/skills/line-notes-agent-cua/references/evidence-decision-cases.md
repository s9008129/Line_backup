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
- **允許動作：** 暫停 B；以 A 的原事件、原 viewer、原目的地 reconcile。若正面完成證據成立才可 `DOWNLOAD_FINISHED` 並 verify；否則維持 `UNKNOWN`。
- **禁止推論：** 晚到結果算成 B；重設 A；看到檔案就直接 verify；為 B 建 intent 或重送。
- **缺少證據：** attempt／viewer／目的地歸屬、終結訊號、穩定檔集；若檔案存在，還缺 hash、解碼與 completion。

## C5 播放結束不是下載完成

- **前提：** 影片 attempt 已存在。
- **觀察（假設）：** viewer 播放到結尾或顯示「重播」，但沒有可歸屬下載終結訊號或穩定結果檔。
- **可支持命題：** 只支持播放狀態；不代表已下載，也不能推論媒體種類。
- **允許動作：** 將播放觀察與下載狀態分開；回到原 attempt 查可歸屬終結證據。尚無 outcome 時先以 `outcome` 記 `UNKNOWN`；已有 `outcome=UNKNOWN` 且有新證據才可 reconcile；若既有 outcome 已是 `DOWNLOAD_FINISHED` 則只接續驗證；其他終態不得重寫。單憑播放狀態不足以 verify。
- **禁止推論：** 播放結束等於下載完成；影片必須出現照片 toast；可跳過 ffmpeg 完整解碼或 completion。
- **缺少證據：** 下載終結訊號、原目的地與檔案歸屬、穩定檔集、ffmpeg／ffprobe 驗證、completion 讀回。

## C6 無 outcome 的 crash window

- **前提：** `intent` 已保存並讀回，可能已輸入；程序在第一筆 outcome 前 crash 或重啟。
- **觀察（假設）：** ledger 有 intent、沒有 outcome；重啟後沒有可歸屬 chooser／進度／檔案，暫存目錄可能為空。
- **可支持命題：** 只支持存在 crash window 與可能已派送；缺少資料不是空帳，也不是未派送證明。
- **允許動作：** 找回原 attempt；用 `outcome` 記第一筆真實結果，證據不足就記 `UNKNOWN`；有後續新證據才可 reconcile。停止新派送、verify 與下一項。
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

- **前提：** 同一 attempt 已有 outcome，準備判斷能否 verify 與計完成。
- **觀察（假設對照）：** 充分的下載終結候選是可歸屬原 attempt／viewer／原目的地的正面終結訊號，加上原目的地的穩定結果檔；充分的完成證據再加入檔案數、非空、SHA-256、逐檔解碼、發布與 completion 讀回全部成立。不足組合是只有 chooser、API 成功、播放結束、照片 toast 單獨一項、空目錄、部分檔案、名稱／hash 相同，或 completion 未讀回。照片的「下載完畢」提示可作可能的終結觀察之一；影片不要求同一 toast，但必須有自己的可歸屬正面終結證據。
- **可支持命題：** 下載終結候選支持 `DOWNLOAD_FINISHED` 與進入 verify；只有完整檔案驗證及 completion 讀回支持 `COMPLETED`。不足觀察只支持進一步查證或 `UNKNOWN`。
- **允許動作：** 已有 `outcome=UNKNOWN` 且下載終結候選成立時，以 `reconcile` 追加新證據；若既有 outcome 已是 `DOWNLOAD_FINISHED`，直接驗證。只有最終為 `DOWNLOAD_FINISHED` 才可 verify，再讀回 completion。尚未有 outcome 的 crash window 依 C6 處理，不把本案例當成第一筆 outcome 的替代。不足時停在上一個已證明層次，不重下補帳。
- **禁止推論：** 終結訊號單獨就是 completion；chooser／播放結束／照片 toast 是所有媒體的必要條件；本機驗證等於服務端原始位元或外部副本完整。
- **缺少證據：** 充分組合仍缺真實 LINE 執行與當次工具輸出；本文件案例不能填補該缺項。

## C9 停止證據：充分與不足

- **前提：** 原 attempt 未確認下載完成，評估是否能終結為 `STOPPED`／`NOT_SENT` 或建立恢復 attempt。
- **觀察（假設對照）：** 充分的觀察是有可歸屬原 attempt、足以正面排除原操作稍後繼續的明確停止／未派送 receipt，且原任務授權涵蓋恢復；不足的觀察只有 timeout、API error、控制隱藏、空目錄、缺少 marker、舊計數為零、播放結束或 Owner 口頭聲明。
- **可支持命題：** 充分 receipt 才可能支持終態；不足觀察只支持 `UNKNOWN`。本文件沒有取得任何真實充分 receipt。
- **允許動作：** 充分、授權且帳本已持久化 `recovery_authorized=true` 時，保留原檔並依下載文件以 `intent --recovery-evidence` 建立另一個新空白恢復目錄；授權未持久化或證據不足時停止。不足時保留 `UNKNOWN`，不 verify、不建新 attempt、不重下、不派下一項。
- **禁止推論：** 假設 receipt 已被本次工具取得；缺 marker 等於停止；新目錄／新 Session 可解鎖；可用相簿控制替代記事本流程。
- **缺少證據：** 真實平台是否能提供足以排除副作用的停止證據仍 `UNKNOWN`；未提供能力不得由案例補齊。
