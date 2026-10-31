# LINE 相簿 Agent 備份

人工開好 LINE 相簿列表並交接前景，由 AI Agent 使用[專案 Skill](.agents/skills/line-album-agent-cua/SKILL.md) 查明舊進度、完整盤點、逐本下載與驗證。照片預設放專案 `backup/`，永久紀錄分開放 `backup-records/<列表 UUID>/`。照片複製到外接硬碟並刪除本機 `backup/` 後，Agent 仍能查歷史、跳過已完成相簿。結果未知先查證，中斷採相簿級恢復。

日常入口是[使用手冊的 Prompt](docs/LINE相簿備份_使用手冊.md)。審查文件或整理專案不會啟動 LINE；群組中文名稱不作身分依據。

## 保留的工具

- `src/line_backup_batch/daily.py`：本地列表、事件、完成與中斷紀錄。
- `src/line_backup_batch/image_decode.swift`：逐檔 SHA-256 與 ImageIO 完整解碼。
- `scripts/agent_resume/modern_ocr.swift`：選用的離線影像 OCR，不截圖或操作 GUI。
- `tests/test_daily_records.py`：記錄、資料保護、恢復與真實 ImageIO fixture 回歸。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
```

工具不操作 LINE、不簽發下載授權，也不獨立證明畫面內容真實。summary 的 PASS 只代表 Agent 提交資料的簿記結果；`sensor_verified=false`、`real_line_e2e=NOT_TESTED`，不能升格為正式 AUTO 或獨立 E2E。

## 唯一核心目錄與備份記憶

`Line_backup` 是唯一核心目錄。`backup-records/` 是跨列表永久紀錄區，`index.json` 僅登錄帳本位置；相簿身分、完成／排除／未知操作與歷史提示，以各列表 UUID 目錄的追加式事件為準。`.local/line-backup/active-task.json` 只定位最近任務，遺失它不等於沒有歷史。日常啟動不查封存、外層舊資料或 Git 歷史。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily groups
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily memory --records-root "$RECORDS_ROOT"
```

`RECORDS_ROOT` 由 Agent 從 `groups` 及已核對列表取得，不由 Owner 填 UUID。`memory`／`summary` 不要求照片 root 存在；整本目錄缺席仍保留完成，另報本機不可用。仍存在的目錄若部分缺檔、內容或身分異常，停止新派送，不重下補帳。外接硬碟不必在線，也不要求另做歸檔登記；外部副本是否完整未經本流程驗證。

保留 `backup-records/` 及專案 `.local/line-backup/` 私有證據，不隨照片刪除。舊照片樹內的帳本需先以 `daily migrate-records` 安全複製並讀回，原件保留、舊入口拒絕寫入；新一批目的地使用 `daily destination` 追加綁定，不改寫歷史。操作方法見[備份與恢復](.agents/skills/line-album-agent-cua/references/backup-and-resume.md)。這項分離保障刪除照片區後仍保留紀錄，無法保證整個專案或磁碟遺失後仍可還原。

舊 Harness、交易程式與專屬測試已退役。穩定操作方法在 Skill／程式中，開發歷程在 Git 中；都不需要啟動舊程式。結構化記憶與轉入限制見[紀錄工具](.agents/skills/line-album-agent-cua/references/daily-backup.md)。

記憶位置、轉入結果與驗證界限見[結構化備份記憶](docs/結構化備份記憶.md)。離線測試不表示新的 LINE 實機或跨 Session 恢復驗收已通過。
