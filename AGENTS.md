# LINE 相簿全自動備份專案憲法

本文件是本專案的補充規範，須與上層通用 Harness 契約及每一輪經審查的任務計畫一併遵循。若本文件與上層安全、證據或授權規範衝突，遵循較高層規範；不得以本文件降低任務計畫中的 gate。

## 專案目標

本專案的完成目標是建立並實證一套完整的 LINE 群組相簿全自動備份流程：能可靠辨識群組與相簿、略過已驗證資料、按安全交易機制派送 LINE 原生下載、驗證所有檔案內容並完成狀態提交，且能安全地移至下一本 eligible 相簿重複流程。只完成畫面辨識、選單定位、單一相簿導覽或離線測試，不得宣稱完整備份 E2E 已完成。

## 強制迭代循環

每輪工作依以下循環進行，直到整體目標達到經核准的完整驗收條件：

1. **高階規劃：** Planner 根據最新程式、任務計畫、先前證據與未解問題，提出本輪目標、範圍、前置條件、停止條件、驗收 gates 和必要的實作／測試步驟。改變架構、狀態格式或寫入者、資料／安全邊界、授權或驗收 gate 時，必須先形成並審查新計畫。
2. **實際驗證：** Implementer 嚴格依核准計畫執行。區分離線測試、唯讀觀察、GUI 操作與真實下載；不得把模擬、候選幾何或人工作業觀察寫成工具 PASS。LINE 前景操作必須遵循使用者交接要求；若前景交接尚未明確完成，先停在不依賴前景的工作。
3. **完整證據回報：** 每輪實際測試都要產生或更新 task package 內的 `E2E測試報告.md`，作為高階 Planner 的持久輸入。報告須記錄目標與計畫版本、實際步驟及順序、使用的工具／程式／命令與關鍵程式片段、測試資料和環境、成功／失敗／未執行項目、預期與實際結果、狀態前後差異、副作用、嘗試歷史及每次嘗試帶來的新資訊；列明未知事項、限制與停止原因。每項關鍵主張須連到 workspace 內的證據檔案，包含相對及絕對路徑；截圖、manifest、OCR、命令輸出、測試記錄和來源檔應提供 hash 或可重現的識別資訊。不得補造未觀察到的證據，也不得把失敗覆寫成成功。
4. **高階重新規劃：** Planner 必須閱讀本輪報告與原始證據，逐項判斷哪些事實改變了假設、哪些 gates 已 PASS／仍 BLOCKED、與完整目標距離如何變化，再提出下一個有界且可驗收的 implement／test 計畫。若本輪遇到超出核准範圍的架構或安全阻塞，保留已證實結果並提交精確的決策需求；不可由 Implementer 自行繞過。
5. **重複直到完成：** 依新核准計畫再實作、再測試、再回報。這個循環仍受上層 Harness 對同一 root issue 的嘗試上限、升級與 material blocker 停止規則約束；不可無限重試或用重複無新資訊的測試代替規劃。只有所有必要 gates 均有明確 PASS 和實際證據，且完整流程驗收通過，才可關閉專案目標。部分成功必須保留為部分成功，並繼續迭代。

## LINE 相簿 E2E 的必要證據與順序

- 相簿候選必須以新鮮畫面及可核對的群組、日期範圍、照片數和窗口／列表連續性確認；點位不得從過期 frame 重用。任何需要 LINE 前景的 UI 操作前，先告知使用者目標 app／畫面與下一個精確動作，請使用者交還前景，並等待明確交接；若前景在操作途中被取回，立即停止輸入，待再次明確交接後重新擷取和核對畫面再繼續。
- Save All 只可在核准的 duplicate、目的地、owner、持久 intent、menu identity／geometry 及 at-most-once gates 全部通過後派送；結果不確定時不得重送。每次派送、chooser 確認、下載、檔案驗收與 state readback 都須有獨立可追溯證據。
- 單一相簿成功不等於完整批次流程。首次交易完成並 VERIFIED、讀回且釋放 owner 後，必須另行驗證「回到相簿列表 → 至少一次 bounded scroll 到新內容 → fresh capture 確認 scroll effect 與卡片連續性 → 選取下一本 eligible 相簿 → 重跑完整備份及驗收」的流程。即使下一張 eligible 卡片原本完整可見，也不得因此跳過使用者特別要求的實際 scroll gate。不得用重新開啟已驗證相簿來製造第二個案例；若沒有 eligible 下一本，記錄 `NO_ELIGIBLE_TARGET`；若未執行 scroll，記錄 `SCROLL_TEST_NOT_RUN`／PARTIAL，不得宣稱該 gate 通過。
- 每次 bounded 0.25-view-height scroll 都需保存操作前、操作與操作後的觀察及截圖；確認同群組／surface／session／PID／window／layout 連續性、至少一張完整唯一相鄰卡片的有序 overlap，以及至少一張新而完整候選的日期和張數。畫面、滾動效果或 identity 不明確時停止，不猜點、不連續滾動或重用舊座標。
- 完整驗收至少分開呈現：UI／menu 校準、單本交易完成、下一本 scroll 與 grounding、第二本交易完成，以及整體批次／狀態驗收。每項只能由其自身證據判定。

## 報告交接與阻塞處理

`E2E測試報告.md` 是迭代循環中的正式證據交接物，不是僅供摘要的備忘錄。每輪報告完成後，將它交給本輪指定的高階 Planner；若執行環境沒有可用的 Planner 通道，保留報告與進度記錄，明確回報尚未完成 Planner 交接，不得聲稱已提交。Planner 輸出須精確指出本輪事實、未知、阻塞、下一個決策及其驗收方式。

遇到 writer guard、狀態不一致、身份歧義、前景中斷、目的地副作用或任何未預期結果時，保留現場證據與既有資料，停止依賴該前置條件的後續操作，並將可重現資訊、錯誤原文、前後狀態和精確所需決策寫入報告。不可為了讓 E2E 看似完整而另換 writer、遷移狀態、刪除資料、降低 gate 或派送未核准的 UI 動作。

## 目標對齊補充：避免一直造工具、卻沒有進入真實相簿

本節補充、不得取代前述專案憲法與全域 Harness V4.8.0；不變更已審核的一次性派送、writer、資料驗收與授權規則。先核對本機真正的 branch、HEAD、dirty/untracked、當前核准 Plan/Handoff、已完成證據及權限；其他 worktree、舊歷史與 GitHub master 不自動代表現行執行權威。

### A. 使用者最終成果與本輪成果分帳

USER_END_GOAL：在真實 macOS LINE.app 列舉目標群組相簿，向下捲到原本未顯示的相簿，精準開啟每一本尚未 VERIFIED 的相簿，經安全交易及獨立授權儲存全部，逐本驗證檔案及狀態，再進入下一本並保留未完成清單。單本成功、57 張基線、已成功的 182 張下載、工具完成、CI PASS 均不等於總目標 DONE；已 VERIFIED 的相簿不再下載以充當成果，也不把 57 張專用 SHA/張數用於其他相簿。

CURRENT_SLICE 由目前有效的 Plan 與授權決定；只允許 read-only、navigation-only、A/B offline 或特定單本交易時須照實標示，不得自行擴大到 Save All／chooser／state 寫入。每輪明列仍缺少的總目標 gates。

### B. 導覽真機成果優先於工具成果

對已核准的「列表 → 捲動 → 第二本 → 詳情」導覽任務，優先取得：

- G0：重新量測現在 Mac 是否解鎖、LINE 是否登入，以及 TCC、視窗、前景身分；舊的 signed-out/locked 紀錄不是今天的事實。
- G1：真實列表原始畫面、AX/Vision 證據、確定的列表容器與可見卡片。
- G2：一個已授權的 bounded scroll；留存前後截圖、事件、列表連續性、新卡／位置改變，並遵守本檔前述 0.25-view-height、卡片 overlap/new-card 要求；posted event 不能冒充 LINE 已捲動。不滿足即記 PARTIAL/BLOCKED。
- G3：用新鮮影像唯一綁定新相簿的群組、日期／標題、張數、卡片，再依核准方法精準點擊；從新的詳細頁驗證身分。不符立即停止相依輸入。
- G4+：僅在另行核准的下載交易前置與授權滿足時，逐本走既有 Save All、chooser、檔案及狀態證據鏈；個別 fingerprint/manifest/ledger 獨立對帳，UNKNOWN 不盲目重送。

先查 AX 列表與可用 scroll；有真實 AX 不支援證據，才在已核准方案內使用 Quartz wheel。每捲後重新觀察；不以固定座標、未確認的 scrollbar、模糊文字或過期幀猜點。未取得真機導航權限就只執行獲准的唯讀步驟，本段文字本身不構成新的 LINE GUI 授權。

### C. 工具開發剎車與偏航偵測

G2/G3 尚未有真實 PASS 前，除非具名的真實故障證據證明既有元件無法達成下一個必要 gate，不得重建 Computer Use、大型 fixture matrix、通用校準平台或另一套並行觀察／交易引擎。優先局部修復已核准的現有實作。每次重大嘗試先記 BLOCKER_FINGERPRINT、可反駁假設、新資訊來源、結果 A/B 的不同後續；換模型、換 worktree、改 prompt 或同義重跑不能重置 root issue。每 root issue 最多三次有證據的嘗試，連續兩次無資訊增益就升級，必要時更早 STOP。

### D. E2E 報告與決策交接

現有 E2E測試報告.md 必須包含 USER_END_GOAL、CURRENT_SLICE、GOAL_GATE_DELTA、FIRST_UNMET_REAL_GATE、INFORMATION_GAIN、BLOCKER_FINGERPRINT、ATTEMPTS_USED、NEXT_DISTINGUISHING_STEP、NEXT_AUTHORIZATION_NEEDED、PARENT_GOAL_STATUS。附 source/contract/runtime 身分、命令、原始 frame/hash、實際結果及副作用；區分 NOT_RUN、OBSERVED、PARTIAL、BLOCKED、PASS。任何只證明工具可運作的結果皆標 ENABLER，不得記作 LINE 真實 E2E PASS。

若當前 Plan 將最終多本自動備份縮為單本／模擬工具卻沒有追蹤剩餘門檻，標 GOAL_COVERAGE_GAP，交 Planner 與適用的獨立審查；Implementer 無權改凍結合約，也不能把 replan 變成無限研究。下一步應是最小、有授權、可取得真實證據的里程碑。
