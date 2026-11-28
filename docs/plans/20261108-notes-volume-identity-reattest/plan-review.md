# 記事本 list directory 重新見證：CRITICAL 獨立 Plan Review

## 本角色結論

**REVISION_REQUIRED。** 草案有一項可修正的協議矛盾：它允許在尚未建立 v3 intent 時再次重新見證，卻要求舊完成物的原始 device 等於上一次轉接後的 binding device。第一次轉接後，這兩個值依草案定義必然不同，因此第二次轉接無法成立。

本判定只針對計畫，不是產品實作失敗或原始備份的新拒絕。其餘範圍、授權、保護與驗證設計未發現另一項計畫阻塞；但下列 B1 修正並由 Owner 決定適用重查前，不應把草案核准為可實作版本。

## 請求、精確版本與獨立性

| 項目 | 綁定／結果 |
|---|---|
| 本次請求 | Owner 在計畫 Simplicity Review PASS 後，明示啟動 CRITICAL 獨立 Plan Review；另授權審查成果的 commit／push 與指定 commit 訊息 helper |
| 使用者目標 | 為目前 list directory 的 device-only 漂移提供精確確認、追加事件、重新完整盤點後接續既有 OPEN_BATCH 的路徑，不改寫歷史或解除 UNKNOWN 保護 |
| 非目標 | 實作、修訂草案、重測產品、真實帳本轉接、LINE GUI、下載、獨立 acceptance、合併或結案 |
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`；目前主 worktree，其他 worktree 未修改 |
| 分支／審查起始 HEAD | `feature/line-notes-media`／`0e681e45a8a6812f9c9dc1061c1b20379a1b894b` |
| 受審計畫版本 | 草案 v1，commit `1ac98575d7296cfd943b871ff24c29ed467dc47a`，tree `b3688cd17a2d973e2925a16f85e90c3e9b3ea347` |
| plan SHA-256 | `661a9f680f527fb52e50f3ed009b952e104879c177b110074833bffc5e8c6a27` |
| handoff SHA-256 | `99ad7111bea2430b600b76b896e5fee5f5e78fe45746f21a96a30abe4cc62186` |
| Simplicity Review | `0e681e45a8a6812f9c9dc1061c1b20379a1b894b`；報告 SHA-256 `4617b42c24bb13b77fd61844e7dfaab7743af3766811fb453aeb2325d2179872`；只代表簡潔性 PASS |
| 審查獨立性 | 本主 Session 未撰寫或修改受審計畫、handoff、診斷或產品，也未參與其設計決策；本輪只有唯讀審查、正式報告及私有檢查產物。不宣稱平台或 OS 隔離 |

目前工作樹中的 plan／handoff 與上述受審提交的 blob hashes 相符。`1ac9857` 相對 `9027d8e` 沒有產品、測試、Skill、手冊或邊界文件差異；至本輪起始 HEAD 仍無這些差異。本報告不會把後續版本納入原審查範圍。

## 審查範圍與需求映射

唯讀對照 `plan.md`、`handoff.md`、`planner-report.md`、`issue-analysis.md`、`problem-report.md`、`progress.md`、計畫 Simplicity Review、專案 `AGENTS.md`、同版本角色 Prompt／policies，以及 `notes.py`、`notes_evidence.py` 和現有 notes 測試布局。未讀取或修改真實帳本、媒體、active hint，未操作 LINE。

| 使用者目標／限制 | 計畫對應 | 審查結果 |
|---|---|---|
| 只解除已定位的 list directory device gate | `plan.md:31–43`、`:110–118`；現行 `notes.py:2183–2200` | 方向對應根因；舊 completion／candidate／staging／availability 不使用新 resolver，避免擴大信任轉接 |
| 保留既有 OPEN_BATCH 與精確 restart scope | `plan.md:49–57`、`:78–85`、`:120–131`；現行 `notes.py:3560–3567`、`:3711–3806` | 有明確 confirmation ref、generation、scope digest、無 v3／candidate／activation 的適用限制；不得新建第二批 |
| UNKNOWN、LOCAL_CHANGED 與舊完成保護 | `plan.md:52–57`、`:108`、`:122–131`；現行 `notes.py:3231–3315`、`:3323–3365` | reattest 不產生 STOPPED、不升格 VERIFIED_PRESENT、不解除 UNKNOWN；scope 外異常仍拒絕 |
| 精確認可、追加事件與 crash 查回 | `plan.md:59–100`、`:133–149` | preview／confirm／replay、tip／witness／evidence 綁定與單筆事件要求具體；但連續轉接受 B1 阻塞 |
| 歷史可重播與相容界線 | `plan.md:110–118`；現行 `notes.py:780–818`、`:1035–1608` | 要求 prefix 驗證、event_ref／raw hash 分離與舊 binary 拒新 kind；不把新版可讀舊帳本寫成反向相容 |
| 新鮮完整 recovery scan | `plan.md:118`、`:122–124`；現行 `notes.py:2328–2353`、`:3711–3733`、`:4887–4919` | 明定 scan START 晚於 reattest，而非只看 COMPLETE；保留 current session、coverage、scope 與媒體身分 gates |
| CRITICAL 人工關卡與授權 | `plan.md:9–11`、`:151–190`；`handoff.md:19–39` | 計畫與實作 Simplicity checkpoints、獨立 Plan Review／acceptance 均有人工 owner；Owner 尚未接受 trust 或授權實作，不被本審查預填 |
| 可驗證性與證據保存 | `plan.md:160–198` | S1 純讀、S2 寫入、T1–T10 有責任者與通過／停止條件；真實 volume 與日常 GUI 須另授權。B1 所需連續漂移案例尚未納入 |

## 阻塞發現

### B1：連續 reattest 的舊 device 比較基準互相矛盾

- **位置：** `plan.md:52` 要求至少一個 completion witness；`:80` 規定 `file_before` 逐字取原始 `completion.target_file`；`:87` 要求每份 old device 等於 `old_binding` device；`:112` 允許 `old_binding_ref` 指向前一 reattest；`:116`、`:124` 保持原 completion 與 LOCAL_CHANGED 不變；`:146` 又允許尚未進入 v3 時以新 preview／同意處理再次漂移。
- **問題：** 第一次轉接 `D0 → D1` 後，有效 `old_binding` device 是 `D1`，但原始 completion 的 `target_file.device` 仍是 `D0`。草案又規定 `D0 != D1`。第二次轉接 `D1 → D2` 時，`:87` 因而要求 `D0 == D1`，與第一次轉接的不等式矛盾。舊 staging 的 `directory_before` 逐字取 v2 intent，也有相同問題。
- **影響：** 在第一次 confirm 後、第一個 v3 intent 前再次發生 device-only 漂移時，草案文字允許恢復，實際規則卻必因必要 completion witness 拒絕。這不是單純文件風格；它影響 crash／漂移恢復、有效 binding resolver 與事件驗證的一致實作。T1–T10 沒有涵蓋這個已明示支持的序列，無法以現有矩陣保證一致行為。
- **支持證據：** 現行 completion availability 在 `notes.py:3275–3304` 直接比對原事件的 directory／file device；草案明確不改寫這些原事件。因此不能把前次 reattest 的 `new_binding` 當成已同步改寫 completion witness。本發現是由固定欄位與事件不變量作出的邏輯推演，不需要真實資料或新下載。
- **最小修正方向：** 若維持最小首版，明定 v1 只接受沒有先前 `list-directory-reattest` 的帳本，再次漂移在 v1 一律停止，並同步收斂 `plan.md:112`、`:146` 與測試預期。若要保留連續 reattest，則須明定舊 completion／staging 在前次轉接後使用哪一份最新 witness 作為比較基準，並在 T2／T3／T4／T5 加入「`D0 → D1 → D2`、第二次漂移發生於任何 v3 之前」的正負例、replay 與 fresh-scan 檢查。兩條路線只能由 Owner 依能力範圍決定，本 Reviewer 不修改草案。

## 非阻塞建議

無。B1 是協議一致性與可驗證性問題，不是風格偏好；本審查不另增產品能力、文件或通用框架要求。

## 事實、推論、未知與未執行項

**事實：** 受審草案與指定 hashes 相符；Simplicity Review 已交付且僅涵蓋簡潔性；產品與測試在受審版本中未變。現行 list gate、completion availability、OPEN_BATCH、scan START／COMPLETE 與 restart intent 的原始碼位置已逐項核對。

**推論：** B1 由草案的 device 不等式、原始 completion 不變與連續 reattest 規則直接推出。修正前，不同 Implementer 可合理得到互相矛盾的事件合法性或 preview 行為。

**未知：** device 改變的外部原因、同一持久物件連續性、完美 clone、舊 UNKNOWN 是否晚到、真實完整 list 子項集合、其他 gates、controlled mount 及 LINE／跨 Session 實際可用性。草案已保留這些限制；本輪沒有消除它們，也沒有新的人眼觀察可標 `OBSERVED`。

產品單元／回歸測試、合成產品交易、真實帳本 preview／confirm、解碼、受控 volume、LINE GUI、下載、跨 Session E2E 與獨立 acceptance 全部 **NOT_RUN**。本輪沒有執行草案新增的 CLI，因為它尚不存在且本角色無實作授權。

## 實際命令、環境與檢查結果

工作目錄均為 `/Users/hsiaojohnny/dev/Line_backup`。私有檢查位於 `.local/line-backup/tasks/notes-volume-plan-20261108/critical-plan-review/`，不覆寫 Planner 或 Simplicity Reviewer 產物。

| 實際檢查 | Exit／結果 |
|---|---|
| `pwd`、`git status --short --branch`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list`、`git log` | 各 0；確認 repo、分支、乾淨起始狀態、HEAD 與 worktree；未整理其他 worktree |
| 初次讀 repo 根目錄 `policies/v4.9.0/workflow-routing.md` | 1；該路徑不存在。隨後以 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 的同版本文件完成核對，未借用其他版本或恢復退役 Harness |
| `git diff --check 9027d8e 1ac9857` | 0；受審計畫差異格式檢查無輸出 |
| `git diff --exit-code 9027d8e 1ac9857 -- src tests .agents AGENTS.md docs/LINE相簿備份_使用手冊.md` | 0；受審計畫沒有產品／測試／Skill／邊界文件差異 |
| `git diff --exit-code 1ac9857 HEAD -- <產品路徑與 plan／handoff>` | 0；本輪起始 HEAD 未改受審草案或產品 |
| `shasum -a 256` 與 `git show <受審 commit>:<path> | shasum -a 256` | 各 0；工作樹與受審提交的 plan／handoff／來源 hashes 相符 |
| `git ls-remote origin refs/heads/feature/line-notes-media` | 0；審查起始遠端 HEAD 為 `0e681e45a8a6812f9c9dc1061c1b20379a1b894b` |
| `cat`／`nl`／`sed`／`rg` 讀取角色 Prompt、同版本 policies／template、計畫、診斷、Simplicity Review、Skill 與相關原始碼 | 讀取命令完成；長輸出截斷後以較小行段重讀關鍵內容，未把截斷輸出當完整來源 |

完整版本／hash 輸出保存於私有 `source-and-version-checks.log`。上述檢查不是產品測試或真實環境驗收。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_REVISION_REQUIRED
IMPLEMENTATION_STATUS: NOT_APPLICABLE_THIS_ROLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_REVIEW_SOURCE_AND_VERSION_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_PLAN_REVISION_DECISION
```

## 人工交接

建議 Owner 攜帶受審 commit `1ac98575d7296cfd943b871ff24c29ed467dc47a`、本報告及 B1 的精確位置，決定是否在 Planner 主 Session 做有界修訂。最小路線是把 v1 明確限於首次 reattest；若需要連續漂移恢復，再核准相應 witness 基準與測試範圍。

草案實質變更後，由 Owner 決定適用的 Simplicity／獨立 Plan Review 重查。現在不啟動 Implementer、不執行真實 reattest／LINE、不把本報告當產品 acceptance，也不結案。本角色到正式報告與已授權文件交付為止。
