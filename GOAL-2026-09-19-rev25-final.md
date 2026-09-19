# Codex CLI /goal — Rev25 Final

> This is the execution goal paired with `PLAN-2026-09-19-rev25-final.md`.
> It supersedes the preliminary `GOAL-2026-09-19-rev25-next.md` for new execution.
> Historical files remain immutable.

```text
/goal

你現在接手的是 LINE 相簿自動備份專案的 Rev25 安全驗證波次。不要依賴舊對話記憶；先讀 repo 內文件與證據，依照檔案本身建立上下文。

【第一優先必讀】
1. PLAN-2026-09-19-rev25-final.md
2. HANDOFF-2026-09-19-rev25-next.md（只作歷史/意圖背景；若與新 PLAN 衝突，以新 PLAN 為準）
3. README.md
4. .agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md（Rev24 歷史契約，不得改寫）
5. evidence/20260916-route/attempt-07/run-ledger.json
6. evidence/20260916-route/attempt-07/gate-5-authorization.json
7. evidence/20260916-route/attempt-07/album-card-locate.json
8. evidence/20260916-route/attempt-07/screen-probe.json
9. evidence/20260916-route/attempt-07/album-open-verify.json
10. e2e/attempt-08/e2e_report.md（若實際路徑在 task/evidence subtree，先以 repo 搜尋找到唯一對應檔，再記錄真實路徑）

【任務總目標】
不要重下載現有 57 張照片。你的任務是：
A. 先證明剛修好的 transaction / authority / status 安全防線真的通過動態測試；
B. 完全零 GUI 地診斷 route attempt-07 為什麼「相簿卡點一次後 S5=NO_EFFECT」；
C. 如診斷有充分證據需要改 card click-point 規則，新增 append-only v6，不得修改 frozen v4/v5；
D. 完成兩次 fresh independent plan review；
E. 擬好 gate-6 並停下來等待 owner 的新一次性 GUI 授權；
F. 只有 owner 在本輪明確授權 gate-6 後，才執行 route attempt-08：
   1 次相簿卡點擊 -> 必須 ALBUM_OPEN_VERIFIED -> live v5 找 ⋮ -> 1 次 ⋮ 點擊 -> 只觀察選單；
G. Rev25 永遠不點 Save All，不碰 chooser，不下載，不寫 formal state/config/run-log；
H. route 關閉後用 e2e/attempt-09 做零 GUI 獨立重算。

【Phase -1：先解除 stale clone blocker，零 GUI；這一步明確授權】
Canonical plan 是 repo 根目錄：
PLAN-2026-09-19-rev25-final.md

不要要求 ~/Downloads/PLAN-20260919-rev25-final.md，也不要把 Downloads 裡的副本當權威。

先跑：
git status --porcelain=v1 --branch
git remote get-url origin
git rev-parse HEAD

要求：
- 工作樹/index 乾淨
- branch = master
- origin 是 s9008129/Line_backup

若不符合就停止；不得 stash/reset/rebase/cherry-pick/force/discard。

若符合，這個 goal 明確允許執行：
git fetch --prune origin master

fetch 後跑：
git cat-file -e 8fb622e4f2a25a2b1297894855303fdc671dafd3^{commit}
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 origin/master
git merge-base --is-ancestor HEAD origin/master

三者都必須 exit 0。

若工作樹仍乾淨且 local HEAD 是 origin/master 的 ancestor，這個 goal 明確允許且只允許一次：
git merge --ff-only origin/master

也可用 git pull --ff-only origin master 取代，但兩者不可都做。
禁止 reset/rebase/cherry-pick/force。若不能純 fast-forward，停止並回報 divergence。

fast-forward 後必須確認：
git status --porcelain=v1 --branch
git rev-parse HEAD
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 HEAD
test -f PLAN-2026-09-19-rev25-final.md
test -f GOAL-2026-09-19-rev25-final.md

只有以上全部通過，才進 Phase 0。fetch/ff-only 不構成任何 LINE GUI 授權。

【程式基線硬閘】
required repair baseline：
8fb622e4f2a25a2b1297894855303fdc671dafd3
它必須是同步後 HEAD 的 ancestor。

【Phase 0：必須先動態驗證修補，零 GUI】
同步完成後再跑：
git status --short
git rev-parse HEAD
git merge-base --is-ancestor 8fb622e4f2a25a2b1297894855303fdc671dafd3 HEAD

工作樹若不乾淨，不得自動丟棄使用者變更；停止並記錄。

接著依 PLAN 執行：
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/test_transaction_core.py

再用全新 append-only evidence root 執行：
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/run_acceptance_wave.py --attempt-root evidence/20260919-rev25-preflight/attempt-N

再用另一個全新 append-only root 執行：
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B tests/automation_verification/run_all.py --attempt-root evidence/20260919-rev25-auto-verification/attempt-N

N 必須選第一個不存在或空的新 attempt；禁止刪除舊 evidence 來重用號碼。

Phase 0 硬性 PASS：
- focused tests exit 0
- acceptance wave exit 0 / all_safe=true
- 01..25 無 failed checks
- verifier/status/authority/legacy summaries 全 match
- readback PASS
- automation wave all_orders_safe=true，兩種順序 readback 都 PASS
- Case 03 與 Case 23b 新增的 direct VERIFIED-finalize 負例必須證明：
  CONFLICT_UNRESOLVED_DISPATCH / exit 4 / state SHA 不變 / registry 不增 / owner 保留 / zero extra dispatch

任一不過：立刻停，分類與修復；修復後用新的 evidence root 重跑 Phase 0。不得豁免後直接碰 LINE。

【Phase 1：唯讀基線】
重新計算，不信任舊文字結論：
- destination = 57 files / 17,924,900 bytes
- baseline digest 與既有 accepted baseline 一致
- source identity v1.1 CONFIRMED；legacy v1 不具權威
- 禎 U+798E 與 楨 U+6968 精確分離
- attempt-07/gate-5/frozen v5 selftest 等歷史錨不變
- v5 selftest = 21/0
- frozen v5 replay = ELIGIBLE
- frozen v4 same-frame baseline = NO_ELLIPSIS_FOUND
- Stage05 attempt-08 仍可重算一致

任何歷史錨不符：停；不得改舊檔使它重新吻合。

【Phase 2：S5 NO_EFFECT 零輸入診斷】
建立 evidence/20260919-rev25-s5-diagnostic/attempt-N/。

必須做：
1. 重建 screen px -> Retina scale -> System Events/Cocoa pt -> LINE window-local 的完整座標鏈。
2. 重新驗證舊 click_point [42,895]px -> {21,448}pt 的數學與語意。
3. 判斷它是否只落在 title/text band、是否可能不是 card hitbox；若無法由證據證明，標 UNKNOWN。
4. 唯讀檢查當時/當前 focus、z-order、window geometry。
5. 唯讀研究實際 runtime「screencapture -x + osascript System Events click at」與原 CUA 假設的差異。
6. 對 S5 changed_fraction 做純離線 sensitivity analysis；絕對不能改寫 Rev24 的 NO_EFFECT，也不能為了 0.047343 < 0.05 而調低門檻。
7. 產出 s5-hypothesis-matrix.md；每個假說只能是 SUPPORTED / REJECTED / UNKNOWN，附證據。

禁止為了「有進度」挑一個未證實原因。

【Phase 3：工具與 plan review，仍零 GUI】
- frozen v4/v5 不得修改。
- 若診斷證明 card click-point 規則需要修正：新增 v6；最小修改；新增自測；凍結幀離線 replay；記 SHA。
- 若證據不足：不要硬做 v6。
- 對這份 Rev25 plan 的 exact SHA 做兩次 fresh independent review；兩者都必須 PLAN_APPROVED。
- review 必須明確檢查 Phase 0 已 PASS、S3 live point 一定從 current frame 導出、沒有歷史座標 fallback。
- 建立 gate-6 草案，top-level 17 keys 必須鏡射 gate-5 schema；綁 exact Rev25 plan SHA、兩份 review SHA、attempt-07 FINAL parent SHA、所有 route tool SHA、one-shot budgets。

【最重要的授權邊界】
到 gate-6 草案完成後，必須停止並向 owner 請求新的明確一次性 GUI 授權。
這份 /goal、這份 PLAN、以及「請你執行自動化測試」這類一般性語句，都不能自行解讀成 gate-6 的 GUI 授權。

若 owner 尚未明確授權：GUI_INPUT_COUNT 必須保持 0。

【只有 owner 明確授權 gate-6 後，才可 Phase 4】
新 route attempt = evidence/20260916-route/attempt-08/。

Budgets：
- album-card/navigation = 1
- ellipsis = 1
- click_count per input = 1
- retry = 0
- menu_item = 0
- Save All = 0
- chooser = 0
- keyboard = 0
- scrolling = 0
- app acquisition = 0
- AX write = 0

執行序：
S1 fresh pre-frame，零輸入。
S2 read-only LINE window/focus/geometry。
S3 精確辨識 2024/05/13～05/17 / 57；必須 ELIGIBLE；click point 只可由 immediate current frame 產生。
S4 exactly one album-card click。禁止重試/雙擊。
S5 fresh post-frame + semantic verifier；只有 ALBUM_OPEN_VERIFIED 才可往下。
若 S5 != ALBUM_OPEN_VERIFIED：立即停止，ellipsis UNSPENT 0/1，絕不再點。
S6 只用 frozen v5 ellipsis locator；current live frame 必須 ELIGIBLE；禁止 v4 fallback。
若 S6 非肯定：停止，不送第二個 input。
S7 exactly one album-level ⋮ click。
S8 只讀觀察 menu；可辨識 menu items / Save All 文字，但永遠不點任何 item。
S9 FINAL ledger；明確寫 SAVE_ALL_DISPATCH_ATTEMPTED=NO。

任何 live coordinate 都不得使用歷史 [304,50]、[305,50] 或任何舊 attempt 點位。

【Phase 5：e2e/attempt-09，零 GUI】
獨立 re-hash/replay，不信任 route ledger 自述。
必須驗證：
- Phase 0 regression evidence
- source identity
- destination baseline unchanged
- frozen anchors unchanged
- gate-6 budgets = actual inputs
- S5 fresh-frame verdict
- 若有 S6/S7，live v5/menu 結果可重算
- Save All / chooser / download / formal state write 全部為 0

【成功定義必須分三層】
1. 現有相簿資料：57 張是否仍完整。
2. 可重用 route：只有
   TARGET_CARD_ELIGIBLE -> ONE_CARD_CLICK -> ALBUM_OPEN_VERIFIED -> LIVE_V5_ELLIPSIS_ELIGIBLE -> ONE_ELLIPSIS_CLICK -> MENU_SURFACE_AFFIRMATIVELY_OBSERVED
   全鏈被獨立驗證，才算 Rev25 route success。
3. 完整自動備份產品：Rev25 結束仍不得宣稱完成，因為本輪禁止 Save All。真正 Save All/chooser/download/dedupe/crash/restart 必須另開新 revision。

【永遠禁止】
- 改寫任何 frozen evidence / gates 1–5 / attempts 01–07 / e2e 02–08 / v1–v5
- 重新下載或修改現有 57 檔
- 把 禎 與 楨 合併
- 用舊座標當 live 座標
- S6 fallback
- retry
- Save All
- chooser
- keyboard
- scrolling
- AX write
- 自我核准 gate
- 為了讓測試通過而降低 frozen threshold
- 在對話貼 screenshots；只回報 path/SHA/size/verdict

【工作方式】
你是自主 agent：在每個已授權的 phase 內自行完成讀取、測試、修復、證據、commit，不要每一步都問 owner。
只有下列情況必須停：
1. Phase 0 任一硬 gate 失敗且無法在不破壞契約下修復；
2. 歷史/基線 evidence 不一致；
3. 需要 GUI gate-6 授權；
4. live frame 非肯定；
5. 任何可能造成 Save All/chooser/download 的風險。

每個 phase 完成後做一次繁中四段式 commit：意圖 / 做了什麼 / 證據 / 下一步。
最後回報必須白話且分開說：
- 本相簿 57 檔狀態
- reusable route 狀態
- full automatic backup product 狀態
- 若未完成，唯一 scoped blocker 是什麼
- 所有新 evidence 路徑與 SHA-256
```
