# F01 實機驗證有界重規劃草案

## 決策摘要

本計畫依補充診斷建立下一次 F01 實機驗證的前提、必要證據與停止判準。**選定最小方案：沿用現有產品與操作規則，先解決來源／歷史關係，再由 Owner 決定是否另開獨立 Acceptance；目前沒有具體程式缺陷，不預定任何實作。** 本文件是草案，不是重測許可、產品 PASS 或新的 GUI 前景交接。

可觀察的規劃成果是：接手者能判斷哪一來源可測、每次輸入依據哪份最新 AX、何者算列表位移、何種證據足以支持底端、何時必須停止，以及哪些結果仍不足以 page／finish／下載。本 Planner 只交付文件，產品、真實帳本及 LINE 均不操作。

本切片分級 **STANDARD**：不改產品、公共介面或資料，可逆，但規劃會影響完整盤點與禁止重送的實機前提，不能當一般排版小修。保留人工啟動的計畫 Simplicity Review；若之後確實需要實作，Owner 須先核定具體差異及路徑，實作首切片再交人工啟動的 implementation Simplicity Review。既有主任務的 CRITICAL／獨立驗收／資料安全要求不因此降級。無實作時沒有可供 implementation review 的新候選，不製造空切片或重審同版產品。

非目標：修復原列表、繼續原捲動迴圈、處理 UNKNOWN／LOCAL_CHANGED、建立新帳來解鎖舊來源、重寫既有 scan 或 completion、驗證所有 F02–F18、下載驗收、跨 Session 恢復、相簿操作、CLI／schema／controller／sensor 改造。本輪不另找 High-Reasoning Reviewer。

## 基準、來源與寫入範圍

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- 起始 HEAD：`f64ba8dc5875fdb88f2e4ac5b9107896ed90cf87`；起始有前輪 `docs/plans/20261103-notes-f01-download-review/progress.md` 修改與 `issue-analysis-addendum.md` untracked。兩者未由本 Planner 修改或 stage。
- 唯讀核對期間外部工作將上述兩檔提交為 `7c71a3f1f3fc23eb0a745f09545f6b0a2d121b32`；本機及遠端均已在此版本、工作樹乾淨。本輪確認此提交僅含前輪兩檔，將它記為規劃基準，不改寫或重新包入本次提交。
- 精確產品候選仍為 `23e35798fe08f39eddd4b93372688ee2ed4e6edf`；前輪測試 HEAD 為 `5ae930d18a946ab448d4108a15b050d19c07e992`。本輪核對候選至規劃基準的 `src tests .agents AGENTS.md` 無差異；文件 HEAD 與產品候選不得混稱。
- 本輪僅可新增本目錄 `plan.md`、`handoff.md`、`progress.md`、`role-report.md`，及私有任務區 `.local/line-backup/tasks/20261103-notes-f01-field-validation-replan/` 的證據與 Git 訊息。原始證據不入 Git。
- 禁止修改：`src/`、`tests/`、Skill／references、手冊、AGENTS、既有計畫／報告、任何真實帳本、index、active task、照片／影片及目的地。不得使用 notes writer、GUI、下載、merge、force-push。本輪明示授權的普通 commit／push 僅交付上述規劃成果。

必要交接來源如下；精確 bytes／hash 見私有 `source-manifest.json`：

| 來源 | 用途與版本界線 |
|---|---|
| [補充診斷](../20261103-notes-f01-download-review/issue-analysis-addendum.md)；Owner 指定的私有同名原稿 | 最新結論為 PLANNER_REPLAN；私有原稿與公開版交付尾段不同，各自保留，不覆寫 |
| [原診斷](../20261103-notes-f01-download-review/issue-analysis.md)、[前輪驗收報告](../../../验收报告.md) | 保存舊判定；原始 receipt 缺口已由補充包解決，不沿用為新 blocker |
| `.local/line-backup/tasks/20261103-notes-acceptance-f01-download/` 的 acceptance／progress／完整 evidence | 舊帳本 blockers、保存圖片與 AX、原離線結果；不是當前 live 狀態 |
| `.local/line-backup/tasks/20261103-notes-f01-input-evidence/` 的 evidence-handoff／raw／SHA256SUMS | 32 次原始 calls／outputs、當時工具文件 ordinal 98、指定錯誤與來源映射 |
| [原 F01 計畫](../20261102-notes-f01-replan/plan.md)、[交接](../20261102-notes-f01-replan/handoff.md)、[實作](../20261102-notes-f01-replan/implementation.md)、[SIM-F01-01 重審](../20261102-notes-f01-replan/sim01-revision/simplicity-implementation-review.md) | 保留逐卡對帳、page 前／後時序、finish 原件重核；舊簡潔性 PASS 不等於本計畫接受 |
| [記事本 Skill](../../../.agents/skills/line-notes-agent-cua/SKILL.md)、[GUI 盤點本文](../../../.agents/skills/line-notes-agent-cua/references/gui-inventory.md) | 現行唯一操作規則，不在計畫再複製成第二套產品規格 |

repo 無 `policies/v4.9.0/`，本輪讀既有全域同版 workflow-routing、subagent-model-policy 及 plan／handoff／role-report 範本；不恢復退役框架、不寫全域證據。

## 已證實、推論與未知

**事實（重讀保存文字，不是本輪 GUI 重現）：**ordinal 338 的 AX 中 `8` 為捲軸、`10` 為最小化按鈕，345／359 卻使用 `scroll(10, "down", 1)`。這兩次不是有效捲軸探測，也不能證明實際最小化。409 等使用 `8` 仍無新位置；490／497 使用 `8` 能完成 184→0→184，因此舊索引不能充分解釋全部阻塞。504／520 無法獨立證明底端。`184` 的單位、最大值與全列表篇數仍未知。

**既有規則評估：**當時 ordinal 98 已要求每次動作後讀取 AX、依最新樹重取索引，screenshot-only 後先取完整樹；macOS 原生 scroll 使用 page count。現行 GUI 本文也已有前景／角色／焦點／映射、輸入後觀察、有效邊界、逐卡對帳及兩次無新資訊即停。已確認的 stale-index 問題屬執行未遵循規則；現有證據未指向 notes.py 缺陷，重複加相同規則不足以構成修復。

**推論：**現有規則足以定義下一次觀察應如何被接受或拒絕；把其證據需求具體落在本驗證方案，比先改程式更小且可核對。但規則存在不能證明 Agent 下次會遵守，也不代表當前工具一定能取得充分底端證據。

**未知：**原來源與哪一份歷史相符、完整篇數／媒體數、實際底端與載入狀態、媒體變化的因果、工具完整歷史版本、真實下載結果。本輪沒有重新讀 live 帳本、檔案或 LINE 畫面；舊保存摘要不冒充本輪驗證。

## 來源／歷史決策：先於任何實機輸入

Owner 需以自然語言釐清一件事：**下一次指定來源與前次備份歷史是何關係？** 可說明它是前次同一來源（可能改名／新增貼文）、已知另一個既有來源，或確實獨立的新測試來源；不要求手填 UUID、ledger ID 或 JSON。Owner 的來源說明仍須由接手 Agent 以當次連續入口、畫面／AX 脈絡、全部 notes 歷史及相符 evidence 交叉核對。僅改顯示名稱、目的地或帳本不能建立新來源。

| 核對結果 | 後續允許與限制 |
|---|---|
| 原來源對應已有 UNKNOWN／LOCAL_CHANGED 等 blocker | 不開始 F01 writer、下載或原方法探測。保留歷史，交 Owner 另定恢復／資料處置工作；這不在本計畫內 |
| 來源仍有歧義、歷史缺損或候選無法排除 | 停在唯讀查證，不 init／bind／scan，不把無精確 signature 當新列表 |
| 真正不同且可核對的獨立新測試來源 | Owner 可另行核定僅 F01 盤點的 Acceptance 範圍與有效前景；接手者按 Skill 自動處理內部身分及記錄，不用空帳繞過原來源歷史 |
| 其他已存在且無禁派送狀態的來源 | 須綁定它自己的歷史，並核對是否有活動 scan／attempt／命名交易；不因與本案不同就自動獲得實機授權 |

本計畫不選定哪一來源為事實。目的地未指定不是新 blocker：產品既有預設為 `backup/記事本/`。僅盤點的驗證不需要為了「隔離」另建照片目的地；新測試記錄若必要，仍使用正式 notes 流程，不手寫事件、不替換真實歷史。

## 有效觀察與底端證據

下述是現有規則在 F01 的驗證判準，尚未執行，也不改 CLI schema。後續需由 Owner 核定，不能被當作本輪新的產品規範或 GUI 許可。

### 每次操作的可核對最小紀錄

保存同一筆操作的事前原件引用、app／window／列表角色、焦點、最新 AX 來源及目標角色、受支援方法與單位、預期效果、原始 input receipt、事後 AX／截圖、卡片固定錨點及載入狀態。記可取得的時鐘／時間；缺失記 UNKNOWN，不以 mtime 補造。

索引不是常數：歷史 `8` 只說明當時正確角色，**新 Session 不照抄 `8` 或 `10`**。以當次工具文件及最新 AX 重新定位；screenshot-only 或視窗／角色／前景變動後，依工具文件重取完整樹。macOS 依當次文件使用 page count，小步後觀察；不猜 pixels、PageDown、setValue 數值或舊座標。若最小受支援步距仍失去 overlap，按現有補接規則處理；不得改用被拒絕的單位繞過。

| 判別 | 必要支持 | 不足以支持的結果與處置 |
|---|---|---|
| 有效列表位移 | 同一列表中可唯一連接的卡片邊界、作者列／日期／互動列等固定錨點相對 viewport 有方向一致的位移；保存共同卡片及次序，並與可用 AX 位置交叉核對。量測記座標空間與前後位置，差異須超過可辨識誤差 | API completed、PNG hash 不同、媒體播放／輪播變化、單一 AX 數字變化不能單獨成立；觀察不足記 UNKNOWN，不往下一頁推算 |
| 可靠頂端／底端 | 連續來源覆蓋接到首／末卡；當次原件可見對應卡片外緣及列表邊界／終止線索；沒有未解部分卡片、下一卡裁切或待載入線索；使用當次有效列表目標的小步向外探測後，同一卡片、順序與可靠外層位置仍相符 | 不把 `0`／`184` 當已知 min／max，不把空白區或相同 AX hash 單獨當邊界。需可指出獨立的邊界線索，例如可辨識的容器終點、端點上的捲軸 thumb 或明確結束標記；缺少時記 BOUNDARY_UNKNOWN，不補作「兩篇即全列表」 |
| 載入未定 | spinner、延遲新增、卡片骨架／內容未定、容器下緣被遮擋，或無法區分停止與載入 | 保留 LOADING_UNKNOWN；可在授權及原停止限制內取得一次針對缺失線索的無輸入觀察，固定等待秒數不能證明就緒。仍無新證據即停止，不無限輪詢／捲動 |
| 工具拒絕／失效映射 | 原始錯誤、not-active、unsupported unit、keyNotFound、目標角色不符或 input receipt 缺失 | 該次不計有效邊界探測；保存輸入與回傳，停止依賴該前提的後續操作，不以另一入口／按鍵／座標繞過 |

底端判定需要「有效輸入前提＋可辨識終止線索＋連續末卡／外層幾何穩定＋無未解載入」。同時符合才支持本次觀察範圍內已到底。若 AX 沒有 max 或 end marker，可使用保存圖片中的可靠外層邊界量測，不要求工具必須提供某個未存在欄位；但看不清容器終點、thumb 或其他可信終止線索時，不放寬成只看不動。真人另行確認只能記 OBSERVED，不能代簽工具 PASS 或豁免未取得的原件。

不要求媒體像素前後完全一致。影片／輪播可變，重點是卡片邊界、相鄰關係、列表角色與外層位置；媒體變化另記，無無輸入對照時不指定其因果。若需要這個對照，只作一次有明確問題的唯讀觀察，不為取得同張媒體畫面反覆輸入。

### F01 覆蓋仍依原產品門檻

可靠頂／底只是必要條件。每個 viewport 的完整及部分卡片先記來源台帳，再產生 rows；來源→rows、rows→來源、局部片段及跨頁有序 overlap 全成立才 `page`。成功後才讀回實際 key／事件，讀回相符才前進；不把未來讀回放進提交前 gate。finish 前重新讀原件邊界與全部 page 讀回，核對有序聯集、無漏卡／重複／來源變動，再決定能否 finish。

若原件有 A／B／C 三卡而 rows 只有 A／C，或非下載附件卡片被略去，即使頂／底成立也不得 page／finish。已提交頁發現漏登時保留原 scan，停止並交 Owner；不靠新 scan、evidence-correct 或改 key 補帳。此計畫不以底端新證據取代既有逐卡規則。

## 首個可驗證切片、檢查與責任

本版**沒有產品實作切片**。STANDARD 的首個可驗證工作是下表 F01-V1：Owner 核定來源及權限後，由另一個正式 Acceptance Session 核對入口、最新定位、可證位移與邊界；同一授權範圍若能持續成立，可繼續 F01-V2，不為每次可逆導覽另問。不能完成 V1 就停止，不自行修復或升級測試範圍。

| 檢查／owner | 必需輸入與可接受證據 | 停止／後續 |
|---|---|---|
| P0 文件與來源核對／本 Planner | 本輪 manifest、86 項補充清單與原 14／50 項清單重算相符、候選差異、UTF-8／連結／範圍及 diff 檢查 | 只支持規劃來源完整，不簽產品 PASS；Git 結果另報 |
| P1 計畫 Simplicity Review／Owner 另開主 Session | 本版精確提交、plan／handoff、補充診斷與原件；判斷是否沿用規則已足夠、底端判準可執行且未重置嘗試限制 | 本 Planner 不代簽。若有具體拒絕或範圍問題，報證據並停；不跨角色修訂 |
| F01-V0 來源與歷史 preflight／獨立 Acceptance | Owner 的來源關係說明、核定驗證範圍／有效前景、精確候選；依 Skill 循序查全部 notes 歷史、active hint、相符 memory 及必要交易細節，保留原始回傳 | 有任一未解來源、活動下載、UNKNOWN、命名交易或 LOCAL_CHANGED，停止依賴該前提的 writer／新派送；不把舊保存摘要當當次結果 |
| F01-V1 定位、位移及頂底／獨立 Acceptance | 當次工具文件／AX、每筆原始輸入及前後觀察、固定錨點／邊界量測、載入狀態、承接的嘗試歷史 | 按本節判別表得到可追溯結論；UNKNOWN 也是應停止的合法結果，不能算 F01 通過 |
| F01-V2 真實完整盤點／獨立 Acceptance | Owner 已明示允許新測試來源的 scan／page／finish 等盤點寫入；逐卡台帳、雙向對帳、page 輸入／讀回、頂底與 finish 原件重核 | 完整成立才可接受 F01 盤點；同數、簿記 COMPLETE 或文件檢查均不足。來源變動／已提交漏卡即停 |
| 新 GUI／下載／媒體驗證／跨 Session E2E | 本版不安排執行；若 Owner 之後要求下載，須另明示該範圍並保留現有 intent／outcome／reconcile／解碼 gates | 本輪及僅 F01 盤點結果一律不外推為下載或整體 E2E PASS |

後續若確有產品差異，必須先提出具體失敗鏈、現有規則不足之處、最小修改路徑、相容／資料風險及首切片檢查，由 Owner 決定重規劃與適用 Plan Review；本版不先授權改 Skill、notes.py 或 CLI。涉及程式變更時保留 AGENTS 所列三項最小回歸；純規劃本輪不跑，不能以重跑測試取代 GUI 證據。

## 嘗試、停止與可保證界線

原 32 calls 不是 32 次修復 attempt。345／359 使用錯誤目標，但歷史後續正確目標仍有無新資訊的重複，原捲動方法已停止；本計畫不分配新額度、不以新 Session、索引校正、新來源或新 ledger 宣稱根因歷史重置。原列表的 184 迴圈不得照舊續跑。

真正獨立的新來源是不同驗證樣本，不是重送原來源；接手者仍須承接相關工具拒絕與已知方法限制。每個有問題的觀察分支按既有規則最多三次有證據嘗試，連續兩次無新資訊即停止；這是上限，不是預訂的輸入數。首次工具拒絕、身分／映射不明、缺少原始 receipt、版本變更、前景中斷、來源變動或寫入衝突，就停止依賴該前提的動作。不能把「再捲一次應該能證明底端」當新資訊。

若要針對同一舊來源提出不同方法，必須先有能區分新命題的具體證據及 Owner 的範圍決定；不能只靠這份計畫、換目標或換 Session 恢復輸入。沒有可取得的終止／載入證據時，報 BOUNDARY_UNKNOWN／BLOCKED 並停，不增加工具控制器或要求廣搜 server log。

外部 LINE 貼文、前景、視窗、帳本或 Git writer 可在觀察間改變；只保證保存當次取得的原件及核對結果，不能保證原子快照、沒有服務端延遲內容、exactly-once、OS 隔離或外部副本。新變動使相關定位／覆蓋失效；不以無限重查承諾一致性。碰到提交路徑或基準 HEAD 在寫入期間變動時，保留差異並停止交付，不 reset／clean／覆寫來強造乾淨樹。

## 草案成功條件與下一個人工決定

規劃成功只表示來源、規則、正常／停止證據、責任人與授權邊界已可追溯；不是產品成功。Owner 的下一步是攜本版精確提交與私有 packet，決定是否啟動計畫 Simplicity Review，並確認可用來源及 F01 盤點寫入範圍。若審查認為現有方法足夠且來源前提成立，可另開獨立 Acceptance，無須先找 Implementer；若需產品變更，先核定有界實作計畫，不直接修復。本 Planner 交付與授權 Git 動作後停止。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_APPLICABLE_THIS_ROLE; NO_PRODUCT_CHANGE_PLANNED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PLAN_SOURCE_AND_DOCUMENT_CHECKS_ONLY; NEW_GUI_DOWNLOAD_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED; NO_NEW_ACCEPTANCE
TASK_CLOSURE_STATUS: BLOCKED
```
