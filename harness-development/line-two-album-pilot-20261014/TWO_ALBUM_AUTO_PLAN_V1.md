# TWO_ALBUM_AUTO/1 — 最小實機計畫

Status: `PROPOSED_PENDING_EXTERNAL_PLAN_REVIEW`

## 固定身份與邊界

- Base HEAD：`516932dfcee94b662082b909b7980fc2483ab9c0`
- Plan 只新增本文件；產品程式、Grant、Ledger、LINE GUI 均不得由本輪修改。
- 不採用 PR #14 的 HUMAN P0、A56-only 或 dirty worktree。
- Plan SHA-256 以本文件提交後的 exact bytes 計算；交付後不得再改本文件而不重新送審。
- `GOAL_CRITICALITY=CRITICAL`；`EVIDENCE_ROLE=PLANNER_PROPOSAL_ONLY`；`CLOSURE_GATE=EXTERNAL_PLAN_REVIEW + EXACT_CODE_REVIEW + INDEPENDENT_E2E`。

## 真正目標

在同一個乾淨、受控的正式流程中，完成：

`A（合格相簿）→ 儲存全部 → 下載 → 逐檔完整驗證 → VERIFIED/readback/release → 回到列表 → 真實 bounded scroll → 找到不同的合格 B → B 的獨立儲存全部/下載/驗證`

不是單本 A56，不是重新開發另一套 Orchestration，也不是人工點最後一下後把結果冒充全自動。

## 已存在的能力（重用，不重寫）

- `runTwoAlbumPilot()` / `runAlbumWorkflow()` 已串接 A → C1 → bounded scroll → 不同 B：`harness-development/line-two-album-pilot-20261014/two_album_entry.mjs:257-302`。
- 單本交易已包含 admit、menu calibration、fresh original intent、atomic dispatch、chooser、finalize、VERIFIED、stop、release：同檔 `:185-254`。
- production runtime 仍要求 `max_albums_per_run=1`，兩本必須是兩個 sequential cap-1 lifecycles：`harness-development/line-two-album-pilot-20261014/mac_runtime.mjs:188-190`。
- `runPilot()` 是既有 AUTO entry；read-only preflight 不取得 GUI，也不初始化 ledger：同檔 `:455-461`、`:493`。
- A 的 VERIFIED/lease/C1/scroll/distinct-B linkage 已由 service 驗證：`src/line_backup_batch/service.py:341-376`；歷史 eligibility 見 `:380-384`。
- 固定 quota 不得改動：`(album_quota, lifecycle_album_limit, save_all_dispatch_limit, chooser_confirmation_limit, reversible_gui_inputs) = (2,1,2,2,23)`：`src/line_backup_batch/cli.py:416-418`。

## 兩個阻塞必須分開

### 已觀察的正式第一拒絕

`FIRST_FORMAL_REFUSAL=PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`。

2026-10-18 的唯讀 formal-route preflight 在 GUI 輸入、menu calibration、Save All 前即被 authorizer 拒絕；候選 source `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d` 與已安裝 closure `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54` 不一致。這是缺 exact external `APPROVE_IMPLEMENTATION` 與 source/runtime/entry/operations/fingerprint 綁定，**不是**點擊幾何問題，也不代表後面的 click gate 已通過。證據：Owner-held `formal-route-preflight-20261018.json`（SHA-256 `65cd1d51c4308c6090f2143bd3fe3d228c71d76f61b43e519d840268eb10af56`）；guard 位置 `src/line_backup_batch/cli.py:313-343`、`:353-388`。

### 尚未解除的技術阻塞

`2PX_PROOF_STATUS=AUTO_CLICK_PROOF_UNSUPPORTED`。

目前正式 AUTO adapter 用 hosted `app.click(...)` 派送點擊（`scripts/line_backup_cua_adapter.mjs:609-630`），但受支援的 `App.click(number|Vec2)` 只回 `Promise<void>`，沒有可稽核的實際 event point、事件 ID、recipient window/PID 或 delivery receipt。SCK/OCR 可以辨識畫面與唯一「儲存全部」列，但不能單獨證明真正被下游接收的輸入點在目標內。歷史座標、OCR 中心、shadow click、EventTap 收據與一次可逆成功都不是 2px 證明。現有 evidence 已量測到這個能力缺口：Owner-held `E2E測試報告.md`（SHA-256 `0b0a375cdbe0f8a721dc10c0a67228539f385d60098ca0af01dbd93a9a5c7a87`），其中 `REAL_SAVE_ALL_DISPATCH_COUNT=0`，且明列 `AUTO_CLICK_2PX_PROOF=AUTOMATIC_CLICK_PROOF_UNSUPPORTED`。

`AUTO_CLICK_EVIDENCE_ROUTE=NONE_CURRENTLY_ADMISSIBLE`。

`rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift` 有未被 AUTO 接上的 `ScreenPoint`、permit 與 topmost-surface 檢查；但 `rev28/Sources/rev28ctl/main.swift:124-130` 的 legacy `live-execute` 是 disabled，且它目前不是 `runTwoAlbumPilot` 的輸入路徑。不能把存在但未接線的原生元件說成現成可執行 AUTO route；把它接成 production click authority 是架構／證據契約變更，必須另案 Plan Review。

## 2px 的適用條件（只有未來經審查的 route 才可嘗試）

現有門檻不得降低：`uncertaintyPx >= 2`、`safeMarginPx >= uncertaintyPx + 4`、安全交集至少 `16×16`（`scripts/line_backup_cua_adapter.mjs:291-294`）。任何新 route 必須同時滿足：

1. 用同一張 fresh frame 的 window frame、capture bbox、scale 做 typed 座標轉換，不重用歷史點位；
2. 目標「儲存全部」列有唯一 identity、日期／張數與實際 menu ownership；
3. 實際送出的 event object 保存同一個整數點，且能在派送前後核對 topmost target window/PID；不能只保存「我打算點的點」；
4. 正例與反例都能重播：位移、錯 ROI、錯視窗、遮擋、過期 frame、錯 row 均拒絕；
5. 所有誤差項有可稽核上界後，才可宣稱 `|dispatched point - target point| <= 2px`。

在上述證據成立前，不得用數值猜測、不得以 OCR 中心或一次成功推導未來安全。

### 必要正反案例

- 正例：fresh A detail 上有唯一、可辨識的「儲存全部」列；frame 幾何、window/PID、menu ownership 一致；安全交集至少 `16×16`；實際 event point 的誤差上界可證明 `<=2px`；一次點擊後出現該次交易的 chooser。
- 反例：歷史座標重放、OCR 中心、shadow click、EventTap-only 收據、錯 app/window/PID、遮擋或過期 frame、重複 row、錯誤日期／張數、安全交集不足、第二次 dispatch、UNKNOWN 後重送、非空目的地、A/B 相同或沒有 eligible B；以上任一即 fail closed。

## 驗收條件

- **AC0｜來源與身分**：clean source closure、installed runtime、native producer、ImageIO decoder、entry、grant、owner、group/window/PID 全部對帳；read-only preflight 不消耗 lifecycle 或 GUI quota。
- **AC1｜候選資格**：A、B 各自是不同且在當下畫面核對的 eligible 相簿；歷史 239 張 VERIFIED 與人工備份 65 張相簿不得重複下載；目的地必須是新的空目的地。
- **AC2｜單次交易**：每本各有一個 durable intent、一次 Save All dispatch、一次 chooser confirmation；不得 replay。任何 UNKNOWN 立即 latch，不重送。
- **AC3｜A 完成**：A 的檔案清單完整且穩定，逐檔 SHA-256 與完整 ImageIO 解碼通過，狀態 `VERIFIED`、readback 與 release 均成立。
- **AC4｜C1 導覽**：回列表後至少一次真實、可觀察、bounded 的 0.25 viewport scroll；保留前後畫面、AX/OCR、位移與新候選證據。
- **AC5｜B 獨立完成**：B 必須與 A fingerprint 不同、通過當下 eligibility，並以新的 cap-1 lifecycle 完成與 A 相同的完整交易。
- **AC6｜保護狀態**：除合法的 A/B 交易外，原 ledger、quota、239 VERIFIED、65 排除、目的地與歷史資料不得變動。
- **AC7｜獨立 E2E**：由 Owner 另行啟動的獨立 DeepSeek 1017 Codex CLI Session 操作正式 GUI；Sol/Luna 不得代操作或代寫 PASS。沒有 eligible B 時，忠實回報 `NO_ELIGIBLE_TARGET`，不宣稱兩本完成。

## 執行順序與停止點

1. **外部 Plan Review**：Owner 將本 Plan、base HEAD、Plan SHA 與證據索引交給外部 ChatGPT。未 `APPROVE_PLAN`，不進 Implementation。
2. **offline exact-source 對帳**：確認 clean worktree、source closure、entry、producer、decoder、runtime、grant 與既有 tests；任何 hash drift 即停止。
3. **read-only formal preflight**：不點擊、不 begin 新 lifecycle；先解除 `PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`，再檢查 fresh owner foreground、空目的地、歷史／duplicate 與 click-proof gate。
4. **A 正式交易**：只有 fresh foreground、有效 grant 與已審查 exact source 才可執行；每本 cap 1，Save All 全局最多 2 次。
5. **C1 與 B**：A 完成 VERIFIED/readback/release 後，才回列表；真實 scroll 至少一次並找到不同 eligible B，再取得 B 的獨立授權，重跑完整交易。
6. **獨立 E2E 與收尾**：逐檔原圖驗證、狀態讀回、release、報告與受保護資料核對；任何 FAIL/BLOCKED 保留原證據，不以成功報告覆寫。

## 立即停止條件

- exact external review、source/runtime/grant 任一缺失或 hash drift；
- 沒有 fresh Owner foreground，或 LINE app/window/PID/group 不連續；
- 自動派送點的實際 event point/recipient evidence 仍不足；
- menu 不唯一、popup ownership 不明、安全交集小於 `16×16` 或誤差上界無法證明 `<=2px`；
- Save All 結果 UNKNOWN、已派送但無法確認、或任何 replay 風險；
- 目的地非空、歷史／人工 65 相簿被選中、B 與 A 相同、或沒有 eligible B；
- A 的逐檔 SHA/完整 ImageIO/VERIFIED/readback/release 任一未完成。

## 明確不做

- 不改 `max_albums_per_run` 為 2，不建立新 Orchestration，不降低 `2px`/`u+4`/`16×16`。
- 不使用 shadow-click、歷史座標、OCR 中心、EventTap 收據或一次可逆成功代替真正 Save All 證據。
- 不使用 PR #14 的 HUMAN P0、A56 grant、舊 CLOSED_NO_REPLAY 或既有 `2/2` 額度。
- 不把 synthetic fixture、offline diagnostic、單本 A 或目前 0 次 Save All 宣稱為兩本 E2E 完成。

## 最小來源變更

`MINIMAL_REQUIRED_SOURCE_DELTA=NONE_CURRENTLY_ADMISSIBLE`。

本 Plan 不提出產品 diff。若未來要改用 native `GatedQuartzActuator`，至少會涉及 `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift`、`rev28/Sources/rev28ctl/main.swift`、`harness-development/line-two-album-pilot-20261014/mac_runtime.mjs` 與對應輸入 bridge/test；這是新的受審架構與證據契約，不是本 Plan 可偷偷夾帶的修補。現階段唯一正確動作是停止在 `AUTO_CLICK_PROOF_UNSUPPORTED`，不猜點、不派送。

## 證據索引

| 證據 | 位置／識別 |
| --- | --- |
| AUTO base | `516932dfcee94b662082b909b7980fc2483ab9c0` |
| A/C1/B 入口 | `harness-development/line-two-album-pilot-20261014/two_album_entry.mjs:257-302`；base SHA-256 `f5981c071709203adc2c1cbbc8d5779a77eb1bc37cf0eb8e0444aa5ee21ab277` |
| runtime cap/preflight | `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs:188-190,455-461,493`；base SHA-256 `a1d2c16528b5584a02780045384afb535715287925cabccdaab2111d03ffe27d` |
| CUA dispatch gap | `scripts/line_backup_cua_adapter.mjs:291-294,609-630`；base SHA-256 `1b41f7c87b65692a69c229bce7e4db3f5c0a82f0f1349d776cf8bcb3254bde5d` |
| quota / authorizer | `src/line_backup_batch/cli.py:313-388,416-418` |
| C1/B linkage | `src/line_backup_batch/service.py:341-384` |
| native candidate, not wired | `rev28/Sources/Rev28Core/Actuation/QuartzActuator.swift:224-250,327-335,460-575`；`rev28/Sources/rev28ctl/main.swift:124-130` |
| real refusal | Owner-held `formal-route-preflight-20261018.json` SHA-256 `65cd1d51c4308c6090f2143bd3fe3d228c71d76f61b43e519d840268eb10af56` |
| real GUI/report | Owner-held `E2E測試報告.md` SHA-256 `0b0a375cdbe0f8a721dc10c0a67228539f385d60098ca0af01dbd93a9a5c7a87`; Save All 0, A/B/chooser/downloads NOT_RUN |
| current direction | <https://github.com/s9008129/Line_backup/pull/10#issuecomment-6263019234> |

## 交接

本文件是待外部審查的 Plan，不是核准、不是 Implementation，也不是 E2E PASS。Owner 下一步只需把固定 base、Plan SHA、本文件與證據索引交給 External ChatGPT Plan Review；在收到 `APPROVE_PLAN` 前不得開始產品修改或任何 LINE 輸入。
