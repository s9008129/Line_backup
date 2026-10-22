# AGENT-RESUME-P0-20261022：M0／M1 離線驗證報告

- 日期：2026-10-22（Asia/Taipei）
- Plan revision：v2.1；SHA-256 `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`
- Handoff SHA-256：`d95c73fca8abcb631a2af56f1c376bbe4d899556eb521f425570038010326d9b`
- Owner 決策：`EXTERNAL_PLAN_REVIEW=OWNER_WAIVED`。本次豁免只涵蓋 Plan Review，不代表產品、Code Review、遠端 legacy CI 或獨立 E2E PASS。
- Feature base：master `64515eb56b04accc40ade9e2db2fe0ad18c1ced3`
- 已驗證的產品來源 HEAD：`cdf92ce94d6fb67080eadda0d4d182b84f83e0cc`
- Feature branch／Draft PR：[`implement/agent-resume-p0-20261022`](https://github.com/s9008129/Line_backup/tree/cdf92ce94d6fb67080eadda0d4d182b84f83e0cc)／[PR #32](https://github.com/s9008129/Line_backup/pull/32)

## 1. 結論與狀態

M0 的零 LINE 接線能力已通過：真 Node process 以 `node:child_process.spawn`、`shell=false` 啟動本地 Python 長活 session，只經單一 stdin/stdout JSON-lines 通訊；固定 runtime root 全域 `flock`、真 process／boot 身分、durable owner record、EOF 永久停止、舊 host／pending input 拒接管，以及 target Mac 的 file fsync、`F_FULLFSYNC`、directory fsync、readback 均有可重現測試。

M1 的離線核心與故障矩陣已通過本地及乾淨 macOS CI：100 本 ordered manifest、單一 checkpoint／generation／checksum、跨 task history／intent barrier、239／109／329／65 唯讀 barrier、durable Save All／Chooser intent、三次穩定 inventory、逐檔 SHA-256、原樣 ImageIO 完整 RGB、post-decode 核對、單次 app click，以及 controller 遺失後永久停止。這些證據只覆蓋合成 fixture 與 fake app。

本輪另修正一個由聚焦回歸找到的根因：deep reconcile 先前可能只信任既有 VERIFIED bytes／hash，沒有再次呼叫 ImageIO 解碼。現已在 deep path 重新 hash／decode；新增回歸測試確認 `_decode_inventory` 確實被呼叫，且 VERIFIED／next ordinal 維持正確。

```text
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=M0_M1_OFFLINE_COMPLETE_M2_CI_B_PENDING
CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY
REQUIRED_VERIFICATION_STATUS=PARTIAL_FEATURE_CI_PASS_LEGACY_CI_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
EXTERNAL_PLAN_REVIEW=OWNER_WAIVED
EXTERNAL_CODE_REVIEW=NOT_RUN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

沒有取得 LINE app、截圖、AX、OCR 畫面、選單、相簿或真實照片；本輪離線程序證據中的 `gui_observations=0`、`gui_dispatches=0`。wrapper 測試只呼叫 fake app，沒有正式 GUI 派送。

## 2. 來源、環境與證據

### 2.1 固定來源

| 項目 | 已核對值 |
|---|---|
| Plan SHA-256 | `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502` |
| Handoff SHA-256 | `d95c73fca8abcb631a2af56f1c376bbe4d899556eb521f425570038010326d9b` |
| Python controller | `scripts/line_backup_agent_resume.py`：`942d89c2f93dc7bd74eab61023072c3aa9be687cea0b03d9982d40eba12e81f0` |
| Node wrapper | `scripts/line_backup_agent_resume_cua.mjs`：`6d442a998272e0871bb8b55fea01989ba960877f40235f1d999ceb89a989257d` |
| Python tests | `tests/test_agent_resume.py`：`8081eddd45d3d2be5384e3ea47437c9e6643065d96df5e483cd63fd809b4818c` |
| Node tests | `tests/test_agent_resume_cua.mjs`：`d38d659873050f79754ad90d33ef31b689ac726677361a5abbc85530d24f727b` |
| Feature workflow | `.github/workflows/agent-resume.yml`：`f3de2131b4adf1c8fd9cd2fc87c05af485431e815e41b5a108b0b6cca881b26f` |
| ImageIO source | `scripts/agent_resume/image_decode.swift`：`238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b` |
| OCR source | `scripts/agent_resume/modern_ocr.swift`：`19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861` |

### 2.2 實際執行環境

本機為 macOS 27.0.1（Darwin 27.0.0，arm64）；Python `3.9.6`、Node `v24.22.1`、Apple Swift `6.3.3`。遠端 feature CI 使用 GitHub Actions `macos-15`。

私有原始證據保留於固定 runtime root 的 task evidence，公開路徑遮蔽為：

```text
<HOME>/Library/Application Support/LineBackup/agent-resume/tasks/AGENT-RESUME-P0-20261022/evidence/m1-complete-20261022T205243/
```

該目錄保存 `python-unittest.*`、`node-test.*`、`mac-imageio.*`、`py-compile.*`、`node-check.*`、`diff-check.*`、`environment.txt`、`source-sha256.txt`、`evidence-sha256.txt` 與 `ci-run.*`。關鍵 exit-code 檔均為 `0`；原始 bytes 的 SHA-256 已逐檔列在 `evidence-sha256.txt`。公開報告不重貼私有照片、個人路徑或憑證。

### 2.3 遠端 feature CI

[run 39782491253](https://github.com/s9008129/Line_backup/actions/runs/39782491253) 綁定 `cdf92ce94d6fb67080eadda0d4d182b84f83e0cc`，`status=completed`、`conclusion=success`：

| Job | 實際結果 |
|---|---|
| `python-core` | SUCCESS；45 tests，215.792 秒 |
| `node-wrapper` | SUCCESS；syntax check 與 wrapper suite |
| `mac-imageio` | SUCCESS；原樣 ImageIO 的 2 個聚焦測試 |

這是 feature CI 的 PASS，不是 legacy CI、Code Review 或 LINE E2E 的替代證據。

## 3. M0 實際結果

### 3.1 Python 核心

命令：

```text
python3 -B -m unittest discover -s tests -p 'test_agent_resume.py' -v
```

本機實際結果：exit `0`，`Ran 45 tests`，`OK`（175.003 秒）。M0 相關測試涵蓋：

- strict JSON duplicate key／NaN／NUL／size 拒絕。
- 真實 controller process start identity、boot identity 與不存在 PID。
- 固定 root 的 real file fsync／`F_FULLFSYNC`／directory fsync／readback，probe 清理後無殘留。
- 固定 root 全域 writer lock；第二 writer 得到 `WRITER_BUSY`。
- active owner 的舊 host 仍活時拒絕接管；host 結束後可接管。
- `pending_input=true` 在 host 已死時仍拒絕接管。
- canonical lock record 損壞或 duplicate key 時 fail closed。
- hello 後 stdin EOF 以 exit `3` 停止，留下 active barrier；舊 host 未退出時不接管。
- 指定 Swift 工具來源 hash 與 Plan 指定值一致。

### 3.2 Node／Python 真程序接線

命令：

```text
node --test tests/test_agent_resume_cua.mjs
```

本機實際結果：exit `0`，`tests 17`、`pass 17`、`fail 0`、`skipped 0`、`duration_ms 5944.132667`。其中 M0 案例驗證：

- Node 以 `spawn` 啟動 Python session，使用單一 stdin/stdout JSON-lines 連線成功。
- hello 的 controller PID/start、host PID/start、boot identity、fixed-root SHA-256、generation 與 writer lock 均由 wrapper 重驗。
- file fsync、fullfsync、directory fsync、readback 四項皆為 `true`。
- clean record 為 `state=closed`；root mode `0700`、lock mode `0600`。
- stale host identity 在 GUI 能力前被拒絕；controller 遺失後 wrapper 永久 closed。
- 舊 host 仍活時新 controller 得到 `OLD_HOST_ALIVE`；第二 controller 得到 `WRITER_BUSY`。

### 3.3 原樣 Mac 工具

ImageIO 與 OCR 來源已逐 bytes 核對 Plan 指定 SHA-256。`MacImageDecoderTests` 的 2 個測試已在本機與遠端 macOS CI 通過：有效 PNG 可完整解碼，截斷 bytes 正確失敗。這是工具能力與正負例結果，不是真實相簿照片的 ImageIO PASS。

## 4. M1 實際結果

### 4.1 已完成能力

- 固定 100 本 ordered manifest；#1～49 為 `SKIPPED_EXISTING`，next safe ordinal 為 #50。
- 單一 canonical checkpoint、generation、payload checksum、append-only event；inspect／reconcile 不寫 checkpoint、照片或 lock。
- 跨 task VERIFIED／日期歧義 barrier；歷史 239／109／329 與 65 排除均以唯讀資料建立屏障。
- Save All／Chooser durable intent、generation／scope／grounding 驗證、readback 後才提供一次 click 資格。
- controller 遺失、回應遺失、result-record 遺失、malformed／oversize／duplicate response 均永久停止新輸入；新 Session 零重試。
- 獨立空目的地、非空目錄／symlink／traversal／partial／zero-byte／未知額外檔 fail closed。
- 三次相同 inventory、3 秒間隔、600 秒上限；逐檔 SHA-256 與原樣 ImageIO 完整 RGB 解碼；post-decode inventory 再核對。
- 既有 VERIFIED 在新 resume deep reconcile 時重新 hash／ImageIO 解碼；缺檔、改檔或截斷會 `BLOCK` 且不補下載。

### 4.2 根因修正

聚焦測試 `test_deep_reconcile_redecodes_verified_album` 暴露：既有 VERIFIED album 的 deep reconcile 先前只重用檔案 bytes／hash 事實，未證明本次仍呼叫 ImageIO。修正後，deep path 會重新呼叫共同 decoder，測試以 spy 確認 `_decode_inventory` 至少被呼叫一次，且 album 維持 `VERIFIED`、next ordinal 正確推進到 #51。

這是目前最重要的一項真實缺陷修正；它仍只由離線合成 bytes 驗證，不能外推為真實照片或實機 E2E PASS。

## 5. TC01～20 對應

下列只是「合成／fake app 測試涵蓋」對照。LINE GUI、真實下載與獨立驗收仍未執行。

| TC | 對應測試／實際涵蓋 |
|---|---|
| 01–02 | `test_ordered_manifest_resumes_at_50_and_read_only_views_do_not_mutate`、`test_fresh_process_without_intent_leaves_50_fresh`；前 49 零增量、#50 fresh |
| 03 | `test_fresh_process_intent_kill_leaves_unknown_without_retry`、`test_intent_before_click_is_unknown_and_never_retried` |
| 04 | `test_fresh_process_save_all_returned_before_chooser_preserves_unknown`、Node `successful click followed by result-record loss stays UNKNOWN with zero retry` |
| 05 | `test_partial_50_blocks_whole_task_and_preserves_32_files` |
| 06 | `test_fresh_process_80_of_80_kill_verifies_then_advances_to_51` |
| 07 | `test_verified_album_missing_modified_or_truncated_file_blocks_without_redownload`、`test_deep_reconcile_redecodes_verified_album` |
| 08 | `test_process_interruption_at_every_atomic_boundary_keeps_one_valid_revision`、`test_enospc_fsync_replace_and_readback_failures_are_explicit` |
| 09 | Node `fake controller protocol failures are terminal...`、`save all and chooser each use the existing app exactly once`、`failed GUI click...zero retry` |
| 10 | `test_stale_generation_and_foreign_scope_grounding_cannot_prepare`、Node `stale host start identity...` |
| 11 | `test_global_writer_lock_and_clean_close`、`test_live_old_host_blocks_takeover_until_it_exits`、`test_pending_input_blocks_takeover_even_after_host_exit`、`test_eof_after_hello_is_unclean...` |
| 12 | `test_cross_task_date_ambiguity_propagates_exact_blocker`；manifest／identity binding negative cases |
| 13 | `test_missing_or_nonempty_destination_blocks_without_recreation`、`test_partial_zero_symlink_and_non_directory_entries_fail_closed`、`test_extra_file_after_returned_chooser_blocks_without_redownload` |
| 14 | `test_store_checksum_schema_and_manifest_bindings_fail_closed`、`test_stale_generation_and_foreign_scope_grounding_cannot_prepare` |
| 15 | `test_decoder_timeout_is_distinct_and_non_mutating`、`test_enospc_fsync_replace_and_readback_failures_are_explicit`、`test_missing_chooser_evidence_blocks_verification_without_mutation` |
| 16 | `test_history_barriers_cover_239_109_329_and_65_without_redownload`、`test_cross_task_verified_album_is_skipped_and_unresolved_intent_blocks_new_task` |
| 17 | `test_fresh_process_resume_completes_50_through_100_with_distinct_pids`、`test_full_50_verification_advances_to_51_then_completes_100` |
| 18 | Strict JSON tests、`test_store_checksum_schema_and_manifest_bindings_fail_closed`、`test_symlink_and_orphan_temp_checkpoint_fail_closed`、destination safety tests |
| 19 | `test_ordered_manifest_resumes_at_50_and_read_only_views_do_not_mutate`、`test_generation_change_during_inspection_is_reported_without_mutation` |
| 20 | `test_protected_fixture_sentinels_remain_byte_identical`；只證明 fixture sentinels 不變，非正式 State／Grant／Ledger baseline |

## 6. 嘗試歷史、未知與限制

- M0：第一次即建立真 process／stdio／lock／sync 能力，無 LINE 呼叫；結果 PASS。
- M1 薄切片：先以 24 Python／9 Node tests 建立 store、history、intent、verifier、wrapper；結果 PASS，但矩陣不完整。
- M1 完整化：擴充到 45 Python／17 Node tests 與 feature CI；聚焦回歸找到 deep reconcile 未重新 decode 的缺陷，修正後全數通過。
- 未證明實體掉電耐久性；`kill -9` 僅是程序故障注入。也不宣稱 OS sandbox 或網路隔離。
- `test_protected_fixture_sentinels_remain_byte_identical` 只使用合成 sentinel，沒有讀寫正式 protected state。
- legacy CI B（PR31 HEAD `1b9a010` 的 inspection fixture／Swift consumer 修復）尚未實作或執行。
- External Code Review、獨立 DeepSeek `deepseek-v4.1-flash:1017` E2E：NOT_RUN。
- LINE app 取得、唯讀觀察、截圖、AX、真實 OCR、scroll：NOT_RUN。
- 真實相簿 Save All、Chooser、下載、逐檔 SHA-256、真實照片 ImageIO、VERIFIED readback：NOT_RUN。
- 兩本不同 eligible 相簿、Mac reboot 接續、no-replay：NOT_RUN。

## 7. 下一個安全動作

1. 完成 M2 的 CI B 工作包：從 PR31 HEAD `1b9a010` 建立 sibling branch，只修改 Plan §5.3 允許的 inspection fixture／workflow／consumer／test／報告檔，於原始 legacy branch 的遠端 required checks 取得精確 HEAD PASS。
2. 更新並讀回 PR #32 的精確 HEAD、報告與兩份 CI 證據，保持 Draft。
3. 將 feature 與 CI B 的 exact HEAD、AC／TC 對照、diff、來源 hash、已知 FAIL／NOT_RUN 交 Owner 轉交外部 ChatGPT Code Review。
4. 只有取得真實 `APPROVE_IMPLEMENTATION`、有效 runtime authorization 與當次 LINE 前景交接後，才可由 Owner 另啟獨立 DeepSeek session 進行兩本真實相簿 E2E；Sol／Luna 不得代替其判定。
