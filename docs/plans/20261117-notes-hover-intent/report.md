# 記事本 intent 後工具列消失：修復交付報告

## 交付結論與限制

本次修復的是 Skill 操作契約的缺口：對連續可稽核、同 Session、尚無下載控制呼叫或 outcome 的新 intent，允許將原第二次安全 reveal 候選延後使用。兩次總額不變；Agent 仍從最新原件判斷，再走既有 grounded download helper。沒有新 controller、notes CLI、event schema 或帳本遷移。

這不是下載成功報告。本輪未操作 LINE、未下載、未 restart、未修改真實帳本或照片。事故提報的成功照片／影片與 completion 仍為 0；舊 `UNKNOWN` 完全不適用新例外，也未被解除。真實新例外是否叫回工具列、能否完成日常備份仍 `NOT_RUN`。

## 依據、計畫與審查

- 基準分支：`feature/line-notes-media`；起點 `cbcbb81fb41a17e300eb91975b62466c83311b20`。
- [修復計畫](plan.md) SHA-256：`85eadf61afe0339f014f5d647455d6e33a143039701e08442421ace6a6a3d20d`。
- [指定 Reviewer 計畫審查](plan-review.md)：`ACCEPT`，沒有阻擋問題。
- [指定 Reviewer 實作符合計畫審查](implementation-review.md)：`ACCEPT`，沒有 blocking findings。審查沒有執行測試或 GUI，不代表實機 E2E。
- 原始討論、保護清單、凍結來源 manifest、回歸 logs 與進度留在專案私有 task：`.local/line-backup/tasks/20261117-notes-hover-intent-repair/`。公開報告不包含群組／作者／媒體名稱、錄影、原始帳本 keys 或未遮蔽畫面。

Tester 核對了事故時序：reveal after 曾看見工具列，intent 建立後重新觀察時已消失；事故後錄影支持可見性與游標位置相關。沒有證據分離 timeout、pointer leave、焦點、capture 與 LINE 重繪的因果，因此不能把其中一項寫成已證明的單一觸發。

當次 CUA 文件沒有無點擊 hover／move。只改成「intent 後可 hover」仍不可執行；本方案可在有當次安全證據時使用既有 selected-filmstrip 非播放安全邊緣 click。它是真實 NAVIGATION，可能改變焦點／選取狀態；因此必須在 after 重核，沒有安全區或任一漂移就停。真實成效沒有保證。

## 最小變更

| 檔案 | 最終行為 |
|---|---|
| `SKILL.md` | 指向 B1 窄例外與原兩次總額，不增加日常入口。 |
| `gui-inventory.md` | B1 唯一決策本文：原第二候選可在完整前置下延後至新 intent 後；下載呼叫一旦開始／不明即關窗。 |
| `evidence-template.md` | 沿用 `persistRevealWithDirectAfter`；固定原 task/inputDir，以 attempt ID 導出 request slot，使用既有 `wx` 與 bytes readback；同份 after 才能交 grounded helper。 |
| `download-and-ledger.md` | intent 前 discovery blocker 與 intent 後真實 outcome 分開；不把既有 intent 改成未派送。 |
| `verification-and-recovery.md` | 矩陣同步，所有資格仍歸 B1，不另授權。 |
| `evidence-decision-cases.md` | C1/C14/C15 同步，新增 C18 正向候選、舊 UNKNOWN／crash／額度不足／漂移等停止反例。 |
| `test_notes_input_helper.py` | 三個合成行為測試，直接執行文件中的既有 helper/composition。 |

本次沒有改 helper 的實作或 notes CLI。固定 slot 依既有 request 的 exclusive 建檔防止**同一路徑**重入；不代表工具會跨任意新路徑自動辨認 attempt 或驗證 GUI 授權。不得換 ID／task／路徑，以及來源、完整連續 input、安全區、額度、同 Session／前景等語意判斷仍由 Agent 遵守與留證，沒有新增全域狀態系統。

失敗仍保留原 intent：第二候選 error／timeout、after／保存缺口、控制再消失或漂移，都耗額並停止；按真實證據記第一筆 outcome，不足為 `UNKNOWN`。不重送、不建新 attempt，不以空 staging、零計數或缺 receipt 證明 `NOT_SENT`。

## 協作與實際偏差

Owner 指定的 Tester `w5:p9` 已完成唯讀釐清；Reviewer `w5:pB` 接受計畫後，同時派送 Worker1 `w5:pC` 與 Worker2 `w5:pD`，寫入白名單互斥。

Worker1 在尚未改檔時遇到 `Stream disconnected / Transport error: timeout`，畫面顯示自動重連 3/5。Leader 中止該回合並確認 idle，接手原四檔切片；沒有重開模型或用其他 LLM 入口繞過。Worker2 完成自己的證據範本、交易文件及測試三檔。不能把這寫成兩個 Worker 都成功交付實作。

整合檢查曾發現兩輪文件一致性問題：殘留 intent 後全面封鎖／不記 outcome 的舊通則，以及 intent 前準備與 staging 建立時序混寫。已在同一授權修復範圍修正；Reviewer 依最終凍結版本核對無 blocking findings。未改計畫接受版本或保護界線。

## 驗證

環境：Darwin arm64、`/usr/bin/python3` 3.9.6、Node.js v24.22.1。下列為 Leader 實際執行的三條最小回歸；各命令 stdout／stderr、exit code 與時間留在私有 task 的 `regression-1.log` 至 `regression-3.log`、`verification-results.json`。

| 實際命令 | 結果 |
|---|---|
| `env PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 73 tests / OK / exit 0；319.948 秒。 |
| `env PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0。 |
| `env PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 330 tests / OK / exit 0；41.459 秒。 |

每條回歸前後，比對真實 notes／album 帳本、兩個 active locator 及既有提報單的檔案清單與 SHA-256，共 5,293 個檔案，新增／缺失／hash 異動均為 0。這是指定保護範圍的位元比對，並非照片內容、整個系統或外部副本稽核。notes 測試 log 中出現的 argparse 錯誤是合成拒絕案例；整體 330 項仍 OK / exit 0，不是對真實任務派送失敗的重試。

Worker2 focused 命令：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py
```

31 tests，`OK`，exit 0。三個新測試分別驗證：request 已讀回才 input、同一路徑不可重入；capture error 沒有 after 下載來源；同份 after bytes 交接 grounded helper 且同一下載 slot 不重複 click。這些不驗證真實視覺判斷、語意授權或跨任意路徑的全域防重送。

Skill validator 初次因系統 Python 缺 `yaml` 退出；在私有 task 建立隔離 venv 並安裝 PyYAML 6.0.3 後，以原 `quick_validate.py` 執行，exit 0，`Skill is valid!`。未改系統工具鏈。`git diff --check` exit 0；六份 Markdown 的相對連結檔案均存在；七個產品／測試來源在凍結後 SHA-256 比對無差異。

真實日常備份、新例外 GUI、hover-only UI、即時 popup、混合附件 chooser、實際落點、跨 Session 恢復與所有模型可重複完成能力：全部 `NOT_RUN`。既有永久記憶、下載基本檢查、restart、相簿 ImageIO 與正式日常 Prompt 未改。

## 六項狀態

| 欄位 | 狀態 | 證據與界限 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `BLOCKED` | 開發修復已交付；真實日常下載未執行，舊 UNKNOWN 仍阻塞。 |
| `IMPLEMENTATION_STATUS` | `PASS` | Skill 規則、證據用法、三個測試；指定 Reviewer 接受實作符合計畫。 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN` | 沒有正式日常 Prompt 的新實機備份結果。 |
| `REQUIRED_VERIFICATION_STATUS` | `PASS` | 三條最小回歸、Skill validator、diff、相對連結與 5,293 個保護檔比對均通過。 |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `PASS`（僅文件審查） | 指定 Reviewer 接受計畫與實作符合性；獨立實機接受為 NOT_RUN。 |
| `TASK_CLOSURE_STATUS` | `BLOCKED` | 缺真實核心結果，不稱整體 DONE；不因 commit/push 解鎖 UNKNOWN。 |

## Git 交付與下一步

只提交本次七個產品／測試檔及本計畫目錄；既有 dirty `問題提報單.md`、untracked `.playwright-mcp/`、私有證據與媒體不納入。沿用 [Draft PR #51](https://github.com/s9008129/Line_backup/pull/51)，不 merge master、不 force-push。

提交訊息已由明示請求 `model=gpt-6-luna` 的原生 subagent 讀完整計畫、兩份審查、交付報告、七檔 diff、實際驗證與保護結果後撰寫，包含「意圖」、「做了什麼」、「下一步的建議」、「驗證與結果」。Leader 負責逐檔 add／commit／push 及實際 message body／遠端精確 HEAD 核對；實際提交與推送回執留私有 task，最終 HEAD 在交付回覆提供。模型請求參數、Session 顯示與 provider usage 分開，不宣稱已由 usage 證明後端身分。

後續真實確認沿用手冊正式記事本 Prompt；若仍有舊 UNKNOWN，先遵守既有停止／精確恢復規則。本輪不另授權 restart、不要求用 Acceptance/E2E Prompt 取代日常入口，也不因修復完成就自動下載。
