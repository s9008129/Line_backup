新增 LINE 全螢幕定位研究與 E2E 修復計畫

意圖
整理讓 LINE 相簿備份不再依賴使用者提供完整選單截圖的研究與執行計畫。計畫以自動取得完整桌面畫面、同源定位與安全派送為首要修復方向，並要求以真實檔案及 state 驗證備份完成。本提交包含研究與計畫，不代表已完成實作或 E2E。

已完成
- 新增 Apple／WWDC 技術研究與官方來源快照，分析 Vision OCR、OCRTool、ScreenCaptureKit、視窗與座標定位、派送及備份驗證，並區分已查證事實、推論與未知。
- 新增不含影像的 SDK／設定探針及原始執行紀錄。macOS 27.0.1 上讀得 modern minimumTextHeightFraction=0.03125、legacy minimumTextHeight=0.0；兩者 revision 均為 3，語言支援查詢包含 zh-Hant。
- 新增可直接交給 Implementer 的全螢幕定位與 E2E 修復計畫，以及 v3 合約、handoff、授權與使用者免審查決策、planner 結果和文件檢查紀錄。handoff.json 與 plan-contract.json 雜湊相同；兩者及 planner.result.json 的文件 shape 檢查均為 VALID。
- 計畫保留已知歷史 3+1 額度，另記使用者授權的 +5 material attempts；要求完成兩個不同且未 VERIFIED 相簿的真實 E2E。既有 verified 相簿不得重下載；不確定 Save All 是否派送時，先 reconcile，不得重送。
- 新增本次 Git publication 與 pre-publication preservation 紀錄，以保存實際交付範圍及工作樹基準。依使用者指定，以唯一 GPT-6-luna（xhigh）唯讀子代理梳理上下文、撰寫提交訊息；root 核對後執行 Git 交付。

已觀測驗證與限制
- 指定 Xcode 所附 macOS 26.5 SDK 的設定探針建置及執行成功；指定 macOS 27 SDK 的 typecheck 失敗，紀錄指出 Swift 6.3.3 與 SDK Swift 6.4 不相容。macOS 27 SDK 存在，不代表 OCRTool 已成功建置或執行。
- 本輪沒有執行影像 OCR、螢幕擷取、LINE 操作、下載、state 寫入或 E2E；沒有修復實作、實作測試 PASS、產品 Acceptance 或產品 DONE 結果。
- 研究報告中較早的建議曾要求新計畫先經獨立審查及另行授權；之後使用者明確要求直接交由 Implementer 執行並免除該審查前置。新封包以獨立 waiver 記錄此後續決策；合約中的 plan_review_required 仍保留，免審狀態是 WAIVED，不是 PASS。
- Apple legacy minimumTextHeight 網頁預設值與本機 SDK／runtime 的 0.0 讀值不同，研究保留此矛盾；未把預設值差異宣稱為既有 OCR 錯誤的已證實根因。
- 研究引用部分本機歷史報告、程式及證據；它們不全包含在本次提交中，因此單靠本提交未必能重現所有引用內容。探針執行檔、module cache 及其他既有 dirty／untracked 工作均未納入本次提交。
- Git 交付期間，交接目錄出現新的實作起始快照及進度更新。提交鎖定本次研究與規劃檔案清單，保留這些並行產生的實作資料；上述未執行項目描述本次研究及 Git 交付，不代替其他執行流程的即時狀態。

下一步建議
Implementer 依計畫記錄 fresh baseline，先在 CUA 開啟選單後、進行其他 UI 觀察前立即擷取完整桌面原圖，再驗證 popup、同源映射與安全點。接著完成兩個不同 eligible 相簿的檔案、內容及 state 閉環，提交逐步 E2E 報告。遵守 +5 attempt 上限及同一根因最多 3 次的規則；同一根因連續兩次沒有新資訊、額度耗盡或必要能力不存在時，保存證據並停止。不確定的 Save All／確認輸入不得重送。無法取得第二個 eligible 相簿時如實回報 PARTIAL；正式獨立 Acceptance 安排在 E2E 報告之後。
