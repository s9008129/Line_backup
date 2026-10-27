# LINE 相簿 Agent 備份

人工開好 LINE 相簿列表並交接前景，由 AI Agent 使用[專案 Skill](.agents/skills/line-album-agent-cua/SKILL.md) 查明舊進度、完整盤點、逐本下載與驗證。未另指定時預設保存在目前專案根目錄的 `backups/`；專案搬移後若舊紀錄綁定不符，先保護原件並停止接續。已完成的不重下，結果未知先查證，中斷採相簿級恢復。

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

`Line_backup` 是唯一核心目錄。`.local/line-backup/active-task.json` 指向本專案 `backups/backup-records`；相簿身分、完成／排除／未知操作與身分未明的照片提示，保存在其中的追加式 JSON。日常啟動不查封存、外層舊資料或 Git 歷史。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily memory --root "$PWD/backups"
```

這個唯讀指令投影目前記憶；事件仍是唯一狀態來源，不另存一份可變游標。歷史來源只在轉入時評估，後續直接讀已保存的事實。照片與逐檔完成證據留在本專案，異動時停止、不重下。未釐清的照片提示只保護可能相符項目，不擋住無關相簿，也不當成跨列表完成證明。

舊 Harness、交易程式與專屬測試已退役。穩定操作方法在 Skill／程式中，開發歷程在 Git 中；都不需要啟動舊程式。結構化記憶與轉入限制見[紀錄工具](.agents/skills/line-album-agent-cua/references/daily-backup.md)。

記憶位置、轉入結果與驗證界限見[結構化備份記憶](docs/結構化備份記憶.md)。離線測試不表示新的 LINE 實機或跨 Session 恢復驗收已通過。
