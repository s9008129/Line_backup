# 記事本中斷恢復 S2：實作報告

## 本輪結論與邊界

本輪依 Owner 指定的 Implementer Prompt 完成 S2 候選：先釐清 `SI-U01`，再核對 C01–C12 離線矩陣，整合 AGENTS、記事本 Skill／references、證據範本與唯一日常 Prompt，最後執行核准的離線回歸。這是實作候選報告，不是 Acceptance、獨立驗收或整體 DONE。

本輪沒有操作真實 LINE／CUA、chooser、私人帳本、真實照片／影片或 active 檔；沒有下載、覆寫、取消 modal、合併 `master`、force-push 或啟動下一個正式角色。

## 授權、版本與起始身分

- 角色 Prompt：`~/.codex/prompts/v4.9.0/04_implement_prompt.md`。
- Repo／worktree：本專案 `Line_backup`；branch `feature/line-notes-media`。
- 起始 HEAD 與當次遠端 HEAD：`0505912eec4ff66fe42c8abe85dc8b42900b78cd`。
- 核定計畫／原 handoff 共同提交：`c3c8827cea817db633736d9f8303c43f454fa7cd`。
- S1 交接提交：`9f9748cbbc00caa516d541e4c8a808a9e0cc8156`。
- 計畫簡潔性審查提交：`2292aec`；獨立 Plan Review 與產品基準提交：`97a1cbc`。
- S1 簡潔性複查與交接時產品候選：`0505912`；其已審產品 commit／基準為 `275f15e74ac0a97dd1876922da7151b4236d6403`。
- 起始未提交候選：`AGENTS.md`、notes `SKILL.md`、`download-and-ledger.md`、`src/line_backup_batch/notes.py`、`tests/test_notes_restart.py`。本輪未 reset／clean，也沒有改寫其他 worktree 或私有資料。

起始 status、完整 diff、檔案 SHA-256 與環境保存在 `.local/line-backup/tasks/20261108-notes-s2-implementation/`；這些私有證據不進公開 Git。

## 承接候選與本輪變更

承接候選的 `notes.py` 已經包含 `SI-U01` 所需的 `candidates_by_restart` 投影修正與部分直接案例。本輪沒有重寫該根因修正，而是核對實作、保留原有 dirty，並補上跨 generation、scope 外異常、並行 writer 與正式入口證據。

本輪新增／調整的公開路徑：

| 路徑 | 用途 |
|---|---|
| `src/line_backup_batch/notes.py` | 承接並核對 restart candidate 依 `restart_id` 隔離、第二個 generation 的 active 取代、舊歷史保留與 active 目錄一致性檢查 |
| `tests/test_notes_restart.py` | 補第二個 generation、scope 外 completed drift、錯誤 scan context、concurrent records writer 等直接案例；最終 35 tests |
| `AGENTS.md` | 只加入記事本精確 restart 例外；相簿規則不變 |
| `.agents/skills/line-notes-agent-cua/SKILL.md` | 普通 scan 與已確認 restart 的 recovery scan 分流、唯一日常流程 |
| 同 Skill `references/download-and-ledger.md` | confirm、必要中斷、完整 recovery scan、逐項 intent、activation 的唯一順序 |
| 同 Skill `references/verification-and-recovery.md` | `UNKNOWN`／無 outcome／`LOCAL_CHANGED` 與 scope 外保護 |
| 同 Skill `references/gui-inventory.md` | confirm 後重新觀察來源；不得沿用舊 page rows、cursor、viewer 或 chooser |
| 同 Skill `references/evidence-template.md` | 私有 restart 批次欄位；不新增 CLI schema |
| 同 Skill `references/evidence-decision-cases.md` | preview 不是同意、再次中斷／scope 漂移／晚到結果案例 |
| `docs/LINE相簿備份_使用手冊.md` | 第 5 節正式記事本 Prompt 加入批次確認、recovery scan 與歷史保護條款 |
| 本報告 | S2 候選、矩陣映射、命令與未測界線 |

## `SI-U01`：同媒體第二個 generation

### 根因與修正

舊 projection 以 `media_key` 為全域 candidate key；同一媒體第二次 generation 的 candidate 會與第一個 generation 爭用同一個投影位置，activation replay 便可能把前一代 candidate 當成 current，或在已 active 後拒絕合法的下一代。

承接候選現在以 `candidates_by_restart[restart_id][media_key]` 隔離 candidate，activation 也只驗證自己所屬 restart 的 candidate。`active_by_media` 可被較新的 activation 取代，但舊 confirmation、candidate、activation、completion、UNKNOWN 與舊版本路徑都保留；啟動後重新核對同一貼文只能有一個 active version directory。

### 直接案例

- `test_second_generation_replaces_active_media_and_keeps_history`
- `test_second_generation_failure_keeps_first_active_unchanged`
- `test_second_generation_permission_failures_keep_first_active`
- `test_second_generation_hash_and_decode_failures_keep_first_active`

四例均通過：成功案例重開後只有一個 media row、active generation 為 2，舊事件 bytes 與舊漂移檔未改；copy／activation／權限／hash／decode 失敗時 active generation 仍為 1。

## C01–C12 離線映射

以下映射使用精確測試名稱；不是只依測試標題推論。

| 條目 | 直接測試／證據 | 結果與限制 |
|---|---|---|
| C01 | `test_unconfirmed_forged_and_wrong_confirmations_append_nothing`、`test_confirm_rejects_scan_drift_and_cross_list_preview`、`test_confirm_rejects_old_version_change_after_preview` | 未確認、偽造 preview、錯誤 list／scan context、scan drift、cross-list 與舊版本改變均拒絕且事件 bytes 不變。真人沉默／拒絕本身沒有 GUI 自動化，對應的是同一「無有效 confirm」gate；不冒充 GUI PASS。 |
| C02 | `test_restart_unknown_and_no_outcome_attempts_can_be_superseded`、`test_no_outcome_pre_restart_attempt_is_superseded_without_fake_stop` | UNKNOWN 與無 outcome 可在已確認批次建立新 v3 attempt；舊 raw／events 保留，沒有假 `STOPPED` 或假 reconcile。 |
| C03 | `test_restart_scope_expands_only_the_affected_post`、`test_source_missing_stays_owed_and_never_triggers_restart`、`test_new_media_after_activation_publishes_into_active_version` | 受影響貼文包含已完成 sibling；scope 外 completed、`LOCAL_MISSING`、`EXCLUDED`、`PROTECTED_HISTORY` 不重下；source missing 保持欠件且不稱全部完成。 |
| C04 | `test_restart_vertical_path_isolated_candidate_and_reopen`、`test_scope_outside_completed_drift_blocks_restart_intent`、`test_candidate_drift_is_replaced_by_new_unique_copy`、`test_candidate_extra_file_fails_closed_without_activation`、`test_candidate_symlink_hardlink_and_inode_drift_are_rejected`、`test_second_generation_replaces_active_media_and_keeps_history` | scope 內 `LOCAL_CHANGED` 保留舊檔並在新版本重建；scope 外 drift 仍擋下 intent；缺檔、額外檔、hash／inode／symlink 異常 fail closed。 |
| C05 | `test_confirm_rejects_scan_drift_and_cross_list_preview`、`test_confirm_rejects_old_version_change_after_preview`、`test_unconfirmed_forged_and_wrong_confirmations_append_nothing`、`test_scope_outside_completed_drift_blocks_restart_intent`、`test_restart_confirm_refuses_concurrent_records_writer`、`test_source_change_before_isolation_is_rejected`、`test_restart_replay_rejects_v3_prior_attempt_drift` | preview 後 scan／cross-list／舊版本／scope 外／來源改動均拒絕；另一程序持有 records lock 時得到 `NOTES_LOCK_BUSY`，不追加確認。沒有擴權或靜默重送。 |
| C06 | `test_interrupted_recovery_scan_and_new_session_are_bound_to_new_attempt`、`test_confirmed_pending_publish_is_suppressed_not_republished`、`test_lists_recovers_all_ledgers_without_active_hint` | 中斷 scan 與新 Session 重新 bind／recovery scan 後使用新 attempt；舊 attempt 保留原 scan；已確認 pending publish 不再發布；active hint 遺失仍由 `lists` 找回帳本。 |
| C07 | `test_confirmation_intent_and_outcome_reply_losses_read_back_once`、`test_restart_unknown_and_no_outcome_attempts_can_be_superseded`、`test_no_outcome_pre_restart_attempt_is_superseded_without_fake_stop`、`test_candidate_reply_loss_is_read_back_without_duplicate` | confirmation／intent／outcome／candidate 回覆遺失均從 ledger 讀回一次；新下載再次 UNKNOWN 回到原批次，只換未完成項。 |
| C08 | `test_copy_failure_does_not_publish_a_candidate_or_activate`、`test_copy_plan_file_and_directory_fsync_failures_leave_no_candidate`、`test_version_directory_sync_failure_keeps_plan_without_candidate`、`test_verification_and_manifest_failure_leave_batch_unactivated`、`test_candidate_reply_loss_is_read_back_without_duplicate`、`test_activation_reply_loss_is_read_back_without_duplicate`、`test_activation_append_failure_retries_without_new_candidates` | copy／file fsync／directory fsync／verification／manifest／activation 前後故障不啟用半成品；activation 回覆遺失只讀回原事件，append 失敗可重試同 candidate。 |
| C09 | `test_restart_vertical_path_isolated_candidate_and_reopen`、`test_source_change_before_isolation_is_rejected`、`test_old_raw_path_recreated_after_candidate_does_not_change_candidate` | 舊 raw fd 晚到寫入只改舊 inode；新 candidate device/inode/hash 不同；舊 raw path 重建不影響已驗證 candidate。 |
| C10 | `test_copy_failure_does_not_publish_a_candidate_or_activate`、`test_copy_plan_file_and_directory_fsync_failures_leave_no_candidate`、`test_candidate_extra_file_fails_closed_without_activation`、`test_candidate_symlink_hardlink_and_inode_drift_are_rejected`、`test_second_generation_failure_keeps_first_active_unchanged`、`test_second_generation_permission_failures_keep_first_active`、`test_second_generation_hash_and_decode_failures_keep_first_active` | disk full、copy、權限、hash、decode、extra file、symlink／hardlink／inode drift 均不 activation；舊 active 保留，不自動清理 orphan candidate。 |
| C11 | `test_second_generation_replaces_active_media_and_keeps_history`、`test_restart_replay_rejects_v3_prior_attempt_drift`、`test_completion_manifest_readback_and_immutability`、`test_v1_intent_compatibility_and_forged_post_correction_order`、`test_recovery_graph_is_fail_closed` | 舊事件 bytes／completion 不因新 generation 改寫；summary 對一 media 只投影一個 active；v1 相容與 v2 recovery graph 的既有拒絕保留。 |
| C12 | `test_cli_help_success_and_refusal_exit_codes`、`test_cli_unexpected_exception_is_internal_error`、`test_request_precedes_one_child_and_each_capture_uses_new_receipt`、`test_lists_recovers_all_ledgers_without_active_hint`、`test_daily_records.py` 73 tests | CLI 0／2／4／70 語意、單次 capture、active hint 遺失找回與相簿回歸有離線證據。「同一根因兩次無新資訊停止」是 Agent 流程規則，CLI 沒有自動次數 counter；不得把文件規則說成 runtime 已實測。 |

## 正式入口整合

普通路徑仍是：找回帳本 → 核對前景並 `bind` → 處理可接續交易 → `scan start` → 完整盤點／`finish` → `post`／`media` → 符合資格才下載。只有 `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH` 時，才進精確批次例外：

1. 以白話列出列表、受影響貼文／媒體、已完成 sibling、舊位置、新 `versions/gNNNNNNNN/`、空間、缺項與保留項。
2. 只有 Owner 對該批的明示回覆才是同意；Prompt、沉默、逾時與一般「繼續」都不是同意。
3. `restart confirm` 後，若有尚未結束 scan，先明確 `scan interrupt`；再完成新的完整 `scan start --recovery`、page、finish、post／media。
4. 每一項使用新的空白 staging 與 `intent --restart-id`，每次下載控制仍最多一次；全部 candidate 驗證後才單筆 activation。
5. 同一確認批次涵蓋完成前再次中斷；scope、身分、目的地或版本策略改變要重新 preview／confirm。舊 UNKNOWN、活動下載、pending 與舊路徑不解鎖、不清理、不宣稱停止。

`LOCAL_MISSING`、scope 外異常、`EXCLUDED` 與 `PROTECTED_HISTORY` 不因 restart 解除；相簿 Save All／選單／chooser／座標仍不得作為記事本 fallback。

## 實際檢查與結果

環境：macOS 27.2 arm64、`/usr/bin/python3` 3.9.6；工作目錄均為 repo 根目錄。輸出在 `.local/line-backup/tasks/20261108-notes-s2-implementation/`。

| 命令 | 結果 | 證據 |
|---|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py` | 35 tests，OK，7.242s，exit 0 | `test-restart-s2-final.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 171 tests，OK，20.255s，exit 0 | `test-notes-all-s2-final.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 73 tests，OK，320.182s，exit 0 | `test-daily-s2-final.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；列出 `restart` 與 0／2／4／70 契約 | `notes-help-s2-final.log` |
| `PYTHONPATH=src /usr/bin/python3 -B -m py_compile src/line_backup_batch/notes.py tests/test_notes_restart.py` | exit 0 | `py-compile-s2-final.log` |
| `git diff --check` | 報告寫入前 exit 0；本報告與進度寫入後重跑 | `git-diff-check-pre-report.log`／最終 log |

notes 全套輸出中的 `INVALID_--SIGNALS` 與 evidence JSON 來自既有負向案例，最終結果仍為 OK／exit 0。測試只使用專案內隔離的合成資料；沒有把測試替身、簿記 PASS 或檔案解碼當成真實 LINE E2E。

## 精確候選

報告寫入前的公開差異為 10 個路徑；下表保存產品與入口檔案 SHA-256。本報告本身另由 Git tree／commit 綁定，不自填自己的 hash。

| 檔案 | SHA-256 |
|---|---|
| `src/line_backup_batch/notes.py` | `80d0ab5b61b27eee4b5ee9727eef6176ba5a489365ae1651e27f0295fc1170b0` |
| `tests/test_notes_restart.py` | `de9c4b08bd31c43528b191911f48f45ea8104cd51f982a1871a231b80fe393e9` |
| `AGENTS.md` | `f9bbab52c96cbdda8d24c6232a362170fb7e26d1b6c732723a92328917146fd8` |
| `.agents/skills/line-notes-agent-cua/SKILL.md` | `445956c2863c5b3358b836c8f03ce640ef4f6afdfcfe842ba887bbfcc6ac5c8d` |
| `references/download-and-ledger.md` | `ade916615dc34f06cf9e53d53b34d51307b61f18e28f1142052b443431fe03e4` |
| `references/verification-and-recovery.md` | `28af45829c8fbbf6d5809aa3cef9ff7c4cf8f2a4c1fe2cb8b44ac825dccaacf5` |
| `references/gui-inventory.md` | `05e7763eb3c30571dfe2a07950577324fff3e731c6edb90c8de33b0c80289731` |
| `references/evidence-template.md` | `6ca2408474b90d01e30a16968bda4becc4390959ca3ce11b2a6d5bfbb657118e` |
| `references/evidence-decision-cases.md` | `b1ecb2e92afd5601aa3070b6b8a9e513e71cf8ed35d092b430af2f837c261171` |
| `docs/LINE相簿備份_使用手冊.md` | `45fff5285373ec7c448945db38563dd6efba3ccc709b158529837001ab1211de` |

最終 commit SHA 由提交後的 Git receipt 與回覆提供，不在此預填。

## 事實、推論、未知與未完成

- 事實：`SI-U01` 的第二個 generation 路徑、C01–C12 的離線直接案例、正式入口文字與核准回歸均有上述結果。
- 事實：本輪沒有寫入真實帳本／媒體，沒有 GUI `OBSERVED`，也沒有獨立 Acceptance。
- 推論：在合作 CLI、持鎖、candidate 未交給 LINE 的前提下，獨立 inode 與單一 activation 能避免舊 raw 晚到寫入改動 current；這不保證 LINE 服務端去重或任意外部寫入。
- 未知／`NOT_RUN`：真實 LINE／CUA 的 chooser 晚到輸入、取消 chooser、跨 Session 實機恢復、Owner 日常 Prompt 試用、外部副本、真實 videos／mixed attachment、所有模型重複可用性。
- `NOT_RUN`：CLI 對「同一根因連續兩次無新資訊」的自動計數；該限制仍是 Skill 的人工／Agent 判斷規則。相簿真實 GUI 與記事本真機 E2E 也維持 `NOT_RUN`。
- 已知限制：測試中的 copy／fsync／permission／decoder 故障是以 mock 或 synthetic media 注入；不代表磁碟、檔案系統、LINE 或 CUA 每個平台故障窗口都已被實機覆蓋。

## 六項狀態與下一步

```text
PRIMARY_OUTCOME_STATUS: S2_IMPLEMENTATION_COMPLETE
IMPLEMENTATION_STATUS: S2_CANDIDATE_UPDATED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

`PRIMARY` 只代表 S2 實作與本輪離線候選完成；`IMPLEMENTATION` 表示候選已更新，不是產品接受。`REQUIRED` 仍缺真實 GUI／跨 Session／Owner 日常試用；`INDEPENDENT_ACCEPTANCE` 與 `TASK_CLOSURE` 未完成，整體不標 DONE。

下一步由 Owner 決定是否以此精確 commit 啟動適用的獨立檢查，再安排允許重下的日常實機測試。本報告不授權自動啟動 Acceptance、Review、另一個正式角色、真實下載或資料取代。
