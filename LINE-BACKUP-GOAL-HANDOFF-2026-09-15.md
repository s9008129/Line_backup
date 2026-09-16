# LINE 相簿自動備份：接手文件

日期：2026-09-15。用途：新對話的 Goal 啟動輸入。
本文件是使用者目標與已觀察工作的交接，不是既有 Stage 03 handoff 的替代批准。實際產品變更與 GUI 試驗須依下述範圍及目前計畫審查執行。

## 1. 目標與本輪優先順序

最終目標：安全自主備份 LINE 群組相簿照片，能驗證檔案、保存結果、中斷後恢復並防止重複下載。

指定 LINE bundle：`jp.naver.line.mac`。
使用者指定群組：`旻謙允禎成長日記`。
首個驗收相簿：`2024/05/13～05/17`，預期 57 張。
本輪不擴展群組批次下載。

下一個優先里程碑：確認實際執行 runtime 哪一條合法路徑，能肯定辨識真正的「儲存全部 / Save All」，並可靠支援後續下載交易。

bridge readiness 是候選實作的前提，不是最終備份目標。不得預設它必須成為所有備份路徑的全域門檻。也不得因希望簡化就宣稱 Computer Use 已滿足選單能力。

## 2. 工作位置

- Bridge：`/Users/hsiaojohnny/Documents/Codex/2026-09-12/line-native-ax-gui-session-bridge`
- Controller：`/Users/hsiaojohnny/Documents/Codex/2026-09-12/line-native-ax-readonly-scrollbar-probe`
- 既有任務：`/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/.agent/tasks/T20260914-0120-01-c04-observation-architecture`
- Skill：`/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md`
- 使用者先前指定的備份專案：`/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state`
- 安裝目錄：`/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge`
- LaunchAgent label：`com.openai.line-native-ax-gui-session-bridge`
- 兩個 release binaries：Bridge 的 `work/release/`。

備份 project_root 與 backup_root 不可用程式 repo 或 cwd 代替。沿用已授權專案並從 config 核對目的地、registry、intent 與 writer；缺失不可初始化空歷史。

## 3. 第一性原理結論

備份必需能力是：正確目標 → 真正 Save All → 正確目的地 → 完整圖片 → 持久化與重複防護。

已取得相簿視窗，不等於能取得浮出選單；選單可見，不等於能安全點擊；UI 顯示完成，不等於檔案完整。

先前工作逐漸集中於 bridge 的安裝、簽署、程序鎖與證據包，尚未閉合「bridge 是否是完成備份的必要路徑」。部分修復是真實且有價值，但不可把其局部完善取代端到端驗收。

Skill 的 `references/ui-procedure.md` 校準規則允許 Accessibility label 或可靠視覺文字來辨識 Save All；既有 C04 計畫則要求 AXObserver/WindowServer/bounded hit-test 的更嚴格語意證據。兩個契約有差異。若改採視覺路徑，須先正式修訂計畫並獨立審查等效安全性，不能默默降級，也不能把 OCR 字串單獨當成正確目標證明。

## 4. 已知事實與界線

### 已核對的檔案與輸出

- 當前讀到的 plan revision 是 34，SHA-256：`61860dee7ea66cf1d3a1eca23f92f611ed7f080716eaa4f8ea7c020c30f21f06`。接手需重驗是否已變更。
- `handoff.md` 與 `execution.md` header 都引用 revision 34 與此 plan hash。
- plan header 仍有 CANDIDATE、REPLAN_REQUIRED 等狀態；不能由 handoff 的 PLAN_APPROVED 字串推論所有驗收通過，需核對實際 review。
- 下列目錄的 focused/full regression exit-code 已讀取為 0：`e2e/attempt-14/revision34-verification-3/`。
- 同目錄 `formal-release-build.exit-code`、`current-codesign-verification.exit-code`、`current-read-only-safety-scan.exit-code` 已讀取為 0。
- 安全掃描只涵蓋 Bridge 的指定來源與腳本；token scan 不是完整行為安全證明。
- fault fixtures 的 device creation 與 deterministic parent replacement race 明確為 UNAVAILABLE，不可稱測試已通過。
- `execution.md` 內部分測試連結仍指向 `revision34-verification-2` 及較舊檔名；它與最新 evidence 索引需更正。保留原始證據，不重建 raw output。
- 最近一次用 `^CASE_EVIDENCE=` 查詢沒有找到結果，不能由此說缺 JSON：先前 harness 採 JSON 記錄，需讀實際格式再解析，禁止再犯查詢模式錯誤即判定證據缺失。

### bridge 故障

既有 execution 與前序診斷記錄描述：舊 daemon.lock 的 PID 794 已屬於 macOS extensionkitservice，舊 bridge 用 PID-only 存活檢查而誤判已有 daemon，導致 spawn-scheduled/exit 1。

修復來源已改為 descriptor-anchored openat、flock、FD_CLOEXEC、嚴格 payload 與 legacy ownership 檢查。這是服務啟動修復，不能據此宣稱 Accessibility 已修復。

歷史 formal controller 曾回報 trust=false、AX root-read=-25211。其 TCC responsible process 與拒絕根因仍未確證。

- `-25211` = kAXErrorAPIDisabled。
- `-25204` = kAXErrorCannotComplete。
- AXIsProcessTrusted 是目前呼叫程序的信任結果，不是全部 Computer Use runtime 的結果。
- 重新簽署會影響 raw hash；raw hash 差異不獨立證明版本舊。
- service missing、sandbox denied、request-store failure、TCC denial 不可混稱。

截至本次交接，沒有新證據證明修復版已正式部署、formal trust=true、C04 通過或本輪相簿備份成功。原本準備的一次部署尚不能視為已執行。

## 5. 接手後的最小決策流程

### A. 唯讀建立能力與證據表

先讀適用 AGENTS、skill 及本階段必要 references、目前任務計畫和原始證據。不要把全部歷史 revision 當成待做清單。

列出實際 runtime/provider，以及它是否有 documented：畫面觀察、浮出選單觀察、座標映射、點擊、必要等待與 chooser 操作。分別標為 VERIFIED / HISTORICAL / UNKNOWN / UNAVAILABLE，附證據。

不同模型、ChatGPT、Codex desktop、CLI 的結果不能互代。不得因同叫 Computer Use 就假設能力一致。只做會改變選路決策的檢查。

### B. 計畫修訂與選路

以現有 skill 的安全要求為基礎，審查是否可用直接 Computer Use 完成選單辨識與操作。

- 若有可信能力證據：規劃直接路徑，bridge 作非阻塞輔助。
- 若已定位直接路徑的選單觀察缺口：評估 bridge 是否能補足該缺口；只測相應能力。
- 若未確定：設計一個有停止條件、能區分假設的 observation 試驗，不能以反覆相同點擊探索。

計畫需明示 CORE、SUPPORTING、BEST_EFFORT。所有全域 gate 必須保護正確相簿、正確動作、正確目的地、防重複或驗收可信度。
按 CRITICAL 流程更新同一 plan revision、獨立 review、handoff，再實作語意變更。保留既有 C04 歷史，不假稱原 AX contract 已通過。

### C. 必要測試與現場驗證

只重跑受變更影響或有具體未決疑慮的測試。並行代理限互不重疊的審查與測試；一檔一 writer。

若選 bridge，只有證明 runtime 修復是所選路徑必要條件時，才做一次已審查部署；預先完成測試、回滾及證據準備。部署後一次正式 readiness 分開判斷服務與 AX。若仍拒絕，不能返回重裝循環。

若需要 GUI observation，先核對歷史 ledger 和授權額度。最近明確執行範圍止於 C04_READY 且禁止 GUI；本交接不自行增加點擊額度。先完成所有無 GUI 的前置工作，再提出一次精確 observation 授權。不得因新 goal/run ID 重置舊額度。

observation 試驗必須肯定辨識實際 Save All、目標群組/相簿、當前幾何與 provenance；不可用歷史 row order、舊座標、公式或 OCR-only 通過。原 C04 試驗若被採用，ellipsis 後維持零其他 GUI input、結果 PASS 或 SAFE_ABORT 即停止。

### D. 單相簿備份驗收

先唯讀 reconciliation。歷史聲稱已有 57 張 VERIFIED，候選位置：`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57`。這是待驗線索，不能作為下載成功證明。

群組「旻謙允禎成長日記」與歷史 config/state 的「旻謙允楨成長日記」有字形差異；skill 另含其他歷史標題。不得自行合併或改寫。先查權威 config 與 provenance，仍有歧義才問一次精確身分問題。

有效既有備份採 verify-only；缺失/不完整/來源不明不授權重送。只有真正需要下載時，在完成前置工作後取得指定群組、相簿、57 張、確切安全目的地、一次下載的 production gate。

依 skill 完成 intent/read-back → at-most-once dispatch → chooser destination verification → bounded filesystem observation → terminal state/read-back。dispatch 不明不得重點 Save All。

驗收：57 個可辨識圖片、零空檔/partial/temp/不明一般檔、穩定 inventory、每檔 SHA-256/byte length、來源對應、state/registry/intent/writer 一致。現在的 hash 不能補證歷史來源。
恢復/重複防護用隔離 fixtures 測，不對真實相簿重複下載。

## 6. 人類介入與安全

使用者已重裝、移除重加 Accessibility 至少十次。禁止無新證據要求重複操作。使用者不做 Terminal diagnostics。

只有不可自動完成的 OS permission/login/security-policy、缺失的目標身分、必要 GUI 試驗額度或首次正式下載授權才提問；列新證據、精確對象、一次最小步驟與驗證方式。

使用正式 runtime 權限申請；不改 TCC DB、不停 SIP、不全域重置隱私、不透過 GUI Terminal/AppleScript/其他程序繞過限制。
禁止 AXPress、AXUIElementPerformAction、AX write。任何下載使用實際 runtime documented Computer Use。
在新增合法 GUI/production 授權前，所有 GUI 與備份狀態寫入计數維持 0。

## 7. 成功與交付

交付：選路決策與必要性、plan/review/handoff、必要 diff、測試與限制、原始命令/stdout/stderr/exit、reviewer 報告、action ledger、明確 required artifacts 清單及 SHA-256/byte length 驗證。

分別報告 ROUTE_DECISION_STATUS、MENU_OBSERVATION_STATUS、BACKUP_IDENTITY_STATUS、BACKUP_FILES_STATUS、BACKUP_STATE_STATUS、REQUIRED_VERIFICATION_STATUS、INDEPENDENT_ACCEPTANCE_STATUS、TASK_CLOSURE_STATUS。

整體完成只在指定相簿的真實備份或有效 verify-only、狀態一致性、必要獨立驗收及可重用恢復流程全部有證據時成立。文件、build、bridge readiness、C04 各自僅是里程碑。

遇到不能合法繼續的阻塞，保存可供高階模型判斷的 Issue：事實/未決假設、最小重現、原始證據、下一個有區辨力的實驗與 Human Gate。依 runtime goal blocked 規則處理，禁止空轉。
