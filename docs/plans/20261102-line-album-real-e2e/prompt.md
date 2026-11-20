# LINE 相簿真實下載：獨立 E2E 測試者 Prompt

> 使用方式：Owner 請先登入 LINE、人工開啟指定的單一相簿列表，確認該列表就是本次要測試的對象，然後在**新的獨立主 Session** 貼上本文件全文。貼上本文件即表示 Owner 授權本次相簿備份、當次前景交接，以及 Skill 已支援的下載與驗證操作；不是只討論或審查文件。

BACKUP_ROOT=
EXCLUSIONS=[]

## 一、角色、授權與獨立性

你是本次的**獨立 E2E 測試者**，不是本次相簿流程的實作者、修正者或實作者 helper。你的任務是用真實 LINE 畫面與真實下載，驗證 Owner 指定的這一份相簿列表能否依現行專案 Skill 完成備份、驗證與持久紀錄。

本次授權範圍：

- 只處理 Owner 當次開好並交接前景的**單一連續 LINE 相簿列表**。
- 依 `.agents/skills/line-album-agent-cua/SKILL.md` 與 references，實際使用原生 Mac Computer Use 觀察、導覽、完整盤點、逐本下載、驗證及保存進度。
- 授權使用相簿詳細頁的 `⋯ → 儲存全部`，以及它開啟的原生資料夾 chooser。
- `BACKUP_ROOT` 留空時使用專案根目錄下的 `backup/`；若 Owner 當次指定其他工具支援的專案內絕對路徑，以指定路徑為準。
- `EXCLUSIONS=[]` 表示本次沒有新增排除；它不解除既有排除、完成、UNKNOWN 或受保護歷史。
- 本次若沒有另行限縮，預設處理此列表內所有合格且尚未完成的相簿；不可只處理第一本後就把整份列表宣稱完成。
- 允許依 Skill 在同一列表內重新觀察、補接缺頁、重新定位、等待下載、驗證檔案及接續中斷；不需要 Owner 逐本下令或在盤點後另說「開始下載」。

本次**不授權**：

- 不操作這個列表以外的相簿、其他群組、記事本或其他產品流程。
- 不發訊息、不刪除、不分享、不覆寫既有照片，不修改既有完成、排除、UNKNOWN、pending naming 或受保護歷史事實。
- 不修改產品程式、tests、Skill、references、手冊、AGENTS、plan、handoff 或既有報告；發現問題只記錄 finding，不自行修復。
- 不自行 commit、push、merge、建立 PR、force-push、改寫 Git 歷史或啟動下一個正式角色。
- 不使用 `codex exec`、SDK、API、背景 LLM、shell／AppleScript 或其他控制通道繞過原生 Computer Use 的角色邊界。
- 不把先前任何 Session 的座標、畫面或成功結果當成本次可重用證據。
- 不把「記事本離線相容驗收」或舊的四本／141 張相簿 E2E 結果，升格成這次相簿候選的 PASS。`docs/plans/20261102-notes-fieldtest-review/a0-acceptance.md` 只是記事本離線背景，不是本任務證據；也不要載入 notes CLI、notes Skill、notes 帳本或影片流程。

你必須先確認自己與本次相簿候選沒有實質貢獻關係。如果你曾參與本次候選的實作、修正或主要審查判斷，立即停止並回報 `BLOCKED`，不可簽發獨立 Acceptance。Helper 只能做互不重疊的唯讀或測試協助，不能替你形成正式結論。

本次模型與 reasoning effort 由 Owner 在啟動新 Session 時選定；不要自行改 model、提高 effort，或把設定值宣稱成 provider 的後端身分或實際用量。

## 二、精確起點、來源與禁止混淆

交付本 Prompt 時的預期起點：

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`
- Branch：`feature/line-notes-media`
- HEAD：`76d56d21a7533af818012dcd6fc8b865b6780f3a`
- 遠端同名 branch 在交付 Prompt 時應指向同一個 HEAD
- 本 Prompt 檔案本身是 handoff 文件，不是產品變更；若它以未追蹤檔案存在，允許它出現在 `git status`，但不能有其他未授權的產品變更

若 Owner 之後只為了保存本 Prompt 或先前驗收報告而新增文件 commit，先記錄新的精確 HEAD，並核對自 `76d56d2` 起沒有產品程式、tests、Skill、references、手冊或 AGENTS 的變更；若無法證明，或 HEAD、branch、遠端不一致，停止並回報 `BLOCKED`。不得 reset、clean、切 branch、重寫歷史或自行改驗收標準。

開始前至少讀完：

1. `/Users/hsiaojohnny/dev/Line_backup/AGENTS.md`
2. `/Users/hsiaojohnny/.codex/prompts/v4.9.0/05_acceptance_prompt.md`
3. `/Users/hsiaojohnny/.codex/policies/v4.9.0/workflow-routing.md`
4. `/Users/hsiaojohnny/.codex/policies/v4.9.0/subagent-model-policy.md`
5. `.agents/skills/line-album-agent-cua/SKILL.md`
6. `.agents/skills/line-album-agent-cua/references/daily-backup.md`
7. `.agents/skills/line-album-agent-cua/references/backup-and-resume.md`
8. `.agents/skills/line-album-agent-cua/references/inventory.md`
9. `.agents/skills/line-album-agent-cua/references/verified-experience.md`
10. `.agents/skills/line-album-agent-cua/references/visual-grounding.md`
11. `docs/LINE相簿備份_使用手冊.md`
12. `docs/LINE相簿SaveAll決策根因與E2E修正紀錄.md`（只作歷史與方法背景，不是本次候選證據）
13. `docs/line-album-naming/plan.md` 與 `docs/line-album-naming/handoff.md`（只讀產品邊界與已知限制，不用來取代本次實機結果）
14. `docs/plans/20261102-notes-fieldtest-review/a0-acceptance.md`（只作背景；它是記事本離線驗收，與本相簿任務無關）

也要讀取 `src/line_backup_batch/daily.py`、`src/line_backup_batch/image_decode.swift`、`tests/test_daily_records.py` 及本次需要的既有程式／證據。文件寫的內容、單元測試、工具簿記與真實 GUI 操作是不同證據層，不可互相代替。

## 三、Owner 的交接與本次測試對象

Owner 提交本 Prompt 時，必須：

- 已在具有原生 Mac Computer Use 的環境登入 LINE。
- 已人工開啟一份指定的單一連續相簿列表，且該列表在前景。
- 同意你操作該列表的相簿詳細頁、`⋯`、`儲存全部`、原生資料夾 chooser，以及必要的 LINE／popup 唯讀觀察。
- 不在你操作期間接管滑鼠、鍵盤、前景或下載視窗；若需要暫停，先明確中斷本次前景交接。

你要先以當次真實畫面／AX 核對：

- 這是相簿列表，不是聊天室、記事本、單張照片檢視器或相簿詳細頁。
- 畫面對應 Owner 剛剛交接的同一個列表，且沒有出現兩個以上列表或群組的歧義。
- LINE 已登入、可觀察、可操作；原生 Computer Use 與必要權限可用。
- 預設照片根目錄可寫入且有足夠空間；不要把照片寫入永久帳本區。
- 至少有一本需要本次處理的合格相簿。若整份列表已完成、已排除或全部受保護，本次不能產生「真實下載 PASS」；應回報沒有可測下載對象，記 `NOT_RUN` 或 `BLOCKED`，不得偽造一次下載。

不要用中文群組名稱、OCR 文字、日期／張數或資料夾名稱單獨認定列表或相簿身分。名稱只供顯示與路徑使用；身分依當次畫面、清單順序、卡片內容、詳細頁與工具提供的 identity 資料共同核對。

## 四、開始前的 Git、環境與能力檢查

在 repo root 保存下列命令的實際 argv、stdout、stderr、exit code、執行時間與輸出 SHA-256：

```sh
cd /Users/hsiaojohnny/dev/Line_backup
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --untracked-files=all
git diff --exit-code
git diff --name-only 76d56d21a7533af818012dcd6fc8b865b6780f3a..HEAD
git ls-files --others --exclude-standard
git ls-remote origin refs/heads/feature/line-notes-media
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily --help
```

另外記錄：

- macOS 版本、CPU 架構、Python 版本、Git 版本、Swift／編譯器版本（若本次需要建置 decoder）、原生 Computer Use 的實際可用能力與限制。
- `daily groups`、`.local/line-backup/active-task.json` 與相關 `memory` 的讀取結果；例如保存下列輸出（`RECORDS_ROOT` 由實際帳本取得，不可自行猜測）：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily groups
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.daily memory \
  --records-root "$RECORDS_ROOT"
```

  `active-task.json` 只協助定位，不是唯一歷史入口。
- 全部永久帳本、相符的 `records_root`、既有完成／排除／UNKNOWN／pending naming／受保護歷史及本機照片可用性。
- 本次使用的絕對照片根目錄、任何新空白目的地、私有證據目錄與 decoder 路徑。

起始 `git status` 只允許三種非產品內容：本 Prompt handoff 檔、本任務私有證據，以及測試完成後才建立的 `acceptance.md`。除此之外的任何 untracked、tracked diff、產品程式或 Skill 變更都要先停下，不可把它們當成測試前置或測試產物。

若 `git ls-remote` 因網路暫時不可用而失敗，如實保存錯誤，不要捏造遠端身分；若無法可靠確認精確候選，應把 `INDEPENDENT_ACCEPTANCE_STATUS` 降為 `BLOCKED` 或 `NOT_RUN`，不要用舊結果補上。

所有私有輸出放在：

`/Users/hsiaojohnny/dev/Line_backup/.local/line-backup/tasks/20261102-line-album-real-e2e/`

不得把真實照片、群組／人名、原始檔名、未遮蔽畫面、授權檔案、憑證或其他敏感證據加入 Git。公開報告只寫去識別化的相簿別名、摘要與證據位置／hash。

## 五、實際執行流程

以下順序以現行相簿 Skill 與 references 為準；若文件與當次工具狀態衝突，先保存證據並停止，不要自行改產品規則。

### 1. 找回舊任務與唯一帳本

1. 先執行 `daily groups` 查全部永久帳本，不只看最近一次 active-task。
2. 讀取相符列表的 `memory`，核對既有完成、排除、UNKNOWN、pending naming、受保護歷史及本機照片狀態。
3. 若只有一個帳本與當次列表可唯一對應，沿用它的 `records_root`，開新 scan 並重新盤點；不要重用上一個 Session 的 cursor。
4. 若是新列表，依 Skill 的新列表流程建立帳本與必要證據；不可只因資料夾空白或名稱相似就建立空帳，也不可把日期／張數相同當成同一列表。
5. 若有多個候選帳本、歷史身分衝突、缺可靠對應或工具拒絕，停止建立／綁定並回報具體歧義，不得猜配。

### 2. 完整盤點這一份列表

1. 從列表頂端開始；用小幅、可重疊的原生 Computer Use 捲動逐頁觀察。
2. 每張卡片記錄本次流水號、日期範圍、預期張數、封面／詳細頁／鄰接卡片等可區分的視覺依據，以及必要時取得的相簿顯示名。
3. 下一頁必須和上一頁有共同卡片，且順序、首尾重疊一致；不可用「看起來差不多」拼接，也不可用捲動次數推算總數。
4. 到列表末端後再做一次小幅向下觀察；只有同一末卡、同列表、卡片順序及可靠位置／視覺位移都不變，才可支持到底。
5. 將每本唯一歸入完成、排除、待下載、先前未完成、UNKNOWN、受保護歷史之一；六類總數必須回到盤點總數。
6. 在盤點完成並保存覆蓋證據前，不派送任何 `儲存全部`；盤點完成後直接進本次已授權的逐本下載，不要等 Owner 另一道命令。

任何缺頁、未解卡片、列表重排或身分歧義，都要在該階段保存狀態；不能把盤點未完成說成完整覆蓋。

### 3. 逐本處理：一次只處理一本相簿

對每個待處理的合格相簿，依下列固定順序執行：

```text
capture-group-name（同列表一次）
→ capture-album-name（每本）
→ detail（最新相簿詳細頁）
→ intent（新空白目的地、禁止重送紀錄）
→ Save All（每 attempt 最多一次）
→ outcome（第一個已知結果）
→ verify（檔數、穩定性、非空、SHA-256、ImageIO 完整解碼）
→ completion（保存並讀回）
```

具體要求：

1. **身分**：先在目前列表重新觀察目標卡片，確認日期、張數、封面／鄰接脈絡與詳細頁內容一致。已在盤點中確認過的相簿仍要在進入下載前核對目前詳細頁與目標相簿一致。
2. **名稱**：同列表只捕捉一次 group 顯示名；每本捕捉 album 顯示名。名稱只用於顯示與路徑，不可用來搜尋、選擇、核准、dedupe、跨列表合併或單獨認領歷史。完全讀不到時才問 Owner，不要用空名稱或舊 `albums/<UUID>` 猜新備份。
3. **目的地**：為本次 attempt 準備新的空白目的地。預設是 `BACKUP_ROOT/<相簿實際目錄名>/`；同名不同實體由工具加後綴，不可覆寫。不得使用舊 attempt 目錄、已存在檔案目錄或 symlink 目的地。
4. **派送前持久化**：用 `daily detail`、`daily intent` 或 Skill 指定的直接參數保存並讀回 target、destination、預期張數、授權來源與「可能已派送、禁止自動重送」紀錄。任何寫入失敗、讀回不一致、目的地碰撞或工具拒絕，都不可以點 Save All。
5. **開選單與觀察**：在已核對的相簿詳細頁開啟 `⋯` 一次。若 app-bound screenshot／AX 看不到獨立的原生 popup，依 `visual-grounding.md` 使用本次已授權且平台支援的唯讀桌面／區域截圖補看。保存完整五項選單、唯一 `儲存全部`、危險鄰項及可證明的座標映射；不得沿用舊座標、猜 Retina 倍率或直接把裁圖座標當成點擊座標。
6. **一次派送**：只有在最新畫面能唯一辨識 `儲存全部`、映射安全且前次確定沒有派送時，才點擊一次。`選擇項目`、逐張下載、單張檢視器或其他下載入口都不是 fallback。點擊後立刻觀察 chooser、進度、錯誤或結果；若沒有 chooser／進度／明確錯誤，先當結果未知，不得第二次點擊、重開選單或改走替代路徑。
7. **chooser**：看到資料夾選擇視窗後，使用「前往資料夾」輸入完整專案內絕對路徑，讀回欄位與末層資料夾，確認是本 attempt 的新空白目的地才確認一次。欄位不精確、路徑逸出、symlink、舊目的地或潛在覆寫風險時停止。
8. **等待下載**：讓 LINE 原生下載流程自行完成；不要因為看到 `0/N`、短暫不變或進度落後就取消、重開、重送或開新 attempt。若視窗仍在但狀態未知，保留原檔與現場，先唯讀查證。
9. **outcome**：下載有第一個可證據化的已知結果時立即保存 `outcome`；只有確認下載結束且檔案可用，才可進 `verify`。明確 `UNKNOWN` 不可由普通 outcome 改成其他結果，也不得自動重送。
10. **檔案驗證**：下載穩定後核對實際檔數、非空檔、至少三次穩定清單、逐檔 SHA-256 與 ImageIO 完整像素解碼；記錄 decoder 路徑、來源與 SHA-256。解碼成功只證明本機 bytes 能完整解碼，不證明與 LINE 服務端原始位元相同。
11. **完成紀錄**：全部驗證通過才執行 `daily verify`，保存 completion 並讀回。完成後再處理下一本；不可等整批下載完才一次補紀錄。
12. **下一本**：只在有可靠返回控制與已確認原列表入口時返回清單；以新畫面重新定位下一本、重新建立座標映射，不重用上一本位置。無可靠返回依據時保留原視窗，停止相關輸入並回報入口缺口。

若前次紀錄顯示已完成且本機目錄完整，跳過不重下；整本完成目錄已缺席時保留完成並回報本機不可用，不推定外部副本完整；目錄仍存在但有缺檔、額外檔、hash／身分漂移或 symlink，保護原件並停止依賴該本的新派送。

若前次是已確認停止且未完成的合法相簿級恢復，依原任務授權在原目錄之外建立新的空白恢復目的地，保留舊檔與舊 attempt；不得對 UNKNOWN 使用恢復解鎖，也不得把「目錄是空的」當成新下載授權。

## 六、必須停止的情況

遇到任何一項，停止依賴該前提的新 GUI 輸入，保存目前畫面、目的地、工具輸出、最後動作與是否可能已派送，然後回報：

- 前景交接中斷、Owner 接管、LINE 未登入、列表不是相簿列表、畫面落在單張檢視器／其他列表，或無法確認同一列表連續性。
- 工具不支援本次所需操作、Computer Use 失敗、截圖／AX 權限不足、無法建立可靠座標映射，或 popup 不唯一／可能點到刪除或分享。
- 已開選單但無法確認是否已派送；已點 Save All 但 chooser／進度／錯誤結果未知；下載視窗仍在變動。
- 目的地已存在、不是空白、路徑逸出、symlink、候選檔名碰撞、磁碟空間／寫入錯誤，或可能覆寫既有照片。
- 檔案數量不足、清單不穩定、空檔、SHA-256 不符、ImageIO 解碼失敗、額外檔案、metadata／身分漂移或 decoder 來源無法核對。
- 帳本、memory、completion、active 紀錄彼此衝突；有 UNKNOWN、pending naming、未解 attempt，或工具回傳需要人工 review。
- 需要修改產品程式、變更資料語意、降低 gate、改驗收標準或跨角色修補。
- 測試期間 HEAD、branch、產品檔案或 Skill 檔案改變；受影響證據立即失效，不可混用版本。
- 任何超出本次單一列表、真實相簿、照片備份授權的操作。

不要在真實照片上刻意製造 UNKNOWN、危險選單歧義、刪除／分享風險或不明派送；負向分支若無法用既有隔離資料安全證明，記 `NOT_RUN`。

## 七、證據、報告與判定

### 原始證據

私有任務區至少保存：

- 起始與結束的 cwd、repo、branch、HEAD、remote HEAD、`git status`、tracked diff、候選差異與 prompt／report 檔案狀態。
- 環境版本、實際 argv、stdout、stderr、exit code、時間、輸出 SHA-256；不要把 stdout／stderr 只看過就丟棄。
- 每個相簿的列表身分、visual key、詳細頁證據、名稱來源、destination、intent／outcome／verify／completion 讀回結果。
- 選單與 popup 的原始截圖／AX、當次映射量測、`menu_open_inputs` 與 `save_all_dispatches` 分開的計數。
- chooser 路徑讀回、下載進度／結果、檔案清單、逐檔 SHA-256、ImageIO 結果與 decoder hash。
- 每次停止、恢復、skip、NOT_RUN 或 blocked 的原因及最後已知狀態。
- 測試前後的 Git 狀態；私有證據不得 stage。

### 報告

完成後在下列路徑新增唯一公開報告：

`docs/plans/20261102-line-album-real-e2e/acceptance.md`

報告使用繁體中文，至少包含：

1. 角色、授權、來源、獨立性與 helper 關係。
2. 起始／結束 HEAD、branch、遠端 HEAD、工作樹與候選穩定性；明確標示本 Prompt、`acceptance.md` 與私有證據是 handoff／report-only addition，不是產品變更。
3. Owner 交接的列表身分、測試範圍、總本數、可下載本數、已完成／排除／UNKNOWN／待處理本數。
4. 需求與證據矩陣：入口核對、完整盤點、逐本身分、名稱、detail、intent、popup/Save All、chooser、outcome、檔案驗證、completion、返回與下一本、最終 summary。
5. 實際命令、環境、cwd、argv、exit code、原始輸出位置與 hash。
6. 事實、推論、未知、`NOT_RUN`；GUI 觀察、工具回傳、檔案驗證、completion 必須分層。
7. findings；每項寫出 requirement、candidate path／behavior、evidence、impact、是否需要 bounded fix、plan change 或只是外部 gate。
8. 六項狀態分開列出：

```text
PRIMARY_OUTCOME_STATUS:
IMPLEMENTATION_STATUS:
CORE_ACCEPTANCE_STATUS:
REQUIRED_VERIFICATION_STATUS:
INDEPENDENT_ACCEPTANCE_STATUS:
TASK_CLOSURE_STATUS:
```

判定只能用：

- `PASS`：所有本次適用的真實相簿 E2E 條件與 gate 都由同一精確候選、當次真實畫面與檔案證據支持，且沒有未解 finding。
- `FIX_REQUIRED`：有可在原計畫內修正的實作缺陷；只在報告記錄，不自行修改。
- `REPLAN_REQUIRED`：必須改需求、計畫、資料語意或 gate，交 Owner 決定。
- `BLOCKED`：必要證據、授權、候選身分或能力不足，無法可靠判定；未執行項目一律記 `NOT_RUN`。

`PASS` 只代表本次真實相簿下載與適用的 E2E gate 通過，不代表記事本流程、影片流程、跨 Session 恢復、名稱校正、GUI 任意環境、外部副本、服務端原始位元、可合併 master 或可結案。要寫成相簿 E2E PASS，必須同時符合：本次授權列表內所有合格相簿都已依規則完成、排除或有可證明且不需本次處理的既有狀態；至少有一本是在本次候選上實際完成下載、檔案驗證與 completion 讀回；所有未完成、UNKNOWN、受保護歷史或工具限制都已如實列出。只完成其中一本，不能替整份列表宣稱 PASS。

完成報告後停止。不要 commit、push、merge、修正 finding、降低 gate、重測或啟動下一個正式角色；把精確候選、證據位置、未解事項與需要 Owner 決定的人工 gate 交回。
