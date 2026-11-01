# Issue #50 計畫審查交接 v1

## 任務與精確版本

- 本次角色 Planner；正式交付是同目錄 plan.md v1 與本文件。兩者由同一 Agent commit 識別，審查者先用 git log／git show／status 核對實際提交；不要把產品基線當成文件提交。
- 產品基線：feature/line-notes-media，`b3cf231b8159622c5532520cc8b178182c9d37b9`；起始工作樹與暫存區乾淨。
- Owner 選擇：先建立可靠證據流程，舊 UNKNOWN 無新證據保留；沿用既有 CLI，僅補記事本 Skill／references、證據範本及判定案例。
- 本次實際新增只有規劃與交接文件；不修改產品、Skill 或測試，不操作 LINE 或真實帳本。Owner 已明示本次文件 commit／push；不包含 merge、force-push 或其他正式角色派送。

## 給另一位 Agent 的審查任務

請由 Owner 在獨立主 Session 啟動計畫 Simplicity Review，先讀 AGENTS.md、適用 4.9 政策、本文件與 plan.md。保持唯讀產品邊界，不實作、不修復、不重測真實 GUI、不操作帳本，不替本計畫預填 acceptance。

重點核對：

1. 目標是否以證據流程改善為限，沒有承諾解開既有 UNKNOWN 或關閉整個 Issue。
2. 是否沿用既有 reconcile 出口，保持同一列表帳本的序列化與晚到結果保護。
3. 矩陣是否清楚區分定位、input receipt、App acknowledgement、下載結果、檔案完整與 completion；timeout、空目錄與缺 marker 均不推 NOT_SENT。
4. 文件切片能否在不增 controller、schema 或公共介面的前提下完成；若提出阻擋項，請指出具體必要條件與證據，不以風格或抽象完整性擴張需求。
5. 離線規則檢查與真實能力驗證是否分開；未知能力、原始觸發因素及未測範圍是否誠實保留。

若範圍、候選或風險有實質變更，交 Owner 決定下一步與須重做的檢查。拒絕或有未解 blocker 時保存證據並停止，不自動啟動 Implementer。

## 必須傳遞的證據

- 同目錄 plan.md、本 handoff.md 與包含兩者的精確 commit。
- 私有原分析：`.local/line-backup/tasks/20261101-issue50-high-reasoning-review/issue-analysis.md`；該目錄另有原證據 manifest 與六項引用 hash 核對結果。本輪未把這些舊結果冒充重新全帳稽核。
- Issue：<https://github.com/s9008129/Line_backup/issues/50>，含補充留言 6555471050；Issue 的舊說法應與本輪較精確的證據界限一併看待。
- Owner 原影片：SHA-256 `54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6`。私有來源位置不公開，審查若需原件由 Owner 在本機提供；示範片並非失敗當次。
- 來源 PTS 影格：`.local/line-backup/tasks/20261101-issue50-replan/video-cache/` 的 `*source-pts.jpg`。`overview.jpg` 是初始重採樣預覽，不用其標籤當原始精確時間。
- 原截圖與保存輸出位於 `.local/line-backup/notes-20261101-1121/`；以 plan 的指定項核對，不廣搜私人資料、不載入真實帳本。檔名宣稱不替代圖像內容，成功第 2 項與失敗第 3 項的保存控制圖都未呈現工具列。
- 當次規劃落檔檢查與進度放在私有 `.local/line-backup/tasks/20261101-issue50-replan/`，不提交私人畫面或原始資料。

## 已知、未知與審查後路由

已知：既有狀態機有合法出口，證據不足才無法選終態；示範片可看到工具列顯示變化、影片載入、chooser 與照片完成提示。UNKNOWN 的 blocker 為同一列表帳本。

未知：原始 click 為何未產生可判結果；平台是否提供足以證明 NOT_SENT／STOPPED 的 receipt；真正混合附件與跨 Session 實機能力。示範片與新流程不回填舊 attempt。

其他 Issue 問題繼續保留：媒體種類矛盾、來源到期、EAGAIN、引用 hash／輸出覆寫及詳細盤點缺項。審查此計畫不代表這些已解。

下一個人工步驟：Owner 啟動計畫 Simplicity Reviewer。通過後由 Owner 決定啟動 Implementer；首個完整文件候選後再由人啟動 implementation Simplicity Review。若已無剩餘實作，不重開 Implementer 或重複同一審查。真實能力診斷或備份需另有適用任務與有效前景。

## 六狀態

```text
PRIMARY_OUTCOME_STATUS=PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=BLOCKED
REQUIRED_VERIFICATION_STATUS=BLOCKED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=BLOCKED
```

未執行為 NOT_RUN；影格觀察為 OBSERVED；文件與 Git 檢查不構成產品 PASS。不得以本交接作為 GUI、解除 UNKNOWN 或後續角色的自動授權。
