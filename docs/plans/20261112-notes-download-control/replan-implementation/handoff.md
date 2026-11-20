# 可直接貼給 Implementer 的 Prompt

```text
你現在是本任務的 Implementer。請依第一性原理及最佳實務完成下列有界實作，不要重新規劃或啟動獨立審查。

Owner 已選定本次 replan 進入實作，明示「本計劃不需要獨立審查」。不要求 Plan Review、Simplicity Review 或另一份核准文件；必要本機檢查及原生唯讀 smoke 仍須完成，自檢不冒充獨立接受。

工作目錄：/Users/hsiaojohnny/dev/Line_backup
開發分支：feature/line-notes-media
交接來源 commit：9dbd5a906754f32246f6a66ac336afa67b8d63d6
完整交接：docs/plans/20261112-notes-download-control/replan-implementation/handoff.md
核定計畫：docs/plans/20261112-notes-download-control/replan.md
計畫 SHA-256：7f07148f4787bc2943468714ee621916b2d7f57f8d2322f13f703b3164686cf4

先完整讀取本 handoff、replan、AGENTS.md、記事本 Skill 及適用 references；核對 Git root/worktree/branch/HEAD、dirty/untracked 與本文件列出的來源 hashes。含本 handoff 的 commit 會晚於交接來源 commit，HEAD 不必等於舊 SHA；相關內容相同而僅新增交接文件時直接接續，不 checkout/reset。保留既存 issue提交單.md，不讀正文、不 stage、不改動。

本輪執行 replan S1：主要只修改 .agents/skills/line-notes-agent-cua/references/evidence-template.md 的 CUA 原件保存範例；必要時在 gui-inventory.md 補短說明／連結。不要改 src、Python tests、CLI／事件 schema、相簿流程、正式 Prompt、AGENTS、真實帳本、active hint、照片或 LINE 資料。

已證實的直接原因：CUA 回傳有效 162388-byte Buffer，但舊 screenshot instanceof Uint8Array 為 false；同一物件的 Buffer.isBuffer 與 node:util 的 types.isUint8Array 均為 true，原始 AX／截圖可保存並逐 bytes 讀回 MATCH。修的是範例型別誤判與失敗不可判別性，不是要求 Owner 修復 CUA；實際下載控制 U1 仍未證實。

由你監督原生實作 subagents，必須使用 model=gpt-6-luna、reasoning_effort=high、fork_turns=none。按互斥檔案或唯讀檢查分工；助手不能簽獨立接受、另派助手或執行 Git／真實資料操作。派送失敗依 AGENTS 保留錯誤，由主代理在原授權內接手，不改用其他模型／API／背景 LLM 繞過；如實記錄指定委派未完成。

修正必須可靠辨識真正 byte array、複製精確 view bytes、保留同次原始 AX／截圖、不可覆寫、私有 canonical 路徑、逐 bytes 讀回。拆開 AX／影像型別／空值／寫入／讀回的錯誤階段，保存可保存的部分原件及診斷 metadata；不完整就停在 bind 前。不得接受任意 array-like／字串、只憑 constructor.name，或把整個 backing buffer 當成影像；不要加入未實證的泛用 adapter。

驗證最終 Markdown 範例本身：先以專案私有 fixtures 核對 Buffer、跨 realm Uint8Array、offset 子視圖、無效型別、檔案碰撞、寫入／讀回失敗保護；再在 CUA runtime 執行一次同次 AX＋截圖保存／讀回的唯讀 smoke。只能觀察與保存，不 click、scroll、按鍵、不 bind、不讀寫真實帳本、不建立 intent、不下載。既有同根因 capture 已兩次；這次 smoke 限第三次一次，仍失敗即保留證據停止，不換 Session 或 API 重置次數。

執行 replan 第 8 節三條既有回歸，各保存一次原始 stdout/stderr/exit。不得只靠 Python tests、文件核對或另寫相似腳本就宣告原生範例修復。非零結果不在本範圍自行修 src。

證據放新建的 .local/line-backup/tasks/ 私有任務目錄；公開實作報告放 docs/plans/20261112-notes-download-control/replan-implementation/implementation.md。記錄前後差異、實際命令／exit、原生 smoke、未測項與六項狀態，修正舊外部故障推論但不覆寫歷史。

完成後逐檔 stage 同範圍成果，依既有授權 commit/push；commit body 填「意圖」「做了什麼」「下一步的建議」「驗證與結果」，核對實際 body 與遠端精確 HEAD。不 merge master、不 force-push、不新增審查流程。

本角色做到 S1 實作及適用檢查後交付。S2／S3 由既有記事本日常正式入口核對來源並下載，不能因本交接自行轉下載角色；也不能要求日常使用者帶開發計畫、內部 JSON 或重新授權已有效的相同範圍。S1 成功只代表原件保存範例修好，不代表五張照片已完成，不把未執行的獨立接受寫為 PASS。
```

## 1. 交接效力與當前階段

這份是 **Owner 選定 replan 後、直接進入 Implementer 的正式交接資料**。本輪只準備文件；沒有派送實作、Review 或下載。Owner 將開頭 Prompt 貼到自行選定的實作主 Session 後，實作者依該交辦與本文件執行。

- 使用者明示本計畫不需要獨立審查，故不以審查報告或核准收據作為 S1 前置，也不啟動獨立審查。
- 「不需要獨立審查」不表示測試、原生 smoke 或資料保護可省略，也不是獨立接受 PASS。
- 正式角色由人啟動。實作助手是同角色協作，不是 Reviewer；本交接不授予助手跨角色下載或結案權限。
- 本交接的下一步是 S1 實作。S2／S3 是產品實用結果的後續路徑，不是要求 Implementer 在沒有當次日常入口／有效前景時操作真實資料。

較早的 `../handoff.md`、`../plan.md`、歷史診斷 Prompt 與其他舊報告保留其原版本與綁定，不是這次實作指令。`../replan-handoff.md` 是 replan 交付當時的短交接；本文件補足 Owner 本次「直接實作、不獨立審查」的明確選擇。與當前交辦衝突時，以 Owner 最新明示及本次 replan 範圍為準，不改寫舊文件。

## 2. 任務、版本與必要輸入

| 項目 | 精確值／用途 |
|---|---|
| 使用者最終目標 | 指定記事本貼文的五張照片能依同一日常入口完成下載、驗證與 completion；不擴成其他貼文下載 |
| 本輪實作目標 | 修好 CUA 原件保存範例，讓有效 Buffer 不再被錯拒，失敗時能辨別原因並維持原保護 |
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup` |
| 分支 | `feature/line-notes-media`；master 不變 |
| 計畫交付 commit | `9dbd5a906754f32246f6a66ac336afa67b8d63d6`，當時已推送並核對遠端精確 HEAD |
| 本 handoff 製作起點 | 同上；僅既存 `issue提交單.md` 未追蹤，沒有其他 tracked dirty |
| 核定計畫 | [replan.md](../replan.md)，SHA-256 `7f07148f4787bc2943468714ee621916b2d7f57f8d2322f13f703b3164686cf4` |
| 對照舊成果 | [前輪 S1 實作報告](../implementation/implementation.md)，僅保留其原本已證明結果 |
| 本次基準 diff | 對上述交付 commit，比較實作前後精確路徑；不可只交口頭摘要 |

實作者先核對以下產品來源 hashes；它們對應 replan 的已觀察版本：

| 路徑（repo 相對） | SHA-256 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | `633824c00a5692dab87d3f2cfc03d1f08ec502d38a8ee8321b7c6f22b1408511` |
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` | `04e64a88e0aceb897b864757bf4a95aa70e168f0f7e6eb63662b8a0b5c8db974` |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md` | `c9ae089352825198519ca03e167ee5c49aec7e750c5f88a6497e319994b6651d` |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | `6238e5fe26b67b17518c3c973b82fa66ed86eeb4c5d13317a36caad8495fc365` |

本文件由較新的 commit 承載，不放自我引用的固定 HEAD／self-hash。HEAD 晚於來源 commit 不構成拒絕理由；先核對 ancestry、相關內容與來源 hashes。若相關產品或計畫實質漂移，停止依賴該基準的實作，列出精確差異；不能自動 checkout/reset 或冒用舊 PASS。無關 dirty／其他 worktree 不納入成果。

## 3. 已證明的因果鏈與仍未知事項

1. 舊範例把非空 AX、截圖型別及長度合併成同一個 `CUA_RAW_OBSERVATION_UNAVAILABLE`。
2. 本次 CUA 截圖實際為有效 Buffer，162,388 bytes。舊 `instanceof Uint8Array` 是 false，`Buffer.isBuffer`、`ArrayBuffer.isView` 與 `util.types.isUint8Array` 均為 true。
3. 父代理以同一筆記憶體物件保存 AX UTF-8 353 bytes 與截圖，逐 bytes 讀回 MATCH，並實際看見記事本列表。因此「CUA 沒有截圖、要 Owner 修復介面」的舊推論不成立。
4. 不同 realm／建構子原型身分差異是高信心機制解釋，沒有檢查 CUA 內部 VM，不能宣稱內部架構已確診。精確 runtime 版本 UNKNOWN；CUA 未提供 `process` global，別把本機 Node 或網頁文件版本當它的版本。
5. 當次 Agent 另有執行偏離：未用既有 notes_capture 保存完整 lists、截斷候選、任選一份未確認相關的 memory。其修法先是遵循既有流程，不是新增 CLI 或繼續疊條文。
6. 目標帳本唯一對應、全列表覆蓋、五張媒體資格、Notes viewer 的下載控制 U1、chooser／派送、檔案驗證及 completion 尚未證實。空白 AX 標題不能取代實際畫面判讀；本輪截圖可見列表也不能單獨認領歷史。

停止在 bind 前符合原資料保護。S1 要修正誤判和診斷品質，不刪除 bind／intent gate，不改禁止重送或 UNKNOWN 語意。

## 4. 可取得的證據包

診斷根目錄：`.local/line-backup/tasks/20261112-notes-observation-replan/`。原件私有、不提交、不外傳。實作者以既存檔案唯讀核對，缺件時列出缺件及受影響檢查；不從聊天重建原件、不為補證據重播 GUI 輸入。

| 檔案 | 已證明內容／限制 |
|---|---|
| `preflight.json` | 規劃來源、當時 Git、來源 hashes；不是實作版本 PASS |
| `observation-shape.json` | 同次 capture 的 keys、AX 型別／長度、Buffer 型別與舊 predicate 結果 |
| `byte-persistence-diagnostic.json` | 真實 byte 數、SHA-256、原樣保存讀回 MATCH |
| `type-check-comparison.json` | 同物件 `util.types.isUint8Array=true`、舊 `instanceof=false` |
| `observations/shape-diagnostic.ax.txt`、`observations/shape-diagnostic.jpg` | 同次原始 AX／JPEG；只證明該次觀察，不是當次前景授權或列表歷史認領 |
| `observation-paths.json` | 原始 JPEG 副檔名更正說明，bytes 未轉碼 |
| `document-validation.json` | replan 文件九項核對；不是產品測試或範例 smoke |
| `final-git-receipt.json`、`source-manifest.json` | replan 來源／交付與精確遠端 HEAD；不是獨立接受 |
| `progress.md`、`helper-findings.md` | 嘗試歷史、Agent 偏離及同角色助手整理；摘要不是 raw receipt |

本 handoff 製作的核對收據另放 `.local/line-backup/tasks/20261112-notes-implementer-handoff/`。兩份早期公開問題提報、舊進度與報告可供追溯，不得拿其中未證實敘述覆蓋本輪直接診斷。

## 5. 實作 scope 與禁止事項

| 範圍 | 允許內容 |
|---|---|
| `references/evidence-template.md`（記事本 Skill 下） | 主要且必要修正：可靠型別判斷、精確 bytes 副本、錯誤分階段、部分原件與同物件查證 |
| 同目錄 `gui-inventory.md` | 確有必要才補短說明／連結；AX 不足時看原圖、區分觀察轉接與來源問題，不複製完整交易規則 |
| 本目錄 `implementation.md`、`progress.md` 及必要非私人交付附件 | 新實作報告、實際驗證、差異、未測與交接；不覆寫本 handoff、replan 或歷史成果 |
| 新 `.local/line-backup/tasks/<task>/` | 私有 fixtures／擷取／收據／hash／HTML；不提交 |

預設不改 `SKILL.md` 或 `download-and-ledger.md`；replan 已允許必要的短定位連結，限證據範本可發現性，不能新增門檻或改交易語意。若不需要就維持原文。

禁止修改 `src/`、Python tests、CLI／事件格式、相簿 Skill／工具、使用手冊正式 Prompt、AGENTS、全域 `.codex`；禁止真實帳本／索引／active／照片／LINE 資料寫入，禁止 merge master、force-push、另建 GUI 控制器、固定座標、相簿 Save All fallback 或未實證的 regions adapter。

原生 smoke 只能使用原生 CUA 觀察 API 與 Node 檔案保存；不透過 AppleScript、JXA、System Events、其他 LLM／SDK 或背景程序操作 UI。本交辦不包含點擊、捲動、按鍵、bind、init、scan、intent、下載、分享或刪除。

## 6. 執行順序與可觀察完成條件

| 順序 | 執行者與工作 | 必要證據／成功條件 |
|---|---|---|
| 1 | 主代理：核對版本、授權、來源、私有證據及 dirty | exact HEAD、path、hash、原有工作保護；無失效 HEAD 陷阱 |
| 2 | 主代理監督指定實作助手；互斥寫入與唯讀驗證分工 | 原生派送參數、回傳與每位助手 scope；不得因同檔競寫破壞唯一版本 |
| 3 | 範例修正 | 真正 byte array 檢查；正確 view bytes 副本；原始格式、`wx`、私有 canonical 路徑、逐 bytes 讀回；失敗不 bind |
| 4 | 私有離線 fixtures，必須取自最終 Markdown 範例的實際邏輯 | Buffer、本 realm／vm realm Uint8Array、非零 offset 子視圖均保留精確 bytes；空值、字串、Array、DataView、Uint16Array、偽裝物件拒絕；碰撞、寫入／讀回錯誤不虛報成功 |
| 5 | 主代理：最終 Markdown 範例原生唯讀 smoke 一次 | 同次完整 AX＋截圖保存並讀回 MATCH；原件／metadata／輸出可重核；沒有 GUI 輸入或真實帳本副作用 |
| 6 | 主代理：三條既有回歸各一次 | 原始 argv、環境覆寫、stdout、stderr、exit；沒有非零失敗被忽略 |
| 7 | 主代理：公開報告及 Git 交付 | 精確 diff、可寫 scope、私密資料遮蔽、六項狀態、message body、遠端精確 HEAD；保留既存 untracked |

型別判斷優先沿用已在同物件實測的 Node 內建 `types.isUint8Array`，顯式匯入 Buffer；`ArrayBuffer.isView` 單獨使用會過寬。只保存真正觀察 bytes；未確認格式可用 `.bin`，不要轉碼或把截圖重新生成為原件。

如果 AX 合格而影像缺失、影像合格而 AX 缺失，安全保留已取得的原始部分並記錄具體階段；完整 gate 仍不成立，不封裝成可 bind 的完整 observation。錯誤 metadata 不公開整份私人 AX 或影像。實作需驗證這些分支，不能只驗 happy path。

三條回歸（工作目錄為 repo）：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

測試使用合成 fixtures，不讀寫真實備份資料。沿用相符現有 Swift SDK，不修改系統工具鏈。前輪的 73／228 tests 舊 PASS 不覆蓋本候選；本輪需要保存實際結果，不預填數目或成功。

S1 要同時具備最終範例修正、離線 fixtures、一次原生範例 smoke 及適用回歸證據，才可把本切片標為 COMPLETE。工具缺失／smoke NOT_RUN 時保留已實作結果，明列未滿足項；不能只交文案或相似腳本測試就宣稱原生問題已修好。

## 7. 嘗試歷史與停止條件

- 同根因已發生兩次 CUA capture：前次舊 guard 失敗一次、本次 replan 唯讀診斷一次。同一物件的保存／型別比較不是新 capture；不得重置歷史。
- 最終範例 smoke 限再一次，仍失敗即保留原件／原因並停止。不得換 Session、API、目的地或新目錄反覆試到成功；兩次連續沒有新資訊亦停止相同方法。
- 已取得合法 capture 而本地判定失敗時，可唯讀分析同一物件，不重做 GUI 輸入。沒有 bytes 不能補造，有部分原件不能冒充完整證據。
- 若當次回傳換成未實測 regions、需要變更資料／公共介面／架構或越過可寫 scope，交回精確證據與所需範圍決策；不自行擴張本實作。
- fixture 或基線測試非零、來源不符、寫入衝突或唯一版本歧義，先保留已證明結果，不修範圍外程式、不覆寫別人工作。
- 原生助手派送失敗不能繞道另一模型、CLI／SDK／API／MCP 或背景 LLM；主代理可依契約接手原授權工作，另報指定委派未達成，不冒稱已用指定模型。
- 相關資料／來源權限真正不足才停止依賴動作，指出具體缺口；不因本地型別錯誤要求 Owner 重貼授權或修復未證實的外部故障。

## 8. 模型證據與交付報告

本次實作助手沿用 Owner 明示選擇 GPT-6 luna、high；這不替主 Session 指定模型。保存四層證據：設定預設、實際請求參數、平台顯示、provider usage；不能以其中一層宣稱另一層已證實。未有 backend／用量證據就標 UNKNOWN，不主張 token 或費用節省。

實作報告至少記錄：起始與交付 HEAD／分支、計畫 hash、實際修改路徑及原因、助手分工與證據層、實際命令及 exit、原件／fixture／smoke／回歸結果、保留的歷史、未測及具體下一步。原件只留私有 task，公開報告使用匿名描述／引用。

commit body 必須填妥「意圖」「做了什麼」「下一步的建議」「驗證與結果」，用 `git show -s --format=%B` 核對實際本體。stage 限授權成果；不含私人證據或原有 `issue提交單.md`。推送後唯讀核對遠端精確 SHA；失敗如實報 `COMMIT_OR_PUSH_BLOCKED`。不為交付自動新增 Review／PR 審查流程。

## 9. 六項狀態及後續日常入口

以下是本 handoff 製作時的整體狀態，實作者依實際證據更新；不要把此表當預填測試結果：

| 狀態 | 當前值／更新規則 |
|---|---|
| PRIMARY_OUTCOME_STATUS | BLOCKED：指定照片尚無完成證據；S1 成功不代表照片完成 |
| IMPLEMENTATION_STATUS | NOT_RUN：本 replan 尚未實作；適用切片與檢查完成才更新 |
| CORE_ACCEPTANCE_STATUS | BLOCKED：仍缺來源唯一核對、下載與照片 completion |
| REQUIRED_VERIFICATION_STATUS | PARTIAL：舊 guard 誤判診斷／同筆原件讀回有證據；本候選 fixtures／smoke／回歸及真實下載仍 NOT_RUN |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN：Owner 不要求獨立審查，不可改填 PASS |
| TASK_CLOSURE_STATUS | BLOCKED：交接文件可交付，修復與照片任務未結案 |

S1 交付後，實際照片備份仍走[使用手冊附錄 C：記事本正式 Prompt](../../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt)，由日常 Agent 自動查完整帳本、核對列表、覆蓋全部卡片、細盤指定貼文，再依真實控制與 intent 單次派送、outcome、逐檔 ImageIO／hash 及 completion 收尾。不使用 Harness Acceptance／E2E Prompt 代替。

正常入口不新增要求 Owner 攜帶開發計畫、挑模式、手填 key／JSON 或逐張授權。既有有效授權持續有效，只有具體前景中斷／來源歧義等真正缺口才需重新交接或詢問。完成項不重下，UNKNOWN／活動下載／命名未完／LOCAL_CHANGED 等仍按原規則處理；U1 未解就停在相應 gate，不將 S1 成功擴張成下載控制已解。

## 10. 本交接製作已執行的核對

- Git root／worktree／branch／HEAD／status 及交接 Prompt／來源讀取命令 exit 0；起始版本與無關工作見第 2 節。
- `replan.md` SHA-256 與四份產品 references／Skill hash 已直接讀檔核對；先前 handoff／replan／產品來源均未修改。
- 文件檢查腳本 exit 0、14 項核對通過，包含開頭 Prompt、精確版本、指定模型參數、無獨立審查前置、三條回歸、角色邊界、連結、嘗試限制及六項狀態；收據在本輪私有 task 的 `document-validation.json`。
- 本輪沒有跑產品 tests、CUA、真實帳本或下載；這些不是本交接文件的 PASS。實作／smoke／產品回歸仍屬下一角色。
- 本文件交付 commit、實際 message body、推送及遠端核對結果，以同私有 task 的最終 Git 收據和最終回覆為準；不在文件內製造自我引用 SHA 或預填發布成功。
