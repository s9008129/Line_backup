# Replan 06：先接通真實證據，再完成兩本 LINE 相簿備份

日期：2026-10-11；角色：PLANNER／Replanner；版本：minimal-live-06（凍結執行契約）。

## 0. 固定位置與本次交付

- **ROOT（使用者指定）**：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
- **TP**：`harness-development/line-v3-live-e2e-20261010`。
- **R／本輪 continuation**：`harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06`；**RUNROOT**＝ROOT/R。
- **P／上一輪**：`harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02`。
- task_id 沿用既有 v3 父任務 **`TASK-20261010-line-v3-live-e2e`**；另產生新 run_id、continuation 與 evidence ID。P 的本地工具任務 ID 不拿來代替父產品授權。舊 v2 任務、既有契約、失敗收據不改寫。
- 配對交接文件：[handoff.md](handoff.md)。本輪兩份文件是規劃交付；文件核對及文件發布保全不等於 IMPLEMENT gate、實機測試或 native schema PASS。
- 編寫前實際 HEAD：`7cea58d42072d9da6140c36157aa1580fe320bdb`，branch：`v43-ab/codex-rev28`，index 空。這是出版時觀察；文件 commit 後 Implementer 必須重新取得 fresh HEAD／index／filesystem baseline。

**本輪要取得的答案**：現在這個程式，能否使用真正的 CUA LINE 畫面，經同一條正式證據鏈，安全完成第一本下載、驗證與狀態讀回，再實際捲動到不同 eligible 相簿，完成第二本？若不能，留下第一個可重現、可定位的真實阻塞，交回本 Replanner。

## 1. 結果、授權與工作流

### 1.1 有界終點

本輪最多兩本，不改 config 的每 lifecycle 上限 1：第一個 lifecycle 完成 1 本並 VERIFIED／readback／owner release，執行實際 post-release scroll，再建立第二個新 owner，完成另一本不同 eligible 相簿。兩次交易共用既有 GUI ledger 與原安全政策。兩本通過只能證明這個有界批次，完整群組自動備份目標仍需後續循環。

必要順序：完整保全基線 → 真實 raw capture 診斷 → 最小 production 接線／凍結 → 真實 `G_REAL_LINK` → 全部必要離線檢查 → 第一本交易／內容／狀態驗收 → 實際捲動與新卡片 grounding → 第二本完整交易 → 保全與正式報告 → 獨立 Acceptance。

### 1.2 已有授權，不重複索取

使用者先前已選擇橋接修復＋兩本 E2E、加入 v2 evidence、允許為可觀測性調整版面，並明示「本次不需要獨立審查」。本輪最新明確決策原文：

> 核准一次有界延續，接到兩本 E2E（建議）

這個決策授權下述範圍、步驟與檢查；不是把已用盡的 3/3 清零，也不是允許同輪修正後反覆重跑。Plan Review 保留 `plan_review_required=true` 的 CRITICAL 契約要求，以另份 `plan-review-waiver.json` 記錄 **USER_WAIVED_NOT_RUN**；不得寫 reviewer PASS。父任務獨立 Acceptance **仍 required**。Handoff 不需要獨立審查，採相同契約的確定性複製。

LINE 前景交接是一個尚未完成的操作前提：任何需要 LINE 前景的 input 前，用白話告知 app、目標畫面、下一個精確動作，透過可用的提問管道請使用者交還前景，等待明確回覆。沿用工作授權，但不假設前次前景交接仍有效。被取回前景立即停止輸入，重新交接、擷取、核對後才能繼續。

### 1.3 角色及能力

風險 **CRITICAL**：證據解析直接決定真實照片下載與持久 intent。根 Implementer 串行，`max_parallel_read_only_helpers=0`、`max_parallel_writers=0`。文件發布時使用者另行指定的 GPT-6 luna（xhigh）commit-message helper 只讀文件／證據、提供文字，不是 IMPLEMENT allocation、Plan Review 或 Acceptance。

Harness immutable resource root：
`/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source`。

讀取其 `policies/v4.8.0/workflow-routing.md`、`templates/v4.8.0/runtime-defaults.json`、`schemas/v3/task.schema.json`、`schemas/v3/result.schema.json`。預設 Implementer 為 GPT-6 luna／xhigh，Acceptance 為 GPT-6.1-sol／high；實際 host/model/session 必須按真實記錄回報。現場無 native controller stage packet；固定 Harness Python launcher 指向缺失 runtime，native admission／CONTRACT／RESULT validation 為 **NOT_RUN**。不得改 global `.codex`、自行建 validator、替換 release 或虛構 stage completion。日後若 controller 提供 packet，只執行它發出的固定 validation 命令。

缺 native packet 不用來再次推遲本契約已授權的安全產品驗證；正式 REQUIRED_VERIFICATION／TASK_CLOSURE 維持未滿足，直到原要求真的完成。不能以本地 parse／hash／equality 代替 native PASS。`network=OFF` 指本輪程式不新增網路請求；LINE 原生已授權下載是既定產品動作，不能聲称工具政策證明 OS network denial。

## 2. 第一性原理：瓶頸與真正根因

一次可靠備份需要同時證明四件事：**看到哪一本 → 點到同一本 → 下載到正確空資料夾 → 檔案完整且登記成功**。每一件都必須由當下的可追溯證據建立，前一件未證明，後一件不具備安全執行條件。

| 層次 | 已證實事實／原因 | 本輪修正方向 |
|---|---|---|
| 規劃與驗證順序 | live-grounding-03 曾寫早期 runtime/capture gate；但 production analyzer／geometry／catalog callbacks 沒有真實串接證據，就先投入大量 mock/offline 檢查。不能說 Planner 完全沒寫這件事，問題在執行時機及 gate 的可操作定義。 | 把真實 raw sample 提前；再用 production entry 的 probe 走通整鏈，作為下載前硬前提。 |
| 實作覆蓋 | ALBUM_DETAIL、cards=[] fixture 沒走到 ALBUMS 成功分支；ALBUMS boundary key sort 與未排序 literal 比較，合法資料必然被拒；frameSupport 遺失 `intersectionPx`。 | 非空真實卡片、正負 fixtures、跨 JS/Python 語義一致及欄位完整傳遞。 |
| host 介面 | 真實 screenshot 是跨 realm Buffer；曾 `instanceof Uint8Array=false`，`ArrayBuffer.isView=true`。183645 bytes 與原 hash 在 normalization 後保持一致；adapter 現有 31/31 offline 已通過。 | 使用已修復 normalization，保留 subarray 範圍、bytes/hash/readback；CLI Node 與 CUA host 能力分開驗證。 |
| runner 與基線 | 舊 runner 用目錄層數推 ROOT，child cwd 變成上層 ChatGPT，產生 MODULE_NOT_FOUND；基線初次 NameError、再遇 FIFO 中斷。部分／空 records 被誤當完整盤點，衍生「98,513 路徑缺失」。 | 固定使用者 ROOT、argv array／shell=false、讀前身份檢查；partial scan 只能 BLOCKED，不比較刪除。 |
| 保存工具自我干擾 | recovery-02 的 p1→p2 讀到自己尚未完成的 stdout；policy 只列四個 inventory JSON，漏掉 stream outputs。G_PRESERVE FAIL 的 7 筆是 2 個新增 stream＋同一 stdout 的 5 個欄位變化。 | 兩次掃描、streams、比較都先在 host 記憶體完成，最後依事前精確政策發布；不豁免整個 tmp/evidence 目錄。 |
| 授權／寫入邊界 | `Store._ledger_write` 在 TP 建隨機 temp，原 scope 只允許 ledger file；finally 無條件 unlink 的做法若改固定名稱，會誤刪既有碰撞檔。 | 同一 canonical writer／shared lock，改為明確列入 scope 的固定 temp；exclusive create，僅清理本次實際建立且 identity 仍一致的檔案。 |

結論：停在安全前提是正確的；長期無法進入實機，主要是**真實 production 串接缺口沒有在最早的小測試暴露，加上測試工具與輸出政策自身有錯**。Planner 要把步驟和判定寫成可執行契約，Implementer 要用真實成功分支及資料流證明它，報告要保留每次新資訊。責任跨越三者，現有證據不支持把全部歸咎單一角色或每個未留紀錄的行為。

有兩本歷史 VERIFIED，不能寫「從未成功備份」。歷史成功不能證明目前這版 production 接線與第二本 scroll 流程已完成。

## 3. 證據輸入與已知狀態

下表相對路徑均從 ROOT 解析。**絕對路徑＝ROOT＋`/`＋該相對路徑**；P 的全部 83 筆原始引用另由 `P/evidence/report-manifest.json` 的 `files[].absolute_path` 提供，Implementer 必須逐筆讀回 bytes/hash；下表不能代替原始證據。

| 相對路徑（P＝§0 固定路徑） | bytes | SHA-256 |
|---|---:|---|
| P/E2E測試報告.md | 43533 | 0336b8990edae40bc6ea561d161a9059e97e58fab5398964bdc331f26b71feca |
| P/progress.md | 4267 | 3f626c55ba07a4fe8a542651d118dc20b8e3ceaf9e641e08bf9b1c37a49b592a |
| P/evidence/report-manifest.json | 50795 | 1cdb2cba9089460179f018c6b7a03fccafec563156c3353cacd4ff31a795edc0 |
| P/evidence/implementation-result.json | 16276 | bcc3d6adb1615d4c9b23da2b5d5506ab9953771fec5b796d66d9dee6cb97d066 |
| P/evidence/attempt-ledger-recovery-02.json | 35079 | 827c52410a8f52ba88041dc5d0efb860262737dc1b071c5f2e3b415a37676485 |
| P/檢討報告.md | 39827 | 54bb7bca54ee386f32cff65fc466261a6433d0c9d9be796c16d153d2b5d15f89 |
| P/evidence/g-baseline-recovery-02.json | 24360 | 879e4aec93999278f32b175b7850ac1ff87527eafe86829a46c0c708fc772279 |
| P/evidence/g-runner.json | 7361 | 072bf7c508a2631315b2e23f7c47f47c82c8ed408340e45cf86b43acfeaf202b |
| P/evidence/g-adapter-offline.json | 8948 | ad59db8d590adf580f48c34b103f0989b0abe0a3cc8266bba5a95f2f699257b1 |
| P/evidence/preservation-recovery-02.json | 18870 | c8d9d2ba15250bc595944c2abbcae4261ddb723a7d616020720e506e7f6ae9d7 |
| P/evidence/compare-preservation.json | 21100 | 3ee56302567089d4a0739e301a52c70e18e243a477cb159904a5f8f263d675bd |
| P/plan-contract.json 與 P/handoff.json | 各 2811 | 057145c121290465b8c4970ed85f30ad860be91013336c301f46ea77c1c6f45a |
| P/check-specs.json | 11288 | 5bd52c11c232fecee06b6edb83b009ea49fcb1378459a5653f31310bb8b59d4c |
| P/check-specs-freeze.json | 2278 | 1010261ee03bf1d327410d125488b00fc8ae5678d1fe0516e12dcd95ba5a6a70 |

重要主檔絕對路徑：

- `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/E2E測試報告.md`
- `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/evidence/report-manifest.json`
- `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/檢討報告.md`

補充只讀來源：`TP/continuations/live-grounding-03/{plan.md,live_runner.mjs,live_classifier.mjs,chooser_locators.mjs}`、`TP/continuations/live-grounding-04/plan.md`、`TP/continuations/scope-recovery-05/{E2E測試報告.md,evidence/g-baseline.json,evidence/g-baseline-failure-detail.json}`、`TP/continuations/implement-02/user-decision-A.json`。讀取後把完整相對／絕對路徑、bytes、hash 寫入新 input manifest；原件保持不動。

83 筆引用實際為 **81 筆專案內檔案＋2 筆固定外部 runtime（Python／Node）**；外部 runtime 只依 Plan §7 的精確路徑唯讀核對，不由此授權修改或搜索其他環境。

### 3.1 可保留的成果與待釐清的敘述

- recovery-02：G_BASELINE **37/37 PASS**、G_RUNNER **11/11 PASS**、G_ADAPTER_OFFLINE **15/15 PASS**（Node suite 31/31）；G_PRESERVE **FAIL**（23 checks 中 22 ok）；G_REPORT 的本地 manifest/result tail 已完成。全部是舊 build 的已證實成果，不直接 reuse 成本輪 PASS。
- 報告／progress 仍有 tail PENDING 敘述；現存 result＋83 筆 manifest 是後續完成證據。新 reconciliation 並列原敘述與最新讀回，不改舊報告。
- `baseline-selftest-02.stdout` 的 removed paths 是 68；`runner-selftest-01.stdout` 只列 fixture 根 1。舊 ledger 的歸因混淆須在新報告更正。failed-smoke 兩棵樹只有 listing/note，缺獨立刪除收據，保留 UNKNOWN。
- `planned-additions.json` 最後版本從 p2 實際 diff 組成；不能單憑吻合就宣稱全部新增曾在寫入前授權。新輪把事前許可與事後 observed manifest 明確分開。
- pre-freeze smoke、helper finding、失敗都保留；沒有紀錄的 attempt 是 UNKNOWN，不等於 0，也不以「非正式」隱去有意義嘗試。
- b1/b2 records＝128671／128672；p1/p2＝128703／128706。已知 FIFO 四份觀察一致；239 既有 backup regular files 全部 read_verified。新的 baseline 以現在工作區為準。

### 3.2 開始前的參考錨點（必須重新讀回）

| 對象 | 已知值 |
|---|---|
| config | schema 2，group=`旻謙允禎成長日記`；group_key=`line:jp.naver.line.mac:旻謙允禎成長日記`；app=`jp.naver.line.mac`；backup_root=ROOT/backups；每 lifecycle 1；recovery_limit 1；poll 5 秒、stable 3、max_wait 600 秒；384 bytes／SHA 5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362。 |
| state | schema **3**、revision 35；252115 bytes／SHA 455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6；active_batch／active_writer_id／context_lock 均 null；2 本 VERIFIED（2024-05-13～17，57 張；2024-05-06～10，182 張）。 |
| shared GUI ledger | TP/gui-ledger.json；參考 123 bytes／SHA 92bab0cf122871b42f3db62af956289b62fbf4e279219766a8850b61f20e135f；不重置 cap／已用額度、不另開新 ledger。 |
| adapter | scripts/line_backup_cua_adapter.mjs；39953 bytes／SHA bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2。 |
| 既有 dirty adapter tests | tests/test_cua_adapter.mjs；18529 bytes／SHA 0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd；只讀，不覆蓋其使用者修改。 |

若 config／state／ledger 的 fresh 值變了，先建立變化來源及授權；有競爭 writer、未知 intent、資料身份變化即停止，不能硬套上表或把所有 drift 都當無害。

## 4. 寫入範圍與資料邊界

### 4.1 唯一可改的產品檔案（9 個 literal paths）

1. `scripts/line_backup_cua_adapter.mjs`
2. `src/line_backup_batch/cli.py`
3. `src/line_backup_batch/observations.py`
4. `src/line_backup_batch/store.py`
5. `rev28/Sources/rev28ctl/main.swift`
6. `rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift`
7. `rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift`
8. `rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift`
9. `rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift`

新增檔若已存在，保留並停止確認其來源，不用覆寫。只修改任務必要部分；編輯前保存原 bytes/hash/diff。不得修改其他 dirty Composition／Sensor／NativeObservationSession 檔案、root tests、Package.swift、config、AGENTS 或歷史 task package。

### 4.2 Task artifacts 與真實交易

可在 R 內建立本輪 tools／checks／host modules／build／fixtures／evidence／報告。R 中出版時已有的 `plan.md`、`handoff.md`、`.local` 內容屬新 baseline，不覆寫。generated contract、grants、receipts 一律 fresh exclusive 路徑、no-follow、readback；語義 gate 只接受凍結檔案及本輪 invocation。

正常 canonical 交易允許以下 literal paths：

- `state/backup_state.json`
- `state/.line-backup-state.lock`
- `state/.line-backup-v3.tmp`
- `harness-development/line-v3-live-e2e-20261010/gui-ledger.json`
- `harness-development/line-v3-live-e2e-20261010/.gui-ledger-v3.tmp`
- `backups/旻謙允禎成長日記`（只可建立本輪精確空 destination，由 LINE 原生新增下載檔；既有資料不可改、刪、搬、覆寫）

資料路徑在 contract 中是邊界，不是全目錄修改權。實際 destination 必須在選定 fingerprint 後、建立之前登記事前 receipt，經 config／realpath／no-symlink／empty checks；最多 2 個新 destination。Native 下載檔名不由程式指定，事前授權的是該 transaction 的 exact destination 與新 regular image／已辨識 metadata 類型及 expected count，驗收逐檔核對，不能將事後 diff 轉成新的許可。

GUI ledger temp：在現有共享 state guard／CAS 下 exclusive create 固定 `.gui-ledger-v3.tmp`，O_EXCL／O_NOFOLLOW，fsync→atomic replace→parent fsync→readback。碰撞即拒絕；finally 只能清理由本次成功 create 且仍是同 dev/ino 的檔案，不能刪掉 preexisting、symlink、替換後 identity 不同的 temp。保留 ledger schema、quota、reserve/consume、shared writer；不改成 JS writer 或第二份狀態。

### 4.3 明確禁止

不 migrate、初始化空 state、換 writer、放寬 freshness／menu／duplicate／intent gates、不重送 Save All、不將未知改 0／false、不額外增加 GUI automation 技術。GUI input 只用已文件化 CUA；repo native 只做本計畫授權的 passive observation／capture／OCR／decode。不可用 AppleScript、AX writes／PerformAction、shell GUI automation、外部 daemon／bridge 或猜 API 取代 CUA。人工版面調整後也要 fresh 再綁定，不能沿用原座標。

本 Implementer 不 commit／push：本次文件出版的明確 git 授權由目前 root 執行。後續產品提交需使用者另有指令；不得把未完成實作混入這次兩份文件的 commit。

## 5. 先修保全工具，避免再被工具阻塞

### 5.1 無循環的 bootstrap

先把兩份文件中相同 machine contract 讀入記憶體，不需先落地 contract 才能知道 scope。任何新工具寫入前，host 做兩次全 namespace／metadata anchors，保留 HEAD／branch／index／dirty diff／config／state／ledger／protected hash。一致後，依事先列出的 bootstrap output paths exclusive materialize contract、check specs、工具、fixtures。

`R/plan-contract.json` 與 `R/handoff.json` 是附錄 A block 原始 UTF-8 bytes（含末尾一個 LF）的逐 byte 副本；兩份 hash 相同。不透過 pretty-print 另造語義相同但 bytes 不同的 contract。bootstrap 的最小 host scanner 可直接使用 P/tools/inventory.py 的純唯讀 `scan_tree`，讀取與調用的 source hash 必須留存；不要調用其會自寫輸出的舊 CLI main。

### 5.2 新輸出政策與兩次記憶體掃描

bootstrap 前建立不可回填的 `output-policy-bootstrap`；完整基線前建立 `output-policy-frozen.json`，列每一固定檔名、父目錄、建立／有限更新階段、類型、大小 cap、producer 與 readback 規則。動態 frame／action／poll artifact 以已凍結 kind＋sequence（正整數、上限 5000）規則，**每次寫前**先登記 exact normalized path；registration 本身為預宣告 exclusive receipt。允許的 kinds 限 screenshot-png、raw-ax、native-context、sck-capture、ocr、grounding、classifier、chooser、action、catalog、download、verification、state-readback、command、gate；extension／類型須吻合。不能宣告整個目錄免比較。

build／module cache 及 fixtures 使用 exact root 與明確 producer/lifetime，無執行權外溢；Swift 編譯器可在其 exact scratch root 建立 regular／dir cache，允許 compiler cache symlink 只在該 root 內且記錄 link target，不可跟隨到其他寫入 scope。fixture 删除僅限本輪預登記、實際建立且身份匹配的 fixture；歷史 failed-smoke 樹不清理。

每組 baseline／preservation：**scan-1→scan-2→完整性確認→compare 全在 host 記憶體；兩次之間不建立 invocation、stdout、stderr 或 inventory 檔**。child 如需 stream capture，由 host pipe 收完整 bytes，不能先把 stdout redirect 到工作區。完成比較後才 exclusive 發布該組 inventories、streams、compare 與 receipts，依 frozen policy逐 byte讀回並驗證 exact directory additions；記錄 publish-before／publish-after metadata 與每個新檔 hash。自己的輸出走明示的發布生命週期，不藉 blanket SELF_OUTPUTS 跳過檢查。

full scan 必須遍歷 namespace，regular files no-follow讀取、前後 identity／size／mtime／ctime 一致並 hash；directory entries、symlink targets、known FIFO 的完整 metadata 保留。計時在掃描**之前**開始，記 UTC 與 monotonic start/end、errors、complete 與 records 數。partial／timeout／read race 一律 `complete=false`、delta **BLOCKED**，不得把空 records 與歷史比較出大批 missing。

唯一已知 FIFO：`evidence/20260916-auto-verification/attempt-01/archive-phase1/private-tmp/line-backup-acceptance-verifier/special/backup/destination/special.fifo`。只 lstat，不 open/read/hash/move/recreate。其他未知特殊物件先 lstat 留證、BLOCKED，不讀它。排除 `.git` 的控制資料，另以 Git identity/index/diff guards 檢查；不排除 R 外其他資料。

G_BASELINE_06 必須完整、兩次一致、bootstrap delta 符合事前 policy、protected files 原值仍在。G_PRESERVE_06 新掃描與新 baseline 比較；所有產品差異恰落 9 檔且可解釋，交易 state／ledger 都由 canonical receipt 支持，239 既有 backup 檔與歷史 VERIFIED 不變、無範圍外變更。舊 G_PRESERVE FAIL 永遠保留。

### 5.3 固定 root runner

實作 `R/checks/run_command.py`：固定 ROOT/R，不從 parents[N] 猜；cwd／HEAD／branch／empty-index／command ID／contract／spec／runtime source preflight。所有命令 argv array、shell=false、固定 cwd、timeout、stream cap、child exit/signals，env diff 與實際 executable realpath/hash 留證。receipt／stream path collision、symlink、source drift 在 launch 前拒絕。每個正式 check ID 至多 launch 一次；先 exclusive claim，再啟動，failure claim 不刪、不重用。stream 在 host memory 捕捉後發布，不能污染成對 scan。

## 6. 最小真實串接與修正內容

### 6.1 Host 接線：同一個 entry 的 probe 與 E2E

本輪建立並綁定：`R/host_io.mjs`、`live_analyzer.mjs`、`live_classifier.mjs`、`live_runner.mjs`、`live_entry.mjs`、`chooser_locators.mjs`、`checks/validate_real_frame.py`。從 live-grounding-03 的介面與現有 adapter 出發，修正 continuation/hash、dependencies 與已知缺陷；原來源不改。

- `host_io.mjs` 提供 exclusive no-follow retain/readback、bounded child process、明確 ROOT／Python／producer／env／clock；不把整份 canonical state 經 JS Number 讀寫。
- `createLiveEntry({app, repoRoot, runRoot, pythonBin, producerBinary, authorization, ...})` 接收**真正 cua.getApp 的 app object**；`probe()` 與 `runTwoAlbums()` 必須共享 production capture／retain／analyzer／classifier／frame validator。entry 嚴格檢查 mode，不接受 fixture callback、load JSON frame 代替 fresh authority。
- `probe()` 做 passive capture/分析/驗證，**不 acquire owner、不建 destination、不寫 state／intent、不送 UI input**。輸出包括原圖、raw AX、native receipts、mapping／OCR／完整非空 ALBUMS frame、Python read-only validation 和 state unchanged 比較。
- raw sample 診斷先於大型離線 suite：真正 `getAXStateAndScreenshot`→normalize→原樣 exclusive retain→readback hash，記型別、view offset/length、圖像格式／尺寸、真實工具 timing。這只是診斷，不冒充 G_REAL_LINK。

規劃時唯讀能力觀察：CUA runtime 中 fs read/write/open、crypto createHash、child_process execFile/spawn 可用，adapter file import 成功（未執行 factory／產品檢查）。全域 `process` 不存在，`node:process` import 被 host 阻擋。不能把 CLI Node 26.7.0 當作 CUA host 版本或直接使用 ambient `process.env`。在 module 中做已允許 capability probe、明確傳參／env；不改 package/runtime/global 設定。

### 6.2 Repo passive native producer

在已列出的 Swift 檔加入 `rev28ctl native-context`：必填 `--project-root --grant --grant-sha256 --output --session-id --request-id --phase before|after`；after 額外綁 `--pair-frame --pair-frame-id --cua-captured-at` 及 before receipt ref/hash。輸出原生版本化 receipt：真實 producer/source/binary、UTC/monotonic interval、bundle／PID／process instance、SC/CG window descriptors、AX window/focus/tree、display bounds/scale、permission 及原始 errors、artifact refs。

只讀 NSRunningApplication、SCShareableContent、CGWindowInventory、AX attributes；重用現有 selector、FrameCaptureSupport、ScreenCaptureKit、Vision `.accurate` OCR（zh-Hant/en-US）；不要求新 permission prompt、不 activate、不操作 AX。未知/null/offscreen/truncation 原樣保留。

來源順序：native before→CUA screenshot/AX→native after→SCK support；要求同一 process instance/window/display/layout，不能宣稱四者原子同步。唯一窗口以 fresh CUA 視覺與實測 AX／SC／CG／SCK 關聯證明，不選第一個同尺寸窗口，也不要求全桌面只能有一個 LINE window。

mapping 由真實 crop／scale／native geometry 與三個唯一、分散且非共線 anchors 證明：triangle distribution ≥0.02 frame area，max residual ≤2 source px，uncertainty ≥2，safe margin ≥uncertainty+4，interactive intersection ≥16×16，含完整 display/menu-bar witness，action freshness **5 秒不變**。`intersectionPx` 明確向 classifier／Python 傳遞。跨 display／遮蔽／crop origin 不唯一／PID reuse／布局漂移拒絕，不依圖尺寸推 transform。

### 6.3 v2 真實 witness，state 3 與 17-key frame 不變

保持 frame 恰好 17 keys：`frame, frame_id, session_id, group_key, surface, captured_at, provider, layout_key, window_id, pid, width, height, mapping, cards, boundary, editable_focus, occlusion`。

新 production 使用明確 strict v2 grounding／classifier／chooser evidence；原 v1 僅可歷史 read-only validation，不變 fresh action authority。JS/Python 同步驗證版本、key set、required refs、hash、temporal/provenance 與判定；key-set 比較對兩邊一致排序／集合，不靠 insertion order。

每卡 `source_kind=AX_NATIVE|VISUAL_NATIVE`：AX_NATIVE 使用真實當下 card/image node；VISUAL_NATIVE 只支援可證明的單欄 cover/container 布局，保留像素 card／thumbnail／metadata 區域、raw Vision OCR text/bounds、native container、SCK pair、邊界／鄰卡分隔。現有 date-anchor segmentation 只供候選搜尋，不能當完整卡片／thumbnail／safe-area 證明。safe metadata 為同幀實測 metadata 扣除 thumbnail／ellipsis／其他控制／鄰卡，再按 uncertainty erosion；完整 card 包覆及安全餘量不足即拒絕。

不合成 CUA index、enabled、image node、identifier 或不存在 bounds；native traversal index 與 CUA index 只有唯一、實際控制關聯才可對接。AX dump null/offscreen/depth/node-limit 必須留原件及 completeness；未知不夾成屏內值。dates 明確解析 observed tilde／全形波浪分隔、保留原 text、輸出 canonical ISO；不猜缺年／跨年、不以近似字合併歧義群組；duplicate／partial／count drift／cross-pair 拒絕。

layout key 含 version/language/window class/size/native scale/surface 結構，排除日期、張數、row count、scroll offset。焦點 unknown 不改 NONE；LOW_GHOST 只適用既有已核准 class-1 navigation，不能放寬 intent／Save All／chooser 輸入條件。操作用 capture timestamp，retention/OCR/parse 不刷新五秒時鐘；若 pipeline 太慢而過期，停止輸入、保留 timing evidence，不調高 threshold。

### 6.4 Chooser 按真實階段判定

| 階段 | 必要證明 |
|---|---|
| APPEARED | 真實 folder chooser root、owner/PID/window continuation 與 dispatch/run 綁定；不要求 path field 此時已顯示。 |
| GO_TO_FOLDER | 當下唯一、focused、可輸入的 PathTextField，fresh bounds/index。 |
| PATH_FILLED | 當下 field 的**完整絕對路徑**與 exact destination 相同。 |
| DESTINATION_SELECTED | 當下 current-directory 資訊，或可驗證的完整路徑導航結果＋跨幀連續性；folder leaf、enabled confirm、安全 bounds。不能只看到相同 leaf 就 PASS；也不要求已關閉 field 仍存在。 |
| CONFIRM_ATTEMPTED | 只一次 invocation，fresh matched control 與 frame／owner／destination；後續 capture 與獨立 FilesystemDelta 下載開始證据。 |

同步修改 adapter、task classifier、chooser locators、Python validator。phase/version keys 嚴格，不用整體 screenshot 或 chooser closed 推定 download。owner／full path／focus 無法證明即停止，不 spoof 控制。

### 6.5 Source closure／grants

Python CLI、Swift producer、JS runner 的 CONTRACT_PATH／SHA／continuation 必須同時綁 R 與附錄 A **實際 bytes hash**。維持既有 V2 live grant 與 `user-decision-A.json` 的父 task_id；owners 精確為 `minimal-live-06-g1`、`minimal-live-06-g2`。

closure 包含既有 `SOURCE_PATHS` 21 項、全部相關 Swift Sources／Package.swift、本輪所有 formal host/analyzer/classifier/runner/entry/chooser/validator modules、固定 Python、producer、ImageIO decoder。實際 membership／bytes/hash／二進位 executable/realpath 寫 `runtime-binding.json`；更新 Python、JS、Swift 同一 membership 規則。fixture grants 不含 production credentials，不能被 real ROOT 接受。source 或 grant 漂移拒絕。

`authorization.json`、2 個 live-grant、plan-review-waiver、attempt-extension 彼此 hash 綁定，保留原 parent decision ref。總 album_quota=2；lifecycle_album_limit=1；Save All cap=2；chooser confirmation cap=2；reversible GUI cap=1000 依原 shared ledger 已用 entries 計算，不重置。Loaded intent 不提供新 dispatch permission。

probe 私有 wrapper 可調用既有 `authorize(...,'frame_support')` 加 ProjectReader/read-only frame validator；CLI parser 現未暴露此 operation，不為省事另開公用 mutate API。probe 沒有 owner mutation 權。

## 7. Runtime 與檢查規格（Implementer 寫成固定 check-specs）

### 7.1 Runtime 綁定

- **PY**：`/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13`；52640 bytes；SHA `34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804`。
- **NODE**：`/opt/homebrew/Cellar/node/26.7.0/bin/node`；50320 bytes；SHA `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`。
- **SWIFT**：`/usr/bin/swift`；已觀察 Swift 6.3.3、arm64-apple-macosx28.0；SHA `34129c71a01a74f7f3b2443521519b2e5447553fa187f5fcafaaf8c42cc192e2`。重新核對實際 executable 與 SDK metadata，不改全域設定。
- **SDK**：`/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk`（symlink→MacOSX.sdk；SDKSettings.json Version/CanonicalName=26.5/macosx26.5）。凍結 resolved path、settings bytes/hash；不把目錄名當實際 SDK 版本。
- **DECODER**：沿用 TP/bin/image_decode 與 CLI 已凍結 SHA `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`；只讀 hash/readback，drift 即停止，不建另一個 decoder。

所有 shell 範例是 **argv 規格表示**；實作 runner 不執行 shell 展開。ROOT／R／PY 等在 frozen specs 轉成 literal absolute paths。普通 cwd=ROOT；Swift 也用 `--package-path ROOT/rev28`，不可把暫存漏到 root .build。

child env：保存實際必要 PATH／locale 等鍵及 diff，不输出 secrets；強制 `PYTHONPATH=ROOT/src`、`PYTHONDONTWRITEBYTECODE=1`、`LINE_BACKUP_BATCH_TASK=R`、`LINE_BACKUP_INSPECTION_TEST_ROOT=RUNROOT/fixtures`、`LINE_BACKUP_INSPECTION_FIXTURES=RUNROOT/fixtures/swift-inspection`、`TMPDIR=TMP=TEMP=RUNROOT/tmp`。Swift caches：`CLANG_MODULE_CACHE_PATH=RUNROOT/module-cache/clang`、`SWIFTPM_MODULECACHE_OVERRIDE=RUNROOT/module-cache/swift`，並用下面 compiler flags；不得 repurpose HOME/CODEX_HOME 或安裝依賴。

### 7.2 精確 check IDs、argv、執行時機

每項 `automatic_retry=false`、source/freeze hash 綁定、exclusive invocation/receipt、stdout/stderr 分開。格式要求的 `transient_read_only_retries=2; delays=[10,30]` 只是 immutable task schema 常數；本集合**不使用自動 retry**，不得拿它重跑 check 或 GUI input。

| ID | argv（依上節把符號轉 literal） | timeout／每 stream cap | 時機 |
|---|---|---|---|
| E01-evidence-policy | PY -B R/checks/test_evidence_policy.py | 120 秒／2 MiB | bootstrap 工具完成後、產品改動前；只本輪 fixtures。 |
| E02-runner-selftest | PY -B R/checks/test_run_command.py | 120 秒／2 MiB | 同上；不得啟動產品 checks。 |
| B01-baseline-pair | PY -B R/tools/inventory_pair.py baseline | 各 scan 1200 秒；pair 2500 秒／每 stream 1 MiB | 完整基線；records JSON cap 各 128 MiB，讀取 cap 明示。 |
| D01-raw-cua | genuine CUA capture/retain/readback 記錄 | capture 60 秒／image 32 MiB、AX 16 MiB | G_BASELINE PASS 後，大型 offline suite 前；只診斷。 |
| S01-build | SWIFT build --package-path ROOT/rev28 --scratch-path RUNROOT/swift-build --sdk SDK --product rev28ctl -Xswiftc -module-cache-path -Xswiftc RUNROOT/module-cache/swift -Xcc -fmodules-cache-path=RUNROOT/module-cache/clang | 1200 秒／16 MiB | 完成必要實作、source freeze 後，probe 前；build 一次、producer exclusive 複製到 R/bin/rev28ctl、hash/readback。 |
| R01-real-link | live_entry.probe() → PY -B R/checks/validate_real_frame.py --project-root ROOT --grant R/live-grant-1.json --frame-ref REF | 整體 120 秒；native/validator child 各 60 秒／1 MiB | genuine CUA nonempty ALBUMS，全部 production modules；5 秒 action freshness不延長。 |
| N01-syntax | NODE --check FILE | 每個 FILE 60 秒／1 MiB | FILE 恰為 adapter＋R 的 6 個 mjs；每個獨立 ID suffix 01…07。 |
| N02-tests | NODE --test tests/test_cua_adapter.mjs R/checks/test_host_io.mjs R/checks/test_live_classifier.mjs R/checks/test_live_runner.mjs R/checks/test_chooser_v2.mjs | 300 秒／8 MiB | G_REAL_LINK 後完整 Node suite 一次。 |
| P01-batch | PY -B -m unittest discover -s tests -p test_batch_*.py -v | 300 秒／8 MiB | 所有既有 batch tests，包含使用者 dirty authority tests 原样執行。 |
| P02-binding | PY -B -m unittest discover -s tests -p test_project_binding.py -v | 300 秒／8 MiB | existing read binding suite。 |
| P03-transaction | PY -B -m unittest discover -s tests -p test_transaction_core.py -v | 300 秒／8 MiB | existing canonical transaction suite。 |
| P04-v2 | PY -B -m unittest discover -s R/checks -p test_*_v2.py -v | 300 秒／8 MiB | 必須至少 test_authority_v2.py、test_observation_v2.py，discovery 0 cases 不能 PASS。 |
| S02-tests | SWIFT test --package-path ROOT/rev28 --scratch-path RUNROOT/swift-build --sdk SDK -Xswiftc -module-cache-path -Xswiftc RUNROOT/module-cache/swift -Xcc -fmodules-cache-path=RUNROOT/module-cache/clang | 1200 秒／16 MiB | 完整 Swift suite 一次，不只兩個新 test。 |
| B02-preservation-pair | PY -B R/tools/inventory_pair.py preservation | 同 B01 | 交易結束或任一 material blocker 後；report tail 依 §5 明確生命周期另讀回。 |

R01 的 REF 在 source freeze 前凍結 exact policy、capture 前登記 exact file，完成 retain 後以實際 `{path,bytes,sha256}` 引用；不拿尚未存在的 hash 當既定事實。CUA invocation 是 host API，不能用 CLI Node 開另一個 app mock 冒充。child 超時、cap 截斷、no cases、非 0 exit、protocol error 都不能 PASS。長命令非同步執行、至少每 60 秒提供進度；poll/wait 單次不超過 60 秒。

### 7.3 必須涵蓋的 fixtures 與 assertions

- evidence policy：delayed stdout completion、scan 中禁止輸出寫入、partial/race/timeout 比較 BLOCKED、FIFO lstat-only、未知特殊類型 stop、planned vs observed 分離、metadata directory delta、tail publication/readback、exclusive collision/symlink/source drift/cwd 拒絕。
- ledger fixed temp：既有 regular／symlink collision 不刪、open 失敗不 cleanup、created temp 被替換不刪替身、write/fsync/replace/readback failure 原證據保留，shared lock與quota、owner／revision conflict 拒絕。只能在 fixtures，不對真實 state 注入失敗。
- host/classifier：跨 realm Buffer、ArrayBuffer/view/subarray exact bytes；非空合法 ALBUMS 正例；缺/多/亂序 keys；`intersectionPx` 不丟；native unsupported/permissions/PID reuse/window ambiguity/display/crop/scale drift/occlusion/truncation、null/offscreen AX 不造假。
- visual：真實單欄 card/container/pixel boundaries、thumbnail exclusion、safe metadata erosion、日期原字串／ISO 一致、無缺年猜測、partial/duplicate/count/cross-pair 拒絕；JS／Python 對相同 fixture 結果一致。
- chooser：各 phase field 是否存在；stale frame、wrong full path、same leaf different parent、wrong owner/focus/window/control、closed field、one-shot/replay 拒絕；download evidence 與 UI 結果分離。
- orchestration：production dependency 完整，fixture/fabricated/loaded JSON fresh authority 拒絕；第一本 VERIFIED＋terminal readback＋finish/release 早於 post-release scroll／g2；actual scroll NO／UNKNOWN／無 overlap／無新完整卡拒絕；source/grant drift、loaded intent 無 dispatch 權。

## 8. 凍結執行順序與成功證據

### Step 1 — 接收與對帳

讀 AGENTS、兩份文件、P 報告／result／ledger／83 manifest entries 和上次檢討；取得 fresh Git／filesystem anchor。不對 P 做清理／補檔。建立新 input/reconciliation/attempt-extension receipts；記實際 host/session/model、controller能力。所有舊FAIL及UNKNOWN引用保留。

### Step 2 — 工具與新基線

依 §5 bootstrap→固定工具→E01/E02→完整 B01。成功需 G_EVIDENCE_POLICY、G_BASELINE_06 明確 PASS。任何必要 fixture/scan失敗，本輪不得修後重新執行正式 ID；只保留本地故障位置、收 preservation／report，交 Replanner。

### Step 3 — 最早的 raw 真實樣本

選用 documented CUA entry；fresh 讀取 app `jp.naver.line.mac`，在使用者準備好的 canonical Albums 畫面做 D01 passive capture。若取樣需 activate/input，先完成前景交接。無 true ALBUMS／可讀樣本／retention 時先留下現場，不投入大型 suites。D01 未完成不能宣稱 production 可用。

### Step 4 — 必要實作、凍結與一次 build

完成 §6 小範圍修正與 §7 新測試，freeze tools／checks／products／modules／runtime/SDK；最小 wiring 靜態核對，S01 build。由實際 producer hash materialize兩個grants、runtime-binding、authorization／waiver。已完成編譯不表示 native capture 成功。來源凍結後不能為了後續 FAIL 直接改 code重跑；source drift使舊證據無效並停止。

### Step 5 — G_AUTH_RUNTIME 與 G_REAL_LINK

read-only probe經同一 production entry：native before、真實CUA、原样留存、native after、SCK/OCR/analyzer、strict frame、Python read-only validator。需非空 ALBUMS、configured group、至少一張完整唯一可證 card，17 keys／hash／mapping／intersection／focus／occlusion均實際可核對，state/config/ledger無 mutation；拒絕 fixture callbacks及人工作業觀察當PASS。這是本輪第一次回答「真实端到端觀測是否可用」。

### Step 6 — G_OFFLINE

上述真實連接 PASS 後執行 N01/N02/P01…P04/S02 全部一次；tool checks/build/real-link也纳入freeze receipts。任何 mandatoryFAIL停止下載。source/build bytes未改才可沿用同一freeze；有更動不得把前面PASS保留成新build的結果。

### Step 7 — Catalog、候選、menu

先獲得明確前景交接，再 `inspect→begin` 第一個 batch/lifecycle。Canonical group可從已準備的Albums開始，須程式自己驗證，不宣稱任意MAIN_CHAT自主導覽已通過。若版面不足，向使用者說明需調整哪個窗口、為何沒有安全區；人工調整是OBSERVED，重新fresh觀測，不自行新增窗口 actuator。

production callbacks 完成 `analyzeCapture/captureCatalog/prepareCandidates/finalRecords/locateMenu/locateBack/producerGeometry/scrollTarget/preparePostReleaseScroll`；按實際top/bottom及每次≤0.25 view-height、fresh完整唯一有序overlap建立完整catalog；600秒catalog age及5秒actionfreshness不變。不能回傳舊records作freshfinalcatalog。

按manifest order skip VERIFIED／unresolvedbarrier；候選dates/count/group/fingerprint無歧義，fresh同幀fullcard＋safe metadata＋鄰卡安全，先持久binding/readback再CUAclick。任何中間scroll/reflow/unrelatedinput使binding失效，重新觀察；post-openfingerprint必須MATCH，MISMATCH本輪終止，無intent/noSaveAll。

menu calibration在intent前，用真正SaveAlllabel/row／相鄰rowmargin／provider版本布局scale／SCKguard／latency證據確認；校準menu安全關閉且無commandactivation。未知、wrong-row、freshness不足即stop，不能用公式或歷史座標。第二本另做自身G_CATALOG_2與G_MENU_2。

### Step 8 — 第一本交易、下載、檔案與狀態驗收

duplicate、exactemptydestination、owner、persist/readbackintent、menuidentity/geometry、freshness、at-most-once全PASS才派送。Save All為同一不中斷chain的ellipsisclick→既定wait→SaveAllclick；兩click之間無capture/getState/persistence/keyboard/appswitch。區分ellipsisresult與SaveAllinvocationboundary，記一次派送。持久intent是必要前提，不是派送成功證明；loaded/uncertainintent不得重送。

chooser依§6.4fresh每phase確認，GoToFolder完整絕對路徑／leaf／currentdestinationproof，confirm只一次；保留原UI及獨立destinationdelta證明downloadstarted。下載開始後停止LINEGUI，5秒poll、3次完全相同inventory及bytes、max600秒。含hiddenentries／alltypes，不followlinks：expectedimagesexact、zero/partial/temp/unrecognized=0、無異常subdir/symlink，逐檔content/MIME＋**完整ImageIOdecode**，前後inventory一致／hash穩定，不能只看副檔名／數量。

canonicalfinalize將VERIFIED、registry與owner/context清除同一revision提交、讀回；FilesystemPASS、terminalCOMMITTED、readback、實際错误分別列。終止owner不再普通mutate；後續returnlist使用既有nav-onlyauthority，freshfinalcatalog→finish→releasebatchowner；在第二步開始前證明active_writer/context/batch狀態符合既有終端生命週期。

### Step 9 — 不可省略的 post-release 實際捲動

第一本VERIFIED／readback及lifecycleowner釋放後，fresh回Albums；即使第二張已可見，也需一次**實際 downward 0.25-view-height scroll**。保存before／invocation／after原圖與frame；同group／surface／session／PID/processinstance/window/display/layout，至少一張完整唯一相鄰card有序overlap，觀察到位移effect，至少一張新完整card可讀dates/count。座標只依latestframe。

NO或UNKNOWNeffect、overlap缺失、只partial／duplicate、新candidate不明確都不可連續輸入或猜點；保留阻塞。無eligible下一本記NO_ELIGIBLE_TARGET；未捲動記SCROLL_TEST_NOT_RUN/PARTIAL。不得reopenVERIFIED製造第二案例。G_SCROLL只能由此實際證據PASS。

### Step 10 — 第二本、保全、回報與Acceptance

建立`minimal-live-06-g2`、新的cap1lifecycle；不同fingerprint、fresh完整catalog與card、destination/intent/menu/chooser/download/content/terminalreadback全部重跑，仍受總quota與ledger限制。任何第一本或scrollfailure都不開始第二本。

成功或materialstop都收B02／tailreadback、E2E報告／progress／ledger／format3result／manifest，交本Replanner。獨立Acceptance由未參與任何產品／本輪artifact貢獻的Reviewer對mergedcandidate及實際證據判定；本Implementer不能自評PASS。缺通道則PENDING，保留handoffpacket，不宣稱已交接。

## 9. Gates：明確 PASS 才算通過

所有 IMPLEMENT gate：owner ROLE、evidence_source ROLE_OBSERVATION、required true、reuse NEVER；G_ACCEPTANCE改phase ACCEPTANCE、獨立Reviewer。其餘machine欄位完全依附錄A。

| Gate | PASS所需證據 | criticality／role／closure |
|---|---|---|
| G_BASELINE_06 | 完整2scan一致、bootstrap/writepolicy、protectedreadback、FIFOmetadata、freshGitidentity。 | CORE／MUST_NOT_BREAK／BASELINE_DELTA |
| G_EVIDENCE_POLICY | E01/E02（含tail生命週期fixtures）、不可回填allowlist、記憶體streams／成對scan、bootstrap exclusive publication/readback；實際最終tail納入G_PRESERVE_06與G_REPORT。 | CORE／MUST_NOT_BREAK／HARD_CLEAN |
| G_AUTH_RUNTIME | 父決策＋本輪extension/waiver、g1/g2、sharedquota、sourceclosure、PY/NODE/SDK/producer/decoder全部實測hash。 | CORE／MUST_NOT_BREAK／HARD_CLEAN |
| G_REAL_LINK | genuineCUA→retainreadback→native/SCK/OCR→nonemptyALBUMSstrict17key→Pythonvalidator；無state/UI副作用。 | CORE／OUTCOME／HARD_CLEAN |
| G_OFFLINE | §7全部mandatorycommands一次成功、casecount正確、frozenbuild/refs相符。 | CORE／MUST_NOT_BREAK／HARD_CLEAN |
| G_CATALOG_1、G_CATALOG_2 | 各自freshcompletecatalog、order/coverage/duplicates及eligiblefullcardproof；不能相互替代。 | CORE／OUTCOME／HARD_CLEAN |
| G_MENU_1、G_MENU_2 | 各自真實SaveAllidentity／geometry／freshbinding／safeclose／menuSCKguard及dispatchpreconditions。 | CORE／MUST_NOT_BREAK／HARD_CLEAN |
| G_FIRST | 第一本完整交易、onceSaveAll/confirm、download、全檔decode、VERIFIED/registry/ownerreadback。 | CORE／OUTCOME／HARD_CLEAN |
| G_SCROLL | 第一本交易完成與release後實際0.25scroll、freshcontinuity/orderedoverlap/movedeffect/newcompletecandidate。 | CORE／OUTCOME／HARD_CLEAN |
| G_SECOND | 不同eligible第二本全部獨立交易、內容、state/readback/finish/release，無多餘派送。 | CORE／OUTCOME／HARD_CLEAN |
| G_PRESERVE_06 | 新baseline→post、範圍精確、原239files/history保持、state/ledger diff合法，reporttail依policyreadback。 | CORE／MUST_NOT_BREAK／BASELINE_DELTA |
| G_REPORT | 完整報告／progress／attemptledger／format3result／manifest逐byte核對，關鍵事實連原始證據。 | SUPPORTING／OUTCOME／HARD_CLEAN |
| G_ACCEPTANCE | 獨立Reviewer對兩本、scroll、交易、資料與保全明确PASS；nativeclosure限制如實保留。 | CORE／OUTCOME／HARD_CLEAN |

Waiver是獨立使用者決策，不是上述toolPASS。OBSERVED／NOT_RUN／BLOCKED／FAIL不能寫成PASS；formalnativevalidation缺失不能用G_REPORT的本地結構核對掩蓋。

## 10. 嘗試預算、停止與失敗處理

產品rootissue `LIVE_CLASSIFIER_CHOOSER` 歷史3/3已用盡，第三次於2026-10-11T03:14:19.529959Z syntaxlaunch消耗；本輪extension允許**額外1個完整、有界collection（累計第4）**，不是新的3次。在本輪第一個產品證據動作（D01 rawcapture）launch前，persistextension＋attemptstart。所有后續probe/offline/E2E是同一collection的子步驟，每個formalID只一次。

工具保全issue已有1次已知preservationFAIL；baseline舊NameError/FIFO失敗及smoke歷史另引用，不重置、不擅合併成0。E01/E02若失敗也留attempt、新資訊及決策，不能修改后再假装首次正式成功。探索性source閱讀／靜態核對不當產品check；有意義的probe／smoke照實入ledger。舊未知次數保持UNKNOWN。

停止：任何requiredFAIL、materialblocker、unexpectedwrite、unknownidentity/focus/path、permission缺失、source/grantdrift、writerconflict、freshness不足、intent/dispatch不确定、用戶取回前景。暫停輸入不代表自動取得重試權；failedcollection只收保存／報告，不以新ID重跑同rootissue。

如尚未intent：依現有canonicalstop/terminalprotocol保留SAFE_ABORT，無SaveAll。已intent／attempteddispatch：不重送，依canonicalprotocol保留barrier與retry=false；明確non-dispatchresolution只能依既有proof及持久readback辦理，不能用emptyfolder推定。finalization或writerguard失敗時不另換writer／直接改JSON。fixturecleanup只本輪已建立且identity匹配；realbackup及未知temp不刪。下一步交回Replanner，報告最小reproduction／rawerror／狀態前後／已用attempt／新資訊／精確所需決策。

## 11. 必交產物與六個獨立狀態

Implementer在R（非global.codex）建立：

- `plan-contract.json`、byte-identical `handoff.json`、`check-specs.json`、`check-specs-freeze.json`、`authorization.json`、`plan-review-waiver.json`、`attempt-extension.json`、`live-grant-1.json`、`live-grant-2.json`、`runtime-binding.json`、`input-manifest.json`。
- bootstrap／immutableoutputpolicy／observedmanifest／pairedinventories／publicationreadbacks／commandinvocations&streams／gate receipts；frame/native/AX/SCK/OCR/mapping/chooser/action evidence、每本destination manifest／full decode／state/ledgerreadback、post-release scroll證據。
- `E2E測試報告.md`、`progress.md`、`evidence/attempt-ledger-06.json`、`evidence/implementation-result.json`（format3）、`evidence/report-manifest.json`；可用時獨立`acceptance.result.json`及controller原生驗證收據。

manifest每項相對/絕對path、bytes/hash、producer、invocation/phase和claim；self-reference不假造自己的hash，manifest/result/report尾檔採預宣告order及exclusivehashreadback。報告記目標/版本、完整實際時序、工具/argv/env/關鍵片段、環境與資料、expected/actual、PASS/FAIL/NOT_RUN、所有sideeffects/前後diff、每次attempt新資訊、未知/停止原因、下一個決策。不能只交摘要或用人工作業觀察代替工具證据。

六status不得合併：PRIMARY_OUTCOME（有界兩本實證）、IMPLEMENTATION（程式完成度）、CORE_ACCEPTANCE（自身gates）、REQUIRED_VERIFICATION（含native未完成）、INDEPENDENT_ACCEPTANCE（獨立結果）、TASK_CLOSURE（是否全部满足）。只有第一本PASS時保留它，第二本BLOCKED仍報PARTIAL；兩本/scrollPASS但native或Acceptance未完成時保留產品成果，closure仍PENDING/INCOMPLETE，不能DONE。父完整群組目標未滿足不可關閉。

## 附錄 A：唯一 format 3 machine contract

以下 block 与 handoff.md 的同名 block **逐 byte一致**；Implementer extraction只取opening/closing fence之間UTF-8原始bytes，包含末尾一個LF，不加BOM、不改keyorder/whitespace。本地parse/equality/readback只證明文件一致性，native validation仍NOT_RUN。

<!-- FROZEN_CONTRACT_START -->
```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "In one user-authorized additional bounded collection, repair task evidence publication and the real CUA/native observation pipeline, prove the shared production probe, then complete two distinct eligible LINE album transactions in separate cap-one lifecycles with an actual post-release 0.25-view-height scroll, complete content/state verification, preservation, reporting and independent Acceptance; preserve historical failures and unrelated work.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06",
    "scripts/line_backup_cua_adapter.mjs",
    "src/line_backup_batch/cli.py",
    "src/line_backup_batch/observations.py",
    "src/line_backup_batch/store.py",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift",
    "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift",
    "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift",
    "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-v3.tmp",
    "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "harness-development/line-v3-live-e2e-20261010/.gui-ledger-v3.tmp",
    "backups/旻謙允禎成長日記"
  ],
  "required_evidence": [
    "E_BOOTSTRAP_06",
    "E_INPUT_RECONCILIATION_06",
    "E_ATTEMPT_EXTENSION_06",
    "E_PLAN_REVIEW_WAIVER_06",
    "E_EVIDENCE_POLICY_06",
    "E_BASELINE_06",
    "E_AUTH_RUNTIME_06",
    "E_RAW_CUA_06",
    "E_REAL_LINK_06",
    "E_OFFLINE_06",
    "E_CATALOG_1_06",
    "E_MENU_1_06",
    "E_FIRST_06",
    "E_POST_RELEASE_SCROLL_06",
    "E_CATALOG_2_06",
    "E_MENU_2_06",
    "E_SECOND_06",
    "E_PRESERVATION_06",
    "E_REPORT_06",
    "E_INDEPENDENT_ACCEPTANCE_06"
  ],
  "gate_specs": [
    {
      "gate_id": "G_BASELINE_06",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "BASELINE_DELTA",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_EVIDENCE_POLICY",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_AUTH_RUNTIME",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_REAL_LINK",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_OFFLINE",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_CATALOG_1",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_CATALOG_2",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_MENU_1",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_MENU_2",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_FIRST",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_SCROLL",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_SECOND",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_PRESERVE_06",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "BASELINE_DELTA",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_REPORT",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_ACCEPTANCE",
      "required": true,
      "owner": "ROLE",
      "phase": "ACCEPTANCE",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    }
  ],
  "capability_policy": {
    "network": "OFF",
    "browser": false,
    "destinations": []
  },
  "retry_policy": {
    "transient_read_only_retries": 2,
    "delays_seconds": [
      10,
      30
    ]
  },
  "resource_policy": {
    "prompt_bytes": 65536,
    "state_bytes": 524288,
    "inspect_bytes": 16384,
    "log_bytes": 134217728
  },
  "workflow_policy": {
    "plan_review_required": true,
    "independent_acceptance_required": true,
    "max_parallel_read_only_helpers": 0,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
<!-- FROZEN_CONTRACT_END -->
