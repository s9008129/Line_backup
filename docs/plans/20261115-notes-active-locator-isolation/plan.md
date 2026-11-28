# 記事本測試 active locator 隔離修復計畫

## 決策摘要

狀態：`PLAN_DRAFT_COMPLETE`。以下保留初稿基準與檢查定義；最新執行授權見本節。計畫本身不代表實作或驗收。

2026-11-15 Owner 後續明示指定本 session 為 Planner 及修復總指揮，要求直接管理最多三個 Herdr Worker panes，以 Codex CLI `gpt-6-luna/high` 完成單檔修復，完成後由 Luna 子代理撰寫詳細提交訊息，再 add／commit／push；並明示不必重啟。本 session 依此新授權協調執行，不再以初稿的「只規劃」限制停止。先前 Herdr／Git 權限拒絕保留為歷史；當前 Herdr live 操作已成功。

Owner 隨後明確選擇：「保留單檔修復，完成安全檢查與提交；完整 notes suite 標 NOT_RUN」。因此 V8 不屬本輪必跑關卡，V5 盤點所見 locks child 模組隔離疑慮列為後續事項，不擴檔、不以未隔離 suite 冒險驗證。修復交付依 V0–V4、V6–V7、候選 peer 核對與文件／Git 檢查；原正式獨立接受及實機備份仍不包含在本輪授權成果內。

本輪選用 **兩個** Worker panes：Worker1 單獨持有實作檔；Worker2 先唯讀核對計畫及廣回歸的安全前提，候選形成後做未參與實作的同任務核對，最後梳理上下文撰寫提交訊息。主 session 整合與執行 Git 交付。Workers 不派下一層、不改範圍、不自行 commit。其核對記為 peer 檢查，不冒稱原合約的人啟獨立正式接受；正式獨立接受與原備份仍分開報告。若出現具體安全阻塞，依停止條件交 Owner。

目標是在 `tests/test_notes_records.py` 內，讓父程序及每個 CLI child 的 active locator 讀寫都留在當次合成 fixture。成功 child bind 必須繼續使用產品真實 writer，並可讀回正確 locator；拒絕、異常退出與 fixture 清理不可把定位寫到 fixture 外。

分級：**STANDARD**。修改只涉及單一測試檔，沒有產品介面或資料格式變更；但目前測試會影響日常 locator，涉及真實資料定位保護，不能視為普通斷言小修。採人工啟動的計畫後、首切片後兩次 Simplicity Review，另保留獨立的離線修復接受。未規劃資料遷移、產品變更或實機派送，因此不列 CRITICAL。若發現必須處理真實資料或改產品 gate，即停止並重交 Owner 定界，不沿用此分級擴做。

最小充分方案：修改該測試類別的初始化／清理及 `run_cli`，以 fixture 專用 `_active_task_path` 取代父程序 writer no-op；child 在同一個 notes 模組實例完成 locator 注入後呼叫 `notes.main`。增加既有 bind 案例的 locator 斷言與少量生命週期保護斷言。完整首切片預期就是最終候選，不刻意拆出另一輪實作。

不採方案：只 mock writer 無法觀察成功 bind 副作用；只 patch 父程序未封住新 Python；跑完再恢復真實 active 會讀寫真實資料並可能覆蓋並行更新；產品 flags、canonical 放寬、控制器或遷移功能均超出已證實缺陷。

非目標：事故歷史 writer 的直接歸因、真實 active 清理、列表歷史認領、恢復備份、修帳、產品功能、Skill／正式 Prompt 修改、GUI／實機 E2E。原備份維持 `BLOCKED`。

## 範圍與精確基準

| 項目 | 基準 |
|---|---|
| Repo | `Line_backup`，啟動時以 `git rev-parse --show-toplevel` 核對 |
| 分支 | `feature/line-notes-media` |
| Planner 輸入 HEAD | `42bc0e9ee55c2e2c281e4aea8ea65484a83caa75` |
| 分析 commit | `c105002ad8cfde194e48d22dc9635fd9c521dd20`，已核對為祖先 |
| 啟動 tracked／untracked | `git status --porcelain=v1` 空輸出；未吸收並行工作 |
| 實作來源白名單 | **僅 `tests/test_notes_records.py`** |
| 唯讀參考 | `tests/test_notes_locks.py`、`src/line_backup_batch/notes.py`、本分析及已列合成證據 |
| Planner 文件白名單 | 本目錄 `plan.md`、`handoff.md`、`planner-report.md`、`progress.md` |
| 私有規劃證據 | `.local/line-backup/tasks/notes-active-locator-plan-20261115/`，不入 Git |

本次 Planner 只寫文件及私有規劃證據。後續實作者還需 Owner 人工交接本計畫及明示實作階段；本草案不自行授權實作或擴大檔案白名單。新建的純合成 fixture 及實作者私有證據可置於專案私有 tasks；清理限該次自己建立、可辨識的 fixture，不得清其他歷史任務。

禁止讀寫真實 active、index、events、hint 目標帳本或照片；禁止操作 LINE、刪歷史、重跑分析合成腳本、執行未隔離原測試、修改產品／其他測試／Skill、合併 master。不得用事後全域檔案還原代替隔離。

| 固定來源 | SHA-256 |
|---|---|
| `issue-analysis.md` | `ff5a1c0521387518b71e1bde506aca0f865ac4d7809d266903f16ea3a67d2ccb` |
| `planner-start.md` | `2ab8b1afef9a2c31e72aeebe96a456d08cf6e9947152ccb9554f2f7858db39d9` |
| `src/line_backup_batch/notes.py` | `fcd5bd4196e9963d93ca94b6025ea2c1065ff9202373afd3311b3a8a8dc4ea00` |
| `tests/test_notes_records.py` | `7264f74f68ca9ca8c5e4c6df688ee3bb72abc7c13049e45da0bbda20b3a495e5` |
| `tests/test_notes_locks.py` | `1494a9a3c2f839900d7a5fcb99b78d11c4c5c92f590da85304849c1ae457c151` |

完整來源：[分析](../../diagnostics/20261115-notes-active-locator/issue-analysis.md)、[Planner 啟動交接](../../diagnostics/20261115-notes-active-locator/planner-start.md)。分析私有證據可唯讀核對交接已列腳本、去識別結果及 manifests，不可沿腳本中的路徑讀其他原件。

## 事實、推論與未知

- 已證實：父程序 `_write_active_hint` mock 不會進入 `run_cli` 啟動的新 Python；成功 child bind 可寫 locator，fixture 清理後留下失效定位。分析已用私有合成 locator 重現 child exits `4 / 0 / 4`，本 Planner 未重跑。
- 已證實：`canonical` 不是固定預設 collection 限制，不能以改 collection gate 修此缺陷。
- 推論：事故 session 精確匹配測試常數，路徑前綴亦吻合，支持測試來源高度吻合；不等同歷史 writer 直接 trace。
- `UNKNOWN`：事故當時目標 metadata、真正寫入者、真實列表與歷史唯一匹配、其他測試檔在完整回歸中的隔離充分性。
- 本檔其他 list-key 測試類別有不同隔離策略，沒有該 `run_cli` child 路徑。保持原狀；若必須改它們才能安全執行，先列證據並交 Owner，不擴張修復。

## 首個可驗證切片

此切片所有隔離設置與靜態檢查完成後，才執行任何目標測試。

1. 在 `NotesRecordsTests.setUp` 建立專用的外層合成邊界目錄，內含外層 sentinel 與內層 fixture。sentinel 位於內層 fixture 外，但仍是本次測試新建、受控的私有檔案。給 sentinel 固定合成 bytes，必要時使用合法合成 hint schema；不讀真實 active 取得初值。
2. 在任何 NotesCollection／NotesRecords 動作前，父程序先把 `_active_task_path` 的測試 fallback 指向 sentinel，再安裝內層 fixture locator。外層 sentinel 必須是可被遺漏內層重導所命中的控制路徑，不能只是旁置一個不參與定位的檔案。不改 `CORE_ROOT` 或產品常數以擴張測試環境。
3. 將父程序 writer no-op 換成路徑隔離，保留真實 reader／writer。登錄 `addCleanup` 或等效有界 cleanup，確保 setUp 中途失敗也能回收自己建立的資源、還原 mock。安排外層清理前的 sentinel 比對及內層缺席斷言；不在 mock 還原後執行 notes 動作，不與 tearDown 重複清理。
4. `run_cli` 統一使用明確的 Python `-B -c` bootstrap：載入 notes，先裝受控 sentinel fallback，再裝 fixture `_active_task_path`，確認路徑在內層後，於該模組實例呼叫 `notes.main(argv)` 並傳回 SystemExit code。把路徑與原 CLI 參數以 argv 傳入，不拼成 shell 指令。失敗安裝不得進入 `main`。
5. 唯讀參考 locks 的 child bootstrap 思路，**不複製其 reader／writer no-op**。也不混用預先 patch 的匯入模組與另一次 `-m` 執行實例。保留既有 `CompletedProcess`、stdout／stderr、parser、JSON 與退出碼可觀察性，不新增公共 flags 或產品注入入口。
6. 加強既有 context-bind 案例，讀回 fixture locator，核對 `schema`、root、local_list_id、session。錯誤 context 前後 locator bytes、既有 events bytes 不變；成功 bind 必須真的改為該 child session，不能僅依 exit 0。另在成功後測一次拒絕，證明已有 locator 亦不被改寫。
7. 用同檔內最小生命週期回歸，覆蓋成功 bind 後內層清除、正常 cleanup 與受控失敗 cleanup。核對內層及其 locator 缺席，並在外層清除前比對 sentinel bytes。依 Worker2 計畫核對採納簡化：不再重測「刪 fixture 後 memory canonical 拒絕」的產品 gate；該機制已有分析合成證據，並非此隔離修復的新增必要條件。

低影響選擇交實作者：私有 helper 名稱、合成檔名、是否合併正常及失敗 cleanup 的測試案例；必須保留上述可觀察行為。不得另建通用測試控制器。若最小方案需要白名單外改動，停止。

## 成功條件、風險與證據

| ID／要求 | owner | 成功證據 |
|---|---|---|
| S1 父子初始化先隔離 | Implementer；後由獨立接受者核對 | 靜態 diff 所有 notes 動作均在 locator 注入後；child 入口統一且沒有 writer no-op |
| S2 成功 bind 可觀察 | Implementer | child exit 0；讀回 fixture hint root／ID／session 精確對應；sentinel bytes 不變 |
| S3 拒絕不寫 | Implementer | bind exit 4／WRONG_NOTES_CONTEXT；locator 及 events bytes 不變；成功前與成功後均覆蓋 |
| S4 清理與失敗邊界 | Implementer | 合成 bind 拒絕／成功／拒絕 exits 4／0／4；正常及受控失敗 cleanup 後內層及 locator 不存在，sentinel 比對成立；bootstrap 失敗不進 main |
| S5 CLI 相容 | Implementer | 既有 help／argparse／業務拒絕／內部錯誤斷言維持 0／2／4／70，不刪減既有斷言 |
| S6 最小變更／回歸 | Implementer | 來源 diff 僅白名單檔；相稱回歸 exit 0，附命令、計數、stdout／stderr、候選 hash |
| S7 獨立接受 | Owner 人工另啟的接受者 | 對精確候選逐項映射 S1–S6，獨立安全檢查；不是實作者自評 |

| 風險／依據 | 緩解／回復 |
|---|---|
| 新 Python 不繼承 patch | child bootstrap 明確注入；靜態檢查先於測試 |
| sentinel 斷言變成空證據 | 使其成為受控 fallback；同時核對實際 fixture hint，限定證明 locator 路徑邊界 |
| 模組實例不一致／啟動 hook 失敗 | 用同一 notes 實例呼叫 main；安裝失敗即終止 child，不依賴可被忽略的 startup hook |
| setUp 失敗略過 tearDown | 資源及 patch 取得即登錄 cleanup；受控失敗案例檢查 |
| 父程序真實 writer 改變既有 fixture hint | 保留產品語意；以單檔回歸核對既有斷言，不把不符當理由恢復全域 mock |
| 廣泛回歸含其他未隔離測試 | 執行前唯讀檢查測試 active／child 邊界，若不安全停止，不先跑再修 |
| 並行修改／環境改變 | 每個人工交接及 checkpoint 核對 Git；保存不同工作，不 reset、不混入、不無限重查 |

此方案能證明所測父子入口透過 `_active_task_path` 的讀寫落在合成範圍，以及 sentinel 在受測期間未改。它不提供 OS sandbox，不觀察其他程序，也不能證明真實 active 沒有被其他合法 writer 更新。不可為了擴大這個保證而讀寫真實 active。GUI 狀態、provider 路由及實機備份均無本次保證。回復限還原本次測試來源差異或清理自己新建的 fixture；既有原件／歷史不在回復範圍。

## 檢查命令、順序與停止條件

以下全是**後續獲交辦角色的計畫命令，本 Planner 均未執行**。工作目錄為 repo 根；保留各命令獨立退出碼，不以 shell 串接掩蓋失敗。

| 次序／owner | 命令或觀察 | 通過證據／停止點 |
|---|---|---|
| V0 Implementer | `git status --short`；`git branch --show-current`；`git rev-parse HEAD`；來源 SHA-256 比對 | 與 Owner 交接的規劃 checkpoint 一致，測試來源仍符合本基準；未知差異停止 |
| V1 Implementer | `git diff --check`；`git diff -- tests/test_notes_records.py`；`rg -n 'active|run_cli|subprocess|Popen|cleanup|tearDown' tests/test_notes_records.py` | S1 完整後才可測試；列出所有父子 notes 入口，確認沒有外逸；靜態判讀記來源依據，不冒稱動態驗證 |
| V2 Implementer | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py -k test_bind_omitted_context_inherits_saved_context` | exit 0，含 S2／S3 證據，缺 locator 斷言即不算通過 |
| V3 Implementer | 同一 discover 命令，以 `-k` 選新生命週期案例；名稱由實作者在報告列明 | exit 0，S4 正常／失敗 cleanup，context 案例另含 bind 4／0／4；選取 0 tests 不算通過 |
| V4 Implementer | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py` | exit 0，原有 context、CLI 及資料保護測試未刪減 |
| V5 Implementer | 唯讀檢查 `test_notes*.py` 與 daily suite 的 fixture／child active 隔離；不讀真實資料 | 所有即將執行入口的安全前提有來源證據；若發現額外缺口停止交 Owner，不擴檔修復 |
| V6 Implementer | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | V5 後 exit 0；相簿相容回歸，不是實機接受 |
| V7 Implementer | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0，僅 help，不附真實路徑，不執行 lists／memory |
| V8 NOT_RUN（Owner 已選定） | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | locks child 模組實例的隔離未有充分證據；Owner 選擇維持單檔，不跑此完整 suite |
| V9 獨立接受者 | Owner 指定精確實作候選後，靜態核對 S1–S6 並獨立執行已證明安全的 V2–V4／生命週期案例 | 保存獨立報告及命令結果；是否補跑 V6–V8 由 Owner 依候選變更決定 |

現有 unittest 的 `-k` 選取能力需由實作者確認；若不支援，使用明確模組／類別／方法選取同案例，保留真實命令，不因此跑未隔離測試。不更換系統 Python／Swift SDK 或安裝工具鏈來繞過失敗。產品 70 在受控既有分類測試中是預期斷言；預期之外的 child 70 則停止，不改入口重試。

停止條件：任何真實資料存取需求、sentinel 改變、locator 越界、未知派送／寫入、來源／branch／HEAD 不符、必要修改超出單檔、scope／介面／驗收標準變更或所需回歸無法安全執行。保存最小證據交 Owner。一次根因最多三次有證據修復嘗試；連續兩次無新資訊即停，不因換 session 重置。此前分析的兩項合成診斷已保存，不重跑以充次數；目前無產品修復嘗試。

## 人工檢查點與交接

1. 本草案交付後，由 Owner 決定是否另啟 **Simplicity Reviewer（計畫）**；先唯讀檢查此方案是否最小且保留可靠性控制。不自動派送。
2. 計畫審查後，由 Owner 決定是否另啟 Plan Reviewer 或直接授權單檔 Implementer。STANDARD 不預填獨立計畫接受。
3. Implementer 交付首切片、V0–V8 證據及候選後停止，由 Owner 另啟 **Simplicity Reviewer（實作）**。首切片若已是最終候選且沒有剩餘實作，不重開空 Implementer。
4. 由 Owner 人工交接獨立離線接受。以上都不能恢復原備份；實際可用性後續仍用手冊記事本正式日常 Prompt，需有效任務授權及前景交接，不以 Harness E2E Prompt 取代。

本 Planner 不開始上述角色。計畫拒絕、阻塞或需擴界時保存證據並停止，不跨角色修正或重測。

## 交付狀態

| 狀態 | 本 Planner 判定 |
|---|---|
| PRIMARY_OUTCOME_STATUS | PLAN_DRAFT_COMPLETE |
| IMPLEMENTATION_STATUS | NOT_RUN |
| CORE_ACCEPTANCE_STATUS | NOT_RUN |
| REQUIRED_VERIFICATION_STATUS | NOT_RUN：修復檢查尚未執行；文件／基準核對另列報告 |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN |
| TASK_CLOSURE_STATUS | BLOCKED：原備份、實作及接受未完成 |

計畫可執行不等於產品接受；本角色不發出產品 PASS 或整體 DONE。
