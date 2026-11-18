# 記事本延後候選預備決策：交付報告

## 結論與修復範圍

新證據指出，Gis 的 intent 後窄例外沒有被執行：當次停止紀錄明寫，intent 前沒有持久保存第二候選的 request 骨架，因此不能在控制消失後補造。這不是已證實的音訊格式、下載 API 或 notes.py 缺陷，也不是窄例外已通過 gate 後的 GUI 失敗。

本次把 B1 的「若預計可能使用」改成客觀準備條件。候選 1 原件完整讀回、仍有原第二額度、同 scope／viewer／前景連續且安全方法有證據時，intent 前必須保存並讀回骨架，不要求 Agent 預測工具列會消失。這修正了可重複性指示缺口；工具列消失的精確觸發及新指示的實機成效仍未知。

本輪只改四份 Skill Markdown。沒有改 helper／composition 執行碼、src、tests、CLI、event schema、帳本、媒體或正式日常 Prompt。沒有 LINE GUI 輸入、下載、restart 或重送。照片／影片範圍不變；未證實來源為音訊，未擴充 AUDIO。

## 證據與責任分層

- 基準：`feature/line-notes-media`，`1aa3568283a0905a5eea8933dac7f2158d7eea1b`。
- Tester 原件核對：Gis 候選 1 的 request／raw／after 已保存讀回，仍有第二額度；stop reason 明寫未預備骨架。現行 B1 以預測決定準備，可能使正常未預測 transient 的 Agent 失去窄例外資格。
- 執行上沒有準備是事實；但沒有持久證據證明 Agent 事前已打算使用候選 2，不能把有條件命令描述成被明確違反的無條件命令。Skill 的決策缺口與 Agent 執行缺口需分開。
- G、Gis 都沒有持久保存當次 checkout HEAD。G 的時間早於、Gis 的時間晚於前輪 commit，且 Gis 引用新 B1，但這些只支持情境推論；實際執行 HEAD 仍為 UNKNOWN。
- G 的兩個 NOT_SENT 是帳本已保存的事實；零 receipt／零計數與 Agent audit 不是 OS event trace，也不能獨立排除晚到作用。不能據此聲稱已驗證安全恢復，亦不授權改寫舊結果。Gis 的 UNKNOWN 同樣原封保留。
- 音訊 classifier 的不支援是現行產品範圍下的條件式下游限制；沒有實際音訊 bytes／MIME 或 chooser 證據，無法用它解釋派送前控制消失。本輪不播放或為種類取證，不把音訊改名成影片。

原始識別碼、statement、帳本事件、畫面與完整協作紀錄留在專案私有區；本公開報告不重述群組／作者／媒體名稱、帳本 keys、錄影或原始畫面。

## 計畫與協作

[修復計畫](plan.md) SHA-256：`691a141f59e3a6aeebb3d387ae37ed6de5739fd848795fde1dcdb829837b7f97`。

[指定 Reviewer 計畫審查](plan-review.md)：ACCEPT，沒有 blocking findings。接受精確版本後，單一 Worker pane `w5:pK` 與 Leader 平行處理互斥切片：

| 負責人 | 修改檔案 | 內容 |
|---|---|---|
| Leader | notes `SKILL.md`、`references/gui-inventory.md` | 入口指向 B1；依客觀條件準備、保存／讀回失敗停在 intent 前、未備妥原因與額度語意。 |
| Worker | `references/evidence-template.md`、`references/evidence-decision-cases.md` | 兩階段證據用法及 C19–C21 情境案例；沿用既有欄位與 request slot。 |

Tester `w5:pH` 完成指定原件唯讀釐清；Reviewer `w5:pM` 接受計畫後再核對四檔最終 diff；[實作符合計畫審查](implementation-review.md) 亦為 ACCEPT，沒有 blocking findings。Workers 沒有簽發獨立接受。沒有新增 panes、控制器、日常啟動步驟或全域預備登錄。

## 最終行為與保護

1. 依客觀條件必須預備時，骨架保存／讀回失敗就停在 intent 前，不能把 I/O 失敗冒充方法不足而繼續。
2. 缺安全方法、額度不足／不明或候選 1 原件不全時，記錄延後例外未備妥與原因；它不新增對「原本符合所有既有 gate 的直接下載」的阻塞，也不准為準備額外探索。全局 UNKNOWN／未解輸入等仍停止派送。
3. 骨架不是真正 input request。未分配的 attempt ID／intent event ref 待 CLI 成功及唯讀事件核對才補入；不猜值、不預建 staging／event。骨架 budget 1→2 是計畫值，準備本身不耗額、不派送。
4. intent 後只有原窄例外全部成立，才可依當次 fresh 證據重核身分、安全區及 mapping，建立固定 canonical slot 的真正 request 並讀回。不能重播骨架舊點，不能因已準備就自動輸入。
5. 每媒體最多兩候選、下載控制及 chooser 最終確認各最多一次。timeout／error／UNKNOWN／crash 與缺證仍依原規則保護額度；缺 receipt 不等於未呼叫。舊 UNKNOWN、crash、中斷與既有未解狀態不解鎖。

## 驗證與限制

Worker 執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py
```

31 tests，0.974 秒，OK，exit 0；`git diff --check` exit 0。未新增比對措辭的測試；既有合成測試驗證 helper 的 exclusive request／bytes readback／單次輸入／after 保存，不證明 Agent 必定遵循新指示。

Leader 三條最小回歸全部 exit 0，環境為 Darwin arm64、`/usr/bin/python3` 3.9.6：

| 實際命令 | 結果 |
|---|---|
| `env PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 73 tests / OK / 319.619 秒 / exit 0。 |
| `env PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0。 |
| `env PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 330 tests / OK / 41.584 秒 / exit 0。 |

三條回歸前後，5,371 個指定保護檔的清單與 SHA-256 均無新增、缺失或內容差異。完整 stdout／stderr、exit code 與計時留私有 task 的 `regression-1.log` 至 `regression-3.log`、`verification-results.json`；notes 合成 argparse 拒絕案例的 stderr 不代表整體測試失敗。

Skill validator 已通過（沿用專案私有隔離 venv 的 PyYAML 環境，不改系統工具鏈）；六份 Skill Markdown 相對連結檔案均存在，diff check 通過。兩個可執行 helper／composition 區塊與基準 HEAD 逐 bytes 相同。

私有 task `.local/line-backup/tasks/20261118-notes-dispatch-rca-repair/` 保存凍結來源 manifest、回歸 logs、5,371 個指定保護檔的前後清單／SHA-256、Tester／Worker 原始協作、Reviewer 原文與進度。這項比對只涵蓋指定帳本／locator／提報單，不是照片內容、整個系統或外部副本稽核。

真實日常備份、第二候選 GUI 成效、音訊來源／下載、chooser、跨 Session 恢復及不同模型可重複完成能力：全部 NOT_RUN。六項狀態不可用文件接受、簿記、回歸或 Git 推送互相替代。

## 六項狀態

| 欄位 | 狀態 | 範圍 |
|---|---|---|
| PRIMARY_OUTCOME_STATUS | BLOCKED | 指示缺口已修正；真實備份未執行，舊未解交易不變。 |
| IMPLEMENTATION_STATUS | PASS | 四份 Skill 文件，無執行碼變更。 |
| CORE_ACCEPTANCE_STATUS | NOT_RUN | 沒有正式日常 Prompt 的新實機結果。 |
| REQUIRED_VERIFICATION_STATUS | PASS | 三條回歸、validator、diff、相對連結、5371 個指定保護檔比對通過；四檔凍結後未變。 |
| INDEPENDENT_ACCEPTANCE_STATUS | PASS（文件審查） | 指定 Reviewer 接受計畫及實作符合性；實機接受仍 NOT_RUN。 |
| TASK_CLOSURE_STATUS | BLOCKED | 不以文件修正宣稱整體 DONE。 |

## Git 交付與下一步

僅提交四個 Skill 檔與本計畫目錄，既有 dirty `問題提報單.md`、untracked `.playwright-mcp/`、私有證據與媒體不納入。沿用 [Draft PR #51](https://github.com/s9008129/Line_backup/pull/51)，只推 `feature/line-notes-media`，不 merge master、不 force-push。

已依 Owner 指定成功派送原生 subagent（請求 `model=gpt-6-luna`），讀取完整本輪計畫、兩份審查、報告、四檔 diff、實際驗證與保護結果後，撰寫含「意圖」、「做了什麼」、「下一步的建議」、「驗證與結果」的詳細繁中 commit 訊息。主代理已讀回核對內容；提交與推送由主代理執行，實際 message body 與遠端精確 HEAD 的回執留私有 task，最終 HEAD 在交付回覆提供。模型請求、Session 顯示與 provider usage 分開；不以參數冒稱後端身份。

未來實機確認仍用手冊正式記事本 Prompt 與有效前景交接；不另加驗收角色或逐項下令。現有 G／Gis 歷史不因本修復改變；精確恢復／restart 如有需要，仍遵守原先證據與 Owner 確認規則。本輪沒有執行或新增這類授權。
