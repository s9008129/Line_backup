# 直接交給 Implementer 的 Prompt

你是本案 Implementer。Owner 已於 2026-11-10 在交接製作請求中明示批准本計畫，採方案 C；請完成下述已核准範圍的實作與必要離線驗證。先核對 Git／worktree／branch／HEAD，保留所有無關 dirty 與私人 untracked；讀取 AGENTS.md、本 handoff、同目錄完整 plan.md、issue-context.md、兩份 review 及 progress.md，再閱讀實際來源與測試。不要只依這段摘要實作。產品只能在 feature/line-notes-media 修改；從本交接提交的 HEAD 開始核對，若出現未解版本或外部修改衝突，停止依賴動作並報告。

精確核准計畫是 commit 423fd96f809307ad3f8d09c3faf1631ca74a2870 的 plan.md v1，SHA-256 為 5ed302615f4261cddeda83d47cb223029341688f8360c9e4bb02c6f80f26c040；兩項計畫審查由同一 reviewer 在 fc4fb251e68e7e767ce185693652c568baf45d56 交付 PASS。Owner 批准的是 C：僅 ffmpeg 逐 stream 解碼的非空 stderr 不再獨立否決；未知診斷亦依同一政策處理，不新增 allowlist 或日常人工核准。這不證明任何事故診斷無害。ffprobe、工具版本探測、照片及其餘安全判準不變。

S1 必須同步完成 runtime、normalizer、普通 verification 與 restart candidate loader 的政策一致性；保留固定工具／binary hash、嚴格 flags、真正整數 exit 0、stdout EOF、合法 progress end、所有音視訊 stream 精確 coverage、watchdog、前後檔案與工具穩定、身分、manifest 與持久化讀回。保留真實 stderr_empty、非負整數 bytes、SHA-256、有限 preview，驗證欄位一致性；不得清洗診斷或降低 loglevel。只在既有 payload 加明確 policy 標記；缺標記依 legacy 嚴格語意，未知／錯誤型別標記及矛盾欄位拒絕；新標記才啟用 C 並重算 coverage。不改外框或遷移歷史，不增加 CLI 模式。

實作只可修改 plan allowlist：src/line_backup_batch/media_verify.py、src/line_backup_batch/notes.py、tests/test_notes_media_verify.py、tests/test_notes_regressions.py、tests/test_notes_restart.py、.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md，以及本任務報告與專案私有證據。不得修改相簿、公用 record_store、Swift、AGENTS、CLI 參數／退出碼、固定啟動 Prompt 或歷史 plan。policy 字面名稱由你選定並記錄，不能讓 Agent 任選驗證標準。

必須驗證 clean／DTS／未知診斷在完整證據下通過，以及非零退出、缺 EOF、短 coverage、漏／重複 stream、停滯、漂移、legacy 非空、未知 policy、bool／float 偽整數、矛盾診斷及偽造 coverage 被拒絕且不產生 completion。使用固定工具產生有聲／無聲、多 stream、截斷／損壞的合成影片；記錄拒絕階段與實際退出碼。以隔離合成帳本驗證 legacy clean 與新診斷候選混合批次重開、activation／completion，並以精確基線 reader 驗證新非空證據安全拒絕。注入或 subprocess 診斷 fixture 不是真實影片事故重現。

執行 plan:94–106 的必要回歸並保存分組結果：notes_media_verify、notes_regressions、notes_restart、daily_records、notes --help、全 notes suite 及 git diff --check；完整 suite 已有同候選分組證據時不用重跑前三組。只用既有相符 Swift SDK 與固定 Homebrew ffmpeg／ffprobe，不安裝升級、不換 pin；必要案例 skip／工具不可用標 NOT_RUN，不降低關卡。同步更新既有 Skill reference；不得新增日常啟動步驟。

如果壞檔真正解碼失敗卻以 exit 0 及完整 coverage 通過，停止交 Owner 決策，不新增未核准 parser、替換工具或刪反例。需要遷移、新 CLI、超 allowlist、重要語意變更或遇版本／寫入衝突亦停止。同根因最多三次有證據嘗試，連續兩次無新資訊便停止，不藉換 Session 重置。

本次只授權產品開發及合成／隔離驗證，不授權 LINE GUI、下載、讀寫真實媒體／帳本、真實 verify／resume／activation／reattest／restart confirm；verify 會寫 candidate，resume 可能 activation，不能冒充唯讀。保護既有 completion、UNKNOWN、candidate、staging，不重下、不改 scope／generation、不換目錄繞 gate。私人原件不可提交。未來真實備份另由 Owner 使用日常正式 Prompt 與有效前景交接。

交付第一個可驗證切片時，記錄完整候選 SHA、差異、實際命令／退出碼／skip、證據與 hashes、六項狀態及剩餘工作，交 Owner 人工啟動 S1 Simplicity Review。可以在第一切片完成所有既定工作；即使它是最終候選，仍不得省略此關。審查前不自啟下一角色；若尚有實作，待人交回，若無則直接交下一適用獨立驗收，不造空切片。離線測試、review PASS 或 Git 推送都不是實機或獨立驗收。沿用同範圍 commit／push 授權，逐檔 stage，commit body 包含意圖、做了什麼、下一步的建議、驗證與結果；核對實際 body 及遠端精確 HEAD，不 merge master、不 force-push。

---

# 已核准計畫交接 v2

## 版本、批准與目前狀態

Owner 在本輪明示「我已經批准此計劃」，承接推薦 C 與兩項 PASS。本交接只把既有核准範圍轉成可執行交接，不更動 plan 的產品設計、驗收標準或資料授權。03_handoff_prompt.md 是人工清單，不另外創造 Handoff Agent 角色；本輪依 Owner 明示要求整理文件，未啟動 Implementer。

Repo：/Users/hsiaojohnny/dev/Line_backup；分支 feature/line-notes-media；主 worktree。交接起始 HEAD 為 fc4fb251e68e7e767ce185693652c568baf45d56，tracked／index 無差異，只有既有私人 issue提交單.md 未追蹤，必須保留、不 stage。產品內容基線仍為 2f53bebd0875239312dacb0cb2cf843792a6377d。接收時從包含本交接的實際 commit 核對，不把起始 HEAD 當成交接提交 SHA。

## 必帶資料與證據

- [完整核准計畫](plan.md)：內容不變，精確 commit／hash 見開頭 Prompt；原文保留 Planner 當時「待核准」歷史表述，批准事實由本交接及 Owner 當次訊息補充，不回寫原批准史。
- [簡潔性審查](simplicity-plan-review.md)、[計畫審查](plan-review.md)：均 PASS，相對 Planner 獨立，但來自同一 reviewer；不是兩位獨立意見或產品驗收。
- [遮蔽來源](issue-context.md)、[Planner 報告](planner-report.md)、[進度](progress.md)：保留需求、未知與既有證據界限。
- 專案私有證據 .local/line-backup/tasks/20261110-notes-video-stderr-policy-plan/ 與同前綴 -review/：來源 hashes、文件檢查與 Git 交付。不可將私人原件轉交公開審查；缺少私有歷史不授權重建真實狀態。

## 已知、未知與後續責任

已知來源證實 runtime 與 loader 同時要求空 stderr，故須同步調整；probe 與版本 gate 獨立。事故完整 stderr、coverage、現時真實資料狀態仍未知；Post1／Post2 僅是歷史遮蔽代稱，不可用於認領媒體。產品測試與真實操作本輪均 NOT_RUN。

Implementer 負責上述 S1、必要後續切片及 plan 檢查矩陣；Owner 啟動第一切片簡潔性審查與核心條件獨立驗收。獨立驗收須對精確產品候選重現合成正負例與相容性，不等於 LINE E2E。真實列表完成仍需另有日常任務證據。實作候選 SHA 尚未存在，由 Implementer 交付時產生，不能預填。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: APPROVED_PLAN_HANDOFF_READY; BACKUP_NOT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: DOCUMENT_HANDOFF_ONLY; PRODUCT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_STARTED_IMPLEMENTER
```

第一個具體動作：Owner 將本文件開頭 Prompt 與精確交接 commit 帶入新的 Implementer 主 Session。不要要求 Owner 再決定已批准的 C；有實質版本或範圍變動才提出具體決策。本輪只交接，不實作、不重測或結案。
