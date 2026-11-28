# 記事本 Agent 流程與程式修剪計畫 v1

## 決策摘要

角色結論：`PLAN_DRAFT_COMPLETE`。本版依 Owner 更正後的 Planner 指示，提出可直接實作的刪減範圍；不是產品修復、獨立審查或備份完成結果。

Owner 的目標是：一次交接指定記事本列表後，Agent 由 Skill 引導，自行查歷史、完成列表盤點、逐篇下載照片／影片、驗證並保存；換 Session 或一般中斷後仍能接續。工具應保存 Agent 無法靠對話可靠保存的事實，而不應要求 Agent 重複輸入工具已持有的資料，或讓尚未完成的觀察永久阻止重新觀察。

**選定方案：刪除三處已能說明冗餘性的程式限制，並同步縮短日常操作。** 不以刪除行數為目標；每一項須有可觀察的流程改善與保護仍成立的證據。一次交付完整候選，不新增框架、控制器、CLI 子命令、事件版本或遷移。

分級 **STANDARD**：變更的是省略參數的預設行為與盤點完成度的適用範圍；不變更來源身分、派送互斥、完成事實或檔案發布規則。需要相稱的行為回歸與兩個預設 Simplicity Review 檢查點。若實作需要改動 UNKNOWN、交易或歷史格式，已超出此分級與計畫，須交回 Owner。

## 範圍與基準

| 項目 | 精確綁定 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，目前主 worktree |
| 分支／產品基準 | `feature/line-notes-media`／`94700e92ac11c6bbc6140f45a1ac680bc08b875a` |
| 起始 Git | tracked 無差異；既有未追蹤 `issue提交單.md` 保留原 bytes，不納入成果 |
| 本輪任務文件 | 本目錄的 `plan.md`、`handoff.md`、`planner-report.md`；版本 hashes 見 `artifact-hashes.sha256` |
| 私有證據 | `.local/line-backup/tasks/notes-agent-simplification-plan-20261111/` |
| 舊計畫 | 保留原文件、基準與審查結論；本版只提出下列明列規則的修改，不繼承舊 PASS |

Planner 本輪只寫本任務文件與私有證據。後續 Implementer 的產品許可路徑僅為：

- `src/line_backup_batch/notes.py`：下表 C1–C3、相關 help 與必要註解。
- `tests/test_notes_records.py`、`tests/test_notes_regressions.py`：直接對應的正負例；沿用既有 fixture/helper。
- `.agents/skills/line-notes-agent-cua/SKILL.md` 與其 `references/download-and-ledger.md`、`evidence-template.md`、`gui-inventory.md`、`verification-and-recovery.md`：只整理本版工作順序與證據時機。
- `docs/LINE相簿備份_使用手冊.md`：記事本說明及正式 Prompt 的相同規則；不增加 Owner 欄位。
- `AGENTS.md`：僅釐清日常可修正的呼叫前置條件及局部待盤點範圍，不改正式角色交接契約。

不修改相簿程式／Skill、媒體驗證器、工具鏈、證據包或 capture 模組、舊事件 reader、六類狀態、CLI 子命令與既有 flag。真實帳本、索引、active 檔、照片／影片及舊計畫均不在本輪寫入範圍。Planner 不操作 LINE；本開發計畫不代替日常任務的前景交接。

## 第一性原理與已確認根因

Agent 負責當次來源辨識、卡片覆蓋、媒體種類、viewer／chooser 歸屬與操作選擇。工具負責持久記憶、原件引用、禁止重送、檔案驗證及不可覆寫發布。工具只比對字串或證據 bytes 時，不能因此聲稱已辨識真實 LINE 畫面。

本次實際 `bind` 命令省略 `--context-id`，回傳 exit 4、`WRONG_NOTES_CONTEXT`。靜態呼叫鏈已足以解釋這個結果：CLI 將該參數列為 optional（`notes.py:6976`），main 把省略值 `None` 傳入（`:7208–7213`），`bind` 卻要求它等於帳本已保存的 context（`:2498–2500`）。這證明呼叫與介面預設不一致；不能由這個拒絕推論真實列表錯誤。先前 Agent 將此直接交回 Owner，沒有先查出這個可由既有資料消除的前置條件，屬處理缺口。

程式基準見 [notes.py](../../../src/line_backup_batch/notes.py)；操作文件見 [記事本 Skill](../../../.agents/skills/line-notes-agent-cua/SKILL.md)。以下行號皆綁定上述產品基準。

## 必做的程式修剪

| ID／位置 | 刪除或縮限的片段 | 修剪後的行為與仍成立的保護 |
|---|---|---|
| C1 `bind:2494–2514`；`_require_session:2482–2492` | 移除「省略 context 也必須逐字重傳歷史值」的限制；刪除 `_require_session` 無 caller 使用的第二參數與分支 `:2488–2489` | `bind` 省略 context 時，直接採所選帳本已有值；明示不同值仍拒絕。無歷史 context 的行為保持。最新 Session、同一 list key 的證據檢查及已保存 binding 與帳本的一致核對保留。歷史 context 是資料沿革，不是當次前景證明；不刪欄位、不重算 key、不改事件 schema。 |
| C2 `start_scan:3307–3309` | 刪除「上一完整列表 scan 的逐篇媒體 detail 也必須完整，才能開始新 scan」的三行前置條件 | 沒有未決 attempt／命名交易時，新 Session 可重新盤點，不需修補上一輪 detail 或誤用 recovery 旗標。新 scan 仍要自己的頂底、卡片對帳與重疊。舊 scan 原件保留；舊 scan 尚開放時，沿現有 `scan interrupt` 明確結束後再開始，不容許多個 open scan。 |
| C3 普通 `intent:4839` | 移除普通 intent 對全列表媒體 detail 的 `_assert_dispatch_coverage()` 呼叫 | 先完成整份列表的卡片覆蓋，再逐篇完成媒體盤點與下載。目標貼文的 detail、完整媒體數／次序及目標 media 必須屬於最新完整 scan；另一篇僅有待盤點資料時，不阻止合格篇。既有 `record_media:3673–3688` 與 loader `:2139–2149` 已核對當篇數量／次序，不另造重複 gate。 |

C3 是明確的日常行為調整：取消「所有篇的媒體都盤完才准下載」，保留「整份列表卡片盤完，且當篇媒體盤完才可下載」。列表身分／覆蓋不明仍停整份；當篇身分／媒體不明則留待確認，先完成其他合格篇。不能把待盤篇寫成 NO_MEDIA、EXCLUDED 或完成。

`_assert_dispatch_coverage()` 的 restart 呼叫（`:4769`）保留；restart 的精確確認 scope、新 recovery scan、candidate 與 activation 規則不變。`_coverage_errors()` 及 summary 的未解資訊保留。`dispatch_blockers` 是待處理條件清單；其中局部 detail／stale 訊息不再被 Skill 當作整份列表一律停派的判斷。全列表未決 attempt／活動下載／命名交易仍互斥，不能藉 C3 改派其他項。

摘要的完整判準保留：B 篇待盤時，即使 A 篇已完成，`all_known_media_complete` 必須仍為 false，回報列出 B 與未知總數。已知媒體數不冒充整份列表實際總媒體數。

## 同步減少操作負擔

| ID | 要刪除的重複工作 | 採用既有能力 |
|---|---|---|
| D1 | lists → summary → memory 無條件連查，以及同一 lock domain 的平行重查 | `lists:618–635` 已回完整摘要；`memory:5456–5457` 是 summary alias。先枚舉全部帳本、唯一定位；只在需刷新時序列讀選中帳本的一種摘要。保留狀態變更後必要讀回。 |
| D2 | 規定 init／bind 的不同證據欄位一定要分開建立 bundle | 同一完整觀察若涵蓋各命題、適用 ID 的 context 相同，可共用 bundle。不同內容或 context 才分開。既有 create／bind 本已接受同一包，不改 parser/schema。 |
| D3 | 每個 GUI 階段都先另外執行一次 evidence-pack | intent 仍先持久化與讀回；每次 GUI 控制／chooser 的當次定位與原始回傳即時保存。在需要寫 outcome 等事件前，將同一 attempt 適用的原件封裝；需要新事實或 context 的事件仍用新包。原件不能事後重建，未持久化必要操作紀錄時停止。 |
| D4 | 把可從現有工具輸出排解的呼叫錯誤一律當成人工終止 | 日常無新派送、無不明寫入且有具體原因時，允許在授權內修正呼叫前置條件；例如依正確 flag 使用既存值、序列處理 `NOTES_LOCK_BUSY` 的 retry_safe 回覆。最多三次有證據嘗試、兩次無新資訊就停。不得重播 intent／GUI、換帳本／路徑、手改事件或處理 exit 70 當可重試。正式角色的拒絕交接規則不變。 |

D1–D4 不新增工具。Skill 保留一條日常順序：歷史與入口 → fresh bind → 舊交易處理 → 完整卡片盤點 → 逐篇盤媒體並逐項下載／驗證 → 最終對帳。未完的純盤點 scan 可沿現有 interrupt 後重建，不要求 Owner 決定內部模式或提供 ID。

## 保留範圍、替代方案與風險

必要保護有具體對象：列表→貼文→媒體身分避免跨來源認領；intent 與一次控制避免重送；UNKNOWN／無 outcome 避免晚到副作用誤歸下一項；pending naming 避免重複發布；空 staging、非 symlink、hash 與完整解碼保護內容；不可變 completion 保存跨 Session 進度。這些不能由「繼續」推論為已解除。

只補文件教 Agent 重傳 context，能解當次呼叫，仍留下隱性條件與其他觀察阻塞，因此不足。整套重寫帳本、刪除 restart／reattest／evidence reader，會牽涉真實歷史相容與未決交易，且沒有逐項可刪證據，因此不選。只做共用模組抽取也不會改善上述工作行為，不納入本次。

採用 C3 後，列表中的貼文可能尚未逐篇核完就開始處理合格篇；不能承諾來源為原子快照。Agent 仍須每次重新核對目標；發現列表新增、刪除或重排而使覆蓋失效，就停止新派送並保留變動證據。CLI lock 不能控制 LINE、Finder 或其他 Session；不以無限重查承諾 exactly-once、OS 隔離或外部內容不變。

相容回復以程式版本為單位，不能撤銷新事件或完成事實。此版不新增事件格式，因此不需要資料遷移；回退舊版可能恢復原有拒絕，不得以重送或清帳解決。若實作發現必須改舊 reader 或資料才能通過，停止此切片並回報。

## 單一可驗證切片與成功證據

首個切片就是本計畫完整候選：C1–C3、D1–D4 與直接回歸一次交付。沒有剩餘實作時，不製造第二切片或重複進行同一審查。下表全部為**待執行**，本輪產品檢查 `NOT_RUN`。

| ID／owner | 可觀察成功條件、檢查與停止條件 |
|---|---|
| V1 Implementer | 合成有 context 帳本：新 Session 省略 flag 可 bind，正確明示值可 bind，錯誤值 exit 4 且事件不增加。無 context 帳本保持既有行為；CLI 與直接方法都覆蓋。舊事件 bytes／list key 不變。 |
| V2 Implementer | 上輪已 finish 卡片 scan、部分 detail 未完、沒有 attempt：fresh bind 後可開始新普通 scan；上輪尚 open 時可明確 interrupt 後重開。新 scan 未 finish 前 intent 仍拒絕；舊 scan/event 保留。 |
| V3 Implementer | 最新完整卡片 scan 有 A、B：A 的當篇媒體完整、B detail 待盤時，A 可取得唯一 intent；B 仍待盤，摘要不報全部完成。A 完成後可補 B detail 並處理；跨 Session 重新盤點後，A 不得重下。測試保存事件與預期狀態，不只檢查沒有 exception。 |
| V4 Implementer | B 若已有 UNKNOWN／無 outcome／DOWNLOAD_FINISHED 待驗證，或任何 pending naming，A 仍拒絕新 intent，拒絕前後無新 staging／intent。錯列表、stale 目標、當篇數量錯誤、受保護／完成項、LOCAL_CHANGED、證據漂移與 symlink 原負例保留。 |
| V5 Implementer | 使用既有 notes_v1 fixture 驗證讀回；既有 restart／reattest／媒體驗證 suite 不因修剪而放寬。調整 `test_start_scan_and_intent_share_coverage_gate` 的舊政策斷言，新增分開的重新觀察與當篇資格案例，不能刪整個負例 suite 取綠燈。 |
| V6 Implementer／Simplicity Reviewer | diff 實際刪除三處限制及無 caller 分支；沒有新 bypass flag、schema、控制器、Owner 啟動步驟或無關重構。Skill／references／正式 Prompt 不能殘留「所有篇媒體先全盤完」與「每階段必另包」的衝突。 |
| V7 Owner 日常試用 | 修正後使用手冊同一正式記事本 Prompt 與有效前景：從既有紀錄定位、正常綁定、卡片盤點、處理合格媒體、hash／解碼與 completion 讀回。已完成跳過，未解篇明列。自然發生跨 Session 時再核對接續；不為製造測例重下或改真實帳本。未出現的真實中斷／混合附件情境仍 NOT_RUN。 |

Implementer 先跑與 C1–C3 對應的既有 records/regressions 案例；完整候選執行專案三條最小回歸一次，通過後不因流程重複執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

合成帳本／輸出放 Implementer 的專案私有任務目錄；保存精確候選、命令、退出碼、counts 與原始結果。工具不足或真正失敗需保留證據，不用 mock 冒充真解碼／GUI 成果。V7 是日常產品入口，不另換 Acceptance/E2E Prompt，也不以開發文件作為下載必要輸入。

## 人工檢查點與停止條件

本 Planner 交付後，由 Owner 啟動計畫 Simplicity Review，評估三個刪減是否充分且未新增層次；需要額外 Plan Review 由 Owner 決定。核定後 Implementer 一次交付上述候選，再由 Owner 啟動首切片 Simplicity Review。候選已完整時，直接交 Owner 以日常入口試用，不加空實作或重複審查。本輪 helper 只是同角色讀源碼，沒有授予獨立 PASS。

需 Owner 對本版做的產品決定只有已明列的 C3 順序調整；不拆成每次日常的確認。已授權的正常唯讀查證與可逆導覽不重新求准。若需要改寫真實歷史、解除 UNKNOWN、放寬資料／授權邊界、刪掉相容 reader、修改 restart scope 或變更計畫以外公共介面，停止並提交具體差異。不得逐項關掉新遇到的保護直到下載成功。

## 初始狀態

PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE（本輪規劃；實際備份目標尚未完成）

IMPLEMENTATION_STATUS: NOT_RUN

CORE_ACCEPTANCE_STATUS: NOT_RUN

REQUIRED_VERIFICATION_STATUS: NOT_RUN（產品回歸／實機；本輪文件檢查另記）

INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN

TASK_CLOSURE_STATUS: NOT_DONE（Planner 已交付，產品尚待實作與確認）
