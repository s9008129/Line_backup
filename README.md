# LINE 相簿與記事本 Agent 備份

本專案有兩條獨立的日常備份流程：LINE 相簿照片，以及 LINE 記事本貼文內照片／影片。兩者都由 AI Agent、專案 Skill 與原生 Mac Computer Use 執行，但入口、Skill、工具、目的地與永久帳本互不共用；不得把相簿狀態套到記事本，也不得把不同記事本列表混成同一份帳。

## 相簿備份

人工開好 LINE 相簿列表並交接前景，由 AI Agent 使用[相簿 Skill](.agents/skills/line-album-agent-cua/SKILL.md) 查明舊進度、完整盤點、逐本下載與驗證。照片預設放專案 `backup/`，永久紀錄分開放 `backup-records/<列表 UUID>/`。照片複製到外接硬碟並刪除本機 `backup/` 後，Agent 仍能查歷史、跳過已完成相簿。結果未知先查證，中斷採相簿級恢復。

日常入口是[使用手冊的 Prompt](docs/LINE相簿備份_使用手冊.md)。審查文件或整理專案不會啟動 LINE；群組中文名稱不作身分依據。

## 記事本照片與影片備份

Owner 先人工開好單一 LINE 記事本列表，再提交使用手冊的記事本正式 Prompt 並交接當次前景。AI Agent 使用[記事本 Skill](.agents/skills/line-notes-agent-cua/SKILL.md) 自動查詢永久記憶、初始化或綁定列表、完整盤點貼文與媒體，逐貼文、逐媒體下載及驗證，並依紀錄跳過完成項或恢復中斷。媒體範圍只含貼文內照片與影片；留言、貼圖及連結不納入。純文字貼文記為貼文層 `NO_MEDIA`，不是下載完成。

記事本預設目的地是 `backup/記事本/`，永久紀錄獨立放在 `notes-backup-records/<local_list_id>/`；`notes-backup-records/index.json` 只登錄帳本位置，追加式事件才是事實來源。`.local/line-backup/active-notes-task.json` 只協助定位最近任務，不是唯一歷史入口。記事本 CLI 入口為 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes`。不得與相簿的 `backup-records/`、`daily` 或 `active-task.json` 混帳。

記事本一次只處理一個媒體 attempt：下載前先保存並讀回 intent、新空白目的地與禁止重送紀錄，每個 attempt 的記事本當次下載控制最多派送一次；若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不得沿用相簿入口。結果未知先查證，不用新目錄或零計數解鎖；已完成的跳過，整篇完成目錄缺席與目錄內容異常分開處理。正式 Prompt、`NO_MEDIA`、資料保護與恢復規則見[使用手冊](docs/LINE相簿備份_使用手冊.md)。

本次記事本新功能在 `feature/line-notes-media` 開發；Owner 實機測試通過前不合併 `master`，既有主分支相簿流程不受影響。真實記事本 GUI、混合附件 chooser、跨 Session 接續與恢復目前均為 `NOT_RUN`。

## 保留的工具

- `src/line_backup_batch/daily.py`：本地列表、事件、完成與中斷紀錄。
- `src/line_backup_batch/notes.py`：記事本獨立帳本、列表／貼文／媒體交易與恢復入口。
- `src/line_backup_batch/media_verify.py`：照片完整解碼與成對 ffmpeg／ffprobe 的影片驗證。
- `src/line_backup_batch/image_decode.swift`：逐檔 SHA-256 與 ImageIO 完整解碼。
- `scripts/agent_resume/modern_ocr.swift`：選用的離線影像 OCR，不截圖或操作 GUI。
- `tests/test_daily_records.py`：記錄、資料保護、恢復與真實 ImageIO fixture 回歸。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily --help
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
```

工具不操作 LINE、不簽發下載授權，也不獨立證明畫面內容真實。相簿 `daily summary` 的 `ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS` 只代表相簿簿記覆蓋完整；記事本 `notes summary` 的 `all_known_media_complete=true` 只代表已知貼文／媒體投影一致且 `dispatch_blockers=[]`，不提供 `PASS` 或 `sensor_verified` 欄位。兩者與 notes 的 `external_copy_verified=false`、`real_line_e2e=NOT_TESTED`，都不能升格為 GUI、正式 AUTO 或獨立 E2E。

## 唯一核心目錄與分離的備份記憶

`Line_backup` 是唯一核心目錄。`backup-records/` 是跨列表永久紀錄區，`index.json` 僅登錄帳本位置；相簿身分、完成／排除／未知操作與歷史提示，以各列表 UUID 目錄的追加式事件為準。`.local/line-backup/active-task.json` 只定位最近任務，遺失它不等於沒有歷史。日常啟動不查封存、外層舊資料或 Git 歷史。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily groups
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily memory --records-root "$RECORDS_ROOT"
```

`RECORDS_ROOT` 由 Agent 從 `groups` 及已核對列表取得，不由 Owner 填 UUID。`memory`／`summary` 不要求照片 root 存在；整本目錄缺席仍保留完成，另報本機不可用。仍存在的目錄若部分缺檔、內容或身分異常，停止新派送，不重下補帳。外接硬碟不必在線，也不要求另做歸檔登記；外部副本是否完整未經本流程驗證。

記事本記憶是另一套獨立結構：先用 notes CLI 查全部記事本帳本，再讀相符帳本的追加式事件；`index.json` 只登錄位置，`active-notes-task.json` 只協助定位。相簿的 `daily groups`／`memory` 不會把記事本當未登錄相簿，notes CLI 也不得讀寫相簿完成事實。列表、貼文與媒體三層身分不可用中文名稱、日期、總數、序號或單一檔案 hash 跨列表認領。

保留 `backup-records/` 及專案 `.local/line-backup/` 私有證據，不隨照片刪除。舊照片樹內的帳本需先以 `daily migrate-records` 安全複製並讀回，原件保留、舊入口拒絕寫入；新一批目的地使用 `daily destination` 追加綁定，不改寫歷史。操作方法見[備份與恢復](.agents/skills/line-album-agent-cua/references/backup-and-resume.md)。這項分離保障刪除照片區後仍保留紀錄，無法保證整個專案或磁碟遺失後仍可還原。

舊 Harness、交易程式與專屬測試已退役。穩定操作方法在 Skill／程式中，開發歷程在 Git 中；都不需要啟動舊程式。結構化記憶與轉入限制見[紀錄工具](.agents/skills/line-album-agent-cua/references/daily-backup.md)。

相簿記憶位置、轉入結果與驗證界限見[結構化備份記憶](docs/結構化備份記憶.md)。離線測試不表示新的 LINE 實機或跨 Session 恢復驗收已通過；記事本的真實下載、混合照片／影片附件、跨 Session 與 chooser 亦然，均在另行取得正式任務授權及有效前景後才能驗證。
