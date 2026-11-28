# 記事本 S3 有界補充：A0 獨立驗收

## 1. 決策、角色與授權

**A0 判定：`PASS`。**

本判定只涵蓋本機、離線、合成隔離資料上的 A0 相容與介面驗收。它不代表真實
LINE／GUI／chooser／popup／Save All／影片下載已通過，也不代表 G0、D1、D2、
G1、G2、T7、整份列表完成、外部副本已驗證、可合併 master 或可結案。

- 角色：Acceptance Reviewer（A0 獨立驗收者）。
- 授權來源：Owner 於本 Session 明示啟動 A0，並於完成後另行要求只提交驗收
  報告、commit 及 push。該後續交付要求不擴張 GUI、真實資料、產品修改、
  merge 或下一個正式角色授權。
- 驗收範圍：核定 `plan.md` §7 的 C1–C4、`replan.md` §7 的 T1–T6、v1
  frozen／golden 相容、追加式 event 順序、錯誤零有效 event、投影／summary／
  scan／completion／資料 preview，以及精確候選身分與來源一致性。
- 明確排除：未啟動 LINE、CUA、GUI、chooser、popup、Save All、任何下載
  控制；未執行 G0、D1、D2、G1、G2、T7；未操作真實 `backup/`、
  `backup-records/`、`notes-backup-records/`、active task、既有完成事實、
  真實照片或影片；未解鎖舊 `UNKNOWN`、重送、改寫 ledger 或建立 attempt。
- 唯讀邊界：本角色未修改產品程式、tests、plan、handoff、Skill、references、
  手冊、AGENTS 或既有報告；未修正 finding、降低 gate、自動重測或啟動下一個
  正式角色。本報告是唯一交付變更。
- 獨立性：本 Session 未參與本次候選的實作或修正，也沒有將候選工作交給
  helper 代為取得正式 Acceptance。所有補充檢查腳本均在私有任務區內新建，
  只讀取候選、執行合成 tests，沒有寫入候選產品路徑。

### 已讀取及核對的來源

已完整讀取 Owner 指定文件、現行記事本 Skill 與五份 references、`notes.py`
及相關 tests；下列為驗收來源與用途：

| 來源 | 用途 |
|---|---|
| `AGENTS.md`、v4.9.0 Acceptance Prompt、workflow routing、subagent policy | 角色、停止條件、證據與六狀態契約 |
| `docs/plans/20261102-notes-fieldtest-review/plan.md` | 核定 A0 範圍與 C1–C4 |
| `docs/plans/20261102-notes-fieldtest-review/handoff.md` | S3a／S3b 接續路由及歷史邊界 |
| `docs/plans/20261101-notes-all-issues-replan/replan.md` | 原 T1–T6、v1、gate 與停止條件 |
| `implementation-s3a.md`、`implementation-s3b.md`、`implementation-s3b-sim01-revision.md` | 實作範圍、已知限制與 S3B-SIM-01 修正 |
| `simplicity-plan-review.md`、`simplicity-implementation-review.md`、`s3b/simplicity-implementation-review.md`、`s3b/sim01-revision/simplicity-implementation-review.md` | 計畫／實作簡潔性審查背景；不作本次產品 PASS 的替代證據 |
| `issue-analysis.md` | N26／B1 診斷到需求映射 |
| `.agents/skills/line-notes-agent-cua/SKILL.md`、五份 references | CLI、GUI 操作契約與文件一致性 |
| `src/line_backup_batch/notes.py`、`tests/test_notes*.py`、`tests/fixtures/notes_v1/` | 精確候選行為、合成 tests 與 v1 frozen／golden 證據 |

舊 `docs/plans/20261101-notes-media-acceptance/acceptance.md` 只作背景；前輪
73／136 tests、舊 CLI 結果及舊照片完成結果都沒有升格成本候選的證據。本報告
只採用本次在 `af4abd85e1ae6e6e5a75d13925f39885e6838806` 上新取得的輸出。

## 2. 固定候選與身分穩定性

| 項目 | 本次觀察 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup` |
| Branch | `feature/line-notes-media` |
| 起始與測試後 HEAD | `af4abd85e1ae6e6e5a75d13925f39885e6838806` |
| 產品／文件基準 | `b6cfd68c3941dde9aca793d77265d6d1ba5eccf8` |
| 遠端 branch HEAD（起始核對） | `af4abd85e1ae6e6e5a75d13925f39885e6838806` |
| 起始 index／tracked diff／非忽略 untracked | 全部乾淨；`git diff --exit-code` exit 0 |
| `b6cfd68..af4abd8` 變更檔 | 僅 `docs/plans/20261102-notes-fieldtest-review/s3b/sim01-revision/simplicity-implementation-review.md` |
| Candidate diff SHA-256 | `b4371e1168c94d8ebfc9dc3f5c68a86c2fde02f0982a831cdef5f0989e66bb88` |
| Candidate 變更檔名清單 SHA-256 | `c0ddff1f04e7c0a2476a2988b324178c5545e25f2c6e1aacba4b3a5573ab0f47` |
| 核定 `plan.md` SHA-256 | `d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899` |
| 現行 `handoff.md` SHA-256 | `63fd3e530eee29688c14ede8f887dfc1a1b8b43ee1a2f85d3a66f208cf5c1ed8` |

測試前後重新核對 branch、HEAD、候選 diff 與工作樹；測試期間候選沒有變動。
報告寫入後只新增本文件，屬 **report-only addition**；候選 `af4abd8` 的產品、
tests、Skill 與 references bytes 沒有改變。後續交付的 report commit 是本候選
的子提交，不是新產品候選。

## 3. 環境、命令與原始證據

### 環境

- cwd：`/Users/hsiaojohnny/dev/Line_backup`
- macOS：27.0.1（Build 26A434，arm64）
- Python：`/usr/bin/python3` 3.9.6
- Git：2.52.0
- Homebrew `ffmpeg`：7.0；`ffprobe`：7.1.1
- 原始輸出與私有 fixture：`.local/line-backup/tasks/20261102-notes-a0-acceptance/`
- 所有合成 fixture、collection、photo root 與 active hint 都位於上述私有
  任務區；未預設載入日常真實帳本或照片。

### 計畫指定最小回歸

| 命令 | 結果 | 原始輸出／SHA-256 |
|---|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0；`Ran 73 tests in 319.397s`；`OK` | stdout 空檔 SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；stderr `4785ea8570c374421fa549a88917518e96eb0d008ede15735d1f53be2ecd8f94`；見 `checks/daily.*` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；列出全部現行命令與 0／2／4／70 契約 | stdout `bdc976599f5475df72d28f7d6da813d6183f205aef87053fd2138db7c9e0fa96`；stderr 空檔；見 `checks/help.*` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | exit 0；`Ran 136 tests in 13.442s`；`OK` | stdout `2c46702cf3d18d6e3324d9a934db2f56e07c27dd7ebdb253eef07e4d5ee8e7d4`；stderr `c85abeb04e0ba74669c61192c974c283cf0e8ed19926f2665d29ebb184d8b488`；見 `checks/notes.*` |
| `git diff --check` | exit 0；沒有輸出 | 空輸出 SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；見 `checks/git-diff-check.*` |

`test_notes*.py` 的 stderr 含一個預期的 `--signals` argparse 拒絕案例；該案由
test 明確驗證 exit 2，不代表 136 tests 失敗。daily tests 的 stderr 是正常的
unittest 進度與摘要。

### 獨立補充檢查

| 檢查 | 實際 argv／結果 | 原始輸出／SHA-256 |
|---|---|---|
| C1／C2 | `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-a0-acceptance/scripts/independent_c1_c2.py`；exit 0；`{"status":"PASS","c1_checks":21,"c2_checks":4,...}` | stdout `6c53196297f2674d88d88caddc02e6404f4d97d337080653661a3878cc104440`；stderr 空檔；見 `checks/c1-c2.*` |
| C3 | `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-a0-acceptance/scripts/independent_c3.py`；exit 0；合成 bootstrap 鏈與所有路徑拒絕為 `PASS` | stdout `9aa9c63b723dfceff43071e31afe57e4274c3c47bcdf3a81de0d1970f0960062`；stderr 空檔；見 `checks/c3.*` |
| C3 第一次檢查 | 同一腳本 exit 1；原因是自有檢查腳本誤以為 `init` 會寫 active hint，非產品失敗 | stderr `914efdc5e645a97c3dfc27ffaabddbc26af339b353946aed5a7d9b88be5d990f`；完整保留於 `checks/c3-attempt1.*` |
| T3 cross-scope／new-scan | `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-a0-acceptance/scripts/independent_t3_cross_scope.py`；最終 attempt exit 0；跨列表拒絕、零 event mutation、新 scan 保留 key／kind／source order | 最終 stdout `879f556118556810536250e05bcd16608490a22fd6bb1a2a42485d3880e8dba1`；見 `checks/t3-cross-scope-attempt2.*` |
| T3 第一次檢查 | 同一腳本 exit 0；保留為前一版檢查，不取代最終新 scan key 證據 | stdout `289f3f82c0aee5c4af1ea3c66c88020116ea6df1b91fb4e0a4db50af493e29a1`；見 `checks/t3-cross-scope-attempt1.*` |
| T4／T5 | `PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-a0-acceptance/scripts/independent_t4_t5.py`；exit 0；20 項中僅目標項 `EXPIRED`、其餘 19 項 `PENDING`；resume mismatch 與 pending-naming blocker 零 mutation | stdout `fe94d9f631ac4205f84b8f1a5fc078ea7aed6daecc012e0a3a9f1df2508d6fd8`；stderr 空檔；見 `checks/t4-t5.*` |

C3 第一次檢查的新資訊是「修正自有假設後才可正確判定 active hint 未被寫入」；
第二次在同候選重跑得到 `PASS`。這不是產品重試，也不是用改 session、換入口或
重寫 ledger 解鎖。

## 4. 需求證據矩陣

### C1 key 等價與邊界

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 候選行為與證據 | 判定 |
|---|---|---|
| `list-key` 與 `init` 對同一 identity 產生相同 key | `tests/test_notes_records.py::NotesListKeyCliTests::test_list_key_matches_init_and_readback`；獨立 C1 腳本亦以 init 讀回比對 | PASS |
| signals JSON 排版與 object key 次序不影響 key | `test_list_key_preserves_identity_json_semantics_and_boundaries`；獨立腳本比較壓縮／空白與重排 object keys | PASS |
| omitted、`null`、`{}` 保持不同語意 | 同上 test 與獨立 C1 檢查 | PASS |
| context 缺省、空白、有效 Unicode 與前後空白 | 同上 test；獨立腳本含有效 Unicode、前後空白、空字串與全空白拒絕 | PASS |
| 陣列次序保留，不自行排序 | 同上 test 與獨立 C1 檢查 | PASS |
| 現有 4096 字串與 256 KiB identity 限制 | `test_list_key_preserves...` 邊界案例 | PASS |
| 缺參數／壞 JSON／空白 identity／非預期例外為 2／4／70；成功為 0 | `test_list_key_preserves...`、`test_cli_help_success_and_refusal_exit_codes`、`test_cli_unexpected_exception_is_internal_error`；獨立腳本逐一觀察 exit code | PASS |
| 成功與拒絕 JSON 的 `dispatch_authorized` 始終為 false | `test_cli_help...`、`test_lists_records_root...`、`test_list_key...`；獨立 C1／C2 輸出 | PASS |
| 不額外做 NFC、大小寫、顯示目錄或自訂正規化 | 獨立腳本確認 NFC／NFD distinct、casefold distinct；源碼共用既有 `list_identity`／`list_key` 路徑 | PASS |

### C2 無資料副作用

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 候選行為與證據 | 判定 |
|---|---|---|
| 無帳本時仍可計算 list-key | `NotesListKeyIsolationTests::test_list_key_reads_no_files_or_constructs_ledgers_without_signals_file` | PASS |
| 不建構 `NotesCollection`／`NotesRecords`，不讀寫 index、active、lock、events 或照片 | 同一 test 使用 mock／隔離路徑阻止建構並核對不變；獨立 C2 快照前後 bytes 完全相同 | PASS |
| 除明示 `@FILE` 外不讀其他資料；`@FILE` 只讀指定檔一次且不重試 | `test_list_key_reads_only_the_named_signals_file_without_retry`；獨立輸出 `signals_file_reads=1` | PASS |
| `@FILE` 沿用 init 的 strict JSON，壞 JSON 不自動補檔或重試 | 同上 test 與 `test_list_key_preserves...`；stderr 保留 exit 2 證據 | PASS |
| collection／photo／active／lock／events 無未授權變動 | 隔離目錄前後清單及 bytes 比對；`isolation_snapshot_unchanged=true`、`private_paths_only=true` | PASS |

### C3 bootstrap 與 path

**結果：`PASS`（A0 合成範圍）。**

獨立 C3 腳本完成以下真實 CLI 合成鏈：

```text
list-key
  → 兩份相同 context 的 line-notes-evidence/v2 bundle
  → init
  → summary 讀回相同 list key
```

腳本輸出確認 `absolute_chain_success=true`、`active_hint_not_written=true`、
`invalid_bundle_no_side_effects=true`、`wrong_context_no_side_effects=true`，
且所有 collection、records、photos 與 evidence output 均位於私有 fixture root。

| 核定要求 | 候選行為與證據 | 判定 |
|---|---|---|
| 正確 absolute path 可完成 bootstrap | 獨立 C3 合成鏈；`tests/test_notes_evidence.py` 的 v2 bundle／init 測試 | PASS |
| relative input／output 拒絕 | `test_relative_paths_missing_parent_and_hard_link_are_rejected`；獨立 C3 分別觀察兩種拒絕 | PASS |
| 缺父目錄、symlink、逸出、collision 拒絕 | `test_parent_child_tamper_symlink_missing_and_escape_are_rejected`、`test_source_symlink_and_non_private_output_are_rejected`、`test_relative_paths...`；獨立 C3 全部確認拒絕 | PASS |
| 錯 context 的 init 不建立帳本或照片 | `test_init_context_mismatch_has_no_collection_or_photo_side_effects`；獨立 C3 比對副作用為零 | PASS |
| evidence pack 拒絕不產生有效 business event | `test_init_rejects_invalid_bundle_before_collection_or_photo_side_effects`、`test_rejected_evidence_pack_does_not_append_business_event` | PASS |

### C4 query、CLI 與文件一致

**結果：`PASS`（介面與文件契約；GUI 實機仍 `NOT_RUN`）。**

| 核定要求 | 候選行為與證據 | 判定 |
|---|---|---|
| `lists` 回傳 `records_root`，可直接供 `summary` | `test_lists_records_root_feeds_summary_without_local_list_id_flag`；合成 `lists` 的唯一列 `records_root` 直接餵給 `summary` | PASS |
| 未知 `--local-list-id` 仍 exit 2 | 同一 test 明確確認 | PASS |
| CLI help 與現行命令一致 | 本次 candidate `notes --help` exit 0；stdout 列出 `list-key`、`evidence-pack`、`evidence-audit`、`evidence-correct`、`media-kind-correct`、`source-unavailable` 等命令與退出碼 | PASS |
| 五份 references、`SKILL.md`、使用手冊一致 | 已逐份核對 `download-and-ledger.md`、`evidence-decision-cases.md`、`evidence-template.md`、`gui-inventory.md`、`verification-and-recovery.md`、`SKILL.md` 與手冊；bootstrap、絕對 evidence path、`lists → records_root → summary`、六類／`NO_MEDIA` 分界一致 | PASS |
| 完整範例沒有相對 evidence 成功例、舊座標、假原始 receipt，或把未實作命令寫成成功 | 文件核對未見上述情形；`download-and-ledger.md:5` 明示 branch 尚未經真實 GUI E2E；`evidence-template.md:29-37` 明示相對輸入／輸出／缺父目錄的拒絕；`gui-inventory.md` 不含舊座標重用承諾 | PASS |

十項 N26／B1 對照如下。表中的「文件契約 PASS」只表示本次候選的文字與介面
相符；N26-AX、TOOLBAR、PANEL、NAME、TOAST、SPINNER、CARD 與 B1 的真實 GUI
證據仍全部 `NOT_RUN`，不升格為實機 PASS。

| ID | 文件來源 | A0 可支持的命題 | 邊界 |
|---|---|---|---|
| `N26-INIT` | `SKILL.md:52`、`download-and-ledger.md` bootstrap 段、手冊 `:250` | `list-key → 兩份 v2 evidence → init → 讀回` 已有一致入口與 C1／C3 合成證據 | 真實新列表尚未實機驗證 |
| `N26-PATH` | `download-and-ledger.md:12`、`evidence-template.md:29-36` | absolute input／output、父目錄、symlink、逃逸與 collision 規則一致；正例及拒絕案例有測試 | 真實 GUI 證據路徑未操作 |
| `N26-SUMMARY` | `download-and-ledger.md:9-10`、手冊 `:254-267` | collection 與 ledger 分離；`lists.records_root → summary` 可行；未知 flag exit 2 | 真實唯一列選取仍待實機 |
| `N26-AX` | `gui-inventory.md:82-90`、`evidence-template.md:46` | AX／CUA client、API scope、app/window、role/children、raw return 分層及 `UNKNOWN` 邊界一致 | 無原始 AX／CUA receipt；G0 `NOT_RUN` |
| `N26-TOOLBAR` | `gui-inventory.md:76` | 不以 intent 前後順序推定因果；比較欄位與停止規則一致 | 真實焦點／hover／幾何對照 `NOT_RUN` |
| `N26-PANEL` | `download-and-ledger.md:224`、`evidence-template.md:50` | PathTextField、panel current directory／where、intent staging 三層分開；最多一次確認規則一致 | 真實 chooser 三層讀回 `NOT_RUN` |
| `N26-NAME` | `download-and-ledger.md:223`、`verification-and-recovery.md:97-99`、`evidence-template.md:158-160` | 不新增全域改名器；basename／hash／順序不能單獨認領媒體或 attempt | 真實同名／隱藏副檔名案例 `NOT_RUN` |
| `N26-TOAST` | `verification-and-recovery.md` 證據矩陣、`evidence-template.md:51、164-165` | 截圖／AX／input receipt／原始工具回傳／真人觀察分層；終結提示不替代驗證與 completion | 真實 popup／toast 原始來源 `NOT_RUN` |
| `N26-SPINNER` | `gui-inventory.md:63-67`、`SKILL.md:54` | spinner、黑底、disabled slider、`00:00` 或缺控制不判種類；未就緒不定種類、不定位下載 | 真實瞬態 `NOT_RUN` |
| `N26-CARD` | `gui-inventory.md:53-61` | 允許當次已展開卡片直接以「卡片 → 縮圖 → viewer」交叉，不虛構詳情頁 | 真實卡片／版本差異 `NOT_RUN` |
| `B1` | `gui-inventory.md:63-67`、`SKILL.md:54` | 要求正面就緒與種類特徵，無固定 sleep 或黑底推斷 | 真實 viewer 就緒與種類判定 `NOT_RUN` |

### T1 evidence、event 與 v1 相容

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| v1 frozen 資料的新 reader 投影不變；不自動升級 bytes | `tests/test_notes_evidence.py::NotesV1CompatibilityTests::test_frozen_v1_projection_and_bytes_do_not_upgrade`；v1 golden fixture | PASS |
| 完整 v2 重開後原 `source_path` 移走仍可讀 | `NotesEvidenceTests::test_v2_reopens_after_sources_move_and_keeps_parent_bytes` | PASS |
| 父／子缺件、錯 hash、symlink、逃逸、duplicate JSON key、不支援版本、context 衝突拒絕 | `test_parent_child_tamper_symlink_missing_and_escape_are_rejected`、`test_duplicate_json_version_and_context_are_rejected`、`test_source_symlink_and_non_private_output_are_rejected` | PASS |
| init 已知無效 bundle 在建立資料前拒絕；鎖內漂移再查 | `test_init_rejects_invalid_bundle_before_collection_or_photo_side_effects`、`test_init_rejects_bundle_changed_after_preflight_without_event` | PASS |
| 寫入失敗零有效 event，明列中斷產物保留 | `test_preserve_failure_keeps_interrupted_blobs_and_no_event`、`test_published_blob_is_retained_when_post_link_sync_fails` | PASS |
| 已保存子檔漂移時 load 拒絕 | `test_parent_child_tamper...` 的 `child_drift` 案例 | PASS |
| legacy 不自動升格；新 writer 拒絕 opaque legacy 且無副作用 | `test_new_writer_rejects_frozen_opaque_evidence_without_side_effects`；legacy 保持唯讀 | PASS |
| page correction 原 hash／鏈錯拒絕；正確更正不變 page／scan 語意 | `test_evidence_correction_appends_only_to_exact_target_and_chain`、`test_evidence_correction_scopes_to_target_page_and_scan` | PASS |
| audit 能列引用漂移且 exit 4，不把被拒絕的 summary 當可信投影 | `test_evidence_audit_reports_outer_drift_and_refuses_projection`、`test_evidence_audit_reports_child_missing_and_symlink_drift`、`test_evidence_audit_stops_on_malformed_structural_ref` | PASS |
| 錯誤不追加有效事實；completion 不被測試或錯誤資料改寫 | 上述保留／零 event 案例、`test_completion_manifest_readback_and_immutability`、rejected outcome／completion 測試 | PASS |

### T2 capture

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| 相同命令兩次各建立新 receipt／目錄，child 正常執行一次 | `tests/test_notes_capture.py::test_request_precedes_one_child_and_each_capture_uses_new_receipt` | PASS |
| refusal → success 原兩份 receipt 都保留 | `test_refusal_then_success_keeps_both_receipts` | PASS |
| 完整保存 exit 0／2／4／70 與 signal | `test_real_fixed_child_help_records_execution_contract_and_succeeds`、`test_child_exits_70_and_signal_are_preserved_exactly`；既有 CLI 契約 tests | PASS |
| child=0 但 receipt 磁碟失敗時 wrapper=70、child_exit=0、child 只執行一次 | `test_child_zero_then_post_child_persistence_failure_is_wrapper_70` | PASS |
| 中斷不能自動重執行 | `test_child_launch_failure_is_wrapper_70_without_retry`、`test_program_drift_after_child_is_incomplete_without_reexecution` | PASS |
| receipt 目錄／檔名 collision 或 symlink 在 child 前拒絕，child 次數 0 | `test_receipt_and_request_name_collisions_are_rejected_before_child`、`test_unsafe_output_roots_are_rejected_before_child`、`test_receipt_symlink_is_rejected_before_child` | PASS |
| wrapper 保存失敗停止，不以重跑補輸出 | 上述 wrapper 70／程式漂移案例明確禁止自動重執行 | PASS |

### T3 media kind

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| 19 項合成更正總數／key／source_order 不變；更正後 v2 attempt 重開 | `tests/test_notes_regressions.py::test_media_kind_correction_preserves_nineteen_items_and_v2_attempt` | PASS |
| cross-list／post、stale scan／inventory hash、歧義拒絕 | `test_media_kind_correction_rejects_scope_hash_and_stale_scan`；獨立 T3 腳本跨列表拒絕 `MEDIA_KIND_SCOPE_CHANGED` 且零 mutation | PASS |
| attempt 後或完成後更正零追加 | `test_media_kind_correction_rejects_after_attempt_or_completion` | PASS |
| v2 intent／verification 使用 VIDEO 驗證器 | 同一 kind correction test 與 `tests/test_notes_e2e_media.py` 的 production verifier 測試 | PASS |
| 重開／新 scan 沿原 key、kind、source order | 獨立 T3 最終腳本 `new_scan_preserves_effective_kind=true`、`new_scan_preserves_keys=true`、`new_scan_preserves_source_order=true` | PASS |
| 合法 v1 intent／completion 保持原行為；更正後偽造 v1 intent／錯序 load 拒絕 | `test_v1_intent_compatibility_and_forged_post_correction_order` | PASS |

### T4 source expiry

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| STOPPED 加單項到期事件維持 `PREVIOUSLY_INCOMPLETE`，且禁該項 recovery | `test_source_unavailable_preserves_incomplete_without_recovery`；獨立 T4 顯示 20 項中僅 1 項 `EXPIRED`、其餘 19 項 `PENDING`，六類計數不變 | PASS |
| 重複標記、偽造到期後 intent／recovery 在 load 拒絕 | `test_source_unavailable_rejects_unknown_and_forged_recovery`；獨立腳本確認無 recovery／intent 追加 | PASS |
| 無資料不能推另 19 項到期 | 獨立 T4 檢查 `t4_other_items_pending=true`、`t4_target_only_expired=true` | PASS |
| `UNKNOWN` 不可用 `source-unavailable` 終結 | `test_source_unavailable_rejects_unknown_and_forged_recovery` | PASS |
| 舊 STOPPED 提示 `REVIEW_REQUIRED` 且不自動重送 | 同一 regression 與 summary／blocker 投影 | PASS |
| 未授權排除不改 `EXCLUDED`／`COMPLETED` 計數 | 獨立 T4 `t4_counts_preserved=true`；既有排除授權 tests | PASS |

### T5 coverage、scan 與 resume

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| summary 與 intent 對全部細盤缺口一致 | `test_summary_blocks_detail_pending_even_when_known_media_complete`、`test_summary_blocks_media_count_coverage_mismatch`、`test_start_scan_and_intent_share_coverage_gate` | PASS |
| `NO_MEDIA` 正確且不計下載完成 | `test_no_media_post_is_indexed_without_media_attempt`、`test_start_scan_and_intent_share_coverage_gate` 的 NO_MEDIA 分支 | PASS |
| `UNKNOWN`／無 outcome／`VERIFY_REQUIRED`／pending naming 禁止新 scan | `test_start_scan_blocks_unresolved_attempts_and_verify_required`、`test_start_scan_blocks_pending_naming_transaction`；獨立 T5 blocker 零 mutation | PASS |
| 原 scan 仍可正常調和與 verify | `NotesRecordsTests::test_unknown_is_blocked_until_reconcile` 及 regression 的 reconcile／verify 案例 | PASS |
| 舊跨 scan UNKNOWN 保護案例保留為 legacy fixture，不靠新 writer 製造舊 bug，也不刪測試 | `test_summary_blocks_unknown_attempt_outside_latest_scan`（`tests/test_notes_regressions.py:774`）保留；該案例先經正常 public gate 建資料，再由 test helper 直接改為 legacy `UNKNOWN`，其 `append_historical_scan()` 亦直接構造 legacy graph。這是合成 legacy fixture，不是 public writer 產生舊 bug，也不是產品歷史資料 | PASS |
| resume 對 mismatch 不改綁定；pending naming 分支零檔案 mutation | 獨立 T5 `t5_resume_binding_mismatch_refused=true`、`t5_resume_mismatch_zero_mutation=true`；`test_pending_publish_is_blocked_before_local_changed` | PASS |

### T6 lock 與退出碼

**結果：`PASS`（A0 合成範圍）。**

| 核定要求 | 證據 | 判定 |
|---|---|---|
| 真正子程序持 collection／records flock，另一唯讀命令得到精確 `NOTES_LOCK_BUSY`；釋放後成功 | `tests/test_notes_locks.py::test_real_cli_readonly_commands_are_lock_busy_then_succeed`、`test_collection_lock_is_precise_for_reads_and_mutations`、`test_records_lock_is_precise_for_reads_and_resume` | PASS |
| 非 flock 讀寫 EAGAIN 不能 `retry_safe` | `test_non_flock_eagain_is_not_marked_retry_safe` | PASS |
| mutation／resume 不能 `retry_safe` | `test_notes_locks.py` 的 lock scope／resume 案例 | PASS |
| exit 70 不重試、不再送 | `test_internal_error_is_not_marked_retry_safe` | PASS |
| 0／2／4／70 與 UNKNOWN intent 拒絕 tests 保留 | `test_cli_help_success_and_refusal_exit_codes`、`test_unknown_is_blocked_until_reconcile`、locks 與 records 的拒絕案例 | PASS |

### 事件、投影、completion 與資料 preview

| 核定邊界 | 證據 | 判定 |
|---|---|---|
| 有效 event 只在成功交易後追加；錯誤零有效 event | evidence failure／preserve／bundle drift tests；capture wrapper 失敗案例 | PASS |
| event 追加順序與 v1 reader 相容 | v1 frozen projection／bytes tests；v2 reopen tests；legacy opaque 不升格 | PASS |
| summary／memory 投影、scan／coverage、completion 與資料 preview 規則一致 | summary blockers、latest complete scan、coverage mismatch、NO_MEDIA、completion immutability、evidence audit 與 `lists.records_root` tests | PASS |
| 被明列為未引用的中斷 blob 會保留並回報 | `test_preserve_failure_keeps_interrupted_blobs_and_no_event`；失敗不追加有效 business event | PASS |
| 不以測試派 GUI、覆寫原件或改真實資料 | 本次所有 tests／腳本使用合成隔離路徑；沒有 GUI、網路、真實帳本或照片操作 | PASS |

## 5. 測試前後 Git 狀態與 report-only 邊界

- 開始：HEAD `af4abd85e1ae6e6e5a75d13925f39885e6838806`；branch
  `feature/line-notes-media`；index、tracked diff、非忽略 untracked 全部乾淨；
  `git diff --exit-code` exit 0；remote branch HEAD 同為 `af4abd8`。
- 測試完成後：HEAD、branch、candidate diff 不變；沒有因 tests 產生產品、
  fixture、帳本或照片變更；私有輸出只存在被忽略的 `.local/` 任務區。
- 本報告加入後：唯一新增 tracked／untracked 交付內容是
  `docs/plans/20261102-notes-fieldtest-review/a0-acceptance.md`。這是
  **report-only addition**，不是產品變更、不是新下載結果，也不是新的
  candidate acceptance 週期。`git diff --check` 在提交前重新執行並保留 exit 0。
- 私有 `checks/`與 `fixtures/` 不 stage、不提交；只提交本報告。

## 6. 事實、推論、未知與 `NOT_RUN`

### 事實

- 本次是在精確候選 `af4abd85e1ae6e6e5a75d13925f39885e6838806` 上重新執行
  daily 73 tests、notes 136 tests、CLI help 與 `git diff --check`；四者 exit 0。
- 補充 C1／C2、C3、T3 cross-scope／new-scan、T4／T5 腳本最終均 exit 0，
  原始 stdout／stderr 與 SHA-256 已保存。
- `b6cfd68..af4abd8` 只有一份指定的 S3B-SIM-01 修正版審查文件新增；沒有產品
  程式、tests 或 Skill 變更。
- 本輪沒有讀寫真實 `backup/`、帳本、active task、真實照片或影片，也沒有
  啟動 LINE／GUI／CUA／chooser／popup／Save All。

### 推論（不是新增產品 PASS）

- 既有 v1 reader／golden 與新 writer 的界線在本次合成樣本中保持不變；這支持
  A0 的相容性判定，但不證明服務端原始位元或所有未來資料樣本等價。
- 現行文件與 CLI help 對 A0 可執行命令、退出碼及 bootstrap 邊界的描述一致；
  這不證明文件中每一個 GUI 操作已在真實 App 上可完成。

### 未知

- 真實 LINE 記事本入口、列表身分、AX／CUA 原始 envelope、popup／toast、
  chooser 三層目的地、影片與混合附件、前景中斷及跨 Session 的實際表現。
- 真實外部副本是否完整、服務端原始位元是否相同，以及真實資料上的
  `external_copy_verified`（仍為 `false`）。
- 真實 GUI 的焦點、時鐘、幾何映射、控制可見性、檔案歸屬與使用者可見版本差異。

### `NOT_RUN`

以下項目均為 `NOT_RUN`，不是 PASS：

- G0、D1、D2、G1、G2、T7。
- 真實 LINE／GUI／CUA、即時 chooser、popup／toast、Save All、spinner 瞬態、
    真實影片下載、混合附件、前景中斷、跨 Session 接續及整份列表對帳。
- 任何真實 `backup/`、`backup-records/`、`notes-backup-records/`、active task
  或既有完成事實的讀寫、重試、更正或解鎖。
- 外部副本驗證、服務端原始位元驗證、provider 身分／成本或 token 節省。

## 7. Findings

**本次 A0 沒有已確認的產品 finding。** 沒有需要 bounded fix 的實作缺陷，也
沒有需要修改需求、計畫、資料語意或 gate 的 finding。

以下不是缺陷 finding，而是本輪的外部 gate／邊界：

| 類別 | requirement／候選行為 | evidence／impact | 處置 |
|---|---|---|---|
| 真實 GUI 證據缺席 | N26-AX、TOOLBAR、PANEL、NAME、TOAST、SPINNER、CARD、B1 的實機命題 | 只有文件契約與合成邊界；不把文件一致升格為 GUI PASS | 外部 gate `NOT_RUN`，不是 A0 FIX |
| 外部副本／服務端一致性 | 完成檔案不等於外部副本或服務端原始位元 | `external_copy_verified=false`；解碼成功及 SHA-256 只支持本機 bytes／內容 | 保留外部驗證邊界 |
| 真實資料操作 | 未授權讀寫真實 ledger／照片／active | 未執行；沒有新增 UNKNOWN 或重送 | 等 Owner 另行授權 |
| 舊跨 scan UNKNOWN | T5 legacy fixture 保留舊案例 | 以 test helper 直接構造 legacy graph，不使用 public writer 製造舊 bug；沒有刪除測試或把 fixture 當真實歷史 | A0 邊界已透明記錄，無 plan change |

## 8. 六項狀態

```text
PRIMARY_OUTCOME_STATUS: A0_ACCEPTANCE_PASS
IMPLEMENTATION_STATUS: CANDIDATE_VERIFIED; PRODUCT_UNCHANGED_BY_A0
CORE_ACCEPTANCE_STATUS: PASS_FOR_A0_SCOPE
REQUIRED_VERIFICATION_STATUS: A0_LOCAL_OFFLINE_CHECKS_PASSED; REAL_LINE_G0_D1_D2_G1_G2_T7_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: A0_PASS_FOR_FROZEN_CANDIDATE
TASK_CLOSURE_STATUS: NOT_CLOSED_PENDING_OWNER_GATES_AND_MERGE_DECISION
```

## 9. Owner 下一個人工 gate

Owner 現在要決定是否接受本次 A0 的 `PASS`，以及是否另行授權下一個角色或
真實 gate。不得由本 A0 自行啟動下一個正式角色、派 GUI、重測、修正 finding、
commit 產品變更、merge、force-push 或宣稱結案。

在取得新的明確授權前，G0／D1／D2／G1／G2／T7、真實 LINE 與整份列表完成度
仍維持 `NOT_RUN` 或外部 gate；本報告只交付精確候選 `af4abd8` 的離線 A0
證據與待人工決策。
