# 計畫草稿 v1：記事本啟動接續與五張照片完成路徑

## 決策摘要

**先交付一個完整、有限的指示修正切片，再用既有日常入口確認實際能力。** 不再以尚未執行的控制診斷阻擋已有證據的啟動修正；也不把指示修正當成 viewer 控制已解決。

- 目標：Owner 明示更新授權後，Agent 能重新核對剩餘條件，自行從指定列表前進到目標媒體；在安全條件成立時完成指定五張照片的下載與驗證。
- 分級：**STANDARD**。雖然預定只改四份文件，但 Skill 指示直接影響真實 GUI、身分認領與派送前置。保留計畫及首個實作切片後的人工 Simplicity Review；不因未涉及資料格式／遷移而升為 CRITICAL。
- 本 Planner 的交付是 `PLAN_DRAFT_COMPLETE`，不是實作核准、產品 PASS 或下載授權。
- 最小充分方案：補「授權更新→剩餘條件重核→繼續或具體停止」分支、整理已有帳本摘要、補列表／viewer 分流，並撤下舊診斷 Prompt 的現行啟動指示。
- 不增加 Owner 的啟動步驟、模式、內部欄位或角色文件。記事本唯一日常入口維持[使用手冊附錄 C](../../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt)。本計畫及舊診斷文件均不是日常依賴。

### 要修正與要證明的問題

| ID | 問題／依據 | 最小處理與可觀察成功條件 |
|---|---|---|
| F1 | 授權更新後未重新評估；[補充分析](../startup-resumption-review/issue-analysis.md)第 2 節。具體事發決策仍依提報，原對話未知 | Skill 明列明示更新只取代對應舊限制；重核前景、身分、帳本後接續；沒有明示解除時仍不下載 |
| F2 | 舊診斷 Prompt 精確基準早於承載它的 commit；同分析第 1 節 | 舊文件改為歷史診斷參考、停止要求原樣貼上；日常不帶此版本門檻。正式角色仍核對 Owner 選定的交付候選，不自行 checkout/reset |
| F3 | 列表／viewer 說法不一致被當成終點；同分析第 2 節 | 先唯讀確認 app/window、來源與列表連續性；同列表且前景有效才正常導覽，仍不明只問一項具體缺口 |
| F4 | lists 大輸出未整理，已含摘要卻未用；`notes.py:618–635、5427–5450` | 保存完整輸出與退出碼、全部候選短表，hint 精確定位後仍交叉核對；只有刷新需要才查一次 summary |
| F5 | 舊文件錯引「手冊 B 區」；實際附錄 B 是相簿，C 是記事本 | 新交接與舊診斷文件的導引只連附錄 C；舊 plan／handoff／issue-analysis 保留為歷史，不再作現行步驟 |
| U1 | 舊 viewer 內沒有可證明下載控制；[原控制分析](../issue-analysis.md)第 3、5、7 節 | 必須另有同一 Notes 媒體的控制歸屬、作用、可用性及定位證據，並實際完成五張；只改文件或觀察到工具能力不足不能關閉此項 |

F1–F5 有具體指示修正位置。U1 的顯示機制仍 `UNKNOWN`；本計畫安排可驗證路徑及停止邊界，不預寫 hover 有效或 LINE 缺陷的結論。「全部問題已修復」必須包含 U1 的功能結果，不能只關閉文件項。

### 替代方案與取捨

- **採用現有 CLI＋小範圍指示修正。** lists 已回所有摘要，已有綁定／盤點／單次派送／驗證工具；無需新介面。
- 僅重貼舊診斷 Prompt：仍帶不下載與過期 HEAD，不採用。
- 先再做同內容診斷才准修啟動：會重新阻擋已有證據的 F1–F5，不採用。U1 保留獨立查證要求。
- 新增 GUI 控制器、compact CLI、schema、重試入口或更長正式 Prompt：沒有必要性證據，不採用。

## 範圍、版本與授權

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- **規劃輸入基準**：`3b12e41cd12e458118e94f62feab8da3c6054db9`，本輪起始遠端同 SHA。產品路徑自原事件版 `02db924fd89ff79067cd4958729a3ac6b8157437` 到此無差異。
- 輸入基準只識別分析來源，**不是要求承載本計畫的新 commit 還等於舊 HEAD**。本輪交付候選由提交後的精確 commit、plan SHA-256、來源 manifest 識別；Owner 將該 commit 交給下一角色。內容或候選實質改變由人決定重做哪些檢查，不能自動承接 PASS。
- 本輪可寫／提交：本子目錄 `plan.md`、`handoff.md`、`planner-report.md`、`progress.md`、`source-manifest.json`。
- 私有證據：`.local/line-backup/tasks/20261112-startup-resumption-planning/`，保存 preflight、來源 hash、命令／exit、助手資訊、文件驗證、HTML 與 Git 收據。不提交私人原件。
- 初始只有根目錄既存 untracked Markdown；不讀正文、不 stage、不改動，前後 SHA-256 核對。其他 worktree、既有計畫、提報、審查與 release 不改。
- 本輪授權是規劃及同範圍文件 checkpoint。**沒有當次 LINE 前景或真實帳本／照片操作授權。** 後續實作與日常試用由 Owner 按既有契約啟動，本文件不自動派送。

### 待核准的四檔產品修正範圍

| 路徑 | 可改區域與要求 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | 「日常入口與 Agent 責任」加短接續決策及 reference 定位。不重複抄交易硬規則；不讓 Planner／Reviewer 憑歷史授權轉成下載角色 |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | 「啟動與帳本對帳」補完整保存 lists、所有候選短表、hint root＋ID 匹配與必要時刷新。沿用既有 capture，不另造執行器或更改 CLI flags |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md` | 「入口判定」補畫面角色不同時的唯讀核對分支；在既有觀察規則處說明控制未見時的有限來源／狀態查證，不宣稱具體 UI 觸發已驗證 |
| `docs/plans/20261112-notes-download-control/next-agent-prompt.md` | 撤掉「原樣貼上」的現行使用指示，標明歷史非下載診斷。原 fenced Prompt 保留作歷史、不重寫過往授權；現行導引連記事本附錄 C，不提供另一份下載 Prompt |

實作者可在新私有 task 內使用不提交的機械整理腳本，限處理明示來源與輸出，不生成 LLM／GUI 控制器；不作新的日常安裝依賴。報告與範圍內文件可在本任務新增 `implementation/` 子目錄，不能覆蓋本輪 plan／handoff／來源。

禁止修改 `src/`、`tests/`、相簿 Skill、使用手冊正式 Prompt、`AGENTS.md`、全域 `.codex`、帳本／索引／active／照片或 LINE 資料庫；不建新 framework、移除 gate、變更資料語意、merge master 或 force-push。若實證需要以上修改，停止並交 Owner 重新決定範圍，不把「fix all」視為無界修復。

## 實作行為與首個可驗證切片

### S1：四份指示構成同一個最小完整切片

S1 可為最終文件切片，不拆出先放寬規則、日後再補保護的中間版。低影響措辭與段落位置由 Implementer 決定；不得增加新日常前置。

1. **更新任務狀態。** Owner 明示從診斷切換為指定備份、解除不下載或接受目前版本時，記錄新範圍與被取代的限制，逐一重核剩餘條件。只有一般「繼續」不推成解除限制。日常更新不替代正式角色的人工交接，審查角色不因引用歷史授權自動下載。
2. **收斂帳本候選。** 完整保存一次成功 lists（含 stderr／exit），先確認可解析與成功，再為所有候選顯示內部短表；不得用 head／工具截斷當全部結果。hint 的 root＋ID 只定位，當次來源仍須支持 identity/context。缺 hint 保留全部候選；無匹配、多候選或歷史異常不建空帳。只需刷新才序列查 summary，不沿用 hint 的舊 session ID 綁定。
3. **判定當前畫面。** 在有效交接內取得最新 app/window、AX／畫面、來源範圍並保存原件。列表是正常入口；來源未確認前不點卡片、不捲動、不建 intent。同列表、前景與身分已成立，照原流程盤點卡片、細盤目標及開 viewer；不逐點請示。仍不明只說明具體缺口並問一件事，真正前景中斷則等重新交接。
4. **面對未見控制。** Viewer 就緒與媒體身分成立後，先核對當次工具能力與觀察 scope。可用時，以同媒體、同幾何取得最小來源對照；只有原生文件明確支援無點擊移鼠，且目標區域／映射／作用安全有據，才作一次狀態對照並重新觀察。未支援記 NOT_RUN，不猜 API、不用點擊／拖曳／右鍵模擬、不切五張充當控制實驗。不把此方法寫成已驗證的「顯示下載按鈕」操作。
5. **維持派送門檻。** 找到圖示仍需證明是此 Notes 媒體的控制及作用，才依原 Skill 建 intent；仍不明就停在 intent 前。未知派送依原歷史規則收斂，不能用新目錄或另一入口重送。精確 restart 例外保持原條件，不由授權更新分支擴張。
6. **清楚回報。** 說明目前畫面／已確認事項／缺哪一條件／已下載及已驗證數／下一步；版本與內部帳本細節只在對決策有用時展開。下載與驗證分開計數，不用「尚未下載」取代所有可做的查證。

## 驗證、責任人與停止條件

### 文件層：S1 必須證明的決策情境

以下是人工對照矩陣，不新增仿實作測試。Implementer 在交付報告逐項引用最終文件位置，Simplicity Reviewer 獨立核對，不憑助手自評批准。

| 情境 | 應有決策 | 不合格／停止條件 |
|---|---|---|
| 明確不下載仍有效 | 不下載；可在既定診斷範圍讀取 | 擅自當作備份授權 |
| Owner 明示解除且限定五張 | 更新對應限制，重核剩餘條件後接續 | 繼續引用已解除限制、擴成其他貼文下載或要求重貼整套 Prompt |
| 只說「繼續」 | 保留未明示解除的限制 | 猜測已取消不下載 |
| Owner 接受目前版本 | 不再以已接受的舊 HEAD 差異阻塞日常備份 | 忽略格式／資料損壞、換候選仍冒用舊 PASS |
| lists 多候選、hint 無／過期／不符 | 保留完整候選並核對來源；無法唯一對應即具體停止 | 唯一依 hint、名稱、日期或五張數字認領；另建空帳 |
| 正確列表、viewer 尚未開 | 核對後按既有盤點與導覽前進 | 把列表當下載功能失敗、未確認前猜點 |
| 另一列表或前景中斷 | 停止依賴該前提的輸入，保留資料並指出缺口 | 用新授權、猜返回或舊座標繞過 |
| 控制未見／工具不支援 | 有限查證、誠實列能力與未知，仍不明停在 intent 前 | 虛構 hover 成功、猜控制、無限重查 |
| UNKNOWN／活動下載／命名未完／LOCAL_CHANGED | 沿用原保護及精確例外條件 | 用接受版本／一般繼續解除帳本阻塞 |
| Planner／Reviewer 讀到歷史下載授權 | 維持當次角色邊界 | 擅自轉下載或寫真實帳本 |

### 必要檢查與所有者

| 檢查 | Owner／證據 | 停止條件／目前狀態 |
|---|---|---|
| 候選、來源、既有工作 | 各角色開始／收尾；Git root、branch、HEAD、status、來源 manifest／hash | 身分／寫入衝突或必要來源不明；Planner 已做唯讀核對 |
| 文件切片範圍／連結／一致性 | Implementer；精確 diff、四檔對照、上列情境、硬規則未放寬、無私人內容 | 超出四檔或引入新啟動步驟即停；NOT_RUN |
| 既有最小回歸 | Implementer；下列三條專案命令的 stdout／stderr／exit，僅確認既有工具基線 | 非零 exit 如實保留，不在文件範圍自行修程式；NOT_RUN |
| 計畫與實作切片的簡潔性 | Owner 分別啟動 Simplicity Reviewer；精確 plan／candidate 對應的報告 | 拒絕或未解 blocker 交人決定，不自行 repair；NOT_RUN |
| 日常入口實際能力 | Owner 用附錄 C 授權且交接前景；日常 Agent 保存當次原件／帳本／下載／驗證證據 | 舊授權不代表本輪前景；控制／身分／帳本不明仍停；NOT_RUN |
| 本批成果確認 | Owner；可讀摘要與已驗證五張，人工檢視另記 OBSERVED | 人眼與工具結果各自記錄；不當作正式獨立接受；NOT_RUN |

保留專案所列的既有最小回歸，不另寫測試框架，也不把這些測試當提示詞或 GUI 可用性證明：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

### 功能層：實際五張照片才是本案成功證據

實作切片經適用人工檢查後，Owner 依**同一記事本附錄 C 正式 Prompt**啟動日常試用。開好列表、提交授權與前景即可；不交這份開發計畫、不開 Acceptance/E2E 角色、不要求逐張操作指令。當次較窄的五張範圍必須保留；來源或授權改變先列差異，不能用歷史「五張」當成現況，也不能默認擴大下載。

- 自行找回永久歷史、辨識列表及目標、完成當輪全列表卡片覆蓋與目標細盤；跳過完成／受保護項，不以新 scan 掩蓋舊交易。
- U1 必須有當次可重核的控制歸屬、作用、可見／可用、映射與媒體連續性。找不到可靠控制就保存已取得的新區辨並停止；這叫阻塞，不叫修復完成。
- 合格待下載項逐項遵守 intent／空白 staging 讀回、下載控制與 chooser 最終確認各最多一次、真實 outcome、穩定清單、非空、SHA-256、ImageIO 完整像素解碼及 completion 讀回。已完成項不為試用重下。
- 五張均有可歸屬完成證據、且本批無未解 attempt／pending naming，才支持「本批已完成」。LOCAL_MISSING 與本機實際可用性仍分開回報；外部副本未驗證不得聲稱存在。
- 文件／回歸通過、看到控制、工具簿記 PASS、真人 OBSERVED、真實備份及正式獨立接受分開記錄。影片、混合附件、跨 Session、其他模型與其他版本仍 NOT_RUN，除非另有實測。

若試用發現可重用且有實證的控制方法尚未在 Skill 中，日常 Agent 先交回證據，不在備份中修改產品。Owner 再決定是否在同一 GUI reference 作必要整合；未整合前不能宣稱入口已可重用。若仍需未知的程式／資料／工具能力改動，停止，不自動延伸本計畫。

## 人工檢查點、風險與回復

1. **下一步：Owner 另開主 Session 啟動計畫 Simplicity Review**，提供承載本草稿的精確 commit、plan 與 handoff。這是一次具體計畫審查，不要求 LINE 前景。
2. 計畫獲適用檢查與 Owner 決定後，Owner 啟動 Implementer 交付 S1。沒有另核准的程式修復；不先重跑同內容根因診斷。
3. 首個可驗證切片後，Owner 啟動實作 Simplicity Review。S1 若已是最終文件候選，不再造剩餘實作或重複審同版。
4. Owner 按日常附錄 C 確認實際能力及成果；這不是新增的 Harness Acceptance 備份入口。若有獨立計畫／程式安全審查需求由 Owner 依風險安排，不預填批准，不自動擴成 CRITICAL。

文件回復採保留歷史的後續 commit，不能 reset／改寫舊 commit；既有帳本與照片不因文件回復而回退。版本接受不能抹除資料完整性異常。對外部 writer／服務端改動、前景／popup／焦點、工具能力或 provider 不能保證原子快照、OS 隔離、exactly-once 或所有模型一致成功；只報當次證據。

同根因沿用既有嘗試；最多三次有證據嘗試，連續兩次沒有新資訊即停止相同方法，不用換 Session／API／路徑重置。exit 70、工具拒絕、身分歧義、不明派送、寫入衝突、scope／安全／資料／介面／驗證邊界變更，均保存已證明結果並交 Owner。依當次 CLI 契約處理 exit 2／4，不擴張為重播 intent 或 GUI 的許可。

## 草稿狀態

- PRIMARY_OUTCOME_STATUS: BLOCKED（依補充提報五張尚無完成證據；本輪未操作實機）
- IMPLEMENTATION_STATUS: NOT_RUN
- CORE_ACCEPTANCE_STATUS: BLOCKED（缺本批完成證據）
- REQUIRED_VERIFICATION_STATUS: PARTIAL（來源及規劃核對；實作回歸與真實備份 NOT_RUN）
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
- TASK_CLOSURE_STATUS: BLOCKED

本角色 `PLAN_DRAFT_COMPLETE` 只表示可交接草稿，不是修復完成。既有來源、未知與嘗試歷史見 [source-manifest.json](source-manifest.json)、[planner-report.md](planner-report.md)；本輪到交付即停止。
