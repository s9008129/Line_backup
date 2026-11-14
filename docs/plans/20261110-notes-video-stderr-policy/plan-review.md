# 獨立計畫審查：PASS

## 結論與審查身分

結論為 `PASS`：草案對方案 C 的範圍、政策風險、相容性、驗證責任及真實資料邊界已有可執行的定義，未發現需先修訂的計畫阻擋項。**PASS 不代替 Owner 採用 C 的決策，也不授權實作或真實 verify。** 本次未修改受審計畫。

- 日期：2026-11-10；checkpoint：計畫草案審查。
- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup` 主工作目錄。
- 分支：`feature/line-notes-media`。
- 審查 HEAD／精確草案：`423fd96f809307ad3f8d09c3faf1631ca74a2870`。
- 產品基線：`2f53bebd0875239312dacb0cb2cf843792a6377d`；至草案只有五份文件新增。
- [plan.md](plan.md) v1：blob `983bff639ad2d05890965c961825cca16f68d5fc`；SHA-256 `5ed302615f4261cddeda83d47cb223029341688f8360c9e4bb02c6f80f26c040`。
- [handoff.md](handoff.md) v1：blob `b6004c2363380a29dd937591b310548f327963ef`；SHA-256 `bcb11d80f1fa24df7ab7734a2c51c0ae6979da85b485300547bdfd6320a365ff`。

Reviewer 未撰寫或實質參與受審 plan／handoff 或其產品決策。Owner 本次明示由同一主 Session 承擔兩個審查角色，故另交 [simplicity-plan-review.md](simplicity-plan-review.md)。這是相對 Planner 的獨立審查，並非兩位獨立 reviewer 的共識；也不建立日後跨角色自動接續的許可。後置 Luna helper 只整理提交訊息，不簽發本報告或獨立接受。

本報告依 Owner 當次委任、Plan Reviewer Prompt、AGENTS、全域 v4.9.0 手動政策及 role-report 模板出具。政策要求的人工作業邊界保留；本輪同時委任只涵蓋兩份審查及指定 Git 交付。

## 需求、範圍與風險映射

需求以原提交單在本機的決策請求、非目標及建議條件作唯讀核對；可提交摘要見 [issue-context.md](issue-context.md)。沒有把提交單的歷史描述當成本輪實測，也沒有打開其引用的私人帳本、媒體或 GUI 原件。

以下行號綁定上述草案；產品行號綁定相同內容的產品基線。

| 需求／限制 | 計畫對應 | 審查判斷與依據 |
|---|---|---|
| 決定 stderr 是否為獨立產品條件，不直接修事故 | plan:5–17、57；handoff:18–24 | A／B／C 明列，C 的未知診斷風險沒有隱藏；未把推薦當批准 |
| 完整解碼不能只憑 exit 0 或 progress=end | plan:55、61、86–88 | 所有 stream、EOF、coverage、穩定性與反例仍必須成立；既有 `media_verify.py:876` 可重用 |
| runtime 與已保存證據一致 | plan:33–34、65–75 | 包含 normalizer、普通 verification、restart candidate 的寫入與重開；`notes.py:6419` 證實第二個 gate 確實存在 |
| probe 與版本探測要另決策，不默認放寬 | plan:5、33、57 | 本案明確保留既有判準；`media_verify.py:456`、`:587`、`notes.py:6574` 與之相符 |
| 保留診斷證據，不清洗 false 或降低 loglevel | plan:55–59、86–87 | 延用 bytes／hash／preview，新增內部一致性要求；不宣稱摘要可還原全部 log |
| 新舊 candidate／completion 與 UNKNOWN 保護 | plan:65–69、89、113–114 | 缺標記按 legacy 嚴格讀取、未知標記拒絕；不遷移或重寫歷史；降版限制有說明 |
| 僅必要來源與測試可寫 | plan:29–41、116 | 六個產品／測試／reference 路徑加任務報告；排除相簿、公用 record store、CLI 介面與退出碼變更 |
| 保留無關 dirty／私人原件 | plan:23、116 | 起始 Git 只有既有私人 untracked；未納入提交，變動時停止依賴動作 |
| 不新增日常啟動步驟 | plan:38、41、108；handoff:40–46 | 更新既有 reference，固定正式 Prompt 不變；開發計畫不成為日常依賴 |
| 真實資料另有精確授權，不順手 activation | plan:26、69、92、113；handoff:40–44 | 明示 verify 會寫 candidate、resume 可能 activation；本案沒有真實操作授權 |
| 外部 writer／中斷／回退 | plan:112–116 | 不承諾原子快照或 exactly-once；新政策落入真實事件後停寫保護原件，不靠刪事件回退 |

原始計畫 `docs/plans/20261031-notes-media/plan.md:54` 要求全部音視訊解碼至 EOF，拒絕非零退出、截斷與解碼錯誤；目前 reference:89 另要求 stderr 空白。新草案以後續增補和 reference 對齊處理差異，保留原計畫不可回寫的歷史身分，沒有漏掉規範整合責任。

## 成功條件是否可驗證

以下是對未來檢查設計的評估，**不是已執行結果**。共同產品候選應由後續實作報告記錄完整 commit／檔案 hashes；本次草案不可能預先具有實作 SHA，這不是缺件。

| 成功條件 | 負責者與方法 | 候選及足夠證據 | 評估 |
|---|---|---|---|
| 新政策下診斷非空而其餘完整時，runtime／重開結果一致 | Implementer；plan:73–75、86 的 subprocess／evidence 正例與重開 | 精確 S1 候選；實際 stderr bytes／hash／preview、完整 stream／coverage 及重開結果 | 可用既有 dependency injection 與 ledger fixtures 實現；不是重現真實事故 |
| 硬性失敗仍拒絕 | Implementer；plan:86–88 的 exit／EOF／短 coverage／漏流／停滯／漂移反例 | 同候選；拒絕原因、退出碼及沒有 completion 的證據 | 負例範圍直接對應本次 gate 改動 |
| legacy clean 可讀、legacy 非空及未知／矛盾 payload 拒絕 | Implementer；plan:66–68、87，`test_notes_regressions.py` | 同候選；合成事件重開、拒絕階段與歷史保留 | 現有 `:685` 具偽造 coverage 測試入口，無須真實帳本 |
| 固定工具可完整處理有聲／無聲及多 stream，壞檔拒絕 | Implementer；plan:88、94–106 | 同候選；實際工具 hash、fixture 來源、解碼結果及 skip 原因 | 方法可行；本輪未測工具可用性，必要案例 skip 保持 NOT_RUN |
| mixed-policy restart 讀回與基線 reader 安全拒絕 | Implementer；plan:68、89，`test_notes_restart.py` | 同候選＋明確基線 reader SHA；candidate／activation／completion 重開結果 | 僅隔離合成資料；舊 reader 非空新證據拒絕，不承諾全面向後可讀 |
| Skill 與程式說明一致，日常 Prompt 不加步驟 | Implementer；plan:38、77、108 | 同候選 reference 差異、引用檢查及報告 | 路徑已在 allowlist，無需動 AGENTS 或歷史 plan |
| 既有日常能力與 CLI 介面保留 | Implementer；plan:94–106 的 daily、notes help、notes suites 與 diff check | 同候選；逐項結果與必要 skip，不重複計已包含的測試 | 檢查與變動相稱；測試未執行不影響草案可審性 |
| S1 簡潔性及核心條件獨立驗收 | Owner 人工開主 Session；plan:90–91 | 精確實作候選、批准版 plan／handoff、實作證據 | 已保留 CRITICAL 必要關卡，不由 implementer helper 代簽 |
| 真實列表完成 | Owner 正式日常 Prompt；plan:92、108 | 另有精確資料／前景授權及實際備份證據 | 本案明確不納入；不能以離線 PASS 聲稱完成 |

`tests/test_notes_media_verify.py:291–357` 已有 clean、有損與非零退出 subprocess 的可擴充入口；`tests/test_notes_restart.py:2584–2640` 已有合成真實工具及 lifecycle 入口。這是來源可行性證據，不是本輪測試 PASS。

## 分級、檢查點與阻擋判斷

CRITICAL 理由成立：即使程式差異很小，影片完成必要條件與持久化證據語意都會改變。plan:85、90–91、120 同時保留計畫簡潔性、獨立計畫審查、第一切片簡潔性及獨立驗收。舊功能的歷史審查豁免不移植；S1 即最終候選時仍審查，沒有剩餘實作便不造空切片，符合 v4.9.0。

**阻擋項：無。** 未發現權限、範圍或證據設計有未被界定的必要缺件。本輪審的是尚未批准的草案；Owner 尚未決定 C 不構成草案審查的 BLOCKED，但仍是未來實作前的必要決策。

非阻擋建議：合成損壞影片的報告宜列明拒絕發生於 probe、decode 或 coverage，讓後續驗收能看出是否實際測到本次變動路徑；不要求增加解碼器或新測試框架。基線 reader 測試也應記錄所用完整 SHA，避免把同名函式當成版本證據。這些可在既定檢查／報告內完成，無須改計畫。

## 事實、推論、未知與停止條件

- 事實：runtime 的 decode gate 位於 coverage 前；目前持久化 loader 要求 stderr 空白。只刪 runtime 一行不足以完成一致性修正。
- 事實：上游固定 tag 的 DTS 訊息屬 `AV_LOG_ERROR`／`EINVAL`；`-xerror` 文件描述遇錯停止，`explode` 描述偵測到小錯誤便中止解碼。[mux.c](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/libavformat/mux.c#L758-L767)、[ffmpeg.texi](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffmpeg.texi#L2188-L2189)、[codecs.texi](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/codecs.texi#L191-L214)
- 推論：這些文件不足以證明每筆 log 都使最終退出非零；草案沒有做這項過度推論。C 是接受剩餘風險的政策取捨，不是證明所有診斷無害。
- 未知：事故完整 stderr、全部 stream coverage、現時私人資料狀態，以及此候選在固定工具下的所有合成測試結果。本輪不補造。
- 若未來反例顯示真正解碼失敗仍以完整 evidence 通過，plan:61 要求停止交 Owner 重決策；不得臨時 parser、換 pin 或刪反例。
- 若新增事件欄位無法在既有 payload 相容處理、需遷移或超 allowlist 修改，plan:69、116 要求停止；不授權 reviewer 代修。

## 實際命令、環境與證據

環境：macOS 27.2（26B123）、zsh、Python 3.9.6、Node v24.22.1。完整逐命令 stdout／stderr／退出碼與來源 hashes 在專案私有 `.local/line-backup/tasks/20261110-notes-video-stderr-policy-review/review-baseline.json`，未提交私人原件。

- `git rev-parse --show-toplevel`、`git rev-parse HEAD`、`git branch --show-current`、`git worktree list`：exit 0，綁定上述主 worktree 與草案。
- `git status --short`、`git diff --exit-code`、`git diff --cached --exit-code`：起始均 exit 0，tracked／index 無差異，只有既有私人提交單未追蹤。
- `git diff 2f53bebd0875239312dacb0cb2cf843792a6377d HEAD --name-status`：exit 0，產品未變，五份文件與交付相符。
- `git ls-remote origin refs/heads/feature/line-notes-media`：exit 0，審查時精確遠端 HEAD 為受審 SHA。
- `nl`／`sed`／`cat` 及正確路徑的 `rg`：exit 0，用於唯讀需求、政策、計畫與相關來源／測試核對。初次搜尋包含不存在的 repo `policies` 而 exit 2，已改讀同版全域政策；不是產品測試失敗。
- `git diff --check` 起始：exit 0；來源 SHA-256／Git blobs 已保存。文件落檔後的檢查與 Git 交付另記 [progress.md](progress.md)。
- GitHub connector 對本分支 open PR 的唯讀搜尋回傳空清單；未建立 PR、送 review comment 或要求他人審查。
- 唯讀核對 FFmpeg n7.1.1 官方來源；GitHub 頁面擷取缺少 xerror，改讀同 tag 官方 raw 文件後確認。不推定當次 binary 的事故結果。

**NOT_RUN：** 產品測試、合成影片生成／解碼、真實媒體或帳本查詢／寫入、LINE／GUI、下載、verify、resume、activation、reattest、restart confirm、真實 E2E 及獨立驗收。本輪無新增 GUI `OBSERVED`。這些未執行是審查邊界，不能預填成通過。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: PLAN_REVIEW_PASS; BACKUP_NOT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: READ_ONLY_PLAN_SOURCE_REVIEW_COMPLETE; PRODUCT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_OWNER_POLICY_AND_PLAN_APPROVAL
```

建議 Owner 明確認可 C 對未知診斷的處理及 legacy／新 payload 相容性邊界，核准上述精確計畫後，再人工啟動 Implementer；不把本次審查當成該決策。S1 審查、獨立離線驗收與後續日常實機成果仍各自交接。本報告不涵蓋日後修訂版本，沒有啟動修復、重測或結案。
