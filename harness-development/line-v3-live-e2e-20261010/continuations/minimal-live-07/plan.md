# Replan 07：修復證據鏈，立即推進 LINE 實機測試

日期：2026-10-11。角色：根 Planner。風險：CRITICAL。文件交付不是 implementation、native validation 或 E2E PASS。

## 1. 結果、來源與凍結決策

ROOT：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
TP：`harness-development/line-v3-live-e2e-20261010`。
R：`harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07`。
RUNROOT：ROOT/R。EPOCH：RUNROOT/epochs/e01；修正依序使用 e02、e03。
父 task：`TASK-20261010-line-v3-live-e2e`；新 continuation、新 run ID，不重置父 root issue。

目標：先修復 minimal-live-06 全部七項證據工具缺陷，完成 E01/E02 和可信 B01 後立即取得真正 LINE raw sample；再修復 production observation chain，完成必要離線測試、第一本完整交易、owner release 後實際 scroll，以及不同第二本完整交易。不能完成時留下第一個可重現的實機或工具阻塞，回饋 Planner。最多兩本、各自 cap-one lifecycle；兩本成功不代表全群組備份完成。

已核實：HEAD `6b63e9df72f27eadc73a3cd631faca923d09a532`、branch `v43-ab/codex-rev28`；minimal-live-06 manifest 39 項逐項 bytes/hash 吻合。另有 11 個既存 tracked 修改及大量 untracked 資料。E01/E02/B01/D01 未執行，沒有本輪正式測試失敗或照片遺失證據。四個預定新增 Swift 檔目前不存在。Implementer 在文件 commit 後重新取得 fresh HEAD、index 和 filesystem baseline，不硬套此出版前 HEAD。

重要輸入均位於 minimal-live-06：

| 檔案 | SHA-256 |
|---|---|
| 問題提報單.md | 1ab89332a1bb8638595c10cf851bda03154b376682aece87d4d690c8bb07f690 |
| E2E測試報告.md | 4d12a17ae0f027e8765d480fd5f3af208c1e1e7dc5ec7c572a2a35bd6d5fa18a |
| plan.md | 57090d3af4ea0075b23d40c6733e7e094a757ed3b8f0969e91b48a0f8da94cb8 |
| prewrite-anchors.json（本機，未納入該提交） | a3c4160b6eeb8f653f45313bf470fd8db72ffd4a323e9d477395c154a7930e69 |

原 anchor 含 workspace dirty diff，只讀；它是 Git/metadata/protected-file anchor，不能宣稱全 workspace content preimage。minimal-live-06、舊契約、歷史 failures、.local、backups 保留原樣。本輪 GPT-6 luna 已完成唯讀技術研究，並非 Plan Review 或 gate PASS。

使用者已明確決定略過 Plan Review、保留最後獨立 Acceptance，並允許範圍內有界修正重測；不再重問工作授權。CRITICAL 的 plan_review_required 保留 true，以獨立 USER_WAIVED_NOT_RUN 決策記錄豁免，不寫 reviewer PASS。handoff_review_required=false。使用者後續授權本輪文件 add/commit/push；此授權不自動擴張為未來產品提交。

## 2. 第一性原理及全部 issue 裁定

可信備份的因果鏈是：操作前資料 → 已授權動作 → 可歸因差異 → 檔案驗證 → canonical state 提交及讀回。兩次 scan 相同只證明两个觀察一致，不能單獨證明 bootstrap 合法、原資料保存或交易變更合法。

| Issue | 根因 | 必做修正 |
|---|---|---|
| 1 comparator 漏讀政策 | publisher/comparator 使用不同授權模型 | 唯一 evaluator 同時驗證 exact path、phase、producer、type/cap、lifecycle、receipt |
| 2 B01 不對帳 anchors | 將 pair 一致誤當可信 baseline | fresh anchors、protected preimages、bootstrap delta、Git identity 全部對帳 |
| 3 flat fixed_files | 檔名沒有合法生命週期 | 逐項政策，未知或未實作規則拒絕，禁止 blanket directory exemption |
| 4 舊 runner/無 claim | 複製舊 binding，缺少持久 launch boundary | literal ROOT/R/task/epoch，preflight 後 O_EXCL claim、fsync/readback 再 launch |
| 5 E01 不完整 | stub 沒驗證真正副作用 | 真實 scanner/publisher/subprocess；證明 scan 無寫、special 未 open、tail 與 registration 次序 |
| 6 E02/spec/freeze 缺失 | 未先完成最小驗收垂直切片 | 補 spec/freeze/selftest，正式 launch 前完成 readiness |
| 7 cp 無 exclusive 證據 | 目標不存在不等於 exclusive-create | 新輪正式 publication 使用 anchored dirfd/O_EXCL/no-follow/fsync/readback；舊限制不補造 |

工程根因：政策、執行器、比較器與測試分別演進，沒有先完成一條完整可驗收的路徑。本輪順序固定為 evidence 核心 → E01/E02 → B01 → D01，不在工具失效時繼續堆疊產品骨架。

## 3. 寫入範圍與技術邊界

唯一九個可編輯／新增產品 literal paths：

```text
scripts/line_backup_cua_adapter.mjs
src/line_backup_batch/cli.py
src/line_backup_batch/observations.py
src/line_backup_batch/store.py
rev28/Sources/rev28ctl/main.swift
rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift
rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift
rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift
rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift
```

R 內可建立本輪 drafts、tools、checks、modules、epochs、fixtures、build、evidence、reports。正式來源/outputs 分 epoch CREATE_ONCE；不要覆寫前一個 frozen epoch。draft 僅在凍結前可更新。

交易資料 paths：`state/backup_state.json`、`state/.line-backup-state.lock`、`state/.line-backup-v3.tmp`、`TP/gui-ledger.json`、`TP/.gui-ledger-v3.tmp`、`backups/旻謙允禎成長日記`。這是 canonical transaction 邊界，不是任意編輯權。backup 僅允許最多兩個事前登記的新空 destination，由 LINE 原生新增檔；既有照片不可改、刪、搬、覆寫。

`harness-development/.writer-coordination` 僅授權原 immutable controller 的 allocation/reservation lifecycle；啟動前從 controller 來源列出 exact outputs/producer/lifecycle。不由 task 工具任意修改或豁免整個目錄。

不得修改既有 dirty Composition/Sensor/NativeObservationSession/root tests、config、Package.swift、AGENTS、歷史 task package；不得遷移 state、換 canonical writer、另建 ledger、放寬 5 秒 freshness、重送 Save All、新增 AppleScript/AX writes/shell GUI automation。

## 4. 實作架構與執行順序

### A. 唯一證據核心與 output lifecycle

建立 `tools/evidence_io.py`、`tools/output_policy.py`、`tools/inventory_pair.py`、`checks/run_command.py`、E01/E02 fixtures。正式版本、spec、grants、runtime binding、source freeze 放在 EPOCH。正式 sources/output 不覆寫；修正以新 epoch 发布。

每條 policy rule 必含 rule_id、exact_path 或受限 kind/sequence 展開、exact_parent、producer、allowed_phase、entry_type、max_bytes、lifecycle、required_receipt、readback_requirement。publisher/comparator 共用一個 evaluator；禁止 flat filename 直接放行、未知 rule silently ignore 或事後填 allowlist。

生命周期：CREATE_ONCE（claim/spec/grant/streams/receipt/artifact）、DRAFT_BEFORE_FREEZE、CANONICAL_TRANSACTION、PRODUCER_SCRATCH（exact producer/root/lifetime）。動態 artifact 寫前先發布 exact normalized path registration；observed manifest 只記發生，不能授權。來源 draft 使用直接 edit tools；正式 publication 從已完成 literal source bytes exclusive materialize，不用 cp 覆寫。

從可信 ROOT directory FD 逐層 open O_DIRECTORY|O_NOFOLLOW，每層 fstat 驗證；leaf O_CREAT|O_EXCL|O_NOFOLLOW。處理 short write/EINTR；regular-file fstat、file fsync、parent fsync、同 parent dirfd no-follow readback，核對 bytes/hash/dev/ino。resolve/lstat 後再完整 path open 不能替代逐層 dirfd。runtime capability 或 directory fsync 不支持，保留原錯誤並 BLOCKED，不降級成成功。

### B. 固定 binding runner 與可信 inventory

runner 順序：純讀 preflight → exclusive claim → fsync/readback → invocation → launch → reap → streams → receipt。CLI 只接受 frozen epoch/check ID，不接受任意 argv/env/root override。check specs 在 launch 前把符號展成 exact absolute argv；所有 child argv array、shell=False、cwd=ROOT。

preflight 驗證 ROOT、R、task、epoch、HEAD/branch/empty staged index、原 unrelated dirty preimages、exact argv/cwd、runtime realpath/hash、contract/spec/source hashes、phase prerequisites、output collision/symlink。保存必要 env overrides/diff，不输出 secrets，不改 HOME/CODEX_HOME。

claim 持久化即消耗 (epoch,check ID)，launch 前 crash 也不刪 claim 或重用 ID。claim 無 completion 記 UNKNOWN；process 不存在或 outputs 缺失不是 non-launch proof。streams 在記憶體，到 child/group reap 後發布；timeout/cap breach kill/reap 並保留已收到 bytes。

B01：fresh namespace/metadata/Git/protected-content anchors → 對帳事前 bootstrap 許可與 publication receipts → 完整 scan-1 → scan-2 → completeness/compare → publication/readback。兩個 scan 之間禁止任何工作區寫入；runner claim/invocation 在 scan-1 前完成。inventory child 出結果後才發布 inventories，runner child reap 後才發布 streams/receipt，兩者都納入 publication tail audit。

regular file no-follow、前後 dev/ino/size/mtime/ctime 穩定並 hash；symlink 只記 link target。唯一已知 FIFO 路徑沿用原 §5.2，只 lstat；未知 socket/FIFO/device 不 open/read/hash，留 metadata 並 BLOCKED。partial/race/timeout complete=false，不計算巨量 removed。directory metadata 變動僅以合法 child-entry delta 和相符 before/after publication receipt 解釋，identity/mode/owner仍受保護。

B01 PASS 需完整一致 pair、fresh Git identity、bootstrap delta 合法、protected config/state/ledger/history/backups preimages 保存。舊 metadata anchors 不偽稱全內容基線。

B02 比較 fresh B01 與 post pair：產品 diff 只九檔，全部 outputs 有合法 lifecycle/producer/receipt，canonical state/ledger revision/owner/run/operation 鏈合法，原照片及历史 registry 不變。unknown native filenames 只允許 LINE 在事前已授權 exact empty destination 新增；不能事後放寬 scope。成功或 material blocker 都收 preservation；無可信 baseline 只能報無法完整判定。

### C. 最早 D01 與 production observation

E01/E02/B01 PASS 後立即 genuine CUA raw sample，不等大型產品 suites。app=`jp.naver.line.mac`、configured group=`旻謙允禎成長日記`。capture→normalize→原 bytes retain/readback；記 screenshot/AX、dimensions、Buffer/view offset/length、bytes/hash、UTC/monotonic/timing。D01 不 acquire owner、不建 destination、不寫 state/intent、不送 UI input。若需前景切換或導覽，先完成專案明確前景交接；未交接先做其他工作。D01 不等於 G_REAL_LINK。

production entry 的 probe() 和 runTwoAlbums() 共用 capture/retain/native/SCK/OCR/analyzer/classifier/Python validator；不允許 fixture callbacks、loaded frame 冒充 fresh authority。建立 host_io、live_analyzer、live_classifier、live_runner、live_entry、chooser_locators 六個 mjs 及 validate_real_frame.py。

保留原 §6 的 native-context passive producer、before/CUA/after/SCK 非原子關聯、三個非共線 anchors mapping、intersectionPx、5秒 action freshness、17-key frame、state schema3、strict v2 witnesses、完整單欄 card/thumbnail exclusion/metadata erosion、chooser 分phase full-path/owner/control驗證。四個新增Swift檔是實作任務，不假設已存在。

source closure 含既有 SOURCE_PATHS、全部相關Swift Sources/Package.swift、本epoch modules、runtime、producer與ImageIO decoder。CONTRACT_PATH綁R/plan-contract.json；runtime-binding/live grants綁exact epoch refs，JS/Python/Swift同步验证同一 membership。不改V2 grant key集合；更新其既有ref語義驗證以支持此已核准exact epoch路徑。

### D. 實機兩本

必要順序：G_AUTH_RUNTIME/G_REAL_LINK → G_OFFLINE → 第一本 → VERIFIED/readback/finish/release → 實際scroll → 第二本。

fresh完整catalog與same-frame完整card/safe metadata binding後開相簿；post-open fingerprint必須MATCH。menu校準在intent前，真實Save All identity/geometry/safe-close/margin，不靠公式/舊座標。duplicate、exact空destination、owner、持久intent/readback、menu/freshness/at-most-once全部PASS才dispatch。atomic ellipsis→wait→SaveAll之間無capture/persist/keyboard/appswitch。

chooser逐phase驗證完整絕對路徑及window/owner/control continuity；confirm只一次。filesystem delta獨立證明download started，之後停止LINE GUI。poll5秒、3次相同完整inventory/bytes、max600秒；hidden/alltypes、MIME、完整ImageIO decode、hash與穩定性全部驗證。canonical finalize同revision提交VERIFIED/registry/owner及context release，讀回；Filesystem PASS/state COMMITTED分列。

第一本finish/release後實際downward0.25-view-height scroll，即使第二張已可見也不可省略。保存before/invocation/after；同group/surface/session/process/window/display/layout、位移、完整唯一有序overlap及新完整候選。NO/UNKNOWN或缺overlap停止，不連續猜scroll。第二本不同fingerprint，重新完整catalog/menu/交易。無下一本NO_ELIGIBLE_TARGET；未scroll SCROLL_TEST_NOT_RUN。

## 5. 並行與有界修正

contract helpers/writers ceilings各4；host總slots4，根之外最多3同時子代理。W1：本epoch evidence tools/runner/E01/E02；W2：五個Swift產品/測試檔；W3：三個Python產品檔及本epoch Python v2 fixtures。根負責adapter/host modules、政策、serial merge、LINE與canonical transactions。writer scopes literal、互斥；不以R整目錄分派W1。

每位writer須實際controller allocation/external Git worktree/actor/session/frozen HEAD/receipts，不共享主工作樹。main scope有dirty/untracked時不得allocation；root串行處理。所有gates在merged candidate；writer缺失/失敗/越界/不可驗merge即停止。pair scans期间暫停main merge/controller publication。

目前immutable4.8 launcher Python symlink指向不存在Python3.14。Implementer只作一次有界readiness檢查，若仍不可用，root串行、最多3只讀協助，不能虛構writer allocation、自製替代controller、修global.codex或更換release。能力限制不是欠缺授權，也不延後已授權安全產品測試；native REQUIRED_VERIFICATION/closure保持未滿足。

歷史LIVE_CLASSIFIER_CHOOSER3次＋已授權1 collection保留；D01前持久attempt-start，累計4記append-only ledger。不能變成新的3次collection。工具readiness audit及歷史preservationFAIL保留；root issue最多3次evidence-bearing attempts扣除已知已用，未知不當0；連續2次无新資訊停止。

範圍內修正新epoch/claim，保留FAIL；source改動使相應freeze/build/grant/probe/tests失效，不能搬舊PASS。同正式ID不可重用，epoch不重置SaveAll/confirm/quota/barrier。每次修正先回報實際錯誤、新資訊、影響gates及剩餘預算；架構/安全/state/gate meaning變更回Planner，不由Implementer繞過。writer-owned合併結果若再變更，先使舊receipt失效並按controller可驗證流程處理，不能保留舊merge PASS。

format3 convergence.meaningful_attempts定義為該result局部有界attempt count；analysis明示scope，累計collection4在独立ledger，不填schema-invalid4、不截3。controller不支持extension時nativevalidation/closure BLOCKED，不冒稱PASS。

## 6. 測試、gates與交付

E01：真實pair/延遲streams/scan無寫、partial/race/timeout、special未open、wrongphase/producer、未registration、tail ordering/readback、碰撞/symlink/source drift/cwd。E02：ROOT/task/HEAD/branch/index/source/argv拒絕、claim競爭、launch前後crash、timeout/cap、reap、ID不可重用。B01/B02：anchor/bootstrap/directorydelta及合法/非法transactions和原照片保全。

S01 frozen build、R01同production nonempty ALBUMS probe且state/ledger不變；N01/N02/P01-P04/S02全部既有suite＋新v2fixture，no cases不能PASS。ledger fixed temp collision/替換identity不刪/write/fsync/replace/readback failure/owner/revision/quota；live transaction和scroll各自身證據。精確argv/runtime/timeout/caps見附錄技術規格，launch前在本epoch specs凍結。

required gates：G_BASELINE_07、G_EVIDENCE_POLICY、G_AUTH_RUNTIME、G_REAL_LINK、G_OFFLINE、G_CATALOG_1、G_MENU_1、G_FIRST、G_SCROLL、G_CATALOG_2、G_MENU_2、G_SECOND、G_PRESERVE_07、G_REPORT、G_ACCEPTANCE。criticality/evidence role/closure/owner以附錄machine contract為準。PlanReview豁免不是PASS；Acceptance須未參與貢獻的reviewer。

每次實測更新E2E測試報告.md：版本、實際順序/工具/argv/env/關鍵片段、資料/環境、expected/actual、原始錯誤、前後diff、副作用、attempt learning、未知/停止原因，關鍵證據含相對/絕對path、bytes/SHA/producer/invocation。成功/stop都收B02及tailreadback。

尾檔預宣告順序：報告→progress→attempt ledger→format3result→manifest→publication tail receipt。manifest明列排除self及其後的預宣告tail，不虛構selfhash；每項由publisher實際讀回回傳ref，不要求循環hash。六個status分開；native/Acceptance/必要livegate未滿足不得DONE。報告交根Planner；無通道則NOT_SUBMITTED，不冒稱提交。

本輪兩份MD附錄machine contract字節完全相同；Implementer擷取原UTF-8 block（末尾一LF）exclusive materialize plan-contract.json及handoff.json，不重新序列化。03_handoff_prompt是optional reviewer規範，不是正文template，本交接遵循exact contract copy。native CONTRACT/RESULT只用controller發出的固定命令，不自製validator。

## 7. 官方技術依據

- [Python os/dir_fd/fsync](https://docs.python.org/3.13/library/os.html)：平台能力需實測。
- [Apple open(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/open.2.html)：O_EXCL及O_NOFOLLOW；後者不保護全部中間元件。
- [Apple fsync(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html)：fsync/readback不宣稱絕對硬體/斷電保證。
- [Git worktree](https://git-scm.com/docs/git-worktree)：獨立HEAD/index、共享repository metadata；不是OS sandbox。

附錄的原技術規格為相同可讀來源的逐段移植。本輪1-6節與machine contract優先；尤其R/epoch binding、修正重測及delegation取代原一次失敗即交回和writers=0政策。


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
