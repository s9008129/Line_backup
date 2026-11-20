# 需求澄清後的 Plan Review 與 Planner 交接

## 結論

**REVISION_REQUIRED（需要重規劃）。下一個角色：Planner，已由 Owner 明確指定。**

Owner 要的是「不論預期或非預期中斷，下次都能簡單繼續完成備份」。Owner 接受重新下載，並提出覆蓋前詢問使用者。舊計畫仍以證明原下載停止、收斂 UNKNOWN 作為重新下載的前提，且只允許文件修改，沒有設計使用者確認後的重新下載／覆蓋流程。因此不能照舊計畫直接實作。

下一步應由 Planner 把這個恢復方式規劃清楚，交付新版計畫。**不再要求 Owner 先替舊方案尋找 LINE 停止證據，也不以單純把此分支標成未支援作為滿足核心目標的交付。** 若遇到具體技術限制，由 Planner 說明限制、可行替代方案與需要的明確決定。

## Owner 最新意圖及本輪範圍

本輪依據是 Owner 在本對話中的原話：

> 我的核心意圖是要設計一個完善的機制，讓程式在中斷之後可以接續，尤其是遇到非預期的中斷事件時。我建議直接重新下載，然後詢問使用者是否要覆蓋所有資料，這樣比較單純，不要過度複雜化。

Owner 隨後要求重新 review plan、輸出結論及精確路徑，並明確指定：「我直接指定下一個角色為 Planner 的角色。」

可確認的設計方向：自動找回進度；重新下載是可接受的恢復方式；覆蓋須先讓使用者確認；流程簡單。需要 Planner 定義的細節是「所有資料」的實際範圍、確認時機、取代失敗或再次中斷時的處理。不能自行把「所有」縮成單一檔案，也不能擴成整個備份庫或永久帳本。這些應由計畫提出具體預設及使用者看得懂的確認內容。

本輪是需求變更後的補充審閱與交接，不是 Planner 實作。本 Session 已在對話提出暫存後取代的建議，故不宣稱對該新方向作獨立 PASS；新計畫仍須適用的獨立審查。沒有改寫舊 plan／handoff／審查報告，也沒有操作 LINE、真實帳本或媒體。

## 精確版本

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`。
- 分支：`feature/line-notes-media`；本輪起始 HEAD／查得遠端 HEAD：`9b29601b2c05715b3354911239ced058b59a0dc9`；初始工作樹乾淨，其他 worktree 保留。
- 受審 plan／handoff 共同提交仍是 `414e61db1cd42e85c27d1edeef3cbb06d77bc2c2`，與本輪入口 HEAD 的內容相同。
- plan SHA-256：`c69d2fd59ba460c9e48085a22d75e4b301880f300fdc13a74fb0dab296b0e763`。
- handoff SHA-256：`3a7a59e27f07d19fabfe658c3a35ce5ef4575f4c00b865f0f46703a4014adfac`。
- 舊 `plan-review.md` 的 BLOCKED／PR-B01 保留為舊方案的審查結果；它沒有因本輪討論被證明解除。本輪新增「需求已澄清、計畫不符新方向」的判定，**目前交接建議以本報告為準**。
- 舊 Simplicity PASS 只綁定原計畫，不自動批准新的重新下載／覆蓋方案。

## 需要修改的計畫缺口

以下 L 行號指原 `plan.md`。

| 發現 | 位置與證據 | 影響 | 最小修正方向 |
|---|---|---|---|
| PR-R01：恢復主路徑不符合最新意圖 | L45、76–92、119、124–125：只有停止或完成證據成立才可前進，否則保留 UNKNOWN。`notes.py:2646–2698` 也實際限制舊 attempt 須 STOPPED／NOT_SENT 才能重建 | Owner 接受重新下載並確認覆蓋，舊計畫卻仍可能永久卡在舊終態，沒有把簡單可用的恢復流程作為主要交付 | 以「找回進度→確認重新下載及覆蓋範圍→重新下載→驗證→保存新結果」為主要候選；定義對 UNKNOWN 的正式恢復處理，保留真實歷史，不虛構 STOPPED／NOT_SENT |
| PR-R02：文件限定與驗證條件無法承載新行為 | L11、23–36、109、113、121：不改 CLI／gate／資料語意，只改六份文件；沒有覆蓋確認、取代中斷與新舊完成版本的接受條件 | 單改文案無法讓現有禁止重送及不可覆寫發布入口自動支援新機制；Implementer 也不能在六檔外臨時擴充 | Planner 盤點最小必要程式／Skill／Prompt／規範變更，明列新白名單、資料相容性及驗證。不得把未核准的政策變更藏在實作細節中 |

這兩項是新需求相對於原計畫的具體缺口，不表示 Planner 在 Owner 澄清前已知此新選擇。程式段落為本輪唯讀核對結果，不是執行測試結果。

## Planner 應交付什麼

請下一個 Planner 交付新版 `plan.md`、`handoff.md`，讓 Reviewer 與 Implementer 能回答以下問題：

1. **中斷後怎麼繼續？** 正常啟動時自動找回已完成、未完成與結果不確定的項目；以同一日常正式 Prompt 接續，不要求 Owner 提供內部 key 或開發文件。
2. **使用者要確認什麼？** 用白話列出這次重下與取代的列表／項目／目錄範圍、會影響的現有資料，以及拒絕時保留的進度。可對同一恢復批次一次確認，避免逐檔反覆問；範圍變更後不得沿用舊確認。Owner 現在表達的是機制設計方向，尚未確認任何一批真實資料覆蓋。
3. **怎麼讓再次中斷仍可恢復？** 規劃先下載到新暫存位置、驗證後再取代的最小方案，說清楚下載中、取代中、寫完成紀錄中再次中斷時，下一次啟動要做什麼；舊可用資料何時才可被取代。
4. **舊下載與舊紀錄怎麼處理？** 保留歷史真相，讓新恢復與舊 attempt 可追溯；明確處理舊下載晚到、新舊檔案互相干擾及既有 LOCAL_CHANGED。單靠新資料夾不保證舊程式不能寫入；若需要隔開或有界停止方法，由 Planner 查證並規劃，不能把抽象證明責任丟給 Owner。接受重複傳輸不代表資料必須互相混寫。
5. **怎麼證明機制有效？** 對中斷前後、拒絕／同意覆蓋、重新下載再次中斷、驗證失敗、取代／完成紀錄中斷、跨 Session 找回，列可執行的最小驗證與成功標準。驗證要針對使用者最後能完成備份的行為；單元測試、真實 LINE 操作及獨立接受仍分開記錄。

以上是審查要求及候選方向，不預先指定新 schema、命令名稱、資料遷移或背景控制器。Planner 仍須選擇最小可行改動、界定並行寫入保證、必要獨立審查與授權範圍。既有相簿、其他列表及私人資料不因本方向自動納入。

## 交給誰及精確路徑

**下一角色已指定為 Planner，由 Owner 在另一個主 Session 啟動。**

Planner 角色 Prompt：`/Users/hsiaojohnny/.codex/prompts/v4.9.0/01_plan_prompt.md`。

請交付以下輸入；本報告已包含 Owner 新意圖，不需要再讓 Owner 解釋停止 receipt：

- **本次結論與新意圖：** [plan-review-owner-intent.md](plan-review-owner-intent.md)。
- **需要重規劃的原計畫：** [plan.md](plan.md)。
- **原交接與限制：** [handoff.md](handoff.md)。
- **前輪阻塞依據：** [plan-review.md](plan-review.md)。
- **既有中斷事實與未知：** [issue-analysis.md](../20261107-notes-interruption-review/issue-analysis.md)。

為保留舊版本綁定，建議新版計畫的產出位置如下（**尚未建立，是交給 Planner 的建議位置**）：

```text
/Users/hsiaojohnny/dev/Line_backup/docs/plans/20261107-notes-restart-overwrite-replan/plan.md
/Users/hsiaojohnny/dev/Line_backup/docs/plans/20261107-notes-restart-overwrite-replan/handoff.md
```

Planner 完成草案後交 Owner 決定後續審查；本 Reviewer 不啟動 Planner、不改原計畫、不直接交付 Implementer。模型與推理強度由 Owner 選擇，角色沒有預設模型。

## 實際查核、未執行項與狀態

本輪執行 Git 身分／狀態／worktree／遠端查詢（exit 0），唯讀重讀原 plan、handoff、前輪 review、相關根因段落、Planner／Reviewer Prompt 與政策，並核對 `notes.py` 的恢復前置條件。7 份 repo 來源與入口 HEAD 逐 bytes 相符。文件檢查 PASS：UTF-8、5 個相對連結存在、無尾端空白、來源不變及唯一新增本報告；檢查腳本與 `git diff --check` 均 exit 0。來源 SHA-256／大小、命令及檢查原件留專案私有任務區 `.local/line-backup/tasks/20261107-notes-interruption-owner-intent-review/`，Git 交付另存該區 receipt。

事實是新意圖與舊路線不一致；推論是需要 Planner 重新界定行為與最小修改範圍。覆蓋確認、再次中斷恢復與並行寫入隔開方法的實際可行性仍未驗證。本輪產品回歸、GUI、真實帳本／媒體操作及獨立接受皆 **NOT_RUN**，沒有新增真人 GUI 的 OBSERVED。沒有原故障重試或重設既有嘗試額度。

```text
PRIMARY_OUTCOME_STATUS: PLAN_REVIEW_REVISION_REQUIRED
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

本次交接方向已明確，不等於新計畫通過或中斷機制已完成。下一步只交 Planner 重規劃。
