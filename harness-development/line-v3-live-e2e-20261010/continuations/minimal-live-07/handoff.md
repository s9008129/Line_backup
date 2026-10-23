你是本輪根 Implementer。請依 Replan 07 修復 minimal-live-06 提報的全部七項證據工具缺陷，先完成共用 output-policy evaluator、安全 publication、正確綁定的 one-shot runner、E01/E02及 anchor-aware B01，再立即以真正 CUA取得 LINE raw sample。其後修復同一 production entry 的 native/CUA/SCK/OCR/classifier/Python證據鏈，完成必要離線測試，再執行兩本不同 eligible相簿的完整備份；第一本 VERIFIED、terminal readback及owner release後必須實際捲動0.25視窗高度，確認continuity、ordered overlap及新完整候選，才開始第二本。使用者已授權範圍內編輯與最多可安全配置的並行writer，不重問工作授權；Plan Review豁免、最後独立Acceptance仍必要。保留所有dirty/untracked資料、歷史失敗和累計attempt；Save All不確定即禁止重送。範圍內有界修正使用新epoch、保留FAIL並重驗相應gates。只回報實際觀察，不把模擬、人工觀察、本地parse或不存在controller收據寫成PASS。每輪實測更新E2E測試報告並交根Planner；達成全部必要gates才結案。

# Replan 07 implementation handoff

日期：2026-10-11。本文件與plan.md共同凍結實作契約；附錄machine contract字節一致。文件交付不是實作或E2E完成。

## 1. 接手定位及優先順序

ROOT=`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；TP=`harness-development/line-v3-live-e2e-20261010`；R=`TP/continuations/minimal-live-07`；EPOCH=`ROOT/R/epochs/e01`，修正e02/e03。父task=`TASK-20261010-line-v3-live-e2e`，新run ID；舊continuation與root issue不重置。文件出版前HEAD=`6b63e9df72f27eadc73a3cd631faca923d09a532`；接手使用fresh post-publication HEAD。

優先順序：使用者授權/AGENTS → 本輪plan及machine contract → 本輪handoff → 舊報告原始證據 → 附錄原§6/§7技術規格。舊R、writer=0、formalFAIL即停止、sources不可修後重测等由本輪epoch/有界修正規則取代；舊產品安全要求保持。

必讀minimal-live-06的問題提報單、E2E報告、plan、result、attempt ledger、manifest和本機prewrite anchor。manifest39項已在planning核對吻合，但Implementer仍作fresh readback。四個主要source hashes：

```text
問題提報單.md 1ab89332a1bb8638595c10cf851bda03154b376682aece87d4d690c8bb07f690
E2E測試報告.md 4d12a17ae0f027e8765d480fd5f3af208c1e1e7dc5ec7c572a2a35bd6d5fa18a
plan.md 57090d3af4ea0075b23d40c6733e7e094a757ed3b8f0969e91b48a0f8da94cb8
prewrite-anchors.json a3c4160b6eeb8f653f45313bf470fd8db72ffd4a323e9d477395c154a7930e69
```

anchor含dirty diff且未納入舊提交，只讀；metadata/Git/protected scope不偽稱完整content baseline。舊正式E01/E02/B01/D01 NOT_RUN，不能寫runtime FAIL；這是tool readiness blocker，不是資料遺失。

## 2. 範圍、權限與能力

九個產品paths及canonical transaction paths以附錄contract為唯一allowlist；只有ROOT/R新task artifacts與九檔必要產品修改。保留11個既有tracked dirty與全部untracked/ignored工作；config、其他Swift/root tests、Package.swift、AGENTS、歷史package及照片不改。

state schema3、17-keyframe、V2grant keys、現有lock/CAS/canonical writer、共享ledger/quota、每lifecycle1、5秒actionfreshness全部保持。兩本不同fingerprint、最多兩個exact new destination，不能同lifecycle擴quota。CONTRACT_PATH=R/plan-contract.json；grants/runtime-binding/modules綁exact EPOCH，source closure同JS/Python/Swift。

PlanReview USER_WAIVED_NOT_RUN；handoff review不要另起；最後独立Acceptance required。使用者本次add/commit/push只針對交付文件，不推導產品git publication權限。

immutable Harness4.8 resource root沿用原plan；launcher指向缺失Python3.14已觀察。只作一次bounded readiness；沒有nativecontroller就root串行＋只讀helpers，不偽造allocation/validation、不修global.codex、不換release。native closure限制明列，但不拿來延後已授權安全產品驗證。

helpers/writers上限4，host總slots4；root之外最多3同時。W1 literal epoch tools/checks，W2五Swiftpaths，W3三Pythonpaths及literal v2 fixtures；root owns adapter/host modules/政策/合併/LINE/state。只有實際controller登記externalworktree及completed/merged receipts後才能writer編集。不能把helpers改名繞過writer gates。

## 3. 必須完成的架構及issue對照

1. output_policy.py是唯一evaluator；publisher和comparator共用。每rule exact path/parent、phase、producer、type/cap、lifecycle、receipt/readback；unknown rule fail closed。消除flat filename放行，補check/inventory/gate/dynamic/transaction規則。
2. evidence_io.py從ROOTdirfd逐層O_DIRECTORY|O_NOFOLLOW，leaf O_EXCL|O_NOFOLLOW，shortwrite/EINTR、fstat、fsync/parentfsync、bytes/hash/dev/ino讀回。dynamic寫前registration，observed不授權。新正式publication不用cp；舊cp不追認exclusive。
3. runner綁本輪literalROOT/R/task/epoch，純讀preflight後claim fsync/readback，再invocation/launch；argvarray shellfalse cwdROOT；source/runtime/HEAD/branch/index/preimage/outputcollision驗證。claim持久即消耗，不刪、不重用，未知launch不能推定未執行。
4. child streams記憶體捕捉，killgroup/reap後發布，timeout/cap/exit/signals完整記錄；env只必要差異不含secrets。pair期間沒有寫檔。
5. B01對帳freshanchors/bootstrap/protected/Git，再完整雙scan及publication。special只lstat，partial/race/timeoutBLOCKED不算missing；directorymeta只能由合法childdelta/receipt解釋。
6. B02支持canonicaltransactionreceipts；九產品diff、新artifact、state/ledger revision chain/owner/quota合法，原照片/历史registry不變。native filenames事後observedmanifest不能擴張destination授權。
7. E01用真scanner/publisher/delayed subprocess和IO spy；E02補全，spec/freeze完整後launch。語法compile不是formalPASS。

production接線建立六mjs與Pythonvalidator；probe和runTwoAlbums同capture/analyzer/classifier/validator。probe無owner/destination/state/input。native-context只passive；真before/CUA/after/SCK/window/process/display/anchors關聯，不能合成AX或圖像geometry。明確傳遞intersectionPx，非空ALBUMS正例、JS/Python一致keys、VISUAL_NATIVE完整card/thumbnail/metadata witness，chooser依phase驗完整path/owner/focus/control。

## 4. 執行順序及重測

1. freshGit/index/unrelatedpreimages/protected/namespaceanchors，inputs對帳；原件保留。
2. bootstrap/outputpolicy/spec/tools，E01/E02 PASS，B01 PASS；出版自己的outputs有tailreadback。
3. attempt-start/extension持久化，立即D01 genuineCUA retain/readback；raw不是productionPASS，不等大型suite。
4. 根據raw最小實作、sourcefreeze、S01build、exactruntimebinding/grants。
5. G_AUTH_RUNTIME與R01 genuine nonemptyALBUMS productionprobe，state/ledger unchanged；全部offline suitesPASS。
6. 前景明确交接後第一本catalog/card/menu/destination/intent/once dispatch/chooser/download/full decode/finalize/readback/finish/release。
7. release後actual downward0.25scroll，before/invocation/after、identity/effect/orderedoverlap/new完整card。
8. 不同第二本重跑自身全部gates；失敗/uncertainty不進下一本。
9. B02、tailreadbacks、E2Ereport/progress/attemptledger/format3result/manifest，交Planner及独立Acceptance。

每rootissue3次evidence-bearingattempts扣除歷史，2次无資訊增益停止；未知不是0。LIVE_CLASSIFIER_CHOOSER歷史3＋一次extensioncollection保留，累計4在ledger；format3 convergence局部scope在analysis明示，不能填4或暗截3。新epoch/新claim保留FAIL，source改動重驗受影響freeze/build/grant/probe/tests。epoch不重置quota/dispatchbarrier。架構/資料/gate變更回Planner。

前景未交接只做不依賴前景工作；被取回停止input並fresh重新核對。unknownintent/dispatch不重送，emptydirectory不是non-dispatchproof；不換writer/directJSONrepair/降低gate。

## 5. 驗收與持久交付

E01/E02/B01是D01前置；S01/R01及N01/N02/P01-P04/S02是下載前置。formalcheck每(epoch,ID)一次，no cases/timeout/cap/protocol/nonzero不能PASS。fixedledgertemp碰撞/替身不刪及write/fsync/replace/readback/owner/CAS/quotafault僅fixture。

SaveAllpair不能穿插觀察/持久化；chooserUI与downloaddelta分開。5秒poll/3stable/max600，hidden/alltypes、MIME/fullImageIOdecode/hash；FilesystemPASS與stateCOMMITTED分列。實際scroll不可由visible第二卡替代；NO_ELIGIBLE_TARGET或SCROLL_TEST_NOT_RUN如實記。

每次測試E2E報告完整實際順序、工具/argv/env/關鍵片段、expectedactual/錯誤/前後diff/副作用/attemptlearning/未知，証據relative+absolutepath/bytes/SHA/producer/invocation。尾檔報告→progress→ledger→result→manifest→tailreceipt，manifest不selfhash、不循環，最後publisher實際readbackref。六狀態分開，native/Acceptance/live不足不能DONE。

本輪附錄machinecontract已凍結；擷取原UTF8 bytes（一末尾LF）到plan-contract.json和handoff.json，fullbyte/hash相同，不prettyprint重造。只能使用controller實際emittedCONTRACT/RESULT命令；parse/hash/equality不是nativePASS。

以下附錄移植原§6/§7精確技術/argv；本輪上文覆蓋其旧continuation/source binding、run ID、writers與一次失敗即停規則。附錄R指本epoch工作root，CONTRACT_PATH例外固定本輪R/plan-contract.json。


## 附錄 A：來源技術規格與精確檢查 argv

來源：minimal-live-06/plan.md §6、§7，SHA-256 57090d3af4ea0075b23d40c6733e7e094a757ed3b8f0969e91b48a0f8da94cb8。以下 R/RUNROOT 指本 epoch 工作 root；CONTRACT_PATH 固定本輪 continuation 的 plan-contract.json，grants/runtime-binding/source refs 改綁 exact epoch。舊 formal ID 一次約束作用於 (epoch, check ID)；本輪允許有界修正後建立新 epoch，所有 FAIL 保留。附件的 fixture/safety/numeric thresholds 保持，本輪正文的 scope、waiver、delegation、retry/epoch 規則優先。歷史 runtime 能力為參考，接手必須 fresh 驗證，不當本輪 PASS。

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

Python CLI、Swift producer、JS runner 的 CONTRACT_PATH／SHA／continuation 必須同時綁 R 與附錄 A **實際 bytes hash**。維持既有 V2 live grant 與 `user-decision-A.json` 的父 task_id；owners 精確為 `minimal-live-07-g1`、`minimal-live-07-g2`。

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


## 附錄 B：唯一 format-3 machine contract

以下 code block 的原始 UTF-8 JSON bytes，含末尾一個 LF，在 plan.md 與 handoff.md 完全相同。USER_WAIVED_NOT_RUN、actual host capacity、publication/epoch lifecycle 另由正文規範及本輪 receipts 記錄，不偽造 schema 欄位。

```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "Repair all seven minimal-live-06 evidence-tool blockers through a shared lifecycle policy, one-shot runner, anchor-aware baseline and transaction-aware preservation; acquire genuine LINE raw evidence immediately after E01/E02/B01, repair the common production observation chain, pass required offline checks, and complete two distinct cap-one album transactions with actual post-release 0.25-view-height scroll, full content/state verification and independent Acceptance. Preserve historical failures, unrelated work, at-most-once barriers and cumulative attempts; permit bounded in-scope repair using fresh immutable epochs.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07",
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
    "backups/旻謙允禎成長日記",
    "harness-development/.writer-coordination"
  ],
  "required_evidence": [
    "E_BOOTSTRAP_07",
    "E_INPUT_RECONCILIATION_07",
    "E_ATTEMPT_EXTENSION_07",
    "E_PLAN_REVIEW_WAIVER_07",
    "E_EVIDENCE_POLICY_07",
    "E_BASELINE_07",
    "E_AUTH_RUNTIME_07",
    "E_RAW_CUA_07",
    "E_REAL_LINK_07",
    "E_OFFLINE_07",
    "E_CATALOG_1_07",
    "E_MENU_1_07",
    "E_FIRST_07",
    "E_POST_RELEASE_SCROLL_07",
    "E_CATALOG_2_07",
    "E_MENU_2_07",
    "E_SECOND_07",
    "E_PRESERVATION_07",
    "E_REPORT_07",
    "E_INDEPENDENT_ACCEPTANCE_07"
  ],
  "gate_specs": [
    {
      "gate_id": "G_BASELINE_07",
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
      "gate_id": "G_PRESERVE_07",
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
    "max_parallel_read_only_helpers": 4,
    "max_parallel_writers": 4,
    "handoff_review_required": false
  }
}
```
