# AGENT-RESUME-P0-20261022：Fast Interrupted Download Resume

- 日期：2026-10-23（Asia/Taipei）
- 目標：Mac 重開機、Codex Session 中斷或程序終止後，新 Session 只靠唯一 canonical checkpoint 找到第一個尚未安全完成的相簿，跳過既有 VERIFIED，安全接續下載。
- 基線：`a03bf504a2ea0f315d8f56c25f685e97e5410007`；branch `implement/agent-resume-p0-20261022`；Draft [PR #32](https://github.com/s9008129/Line_backup/pull/32)，base `master`。
- 本次已驗證程式 HEAD：`4ba44a8b4eda1f500c0eeb4386b774e6c27233dc`。Docs-only commits 不改寫此程式綁定。
- 沿用 Plan v2.1（SHA-256 `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`）；沒有新增第二份計畫、資料庫、cursor store、daemon 或 GUI framework。
- 前一外部 Code Review 綁定 `a03bf50`，結論為 `CHANGES_REQUIRED_BEFORE_APPROVE_IMPLEMENTATION`；本輪只處理 R32-01 small manifest、R32-02 ambiguous chooser crash、R32-03 runbook 三個 bounded 缺口。**目前 HEAD 尚未取得新的外部 Code Review 核准。**

## 1. 結論與狀態

Fast Resume 已把「已完成」與「下一個合法動作」完全由既有 checkpoint 事實推導：`album_order`、`verification`、`save_all_intent`、`chooser_confirm_intent`、`generation`、`payload_sha256`、`session_owner`。沒有新增持久 `next_index` 或需要同步的第二份狀態。

正常 preflight 對先前 VERIFIED 相簿只做檔名、檔數、size、mtime_ns、ctime_ns、regular-file、owner 與 symlink 防護的輕量 metadata 核對；不重新讀取圖片 bytes、不呼叫 SHA-256、不呼叫 ImageIO。新下載目標仍走原本嚴格的三次穩定 inventory、逐檔 SHA-256、ImageIO 完整解碼與 post-decode／post-flush 核對。Owner 主動執行 `reconcile` 時，仍保留完整 deep audit。

```text
PRIMARY_OUTCOME_STATUS=NOT_YET_ACHIEVED_REAL_MAC_RESUME
IMPLEMENTATION_STATUS=FAST_RESUME_OFFLINE_COMPLETE
CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY
REQUIRED_VERIFICATION_STATUS=LOCAL_AND_FEATURE_CI_PASS
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
EXTERNAL_CODE_REVIEW_AT_THIS_HEAD=NOT_RUN
REAL_MAC_E2E=NOT_RUN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
TASK_CLOSURE_STATUS=OPEN
```

本輪沒有取得 LINE app、截圖、AX、OCR、相簿、Save All、Chooser、下載或真實照片；所有程式證據都是合成 fixture 或 fake app。`gui_dispatches=0`，不可寫成實機下載 PASS。

## 2. 實際行為與聚焦案例

| Case | 實際行為 | 測試證據 | 結果 |
|---|---|---|---|
| 1／2／5／10 本 manifest | 非空 Owner ordered manifest 可建立；空 manifest 以 `TASK_MANIFEST_EMPTY` 拒絕；上限 10,000 | `test_small_owner_authorized_manifests_and_empty_manifest_rejection` | PASS |
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

- Python：exit `0`，`Ran 49 tests in 45.651s`、`OK`；原始輸出見 [local-python-tests.txt](evidence/local-python-tests.txt) 與 [exit code](evidence/local-python-tests.exit)。
- Node：exit `0`，`tests 17`、`pass 17`、`fail 0`、`duration_ms 6588.837917`；原始輸出見 [local-node-tests.txt](evidence/local-node-tests.txt) 與 [exit code](evidence/local-node-tests.exit)。
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

### 3.4 來源與證據識別

| 項目 | SHA-256 |
|---|---|
| Python controller | `82aada19edb2039fa6c254906904f1d478b6d8158b2456a943d792f39c7d87cb` |
| Node wrapper | `bfd2cdceffe7e4af2e506133b76989f280a47133d794e4c0e7d5777ffe3fb585` |
| Python tests | `c55b5af3d702c05cc5d8fbd85a7788404a140d1152170daf0d32d19407fa106b` |
| Node tests | `4c92e3dabad573b517871e9083de2595d74285e8a9a61c68d5eec628d6b61a1c` |
| Runbook | `4e64e38a0bd1526682045d192729e02d7eed6e1fbdcddaef3e07bac0bd2cf02c` |
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
- 未證明真實 LINE 畫面、fresh screenshot／AX／Vision OCR、scroll、menu identity、chooser 目的地或實際點擊 correspondence。
- 未證明真實相簿 80/80 檔案的 SHA-256、ImageIO、VERIFIED readback 或 release。
- 兩本不同 eligible 新相簿的 F → reboot → G 實機流程：`NOT_RUN`。
- 外部 Code Review 對 `4ba44a8` 的新一輪審查：`NOT_RUN`；本報告不把前一輪 `a03bf50` 的審查轉移到新 HEAD。

## 6. Overengineering Audit

- `KEEP`：單一 canonical checkpoint、atomic fsync／readback、checksum／generation、single writer lock、Save All／Chooser durable intent、UNKNOWN 保留、SHA-256／ImageIO、target-only 嚴格驗證、explicit deep reconcile、239／109／329／65 歷史 barrier。
- `REUSE`：既有 PR #28 Agent CUA／AX／OCR／GUI 入口；本輪沒有新增 OCR、AX、NativeDiagnostic、資料庫、daemon、scheduler 或第二套 cursor store。
- `SIMPLIFY`：移除 100 本硬下限與每次 Session hello／GUI preparation 的強制全歷史 deep reconcile；normal resume 只做一次輕量 metadata preflight，explicit audit 仍可按需 deep。
- `DEFER`：真實 Mac F／G E2E、外部 Code Review、正式 TWO_ALBUM_AUTO／grant／ledger 驗收。這些不能以合成測試、PR 留言或 CI 綠燈替代。

## 7. 下一個安全動作

1. 由 Owner 指定的外部 Code Reviewer 對精確 `4ba44a8` 產品來源、PR #32 最新 docs HEAD、本報告與 evidence hashes 做 bounded re-review；不得宣稱已核准，直到有真實審查結果。
2. 審查通過後，Owner 另啟全新、獨立的 DeepSeek `deepseek-v4.1-flash:1017` Session，依 [Mac實機接續Runbook.md](Mac實機接續Runbook.md) 先完成新相簿 F、重開 Mac、新 Session 快速跳過 F，再以 fresh GUI identity 定位不同的 eligible G。
3. F／G 未完成前維持 `CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY`；任何 UNKNOWN／PARTIAL 只輸出精確 blocker，不重送、不刪 checkpoint、不繞過 pending input。
