# 專屬 Skill 完備性審查（離線）

本文件記錄 Skill 整理，不是 LINE 測試報告。原檔名誤用 E2E，已依 Owner 提醒更正；歷史實機測試報告未因此改名或改寫結果。下文的 YAML／連結／情境檢查都是離線文件檢查。

日期：2026-10-25；task_id：SKILL-COMPLETENESS-20261025；revision：1。

## Owner 意圖與範圍

僅深度確認並優化專屬 Skill。清理／分支整併任務暫停；本輪 Git 交付只保存 Skill 切片。Owner 人工選好相簿列表及目的地、交接前景；不用群組名稱辨識；先完整盤點；相簿級恢復；AI Agent 與提示詞驅動，不新增控制器／P3。

本輪沒有操作 LINE GUI、開啟 LINE 或下載。較早曾誤把「先完整盤點」當成立即實機盤點：實際只呼叫 `cua.getState()`，其 inventory 回 LINE isRunning=false；未呼叫 getApp、未啟動 LINE、未派送輸入。Owner 隨後澄清現在只審查 Skill，因此不再要求交接前景。尚未實機驗證項維持 NOT_RUN。

## 判斷

Skill 已有必要基礎，但尚不能認定可可靠重複完成整體任務。知識文件、可用工具與實際行為驗證要分開判斷。完整盤點已補入必備流程；這不是宣稱真實列表已盤完。

| 要求 | 查核事實與缺口 |
|---|---|
| Owner 前景指定／不用群組名稱 | 既有本地 UUID 與目的地脈絡可保留；原文只禁止「精確中文相等」不夠嚴格，已補成禁止名稱及模糊 OCR 決定對象。接續疑似另一列表才問 Owner |
| 完整盤點與下載清單 | 既有 PR28/PR32 有單次真實捲動經驗；daily.py 有有序重疊與頂底檢查。原 Skill 缺獨立只盤點模式、必須先列總數與清單的明確結束點；本輪補入 inventory.md。完整真實列表的新流程仍未測 |
| 相簿級恢復 | 文件已有保留原檔、新空白目錄、舊完成跳過及 UNKNOWN 不重送。還缺從真實中斷到新 Session 讀回、確認終止、授權及完成的獨立行為驗證；不是缺少原生逐張 resume |
| 新 Session 接續提示詞 | 目前手冊偏重一次備份；尚缺獨立精簡 RESUME 啟動 Prompt，列明紀錄來源、前次結果與唯一下一本。不可依聊天記憶或舊 UI 座標續跑 |
| 歷史紀錄可接續 | 舊 private completion 與新 daily 正規 history 未有通用已驗證對應方法；PROTECTED_HISTORY 會保護舊完成並阻止完整 PASS。缺的是最小來源對帳方法，不能忽略舊資料或再造 issuer |
| 工具可用性 | 現有 CUA 支援 Mac App 的 AX／截圖／scroll。歷史獨立 popup 用到 native window list／指定視窗截圖／OCR，但本次 CUA 公開文件未提供完整 Mac 對應入口；不能保證這個 Session 可直接重現。需要先確認受支援工具，不能以歷史 window ID、shell GUI 或猜 API 代替 |
| 目的地 chooser | 新 Skill 只寫「核對新空白目錄」，缺普通選擇視窗、Go to Folder、目的地不符／取消的簡明操作分支。舊 line-album-backup Skill 有可借用的方法，需依本次工具契約整理，不整套搬入它的舊限制 |
| 驗證工具 | 已存在 image_decode.swift 與 daily.verify_directory：逐檔 SHA-256、完整 RGB 解碼、預期張數、穩定樣本及讀回。不是缺新 decoder。尚應在 Skill 明列工具呼叫、可接受輸出及格式／尺寸限制；可解碼不等於已證明服務端原圖忠實度 |
| Owner Prompt 與舊正式架構 | SKILL.md 第 5 步及 daily-backup 最後一節仍要求舊 formal runtime／一般 issuer。P3 不在本工作樹，不能說它已啟用；但「缺 issuer 所以再開發一般簽發系統」的方向與 Owner 最新 Agent／Skill 產品方向不一致。應先釐清日常 Agent 路徑與保留的舊 formal 研究路徑，再精簡文件；本輪沒有移除可執行 gate 或修改 grant |
| 模式與授權 | 已補 REVIEW／INVENTORY_ONLY／BACKUP／RESUME。審查不操作、盤點不下載，防止再次把流程討論誤認為執行授權 |

## 本輪實際修改

- `.agents/skills/line-album-agent-cua/SKILL.md`：禁止群組名稱／模糊 OCR 作對象判斷；增加模式邊界；完整盤點為下載前必要流程。
- `references/inventory.md`：記錄現有原生四分之一頁捲動形狀、新鮮 AX／畫面、頂底證據、有序重疊、缺頁修補、逐本狀態、總數等式與只盤點 Prompt。例子是已記載工具的呼叫形狀，不宣稱執行過新實機測試。
- 未改產品 Python／Swift／JS、AGENTS、state、grant、ledger、照片或舊驗收結論。未新增依賴、控制器、安裝外部 Skill 或呼叫其他模型審查。

## 適合借用的 Skill 與官方資料

1. 本機系統 `skill-creator`：最適合維護此專屬 Skill。採用「預設 Agent 已有能力」「只寫非顯而易見知識」「主入口簡明、細節按需載入」「腳本僅在重複且確有價值時加入」；不是把 Skill 做成新軟體。
2. `openai-docs`：只協助查核 Codex Skill 的官方行為與最佳實務，不參與 LINE 操作。已實際搜尋並開啟官方頁面。
3. 本機舊 `line-album-backup`：可借用 chooser／Go to Folder、隱藏 partial 檔辨識、目的地與狀態核對；其群組名稱比對、舊 config/state 及 atomic two-click 規則不應整套移入。沒有證據支持它是全世界「最佳」LINE Skill。

官方來源：

- https://learn.chatgpt.com/docs/build-skills ：內建 skill-creator、instruction-only 預設、repo Skill 與 progressive disclosure。
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra ：避免互相衝突及冗長描述、按需載入、避免過度固定模型的路徑。這是 Skill 作者參考，不是本專案已獲官方審核。

## 方法、驗證與限制

唯讀閱讀 Skill、references、手冊、daily.py、image_decode.swift 與舊 Skill 參考；檢查本地 Markdown 連結，全部存在。主 Skill 指向使用手冊的相對連結實際正確，未誤改。

- `git diff --check -- .agents/skills/line-album-agent-cua`：PASS。
- 全部 Skill 本地 Markdown references 存在：PASS。
- `python3 -B <system skill-creator>/scripts/quick_validate.py <project skill>`：BLOCKED，退出 1，`ModuleNotFoundError: No module named 'yaml'`。未安裝依賴或假報 validator PASS；一般連結檢查不能取代官方 validator。
- 真實列表全盤點、popup、chooser、相簿級恢復、跨 Session 接續、逐檔照片驗證：NOT_RUN。本輪沒有新增 GUI 派送。

沒有修復重試迴圈；未使用實作／驗收子代理。沒有聲稱正式外部 Plan／Code Review 或獨立 E2E。未取得目前任務完整官方 schema/controller 資源，不借用舊 lineage 來虛構 gate PASS。

## 下一步

先與 Owner 釐清並精簡「日常 Agent 路徑」與舊 formal 研究路徑的文件邊界，再補恢復 Prompt、舊紀錄對帳及 chooser／工具參考。每項實機驗證先給明確範圍，待 Owner 人工開列表並交接後只測該方法；不以優化 Skill 為由啟用下載。完整盤點目前只有規範補齊，實機驗證留待另外授權。

```text
PRIMARY_OUTCOME_STATUS=SKILL_AUDIT_COMPLETE_GAPS_IDENTIFIED
IMPLEMENTATION_STATUS=INVENTORY_AND_MODE_DOCUMENTATION_UPDATED
CORE_ACCEPTANCE_STATUS=NOT_COMPLETE_FOR_END_TO_END_BACKUP
REQUIRED_VERIFICATION_STATUS=LINKS_AND_DIFF_PASS_VALIDATOR_BLOCKED_LIVE_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN_OWNER_DESIGN_CLARIFICATION_AND_SKILL_GAPS_REMAIN
```

## 後續 Owner 決策與官方作者流程

Owner 已明確選擇「日常 Skill 依 Agent 流程精簡」，要求萃取方法而非引用 PR／分支；之後再次要求安全封存過時資料、所有分支只保留有價值內容並收斂 master。這些新指示取代前文尚待決策狀態；不代表舊外部 review 通過，不授權 LINE 下載。

本輪實際使用本機 OpenAI `skill-creator`，並開啟 OpenAI Build skills 與 Anthropic Skill authoring best practices 官方頁面。採用主入口精簡、按需載入、保留 Agent 判斷自由、只對容易造成資料風險的步驟明訂條件，以及用實際使用情境檢查的做法。

已完成文件調整：

- 主 Skill 改成任務邊界、五步工作流程及必要保護；不再列過時案例／PR／分支，也不要求先開發一般 issuer。
- 成功經驗萃取為文字區開啟、重疊捲動、獨立選單觀察、完整路徑選擇、檔案驗證及取消／不明派送教訓。
- 盤點參考、備份／相簿級恢復、記錄工具按需讀取；恢復 Prompt、chooser／Go to Folder、ImageIO 呼叫與限制已補入。
- 舊正式研究限制另存歷史參考；程式 gate、grant、ledger、VERIFIED 及原測試結果沒有修改。
- 使用手冊改為一份 MODE／保存位置的結構化啟動 Prompt，預設只盤點；不要求群組名稱或填 JSON。

依 skill-creator 的 Independent Forward-Testing 指引，唯一只讀 GPT-6-luna/high 評估者用三個獨立情境檢查會採取的步驟：審查 Skill、盤點有歧義卡片與捲動缺頁、接續已有完成及 UNKNOWN 的任務。三者均判斷不得越界下載，也保留 UNKNOWN barrier。評估指出主流程不應對純盤點要求儲存位置，以及缺頁應先安全回捲修補而非立刻問 Owner；兩項均修正。這是文件前推檢查，不是 formal reviewer／真實 GUI／獨立 E2E。

新的離線檢查：Ruby 標準 YAML parser 解析主 Skill frontmatter／name／description 通過，所有本地連結存在、diff whitespace 檢查通過、Skill 無 PR 數字或工作分支名稱。原 OpenAI Python validator 仍因缺 PyYAML 無法執行，未安裝依賴、不改寫為該 validator PASS。

仍需實測的新能力是完整真實列表遍歷與跨 Session 相簿級恢復；獨立 popup 支援則須依當次工具確認。這些未測項不因文字重整而通過。現有源碼與保護紀錄的使用限制仍有效。

```text
PRIMARY_OUTCOME_STATUS=SKILL_METHODS_RESTRUCTURED
IMPLEMENTATION_STATUS=DOCUMENTATION_COMPLETE_FOR_CURRENT_OWNER_DECISIONS
CORE_ACCEPTANCE_STATUS=OFFLINE_BEHAVIOR_CHECKED_LIVE_NOT_RUN
REQUIRED_VERIFICATION_STATUS=LINKS_YAML_DIFF_PASS_PYTHON_VALIDATOR_BLOCKED
INDEPENDENT_ACCEPTANCE_STATUS=READ_ONLY_SCENARIO_CHECK_ONLY_NOT_FORMAL_E2E
TASK_CLOSURE_STATUS=SKILL_SLICE_READY_REPOSITORY_CONSOLIDATION_IN_PROGRESS
```
