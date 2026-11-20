# 記事本 reveal 觀察時序最小修復計畫

## 目標與授權

由 Agent 讀取同一份日常 Skill，依當次 LINE 畫面自適應選擇安全操作，減少 reveal 輸入與 after 觀察之間可避免的模型回合延遲。保留現有控制歸屬、單次派送、永久記憶及檔案檢查規則。

Owner 本輪明示指定 Leader 統籌、Tester 釐清、Reviewer 審查計畫、Worker1／Worker2 平行實作，最後由指定 GPT-6 Luna 子代理梳理上下文與撰寫 commit 訊息，再執行 add／commit／push。這次是開發授權，沒有真實 GUI 輸入、下載、改帳或修改照片授權。

起點：`feature/line-notes-media`，HEAD `2a98a60bee9fdf5f070f49484bb18866ab799f72`。既存 `問題提報單.md` 修改與 `.playwright-mcp/` untracked 均保留，不納入本次提交。原始證據及保護檔案 hashes 放專案私有 task；公開文件只保留遮蔽後判斷。

## 根因與證據界限

- **事實：** 本次沒有 intent、下載控制、chooser 或 completion；最早阻塞是未取得可歸屬下載控制。這不證明 LINE 下載功能失效。
- **事實：** 既有 B1 已要求 reveal 後觀察、正面控制證據才建 intent；已明定 AX 缺失不能否定截圖、不得宣稱 capture 原子或即時。
- **事實：** 提報單指出 raw 檔與 after 圖片 mtime 有 7／48／8 秒差距。這是落檔時間差，不能充當 OS click 或 screenshot capture 的精確時間。
- **Tester 核對：** 事故 transcript 的 C 段在 `persistSingleInput` 完成後另開 shell，之後才呼叫 `captureAndPersist`；B2 也有同樣跨回合序列。B1 精確跨回合順序仍為 `UNKNOWN`。私有 task 保存 Tester 的完整交接及原件定位；公開報告不包含私人 Session 內容。
- **指示／執行落差：** 既有指示存在，但沒有可執行範例把 action 與 observation 綁為同次呼叫；實際 C／B2 序列未實現其時序意圖。未證明工具缺陷、環境阻塞或 Agent 故意違反。
- **推論：** 分離輸入與觀察的模型回合可能錯過短暫工具列；縮圖邊緣的差異是另一個未排除因素。兩者不能寫成唯一已證實根因。
- **未知：** 左上／右上是否必定有效、toolbar 是否 hover-only、實際顯示期限、現行原生 capture latency。
- **修復對象：** 將既有「輸入後觀察」落成可直接執行、可離線檢查順序的短範例，避免靠 Agent 臨場分開呼叫。這能修正操作指示的可執行性缺口，不能保證真實 toolbar 或下載成功。
- **當次工具文件：** 主 Session 唯讀取得的 CUA 文件明列 `click(target: number | Vec2): Promise<void>`、`getAXStateAndScreenshot({emit, disableDiffing})`，並支持同次 action 後取得 state。觀察 API 會內部等待，沒有毫秒 SLA；未列 hover／move。必要摘錄留私有 task 的 `cua-api-evidence.md`，未把當次畫面用作操作交接或 bind 證據。

## 最小設計

1. reveal 前先備妥 input／after observation 目錄及唯一 ID，不在輸入後另開 shell 建目錄。沿用 `persistSingleInput`，只用 `input_phase=NAVIGATION`。在其 `invoke` callback 內以已持久讀回 request 的 target 呼叫一次當次文件支持的 `app.click`；回傳後直接呼叫同一 app 的 `getAXStateAndScreenshot`。兩者位於同一次 CUA runtime invocation，之間不得有模型回合、固定等待、再取 app、寫檔或新輸入。
2. 在記憶體分開保留原生 input return、capture return 與 capture error；callback 回傳原 input return，保留 `undefined` 的既有 typed 表示。capture 失敗不能把已發生的 input 偽報為未送出，也不能觸發再點。
3. callback 返回後由既有 helper 保存 input raw／diagnostic，再用 `persistObservation` 保存剛才取得的同一份 after bytes，不重新 capture。request 寫入／讀回失敗時既不輸入也不 capture；已送出但 capture／落檔失敗時保留 input 證據並停止，不補送候選。
4. 記錄 host call 前／回傳時間與相對順序；來源未提供 OS event 或個別 screenshot 時間則記 `UNKNOWN`。明示同一 invocation 仍是兩個相依 API 呼叫，不是 atomic／0–1 秒保證。觀察充分與否由 Agent 按原 B1 判讀，不以任意毫秒門檻授予 intent。
5. 幾何只作當次候選的來源與安全證據；歷史正向熱點不能泛化為任意邊緣，也不能硬編碼左上或跨 Session 座標。沒有當次安全作用區或工具文件支持就停。
6. 保留既有 `TOOLBAR_VISIBLE`、`TOOLBAR_NOT_SHOWN`、`REVEAL_TRANSIENT`、觀察 `UNKNOWN` 語意；強調 `NOT_SHOWN` 僅是 bounded observation 未見，非「期間從未顯示」。不新增結果 enum、event、schema 或 CLI gate。

主 Session 當次文件已支持此序列；未來執行仍須重新核對當次工具文件。若 API 不可用，保留能力缺口並停止，不猜 API 或尋找另一輸入通道繞過。

capture 或程序若中斷於 raw 落地前，request 仍保留，但不證明 input 未送出；按未解輸入停止並保護該候選額度。記憶體中曾取得 capture 不等於原件已持久保存，不得用缺 raw 或缺 after 解鎖重送。此順序只減少可避免的外部等待，仍保留原生觀察等待及 crash window 的限制。

## 不變邊界

- 每個 list／post／media reveal scope 最多兩次候選；根因最多三次、連續兩次沒有新資訊即停，兩者同時適用。不能換媒體、新 Session 或新目錄重置根因歷史，也不能把三次根因上限誤寫為每媒體三次。
- 舊事故候選額度與停止事實保留；此次文件修復本身不授權新的實機嘗試。後續若要恢復須有決策相關新證據與正式日常入口。
- 不點主內容、播放、時間軸；不以相簿控制作 fallback；不新增 hover／拖曳 API、連續多幀、版本化 viewer registry 或控制器。
- intent 前仍須完整盤點、身分、可見／歸屬／啟用／映射皆成立；intent 後不 re-arm，下載仍走既有 grounded wrapper。
- 不改 `src/`、notes CLI、ledger 格式、六類狀態、completion、restart、相簿 Skill 或使用手冊啟動 Prompt。

## 切片與互斥寫入

| 負責人 | 可修改檔案 | 工作與依賴 |
|---|---|---|
| Worker1 | notes `SKILL.md`、`references/gui-inventory.md`、`references/evidence-decision-cases.md` | 精簡入口摘要；B1 加入相依呼叫時序、幾何假設界限、雙層額度；增加少量可判斷的案例。只連結範例，不複製 helper。 |
| Worker2 | `references/evidence-template.md`、`tests/test_notes_input_helper.py` | 在既有 helper 外加入短而可執行的 composition 範例與穩定擷取標記；測試直接擷取文件程式，驗證操作與保存順序、原始回傳、capture error、不重送及 request gate。原 helper 非必要不改。 |
| Leader | 本計畫、progress、交付報告 | 整合、三條既有回歸、保護 hashes、Git 精確交付；不替 reviewer 簽獨立通過。 |
| Tester | 唯讀原件釐清；完成後可對新範例做離線情境檢查 | 不改產品、不操作 LINE、不改真實帳本；檢查結果分開報告。 |
| Reviewer | 計畫審查；必要修訂後重審 | 以具體 finding、檔案與行號回報；只接受自己的審查範圍，不替真實 E2E 簽通過。 |

Reviewer 接受同一版計畫後，才同時派送兩個 Worker；Worker 不自行 commit／push、不增加 subagent，不改其他人的檔案。發現範圍不足先回報。Owner 明示要求修正計畫至通過；不得為取得通過移除保護條件或無限重送相同方案。

原 Gemini reviewer 曾回報 `Model unavailable`，沒有簽發接受。Owner 隨後明示授權以 herdr 另啟 `codex --yolo` 備援 reviewer，使用與 Leader 相同的模型／推理強度。Leader 當次 pane 顯示為 `GPT-6.1-Sol high`；備援啟動請求使用 `gpt-6.1-sol`／`high`。顯示、請求與 provider usage 分開記錄，不宣稱後端身分。備援獨立審查此計畫，不承接不存在的通過結論。

## 驗證與完成判準

新增離線測試限於具體風險：request 未讀回前不能輸入；一次 input 後直接 capture，raw 持久化晚於 capture；capture error 保留 input return、不再點；capture 成功後原 bytes 被保存，不再 capture；partial persistence 不授予控制可見或交易資格。測試使用 mock app／合成資料，不操作 LINE 或真實帳本。

整合後執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

另核對 Git diff、連結、code fence、變更白名單與受保護檔案 hashes。新範例的離線行為通過只支持時序與保存契約；真實 reveal、chooser、下載、跨 Session 及同一日常 Prompt 的可重複完成能力均為 `NOT_RUN`。Owner 後續沿用手冊正式記事本 Prompt，不加新啟動步驟。

分別記錄六項狀態：`PRIMARY_OUTCOME_STATUS`、`IMPLEMENTATION_STATUS`、`CORE_ACCEPTANCE_STATUS`、`REQUIRED_VERIFICATION_STATUS`、`INDEPENDENT_ACCEPTANCE_STATUS`、`TASK_CLOSURE_STATUS`。計畫接受、實作完成、離線驗證與真實下載成果不得互相替代；適用實機證據缺少時整體不稱 `DONE`。

最後由原生 subagent 明示請求 `model=gpt-6-luna`、不自訂或提高 reasoning effort，先讀計畫、diff、實際驗證與狀態，再撰寫詳細繁中 commit 訊息。主代理逐檔 add 並核對 staged diff，不納入提報單、私有證據或照片。實際 message body 必須包含「意圖」、「做了什麼」、「下一步的建議」、「驗證與結果」；commit 後用 `git show -s --format=%B` 核對。僅 push 本 feature branch，核對遠端精確 HEAD；不 merge master、不 force-push。
