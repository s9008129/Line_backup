# 提交單遮蔽摘要與來源索引

此頁為本輪規劃引用的可提交摘要。Owner 的 `issue提交單.md` 留在本機，包含私人列表名稱、身分與檔案路徑，原樣保留、不提交。下述 Post1／Post2 只是遮蔽代稱，不可用於認領真實媒體。

## 提交單記錄的現況（本輪未重測）

列表有兩篇、兩個影片，盤點記錄為 COMPLETE；業務狀態為 COMPLETED=1、PENDING=1，另有 LOCAL_CHANGED=1。open restart batch 尚未 activated，整份列表尚未完成。blockers 包含 COMPLETED_FILES_CHANGED、RESTART_BATCH_OPEN、VERIFY_REQUIRED。

| 代稱 | 已提供的證據 | 不能推定 |
|---|---|---|
| Post1 | 新 candidate 已通過當時 verify，舊完成目錄保留 | 不等於批次已 activation 或本機變更已解除 |
| Post2 | 新 attempt 有 DOWNLOAD_FINISHED；verify 回報 exit 4／REFUSED／DECODE_STDERR | 沒有 candidate／completion，不能稱列表完成 |
| Post2 decode evidence | exit 0、stdout_eof=true、progress=end、final_frame=5236、final_out_time_us=202750000；stderr=44400 bytes，只有前 4000 bytes preview | 未保存完整診斷，coverage 尚未執行／保存；不能稱已通過所有檢查 |

Post2 preview 是 null muxer 的非單調 DTS 診斷。提交單將其描述為警告；本輪官方來源核對補充：相同文字在 n7.1.1 `libavformat/mux.c:763-767` 是 `AV_LOG_ERROR` 並回傳 `EINVAL`。這不證明當次所有診斷、最終退出傳播或影片受損情況，也不支持直接宣告無害。

## 本輪直接核對的 repository 證據

產品基線：`2f53bebd0875239312dacb0cb2cf843792a6377d`。行號僅適用此基線。

| 來源 | 事實 |
|---|---|
| `AGENTS.md:52` | 成對工具、有效影像、完整解碼，未另列零 stderr |
| `docs/plans/20261031-notes-media/plan.md:54` | 全部音視訊解碼至 EOF，非零退出／截斷／解碼錯誤不得完成 |
| `docs/plans/20261031-notes-media/handoff.md:49` | 評估 xerror／explode／精確映射與 null，不等同服務端原始位元 |
| `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md:89` | 明文要求 stderr 空白，任何警告／錯誤拒絕 |
| `src/line_backup_batch/media_verify.py:623`、`:858`、`:876` | 保留嚴格 flags；stderr gate 先於 coverage |
| `src/line_backup_batch/media_verify.py:456`、`:587` | 工具版本與 ffprobe 的 stderr 有各自獨立 gate |
| `src/line_backup_batch/notes.py:6419`、`:6574`、`:6752` | persisted decode／probe 條件及 runtime 結果正規化位置 |
| `tests/test_notes_media_verify.py:291`、`:315`、`:343` | clean、有損、非零退出等既有測試；未找到完整 coverage＋exit 0＋非空診斷的政策邊界測試 |
| `tests/test_notes_regressions.py:545`、`:620`、`:685` | clean synthetic evidence、重開與偽造 coverage 負例 |

`git log -S'DECODE_STDERR'`、`git log -S'stderr 應為空'` 與該條文 blame 均指向初始提交 `81d9db40a702a145cd2e2e9004cc01ce6df912e3`；其檔案清單不包含原始 plan。支持「上游要求與實作嚴格代理不一致」的推論，不證明作者主觀動機或完整批准史。

## 官方外部來源

- [FFmpeg n7.1.1 的 DTS 訊息與 log level](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/libavformat/mux.c#L758-L767)：該分支記為錯誤，回傳 EINVAL。
- [FFmpeg n7.1.1 的 xerror](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffmpeg.texi#L2188-L2189)：錯誤時停止退出的選項說明。
- [FFmpeg n7.1.1 的 err_detect](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/codecs.texi#L191-L214)：explode 的解碼錯誤偵測行為。
- [FFmpeg n7.1.1 的 progress](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffmpeg.texi#L969-L976)：程序進度輸出格式；單獨不足以證明每條 stream 的 coverage。

本輪也依 Context7 文件 skill 查詢 `/ffmpeg/ffmpeg`；回傳是 master 的通用退出碼片段，沒有足夠的 n7.1.1 診斷細節，因此不採它作版本特定結論，以上游固定 tag 原始碼／文件為準。

## 本機證據與限制

私有規劃證據放在 `.local/line-backup/tasks/20261110-notes-video-stderr-policy-plan/`。`source-baseline.json` 保存原提交單與關聯程式／規範的大小及 SHA-256，`git-status-before.txt`／`worktrees-before.txt` 保存起始快照。這些是本輪來源完整性證據，不是影片驗證證據。

真實事故證據沿用原提交單的本機索引；本輪不複製媒體、私人 ledger、原始畫面、session ID 或原始檔名進可提交文件，不將它們讀回或重新驗證。現時真實資料是否與提交單一致維持 UNKNOWN。
