# 記事本下載防錯：根因與實作交付

## 目標與根因

Owner 已確認三項修復並明示實作、commit/push；起始分支 `feature/line-notes-media`，HEAD `8d864a1babb0dbd9b76f0cdba3c61f27497842d1`，工作樹乾淨且遠端對齊。

保留 AI Agent 觸發 Skill、自適應判讀 LINE 畫面及選擇下一步；小工具只核對證據、記錄及一致性，不增加控制器、常駐服務、固定座標或 Owner 啟動步驟。

- P3 候選點在報告量測的視覺區域外，是定位證據不足；沒有 native hit-test，不能定案為原生命中失敗。
- 原保存 helper 沒有幾何 gate，且讀回後仍將原可變物件交給任意 invoke。按原保存契約正常運作，不能阻止 Agent 選點錯誤。
- 原 restart 規格及測試允許同批次以無 outcome/UNKNOWN 連續建立替代 attempt。每個 attempt 一次不等於媒體不重派，缺少 confirmation 前後邊界；Owner 本輪明示收緊此規則。
- 舊 completion、current-scan media 狀態及新 restart attempt 結果是不同維度；摘要 scope 不明且舊完成會遮蔽新未決，容易誤讀，不能據此宣稱原事件損壞。

`undefined` 同時出現於成功與失敗，不能判斷派送；較晚的 native pipe 錯誤不是前兩次下載無結果的已證實原因。PHOTO/VIDEO 差異不授權改 key、改歷史或重下。

## 最小變更及資料邊界

1. 現有文內 helper 補下載專用入口，Agent 仍提供當次控制區域與映射；工具檢查來源 bytes/hash、幾何及 target 一致性，從保存讀回內容產生一次呼叫。這不證明框選正確、native 命中或 OS 隔離。
2. 既有鎖內投影本批次 confirmation 後所有未決 v3，阻擋新 intent/activation；保留原 attempt 的 outcome/reconcile/基本檢查。confirmation 前精確 scope 的首次替代仍可用，舊歷史保持可讀。
3. 摘要只補 scope、全部已知 media 計數及本批次未決清單，保留既有欄位與 ledger schema。原正式 Prompt 與日常入口不變。

不操作真實 LINE、ledger、媒體、P3 重送或 activation。不把離線測試當實機 E2E 或獨立接受。

## 協作與證據

Owner 最新指定 Herdr Codex CLI BYOK `deepseek-v4.1-flash:1017`、`max`。原生助手已停止；其未完兩檔修改由新程式 Worker 接手。新 Worker `notes-fix` 在 `w2:p8` 處理程式/helper/tests，`w2:p6` 僅寫三份 Skill 文件，主代理整合與回歸。Herdr 啟動 argv 是請求參數證據，不證明 provider 實際後端與 usage；不宣稱成本節省。

原始命令輸出、exit 與進度保存於專案私有 `.local/line-backup/tasks/notes-safety-fix-20261115/`。正式角色仍由 Owner 決定；Worker 回報與主代理自檢都不是獨立接受。

## 驗證與狀態

主代理在所有 Worker 停筆後執行以下計畫要求的回歸：

| 實際命令 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS，73 tests，319.196s，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | PASS，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | PASS，293 tests，36.632s，exit 0 |
| `git diff --check` | PASS，exit 0 |

Worker 另回報 helper 16 項與 restart 45 項測試通過，均包含於主代理的完整記事本回歸，不重複累加。完整 suite 的 argparse 錯誤文字來自預期拒絕案例，最終結果為 OK。Worker 初次 restart 測試曾遇舊 action 字串斷言，更新為新契約後通過；未放寬產品 gate。

實作含零次 click 拒絕、來源及映射原件核對、request 突變防護、原生 undefined 忠實保存、同媒體及跨媒體未決阻擋、拒絕時零新增 staging/事件、舊完成不遮新未決，以及舊版多次替代事件仍可回放。舊 history validator、ledger schema、相簿程式及正式 Owner 啟動 Prompt 未修改。

整合期間將未完成切片誤放在 `_restart_attempt_scope` 的 gate 移到 activation，避免阻擋 outcome/reconcile；映射證據可獨立於 screenshot，避免限制 Agent 的當次判讀。下載 wrapper 的示例全為合成值，不可照抄為定位座標。

## 六項狀態與未測範圍

- `PRIMARY_OUTCOME_STATUS=PARTIAL`：三項軟體修復與離線回歸完成，P3 真實結果仍未知。
- `IMPLEMENTATION_STATUS=PASS`：本次有界程式、Skill 與測試切片完成。
- `CORE_ACCEPTANCE_STATUS=PASS`：限本次離線行為證據，不代表正式實機接受。
- `REQUIRED_VERIFICATION_STATUS=PASS`：計畫三條最小回歸及 diff 檢查通過。
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`：Worker 測試與主代理自檢不是獨立接受。
- `TASK_CLOSURE_STATUS=BLOCKED`：P3 及完整日常備份結果未收斂，不稱整體 DONE。

真實 LINE 影片下載、原生 hit-test、chooser、跨 Session、全列表備份、真實 ledger 更正、P3 重送與 activation 均 NOT_RUN。本次不操作這些資料；後續以原正式日常 Prompt 與有效前景取得實機證據，不能用本次 Git 交付解除 UNKNOWN。舊版 superseded UNKNOWN 若受 latest-only reconcile 限制，保留證據並另報精確資料阻塞，不改歷史或擴寫更正入口。
