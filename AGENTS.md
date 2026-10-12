# LINE 相簿全自動備份專案憲法

本文件是本專案的補充規範，須與上層通用 Harness 契約及每一輪經審查的任務計畫一併遵循。若本文件與上層安全、證據或授權規範衝突，遵循較高層規範；不得以本文件降低任務計畫中的 gate。

## 專案目標

本專案的完成目標是建立並實證一套完整的 LINE 群組相簿全自動備份流程：能可靠辨識群組與相簿、略過已驗證資料、按安全交易機制派送 LINE 原生下載、驗證所有檔案內容並完成狀態提交，且能安全地移至下一本 eligible 相簿重複流程。只完成畫面辨識、選單定位、單一相簿導覽或離線測試，不得宣稱完整備份 E2E 已完成。

## 有界、真機優先的執行循環

**既有 Harness 安全、授權、CRITICAL 審查及 frozen Plan/contract 均繼續有效。** 本節不是新 GUI 授權、不是 controller waiver、不是要求不計代價直接點擊。每輪只完成當前經核准的範圍；不因「直到總目標完成」就自動創建下一輪工具開發任務。

1. **先找第一個真實阻塞：**明列原始 END_GOAL、CURRENT_SLICE、FIRST_UNMET_REAL_GATE、舊根因額度、該 Gate 所需真實 LINE 證據；先確認既有 live producer → retained screenshot/AX → analyzer → observation 是否已能成功運行。必要的既有安全 preflight 不得省略。
2. **以真機結果決定是否修工具：**若環境與授權允許，優先做一次有界的真實唯讀資料鏈／已核准的導覽測試。只有可重現的真實斷點能證明必要性時，才做對應最小修正及最少的針對性回歸；模擬資料、fixtures、CI PASS、文件與報告只能標為 ENABLER，不得當成 LINE 產品 PASS。
3. **防止模擬無窮循環：**沒有真實證據指出新需求前，不新增另一套通用測試框架、synthetic matrix、模擬 producer、校準引擎或廣泛重構；Reviewer 不得把與當前必需 Gate 無關的建議轉為阻塞。本規則不豁免已有必要測試、資料完整性或安全驗收。
4. **真實動作仍然受控：**LINE 前景交接與當輪具體 GUI 授權須已成立；送出 scroll/click 後保存新鮮前後畫面並證實新卡／正確詳細頁。若沒有真機能力、權限或 frame 證據，立刻以 BLOCKED 回報，不改跑更多 fixtures 充當進展。Save All、chooser、下載及持久 state 一律遵循既有一次性交易 gate。
5. **停止與交接：**同一根因最多三次有證據的嘗試、連續兩次無資訊增益即停止或升級；跨任務／worktree／模型不可重置。保存 E2E測試報告.md 與原始收據，逐項寫 GOAL_GATE_DELTA、INFORMATION_GAIN、NEXT_AUTHORIZED_REAL_STEP 和未完成總目標。只有語意／架構／安全／frozen gate 變更，才依既有 Harness 重新規劃與獨立審查，不能為每個小測試失敗不斷凍結新計畫。

## LINE 相簿 E2E 的必要證據與順序

- 相簿候選必須以新鮮畫面及可核對的群組、日期範圍、照片數和窗口／列表連續性確認；點位不得從過期 frame 重用。任何需要 LINE 前景的 UI 操作前，先告知使用者目標 app／畫面與下一個精確動作，請使用者交還前景，並等待明確交接；若前景在操作途中被取回，立即停止輸入，待再次明確交接後重新擷取和核對畫面再繼續。
- Save All 只可在核准的 duplicate、目的地、owner、持久 intent、menu identity／geometry 及 at-most-once gates 全部通過後派送；結果不確定時不得重送。每次派送、chooser 確認、下載、檔案驗收與 state readback 都須有獨立可追溯證據。
- 單一相簿成功不等於完整批次流程。首次交易完成並 VERIFIED、讀回且釋放 owner 後，必須另行驗證「回到相簿列表 → 至少一次 bounded scroll 到新內容 → fresh capture 確認 scroll effect 與卡片連續性 → 選取下一本 eligible 相簿 → 重跑完整備份及驗收」的流程。即使下一張 eligible 卡片原本完整可見，也不得因此跳過使用者特別要求的實際 scroll gate。不得用重新開啟已驗證相簿來製造第二個案例；若沒有 eligible 下一本，記錄 `NO_ELIGIBLE_TARGET`；若未執行 scroll，記錄 `SCROLL_TEST_NOT_RUN`／PARTIAL，不得宣稱該 gate 通過。
- 每次 bounded 0.25-view-height scroll 都需保存操作前、操作與操作後的觀察及截圖；確認同群組／surface／session／PID／window／layout 連續性、至少一張完整唯一相鄰卡片的有序 overlap，以及至少一張新而完整候選的日期和張數。畫面、滾動效果或 identity 不明確時停止，不猜點、不連續滾動或重用舊座標。
- 完整驗收至少分開呈現：UI／menu 校準、單本交易完成、下一本 scroll 與 grounding、第二本交易完成，以及整體批次／狀態驗收。每項只能由其自身證據判定。

## 報告交接與阻塞處理

`E2E測試報告.md` 是迭代循環中的正式證據交接物，不是僅供摘要的備忘錄。每輪報告完成後，將它交給本輪指定的高階 Planner；若執行環境沒有可用的 Planner 通道，保留報告與進度記錄，明確回報尚未完成 Planner 交接，不得聲稱已提交。Planner 輸出須精確指出本輪事實、未知、阻塞、下一個決策及其驗收方式。

遇到 writer guard、狀態不一致、身份歧義、前景中斷、目的地副作用或任何未預期結果時，保留現場證據與既有資料，停止依賴該前置條件的後續操作，並將可重現資訊、錯誤原文、前後狀態和精確所需決策寫入報告。不可為了讓 E2E 看似完整而另換 writer、遷移狀態、刪除資料、降低 gate 或派送未核准的 UI 動作。
