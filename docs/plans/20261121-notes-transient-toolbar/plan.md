# LINE 記事本短暫工具列與中斷接續修復計畫

修訂版 v3。保留已核准的 v2 契約，依候選 v2 的第二輪 Code & Security Review `REQUEST_CHANGES` 補列三項最小修正。複審的新增範圍及通過條件見「第二輪審查修訂」。

## 目標與基準

以同一份正式記事本 Prompt 啟動。Agent 使用既有 Skill 和原生 CUA 核對目標。工具列在 intent 前可見、讀回 intent 後消失時，若已有合格的安全方法，Agent 自行顯示工具列一次。中斷後，Agent 依帳本判定接續原交易、隔離後補下載，或保留欠件。平常無需 Owner 判讀每個媒體。

修訂基準是 `Line_backup` 的 `feature/line-notes-media`，本機 HEAD `3e2b1dbbd5d5444e8c100ddb6d276a10804e9023`，受審公開候選 `bb88c92395d7aad125089176045752079ccf1dde`。兩者的七份修復檔一致。保留既有 `AGENTS.md` 修改與 `.playwright-mcp/` 未追蹤目錄。沿用 STANDARD，修正集中於既有 Skill 範本與其合成測試，但會碰觸可派送 GUI 輸入的邊界，需獨立計畫複審及候選的 Code & Security Review。

- 11/19 報告記錄 G 的兩次 `NOT_SENT` 與 Gis 的 `UNKNOWN`。三次都在可見觀察和 intent 讀回後找不到下載控制，未觀察到 chooser 或檔案。空 staging 只描述讀取當時。工具列消失的精確觸發、存活時間及下載命中均未量測。[TOCTOU 提報](../../問題提報單_記事本TOCTOU與reveal派送抽象錯置_20261119.md#4-時間線與證據判讀)
- `65ecad9` 已把正式的下載定位移到 intent 後。本輪候選已具備 DIRECT 與 REVEAL 預檢、intent 後重核與固定 slot。Reviewer 證明可複製範本的跨區塊宣告與分支求值會中斷，並重現部分原件過期及請求突變仍觸發輸入。基準原始碼已核對到對應判斷與非同步邊界。[B1](../../../.agents/skills/line-notes-agent-cua/references/gui-inventory.md#目標與下載控制就緒b1) [可執行範本](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md#intent-前下載就緒-gate)
- `3bb6fcb` 已實作 `UNKNOWN` 隔離、每媒體單次 v5 補下載及安全耗盡後續行。原切片 B 修正正式 Prompt 的隔離條件，Reviewer 核對受審版本已對齊 CLI phase 與接續驗證補件。[正式 Prompt](../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt) [帳本實作](../../../src/line_backup_batch/notes.py)
- 11/20 另有下載 helper 在呼叫前因 `APP_WINDOW_CONTEXT_REQUIRED` 拒絕。現有就緒 gate 會提早攔缺 ID。現有證據只支持該次未取得 ID，平台能否取得合格 ID、當次是否可用及 hover 是否可用仍待查明。保留原 gate。[11/20 提報](../../../問題提報單.md)

## 切片 A：依五項審查發現修正範本與安全邊界

### A1 · Finding 1 · 同一 REPL 的選路與派送

- intent 前只在分支啟用時建立其 decision。可見時才求值 DIRECT 欄位。可見性已知且安全 reveal 方法獨立成立時才求值 REVEAL 欄位。未啟用分支的佔位符可完全未宣告。可見但 DIRECT 不合格時，停止建立 intent，即使備選 REVEAL 合格亦同。
- 將直接派送範本的 `directDecision` 改名為 `directDispatchDecision`。保留同一 REPL 的 `retainedReveal`，只把 REVEAL 的 `READY` 留到 intent 讀回後。最多建立一筆 intent。預檢的 capture、GUI 輸入、固定 slot 寫入及額度消耗均為零。
- **通過條件**。從 Markdown 抽取實際可複製區塊，依序跑預檢、intent 讀回、唯一 capture 與所選派送。每個案例有獨立 Node 程序，案例內各區塊共用頂層作用域。依實際路徑執行適用區塊，包含候選 2 適用範例。只代入臨時測試路徑及有證據的 fixture 值。保留原宣告及區塊順序，未用分支的識別字保持未宣告。沿用現有 Node／unittest 執行器。逐塊語法檢查與仿寫選路皆無法替代此回歸。

| 合成事前情境 | 應選結果 |
|---|---|
| 可見，DIRECT READY，備選 REVEAL READY | DIRECT，保留同次合格備選 |
| 可見，DIRECT READY，無安全 reveal 方法 | DIRECT，備選欄位不需宣告 |
| 可見，DIRECT READY，備選 REVEAL STOP | DIRECT，`retainedReveal=null` |
| 隱藏，REVEAL READY | REVEAL，DIRECT 欄位不需宣告 |
| 可見性不明，或隱藏且無合格 REVEAL | 各自停止於 intent 前，零輸入 |
| 可見，DIRECT STOP，備選 REVEAL READY | 停在 intent 前，零輸入 |

### A2 · Finding 2 · 兩份 intent 後原件都需獨立更新

- 在 `checkRevealBefore` 判定新鮮度時，只要 observation ID 重複，或截圖、AX 任一對應原件的路徑或完整 file ref 重複，就回 `REVEAL_BEFORE_OBSERVATION_NOT_FRESH`。即使同一路徑的 hash 或長度改變，仍拒絕重用。沿用 request 與 observed assets 的配對檢查。兩份新擷取各有新路徑時，允許內容 SHA-256 恰好相同。
- **通過條件**。分別測僅截圖過期、僅 AX 過期、路徑重用但其他 ref 欄位不同及 observation ID 重用。各案均拒絕，零 click、零 reveal-after capture、零 reveal slot 寫入。另測新 ID、兩個新路徑及相同內容 hash 可通過其餘適用 gate。

### A3 · Finding 3 · 驗證、落地與輸入使用同一份請求

- 由 `evidenceTools` 匯出既有 `snapshotJsonValue`。`persistReveal` 在第一個 `await` 前建立與呼叫端巢狀物件脫離的私有 JSON request 快照。缺參數或快照失敗回傳具原因的 STOP。以該快照執行 `checkReveal`、`checkRevealBefore` 和 `persistRevealWithDirectAfter`。既有固定 slot 先寫入並讀回，再由已驗證的讀回值取得實際 target。live app handle 沿用原介面，保留其方法接收者。
- 同步保存校驗通過的 ordinal、事前 observation ID、intent 後 before observation ID。回報使用這些定稿值。其他輸入路徑沿用既有序列化與派送契約。
- **通過條件**。以 stub app 和確定的非同步時序，在呼叫後、request 持久化前改動呼叫端的巢狀座標、安全區、候選 ordinal 及 observation ID。核對磁碟 request、實際 mock target 和回報 metadata 仍一致採用原已驗證值，且只有一次預期輸入。不可完整序列化的 request 必須在 slot、click 或 after capture 前 STOP。

### A4 · Finding 4 · 保存 capture 到下載呼叫的 host 時間邊界

- 在 intent 後唯一 capture 的 `app.getAXStateAndScreenshot` 呼叫前及結束時記錄 `capture_call_started_at`／`capture_call_returned_at`。把 `hostCalls` 隨 observation ID 存入既有 observation diagnostic，執行原有讀回檢查。沿用 capture 拋錯處理與現有 reveal-after 的時間資料。
- 在原 grounded click callback 呼叫 `click(target)` 前及結束時記錄 `dispatch_call_started_at`／`dispatch_call_returned_at`。沿用 dispatch context，把 `hostCalls` 帶入 receipt 與同一 operation ID 的既有 diagnostic。拋錯也記結束時間及原失敗狀態。gate 或 slot 在呼叫前拒絕時，相應時間欄位維持 `NOT_RUN`。欄位僅加在本機診斷證據。
- 保留 `clock_source='HOST_JS_DATE'`、`precision='CALL_BOUNDARY_ONLY'`、`os_event_time='UNKNOWN'`。以 DIRECT 共用 capture 或 REVEAL 同次 after capture 的結束，對到下載呼叫起點。缺值、時間來源不可比或時鐘倒退時，延遲記為不可判定。時間證據只表示 host API 呼叫邊界，工具列壽命、OS hit-test 與下載結果各依自身證據判定。
- **通過條件**。以 mock 驗證成功、拋錯及輸入前拒絕的欄位、先後與狀態。核對 DIRECT 與 REVEAL 選用的時間對應正確原件，回傳與已讀回的 diagnostic 一致。量測增加的 capture、click 和 retry 次數均為零。

### A5 · Finding 5 · 共用一次 intent 後 capture 與補足拒絕測試

- 將 Block 9 改名為「intent 後唯一 capture」，以 `intentObservation` 和其 capture 結果接到兩條路徑。DIRECT 從共用原件取得定位及截圖 bytes。確定控制未見且安全門檻成立時，Block 12 直接以同一變數作 `beforeObservation`，移除 `FRESH_INTENT_OBSERVATION` 佔位符。REVEAL 仍要求同一 viewer／window、有效前景、選取及身分一致、無 chooser／活動下載／未決輸入、保留的 READY 和原額度。證據不足、已有下載呼叫或 outcome 時沿用原停止規則。
- REVEAL 後的同一 callback 仍取得該次輸入的 after。需由 Agent 以同一份 after 與同一 window 核對控制和映射，才以原 helper 派送下載。after 失效沿用停止規則，禁止重拍再點。核對與派送之間維持原來的最短路徑。保留每 attempt 一次 reveal、每媒體兩次 reveal 額度、候選 2 新證據、固定 slot、下載和 chooser 最終確認各一次。輸入開始即耗原額度，`UNKNOWN` 與 `NOT_SENT` 沿用原判定。
- **通過條件**。以 A1 的真範本測可見→仍可見、可見→隱藏與起始隱藏。成功 DIRECT 有一次 intent 後 capture、零 reveal、一次下載。成功 REVEAL 有一次 intent 後 before capture、一次 reveal 及其一次 after capture，下載使用該 after。另測「事前 DIRECT READY＋REVEAL STOP，intent 後控制消失」，共用 capture 後零 reveal、零下載、零重拍。
- 分別測 `preIntentReveal` 缺值、STOP、DIRECT，以及 `candidate_ordinal`、`budget_before`、`budget_after`、`prior_candidate_refs` 漂移。斷言具體拒絕原因。需要結構合法的比較時使用各自合法的候選資料。單欄改動若本身破壞 ordinal／budget 契約，驗證是原 gate 提前拒絕。各拒絕案例均零 click、零 reveal-after capture、零 slot 寫入。

## 切片 B：正式入口的自主接續

1. 以 `unresolved_attempts` 的 `has_outcome`、`last_result`、`attempt_phase` 及原事件辨識待辦。重新取得有效前景及 bind 後讀當次摘要。先依真實證據記第一筆 outcome，已記 `UNKNOWN` 只在新結果證據足夠時 reconcile。原交易已完成下載就用原 `download-check`，待命名走 `resume`。
2. 原結果仍不明時，由 Agent 自行核對同一項、原目的地、舊空 staging、有效前景、持久恢復資格，並排除 chooser、可歸屬活動下載、pending naming、檔案／身分異常及手動 restart。首筆可安全隔離的 `UNKNOWN` 依 `isolate` 的 `RECOVERY_SCAN_REQUIRED`，由目前綁定 Session 完成隔離後新普通掃描與目標細盤，B1 合格後僅一筆 v5 intent。若之後補下載又不明，在相同安全前提下隔離，按 `RECOVERY_EXHAUSTED` 留欠件並自動續做其餘合格項；該次隔離不需剩餘額度，也不建立第三筆自動 attempt。
3. Agent 以各自媒體的持久事件及時序判斷額度，不從列表總覽或其他媒體狀態猜測。摘要只提供既有欄位，不臆造數值。晚到檔留原 staging，未安全隔離的交易仍停止所有新派送。已證實 `STOPPED`／`NOT_SENT` 的精確恢復、restart／reattest、命名及資料異常維持各自現行 gate。前景中斷後須重新取得有效交接；接續的業務判斷由 Agent 依持久紀錄完成。

## 複審交接與驗證

- **當輪交付**。只修改本計畫，交由 Owner 提交獨立 Reviewer。以本機、公開基準及隨交付提供的計畫 SHA-256 綁定版本。前次計畫通過不涵蓋本版。
- **複審通過後的實作範圍**。僅 `.agents/skills/line-notes-agent-cua/references/evidence-template.md`、`tests/test_notes_input_helper.py`。切片 B、`test_notes_unknown_recovery.py`、驗證補件、Python 產品碼、帳本和公開資料格式維持受審內容。這次沿用原 helper、固定 slot、觀察原件與診斷路徑。保留現有 Git 工作。
- **首個可驗證切片**。實作者在上述兩檔完成 A1～A5，先執行輸入 helper 回歸並保存逐項測試名稱、命令、退出碼、測試數及關鍵 mock／diagnostic 證據。用乾淨的合成環境確認新測試可區辨受審版本與修正版，再跑全套。若拒絕案例出現 GUI 輸入或 slot 寫入，或範本驗證拆散了共用作用域，停止交付並保留證據。
- **審查與產品驗收**。Owner 交接計畫複審、實作後簡化檢查及獨立 Code & Security Review。Reviewer 以精確候選核對 A1～A5 和當次測試。真實 LINE 的 E1～E3、chooser、檔案落地、completion 與跨 Session 接續另須有效前景及任務授權，沿用正式記事本 Prompt。
- **狀態與停止**。原候選的 `REQUEST_CHANGES` 仍生效。Reviewer 回報的 40／17／356 測試是受審版本的既有結果。新回歸、實機與獨立產品驗收均為 `NOT_RUN`。計畫複審通過前停在本交接。

核准後由實作者執行下列檢查。Reviewer 核對相同候選及其結果。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_input_helper.py'
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes_unknown_recovery.py'
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
git diff --check
```

複審以 A1～A5 對照 Findings 1～5，核對每項通過條件及兩檔範圍。若需變更路徑、資料邊界或驗收條件，交由 Owner 決定。

## 第二輪審查修訂

基準為本機 HEAD `1528e58a899625773861051204b41595bd1abba9` 上的兩檔未提交候選。受審 diff SHA-256 為 `3cc82308d6806482c8ce489968178aea2ccae654f25ce8d040cb93f3474abc8f`，原 v2 計畫 SHA-256 為 `89990d483de0ee333e72caacb751bb87ef10649b307f37f28f75f75b25af7ce5`。Reviewer 已確認 A2～A5 核心機制及檔案範圍合格。A1 與既有安全回歸補正如下。實作範圍沿用上述兩檔，保留已通過的 v2 變更、切片 B 與工作樹既有檔案。

1. **候選 2 的實際事前預檢。** 修正 `evidence-template.md` 在 `notes-intent-preflight` 前的說明。只在啟用的 REVEAL 區塊內讀取 `REVEAL_CANDIDATE_ORDINAL`，以區塊作用域資料建立符合當次選擇的 arm。候選 1 為 `0→1`、`NONE`，不求值候選 2 專用欄位。候選 2 為 `1→2`，需保存可信 prior refs 及既有 rearm 條件與新資訊。無效 ordinal 依既有 gate 停止，不默認成候選 1。intent 後用同一候選、額度與前次引用重核，保留新鮮證據與既有漂移拒絕。移除測試的 `CANDIDATE_TWO_PRELUDE`。以真實 `notes-intent-preflight`、讀回、擷取、reveal 與 after 下載區塊在同一 Node 作用域依序執行。斷言事前 READY 的 ordinal、候選引用與派送 request 一致，原件及固定 slot 檢查成立，並確認一次 before capture、一次 reveal、其一次 after capture 和一次下載。沿用現有候選 1 與兩路計數測試。
2. **停在預檢時不求值未啟用欄位。** 將 `commonDecision` 改為只在啟用的 DIRECT 或 REVEAL 分支內求值的建構方式。`B1_CONTROL_VISIBLE=null` 或隱藏且無可用 reveal 時，測試 fixture 完全不宣告 `CURRENT_*`、`REVEAL_CANDIDATE_ORDINAL` 或候選 2 欄位，執行原範本並斷言 `B1_LOCAL_STOP`，零 capture、click、intent 動作與 slot 檔。追加可見 DIRECT 且無 REVEAL 的斷言，確保不讀取 ordinal。
3. **補回稀疏陣列安全回歸。** 在既有 invalid prior-ref 測試保留 `[42]` 並補回 `Array(1)`。前者驗證型別限制，後者驗證稀疏陣列在 `checkDownloadReadiness` 回 STOP 含 `REVEAL_ORDINAL_BUDGET_MISMATCH`，在 `persistReveal` 由同步 JSON 快照回 STOP 含 `REVEAL_REQUEST_SERIALIZATION_FAILED`。兩案都應零 click、零 after capture、零 slot 寫入。沿用既有 fixture、測試方法與兩階段 gate。

交接依序為 v3 計畫複審、兩檔最小實作、完整回歸，再以新候選送獨立 Code & Security Review。Implementer 留下逐項對照三個 finding 的測試名稱及執行證據，並提供計畫、兩檔與合併 diff 的 SHA-256。至少以原 v2 候選與修正版對照前兩項可複製範本測試。稀疏陣列屬補回的保護證據，獨立核對兩層拒絕及零副作用。其餘 v2 通過條件與整合命令沿用。新候選審查在相同雜湊下明確 `APPROVE` 後，才交由 Owner 沿用正式記事本 Prompt 進行實機測試。
