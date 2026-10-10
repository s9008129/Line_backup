# live-grounding-04：修復正式證據鏈，完成兩本 LINE 相簿 E2E

Task：TASK-20261010-line-v3-live-e2e；角色：PLANNER。Project root 固定為 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup。所有相對路徑均從該 root 解析。

本目錄（CON）：harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04。
原 task（TP）：harness-development/line-v3-live-e2e-20261010。

## 1. 結果、授權與基線

本輪驗收終點為：第一本 VERIFIED／readback → 回到相簿列表／fresh catalog → finish／owner release → 至少一次實際 bounded downward scroll → 不同 eligible 第二本完整交易 → 狀態／內容驗收 → 獨立 Acceptance。兩本是本輪範圍，不能因此宣稱整個群組全部完成。

使用者已明確選擇「橋接修復＋兩本 E2E」、「加入 v2 證據」、「允許調整版面」，豁免本輪獨立 Plan Review，並授權文件落檔與 add、commit、push。當前文件交付階段只寫本目錄文件；不執行本計畫的產品修改、LINE input、下載或 state mutation。後續使用者將本 Handoff 交給 Implementer 要求 IMPLEMENT 時，凍結路徑與檢查承接原授權，不在每個角色重複詢問。

風險為 CRITICAL：v2 evidence 會參與真實照片下載、GUI targeting 與持久 intent 決策。immutable v4.8 contract 保留 plan_review_required=true；實際 Review 由獨立 waiver 記 USER_WAIVED_NOT_RUN，不是 reviewer PASS。independent_acceptance_required=true，handoff_review_required=false。root 串行，max_parallel_writers=0；最多一名 depth-one 唯讀 research helper。已完成的 GPT-6 luna helper 只研究官方資料，沒有修改或審查本契約。

本次 baseline.json 為正式基線：HEAD 0838a45dab1860801b6f8d51309def9f1c5195aa、branch v43-ab/codex-rev28、staged 空；11 個既有 tracked dirty 檔案及大量 untracked 工作。不得 reset、checkout、清理或整批 stage 它們。文件提交後的 HEAD 可為基線後繼，須確認新增提交只有本文件包。

State schema 3、revision 35、SHA-256 455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6；2 runs、2 verified albums，active_batch／active_writer_id／context_lock 均 null。Config group 為旻謙允禎成長日記、app 為 jp.naver.line.mac、backup root 為本專案 backups，每 lifecycle cap 1。config 原檔不在可編輯範圍。不得重新 migrate 或換 writer。

## 2. 第一性原理與根因

核心問題是如何證明「當下看到的相簿、可操作區域及被派送的動作是同一個對象」，並將原始觀察保留成可重驗的證據。必要條件依序為：真實 bytes → 原樣留存／readback → capture 時間與 session → 原生窗口／display 身份 → 跨來源映射 → 卡片／metadata／thumbnail 分隔 → 新鮮的動作綁定。單一工具顯示成功不能代替這條鏈。

已證實的問題及原始研究來源詳見 research.md、research-facts.json 與 input-manifest.json：

1. CUA 的 getAXStateAndScreenshot 回傳 screenshot bytes；Node 可直接寫檔，runner 已有 createRetain。因此 host 先提供檔案參照不是必要條件，真正缺口是 production 綁定。
2. 實際 screenshot 是跨 realm Buffer。instanceof Uint8Array=false，而 ArrayBuffer.isView=true、tag 為 Uint8Array。複製至當前 realm 後，183645 bytes、SHA-256 2e93f01caf5ade784f7e409f91a376fe99badcd828dc9aa266439692d3b297d6 均不變。這是記憶體觀察，沒有 workspace 原图，不是 G_CATALOG PASS。
3. analyzer、native geometry、catalog／navigation callbacks 尚未 production wired。現有 tests 可通過空的 ALBUM_DETAIL cards，未證明真實卡片解析。
4. live-grounding-03/live_classifier.mjs 的 ALBUMS boundary keys 排序後，與未排序 literal 比較，合法資料必然拒絕。live_runner.mjs 的 frameSupport hook 漏傳 intersectionPx，chooser 之後卻使用該欄位。
5. chooser APPEARED 過早強制要求 PathTextField；DESTINATION_SELECTED 又要求已可能關閉的 Go to Folder field。階段資料必須反映實際當下控制。
6. card／image AX 強制來源與目前匿名 AX rows 不符；原始 OCR 日期分隔符與 canonical title 的直接 equality 也須明確處理。
7. 舊 frozen Python 3.14 真實路徑及 v4.8 venv launcher 已失效；已唯讀確認 Python 3.13 可啟動，必須重新凍結 runtime closure。這不是沿用舊 G_AUTH 的理由。
8. 目前畫面僅一張完整卡片，不能直接保證每次 scroll 的完整 overlap＋新完整卡片。需先調整及量測可行版面；僅顯示兩張卡片也不是 scroll PASS。

兩個 installed 程式的結論：GUI-session bridge 有 request／claim／nonce／timeout 設計參考價值；probe 有唯讀 AX、WindowServer／menu observation 設計參考價值，也有 explicit AX navigation。兩者沒有本次必要的 CUA screenshot/SCK export；probe binary 與 deployment manifest 的 hash、size、CDHash 不符，來源對應未知。既有 readiness 是 2026-09-15 的 TCC_TRUST_DENIED，不能當今日權限。正式 production 使用 repo 自有唯讀 producer；外部 bridge/source 僅研究，不納入 authority，也不部署或卸載它們。

## 3. 實作、介面與資料流

### 3.1 CUA capture 邊界與證據留存

在 scripts/line_backup_cua_adapter.mjs 的兩條 observation 入口加入單一 byte normalizer。接受真實 Uint8Array／Buffer byte views，檢查 ArrayBuffer.isView、byte element 型別與長度，複製至當前 realm；拒絕 DataView、其他元素寬度 typed array、假物件、空值、非 bytes 及 >16 MiB。處理 byteOffset／byteLength，不能把整個 backing buffer 當影像。

同一 fresh capture 保存 screenshot、full AX text、UTC request start/end、monotonic interval、bytes／SHA-256；原樣寫入後 bounded readback 驗證。frame_id 是保存前原始 bytes 的 SHA，copy 不得改變它。capture timestamp 從 request 前取得，持久化、解析與 OCR 不得刷新它。readback 失敗立即停止，不送 input。

CON 新增真正的 Node filesystem/process hooks，使用固定 cwd、argv array、bounded stdout/stderr、timeout、exit code，禁止 shell substitution。全部 artifacts 和 child-process 暫存寫在 CON；過去留存程式複製後修改 CON 綁定，原 live-grounding-03 程式／契約保持歷史原件。

### 3.2 Repo 自有 passive native context

新增 rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift 及 rev28ctl native-context 子命令。必需參數為 --project-root、--grant、--grant-sha256、--output、--session-id、--request-id、--phase before|after。after 另外綁 retained --pair-frame、--pair-frame-id、--cua-captured-at 及 before receipt reference/hash。

只讀取 NSRunningApplication／ProcessInstanceID、SCShareableContent、CGWindowInventory、AX attributes；不建 actuator、不呼叫 AX write／PerformAction、不 activate app、不發起 permission prompt。reuse 現有窗口 selector、FrameCaptureSupport 與 VisionOcrEngine；不複製整個外部 bridge 或建立第二個常駐 daemon。

輸出版本化原始 receipt：producer/source/binary、request/session/phase、實際 UTC／monotonic observation interval、bundle/PID/process instance、SC/CG window descriptors、AX window/focus/tree、display id/bounds/scale、獨立 AX/screen permission 結果、原始 error 及 retained artifact refs。unknown 保留為 null／UNKNOWN。before → CUA capture → after → SCK support 的身份／幾何必須穩定；時間只是有序觀察，不宣稱原子同步。

窗口以 fresh CUA 視覺、實測 AX/SC/CG 關聯和 SCK anchor 配對唯一選取；不要求全桌面只有一個 LINE window，也不選第一個窗口。跨顯示器、遮蔽、同尺寸競爭或 CUA crop origin 不唯一即拒絕。保留原生 points、CUA pixels、SCK pixels 各自來源；尺寸相同不等於映射已證明。

沿用 frame-support／album-support／guard 的三個唯一、分散非共線 anchors、distribution ≥0.02 frame area、maximum residual ≤2 source px、uncertainty ≥2、safe margin ≥uncertainty+4、interactive intersection ≥16×16、完整 display/menu-bar witness、原五秒 freshness。Hook 明確傳回 producer 驗證的 intersectionPx。producer grant/path/source closure 改綁本 CON/hash，不能把 path 改成任意可讀檔。

### 3.3 v2 grounding 與 production analyzer

維持既有 17-key frame 與 state schema 3；新增 strict v2 grounding／classifier／AX raw evidence，JS 與 Python 對同一版本／判定規則一致驗證。v1 保留歷史驗證，但新 production 必須使用明確版本及當前 runtime 綁定，不能把歷史 v1 升格為 fresh PASS。

card witness 用 source_kind=AX_NATIVE|VISUAL_NATIVE。AX 路徑使用真實當下 card/image nodes。VISUAL_NATIVE 路徑保存 raw screenshot、pixel-derived card/thumbnail/metadata regions、原始 Vision OCR bounds/text、native context、SCK support／transform、邊界與鄰卡分隔證據。不得合成 image node、CUA index、enabled、identifier 或不存在的 bounds。必要 native/CUA 控制關聯必須唯一，不能按 traversal ordinal 強行配對。

視覺 detector 限於 fresh 原圖中可證成的單欄相簿 cover/container 布局：native list/container 為範圍旁證，像素邊界與同幀日期／張數定位 metadata，SCK 配對驗證同一布局。卡片／thumbnail／metadata 完整包覆與分隔必須可重算；safe metadata 區為實測 metadata 扣除 thumbnail、ellipsis／其他控制及鄰卡，再按 uncertainty erosion。位置無法證成或沒有安全餘量即拒絕，不建立固定座標 fallback。未支援布局產生 raw blocker 而不是現場發明另一條 targeting authority。

日期 parser 明確正規化既有 UI 的 tilde／全形波浪等分隔形式，原文字保留在 witness；frame title 維持既定 canonical form。日期有效性、年分範圍、count、group、fingerprint 由同一畫面證成；不合併歧義群組、不猜跨年、不靠歷史順序。partial／duplicate／count drift／cross-pair 均拒絕。

raw AX 全部保留；v2 可明確標示未定位／offscreen bounds，而非夾成畫面內。action control 必須有當下有效 bounds。layout_signature 僅含 version/language/window class/size/native scale與固定 surface 結構，排除 card text、row count、scroll offset。修正 key-set 比較為一致集合驗證。

焦點保留原始值及分級理由。無法核對的 focus 不改成 NONE；LOW_GHOST 只供已核准 class-1 navigation evidence，不放寬 intent／Save All／chooser gates。需要輸入的階段仍須 fresh 通過原安全條件；真實 caret/editable 或未知焦點阻塞即停止。

### 3.4 Chooser 與完整 orchestration

實作 live.analyzeCapture、captureCatalog、prepareCandidates、finalRecords、locateMenu、locateBack、producerGeometry、scrollTarget、preparePostReleaseScroll，明列依賴並 await。不得用 fixture callback 供 production。

captureCatalog 由實際 top/bottom及每次 ≤0.25 view-height scroll 的 fresh continuity／完整唯一有序 overlap 建立完整 catalog，保持既有 admission policy。600 秒 catalog age／五秒 action freshness 保留。候選重新擷取到 session latest frame，按 manifest 順序 skip VERIFIED；post-open fingerprint 必須 MATCH。finalRecords 重新掃描及 drift check，不能傳回舊 records 充當新 catalog。

Chooser 按階段辨識：APPEARED 只需真實 root／owner continuation；GO_TO_FOLDER 需當下唯一 focused PathTextField；PATH_FILLED 核對完整 path；DESTINATION_SELECTED 需當下顯示的完整目的地／leaf／enabled confirm 控制及安全 bounds，不要求已消失的 field；CONFIRM_ATTEMPTED 記錄一次 invocation 與後續 capture，並用獨立 download evidence 確認開始。每階段新 frame/index，原 dispatch/run/destination 綁定不變。

menu 開／觀察／guard／無命令關閉先實測 latency。intent 後沿用既有核准 dispatch sequence，不加入額外 CUA 觀察或校準。loaded intent、timeout或不確定 outcome 不授予第二次 Save All／confirmation。

第一本 content VERIFIED／state readback、返回列表／fresh final catalog、finish／release 完成後，navigation-only observer執行實際 downward scroll。before/action/after 同 group/surface/session/PID/window/display/layout；至少一個完整唯一有序 overlap、新完整候選及 moved effect。釋放 owner 後只准既有 navigation ledger，不恢復交易 mutation authority。第二 lifecycle 新 owner，重新完整 catalog與所有交易 gates，必須不同 fingerprint。

### 3.5 Runtime、前置條件及測試輸出

本輪產品 Python 使用已觀察可啟動的 /opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13，執行前核對 executable/hash。最終來源完成後重建 exact 21-product-source membership、全部 Swift sources/package manifest、全部 task modules、Python executable、producer、既有 decoder closure，並同步 JS/Python/Swift contract constants；不接受任意 manifest member。

新的 helper/analyzer 模組全部納入 task_modules allowlist。兩 owner＝live-grounding-04-g1/g2，各 lifecycle cap 1，共用 TP/gui-ledger.json；總兩本、兩次 Save All、兩次 chooser confirmation、1000 可逆 input。沿用已使用 ledger/reservations，不清零、不退款。先驗 state/history、空目的地、symlink/realpath及 grant，才能 acquire／派送。

正式 catalog 前調整窗口並 fresh 量測可行性；僅完整显示兩張卡片不是 sufficient proof。CUA 缺乏已證成安全 resize 路徑時，請使用者做一次精確窗口調整並重新交還前景；不得另用 AX write 改窗口。版面仍不滿足完整 overlap／新完整候選便記 geometry blocker，不降低 scroll gate。

test fixtures、cache、scratch、TMPDIR、logs、inputs全部在 CON。提供 CON 自有 fixture_support／必要 config/decoder seeds，明確綁定 LINE_BACKUP_BATCH_TASK=CON、LINE_BACKUP_INSPECTION_TEST_ROOT=CON/fixtures、LINE_BACKUP_INSPECTION_FIXTURES=CON/fixtures/swift-inspection、PYTHONDONTWRITEBYTECODE=1，Python 用 -B。不得直接執行舊 helper 造成 TP/evidence 或 src/__pycache__ 新副作用。舊 14 個 scope drift artifacts保留並在 baseline 比較。

## 4. 凍結 gates、必要檢查與停止條件

gate_specs 的 owner、phase、criticality、evidence_role、closure_gate、reuse以 plan-contract.json 原文為準；本表補完輸出及判定。

| Gate | Owner/phase | 必要證據與判定 | Failure route |
|---|---|---|---|
| G_PLAN_REVIEW_WAIVER | HUMAN/PLAN | user-decisions＋contract-bound waiver；Review為WAIVED_NOT_RUN | 缺明確決策→停止交接 |
| G_AUTH | ROLE/IMPLEMENT | baseline、runtime/source/binary/config／scope／grant membership／shared quota；g-auth.json | 漂移／缺失→停止實機 |
| G_OFFLINE | ROLE/IMPLEMENT | invocation/stdout/stderr/exit；Node/Python/Swift要求的case與回歸明確PASS；g-offline.json | root-issue規則修復／升級 |
| G_MIGRATION | ROLE/IMPLEMENT | schema3/history／大整數／既有prefix、原migration原件、state-continuity.json；不再migrate | writer/history漂移→REPLAN |
| G_CATALOG | ROLE/IMPLEMENT | 兩lifecycle真實top/bottom完整scan、fresh continuity、raw bytes/AX/native/SCK/v2；catalog-1/2 manifests | gap／drift／unknown→SAFE_ABORT |
| G_MENU | ROLE/IMPLEMENT | 每本SaveAll row／geometry／SCK pair/guard／無命令closure／pre-intent latency；menu-1/2、latency | unknown／超時→停止，不寫intent |
| G_FIRST | ROLE/IMPLEMENT | 單次dispatch、chooser、download、content decode／3×5秒inventory、VERIFIED state/readback及release；first manifest | 不確定保留barrier，停止batch |
| G_SCROLL | ROLE/IMPLEMENT | 第一釋放後actual scroll before/action/after；≤0.25、有序完整overlap/new完整card/effect；scroll manifest | UNKNOWN不重送；未跑SCROLL_TEST_NOT_RUN |
| G_SECOND | ROLE/IMPLEMENT | 不同eligible fingerprint的新owner完整交易／content／state readback；second manifest | NO_ELIGIBLE_TARGET或SAFE_ABORT，不製造案例 |
| G_PRESERVE | ROLE/IMPLEMENT | baseline_delta、既有dirty/untracked/state/config/backup保全；preservation.json | 範圍或資料副作用→停止並报告 |
| G_REPORT | ROLE/IMPLEMENT | E2E測試報告.md含順序、命令、環境、結果、副作用、嘗試、relative/absolute/hash、原始證據連結 | 缺證據不得主張PASS |
| G_ACCEPTANCE | ROLE/ACCEPTANCE | 獨立於contributors的完整merged evidence review及format3 result | missing/FAIL→不能DONE |
| G_DELIVERY | ROLE/IMPLEMENT | 驗證後機器結果／完整交接／所有artifact readback/hash及未決限制；delivery manifest | 部分交付保留部分事實 |

必要本地檢查：Node syntax與test_cua_adapter、CON classifier／runner／production wiring suites；Python test_batch_*、test_project_binding、test_transaction_core及新v2 witnesses／authority cases；Swift全套及PassiveContextObservation／FrameSupport cases。只在隔離fixtures驗 crash/resume／duplicates，不對真實相簿重送。既有PASS只是歷史，不能認證新candidate。

cases 必須包含：真正跨 realm Buffer與byteOffset copy/hash一致；readback失败；真實型態ALBUMS含非空完整card；key ordering；native PID reuse、同尺寸窗口歧義、多display/negative origin、scale/crop drift、遮蔽、permission失敗；v2偽造AX/visual witness、缺边界/鄰卡/原始OCR、日期分隔符/跨年/競爭count；chooser各階段field出現/消失、stale index、禁重複confirm、intersection缺失；runtime/source/membership drift；original五秒超時；post-release scroll前後context與new完整card；兩fingerprint/lifecycle共享quota。

前景需求：每個必要LINE UI操作之前公告app／surface／精確動作，取得明確有效交接；被取回即停輸入，重新交接後fresh capture。歷史交接不是本Implementer的無限前景授權。

同一root issue最多三次有證據attempt，兩次連續無資訊即升級，material blocker更早停。沿用原attempt-ledger與失敗學習；新的CON或問題名稱不重置額度。已解NON_MENU_SCK_SUPPORT的三次Swift suite史完整保留；新native-context/interface工作需先核對可用issue額度，unknown不得寫0或自行增額。

任何身份歧義、writer guard、state/config漂移、目的地非空/symlink、副作用、timeout、前景中斷、dispatch不明即停止依賴工作，保存最小重現与blocker。不得切writer、清資料、降低gate、刷新時間戳或重送token。檔案內容成功但state pending分開報告；完整decode不是download-start proof。所有gate有自身PASS與獨立Acceptance才可宣告本輪兩本完成。

## 5. Harness、文件與交付

文件順序：plan.md＋plan-contract.json落檔 → 原文hash freeze → waiver/result／required evidence → deterministic本地複製為handoff.json → handoff.md首段精準接手prompt → equality/readback/preservation → 明列文件stage／commit／normal push。

03_handoff_prompt.md是可選Handoff Reviewer，不是必需模型作者。本輪handoff_review_required=false；不啟動該review，不改contract、不添gate。handoff.json與plan-contract.json逐byte相同；handoff.md引用相同hash及完整contract。

Harness immutable4.8 controller固定為 /Users/hsiaojohnny/.codex/harness-releases/4.8.0/2743a20a3a89ab644b9b77abd849559cfc9a53a6ec9333166e7b2aaf742dbf1f/source/tools/task-orchestrator.py。其原runtime /Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3現不可執行。不得改global runtime、immutable release／schemas、另造invitation，或改用Python3.13假裝原native emitted command已PASS。

正式native publication／CONTRACT／RESULT須使用真正stage packet所發的固定命令。缺runtime／packet時記native_admission、native_stage_publication、native_contract_validation、native_result_validation=NOT_RUN，附native-admission.json及精確blocker。文件的JSON解析、契約equality／hash／scope只屬document consistency，不是JSON Schema tool PASS或native admission。保留schema3形狀並精確區分未執行驗證。

每轮实测更新CON/E2E測試報告.md與progress.md，來源必有relative／absolute／bytes/hash；screen capture未落檔者標OBSERVED／NON_GATE，不能補造PNG。把報告交给高階Planner；無可用通道就記未交接。六狀態分列，文件完成不代表產品／E2E DONE。

本次已授權向origin的v43-ab/codex-rev28 normal push。origin當前為77b83c4，正常push亦會送出先前已存在的0a98564、0838a45兩個LINE相關提交；本次新commit只含CON文件，不stage既有dirty/untracked檔案。提交訊息須包含意圖、實際文件內容與下一步／native驗證限制；不force push、不修改產品。
