# 現行交接：直接啟動 S1 Implementer

**Owner 已明示免除實作前的計畫 Simplicity Review 與獨立 Plan Review，採本版 replan 作為實作依據，直接交 Implementer。** 本節是目前有效路由，取代下方原 Planner 交接及 replan 第1、7、8節中 P0 的前置要求；技術契約、驗證與資料保護不變。下方原文保留為796198a版本歷史，不是目前下一步。

Owner 原指示：「本次無需進行Simplicity Review 與獨立 Plan Review。直接梳理上下文後精準的交接給implemnter」。據此記錄：

```text
PLAN_SIMPLICITY_REVIEW_STATUS: WAIVED_BY_OWNER
INDEPENDENT_PLAN_REVIEW_STATUS: WAIVED_BY_OWNER
IMPLEMENTER_ENTRY: S1_AUTHORIZED
```

這是Owner流程決定，不是獨立審查PASS；沒有新的計畫審查報告，**不要求、等待或補造這兩份已免除的報告才開始S1**。S1後implementation Simplicity Review、最終獨立相容／Acceptance及G0／D1／D2／G1／G2的資料與實機門檻仍依原計畫保留。本輪只整理交接，不執行實作、不派送另一正式角色。

## 可直接交給下一主 Session 的 Implementer 指令

你是本任務的 **Implementer**。Owner將本文件交給你時，直接執行下述S1，不必再詢問計畫審查許可。先讀AGENTS、你的`04_implement_prompt.md`、適用4.9政策、[完整replan.md](replan.md)及本節；不要只依摘要實作。Owner本次免除決定優先於文件的P0預設，不擴張其他授權。

### 精確基線與第一個動作

- Repo／worktree：`Line_backup`核心目錄；分支`feature/line-notes-media`。
- 技術計畫提交：`796198a51dfa6814e0acf1fe1765656e03bbed54`。replan SHA-256為`da2af8f3fbcd54e5492f06a042e3c2b3d03d6c4b3c5c42b6b3942acf787b2113`；本次未更改replan bytes。
- 本輪交接起始HEAD及遠端均為796198a，工作樹／index乾淨。接手時應使用**包含本更新的交接提交**，不是上一筆796198a；以`git log -1 --format=%H -- docs/plans/20261101-notes-all-issues-replan/handoff.md`讀回，與Owner攜帶的精確commit核對，勿要求文件自含未來提交SHA。
- 第一個動作：核對pwd、Git status／branch／HEAD／worktree、交接提交及replan hash。796198a到交接提交應只改handoff.md、plan.md；src／tests／Skill／AGENTS無差異。保留無關dirty／untracked、不清理其他worktree、不reset以假裝符合基線；版本或產品差異不符就停止依賴該前提並回報。
- `notes.py`基準SHA-256：`9cdb1f75d19ae61939b98fbea3c0fbe95367e8caef6f69b1c3724946804c36f9`。`media_verify.py`為`7c8051d1699449434dbaa41682a5a50f949858d593ee39cd2a1f38a1e1c6dd99`，本切片禁止修改它。

### 只執行 S1：A1、A3、E

全目標仍是replan的R1–R10，本次先完成第7節S1。S1是離線程式切片，不依賴原UNKNOWN解鎖或G0，不能因既有備份blocker改為等待已免除的計畫審查。

1. **A1 evidence bundle與舊讀相容。** 按replan固定schema／context／子ref欄位實作`line-notes-evidence/v2`與evidence-pack，保持外層exact `{path,bytes,sha256}`。原件hash由工具計算，init已知無效在資料副作用前拒絕，鎖內再核對漂移；先保存子blob、再原bytes父manifest，失敗不追加有效事實event。source_path只作匯入來源，重開讀目前帳本evidence／digest，不跟隨原件路徑。新寫要求v2，舊opaque可讀但不升格已驗證。statement／畫面／AX非空，stdout／stderr可零bytes；單層leaf，不加自由文字hash parser或遞迴框架。
2. **A3 notes專用capture。** 固定interpreter／專案notes模組與argv陣列，只啟動child一次；無shell、任意executable、GUI或自動retry。安全新UUID receipt目錄，request先保存讀回；全量stdout／stderr、child exit／signal、時間／時鐘與程式hash，拒覆寫、fsync／讀回後最後發布complete。capture保存失敗即wrapper=70，即使child=0也不得回成功；保留已知child_exit，INCOMPLETE不得重執行child補輸出。
3. **E 精確LOCK_BUSY。** 僅flock尚未取得時分類EAGAIN／EWOULDBLOCK，保留collection／records scope、exit4及dispatch_authorized=false。只有已實作的純唯讀allowlist可於此精確情況標retry_safe=true；resume／mutation、非flock I/O及exit70不得重送。不為S2的evidence-audit預先加入假成功入口。

S1不實作A2 audit／page correction、B2種類更正／intent-v2、C到期事件、D coverage／scan改動或S3操作文件；它們列為S2／S3未完成，不能宣稱全問題已修復。

### 可寫範圍與禁止事項

可改`src/line_backup_batch/notes.py`的S1必要部分；最多新增`notes_evidence.py`、`notes_capture.py`；`tests/test_notes*.py`、必要的新evidence／capture測試及合成`tests/fixtures/notes_v1/`；本目錄新增`implementation.md`。私有進度與輸出放`.local/line-backup/tasks/20261101-notes-s1-implementation/`。不為湊模組拆檔，不更改replan／handoff／plan以迎合實作。

禁止改daily.py、image_decode.swift、media_verify.py、相簿Skill／測試、離線OCR、AGENTS、全域政策、舊任務。本切片不改Skill／手冊，相關日常切換文件在S2／S3處理；S1不應用到真實備份。

不讀寫真實notes-backup-records、backup-records、backup、active task，不執行真實列表的lists／summary／resume，不操作LINE或建立下載attempt。測試CLI只指向專案隔離合成目錄；先核對collection、photo root、active hint隔離，避免capture child使用真實預設帳本。UNKNOWN、完成事實與到期項原樣保留，不換列表／入口／目的地繞過。

### 必做檢查與證據

本機檢查由Implementer執行，保存實際argv、cwd／環境、版本、stdout／stderr、exit與hash；後續獨立驗證由Owner另啟動，不能由你或helper簽發。

| 檢查 | S1通過證據 |
|---|---|
| T1的A1部分 | 真正pre-S1合成v1 frozen帳本投影不變；v2重開、原source_path移走仍可讀；legacy不升格。父／子缺件、錯hash、symlink、逸出、duplicate JSON key、版本／context錯均拒絕；init已知錯誤前置拒絕；漂移不追加有效event，明列未引用中斷blob保留並回報 |
| T2 capture | 同命令兩次新receipt；refusal→success兩份都保留；0／2／4／70／signal如實保存。child=0但保存失敗時wrapper=70且child只跑一次；receipt碰撞／symlink啟動前拒絕、child次數0；中斷不得自動重執行 |
| T6 lock／exit | 真子程序分別持collection／records flock，純唯讀命令得到精確LOCK_BUSY，釋放後可成功；非flock EAGAIN、mutation／resume不標安全重試；70仍為INTERNAL_ERROR／UNEXPECTED_EXCEPTION；原UNKNOWN禁止intent的斷言保留 |

T1的audit／page correction部分屬S2，列NOT_RUN，不為完成整張T1提前實作。更新新寫入fixture符合v2時，另外保留真正pre-S1 v1 frozen fixture及原安全斷言；不得用新writer重造v1後冒稱舊格式相容。必要針對性案例納入notes discovery。最後執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

不預填82／73或沿用舊候選PASS。檢查通過且無相關變更／失效證據就不重複全套。GUI、chooser／popup、混合附件、影片真實下載、跨Session、D1／D2仍NOT_RUN。可在核准範圍內做相稱機械修正，不能降標或改契約；同根因最多三次有證據嘗試、連續兩次無新資訊停止，不重置原歷史。

### 交付與切片停止點

提交`implementation.md`：Owner決定與計畫／交接精確commit／hash、起始及最終候選、逐檔差異、S1需求到程式／測試映射、實際命令／exit／私有證據、相容性、未完成S2／S3／實機項及六狀態。IMPLEMENTATION_STATUS僅描述本切片已證範圍，不代表整體DONE。

沿用Owner同範圍commit／push授權；逐檔stage受權程式、測試及去識別化報告，不夾帶照片、人物／列表資料、原始檔名、憑證或原始證據。commit實際body須含意圖、做了什麼、下一步的建議、驗證與結果，以`git show -s --format=%B`讀回；非強制push後核對遠端精確HEAD。不merge master、不force-push、不改審查歷史或關閉Issue；失敗如實記COMMIT_OR_PUSH_BLOCKED。

**S1交付後停止**，由Owner按原計畫另啟動implementation Simplicity Review。不自行進S2／S3、派Reviewer、操作真實帳本或實機重測，不提供獨立acceptance。版本／hash／權限不符、需改白名單或高影響契約、工具拒絕、不同根因或嘗試超限時，保留證據交Owner，不自行改計畫。

必讀來源：完整replan、[最新根因分析](../20261101-notes-result-closure-review/issue-analysis.md)、[原獨立驗收](../20261101-notes-media-acceptance/acceptance.md)、[舊文件計畫](../20261101-issue50-evidence-flow/plan.md)與其實作／審查、記事本Skill／references及現有notes測試。舊PASS僅屬舊文件候選。S1無需重做實機研究或讀真實ledger；指定私有證據只在必要時按檔唯讀，不廣搜私人影像。原input trace、UNKNOWN結果及當前真實資料變動仍未知，新程式不能補造。

## 本次交接狀態

本次只核對Git、文件／源碼bytes、SHA-256、連結及允許差異。Git身分／遠端核對、來源manifest計算、相對連結／replan原bytes與hash／僅兩文件差異檢查、`git diff --check`皆exit0；src／tests／Skill／AGENTS無差異。原件manifest、命令／exit、進度與Git交付紀錄在`.local/line-backup/tasks/20261101-notes-implementer-handoff/`。無helper、無產品修改、無產品回歸或真實資料操作；本輪產品檢查均NOT_RUN。文件檢查／Git成功不等於產品驗收。

```text
PRIMARY_OUTCOME_STATUS: IMPLEMENTER_HANDOFF_READY
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

原產品與獨立驗收BLOCKED保留；Owner已採用計畫並免除P0，S1離線實作可直接開始。

---

# 原 Planner 交接（796198a 歷史，現行路由以上方為準）

本輪角色為 Owner 明示指定的 Planner。目標是補齊 Issue #50 所有未解問題的修復計畫；唯一需求本文是 [replan.md](replan.md)，[plan.md](plan.md)僅為入口。此交接不是Implementer啟動Prompt，也不執行建議或啟動其他正式角色。

## 精確版本與已完成工作

- Repository：`Line_backup`；核心worktree／分支 `feature/line-notes-media`。
- 起始產品／文件HEAD：`d777c0148a17edc707826ff29f740dbad05f9fa7`；起始工作樹及index乾淨，遠端精確HEAD相符。
- 規劃版本：本目錄三檔共同提交的精確commit；以 `git log -1 -- docs/plans/20261101-notes-all-issues-replan/replan.md` 讀回，勿把起始HEAD當計畫提交。使用 `git show <計畫提交>:<path>` 核對內容並重新算SHA-256；文件不自含未來commit。
- 本版replan.md SHA-256：`da2af8f3fbcd54e5492f06a042e3c2b3d03d6c4b3c5c42b6b3942acf787b2113`。候選或hash不符時停止依賴此交接，不把舊審查套到新版本。
- 本輪只新增規劃、入口、交接；原診斷、舊計畫／審查／驗收、產品、Skill、測試及真實資料均保留。
- 已將R1–R10逐項對應到設計、切片、責任人、成功證據、外部gate與停止條件。新增scan綁定風險只標為源碼推導，不冒充真實重現。
- 命令與source-manifest、Issue快照、helper研究摘要及Git交付留 `.local/line-backup/tasks/20261101-notes-all-issues-replan/`；不含任何新的真實備份操作。

## 下一個人工步驟

由Owner在獨立主Session啟動計畫Simplicity Reviewer，攜帶精確規劃提交、本文及replan列出的來源。CRITICAL另需獨立Plan Review；兩個關卡由Owner分別啟動，不能由本Planner或helpers自評替代。

審查須精確核對：

1. 新reader讀舊資料、新寫入要求v2 bundle及舊reader不能讀新事件的實際相容邊界；不能把新格式擴成GUI語意驗證器。
2. 一層資產強制hash核對與notes專用單次capture是否足以補位元引用／拒覆寫；不可刪必要可靠性保障來求簡化。
3. 種類更正保留key、僅限從未有attempt者，新intent/v2凍結effective_kind；到期另記來源不可用、維持欠件、不自動exclude。
4. 先處理舊attempt再重掃、完整細盤後才派送，以及legacy跨scan未決不能靜默改綁定。
5. G0控制可觀察能力不等於D1原UNKNOWN結果，兩者不能互相豁免；資料預覽批准與真實下載授權均未被此草案授予。
6. S1的獨立可驗證邊界、後續所有問題覆蓋及實機驗收；無法取得舊結果／到期檔案時整體仍BLOCKED，不能降標稱全部修好。

通過後由Owner決定另啟動S1 Implementer。首個切片完成即交人工啟動implementation Simplicity Review；後續S2／S3、獨立相容驗證及D1／D2／G1／G2按replan依賴執行，不由箭頭自動派送。任何拒絕、版本不符或新高影響問題，保留證據並交Owner決定，不自行修復／重測／結案。

## 必須傳遞的來源與限制

- [最新根因分析](../20261101-notes-result-closure-review/issue-analysis.md)、[原獨立驗收](../20261101-notes-media-acceptance/acceptance.md)、[舊文件計畫](../20261101-issue50-evidence-flow/plan.md)及其審查／實作報告、[原功能計畫](../20261031-notes-media/plan.md)。舊PASS只對原版適用。
- [Issue #50](https://github.com/s9008129/Line_backup/issues/50)及兩則留言；本輪仍OPEN。
- 基線 `notes.py`／`media_verify.py`及notes測試／Skill。replan第2節有重要來源hash，完整manifest在私有任務區。
- 指定錄影及前輪私有PTS／原始來源只按需本機唯讀；SHA-256見replan。沒有原失敗的完整input trace，不得以示範回填原點擊。
- 真實帳本、19項是否仍未派送、原件是否完整、原UNKNOWN是否已有晚到證據、chooser實際觀察能力皆須在另獲適用授權時重新核對，不能只依舊報告直接應用更正。

## 六狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

本輪Git commit／push明示授權持續有效；不得merge master、force-push、修改Issue或夾帶私人原件。提交訊息本體需含意圖、做了什麼、下一步的建議、驗證與結果，讀回核對；推送後核對遠端精確HEAD並交Owner。Git交付成功不改以上產品／驗收狀態。
