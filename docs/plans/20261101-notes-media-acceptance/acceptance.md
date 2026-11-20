# LINE 記事本照片與影片備份：獨立驗收報告

## 結論

`BLOCKED`。本次以精確候選 `d41a859301d976ca62e11b75d7c8def8577e58f6` 進行唯讀與真實 LINE 前景核對；離線回歸全部通過，但既有未收斂的下載結果仍使後續派送被安全規則阻擋，因此無法完成整份列表下載、影片 E2E、混合附件 chooser 或跨 Session 恢復驗收。Issue #50 另有同一產品基線的 OPEN 異常，涵蓋媒體種類錯記、影片來源到期及 evidence 內容 hash 缺口；本次沒有 fresh reproduction，也沒有把它們誤判為已修復。

本角色沒有修改產品程式、Skill、ledger、completion、LINE 內容或既有下載事實，也沒有重送任何 `UNKNOWN`。發現維持原樣，交由高階模型／Planner 判定根因與下一步。

## 角色、授權與獨立性

- 角色：依使用者指定的 v4.9.0 Acceptance／E2E Reviewer Prompt 執行獨立驗收。
- 授權：使用者明確提交驗收任務、交接 LINE 前景，並授權測試、撰寫 GitHub 驗收報告及對本範圍成果執行 commit／push。
- 邊界：發現異常時不修復；不降低門檻；不建立新下載 attempt；不改寫 ledger；不改用相簿入口或另一個列表。
- 獨立性：本 Acceptance Session 未參與候選實作或修改產品程式；本次沒有使用 helper。候選實作者與 helper 都沒有替本角色提供 acceptance。

## 候選身分與穩定性

| 項目 | 證據 |
|---|---|
| Repository | 本機 `Line_backup` repository root |
| Branch | `feature/line-notes-media` |
| Candidate HEAD | `d41a859301d976ca62e11b75d7c8def8577e58f6` |
| Remote tracking HEAD | 測前與本機相同；報告提交前再次核對仍相同 |
| Worktree／index | 測試前受測產品樹乾淨；測試後只新增本報告，產品樹沒有 tracked、staged 或 unstaged 差異 |
| Product tree listing SHA-256 | `a18257c21be313bd53fc832b33a221efe9d5b847865f1e701ed829f51afcaf19` |
| 與產品實作基線差異 | `b3cf231b8159622c5532520cc8b178182c9d37b9..d41a859` 只改 Skill／規劃／審查文件；`src/` 與 `tests/` 無差異 |

候選在實機核對期間沒有變更。本報告後續的 report-only commit 只新增驗收文件，不改變受測產品樹。

## 核准要求與證據矩陣

核准要求取自 `docs/plans/20261031-notes-media/plan.md` 與對應 Skill。Issue #50 紀錄同 feature branch 的真實異常；本候選自文件基線 `b3cf231` 起，`src/` 與 `tests/` 沒有差異，因此其風險仍適用於本候選，但本報告不把既有觀察冒充成本次新執行結果。

| 編號 | 要求 | 本次結果 | 證據／界線 |
|---|---|---|---|
| R1 | 核對單一指定記事本列表的入口與身分，不以名稱或 OCR 單獨認領 | `OBSERVED` | 真實 LINE 畫面、當次 AX、既有 ledger 與已完成貼文的 `1/9`／`3/9` viewer 交叉核對；只涵蓋當次前景 |
| R2 | 從列表頂端到底端完成盤點 | `PASS`（既有帳本投影） | `scan_coverage=COMPLETE`、187 篇；不代表每篇媒體明細已盤點 |
| R3 | 逐篇盤點所有貼文與媒體 | `BLOCKED` | 只有 4/187 篇有詳細盤點；183 篇仍是 `DETAIL_PENDING` |
| R4 | 一次一項安全下載所有合格照片與影片 | `BLOCKED` | `UNKNOWN=1` 形成 `UNKNOWN_ATTEMPT`；後續合格項不可再派送 |
| R5 | `UNKNOWN` 未收斂前不重送、不建立新 attempt、不改寫事實 | `PASS` | 本次未再點下載控制、未新增 intent、ledger 事件數維持 219 |
| R6 | 照片完成後做穩定檔、非空、SHA-256、ImageIO 完整解碼與 completion 讀回 | `PARTIAL` | 兩張既有完成照片可讀且本次 ImageIO 完整解碼 PASS；下載與 completion 發生於先前候選，本次只作相容性及本機可用性核對 |
| R7 | 影片完成後以成對 Homebrew ffmpeg／ffprobe 檢查影像串流與完整解碼 | `NOT_RUN` | 沒有安全的新影片 attempt；本次沒有影片下載或解碼驗證 |
| R8 | 混合照片／影片貼文、chooser、popup 與前景中斷 | `NOT_RUN` | 本次只做唯讀 viewer 切換；未模擬前景中斷或新的 chooser |
| R9 | 跨 Session 恢復與既有交易接續 | `PARTIAL` | 新 Session 能讀到既有帳本與 blockers；`resume` 顯示兩個待處理動作，但沒有安全執行 |
| R10 | 最終對帳不得把未解項宣稱為全部完成 | `PASS` | `all_known_media_complete=false`、`current_incomplete=46`、`real_line_e2e=NOT_TESTED` |
| R11 | 保留相簿／記事本帳本隔離與既有資料 | `PASS` | 未寫入相簿帳本、未移動或刪除私人媒體；本次前後照片區皆為 2 個檔案 |

## 實際檢查

環境：

- macOS 27.0.1（build 26A434），arm64。
- `/usr/bin/python3`：3.9.6。
- `/opt/homebrew/bin/ffmpeg` 與 `/opt/homebrew/bin/ffprobe`：7.1.1；成對影片工具存在。
- PATH 中另有非 Homebrew 的 `ffmpeg`；未來影片驗證仍須使用文件指定的 Homebrew 成對絕對路徑，不混用 PATH 版本。

| 檢查 | 命令 | Exit | 結果 |
|---|---|---:|---|
| 候選與工作樹 | `git status --short --branch`；`git rev-parse HEAD`；`git diff --name-only` | 0 | branch、HEAD 與乾淨工作樹符合上表 |
| notes CLI 入口 | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 子命令與 0／2／4／70 契約可見 |
| 記事本摘要 | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes summary --records-root "$RECORDS_ROOT"` | 0 | 2 `COMPLETED`、44 `PENDING`、1 `PREVIOUSLY_INCOMPLETE`、1 `UNKNOWN`；blockers 為 `POST_DETAIL_PENDING`、`UNKNOWN_ATTEMPT` |
| 恢復投影 | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes resume --records-root "$RECORDS_ROOT"` | 0 | `NO_NAMING_TRANSACTION`；一個 `RECOVERY_AVAILABLE`、一個 `RECONCILE_REQUIRED` |
| 記事本回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 82 tests，`OK` |
| 相簿回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 tests，`OK` |
| 格式檢查 | `git diff --check` | 0 | 無輸出 |
| 既有完成照片解碼 | `<private ImageIO decoder> "$PRIVATE_POST_DIR" 2` | 0 | `verdict=PASS`、`actualEntries=2`；兩檔均為完整像素解碼 JPEG |
| 真實 GUI 核對 | Computer Use 讀取 LINE 前景、AX 與截圖；正常可逆地開啟／切換／關閉 viewer | — | `OBSERVED`；未按任何下載控制，見下節 |

私有原始 log、截圖與 AX 保存在本機私有任務證據區，不納入 Git；實際路徑省略。公開命令中的 `$RECORDS_ROOT`、`$PRIVATE_POST_DIR`、`<private ImageIO decoder>` 與 `$PRIVATE_EVIDENCE_DIR` 是去識別化占位符。

## 真實 LINE 前景觀察

1. 交接後的 LINE 前景是記事本列表；沒有 chooser、下載進度或其他 modal。
2. 既有已完成貼文的 viewer 顯示 `1/9` 與 `3/9`，與既有帳本記錄的 `viewer_total=9` 相符。
3. 既有完成項的本地兩個 JPEG 仍存在，沒有 symlink；本次重新以相符的 ImageIO decoder 完整解碼為 PASS。
4. 切換到既有 `UNKNOWN` 對應的 `3/9` viewer 時，當次截圖沒有可見工具列，AX 也沒有下載按鈕、tooltip 或可執行下載節點。
5. 本次沒有在該 viewer 按圖片中央、下載圖示、chooser 或其他可能派送的輸入；因此不重送、不新增 outcome／reconcile、不嘗試把 `UNKNOWN` 改成 `NOT_SENT`。
6. 關閉 viewer 後回到同一記事本列表，沒有觀察到下載結果或新檔案；LINE 維持前景。

證據（私有檔案）：

| 觀察 | 截圖 SHA-256 | AX SHA-256 |
|---|---|---|
| 交接後列表 | `74a70cc50cf7bb8ea4dc85b1816bd0ef84a8562b47a4c16e9773c0059c2b7a81` | `4b758fdc1025c8ddea6ed3d30e8d102e034436c6b3b59a86db6cdf0346756522` |
| 既有未知項目 viewer | `67b35e6cd8bc430defbca1df7a7fc8554d88b472f835b8a52d0793dcdd9a0e6d` | `381eb3030973d0914c41335a797d84d6075ac0906bc3387a061b6db37ebeaba3` |
| 測試後列表 | `a6947a03bf9f5663058c6acbe53bfd9d1130b6a7293d1ebb280d195a11af613a` | `910b8a5fbf59441aea9264ffbb40eba05511187b215e22b978d7121c7c78e43c` |

上述只支持當次 GUI 觀察，不是下載控制命中、App acknowledgement、檔案歸屬或整份 E2E PASS。

## 發現

### F1（阻擋級，維持 OPEN）：既有 `UNKNOWN` 使後續所有媒體派送無法開始

- 對應要求：R3、R4、R7、R8、R9。
- 候選行為：帳本保留一筆已派送但結果未知的媒體；`summary` 回報 `UNKNOWN_ATTEMPT`，`resume` 對同一項回報 `RECONCILE_REQUIRED`。
- 影響：即使其餘媒體身分明確、既有完成項也仍可讀，仍不能在本次安全建立任何新 intent；整份 187 篇列表無法完成備份。
- 已知事實：安全拒絕有效、既有事實未被改寫、沒有重送。真正觸發因素仍未定位；本報告不把它誤寫成產品已證實缺陷。
- 需要的決定：由高階模型／Planner 分析可在不重送前提下取得哪些新證據，以及是否調整 `UNKNOWN` 的 reconciliation 或 blocker 粒度。

### F2（證據缺口）：目前 viewer 沒有暴露可語意定位的下載控制

- 對應要求：R4、R8。
- 當次觀察：既有未知項目 `3/9` 的截圖與 AX 沒有下載按鈕或可執行節點；工具列也未顯示。
- 影響：即使沒有既有 `UNKNOWN`，當次也缺少可證明「控制屬於此 viewer、可見、可操作」的派送前置證據；固定座標不能替代該證明。
- 既有交叉證據：Issue #50 顯示成功與失敗 viewer 的 AX 都沒有下載節點，但視覺工具列可見性不穩定；因此本次單次 `OBSERVED` 與既有證據一致，仍不足以單獨證明任何特定 UI 延遲、auto-hide、座標或事件傳遞根因。

### F3（覆蓋缺口）：大部分貼文與影片仍未驗收

- 對應要求：R3、R7、R8、R9。
- 現況：187 篇中僅 4 篇有詳細盤點；已知 20 個影片候選，未完成新的影片下載、ffprobe 串流檢查或 ffmpeg 完整解碼。
- 影響：目前不能宣稱所有照片／影片、混合附件、chooser、popup、前景中斷或跨 Session 恢復已通過。

### F4（已控制，非新缺陷）：本次沒有重現 `summary` 的 EAGAIN

- 本次 `summary`、`resume` 均 exit 0；先前 Issue 所述的 `Resource temporarily unavailable` 本輪未出現。
- 不把「本次未重現」寫成已修復或 PASS；仍保留既有 Issue 的證據。

### F5（OPEN，既有 Issue #50 證據）：同一 viewer 的延後影片特徵可能已被記成 PHOTO

- 對應要求：身分／種類盤點、R3、R4、R7。
- 既有觀察：某篇初次盤點把 19 項全部記為 `PHOTO`；稍後同一 viewer 第 1 項顯示可操作影片滑桿與 `00:00 00:05`，第 18、19 項也有影片特徵，但 ledger 已經寫入 `PHOTO`。
- 影響：媒體種類與後續驗證器選擇可能錯誤；影片候選數與逐篇覆蓋不能只依單次 AX 快照推定。
- 邊界：這是 Issue #50 的既有真實觀察，不是本次新重現；原事件未改寫，本輪也未對該篇建立 intent。根因可能涉及延後狀態、快照時序、thumbnail／viewer 對應或其他流程缺口，尚待 Planner 判定。

### F6（OPEN，既有 Issue #50 證據）：影片下載顯示來源儲存期限已到期

- 對應要求：R4、R7、R8。
- 既有觀察：一篇含多個影片的貼文，對第 1 項建立 intent 並只輸入一次下載控制後，LINE 顯示「儲存期限已到期。」modal；沒有 chooser、進度或檔案，目的地仍為空，outcome 記為 `STOPPED`。
- 影響：至少該項不能產生新檔案；其餘影片尚未逐項測試，不能概括為全部到期，也不能據此完成影片 E2E。
- 邊界：這是既有 Issue #50 證據；本輪沒有重送、改寫 outcome 或建立替代 attempt。

### F7（OPEN，既有 Issue #50 證據）：evidence 文字的截圖 hash 未被自動核對，且有輸出檔名覆寫

- 對應要求：證據完整性、R3、R6、R10。
- 既有觀察：至少三個 page 的 evidence correction 曾包含錯誤截圖 hash；notes CLI 當時只驗證 evidence 檔案存在、非空與 regular file，沒有自動核對文字內 hash。另有 refusal 與成功輸出使用同一檔名而覆寫較早輸出的情形。
- 影響：帳本投影與檔案存在本身不能證明 evidence 文字引用正確；驗收不能把 ledger evidence 直接當成完整證據鏈。
- 邊界：原 page event 與 ledger 未改寫；這是既有異常，本輪沒有重現或修復。

## 未執行項目

| 項目 | 狀態 | 原因 |
|---|---|---|
| 新的照片下載 | `NOT_RUN` | 既有 `UNKNOWN` 阻擋新派送；不得重送 |
| 新的影片下載與 ffmpeg 完整解碼 | `NOT_RUN` | 同上；不能略過 blockers |
| 混合照片／影片貼文的完整覆蓋 | `NOT_RUN` | 尚無安全的新派送與 viewer 覆蓋證據 |
| 新的 chooser、popup、下載完成訊息 | `NOT_RUN` | 本次只做既有 viewer 的唯讀核對 |
| 前景中斷與恢復 | `NOT_RUN` | 未進行會影響來源／輸入的測試 |
| 跨 Session 實際接續或 recovery attempt | `NOT_RUN` | 已讀到 pending 投影，但建立或執行 attempt 會越過本次可接受的唯讀邊界 |
| 183 篇詳細盤點 | `NOT_RUN` | 受既有 blocker 與本次唯讀驗收範圍限制 |
| Issue #50 的種類錯記、來源到期與 evidence hash 異常 fresh reproduction | `NOT_RUN` | 依驗收邊界不重送、不改寫 ledger；既有 Issue #50 證據保留，交高階模型分析根因 |
| 人眼最終驗收 | `NOT_RUN` | Owner 尚未對完整列表結果作最終確認 |

## 六個狀態

```text
PRIMARY_OUTCOME_STATUS: BLOCKED
IMPLEMENTATION_STATUS: NOT_APPLICABLE
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

`REQUIRED_VERIFICATION_STATUS: PARTIAL` 只表示指定的離線回歸、CLI 入口、候選穩定性與既有完成照片解碼已完成；不表示真實下載、影片、混合附件、chooser、跨 Session 或整份列表通過。

## 後續人工交接

1. 保留既有 ledger、`UNKNOWN`、兩個待處理恢復投影及私有證據，不重送或手改狀態。
2. 由高階模型／Planner 分析 F1、F2、F5、F6、F7 的根因與可安全取得的 acknowledgement／reconciliation 證據。
3. 若需要新的下載或恢復 attempt，應先形成符合核准計畫的新授權與驗收條件；本次不自行進入修復或重測。
