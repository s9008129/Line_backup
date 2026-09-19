# Handoff — Rev24 波次結案 → 下一步交接（2026-09-19，新對話用）

> 讀者：下一個新對話的另一個模型（agent）。目標：不靠舊對話記憶，只讀本文件＋所列檔案，就能正確接手。
> 位置：本文件置於專案根目錄，僅為交接副本；權威證據一律以 repo 內原路徑為準。

## 0. TL;DR（30 秒版）

- 專案：LINE 相簿備份驗收（`T20260916-0102-01-line-backup-acceptance`），目標相簿「2024/05/13～05/17」57 張，目的地 57 檔完整、基線 `ab6747f2…` 不變。
- Rev24 波次已結案：route attempt-07 在 S5 止步（`STOPPED_AT_S5_NO_EFFECT`）——相簿卡點了 1 次但畫面無開啟反應，⋮ 依規未送、零副作用；v5 修正規則因此**未取得 live 測試**（離線證明仍成立）。Stage 05（`e2e/attempt-08`）獨立重算全 PASS。
- 最終六欄：`UNKNOWN | COMPLETE | BLOCKED | PASS | PASS | CORE_ACCEPTANCE_BLOCKED`；唯一 scoped blocker＝`CUA_ROUTE_DECISION`（owner 保留）。
- **下一步必須是 NEW revision（Rev25），不能在 Rev24 內再試**（`OOS-V24-5`）。且在 owner 明確選 A（結案 `ROUTE_NOT_NEEDED`）或 B（新一輪一次性觀察）之前，**新 agent 不得送任何 GUI 輸入**——先做唯讀診斷＋擬 Rev25，停下來問 owner。

## 1. 第一性原理梳理（為什麼整件事長這樣）

### 1.1 目標樹：三層邏輯不要混

1. **產品層**：57 張照片是否完整備份？→ 已答：是（基線 `ab6747f2…`，57 檔／17,924,900 B，`UNCHANGED`）。
2. **事實層（§16.4）**：使用者事實紀錄 v1.1 是否精確對應？→ 已答：`CONFIRMED`（`user_fact_v1_matches`：v1.1 True、v1 False；無正規化、無禎/楨合併）。
3. **路線層（CUA_ROUTE_DECISION）**：能否用機器證明「在真實 LINE UI 上找到並點開相簿層 ⋮」？→ **未答**：attempt-06 到 S6（`NO_ELLIPSIS_FOUND`）、attempt-07 到 S5（`NO_EFFECT`），兩次都 fail-closed 停止。這是唯一卡點，且是 owner 保留的處置問題，不是實作缺陷。

### 1.2 為何 GUI 層刻意「零容錯」

真機點擊不可逆：點開 ⋮ 會彈選單，誤觸任一項目（尤其 Save All）會在外部應用產生無法回收的副作用。所以 runbook 規定 at-most-once、零重試、零替代座標、fail-closed（任一非 `ELIGIBLE` 即停）。**「停」是安全設計，不是失敗。**

### 1.3 為何拆成「離線重播＋live 觀察」

- 離線重播（凍結幀＋凍結工具）：可重複、可稽核，用來證明工具有效（v5 在 `4cb8a6b4…` 幀 `ELIGIBLE [304,50]`、v4 同幀仍 `NO_ELLIPSIS_FOUND`——基線未被翻案）。
- Live 觀察（一次性 gate）：只證明「當下真實 UI」，每次最多 2 個輸入，用完即焚。兩者缺一不可：工具有效 ≠ 當下畫面可點。

### 1.4 證據鏈邏輯（新 agent 的心智模型）

`凍結工具 → 凍結授權(gate) → 凍結 runbook/ledger skeleton → 執行（記證）→ FINAL ledger → Stage05 獨立重算 → result.md`。Stage 05 永遠從**新鮮證據**重推，不信任 Stage 04 的自述。任何「改寫舊證據」的要求＝TASK_REGRESSION，直接拒絕。

## 2. 本次測試結果（Rev24 波次，精確到可驗證）

### 2.1 Route attempt-07（本波唯一 GUI，commit `b2c4664`）

- S1 綁定讀取（零輸入）：`/tmp/route7_frame_pre.jpg`（2,136,819 B，2294×1490，`28976287…`）。
- S3 卡片定位（凍結 v4）：`ELIGIBLE`，標題 `2024/05/13~05/17` bbox `[30,883,257,907]`，count `57 MATCH`，`click_point [42,895]`。→ `album-card-locate.json`（3,278 B，`94694c92…`，帶 v4 reader block）。
- S2 探針（唯讀、非關卡）：凍結 v3 雙尺度皆 `TARGET_COUNT_MISMATCH`（count 誤讀 5/27）→ `screen_scope=UNAVAILABLE`。→ `screen-probe.json`（5,036 B，`38130a6a…`）。
- S4 輸入#1（全波唯一 GUI）：`osascript System Events click at {21,448}`（`[42,895]px/2`），exit 0，命中 LINE 窗；`clickCount=1`、無修飾、無 bring-to-front。卡片 1/1＋導航 1/1（別名IBC）。
- S5 開啟驗證（凍結 v4）：**`NO_EFFECT`**（exit 3）：post 仍是相簿列表（同 bbox、同 count），`changed_fraction 0.047343 < 0.05`，變化區在右側終端區而非 LINE 卡；以新鮮 pre 重算亦 `NO_EFFECT`（0.014715）——排除 stale-pre 假象。→ `album-open-verify.json`（4,543 B，`aa0a2161…`）。
- S6–S10 未執行（無 live 相簿幀；⋮ 輸入 `UNSPENT 0/1`，正確被禁）。無 `route-result.json`／`manifest.json`（止步政策）。→ FINAL ledger（20,183 B，`7c8ea39a…`，`CLOSED_AFTER_INPUT_1`）；執行紀錄 `execution-rev24.md`（11,191 B，`8f8d2b3d…`）。

### 2.2 離線雙列（v5 有效、v4 未被翻案）

- 同一凍結幀 `route5r_frame_post.jpg`（`4cb8a6b4…`）：v5 `ELIGIBLE`（dots `[[304.5,44.0],[304.5,49.5],[304.5,55.0]]`，click `[304,50]`）＋ v4 `NO_ELLIPSIS_FOUND`（exit 3）。v5 自測 21 cases／0 failed（`e207f502…`）。

### 2.3 Stage 05 `e2e/attempt-08`（零 GUI，commit `6e18889`）

- §16.4 重推 `CONFIRMED`；route 重推 `STOPPED_AT_S5_NO_EFFECT`；S3/S5/v5/v4 四重播全再現；基線重跑 `IDENTICAL`；15/15 凍結錨相符。→ `e2e_report.md`（13,106 B，`f7bf7b20…`）。
- `result.md` 改寫為 Rev24 關閉（11,414 B，`0fe26fb6…`），六欄不變（見 §0）。

## 3. 目前遇到的問題（誠實、不猜）

1. **P0 — S5 `NO_EFFECT`（卡片點了但相簿沒開）。** 僅記錄為假說（未驗證、未重試）：px→pt 座標映射捨入、`click at` 語意、單擊 vs 預期手勢、視窗焦點/z-order。gate-5 已耗 card 1/1，**禁止任何重試或補點**。
2. **P1 — v5 無 live 測試。** 離線有效，但真實 UI 上的相簿層 ⋮ 仍未被機器證明或證偽。任何「v5 可用／不可用」的結論目前都是過度推論。
3. **P2 — 執行期偏差（已如實記載，非隱瞞）：** skeleton 假設 `cua_repl`＋AX，但本機實際無 CUA 執行器，改用 `screencapture -x`＋`osascript`＋System Events 視窗幾何；S3 先於 S2（皆唯讀、皆在輸入前，`decided_before_the_input` 仍成立）。FINAL ledger 已更正 `runtime/provider`。
4. **約束 — `OOS-V24-5`：** Rev24 內不得再開新 attempt；要再觀察必須 NEW revision＋新 gate＋新獨立複審。

## 4. 接下來預計測試的方向與邏輯（新 agent 照此走）

### 4.1 決策樹（owner 二選一，agent 不得代選）

- **A：結案（`ROUTE_NOT_NEEDED`）** — 接受 57 檔＋`CONFIRMED` 為本任務終點，路線維持「已如實記錄的未驗證」。工作量最小：只需 owner 明示，寫一次結案備忘（append-only），不碰任何凍結證據。
- **B：新一輪一次性觀察（Rev25）** — 先唯讀診斷 P0，再擬 Rev25（新 gate-6、新 route attempt-08、新 e2e attempt-09；注意 attempt 號與 e2e 號分屬兩系列，不可混稱）。gate-6 未凍結前零輸入；凍結後最多 2 輸入；任一非 `ELIGIBLE` 即停。

### 4.2 若選 B：建議的診斷順序（零 GUI 先行）

1. 重讀 attempt-07 三幀＋ledger，確認 NO_EFFECT 的變化區語意（已證：變化在終端區）。
2. 校準座標鏈：Retina 2x（2294×1490 px ↔ 1147×745 pt）、System Events `{21,448}` 與 title band（pts y 441.5–453.5）的包含關係、WIN1（`(0,27)pt 327×643`）z-order。
3. 查 LINE 該卡片的開啟手勢（單擊是否足夠？是否需雙擊？——**只能讀文件／讀碼，不能動手試**）。
4. 擬 Rev25：工具沿用 v5（若修座標規則才動工具；動工具＝重跑自測＋離線雙列）；gate-6 鏡射 gate-5 的 17-key schema，parent 綁 `7c8ea39a…`；runbook 明訂 S5 失敗即停、S6 綁 v5、禁 fallback。
5. 停。把 Rev25 草案＋診斷結論交給 owner，**等 owner 明確授權 gate-6 才可排 GUI**。

### 4.3 非 GUI 替代（任何分支都可做）

基線／§16.4／錨點重算皆可在零風險下重跑；`禎(U+798E)`／`楨(U+6968)` 永不合併；目的地 57 檔永不重下載、不刪改；正式 config／state／run-log 唯讀。

## 5. 精確起點（新 agent 的檢查清單）

- 先讀：本文件 → `GOAL-2026-09-19-rev25-next.md`（根目錄 goal 指令）→ `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（Rev24，`40eb0198…`）→ `result.md`（`0fe26fb6…`）→ `execution-rev24.md` → `e2e/attempt-08/e2e_report.md`。
- 唯讀基線：`git status` 須乾淨；重算關鍵 SHA（`ab6747f2…` 基線、`a8c10551…` v1.1、`7c8ea39a…` attempt-07 FINAL、`f7bf7b20…` attempt-08 報告、`40eb0198…` 計畫）；任一不符→停、記證、通知。
- 絕對不碰：v1–v5 工具、v3/v4/v5 自測、attempt-01..07、`e2e/attempt-02..08`、gates 1–5、各 ledger、已封存 handoff、`result.md` 歷史、目的地 57 檔、正式 config／state／run-log。python 一律 `-B`；對話零圖片（只報路徑＋SHA-256）。
- 指令規範：每次階段完成→繁中四段式 commit；不得自我豁免 gate；不確定就停下來問。

## 6. 附錄：權威指紋（節錄）

| 項目 | SHA-256（前綴） |
|---|---|
| plan.md Rev24 | `40eb0198…` |
| task handoff.md（Rev24） | `fee98581…` |
| result.md（Rev24 關閉） | `0fe26fb6…` |
| attempt-07 FINAL ledger | `7c8ea39a…`（parent `906c1433…`） |
| attempt-08 e2e_report | `f7bf7b20…` |
| gate-5 | `2817b122…`／runbook `a9669a99…` |
| v5 ellipsis | `6a015ea6…`／v5 自測 `e207f502…`（21/0） |
| baseline-pre | `ab6747f2…`（57 檔／17,924,900 B） |
| v1.1／v1／gate-answer | `a8c10551…`／`2cd7eccd…`／`03ffff57…` |

HEAD：`6e18889`（`git log --oneline -3`：`6e18889`／`b2c4664`／`8f61ff1`）。
