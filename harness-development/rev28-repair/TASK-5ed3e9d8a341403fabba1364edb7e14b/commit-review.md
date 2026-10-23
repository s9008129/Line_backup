# 最近 10 個 commit 的第一性原理審查

審查基準：HEAD 07a7ec3f64f2a7a9837a78f9ae0e731b60252519；2026-10-04；按 HEAD 向前最近 10 筆，未解讀為創始 10 筆。起始工作區 clean。此報告先於修復，修復结果另見 execution/result。

成功的最低必要條件是：同一正確相簿的當前可操作表面 → 經當前原始證據證實的候選 → 持久化授權／预算 → 一次受控事件 → 直接後置觀察 → 完整穩定檔案 → 與 baseline 內容相等 → 獨立重算。點擊、文件、hash 相符、測試數量和離線 review 都只能支持其中一些命題，不能替代真實備份結果。

| Commit（時間正序） | 實際內容 | 對關鍵路徑的意義／限制 |
|---|---|---|
| 5bfa651 | 記錄 V-09 attempt-03 三份 review；0 MAJOR，但發現 1-pixel 與 1-point 邊界差異 | 有效的新反例，應修單位轉換；既有 review 的其他 VERIFIED 仍須核對控制流 |
| cf39fdc | 唯一產品修正：共享 1-point margin，按 capture scale 換算；增加 1×/2×/3×/NaN regression | 修正坐標單位根因；未修復 readiness provenance 或 durable error 路徑 |
| 3d74248 | 將歷史 focused 11 suites 標籤改為實測 8 suites | 修正紀錄準確性；不改產品，也不改 immutable bindings key |
| c945f04 | 收錄修復樹的 build/focused/full/adversarial/replay/provenance、CLI refusal 和 digest | 支持離線測試／byte identity；ScriptedOcr/FakeActuationEnvironment 的成功不能證實 production readiness |
| 5ed7106 | 綁定 attempt-04 至 cf39fdc / 48-path digest | 解決證據與 source 身分綁定；hash 本身不證實語意正確 |
| 815e9f1 | 收錄三份 attempt-04 review、Stage 06 identity reconciliation 與 decision | 正確辨別 luna 舊分支的 missing composition 已被同一 lineage 解決；但 timing review I-2 錯誤地將 try? durable write 判為不會 fail-open |
| ce52103 | 新增跨 session 導航 handoff | 有助 preservation；卻仍依赖手寫 status/操作指引，需要與實際 goal-slot policy 一致 |
| 69de4cb | 改為 prompt-first；收錄 Phase A refusal；指示 fresh runID 重跑 | 主要新增缺陷：fresh runID 與保留的 goal slot 綁定衝突；不能靠新授權繞過 |
| d287be3 | 收錄 attempt-01 config、單筆 authorization ledger、anchor、refusal log | 直接證據：targetWindowNotUnique(found=2)，exit77，0 irreversible，尚無 Phase A report。這次 refusal 的環境根因成立，但不能推出所有剩餘問題都只是環境 |
| 07a7ec3 | 整合 V4.3.1 全域操作規則、六狀態、budget與角色 | 增強狀態語意；複製的舊版本路徑與現行 global authority 漂移，且再次強化 fresh-run dead end 和無 code work 的過度結論 |

10 筆中 9 筆只改文件／證據；1 筆改產品。這是關鍵路徑上的證據集中，不是測得的性能瓶頸。未做 runtime profiling，因此不聲稱 CPU、Vision 或 SCK 是主要性能原因。

## 已證實的問題與因果链

1. **Durable write fail-open（高嚴重度）**：QuartzActuator.swift 的 post-hover revalidation 成功後呼叫 recordRevalidationOutcome；該 helper 用 try? owner.recordCandidateRevalidation；失敗被丟棄，緊接 sink(down) / sink(up)。此前 reservation 成功無法證明之後的 ledger/anchor 寫入成功。典型反例是在 hover 之後改變 ledger 或令 anchor 無法寫入。修正必須傳播這次錯誤並保證只有 move，不得下/上點擊。
2. **Readiness 的來源與新鮮度被分割（高嚴重度／可用性）**：captureLive 另走原始 SCScreenshotManager，沒有 session 的完整 frozen-rule/independent backing scale 證據；畫面 hash 必須與舊候選完全相等，卻把 currentEpoch/currentBinding 設為旧 identity/candidate。C3 明文要求等像素也不代表新 observation、hash 改變要重新定位。hover highlight、時間／通知 redraw 可造成無必要拒絕；未做真實觀察，發生率未知。修復需要 fresh retained bundle 和安全位置再驗證，不是單純移除 hash 檢查。
3. **Fresh-run 續跑指引必然衝突（高嚴重度／阻塞）**：GoalSlot key 不含 runID，但 verify 同時比較 runID 和 stagingRunDirectory；attempt-01 已建立 slot，並在 archive ledger 寫入 transaction.authorization。新 run 使用相同 slot key、不同 identity，預期 goalSlotConflict。這是純 source/data contract 結論；沒有讀寫 production slot。本次 Python in-memory replica 指出 mismatch=[runID,stagingRunDirectory]，不是 Swift runtime測試。GoalSlotTests 也明確要求拒絕不同 run 身分。修正 operator 指引，保留既有安全 policy。
4. **假設被升格為 PASS（高嚴重度／證據）**：PhaseAEvidence 的 popup/occlusion 條件僅檢查候選、正尺寸與 retained hash；沒有證明 topmost addressed surface、popup census 或遮擋。frozen geometry 條件也把規則存在／合法 frames 與實際 current-composer calibration 混在一起。沒有量測的義務必須 UNKNOWN並阻擋 B。
5. **CLI 成功與 required evidence 不一致（中高嚴重度）**：live-preflight 發佈含 FAIL/UNKNOWN 的 report 後仍輸出 preflight=passed並exit0。報告内部 phaseBPreventedBy 可保護後續，但 operator/API 表面訊息錯誤。修正為非零、明確 incomplete/blocked，同時保留 report。
6. **明細與後續表面身分弱（中高嚴重度）**：albumDetailVerified 將 OCR 存成 Set，只要求 group+57張照片，不要求唯一 date；ellipsis/group header duplicate 也可能被轉成 nil 的可選排除框。必須使用當前畫面的唯一 exact identity，避免跨 capture 的先前身分取代 current proof。
7. **狀態／文件來源漂移（中嚴重度）**：ARCHITECTURE/CAPABILITY仍寫缺 native provider或preflight消耗one-shot；實際 main已接LiveCompositionFactory並保持slot未消耗。root handoff未將Phase A outcome回填舊progress/execution；本次不改寫歷史，只用新v3紀錄與明顯supersession建立 current navigation。

## 重新核驗過的事實

48-path implementation digest仍為6734dda58539c28b7ae74755dbafc3d50aecd08c869a88497e08235582a0a686。canonical Plan和Handoff hashes分別05413807f5d7c04d5fe57eb058da6da734ddef5e350a9b023bfa8f8d72f84c1b／67fc16a638b115fef8b8e99e57ec0d6a2fc344cdd15c6eaf6a72bcdb1c227a33；frozen artifacts9/9 byte-identical。歷史Phase A ledger hash-chain和anchor重新核驗通過；只有transaction.authorization，沒有irreversible record。a52/a53 archived replay bytes identical，sha81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261。這些是本次唯讀重算；未把歷史build/test當成本次執行結果。

## 瓶頸與根因

直接歷史阻塞是兩個LINE視窗的正確拒絕。系統性瓶頸則是已審查的離線契約與真實執行證據沒有形成一個閉合路徑：raw readiness acquisition、scripted成功資料、config geometry、語意錯誤的review disposition，以及與durable identity不一致的交接指引。root cause不是安全檢查太嚴，而是部分檢查使用錯誤來源或證實不足，並且副作用邊界有錯誤傳播漏洞。

採用的實作原則：一個可信觀察來源、typed evidence／fresh provenance、變更後重新定位、durable error propagation先於effect、未知保持未知、故障注入與反例測試、immutable history、獨立review。Swift throws/try的參考是官方 Swift repository docs/ErrorHandling.md；Context7僅用generic API問題，未送出專案資料。

Stage 06 routing：PLANNER_REPLAN。使用者已明示同意新v3本地修復。成功標準是已審查的修正通過當前本地測試與獨立Acceptance；停止條件為實作超出凍結計畫、未解決安全／語意阻塞或3/2收斂門檻。actual LINE Phase A/B與內容驗收仍未執行。
