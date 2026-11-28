# F01 診斷進度與交付

## 目標與邊界

2026-11-02 由 Owner 啟動 High-Reasoning Reviewer，只診斷 F01 掃描完成偽陽性，交付 [issue-analysis.md](issue-analysis.md)。不修改產品、Skill、測試、舊報告、帳本或照片，不啟動其他正式角色。Owner 已明示只下載照片／影片；文件、PDF、網頁文件不下載。

## 已完成與學習

- 起始分支 `feature/line-notes-media`、HEAD `7a3045aa2ac5b13b4e0b9186f5884c846f402583`；工作樹乾淨，遠端同 HEAD。受測候選為 `260a49612cb3f7570a57f135921b4101e2c8ee99`，報告提交對產品路徑無差異。
- 按需讀取指定 F01 私有原件與 23 份 scan／page 事件，保留來源 manifest；未讀取照片區，未對真實帳本執行命令或寫入。
- 保存圖像的本機目視 `OBSERVED`：舊 page 2 的原件已顯示新別名 P06；舊 rows 卻從 P05 跳到 P07。兩張圖的 hash 都存在於原 page bundle。這將漏點定位到畫面轉成清單，不是最後 key 去重。
- 一次唯讀腳本診斷 exit 0、stderr 為空：舊／新事件在 `_open_scan()` 中分別接受 14／15 篇；23 個 bundle 及保存子件讀取檢查成功；選定 events bytes 前後不變。不代表完整 loader／整本 audit／GUI PASS。
- 唯一路由為 `PLANNER_REPLAN`，只定義 F01 的來源卡片覆蓋與 finish 契約，不合併 M09、`NO_MEDIA`、chooser 或其餘 finding。重掃找到 15 篇不是產品修復。
- 同根因完整修復嘗試歷史未知，不宣稱尚餘次數。本輪沒有 GUI 重掃或重下。

## 驗證與停止點

原始輸出、實際命令、來源 hashes、模型 dispatch／Git 交付證據保存在專案私有任務目錄 `.local/line-backup/tasks/20261102-notes-f01-scan-review/`。文件／Git 檢查依實際結果補記；三項最小產品回歸、即時 LINE 操作、修復後 E2E 與正式 Acceptance 本輪均 `NOT_RUN`。這是診斷文件切片，沒有程式差異。

分析完成後依 Owner 指定，已以原生 subagent 的 `model=gpt-6-luna`、`fork_turns=none` 派送**一個** helper。helper 回報讀完角色規範、本次兩份文件、測試報告相關章節及原 replan D／T5，已產出含四個必要段落的詳細 commit 訊息，主 Session 已讀回。helper 僅協助本角色交付，不簽發獨立審查，不修改產品、不執行下一步建議。dispatch 回傳 task name，未回傳模型欄位或 provider 用量；不從請求名稱推論實際後端身分、費用或節省量。

文件檢查 `verify_report.py` exit 0：兩份文件 UTF-8／換行／空白、相對連結、六狀態、診斷來源 hashes 均符合；Git 核對產品與原報告無差異。本輪只提交兩份去識別化報告，私有證據與 helper 訊息不進 Git。提交／推送的實際命令、退出碼、message 讀回與遠端精確 HEAD 核對另存本任務私有交付紀錄，最終 SHA 隨交接提供；Git 成功不改變下列產品狀態。

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: FIX_REQUIRED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

停止於診斷與獲授權的 commit／push。下一個正式角色由 Owner 決定並另開 Session，Git 成功不解除任何產品 gate。
