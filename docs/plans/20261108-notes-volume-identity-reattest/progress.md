# 目錄 device 漂移診斷進度

## 目標與邊界

Owner 於 2026-11-08 指定 High-Reasoning Reviewer，診斷單一根因：記事本 restart 在第一個 v3 intent 前被 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED` 阻擋。只產出診斷與交接，不改產品、ledger、媒體或操作 LINE。Owner 另明示授權完成後以 GPT-6 Luna helper 整理詳細 commit 訊息，再 add、commit、push 文件成果。

## 已知與新增學習

- 初始分支 `feature/line-notes-media`，HEAD `3cfb068cc83508b308f427cdf69ebcd6b13fbcd4`，工作樹乾淨。
- 原提報基準與候選間只有提報文件差異，產品版本相同。
- 原事故只有一次已記錄的 v3 intent 拒絕；未因換 Session 重置嘗試歷史。本輪沒有重跑該命令。
- 直接讀取 28 個原事件與原任務結果，確認 2 個 v2 intent、1 個 completion、1 個已確認但未 activation 的 restart 批次，沒有新 v3 intent。
- 目前 list directory 的路徑、inode 相符，device 不符。舊完成檔的 inode、size、mtime、ctime、SHA-256 與目錄名稱集合均相符。
- 一組隔離合成對照重現：device 不符足以拒絕 directory gate，亦使 completion 投影為 `LOCAL_CHANGED`。這不是 remount 或 LINE E2E。
- 診斷前後 1,102 個記事本紀錄檔案／active hint 的內容清單不變。
- remount 原因未證實，不能宣稱已排除 clone／volume replacement。
- 最小候選方向是 list-only binding 轉接，維持舊 completion／candidate／staging guard。既有 restart 允許精確 scope 的 `LOCAL_CHANGED`，不必先把舊完成物重新見證成 verified。

## 阻塞與停止

原備份仍阻塞，舊 UNKNOWN 未解，沒有新增派送。產品資料／公開介面／信任邊界需要先有規劃，所以只推薦 `PLANNER_REPLAN`，不自行起下一角色。OPEN_BATCH 的保留、binding 轉接確認與新 recovery scan 順序必須進入規劃。

## 驗證與交付

- 私有 `diagnose.py` exit 0；事件鏈結、檔案 witness、合成斷言與受保護檔案前後內容核對成立。
- `notes --help` exit 0。
- 本輪完整 notes／daily 回歸、解碼、真實 remount、LINE GUI、跨 Session、獨立 acceptance：`NOT_RUN`。
- `issue-analysis.md` 保存實際命令、來源、SHA-256、原始觀察與推論界線、唯一建議路線及六項狀態。
- 文件差異、Luna helper、commit 本體及 push 精確 HEAD 的核對留在本輪私有 `delivery-receipt.md`；本文件不預填推送或模型執行成功。

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_APPLICABLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PASS_DIAGNOSTIC_ONLY; OTHER_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE
```
