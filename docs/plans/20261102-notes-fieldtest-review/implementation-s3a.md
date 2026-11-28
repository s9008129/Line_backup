# 記事本 S3a 首切片實作報告

## 角色、授權與精確版本

本輪依 Owner 已明示的「授權採納新增 CLI 與有界 S3 範圍，再啟動 S3a」，以
Implementer 身分只完成 plan 第 4 節與 C1–C4 的首個離線可驗證切片。這不是
S3b、GUI／G0、A0、正式 Acceptance 或結案授權。

- Repo：`/Users/hsiaojohnny/dev/Line_backup`
- Branch：`feature/line-notes-media`
- 起始本機／遠端 HEAD：`1cdb88bdff8a201173d2712ac827de6896181603`
- 核定 plan：`docs/plans/20261102-notes-fieldtest-review/plan.md`
  - 提交：`75d4053332aa518a3e91e67b03dbd611e5efaf72`
  - SHA-256：`d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`
- 現行 handoff：`docs/plans/20261102-notes-fieldtest-review/handoff.md`
  - 提交：`1cdb88bdff8a201173d2712ac827de6896181603`
  - SHA-256：`63fd3e530eee29688c14ede8f887dfc1a1b8b43ee1a2f85d3a66f208cf5c1ed8`
- 計畫簡潔性審查：`docs/plans/20261102-notes-fieldtest-review/simplicity-plan-review.md`
  - SHA-256：`8bafb851527ad9d54fe02eee366a9f4ea98a319117109c3894feb2e9cb0fc024`
- 受測產品基線：`8814d6db0e0a7f368fa5b241fc5ab0010540ea63`

接手時工作樹已有本切片預期的七個修改檔，沒有其他 tracked dirty 或非忽略
untracked 變更。未 reset、clean、切換 worktree 或碰觸其他 worktree。另核對
`8814d6db0e0a7f368fa5b241fc5ab0010540ea63..1cdb88bdff8a201173d2712ac827de6896181603`
在 `src tests .agents/skills AGENTS.md` 的差異為 exit 0；先前的計畫與交接沒有
偷帶產品改動。

## 候選身分與逐檔差異

本報告寫入前、尚未提交的產品／文件候選為：

- 基準 HEAD：`1cdb88bdff8a201173d2712ac827de6896181603`
- 七個 tracked 修改檔的完整 diff SHA-256：
  `576220d111140ce615f5214fe5bbc330157f8a74264c41e5c587a92a06db421b`
- 七個 tracked 修改檔合計：`551 insertions(+), 26 deletions(-)`

| 路徑 | +／− | SHA-256 |
|---|---:|---|
| `src/line_backup_batch/notes.py` | +30／−10 | `34ff6be9c6e9f74d2c450f3cc91aa8c6d1a0043cd0daef60f0680070b0e43247` |
| `tests/test_notes_records.py` | +334／−0 | `45d8804987a0798396f7cb3bf04bb0805ab0ee97ed7c7087e8b6f9f53e99d256` |
| `tests/test_notes_evidence.py` | +50／−0 | `fe11379d43373980243a8fcff1574b6efa79afbd536d9c25fe37610f6520afe3` |
| `.agents/skills/line-notes-agent-cua/SKILL.md` | +2／−2 | `417b374ca44d79c444f3a6c1ea6da6db99b918258862866794892710930955b2` |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | +87／−5 | `a7f071c6a08fb765826fd623e8c1a30295fe8e2e45f94782613e1ba9e098f736` |
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` | +27／−7 | `48ff722aa1e78bfc13a24db5b88dba1ee89e18f74ae5cd0dd8bec97195cb903f` |
| `docs/LINE相簿備份_使用手冊.md` | +21／−2 | `d1e01e86720350b659fa0a2840f9c387d427f17c65e29d799338371173b83f48` |

候選另新增本報告。完整候選 manifest（包含本報告自身 hash）保存在專案私有
證據區，不加入 Git。

## 實作內容

### `notes list-key`

- 新增 `notes list-key --visual-key TEXT [--context-id TEXT] [--signals JSON_OR_@FILE]`。
- `list-key` 與 `init` 共用同一個小型
  `_list_identity_cli()` → `_json_cli_argument()` → `list_identity()` 路徑。
- 成功結果由既有 `_print_cli_result()` 輸出，含 `identity`、`list_key` 與
  `dispatch_authorized=false`。
- 未複製 identity hash 或新增正規化、schema、cache、ledger、lock 或 retry。
- `list-key` 不建構 `NotesCollection`／`NotesRecords`，不讀寫 index、active、
  lock、events 或照片；只有明示 `--signals @FILE` 會讀該指定檔。
- `init` 的 identity 行為維持原樣，只改用同一個解析 helper。

### 證據路徑與查詢文件

- `evidence-pack` help 明列 absolute project-local statement／asset，以及
  位於私有 tasks 下、父目錄須已存在的新 absolute output。
- `init --signals` help 改為與現行行為一致的 strict JSON text／`@JSON-file`。
- 證據範本、下載與 ledger reference、Skill 與使用手冊加入：
  - 固定 identity → `list-key` → 兩份同 context v2 evidence → 同 identity
    `init` → `summary` 讀回 key → `bind` → `scan start`；
  - statement、asset、bundle 與 output 的絕對路徑前提；
  - `PROJECT_LOCAL_EVIDENCE_REQUIRED`、
    `NEW_EVIDENCE_DIRECTORY_REQUIRED`、`EVIDENCE_OUTPUT_PARENT_REQUIRED`
    三種不同拒絕；
  - `notes_capture` 僅保存單次 child 的輸出與程式身分，不是 GUI receipt；
  - `lists --collection` → 唯一相符列的 `records_root` → `summary
    --records-root`，並明確否定 `--local-list-id` 與以名稱猜目錄。
- 正式 Owner Prompt 與相簿章節未改；`gui-inventory.md`、
  `verification-and-recovery.md`、`evidence-decision-cases.md` 的 S3b／B1
  內容未改。

## C1–C4 對照

| 檢查 | 程式／案例 | 實際結果 |
|---|---|---|
| C1 key 等價與邊界 | `test_list_key_matches_init_and_readback`；`test_list_key_preserves_identity_json_semantics_and_boundaries` | PASS。list-key／init／summary 的 key 相同；JSON 排版與 object key 次序不變 key；omitted／null 相同、`{}` 不同；陣列次序、Unicode、前後空白保留；4096／4097 與 256 KiB 邊界成立；成功 0、語法錯 2、業務拒絕 4、非預期例外 70；成功、4 與 70 JSON 均為 `dispatch_authorized=false`，exit 2 不輸出 JSON。 |
| C2 無帳本副作用 | `NotesListKeyIsolationTests` 的兩個案例 | PASS。無帳本仍可計算；封鎖 `NotesCollection`／`NotesRecords`、active、lock、subprocess 與未指定檔案讀取後仍成功；隔離 collection、photo、active、lock、events 的前後目錄／bytes 快照相同。指定 `@FILE` 只讀一次；duplicate-key 壞檔 exit 2、不輸出 JSON、不重試、快照不變。 |
| C3 bootstrap／path | `test_list_key_matches_init_and_readback`、`test_relative_paths_missing_parent_and_hard_link_are_rejected`、既有 symlink／escape／collision／preflight drift 案例、`test_init_context_mismatch_has_no_collection_or_photo_side_effects`、`test_rejected_evidence_pack_does_not_append_business_event` | PASS。合成鏈完成 list-key→兩份 v2 evidence→init→summary key 讀回；絕對正例成功；相對 statement／asset、相對 output、缺父目錄、symlink、hard link、逸出與 collision 仍拒絕；錯 context 的 init 不建立 collection／photo；被拒 evidence-pack 不建立 output、不追加 business event。 |
| C4 query／文件一致 | `test_lists_records_root_feeds_summary_without_local_list_id_flag`、`test_cli_help_success_and_refusal_exit_codes`、文件契約檢查 | PASS（限 S3a 文件範圍）。合成 `lists` 的唯一列 `records_root` 可直接餵給 `summary`；未知 `--local-list-id` exit 2；root help 含 `list-key`；五份 reference、Skill、手冊與 plan 的十個 N26 ID 均核對存在，S3a 三項與 S3b 七項責任邊界已人工對照，無舊「除 lists/init 外全部 records-root」概括或相對 evidence 成功範例。S3b 的 GUI／B1 實作與實機現象仍 `NOT_RUN`。 |

## 資料隔離、相容與未變更界線

- 所有產品測試只使用專案私有 tasks 下的合成暫存目錄與合成 bundle；沒有讀寫
  真實 `backup/`、`backup-records/`、`notes-backup-records/`、
  `active-notes-task.json` 或既有照片。
- `list-key` 的 isolation 測試直接 mock fail closed 並比對整個隔離樹的目錄
  mode 與檔案 bytes；不是只比較回傳值。
- 未修改 identity 演算法、`line-notes-identity/v1` 或其他 schema、事件種類／
  格式、store／list／memory 投影、`READ_ONLY_COMMANDS` 或 retry allowlist。
- 未修改 `daily.py`、Swift decoder、OCR、相簿 Skill／測試、
  `media_verify.py`、`notes_evidence.py`、`notes_capture.py` 或 v1 fixture。
- 未操作 LINE、未呼叫 GUI／chooser／Save All，未下載、重送、改寫帳本或變更
  既有兩張照片的完成事實。

## 實際驗證與結果

環境：macOS 27.0.1（26A434）、arm64、`/usr/bin/python3` 3.9.6、
Git 2.52.0、cwd `/Users/hsiaojohnny/dev/Line_backup`。所有命令均帶
`PYTHONPATH=src`。完整 argv、時間、stdout／stderr、exit 與 hash 保存在
`.local/line-backup/tasks/20261102-notes-s3a-implementation/checks/`，該
私有證據目錄不加入 Git。

| 命令 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0；73 tests OK，耗時 319.539 秒；stderr SHA-256 `ee8bd7dd3160081c953693ffbe25b4137a200ad55ce89552c750630feba1e5af`。 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；stdout 2,410 bytes、SHA-256 `bdc976599f5475df72d28f7d6da813d6183f205aef87053fd2138db7c9e0fa96`；stderr 空。 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | exit 0；136 tests OK，耗時 13.780 秒；stdout SHA-256 `23a253cb23e81ab96ab53e37b7d14c2ad34476081b4a9014f3e0023e9b9c6ae4`，stderr SHA-256 `200295d0b63f512197e113efaf2d1b32994444e0c22fc26efdbeb12ca7bcc3b5`。 |
| `git diff --check` | exit 0；stdout／stderr 空。 |
| 私有文件契約檢查 | exit 0；五份 reference 存在、help／Skill／ledger／手冊含新契約、三種路徑錯誤存在、舊概括不存在、十個 N26 ID 均存在；stdout SHA-256 `4481f73c45eba7972104815783ec40b97185e676310f7bee35962c44cd8865a4`。 |

先前的針對性執行亦分別為 `test_notes_records.py` 22 tests OK 與
`test_notes_evidence.py` 15 tests OK；最終同版完整 notes 回歸再次涵蓋兩者並
全部通過。

## 未完成、未知與停止點

以下不因本切片 PASS 而完成：

- S3b 的七項 GUI／B1 文件擴充、C5／R1–R10 整合矩陣與最終回歸：`NOT_RUN`。
- A0 獨立相容驗證、implementation Simplicity Review 與正式 Acceptance：
  `NOT_RUN`。
- G0、D1、D2、G1、G2：`NOT_RUN`；沒有新的實際前景、來源或資料授權。
- 真實 LINE 記事本 GUI、即時 popup／chooser、混合附件、Save All、影片下載、
  跨 Session 恢復、前景中斷與真實 E2E：`NOT_RUN`。
- 外部副本、服務端原始位元、兩張既有照片的重新解碼或重新下載：未驗、未做。

`dispatch_authorized=false` 仍只是 CLI 欄位；合成測試 PASS 不是 GUI、資料、
服務端、E2E 或獨立 Acceptance。`external_copy_verified=false` 與
`real_line_e2e=NOT_TESTED` 不變。

本切片交付後停止。下一步由 Owner 另啟 **implementation Simplicity
Review**；不得由本 Implementer 自行啟動 S3b、G0、D1／D2／G1／G2、Acceptance、
merge master 或結案。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: S3A_CANDIDATE_READY
IMPLEMENTATION_STATUS: S3A_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: S3A_DAILY_NOTES_HELP_DIFF_AND_DOC_CONTRACT_CHECKS_PASSED; REAL_GUI_AND_INDEPENDENT_ACCEPTANCE_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_IMPLEMENTATION_SIMPLICITY_REVIEW_AND_REMAINING_S3B
```
