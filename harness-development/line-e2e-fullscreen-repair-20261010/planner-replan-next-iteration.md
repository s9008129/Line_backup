# 高階 Planner 回饋：下一輪範圍與驗收計畫

日期：2026-10-10（Asia/Taipei）
任務：`TASK-20261010-line-e2e-fullscreen-repair`
規劃依據：本 task package 的 [E2E 測試報告](E2E測試報告.md)、核准技術計畫 `20261010_LINE全螢幕定位與相簿備份_E2E技術修復計畫.md` §§3–13、以及 LINE batch／acceptance service 原始碼。
角色：唯讀高階 Planner；本文件是建議與決策輸入，不是新的實作授權或已審查的執行計畫。

## 本輪判定

本輪只驗證成功到「相簿 detail 的 Save All 原生選單可由完整螢幕影像觀察、辨識並產生安全點位候選」。SCK 原圖、menu OCR、v2 幾何 replay 與安全關閉均有證據；交易 owner、持久 intent、Save All dispatch、chooser、真實下載、檔案完整性與 terminal state 均沒有完成。整個自動備份 E2E 維持 **PARTIAL / BLOCKED**，不能把 menu 幾何 PASS 外推成相簿備份 PASS。

已確認的核心阻塞如下：

1. Canonical state 是 schema 2、revision 34。task-local schema-2 `acquire` 被共用 writer guard 以原文 `Canonical state requires the v3 service` 拒絕。拒絕前後 state SHA 相同，沒有 active owner、canonical committed intent 或 dispatch。
2. 被拒絕的 acquire 在呼叫 writer 前先建立目標相簿的精確目的地目錄。唯讀 inventory 是 0 entries；這個目錄是本次唯一新增的備份目的地副作用，必須保留，不能刪除、改名、加 suffix 或覆寫。
3. 原核准計畫凍結 schema 2／RC2 與 `backup_one`，並排除把 schema-3 Store 當成本輪 live schema-2 authority；同時允許第一個完整可見 eligible album 直接進入 E02。改用 v3 會觸及 writer、授權／Acceptance 順序及完整 catalog admission，超出原計畫核准的機械實作範圍。
4. v3 production CLI 的 mutation 路徑要求 `authorization.json` 中 `config_cap=1`、精確的 `user_message`，以及帶 `INDEPENDENT_ACCEPTANCE_STATUS=PASS` 和 I0–I4／A1 gate 結果的 Acceptance artifact。現有授權記錄的原話不同，且明定正式 product Acceptance 在 E2E/report 後；目前未找到符合要求的 Acceptance artifact。不可改寫、補造授權或把未跑的 Acceptance 標成 PASS。
5. v3 coordinator 先做完整 catalog admission，並在結束時檢查 catalog identities 與起始資料一致。v3 提供 `backup_batch`／`catalog_only`，沒有 `backup_one`；設定 `max_albums_per_run=1`。若批准 v3，兩本相簿必須是兩個各自限額 1 的獨立 batch lifecycle，不可把兩次交易合併或重置額度。
6. 沒有證據表明使用者要求的「第一筆 VERIFIED、readback、release 後回列表，實際 bounded scroll 至下一本」已測過。v3 admission 的 catalog scroll 也不能代替這個獨立 E03 gate。

對空目錄的處置是**建議新計畫明確核准採用這個精確 leaf**，前提是實際 writer 前重新做 no-follow path、非 symlink、0 entries、父目錄與 inode 穩定性檢查。若新計畫不批准採用，就保留原狀並停止該筆交易；任何人都不應自行清理或改名。

## 必須由新計畫決定的架構選項

### A. 留在 schema 2

制定並審查一條正式、會被共用 canonical writer guard 接受的 schema-2 owner／intent／terminal write path，明確保留 CAS、歷史與 at-most-once 語義。不得旁路 guard、直接編輯 canonical JSON 或換用另一份 state。

### B. 正式採用 v3

明確批准 schema 2→3 migration 及唯一 canonical authority；把執行授權和事後獨立 Acceptance 分開，解決目前 CLI precondition 與 E2E 後 Acceptance 的順序循環；批准完整 catalog admission／final catalog drift 檢查；定義兩個分離的 cap=1 batch lifecycle。必須以可追溯使用者授權支持這些改動，不能推定現有授權等於批准 v3 架構。

### C. 維持唯讀／部分狀態（Planner 建議的近期選項）

在 A 或 B 尚未經正式新計畫決定前，只做不改 state、不觸碰 LINE 的唯讀診斷、契約比對及離線測試。保留本輪 menu 驗證為 OBSERVED／候選幾何已通過，整體 E2E 為 PARTIAL / BLOCKED。這是當前建議，不是替使用者選定架構。

## 建議的下一輪有界工作分段

以下 P0–P8 是供新計畫採納或修改的建議順序。P0–P3 不需 LINE 前景；P4 起涉及 live app，必須在開始前明確告知使用者當下 app、畫面與唯一下一個動作，等待使用者交還前景。任何前景中斷都使舊畫面、錨點與座標失效。

### P0：重建額度與只讀基線

- 建立 append-only attempt／GUI invocation 帳本，從現存 action receipts、build receipts 和舊紀錄重建已知事實；build attempts 01–08 不等同 material attempts。
- 原計畫的 `+5 material attempts` 是追加額度，不重設歷史；同一 root issue 仍受 Harness 最多三個 evidence-bearing attempts、兩次無新資訊即升級／停止的約束。
- 目前 task package 未找到完整 append-only attempt ledger，且無完整 GUI invocation 總帳。不得把未知當 0；如果無法重建使用餘額，停止任何新 LINE UI 操作。
- 重新讀取 canonical config/state/source，保存 argv、exit code、stdout/stderr、SHA 與 pre/post snapshots；核對 revision、authority、duplicate registry、unresolved intents、active owners 及設定 hash。
- 對既有空目的地做 no-follow inventory，記錄精確路徑、symlink 狀態、entries、父目錄與 inode；不刪除或改名。

### P1：凍結架構與授權契約

- 由高階 Planner 選定 A 或 B，明訂唯一 canonical state writer、schema／migration、Execution authorization、Acceptance 先後順序、catalog admission 語義、每本相簿的 run boundary、empty-destination 政策和失敗傳播。
- 核對目前授權原始記錄；不得把 CLI 要求的精確字串倒填成使用者授權，也不得以 waiver 冒充 Acceptance PASS。
- 對兩個不同相簿各跑 cap=1 的語義要明示：第一本 VERIFIED、讀回並 release 後，才能開始第二本新的 owner／admission／intent／transaction／verification／release。

### P2：先做離線契約測試

在 live UI 之前驗證：canonical compare-and-commit／history preservation；空 destination 的精確採用／拒絕政策；CLI execution grant 與事後 Acceptance 分離；catalog ordered-overlap、top/bottom boundary、mapping、final drift；兩個獨立 cap=1 run；scroll 判定；CUA frame 保存及自動 anchor mapping。每個拒絕案例都要確認不造成 state 或資料副作用。

### P3：唯讀 live eligibility／catalog preflight

只在 P0 額度有明確餘額且 P1/P2 gates 通過後，取得新的前景交還與新鮮觀察。重新辨認群組、Albums surface、process/window/session/layout 與完整可見卡片；動態略過 registry 中 57 張和 182 張既有 VERIFIED 相簿。未達當前核准 catalog completeness 要求、identity 不明或候選不唯一時停止，不點擊卡片。

### P4：第一筆獨立交易及驗收

在批准的唯一 writer 下，重算目標 fingerprint、duplicate 與精確 destination；fresh owner、persisted intent、readback、menu identity／geometry／安全 margin 全數 PASS 才能一次派送 Save All。結果不明就保留 at-most-once barrier，不重送。之後只做 chooser 的精確路徑確認與唯讀檔案驗證；要求穩定 inventory、expected count、零 byte／partial／unrecognized 為 0、每張圖完整 decode、terminal state commit/readback 及 owner release。

### P5：獨立驗證使用者要求的 scroll transition

在第一筆 VERIFIED、state readback 成功且 owner release 後，回到 Albums surface，實際做至少一次不超過 0.25 viewport height 的 bounded scroll。保存 scroll 前、操作與操作後的 CUA/SCK observations、影像 bytes/path/dimensions/SHA、action/result、時間，以及同一 group／surface／session／PID／window／layout 的連續性。必須有至少一個完整唯一相鄰 fingerprint 的有序 overlap，並出現至少一張新的完整日期/count 候選；之後才可重新綁定新卡片。若未知、無進展、context drift 或歧義就停止，不重試舊座標、不盲目連續滾動。沒有 eligible 目標記 `NO_ELIGIBLE_TARGET`；未滾動或先決條件不過記 `SCROLL_TEST_NOT_RUN`／PARTIAL。

### P6：第二筆獨立交易

只從 P5 新鮮畫面重新取得候選與 click binding。對另一個不同 fingerprint 重做 destination／duplicate／owner／intent／menu／一次派送／download／file decode／state readback／release 全流程。不得以再次打開已 VERIFIED 的相簿充當第二案例。

### P7：批次與 preservation 收尾

證明兩筆交易各自 VERIFIED 且獨立，既有照片未被刪改或覆寫，duplicate registry 一致；保存完整命令、inventory、decode、state revision/hash、前後差異和每一個副作用。明確標記無法證明的 OS sandbox／network denial 為 unknown。

### P8：事後獨立 Acceptance

依新核准順序，使用與實作者獨立的 Acceptance reviewer 重新讀取合併後證據，完成 I0–I4／A1 等所需 gates；若 Acceptance 是 v3 CLI 寫入的先決條件，P1 必須先消除循環，不能以事後報告補成先前 PASS。只有所有適用的 implementation、core、required verification、independent acceptance 與 closure gates 均有實際 PASS，才可宣告完整 E2E。

## CUA 與螢幕證據界線

- 將 `HOSTED_CUA` frame 和完整桌面 ScreenCaptureKit frame 分開標記。SCK popup 原圖可以證明原生選單在完整螢幕中可見，不是 CUA frame；不可混用來源名稱。
- 後續每個關鍵 CUA frame 必須保存原始 bytes、path、尺寸、SHA、時間、session/window/PID/layout 和 mapping provenance。現有 CUA supporting frame bytes 未保存，故其畫面只能記為 `OBSERVED`，不能宣稱完整可重現。
- 若計畫要求自動定位，需程式自動取得至少三個分散唯一 anchor、自動重建座標 mapping；結果可重現，最大 residual ≤2 source pixels，且安全 margin 高於量測不確定度加 4 px。若含人工對應，必須明示為候選或人工 `OBSERVED`，不列 full-auto PASS。

## 停止條件與前景協定

任何 state drift、active owner、unresolved intent、destination 政策未決／非空、mapping 或 scroll 不確定、未取得明確前景交接、使用餘額未知、或一個步驟結果 UNKNOWN，都應停止依賴該條件的後續工作。Save All 不明時絕不可再送一次。若需要 live 前景，先精確說明「LINE 哪個畫面、要做的單一動作、預期觀察」，待使用者明確交還前景才開始；操作期間若使用者取回前景，立即停止並丟棄舊 mapping。

## 給下一位 Planner／Implementer 的交接

先以本文件與 [E2E 原始證據索引](E2E測試報告.md#核心證據索引)作為事實基線。下一個正式 Plan 必須把 CUA/GUI 額度重建、writer 架構選擇、authorization／Acceptance 次序、catalog 語義及空目的地政策列為明確前置 decisions；在這些 decisions 被審查前，不得開始新的 state write 或 LINE 操作。本輪對完整備份目標只證明 UI menu sensing／candidate geometry 部分成功，沒有產生任何照片備份。
