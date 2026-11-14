# 記事本第 4 張下載結果未知：選點與控制區域的因果分析

## 本角色判定與邊界

**ANALYSIS_COMPLETE；唯一建議路線：`IMPLEMENTER_FIX`，限既有定位步驟與證據說明的最小文件修正。**

保存的第 4 張輸入 receipt 記載 `[1226,158]`，與下載前原圖中的下載圖示區域不一致。第 3 張成功案例的 `[1226,119]` 則落在同位置的圖示範圍內。這支持「此次視覺選點未與實際送出參數完成核對」為高置信度直接根因候選；**不是 CUA 原生事件落點、LINE hit-test 或完整工具根因已確認**。

指定的 `06_high_reasoning_review_prompt.md` 明定本角色只診斷，不修改產品、不執行建議、不啟動下一正式角色。使用者要求第一性原理與最佳實務，本報告據此分析並給出可執行的最小矯正邊界；「fix all issues」不在本角色內轉成實作或重新下載。本輪只新增分析與離線診斷 artifacts，沒有修改 Skill、程式、提報單、帳本或照片。

底層備份仍受阻：保存的最終 summary 為 3 張完成、第 4 張 UNKNOWN、第 5 張 PENDING。本輪未刷新真實帳本或重新解碼照片，保留這些已證明結果，不宣稱列表完成。

## 1. 問題、候選與授權身分

- 選定根因：`R-NOTES-CLICK-GROUNDING-20261112-01`，解釋「已可見下載控制，但一次控制輸入後沒有可歸屬結果」。
- Repo：`Line_backup`；分支：`feature/line-notes-media`；本輪輸入 HEAD：`0d85dfa6564fcaebbc7b49bd001dac5bd8682a01`。
- 提報單記載的事發產品 HEAD：`65e93d51fc3fc8bb6b1aa58136cd862bf39600ee`。本輪核對這兩版的 notes Skill 與 `notes.py` 無差異；輸入 HEAD 只新增提報單。
- `notes.py` 本輪 SHA-256：`75bf2f7663fbd21106ea61da3c50da66262f962a9a36fe0a3b021a89909654aa`，與提報單相符。
- 起始本機與遠端分支 HEAD 相符；唯一既存未追蹤檔為 `issue提交單.md`，保留原狀。
- 事發版本由提報單記載：macOS 27.2.1／26B131、LINE 26.0.2／3828、Python 3.9.6。本輪沒有重新查詢事發 app 版本；CUA build、精確輸入與 capture 時鐘仍 UNKNOWN。
- 可讀範圍：交接報告、相關規範、該私有任務保存的 GUI 原件／receipt／CLI capture；沒有搜尋私人 Downloads、其他列表、實際媒體或帳本 events。
- 可寫範圍：本診斷目錄及該私有任務新增的 `diagnostics/click-grounding-review-20261112/`。未取得新的 GUI 前景或下載授權。

本輪使用一名原生、繼承 session 設定的同角色唯讀助手核對規範與責任分層，未提供 model／effort override。此為請求參數與工具回覆層的事實；沒有 provider 使用紀錄，不主張後端身分、token 節省或量測成本。助手不是獨立驗收者。

## 2. 第一性原理：何處的必要關係斷裂？

下載至少經過下列互不替代的命題：

| 層次 | 必要命題 | 本案可支持的範圍 |
|---|---|---|
| 來源與資格 | 指定列表／貼文／媒體合格，intent 已持久化 | 保存的任務紀錄與 capture 支持；本輪不重建帳本 |
| 視覺定位 | 當次來源中的控制歸屬與作用已辨識 | 原圖可見 LINE 工具列右側向下箭頭；照片內的網頁介面不是 LINE 控制 |
| 參數一致性 | 送出點落在當次選定控制區域，座標空間一致 | **receipt 記載的點與原圖圖示區域不一致** |
| 原生輸入 | 工具將事件送至預期 window／view | UNKNOWN；無 native event／hit-test trace |
| App 回應 | LINE 接受控制並產生可歸屬 chooser 或下載結果 | 第 3 張有保存的 chooser；第 4 張未取得正面證據 |
| 檔案與完成 | 原目的地穩定檔集、hash、解碼與 completion | 第 1–3 張沿用已保存結果；第 4 張沒有可驗證結果 |

若以截圖像素表示圖示區域 `G`、receipt 記載點為 `p`、工具轉換為 `T`，視覺定位至少應滿足 `p ∈ G`。原生命中還需要 `T(p)` 落在實際控制的 hit area。前者不成立，已足以拒絕把該點當成可靠定位；前者成立仍不能證明後者。

因此安全停止與任務可完成性必須分開：UNKNOWN 保護了尚不能排除的副作用，但沒有修好視覺選點。第 5 張的 PENDING 是第 4 張未決交易造成的下游阻擋，不是第 5 張圖片本身故障的證據。

## 3. 新增直接證據與提報內容校正

### 3.1 改用下載前的原件，避免時間順序倒置

提報單第 3.1、15 節把 SHA-256 `f539965e…b8e67c` 圖稱為 pre-click。該 observation 的 input label 是 `16:51:44`，metadata 的 capture label 為 `16:51:45`；第 3 張同名 download-control observation 已是「儲存」chooser。故不能把這組 download-control 圖當成已證實的輸入前畫面。

本輪改以第 3／4 張各自較早的 **reveal-toolbar observation** 比較下載前圖示。第 4 張該 label 為 `16:51:15`；輸入與 capture 的精確時鐘均 UNKNOWN。這是保存序列的重建，不能保證直到實際 mouse-down 間完全沒有 UI 漂移。

### 3.2 可重核的圖示像素量測

直接檢視兩張 reveal-toolbar 原圖後，使用 macOS `/usr/bin/sips` 另產 BMP 診斷副本，以 Python 標準庫讀像素；原 JPEG bytes 不改。固定分析區域為半開區間 `[1215,96,1258,139)`，選取 RGB 各通道均不小於 180 的亮色像素。

| 項目 | 第 3 張 | 第 4 張 |
|---|---:|---:|
| 原圖／副本尺寸 | 1280×960 | 1280×960 |
| 圖示亮色像素包圍框，含端點 | `[1220,103,1251,134]` | `[1220,103,1251,135]` |
| 包圍框中心 | `(1235.5,118.5)` | `(1235.5,119.0)` |
| receipt 記載的下載點 | `[1226,119]` | `[1226,158]` |
| 該點在亮色包圍框內 | 是 | 否；y 比下緣再低 23 px |
| 保存的後續結果 | chooser／後續完成紀錄 | 無可歸屬正面終結，記 UNKNOWN |

量測的是**可見圖示像素**，不是原生按鈕 hit area；固定 ROI 與亮度門檻由分析者選定，不是控制偵測器。它支持兩張原圖的工具列圖示位置近乎相同，不證明 window origin／Retina scale／native event mapping 一致。中心 x 約 1235.5；提報的 x=1226 是輸入值，不能再稱精確圖示中心。

原圖也顯示 y=158 已在照片顯示內容內；其中的網頁操作介面是圖片的一部分。提報單「下方淺色 app bar」的說法會混淆 LINE 活控制與照片內容，應一併校正。這些座標只是本事故的分析數值，**不得寫成之後的固定點位**。

### 3.3 receipt、原件與帳本證據的界限

- 第 4 張 `.input.json` 記錄 target、coordinate_space、`call_completed=true`、字串 `raw_return="undefined"`；第 3 張相同回傳卻有 chooser。因此 undefined 不能用作失敗根因。
- `.input.json` 是 Agent 保存的 `line-notes-cua-input/v1` 紀錄，沒有 native event trace／tool-call ID 或可信精確時鐘。本輪確認的是**保存紀錄所報參數**，不能升格為 OS 已送達的物理座標。
- 第 4 張 bundle 的 14 個 assets 加 1 份 statement，共 15 份來源的 bytes 與 SHA-256 全部相符。這證明引用內容身分，不證明 statement 中「點到下載」的敘述為真。
- 封存 final summary capture 為 `COMPLETED=3`、`UNKNOWN=1`、`PENDING=1`、`dispatch_blockers=["UNKNOWN_ATTEMPT"]`。它是歷史保存結果，本輪未執行 summary／verify／reconcile。
- staging 空、app-bound 未見 chooser、沒有錯誤 UI 都只是有限範圍的觀察，不能證明原操作不會晚到，也不能排除其他位置的結果。

## 4. 最小失敗軌跡與既有嘗試

以下只重建已保存序列，**沒有重播**：

1. 第 3 張 reveal-toolbar 原圖顯示工具列；receipt 記載 `[1226,119]`；後續保存「儲存」chooser、一次最終確認及完成紀錄。
2. 第 4 張選取與 pre-download observation 顯示 4/5 viewer；縮圖列收合後，reveal-toolbar 原圖顯示同位置的向下箭頭。
3. 第 4 張 download-control receipt 記載一次 `[1226,158]`；其後兩張 app-bound 畫面沒有可歸屬終結訊號。
4. staging 觀察記零個頂層項目；outcome capture 的 child／outer exit 都是 0，保存 UNKNOWN。CLI 成功不等於下載成功。
5. 保存的 summary 以 UNKNOWN_ATTEMPT 阻擋後續；第 5 張尚未建立 intent。

| 既有工作／本輪核對 | 新資訊 | 重試歷史如何處理 |
|---|---|---|
| 先前「控制不可見」診斷與後續控制發現 | 從 intent 前停滯轉成能看見並使用控制 | 與本次已見控制後的選點偏差是不同失敗條件；不拿來充當同根因修復次數 |
| 第 1–3 張既有完成 | 證明部分來源與當時控制路徑可完成 | 不是本次第 4 張的重試；也不能保證第 4 張會成功 |
| 第 4 張一次下載控制呼叫 | 保存參數與無終結結果，之後保護性停止 | 沿用這一次事故與 UNKNOWN；不能因新 session 重新計算 |
| 提報單 0d85dfa | 找出 119／158 差異 | 文件整理，不是修復或新派送 |
| 本輪 | 改正前後圖順序、比較真正較早原圖、像素量測、15 份引用完整性、責任分層 | 有新資訊的離線診斷；下載／修復嘗試均未新增 |

可得證據未列出本根因的其他修復嘗試；不宣稱尚有可自由使用的兩次下載額度，也不把記錄缺席當成不存在。後續仍須沿用同根因最多三次有證據嘗試、連續兩次無新資訊即停止的限制。

## 5. 因果判定、替代解釋與可反證性

**首選解釋：視覺控制已辨識，但送出前沒有成功核對「這個具體點是否仍落在這個控制區域」。** 現有規範其實已要求 fresh 定位；故不能把事故說成完全沒有規則。此例同時暴露規範尚缺可回核的「控制區域↔準備送出點」對帳方法，泛稱重新定位未能攔下這次矛盾。

規則來源為 `.agents/skills/line-notes-agent-cua/SKILL.md:59`、`references/download-and-ledger.md:266–269` 與 `references/gui-inventory.md:112–115,130–132`；證據模板 `references/evidence-template.md:365–366` 尚未明列控制區域與候選點的對帳。UNKNOWN 的正面停止證據要求見 `references/download-and-ledger.md:272` 與 `references/verification-and-recovery.md:24–35`，不能由本案的像素分析取代。

| 解釋 | 支持／限制 | 反證或改判條件 |
|---|---|---|
| Agent 選點／參數一致性失誤 | 兩張較早原圖的圖示 y≈119；receipt 卻記 158 | 原始工具呼叫參數其實不同、較晚可靠原圖顯示圖示移到158，或工具明示輸入採其他座標空間 |
| receipt 記錄錯誤或來源不一致 | 現有 receipt 不是底層 event trace | 若原始呼叫／平台 trace 證明不是158，應改查記錄與工具映射，不能繼續指控實際誤點 |
| CUA crop／scale／origin 轉換錯誤 | 仍未知；同 Session 第3張成功限制了「一律固定偏移」的解釋 | 取得當時工具版本與轉換證據，顯示正確參數被轉至錯誤位置，才支持工具缺陷 |
| LINE 忙碌／disabled／服務問題 | 沒有明確 app 錯誤，且第4張尚未證實命中控制 | 原生 trace 證明命中有效控制，卻產生可歸屬拒絕或故障，才需優先查此分支 |
| chooser 晚到或範圍外 | app-bound 與空 staging 無法排除 | 可歸屬該原 attempt 的新證據可調整結果判定；本角色不搜尋其他私人目錄或操作 GUI |

因此目前可以定位**最早有直接可見矛盾的層次**，不能定位 y=158 的心智計算來源，也不能確認是哪段 CUA 程式有 bug。H1「選點偏差」與 H3「點到背景／照片」是同一因果鏈的不同描述，不宜當成兩個獨立故障，要求 Agent／Skill／CUA 三層一起改。

## 6. 唯一建議路線：IMPLEMENTER_FIX

**由 Owner 另開實作 Session，限下列三個文件路徑的小修。** 這是路線建議，不是實作派送或驗收 PASS。本輪已完成可做的原件對帳，不建議再重做相同離線比較來等待更多報告。

| 路徑／範圍 | 應交付的具體修正 |
|---|---|
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` 的「讀回後再次定位」 | 沿用原步驟，要求由當次原件標出控制可辨識區域與準備送出的點，確認來源空間及點位一致；點在區域外或不確定就停在輸入前。不得以第3張點位作第4張固定模板 |
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` 的定位／輸入紀錄 | 補入原件引用、pre/post 或先後未知、當次控制區域、候選點及核對結論。這些是私有 Agent 證據欄位，不增 notes CLI／event schema 必填欄位；bbox 不是 native hit-test，capture label 不是可信操作時鐘 |
| `問題提報單.md` | 校正 f539 圖的 pre-click 稱呼、精確中心與照片內容區敘述；第12節的「明確未命中」僅作定位分析，不得直接推成 NOT_SENT 或解鎖規則 |

此修正採用的原則是：**在不可安全重送的輸入前核對具體參數，將每一層的證據與結論分開；結果未知時保留原交易。** 不新增 controller、不硬編碼座標、不增加 Owner 日常啟動步驟、不以 AX 缺標籤擴張架構，也不加入缺乏本案證據的 CUA／LINE 程式修正。

成功檢查：

- 以本次保存證據作文件走讀，能在輸入前拒絕 y=158，並說明 y=119 只在當張來源與映射核對成立時可作候選；不能把「落在像素 bbox」當成下載成功。
- 缺原件、來源空間／控制歸屬不明、pre/post 不可判定或幾何改變時，文件給出明確停止而非猜點。
- 已呼叫輸入後，即使圖示外落點，也不能僅據此把 UNKNOWN 變成 NOT_SENT；正面停止證據與原有 recovery／restart gate 保留。
- diff 只在上述文件；相簿公共介面、notes 程式／事件／摘要語意、歷史完成與 UNKNOWN 均不變。文件檢查不替代真實 GUI、chooser 或跨 Session 驗證；那些維持 NOT_RUN。

停止條件：需要修改 CLI／平台映射、增加重試、改帳、擴及其他檔案或必須取得新 GUI 前景才能繼續時，回報具體證據並交回 Owner。遇到與保存 receipt 衝突的原始工具 trace，也先停止，不在同一角色跨層修復。

所需人工決策只有後續角色交辦：是否依上述有界文件範圍啟動 Implementer。**本建議不處理原 UNKNOWN 的恢復授權，也不自動派送第5張。** 日後確認實際備份能力仍用使用手冊對應的日常正式 Prompt；不能拿此診斷或文件走讀當真實備份驗收。

## 7. 實際命令、證據與未執行範圍

工作目錄為專案根目錄。公開來源與量測值見 [sources.redacted.json](sources.redacted.json)；原始畫面、statement、derivative BMP、完整關鍵命令 `commands.md` 與 51 檔案的前後 manifest 均留在專案私有任務的 `diagnostics/click-grounding-review-20261112/`，不提交。收尾 51 份來源 hash 均未變，公開文件的姓名、列表名、完整家目錄與列表 UUID 掃描未發現未遮蔽值；這是限定詞彙檢查，不是通用匿名化保證。

| 本輪實際命令／工具 | 退出碼或結果 | 可證明範圍 |
|---|---|---|
| `pwd`、`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | exit 0 | 起始 repo／候選／既有未追蹤工作；未操作其他 worktree |
| `git diff --exit-code 65e93d51fc3fc8bb6b1aa58136cd862bf39600ee HEAD -- .agents/skills/line-notes-agent-cua src/line_backup_batch/notes.py` | exit 0，無差異 | 事發產品與本輪對應路徑一致 |
| `git ls-remote --exit-code origin refs/heads/feature/line-notes-media` | exit 0，回傳 0d85dfa6564fcaebbc7b49bd001dac5bd8682a01 | 起始遠端 HEAD；不是外部審查 |
| `shasum -a 256 src/line_backup_batch/notes.py` | exit 0，與提報 hash 相同 | 模組 bytes 身分 |
| `view_image`：第3／4張 reveal-toolbar 與第4張 download-control 原圖 | 成功 | Agent 檢視封存畫面；不標真人 OBSERVED／即時 GUI PASS |
| `/usr/bin/sips -s format bmp <第3或4張reveal-toolbar原圖> --out <私有新BMP>`，各一次 | 均 exit 0 | 離線衍生副本；原圖未改 |
| `/usr/bin/python3 -B -`，讀 BMP header／像素及保存 JSON | exit 0 | 24-bit 未壓縮 BMP；上述固定ROI／亮度法的量測結果 |
| `/usr/bin/python3 -B -`，bundle引用 bytes／SHA-256 與來源 manifest | exit 0，15份引用全相符 | 來源身分與引用完整性，不能認證語意 |
| 初次 `rg` 包含 notes 不存在的 `verified-experience.md` | exit 2；其他列出的 notes reference 仍有結果 | 搜尋路徑誤用，後續只讀 notes 正確 references；未執行任何產品或GUI命令 |
| GitHub connector `search_prs`，query 與 per_page 參數 | `INVALID_ARGUMENT`，argument_binding | 未取得 PR 資訊；不影響本機分析，未建立或更新 PR |

notes CLI、產品單元回歸、即時 LINE、下載、chooser、reconcile、verify、restart、影像重新解碼與獨立驗收本輪均 **NOT_RUN**；本角色未改產品，亦無此輪 GUI／真實資料操作授權。Git 文件檢查、checkpoint 與推送結果另存私有交付收據，不預填成產品通過。

## 8. 六項狀態與交接

- `PRIMARY_OUTCOME_STATUS=BLOCKED`：底層備份第4張 UNKNOWN、第5張 PENDING；本角色分析為 ANALYSIS_COMPLETE。
- `IMPLEMENTATION_STATUS=NOT_RUN`：修正僅為建議，未修改產品。
- `CORE_ACCEPTANCE_STATUS=BLOCKED`：指定列表尚未完成，未執行新接受檢查。
- `REQUIRED_VERIFICATION_STATUS=PARTIAL`：原件、引用、像素與版本對帳完成；產品回歸、即時 GUI、下載及恢復未執行。
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`：本診斷及助手結果不是獨立接受。
- `TASK_CLOSURE_STATUS=BLOCKED`：交回 Owner 決定下一角色，不自行修復、重測或結案。

本次最小修正能降低相同選點矛盾再次通過的風險；尚未經實作或日常入口實測，不能保證不同模型／Session 都能可靠完成。原3張完成事實保留，第4張原 attempt 與 staging 保留；本輪到此交接停止。
