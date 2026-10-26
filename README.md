# LINE 相簿 Agent 備份

人工開好 LINE 相簿列表、首次指定保存位置並交接前景，由 AI Agent 使用[專案 Skill](.agents/skills/line-album-agent-cua/SKILL.md) 查明舊進度、完整盤點、逐本下載與驗證。已完成的不重下，結果未知先查證，中斷採相簿級恢復。

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

## 本機資料與封存

`.local/line-backup/active-task.json` 指向當前原始紀錄；`history-index.json` 指向退役流程的原始來源與證據。兩者都要讀，缺失不能當成沒有舊備份。照片及 backup-records 保留原位，不因專案整理重新下載或改寫。

舊 Harness、`harness-development`、頂層 `evidence`、`rev28`、`policies`、config／state 與專屬程式、測試已封存移出。舊 batch 主入口明確拒絕，acceptance CLI 與 `authorization-request` 已退役。[封存查找方法](.agents/skills/line-album-agent-cua/references/legacy-formal.md)保留原來的去重與未知派送保護。

整理結果與驗證見[專案精簡報告](docs/專案精簡報告.md)；先前整併歷史見[整理紀錄](docs/專案整理紀錄.md)。整理與離線測試不表示新的 LINE 實機或跨 Session 恢復驗收已通過。
