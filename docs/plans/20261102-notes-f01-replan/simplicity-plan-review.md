# F01 計畫簡潔性審查

## 本角色結論與精確候選

**判定：PASS，僅限計畫階段的簡潔性。** 本版把修正放在已定位的「原件卡片→page rows」轉錄邊界，沿用既有 statement／v2 evidence-pack，未引入新的 CLI、事件、識別鍵或控制器。未發現有具體證據支持、且會違反最小充分目標的重大可避免複雜度。必要的來源核對、部分卡片處理與資料保護仍有明確對應。

本結果不證明 F01 已修復、流程足夠可靠、計畫已獲 Owner 採納或可開始下載。能否改善實際 Agent 行為，仍須由首切片、C1–C7、獨立 Acceptance 與適用 G-F01 提供證據。

- 角色／checkpoint：Simplicity Reviewer／plan。
- Repo／worktree：`Line_backup` 核心工作目錄；實體 Git root 與 cwd 已核對，完整路徑留私有命令紀錄。
- Branch：`feature/line-notes-media`。
- 唯一候選／審查起始 HEAD：`015d96ba4f8448b36d7d88b35b413c22b01f91a3`。Owner 在本 Session 明確指定該版本的 [plan.md](plan.md) 與 [handoff.md](handoff.md)，不審查其他候選。
- 候選差異：`f427472335e611ca0efdd8b99011d87d7f7beaa9..015d96ba4f8448b36d7d88b35b413c22b01f91a3` 僅新增本目錄的 plan／handoff／progress；它是規劃提交，沒有 F01 產品修復 diff。
- 起始 tracked、index、非忽略 untracked 乾淨；遠端同分支精確 HEAD 與候選一致。其他 worktree 及忽略資料保留。
- 獨立性：本主 Session 未參與該候選起草或其產品實作；本輪只寫本報告及私有審查／交付紀錄。後續依 Owner 指定使用的 Luna helper 僅協助 Git 交付，不簽發本報告、獨立審查或 Acceptance。

| 唯一候選檔案 | SHA-256 |
|---|---|
| `plan.md` | `58e38a4755717fc3c6ac39b82c49fd3c2c65c45e8bc662e05b0158e6f3620dfc` |
| `handoff.md` | `6ab8d3bb102ecd7329c7da3b0997e72b21ba8d3ad79c7dc6ea92a8392eca07b8` |

候選以 `git show <完整 SHA>:<path>` 的 bytes 核對現存檔案；不把文件中 Planner 的起始 f427472 當成待審計畫版本。本報告後續提交不擴張被審版本。

## 審查來源與責任界線

已讀指定 4.9.0 Simplicity Reviewer prompt、同版 workflow-routing／subagent-model-policy／role-report template、專案 AGENTS，以及：

- 本候選 plan、handoff、progress 與實際 Git 差異。
- [F01 診斷](../20261102-notes-f01-scan-review/issue-analysis.md)及[測試報告 F01](../../../測試報告.md)；使用公開去識別描述，未重讀私人截圖、真實帳本或照片。
- [原 replan](../20261101-notes-all-issues-replan/replan.md) D.4／T5、其[現行交接](../20261101-notes-all-issues-replan/handoff.md)，及 [S3 計畫](../20261102-notes-fieldtest-review/plan.md)／[交接](../20261102-notes-fieldtest-review/handoff.md)，核對相容、資料與實機 gates 沒有被本版 STANDARD 免除。
- 現行[記事本 Skill](../../../.agents/skills/line-notes-agent-cua/SKILL.md)、[GUI 盤點](../../../.agents/skills/line-notes-agent-cua/references/gui-inventory.md)、[證據範本](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md)；[notes.py](../../../src/line_backup_batch/notes.py) 的 `_validate_page_overlap()`、`page()`、`finish_scan()`、`evidence_correct()`，及 [overlap／completion 測試源碼](../../../tests/test_notes_regressions.py)、[evidence 模組](../../../src/line_backup_batch/notes_evidence.py)。

專案根目錄沒有指定的 `policies/v4.9.0/`；首次讀取回傳 exit 1，隨後以 `rg --files` 找到並讀取既有 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 同版檔案。沒有新增或恢復退役 Harness。

## 機制對需求的映射與複雜度判斷

| 提議機制／位置 | 對應需求或必要保障 | 成本、較小替代與判斷 |
|---|---|---|
| plan A：先從原件列完整／部分卡片，再建 rows | 診斷記錄原件含 P06、輸入漏 P06；必須把獨立可見卡片逐一帶入清單 | 多一份來源逐卡紀錄及原件區域定位，但直接針對缺口；只增加總數／overlap 聲明無法檢出頁內漏卡。沒有新 parser 或 identity 系統 |
| plan A／C3：片段連結、高卡片與待解項 | 小步捲動可能呈現同卡多段；既要避免漏篇，也要避免把片段算成新篇 | 需保存相鄰脈絡，且無法唯一對應即停；已有 GUI reference 要求部分卡片與共同錨點，本版將提交前條件說清楚。不能以刪除片段紀錄求簡化 |
| plan B：一 viewport 為原則，僅為解卡的連續補觀察可共頁 | 診斷中的多 viewport 聚合具有來源難以追查的成本；但高卡片不宜被硬切成假 row | 窄例外保留正常補接，不要求每次截圖一律新增 page；不另造空頁、重複貼文或新的頁格式。屬限制聚合範圍，不是額外盤點模式 |
| plan B：page 前雙向核對，提交後附回傳 key／事件讀回 | 同時檢查來源缺 row、row 無來源、誤合併與重複計數；key 不證明畫面齊全 | 每卡／row 多一次對照，但兩個方向驗證不同錯誤；沿用同一 page statement／assets，不維護另一份公共帳本。只核對 row 聯集不能取代 |
| plan C：最後補觀察後直接重讀原件，對照已提交 rows 與有序聯集 | 結束前不能只信先前自行整理的清單；F01 即為自洽而不完整 | 再讀已保存原件與 rows，沒有要求第二輪完整 GUI 重掃。與 page 前檢查分別守住提交、結束兩個邊界；不能將複核改成重讀對帳表便宣稱等價 |
| plan C／D：已提交頁缺口、來源變動或歧義即停 | 不用新 scan、更正 evidence、改 key 或改舊 COMPLETE 掩蓋缺口；保護原歷史及 UNKNOWN | 犧牲自動前進是維持現有追加式與禁止重送邊界的必要代價。`evidence_correct()` 不改 page 成員；本方案沒有增加不可證實的自動修補能力 |
| 三份產品文件，GUI reference 為唯一操作本文 | Agent 需要入口摘要、實際方法與既有 statement 的記錄例子 | 三處分別有既有用途；plan 要求用連結避免重複本文，不新增手冊模式、CLI、schema、測試框架或全域政策。未發現可安全刪去一處而仍維持操作與證據入口一致的具體理由 |
| C1–C7、首切片審查、獨立 Acceptance、G-F01 | 正常鏈、同時刻、部分卡片、照片／影片中段漏篇、缺 overlap、變動及已知失敗都需可核對結果 | 案例覆蓋不同失敗軸；不要求新增單元測試或字串快照。合成與實機證據分開，原 CRITICAL gates 保留，沒有以文件演練代替功能接受 |

上述「足以保留」是簡潔性設計判斷，不是行為案例已通過。沒有要求擴充下載種類、處理 F02–F18、補寫舊帳本或增加機械 sensor。

## 原始缺口與候選界線的交叉核對

**本輪從源碼確認的事實：**`page()` 依提交 identities 產生 rows；`_validate_page_overlap()` 檢查前頁尾／次頁頭與重複鍵，未從畫面取得必填卡片集合。`finish_scan()` 要求同 Session、存在 pages、頂底旗標，再對既有 rows 取有序去重聯集。現有相關測試檢查給定資料的 overlap 形狀與 completion 聯集，不能證明保存畫面沒有漏卡。evidence 模組亦明示 bytes／context 不證明 GUI 真實。

**本輪引用的前輪事實：**F01 診斷記載舊 page 2 原件含 P06、rows 從 P05 接 P07，並記錄舊 14／新 15 篇均可符合內部重播。這是前輪診斷與 `OBSERVED` 來源，本輪沒有重新目視或重播該私人資料。

**推論：**在不改公共介面及帳本語意的限制下，先分離來源列卡、再雙向核對，能讓已觀察卻未入 rows 的缺口有明確阻止點。它是值得驗證的最小流程候選。若 Agent 同時漏看原件與漏寫對帳，CLI 仍可能接受不完整輸入；計畫已在「替代方案與可保證界線」明示，不是被本審查補上的例外。

固定兩次重掃或比較總數不能排除同樣漏篇；只加 coverage 布林聲明也可能與 rows 同漏。要求 CLI 自動辨識卡片、OCR parser 或獨立總數 oracle，會引入本輪沒有可靠來源與相容計畫的新機制，不能以簡潔性 finding 強迫擴張。若 Owner 改選機械拒絕目標，須另定範圍，不由本 PASS 批准。

計畫沒有宣稱 GUI／CLI／外部 writer 共享原子快照；hash、讀回與本機鎖的保證範圍有明確上限。來源變動後保留未完成，不靠無限重查維持完成承諾。

## Findings、非阻塞建議及未知

**阻塞 findings：無。** 未找到可指出具體新增成本與必要保障等價替代、足以要求 `REVISION_REQUIRED` 的機制；亦無缺失的唯一候選或必要計畫來源而需 `BLOCKED`。

非阻塞建議：實作可讓 page 對帳與 finish 結果引用同一份逐卡紀錄及原件，只追加讀回引用與最終判斷，避免複製三份可能漂移的表格。這是 plan B／C 與單一操作本文方向的落地建議，不是新增接受條件，不要求改本版計畫。

未知及未涵蓋項目：

- 實際 Agent 是否能依新方法發現同時刻、跨 viewport 與中段漏篇；C1–C7 尚未實作或執行。
- 真實 LINE 是否可取得全部案例、G-F01 的授權與資料範圍；本輪無 GUI／帳本寫入授權，不執行它們。
- 完整歷史修復嘗試帳及未觀察的服務端變化；不因本 Session 重設嘗試次數，也不承諾零漏篇。
- 本報告不重驗私人診斷原件、真實完成照片、外部副本、F02–F18 或既有 UNKNOWN。既有其他 findings／外部 gates 不因本 PASS 消失。

## 實際檢查與結果

私有任務區為 `.local/line-backup/tasks/20261102-notes-f01-plan-simplicity/`；`commands.jsonl` 保存重新執行的關鍵 argv、cwd、stdout、stderr 與 exit，`source-manifest.json` 保存 16 份專案來源 bytes／SHA-256。原始讀取與本輪檢查不操作真實帳本或 LINE。

| 實際命令／檢查 | 結果與限度 |
|---|---|
| `pwd`、`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | preflight exit 0；根目錄、乾淨狀態、分支與候選確認，其他 worktree 保留 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-f01-plan-simplicity/check_review.py baseline` | exit 0，24 項核對成立；逐檔 `git show` bytes、基線、遠端、Python 與 worktree 證據留 `baseline-checks.json`。這是來源檢查，不是產品測試 |
| `git diff --exit-code 260a49612cb3f7570a57f135921b4101e2c8ee99 015d96ba4f8448b36d7d88b35b413c22b01f91a3 -- src tests .agents AGENTS.md` | exit 0；候選仍沿用實機受測產品，沒有已交付的 F01 產品修復 |
| `git ls-remote --heads origin refs/heads/feature/line-notes-media` | exit 0；審查前精確遠端 HEAD 為唯一候選 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-f01-plan-simplicity/check_review.py report` | exit 0；來源未變、報告 UTF-8／換行／空白／連結／六狀態、唯一新增報告與 Git diff 檢查成立，結果留 `report-checks.json` |
| 產品三項最小回歸、C1–C7、G-F01、真實 GUI、獨立 Acceptance | 全部 `NOT_RUN`；本輪只審規劃與源碼，不執行實作、產品測試或外部任務 |

本機環境為 macOS、zsh、`/usr/bin/python3` 3.9.6。純來源檢查不會將前輪 73／136 tests、原 A0 或實機結果升格到本版。Git add／commit／普通 push 依 Owner 本輪授權另存實際輸出；提交後核對 message body，推送後核對遠端精確 HEAD，Git 成功不代表產品接受。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: F01_PLAN_SIMPLICITY_PASS
IMPLEMENTATION_STATUS: FIX_REQUIRED; PRODUCT_UNCHANGED_THIS_ROLE
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: REVIEW_SOURCE_AND_DOCUMENT_CHECKS_PASSED; PRODUCT_BEHAVIOR_AND_GUI_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_OWNER_ADOPTION_IMPLEMENTATION_AND_APPLICABLE_ACCEPTANCE
```

由 Owner 決定是否採納此流程候選，然後在另一個主 Session 啟動 F01-S1 Implementer，攜唯一候選 plan／handoff、本報告與 F01 診斷；本審查不自行啟動它。首切片交付精確 candidate／diff／V1／V2 後，由 Owner 啟動 implementation Simplicity Review，再安排獨立 Acceptance 與適用 G-F01。若首切片已是最終候選且審查沒有剩餘實作，不重開無必要 Implementer。

改候選、改為機械契約、擴白名單或變更資料／授權／驗證邊界時，由 Owner 決定適用重審。三份產品文件、C1–C7、原資料保護與 CRITICAL gates 依其原版本維持，不以此 PASS 豁免。交付本報告與已授權 Git checkpoint 後，本正式角色停止，不跨角色修復、重測或結案。
