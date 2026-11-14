# 給下一位 Implementer 的啟動 Prompt

你是本任務的 Implementer。Owner 已指示將通過審查的 Issue #50 證據流程計畫交給你實作；本 Prompt 由 Owner 在新主 Session 提交時啟動此角色，目前整理交接的 Session 不執行實作。

先核對 repo `/Users/hsiaojohnny/dev/Line_backup`、worktree、分支 `feature/line-notes-media`、HEAD 與 dirty/untracked，保留無關工作。讀 AGENTS.md、你的 Implementer 角色提示、適用 4.9 政策，以及本目錄 plan.md、plan-review.md、simplicity-plan-review.md 和下列來源。計畫基準為提交 `abd363c3c6154314ed7af252f707522e4ad70517`，兩項審查交付為 `005f08986f3b52f6e03d5711a9d39ee12c5c9976`；本交接版以包含本文件的提交識別（用 git log -1 -- handoff.md 讀回），不可要求未來提交自含其 hash。plan.md SHA-256 必須為 `4569ed0e9bd80f16665d9a71c61d87981203c19c40b084ad62758743dacc9634`。兩份審查均 PASS，但出自同一位獨立於計畫作者的主審，不是兩位不同審查者或產品 acceptance。候選或必要來源不符就停止依賴該前提的工作並回報，不自行套用舊 PASS。

任務是完成 plan.md 第 4 節的單一完整文件切片：沿用 CLI，補記事本證據矩陣、操作順序、範本及判定案例。只可修改 `.agents/skills/line-notes-agent-cua/SKILL.md`、其 references，以及本計畫目錄內案例與角色交付文件；不要改被審 plan.md 或覆寫兩份審查。操作順序唯一維護於 download-and-ledger，GUI reference 管定位／觀察，verification reference 管結果／驗證，主 Skill 摘要連結。不要新增 controller、observer、schema、parser、狀態、attempt 查詢或測試框架；不改 notes.py、事件、CLI、列表 blocker、相簿程式／decoder 或現有測試。

實作須完整覆蓋：intent 前資格／來源／控制預檢，intent 持久保存與讀回後再次定位；下載與 chooser 各自最多一次並分記真實回傳；popup 未被截圖涵蓋不等於不存在；證據範本含三層 key、attempt、原目的地、觀察來源／範圍／尺寸、可取得時間與時鐘、座標映射、控制可見性、input 回傳、chooser／檔案歸屬，缺值寫 UNKNOWN，引用 hash 由工具計算核對且輸出唯一檔名。無 outcome 先記第一筆真實結果，已有 UNKNOWN 才 reconcile；缺 marker、空目錄、timeout、API 成敗、播放結束均不足以判未送出或完成。保持晚到結果保護，未收斂不 verify、不新 attempt、不派下一項；不重點下載查證。

案例至少包含控制檢查後隱藏、API error 但 chooser 出現、chooser 延遲／出處不明、晚到結果、播放結束、無 outcome crash window、UNKNOWN 未收斂，以及充分／不足的完成和停止證據。每例列前提、觀察、可支持命題、允許動作、禁止推論、缺少證據；說明可接受的正面證據組合，不把照片單一 toast 變成所有影片的必要條件。假設案例不可冒稱已取得真實停止 receipt；不足仍保留 UNKNOWN。不要用未提供的平台能力補齊欄位。

這是文件實作授權，不是 LINE GUI／真實帳本授權。不得讀寫真實 ledger 或照片區、解除舊 UNKNOWN、下載、導覽 LINE、跨列表、搬移資料、改寫完成事實或關閉 Issue。舊 UNKNOWN 無可歸屬新證據就保留；本次成功不以原列表解鎖或整個 Issue 修復為前提。原分析與指定影像只按需唯讀，私有證據留在專案 .local 任務區，不提交／外傳。

完成文件一致性、連結與案例逐項對照，保存實際命令、退出碼及輸出，執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

成功條件是計畫第 4 節各要求均能追到最終文件與案例、引用可解析、上述檢查 exit 0、沒有禁改路徑差異。測試只使用隔離 fixture；不新增字串比對測試。任一檢查失敗、需要改公共介面／資料語意／授權邊界、缺必要能力、工具拒絕或寫入衝突時，保留證據與已證成果並停止交人決策，不跨角色修復或自行豁免。notes exit 70 不可當可重試業務拒絕。同根因最多三次有證據嘗試，連續兩次無新資訊就停，不重置既往次數。

交付 implementation-report.md：列需求到差異／案例的映射、精確候選、實際檢查及六狀態，白話 progress 放專案私有任務區。GUI、混合附件、跨 Session、產品獨立 acceptance 未執行維持 NOT_RUN；原 Issue 仍 BLOCKED。依持續授權逐檔 stage、commit／push（提交本體含意圖、做了什麼、驗證與結果、下一步的建議並讀回），核對遠端精確 HEAD；不得 merge master、force-push 或改寫審查歷史。首個切片就是最終文件候選，交回 Owner 啟動 implementation Simplicity Review；你不自派下一正式角色、不把自評當獨立通過。沒有剩餘實作就不重開 Implementer。

## 本次交接更新與來源

Owner 本輪明示將上述計畫交給下一位 Implementer，並授權本交接 add／commit／push。這是既定計畫的交接更新，不變更 plan.md 的範圍與成功標準。前次兩份 PASS 報告保留原版本綁定；本次交接本身未取得新的獨立審查。起始 HEAD 為 `005f08986f3b52f6e03d5711a9d39ee12c5c9976`，工作樹乾淨。原分析、影片及指定截圖位置見下方歷史來源清單；不必為文件實作重做實機研究。當次審查證據位於 `.local/line-backup/tasks/20261101-issue50-plan-reviews/`。

```text
PRIMARY_OUTCOME_STATUS=IMPLEMENTER_HANDOFF_READY
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=BLOCKED
REQUIRED_VERIFICATION_STATUS=BLOCKED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=BLOCKED
```

本輪只檢查交接文件與 Git，產品回歸／GUI NOT_RUN；交付命令、退出碼及最終 HEAD 留在私有交接任務紀錄與本輪回覆。以下 v1 是原始 Planner 交付歷史，保留來源與當時狀態；其「下一步計畫審查」已完成，目前路由以上方 Implementer Prompt 為準，不重啟已完成審查。

---

# Issue #50 計畫審查交接 v1

## 任務與精確版本

- 本次角色 Planner；正式交付是同目錄 plan.md v1 與本文件。兩者由同一 Agent commit 識別，審查者先用 git log／git show／status 核對實際提交；不要把產品基線當成文件提交。
- 產品基線：feature/line-notes-media，`b3cf231b8159622c5532520cc8b178182c9d37b9`；起始工作樹與暫存區乾淨。
- Owner 選擇：先建立可靠證據流程，舊 UNKNOWN 無新證據保留；沿用既有 CLI，僅補記事本 Skill／references、證據範本及判定案例。
- 本次實際新增只有規劃與交接文件；不修改產品、Skill 或測試，不操作 LINE 或真實帳本。Owner 已明示本次文件 commit／push；不包含 merge、force-push 或其他正式角色派送。

## 給另一位 Agent 的審查任務

請由 Owner 在獨立主 Session 啟動計畫 Simplicity Review，先讀 AGENTS.md、適用 4.9 政策、本文件與 plan.md。保持唯讀產品邊界，不實作、不修復、不重測真實 GUI、不操作帳本，不替本計畫預填 acceptance。

重點核對：

1. 目標是否以證據流程改善為限，沒有承諾解開既有 UNKNOWN 或關閉整個 Issue。
2. 是否沿用既有 reconcile 出口，保持同一列表帳本的序列化與晚到結果保護。
3. 矩陣是否清楚區分定位、input receipt、App acknowledgement、下載結果、檔案完整與 completion；timeout、空目錄與缺 marker 均不推 NOT_SENT。
4. 文件切片能否在不增 controller、schema 或公共介面的前提下完成；若提出阻擋項，請指出具體必要條件與證據，不以風格或抽象完整性擴張需求。
5. 離線規則檢查與真實能力驗證是否分開；未知能力、原始觸發因素及未測範圍是否誠實保留。

若範圍、候選或風險有實質變更，交 Owner 決定下一步與須重做的檢查。拒絕或有未解 blocker 時保存證據並停止，不自動啟動 Implementer。

## 必須傳遞的證據

- 同目錄 plan.md、本 handoff.md 與包含兩者的精確 commit。
- 私有原分析：`.local/line-backup/tasks/20261101-issue50-high-reasoning-review/issue-analysis.md`；該目錄另有原證據 manifest 與六項引用 hash 核對結果。本輪未把這些舊結果冒充重新全帳稽核。
- Issue：<https://github.com/s9008129/Line_backup/issues/50>，含補充留言 6555471050；Issue 的舊說法應與本輪較精確的證據界限一併看待。
- Owner 原影片：SHA-256 `54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6`。私有來源位置不公開，審查若需原件由 Owner 在本機提供；示範片並非失敗當次。
- 來源 PTS 影格：`.local/line-backup/tasks/20261101-issue50-replan/video-cache/` 的 `*source-pts.jpg`。`overview.jpg` 是初始重採樣預覽，不用其標籤當原始精確時間。
- 原截圖與保存輸出位於 `.local/line-backup/notes-20261101-1121/`；以 plan 的指定項核對，不廣搜私人資料、不載入真實帳本。檔名宣稱不替代圖像內容，成功第 2 項與失敗第 3 項的保存控制圖都未呈現工具列。
- 當次規劃落檔檢查與進度放在私有 `.local/line-backup/tasks/20261101-issue50-replan/`，不提交私人畫面或原始資料。

## 已知、未知與審查後路由

已知：既有狀態機有合法出口，證據不足才無法選終態；示範片可看到工具列顯示變化、影片載入、chooser 與照片完成提示。UNKNOWN 的 blocker 為同一列表帳本。

未知：原始 click 為何未產生可判結果；平台是否提供足以證明 NOT_SENT／STOPPED 的 receipt；真正混合附件與跨 Session 實機能力。示範片與新流程不回填舊 attempt。

其他 Issue 問題繼續保留：媒體種類矛盾、來源到期、EAGAIN、引用 hash／輸出覆寫及詳細盤點缺項。審查此計畫不代表這些已解。

下一個人工步驟：Owner 啟動計畫 Simplicity Reviewer。通過後由 Owner 決定啟動 Implementer；首個完整文件候選後再由人啟動 implementation Simplicity Review。若已無剩餘實作，不重開 Implementer 或重複同一審查。真實能力診斷或備份需另有適用任務與有效前景。

## 六狀態

```text
PRIMARY_OUTCOME_STATUS=PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=BLOCKED
REQUIRED_VERIFICATION_STATUS=BLOCKED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=BLOCKED
```

未執行為 NOT_RUN；影格觀察為 OBSERVED；文件與 Git 檢查不構成產品 PASS。不得以本交接作為 GUI、解除 UNKNOWN 或後續角色的自動授權。
