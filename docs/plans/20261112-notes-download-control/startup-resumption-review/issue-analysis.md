# 補充根因分析：授權更新後未接續記事本備份

## 本角色結論

**ANALYSIS_COMPLETE；唯一建議路線：`IMPLEMENTER_FIX`，限縮為入口與接續決策的文件修正。此建議尚未執行。**

白話說：前一次 Agent 沒有把你更新的授權，轉成「重新核對還缺哪些條件，然後繼續」的動作。診斷交接又帶入會過期的版本門檻，使任務先卡在內部流程。這是目前最有支持的流程根因；不能據此宣稱 LINE 不能下載，也不能說直接點畫面上的卡片就一定安全。

本輪只診斷。Owner 指定的 `06_high_reasoning_review_prompt.md` 要求「This is diagnosis only: do not modify product files」；專案與全域手動工作契約禁止在本角色跨入修復、重測或結案。一般「fix all issues」在這個明示角色下，不能當成已取消其邊界。已完成可供決策的修正交接，不宣稱完成修復。

### 問題與候選身分

- 本輪單一問題：`R-NOTES-STARTUP-RESUMPTION-01`，解釋補充提報中「解除診斷限制後，仍未前進到目標圖片檢查」的停止。
- 舊問題 `R-NOTES-CONTROL-OBSERVABILITY-01` 是「已在 viewer，仍未證明下載控制」。它仍未解決；本報告不覆蓋舊分析、不重設其嘗試歷史，也不把兩者混成同一次 UI 失敗。
- 工作區：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- 本輪輸入 HEAD：`12fe38ca387dc59e99d4291ca80c4f70b011de77`。
- 補充提報所述事發 HEAD：`1fd7954d8aab8b7e088b7c8279ea4811692edabf`；原診斷基準：`23e98bcc718859cca5c583a9255262e9ce1f9794`。
- 初始僅有既存 untracked Markdown；保留內容、未 stage。其他 worktree 不操作。
- 本輪來源為提報、Git、現行 Skill／references／手冊與程式。未讀事發聊天原文、該次原始 CUA 或真實帳本，不把提報作者敘述當成本輪直接 GUI 觀察。
- 一名同角色唯讀助手核對 `lists` 與摘要原始碼；沒有模型覆寫、沒有正式獨立接受，也沒有 provider 用量主張。

## 1. 已證實事實與最小失敗軌跡

| 階段 | 可核對的內容 | 證據強度與限制 |
|---|---|---|
| 初始診斷交辦 | 指定 viewer、精確舊 HEAD、不下載、基準不符停止 | 直接讀取 [next-agent-prompt.md](../next-agent-prompt.md) |
| 該 Prompt 發布 | `1fd7954` 才新增 Prompt，內文卻要求 `23e98bc` | Git 直接證據；取得含該 Prompt 的新 HEAD 便不符其內文基準 |
| 後續授權更新 | Owner 接受目前版本、解除只診斷限制，授權同篇五張圖片 | [補充提報](../問題提報單-啟動阻塞與流程負擔.md):9–23；未讀原對話，不冒充逐字授權原件 |
| 停在列表 | 取得 LINE 列表／卡片畫面，尚未確認與目標的關係 | 同提報:39–47；未保存可由本輪重核的該次 observation bundle |
| 記憶查詢 | `lists` 回傳大量資料及 active hint，未收斂到目標身分核對 | 同提報:34–35、51–55；「未另跑 summary」本身不是錯誤 |
| 未派送 | 該次沒有 intent、viewer 操作、下載、驗證或 completion | 提報:49–56；五張尚未備份是提報事實，現況未另查 |

直接 Git 核對：`23e98bc..1fd7954` 只新增診斷 Prompt；`23e98bc..12fe38c` 只新增該 Prompt 與補充提報。`02db924..12fe38c` 在 `src`、`.agents/skills`、`AGENTS.md` 與使用手冊沒有差異。因此本案的這段 HEAD 差異不能當作已發生產品修正或帳本格式遷移。

本輪沒有重播失敗。事發聊天、畫面／焦點／前景連續性、完整 `lists` stdout 是否被工具截斷、目標帳本當時 blockers，均為 `UNKNOWN`。

## 2. Agent 決策錯誤與資訊不足

### 授權與停止條件必須分開更新

初始「不下載」有效時，Agent 不下載是正確的。若後續原始訊息確如提報所述，Owner 已明示解除同一任務的限制，舊的任務限制就不應持續當成有效拒絕理由。Agent 應記下新的授權範圍，再逐一核對尚未成立的條件，無須要求重貼整段 Prompt。

解除的只是特定任務限制與 Owner 已接受的版本差異。仍有效的是：僅指定五張的範圍、當次有效前景、列表→貼文→媒體身分、完整卡片覆蓋、目的地、未決交易、單次派送及禁止重送。允許盤點其他卡片，不等於授權下載其他貼文。接受版本更不代表接受資料損壞或 UNKNOWN。

Owner 若只說「繼續」而未明示解除「不下載」，不能猜已解除。本案提報明確聲稱兩項限制都已更新；原文未提供，故判斷保持條件式。

### 看到列表，不代表前景一定失效，也不代表已認出目標

Skill 的正常入口本來就是記事本列表。看到列表時找不到下載控制是預期現象，不能拿來證明 viewer 或 LINE 功能失敗。

最小下一步是：在仍有效的交接內，重新取得 LINE 的當次 app/window、AX／畫面與來源範圍，保存原件；將候選帳本與當前列表的連續入口、貼文錨點交叉核對。這一步可唯讀進行，不先點卡片、不建 intent。

若證明是同一列表、前景有效且身分無歧義，依原 Skill 完成當輪卡片覆蓋，再開啟已確認目標的媒體；正常可逆導覽不逐點請示。若仍不能排除另一列表／視窗，只問一個具體問題，例如「目前 LINE 停在這份記事本列表，請確認它是否包含這次指定的貼文」。不要求 Owner 提供 UUID、JSON 或重新承擔整套內部流程。

如果確有前景中斷，GUI 輸入仍須等重新交接。這與單純的「列表／viewer 說法不一致」不同，不能憑後者自行斷言前者已發生。

### 缺少收斂，不是缺少另一道 summary 儀式

`NotesCollection.lists()` 已對所有登錄帳本呼叫 `summary()`（[notes.py](../../../../src/line_backup_batch/notes.py):618–635）。故提報中「沒有再讀單帳 summary」不足以單獨認定違規；真正漏掉的是解析已有資料、核對候選並選出下一步。

active hint 只有定位功能，讀取函式只驗 schema／型別（同檔:494–508），不證明目前畫面身分。安全且簡潔的方法是：

1. 保存一次成功 `lists` 的完整 stdout、stderr、exit code 至專案私有 task，確認成功才解析，不用截頭輸出丟掉候選。
2. 對全部候選產生短表：內部識別、records root、list key、context、覆蓋、六類計數、未決交易與 blockers；內部表不公開私人內容。
3. 用 hint 的 records root 加 local list ID 精確找候選，再和當前入口／identity／context 交叉核對。無匹配或有歧義則保留全部候選，不建空帳。
4. 展開選中 row 的目標貼文／媒體與未決項；需要刷新才序列執行一次 `summary --records-root`。不沿用舊 session ID 作新綁定。

現行 CLI 已提供這些欄位（同檔:5427–5450）；目前沒有需要先改 `notes.py` 才能推進的證據。這不等於證明 CLI 所有功能皆無缺陷。

## 3. 第一性原理、根因候選與信心

安全完成需要同時成立：有效授權、有效前景、正確來源身分、帳本資格、可證明的下載控制、可歸屬結果與檔案驗證。某一條件更新，不會自動滿足其餘條件；某一條件未滿足，也不代表所有唯讀查證都必須停下。

**選定因果解釋（中高信心推論）：流程沒有把「授權／版本已更新」連接到「只重新評估剩餘阻塞並接續」的明確決策，Agent 把一次停止當成任務終點。** 具體表現是未從已有帳本摘要與當次列表重新建立可執行路徑。此缺口解釋本輪啟動停滯，不解釋舊 viewer 內控制的物理顯示機制。

| 候選 | 信心／證據 | 反證或限制 |
|---|---|---|
| 精確 HEAD 交接易失效 | 高；Prompt 新增的 commit 已不符其內文基準 | 若任務明確要求另取舊 candidate，可保留精確版本門檻；不能偷偷 checkout |
| Agent 未重新評估已解除阻塞 | 中高；提報明示授權更新但未推進 | 原對話若未真正解除，或已有不可解的資料／前景阻塞，須改判 |
| Skill 接續分支不夠具體 | 中；已寫自主查帳與導覽，但沒有明列這組授權更新＋畫面角色不同的分支 | 不是整份 Skill 無法使用的證明；補一處決策即足，不另建控制器 |
| 工具輸出量造成負擔 | 中；提報與程式均支持回傳多份完整摘要 | 是否截斷未知；不能據此要求修改公共介面 |
| 列表／前景真的不符 | 未知；提報記載畫面說法不一致 | 足以禁止猜測點擊，但不妨礙先唯讀核對 |
| LINE 沒有下載功能 | 無支持 | 該次尚未開啟目標 viewer，沒有測到此命題 |

若原始來源證明 Agent 已完成候選核對，且當時確有不可解的身分／前景或帳本阻塞，則「應可繼續」必須縮為「應準確回報具體阻塞」，不能要求越過它。

## 4. 既有嘗試與新增學習

- 原日常備份、Planner 與舊高推理分析：針對 viewer 控制發現，結果及來源保留在上層既有文件。本輪未重算舊原件 hash，不將其二手結論當新實測。
- 後續診斷交接：增加一次非下載觀察設計，卻固定舊 HEAD；補充提報顯示執行停在版本／入口，未完成該對照。不能計作成功的控制揭露實驗。
- Owner 解除限制後：依提報，CLI help 與 lists 成功；未完成目標核對。新學習是「停止後如何接續」與「viewer 內如何找控制」必須分開處理。
- 本輪：直接證明 HEAD 差異僅文件、Prompt 的版本陷阱，以及 lists 已含摘要；提出最小文件修正。沒有新的 GUI／下載／修復嘗試，不虛構已用掉幾次額度。

不建議重複貼舊診斷 Prompt、重跑大段 lists 輸出、重切五張圖或另開空帳。沿用同根因最多三次、連續兩次無新資訊停止的規則。

## 5. 唯一建議路線：IMPLEMENTER_FIX（未執行）

建議由 Owner 在另一主 Session 啟動有界文件修正；不再先做一輪同內容診斷。修正目標是讓現有日常入口在授權更新後知道下一步，不增加新的啟動文件。

| 精確位置 | 最小修正內容 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md`「日常入口與 Agent 責任」 | 增一個接續分支：記錄 Owner 明示更新，撤銷被取代的任務限制；核對剩餘前景／身分／帳本條件後繼續；保持原下載 scope，不要求重貼 Prompt |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md`「啟動與帳本對帳」 | 補完整保存 lists、全部候選短摘要、精確定位與只在需刷新時 summary 的方法；不新增 CLI flags／schema |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`「入口判定」 | 補列表／viewer 描述不一致時先唯讀定位的分支；身分成立才正常導覽，前景中斷或仍有歧義才問一件事 |
| `docs/plans/20261112-notes-download-control/next-agent-prompt.md` | 保留其歷史診斷性質並明示「不作日常下載入口」；若再執行診斷，由 Owner 指定實際 candidate，不把發布前 HEAD 當永久啟動門檻；不解除不下載限制 |

不改 `src`、測試、相簿流程、帳本語意、永久記憶、派送保護或手冊的唯一正式入口；本次已窄於 Skill 預設的五張授權不得擴成整列表下載。若必須改程式／資料／架構或新增 Owner 啟動步驟，停止此路線，回報證據由 Owner 決定。

### 成功檢查與未測範圍

- 文件對照：舊限制有效時仍不下載；明示更新後不再引用已被解除的限制；接受程式版本不能放行資料異常。
- 候選處理：保存全部候選、hint 不作身分證明、不遺漏缺損歷史、不沿用舊 session、不為摘要重複查帳。
- 日常正式 Prompt 真實試用：從列表出發，由 Agent 自行核對與盤點，開啟已確認貼文的五張；不要求 Owner 提供內部 key 或逐張下令。使用既有窄 scope 時仍只下載那五張。
- 每項仍須：本記事本自身控制、intent 及新空白目的地讀回、單次派送、outcome、穩定檔案／非空／SHA-256／ImageIO 解碼、completion 讀回；五張均有證據才可稱這批完成。
- 反向情境：另一列表、前景中斷、UNKNOWN、活動下載、未完成命名、LOCAL_CHANGED 應保留正確停止；不可藉接續分支解除。
- 如果再次進到舊 viewer 控制停止點，準確交回該獨立缺口；文件修正不能冒稱已解控制問題。

以上皆為建議驗證，非本輪 PASS。真實 GUI、chooser、下載、五張驗證、影片、混合附件、跨 Session 恢復及獨立接受均 `NOT_RUN`。僅文件修正可先做範圍／連結／diff 核對；若後續實作超過文件範圍，應停止並重新決定必要回歸。

## 6. 實際命令、來源與交付界限

環境為 Owner 提供的 macOS 專案工作區、zsh；沒有選擇或變更模型／effort。所有證據 metadata 放本專案 `.local/line-backup/tasks/20261112-startup-resumption-review/`，不放全域 `.codex`。來源與 SHA-256 見同目錄 metadata；公開報告不重複私人帳本 ID／群組名稱／原圖。

- `git status --short`、branch／HEAD／worktree、log／show／diff：已執行，確認候選及文件差異；精確產品路徑 diff exit 0。
- `cat`／`nl`／`rg` 讀本角色 Prompt、全域 v4.9.0 policies、role-report 模板、本任務文件、Skill／references／手冊與所列原始碼：已執行。第一次將不存在的 repo `policies` 放入 `rg`，exit 2；其餘結果仍有輸出，後續改讀既存全域 policies，未建立退役框架。
- 一次模板讀取工具呼叫在 dispatch 前 aborted；未執行命令。後續相同唯讀讀取 exit 0；不是產品錯誤或 GUI 嘗試。
- `git check-ignore` 對未忽略的新分析路徑 exit 1，表示不在 ignore 中；不是產品失敗。
- 原生同角色助手只讀 source／tests，結論由主代理讀程式交叉核對；沒有執行 tests，不列測試 PASS。
- 本輪未操作 LINE、未執行 notes CLI、未讀寫真實帳本／照片；沒有本輪 GUI 的 `OBSERVED` 或 E2E PASS。
- 文件及 Git 收尾的實際結果另存本任務 `progress.md` 與私有收據；不預填 commit／push 成功。

## 7. 六項狀態與人工交接

| 狀態 | 值與解釋 |
|---|---|
| PRIMARY_OUTCOME_STATUS | BLOCKED：依補充提報，指定五張尚未備份；本輪分析為 ANALYSIS_COMPLETE |
| IMPLEMENTATION_STATUS | NOT_RUN：本輪沒有產品修正 |
| CORE_ACCEPTANCE_STATUS | BLOCKED：未有指定五張完成證據 |
| REQUIRED_VERIFICATION_STATUS | PARTIAL：版本／規範／原始碼核對完成；實機與檔案驗證 NOT_RUN |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN |
| TASK_CLOSURE_STATUS | BLOCKED：分析可交接，修復與備份仍未完成 |

下一個建議責任角色為 Owner 啟動的 Implementer，輸入本報告與目前候選 HEAD，限第 5 節文件範圍。這是建議，不是已派送、核准計畫或已通過審查。Owner 決定是否採用該有界修正；本角色到此停止，不自行修復、重測、下載或啟動另一角色。
