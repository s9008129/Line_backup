# 記事本跨盤點下載收斂修復

## 目的與原因

以相同 Skill／正式 Prompt 驅動 Agent 接續備份。新盤點是來源觀察，原 intent 與 outcome 是已發生的交易；新 scan 不應單獨使已成功下載的原交易永遠無法完成檢查。

修復前：scope 外舊 DOWNLOAD_FINISHED 被 latest-only gate 拒絕；scope 內 restart intent 又被這筆未決交易擋住。既有 origin validator 仍讀最新 media projection，重新細盤後也會誤拒絕。發布與 resume 重複使用同一 latest-only gate，單改 download-check 不足以修復。

## 本次變更

- 原始來源核對改讀 intent 之前的事件前綴，核對當時完整 scan、post detail、media identity；不改寫舊 scan 或事件。
- 日常 download-check、BASIC 發布與命名恢復使用同一已下載交易檢查。legacy 嚴格 verify 的 latest-only 規則不變。
- 已確認 restart scope 外的舊下載可完成或依明確非媒體 MIME 合法排除，排除項保留 staging。排除項不再阻擋 scan／intent，也不再顯示待 verify。
- scope 內 LOCAL_CHANGED 僅在原確認範圍受保護保留；scope 外異動仍拒絕。restart intent 核對 confirm 後完整卡片覆蓋與 scope 一致性，不要求 scope 外所有貼文先細盤。
- restart progress 只增加唯讀 blocking_attempts；沒有新 CLI、事件種類、授權入口或 Owner 啟動步驟。
- Skill 與 references 改為依 resume 分流。VIDEO identity 下載實際圖片時沿用既有 PHOTO／DOWNLOAD_ONLY 語意，不追加種類更正、不解碼、不證明來源影片完整保存。

## 驗證

命令、退出碼與完整原始輸出保存在專案私有 `.local/line-backup/tasks/20261114-scan-settlement/`。使用既有測試建立合成帳本，沒有寫入真實帳本或操作 LINE。

| 檢查 | 實際結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS，73 tests，321.890s |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | PASS，正常輸出說明 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | PASS，275 tests，37.066s |
| 新增與相關 download-only／restart 整合測試 | PASS，27 tests，4.108s（亦包含於完整回歸） |
| `uv run --with pyyaml python <skill-creator>/scripts/quick_validate.py .agents/skills/line-notes-agent-cua` | PASS，Skill is valid；系統 Python 原先缺 PyYAML，未改專案依賴 |
| `git diff --check` | PASS |

新增案例覆蓋舊 v2 成功下載在新 scan 未細盤／重新細盤、BASIC 發布中斷跨 Session 接續、UNKNOWN／無 outcome 拒絕、open restart 下 scope 外 HTML 排除與 blocking_attempts 收斂、scope 內非媒體拒絕，以及其他貼文待細盤時 scope 可接續。既有嚴格 verify 跨 scan 拒絕與 scope 外 LOCAL_CHANGED 阻擋測試保留並通過。

## 六項狀態

| 狀態 | 結果 |
|---|---|
| PRIMARY_OUTCOME_STATUS | PENDING_OWNER_VALIDATION：修復交付通過離線驗證；真實列表仍待日常確認 |
| IMPLEMENTATION_STATUS | PASS |
| CORE_ACCEPTANCE_STATUS | NOT_RUN：未操作真實日常入口 |
| REQUIRED_VERIFICATION_STATUS | PASS：本次程式與 Skill 離線檢查 |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN：同角色測試輔助與自查不算獨立驗收 |
| TASK_CLOSURE_STATUS | PENDING_OWNER_VALIDATION；不標 DONE |

## 保留邊界與下一步

UNKNOWN、沒有 outcome、被取代 attempt、來源證據不足、staging／檔案漂移、symlink、額外檔、MIME／suffix 不符仍須拒絕。scope 內非媒體仍回 RESTART_SCOPE_NON_MEDIA，不修改確認 scope。原 completion、scope digest、generation 與事件 bytes 不變；不新增同一媒體的下載 intent。

本次成果是程式與 Skill 修復交付，不是整份列表備份完成。依原提報，51 篇中有完成媒體的僅 2 篇、其餘 49 篇待細盤；本次沒有重新觀察這份真實列表。真實舊下載收斂、GUI、activation、completion、跨 Session 實機恢復與真實 E2E 全為 NOT_RUN。Owner 後續沿用手冊中的記事本正式日常 Prompt 與有效前景交接確認，不增加 Harness Acceptance 入口。

兩個測試輔助及提交訊息輔助均以 GPT-6-luna、high 請求派送；這是工具請求參數的證據，不推論 provider 後端身分、token 或費用，也不算獨立驗收。
