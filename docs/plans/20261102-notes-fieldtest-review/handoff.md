# 現行交接：Owner 已採納，直接執行 S3a

## 給下一個 Implementer 的完整啟動 Prompt

你是本任務的 **S3a Implementer**。Owner 已明示：「我授權採納新增 CLI 與有界 S3 範圍，再啟動 S3a」。請直接完成下列離線首切片，不再詢問已取得的實作許可。這不是 GUI、真實帳本或 S3b 授權。先完整讀 AGENTS.md、你的 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md`、同版 workflow-routing／subagent-model-policy、本文件、[核定 plan.md](plan.md) 及 [計畫簡潔性審查](simplicity-plan-review.md)，再實作，不得只看摘要。repo 無 policies 時使用既有 `/Users/hsiaojohnny/.codex/policies/v4.9.0/`，不建立 controller。

### 精確版本、第一個動作與必讀脈絡

- Repo `/Users/hsiaojohnny/dev/Line_backup`；唯一開發分支 `feature/line-notes-media`。本次交接起始 HEAD `4bd709231cc240ca2de882e100081ad56fe8ddae`，工作樹乾淨。
- Owner 採納的是規劃提交 `75d4053332aa518a3e91e67b03dbd611e5efaf72` 的 plan（SHA-256 `d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`）。審查報告提交為上述 4bd7092，PASS 只限計畫簡潔性。
- 接手使用**包含本更新的 handoff 提交**；以 `git log -1 --format=%H -- docs/plans/20261102-notes-fieldtest-review/handoff.md` 取得並與 Owner 攜帶的精確提交核對。文件不預填自己的未來 SHA。核對 repo／branch／HEAD／worktree／Git status、plan hash 及審查版本，保留無關 dirty/untracked，不 reset/clean；版本衝突停止相依工作。
- 必讀 [原 replan](../20261101-notes-all-issues-replan/replan.md)、其現行 handoff、[S2 報告](../20261101-notes-all-issues-replan/implementation-s2.md)、[十項診斷](issue-analysis.md)、記事本 Skill 與五份 references。受測產品 `8814d6db0e0a7f368fa5b241fc5ab0010540ea63` 至本交接起始 HEAD 的 src/tests/Skill/AGENTS 無變更；開始前自行核對，不把報告提交當新產品。
- Planner 私有來源／補充：`.local/line-backup/tasks/20261102-notes-fieldtest-s3-plan/`；審查證據：`.local/line-backup/tasks/20261102-notes-fieldtest-simplicity-plan/`。僅按指定文件讀取，不廣搜私人資料。原始 GUI envelope、clock source、幾何與焦點仍未知；整理 JSON 不是真實工具 receipt。兩張照片的完成按歷史來源保留，不重下、不以成功解鎖別列表。

### 本次只完成 S3a

交付 plan §4 的 CLI/help、bootstrap、路徑與查詢文件，及 §7 C1–C4。S3b 的七項 GUI/B1 文件擴充與最終 C5/R1–R10 整合留待 Owner 後續交接；本輪報告須明列未完成項，不能稱整體修好。G0 欠件不阻擋獨立的 S3a 合成工作。

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


### 本切片可寫範圍

僅 `src/line_backup_batch/notes.py` 的上述 parser/dispatch/help；`tests/test_notes_records.py`、有實際缺口才改 `tests/test_notes_evidence.py`；記事本 Skill 入口摘要、`references/download-and-ledger.md`、`references/evidence-template.md`；手冊僅第5節必要 CLI/入口一致性；新增本目錄 `implementation-s3a.md`。不得因 plan 的完整白名單含 S3b 檔案就提前實作 S3b。

禁止改 identity/hash/schema/events/retry allowlist、notes_evidence.py/notes_capture.py 行為、v1 fixture、verifier、daily、Swift/OCR、相簿、AGENTS、全域政策、既有計畫與審查。不得讀寫真實 backup/、任何永久帳本或 active task，不操作 LINE、不建立真實 intent。測試在專案私有新任務區，所有 collection/photo/active hint 明確隔離；capture child 亦不可落入真實預設。

### 必做 C1–C4 與回歸

- **C1 key 等價與邊界：**同一 identity 的 list-key／init 結果一致；signals JSON 排版／object key 次序、omitted/null/{}、context 缺省／空白、有效 Unicode／前後空白、陣列次序及既有長度限制按現行函式結果；合法與拒絕輸入都不得另做正規化。缺參數／壞 JSON、空白 identity、非預期例外分別驗 2／4／70，成功 0；JSON 的 dispatch 始終 false。
- **C2 無資料副作用：**list-key 在無帳本時可算；以 mock 阻止 NotesCollection／NotesRecords 建構並核對隔離 collection／photo／active／lock／events 前後清單與 bytes。除指定 signals 輸入外無資料讀取；@FILE 與 init 同 strict JSON，碰到錯誤不自動補檔或重試。
- **C3 bootstrap／path：**先 list-key→兩份 v2 evidence→init→讀回 key 的合成鏈，明確隔離所有資料。正確絕對路徑成功；相對輸入／輸出、缺父目錄、symlink、逸出、collision、錯 context 仍拒絕。沿用既有覆蓋，只補實際缺口；錯 context 的 init 不建立帳本／照片，證據 pack 拒絕不產生有效 business event。
- **C4 query／文件一致：**合成 lists 回傳 records_root 供 summary 使用，未知 `--local-list-id` 仍 exit 2；對照 help、五份 reference、Skill／手冊及十 ID 矩陣。Owner 只需正式 Prompt，不填 key／JSON；完整範例無相對 evidence 路徑、舊座標、假原始 receipt 或未實作命令當成功。

審查非阻塞建議：C2 用同檔獨立小型 class，避免既有 setUp 先建帳；C1 可用 subTest；C3 沿用現有 context/symlink/collision/preflight drift 案例，只補缺口。這些不是額外接受條件，不造新框架或字串快照測試。

實作後必跑並保存 cwd、argv、版本、stdout/stderr、exit、hash：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

不預填測試數，不把舊 PASS 當本次結果；同版無變更/失效不重跑全套。需要 Swift SDK 時只選本程序相符既有版本，不改系統工具鏈。影片工具規範不變；本切片無真實媒體驗證。

### 驗收證據、Git 交付與停止

`implementation-s3a.md` 必含核定 plan/本handoff 精確版本、起始/候選身分與逐檔 diff、C1–C4→程式/案例/實際結果映射、資料隔離證據、相容與無副作用界線、源碼與輸出 hashes、六狀態、剩餘 S3b/A0/GUI 項及停止原因。合成 PASS 不等於 GUI/獨立 Acceptance；舊 S1 PASS 不涵蓋 S2/S3。

沿用 Owner 同範圍 commit/push 授權，逐檔 stage，私有證據不入 Git。commit body 填意圖、做了什麼、下一步的建議、驗證與結果；`git show -s --format=%B` 讀回，普通 push 後核對遠端完整 HEAD。不得 merge master、force-push、關 Issue 或改外部審查歷史；失敗記 COMMIT_OR_PUSH_BLOCKED。

首切片交付後停止，由 Owner 另啟 implementation Simplicity Review，即使首切片已是最終候選仍適用。不得自行啟動 S3b、Acceptance 或 G0/D1/D2/G1/G2。原 CRITICAL 相容/資料/實機 gate 保留；沒有新格式/資料授權。需超白名單、改公共既有參數/安全gate/資料語意、工具拒絕、來源漂移或寫入衝突時保存證據停止。同根因最多三次有證據嘗試，連續兩次無新資訊就停，不因換角色重置。缺原始 GUI 證據維持 UNKNOWN，不以右鍵/下載重現。

## 本次交接整理結果

本輪只依 Owner 決定更新 handoff，不實作。03_handoff_prompt 是人工交接檢查單，未據此派正式 handoff agent。下方舊 Planner 文稿原樣保留為歷史；其中「待採納／下一步計畫審查／僅兩文件可寫」及舊六狀態只描述當輪，現行入口以上文與本節為準。plan 原 bytes 與原審查不修改。

```text
PRIMARY_OUTCOME_STATUS: S3A_IMPLEMENTER_HANDOFF_READY
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: HANDOFF_DOCUMENT_CHECKS_PASSED; PRODUCT_AND_GUI_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_S3A_AND_REMAINING_VERIFICATION
```

實際 Git/文件核對與交付 receipt 保存 `.local/line-backup/tasks/20261102-notes-s3a-handoff/`。本輪產品測試/CLI/help、GUI、真實資料及獨立驗收 NOT_RUN。Owner 已採納/授權 S3a 是事實；未來實作能否通過仍未知。本輪完成交接與 Git 交付即停止。

---

# 原 Planner 交接（75d4053 歷史）

# S3 補充規劃交接與 Planner 報告

## 任務與精確版本

本輪角色為 Planner，Owner 指定 `01_plan_prompt.md` 並要求完成計畫後 add／commit／push。交付 [plan.md](plan.md) 草案：補既有 S3 的建帳前 key、絕對證據路徑、lists→summary、十項診斷與 G0 工作單。本輪不實作、不重測、不啟動下一正式角色、不提供產品 PASS。

- Repository／worktree：`/Users/hsiaojohnny/dev/Line_backup`，`feature/line-notes-media`。
- 起始 HEAD：`93815bfd5fb742dc0ac630fe3c807a3f3b2939c4`；起始 index／tracked／非忽略 untracked 乾淨，遠端精確 HEAD 相符。其他 worktree 保留。
- 受測產品／S2：`8814d6db0e0a7f368fa5b241fc5ab0010540ea63`；實機報告 `a985893178971b9ea39c50639a7ab0b468e8ff2b`；診斷為起始 HEAD。已核對產品／tests／Skill／AGENTS 在受測產品至本輪起始 HEAD 相同。
- 本版規劃以 **新增 plan.md 與 handoff.md 的共同提交** 綁定；提交後以 `git log -1 --format=%H -- docs/plans/20261102-notes-fieldtest-review/plan.md` 取得精確規劃 SHA，再讀 `git show <SHA>:<path>` 及重算 hash。不把起始 HEAD 當規劃提交，不在文件預填未來自己的 commit。
- 舊 [replan.md](../20261101-notes-all-issues-replan/replan.md) 及其 plan／handoff 不改寫；原 R1–R10、S1／S2 範圍、舊 waiver、審查與完成事實各保留原版本綁定。

## 本輪結果、事實與未知

**事實：**既有 list_identity／list_key 不需帳本，init 先核對計算結果的 evidence context；證據範本的相對 output 與程式矛盾；lists／summary 已區分 collection 與單帳本。計畫已規定 additive `list-key` 的輸入輸出、原樣 identity 語意、退出碼、無資料副作用、可寫路徑及 C1–C5 檢查。它目前只是待採納介面，尚未實作。

**事實來源限制：**Owner 在本輪補充 Agent 的唯讀說明，明確確認 input JSON／statements 是事後整理，原始 CUA invocation／return envelope 未保存。API 名稱、app-bound 範圍及圖像尺寸按該說明記錄；本 Planner 沒有重看私有圖像或觀察 LINE。兩張照片的歷史 completion／summary／audit 結果按診斷保留，不重算為本輪驗證。

**推論：**窄 CLI 可用既有 capture 保留相同解析路徑，足以補日常 bootstrap 缺口，無需改 context／hash／ledger。這是待人工審閱的設計判斷；原純函式文件入口是已評估的更小替代方案，並非不存在。

**未知／阻塞：**原始工具參數／handle／envelope、clock source、intent 真正起訖／焦點效果、capture crop／frame／point／scale、獨立 AX 結果與 GUI 各根因。約 09:13:20 來自檔名／mtime；整理 JSON 的毫秒時間也沒有 clock source，不能當原始平台時間。前後 titlebar／範圍差異使同像素座標不保證同實際點位。「AX 壞掉」「CUA 綁錯 subtree」「第一次右鍵被吞」「intent 隱藏工具列」均未定案。

原兩張照片成功不解鎖另一列表／舊 UNKNOWN，不代表影片、混合附件、Save All、跨 Session、外部副本或獨立 Acceptance。缺失的原始 receipt 不由新 G0 回填。本輪沒新增人眼 `OBSERVED`；既有 Agent／Owner 的觀察明確標來源。

## 實際工作、命令與證據

工作目錄為上述 repo，macOS，`/usr/bin/python3` 3.9.6。repo 沒有兩份指定 policy，讀取安裝根目錄 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 的 workflow-routing／subagent-model-policy 與同版角色模板；沒有恢復退役 controller。已讀指定 Planner Prompt、AGENTS、診斷、原 S3／S2、現行 Skill／五份 references 與相關源碼。

私有任務區 `.local/line-backup/tasks/20261102-notes-fieldtest-s3-plan/` 保存完整紀錄；原始 GUI、照片、真實帳本／active 未讀寫。

| 本輪實際檢查 | 結果／證據 |
|---|---|
| `git status --short --branch`、`git rev-parse --show-toplevel`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | 各 exit 0，分支／基線／乾淨狀態如上；`preflight-commands.json` |
| `git diff --exit-code 8814d6db0e0a7f368fa5b241fc5ab0010540ea63 HEAD -- src tests .agents/skills AGENTS.md` | exit 0；源碼／測試／Skill／指引無版本漂移 |
| `git ls-remote --heads origin refs/heads/feature/line-notes-media` | exit 0；起始遠端 HEAD 為 93815bfd 完整 SHA |
| `/usr/bin/python3 --version` | exit 0；Python 3.9.6 |
| 私有 Python 來源 manifest 與 preflight capture | exit 0；26 份來源記錄 bytes／SHA-256，沒有產品命令或真實資料存取 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-fieldtest-s3-plan/check_plan.py`：文件連結、十 ID／六狀態、引用 source hash、僅兩份新增文件、保護來源前後 bytes 及 `git diff --check` | exit 0，94 項文件／基線核對成立；`document-checks.json` 保存檢查與兩份文件 hash，不視為產品 PASS。交付前按最終文稿再核對 |
| 逐檔 stage／commit、`git show -s --format=%B`、普通 push、遠端精確 HEAD／工作樹 | 文稿完成後執行；實際輸出與 exit 留 `delivery-commands.json`，不預造 commit SHA 或 push 成功 |

探索性的 `rg` 含不存在 repo policies 目錄時 exit 2；檔案讀取亦確認記事本沒有 `verified-experience.md`，改按實際五份 references 讀取，沒有借用相簿流程。這些是文件定位結果，不是產品測試失敗。

一名同角色唯讀 helper 協助 CLI／path／identity 研究，未改檔、未執行產品測試、未接觸真實資料或簽發獨立接受；關鍵程式由主 Session 複核。未傳 model／effort override，未取得 provider usage；不宣稱後端型號、成本、節省或 OS 隔離。

**本輪 NOT_RUN：**daily／notes 產品測試與 CLI help、ImageIO 重解碼、G0、D1／D2／G1／G2、真實 GUI／chooser／popup、影片、混合附件、Save All、跨 Session、獨立相容／Plan Review／Acceptance。前輪測試數／PASS 只保留其來源候選，沒有移作本版通過。

## 下一個人工決定與執行邊界

建議 Owner 在另一正式主 Session 啟動本補充的 **計畫 Simplicity Review**，攜帶精確規劃提交與以下來源。首先核對是否採納新增公共純計算入口；本版建議 STANDARD，原總計畫 CRITICAL 的獨立相容／資料／實機要求仍有效。舊 P0 waiver 不自動涵蓋本補充，Planner／helper 不能自行批准或開始實作。

採納後，由 Owner 啟動 **S3a Implementer**，只執行 plan 第 4 節與 C1–C4，交精確候選及 implementation-s3a.md 後停止；Owner 再啟動 implementation Simplicity Review。S3b 的十項 GUI／B1 文件與 R1–R10 最終矩陣、最終回歸由 Owner 另決定續交；候選若已完整，直接交適用下個角色，不重開無必要實作。S2 尚缺獨立驗收，本規劃不能補簽或倒算為 S2 已承諾修完而失敗。

G0 是獨立外部工作單，**目前 BLOCKED／NOT_RUN**；另有指定 viewer／列表、明確只讀與最多一次必要移鼠範圍、有效前景及工具能力後才可執行。不得點中央／右鍵／下載、開 chooser、建 intent 或改帳。獨立 AX client 不存在、原始來源／映射／焦點不足就停止相依診斷，不安裝工具／換入口繞過。G0 成功仍不替 D1 舊 UNKNOWN 調和，也不授權 D2 真實更正或 G1／G2 下載。

必須傳遞：

- 本版 plan／handoff 及精確提交／diff；[issue-analysis.md](issue-analysis.md) 與本輪 Owner 轉交補充（私有備忘僅供本機，不發布原始資料）。
- 原 [replan.md](../20261101-notes-all-issues-replan/replan.md)、[plan 入口](../20261101-notes-all-issues-replan/plan.md)、[handoff](../20261101-notes-all-issues-replan/handoff.md)、[S2 報告](../20261101-notes-all-issues-replan/implementation-s2.md) 及 [S1 簡潔性審查](../20261101-notes-all-issues-replan/simplicity-implementation-review.md)，各自只在原版本有效。
- [實機報告](../../../验收纪录.md)、現行記事本 Skill／五份 references、notes 源碼與相關測試、plan 所列 source hashes；原 R1–R10／T1–T7 與 A0／G0／D1／D2／G1／G2 不可省略。

實作權限須由 Owner 採納本草案及啟動下一角色建立；本輪只授權規劃與 Git 交付。不得改舊事件／完成事實、安全 gate、既有 public flags、相簿／verifier 或真實資料；需擴白名單、遇拒絕／版本衝突／映射歧義或同根因嘗試上限即留證停止。每根因最多三次有新證據嘗試，連續兩次無新資訊就停，不以換角色重置。

Git 沿用 Owner 本輪 add／commit／push 授權；只 stage 本版兩份文件，commit body 填「意圖」「做了什麼」「下一步的建議」「驗證與結果」並讀回。push 後核對同分支遠端完整 SHA，不 force-push／merge master／改外部審查歷史。失敗記 `COMMIT_OR_PUSH_BLOCKED`，已證結果保留；Git 交付不等於獨立驗收。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PLANNING_SOURCE_AND_DOCUMENT_CHECKS_COMPLETED; PRODUCT_AND_GUI_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_HUMAN_REVIEW_AND_REMAINING_S3_VERIFICATION
```

規劃草案可交付；原產品阻塞與兩張照片已證結果同時保留。交接完成後本 Planner 停止，不自動修補、重測、派下一角色或結案。
