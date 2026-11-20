# 記事本列表容器 device 政策：有界修訂 v1（待審）

## 決策摘要

角色結論：`PLAN_DRAFT_COMPLETE`，不代表獨立計畫審查或產品接受。本輪按 Owner 明示的「進行 re-plan、符合意圖與核心目標、避免過度工程化」撰寫計畫。Owner 同時附的 02 為唯讀 Plan Reviewer；本輪以明示的重規劃要求為準，採 Planner 產物，不自評為獨立 PASS。

核心目標不變：Owner 開好指定記事本列表並交接前景後，不同 Agent／Session 使用同一份正式 Prompt 與 Skill，自主查歷史、完整盤點、逐項下載照片／影片、驗證並保存。內部 metadata 應幫助任務完成，不應把沒有媒體或交易受損證據的列表容器差異變成額外的 Owner 操作。

**選定方案：只在共用的列表容器檢查中區分普通目的地與已重新見證的目的地。普通目的地保留 path／inode／canonical／非 symlink 及授權邊界；歷史 device 值保留在事件作診斷，不再單獨作為列表容器的拒絕條件。** 新 staging、既有媒體與交易仍依各自證據核對，不改寫任何事件。

這是列表容器政策修正，不是「所有 device 檢查都失效」。不增加首次下載 reattest、warning 事件、磁碟 registry、marker、背景程序或 Owner 啟動步驟。一般下載沿用原流程；工具已接受後，Agent 不必為單獨的列表 device 差異另求確認。

分級 **CRITICAL**：改的是目的地連續性判定，且共用函式通往發布與恢復。保留相稱的獨立計畫審查及接受；這是開發流程，不加入日常產品入口。實作以一個完整可驗證切片交付，不為流程額外拆出多輪功能。

## 基準、來源與原計畫效力

| 項目 | 綁定 |
|---|---|
| Repo／worktree | `Line_backup`，目前主 worktree；不整理其他 worktree |
| 分支／基準 HEAD | `feature/line-notes-media`／`60c1a251b6bff7e9d3b5e72c455cc01228657242` |
| 起始 Git | tracked 無差異；原有一份 Owner 未追蹤檔，保持 bytes、不納入提交 |
| 根因來源 | [issue-analysis.md](../../diagnostics/20261111-notes-directory-device-binding/issue-analysis.md)，綁定 `5c3b937` 的產品；`5c3b937..60c1a25` 只有診斷文件，產品無差異 |
| 舊計畫 | `../20261108-notes-volume-identity-reattest/plan.md` 及 handoff；舊檔保持原綁定，不覆寫 |
| 本輪私有證據 | `.local/line-backup/tasks/notes-list-device-replan-20261111/`；來源 hashes、命令／退出碼、progress、交付頁及 receipt |
| 核准狀態 | 本輪授權重規劃與文件 checkpoint；實作、新政策剩餘風險、實機及接受尚待本版適用核准與檢查 |

此計畫只取代舊 v3「device／witness 協議不可變更」中**普通列表容器的歷史 device 相等要求**。舊環境附屬項分類、已完成／交易檢查、reattest 的 witness／事件／一次性規則維持。舊版 PASS 不擴張到本版；本次不重做已完成的 preview／confirm 或環境項修正。

直接事實：前次分析確認，零 attempt 的列表在 device-only 差異下被普通 intent 拒絕，reattest 因沒有 OPEN_BATCH 不適用。前次合成診斷可重現；本輪不重跑真實帳本或診斷。推論：按下列分層修改共用判定可覆蓋完整流程。未知：device 改變的 OS 原因，以及新候選在真實 LINE 的結果。前次診斷 harness 的兩次失敗及第三次成功保留在原報告，不重設歷史或冒充產品修復嘗試。

## 一致且最小的產品規則

| 檢查對象／狀態 | 本版要求 |
|---|---|
| 普通有效 binding（created／destination） | `_require_current_list_directory` 保留根目錄、路徑、目錄型態、canonical、非 symlink、inode、現有已驗證授權邊界；只有歷史 list device 不同不能單獨拒絕 |
| 有效 binding 是 `list-directory-reattest` | 保留原 device／inode 嚴格相等及再次漂移停止；不讓普通分支繞過既有單次轉接契約 |
| 同次讀取、原子搬移 | `directory_info` 前後 device／inode，以及 link／原子操作的同檔案系統要求不變 |
| 新 attempt | 新建唯一空白 staging，intent 記錄 staging 當下 device／inode；仍先保存並讀回，當次下載控制最多一次 |
| 舊 staging、completion、active、pending | 繼續與各自 intent／manifest／發布進度的 device、inode、metadata、hash 與身分比對；不自動重綁 |
| UNKNOWN、活動下載、未完成命名、受保護歷史 | 不因列表 device 政策改變而獲得重送資格；未知先查證，原停止與恢復規則不變 |
| 完成目錄缺席／仍在但異動 | `LOCAL_MISSING` 保留完成且禁重下；`LOCAL_CHANGED` 保留原件，依原規則停止；不改記空帳 |

不採「零 intent 才放行」：第一次 intent 寫入後，verify 與發布仍用共用 gate，會再被舊值擋住。規則須以**保護物件**區分，而不是依目前跑到第幾張暫時跳過。

已核對的共用呼叫點（行號綁定基準產品）：`notes.py:4710`、`:4806`、`:5467`、`:5473`、`:5592`、`:5642`、`:5932`、`:5950`、`:6009`。實作者應沿共用函式完成，無須在九處各加一套條件。既有有效 binding 的事件種類已可區分兩分支，不需要持久化新旗標或事件。

**與舊資料的界限：** 放行普通 list gate，不代表舊 staging 或已完成檔的 device 漂移也可放行。有這些情況仍由原 gate 拒絕，必要時使用原有且適用的恢復路徑。既有 OPEN_BATCH 所需 witness 轉接不刪除；Skill 要根據真正受影響的受管理物件說明，不再宣稱所有列表 device 差異都須 reattest。本切片不承諾解決舊兩影片任務的所有狀態或未測阻塞。

## 變更範圍

| 階段／路徑 | 許可的最小內容 |
|---|---|
| 本輪 Planner | 本任務 plan、handoff、progress、私有證據及 HTML；不修改產品或舊報告 |
| 待核准 `src/line_backup_batch/notes.py` | 共用列表容器判定及必要註解；保留 reattest 分支與全部交易檢查 |
| 待核准測試 | `tests/test_notes_records.py`、`test_notes_reattest.py`；只在需覆蓋既有 restart 業務出口時改 `test_notes_restart.py`；沿用 fixture，不另建測試框架 |
| 待核准 Skill／references | 記事本 Skill、`references/download-and-ledger.md`、`verification-and-recovery.md`：區分普通列表容器與受管理資料／轉接，不增加流程 |
| 待核准 AGENTS.md | 僅新增下一節的短原則，落實 Owner 已要求記錄的產品方向；不重寫其他保護條款 |
| 待核准手冊 | 只修記事本 device／reattest 的衝突敘述；正式 Prompt 的啟動方式及相簿部分不變 |

禁止改相簿程式／Skill、媒體驗證器、notes evidence、公開 CLI／事件 schema、六類狀態、工具鏈、舊 fixture、歷史計畫／審查結論或真實帳本／索引／active／照片影片。不下載、不操作 LINE、不遷移或清理實際資料、不 merge master、不 force-push。

### AGENTS.md 的最小原則草案

> 本專案以 Agent 使用正式 Skill 完成 Owner 指定列表的備份為核心；程式、帳本與檔案系統檢查負責輔助記錄、去重與驗證。檢查應對應具體保護物件及可說明的風險；普通列表容器的歷史 device-only 差異，不應單獨阻擋已核對授權路徑的合法備份。受管理檔案或交易的身分／完整性異常、UNKNOWN、活動下載、未完成命名、跨列表或授權歧義仍依原規則停止。Agent 不得自行略過工具拒絕或改寫歷史；需要調整規則時，以有界開發修改及相稱驗證處理。

這段承接 Owner「工具服務於任務」的意圖，也維持日常 Agent 能確實遵循的停止規則；不將「尚不能證明重大損害」當成任意忽略完整性失敗的理由。本輪只提出草案，未改 AGENTS.md。

## 方案取捨與剩餘風險

直接修共用判定已足夠，不擴張 reattest 至首次下載：首次情境沒有 witness，硬加新轉接會增加事件、確認及恢復負擔。也不新增磁碟 UUID／bookmark／marker，因為那會引入新資料與遷移，超出已證實問題。保留歷史 device 欄位可以維持事件相容，不需刪欄或重建帳本。

剩餘風險必須明示：不同檔案系統可能存在同路徑、同 inode 的另一份目錄，保留 inode 不是實體身分的完整證明。本版選擇信任已授權的 canonical 路徑與當次來源辨識；不是偵測惡意完美 clone 的方案。Owner 核准本計畫須涵蓋此**列表容器**政策取捨；過去對既有 witness 的同意不自動代替本版核准，也不向日常使用者逐項重問。

records lock 無法鎖住 Finder、LINE、其他 Session 或掛載變更。保留現有有限前後檢查及受管理物件驗證，不承諾整樹原子快照、GUI exactly-once 或 OS 隔離。若當次物件有實際變化則按既有 gate 停止，不新增無限重查。

回復限程式版本相容回退；不刪事件、不撤銷新完成事實。舊 CLI 可能再次因原 list gate 拒絕；不能以清帳或重送解決。因不新增 schema，不新增資料遷移工作。

## 單一可驗證切片與檢查

計畫核准後，Implementer 一次完成共用判定、下列業務正負例及一致文件，交付首個可驗證候選。若該切片已完成全部要求，仍交首切片 Simplicity Review，不製造 F2 或空實作。

以下全部是**待執行條件，本輪 `NOT_RUN`**。每項保存精確候選 HEAD／diff、cwd、命令／退出碼及原始結果；synthetic TMPDIR 與帳本均置於專案私有任務目錄，不使用真實照片區。

| ID／owner | 成功證據及停止條件 |
|---|---|
| V1 Implementer：主正例 | 新列表、零 attempt、完整盤點兩張 synthetic 照片；只模擬歷史 list device 差異。第一項走 intent→outcome→production 圖片驗證／發布→completion 讀回；新 Session 重新 bind／完成所需 scan，第一項仍完成且禁重下，第二項走到完成；summary 兩項完成。新 staging／completion device 為當下實值，舊事件 bytes 不變。只到 intent 不算成功 |
| V2 Implementer：容器負例 | path／inode 改變、目錄缺席、非目錄、symlink（含祖先）、越界及錯列表仍拒絕；不創建新 intent／不覆寫原檔。沿現有失敗碼，不為新測試弱化型態或授權檢查 |
| V3 Implementer：交易與歷史 | 普通 list-only 差異下，UNKNOWN／活動 attempt、pending 命名仍不可新派送；另測 staging／completion／active 自身 device 或 inode／hash 漂移仍拒絕，完成缺席仍完成且禁重下。驗證 outcome、completion 與事件鏈未被變更。這些負例不得被 list 放行遮蔽 |
| V4 Implementer：舊協議 | 沿既有 reattest suite 驗證精確 preview／confirm／replay、scope／generation、新 recovery scan 與一次性；曾轉接後再漂移仍拒絕。restart 既有控制案例照跑，禁止以普通分支旁路。不要為測試綠燈重定義舊事件 |
| V5 Implementer：文件與最小回歸 | Skill／references／手冊不再把普通 device-only 列表差異一律導向 reattest；保留受管理物件及 OPEN_BATCH 的既有規則。正式入口不增加步驟。下列三條命令均 exit 0，保存 counts；真解碼缺工具則標 NOT_RUN 並回報，不用 mock 代替 V1 的圖片驗證 |
| V6 Owner：日常實機 | 修正後用手冊記事本正式 Prompt＋有效前景交接，先查永久歷史與當次身分、盤點，再執行合格照片下載、hash、ImageIO、completion 讀回與收尾對帳。保留真實派送／outcome／驗證證據；不為測試重下已完成項。沒有自然的 device-only 差異時，只能證明當次備份，不能宣稱實機漂移情境已測；不改真實 ledger 或操弄掛載製造情境 |
| V7 獨立接受者 | 對精確候選逐項映射 V1–V6；以原日常入口產生的真實結果檢查核心目標。合成回歸、檔案驗證、Owner OBSERVED、實際 GUI、跨 Session 與獨立接受分別記錄；未測範圍 NOT_RUN |

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

開發中按變更選擇既有 records／reattest／restart 局部測試，最終一次跑上述完整最小回歸；完整套件已涵蓋局部時，不無故重跑。ImageIO 使用現有工具與相符 SDK，不改系統工具鏈；本案不新增影片政策或 ffmpeg 工作。

## 人工檢查點、停止與交接

Owner 決定本版政策及啟動適用檢查：計畫 Simplicity Review → CRITICAL 獨立 Plan Review → 核准後 Implementer → 首切片 Simplicity Review → 獨立接受。本 Planner 不啟動任何下一正式角色、不宣稱自己獨立審查通過。Owner 用正式日常入口確認實際能力，不能被開發角色 Prompt 取代。

若實作需要新持久 binding／新 schema、改寫歷史、刪檔、解除舊 UNKNOWN、放寬受管理物件 device／hash、改變 reattest 一次性規則、擴至 path／inode 漂移或相簿，停止並交 Owner 決定。若完整業務路徑在共用 list 政策修正後仍阻塞，先保存具體新 gate 證據，不把其他保護逐一關掉。同根因最多三次有證據嘗試；兩次連續無新資訊即停止，不因重規劃重置。

計畫與交接草案交付後停止；本版未批准產品實作或實機操作。

## 六項狀態

| 狀態 | 本輪值 |
|---|---|
| PRIMARY_OUTCOME_STATUS | BLOCKED（備份未完成；規劃產物 PLAN_DRAFT_COMPLETE） |
| IMPLEMENTATION_STATUS | NOT_RUN |
| CORE_ACCEPTANCE_STATUS | NOT_RUN |
| REQUIRED_VERIFICATION_STATUS | NOT_RUN（產品回歸／實機；文件檢查另記錄） |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN |
| TASK_CLOSURE_STATUS | NOT_DONE |
