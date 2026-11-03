# F01 補充原始輸入證據後的診斷

## 結論與唯一下一步

ANALYSIS_COMPLETE。唯一建議改為 PLANNER_REPLAN：Owner 下一步交給 Planner，在另一正式主 Session 為 F01 實機驗證做有界重規劃。原先 TARGETED_DIAGNOSTIC 的「先補原始呼叫」已由新證據包完成，不需再啟動另一位 High-Reasoning Reviewer，也不建議按原方法繼續捲動。

本輪接續原角色，只分析已保存證據，不啟動下一正式角色。產品缺陷、實際底端及列表身分仍未確認；Acceptance BLOCKED 保留。

## 新輸入與版本

新 packet：.local/line-backup/tasks/20261103-notes-f01-input-evidence/；入口 evidence-handoff.md。起始 HEAD f64ba8dc5875fdb88f2e4ac5b9107896ed90cf87，Git status --short 空白。產品候選仍為 23e35798fe08f39eddd4b93372688ee2ed4e6edf；原測試 HEAD 為 5ae930d18a946ab448d4108a15b050d19c07e992。

本輪以 /usr/bin/python3 -B - 逐項重算 SHA256SUMS.txt 的 86 個 repo-relative 路徑，全部匹配，exit 0。初次核對誤將 repo-relative 路徑接到 packet 根目錄，得到 FileNotFoundError、exit 1；按清單實際路徑基準修正後成功。這是本輪核對路徑錯誤，不是證據缺檔。

## 直接證據與因果界線

- raw/cua-calls.json 保存 32 次呼叫及對應輸出。三筆指定錯誤現在都有原始 output，舊報告的「當時交接 packet 缺原始 receipt」已由本次補充解決；舊報告保留其原時間點，不覆寫。
- ordinal 338 保存的 inventory-01.ax.txt hash 為 ebf7c16cc1767e9f7cdfbf19ac1bd946730e515ea942d6340a9047a203398a4f，其樹中 8 是捲軸，10 是縮到最小按鈕。ordinal 345、359 卻仍呼叫 scroll(10, "down", 1)。這是可確認的索引／目標不符；不能將該兩次當成已正確送到捲軸的底端探測，也不能宣稱它們實際觸發了最小化。
- 當時文件 ordinal 98 明文要求依最新 AX 重取索引，且 screenshot-only 後使用完整樹。故這部分是執行沒有遵循既有工具規則，尚不構成必須修改產品程式的證據。
- ordinal 384 已使用列表 1；409 等已用捲軸 8，仍無新位置。490／497 用 8 能做 184→0→184。這排除「所有 scroll 都不能用」，也證明 stale index 不是整段停在 184 的充分解釋。
- macOS 文件已有 page-count 限制；runtime 拒絕 pixels 與此一致。型別含 pixels 不足以單獨認定 runtime 有 bug。PageDown 的 keyNotFound 只證明該鍵名失敗；not-active 則在重取 state 後恢復。三者不合併為一個工具故障。
- 504／520 的正確索引向下輸入後 AX／位置未變，與真實底端相容，仍不足以獨立確認底端、載入狀態或總篇數。媒體自行變化與輸入造成切換也仍未區分。
- 原使用者指令未指定新列表／舊 ledger 或隔離帳本。缺目的地本身不是新 blocker，Skill 已有預設；真正待人工釐清的是有歧義的來源／歷史身分。不得將「Owner 沒寫 ledger ID」誤當日常備份必須手填內部 ID 的新要求。

## 嘗試與停止

32 次工具呼叫不是 32 次修復 attempt。即使不將所有目標變更歸入同一根因，也已可見 345、359 連續無新的列表位移證據，後續又多次換目標探測。本輪不核發新的重試額度、不重新輸入 GUI；不需已退役 controller 或 retry receipt 才能遵守停止規則。完整歸因仍不明者保留 UNKNOWN。

## 給 Planner 的有界交接

範圍只到建立可執行的 F01 實機驗證方案：

1. 列出 Owner 必須釐清的唯一來源／歷史關係；若採隔離測試，必須是明確的來源與資料範圍，不能用新 ledger 洗掉同來源 UNKNOWN／LOCAL_CHANGED。
2. 沿用既有新鮮索引與輸入後觀察規則，讓定位、目標、單位與 receipt 可逐次核對；先評估既有規則是否已足夠，避免只為強調而重複加規則。
3. 定義能區分有效位移、真實邊界、載入未定與工具拒絕的必要證據，保留逐卡覆蓋及原有資料保護門檻；不要求每次媒體區畫面完全一致。
4. 明列停止條件及需要 Owner 決定的驗證範圍；不得自行重播原嘗試或恢復下載。沒有具體程式缺陷，不預定改 notes.py、CLI、事件格式或帳本。

成功檢查是產出有精確來源、必要觀察、正常／停止判準的有界計畫，供 Owner 決定後續角色。Planner 不自行操作 LINE。若計畫證明需改程式／Skill／流程，按適用計畫審查後再由 Owner 啟動 Implementer→Simplicity Reviewer→新 Acceptance；若既有方法足夠且 Owner 能確定獨立新列表與測試範圍，則無須實作切片，可另開 Acceptance。這些是後續條件，不是本輪另推薦第二條路線。

交接資料：本補充報告、原 issue-analysis.md、前輪验收报告.md／acceptance.md、完整兩份私有 packet、原 F01 plan／handoff／implementation、精確候選及測試 HEAD。獨立 CUA server log 未找到不阻止此次結論，因已有 session 原始輸入／輸出；不再要求泛搜日誌。

## 六狀態

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_APPLICABLE_THIS_ROLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: SUPPLEMENTAL_SOURCE_CHECKS_PASS; NEW_GUI_DOWNLOAD_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED; NO_NEW_ACCEPTANCE
TASK_CLOSURE_STATUS: BLOCKED
```

本輪沒有 GUI 輸入、產品測試、下載、帳本 writer 或產品修改。Owner 隨後明示 add／commit／push，本次據此發布去識別化補充報告；原始證據仍留私有任務區，先前報告保留其原判定。Git 交付不代表產品驗收通過。
