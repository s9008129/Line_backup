# 給實作 Agent 的直接指令

```text
請在 /Users/hsiaojohnny/dev/Line_backup 實作本目錄 plan.md 的 LINE 新備份命名與分層，並完整遵守本 handoff.md 及專案 AGENTS.md。先檢查 repo、branch、HEAD、Git 狀態、現有程式與私有任務入口；保留所有無關變更。先讀 .agents/skills/line-album-agent-cua/SKILL.md、相關 references、src/line_backup_batch/daily.py 和 tests/test_daily_records.py。以最小可驗證變更完成程式、Skill、手冊與測試；不要操作 LINE 或真實照片，除非另有具體任務授權及有效前景交接。不要修改或遷移既有照片、覆寫事件、清除 UNKNOWN、重送或改變群組／相簿身分判斷。實作可中斷、安全接續的命名及名稱校正；完成隔離回歸後安排未參與實作的人或 agent 獨立驗收。若獨立驗收、實機驗收或必要能力不可用，據實標示未完成，不偽稱 DONE。依本文件逐項核對、記錄證據並回報六個狀態。
```

## 任務與已決定事項

- 使用者要求新的備份以 `根目錄／群組名稱／相簿名稱／相簿名稱_序號.副檔名` 顯示。名稱以實際交接畫面的 OCR 結果為準；不要求逐本確認。完全讀不到名稱時才問使用者；錯字由使用者透過校正工具修正。
- 既有備份保留、不遷移。原始檔名按 Python 字串的確定性升序排序，序號從 1 起、至少三位；相同影像內容仍各保留一檔。副檔名原樣保留。若名稱必須消除碰撞，使用最後實際的相簿目錄名作照片前綴，確保目錄與照片易於對照。
- 對同名或標準化後同名的不同相簿／群組使用可讀的 ` (2)`、` (3)` 等後綴；依已綁定的本地身份選擇既有目錄，不能因名稱相同認領別人的目錄。恢復使用可讀的 ` (恢復 2)` 等不同空白相簿目錄，且保留前一次目錄。
- 將 OCR 顯示名與 `album_key`、`local_group_id`、`context_id` 分離。名稱不是群組搜尋、列表選擇、歷史合併、相簿去重或授權證據；畫面不可靠或身份歧義時照原流程停止。
- 使用者明確取消本計畫的獨立 review，沒有取消實作後的獨立驗收；實作者不能自評冒充獨立通過。

## 現況與相容要求

- `DailyRecords.initialize` 以根目錄的路徑、device 與 inode 綁定 `backup-records/group.json`。保留根目錄及綁定，不把它移進群組目錄；`backup-records` 繼續作為事件唯一來源。
- `album_key()` 只接受 `start_date`、`end_date`、`expected_images`、`visual_key`；不要直接將名稱加入 identity 或改變舊 key。`intent()` 目前在 `albums/<attempt UUID>` 建立目的地並記錄不可重送；新目的地必須仍在首次 dispatch 前建立、保存並讀回。原 `UNKNOWN`、恢復及一次一本規則不變。
- `completion` 保存目的地和逐檔 manifest；`status_map()` 會依目的地、檔名、大小、mtime、ctime 檢查完成檔。改路徑／檔名後若未提供受驗證的新投影，舊驗證會失效。保留原事件與證據，以追加式事件及確定性投影支援新路徑；舊完成事件照舊檢查。投影須先讀取完整事件鏈並驗證校正關聯，再對最新有效路徑做檔案檢查，不能在逐筆重播時先檢查已合法搬移的舊路徑；未完成校正只能進入受保護的恢復路徑，不得視為正常完成。禁止修改、刪除或重算舊事件以掩蓋變更。
- `verify_directory()` 做三次穩定取樣、數量檢查及 ImageIO 解碼；改名完成後再次執行它。SHA-256 證明本機前後內容一致，並不證明與 LINE 服務端原始位元一致。
- `scripts/agent_resume/modern_ocr.swift` 是既有離線 OCR，只讀取已保存影像，不截圖、不操作 LINE；其 confidence 未校準。由 Agent 根據當次畫面脈絡擷取文字，不將 OCR 文字當身分證明。
- 本 repo 沒有可用的 v4.8 controller、schema 或 stage packet。此文件是人工交接，沒有 frozen machine contract、controller receipt、正式 IMPLEMENT／AUTO PASS 或平台隔離保證；不要自行建立替代框架或偽造這些結果。

## 實作契約

1. **允許變更：**`src/line_backup_batch/daily.py`、`tests/test_daily_records.py`、`.agents/skills/line-album-agent-cua/SKILL.md`、`.agents/skills/line-album-agent-cua/references/backup-and-resume.md`、`.agents/skills/line-album-agent-cua/references/daily-backup.md`、`.agents/skills/line-album-agent-cua/references/inventory.md`、`docs/LINE相簿備份_使用手冊.md`；確有必要時可新增 `src/line_backup_batch` 與 `tests` 內專用檔案。其餘產品路徑不在此交接範圍；需擴大時先停下說明。
2. **名稱處理：**保存可顯示名稱、實際安全路徑名稱、來源及身份綁定。安全處理斜線、NUL、控制字元、`.`／`..`、隱藏名稱、空白、macOS 大小寫與 Unicode 正規化碰撞，以及路徑元件長度；禁止路徑逃逸、符號連結及覆蓋。名稱清理後若空白或無法安全表示，請使用者提供名稱，不捏造。
3. **介面：**在現有 CLI／方法增加取得及持久保存群組與相簿名稱、準備新目的地、完成後命名，以及使用者可操作的群組／相簿校正入口。校正介面以 CLI 參數接受新名稱與可由 `memory` 查得的相簿識別，不要求使用者編輯 JSON；提供清楚的 `--help` 和手冊範例。維持既有 CLI 與舊事件向後相容，不改變工具 `dispatch_authorized=false` 的意義。
4. **下載後命名：**只有明確 `DOWNLOAD_FINISHED`、預期數量相符且原始清單穩定時才開始。先保存完整原名／目標名／大小／SHA-256 對照和交易狀態並讀回；逐步使用同一檔案系統上的不覆寫操作，確保新舊名稱互相衝突也不會丟失檔案。每次持久化後可辨識中斷點；所有檔案命名完後做完整驗證並追加 completion。完成前失敗不得宣告完成或重新派送 Save All。
5. **校正：**只處理本規則產生且有完整驗證與明確身分綁定的備份。群組校正必須涵蓋該群組所有受影響的新格式相簿與相應路徑投影；相簿校正同步更名資料夾及照片前綴。執行前完整核對來源及目標、逐檔 hash 與有效完成狀態；有活動、未知或未釐清 attempt、舊格式／外來項目、衝突或不一致則停止，不對部分集合宣稱成功。原完成事實不可變；新事件要可追溯至原完成及每一筆前後對照，並保存重新驗證證據。
6. **交易與恢復：**沿用根目錄鎖與追加式紀錄，將操作意圖、逐步進度、最終驗證 durable 保存並讀回；先核對再改名，防止覆寫和競態。中斷後檢查 journal 與實際檔案 hash，只有來源／目標狀態唯一且一致時才能安全接續；不確定、資料異動、缺紀錄、符號連結或衝突即 fail closed，保留證據與所有檔案。不得用重置事件、忽略狀態或重下照片恢復。
7. **證據與隱私：**任務原始證據放專案私有 `.local/line-backup/` 任務目錄，白話 `progress.md` 記目標、阻塞、嘗試、學習與下一步。不得把真實群組／人名、照片、原始檔名、授權或未遮蔽證據納入 Git 或公開報告。

## 測試與驗收

- 加入隔離 fixture 測試：群組／相簿分層、既有根目錄與舊事件相容、名稱與 identity 分離、OCR 無結果、非法及過長名稱、大小寫／Unicode／同名碰撞；驗證不以名稱錯配不同列表或相簿。
- 測試原名排序、序號寬度、不同副檔名、相同內容多檔、改名前後逐檔 hash、驗證失敗、恢復 attempt 的新空目錄及原 attempt 保留。
- 測試群組／相簿校正、群組多本相簿投影、舊格式拒絕、直接 Finder 異動拒絕、未釐清 attempt 拒絕、目標存在不覆寫、符號連結及路徑逃逸拒絕；模擬每個持久化／改名邊界中斷後安全接續或 fail closed。
- 執行 `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py`，另執行實際新增的必要測試；記錄環境、實際命令與退出碼。使用現有相容 Swift SDK，不更改系統工具鏈。
- 獨立驗收者不得參與計畫以後的實作，須檢查實際變更及證據。此驗收若不可用，記 `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`、`TASK_CLOSURE_STATUS=BLOCKED`，不可宣稱 DONE。離線 fixture 不等於真實 LINE 多本下載、即時 popup 或跨 session 恢復；實機未獲授權時記 `real_line_e2e=NOT_TESTED`。

## 授權與報告

使用者授權依計畫做本機實作和隔離測試；此 handoff 本身不是 LINE GUI、Save All 或修改真實備份的授權。必要的架構、資料安全、公開介面、驗收標準或範圍變更須另行提出有界計畫。遇到實際身分不明、工具拒絕、寫入衝突或不明派送，停止依賴該前提的動作，不換入口繞過。

最終分開回報 `PRIMARY_OUTCOME_STATUS`、`IMPLEMENTATION_STATUS`、`CORE_ACCEPTANCE_STATUS`、`REQUIRED_VERIFICATION_STATUS`、`INDEPENDENT_ACCEPTANCE_STATUS`、`TASK_CLOSURE_STATUS`；列出事實、推論、未知、實際命令及限制，不補造 PASS。按 AGENTS.md 保留無關工作並檢查 Git；後續 commit／push 的授權以當時使用者指示與專案規範為準。
