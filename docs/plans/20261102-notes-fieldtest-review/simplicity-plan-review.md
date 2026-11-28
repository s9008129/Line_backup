# S3 補充計畫簡潔性審查

## 本角色結論與版本

**結論：PASS。** 在本次精確規劃版本中，未發現有具體證據支持的重大、可避免複雜度。窄的 `list-key` 入口、操作文件修正及既有 G0 工作單均可連回已定位的需求，必要的身分、證據、禁止重送與獨立驗收門檻仍有保留。這只通過計畫簡潔性，不是公共介面採納、實作授權、功能或實機驗收。

- 角色／checkpoint：Owner 在另一正式主 Session 啟動的 Simplicity Reviewer，**plan checkpoint**；依指定 `07_simplicity_review_prompt.md` 執行。
- 使用者目標：將十項實機診斷轉為既有 S3 的最小充分工作單；補建帳前 key、絕對證據路徑與 lists→summary；GUI 根因維持未知，原 R1–R10 仍須逐項交代。
- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；branch：`feature/line-notes-media`。
- **精確受審提交：`75d4053332aa518a3e91e67b03dbd611e5efaf72`**。起始本機／遠端 HEAD 相同，index、tracked 與非忽略 untracked 乾淨；其他 worktree 未更動。
- 受審文件：[plan.md](plan.md)，SHA-256 `d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`；[handoff.md](handoff.md)，SHA-256 `50582b29dcf6f5e9ce47cb9a67848da5c0b5f25c99b8b3f8f0bccfeea2cfc4aa`。兩者均核對指定 commit bytes，不能以起始舊 HEAD 或後續報告提交替代。
- 受測產品仍為 `8814d6db0e0a7f368fa5b241fc5ab0010540ea63`；到受審提交的 `src tests .agents/skills AGENTS.md` 差異核對 exit 0。本報告不重新接受該產品或 S2。

本 Session 未參與受審 plan／handoff 的起草或產品實作；本輪只寫本報告及專案私有審查證據。使用一名同角色唯讀 helper 核對 CLI、路徑與既有測試，主 Session 複核 identity、init、JSON、dispatch、capture 與測試 setup 的關鍵位置。helper 沒有正式接受權，也不是第二份獨立審查。

## 審查範圍與機制到需求的映射

直接審查本版 plan／handoff、[十項診斷](issue-analysis.md)、[原 replan](../20261101-notes-all-issues-replan/replan.md) 與現行交接、[S2 報告](../20261101-notes-all-issues-replan/implementation-s2.md)、記事本 Skill、已取得的 GUI／驗證／判定案例文件、相關源碼與測試。另讀指定的 Planner 私有補充備忘；它是轉交摘要，沒有升格為原始工具回傳。本輪未重看私有 GUI 圖像或讀真實帳本。

| 機制／受審位置 | 具體需求或必要保護 | 複雜度成本及判斷 |
|---|---|---|
| `list-key`，plan §4.1、N26-INIT | 在 init 前取得完整相同的 list context，不先建空帳、不放寬 context 檢查；Owner 不填內部 key／JSON | 新增一個公共子命令及維護測試，但只接既有 JSON→identity→key→輸出路徑；禁新模組、hash、schema、cache、帳本、鎖及 retry。與已知 bootstrap 缺口相稱 |
| 同一 identity 輸入與 init 後讀回，§4.1、C1–C2 | 防止空白、Unicode、signals 的 omitted/null/{} 等差異造成不同 key／錯 context | 等價與拒絕案例保護既有 identity 語意，無新正規化或新身分制度；沒有承諾跨程序原子性 |
| 絕對路徑、父目錄存在／子目錄未建，§4.2、N26-PATH | 修正診斷已定位的範本矛盾，同時保留 canonical、symlink、拒覆寫及 context 檢查 | 改範例／help，必要時補合成缺口；不新增路徑轉換器或自動建父目錄行為 |
| 重用 `notes_capture`，§4.2 | 拒絕與成功各自留 receipt，child 最多一次；避免為補輸出重執行 | 使用已存在的 notes 專用 wrapper，不加第二套 runner；receipt 與 CUA 原始回傳仍分開 |
| lists→回傳 records_root→summary，§4.2、N26-SUMMARY | 從全帳本查詢可靠定位單帳本；多候選／壞歷史時停止 | 文件鏈及合成用例即可，不改名既有 flags、不新增查詢層 |
| 七項 GUI 現象／B1，§5 | 對 AX、工具列、panel、檔名、toast、spinner、卡片各自保留可支持命題與未知；就緒後才判種類 | 只補當次觀察的決策規則，依白名單以連結避免多份交易流程；不新增 GUI controller、全域命名器或固定 sleep |
| G0-0～G0-5，§6 | 原 R2／G0 已要求同 viewer 的來源、幾何及能力比較；新來源不能回填舊 trace | 展開原有觀察工作單，記平台可得欄位與 UNKNOWN；獨立 AX 僅用既有可用工具，缺件停止，不安裝 sensor、不觸發下載重現 |
| C1–C4 及既有最小回歸，§7 | 身分等價、零帳本副作用、嚴格證據路徑及查詢契約 | 沿用現有測試且只補缺口；程式切片執行原定回歸，文件切片以文件核對為主，同版無變更／失效不重跑全套，未見多餘測試框架 |
| C5／R1–R10 整合矩陣，§7 | Owner 原目標是處理全部問題，不能只修 bootstrap 就稱全部完成 | 連結既有程式／測試／實機狀態，舊結果標來源及未重跑；不是要求重做已完成切片 |
| S3a／S3b、A0、D1／D2／G1／G2，§7–8 | 首切片人工審查、獨立相容、精確資料授權及真實結果是原 gate | 新增入口的 STANDARD 風險不取消原 CRITICAL 的適用門檻；舊 waiver 不延伸到本版，沒有以安全停住換取完成 |

十個 N26 ID 均有對應工作與停止條件。沒有找到僅為未來泛化而加入的機制，也沒有把多份 hash／重讀、flock 或 CLI receipt 說成 GUI 與帳本的共同原子交易。

## 關鍵取捨與阻塞性發現

**阻塞性發現：無。** 不以行數、文件長度、案例數或個人風格作退回理由。

`list-key` 的較小替代方案已明列：文件直接呼叫內部純函式確實可行，並無計算循環。[notes.py:120](../../../src/line_backup_batch/notes.py#L120)、[notes.py:152](../../../src/line_backup_batch/notes.py#L152) 支持無帳本計算；[init:4398](../../../src/line_backup_batch/notes.py#L4398) 共用 JSON parser 與 identity；[create:607](../../../src/line_backup_batch/notes.py#L607) 在建立資料前以 key 預檢 context。

選窄 CLI 的理由也具體：[notes_capture.py:225](../../../src/line_backup_batch/notes_capture.py#L225) 與 [242](../../../src/line_backup_batch/notes_capture.py#L242) 固定保存並執行 notes child。若改用內部 Python 小段，還須另維護其參數／輸出保存方式，才有同等操作 receipt。**推論：**在本專案已採 notes_capture 的契約下，一個共用解析的純計算子命令具有合理成本；目前證據不足以要求為省公共子命令而另造文件執行入口。Owner 仍須採納這項明列的公共介面增量，本 PASS 不代作該決定。

G0 的欄位較多，但都對應診斷中已知的 scope、時序、crop／titlebar、映射及 AX 歸屬缺口；原 replan §5 已要求能力對照。plan §6 允許不可得欄位記 UNKNOWN，且不用新時段原件回填舊資料，沒有為確定根因擴成觀察平台。獨立 AX client 的要求屬另授權 G0 診斷，不是 S3a 離線切片前置，也未把 AX locator 變成所有 GUI 操作的唯一入口。

C1–C3 涉及身分與禁止副作用；有真實 bootstrap／範本摩擦作依據。測試成本的最小方向是沿用現有拒絕案例，只新增 list-key 本身與完整鏈的缺口，無需減掉安全條件。已有覆蓋來源由 helper 核對，本輪未執行：`tests/test_notes_evidence.py:171,204,230,243,335`，`tests/test_notes_records.py:622,657,674`，`tests/test_notes_capture.py:45,83,192`。

## 非阻塞建議

1. C2 的無帳本案例宜在同一測試檔使用小型獨立 test class。[現有 NotesRecordsTests.setUp:49](../../../tests/test_notes_records.py#L49) 會建立 collection／帳本並 bind；直接沿用會增加 setup，也使「無帳本亦可算」的證據不清楚。此建議保留原白名單，不要求新模組或框架。
2. C1 可用少量表格／subTest 表達輸入的等價與不等價；C3 已有 symlink／collision／context／preflight drift 案例就引用沿用。只補相對路徑、父目錄與 bootstrap 真正缺口即可。這是控制重複成本的建議，不是新增通過條件。

## 事實、未知與本輪實際檢查

**事實：**指定規劃提交只新增 plan／handoff；目前產品與受測 `8814d6db` 在上述產品範圍無差異。主 Session 直接核對的源碼支持既有純函式與固定 notes capture 路徑；計畫沒有實作候選。23 份指定來源的 bytes／SHA-256 與可重現的 Git 檢查留在 `.local/line-backup/tasks/20261102-notes-fieldtest-simplicity-plan/`。

**未知：**尚未有 list-key 實作 diff，不能證明未來 dispatch／無資料副作用／全部案例已通過。GUI 的原始 invocation／return envelope、實際 CLI 起訖、clock source、焦點／幾何映射及獨立 AX 結果仍未知。本輪不推定 LINE、CUA、快取、右鍵送達或 intent 隱藏工具列的根因。

兩張照片的 completion／當次摘要／audit 只按前輪報告保留；沒有重算、查看目前檔案或驗外部副本。本報告沒有新的人眼 `OBSERVED`，也不撤銷既有完成或解鎖舊 UNKNOWN。`external_copy_verified=false` 與 `real_line_e2e=NOT_TESTED` 不變。

工作環境為 macOS、上述 repo cwd、`/usr/bin/python3` 3.9.6。以下為本輪實際執行，不是產品回歸：

| 命令／檢查 | 結果與界限 |
|---|---|
| `pwd`、`git rev-parse --show-toplevel`、`git status --short --branch`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | exit 0；起始身分／乾淨狀態如上，其他 worktree 保留 |
| `git ls-remote --heads origin refs/heads/feature/line-notes-media` | exit 0；起始遠端完整 SHA 與受審提交相符 |
| `git diff --exit-code 8814d6db0e0a7f368fa5b241fc5ab0010540ea63 HEAD -- src tests .agents/skills AGENTS.md` | exit 0；沒有把新增規劃文件當作產品改版 |
| `git show --stat --oneline HEAD`、`git show --format= --name-only HEAD`、`git show --format=fuller --no-patch HEAD` | exit 0；核對規劃提交及僅兩份文件的變動 |
| `cat`、`rg`、`nl -ba …`／`sed -n …` 讀指定來源；來源 SHA-256 及候選 bytes 核對 | 已取得內容與 helper 核對分別記錄；不聲稱廣讀私人原件 |
| `/usr/bin/python3 --version`、本輪私有文件／來源檢查、`git diff --check` | exit 0；最終結果及報告 hash 留私有 `review-checks.json`，不沿用 Planner 的 94 項為本輪測試數 |

工具／來源限制：repo 沒有兩份指定 policy；首次 `ls` 因 repo 路徑缺席 exit 1，改讀已安裝的同版政策與角色報告範本，未恢復 controller。一筆補充讀取 download-and-ledger、evidence-template 與實機報告的工具呼叫顯示 `aborted before dispatch`，未取得內容、沒有命令 exit code；未重試或換入口，這三份文件不列為本輪主 Session 直接讀回證據。相關需求的簡潔性判斷依已取得的 plan／handoff／診斷、原 replan 與源碼，並不要求判定 GUI 原因。helper 一筆含不存在測試檔的探索定位命令 exit 2，其已取得來源與未知另有區分。

同角色研究 helper 的 dispatch 沒有 model／effort override；此處只記請求參數，不由設定推定後端身分或 provider 用量。Owner 後續指定 GPT-6 luna 的協助用途為提交訊息整理，不授予正式接受權；實際派送及結果留交付紀錄。未取得 provider usage，不主張費用、token 節省或平台隔離。

**本輪 NOT_RUN：**產品 CLI／help、daily／notes 單元測試、ImageIO／ffmpeg 重驗、G0、D1／D2／G1／G2、真實帳本／照片／active、GUI／chooser／popup、混合附件、影片下載、跨 Session、獨立相容 Acceptance。原因是本輪為計畫唯讀審查；不以檢查文件或 Git 交付替代這些結果。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: PLAN_SIMPLICITY_REVIEW_PASS
IMPLEMENTATION_STATUS: NOT_RUN; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PLAN_SOURCE_AND_DOCUMENT_CHECKS_PASSED; PRODUCT_AND_GUI_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_HUMAN_ADOPTION_AND_REMAINING_VERIFICATION
```

下一步交 Owner 決定是否採納 `75d4053332aa518a3e91e67b03dbd611e5efaf72` 的公共純計算 CLI 與有界 S3 範圍，再由 Owner 啟動 S3a。若採納，實作者只交該首切片及 C1–C4 的精確候選／diff／報告後停止，implementation Simplicity Review 仍由 Owner 另啟；S3b、A0 與各資料／GUI gate 依原計畫分別交接。舊 waiver、S1 PASS 或本報告均不簽發 S2／S3 相容或實機接受。

本審查不要求改計畫或擴功能。任何後續候選、範圍或 gate 改變均不在本 PASS 覆蓋內，須由 Owner 決定適用複核。完成本報告及已授權 Git 交付後停止，不實作、自修、派下一正式角色、操作 LINE、merge master 或結案。
