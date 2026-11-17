# 記事本 intent 後工具列消失：最小修復計畫

## 目標與授權

讓不同 Agent 使用同一日常記事本 Prompt／Skill，以當次畫面自主完成可安全執行的下載。修復控制可見性與交易順序的規則矛盾，不建立 GUI controller，不以固定座標或舊畫面代替判斷。

Owner 本輪明示由 Leader 與既有 Tester 釐清、交既有 Reviewer 審查計畫、修正至通過，再派既有 Worker1／Worker2 平行實作。此指定涵蓋本輪跨 pane 協調；不把 helper 自評當獨立審查。完成後由明示請求 `gpt-6-luna` 的原生 subagent 梳理上下文並撰寫提交訊息，Leader 執行逐檔 add／commit／push。沒有真實 GUI 輸入、下載、restart、帳本或照片變更授權。

基準：`feature/line-notes-media`，`cbcbb81fb41a17e300eb91975b62466c83311b20`。既有 `問題提報單.md` dirty 與 `.playwright-mcp/` untracked 保留且不提交。私有證據在 `.local/line-backup/tasks/20261117-notes-hover-intent-repair/`。退役的 `policies/v4.9.0/` 當次不存在，不重建舊框架。

## 已知、推論與未知

- 提報單：本次成功媒體 0、completion 0；舊 attempt 為 `UNKNOWN`。零點擊紀錄、空 staging、事故後錄影不證明 `NOT_SENT`。
- B1 要求正面控制證據才建 intent；intent 後全面禁止 reveal。當控制消失時，這兩項規則沒有合法重新顯示控制的路徑。
- 獨立錄影支持工具列可見性與游標位置相關；不能證明原事故由 timeout、pointer leave、capture 或焦點哪一個因素造成。
- 當次 CUA 文件只有 `click` 等，沒有 hover／move。不能把不存在 API 的方案當成目前可執行修復，也不以 shell／其他事件注入繞過工具。
- `persistRevealWithDirectAfter` 已支持單次安全 click 後直接 after；`persistGroundedDownloadClick` 已限制下載控制定位與一次 click。沒有證據需要改 notes CLI／event schema。
- 真實 toolbar 存續、下載、chooser 與跨 Session 執行仍須日後用正式日常 Prompt 驗證，本輪 `NOT_RUN`。

Tester 核對：現有 API 下，延後 selected-filmstrip 安全邊緣 click 是最小可實作的功能候選；它會改變 Skill 的 intent 後操作契約，並未證明可靠叫回 toolbar。單獨移動 intent 邊界不充分。Owner 已明示本輪制定、審查並實作修復計畫；本計畫把該必要操作契約變更明列審查，未增加日常授權、派送次數或舊 UNKNOWN 例外。

## 有界設計（Tester 已釐清；待 Reviewer 接受）

保留 intent 前的正面控制 gate。對**本輪新建立且連續可稽核、尚未呼叫下載控制也尚無 outcome 的同一 attempt**，將既有第二次 reveal 候選允許延後到 intent 讀回後使用；不是另加第三次候選，也不是恢復舊 UNKNOWN 的例外。

1. intent 前仍須完成歷史、全列表卡片覆蓋、目標細盤、三層身分、viewer／返回、可見控制、工具能力與映射。若已知需要延後候選，先保存其方法安全區、before 原件、同 scope 第一候選完整 receipt、剩餘額度及預備 request。不先建 staging。
2. 若 intent 讀回後控制仍可定位，直接使用既有 grounded download helper，沒有額外 reveal。
3. 只有控制曾可見、intent 後當次充分觀察證明同一 viewer 的控制消失，且 Agent 能以完整連續 input 紀錄正面核對下載控制從未被呼叫、沒有 outcome／chooser／活動下載／未解輸入／其他未解 attempt、同 Session 與前景不中斷時，才可使用保留的第二候選。**不能由 `click_count=0`、空 staging、缺檔或缺紀錄單獨成立。**控制由可見轉隱藏是本修復處理的具體新 gate 證據，沒有這個變化不授予候選。
4. 第二候選仍限當次文件支持的無點擊 hover，或既有「已選 filmstrip 縮圖非播放安全邊緣」click。兩方法各有自身安全區證據；沒有 hover API 不猜，沒有已選 filmstrip 安全區就停。不得點下載圖示來顯示它、主內容、播放、時間軸、其他縮圖、返回或 reopen。新鮮映射與身分須在輸入前核對，舊座標不重播。
5. 沿用一次 `persistSingleInput`→直接 after composition，保存 request／raw／after／時序及同 scope `candidate_ordinal=2`、prior refs、budget 1→2、attempt 與 intent ref。目錄、ID、statement 先備妥。輸入前先持久保存並讀回該 attempt 已保留／消耗第二候選，未解／crash 也耗額，不得換 Session／ID／路徑重置。持久 request 是保護標記，不是 CLI 新事件或未派送證明。
6. Agent 讀同次 after 判斷可見／歸屬／啟用／映射，通過才以該份最新原件走原 grounded helper 的最多一次下載控制。此輸入只是已核對目標的控制重新顯示，不是下載、完成或自動點擊決策；helper 不作視覺辨識。若控制再消失、證據保存不全、input error／timeout／未知或任何身分／播放／前景漂移就停。無第三候選、無下載重試，不宣稱 atomic、0–1 秒或成功保證。
7. 失敗後保留同 intent，依真實證據記第一筆 outcome；不足為 `UNKNOWN`，已有 `UNKNOWN` 僅 reconcile。不自動 `NOT_SENT`、新 attempt、restart 或下一項。舊事故已有 `UNKNOWN`，完全不適用這條尚無 outcome 的連續前派送例外。

保留每 list/post/media 最多兩候選、一般根因三次與連續兩次無新資訊停止。同一 scope 已用兩次、額度不明、舊無 outcome crash window、新 Session 或任何未解輸入都停；本次修復不授予補拍／補按或恢復舊事故。

這是 Skill 層的操作例外與證據契約；CLI 不能驗證 GUI 真實或替 Agent 授權。若此設計需新增持久狀態系統或修改 CLI 交易語意，停止並交回 Leader 縮小方案，不讓 Worker 自行擴張。

## 分工與寫入白名單

| 執行者 | 檔案 | 任務 |
|---|---|---|
| Worker1 | notes `SKILL.md`、`references/gui-inventory.md`、`references/evidence-decision-cases.md`、`references/verification-and-recovery.md` | B1 唯一決策本文與入口／矩陣同步；舊 UNKNOWN、新 attempt 成功候選、已用完額度、工具不足、capture failure 等案例。其他檔只引用 B1，不重複完整規則。 |
| Worker2 | `references/evidence-template.md`、`references/download-and-ledger.md`、`tests/test_notes_input_helper.py` | 既有 composition 的延後候選用法、持久預留讀回、原件與額度欄位、同一 after 到 grounded helper 的交接；必要最短可執行 composition／測試，不增 controller／event。 |
| Leader | 本計畫、公開 report、私有 progress／原始協作與檢查 log | 整合、回歸、保護檔案比對、精確提交。 |
| Tester | 唯讀釐清，完成後離線情境核對 | 不修產品、不 GUI、不改真實帳本；獨立指出未知。 |
| Reviewer | 指定計畫審查 | 回覆 ACCEPT／REVISE 與可操作 finding；範圍只限計畫，不替實機簽通過。 |

Reviewer 接受精確 plan 版本與 hash 後才同步派 Worker1/2。Workers 共享目錄，嚴守互斥白名單；不 commit／push、不增加子代理、不改帳本／照片。發現超界先回報。按 Owner 明示修正 reviewer 問題至通過；不得為通過移除保護條件或無限重試相同方案。

## 驗證與交付判準

針對實際風險測試：持久 request 讀回失敗零 input；同 attempt 第二候選不可重入；一次 reveal→一次 after，after 原 bytes 保留；after 失敗不觸發 download；成功後仍由 Agent 提供最新 grounded request，下載最多一次；舊 UNKNOWN／crash／已有一次 download 不進新例外。測試只支持合成呼叫與保護邊界，視覺及授權 gate 是 Agent 職責，不能把 mock boolean 說成真實核准。

最小回歸：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

另跑 Skill validator、diff／連結／白名單檢查。所有測試使用隔離合成 fixture，保護 active locator；真實帳本、locator、提報單的檔案清單與 SHA-256 在回歸前後比對。失敗保留已證明結果，不能換入口或修改真實歷史繞過。

正式日常入口、CLI、event／六類狀態、下載驗證、restart 規則、相簿及 master 不變。實機日常備份、hover-only UI、新例外真實成功、混合附件 chooser、跨 Session 恢復與核心可重複使用性皆 `NOT_RUN`。不以計畫 ACCEPT、離線 PASS、commit 或 push 代替。

六狀態分開記：`PRIMARY_OUTCOME_STATUS`、`IMPLEMENTATION_STATUS`、`CORE_ACCEPTANCE_STATUS`、`REQUIRED_VERIFICATION_STATUS`、`INDEPENDENT_ACCEPTANCE_STATUS`、`TASK_CLOSURE_STATUS`。實作及離線檢查完成可以報 PASS；整體實機核心驗收缺證時不稱 DONE。

提交前由指定 `gpt-6-luna` 原生 subagent 讀計畫／diff／檢查 log／已知限制，寫繁中詳細訊息，包含「意圖」、「做了什麼」、「下一步的建議」、「驗證與結果」。不提高 reasoning effort，不聲稱 provider identity。Leader 逐檔 stage（排除提報單、私有證據、照片），commit 後 `git show -s --format=%B` 核對，再 push feature branch 並核對遠端完整 HEAD，不 merge、不 force-push。
