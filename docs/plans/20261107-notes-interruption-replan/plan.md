# 記事本中斷恢復機制：規劃草案

## 決策摘要

本輪為 Owner 指定的 Planner，只產出草案，不實作、不批准計畫、不操作 LINE 或真實帳本。來源為 [根因分析](../20261107-notes-interruption-review/issue-analysis.md)，根因識別沿用 `NOTES-INTERRUPTION-RECOVERY-GAP`。

目標是讓下一個 Agent 使用**同一份日常記事本正式 Prompt**，自行找回中斷交易、保存當次證據、辨別晚到結果或原操作終結，再依既有追加式 CLI 對帳及恢復。成功的可觀察結果是有一條經實機證明的接續路徑，且第二個 Session 不必讀本開發計畫、另收臨時口令或要求 Owner 填內部資料。證據不足時須指出具體缺口，不能以無限重查代替恢復能力。

**分級 CRITICAL。** 本次文件寫入可逆，但方案涉及未知派送的終態判定與再次下載；判錯可能重複副作用或破壞永久記憶。保留人類啟動的計畫 Simplicity Review、獨立 Plan Review、首切片 Simplicity Review 與獨立接受。這些關卡不取代以日常入口確認實機能力。

選定最小方案：先以既有查詢、事件、v2 evidence 與恢復 intent，補上 Skill／references 的操作方法及證據取得條件。**目前不修改 CLI、事件格式、公共介面或安全 gate。** 原生 CUA 是否能保存原件、LINE 是否能提供充分取消／停止觀察仍待實測；沒有證明的分支明列未支援。首切片即此文件候選，之後經適用審查及日常實機確認，不能先宣稱可恢復。

非目標：修復第一支影片的 `LOCAL_CHANGED`；刪除／解除第二支的 `UNKNOWN`；技術歸因整機斷網與 CUA 失聯；新增 GUI 控制器、下載 API、重試器或觀察服務；相簿流程；其他列表；補下載已完成項；合併 master。

## 範圍與基準

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；branch：`feature/line-notes-media`。
- 起始 HEAD 及本輪唯讀核對的遠端分支 HEAD：`26c165b181480575d3de5e3549b40e2dcea5eacf`；起始 index、dirty、untracked 皆空。其他 worktree 與忽略的私人任務／備份資料保留。
- 根因報告調查的起始候選為 `8108397ddc754db1d78d035edede38a0b017425f`；本版不把目前 HEAD 當前次整個 GUI Session 的版本證明。
- 本輪可寫：本目錄 `plan.md`、`handoff.md`、`progress.md`、`role-report.md`，及專案內忽略的 `.local/line-backup/tasks/20261107-notes-interruption-replan/`。前輪文件不改。
- 來源版本、大小／SHA-256 與命令原件存私有任務區 `sources-before.json`、`commands.json`；公開文件只放去識別結論。沒有重新讀取真實帳本或驗證私人媒體；前輪 19 筆事件與 429 份來源校驗是前輪結果。

計畫經 Owner 採納後，Implementer 首切片的產品白名單限以下六檔；不是本輪編輯授權：

| 路徑 | 有界用途 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | 啟動時指向恢復本文；修正 memory 目的地敘述，不複製交易流程 |
| 同目錄 `references/download-and-ledger.md` | 唯一交易順序：找回、持久 checkpoint、重新綁定、對帳預覽、原 attempt 接續或新 recovery intent |
| 同目錄 `references/verification-and-recovery.md` | 中斷階段矩陣、晚到／停止證據判準、未支援分支及 LOCAL_CHANGED 邊界 |
| 同目錄 `references/gui-inventory.md` | 當次 CUA 文件、AX／截圖落檔與讀回；stale 後新觀察、前景失聯停止 |
| 同目錄 `references/evidence-template.md` | 重用既有欄位，明定中斷 checkpoint 的最低引用與已知／未知呼叫範圍；只是 statement，非 schema |
| `docs/LINE相簿備份_使用手冊.md` | 修正 memory 描述與實測限制；第 5 節正式 Prompt 文字及日常啟動步驟保持不變 |

Implementer 另可在本計畫目錄新增 `behavior-cases.md`、`implementation.md`，證據存本任務私有區。若檢視顯示某檔不需改，不為湊白名單修改；若需改第七份產品檔、程式或測試，先交 Owner 決定範圍，不在實作中擴充。

禁止寫入：`src/`、`tests/`、相簿 Skill、`AGENTS.md`、`backup/`、兩種永久帳本／index／active 檔、舊 tasks／原始證據。不能手寫事件／bundle、清 staging、刪尾事件、改 UNKNOWN、強退／重啟 LINE、整機斷網、換目的地解鎖、排除／保護活動交易。真實任務後續只允許 Owner 精確授權的追加，不因本計畫產生授權。

## 已有能力與限制

| 已核對事實 | 對方案的影響 |
|---|---|
| `notes.py:3076` 的 `unresolved_attempts` 已有 `attempt_id`、`media_key`、`scan_id`、`destination`、`has_outcome`、`last_result`、`pending_naming`、`scan_binding_match`、`source_availability` | 不新增查詢命令。摘要只列每媒體最新未決項，不是完整 intent／歷史／completion；用原事件補細節 |
| `notes.py:1801` bind 不改舊 scan，上一個 scan 未完成會拒絕 | 新 Session 使用新 ID，不重用舊 ID、先開新 scan 或重建帳本來解鎖 |
| `notes.py:2735`／`:2755` 已有 outcome／reconcile；原 intent context 用於 evidence | 無 outcome 先 outcome；已有 UNKNOWN 才 reconcile，終態不再改寫。CLI 核對證據結構，不判語意真實 |
| `notes.py:2646` 已有 recovery intent，建立新 staging 並保存 `recovery_of` | 不新增恢復交易格式。必須先 STOPPED／NOT_SENT、原授權持久為 true、有 recovery evidence、最新完整盤點及其他 gate 皆滿足 |
| `notes.py:2562`、`:3600`、`:3651` 的本機完整性 gate | LOCAL_CHANGED 不直接擋 bind／outcome／reconcile，卻擋新 intent、verify、resume。對帳成功不能推成能驗證或重新下載 |
| `notes.py:2155`、`:2462` 的 scan gate | UNKNOWN／待驗／命名交易先在原 scan 處理；verify／resume 要原 scan binding。STOPPED／NOT_SENT 後若需新盤點才另開，恢復 intent 仍須最新完整 scan 的 post／media |
| `notes_capture.py:211` 保存一次 CLI child，`notes_evidence.py:397`／`:423` 封裝／保存 bundle | 都不會擷取 CUA 畫面。包裝成功、hash 相符、exit 0 不能證明取消生效或原操作停止 |

以上來自本輪程式唯讀核對與同角色 helper；行號僅供此基準定位，接手仍須核對版本。未跑產品回歸，未簽發獨立接受。

## 恢復方法候選

### 1. 先證明原件可保存，再讓交易進入不可盲重送階段

Implementer 將以下決策整合進現有 references；不臆造 API、寫死舊座標或依賴下一個 Agent 另讀開發報告：

1. 當次依工具入口讀原生 CUA 文件；辨別截圖回傳是本機路徑、影像資料或只有顯示。只採當次明示支援的保存方法，記錄實際 API／回傳型別／權限及範圍。不能用不存在的 `save` 方法或換成另一 GUI 通道。
2. 在已授權觀察內，把當次 AX、截圖及輸入原始回傳保存為私有任務內非 symlink、單一 hard link 的 regular files，重新讀取／閱圖並核對範圍；再用既有 `evidence-pack` 讀回 context 與子 blob。若工具只提供畫面而不能保存，**停在新 intent 前**，回報是哪個原件、回傳型別與缺少能力，不能先派送再補。
3. `notes_capture` 只包 CLI，一次 child 後保存失敗不重跑；CUA 回傳需另存。下載控制與 chooser 確認分開保存，error／timeout 也算該次呼叫；未涵蓋的歷史記 UNKNOWN，不填零。

真正證明「可保存」需要當次工具與落檔原件；離線文字案例僅驗決策。無 GUI 授權的 Implementer 不開 LINE 或取得私人畫面，能力實證留待下面 G1。

### 2. 讓下一個 Session 自行還原原交易

日常入口保持 `lists` → active-notes 輔助定位 → 相符帳本 `memory`／必要的 `evidence-audit`。在有效任務與前景內確認三層身分，以新 Session ID bind；若 bind／scan binding／完整性拒絕就停，不換入口。

Agent 從摘要與原 events 唯讀建立最小交易引用：原 attempt／intent event 的 sequence、檔案 SHA-256、五層 context、原 staging 與 device／inode、全部 outcome／reconcile、最新可靠觀察與錯誤、已呼叫控制的範圍、chooser 三層目的地。沿事件引用讀帳本 `evidence/<manifest-hash>` 與同層 blobs；它不是 `evidence/<hash>/bundle.json`。任務區封裝才可能有 `bundle.json`。

重用 `evidence-template` 已有欄位，不建第二份事實來源或新的 active 檔。每次觀察追加新檔與引用；中斷時先保存能取得的原件、第一筆真實 outcome（無結果可 UNKNOWN）與錯誤。若帳本寫入未確認，先查 event，不重跑 writer 補 receipt。不能把缺失歷史反填為「沒呼叫」。

### 3. 依中斷階段選唯一下一步

| 中斷位置／現況 | 可執行的觀察／候選方法 | 既有命令與允許前進 | 必須停止的情況 |
|---|---|---|---|
| intent 後、儲存面板前 | 查原呼叫與回傳、當次 viewer／chooser／原目的地；沒有呼叫紀錄不等於沒有副作用 | 無 outcome 先 `outcome`；有 UNKNOWN 且有新資訊才 `reconcile` | 只有零計數、空目錄、timeout：保留 UNKNOWN，不再按下載 |
| 原 chooser 仍可唯一辨識、Go to Folder 中 | 新鮮 AX／畫面、焦點、process／視窗及原 attempt 連續性；路徑修正與取消分開處理，見下節 | 確認尚無第一筆 outcome 且完整路徑／三層一致、最終確認確未呼叫時，才可能接續**同一** chooser 的一次確認 | 已有 outcome UNKNOWN 時不直接繼續確認；先走終結／對帳。舊 handle、來源不明、呼叫歷史不全或窗口失聯即停 |
| 最終確認的回覆遺失 | 尋找原操作正面終結、原目的地可歸屬穩定檔；確認呼叫即使 timeout 也已用掉 | 充分晚到結果 → 原 attempt `reconcile DOWNLOAD_FINISHED`，再依 gate verify | 不第二次確認；面板消失／空目錄不能判 STOPPED |
| 下載中或進度不可得 | 原 attempt 的進度／終結、目的地與檔集；不點下載查進度 | 完整候選結果才對帳為 DOWNLOAD_FINISHED；其他保留 UNKNOWN | 不用播放結束、單一 toast、單一檔名／hash 或固定等待時長當完成／停止 |
| 已下載、驗證或命名中斷 | 查 outcome、completion、原 scan 與 publish journal | DOWNLOAD_FINISHED → verify；pending naming → `resume` 同交易；已有完成則跳過 | LOCAL_CHANGED、scan 不符、非唯一下一步或 manifest 漂移即停，原件保留 |
| 已有充分 STOPPED／NOT_SENT | 讀回追加終態；保留原目錄／檔案，再核對全列表 blockers、完整盤點、恢復授權與來源可用性 | `intent --recovery-evidence` 引用原 attempt context；讀回新 staging／recovery_of，再依既有至多一次規則下載 | 第一支 LOCAL_CHANGED 仍存在就不得 verify／resume／建立新 intent；不以換 root 解鎖 |

### 4. Go to Folder 分支的取消實證與停止判準

優先實證本次失敗分支。這是待 Plan Review 核定的證據判準，**尚無可直接套用的充分停止 receipt**：

1. 先以新觀察唯一辨識原操作及其 modal 層級。Go to Folder 子面板的取消只可能回到父儲存面板；它不等於取消整筆儲存。辨識不明就不輸入。
2. 在 Owner 明確同意的範圍及有效前景內，以當次可定位、明確作用於該層的取消控制逐層處理，每步各保存前畫面、一次原始回傳、後畫面。不能猜 Escape／Return／Command-W，不能強退 LINE，也不能在一次預寫呼叫裡連按兩層。
3. 候選停止組合須同時支持：原 viewer／attempt／chooser 的唯一連接；**原儲存分支已被 App 正面終結，且終結涵蓋可能仍待執行的該分支確認／寫入**；CUA 沒有尚未回覆、可能晚到的輸入；原目錄身分與現有檔案保留。穩定檔集、回到 viewer、取消按鍵 receipt 或視窗消失只能補強，任何單一項都不充分。
4. 若 LINE／CUA 沒提供能支持第三點的可觀察訊號或已核對語意，取消後仍保留 UNKNOWN。記下確切欠缺的 App 回應／工具能力，不能把靜置 N 秒無變更變成停止證明。`NOT_SENT` 另需正面未派送證據；取消已呼叫的原控制不反推從未派送。

停止判準限定原 LINE 儲存操作及本機寫入生命週期，不要求證明服務端從未傳輸。它也不承諾永久排除非合作程序或未來其他操作者寫檔。獨立 Plan Review 必須判斷此界線是否可操作且充分；若只能證明面板關閉，結論是**本分支未支援**，交 Owner 決定是否另研究環境處置，不能交 Implementer 自行降低標準。

### 5. 先預覽，再追加對帳，最後才檢查恢復資格

當次已有足夠新證據時，Agent 在私有任務區保存精確預覽：帳本與目前 chain tip、原 attempt／context、原 outcome、新候選 result、bundle/hash、理由與剩餘 blocker。這是可讀紀錄，不新增 dry-run 命令、grant 或 schema；沿用既有有效授權，不要求 Owner 為已授權的每筆步驟重複確認。

只有授權涵蓋該追加且證據符合已核定判準，才以原 CLI outcome／reconcile 寫入，保存 receipt、事件 sequence／hash，重讀摘要與 audit。若 tip、來源、檔案或前景改變，停下檢查，不以無限重查宣稱原子性。LOCAL_CHANGED 可讓對帳追加仍有價值，但它會保留驗證／新派送的阻塞。未取得新證據不重複 append UNKNOWN。

## 替代方案、風險與可保證界線

| 方案 | 決定與取捨 |
|---|---|
| 只補 memory 的 destination 文字 | 可修漂移，無法填補證據保存及原操作終結方法；不足以完成目標 |
| 既有 CLI＋有條件的操作本文／實機實證 | 選定。保留交易與資料語意；有能力缺口就如實阻塞，不能保證此舊 UNKNOWN 一定可收斂 |
| 新增 checkpoint schema、CLI resume 控制器或自動 retry | 既有事件／statement 已能記必要引用，尚無缺欄位證據；增加相容性與權限風險，不採用 |
| 刪 UNKNOWN、空帳、新目錄、重按或強退後推定停止 | 不符合資料／副作用邊界；不作修復路線 |

來源、GUI、CUA 回傳、本機檔案及帳本沒有共同原子交易；lock 只約束合作 CLI。外部 writer、來源成員修改、工具通道失聯或當次不能存圖都可能阻塞。不得宣稱 exactly-once、OS 隔離、平台 dispatch 保證、跨模型必然可靠，或以設定推 provider／成本。文件可由後續正常提交回復；事件／完成事實及媒體不可回滾或覆寫。

## 首切片、成功條件與必要檢查

**R1 首切片即文件候選**：上述六檔內的必要修改＋`behavior-cases.md`／`implementation.md`；沒有可驗證的新停止方法時，明列未支援，不把文件寫成修復成功。首切片完成即停止，由 Owner 啟動 implementation Simplicity Review。無程式修改不新增字串快照或模仿文件的單元測試。

| 檢查／owner | 成功證據 | 停止條件 |
|---|---|---|
| P1／Planner（本輪） | Git 基準、來源 hashes、文件連結／UTF-8、白名單、diff 空白檢查與角色邊界；命令／exit 留任務區 | 基準或必要來源不明，不能交可執行草案 |
| P2／Owner 啟動計畫 Simplicity Reviewer | 對精確規劃提交檢查既有能力可重用、範圍及首切片是否最小 | 拒絕後交 Owner，不自修／轉角色 |
| P3／Owner 啟動獨立 Plan Reviewer | 核定取消／停止判準、缺能力時停止的可操作性、資料與 GUI 邊界、下列 G1–G3 的實證範圍 | 判準不可實現或需放寬 UNKNOWN 時保留阻塞，不能以「實作時決定」通過 |
| V1／Implementer | R1 行為演練：每例列已知／未知、實際讀取來源、允許的唯一下一步、禁止動作與停止原因，輸出引用原件／行號 | 負例能走到再次下載或把取消 receipt 當充分即失敗 |
| V2／Implementer | 六檔一致、相對連結、diff 範圍、正式 Prompt 未變、`git diff --check`；現有命令／事件沒有變更 | 須改程式／介面／第七檔或另加 Owner 啟動步驟即停 |
| V3／Owner 啟動首切片 Simplicity Reviewer | 精確首切片與 V1／V2 證據；不因首切片已是最終候選而略過 | finding／拒絕交 Owner，helper 不簽接受 |
| G1／Owner 日常任務的實機 Agent | 同一正式 Prompt；先找原交易、新鮮原件實際落檔及讀回、bind／scan gate；無下載也可先證明保存能力 | 無適用任務／前景／觀察權限，或無法保存原件就停；不新建 intent |
| G2／Owner 精確允許的原 chooser 操作 | 優先 Go to Folder：取消前後各層原件、原始回傳、App 終結依據與 pending input 範圍；由證據決定對帳或仍 UNKNOWN | 原 chooser 不存在／不可歸屬或停止證據不足，標 BLOCKED；不為重現而再按原下載 |
| G3／Owner 日常任務的接續 Agent | 若 gate 全成立：晚到結果在原 attempt 驗證；或 STOPPED／NOT_SENT 後新 recovery intent→至多一次派送→媒體完整驗證→completion 讀回；下一 Session 跳過完成項 | 原 LOCAL_CHANGED 未解仍不可跑 verify／resume／intent；G1／G2 成功也不免除此限制 |
| A1／Owner 啟動的獨立接受者 | 對精確候選逐條比對 V1／G1–G3 原件、帳本追加與媒體結果；必要時在另行授權的日常任務自行操作 | helper／實作者不能獨立接受；未測階段、媒體與跨 Session 情境維持 NOT_RUN |

V1 至少演練：不能存圖則在 intent 前停；無 outcome crash window；只有空目錄與舊零計數；stale 後不得沿用 handle；子面板取消不等於父儲存終結；最終確認回覆遺失不得再確認；晚到結果歸原 attempt；有充分合成停止證據才候選恢復；LOCAL_CHANGED 不擋對帳卻仍擋 verify／intent；scan mismatch、pending naming、退出碼 4／70 與外部狀態變更。既有 `evidence-decision-cases.md` 可直接引用，不複製成新規格；新增演練資料標 SYNTHETIC，不能宣稱真的取得停止 receipt。

若原帳本無法進 G3，不刪 LOCAL_CHANGED 以完成本計畫。Owner 可另指定一份允許備份的測試列表與獨立帳本，驗證恢復能力；須在日常入口下有精確任務／前景與中斷交接範圍，不能混入原帳本、重下原完成項、修改 LINE 貼文或斷整機網路製造故障。這種結果只支持指定測試情境，不代表原任務完成。

純文件 R1 不新增程式測試；V1／V2 為必要檢查。進入整體產品接受前，仍由 Owner 指定的驗證者對精確候選執行專案最小回歸並保留命令／exit：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

現有 `test_notes_records.py` 已含 UNKNOWN／恢復／LOCAL_CHANGED；`test_notes_regressions.py` 已含 recovery graph／scan gate；`test_notes_evidence.py`／`test_notes_capture.py` 已含證據與單次 child。它們不能代替實機。若另核准 CLI 修正，再評估只補「LOCAL_CHANGED＋另一項 UNKNOWN＋新 Session 對帳後仍拒絕 verify／新 intent」的隔離合成組合；本版不預先擴成程式工作。

成功須分三層報告：R1 文件及行為演練、實機恢復能力、原列表實際完成。只有 G1–G3 有相符原件且 A1 獨立確認，才可聲稱指定情境具恢復能力；第一支 LOCAL_CHANGED 獨立解決、原第二支有 completion 且完整對帳成立前，不得稱原列表全部完成。不能推廣為所有模型／版本每次成功。

## 人工檢查點與停止

下一步只建議 Owner 以本版共同提交另開主 Session 啟動**計畫 Simplicity Review**；之後由 Owner 決定獨立 Plan Review、Implementer R1、首切片 Simplicity Review 與日常實機／獨立接受的交接。Planner 不自動派發下一正式角色，不接受自己的計畫。

P3 必須明確決定停止證據判準與實證授權的界線；G2 前須有當次精確取消範圍，G3 保留既有 `recovery_authorized=true`，不再要求重複授予相同備份意圖。本輪既沒有前景交接，也未授權任何取消／帳本追加／下載；有 GUI 實證需求不代表現在可執行。

版本不符、拒絕、身分歧義、原件無法保存、前景失效、未知輸入、寫入衝突、需要強退／資料修復／擴介面或放寬安全判準，即停依賴該前提的動作並交人。原 stale／cgWindowNotFound 的無新資訊恢復查詢歷史保留，不因換 Session 重播。同根因最多三次有證據嘗試、兩次無新資訊就停；歷史總額不完整為 UNKNOWN，不能自稱又有三次額度。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

REQUIRED_VERIFICATION 指產品／行為／GUI 必要驗證；本輪 P1 文件與來源檢查另列 progress／role-report。計畫草案完成不等於修復完成或產品 PASS。
