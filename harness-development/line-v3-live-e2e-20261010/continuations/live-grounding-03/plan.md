# LINE v3 live-grounding-03：修復感測與辨識，完成兩本實機 E2E

Task：`TASK-20261010-line-v3-live-e2e`；continuation：`live-grounding-03`；role：PLANNER。
Project root：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
Branch：`v43-ab/codex-rev28`；source checkpoint：`a26a8e99141d9d4141c08e85f22491d35847f81c`。
文件目錄 `$CON`：`harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03`；原 task `$TP`：`harness-development/line-v3-live-e2e-20261010`。

## 1. 目標、授權與文件順序

本輪完成「第一本 VERIFIED → owner/batch 釋放 → 回到／fresh 確認相簿列表 → 實際向下 bounded scroll → 不同 eligible 第二本 VERIFIED → 獨立 Acceptance」。兩本是本次驗收範圍；不宣稱整個群組全部相簿已備份。

使用者已選 A：新增 non-menu native SCK producer、真機 geometry、grounded classifier、chooser locators，保留原 gates、證據要求、唯一 writer 與狀態語意。其後明示本輪驗收終點為完整兩本 E2E，要求 best practices／相關 skills、GPT-6 luna 技術研究與 subagents 同步分析。本輪最多三名唯讀 helpers、depth 1；root 是唯一 Plan／contract 作者及產品修改者，`max_parallel_writers=0`。helpers 不是獨立 Plan Review，也不能代替 Acceptance。

使用者原話：「本次計劃不需要獨立審查」。本轮 Plan Review 記 USER WAIVED／NOT_RUN，waiver 綁本契約，不是 reviewer PASS。事後獨立 Acceptance 必須保留。immutable v4.8 CRITICAL schema 的 `plan_review_required=true` 不改，免除由獨立 waiver 記錄。

使用者要求先出 Plan、許可後落 Plan、落檔後才 Handoff，並已明確指示「實際落檔、handoff，你要給我兩個檔案交給implementer」。文件流程：本 Plan／contract 落檔及 hash freeze → deterministic Handoff → Implement。`03_handoff_prompt.md` 是可選 Handoff Reviewer；本輪 `handoff_review_required=false`，不啟動該模型角色。`handoff.json` 必須逐 byte 等於已凍結 contract；`handoff.md` 首段為根據落檔 Plan 編寫的精準 Implementer Prompt。

本輪文件完成後，使用者另明確授權 GPT-6 luna 梳理上下文、撰寫包含意圖／实际变更／下一步的提交訊息，再 add、commit、push。這項 Git 授權只適用本輪新文件目錄；不擴及 Implementer 產品提交、其他 dirty／untracked 工作或遠端驗收。

## 2. 已觀察基線與輸入

- 28 個提交包輸入重新讀取，大小與 SHA-256 全部一致；見 `input-manifest.json`，每筆含 repo-relative／absolute path、bytes、hash。
- 原 freeze 的 21 個產品來源與磁碟相符；source digest `7e7f124a563e42dfdc308718774eb9aacabb9d3adbad897eee7e8150d463b077`。包含 `image_decode.swift`，未包含 rev28 producer、task runner、真實 classifier／locators。
- State schema 3、revision 35；sha256 `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`；既有 VERIFIED 2 本、runs 2 筆，active_batch／active_writer_id／context_lock 為 null。
- Config 384 bytes、sha256 `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`；group `旻謙允禎成長日記`；app `jp.naver.line.mac`；每 lifecycle cap 1。
- 歷史 SCK producer 8,821,120 bytes、sha256 `8f6cd81a0cde38d5d182563096131ab98e47cab2d0fd7cca99f471fb871740b0`；decoder hash `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf`。
- 舊 G_AUTH／G_OFFLINE／G_MIGRATION／G_PRESERVE 的 PASS 保留為歷史事實，不能認證新候選。舊六狀態為 NOT_ACHIEVED／BLOCKED／BLOCKED／INCOMPLETE／BLOCKED／REPLAN_REQUIRED。
- CUA inventory 與 module import 已觀察可用，包含 filesystem／child_process／crypto／adapter／runner；沒有執行 child process preflight、LINE capture 或 GUI，也未證明真機分類、geometry、chooser 或五秒 latency 已通過。
- 最新 Git baseline：20 個 tracked dirty 檔案、657 個 collapsed untracked entries、staged 空。`baseline.json` 保存 HEAD／index／dirty hashes；`baseline-untracked.txt.gz` 保存原 64,885 個 expanded untracked paths。保全基線不應整份貼入模型 prompt。

實作開始重新核對 source checkpoint 仍為祖先、HEAD/index、上述輸入及工作區差異。本次文件 commit 可以是 checkpoint 的後繼，前提新增 commit 只包含本文件目錄；不能 checkout／reset 至 checkpoint 而丟掉未提交產品來源。其他來源／state／config 漂移先停止並報告。

## 3. Native frame support、幾何與時間

新增唯讀 `rev28ctl frame-support`。輸入綁 project root、execution grant、retained CUA frame reference/hash、原始 capture time、session、預期 surface 與唯一可證成的 native window/display context；輸出既有 version-1 SCK sidecar、原始 full-display image、CUA/SCK OCR、native geometry、capture timing interval 與 manifest。預期 surface 是待核對條件，不能當觀察結果。

- non-menu 的 ALBUMS／ALBUM_DETAIL／FOLDER_CHOOSER 均要實際 SCK sidecar；選單另沿用 `album-support`／`album-support-guard`。
- 復用現有 full-display capture witness：includeMenuBar、sourceRect absent、contentRect/display bounds、pointPixelScale/backingScale、image dimensions；不發明 CUA bounds，也不靠單一預設 scale 換算。
- Fresh native bundle/PID/window/display 必須唯一且與 CUA 視覺對應。若 panel 改變 window，須保存原 detail → dispatch → chooser 的身份連續性與新 context；不可宣稱被遮住的 group header 已重新看見。
- 至少三個唯一、分散、非共線 OCR anchors；distribution ≥0.02 frame area、maximum residual ≤2 source pixels；uncertainty ≥2、safe margin ≥uncertainty+4、interactive intersection ≥16×16。native provider 與 Python validator 都要拒絕不一致。
- non-menu safe intersection 來自當下可證成 surface/client 幾何，不偽裝成 Save All row；不能以它取代 card 或 menu 專屬 click gate。
- CUA 時間在 capture 前取得；SCK 保存 capture request 的 monotonic/UTC 起訖與現有 capture record。選保守 capture time，OCR／保存完成後不得刷新時間。每格／pair 與 intent permit 的既有五秒限制不放寬。
- 在 intent 前以可逆校準 open/capture/guard/close 實測 latency，涵蓋既有 800–1500 ms menu wait、producer、兩次 OCR、guard 與檔案 precheck。沒有 Apple latency SLA；超時停止，不能等原始 intent 才試、改 timestamp 或重派 token。
- 每個 authority artifact 維持現有 16 MiB read cap；超過時拒絕，不自行放寬。

Native 程式不產生 GUI。GUI 僅由 documented CUA App API 執行。

## 4. Grounded classifier 與 chooser/download 介面

在 `$CON` 新增 `live_classifier.mjs`、`chooser_locators.mjs`、新的 `live_runner.mjs`；原 `$TP/live_runner.mjs` 保持歷史原件。所有模組透過明列依賴注入，由同一持續 CUA kernel 的 genuine App object 操作，fake I/O 僅限離線測試。

Classifier 結合 full AX、Vision OCR 與影像容器邊界：

- ALBUMS／ALBUM_DETAIL 輸出既有嚴格 17-key frame；不得附加 `download_started`。所有 frame/context/SCK/artifact 校驗必須成功。
- 日期／張數／title／fingerprint、完整 card、metadata、安全 metadata 子區、thumbnail 邊界、鄰卡分隔必須來自同一 fresh capture。匿名 AX row、OCR 日期框、歷史 row index、固定點位都不能證成卡片 geometry。
- 完整唯一候選才可開啟；post-open fingerprint 必須 MATCH。identity/count 競爭、partial card、bounds 不可證成或 cross-pair 皆拒絕。
- `layout_key` 綁 LINE version、language、window class、frame dimensions、native scale、布局結構，不包含當下卡片文字或 scroll offset。未知布局拒絕。
- `boundary.top/bottom` 必須有當下 scrollbar/thumb endpoint 或有證據的端點確認；不由第幾次 scan／數量／預期順序推定。LOW ghost focus 須有支持證據，不能因 AX 不方便而降低真實 HIGH focus。

新增 dedicated chooser typed envelope：`version`、17-key identity/frame record、AX reference、SCK reference、chooser phase／control bindings；download evidence 為獨立 reference。generic `frame()` 的 unsafe-focus refusal 保留；dedicated validator 復用 artifact、native binding、freshness 與 SCK 檢查，僅在同一 original dispatch 的可證成 chooser phase，允許明確識別的 Go to Folder PathTextField 真實 HIGH_EDITABLE。其他 HIGH focus 拒絕。

Chooser phase 固定為 APPEARED → GO_TO_FOLDER → PATH_FILLED → DESTINATION_SELECTED → CONFIRM_ATTEMPTED。每個 phase 新 capture、新 index/bounds；確認 path field role、frame ID、當下 focus、實際 full path／leaf、enabled confirm button。原始 permission 只准一次 confirmation；不因 throw／timeout 重試。

新增 `observeChooser`／`classifyChooser` 與独立 download observation，不向 strict frame 偷加字段。`cua-dispatch-receipt-2` 綁 retained chooser phase proofs、confirmation frame 與 download evidence；Service 要驗證實際 bytes/hash/action/session/owner/destination/事件順序。原 receipt-1／grants／歷史 state 原件保持可讀的歷史證據，新 live 使用 v2。

Download evidence 的明確規則：confirmation 後 fresh 實際下載 UI，或在同一 leased destination/inode、先前 empty inventory 之後出現新的可辨識 regular image。保存觀察方式與時間；僅 chooser 消失、常數 boolean 或未知檔案不算。confirmation 後不再輸入 LINE；若 UI 不足，最多 30 秒、每秒一次唯讀 filesystem sampling 尋找開始證據，仍不明確則保留 intent barrier，報 UNKNOWN 並停。後续完整檔案驗收獨立判定。

## 5. Grant v2、來源閉包與 GUI 記帳

`line-batch-execution-grant-2` 保留現有欄位及 quotas，新增：

| 欄位 | 凍結語意 |
|---|---|
| contract_path | 本輪 contract 相對路徑；bytes/hash 必須符合 contract_sha256。 |
| producer_binary | `{path,bytes,sha256}`；實際執行 rev28ctl，與 decoder 分別綁定。 |
| runtime_binding | `{path,bytes,sha256}`；嚴格 runtime manifest reference。 |
| sensor_scope | 固定 bundle/provider；ALBUMS、ALBUM_DETAIL、FOLDER_CHOOSER full-display 與 menu capture/guard。 |

`native_binary_sha256` 仍指 image_decode，不改指 producer。新的 live write 只接受本輪 v2 authority；v1 fixture／歷史證據不因此取得 live authority。authorization 對應本輪真實 user decision／waiver，不逐字搬用舊決策字串。

Runtime manifest 覆蓋既有 21 個 sources、adapter、新 runner/classifier/locators、實際 Python executable、producer executable，以及 `rev28/Package.swift`、`rev28/Sources/Rev28Core` 與 `rev28/Sources/rev28ctl` 中全部 Swift 的字面展開清單。排除 build/cache，membership+bytes/hash 均凍結。啟動 process 前核對 executable；模組載入時核對實際 bytes。任何來源修改必須使 grant 失效，回到離線驗證及重新 freeze，不沿用舊 PASS。

GUI ledger 共用 `$TP/gui-ledger.json`，新增 `menu_calibration` 與 `return_navigation`。每個實際 input 先 reserve，再派送；校準開／關各一次、返回 click/key 各一次，scroll 每次一次。Unknown/crash 不退款，也不把導航假稱 album_open/scroll。仍以 shared ledger 累計兩本、兩次 Save All、兩次 chooser confirmation、1000 次額外可逆 GUI；config cap 固定 1。fresh grant 不清零，若發現未预期 ledger／existing ownership 先停止。

唯一 Store writer、existing lock、CAS、nested transition guards、schema 3 與歷史 immutable/append-only 規則不改；config 不可修改。

## 6. Runner 與 session lifecycle

明列 `adapterModule` 必需依賴；`prepareCandidates`／`finalRecords` 都是 async 並 await；`captureCatalog`／`captureFresh`／candidate reacquisition 驅動 runner own session。

- 第一次完整 catalog admission 後，按 manifest 順序 skip VERIFIED。回到候選並重新 capture，直到該 session latest frame、prepare frame、same-observation card binding 一致；不把 scan 途中 frame 當 fresh。
- 開相簿 → post-open MATCH → menu calibration → close without command → fresh detail → intent。
- Intent readback 後消耗一次 permit；ellipsis → bounded SCK popup capture/guard → 唯一 Save All。guard 只能驗證已校準點，不在 intent 後改點／重校準。pair CUA frame 與 popup SCK frame 分開保存 identity/time/hash。
- Chooser confirmation 後，原 dispatch session 永久 stopped。不得 clear stopped／複製 permit／重開已消耗 action。
- Download、完整 content verify、VERIFIED commit/readback 完成後，建立 navigation-only observer，保留 existing grant owner、重新 capture，不具 Save All／chooser／intent 能力。返回 Albums、fresh full catalog drift check，await finalRecords，既有 Service.finish 仍要求 identities 與 admission 相同；完成 CAP_REACHED／finish／release。
- 第一 batch 完整釋放後建立第二 owner/lifecycle。用 fresh Albums before/action/after 執行至少一次實際向下 ≤0.25-view-height scroll。必須同 group/surface/session/PID/window/layout、有序完整唯一 overlap、新而完整候選及可證成 scroll effect。第二本已可見仍不能省略這一步。
- 第二 lifecycle 仍須完整 catalog admission/drift check，按 canonical 順序選不同 eligible fingerprint，重新 fresh binding 與全部 gates；scroll gate 不能代替 complete-catalog admission。

## 7. Gate、owners、輸出與 evidence 分類

完整 GateSpecs 以本檔附錄及 `plan-contract.json` 为准，原 13 個 gates 的 requiredness／owner／phase／criticality／role／closure／reuse 全部保留。new support evidence 納入原 gate 的必要子檢查，不減少任何既有要求。

| Gate | 實際驗收及 `$CON` 預定證據 |
|---|---|
| G_PLAN_REVIEW_WAIVER | HUMAN/PLAN；本輪 user waiver 綁 contract，underlying review WAIVED/NOT_RUN；不用模型審查或工具 PASS 假稱審查通過。`plan-review-waiver.json`。 |
| G_AUTH | IMPLEMENTER/IMPLEMENT；baseline、source/runtime/bin freeze、雙 owner v2 grants、operation/sensor binding/quota 校驗。`evidence/g-auth.json`＋`runtime-binding.json`＋grants/authorization。 |
| G_OFFLINE | IMPLEMENTER/IMPLEMENT；必要 Python、Node、Swift suites 明確 PASS；producer/classifier/chooser/latency/lifecycle regression。`evidence/g-offline.json`及原始 stdout/stderr/invocation/receipt。 |
| G_MIGRATION | IMPLEMENTER/IMPLEMENT；保留原 migration receipt/hash，fresh schema3/history continuity 檢查，旧 prefix／大整數完整；不重新 migrate。`evidence/state-continuity.json`。 |
| G_CATALOG | IMPLEMENTER/IMPLEMENT；真機 full catalog top/bottom、完整有序 overlap、dates/counts、native/SCK/classifier 真實 grounding。`evidence/catalog-1`／`catalog-2`。 |
| G_MENU | IMPLEMENTER/IMPLEMENT；兩本各自實際 menu row、safe point/geometry、popup pair、nonactivation closure、pre-intent latency。`evidence/menu-1`／`menu-2`／`latency`。 |
| G_FIRST | IMPLEMENTER/IMPLEMENT；第一本完整 duplicate/destination/owner/intent/dispatch/chooser/download/content/VERIFIED/readback/finish/release。`evidence/album-1`＋transaction receipts。 |
| G_SCROLL | IMPLEMENTER/IMPLEMENT；first release 後真实 downward before/action/after，effect／完整 overlap／新 candidate 独立驗證。`evidence/scroll-2`。 |
| G_SECOND | IMPLEMENTER/IMPLEMENT；不同 eligible fingerprint，全部 gates 與交易重跑。`evidence/album-2`。 |
| G_PRESERVE | IMPLEMENTER/IMPLEMENT；BASELINE_DELTA，原 dirty/untracked、config、歷史state、舊備份完整；只批准新增交易/文件差異。`evidence/preservation.json`。 |
| G_REPORT | IMPLEMENTER/IMPLEMENT；本輪 E2E測試報告、progress、attempt ledger、相對/絕對 evidence manifest、unknowns／副作用／前後差異與每次新資訊。 |
| G_ACCEPTANCE | 不參與實作的 ACCEPTANCE_REVIEWER/ACCEPTANCE；分項 menu、first、scroll、second、batch/state、preservation 與 source binding。`acceptance.result.json`。 |
| G_DELIVERY | IMPLEMENTER/IMPLEMENT；成果及正式 evidence、六狀態、required verification/Acceptance 清楚交付。不是本次文檔 commit 就算產品 gate PASS。 |

Local tool tests、真機 tool evidence、唯讀 observation、GUI action、真實 download 分開。Human-only visual observation 為 OBSERVED，不是工具 PASS；helper 建議也不代表 gate PASS。角色不得 pass future phase 或別人的 gate。

## 8. 必要本地檢查與嘗試額度

在完整修改／fixture binding 檢查後執行：

1. `/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3 -B -m unittest discover -s tests -p 'test_batch_*.py' -v`；同 interpreter 分別執行 `test_project_binding.py`、`test_transaction_core.py` discovery。cwd=root、PYTHONPATH=src，新 stdout/stderr/receipts 全落 `$CON/evidence`。
2. `/opt/homebrew/bin/node --check scripts/line_backup_cua_adapter.mjs`；對本輪新 mjs 檔各做 --check；`/opt/homebrew/bin/node --test tests/test_cua_adapter.mjs` 與 `$CON/checks` 的 classifier／runner suites。
3. `/usr/bin/swift test --package-path rev28 --sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk --scratch-path <absolute CON>/swift-build-26.5`；cache/temp/env 綁本輪。

不修改已完成 migration、內容與 transaction core 的來源／測試來迎合新實作；既有 suite 只執行。允許修改的測試檔由契約精確列出。

測試覆盖 stale/timing refresh、anchor/native/window/layout drift、sidecar provider、partial/ambiguous/cross-paired cards、focus/chooser/path/leaf、篡改/replay/foreign owner、source/binary/runtime drift、shared quota、每個 GUI input 記帳、expired consumed permit、download evidence、async final catalog、stopped session、release/第二本順序及歷史保全。Fake suites 的 PASS 僅為離線，不能充當真機。

新 root issues 固定：`NON_MENU_SCK_SUPPORT`、`LIVE_CLASSIFIER_CHOOSER`、`LIVE_RUNTIME_BINDING_ORCHESTRATION`；同一缺陷跨模組/child failure仍同 ledger，不以改名重置。每個最多三次 meaningful attempts，兩次無新資訊或 material blocker 立即停止／升級。Swift package build／filtered test／full test 啟動都先 durable reserve 到 NON_MENU_SCK_SUPPORT ledger；compile/test failure、timeout、crash、missing receipt 均消耗。完成全部必要修改後一次 full suite優先，不用預跑偷增額度。

舊 Swift 四次收據與既有單次例外 325/0 PASS 保留。若重現原舊 issue，回原 issue停止條件，不借新 budget 清零。Inherited 28+1 舊 ledger 只讀引用，新 ledger 實際數從新 issue的可觀察嘗試開始；更早 unknown 維持 UNKNOWN。

## 9. 實機前置與完整 content acceptance

先驗證真正 runtime process bridge、raw screenshot bytes、持續 kernel、同一 frame/action 綁定及新版所有影格 validator。Native capture／classifier catalog/detail grounding 與 pre-intent menu latency 必須先成立；chooser在唯一原始 dispatch 後驗證，不另發一個 Save All 做「試驗」。

每個需要 LINE 前景的有界操作，先公告 app／surface／下一個精確動作並取得明確交接。過期交接、被取回的前景或 identity/context 不明即停止輸入；重新交接後重新 capture/bind。Atomic ellipsis→guard→Save All 事先作為同一有界動作公告，途中不插入鍵盤／app switch／重新點位。

Content acceptance：每五秒唯讀 inventory，三次相同 names／sizes／mtime/inode／bytes，最多600秒。包含隱藏檔，禁止 follow symlink；expected recognized image count相等、zero-byte/partial/temp/unknown regular files為0、無未預期目錄/entry；逐張 ImageIO完整decode；decode及commit/readback前後 inventory/identity不變。filesystem PASS、state commit、readback fence分開。下載後任何不確定不得重送。

無第二 eligible：NO_ELIGIBLE_TARGET；未實際 downward scroll：SCROLL_TEST_NOT_RUN；兩者維持 PARTIAL，不關閉完整兩本 E2E。第二本不得重開剛 VERIFIED 的第一本。

## 10. 停止、證據回報與六狀態

前景被取回、identity/mapping/focus/scroll UNKNOWN、native/anchor/latency不合格、grant/quota/source drift、目的地意外內容、writer guard、state/readback drift、dispatch/confirmation不確定，停止所有依賴動作，保存現場。不得刪資料、換 writer、改 schema/config、降低門檻或釋放未解 intent barrier。

每輪實際測試更新 `$CON/E2E測試報告.md`、`progress.md`、新 `attempt-ledger.json`，保存原始成功/失敗/未執行與順序、argv/env/tools/code refs、before/after、副作用、每次新資訊、bytes/hash與relative/absolute paths。報告正式交下一輪 Planner；無真實 Planner 通道時寫「尚未完成交接」。

PRIMARY_OUTCOME、IMPLEMENTATION、CORE_ACCEPTANCE、REQUIRED_VERIFICATION、INDEPENDENT_ACCEPTANCE、TASK_CLOSURE 六項獨立。只有適用 gates與required Acceptance滿足並保留 waiver事實才可task DONE；核心部分成功不被其他 blocker抹除。本次只有文件，產品／live尚未完成。

## 11. Harness、能力與資料限制

使用 immutable v4.8 release：`/Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source` 與其 runtime/schema，不能拿 moving current v4.9 恢復旧任务。

已讀原 controller：CRITICAL Plan依 `plan_review_required` 路由 PLAN_REVIEW，而 waive_gate僅允許 implementation finished＋Acceptance滿足後；不能在本輪實作前套用此 waiver。故按明確 user authority採本地 deterministic Handoff；native admission、stage publication、emitted CONTRACT/RESULT validation均 NOT_RUN。不修改 Harness，也不捏造 run/invitation/platform receipt。若未來取得 genuine stage packet，只能使用它 emitted的固定命令，不能把本地 schema check稱作native驗證。

本地文件可使用 immutable release既有 `harness.schema_validation.validate_document` API做結構檢查；結果只證明 local schema，不代表 task admission、產品或E2E。`document-run.json`的UUID是本次實際建立的LOCAL_DOCUMENT_AUTHORING標識，絕非controller allocated run。

Contract capability只是聲明政策；OS sandbox／network denial為UNKNOWN。LINE 自身下載由原生app完成；不要在子代理／外部research中傳送相簿內容或私密config/state。所需公開技術資料用官方來源；不安裝新依賴、不做非目標外部動作。

## 12. 技術研究來源與保留 unknowns

已使用 line-album-backup 的 transaction/duplicate/target binding 規則與 context7-mcp 的官方資料查核方法。GPT-6 luna deep research與另一名唯讀介面分析helper供應事實，root定稿；非獨立review。Context7可用性未證成，Apple primary docs為補充來源。

- SCK bounds/scale/filter：https://developer.apple.com/documentation/screencapturekit/sccontentfilter
- Native capture：https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos
- Stream timing/geometry metadata：https://developer.apple.com/documentation/screencapturekit/scstreamframeinfo
- Vision normalized text boxes／候選：https://developer.apple.com/documentation/vision/recognizing-text-in-images
- AppKit panel API：https://developer.apple.com/documentation/appkit/nsopenpanel

官方能力支持方案，但不證明本機CUA capture bounds、現在LINE AX/geometry、private chooser ID、OCR latency或process bridge已通過。Vision boxes需lower-left normalized→top-left pixels換算；confidence/candidates不證成整張card。自建NSOpenPanel不驗證LINE chooser。全部unknown由上述fresh gates決定，失敗即有界停止。

## 附錄 A：凍結 format 3 machine contract

以下JSON原文與plan-contract.json相同。allowed_paths、required_evidence、GateSpecs及workflow limits不得由Handoff或Implementer自行改寫。

```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "Repair non-menu SCK support, grounded visual/AX classification, chooser evidence, grant runtime binding and session orchestration; preserve the canonical schema-3 writer and history; complete two different cap-one album lifecycles with actual post-first downward scroll, full content verification, reporting and independent Acceptance.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "src/line_backup_batch/cli.py",
    "src/line_backup_batch/store.py",
    "src/line_backup_batch/observations.py",
    "src/line_backup_batch/service.py",
    "scripts/line_backup_cua_adapter.mjs",
    "rev28/Sources/Rev28Core/Perception/OcrEngine.swift",
    "rev28/Sources/Rev28Core/Sensor/FrameCapture.swift",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Tests/Rev28CoreTests/OcrEngineTests.swift",
    "rev28/Tests/Rev28CoreTests/FrameSupportTests.swift",
    "tests/test_batch_authority.py",
    "tests/test_batch_observations.py",
    "tests/test_batch_coordinator.py",
    "tests/test_batch_lifecycle.py",
    "tests/test_cua_adapter.mjs",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-v3.tmp",
    "backups/旻謙允禎成長日記",
    "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03"
  ],
  "required_evidence": [
    "E_BASELINE",
    "E_AUTH",
    "E_OFFLINE",
    "E_MIGRATION",
    "E_LIVE_CATALOG",
    "E_MENU",
    "E_FIRST",
    "E_SCROLL",
    "E_SECOND",
    "E_PRESERVATION",
    "E_REPORT",
    "E_ACCEPTANCE",
    "E_DELIVERY",
    "E_PLAN_REVIEW_WAIVER",
    "E_FRAME_SUPPORT",
    "E_CLASSIFIER",
    "E_CHOOSER",
    "E_RUNTIME_BINDING",
    "E_LATENCY",
    "E_SESSION_LIFECYCLE"
  ],
  "gate_specs": [
    {
      "gate_id": "G_PLAN_REVIEW_WAIVER",
      "required": true,
      "owner": "HUMAN",
      "phase": "PLAN",
      "evidence_source": "HUMAN_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "DIAGNOSTIC",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_AUTH",
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
      "gate_id": "G_MIGRATION",
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
      "gate_id": "G_CATALOG",
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
      "gate_id": "G_MENU",
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
      "gate_id": "G_PRESERVE",
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
      "goal_criticality": "CORE",
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
    },
    {
      "gate_id": "G_DELIVERY",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    }
  ],
  "capability_policy": {
    "network": "PROXY_ALLOWLIST",
    "browser": false,
    "destinations": [
      "https://github.com/s9008129/Line_backup.git"
    ]
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
    "max_parallel_read_only_helpers": 3,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
