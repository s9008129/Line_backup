# Replan：記事本觀察型別誤判、啟動執行偏離與照片完成路徑

## 1. 本輪結論與交付範圍

**本次停止的直接原因已定位：Skill 的 JavaScript 範例以 `instanceof Uint8Array` 檢查截圖，當次 CUA 回傳的有效 Node Buffer 卻未通過這個檢查。截圖並未缺失。** Agent 隨後沒有區分檢查失敗原因，就把它解讀成外部 CUA 故障，要求 Owner 修復介面／重新交接；這個根因敘述應予更正。

本輪一次唯讀擷取證明：同一份截圖可保存、逐 bytes 讀回一致，也能看到記事本列表。這只解除「工具根本沒有截圖」的錯誤假設，**不證明目標列表已和帳本對應、不證明下載控制可用，也不等於五張照片已完成**。

本文件是使用者要求的重新規劃，兼列後續交接條件；不覆寫原 plan、handoff、分析或進度。本輪不修改產品、不操作 LINE 控制項、不寫真實帳本／照片，也不啟動實作或驗收角色。

- 規劃結果：`PLAN_DRAFT_COMPLETE`。
- 風險分級：`STANDARD`。預期修正主要是一份 Skill reference 的可執行範例及少量決策指引，但它影響真實來源證據與 GUI 派送前置。
- 沿用使用者本任務明示「不需要 Review」的安排，不自動增加 Review、Acceptance 或 E2E 角色。必要自檢與實際備份證據仍須完成；自檢不能冒充獨立接受。
- 本輪以 `replan.md` 取代新建一份同義 `plan.md`；精確交接另見 `replan-handoff.md`。

## 2. 基準、來源與既有成果

| 項目 | 本輪事實 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup` |
| 分支 | `feature/line-notes-media`；不合併 master |
| 規劃輸入 HEAD | `92c1ca61da62184f110ea8363ff54480f5f3c41c` |
| 起始 Git 狀態 | 僅既存未追蹤 `issue提交單.md`；保留、不讀正文、不 stage |
| 既有產品切片 | HEAD 已整合授權更新、列表／viewer 分流、完整 lists 保存及歷史診斷入口退役 |
| 本輪私有證據 | `.local/line-backup/tasks/20261112-notes-observation-replan/` |
| 先前備份嘗試報告 | `.local/line-backup/tasks/notes-download-20261112T1415+0800/progress.md`；保留原文，僅以新報告更正判斷 |

輸入 HEAD 是來源版本，不是要求含本計畫的新 commit 仍等於輸入 HEAD。後續用本文件 SHA-256 與交付 commit 定位候選；不得因此建立下一個「新文件一提交就不符舊 HEAD」的版本陷阱。

專案未包含 `policies/v4.9.0/`；本輪已讀既存 `/Users/hsiaojohnny/.codex/policies/v4.9.0/` 的對應人工交接規範。未重建退役 Harness。先前 S1 報告的 73／228 個測試通過屬該輪既有證據，本輪未重跑，也不把它們當本次 CUA 範例已通過。

## 3. 第一性原理：保護目標與實作手段必須分開

安全備份要成立的是一條可核對的因果鏈：

`有效授權／前景 → 原始觀察可保存 → 列表與帳本唯一對應 → 全列表卡片覆蓋 → 目標貼文媒體細盤 → Notes 自身下載控制 → intent／新空白目的地讀回 → 單次派送 → outcome → 完整檔案驗證／completion`

每個 gate 只阻擋依賴它的下一步。讀取回傳型別、保存同一個已取得物件及整理候選，不是派送；但沒有完整原件仍不能 bind。觀察可保存不自動證明列表身分，空白 AX 標題也不自動證明列表無法辨認，必須實際看截圖。

| 必須維持的不變條件 | 可替換的實作手段 |
|---|---|
| 保存真正來自 CUA 的原始 bytes，且讀回相同 | 判斷 byte array 的 JavaScript 方法；`instanceof` 本身不是安全需求 |
| 截圖範圍、來源及時間限制如實記錄 | `.bin` 或依原始格式命名；不得轉檔後冒充原件 |
| 查閱全部登錄帳本，不遺漏歷史 | 將完整輸出存檔後產生短表；無需把數萬 tokens 全送到對話 |
| 當次列表→貼文→媒體身分唯一 | 交叉核對畫面、連續入口、帳本與貼文錨點；不要求 AX 必有中文標籤 |
| 未決交易不重送，完成事實不可改寫 | 依既有 CLI 收斂；不可用新目錄、改帳或另一入口解鎖 |

因此最小修正是讓有效資料被正確認出、失敗原因可判別，並讓 Agent 執行已有帳本流程。刪除證據 gate、增加 Owner 確認次數或新建控制器，都沒有處理這次原因。

## 4. 直接證據、推論與未知

### 4.1 本輪唯讀診斷結果

同一次 `getAXStateAndScreenshot({disableDiffing:true, emit:false})` 的結果保留在記憶體，再做型別比較及原樣落地；全程沒有 click、scroll、按鍵、bind 或 intent。

| 觀測項目 | 實際結果 | 私有證據 |
|---|---|---|
| 回傳欄位 | `state`、`screenshot`；沒有使用 regions 形式 | `observation-shape.json` |
| AX | 非空 string，273 字元、UTF-8 353 bytes | 同上、`observations/shape-diagnostic.ax.txt` |
| 截圖 | `Buffer`；162,388 bytes；`Buffer.isBuffer=true` | `byte-persistence-diagnostic.json` |
| 舊判斷 | `screenshot instanceof Uint8Array=false` | 同上、`type-check-comparison.json` |
| 對照判斷 | `ArrayBuffer.isView=true`；`util.types.isUint8Array=true` | 型別／保存收據 |
| 實際保存 | 同一物件的 AX 與截圖均保存並讀回 `MATCH`，含 SHA-256 | `byte-persistence-diagnostic.json` |
| 畫面 | 原件可見記事本分頁、搜尋欄及一張含媒體預覽的貼文卡片 | 截圖由主代理實際查看，`OBSERVED`；未核對全部列表／帳本 |
| 格式 | 原始檔頭為 JPEG；只修正診斷檔副檔名，未轉碼 | `observation-paths.json` |

已證實的缺陷是 **`instanceof` 在目前執行環境錯拒有效 Buffer**。不同 JavaScript realm／內建建構子原型身分不一致能解釋這組結果，屬高信心機制推論；沒有檢查 CUA 內部 VM 實作，不宣稱已證明其內部架構。

一手依據：[Node Buffer 文件](https://nodejs.org/api/buffer.html#buffer) 說明 Buffer 與 Uint8Array 的關係；[MDN instanceof 的多 realm 說明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/instanceof#instanceof_and_multiple_realms) 說明建構子不同可導致誤判；[Node util.types.isUint8Array](https://nodejs.org/api/util.html#utiltypesisuint8arrayvalue) 提供內建型別檢查。本輪另直接證明該函式在同一個 CUA 物件上回傳 true，沒有僅憑文件推定相容。

CUA runtime 的精確 Node／V8 版本仍 `UNKNOWN`；診斷曾讀取未提供的 `process` global 而失敗，移除該非必要欄位後完成比較，未再擷取畫面。網頁文件版本不能當作 CUA runtime 版本。

### 4.2 根因與促成因素

| ID | 判定／信心 | 根因或缺口 | 修正歸屬 |
|---|---|---|---|
| R1 | 已證實／高 | `evidence-template.md:53–56` 用本地 `instanceof` 錯拒有效 Buffer，直接阻止原件落地與 bind | 修範例的 byte array 判斷；保留真正的原件與讀回 gate |
| R2 | 已證實／高 | 多個 predicate 共用 `CUA_RAW_OBSERVATION_UNAVAILABLE`；未留下哪項失敗的 metadata，Agent 因此無法判別 | 拆分失敗階段、保存部分原件與診斷 metadata |
| R3 | 已證實／高 | 當次 `lists` 未走現有 notes_capture，約 63,099 tokens 輸出被截斷；已有保存規則卻未執行 | 優先執行既有 `download-and-ledger.md:225–231`，不新增 compact CLI |
| R4 | 已證實／高 | 在未收斂候選時查了截斷輸出中一份尚未確認相關的 memory | 只展開有來源依據的候選；該帳本 blockers 不得套用目前列表 |
| R5 | 已證實／高 | 把本地合併 guard 失敗說成「CUA 沒有截圖／需要 Owner 修復」，未先作可判別的唯讀查證 | 更正報告，區分未取得、型別不相容、寫入失敗及身分未定 |
| R6 | 已證實的驗證缺口 | 前輪文件核對與 Python 回歸沒有實際執行這份 CUA 範例，沒走到本次失敗點 | 首切片必須在原生 runtime 執行範例並讀回原件 |
| U1 | 仍 UNKNOWN | 舊 viewer 的下載控制如何可靠顯示、定位及證明作用 | 原件修復後沿既有正常導覽查證；不可預設 hover／右鍵有效 |
| U2 | 尚未驗證 | 這次畫面與哪份歷史帳本唯一對應、全列表覆蓋、五張媒體當前身分及資格 | 日常備份步驟；本輪沒有據截圖名稱或張數認領帳本 |

Skill `SKILL.md:21` 及 evidence reference 明文要求原件無法保存時停在 bind 前；**該保護沒有錯**。錯誤在範例誤判，以及 Agent 將未診斷原因升格成外部阻塞。`SKILL.md:31` 本已允許安全唯讀查證，因此不需要再放寬派送權限。

## 5. 先前嘗試與重試界限

| 嘗試 | 真正執行／新增學習 | 不可推論 |
|---|---|---|
| 前輪 S1 文件實作 | 授權更新、入口分流、lists 保存規則等已交付；既有回歸結果保留 | 不代表範例在 CUA 可用、不代表 U1 已解 |
| 本次日常啟動 | 一次 CUA 合併 guard 失敗；未保存原件、未 bind、未 intent | 不證明服務端／LINE 下載失敗，也不證明截圖 bytes 不存在 |
| 本輪重新規劃 | 一次新增唯讀 capture，取得實際型別；同一物件保存、讀回及比較 | 不是下載或產品修復；未核對列表歷史，不計照片完成 |

針對本次觀察誤判已有兩次實際 capture（舊失敗一次、本輪診斷一次）。多次解釋、同一物件的保存／型別比較及未 dispatch 的工具呼叫，不是新 GUI 嘗試。下一個原生修正後 smoke 限一次；若同根因仍失敗，保留新證據並停止，不換 Session 重置次數，不增加第四次。U1 的既有嘗試歷史另保留，不能用 R1 修復宣告其額度重新開始。

## 6. 修正方案與寫入邊界

採用 **現有 Skill 範例的有界修正＋既有流程的實際執行**。只擴大對正確 byte array 的辨識，不降低來源或交易保護。

| 路徑 | 後續實作可改內容 |
|---|---|
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` | 主要切片：可靠型別檢查、保留精確 bytes、分階段錯誤、部分原件及同物件查證說明 |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md` | 最多一個短說明／連結：AX 標籤缺失要實際檢視原始畫面；區分觀察轉接問題與來源身分不明，不重複完整流程 |
| `docs/plans/20261112-notes-download-control/` 新 implementation 子目錄 | 更正舊敘述的實作報告、實際驗證與交接；不覆寫舊報告 |
| 新私有 task | 原件、收據、來源 hash、離線 fixture、範例執行證據、HTML；不提交 |

`SKILL.md` 與 `download-and-ledger.md` 的現有授權更新、bind gate、完整 lists 規則足夠，預設不再增加同義條文。若主要 reference 的短連結確有必要，只能補定位，不新增門檻。

禁止修改 `src/`、Python tests、CLI 公共介面／事件 schema、相簿 Skill、正式 Prompt、AGENTS、全域 `.codex`、帳本／索引／active／照片／LINE 資料庫；禁止新 GUI 控制器、固定座標、相簿 Save All fallback、新日常模式或泛用 adapter。後續日常備份依自身授權使用帳本與照片，不屬開發文件的可寫 scope。

未採用的替代方案：

- 刪除原件保存 gate：會失去跨 Session 可核對的來源，拒絕。
- 只補 `constructor.name === 'Buffer'` 或接受任意 `.length` 物件：不能可靠驗證真正 bytes，拒絕。
- 只用 `ArrayBuffer.isView`：也會接受 DataView／Uint16Array 等非預期型別，不能當完整判定。
- 重裝 CUA、要求 Owner 換介面：已有截圖可保存的直接反證，不採用。
- 新增 compact CLI／更多長條文：現有 capture 已能保存完整輸出；先修遵循與範例。
- 預先支援所有 `screenshots` regions：文件雖允許 optional regions，但本輪實際是單一 screenshot；不擴成未觀察的平台相容工程。遇到不同形式要具體報 unsupported shape，不得誤稱工具無截圖。

## 7. 實作切片及成功條件

### S1：先修可執行範例，走到真正失敗點

1. 使用 Node 內建 `node:util` 的 `types.isUint8Array` 辨識真正 Uint8Array／Buffer，檢查非空 byte length；本輪同一個 CUA Buffer 已實測 true。`node:buffer` 顯式匯入 Buffer，避免依賴未承諾的 global。不要依 constructor 名稱猜型別。
2. 對已確認的 byte array 建立精確視圖範圍的不可變副本，例如 `Buffer.from(image)`；不得只取整個 backing buffer。保存原始影像格式，不解碼／轉碼當原件；沒有可靠 MIME 就使用 `.bin`。
3. 分開記錄 capture shape、AX 檢查、影像型別／空值、AX 寫入、影像寫入、讀回等失敗階段。metadata 只記欄位、型別、長度、錯誤與引用，不把完整原圖／AX 丟進公開錯誤輸出。
4. 同一次 capture 若只有部分資料可保存，先安全保留部分原件與原因，但仍禁止 bind。採唯一新路徑、`wx`、私有權限、canonical 路徑與逐 bytes 讀回；不覆寫既存檔，不把後補 statement 冒充 raw result。
5. 保留同一 capture 供唯讀查證；資料取得成功而本地型別判定錯誤時可檢查同物件，不以重做 GUI 輸入補證據。真正缺 bytes、寫入／讀回不符、來源身分不明，各報對應缺口。
6. 實作者將**最終 Markdown 範例本身**置於原生 CUA runtime 執行一次：只擷取與保存，不 bind、不輸入 GUI。不可只另寫一個相似腳本通過，就宣告範例已修好。

首切片通過須同時有：正確型別接受／錯誤型別拒絕、精確 bytes／hash 讀回、原生範例執行成功、不可覆寫及失敗不 bind。它完成的是 R1／R2／R6，R3／R4／R5 還須由後續實際行為與報告更正關閉。

### S2：依既有日常入口接續來源核對

由日常備份 Agent 使用手冊附錄 C 的既有入口；不要求 Owner 帶 replan、UUID、JSON、內部模式或逐張命令。Owner 既有窄範圍仍只涵蓋指定五張照片，盤點全列表不等於下載其他貼文。

1. 以現有 `notes_capture --output-root ABS_PRIVATE_TASK_DIR -- lists` 保存完整 request/stdout/stderr/exit；capture 保存失敗不得為補輸出重跑 child。確認 child exit 0、完整 JSON 可解析後，只向對話輸出所有候選的必要短表。
2. 用 hint 的 root＋ID 定位候選，再和當次畫面與連續入口交叉核對。hint 過期、指向測試 task 或不在候選內時，不改 active、不任選第一份 memory、不新建空帳；查閱全部候選與必要 history。真有多個不可解候選才問 Owner 一項具體缺口。
3. 需要刷新時只對已選候選序列 capture 一次 summary。另一列表的 LOCAL_CHANGED、restart 或 unresolved 不能套成目前列表 blocker；目標列表自己的阻塞仍必須尊重。
4. 保存並讀回 observation 後才 bind。遵守舊 attempt、scan binding、完整卡片覆蓋／來源 rows 雙向對帳，然後細盤指定貼文。畫面是列表時按已核對入口正常導覽；不要求先看見 viewer 下載控制才能盤點。
5. 當次前景確實中斷才需要重新交接；capture 型別錯誤不自動撤銷原授權。規劃角色仍不憑歷史授權直接轉成下載角色。

### S3：完成照片與如實收尾

1. 重新核對指定貼文的五個獨立媒體來源、順序、種類、viewer 與可歸屬本 Notes 的控制。來源有編輯／張數或身分差異時，保留差異，不擴張授權。
2. 控制仍未能可靠判定時，沿已有 `gui-inventory.md` 有限查證；不猜 hover／右鍵、不沿用相簿控制、不建 intent。U1 必須如實保持 UNKNOWN，不能因 R1 已修就關閉。
3. 一次一項：intent、新空白 staging 與禁止重送紀錄保存／讀回後，重定位控制，單次派送並即時保存原始結果與 chooser；不因結果未知再次點擊。
4. 依真實 outcome 決定 verify／reconcile／resume。逐檔穩定、非空、SHA-256、ImageIO 完整像素解碼、發布與 completion 讀回均成立，才計完成。UNKNOWN／活動下載／未完成命名／LOCAL_CHANGED 及精確 restart 原規則不變。
5. 所有指定照片各有 completion 才能宣告本批完成；已下載、已驗證、待處理與未測分開計數。全列表其他貼文若未細盤，不能說整份列表完成。實際位元與服務端原始檔完全一致、其他模型或其他 Session 一定成功，均非本批證據可保證。

## 8. 驗證矩陣、責任與停止條件

| 檢查 | 責任／充分證據 | 停止條件 | 本輪狀態 |
|---|---|---|---|
| 舊 guard vs 實際 payload | 主代理；同一物件的 shape／型別比較與保存收據 | 無可判別資料不得確診外部故障 | 已取得新診斷證據 |
| 範例的離線語意 | Implementer；從最終範例擷取實際邏輯，私有 Node fixtures：Buffer、本 realm／vm realm Uint8Array、非零 offset 子視圖，均保留精確 bytes；空值、字串、Array、DataView、Uint16Array、偽裝物件須拒絕；碰撞／寫入／讀回失敗不 bind | 接受非 bytes、保存越界 bytes、覆寫或虛報成功 | NOT_RUN |
| 原生範例 smoke | Implementer；實際最終範例在 CUA 執行，同次 AX＋截圖讀回 MATCH；僅觀察 | 第三次同根因 capture 仍失敗即停止 | NOT_RUN；本輪診斷不是最終產品 smoke |
| 現有基線回歸 | Implementer；以下三條既有命令各一次，保存真實輸出／exit | 非零不在文件 scope 自行修程式 | 本輪 NOT_RUN |
| 完整 lists 與候選核對 | 日常 Agent；既有 capture 收據、完整 JSON、全部候選短表、來源對應 | 不完整、不可解析、歷史缺損／歧義，不寫帳 | NOT_RUN |
| 原生備份功能 | 日常 Agent；卡片覆蓋、指定五張來源、Notes 控制、單次派送、outcome、五筆驗證及 completion | 控制／身分未知、前景中斷、未解交易，停止依賴動作 | NOT_RUN |
| 發布前保護 | 各交付者；逐檔 diff、無私人內容、既存 untracked hash 不變、commit body、遠端精確 HEAD | dirty 衝突、非授權路徑或私密內容，不 stage／push | 本輪按交付實際記錄 |
| 獨立接受 | 使用者安排；貢獻者不能簽發 | 未執行保持 NOT_RUN，不預填 PASS | NOT_RUN |

基線命令（後續實作時執行；不能取代原生 smoke 或真實備份）：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

修正不承諾外部 writer、焦點、視窗或服務端永遠不變，也不承諾 GUI exactly-once。可保證的是每次派送前保留可核對 intent、每次 attempt 限定一次當次下載控制，以及結果未知時依原規則禁止重送。

## 9. 具體停止與交接規則

- 只要有效原始資料尚未保存，就停在 bind 前；可在原授權範圍檢查同一次資料及其他安全唯讀來源，不能把停止擴張成所有查證都禁止。
- 真實 notes CLI exit 70、未解派送、ledger 完整性或 scan binding 異常，維持原停止；不換入口／目的地繞過。
- 遇到尚未實測的 regions 格式、需要改 src／資料語意／對外介面或超出可寫 scope，保留精確證據後交 Owner 決定，不自動擴充。
- 同根因最多三次、連續兩次沒有新資訊即停；不重播下載只為補收據／修錯誤報告。
- 舊進度錯誤以新文件指明範圍與新證據更正，不改寫歷史成「當時已知真因」。
- 回報依序說：目前看到什麼、哪一步未成立、已下載／已驗證數、下一個具體動作與責任。只有精確證據支持時才稱外部阻塞；不用籠統 BLOCKED 取代說明。

## 10. 本輪結果、命令與人工交接

本輪完成 Git／規範／原始碼與歷史來源核對，新增一次唯讀 CUA 回傳格式診斷，保存及看過同一筆原件，驗證可靠型別判斷可接受該 Buffer。沒有執行產品回歸、完整 lists 重查、bind、GUI 輸入、下載或獨立驗收。

實際 Git/read 命令、來源 hashes、診斷收據及同角色唯讀助手整理存私有 task；`progress.md` 記錄讀取不存在 repo policy 路徑的 exit 1、一次本地 view_image dispatch 前 aborted、診斷不具 `process` global 等細節。這些不是 LINE／notes CLI 的業務錯誤。沒有重播失敗下載或重新建立歷史事實。

| 狀態 | 本輪判定 |
|---|---|
| PRIMARY_OUTCOME_STATUS | BLOCKED：指定照片尚無完成證據；重新規劃文件已完成 |
| IMPLEMENTATION_STATUS | NOT_RUN：本 replan 修正尚未實作；先前 S1 成果保留 |
| CORE_ACCEPTANCE_STATUS | BLOCKED：缺來源核對、實際派送及照片 completion |
| REQUIRED_VERIFICATION_STATUS | PARTIAL：型別誤判診斷、原件保存讀回及畫面 OBSERVED；最終範例 smoke／回歸／下載驗證 NOT_RUN |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN：未啟動 Review／獨立接受 |
| TASK_CLOSURE_STATUS | BLOCKED：本輪規劃可交接，產品修正與備份尚未結案 |

下一步是由 Owner 按原人工角色契約啟動有界 Implementer，先完成 S1。若沿用本任務既有委派選擇，實作助手請求為 **GPT-6 luna、high**，由主代理監督且不授予獨立接受；本輪唯讀規劃助手未覆寫模型，不能將它冒稱為指定模型的實作成果。實作後以既有日常正式入口完成 S2／S3，無須把 replan 變成新的 Owner 啟動條件。
