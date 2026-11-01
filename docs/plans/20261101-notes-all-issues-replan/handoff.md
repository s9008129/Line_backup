# 全問題重規劃交接

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
