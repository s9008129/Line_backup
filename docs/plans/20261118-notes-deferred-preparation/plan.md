# 記事本延後候選預備決策：最小修復計畫

## 目標、授權與基準

以 Agent 讀取同一日常 Skill 自適應完成記事本照片／影片下載，消除「工具列消失後才知道需要候選 2，但其骨架必須事先準備」的指示缺口。不是新增下載入口，也不保證工具列會重新出現。

Owner 明示授權 Leader 與指定 Tester 釐清、指定 Reviewer 審查計畫並修正至通過、派 Worker 平行實作、最後指定 GPT-6 Luna 原生 subagent 梳理上下文及撰寫詳細 commit 訊息，再 add／commit／push。當次只有一個 Worker pane，因此 Worker 與 Leader 以互斥切片平行處理，不新增 pane 或另換模型。Reviewer 只接受自己的審查範圍。

基準：`feature/line-notes-media`，`1aa3568283a0905a5eea8933dac7f2158d7eea1b`。既有 dirty `問題提報單.md` 及 untracked `.playwright-mcp/` 保留、不提交。私有 task 為 `.local/line-backup/tasks/20261118-notes-dispatch-rca-repair/`，已保存 5,371 個帳本／locator／提報單檔案的前置清單與 SHA-256。沒有 GUI 輸入、下載、restart、帳本或照片變更授權。退役 `policies/v4.9.0/` 當次不存在，不重建 Harness。

目前正式產品範圍仍為照片／影片。已問 Owner 是否另擴 AUDIO；回答前只做可獨立完成的控制鏈修復，不把沉默當成音訊擴充同意。若選擇音訊，另提出有界資料模型／驗證計畫供 Owner 確認，本輪不直接加 suffix、AUDIO enum 或 event。

## 證據、根因與保證界限

- **事實：** 現行 HEAD 已有 B1「intent 後延後原第二候選」窄例外，總額仍兩次，舊 UNKNOWN／crash／中斷不適用。不能把本輪所有事故都當作前輪修復已被實機驗證失敗。
- **事實：** Gis 當次 outcome statement 的 stop reason 明寫：候選 1 完成，intent 前未持久保存 candidate-2 request 骨架，intent 後不得補造；因此窄例外不可用，第一筆 outcome 為 UNKNOWN。實際未執行該例外，不是它已通過 GUI gate 後失敗。
- **Tester 核對：** 候選 1 的 request／raw／after 已保存讀回，仍有第二候選額度；B1 用「若預計可能使用」設定預備條件。Agent 沒有準備是執行缺口，但其事先預期沒有持久證據，不能說它明確違反無條件命令。可重複性指示缺口是讓 Agent 預測 transient 才準備。
- **未知：** 工具列消失的精確觸發、延後候選在真實 GUI 的成效、音訊來源種類仍未證實；本輪不播放或為種類取證。
- **歷史：** G 帳本有兩個 NOT_SENT，Gis 有 UNKNOWN，分開保存；receipt 缺席／零計數／空 staging 的稽核 statement 本身不是 OS trace 或排除晚到作用的正面終態。這不是改寫舊 NOT_SENT 的授權，也不據此再恢復或重送。
- **下游：** 目前 classifier 不支援音訊屬已知產品範圍／條件式完成限制，無法解釋沒有檔案前的控制消失。未證明 notes.py 或 helper 有程式缺陷，不修改它們。

## 最小行為變更

1. 將 B1「若預計可能使用」改為客觀準備：候選 1 的 request／raw／after 完整讀回、同 scope／viewer／有效前景、仍有原第二額度，且該方法的安全作用區與映射有證據時，建立 intent 前必須持久保存並讀回既有 statement／request 骨架；不等待對工具列消失的預測。
2. 把可預先處理的目錄、方法、作用區與欄位骨架放在既有 B1 非 GUI 前置中。候選 1 真實 receipt／after 取得後補齊其引用並讀回，才依現有正面控制 gate 建 intent。這不是新增 stability capture／固定等待，不為準備而做額外 GUI 操作。
3. 尚無安全方法、額度為 0 或不明、候選 1 原件不全等情況，保存既有 statement 的「延後候選未備妥及具體原因」。不得假造正面準備或新增候選。**未準備不自動禁止原本可合法執行的直接下載**：只要既有完整歷史／身分／控制與派送 gate 成立，原路可繼續；但控制消失後維持原停止規則，不能臨時補造骨架。其他未解輸入／UNKNOWN 等全局 blocker 仍停。
4. 清楚分開兩份資料：intent 前只保存非派送骨架；尚未取得的 attempt ID／intent event ref 待 CLI 成功與事件唯讀核對後才填入，不猜值、不建 staging、不建真正下載或候選輸入 request。骨架中的候選 2／budget 1→2 是計畫值，準備本身不派送、不消耗額度、不建立 event，也不是 input receipt 或下載授權。
5. intent 後仍須原窄例外全部成立，重新核對安全作用區、映射與身分，才在固定原 task/inputDir 以 attempt ID 導出的 canonical operationId 保存真正 input request 並讀回、送一次 input→直接 after。不能直接重播骨架舊座標。下載仍走原 grounded helper，首次下載呼叫開始或不明就關閉窗口；error／timeout／保存缺口沿用既有停止及 outcome／reconcile。
6. 新增少量情境案例：符合準備條件但不預測 transient；安全方法不足但目前控制可直接下載；intent 後才發現未準備；既有 UNKNOWN／已用兩次／骨架不等於派送。案例不作真人 OBSERVED 或 GUI PASS。

本輪不改候選總額、輸入安全區、前景交接、intent／outcome／restart 語意、資料模型、helper 實作、notes CLI、來源種類、相簿或正式啟動 Prompt。不得增加新的每日啟動步驟、控制器、全域預備狀態機或登錄索引。

## 互斥分工

| 執行者 | 白名單 | 工作 |
|---|---|---|
| Leader | notes `SKILL.md`、`references/gui-inventory.md`；本計畫／公開 report／私有進度 | B1 唯一決策本文；入口只連結預備分流；整合、三條回歸、保護檔比對與 Git 交付。 |
| Worker `w5:pK` | `references/evidence-template.md`、`references/evidence-decision-cases.md` | 同步兩階段準備／request 用法，既有欄位與讀回引用；少量可判斷案例。可跑既有 focused helper tests，不改測試來鏡像措辭。 |
| Tester `w5:pH` | 唯讀指定事故原件 | 根因釐清與證據保證範圍，不改產品、不 GUI，不替實作簽接受。 |
| Reviewer `w5:pM` | 計畫與最終 diff 唯讀審查 | ACCEPT／REVISE、精確 plan hash／行號與可操作 finding；不替實機簽接受。 |

指定 Reviewer 接受精確 plan 版本後才派 Worker，Leader 同時處理另兩檔。共享目錄不得互改白名單；Worker 不 commit/push、不增子代理、不改實際資料。若需要超界、改 GUI 授權或資料語意，停下回 Leader；同根因最多三次有證據嘗試，連續兩次無新資訊停止，不為通過製造空實作。

## 驗證與交付

本次為指示與證據用法修正，沒有新執行邏輯，不寫只比對措辭或複製實作的測試。Reviewer 核對準備分流與兩階段語意；既有 helper 合成測試僅證明 request exclusive/readback、單次輸入與同份 after 保存，不證明 Agent 必定遵循新指示。

整合時執行以下三條，並保存實際 stdout／stderr／exit code：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

另做 Skill validator、git diff --check、相對連結／白名單核對；隔離合成 fixture，保護真實 active locator。每條回歸前後比較 5,371 個指定保護檔的清單與 SHA-256。原始 logs 留私有 task，公開報告不帶私人內容。未執行的 GUI、日常備份、音訊、chooser、跨 Session 與核心可重複使用能力均 NOT_RUN。

六項狀態分列 PRIMARY_OUTCOME_STATUS、IMPLEMENTATION_STATUS、CORE_ACCEPTANCE_STATUS、REQUIRED_VERIFICATION_STATUS、INDEPENDENT_ACCEPTANCE_STATUS、TASK_CLOSURE_STATUS。文件審查、離線回歸、真實完成與帳本歷史不同層次；缺實機核心結果不稱整體 DONE。

完成後依 Owner 指定，以原生 GPT-6 Luna subagent 梳理本輪計畫、diff、實際驗證與限制，撰寫含「意圖」、「做了什麼」、「下一步的建議」、「驗證與結果」的繁中詳細訊息；不自行改選模型或提高 effort，不以請求參數證明 provider identity。若指定模型不可用，回報實際阻塞，不換 LLM 入口繞過。Leader 逐檔 add，核對 staged diff 不含提報單、私有資料或媒體；commit 後 git show -s --format=%B，push 後核對 origin feature/line-notes-media 精確 HEAD 與既有 Draft PR #51，不 merge master、不 force-push。
