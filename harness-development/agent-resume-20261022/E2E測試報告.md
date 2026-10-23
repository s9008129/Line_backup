# AGENT-RESUME-P0-20261022：Fast Interrupted Download Resume

- 日期：2026-10-23（Asia/Taipei）
- 目前目標（Owner 2026-10-23 更正）：不重開 Mac；取消下載中的任務，再執行同一任務時，辨認相簿總數、已完成相簿及中斷位置，跳過已 VERIFIED 相簿並安全接續。不得把既有的 reboot／new-session 測試描述當成本次驗收條件。
- 基線：`a03bf504a2ea0f315d8f56c25f685e97e5410007`；branch `implement/agent-resume-p0-20261022`；Draft [PR #32](https://github.com/s9008129/Line_backup/pull/32)，base `master`。本次實機觀察前 PR head 為 `72c328c6dcd5257a2fc77c913c3080876cd87be1`。
- 修正前程式 HEAD：`4ba44a8b4eda1f500c0eeb4386b774e6c27233dc`；payload 上限修正 commit：`a247550fb9cdc42e4d68fc7c827f0d24b311f0c2`；本輪產品 source commit：`c501ee4947edf7975fae8f03e4b39b48a13bf4d5`；該 exact-head CI 為 [run 39897242576](https://github.com/s9008129/Line_backup/actions/runs/39897242576)，三個 job 成功。其後 `9b03500`、`72c328c` 是 CI consent／文件提交，沒有產品 source 修改；本輪未手動重跑 CI。
- 沿用 Plan v2.1（SHA-256 `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`）；沒有新增第二份計畫、資料庫、cursor store、daemon 或 GUI framework。
- 前一外部 Code Review 綁定 `a03bf50`，結論為 `CHANGES_REQUIRED_BEFORE_APPROVE_IMPLEMENTATION`；本輪只處理 R32-01 small manifest、R32-02 ambiguous chooser crash、R32-03 runbook 三個 bounded 缺口。**目前 HEAD 尚未取得新的外部 Code Review 核准。**

## 1. 結論與狀態

Fast Resume 已把「已完成」與「下一個合法動作」完全由既有 checkpoint 事實推導：`album_order`、`verification`、`save_all_intent`、`chooser_confirm_intent`、`generation`、`payload_sha256`、`session_owner`。沒有新增持久 `next_index` 或需要同步的第二份狀態。

正常 preflight 對先前 VERIFIED 相簿只做檔名、檔數、size、mtime_ns、ctime_ns、regular-file、owner 與 symlink 防護的輕量 metadata 核對；不重新讀取圖片 bytes、不呼叫 SHA-256、不呼叫 ImageIO。新下載目標仍走原本嚴格的三次穩定 inventory、逐檔 SHA-256、ImageIO 完整解碼與 post-decode／post-flush 核對。Owner 主動執行 `reconcile` 時，仍保留完整 deep audit。

```text
PRIMARY_OUTCOME_STATUS=NOT_YET_ACHIEVED_REAL_MAC_RESUME
IMPLEMENTATION_STATUS=FAST_RESUME_OFFLINE_WITH_LINE_BOUNDARY_FIX
CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY
REQUIRED_VERIFICATION_STATUS=LOCAL_PASS_PR_CI_PASS
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
EXTERNAL_CODE_REVIEW_AT_THIS_HEAD=NOT_RUN
REAL_MAC_CUA_SMOKE=PARTIAL_OBSERVED
REAL_MAC_E2E=NOT_RUN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
TASK_CLOSURE_STATUS=OPEN
```

Owner 同意短暫切至 LINE 做唯讀 Smoke。只觀察當下相簿列表的 AX 與畫面，沒有點擊、捲動、輸入、Save All、Chooser 或下載；觀察到一個可見項目為 65 張，符合既有排除條件，未操作該項目。未留存包含私人內容的原始截圖。此為 `OBSERVED`，不是 CUA 接線、下載或 E2E `PASS`；詳見去識別化紀錄 [line-readonly-smoke-20261023.txt](evidence/line-readonly-smoke-20261023.txt)。`gui_dispatches=0`。

## 2. 實際行為與聚焦案例

| Case | 實際行為 | 測試證據 | 結果 |
|---|---|---|---|
| manifest 上限與 CUA JSON-lines 容量 | 上限為 1,000；identity、history source_kind 和反射的 request/session ID 均有 UTF-8 byte limits。最大 identity／ID 回覆為 182,926 bytes；1,000 本最壞歷史摘要投影（32-byte NUL source_kind）為 544,449 bytes，均低於 1 MiB；超限輸入在 checkpoint 寫入前拒絕 | `test_maximum_manifest_fits_cua_hello_line_and_one_over_is_rejected`、`test_history_source_kind_is_bounded_before_it_can_be_returned`；`real controller hello and reconcile fit the CUA line limit at 1,000 albums`；[capacity receipt](evidence/line-payload-boundary.json) | PASS（合成） |
| 1／2／5／10 本 manifest | 非空 Owner ordered manifest 可建立；空 manifest 以 `TASK_MANIFEST_EMPTY` 拒絕 | `test_small_owner_authorized_manifests_and_empty_manifest_rejection` | PASS |
| 100 本，#1～49 VERIFIED | 只核對既有檔案 metadata；`verified_albums_skipped=49`、`metadata_files_checked=49`、`prior_verified_rehash_bytes=0`、`prior_verified_decode_calls=0`，next ordinal `50` | `test_fast_resume_skips_49_verified_then_verifies_only_50`；[metrics receipt](evidence/local-fast-resume-metrics.json) | PASS |
| #50 未開始 | 由 manifest 順序定位 #50，phase `READY_TO_DISPATCH`，不依賴舊 Session 記憶 | 同上；receipt 的 `next_safe_ordinal=50` | PASS |
| #50 有完整 Save All＋Chooser RETURNED，80/80 已落盤 | `READY_TO_VERIFY` 只暴露 #50；目標相簿執行一次嚴格解碼；成功後 next ordinal 變 `51` | `test_fast_resume_skips_49_verified_then_verifies_only_50`、`test_fresh_process_80_of_80_kill_verifies_then_advances_to_51` | PASS |
| #50 partial 32/80 | `BLOCKED_PARTIAL`／`INCOMPLETE_DOWNLOAD`，whole task 停止，保留 32 檔，不重送 | `test_partial_50_blocks_whole_task_and_preserves_32_files` | PASS |
| Chooser click 已發出，80/80 可能落盤，紀錄前程序被 kill | `CHOOSER_OUTCOME_UNKNOWN`、`pending_input=true`、next safe 為 null；新 mutating session 被 `PENDING_INPUT_UNRESOLVED` 擋下；無額外 Save All／Chooser、無偽造 RETURNED、無 VERIFIED 升級，checkpoint bytes 不變 | `test_chooser_click_then_process_kill_stays_unknown_and_blocks_takeover` | PASS |
| 先前 VERIFIED 目錄被移動／metadata 變動 | 快速 metadata 檢查發現 `DESTINATION_MISSING`、`VERIFIED_CONTENT_CHANGED` 等，fail closed，不自動重下載 | `test_verified_album_missing_moved_or_modified_metadata_blocks_fast_resume` | PASS |
| 明確 deep audit | `reconcile` 仍重新 SHA-256／ImageIO；可發現內容異動 | `test_deep_reconcile_redecodes_verified_album` | PASS |
| 新 process／boot／Session | 新 process 從 checkpoint 恢復，不依賴舊 PID、舊 host 或舊 GUI 座標 | `test_fresh_process_resume_completes_50_through_100_with_distinct_pids`、Node host identity 測試 | PASS（合成） |
| 歷史與跨 task 防護 | 239／109／329／65 合成 history barriers 與 unresolved cross-task intent 維持 fail closed | `test_history_barriers_cover_239_109_329_and_65_without_redownload`、`test_cross_task_verified_album_is_skipped_and_unresolved_intent_blocks_new_task` | PASS（合成） |
| 較早 blocker 與後方 VERIFYING 並存 | 不暴露後方目標；`next_safe` 全部為 null，只回 `STOP_AND_RECONCILE_ONLY` | `test_blocker_never_exposes_a_later_verifying_album_as_next_safe` | PASS |

## 3. 實際命令、環境與結果

### 3.1 本機

```sh
python3 -B -m unittest tests.test_agent_resume -v
node --test tests/test_agent_resume_cua.mjs
python3 -B -m py_compile scripts/line_backup_agent_resume.py
node --check scripts/line_backup_agent_resume_cua.mjs
git diff --check
```

- Python：source commit `8eb5220` 上 51/51 PASS，48.403 秒；包含最大身份、歷史摘要、request/session ID 的容量邊界及超限拒絕；原始輸出：[reviewfix log](evidence/local-python-tests-reviewfix-20261023.txt)、[exit](evidence/local-python-tests-reviewfix-exit-20261023.txt)。
- Node：source commit `8eb5220` 上 18/18 PASS，8.268 秒；包含真實 Python controller hello/reconcile wrapper case；原始輸出：[reviewfix log](evidence/local-node-tests-reviewfix-20261023.txt)、[exit](evidence/local-node-tests-reviewfix-exit-20261023.txt)。
- Python compile、Node syntax、`git diff --check`：exit `0`；[reviewfix static checks](evidence/local-static-checks-reviewfix-20261023.txt)。
- Static checks：exit `0`；見 [local-static-checks.txt](evidence/local-static-checks.txt)。
- 環境：macOS `27.0.1`（Darwin `27.0.0`，arm64）、Python `3.9.6`、Node `v24.22.1`、Apple Swift `6.3.3`；見 [environment.txt](evidence/environment.txt)。

### 3.2 Fast Resume 實測 receipt

以既有 test helper 建立 100 本 synthetic manifest、驗證 #1～49，再以 `inspect` 讀取。這不是實機下載，只證明 normal preflight 的決策與工作量：

```text
task_phase=READY_TO_DISPATCH
next_safe_ordinal=50
first_blocker=null
verified_albums_skipped=49
metadata_files_checked=49
fast_resume_elapsed_ms=7
prior_verified_rehash_bytes=0
prior_verified_decode_calls=0
target_album_decode_calls=0
gui_dispatches=0
```

完整 JSON 與 exit code：[local-fast-resume-metrics.json](evidence/local-fast-resume-metrics.json)、[exit](evidence/local-fast-resume-metrics.exit)。`fast_resume_elapsed_ms` 是單次本機合成觀察值，不是效能 SLA。

### 3.3 遠端 feature CI

[agent-resume run 39887815723](https://github.com/s9008129/Line_backup/actions/runs/39887815723) 精確綁定 `4ba44a8b4eda1f500c0eeb4386b774e6c27233dc`，`status=completed`、`conclusion=success`：

| Job | 實際結果 |
|---|---|
| `python-core` | SUCCESS；`Ran 49 tests in 52.680s`、`OK` |
| `node-wrapper` | SUCCESS；`tests 17`、`pass 17`、`fail 0` |
| `mac-imageio` | SUCCESS |

機器可讀 receipt：[ci-run-39887815723.json](evidence/ci-run-39887815723.json)。這是 feature CI 證據，不是實機 E2E、外部 Code Review 或正式兩本相簿驗收。

### 3.4 PR #32 前一 HEAD CI

較早 PR HEAD `a1a64d3152dce798874079d24b594abf4f3a0eff` 的 [run 39891908001](https://github.com/s9008129/Line_backup/actions/runs/39891908001) 三 job 曾全數 SUCCESS；該來源仍有 payload 邊界漏洞，故不作本輪修補 CI 證據。

### 3.5 本輪 PR #32 exact-head CI

PR #32 的來源／文件快照 `f3e8d42e4d49ba78d52b49c4896d1bc847a317a4`（Draft／Open；base `64515eb56b04accc40ade9e2db2fe0ad18c1ced3`）之 [run 39893993234](https://github.com/s9008129/Line_backup/actions/runs/39893993234) 以 workflow dispatch 綁定 exact head，`python-core`、`node-wrapper`、`mac-imageio` 三 job 全數 `SUCCESS`；該快照的產品程式來源仍是 `8eb52208422fd824dea04079b916b275ac0afeb0`。機器 receipt：[ci-run-39893993234.json](evidence/ci-run-39893993234.json)。PR 可合併且無衝突，但仍為 Draft；reviewDecision 空白，僅有舊 `a03bf50` 的 COMMENTED review，branch-protection API 回 403，因此目前無法確認是否要求新 approval。沒有 GitHub review approval，也沒有 merge。

### 3.6 來源與證據識別

| 項目 | SHA-256 |
|---|---|
| Python controller（source `c501ee4`） | `e81bd218c7d981d4b3f069dade955aff0531995cc0f89a751f8135ca3155bf1c` |
| Node wrapper | `bfd2cdceffe7e4af2e506133b76989f280a47133d794e4c0e7d5777ffe3fb585` |
| Python tests（source `c501ee4`） | `bee788d5436e71fb1b75a5b2dc0e8fe7bc5344e7171cc18928a681566be44900` |
| Node tests | `e02d12ac4362cd2b1530c26073dc05e73a2697b3b31bbe4b0640d592f41601b1` |
| Runbook | `625c88e63f23fb7a02a33d67cc5b9dcf0018e203e41155f7c8d4722bef0835c1` |
| ImageIO source | `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b` |
| Vision OCR source | `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861` |

本機完整證據根目錄為 `harness-development/agent-resume-20261022/evidence/`；其遮罩後的絕對路徑為 `/Users/<USER>/.codex/worktrees/a269/Line_backup/harness-development/agent-resume-20261022/evidence/`。公開報告不包含私人照片、LINE 畫面、憑證或原始 protected state。[evidence-sha256.txt](evidence/evidence-sha256.txt) 逐檔綁定本目錄的證據 bytes。

## 4. Crash／UNKNOWN 邊界

`test_chooser_click_then_process_kill_stays_unknown_and_blocks_takeover` 先完成 #1～49，對 #50 持久化 Save All 與 Chooser intent，寫入 80 個合成檔案，然後在 `record_chooser_result` 前直接 kill controller。新 process 的唯讀 `inspect` 顯示：

- 第一個 blocker 是 #50，state `UNKNOWN`、reason `CHOOSER_OUTCOME_UNKNOWN`。
- `pending_input=true`；owner action 為 `DO_NOT_TAKE_OVER; INSPECT_ONLY; RECONCILE_PRIVATE_FILES_WITH_OWNER`。
- `next_safe_ordinal`／`next_safe_album_key` 為 null。
- `VERIFIED` 仍為 49；`chooser_confirm_intent.result` 仍為 null；沒有新增 Save All／Chooser、沒有偽造 RETURNED，也沒有把檔案數升級成 VERIFIED。
- checkpoint bytes 在 crash 前後完全相同；新 `SessionRoot` 以 `PENDING_INPUT_UNRESOLVED` 拒絕接管。

這是刻意保留的 fail-closed 邊界，不是 `--force` 或缺點。無法安全自動恢復時，唯一合法結果是 `BLOCKED` 加精確人工核對工作。

## 5. 嘗試歷史、未知與限制

- 既有離線核心曾為 45 Python tests；本輪加入 small manifest、fast metadata resume、target-only verify、blocker 順序與 crash 邊界後，增至 49，全數通過。
- 實作後自我審查發現：有 blocker 時仍可能暴露後方 `VERIFYING` 為 next safe；已改為 blocker 存在時 next safe 一律 null，並加入回歸測試。
- 未證明實體斷電、macOS reboot 或真實程序終止後的 durability；只使用 `kill`／atomic fault injection 與合成 filesystem。
- 本輪修正：Python `MAX_TASK_ALBUMS` 原為 10,000，而 Node 每條 response line 限 1 MiB；完整 `resume_state` 陣列隨相簿數增長。先以一般 1,000 本 fixture 量到 172,279 bytes，再以最大身份／反射 ID 及全量歷史摘要投影測得 182,926／544,449 bytes。Node 真實 Python controller 整合測試在 1,000 本下完成 hello 與 reconcile。上限設為 1,000，保留原 100 本 AC。
- 回覆邊界複核：獨立檢查發現 `next_safe_album_identity`、反射 IDs 及 persisted history `source_kind` 都需有界。identity text 上限為 256／1,024／256 UTF-8 bytes，request/session IDs 128 bytes，history source_kind 32 bytes。最大 identity／ID envelope 為 182,926 bytes；1,000 本全帶最大 escaping 歷史摘要 envelope 為 544,449 bytes。超限 album 數、identity、reflected ID、history source_kind 均拒絕或 fail closed。獨立二次來源審視未發現其他無界成功回覆欄位；非 GitHub 審查事件，詳見 [review receipt](evidence/payload-review-20261023.txt)。
- 真實 Mac 唯讀 CUA smoke：`PARTIAL_OBSERVED`。Owner 當次同意後，讀取 LINE 前景相簿列表的 AX 與畫面；零 UI 輸入、零派送。當時看見的 65 張相簿未操作，符合已知排除政策。未保存原始截圖，避免將私人相簿內容納入 PR。
- Canonical runtime 已初始化並匯入既有歷史；本次建立兩本相簿的正式任務後，checkpoint 為 generation 2。唯讀 `inspect` 前後一致，未執行會建立 `SESSION_OPENED`／session owner 狀態的 Node wrapper `hello`。本次可用的 CUA app handle 不能傳給要求既有 PR28 host／`app.click()` 的 Node wrapper，這是交易測試的整合阻塞。
- 未證明 Vision OCR、列表捲動、menu identity、chooser 目的地或實際點擊 correspondence；沒有執行 Save All、Chooser、下載或照片讀取。
- 未證明真實相簿 80/80 檔案的 SHA-256、ImageIO、VERIFIED readback 或 release。
- Owner 更正後的兩本相簿取消／同任務重跑／從中斷位置接續流程：`NOT_RUN`。
- PR #32 exact-head CI 在 `80596cf` 三 job 全通過。沒有目前 HEAD 的 GitHub approval；目前只有舊 `a03bf50` 的 COMMENTED review。branch-protection endpoint 回 403，review 要求未知；本地 read-only source audit 不是 GitHub approval。

## 6. Overengineering Audit

- `KEEP`：單一 canonical checkpoint、atomic fsync／readback、checksum／generation、single writer lock、Save All／Chooser durable intent、UNKNOWN 保留、SHA-256／ImageIO、target-only 嚴格驗證、explicit deep reconcile、239／109／329／65 歷史 barrier。
- `REUSE`：既有 PR #28 Agent CUA／AX／OCR／GUI 入口；本輪沒有新增 OCR、AX、NativeDiagnostic、資料庫、daemon、scheduler 或第二套 cursor store。
- `SIMPLIFY`：移除 100 本硬下限與每次 Session hello／GUI preparation 的強制全歷史 deep reconcile；normal resume 只做一次輕量 metadata preflight，explicit audit 仍可按需 deep。
- `DEFER`：真實 Mac F／G E2E、外部 Code Review、正式 TWO_ALBUM_AUTO／grant／ledger 驗收。這些不能以合成測試、PR 留言或 CI 綠燈替代。

## 7. 下一個安全動作

1. 目前 source `c501ee4` 的 exact-head CI 三個 job 已通過；PR 最新 HEAD 的外部 Code Review 仍未核准。此觀察不是正式 E2E，也沒有進行 Save All。
2. 部分下載目前回 `BLOCKED_PARTIAL` 並禁止重下；要達成 Owner 的取消後接續需求，先由 Planner 提出最小、可審查的恢復規則，再交獨立審查者核對交易與重複下載邊界。
3. 在既有 PR28 host／app handle 可由執行入口提供，且部分下載接續行為完成核准與實機驗證前，維持 `CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY`；UNKNOWN／PARTIAL 時保留資料並停止派送。

## 8. 2026-10-23 真實 LINE 畫面核對（OBSERVED；非 E2E）

- Owner 交付電腦控制權後，以 `mcp__cua_repl` 對當前 LINE 視窗重新取得 AX／畫面。畫面中的群組及兩本 Owner 選定目標均與本機 manifest 相符；公開紀錄遮蔽相簿標題、日期、張數與照片內容。
- 在相簿列表做一次 0.25-page 向下捲動，AX 捲軸從 3991 變為 4531；看到另一個目標卡片完整顯示。以卡片標題進入詳細頁，畫面再次顯示與 Owner 提供資料一致的標題及照片總數。按 Escape 返回列表；向上 0.25 page 後，以同樣方法核對另一個目標詳細頁，再返回列表。
- 有一次捲動因使用過期 AX element ID 失敗，工具明確在派送前拒絕該 ID；重新讀取 AX 後使用當下 ID 成功。沒有重送任何結果不明的輸入。
- 任務唯讀 `inspect` 前後皆為 generation `2`、兩本 `NOT_STARTED`、`READY_TO_DISPATCH`、`pending_input=false`、`gui_dispatches=0`；任務下載目錄檔案數為 0。239 張歷史 VERIFIED 照片未讀寫、未重下載。LINE 前景中沒有 Save All、Chooser、取消下載或照片下載操作。
- CUA 回傳的私人相簿畫面只在本對話操作期間可見，沒有存入 repo 或上傳；因此原始畫面沒有可提供的檔案 SHA-256。去識別化操作紀錄與 runtime 摘要見 [line-cancel-resume-observation-20261023.txt](evidence/line-cancel-resume-observation-20261023.txt)，SHA-256 `b9b03faa601a12948d40d481dfc283f705222a3cef91ed86737484ce46d408b`。這是實際 GUI `OBSERVED`，不是 CUA wrapper PASS、下載驗證或正式 E2E。
- source `c501ee4947edf7975fae8f03e4b39b48a13bf4d5` 的既有狀態推導在收到已確認的部分 inventory 時會回傳 `BLOCKED_PARTIAL`／`INCOMPLETE_DOWNLOAD`，並要求保留檔案及停止，不會從相簿內未完成位置繼續。對應程式 `scripts/line_backup_agent_resume.py:_derive_album_state`、回歸案例 `tests/test_agent_resume.py::test_partial_50_blocks_whole_task_and_preserves_32_files`；這些是既有程式／離線測試證據，本輪沒有執行該測試。
- 本次真實取消／重跑接續測試：`NOT_RUN`；實際 Save All 派送 `0`、下載 `0`。第一個 blocker 是既有 Node wrapper 需要 PR28 host 內可呼叫的 `app.click()` handle，而本次可用的 CUA app handle 位於獨立工具工作階段，不能傳給該 wrapper；另有上述部分 inventory 目前 fail-closed 而不接續的產品缺口。沒有以手動點擊繞過交易入口。
