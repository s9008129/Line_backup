# S3b 實作簡潔性審查

## 本角色結論與精確版本

**結論：REVISION_REQUIRED。** 一項新增的 chooser 必要條件要求目的地「尚不存在」，但既有 intent 已建立並記錄該空白目錄。此條件額外引入無法與既有流程同時成立的狀態要求，會使依文件執行的 Agent 在 chooser 確認前停住。最小方向是移除不存在條件，沿用原 intent 建立的空白目錄；三層路徑核對、身分與單次輸入保護均須保留。其餘受審新增機制未見重大、可避免複雜度的證據。

- 角色／checkpoint：Owner 以 `07_simplicity_review_prompt.md` 啟動的正式 implementation Simplicity Review，範圍為 S3b 文件切片與 C5 整合。
- 使用者目標：核對 S3b 是否以最小充分文件補足七項 N26／B1 操作契約，並保留原 R1–R10、資料保護與適用驗證 gate。
- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- **受審候選／起始 HEAD：`b2cd3e103a187c0cf8232b93af2f458a3e468386`。** 起始 index、tracked 與非忽略 untracked 乾淨；其他 worktree 未變更。
- **差異基準：`72132263ce25aa55e3e6f48626f5c3a73f938fad..b2cd3e103a187c0cf8232b93af2f458a3e468386`**；7 檔，193 行新增、15 行刪除。完整 diff SHA-256：`da2e2327e442e6ae45f25e3663941409a30d2a18eafa7fd1bafedb71cd1bdfc4`。
- 六份 Skill／reference 的 diff SHA-256：`22dc085d472665ed1ccf06dd15a9196506a87cfe10a75b1a7b7800f1149b0c86`；42 行新增、15 行刪除。
- 核定 [plan.md](../plan.md)：提交 `75d4053332aa518a3e91e67b03dbd611e5efaf72`，SHA-256 `d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`。
- 現行 [handoff.md](../handoff.md)：提交 `1cdb88bdff8a201173d2712ac827de6896181603`，SHA-256 `63fd3e530eee29688c14ede8f887dfc1a1b8b43ee1a2f85d3a66f208cf5c1ed8`。其 S3a 限制保留原適用範圍；本輪 S3b 審查授權來自 Owner 當次訊息，不據此啟動 Implementer。
- [implementation-s3b.md](../implementation-s3b.md)：候選內 SHA-256 `618054edf00a6e4bea6520f5eb12fd2cfa225200e65429c90c15530193884686`；報告所列六份來源 hash 均與候選 bytes 相符。
- [S3a 審查](../simplicity-implementation-review.md)：提交 `72132263ce25aa55e3e6f48626f5c3a73f938fad`，SHA-256 `e79aa81e4d3dbca205b16808c6d646d2e12cf6f327bbcf9ffb9607801ea68b7e`，仍只涵蓋 S3a 候選 `c8f1088820d835590d4a54b66de9c73b0308bac5`。為保留該原件與指定報告檔名，本輪報告新增在 `s3b/` 子目錄，不覆寫舊審查。

本主 Session 未參與受審實作或計畫起草。正式結論由主 Session 判定；一名繼承主 Session 設定、未帶 model／effort override 的同角色唯讀 helper 核對 C5 原始需求與 gate，沒有改檔或簽發接受。主 Session 直接閱讀完整候選 diff、七份候選文件、核定 plan／handoff、既有審查及 finding 相關程式。Owner 指定的 GPT-6 luna 僅在審查完成後協助整理提交訊息，不參與正式結論。

## 機制到需求的映射

下表的 Skill／reference 均位於 `.agents/skills/line-notes-agent-cua/`。同一原則在操作文件、statement 欄位與假設案例出現，是分別提供決策、記錄與反例用途；沒有以重複行數本身作為 blocker。

| 新增或修改機制／候選位置 | 核定需求與必要保護 | 成本與簡潔性判斷 |
|---|---|---|
| `gui-inventory.md:84`、`evidence-template.md:46` 與骨架的 AX／CUA client、API scope、app/window、role/children、raw return 引用 | plan §5 N26-AX：來源可追、相同 AX 不代表畫面未變；缺來源仍 UNKNOWN／BLOCKED | 擴充既有 statement，不新增 schema、sensor 或另一套觀察工具；成本相稱，不預填 G0 |
| `gui-inventory.md:76` 的工具列因果限制與對照條件 | N26-TOOLBAR、plan §6：保存焦點／hover／幾何，不由 intent 前後順序推因果 | 一段觀察限制，未新增 runner、固定 sleep、intent 重播或右鍵試探 |
| `download-and-ledger.md:224`、`evidence-template.md:50`、C10 的三層目的地 | N26-PANEL：PathTextField、panel current directory／where、intent staging 不混用；確認最多一次 | 三層核對有必要；額外「尚不存在」條件沒有需求依據且矛盾，見 S3B-SIM-01 |
| `download-and-ledger.md:223`、`verification-and-recovery.md:99`、範本的 basename／副檔名限制 | N26-NAME：檔名不認領媒體／attempt，保留各自空白目錄與原命名交易 | 重用既有隔離與命名，不新增全域改名器、去重器或跨 attempt 合併 |
| `verification-and-recovery.md:14,33`、範本 `terminal_observed_at` | N26-TOAST：AX、截圖、工具回傳、真人觀察分開；提示不替代穩定檔、verify／completion | 補來源／時間欄位，不加入新完成途徑、不為取提示重下；成本相稱 |
| Skill 工作流程第 3 步、`gui-inventory.md:63`–`67` B1 | N26-SPINNER／R3：載入就緒前不先建 PHOTO／VIDEO 身分，不以黑底或缺控制猜種類 | 在既有盤點加前置條件，沒有新狀態機／種類推斷器或計時修復 |
| `gui-inventory.md:54` 的已展開卡片→縮圖→viewer | N26-CARD：以實際畫面交叉覆蓋，不要求虛構詳情頁 | 允許既有畫面完成交叉核對，減少多餘導覽；身分與覆蓋保護保留 |
| `implementation-s3b.md:64`–`86` 的 C5／R1–R10 矩陣 | plan §7 C5：原 S1／S2 程式與測試、S3 文件及實機狀態分列 | 為交付證據對帳，未新增產品機制。來源候選、未重跑 targeted 命令與實機 NOT_RUN 清楚分開 |

`src/`、`tests/`、AGENTS、使用手冊及相簿 Skill 相對差異基準均無變更。S3a 的 CLI／bootstrap 不在本輪重審或重實作；未見 S3b 擴張事件、identity、鎖 allowlist、schema 或控制器。

## 阻塞性發現

### S3B-SIM-01：chooser 多加「目的地尚不存在」條件，與既有 intent 生命週期互斥

**位置與新增機制：**候選 `references/download-and-ledger.md:224` 的第 5 步新增：「只有 PathTextField、where／current directory 與 intent destination 能一致指向同一個尚不存在的新空白子目錄……才可確認」。這是下載控制已呼叫後、chooser 最終確認前的強制條件。

**需求／保護：**plan §5 N26-PANEL 需要三層觀察、精確空白目的地與可歸屬的單次確認；AGENTS 與既有交易要求 intent 先保存並讀回其新空白目的地。沒有要求在 chooser 階段讓該目錄不存在。必須保留獨立 staging、防覆寫、原 attempt 身分與 UNKNOWN 不重送。

**直接證據：**

1. 同一文件第 2 步（`:221`）規定 intent 保存新空白暫存目錄後讀回 destination；第 4 步先呼叫下載控制，第 5 步才處理 chooser。
2. 既有 `src/line_backup_batch/notes.py:2697`–`2700` 呼叫 `_new_unique_directory()` 並檢查空白；該 helper 在 `:404`–`413` 執行 `os.mkdir()`，回傳已存在的 canonical directory。`:2717`–`2725` 將此同一路徑及 device／inode 存入 intent 後回傳。
3. 既有 `_validate_staging()`（`:3256`–`3266`）要求目錄存在、不是 symlink，且 device／inode 與 intent 一致。刪除或重新建立目錄不是相容解法。
4. 本輪新增 C10（`evidence-decision-cases.md:88`）也明列「本次目的地應是該 intent 建立的新空白目錄」；範本要求三層一致，未要求目錄不存在。唯讀候選核對已確認上述字串與程式呼叫存在，無須建立真實或合成 intent 才能辨識矛盾。

**具體成本與影響：**遵照文件的 Agent 無法同時證明「與 intent destination 完全一致」及「該路徑尚不存在」。這額外狀態條件讓正常已建目錄也落入停止／待人工判讀；而此時一次下載控制可能已呼叫，不能靠第二次點擊、新目錄、新 intent 或改寫 UNKNOWN 恢復。這是可直接由生命週期證明的操作複雜度與流程阻斷，並非文字風格或行數偏好。未實測其 GUI 發生率，不聲稱已觀察到真實事故。

**最小安全簡化方向：**只移除 chooser 階段的「尚不存在」要求，明確沿用並核對本 attempt 的 intent 已建立、讀回且仍空白的原目錄；保留 PathTextField、panel current directory／where、intent destination 三層一致、來源／attempt 歸屬與最終確認至多一次。不要新增子目錄、改建目錄、改 CLI、資料／schema、覆寫或重送入口，也不要降低其他安全 gate。這是交人工決定的修正方向，**本角色沒有改任何產品文件或執行修補**。

## 非阻塞建議

`implementation-s3b.md:139` 的「A0……未完成前不得進正式 Acceptance」與 plan §7 的「A0／獨立 Acceptance」用語有歧義。下一次人工交接可明確區分「先啟動 A0 獨立本機相容驗證」與「最終 Acceptance／E2E 仍待適用外部 gate」，避免將 A0 本身也誤解為禁止啟動。這不構成另一個簡潔性 blocker，不要求新增角色、關卡或重開實作來整理用語。

## 實際檢查與證據界線

環境：上述 repo cwd；macOS 27.0.1（26A434）、arm64、`/usr/bin/python3` 3.9.6、Git 2.52.0。私有證據在 `.local/line-backup/tasks/20261102-notes-s3b-simplicity-implementation/`，含 `progress.md`、`reviewed.diff`、`review-checks.json` 與實際檢查腳本；不加入 Git。

| 本輪實際命令／檢查 | 結果與限制 |
|---|---|
| `pwd`、`git status --short`、`git branch --show-current`、`git rev-parse --show-toplevel`／`HEAD`、`git worktree list`、`git log` | exit 0；本機候選與分支相符、起始乾淨；保留其他 worktree |
| `git diff 72132263… b2cd3e1… -- .agents/skills/line-notes-agent-cua`、完整 diff／name-only、指定受保護路徑 `git diff --exit-code` | exit 0；直接審查實際交付，不以摘要推定 diff；受保護路徑無變更 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-s3b-simplicity-implementation/check_review.py` | exit 0；28/28 來源／hash／差異範圍／既有輸出核對成立。腳本未 import 或執行產品，不是功能測試；finding 的必要性判斷由主 Session 作出 |
| `git diff --check 72132263… b2cd3e1…`、`git diff --check` | exit 0；空白檢查，不是實機或功能接受 |
| `cat`／`rg`／`nl`／`sed` 讀取指定政策、角色範本、計畫、來源與程式 | 完成；repo 政策路徑不存在的 `rg` exit 2、`cat` exit 1，依現行 handoff 改讀既有 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 同版政策，未恢復 controller |
| `git ls-remote --heads origin refs/heads/feature/line-notes-media` | exit 128；HTTPS 443 連線失敗（75411 ms）。本輪無法獨立確認起始遠端實際 HEAD，不將前輪回報當成本輪量測；本機精確候選足以進行此次審查 |

一次工具呼叫在 dispatch 前中止，無命令執行；後續同一唯讀讀取成功。私有 progress 初次以 Python stdin 寫入因未宣告 UTF-8 而 SyntaxError、exit 1，未寫成檔；改用 apply_patch 完成。helper 初次定位不存在的 `implementation-s1.md` 為 `rg` exit 2，改讀實際 `implementation.md`。以上均屬工具／來源定位，不是產品拒絕或產品測試失敗。

本輪核對前輪指定保存輸出的 metadata、bytes 與 SHA-256：daily 為 73 tests／OK，notes 為 136 tests／OK，notes `--help` 為 exit 0，均由 **S3b Implementer 執行，本輪未重跑**。daily stderr SHA-256 `0a206c8a2b319e1b43dc0ecccb1880ec3278ce3cacc1a00c9cc9bfc855356330`；help stdout `bdc976599f5475df72d28f7d6da813d6183f205aef87053fd2138db7c9e0fa96`；notes stdout `67abaa53f75705a4b3222042d9da8903fb630a176ef60e39b3680c789ecfbf76`、stderr `2f36b89584333260dcd402878bef9d2a1128089946546c6abb8c7e942f99b9c9`。這些來源結果保留，不因本次文件 finding 而撤銷，也不能證明 chooser 文件可執行。

**事實：**指定候選、七檔範圍與已報來源 hash 相符；存在一項新增且互斥的目的地條件。C5 保留 S1 `423b00e`／S2 `8814d6d` 的來源，列明 targeted 命令未重跑；測試方法名能在現行 tests 找到，原 A0／G0／D1／D2／G1／G2 未獲豁免。

**推論：**移除該不存在條件並沿用既有 intent 目錄，是不擴張產品、能保留必要保護的最小方向；本報告沒有預先審查未交付的修正版。

**未知：**真實 chooser／PathTextField 的當次可讀範圍、原始 CUA envelope、幾何／焦點、獨立 AX 根因、影片／混合附件與跨 Session 能力仍缺證。沒有讀真實照片、帳本、active 或原始私人 GUI 證據，沒有新增真人 `OBSERVED`；`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 保留。

**本輪 NOT_RUN：**daily／notes 產品測試及 CLI／help、媒體解碼、A0、G0、D1／D2／G1／G2、真實 LINE GUI／popup／chooser／spinner／toast、影片／混合附件／Save All、完整真實盤點、跨 Session、獨立 Acceptance／E2E。審查產品唯讀，沒有為缺證重下或重跑同版回歸。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: S3B_IMPLEMENTATION_SIMPLICITY_REVISION_REQUIRED
IMPLEMENTATION_STATUS: S3B_DOCUMENTATION_DELIVERED; PRODUCT_UNCHANGED_THIS_ROLE
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: REVIEW_SOURCE_AND_ARTIFACT_CHECKS_PASSED; PRODUCT_AND_GUI_TESTS_NOT_RUN_THIS_ROLE
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_S3B_SIM01_AND_APPLICABLE_GATES
```

交由 Owner 決定如何處理 S3B-SIM-01，所需輸入是本報告、精確候選／diff、核定 plan／handoff 與 implementation-s3b。若授權另一正式主 Session 修正，保持文件小範圍與既有 staging 契約；修正版需哪些複核由 Owner 決定，本報告不涵蓋後續版本。A0 獨立相容與原外部 gate 依原範圍及授權另行處理，既有已證成果保留，不能以此審查取代最終接受或合併 master。

本 Session 不自行啟動修補、重測、Acceptance、GUI 或結案。完成報告後僅依 Owner 明示指示，使用 GPT-6 luna 子代理梳理提交訊息，逐檔 add／commit／正常 push 這份審查成果並讀回。model 請求、平台顯示與 provider usage 分層記錄，不主張未取得的後端身分、成本、token 節省或 OS 隔離；Git 交付的實際結果另存私有 delivery 紀錄並向 Owner 回報。
