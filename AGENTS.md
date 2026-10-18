# LINE 相簿全自動備份專案憲法

本文件是 LINE 備份專案的補充規範，與適用的上層 Harness／平台限制並行。Owner 已重新指定短期目標為「在真實 macOS LINE 上，連續完成兩本不同且符合資格相簿的 Save All、下載與原圖驗證」。先前僅針對單次捲動或特定合成測試的任務計畫，不能被當作永久的產品目標或禁止新實機診斷的理由；必要時由 Planner 提出有界的專案級計畫／政策／程式修訂，依 Owner 授權及必要獨立審查實施。本文不自動修改可執行的 grant、ledger 或原始碼，也不得超越更高優先層級的限制。

## 專案目標

本專案的完成目標是建立並實證一套完整的 LINE 群組相簿全自動備份流程：能可靠辨識群組與相簿、略過已驗證資料、按安全交易機制派送 LINE 原生下載、驗證所有檔案內容並完成狀態提交，且能安全地移至下一本 eligible 相簿重複流程。只完成畫面辨識、選單定位、單一相簿導覽或離線測試，不得宣稱完整備份 E2E 已完成。

**近期優先交付：**從真實 LINE 畫面辨認相簿 A → 點開及 Save All → 對實際下載檔案逐一核驗 → 回列表並實際捲動 → 找到且核對不同的相簿 B → 點開及 Save All → 完整檔案驗證與狀態核對。優先用真實操作的前後證據找根因、最小修正、再實測；合成測試僅用於回歸，不能取代 LINE 實機結果。若沒有兩本新的 eligible 相簿，忠實回報限制，不能重複下載既有已驗證相簿湊數。

## 強制迭代循環

每輪工作依以下循環進行，直到整體目標達到經核准的完整驗收條件：

1. **精簡規劃：** Planner 先讀真實 LINE 證據，直接選擇能推進兩本 Save All 的最短可驗證步驟。既已授權、同一前景交接範圍內的可逆導覽，不必每一步重新提案或反覆請求相同授權。變更 protected state、不可逆派送、可執行授權機制或驗收契約時，則須準備精確差異、完成必要 Owner 決策與獨立審查。
2. **真實驗證優先：** Implementer 負責必要實作；獨立 E2E 驗收者在合法且有效的執行入口上以真實 LINE 驗證。區分合成、唯讀、實際 GUI、實際 Save All、下載檔案與原圖驗證；不得把任何一項混報成另一項 PASS。LINE 前景操作開始前須有 Owner 當次有效交接；同一不中斷的前景測試不必每次點擊重做交接，若前景變更則停止輸入並重新確認。
3. **完整證據回報：** 每輪實際測試都要產生或更新 task package 內的 `E2E測試報告.md`，作為高階 Planner 的持久輸入。報告須記錄目標與計畫版本、實際步驟及順序、使用的工具／程式／命令與關鍵程式片段、測試資料和環境、成功／失敗／未執行項目、預期與實際結果、狀態前後差異、副作用、嘗試歷史及每次嘗試帶來的新資訊；列明未知事項、限制與停止原因。每項關鍵主張須連到 workspace 內的證據檔案，包含相對及絕對路徑；截圖、manifest、OCR、命令輸出、測試記錄和來源檔應提供 hash 或可重現的識別資訊。不得補造未觀察到的證據，也不得把失敗覆寫成成功。
4. **缺陷驅動迭代：** Planner 對照真實失敗的第一拒絕、實際 GUI 派送數和原始證據，指派最小修正、聚焦回歸並盡快回到實機；不要用大量假資料測試或重複規劃取代實測。專案自訂規則若阻礙可逆導覽，應追到程式與政策來源，提出可稽核的修訂；不得只改報告中的 PASS、偽造授權或跳過仍在執行的 guard。
5. **持續到實際成果：** 每輪依真實資訊增益推進一個操作或可證明的根因。適用的 Harness 停止／升級規則仍有效；遇到實際阻塞時可經 Owner 核准調整本專案的執行設計，而不是永久停在同一個測試計畫。不得在派送結果不明時盲目重試 Save All。只有兩本不同 eligible 相簿的真實 Save All、檔案內容驗證、正式狀態讀回及獨立 E2E 成立，才能回報完整達標。

## 實機診斷與權責分工

- **Owner（使用者）：**目標、範圍、例外政策及真實操作授權的唯一決策者。Owner 本次已概括同意在受控前景下進行真實導覽及針對兩本不同、未備份、符合資格相簿的 Save All 測試；此意向不能冒充已啟用的程式 grant 或當次 Mac 前景狀態。
- **Planner（模型由 Owner 逐階段指定）：**只負責方向、風險、精確 Plan／Contract／交接草案，不負責持續監督 Implementation；需要時才選高階推理模型。
- **Implementer（模型由 Owner 逐階段指定）：**取得已核准 Plan、固定來源與 Handoff 後，在全新 Session 獨立完成最小必要實作、focused tests、Git/PR 交付；不得兼任自己成果的獨立 Code Reviewer 或 E2E。
- **Independent E2E（模型由 Owner 逐階段指定）：**在與 Implementer 不共享對話的全新 Session 中執行獨立驗收；若由真實交易 E2E 唯一控制 LINE GUI，須先具備精確版本審查、有效 runtime/grant 與當次前景交接。
- **外部雲端 Chief Reviewer（Owner 本次指定 ChatGPT／本對話）：**同時擔任獨立 Plan Reviewer 與實作後的 Independent Code Reviewer；不是 Sol 指派的本機子代理，不在本機 Codex Harness 代理樹內運作，不能被本機 Sol 代審或偽造審查結果。Owner 可日後明確改指定其他雲端模型。由 Owner 將 Plan、PR、完整報告及必要證據交給雲端 Reviewer；只有實際完成的雲端審查才可寫入審查狀態。
- **可逆導覽**（被動觀察、在已辨識的相簿列表內捲動、點開相簿及返回）：優先在 Mac 真實執行並保留前後證據；不把 LINE 回傳的多個 `AXFocused=true` 當作已證明有多個真正鍵盤焦點。以正確 app／群組／視窗、唯一列表與安全目標區域、可觀察的結果判定。不得點擊無法排除為發訊息、刪除或 Save All 的目標。
- **正式下載**（Save All、檔案寫入、state mutation）：仍須明確符合資格、排除歷史重複、檢查目的地與派送結果，遵守有效的交易與不重送保護；239 張歷史 VERIFIED 紀錄以及已人工備份的 65 張相簿不可以重複 Save All。
- **政策與執行分界：**AGENTS.md 是工作規範，不是執行時授權。專案目前硬編碼於 `mac/analyzer.mjs` 的焦點條件、`src/line_backup_batch/store.py` 的 `2/2` 觀察配額、`two_album_entry.mjs` 的 ledger 初始化及正式 C1／點擊限制，必須透過明確的源碼／政策修訂與適用授權才能改變行為；不得更改已使用計數、改名 checkpoint 偷渡配額、重置 ledger 或重開已關閉 grant。可由 Owner 授權建立有界的獨立可逆診斷入口，保留 append-only 原始證據，不將其結果冒充正式 Save All gate PASS。

## 多代理協作、獨立審查與完成證據

本節針對本專案修正「過度管理、實作提前交差、共同錯誤假設、假驗收」的風險。**角色是 Planner／外部 Plan Reviewer／Implementer／外部 Code Reviewer／Independent E2E；實際模型與 Provider 每輪由 Owner 決定。ChatGPT 目前為 Owner 指派的外部流程管控者及兩道 Reviewer，不是本機常駐監督 Agent。**依本檔「外部審查與 GitHub Handoff 接力 SOP」進行，保留上層 Harness、執行時 grant、交易 ledger 與真實來源契約。

### 角色與不得混淆的兩道外部審查、實作及獨立 E2E

1. **Plan / Planner（本輪 Owner 指定模型）：**只讀取最小現況、釐清風險／業務 AC、凍結 literal 可修改路徑／證據／Plan 與 Contract、產出交給 Implementer 的 Handoff 草案並提交 Draft PR；完成便停止，不監督實作、不長時間管理子代理。模型不可用就記錄實際模型，不偽稱指定型號。
2. **Independent Plan Reviewer＝Owner 指定的外部雲端 ChatGPT（本機 Harness 外）：**Sol 完成新 Plan 或重大修訂後，先固定 Plan revision／SHA，連同 **Owner 原始需求、真實 LINE 證據、AC 與保護條件**提交 GitHub／提供 Owner 轉交本對話 ChatGPT。ChatGPT 獨立檢視是否偏離「兩本真實 Save All」、架構假設、正反案例、權限與 AC 可驗性，輸出 `APPROVE_PLAN`／`CHANGES_REQUIRED`／`BLOCKED` 與審查連結；**未取得真實雲端 Plan approval，不得把重大新 Plan 宣稱已核准或進入其正式 Implementation**。Sol／Luna 不能透過本機子代理替代、預填審查意見或覆蓋結論。已核准 Plan 內的有界缺陷修正不必每輪重新 Plan Review；只有目標、架構、授權／資料邊界或 AC 實質變更，才提出精確差異重審。
3. **Implementation / Implementer（本輪 Owner 指定模型）：**以新的獨立 Session 取得固定的 approved Plan／Contract／GitHub Handoff／Code base，執行限定範圍的最小改動、focused tests 與階段 Git/PR 交付；不擅自更改 AC、安全或授權、不嵌套管理代理。IMPLEMENT 完成不等於 E2E PASS，阻塞須附原始證據與下輪 Handoff。
4. **Post-Implementation Independent Code Reviewer＝Owner 指定的外部 ChatGPT（目前本對話）：**由 Owner 轉交 Implementer 的精確 PR/HEAD、diff、驗證與接續 E2E Handoff；Reviewer 僅依真實證據判斷 APPROVE_IMPLEMENTATION／CHANGES_REQUIRED／BLOCKED。退回時只交精確缺陷、允許範圍與驗證方式；未獲實際版本核准，不得放行 E2E。外部 Code Review 不等於 runtime grant、正式 GUI 授權或 E2E PASS。
5. **Independent E2E / Owner 當輪指定模型與 Provider：**全新獨立 Session，不讀 Implementer 推理歷史，不同時控制 LINE。唯讀檢查待驗收程式／AC，不自行修產品或修改標準；對經授權且唯一的真實 GUI／交易流程可執行操作並保留事實、檔案及 state readback。模型與工具能力須由 Session 真實紀錄證明，PASS／FAIL／BLOCKED／NOT_RUN 由它獨立判定。對於 HUMAN_ASSISTED 模式，Owner 才是人工點擊者，不能把人工輸入偽裝成模型 Computer Use PASS。
6. **Owner／外部雲端 Reviewer 的主權邊界：**Owner 擁有目標、實機／交易授權、驗收標準及雲端審查模型選擇權；目前由本對話 ChatGPT 擔任兩道外部審查。**Sol 只能向 Owner 交付 Plan／PR 審查包，不能指派、取消、干預或取代這兩項雲端審查。**雲端 Reviewer 不受本機 Codex 子代理數量、角色指令、子代理上下文及排程規則支配，但仍依 Owner 原始目標、可讀證據與專案安全／交易契約進行獨立判斷；外部審查不會自動建立可執行 grant、改寫 ledger 或授權 GUI。Owner 後續可明確選用其他雲端模型，須記錄真實模型與審查來源。

### 子代理調度、執行環境與修復閉環

- **正式 E2E 的獨立交接與 GUI 獨占：**Owner 只在外部 Code Review、正式 runtime/grant／前景條件符合後啟動當輪指定的 E2E Session。只傳固定 AC、精確 Commit、runtime/grant、核准入口、隔離證據位置與階段 Handoff，不傳實作推理歷史或預設 PASS。同一時間只有一位合法 GUI 操作者；HUMAN_ASSISTED 模式由 Owner 輸入、E2E Agent 觀察驗證。換模型不會授權交易或補齊工具能力。
- **少量、有限、可衡量的派工：**預設每個階段只有一個主 Session、零個額外子代理；真正可平行且有不相交寫入範圍才按核准 Plan 與 Harness 限制分工。外部 ChatGPT 審查後由 Owner 發出下一階段 Prompt；禁止長時間高階主代理監控、巢狀代理樹、重複審查同一內容或無新資訊的修復循環。
- **環境先對帳：**每個工作包先確認 Git remote／root／worktree／branch／base SHA、可修改範圍、工具版本、Python／Swift 或 Container、實際 macOS LINE 實例／window、TCC／GUI 授權及測試目的地。實作可用獨立 worktree；E2E 優先使用固定 Commit 的唯讀／隔離 worktree 與獨立證據輸出，禁止與 Implementer 共寫測試、程式或驗收基準。不同 Session 不等於隔離檔案系統／憑證／macOS 前景：若共享資源，須明確限制寫入者，真實 LINE GUI 同時只能有一個操作 owner。
- **不中斷正常 Worker：**Sol 在事先約定的里程碑檢查進度，先查工具是否仍執行、是否有新證據；不可只因暫時沒有輸出、輪詢逾時便中止正在有效工作的 Luna，也不可高頻輪詢或每輪重建子代理。明確小修由原 Implementer 完成；跨模組／證據矛盾由 Sol 分析後再派工；需修改架構／AC 才回 Plan Review。相同根因若連續兩次修復沒有新證據或同樣失敗，停止相同派工，先做第一性原理診斷及必要升級；不能用換模型或新 Session 假裝已修復。
- **禁止提前結案：**Implementer 每項 AC 必須標明完成／未完成／阻塞；Sol 應檢查是否真的整合到指定版本並完成必要測試，不能因 Worker 表示「本輪完成」就宣布整個任務完成。**雲端** Code Review 的 CHANGES_REQUIRED 先退修、固定新 HEAD 後再次送雲端審查；E2E 的 FAIL／BLOCKED 保留完整缺陷與可重現步驟，由 Sol 指派 Implementer 修復，再固定新 Commit、由獨立 E2E 重測受影響與必要回歸項目。結果不明的 Save All 不得盲重送。
- **版本綁定與驗收裁決：**每次 Plan／實作／Code Review／E2E 交接至少綁定 `task_id`、`plan_revision/sha`、`implementation_commit_sha`、worktree／實際執行環境、AC 清單及每項狀態、實際操作／測試方法、證據引用／SHA、未解缺陷與 `next_action`。獨立 E2E 應提供自己的 Session／執行者資訊與原始證據；舊 Commit 的 PASS 不能自動轉移至新 Commit，來源變更後須做影響分析與必要重驗。未完成項一律留在報告，不得用縮減 AC 或另造成功報告抹除。
- **用結果衡量，不用代理數量衡量：**每輪在現有 `E2E測試報告.md` 簡記首輪／最終 E2E 通過情形、修復迴圈、人工介入、實際耗時／使用額度（可得時）與驗收後缺陷；優先追蹤真正的 GUI 派送、Save All 次數、逐檔驗證與兩本不同相簿的完整度。不要為了指標再建立大量 Markdown 或反覆執行沒有資訊增益的合成測試。

## LINE 相簿 E2E 的必要證據與順序

- 真正的相簿候選與可點擊區域須來自當下畫面、群組／視窗、日期／照片數及 AX／OCR／影像交叉證據；不重用過期點位。當次 LINE 前景交接必須真實確認，測試期間可連續執行 Owner 已同意的可逆導覽，前景中斷或目標改變時重新確認。正常列表瀏覽可記錄失敗後返回；不得把探索性點擊當作 Save All 身分核對。
- Save All 只可在核准的 duplicate、目的地、owner、持久 intent、menu identity／geometry 及 at-most-once gates 全部通過後派送；結果不確定時不得重送。每次派送、chooser 確認、下載、檔案驗收與 state readback 都須有獨立可追溯證據。
- 單一本成功不等於兩本成功。A 真實 Save All、完整驗證及狀態讀回後，應返回相簿列表、實際向下捲動至少一次並確認畫面變化，找到且核對與 A 不同的 eligible B，再執行 B Save All 及驗證。若 B 已可見，仍保留至少一次真實捲動的證據要求，但不必為湊出形式上的新完整卡片而額外捲動；不能重開歷史 VERIFIED 相簿製造第二本。沒有 eligible B 就回報 `NO_ELIGIBLE_TARGET`，不宣稱完整達標。
- 每次真實捲動都保留操作前／後截圖、AX 與 OCR、方法及派送結果，核對 app／群組／session／PID／window 連續性和可觀察的位移。捲動步距應有界且記錄實際效果；目前正式程式仍固定 0.25 viewport，任何變動需修改對應專案契約，不能只改文字。對 LINE 的部分可見卡片，可用共同列身份、日期／張數、OCR 位置與畫素位移交叉驗證，不把「兩張完整卡片必須同時出現」當成通用物理定律；若證據不明，先取得新的合法真實觀察再最小修正，不猜點、不把結果不明的動作當成可盲重試。
- 完整驗收至少分開呈現：UI／menu 校準、單本交易完成、下一本 scroll 與 grounding、第二本交易完成，以及整體批次／狀態驗收。每項只能由其自身證據判定。

## 報告交接與阻塞處理

`E2E測試報告.md` 是迭代循環中的正式證據交接物，不是僅供摘要的備忘錄。每輪報告完成後，將它交給本輪指定的高階 Planner；若執行環境沒有可用的 Planner 通道，保留報告與進度記錄，明確回報尚未完成 Planner 交接，不得聲稱已提交。Planner 輸出須精確指出本輪事實、未知、阻塞、下一個決策及其驗收方式。

遇到 writer guard、狀態不一致、身份歧義、前景中斷、目的地副作用或未預期結果時，先保全真實證據並停止依賴該失敗前提的動作；Planner 應快速辨別是 macOS／LINE 技術限制，還是本專案自訂 gate 的假陽性。Owner 明確授權的可逆測試若被不合現況的專案規則擋住，應提出最小且可稽核的政策／源碼修正後重驗，不要無限繞回相同模擬測試。不得偽造 consent、修改歷史紀錄、偷換 writer、繞過仍有效的執行閘門或在不明結果後重送不可逆操作。

## LINE_TWO_ALBUM_PILOT/1 — 有界的 Owner project route

Owner 在後續對話已明確將本專案短期目標擴展為真實 LINE 連續兩本 Save All，並授權所需的可逆導覽實測及符合資格的下載測試。該授權是 Owner 的方向／操作意向，不會自動啟用既有 [LINE_TWO_ALBUM_PILOT/1](policies/line-two-album-pilot-v1.json) 私有 grant，亦不表示可重用 `CLOSED_NO_REPLAY` 或抹除 `2/2` 已用額度。Planner 應優先依 Owner 決策提出有界的專案級授權／測試模式修訂，並保留 source、原 ledger、state 與審查綁定，讓真實導覽能執行、正式 Save All 能獨立驗收。保留上層 Harness／平台限制；不聲稱原生 Controller admission、簽署收據或實體 exactly-once 保證。

## 階段結束前強制 Commit 與可回溯訊息

**強制觸發：**每當 Agent 準備結束本次 Session、交接至下一個 Session、完成一份 Plan（即使尚待外部審查）、完成一個 Implementation 修復切片、完成一次有實質新結果的驗證／E2E 階段，或因 `FAIL`／`BLOCKED` 暫停時，Sol 必須在回報或主動結束前執行一次 **Checkpoint Commit 檢查**。這是有意義的階段邊界，不是每個工具呼叫或每次測試都製造 Commit。即使整體兩本 Save All 尚未完成，也要保存當前已產生的可交付成果與未解問題，不能等整個 Issue 結束才留下 Git 歷史。

1. **先保存實際成果：**確認 repo／branch／HEAD 與 `git status`，整理本階段真正變更的 Plan、程式、測試、可公開的驗證報告或交接紀錄。必要時更新現有 `E2E測試報告.md` 或 Plan／PR handoff，寫明 PASS、FAIL、BLOCKED、NOT_RUN，及可重現證據。僅逐檔 stage 本輪受權變更；不夾帶不相關 dirty／untracked 檔、私有照片、憑證、原始授權或未遮蔽證據。Plan 待審也可提交，**Commit 不代表 Plan／Code Review／E2E 已獲核准**。
2. **Git Commit 本體必須有三段完整內容：**不得只在 PR 描述或聊天室寫詳情，不能只留下 `fix issue`、`update files` 一類摘要。使用精準的 `<type>(<scope>): <本階段變更重點>` 作為 Subject；**Commit message body 必須明確包含且填妥「意圖」、「做了什麼」、「下一步的建議」**三個標題。建議同時填入「驗證與結果」，清楚列出實際執行命令、測試／實機狀態、失敗原因、未執行項目與證據參照；不捏造 PASS、不把預期寫成實際執行：

   ```text
   <type>(<scope>): <具體且可辨識的階段成果>

   意圖：
   - <為何要做；對應 Owner 目標、AC 或已觀察根因>

   做了什麼：
   - <確實修改／新增哪些重要檔案或行為；範圍與保留條件>

   驗證與結果：
   - <真實執行的命令／LINE 操作、PASS／FAIL／BLOCKED／NOT_RUN、證據連結或 hash>

   下一步的建議：
   - <下一個可執行動作、待解阻塞、所需外部雲端審查或 Owner 決策>
   ```

3. **每個階段獨立留痕並核對：**有本輪可交付變更就 `git commit`、依既有持續授權 `git push` 並建立／更新同範圍 Draft PR；推送後用 `git show -s --format=%B <commit-sha>` 與 GitHub 遠端讀回確認**真正 Git Commit 的 body**包含三要素，而非只有 PR 留言。向 Owner 回報 Commit SHA／連結、PR、真實測試結果與下一步。不得 `--amend` 或 force-push 改寫既有審查歷史來補訊息。
4. **沒有可提交差異時不得製造虛假歷史：**若本階段只有真實測試或決策產生新資訊，優先更新既有的去識別化報告／handoff 再提交該報告；若確實無任何必要變更，**不建立 empty commit**，明確回報 `NO_CHANGES_TO_COMMIT`、本階段事實與下一步。若 Git／權限／遠端失敗，保留變更與原始錯誤，回報 `COMMIT_OR_PUSH_BLOCKED`，不得聲稱已提交成功。突發斷線無法保證收尾；下一個 Session 啟動時先對帳未提交與未推送成果，再接續任務。

## 修正完成後的自動 GitHub PR 與雲端審查交接

Owner 對本專案各輪已授權範圍內的修正，持續授權以下交付流程；不必每次重新詢問是否 commit、push 或建立 PR。

1. **每輪修正完成即主動交付：**整理本輪差異、完成適用且可執行的驗證，逐檔加入本輪修改，執行 `git add`、`git commit`、`git push`，並在本專案 GitHub 建立 PR；已有涵蓋同一範圍的 PR 時更新該 PR，避免重複建立。保留無關的 dirty／untracked 工作，不得使用整目錄加入而夾帶私人證據或其他修改。即使整體 E2E 尚有阻塞，也應交付可審查的修正，清楚標記失敗、未執行及未完成項目。
2. **Commit 訊息三要素及 PR 不得省略：**依上節「階段結束前強制 Commit」規則，**每一筆由 Agent 建立的階段性 Commit body** 都必須實際寫出「意圖／做了什麼／下一步的建議」，並附適用的真實驗證結果；PR 標題與說明應概述最後提交的實際內容，但**不能取代 Git Commit 本身的訊息**，也不得沿用過期描述。
3. **完整報告須能在 GitHub 閱讀：**將本輪 `E2E測試報告.md` 或適用的完整驗證／交接報告，上傳為 PR 中的受版本控制檔案或完整留言；不能只提供使用者本機路徑或摘要。保留成功、失敗、未執行、真機與合成測試的區別及可追溯證據識別；私人照片、群組／人名、檔案清單、敏感授權資料及本機個人路徑先做必要遮蔽，並清楚標示遮蔽範圍，保留本機原始證據。
4. **把審查入口交給使用者：**完成推送後核對 GitHub 最新 HEAD、PR 與報告內容，向使用者提供 PR 連結、完整報告連結、精確提交版本與尚待審查的事項。**本次 Owner 已指定 ChatGPT 在本對話擔任獨立 Plan Reviewer 與 Post-Implementation Code Reviewer**；Sol 提供精確 Plan／PR、報告、來源及證據連結供 Owner 轉交，不得自行宣稱雲端審查完成。Owner 日後可明確改指定其他雲端模型或供應商，專案不得硬編碼唯一審查供應商。未經 Owner 另行要求，本機 Agent 不代替 Owner 呼叫或冒充外部審查模型。只有真實派送收據或實際審查結果，才能分別聲稱已送審、已完成或通過；貼出 PR 審查請求或通過本地檢查，都不能冒充外部模型已經審查。
5. **交付不等於核准執行：**沒有另行指示時，PR 維持 Draft，不自動 merge。此持續授權只涵蓋上述 Git／PR 交付，不擴張 GUI、Save All、下載或 protected state 的執行範圍，也不取代適用的獨立審查與精確來源綁定。若推送或建立 PR 實際失敗，保留本輪提交、報告與錯誤，回報真實阻塞及下一步，不冒稱已發布。


## 外部審查與 GitHub Handoff 接力 SOP（Owner 核准試行）

完整規則：[`docs/agent-session-handoff/SOP.md`](docs/agent-session-handoff/SOP.md)；範本：[`templates/plan-to-implement.md`](docs/agent-session-handoff/templates/plan-to-implement.md)、[`implement-to-e2e.md`](docs/agent-session-handoff/templates/implement-to-e2e.md)、[`e2e-to-close.md`](docs/agent-session-handoff/templates/e2e-to-close.md)。此節為本專案執行約束；不修改已安裝 Universal Harness 4.8.0 或全域 `~/.codex/AGENTS.md`。

1. **外部管控者／Review Gate：**目前由 Owner 指定本對話 ChatGPT 擔任；負責發階段 Prompt、獨立 Plan Review、Code Review、E2E 證據審查、退回精確修正及通過後發放下一個 Session 的啟動 Prompt。**ChatGPT 不是常駐背景 Agent**，無法自行讀取本機變動或持續監控；必須由 Owner 在此對話提交 PR URL、精確 SHA 或要求檢查，才實際審查。Agent 不可偽造外部裁決、私自放行或填寫機器批准收據。
2. **模型配置可變、角色獨立：**Planner、Implementer、E2E 的具體模型／訂閱／Provider 由 Owner 在每個階段開始前指定；外部 Reviewer 可建議但不可自動替換。預設高階模型只作一次性 Planner／必要疑難審議；Implementation 和 E2E 可用低成本 BYOK，但驗收須獨立新 Session。即使相同模型，僅能稱 Session 獨立，不能冒稱跨模型獨立。
3. **PLAN → ChatGPT Review：**Planner 依 Harness v4.8.0 `01_plan_prompt.md` 凍結 `plan.md`、schema v3 契約（及可用的 controller 產物）、本輪 `handoff.md` 初稿，Commit／Push 並建立或更新一個該階段的 Draft PR。須提供 exact HEAD、Plan/contract SHA、範圍、AC、風險、最小證據和下一階段接手 Prompt。Owner 將 GitHub PR 交 ChatGPT；`CHANGES_REQUIRED` 僅修被退回的具體問題，再推新 SHA 重審。通過後由外部 Reviewer 提供最終「模型可更換」的新 Session Boot Prompt。
4. **Handoff 是不可省略的交接產物：**每個交接都使用對應 Markdown 範本，**首段為可直接貼給接手者的 Boot Prompt**。每份明確記錄原目標、已接受 AC／Plan、精確來源與 SHA、角色／允許動作／禁區、證據／驗證、真正剩餘阻塞、可重現下一步、停止條件、狀態與收據。先固定 GitHub Commit 才給下一個 Session。模板屬規格，不直接當已核准的具體任務 Handoff。Harness 控制器如可真正編譯 `handoff.json`、`handoff.md`，必須保留其與已審機器契約的原始 bytes／receipt；人工導覽 Handoff 不能取代或偽造它。
5. **IMPLEMENT → ChatGPT Code Review：**Implementer 在獨立 Session 只按核准 Plan 及 Handoff 改動，執行 focused tests，產出實際 diff、結果、精確 source／runtime 身份及下一份 `implement-to-e2e` Handoff，Commit／Push／發佈對應 Draft PR。Owner 將 PR 與 SHA 轉給 ChatGPT；退回只修必要問題。通過後仍須核對已安裝 runtime、有效交易 grant 和當次 Mac 前景，才能進入真實 E2E。
6. **E2E → ChatGPT 結案／修復判定：**由 Owner 指定另一個全新 Session、固定 reviewed Commit、獨立驗收真實結果及證據；產出 `e2e-to-close` Handoff、證據 Manifest、PASS／FAIL／BLOCKED／NOT_RUN，Commit／Push／提交階段 PR 或更新同範圍報告 PR。ChatGPT 審核後才建議結案、精確返工或重大重新規劃。E2E 不得一邊測試一邊改產品、不得在 Save All 不明時重送。
7. **PR／合併與成本紀律：**階段有新可交付差異才開／更新 Draft PR，避免空 PR 或為同一變更重複開 PR；應依 Git 依賴使用明確的 base/head，避免將未核准產品分支誤合併主線。未經 Owner 決定不自動 Merge。每次 Git Commit body 保留「意圖／做了什麼／驗證與結果／下一步的建議」，保護 dirty／private 工作。每個 root issue 遵守 Harness 3 次有資訊嘗試／連續 2 次無新資訊停止；不得因新 Session 重置嘗試或歷史交易計數。無關的大型 log／整段聊天 export 不放進新 Session。
8. **風險／批准契約：**Harness 4.8.0 QUICK／STANDARD／CRITICAL 風險路線及要求仍有效。正式 LINE 原圖下載與 canonical ledger 是 CRITICAL。外部 Review 留言不能憑空成為 Harness controller receipt 或 `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED` 所需的精確機器批准；Review、Deployment、Runtime grant、Owner 操作授權和 E2E 是不同關卡。既有 HUMAN_ASSISTED／AUTO 模式不得混用證據，239 張歷史 VERIFIED、65 張人工排除相簿及未知派送不重送的保護不得變更。
