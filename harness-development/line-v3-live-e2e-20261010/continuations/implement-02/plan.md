# LINE v3 Implement 與兩本相簿實機 E2E 計畫

Task ID：`TASK-20261010-line-v3-live-e2e`；continuation：`implement-02`。
Project root：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
本文件落實本次對話已確認的 proposed plan。執行路線為 deterministic Handoff → Implement → E2E_test；本次獨立 Plan Review 明確免除，記 WAIVED/NOT_RUN。此前已確認的事後獨立 Acceptance 保留為完整專案關閉條件。

## 已核對基線與授權

- 本次落檔前 HEAD：`fad3641a3193e25b2ae5b6b3ce036e8d33843418`；branch：`v43-ab/codex-rev28`；index 無 staged paths。原報告後段已記錄本機 checkpoint，不能沿用早先「未 commit」為現在事實。接手 Agent 仍須重新核對當下 Git。
- State：schema 2、revision 34、252091 bytes、SHA-256 `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`。Config：384 bytes、SHA-256 `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`。
- 歷史 Python 77、Node 10 項離線 PASS；Swift 最後兩次均 320 項中 3 項 FAIL。這是歷史證據，不認證接手後的修改。
- Swift 同 root issue 的四次收據全部保留：`668ea46f205c42f1b5d5ba5aa3f966e4`、`5b37804c7b314bdeb80238d415d2fc1f`、`85355bab929e445c8719cd6056e3c591`、`24fbfc8ff57743af97e60a9edc25ba23`。更早未知歷史仍 UNKNOWN。
- 本次 request_user_input 的實際回覆為 `swift_attempt_exception = 核准單次例外 (Recommended)`，核准修好離線缺口後的一次額外 Swift package 驗證。另一回覆為 `updated_plan_review_route = 直接 Handoff (Recommended)`，明確延續本次 waiver、保留事後 Acceptance。其後使用者再次明示本次計畫不需要獨立審查。
- 唯一 writer、schema 2→3 migration、兩個不同未 VERIFIED fingerprints、兩個 cap=1 lifecycle、兩次 Save All、兩次 chooser confirmation、1000 次額外可逆 GUI invocation，沿用原授權。
- 原 contract SHA-256：`ffef63e5ce295910cf0b07a5cc5615bc2719dc651e425306677666b5d8a68ab1`。新版只補入既定計畫需要的 `state/.line-backup-v3.tmp`，所有原 gates、風險級別及 writer limits 保留。
- CRITICAL 的 immutable Harness 4.8 schema 仍要求 `plan_review_required=true`；實際路線以單獨 waiver 表示。native admission/controller validation 仍 NOT_RUN；不得杜撰 stage packet、驗證命令或 reviewer PASS。

## 實作範圍與順序

### 1. 保全與 fixture 修復

在任何產品修改前保存 fresh HEAD、branch、index tree、dirty/untracked 路徑、現有產品 diff、state/config/source hashes；保全所有無關工作與歷史 task artifacts。root 串行修改，max_parallel_writers=0；最多三名唯讀 helpers，可平行分析但不能改 scope/gates、寫產品或另開 nested sessions。

在本 continuation 的 fixtures 建立六組 hermetic Swift producer packets。外層 `config.json`、`state.json` 目前仍含舊 root，且 bytes/hash 與新 producer report 不一致。統一 project/backup roots、run/intent/registry destinations、必要 evidence references；由修正後的 fixture project 重新產生 report，將同一份 config/state bytes 提供給 Swift loader，生成 inventory。每組正向 fixture 先成功 binding；負向測試先證明原始 fixture 有效，再施加單一變異。不得改舊 fixtures/receipts 來補造成功。

### 2. 交易權限、收據與副作用

- Store 的 operation guard 檢查巢狀 transition：只改當前 run/batch、各 operation 的合法欄位及 append-only events；保全历史 runs，revision 只由 Store 更新。
- prepare 在 shared lock 下重查 grant、CAS、duplicate、destination；任何 mkdir 前持久保存 filesystem intent 並讀回。失敗保留 side-effect receipt 與現場，不刪既有資料。
- GUI task-local ledger 跨兩個 lifecycle 累計。每次輸入先 reserve；atomic dispatch 的兩次 click 在 ellipsis 前 reservation，UNKNOWN/crash 不退款。
- CLI/Service live dispatch 接受 retained adapter receipt reference，驗證實際 bytes/hash、owner/action/session、事件順序、SCK guard、chooser、download-start evidence；caller JSON 布林值不能獨立證成成功。
- execution grants 綁新版 contract、config、完整產品 source inventory、native binary、GUI ledger；fixture authority 不可 live dispatch。兩個 owner 共用任務總額度。
- finalize 使用 task-local transaction lease、已開啟 directory/file identity、commit 前後 inventory 與 readback fence。lease 是協作鎖，不宣稱 OS 強制排他；漂移或不確定時阻塞下一本，保留真實 state replacement 結果。

### 3. SCK 與正式 live bridge

在已列出的 Swift capture/composition/CLI scope 實作唯讀 `rev28ctl album-support` producer，使用 macOS 26.5 full-display SCK，保存原始影格、metadata、Vision OCR、mapping、manifest。接通正式 captureMenuSupport/guardMenu；native producer 不派送 GUI。

分開識別 intent 前 CUA frame 與 ellipsis 後 SCK popup frame，分別保存 hash/time/source；至少三個唯一分散自動 anchors，residual≤2 source pixels、uncertainty≥2 pixels、margin≥uncertainty+4 pixels、actionable intersection≥16×16 pixels。

本計畫沿用已核准 originalObservedDispatch：intent commit/readback → 消耗一次 token → ellipsis → 有界 native popup capture/guard → 唯一 Save All → post-state。這是本專案較 skill 通用 atomic click pair 更具體的已核准順序；不得改回不具 popup guard 的盲點擊。guard 只驗證校準點，不在 intent 後重新校準或換點。不得插入額外 GUI、app switch、可重派 token 或第二個 menu action。

live runner 使用 documented CUA、opaque receipt token 與正式 CLI bridge；runtime 不具 raw screenshot bytes、持續 session 或原子鏈 bridge 能力時停止。全 runtime/source/binary inventory 納入 freeze，更新 source-membership checks。

finish 增加 `CAP_REACHED` completion scope：恰好完成一本且無 unresolved run，才能終止及 release。此結果不宣稱整份 catalog ALL_COMPLETE；fresh full-catalog drift 驗收另行判定。fixture I/O 與 live provider 明確分離。

## 離線測試與有界 Swift 例外

完成全部修改與 fixture coherency 檢查後才執行下列回歸；環境、fixture、scratch/cache、runner outputs 全綁本 continuation。

1. Python：immutable Harness runtime Python，分別 `-B -m unittest discover -s tests -p 'test_batch_*.py' -v`、`-p test_project_binding.py -v`、`-p test_transaction_core.py -v`。
2. Node：`/opt/homebrew/bin/node --check scripts/line_backup_cua_adapter.mjs`，再 `--test tests/test_cua_adapter.mjs`。
3. Swift：`/usr/bin/swift test --package-path rev28 --sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk --scratch-path <本 continuation>/swift-build-26.5`。

Swift runner 啟動 subprocess 前持久消耗唯一 extra-attempt reservation。compile error、test failure、timeout、crash 或收據不完整都耗用；不預跑該 package build/filtered tests，不再跑第六次，不透過 task/issue 改名清零。其他 root issues 延續其實際 ledger，最多三次，兩次無新資訊即停止；未知數不當零。

新增測試覆盖巢狀越權、歷史 run 修改、foreign owner、grant/source drift、receipt 篡改/重播、跨 lifecycle GUI quota、prepare failure、commit/readback 內容漂移、popup frame identity/timeout、release 前禁止第二本，以及正向 fixture 有效性。`tests/test_transaction_core.py` 只執行既有 suite，不列為本輪可修改路徑。

每次保留 argv/env/start/end/exit/stdout/stderr/bytes/hash/source binding 與實際 discovered test count。全部必要 suites 明確 PASS 才能 G_OFFLINE PASS；舊 PASS、317/320、fake I/O、靜態分析均不能替代新候選的驗收。

## 兩本實機 E2E

### A. Gate 與 migration

G_AUTH/G_OFFLINE 通過，完成 source/config/native binary freeze、正式 grants。重查 schema2/rev34/hash、歷史、owner/context lock；保存 original bytes，以唯一 writer 與既有 lock/CAS 遷移 schema3/rev35。readback 證明只改 schema_version、revision、新增 active_batch=null，歷史及大整數精度完整。readback 不確定即停。

### B. Fresh catalog / menu

先告知使用者 LINE app/surface 與下一個精確操作，取得明確前景交接；舊交接不是當下新鮮證據。fresh 核對 configured group、Albums、PID/process instance/window/session/layout、安全焦點。每次單一≤0.25 viewport scroll 建立完整 catalog：肯定 top/bottom、相鄰完整唯一卡片有序 overlap、日期/張數一致性。

依 catalog 順序挑第一本 eligible，略過 VERIFIED、阻塞 unresolved intents/identity ambiguity；空目的地、同一 fresh frame 完整卡片及非 thumbnail metadata 點位、post-open fingerprint MATCH。intent 前觀察實際 Save All row 校準，安全關閉且未啟動命令，完成 G_MENU。

### C. 第一本 transaction

重查 duplicate/destination/owner/calibration/freshness → intent commit/readback → 原始 token 單次 Save All → 真實 folder chooser → Go to Folder 精確完整路徑與 leaf fresh 確認 → 一次 confirmation → download start。從下載開始停止 LINE 輸入。

五秒一次唯讀取樣，三次相同 inventory，最多600秒；expected count、全部 entries、zero-byte/partial/unknown 為零、逐張 ImageIO 完整 decode、decode 後 inventory 不變。commit VERIFIED/registry/release evidence，state readback，再 finish cap1/release。G_FIRST 有獨立證據。

### D. 真實 scroll / 第二本

第一本 VERIFIED 且 active_writer/context_lock/active_batch 全釋放後，建立第二 owner/grant，沿用總額度與感測連續性。fresh 回 Albums，必須實際執行至少一次≤0.25 viewport scroll，保留 before/action/after；證明同群組/surface/session/PID/window/layout、有序完整 overlap、至少一張新完整 eligible card。

fresh full-catalog drift check/admission 後，使用 fresh card binding 選不同 fingerprint，重跑全部校準、intent、Save All、chooser、download、decode、VERIFIED/readback/release。不能重開第一本，不能因第二本原先可見而省略 scroll。無下一本記 NO_ELIGIBLE_TARGET；未scroll記 SCROLL_TEST_NOT_RUN，均為未完成兩本 E2E。

## Gates、報告與結束

原 machine GateSpecs 完整保存於 plan-contract.json；handoff.json 為其逐 byte copy。所有實作/live gates 起始 NOT_RUN/既有阻塞，沒有由本文件補成 PASS。Plan Review WAIVED/NOT_RUN；事後 G_ACCEPTANCE 保留。

更新本 continuation 的 E2E測試報告.md、progress.md、attempt ledger、blocker packet（如需），主張連 workspace 的相對/絕對證據路徑與 bytes/hash。分別判定 menu、first、scroll、second、batch/state、preservation；原失敗保持原件。最新有效歷史 Planner 記錄是 `../../evidence/planner-replan.md`。

六項 status 分開：PRIMARY_OUTCOME_STATUS、IMPLEMENTATION_STATUS、CORE_ACCEPTANCE_STATUS、REQUIRED_VERIFICATION_STATUS、INDEPENDENT_ACCEPTANCE_STATUS、TASK_CLOSURE_STATUS。只有適用 gates 與事後 Acceptance 均滿足才 task DONE。

前景被取回、identity/mapping/scroll UNKNOWN、quota/grant/source drift、目的地異常、uncertain dispatch、writer guard/state/readback 漂移，立即停依賴動作並保留資料及 intent barrier；不重送 Save All、不自行降低 gate。

## 本次文件提交

本次 authoring 工作只落檔本 continuation 的計畫與交接封包，不代表產品 Implement/E2E 已執行。使用者另明確授權：文件完成後，由一名 GPT-6 luna subagent 深度梳理上下文、撰寫含意圖/實際變更/下一步的詳細提交訊息，再 add/commit/push。只 stage 本次新增文件；無關 dirty work 保全。此文件 checkpoint 可在產品 E2E 尚未完成時提交，commit/push 不等於 G_DELIVERY 的完整專案驗收 PASS。
