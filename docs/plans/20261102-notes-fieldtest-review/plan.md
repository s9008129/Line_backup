# 記事本照片實機診斷：S3 有界補充計畫

本輪為 Owner 以 `01_plan_prompt.md` 啟動的 Planner，只產出規劃與交接草案。本文補充既有 [replan.md](../20261101-notes-all-issues-replan/replan.md) 的 **S3 操作契約與整合**，不改寫原 R1–R10、S1／S2 報告、舊審查或完成事實。下一步見 [handoff.md](handoff.md)。本文不是實作、GUI 或真實資料操作授權。

## 1. 決策摘要

可觀察目標：Agent 能在建帳前取得與 `init` 完全一致的 list key，以正確的絕對路徑封裝證據，從全帳本查詢定位單帳本摘要；遇到本輪七項 GUI 現象時，能分清來源、定位、結果與未知，不以重點擊解決觀察不足。十個 N26 ID 都須有處置、證據與停止條件；原整體產品目標仍依 R1–R10 驗收。

建議最小方案：新增一個不接觸帳本的 `notes list-key` 純計算入口，重用既有 identity 解析及 hash；修正證據範本／操作文件，保留嚴格路徑與 context 驗證；補充既有 G0 的原始觀察、幾何及獨立 AX 對照工作單。**新 CLI 是明列的公共介面增量，須經 Owner 採納本版範圍後才可實作**，不由既有 S3 授權自動推定。

本補充分級 **STANDARD**：新增唯讀介面及操作文件，可能影響 Agent 的建帳／定位決策，需計畫與首個切片的 Simplicity Review。沒有新事件、格式遷移、種類更正或真實資料應用。原總計畫的 **CRITICAL** 分級、A0 獨立相容驗證及 D1／D2／G1／G2 門檻保持有效；原 P0 的 `WAIVED_BY_OWNER` 只屬舊版本，不當成本補充的批准或 PASS。若需要資料語意、事件或 gate 變更，停止並交 Owner 重定分級與適用審查。

替代方案與取捨：文件直接呼叫既有 `list_identity()`／`list_key()` 的 Python 小段程式，確實不用新增 CLI，並非無法先算 key；但日常 Agent 必須另維護內部 Python 呼叫、參數解析及 receipt 路徑。選擇窄的 CLI 可沿用 `init` 解析與既有 `notes_capture`，避免兩套操作入口。保留此較小替代方案供人工審閱；若 Owner 不採納新 CLI，由 Planner 另交文件方案，不讓 Implementer 自行變更公共介面。自動轉換相對路徑、建立 bundle 父目錄、改名 summary 參數、增加 GUI controller 或固定 sleep 均無必要證據，不納入。

非目標：重新下載兩張已完成照片、解鎖舊 UNKNOWN、推定 GUI 根因、恢復遺失原始 tool envelope、安裝觀察工具／改系統權限、新增任意 runner／sensor、改相簿流程、改 verifier、真實帳本更正、merge master、force-push、關閉 Issue 或簽發獨立驗收。

## 2. 基線、來源與事實界線

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；branch：`feature/line-notes-media`。
- 本輪起始 HEAD／已核對遠端 HEAD：`93815bfd5fb742dc0ac630fe3c807a3f3b2939c4`；index、tracked 及非忽略 untracked 均乾淨。其他 worktree 與所有既有私有資料保留。
- 受測產品／S2 候選：`8814d6db0e0a7f368fa5b241fc5ab0010540ea63`；實機報告提交：`a985893178971b9ea39c50639a7ab0b468e8ff2b`；診斷提交：上述起始 HEAD。已實跑兩版本間 `src tests .agents/skills AGENTS.md` 的 `git diff --exit-code`，exit 0。報告提交不當成另一產品版本。
- 主要依據：[十項診斷](issue-analysis.md)、[實機報告](../../../验收纪录.md)、[S2 報告](../20261101-notes-all-issues-replan/implementation-s2.md)、原 replan／現行 plan 入口／handoff、現行 notes 源碼與 Skill references。
- Owner 本輪另轉交 Agent 的私有證據唯讀補充，來源是本 Session 的使用者訊息；摘要與來源限制留在本輪私有任務區。它是 Agent 說明，**不是本 Planner 重新目視、原始 CUA receipt 或獨立驗收**。
- 私有任務區：`.local/line-backup/tasks/20261102-notes-fieldtest-s3-plan/`；保存 `progress.md`、`source-manifest.json`、`preflight-commands.json`、補充來源備忘及文件／Git 交付檢查。原實機與診斷私有目錄不改寫、不廣搜。
- 重要 SHA-256：診斷 `6a15ec440848f04f4af7ea8b4d83b92f0075477b0f39e7d3bb3c68c3ef8bb970`；`notes.py` `fd96ea763a42d15a13fcba0eff3e1672ce567c21a6b65f4659b387b664e21576`；`notes_evidence.py` `ee7e4f5f93d6a4a53204bd096545668e9285480fcfdfc2a618d77b6ca3e328e0`。原 replan 維持其既有 hash／版本綁定，完整來源 manifest 在私有區。

已證結果保留：既有保存輸出支持兩張照片 completion（sequence 16、24）、當次 `COMPLETED=2` 與 audit 完整性結果；本輪未重跑，也未確認目前檔案或外部副本。單次下載／chooser 的次數沿用當次報告與整理紀錄，不升格為原始 OS 送達證明。`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 保留。

新增來源限制：補充確認 `*-input.json` 是事後整理，`raw_tool_return="undefined"` 不是完整回傳。`getAXState()`／`getScreenshot()` 名稱與 app-bound LINE 範圍來自 statements；實際參數、handle、request/event ID、原始 envelope、呼叫時間與幾何未知。viewer 1280×960、列表 654×1286 pixels 亦按轉交說明記錄，未作本輪獨立量測。五份 AX 的 499 bytes 與同一 hash 是前輪核對結果；四圖不同及 titlebar 有無差異是補充的視覺說明。

**時序不得過度解讀：**補充將約 09:13:20 的 intent 時間限定為檔名／mtime，CLI 實際起訖未知；這比舊診斷時間表更受限，不能拿該值算精確間隔或因果。input／post-observation 的毫秒時間雖寫在整理 JSON，clock source 未保存。只保留「前一觀察可見、下一觀察不可見；兩次右鍵後結果不同」的報告順序。titlebar／capture 範圍不同且 `mapped_screen_point=UNKNOWN`，相同 screenshot pixel 值不證明同一實際點位。舊文件保留原貌，後續引用須附此限制。

## 3. 精確範圍與保護

**本 Planner 只可新增**本目錄 `plan.md`、`handoff.md`，及上述私有任務紀錄；不得修改既有 `issue-analysis.md`。依 Owner 明示授權逐檔 add／commit／正常 push。

待審、後續 Implementer 的完整白名單：

| 路徑 | 唯一允許用途 |
|---|---|
| `src/line_backup_batch/notes.py` | `list-key` parser／純計算 dispatch／相應 help；只補 evidence-pack 路徑 help，其他命令與儲存行為不變 |
| `tests/test_notes_records.py` | 純計算、與 init 一致、退出碼及無資料副作用的合成案例 |
| `tests/test_notes_evidence.py` | 既有測試缺口才補路徑與 bootstrap 合成整合；不刪安全斷言 |
| `.agents/skills/line-notes-agent-cua/SKILL.md` | 連結與入口摘要，不複製細節控制流程 |
| 同 Skill 的 `references/download-and-ledger.md` | CLI、bootstrap、capture、lists→summary 唯一操作說明 |
| 同 Skill 的 `references/evidence-template.md` | 絕對路徑例子、輸入／輸出前置條件、原始與整理來源分界 |
| 同 Skill 的 `references/gui-inventory.md`、`verification-and-recovery.md`、`evidence-decision-cases.md` | 七項 GUI 現象、B1 種類就緒、G0／幾何與結果判定；以連結避免多份交易流程 |
| `docs/LINE相簿備份_使用手冊.md` | 僅第 5 節記事本說明，保留唯一正式啟動 Prompt 與 Owner 無需填內部資料的責任邊界 |
| 本目錄後續 `implementation-s3a.md`、`implementation-s3b.md`、審查／驗收報告 | 新增各角色結果，不改本計畫迎合實作；原始輸出留各自私有任務區 |

禁止修改 `daily.py`、Swift decoder、OCR、相簿 Skill／測試、`media_verify.py`、`notes_evidence.py`／`notes_capture.py` 的行為、v1 fixture、任何 schema／identity 演算法／事件／retry allowlist、AGENTS／全域政策與舊任務文件。不得讀寫真實照片區、帳本、active 檔或操作 LINE；本計畫只描述日後另獲授權的 G0，沒有當次前景交接。

## 4. S3a：首個可驗證切片

### 4.1 建帳前 key 的明確入口

建議新增的介面如下，**目前尚不存在，不可當成已可執行命令**：

```text
notes list-key --visual-key TEXT [--context-id TEXT] [--signals JSON_OR_@FILE]
成功 JSON：identity、list_key、dispatch_authorized=false；exit 0
```

實作直接共用 `init` 的 `_json_cli_argument()` → `list_identity()` → `list_key()`（現行 `notes.py:120–154,4141–4152,4400–4404`），結果走既有 `_print_cli_result()`。可在同檔做相稱的小型共用解析，不新增模組／schema／cache。不得複製 hash 或新增正規化。

必要語意：visual key／context 的 strip 只用於非空檢查，實值前後空白與 Unicode 原樣保留，不做 NFC、大小寫或顯示目錄正規化。context 未提供為省略；空字串／全空白拒絕。signals 未提供與 JSON null 均省略；`{}` 是實際值，不能以真值判斷丟掉。JSON object 排序沿用 `encoded()`；不同 key 順序／排版不改 key，字串內容與陣列次序不能擅自等同。沿用 4096 字串與 256 KiB identity 限制、strict JSON 的 duplicate-key／非有限常數拒絕。

無 `--collection`、`--records-root`、photo destination 或 evidence 參數；不建構 `NotesCollection`／`NotesRecords`，不讀寫 index／active／lock／events／照片，不啟動子程序或 GUI。唯有明示 `@FILE` 按現有 signals 契約讀該指定輸入；不新增任意檔案政策。缺參數／JSON 語法錯 exit 2、identity 業務拒絕 exit 4、非預期例外 exit 70，沿用原 JSON／stderr 契約。沒有 flock，不加入 `READ_ONLY_COMMANDS` 的 busy/retry 分支。key 只證明輸入計算結果，不證明列表身分或可下載。

日常文件須給一個由 Agent 執行的完整鏈：先 lists／原記憶與當次列表核對 → 確認新列表且無歷史歧義 → 固定同一組 identity 輸入 → list-key → 兩份相同 list context 的 binding／history bundle → init 帶相同 identity → 讀回 key。Owner 不提供內部 key／JSON；不得為取得 key 先 init 空帳，或讓 context 適用 ID 留 UNKNOWN。若輸入或指定 signals 檔變動，舊 bundle 不可沿用；失敗先查副作用，不用重建帳本解鎖。合成整合能比對兩者 key，但不宣稱真實初始化具跨程序原子性。

### 4.2 證據路徑與帳本查詢

範本以確認 repo 根目錄後取得的實體絕對路徑作基底（例如 Agent 的 `TASK_PROJECT_ROOT`），使用正確 shell quoting／argv，所有 statement、asset、匯入 bundle、output 例子皆為絕對路徑。不可插入真實私人名稱或要求 Owner 手填 UUID。輸入為專案內 canonical regular file，無 symlink，讀取沿用單一 hard link 限制；輸出為私有 tasks 下尚不存在的子目錄，其 canonical 父目錄要先存在。Agent 只準備父目錄，不預建輸出子目錄，不自動 resolve 穿過 symlink、不覆寫。明列輸入相對路徑 `PROJECT_LOCAL_EVIDENCE_REQUIRED`、輸出相對路徑 `NEW_EVIDENCE_DIRECTORY_REQUIRED`、父目錄缺席 `EVIDENCE_OUTPUT_PARENT_REQUIRED` 的差別，不能把第一筆未知 argv 的歷史失敗硬歸因到 output。

用既有 `notes_capture --output-root ABS_PRIVATE_TASK_DIR -- <notes argv>` 保存一次 child 的 request、stdout／stderr、exit／signal 及程式身分；不新增 wrapper。capture receipt 與 CUA 原始回傳分開，前者不證明 GUI 輸入。拒絕和成功各保留新 receipt；wrapper 保存失敗即停止，不為補輸出重跑 child。

提供 `lists --collection ABS_COLLECTION` → 從其結果取得唯一相符 `records_root` → `summary --records-root ABS_LEDGER` 的完整例子。無相符帳本／多候選／壞歷史就停止，不靠名字猜路徑；不得把 collection 傳給 summary 或增加 `--local-list-id`。文件須修正「除 lists/init 外全部需 records-root」這類已不適用 evidence-pack／list-key 的概括，逐類說明即可，不改既有參數名。

## 5. 十項診斷到工作與成功證據

下表的文件路徑均指第 3 節記事本白名單；GUI 觀察仍須第 6 節外部授權，不在實作中補測。

| ID | 事實／未知界線 | 工作與負責人／滿足證據／停止條件 |
|---|---|---|
| N26-INIT | 純函式可先算 key；缺入口，非循環 | Implementer：S3a 的 notes／records tests／download-and-ledger。預算→bundle→init 的合成 key 完全相同，前置命令零帳本副作用；需改 hash／context 規則就停 |
| N26-PATH | 範本相對輸出與程式明確衝突；首筆失敗 argv 未知 | Implementer：evidence-template、操作 reference／help、必要 evidence tests。絕對輸入與父目錄條件明確，正例成功、反例仍拒絕；不放寬路徑政策 |
| N26-SUMMARY | CLI 已區分 collection／ledger；原錯用 stderr 未留 | Implementer：lists→回傳 records_root→summary 合成用例與文件；保留原 exit 2 語意，不能藉此重命名介面 |
| N26-AX | AX 五份相同、未呈現工具列變化；責任未知 | G0 執行者：同 viewer、CUA／獨立 AX 原始範圍對照。API scope、app/window role/children 與輸出來源可追；缺 client／綁定／原始來源即 UNKNOWN／BLOCKED |
| N26-TOOLBAR | 只有觀察順序；titlebar／capture 差異，實際點位及 CLI 時間未知 | Implementer 補 gui-inventory；G0 保存焦點、hover／輸入、幾何、等時長靜置對照。不得重播 intent 或右鍵，不能用舊點位／固定等待作修復 |
| N26-PANEL | Go to Folder 預填舊值不等於 panel current directory | Implementer：download-and-ledger／判定案例，分開 PathTextField、where/current directory、intent staging。既有 chooser 才可觀察；未能讀回精確空白目的地就不得確認 |
| N26-NAME | 報告同名／隱藏副檔名，命名來源未知 | Implementer：保留獨立空白 attempt 及檔案歸屬規則；不新增全域改名器或推定同媒體。G0 不為取命名資訊開 chooser；metadata 缺就未知 |
| N26-TOAST | AX 不含提示，截圖可見是原 Agent 說明；整理 false 的來源需釐清 | Implementer：verification／evidence-template 分開 screenshot／AX 與瞬態時間。G0 只查既有來源／現有提示，不觸發下載製造 toast；仍須同 attempt 終結＋穩定檔＋verify/completion |
| N26-SPINNER | 原 OBSERVED，無瞬態原圖 | Implementer：gui-inventory／B1，載入未就緒不定位或先建 PHOTO key；不用黑底、disabled slider、00:00 或沒看見影片控制斷定種類。無原件不補造、不為重現重新下載 |
| N26-CARD | 原 Agent 報告當次已展開卡片無獨立詳情頁 | Implementer：gui-inventory 容許已展開卡片→縮圖→viewer 連續交叉核對；不強迫點文字或創造詳情頁。來源／覆蓋不明保留待盤，不泛稱所有版本相同 |

## 6. G0 外部工作單：先有觀察能力，再談根因

**目前狀態 BLOCKED／NOT_RUN。** Owner 的補充已回答「來源是整理紀錄」及記錄的 API 名稱，不等於補到了原始 tool envelope。舊缺件無法靠新紀錄回填；新 G0 只支持新時段的能力／假說比較。不得把新能力推回舊點擊已送達或舊 UNKNOWN 已收斂。

前置：Owner 另行指定同一列表／已知 viewer，授權唯讀觀察與必要的單次 viewer 內移鼠，提供有效前景；核對沒有依賴未決派送而需改帳。本輪規劃沒有此授權。G0 執行者先讀當次 CUA 工具文件，核對「觀察」是否有啟動／聚焦等副作用；沒有證據不得假定只讀。只使用既有可用、經允許的獨立 AX client；不得為此安裝工具、改權限、讀 LINE 私有資料或建新 sensor。缺能力就記缺件交 Owner。

| 觀察步驟／owner | 原件與最低欄位 | 支持結論／停止條件 |
|---|---|---|
| G0-0 來源核對／G0 執行者 | Owner 轉交補充及指定歷史來源的 bytes/hash；若 Session export 有原始 CUA 呼叫，只讀指定段落，不廣搜 | 分開原始 invocation/return、保存 PNG/AX、整理 JSON、statement、OBSERVED；缺原始資料就列不可恢復，不偽造 receipt |
| G0-1 同 viewer 基線／G0 執行者 | 工具／API／版本、實際參數、app/window handle 或實際可得識別、request ID、原始 return/error、來源時間／精度；每份 screenshot/AX 的 bytes/hash、role/children／scope、焦點／游標 | 同一觀察窗須可證 app/viewer 歸屬；平台不提供的欄位逐項 UNKNOWN；不能用自編 ID 冒充平台 ID。缺足夠歸屬就停 |
| G0-2 幾何對照／G0 執行者 | screenshot pixels、raw/capture rect、window frame/points、scale、screen 映射、titlebar 是否涵蓋；工具支援的最小桌面區域與 app-bound 對照 | 映射要有來源，不能只由 1280×960 推比例；來源或視窗變化即失效，不輸入。桌面／popup 不涵蓋就 UNKNOWN |
| G0-3 獨立 AX 對照／G0 執行者 | 同 viewer／接近時間窗的既有獨立 AX client 工具版本、role/children/window 歸屬、原始輸出與可得時間；記 client 是否改焦點 | 可比較各來源是否暴露控制；缺少／不一致先列範圍與時序限制，不能定責 App、CUA 或快取。不啟動後台 LLM／另一控制通道 |
| G0-4 時序與就緒／G0 執行者 | 無 notes mutation 的有界靜置觀察，記起訖、焦點、hover、所有輸入與 capture 幾何；必要移鼠須在授權內最多一次且映射已知 | 相同條件無 intent 亦隱藏，可削弱「intent 專屬觸發」，不能證明其餘根因。不要執行 intent 當實驗、不右鍵、不改點位盲試；無新資訊按嘗試上限停止 |
| G0-5 現有 popup／chooser／G0 執行者 | 僅已存在且可歸屬的視窗，分開 PathTextField、where/current directory、檔名／副檔名及範圍；不輸入、不確認、不關閉 | 沒有現成 chooser／toast／spinner 就該項 NOT_RUN；不為研究觸發下載。若前景是出處不明的活動交易，先停止依賴它的工作 |

G0 的交付是來源對照表、能力／映射結論、可反駁假說與欠件，不是要求找到一個確定根因。無法取得原始回傳、可靠映射／焦點或獨立 AX 時，相關 GUI 根因診斷維持 BLOCKED；不能以「安全停住」宣稱全部修好。既有兩張照片不因補充來源限制而撤銷完成，也不重下補證。

## 7. 檢查、責任與人工停止點

所有產品測試只用專案私有任務區內的合成隔離 collection／photo root／active hint；先確認隔離，不帶日常預設真實資料。已有案例能證明就沿用，不新增文件字串快照或自製框架。

| 階段／owner | 成功證據 | 停止點 |
|---|---|---|
| 本計畫／Planner | plan＋handoff、來源 manifest、實際 Git／文件檢查 | 提交交接後停止，不自行派下一正式角色 |
| 本補充計畫 Simplicity Review／Owner 啟動 | 精確規劃提交，核對窄 CLI 是否值得、白名單及原 gate；審查報告 | Owner 決定採納公共增量與實作範圍；拒絕就停止，不由 Planner／helper 自評或自修跨角色問題 |
| **S3a 首切片**／Owner 啟動 Implementer | 第 4 節 CLI／help、bootstrap＋路徑／summary 文件及下列 C1–C4，交精確 candidate／diff／implementation-s3a.md | 交付後停止；由 Owner 啟動 implementation Simplicity Review，即使已是最終候選亦不免除 |
| S3b／Owner 決定續交 Implementer | 第 5 節 GUI／B1 文件、來源與案例一致性、原 R1–R10 整合矩陣、最終回歸與 implementation-s3b.md | 不執行 G0／D1／D2／G1／G2；若無剩餘實作，勿重開無必要 Implementer |
| A0／獨立 Acceptance，Owner 啟動 | 最終精確候選，原 T1–T6、v1 相容與事件／投影／資料預覽規則；本補充 C1–C4 | 舊 S1 PASS 不涵蓋 S2／S3。缺證據禁止 D2，沒有自動批准 |
| G0／另行指定執行者；D1／D2／G1／G2 依原計畫 | 第 6 節與原 gate 各自的授權、原件及結果；每項獨立記錄 | 不以 G0 成功代替 D1，不以列表 A 成功解鎖原列表；缺來源／能力／授權即保留 BLOCKED／NOT_RUN |

必要針對性檢查由 Implementer 先執行，Acceptance 獨立核對：

- **C1 key 等價與邊界：**同一 identity 的 list-key／init 結果一致；signals JSON 排版／object key 次序、omitted/null/{}、context 缺省／空白、有效 Unicode／前後空白、陣列次序及既有長度限制按現行函式結果；合法與拒絕輸入都不得另做正規化。缺參數／壞 JSON、空白 identity、非預期例外分別驗 2／4／70，成功 0；JSON 的 dispatch 始終 false。
- **C2 無資料副作用：**list-key 在無帳本時可算；以 mock 阻止 NotesCollection／NotesRecords 建構並核對隔離 collection／photo／active／lock／events 前後清單與 bytes。除指定 signals 輸入外無資料讀取；@FILE 與 init 同 strict JSON，碰到錯誤不自動補檔或重試。
- **C3 bootstrap／path：**先 list-key→兩份 v2 evidence→init→讀回 key 的合成鏈，明確隔離所有資料。正確絕對路徑成功；相對輸入／輸出、缺父目錄、symlink、逸出、collision、錯 context 仍拒絕。沿用既有覆蓋，只補實際缺口；錯 context 的 init 不建立帳本／照片，證據 pack 拒絕不產生有效 business event。
- **C4 query／文件一致：**合成 lists 回傳 records_root 供 summary 使用，未知 `--local-list-id` 仍 exit 2；對照 help、五份 reference、Skill／手冊及十 ID 矩陣。Owner 只需正式 Prompt，不填 key／JSON；完整範例無相對 evidence 路徑、舊座標、假原始 receipt 或未實作命令當成功。
- **C5 整合／Implementer：**R1 未解閉環、R2 能力、R3 種類／B1、R4 到期、R5 證據、R6 capture、R7 lock、R8 全盤點、R9 恢復掃描、R10 實機，各自指向原 S1／S2 程式／測試及 S3 文件／實機狀態。沿用前輪結果須標來源候選與「未重跑」，不把尚未取得證據的項目標 PASS。

有程式改動的 S3a 及 S3 最終候選按原計畫執行下列最小回歸，保存 cwd、實際 argv、環境／工具版本、stdout／stderr、exit 與 hashes。除變更、失敗或證據失效外，不重複跑同版全套；不預填測試數。文件切片以文件核對為主，最終原定回歸仍須交代：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

本 Planner 沒有執行上述產品命令；本輪只跑文件／來源／Git 核對。影片、混合附件、Save All、即時 popup、前景中斷、跨 Session、真實相容或獨立 Acceptance 均不能用離線案例替代；本輪一律 NOT_RUN。

## 8. 風險、回復與外部邊界

新 CLI 是 additive，既有參數、事件、key、完成事實及讀舊資料語意不得改變。純計算可在未寫新資料前回退程式／文件；不回滾、刪除或截斷真實 events，不改 completion，不以新目錄／新帳本／新入口清空 UNKNOWN。若新實作需要資料遷移，已超出本計畫。

CLI、capture、GUI 與外部 writer 沒有共同原子鎖。list-key 和 init 之間 signals／前景可能改變，固定輸入與讀回能檢出指定差異，不能保證全程無人改檔；身分／來源有變就停止，不能靠無限 recheck 承諾原子性。既有 flock 只約束合作程式。新觀察有時序差與可能聚焦副作用，不能保證同時快照、所有 popup 可見、exactly-once、服務端原始位元相同或 provider 身分／成本。

停止條件：來源／版本/hash 不符、審查拒絕、無新資訊連續兩次、同根因三次有證據嘗試上限、工具拒絕、前景／列表／映射歧義、寫入衝突或不明派送、原件異動、需改白名單／公共既有參數／安全 gate／資料語意。歷史嘗試不因換 Session／角色歸零；原記錄不完整就不宣稱剩餘額度。保存最小重現與已證結果交 Owner，不換控制通道、目的地或重試下載繞過。

## 9. 本輪交付狀態

本計畫已具體界定可執行的離線切片與外部工作單；缺原始 GUI trace 只阻擋依賴它的診斷／實機結果，不以推測補齊。本輪一名同角色唯讀 helper 核對 CLI／文件與 identity 語意，沒有產品寫入或接受權；主 Session 複核關鍵源碼。dispatch 沒有 model／effort override，未取得 provider usage，不主張後端型號、token 節省或成本。

實際命令、文件檢查與交付結果詳見 handoff／私有任務區；產品回歸、G0 及其他正式角色未執行。下一人工決定是啟動本補充的計畫 Simplicity Review，採納或退回新增唯讀 CLI 的有界方案，再決定 S3a；本 Planner 到此交接停止。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PLANNING_SOURCE_AND_DOCUMENT_CHECKS_COMPLETED; PRODUCT_AND_GUI_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_HUMAN_REVIEW_AND_REMAINING_S3_VERIFICATION
```
