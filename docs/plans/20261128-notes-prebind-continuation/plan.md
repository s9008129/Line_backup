# 計畫 rev1｜LINE 記事本啟動時接續未完成的步驟

## 決策摘要

**目標。** 使用同一份記事本日常正式 Prompt 交接後，在具有當次授權、有效前景及可用工具時，Agent 要完成 `bind` 前當前可做的步驟。收到具體阻塞才依既有規則停下。成功需看到實際工具呼叫、可核對的 receipt 或原件，以及對應的下一個決策。備份的最終成功仍依正式入口的完整對帳與 `download-check`／completion 讀回判定。

**任務分級。** `STANDARD`。預期只調整 Skill 的一個段落，但該段引導真實 GUI 備份入口與身分綁定前的判斷。採人工交接的計畫簡化審查、獨立計畫審查、實作切片簡化審查及獨立差異審查。實際日常備份確認仍採使用手冊的正式 Prompt。

**已讀證據。** 問題提報顯示 Agent 曾直接執行 `notes lists`、保存重導 JSON，另由 CUA 取得 AX／截圖。提報者確認未執行 `notes_capture`，也未載入或呼叫 `captureAndPersist`。因此缺少完整 capture receipt 和當次落地讀回，`bind` 未執行。提報者未親見 CUA、runtime、當次授權或前景撤除，也未收到 helper 錯誤。正確的第一個未完成步驟是 `notes_capture`。讀回 receipt 後才輪到當次 CUA 原件落地。提報曾引用的舊 `NOT_SENT` 屬另一份列表。目標是舊摘要中的強候選，仍待以當次原件完成全部候選對帳。

**直接原因與推論。** 證據支持 Agent 把「前置程序待做」誤成「已無安全下一步」。Skill 已要求先載入再呼叫。任務未完成且 Owner 未要求暫停、停止或撤回時，應做當前可行的安全動作。風險在於入口把待辦動作、證據狀態和停止條件寫在同一長段，Agent 可能抓到「停在 `bind` 前」而略過可執行的取證。先前修正 `8b38d47` 已處理未載入 helper 的錯誤歸因，本次仍出現同類提早終止。這支持在決策點突出下一步。跨模型的發生率與補強成效仍未測。

**最小充分方案。** 整理 [Skill 日常入口第 2 點](../../../.agents/skills/line-notes-agent-cua/SKILL.md#日常入口與-agent-責任)的啟動分流，直接連到既有的 [完整 `lists` capture](../../../.agents/skills/line-notes-agent-cua/references/download-and-ledger.md#啟動與帳本對帳)和 [CUA 原件落地](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md#cua-觀察原件落地)。沿用原有的候選核對與中途回報契約。

建議文案，實作時整合進既有第 2 點。

> **Pre-Bind 的下一步。** 只有重導的 `lists.json`，先用 `notes_capture` 完成並讀回 `lists` receipt。已具合格 receipt，且 CUA 原件尚未落地時，在同一 CUA Node runtime 載入 `cua-evidence-tools`，立即執行 `cua-initial-observation` 的 `captureAndPersist`，核對當次 AX 與截圖讀回。`NOT_RUN` 只記該步尚未執行。授權、前景與工具可用時，先執行上述第一個尚未完成的安全動作，再回到啟動流程。成功讀回且 `ready_for_bind=true`、`CAPTURE_BOUNDARY=RECORDED` 時，繼續入口與全部候選核對，再依原規則決定 `bind`／`init`。實際工具錯誤、原件核對失敗、通道撤除或身分衝突依既有規則處理。若已無安全下一步，附具體證據回報。

**取捨與非目標。** 維持原文的成本最低，但已觀察到同類決策失誤。單點整理可讓 Agent 直接找到現有操作。把 helper 移到新程式、增加 CLI 狀態或建立控制器，會增加入口與驗證面，現有證據未顯示這些變更有必要。`NOT_RUN` 保留現行語意。「下一個安全動作」用一般文字表達，無需建立 `ACTION_REQUIRED` 欄位。

## 範圍與基準

- Repo `Line_backup`，使用其主要 worktree，分支 `feature/line-notes-media`，基準 `988a5095f18a8cd569cef59648e7442ed27b3194`。現有三處未追蹤工作與私有提報原件留存。
- 產品可寫路徑僅 `.agents/skills/line-notes-agent-cua/SKILL.md`。第一個切片即完整候選。計畫與交接保存在本目錄，執行證據保存在專案私有 task 目錄。
- 維持正式 Prompt、helper 實作、references、CLI、退出碼、事件格式、真實帳本、照片、相簿流程與下載控制的既有邊界。開發使用合成資料。真實 GUI 備份須有另次日常正式 Prompt 和有效前景。
- 單段有共同語意與同一可寫檔，由一位 Implementer 執行。兩個 Worker 並改會增加同段衝突，採序列交接。獨立檢查應針對同一確切候選，避免共享 worktree／index 的寫入者。

## 風險與成功條件

1. **有安全下一步。** 合成的重導 JSON 存在、receipt 從未執行時，下一動作必須是既有 wrapper。receipt 合格、只有對話截圖時，下一動作是在同一 runtime 先定義再執行既有 helper。`CUA_EVIDENCE_TOOLS_NOT_LOADED` 走定義與初次實跑。以上情境須有對應呼叫紀錄，且未提前交回任務。
2. **證據完成。** receipt 合格，capture 持久讀回且時間邊界為 `RECORDED` 後，才繼續全部候選對帳。唯一既有候選維持原 `list_key`；只在既有新列表條件成立時才 `init`。看到多訊號分歧或歷史缺口時沿既有流程停在適當階段。
3. **真實阻塞。** wrapper 非零或 `incomplete.json`、helper 實跑回傳具體錯誤或讀回不符、工具撤除、前景與身分不可核對時，維持既有停止或有限查證。只出現 `ready_for_bind=true` 而缺 `CAPTURE_BOUNDARY=RECORDED` 仍不得採信。保存原證據，沿現有三次上限與連續兩次無新資訊規則處理，同步保留禁止重送及未決交易的全域條件。
4. **未來實機接續。** 由有效的當次日常入口建立合格 receipt 與新 observation，做全候選核對及 `bind`。序列讀回已綁帳本最新 `summary` 和相關原事件。按實際資料處理未決或命名交易及舊 open scan，再做普通完整卡片覆蓋與目標細盤。既有 `STOPPED`／`NOT_SENT` 只按該列表當次證據與恢復規則處理。後續維持 B1、readiness、既有 attempt 上限、單次派送與完成讀回。

新鮮度以工具呼叫邊界和當次讀回證據核對；外部程序可改變前景、原件與帳本鏈頭。檢查不能證明原子快照、provider 選擇或未測模型成效。文字若無法通過決策情境，先保存失敗案例供 Owner 決定是否擴充範圍。撤回變更只需回復該段文字，開發流程不對真實資料建立或撤銷交易。

## 檢查與交接

| 檢查與負責人 | 可核對證據 |
| --- | --- |
| Implementer 靜態檢查 | `git diff --check` 與對基準的精確 diff。確認單一產品檔案、引用仍指向原操作區塊、當前所缺步驟可定位、既有安全門檻保留。 |
| Implementer 離線回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py -k NotesInitialObservationBlockTests` 與 `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_capture.py`。保存候選 SHA、結果、退出碼。兩組只驗證既有 helper 和 wrapper。 |
| Owner 啟動的 Reviewer | 對計畫做簡化和獨立審查。候選完成後對確切 diff 做實作簡化與獨立審查，核對待辦、可前進、真實阻塞三個分支及原有門檻。 |
| Owner 指定的獨立驗證 | 以本計畫成功條件 1–3 的合成情境做盲測。使用既有正式入口文字及確切候選 Skill，從工具呼叫紀錄確認行為。比較基準與候選時固定情境、模型與可用工具，另記各次實際顯示和未測範圍。測不到實際呼叫時，保留為未驗證。 |
| Owner 透過正式記事本 Prompt 的日常確認 | 以合格 capture receipt、當次原件、全候選摘要、`bind`、最新 `summary` 和最終逐項對帳記錄結果。若沒有實際授權與前景則標 `NOT_RUN`。 |

由 Owner 傳遞精確版本並啟動下一角色。一個切片即可接受實作簡化及獨立差異審查。審查拒絕或出現授權、資料、前景、介面或驗證範圍變化時，保留證據並交由 Owner 決定。後續若改變候選，依受影響範圍重新取得證據。

## 初始狀態

- `PRIMARY_OUTCOME_STATUS` `BLOCKED`，原備份未完成，開發候選尚未實作。
- `IMPLEMENTATION_STATUS` `NOT_STARTED`。
- `CORE_ACCEPTANCE_STATUS` `NOT_RUN`。
- `REQUIRED_VERIFICATION_STATUS` `NOT_RUN`，尚無候選可驗證。
- `INDEPENDENT_ACCEPTANCE_STATUS` `NOT_RUN`。
- `TASK_CLOSURE_STATUS` `IN_PROGRESS`，供 Owner 交接計畫。
