## 給接手 Agent 的交接 prompt

```text
你接手的任務是「整套自動相簿備份流程的修復與驗收」。請先讀完本文件，再開始行動。

使用者指定的專案 root 是 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup。
所有新的備份必須放在此專案的 backups 下，使用適當命名。使用者已兩次明示禁止使用原本的外部備份位置；不要再詢問、搜尋、採用或寫入該位置，不要把舊文件的 root 當成當前 authority。

已完成的事實：群組「旻謙允禎成長日記」（禎 U+798E）的「2024/05/13~05/17」57 張相簿，已於 2026-10-05 透過 CUA 保存到本專案。57 個 JPEG、17,924,900 bytes，三次清單一致，全部完整解碼；state revision16 已 VERIFIED 並同時釋放 writer/context；產品 verify-only 與正式獨立 A1 都 PASS。此單一相簿 task 是 DONE，不准以驗收或換 session 為由再次下載它。

尚未完成：可重用的整套原生自動化流程。CUA 曾漏掉實際開啟的浮動選單，需要使用者截圖才能校準。當前 native Phase A 的 FROZEN_CAPTURE_GEOMETRY、POPUP_OCCLUSION_ASSUMPTIONS 仍缺直接綁定證據，原 native GoalSlot/entitlement 仍 UNKNOWN。單次 CUA 成功不證明這些條件通過，也不授權 native Phase B。

先核對 Git dirty/untracked、當前 config/state、已驗收 source SHA 與本文件的證據索引。接手必須使用同一份本機 worktree；本交接 commit 只提交 handoff.md，已驗收修復、config/state、照片與 harness-development 證據仍是本機未提交資料。不要 reset/clean/stash、切分支、回退舊 HEAD 或把 checkout 的舊程式當成已驗收版本。缺檔或 hash 不符時保存差異，停止依賴該證據，不自行重建 registry 或恢復舊 authority。

下一步先做不依賴 LINE 前景的本機唯讀診斷，明確區分 CUA screenshot 與原生 SCK/CG/AX 路徑。查明缺的是觀察能力、collector/evidence binding、產品缺陷，還是必要外部條件。使用者目前可正常使用電腦，不能假設 LINE 仍在前景、選單仍開著或舊 PID/window ID/座標仍有效。

後續安全/持久化/校準/授權語意修復走 Harness4.7.0 format3 CRITICAL：Planner → 獨立 Plan Review → byte-identical machine Handoff → Implementer → 獨立 Acceptance。本文件是交接與既有授權紀錄，不是新 repair Plan 或 production permit。先凍結真正受測入口、來源與副作用邊界、路徑、必要 gate、反例、成功與停止條件，再實作。使用者已授權你自主規劃及本機修復；同範圍角色交接不用重問。需要 foreground/unlock 等實際介入時才請使用者做一個具體動作；擴大到其他相簿、新的不可逆下載、改安全邊界或舊 native 權利時，先完成可審查的方案，再釐清必要授權。

不得重置歷史 PRIMARY_NATIVE_COMPOSITION 3/3，不能換 task/run/model/session/branch/stagingRoot 取得第4次 live attempt；同根因既有 budget 要保留。fresh identity 修復有2次實作嘗試，首輪 FAIL 與後續 PASS 都保留。舊 slot/ledger/anchor 不可刪除、重簽或改寫；新專案 CUA run 不代表舊 native 權利已消耗或已恢復。

先建立清楚的新 v3 continuation Plan 與根因/預算關聯。實際新動作若受舊已耗盡 budget 或未知 native authority 阻擋，整理精確決策給使用者；不能把新 Plan 當成重置。若 controller/native role admission 不可用，誠實提供 advisory 交接，不手動推進 controller state、不偽造 session/provider receipt。

以可觀察的產品行為、實際檔案與 state 關聯驗收；fixture、exit0、文件、單張成功 capture 或人工畫面都不能代替整套成功。保留六個正交 status；人提供的畫面是 OBSERVED，未知仍 UNKNOWN。只有必要實作、驗證與獨立驗收全數滿足，才宣布整套流程 DONE。

開始時用白話回報：已接手哪個目標、保留哪些成果、第一個唯讀診斷要釐清什麼。現在不用先叫使用者開 LINE。
```

# 整套自動相簿備份流程：修復與驗收交接

更新：2026-10-05，Asia/Taipei。接手環境是同一台 Mac、同一份本機 worktree。

本文件取代根目錄先前 2026-09-16 的交接入口；原檔原 bytes 已保留在 `harness-development/rev28-handoff-delivery/TASK-fad90a2bf8e14a6dbb81dc5412cc7839/evidence/previous-root-handoff.md`，SHA256 `c81224e5c29ea9bde5b9ed20ab9279d4f0c950e56629afb5ed7391098854916e`。其他舊 Plan/Handoff、失敗、counter、authority 與證據均保持原樣。舊根目錄文件或 `HANDOFF-2026-09-30-rev28-next.md` 的「使用外部 root」「尚無真實備份」「fresh runID 就能重跑」「產品仍凍結於舊 commit」不能用作當前操作指令。

## 1. 使用者目標、授權與操作狀態

使用者希望整套 LINE macOS 相簿備份能可靠自動執行，並以最佳實務處理安全、定位、持久化及驗收問題。前一輪曾要求深度審查「前 10 個 commit」；實際既有報告採用交付前 HEAD 向前最近 10 筆，並明記此解讀，不是創始 10 筆。該分析已完成，不必重新無差別探索歷史。

使用者後來明示重新開始修復、由 Agent 規劃並自主處理，只有真正需要時才要求介入。「重新開始」指重新診斷，不代表刪除歷史、重置 budget 或抹除不可重試意圖。

最新且優先的資料位置要求：**MUST NOT 使用原本的備份位置，直接存到本專案資料夾下並適當命名。** 新專案 authority 已依獨立審查初始化並完成一個相簿 transaction；不再等待使用者提供外部 root，也不得從旧文件恢復它。

使用者曾把 LINE 相簿放到前景、提供開啟選單與關閉後完整截圖。備份開始後 Agent 已停止所有 LINE GUI 動作。完成下載與驗證後，已告知使用者可正常使用電腦、切換或關閉 LINE。**這些是歷史操作狀態，不是接手時的即時畫面證據。**

本次另明示授權撰寫此交接文件及 add/commit/push。此文件交付的 Git 授權不等於下一輪可自行發布產品改動、擴大相簿範圍或恢復未知 native production permit。

## 2. 當前權威位置與精確身分

| 項目 | 當前值 |
|---|---|
| 專案 root | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup` |
| Git branch | `v43-ab/codex-rev28` |
| origin | `https://github.com/s9008129/Line_backup.git` |
| 交接更新前 HEAD | `07a7ec3f64f2a7a9837a78f9ae0e731b60252519`；此後本次為僅文件 commit，接手時實讀 HEAD |
| 當前 config | `config/line_backup_config.json` |
| 當前 backup state | `state/backup_state.json` |
| 當前 run log | `state/run_log.md` |
| 新備份 root | `<專案 root>/backups` |
| Canonical group | `旻謙允禎成長日記`，禎 = U+798E |
| Canonical group key | `line:jp.naver.line.mac:旻謙允禎成長日記` |
| LINE app identifier | `jp.naver.line.mac` |
| 已完成 fingerprint | start `2024-05-13`，end `2024-05-17`，expected `57` |
| 已完成 destination | `backups/旻謙允禎成長日記/2024-05-13_2024-05-17_57張` |
| 已完成 run | `RUN-20261004-project-album57-45ee0a78` |

`禎` 與 `楨`（U+6968）必須保持不同字串/key，不可正規化或推論為同一群組。曾存在的 legacy identity 問題不能靠相同日期、數量或照片 bytes 合併。

Config 是 schema2；`max_albums_per_run=1`、`recovery_limit=1`、`poll_interval_seconds=5`、`stable_samples=3`、`max_wait_seconds=600`。單一相簿成功不是批次授權。不要為了跑測試改 live config/state 或把 max_albums 擴大。

## 3. 已完成的成果與證據界線

### 3.1 第一輪本機安全修復

位置：`harness-development/rev28-repair/TASK-5ed3e9d8a341403fabba1364edb7e14b`。

`commit-review.md` 已逐筆分析最近 10 個 commit。主要根因是離線契約、當前觀察、durable 副作用邊界和真實執行證據未形成一致流程；沒有 runtime profiling，不能聲稱 CPU/Vision/SCK 性能是主要瓶頸。

已修復 durable write 錯誤吞掉後仍點擊、hover 後觀察與候選新鮮度、當前群組/相簿精確身分、續跑重觀察、Phase A 缺證據仍報成功，以及文件與 source 不符。`acceptance-02.result.json` 是正式本機獨立 PASS；它沒有授權真實 native Phase A/B。前次失敗與其 reservation accounting 修正仍保留。

### 3.2 Fresh process identity 修復

位置：`harness-development/rev28-fresh-repair/TASK-d34338d2680f4814aabd6841ef094c14`。

最新 49 個 Core/CLI source 的 SHA256：

```text
097ed57f97ed9d22ff0919e75bc116237877b84e7b1e78ef505cce7f6d311b19
```

演算法是 manifest 順序中的 repo-relative path + NUL + actual bytes + NUL；必須用 `evidence/candidate-02-source.json` 的實際 files 清單核對，不能拿 Git HEAD tree 或另一組檔案計算替代。

修復後 process-instance 讀取包住 initial SCK 到 final signing/AX/CG；拒絕同 PID/signature/frame 卻已替換的 process。保留實際 post facts、嚴格 AX target 綁定、一次 CG snapshot 的唯一 owner/window/layer/frame 檢查、finite positive geometry、0.5 point frame agreement、包含最後讀取的 deadline。Security signing 只讀 requested PID，失敗不能退回 caller 身分。

既有實際檢查：focused **22/0**、Swift full **268/0**、replay **20 fixtures PASS**、build/provenance/diff exit0。這些是 10/4 已執行的 source-bound 結果，不是交接編寫時重跑的新結果。

第一次 independent Acceptance 的 timing FAIL 保留；第二次修復先以四個 replacement point 重現 1 test / 8 assertion failures，再修復，第二次 Acceptance PASS。此根因已用 2 次實作嘗試，不能換新文件重置。

### 3.3 真實 native capture / OCR 診斷

位置：`harness-development/rev28-native-capture/TASK-b9b7bfc7bf1e433ab26b78f7af9e5188`。

`evidence/verified-outcome.json` 記錄 actual validated bundle：654×1286 PNG、scale2、geometry residual0；process/signing/AX/SCK/CG coherence、deadline、same-frame OCR 與 structural candidate 綁定通過，精確 canonical group/date/57 唯一匹配。

這只證明當時一張 primary frame 的 capture/OCR 路徑。沒有證明 current-composer 全套 calibration、popup ownership、遮擋、chooser 或可重用 end-to-end。當時 PID49988/window4320 等識別值現在只有歷史價值，不能當即時 targeting。這個 diagnostic 沒有輸入 LINE、Save All 或修改 production 權利。

### 3.4 真實 CUA 單一相簿備份已完成

位置：`harness-development/rev28-project-backup/TASK-45ee0a78972048b787c7e3ded76f2e31`，下文稱 **BACKUP_TASK**。

獨立 Plan Review PASS → machine Handoff 與 contract 位元組一致 → reviewed 新 config/state 初始化 → single owner → 空的專案內 destination → same-frame card binding → metadata click → album detail 日期/57 MATCH → 真實 Save All 校準及安全關閉 → 新 intent write/read-back → 同一 uninterrupted execution 的原子 menu action → 精確新 destination → 下載 → filesystem/decode → terminal registration/release → product verify-only → 獨立 A1 PASS。

本輪實際結果：

- **57 個 JPEG，共 17,924,900 bytes**。三份完整 inventory（至少 5 秒間隔）一致；沒有 zero-byte、partial/temp、unrecognized、子資料夾或其他異常。
- 全部 ImageIO 完整 RGB/pixel 解碼成功；獨立 reviewer 再解碼、核對 SHA，檔案不變。沒有宣稱與伺服器原始照片逐張相同、原始解析度或唯一內容。
- Save All **一個 logical invocation**，folder confirmation **一次**；原始 host call/completion 與實際 chooser/download 圖片已保留。不是 OS delivery count 或簽章 provider receipt。
- state revision16 在同一 serialized atomic commit 登記 VERIFIED/fingerprint、清除 `active_writer_id` 與 `context_lock`，精確 read-back 成功。`current_run_id` 仍指向該 terminal run 是有效狀態，不要因此重開/清空它。
- 產品 `verify-only` exit0：filesystem/registry **PASS**、source **CONFIRMED**、state **EXACT**、artifact read-back **PASS**。
- 獨立 reviewer 檢查 664 項 schema/source/state/content/preservation assertions，以及 actual 原始 card/menu/chooser/download evidence；A1 PASS。
- 保留 34,623 個先前檔案/mode、24,536 個歷史檔案及集合、原 HEAD/branch/index。這是當時觀察，後續此文件 commit 合法改變 HEAD/index，不必回退才能符合舊 preservation receipt。

單一相簿 task 的六項狀態是：

| Status | 值 |
|---|---|
| PRIMARY_OUTCOME_STATUS | ACHIEVED |
| IMPLEMENTATION_STATUS | COMPLETE |
| CORE_ACCEPTANCE_STATUS | PASS |
| REQUIRED_VERIFICATION_STATUS | PASS |
| INDEPENDENT_ACCEPTANCE_STATUS | PASS |
| TASK_CLOSURE_STATUS | DONE |

**整套 native 流程仍 PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED、TASK_CLOSURE_STATUS=IN_PROGRESS。** 其餘項目須由新的 Plan/實測按 scope 分別核定；不能套用單一相簿的 DONE，也不能把已證實的本機修復/檔案 PASS 抹掉。

## 4. 還沒解决的問題、已知根因與未知

| 問題 | 已有證據 | 接手時要釐清 |
|---|---|---|
| CUA 畫面漏掉浮動 menu | 實際輸入返回、使用者看到選單；工具擷取仍沒有 popup。後以完整桌面 PNG + offline OCR 確認五列及 Save All | 是 provider/window capture 邊界、popup surface 歸屬，還是不同路徑缺 collector？原因未實測證實 |
| FROZEN_CAPTURE_GEOMETRY | `PhaseAEvidence.swift` condition5 對合法 config/frame 仍回 UNKNOWN，原因是未提供 bound current-composer native calibration observation | 定義並蒐集直接 current-composition 證據；不能只把 UNKNOWN 改成 PASS |
| POPUP_OCCLUSION_ASSUMPTIONS | condition10 的 candidate/frame containment 不證明 ownership/topmost/無遮擋，故保持 UNKNOWN | 實測 popup/overlay census、ownership、可操作表面與畫面/epoch/source 綁定，或提出真正等價且經審查的設計 |
| 原 native authority | 舊 GoalSlot、ledger/anchor/run identity 與 budget 有約束；目前 entitlement/consumption UNKNOWN | 僅使用已存在的專案內授權紀錄做唯讀因果核對。不能尋找或採用使用者禁止的外部 root；不足時提出精準 recovery 決策 |
| 可重用 native E2E | 有 local tests、一張 native frame、一次 CUA 備份；沒有以目前 native composition 完成全套 required acceptance | 新 Plan 定義真的產品入口、每一步 oracle 與 final evidence，而非拼接不同路徑的 PASS |
| 中斷續跑安全 | 已有局部反例/持久化檢查與不可重試 intent；CUA skill 明示 crash-safety 未被完整實測 | 隔離資料/故障注入測試真實入口與各 commit/effect 邊界，不使用 live state 或已完成相簿再觸發 Save All |

`rev28/Sources/rev28ctl/main.swift` 的 live-preflight 組裝 `captureConfiguration=primaryWindow`、`includeChildWindows=false`、`ignoreShadows=true`；Phase A producer 提供 frozen config/frame facts，尚沒有足夠的直接 native calibration/occlusion 證據。這是具體閱讀入口，**不是**已證明 `includeChildWindows` 就是全部問題的根因，也不授權直接改 flag 或任意擴大截圖範圍。

前輪必要的人提供完整截圖與依相同像素尺寸的平移校準，只適用那次 CUA run。它證明當時正確 menu row，不能升格為 native collector PASS、全自動能力或下一輪座標。歷史 click point、safe-close point、1200ms menu wait 與旧窗口大小均不可直接 replay。

兩個已安全恢復且必須保留的 runtime errors：

1. 校準期 input 被拒絕：`The user changed '/Applications/LINE.app'. Re-query the latest state with get_app_state before sending more actions.` 先重新觀察，有限校準 retry 在 intent 前完成，沒有重送 Save All。
2. Chooser paste：`Computer Use server error -10005: Timed out waiting for the application to read the clipboard.` 新 AX/visual 證實欄位未生效，沒有 Return；在已識別的 `PathTextField` 使用公開 supported `setValue` 成功，再核對完整 path、Return 後 leaf、OKButton，僅確認一次。這不是 hidden AX workaround，也不能把 timeout 一律當作 NO effect。

## 5. 接手閱讀順序與產品入口

1. 本文件置頂 prompt、目前對話適用的 AGENTS.md/Harness global contract；不要套用舊 V4.3.1 文件來執行新 task。
2. BACKUP_TASK 的 `acceptance.result.json`、`closure-advisory.json`、`backup-result.md`、`evidence/terminal-validation.json`，接著核對當前 config/state；progress 只看最後更新，早段是 append-only 歷史。
3. Fresh repair 的 `acceptance-02.result.json`、`evidence/candidate-02-source.json`、`plan.md`；先驗 bytes，再認領已接受的 source。
4. Native capture 的 `evidence/verified-outcome.json` 與必要 source/image/OCR binding；不要先掃所有 .build 或 giant start-snapshot。
5. 第一輪 `commit-review.md` 與其 acceptance，只在追該已修根因時讀相應反例。
6. 新修復會用到的實際 product 檔案；其餘歷史只沿精確引用追查。

| 路徑 | 用途 |
|---|---|
| `rev28/Sources/Rev28Core/Observation/NativeObservationSession.swift` | 新鮮 bundle、process/AX/signing/SCK/CG/deadline 閉合驗證 |
| `rev28/Sources/Rev28Core/Identity/ProcessCodeIdentity.swift` | requested PID 的 code identity |
| `rev28/Sources/rev28ctl/ProcessIdentity.swift` | CLI process identity acquisition |
| `rev28/Sources/rev28ctl/main.swift` | native composition/live-preflight evidence producer 與 CLI outcome |
| `rev28/Sources/Rev28Core/Composition/PhaseAEvidence.swift` | per-condition PASS/FAIL/UNKNOWN、current missing facts |
| `rev28/Sources/Rev28Core/Composition/ComposedNativeAdapter.swift` | 觀察、fresh localization、readiness 與 pre-save composition |
| `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift` | gated click、hover 後驗證、durable-before-effect |
| `rev28/Sources/Rev28Core/Transaction/LiveExecutionEngine.swift` | pre-save/Phase B state transitions |
| `rev28/Sources/Rev28Core/Transaction/PersistentTransactionOwner.swift` | ledger、reservation、authority、attempt accounting |
| `rev28/Sources/Rev28Core/Transaction/GoalSlot.swift` | 不得以新 run/destination 繞過的 persistent goal identity |
| `src/line_backup_acceptance/` | 當前 Python state/source/filesystem verifier；與 native Swift ledger 不可混稱同一 authority |
| BACKUP_TASK 的 `operator.py` / `prepare_intent.py` / `prepare_finalization.py` | 此一次 CUA run 的 task-local serialized state helpers，不是已整合的 production native workflow |

Skill：`/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md`。Startup 讀 `references/state-contract.md`；GUI 前讀 `references/evidence.md`、`references/state-machine.md`、`references/ui-procedure.md`；驗證讀 `references/verification.md`。第一次使用向使用者說明；技能流程不替代現在的授權與 reviewed Plan。不得因此重新要求已明示的新備份 root。

Pinned Harness release：

```text
/Users/hsiaojohnny/.codex/harness-releases/4.7.0/1bf92f52081df904cf30e1da488734643ee5ec3603464b4bf81b566263ec670d
/Users/hsiaojohnny/.codex/harness-runtime/4.7.0/.venv/bin/python
```

資源相對此 release 解析：`policies/v4.7.0/workflow-routing.md`、`schemas/v3/`、`templates/v4.7.0/runtime-defaults.json`。角色模型設定與語意分開；預設檔作配置依據，不假造實際 model/session receipt。新 task 不能 resume 舊 v4.6 lineage；v2/更早 state 唯讀。

既有新 v3 任務的 controller `state.json` 多仍 `next_stage=PLAN`、`run_ids=[]`，因 native stage admission 不可用。正式 role/evidence 是 **advisory** 審查紀錄；不可手動改 controller 宣稱已 native-admitted。release verification、檔案 hash 與 post-run audit 都不是 task acceptance 或 OS sandbox/network-denial 證明。

## 6. 首次接手檢查與下一個修復計畫

首先只做本機檢查：

```bash
cd /Users/hsiaojohnny/Documents/ChatGPT/Line_backup
git status --short --branch
git diff --cached --name-only
git log -5 --oneline
```

核對本文件第 8 節的 critical hashes，讀 strict state：one terminal VERIFIED run/fingerprint、retry=false、owner/context null、revision16。依既有 source manifest 逐檔 SHA 與 aggregate material 重算。文件交付後 HEAD/index 改變是預期，不能拿舊 receipt 要求 Git 回退。資料/source 若有新差異，先記錄實際範圍與原因，不能自行還原使用者新改動。

完成 baseline 後，寫一份最小新 v3 continuation Plan，至少包括：

- 具體產品完成定義：正確 group/card/detail → 當前可操作 menu → at-most-once durable action → 正確 chooser → 穩定可解碼 files → exact source/state join → 獨立驗收。
- 一個可驗證的 root issue 及與舊問題/budget 的關聯；對已接受的 source 修復不重新開無差別重構。
- 現在尚未知的 capture/popup/current composition/authority，哪個能先用現有本機證據診斷、哪個需新的即時觀察。
- 字面 allowed paths、actual source/build bindings、真正受測入口、反例/故障注入與外部可觀察 oracle。
- 原始資料、live config/state、已 VERIFIED fingerprint 的保留，以及隔離測試根目錄。沒有真正必要就不改 protected schema/architecture/ledger/entitlement policy。
- 每個 gate 的 criticality/evidence role/closure requiredness、階段、實際 evidence、成功與停止條件；人工 OBSERVED 與 waiver 分開。
- GUI/live continuation 的具體授權與 freshness，成功後操作停止、真正下載後只 filesystem polling；不能把只讀名字視為保證 live-preflight 不會發出可逆導航 click。
- 若舊 attempt/authority 仍阻擋，要用精確 facts/unknowns/decision 給使用者，不能新 task 新 run 繞過。

先獨立 Plan Review，machine Handoff byte-identical，再實作。Reviewer 不參與待審 artifact 的實作；無 helper/writer allocation 可串行，capacity 不是委派義務。若 Plan 容許並實際可用，按 frozen capacity 與 registered scope/worktree receipt 規則使用，不自造 receipt。

同根因最多 3 次 evidence-bearing attempts；2 次沒有新資訊即升級，material blocker 更早停止。這是保留的收斂政策，不是每輪新增三次 quota。高推理 reviewer 只回一個 bounded action；同 approved scope 可用原授權，擴邊界需新 Plan/必要決策。使用者當前電腦可自由使用，直到真的要做 GUI 操作再請短暫配合。

## 7. 驗收標準與硬性停止條件

目前已證實的 268-test/replay/local PASS 不必為了文件或數量再重跑。新 source 更動後，先跑對該根因有意义的 red-to-green 與 focused checks，再執行 reviewed 必要整合/全套檢查。既有命令紀錄可以參考，不覆寫既有 log/output。

中斷/恢復至少需驗證真正入口在 intent write/read-back、dispatch boundary、chooser confirmation、download、final registration/release 各邊界的 fail-closed 行為；loaded intent 不給新 Save All 權限，owner 字串不是 uninterrupted caller 證據，UNKNOWN effect 不重送。完整列出失敗/未知，不靠 scenario fixture 寫死 PASS。

Native current-composer acceptance 必須使用當前 native source 的直接 retained/bound observation；舊 NSOpenPanel fixture、手工 config bounds、CUA 人提供 screenshot、candidate existence 或合法 frames 不足以替代。

若未来真正需要測新的相簿或不可逆動作，先提出最小明確 scope 與 reviewed plan/授權；不要用這個已 VERIFIED 的 57 張作 extra canary 或再次下載。新資料夾永远位於本專案 backups 的現行 config boundary，適當命名；不以新目的地繞過 duplicate/unresolved fingerprint。

以下任一情況停止相應操作，保留實際 evidence 與已證實的其他成果：

- 目標 group/date/count/card/fresh frame 不匹配、partial card、遮擋、menu ownership 或 geometry 不明。
- persisted authority、slot/ledger/anchor、run/source bindings 不足或衝突。
- root/state 缺失，不符 strict schema，或已有 unresolved intent/owner。
- 已 dispatch 或可能 dispatch，但 effect 無法確認；不 retry、不清 barrier。
- 需改 public/security/data/requiredness/failure-propagation policy，而當前 Plan 未涵蓋。
- budget 已耗盡、沒有新資訊、超出 reviewed paths 或必要檢查/獨立 Acceptance 未通過。
- capability unavailable：如實交付 evidence packet，不換未授權工具、hidden AX、AppleScript、shell GUI automation 或猜座標。

不要 commit/push 整個 dirty worktree。此文件 commit 已明示授權；下一輪產品發布要依使用者新的交付範圍及 reviewed結果處理。禁止 reset/clean/stash/rebase/force push、修改其他 worktree、重開 A/B competition 或手動修 ledger/slot。

## 8. 精確證據索引與接手 baseline

以下 SHA 是本次交接編寫時實際重新讀檔計算；不是新測試結果。所有文件以本機實際 bytes 為準，檔名或 PASS label 本身不是證據。

| 檔案／manifest | SHA256 |
|---|---|
| `config/line_backup_config.json`（384 bytes） | `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362` |
| `state/backup_state.json`（71365 bytes，revision16） | `1093dd3065f7ce80ce4cfcb97081cabbb9b4334a53eeb77d1233985e5432acb9` |
| 第一輪 repair 的 `acceptance-02.result.json` | `abb8d891a24c01e43a65e16eb46e46cef9b1ca149a04a38b5867b58a430b1286` |
| Fresh repair 的 `acceptance-02.result.json` | `9d30c703cabdf83c8c32ae6896c58811fab6a7f78e42a751e4860527816eecb5` |
| Fresh repair 49-file current source aggregate | `097ed57f97ed9d22ff0919e75bc116237877b84e7b1e78ef505cce7f6d311b19` |
| Native capture 的 `evidence/verified-outcome.json` | `9e1dafdcf2d98d8d83936393a5a3fc076642841ff4fb093f3bc98d2dc2a50cee` |
| BACKUP_TASK 的 `acceptance.result.json` | `0439be76a89f60074411f4fa77bb21fd099a18d73c3ed0ca458c8fdf227ed03f` |
| BACKUP_TASK 的 `closure-advisory.json` | `483da098e81d9523904c6c83bdd88f406818de09bb8e20b495f69f097d606be6` |
| BACKUP_TASK 的 source aggregate（Core/CLI + verifier + task-local helpers） | `0647382e21ae18f04abfe11f936d64065389c7504d39deefce079b03ababacc9` |

BACKUP_TASK 內重要相對路徑：

- `plan.md`、`plan-contract.json`、`plan-review.result.json`、`handoff.json`：凍結的新 root 單一 CUA backup 計畫及正式 review；此 scope 已完成，不能用作下輪 native repair 批准。
- `source-identity-join.json`：當前 exact source/group/fingerprint/destination/run join；final VERIFIED event 與 registry 使用相同 evidence ref，不要自行重寫。
- `evidence/current-source-binding.json`：目前 composite source/binaries manifest；與 Core-only 49-file SHA 是不同集合。
- `evidence/state-r000001.json` 到 `state-r000016.json`：append-only state receipts；不可因新 session 清空。
- `evidence/verification-receipt.json`、`inventory-001.json` 到 `inventory-003.json`、`image-decode.stdout.json`：57 張 content/MIME/hash、穩定性及完整解碼。
- `evidence/product-verifier/result.json` / `manifest.json`：實際既有產品 verify-only 下游鏈。
- `evidence/user-desktop-menu-open-20261005.png`、`user-calibration-safe-closed-20261005.png`、`menu-ocr-20261005.json`：當時使用者畫面 OBSERVED 與 actual offline OCR；private evidence，不能變成 current observation。
- `evidence/cua-original-session-trace-manifest.json` / `cua-original-session-trace.jsonl` / `cua-original-*.jpg`：從 actual host session 依 call ID 原樣保存的 call/completion/回圖；原 source prefix、行號、bytes/SHA 綁定。接手不必掃全域 .codex sessions，原圖/trace 已在專案。
- `evidence/acceptance-final-assessment.json`、`acceptance-audit.json`、`acceptance-trace-audit.json`、`acceptance-original-card-manifest.json`、`acceptance-decode.json`：獨立 reviewer 的实际核對與原始 card 證據。
- `evidence/after-acceptance-preservation.json`：相簿結案前已驗證的保留性；其當時 HEAD/index 是歷史基準。

舊 native immutable authority 只能在已存在的本專案紀錄中沿精確引用查閱；歷史入口 `.agent/tasks/T20260925-0647-01-rev28-native-closed-loop/` 的 canonical Plan/Handoff 及 `phase-a/attempt-01/RUN-20260930-103002-01/`。讀取不授權續跑。PRIMARY_NATIVE_COMPOSITION 3/3、attempt-01 REFUSED/exit77 等歷史事實保留，當前實機 state/entitlement 不得靠其舊計數推斷。

## 9. Git 交付與工作樹保留

本次文件提交只包含根目錄 `handoff.md`。詳細提交訊息保存於本機 `harness-development/rev28-handoff-delivery/TASK-fad90a2bf8e14a6dbb81dc5412cc7839/commit-message.txt`；實際 commit/push 結果見同 task 的 evidence/implementer result，提交後也可 `git log -1 --format=fuller -- handoff.md` 查看。

交接前 staged set 為空，branch/origin 為上述分支。21 個既有 tracked modified 檔案，以及未 tracked 的 `ProcessCodeIdentity.swift`、對應 test、`harness-development/`、`config/`、`state/`、`backups/` 均保留原樣、未包入這次文件 commit。已接受的產品狀態是本機 worktree bytes，不是目前 Git commit tree；**全新 clone 只有此文件與舊 committed source，無法直接重現本機已接受結果。** 若改用另一台機器/clone，先另行規劃明確的程式與證據移交，不能假稱 artifacts 存在。

接手完成新的修復與驗收後，回報具體 root cause、最小修改、真正執行的檢查、保留的未知與六個 status，以及是否真的需要使用者做下一個動作。沒有必要的介入，就繼續在授權及 reviewed scope 內處理，不再反覆要求使用者把 LINE 開到前景。
