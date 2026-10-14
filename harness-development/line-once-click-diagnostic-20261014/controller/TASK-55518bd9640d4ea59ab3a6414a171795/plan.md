# 一次性 LINE 相簿點擊診斷

END_GOAL 仍是完整自動備份 E2E；CURRENT_SLICE 僅建立獨立、一次性的相簿開啟觀察。FIRST_UNMET_REAL_GATE 是正式准入後，另行取得本次明確前景交接及 screenshot／AX 擷取、一次點擊同意。目前兩者尚未成立；本輪只做 Plan／獨立 Plan Review／deterministic Handoff 准入準備，禁止任何 LINE 觀察或輸入。

採 STANDARD：唯一 UI 動作是可逆的相簿導覽，無下載、資料／安全邊界變更或外傳；使用者明確要求獨立 Plan Review。通過後由 Luna Implementer 串行執行，零 helpers／writers；不另開 Handoff 模型或獨立 Acceptance。既有 Harness 4.8.0 完全不變。只可寫本 Task 目錄的證據、結果、progress.md 及 E2E測試報告.md；所有程式、Harness、原 Task／Issue／c6／28 gates、config、backup state 及既有 dirty／untracked 工作皆受保護。

本 Task 明確連結 intake.json 中 predecessor TASK-4acb4326ea2a4c50ace6f333f2de8751／Issue a2a1e4c39580d6a2fc1f4b6be628f63ee1e6ca53ed7d1fb19c7777bbfba9afc5／c6 run。其 BLOCKED／WAIT_HUMAN、未通過 gates、失敗歷史及根因額度不變；舊剩餘額度本 Planner 未核實，維持 UNKNOWN，本 Task 授予舊根因零次嘗試。此新觀察不是修復、重試、continuation、ML08 或完整備份驗收。

四個 required gates（每項只由自身證據判定）：

1. **P01，PLAN**：發佈 schema-valid Plan／contract；原生邀請、source、Plan hashes 綁定。PASS 只表示 Plan 可送獨立審查；固定 CONTRACT／RESULT schema receipts 由 parent 註冊，未註冊不得宣稱正式准入。
2. **D01，IMPLEMENT**：先確認獨立審查 PASS、原樣 deterministic Handoff、Luna 原生准入及可用的既有 cua_repl。parent 必須在另一輪明列 LINE／相簿列表與精確下一動作，取得明確本次前景交接及擷取／一次點擊同意，留存訊息原文；人類交接為 OBSERVED 授權前提，不冒稱工具 PASS。之後只取得一組 fresh 列表 screenshot＋AX，原始檔保存後以既有觀察能力核對；能力、保留或解析失敗即停止。唯讀 config/line_backup_config.json，綁定 canonical group「旻謙允禎成長日記」；同一組觀察須證明群組、album date range／photo count、完整唯一 card bounds、非 thumbnail 的安全 metadata area、精確 click point 與其座標系／scale，以及 session／PID／window／surface／layout。沒有完整唯一目標就停止。以 task-local target-binding.json 綁定原始檔 hashes／capture identity／時間／授權及上述資料，保存並讀回逐欄相等；不得採舊畫面、猜點或補擷取。
3. **D02，IMPLEMENT**：D01 通過且前景／視窗／layout 無中斷時，先將一次性 dispatch intent（binding hash、point、attempt=1、狀態）持久保存並讀回；恰至多一次原生 click，保留實際呼叫／回傳。任何已送出或結果不確定皆不可重送。隨即只取得一組 fresh 詳細頁 screenshot＋AX，保存原始檔及 hashes，核對同群組／session／PID／window、album-detail surface、date range 與 photo count 全部等於 binding，然後立即停止。wrong page／identity、缺證據、前景取回或未預期結果均不繼續；無 retry、scroll、第二 click、navigation／reacquisition、Save All、chooser、download 或 backup-state writes。前景失去後本 Task 結束，不另行取得前景接續。
4. **D03，IMPLEMENT**：對 intake.protected_before 全部 paths 做精確 hash readback；確認保護值及 Git HEAD／branch／index 未變，另由既有 controller post-snapshot 檢查範圍。原始 screenshot／AX 僅置此 Task 的 private/（0700 目錄、0600 檔案），不得 stage、commit、push、upload 至 GitHub／任何外部服務或在公開報告嵌入。E2E測試報告.md／progress.md 保存原始收據本機連結、GOAL_GATE_DELTA、INFORMATION_GAIN、NEXT_AUTHORIZED_REAL_STEP、真實 click count、未完成總目標及 Planner 交接狀態。無新工具、framework、tests、fixtures、CI／產品修正。

唯一診斷最多一次嘗試，包含 capture；schema 固定 retry_policy 的 2 次／10、30 秒僅保留格式，較窄 Plan 禁止本 Task 任何診斷重試。任何必要 gate 未 PASS，保存真實 format-3 non-PASS result／原始證據並停止，**不得呼叫 importer record_result**：未改動 controller 在 IMPLEMENT PARTIAL／FAIL／BLOCKED 會自動開 Issue，使用者已禁止。正式 admission／closure 因此保持未完成；不可改標 PASS、NOT_RUN 或其他結果規避 guard，不新開 Task／Issue／continuation，不修 controller。成功時亦只能宣稱此獨立一次點擊觀察；既有備份 gates 全部未增加。網路／browser OFF 是角色政策，無 OS sandbox 或 network denial 證明。
