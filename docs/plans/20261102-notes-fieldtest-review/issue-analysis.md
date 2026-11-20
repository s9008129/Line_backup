# 記事本照片實機測試：全部異常的根因診斷

本輪結論為 `ANALYSIS_COMPLETE`：兩張照片的既有成功結果有保存輸出支持；操作摩擦包含可直接定位的 CLI／文件缺口，以及仍未定因的 GUI 觀察問題。沒有證據支持把這次測試稱為下載失敗，也不能把成功照片推廣為完整產品驗收。

**最具體的新發現是證據範本與實作矛盾**：範本示範相對輸出路徑，程式要求絕對路徑。`init` 則是缺少建帳前的 key 計算入口，並非必須先建帳才能得到 key 的循環。`intent` 後工具列消失目前只有先後關係，未證實直接因果。

## 角色、授權與版本

- Owner 指定 `06_high_reasoning_review_prompt.md`，其預設為單一根因診斷；Owner 隨後明確要求「全部」、「我授權給你」，因此本輪分析全部十項現象，各自保留根因身分，不硬併為一個原因。Owner 另提供待核對的原因說明，並可代問驗收 Agent。
- 本輪仍是 High-Reasoning Reviewer：只診斷、保存分析與診斷證據，不實作、不執行建議、不補測 GUI、不豁免關卡、不啟動下一正式角色。
- Repo：`/Users/hsiaojohnny/dev/Line_backup`；branch：`feature/line-notes-media`。
- 受測產品：`8814d6db0e0a7f368fa5b241fc5ab0010540ea63`。
- 本輪起始／交付紀錄 HEAD：`a985893178971b9ea39c50639a7ab0b468e8ff2b`；起始 index／工作樹乾淨。遠端同分支亦核對為此完整 SHA。
- 兩個提交的差異只有根目錄 [验收纪录.md](../../../验收纪录.md)；`git diff --exit-code 8814d6db0e0a7f368fa5b241fc5ab0010540ea63 HEAD -- src tests .agents/skills AGENTS.md` exit 0。以下行號綁定該產品版本，不把未來報告提交當成新產品候選。
- 已讀專案 AGENTS、指定角色提示、全域同版 workflow-routing／subagent-model-policy、角色報告範本、記事本 Skill／相關 references，以及原 replan、S2 報告、前輪根因分析。repo 內沒有指定的兩份 policy，使用既有全域同版文件，未建立任何 controller。
- 使用一個同角色唯讀助手核對 CLI／源碼，主 Session 複核關鍵程式段落。dispatch 未提供 model／effort override；未取得 provider usage，不主張實際後端型號、成本或節省。助手不是獨立 Acceptance。

## 證據邊界與已證結果

原測試來源固定為 `.local/line-backup/tasks/20261102-notes-e2e-fieldtest/`，以下以 `$FIELD` 代稱。本輪私有診斷證據為 `.local/line-backup/tasks/20261102-notes-fieldtest-review/`，以下以 `$REVIEW` 代稱。沒有讀寫真實帳本、目前照片、active task 或即時 LINE。

直接讀回的**歷史輸出**如下；這不是本輪重跑 verify／summary／audit：

| 來源 | 本輪直接核對到的內容 | 能支持的範圍 |
|---|---|---|
| `$FIELD/logs/20261102T091247+0800-media1-verify.stdout.json` | completion sequence 16；保存的照片驗證結果 | 當次工具產出的完成／解碼紀錄 |
| `$FIELD/logs/20261102T092000+0800-media2-verify.stdout.json` | completion sequence 24；保存的照片驗證結果 | 同上 |
| `$FIELD/logs/20261102T092100+0800-final-summary.stdout.json` | `COMPLETED=2`，其餘五類均 0；unresolved／blockers 空；`all_known_media_complete=true` | 該次摘要的投影，不證明目前檔案仍在 |
| `$FIELD/logs/20261102T092110+0800-evidence-audit.stdout.json` | `integrity_ok=true`，24 events、12 references，`business_projection_omitted=true` | 該次 audit 的完整性結果，不代替 summary／GUI／Acceptance |

兩項各一次下載、各一次 chooser 確認，有當次報告與整理後的 input JSON 支持；`save_all_count=0` 是 intent 的初始簿記欄位，不能單靠它證明 GUI 次數。原始工具呼叫來源仍待驗收 Agent 說明。既有輸出中的 `external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 保留。

本輪圖像檢視呼叫在派送前顯示 `aborted before dispatch`，沒有取得可判讀影像結果，未改入口繞行。截圖所見工具列、toast、同名與 spinner 等仍標為原 Agent／Owner 的 `OBSERVED` 報告；本輪只核對指定檔案存在、bytes／hash、AX 文字、CLI 輸出及源碼，不冒充重新目視確認。41 份指定來源的 SHA-256／bytes 留在 `$REVIEW/source-manifest.json`。

## 最小時間線與原嘗試

時間均為原測試報告或 input JSON 的 Asia/Taipei 時間，不以檔案 mtime 充當操作時間；本輪未新增 GUI／下載／ledger attempt。

| 階段 | 已有嘗試與新資訊 | 本輪判斷 |
|---|---|---|
| 初始化封裝 | 第一次 stdout 為 `PROJECT_LOCAL_EVIDENCE_REQUIRED`；第二次為 `EVIDENCE_OUTPUT_PARENT_REQUIRED`；第三次成功 | 兩次拒絕門檻不同，有新資訊。缺完整 argv 時不能確定第一筆是哪個輸入參數錯 |
| 新列表 init | UNKNOWN context bundle 可封裝，init 拒 `EVIDENCE_CONTEXT_MISMATCH`；預算 key、重建兩份 bundle 後 init 成功 | context 不一致有程式與 log 支持；早期 shell rc 未獨立保存，仍為 UNKNOWN |
| 照片 1 outcome | 相對 bundle 路徑被拒；同一 bundle 的絕對路徑成功 | 只改引用，沒有因此重送下載 |
| 09:13:12.599 → 09:13:13.564 | 右鍵 `[640,300]`；整理 receipt 記錄前後時間；報告稱工具列可見 | 是保存的觀察／輸入敘述，非原始平台 receipt 的獨立證明 |
| 09:13:20 左右 | 照片 2 intent 成功；後續報告工具列已隱藏 | 不支持「CLI 主動隱藏工具列」 |
| 09:13:37.178 → 09:13:37.763 | 同位置右鍵後報告仍未顯示工具列 | 一次無效果，不代表未送達 |
| 09:13:45.614 → 09:13:46.363 | 改至 `[500,300]` 右鍵後報告工具列顯示 | 同時改變位置、時間與點擊次數；不能只歸因於位置 |
| 09:13:51.834 起 | 一次下載控制，之後 chooser、路徑讀回、一次確認、outcome、verify | 這次成功保留，不反推前次失敗原因 |

上述座標只用來描述歷史，不是任何新操作的 locator。原嘗試總數未完整保留，不能宣稱尚剩幾次額度。兩張照片的不同 attempt 不與舊 Issue #50 的 UNKNOWN 合併；本輪成功不能解鎖另一列表或舊 attempt。原分析已有工具列可見性不穩與觀察範圍不足的報告，故不建議再盲點中央、重送下載或只改等待秒數。

## 分項診斷：CLI 與文件

### N26-INIT：建帳前 context／key 入口缺口

**直接事實。** [notes.py:607](../../../src/line_backup_batch/notes.py#L607) 從 identity 算 key，接著以該 context 預檢 binding 與 history evidence，之後才建立照片目錄／帳本。`list_identity()`、`list_key()`（同檔 120–130、152–154）不需已存在的 ledger；測試程式也先算 key 再建立 bundle。`notes_evidence.py:239–241` 比對完整 context。指定 init 失敗 log 與 UNKNOWN bundle，以及帶 key 的成功 log 相符。

**診斷。** 已確認的是 key/context 預檢契約與日常 CLI／文件啟動步驟未銜接。稱「雞生蛋」可描述操作者感受，但不是計算上的循環依賴。對齊原 replan 的 context 預檢要求，不能由此主張證據內容／來源語意已真實。

**未知與反證。** 未知完整首次 argv／實際 shell rc。若失敗的兩份原 bundle 其實已有完全相同 context，需推翻目前解釋並查其他 mismatch；目前保存輸出支持 UNKNOWN 與精確 key 的差異。

### N26-PATH：路徑前置條件與範本衝突

**直接事實。** 輸入與輸出必須分開看：

| 對象 | 實作要求 | 主要位置／拒絕 |
|---|---|---|
| statement、assets、匯入 bundle 輸入檔 | 專案內絕對 canonical 路徑、無 symlink、一般檔案；讀取另核對單一 hard link | `notes_evidence.py:59–68,88–105`；相對輸入為 `PROJECT_LOCAL_EVIDENCE_REQUIRED` |
| 新 bundle 輸出目錄 | 絕對路徑，父目錄已存在且 canonical、位於私有 tasks 下；輸出本身尚不存在 | `notes_evidence.py:451–458`；相對輸出為 `NEW_EVIDENCE_DIRECTORY_REQUIRED`，父目錄不符為 `EVIDENCE_OUTPUT_PARENT_REQUIRED` |

[evidence-template.md:12](../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md#L12) 明寫相對 `--output-dir .local/...`；[notes_evidence.py:452](../../../src/line_backup_batch/notes_evidence.py#L452) 直接拒絕此值，CLI 也未先轉成絕對路徑。範本與 help 沒有完整說明父目錄先存在。這是可直接定位的文件缺陷，不只是泛稱錯誤訊息不友善。

**限制。** 第一筆實機錯誤是輸入來源的拒絕碼，程式先讀 statement／assets 再查 output；缺 argv 時不能斷定它恰由範本的 output 觸發。範本矛盾可證，但不是該筆失敗的唯一已證原因。

**反證。** 若父層已將相對輸出轉成絕對值，範本可能成立；`notes.py:4393–4395` 直接傳參的實作不支持此替代解釋。沒有證據支持放寬 symlink／私有目錄／拒覆寫，或必須改成自動建立父目錄。

### N26-SUMMARY：參數誤用與診斷證據缺口

`summary` 只收單一 ledger 的 `--records-root`；全帳本入口為 `lists --collection`。help 在 `notes.py:4175–4182` 已區分，`:4308–4309` 未定義 `--local-list-id`，未知參數會在建立 `NotesRecords` 前由 argparse 拒絕。

原報告記載 exit 2 與改正後成功；指定來源中未取得該次失敗的完整 argv／stderr，故「實機 exit 2」是前輪報告，本輪沒有重現。若只傳 collection 而沒帶未知選項，將進入另一條帳本解析路徑，不能混稱。

已證的是誤用與 help 契約，不足僅憑一次誤用認定公共介面必須改名。若補日常例子，可表達 `lists → 回傳 records_root → summary`；這是待規劃的文件內容，不是本輪修補。

## 分項診斷：GUI 觀察、推論與可反駁條件

| 根因 ID／現象 | 直接證據及原觀察 | 候選原因與目前不能斷言的事 | 區分原因所需證據／反證 |
|---|---|---|---|
| N26-AX：靜態照片工具列未進 AX | 五份 AX 均為 499 bytes、SHA-256 完全相同；有 slider、時間與 `1.0x`，無照片下載等控制。原報告稱相應截圖有可見工具列 | 可能是 App 未暴露自繪控制、工具綁錯 subtree、截斷／快取或非同步快照。五份相同本身不能區分它們，也不能由影片式 controls 把照片改判影片 | 同一可見 viewer、同一時間窗，以既有 CUA 與獨立 AX client 比較 role／children／window 歸屬；獨立 client 有控制而 CUA 沒有，會削弱「App 完全沒暴露」假說 |
| N26-TOOLBAR：intent 前後隱藏、兩次右鍵結果不同 | input JSON 的兩次點位／時間不同；五份 AX 不變。`notes.py:2646–2725` 的 intent 路徑只見帳本／檔案／hash／事件操作，未見 GUI、移鼠、前景切換或子程序啟動 | 不支持 intent 直接隱藏工具列。timeout、hover、焦點、觀察 API 行為、第二次點擊或重繪均未排除；CLI 耗時／資源影響也未排除 | 先回查完整輸入與觀察 trace。若無 CLI 的等時長停留也隱藏，會反駁「intent 專屬觸發」；若中間有明確前景／移鼠變化，需更新解釋。本輪不做此實驗 |
| N26-PANEL：Go to Folder 預填舊路徑 | 兩份 go-postshortcut AX 與照片 2 path-input 整理紀錄支持預填上一個位置 | 目前支持的是 Go to Folder 文字保留，不能直接等同整個 save panel 的 current directory 已切到舊項。macOS／LINE 各自快取責任未知 | 分開保存 PathTextField、where popup、實際 current directory；只有取得 App 設定或可歸屬系統狀態對照，才能分責。每次覆寫精確空白目的地並讀回的保護仍必要 |
| N26-NAME：同名、隱藏副檔名 | 原報告／statement 稱兩次預設同 basename；本輪未重看圖像 | LINE metadata、固定命名或 panel 設定皆可能；不知服務端原檔名。同名不代表同一媒體 | 需來源 metadata／面板完整欄位對照才能定命名來源；不同空白 attempt 已避免本次碰撞，不支持再加跨項全域檔名控制器 |
| N26-TOAST：截圖有完成提示、AX 沒有 | 兩份 post-confirm AX 都沒有「下載完畢」；照片 2 confirm 整理 JSON 的 `download_finished_text=false`，statement／原報告則稱截圖可見 | 若 false 代表 AX 文字搜尋，兩者可一致；若宣稱跨來源皆未見，則紀錄互相衝突。瞬態時序、AX 暴露缺口皆可能，不能定為 CALayer 原因 | 查清該欄位感測來源／時序與原始回傳。單張 toast 不取代同 attempt 終結、穩定檔、驗證與 completion |
| N26-SPINNER：首次黑底 spinner | 只有原 Agent 的 `OBSERVED`，未保存瞬態影像 | 解碼、遠端載入或 UI placeholder 均為猜測，不列已證缺陷 | 缺當次時序／載入來源，不補造；不為重現而重新下載 |
| N26-CARD：卡片無獨立詳細頁 | 原 Agent 報告卡片已展開、點文字只改焦點 | 支持該次導覽行為，不能推廣為所有版本／貼文都沒詳細頁；不是本次下載失敗原因 | 相同已展開狀態的導覽與角色證據可支持流程適配，無需強迫另開頁 |

Apple 官方文件說明自訂控制需要透過 accessibility 元素／children 暴露；它只支持「畫面元素可能需要另外提供 AX 表示」這個候選解釋，不證明 LINE 或 CUA 的責任。[Accessibility for AppKit](https://developer.apple.com/documentation/appkit/accessibility-for-appkit)、[Integrating accessibility into your app](https://developer.apple.com/documentation/accessibility/integrating-accessibility-into-your-app)。Apple 的 [directoryURL](https://developer.apple.com/documentation/appkit/nssavepanel/directoryurl) 只定義面板目前顯示的目錄；不足以證明本案是 NSSavePanel 自動記住前次目錄，更不能將 Go to Folder 預填與目前儲存目錄混同。未使用第三方問答推定根因。

## 尚待驗收 Agent 的來源說明

Owner 願意代詢，已提出以下文字問題，僅需回查既有紀錄，不重測：

1. 工具列各狀態的截圖／AX 實際 API、app／window 與原始呼叫紀錄位置。
2. 可見工具列 → intent → 兩次右鍵之間的前景、移鼠、其他輸入與時間來源。
3. `assets/*-input.json` 是否為工具自動保存或 Agent 整理；`undefined`／`null` 各對應哪個真實工具回傳。

在未取得來源前，這些欄位為 `UNKNOWN`，整理 JSON 不升格為原始平台 receipt；`undefined`／`null` 本身也不是失敗或未派送證明。若補充與既有證據矛盾，保留兩者交 Owner，不自動重試、修帳或補測。

## 唯一建議路由：PLANNER_REPLAN

建議 Owner 另開 Planner 主 Session，針對**既有 S3 操作契約補一份有界工作單**，不是推翻原 R1–R10 計畫或開始另一輪全面框架改造。本輪不執行此建議。

**路徑與範圍。** 以本報告、精確產品 `8814d6d…`、完整欄位測試提交 `a985893…`、既有 replan／S2 報告及驗收 Agent 回覆為輸入。在新的任務文件中，規定如何讓 Agent 建帳前取得完整 identity 的 key；先評估既有純計算函式的明確文件入口，若需新增 CLI，須另列公共介面變更，不默認放寬 context。把範本的輸入檔／輸出目錄契約補齊；提供全帳本查詢到單帳本摘要的一個完整用例。對 GUI 部分只規劃既有 G0 的同 viewer、不同觀察來源／獨立 AX client 與時序對照，不把原因預填為 LINE／macOS 不穩定。

**成功檢查。** 產出可交付 Implementer 的小範圍文件工作單及 G0 證據需求表，涵蓋本報告十個 ID；每項有事實／未知、允許修改路徑、驗證方式與停止條件。若包含 CLI 改動，明列 identity 正規化一致性、資料副作用邊界、相容性與必要測試。保留單項一次派送、空白目錄、context／hash、未知不重送等既有契約。S2 報告已列 S3／獨立驗收未完成，不能把這些新問題倒算成 S2 已承諾完成卻測試失敗。

**停止條件與人工決策。** 新增控制器、放寬安全 gate、公共參數改名、真實資料更正或 GUI 輸入均超出文件小修，需 Owner 決定邊界。若無獨立 AX client／原始 trace，只保留未知，不用反覆右鍵或下載取得答案。新 GUI 診斷須另有明確範圍與有效前景；不為開 chooser 而點下載。舊 UNKNOWN、原件與 ledger 不動，G0／A0／D1／D2／G1／G2 未有適用證據者不豁免；列表 A 的兩張照片成功不替原列表解鎖或簽發整體驗收。

此路由只是建議，不是 Planner 派送、修復結果或 PASS；下一正式角色仍由 Owner 啟動。

## 本輪實際命令、驗證與未執行項

工作目錄為上述 repo；診斷 Python 為 `/usr/bin/python3` 3.9.6。下列均實際執行，原 argv、cwd、UTC 起訖、stdout／stderr／exit 留 `$REVIEW/commands.json`；來源 manifest 及去識別化摘錄留同目錄。

| 命令／檢查 | Exit／結果 |
|---|---|
| `git status --short --branch`、`git rev-parse --show-toplevel`、`git branch --show-current`、`git rev-parse HEAD` | 各 0；起始乾淨、分支／候選如上 |
| 上述受測候選到 HEAD 的 `git diff --exit-code ... -- src tests .agents/skills AGENTS.md` | 0；產品／測試／Skill／AGENTS 相同 |
| `git ls-remote --heads origin refs/heads/feature/line-notes-media` | 0；核對為 a985893 完整 SHA |
| `/usr/bin/python3 --version` | 0；3.9.6 |
| `/usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-fieldtest-review/capture_diagnostics.py` | 0；只讀指定歷史來源，保存 41 份 manifest、完成序號／summary／audit 摘錄及上述命令 receipt |

`git diff --check`、報告連結及最終 Git 交付核對在報告寫完後保存於 `$REVIEW/`。沒有修改產品，未跑 daily／notes 單元測試、產品 CLI、ImageIO 重解碼、影片／混合附件／Save All、前景中斷、跨 Session、獨立相容或 Acceptance，均為 `NOT_RUN`。沒有把前輪測試數字或 GUI 人眼觀察當作本輪 PASS。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN; PRODUCT_CANDIDATE_8814D6D_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: SOURCE_AND_SAVED_LOG_DIAGNOSIS_COMPLETED; NEW_GUI_AND_PRODUCT_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_S3_AND_APPLICABLE_INDEPENDENT_VERIFICATION
```

診斷可交付；兩張照片成功保留。產品、原 Issue／其他列表與正式驗收未由本角色結案。本輪到此停止，不自行進入規劃、修補或重測。
