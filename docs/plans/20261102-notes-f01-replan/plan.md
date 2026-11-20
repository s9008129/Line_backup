# F01 重規劃草案：來源卡片到貼文清單的覆蓋對帳

## 決策摘要

本計畫僅處理 [F01 診斷](../20261102-notes-f01-scan-review/issue-analysis.md)：舊 page 2 原件已含 P06，提交清單卻從 P05 跳到 P07，CLI 依清單內部一致性產生 `COMPLETE`。目標是在 Agent 提交 page 與 finish 前，讓每張來源卡片都有可追溯的清單對應；即使頂底與跨頁重疊成立，中間漏篇仍不得宣告完整或開始新派送。

**選定方案：先採 Skill／reference 的有界流程修正，沿用既有 statement＋v2 evidence-pack；不改 CLI、schema、key、事件、summary 或完成狀態語意。** 對帳表是 Agent 保存、供人核對的私有觀察紀錄，不是新 parser、機械驗證器或 GUI 權限。這是待審方案，尚未授權實作或證明能修復 F01。

分級為 **STANDARD**：此切片只變更觀察與提交前的操作方法，可逆且不觸及真實帳本或公共介面；但它守護下載前的完整盤點，因此不能當一般文字小修。計畫及首個可驗證切片各保留人工啟動的 Simplicity Review，最後另由獨立 Acceptance 核對 F01。原 replan 的 CRITICAL 相容／真實資料／GUI gates 全數保留；本分級不降級原任務。舊 S1 的特定免審不自動套用本次新計畫。Owner 若要求 CLI 機械拒絕新類缺口，須先重規劃新格式／相容邊界與適用 Plan Review。

非目標：F02–F18、M09 kind、`NO_MEDIA` 分類改造、文件／PDF／網頁文件下載、chooser／outcome、舊帳本更正、重掃修補原 inventory、下載、原 UNKNOWN 調和、其他列表、相簿或 controller。**只下載照片／影片**的既有決策保留；不下載的附件貼文仍須列入列表覆蓋，不能以資格過濾消除漏篇。

## 範圍、版本與來源

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；branch：`feature/line-notes-media`。
- 本輪起始 HEAD／核對遠端：`f427472335e611ca0efdd8b99011d87d7f7beaa9`；tracked、index、非忽略 untracked 乾淨。其他 worktree 與被忽略的真實資料保持原樣。
- 原實機受測產品：`260a49612cb3f7570a57f135921b4101e2c8ee99`。本輪核對它至起始 HEAD 的 `src tests .agents AGENTS.md` 無差異；起始 HEAD 是診斷文件提交，不是 F01 修復候選。
- 必讀：[測試報告 F01](../../../測試報告.md)、[F01 分析與 hashes](../20261102-notes-f01-scan-review/issue-analysis.md)、[原 replan D.4／T5](../20261101-notes-all-issues-replan/replan.md)、[原現行交接](../20261101-notes-all-issues-replan/handoff.md)、[S3 計畫](../20261102-notes-fieldtest-review/plan.md)及[交接](../20261102-notes-fieldtest-review/handoff.md)。舊報告只作來源，不把舊 PASS 移轉到本版。
- 實作依據：[記事本 Skill](../../../.agents/skills/line-notes-agent-cua/SKILL.md)、[GUI 盤點](../../../.agents/skills/line-notes-agent-cua/references/gui-inventory.md)、[證據範本](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md)、`notes.py` 的 `page()`／`finish_scan()` 與現有 overlap 測試。現行 CLI 不從畫面萃取必填卡片集合，evidence-pack 也不解析 statement 語意。
- 診斷私有來源定位沿用 `.local/line-backup/tasks/20261102-notes-f01-scan-review/source-manifest.json`；只有另獲適用唯讀授權的後續核對者可按需讀指定原件，不廣搜私人資料。本 Planner 未重讀私有截圖或真實帳本，P06 畫面結論引用前輪 `OBSERVED`，不是本輪目視結果。
- 本輪私有命令、來源 manifest、文件驗證及 Git 交付：`.local/line-backup/tasks/20261102-notes-f01-replan/`。公開只交去識別化的本目錄文件。

本 Planner 可寫本目錄 `plan.md`、`handoff.md`、`progress.md` 及上述私有任務區。未修改產品。

待 Owner 採納後，Implementer 的唯一產品白名單為：

1. `.agents/skills/line-notes-agent-cua/SKILL.md`：完整盤點摘要與提交前對帳入口。
2. `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`：下述逐卡、部分卡片與 finish 方法的唯一操作本文。
3. `.agents/skills/line-notes-agent-cua/references/evidence-template.md`：增補 page／finish 覆蓋紀錄範例，引用 GUI 本文，避免複製一整套規則。
4. 本任務目錄新增 `behavior-cases.md`、`implementation.md`；私有原始觀察及執行輸出留本任務新建的私有子目錄。

不改 `src/`、`tests/`、舊 fixture、手冊正式 Prompt、其他 references、相簿 Skill、AGENTS、全域政策、舊計畫／報告、任何 `backup*`／`notes-backup-records/`／active task。禁止手寫 business events、修改舊 `COMPLETE`、rekey、空帳、清除 UNKNOWN、新 attempt 或 GUI 輸入。若三份產品文件不足，具體列出原因與差異交 Owner，不能自行擴白名單。

## 來源→清單→完成的操作契約

### A. 先列來源卡片，後建立 page rows

每次小步移動後取得當次原件，先直接依畫面由上而下列出**所有可區分的完整及部分卡片**，尚不從預定 posts 清單回填來源。每張卡片記：觀察引用及可定位區域、完整／上段／中段／下段、可見邊界線索、前後卡片、已知對應或待解問題。局部代號只供同次對帳，不能當 post identity、跨 Session 認領鍵或要求 Owner 手填。

觀察編號與卡片區域只是定位索引；需引用原始截圖／AX 及連續相鄰脈絡。不能只寫「5 張、均已記錄」，也不以日期、總數、中文名稱或單一 hash 作同一卡片的證明。相同時間的兩個作者列／卡片邊界是兩個候選，必須各自核對，不因顯示時間相同合併。

部分卡片一律留在對帳紀錄，不能因不計新篇就消失。用小步補觀察，將同一卡片不同片段連到同一貼文；一張高卡片跨多個 viewport 時，需以內容延續、邊界與相鄰卡片證明，不能只用「畫面相似」拼接。直到能唯一對應該篇，才解除待解項；無法分辨是一張延續或新卡片就停止依賴此頁的提交。

### B. 限制 page 聚合並雙向核對

原則為一個已對帳 viewport 對應一個 page。若部分卡片須補接或高卡片跨畫面，允許**僅為解開該卡片而取得的連續補充 viewport** 共用一個 page：逐一列觀察順序、每個原件的全部卡片、片段連結及 page 有序聯集；不得把已越過多張新完整卡片的多次捲動事後彙成一個模糊 page。重複觀察可留在同一頁證據而不重複提交相同 page；既有 CLI 不允許的空頁／重複形狀不能靠假造新貼文規避。

Agent 先保存來源逐卡紀錄，再生成 CLI 支援的 rows；呼叫 `page` 前逐一對照原件做兩個方向的核對：

- 來源→rows：每張完整卡片與每個片段都有唯一貼文對應；待解數為零；每個來源新卡片出現在該 page rows，已見卡片依既有相鄰 overlap 表達。
- rows→來源：每個 row 都能回到至少一個本頁原件區域；不同卡片不被合併，同一卡片不因多個片段重複算新篇；順序與原畫面相符。

對帳紀錄最少包括：`觀察引用／卡片區域／完整或部分／前後脈絡／對應 identity 或 CLI post_key／所在 page row／待解與處置`。page 前尚無回傳 key 時以同一份固定 identity 對應；page 成功後將回傳 key 與事件讀回引用附到紀錄，不以 key 重新推導「原畫面必然齊全」。頁證據與實際 posts 輸入的對照留在同一 page 的 statement／assets；讀回如有差異即停，不以證據更正命令改寫 page 成員。

例：原件可區分 A、B、C 三卡，擬提交 `[A,C]`，即使 A／C 分別可接前後頁，B 的來源→row 對應缺失仍阻止 `page` 與 `scan finish`，不等最後總數才發現。B 若只有附件、沒有照片／影片，也不能被省略；本計畫不改其後續分類語意。

### C. finish 前以來源再次核對整條鏈

在最後一次補觀察完成後，Agent 直接重新讀本輪來源原件的卡片邊界，與已提交各 page 讀回 rows 逐頁核對。不是只重讀自己先前整理的清單，也不是固定重掃整份列表或比較兩次總數。

完成前必須同時成立：

1. 當次列表身分及入口連續；頂端／底端有原件與有效邊界觀察，保留既有小步確認法。
2. 每頁來源卡片與 rows 雙向對應，部分片段皆已解，頁內順序及跨頁尾→頭 overlap 成立。
3. 所有 page 的有序去重聯集與擬 finish 清單相同；每個 key 有來源，不漏卡、不重複計新篇。總數只是對帳結果，不是外部真實總數 oracle。
4. 無未解來源片段、缺頁、page 讀回差異、列表變動或身分歧義；完成 statement 指向逐頁證據及核對結果，而非只有「頂底成立，共 N 篇」。

任一條件失敗：不呼叫 finish、不宣稱完整、不開始新下載。CLI 若已有歷史 `COMPLETE`，仍不得用它取代當次視覺對帳；保持歷史不動，報出本次缺口。若發現本輪**已提交頁內漏登**，停在原 scan 與原證據，交 Owner 決定；既有 `evidence-correct` 不能補成員，禁止自行再建 scan 覆蓋錯誤。尚未提交的局部缺觀察可在有效任務／前景內小步補接，不需逐點請示。

### D. 來源變動與後續媒體 gate

任何已見卡片被新增、刪除、重排、編輯或原件／rows 無法唯一對應時，保留變動前後證據，將本輪覆蓋視為未成立並停止 finish／新派送。不得以剩餘卡片數相同、改 key 或自稱「已更新」掩蓋；是否需要合法新掃描，交依既有未決 attempt／scan gates 與 Owner 決策，這份計畫不新增重掃／解除 gate 能力。

列表卡片對帳完成後仍須通過原有逐篇媒體細盤、summary／intent blockers 與下載授權。照片／影片漏篇與非下載附件漏篇都阻止列表完整宣告；媒體類型和下載資格另判，不把附件卡片誤當照片或藉此改 `NO_MEDIA`。`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 的現行界線不變。

## 替代方案與可保證界線

| 方案 | 取捨與決定 |
|---|---|
| 固定兩次重掃、比總數或再加 overlap | 本例漏卡位於頁內；兩次都漏同篇仍可同數，不能建立來源覆蓋。不選為充分修復 |
| 逐卡對帳＋既有 evidence-pack | 直接對準已定位的轉錄缺口，無格式遷移，來源可供獨立者反查。選為本次最小候選，須經行為與實機驗證 |
| CLI 加 coverage 欄位／布林聲明 | 能查聲明內部一致性，仍可能同時漏寫卡片與 row；加一個自我聲明不足以證視覺完整，還會改介面／相容邊界。本版不選 |
| GUI sensor／OCR parser／總數 oracle | 需新的能力、準確性與授權研究；現無可靠來源保證。超出 F01 最小修正，不新增控制器 |

對帳能暴露**已可區分來源卡片卻無 row**的缺口，不能保證 Agent 同時看漏卡片與對帳紀錄時仍被工具自動擋住。CLI 仍可能接受自洽但不完整輸入；不得宣稱機械拒絕或零漏篇保證。若後續證據顯示此方案仍不能達到下面案例門檻，保留結果停止，由 Owner 決定是否擴成機械契約研究。

前後 GUI、來源列表、外部 writer、檔案與 CLI 沒有共同原子快照；無限 recheck 不能補足這點。保存範圍內的穩定觀察只能支持該時段的結論，不能保證無未觀察的服務端變化。現有 lock 只約束合作程式。不承諾 OS 隔離、原生 dispatch 保證、provider 身分或成本。純文件可經另一次正常提交恢復；不回滾事件／完成事實或照片。

## 首切片、檢查與責任

**F01-S1 首切片即最小最終候選**：三份白名單產品文件＋`behavior-cases.md`＋`implementation.md`。不拆出僅有口號的中間切片；Implementer 交付後停止，由 Owner 啟動 implementation Simplicity Review，即使已無剩餘工作仍適用。無需自造測試框架、字串快照測試或新增 Python 單元測試。

| 檢查／owner | 方式及成功證據 | 停止條件 |
|---|---|---|
| P1／Planner | Git 基線、來源 hashes、相對連結、白名單、六狀態、`git diff --check`；實際輸出留私有任務區 | 精確基線／必要證據不符則不能交可執行草案 |
| P2／Owner 啟動計畫 Simplicity Reviewer | 對本版精確 commit 核對最小方案、三文件範圍與 Agent／CLI 責任；提出報告 | 拒絕後本角色不自修／派另一角色 |
| V1／Implementer | 下表 C1–C7：保存來源、擬 rows、對帳、允許／停止判斷與理由；案例輸出引用區域與邊界，不能只寫預期結論 | 任一漏篇負例允許 finish／新派送，即失敗 |
| V2／Implementer | 直接 diff 核對無公共介面／events／歷史語意改動；三文件一致、連結與 UTF-8／空白檢查、`git diff --check` | 需要超白名單或更動 F02 等其他 finding 即停 |
| V3／Owner 啟動 implementation Simplicity Reviewer | 精確首切片、V1/V2 原件與報告；核對沒有用形式表格替代來源核對 | 有 finding／拒絕即交 Owner，不自行跨角色修復 |
| A1／獨立 Acceptance | 另從原件列卡後與候選 rows 比較；至少 C2/C3/C4/C7 不先看 Implementer 的對帳答案，報實際漏點與判斷 | helper／實作者不能簽獨立接受；證據不足維持 NOT_RUN／BLOCKED |
| G-F01／另行授權的實機執行者及獨立驗收者 | Owner 指定單一列表、有效前景、只盤點不下載的範圍；保存原始每步畫面、逐卡紀錄、page 輸入／讀回與 finish gate 判斷；原件可與 rows 逐張核對 | 無任務／資料寫入授權不啟用 CLI writer；無 GUI 授權不操作。未出現的情境 NOT_RUN，不虛造 |

G-F01 可先在 Owner 準備的測試列表與明確隔離的合成帳本執行，不接觸現有真實備份紀錄；若 Owner 指定真實帳本，必須另給精確追加範圍，原資料 gates 不豁免。不授權建立／修改 LINE 貼文來製造案例。GUI 階段只評 F01 盤點，不能順便下載或驗收其他 finding；既有完成項不重下。只有離線成功不足以聲稱 F01 真實流程已修復。

### C1–C7 行為案例與判準

| 案例 | 來源與輸入 | 可核對的預期行為 |
|---|---|---|
| C1 正常完整鏈 | 合成去識別畫面／示意卡片與完整 rows，頂底及跨頁重疊成立 | 全部卡片雙向對應、無待解；允許走到 finish 前條件成立；不是實際下載成功 |
| C2 同時刻相鄰卡片 | 合成兩張同時刻、不同邊界／內容卡片，其中一張只有非下載附件；rows 少一張 | 指出確切缺卡與區域，不因時間或資格合併；補入完整清單後才解除缺口，不改媒體分類 |
| C3 高卡片／部分邊界 | 合成一張跨三 viewport 高卡片，末端露出下一張作者列；一個版本完整連接，一個版本未解下一卡 | 前者只算一張高卡片並含下一篇；後者保留待解、禁止提交該頁／finish，不重複計片段 |
| C4 中段照片或影片漏篇 | 至少兩個負例：頁內照片篇／影片篇缺 row，但頂底、相鄰 overlap 和聯集內部一致 | 從來源發現漏卡，**不呼叫 page／finish、不開始 intent／下載**；補全未提交 rows 的正例可通過流程對帳。不是斷言 CLI 自動拒絕 |
| C5 缺重疊或錯認片段 | 合成相似外觀、缺共同尾頭或片段無法唯一連接 | 小步補接前保持未完成；不能猜 key／補假 row／靠總數放行 |
| C6 來源變動 | 合成插入／刪除或重排，總數也可能不變；原 rows 與新原件不符 | 保留前後來源、阻止 finish／新派送，不重寫舊 scan 或解除未決 attempt |
| C7 已知 F01 證據對照 | 使用診斷公開的 P04 P05 P07 P08 P09 與來源含 P06 的結構做去識別重建；原私有截圖重放須另有適用授權 | 定位 P05→P06→P07 的缺口；來源沒有 P06 的改變版不可亂補。重建標 SYNTHETIC，引用診斷不是本輪 GUI OBSERVED |

Implementer 的合成來源與執行輸出保留 hashes、實際步驟／命令／exit。案例是操作方法的行為演練，不把 Markdown 字串存在當 PASS。獨立 Acceptance 可用不同去識別卡片集及漏點，避免只會背 P06。缺少高卡片或同時刻情境的真實列表，只能報已測情境，其餘仍 NOT_RUN。

本文件候選沒有程式／測試改動，因此產品回歸不是本輪 Planner 的檢查；Implementer 的純文件切片以 V1/V2 為必需檢查，三項最小產品回歸標 NOT_RUN 並說明沒有程式改動。若 Owner 要將 F01 候選作整體產品發布／Acceptance，原計畫仍要求適用最小回歸，由 Owner 啟動的正式驗證者按精確候選執行，不以本文件豁免：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

## 人工檢查點、停止與交接

下一步是 Owner 攜本版精確規劃提交啟動**計畫 Simplicity Review**，決定採納流程候選或要求更強的機械契約。之後由 Owner 另啟動 Implementer → 首切片 Simplicity Review → 獨立 Acceptance／適用 G-F01；箭頭不構成自動派送或 GUI 授權。計畫 Review 如被 Owner 另行要求，也須獨立主 Session；Planner 不簽批准。

停止條件：版本／來源不符、審查拒絕、寫入衝突、列表／部分卡片歧義、已提交頁有缺口、前景失效、未決派送、工具拒絕、要改資料／事件／介面或擴入 F02–F18。依賴該前提的工作停止並交 Owner；可保留已完成的其他證據。同根因最多三次有證據嘗試，連續兩次無新資訊即停；原 F01 修復嘗試完整歷史 UNKNOWN，不能因換 Session 宣稱次數歸零或剩餘額度。

本角色止於草案與已授權的文件 commit／push。產品尚未修復，整體任務未結案。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: FIX_REQUIRED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

上述 REQUIRED_VERIFICATION 指產品／行為／GUI 必要驗證；本輪規劃來源與文件檢查另見 [progress.md](progress.md)，不能互相替代。
