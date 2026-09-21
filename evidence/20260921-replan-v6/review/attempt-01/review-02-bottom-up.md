# Phase F — Review 2：adversarial / bottom-up review（v6 album-card S3）

- **受審對象（freeze 後、唯讀）**：`evidence/20260916-route/tools/v6/locate_album_card.py`（`d55a974fd61f…`）、`extract_window_geometry.py`（`b396d6a85c9b…`）、`selftest/run_selftest.py`（`104ed68ec6c0…`）、`README.md`（`7527ce3dfc8a…`）；`evidence/20260921-replan-v6/**`。
- **凍結錨點**：`artifact-freeze.json` `d6d705def55c…`（63 artifacts；本 review 開工前已重算 63/63 相符）。
- **方法**：bottom-up / adversarial — 由 repository grounding 與程式碼層出發，逐條列舉攻擊路徑並實際嘗試或逐一覆核其防線；主動搜尋能讓錯誤點變 `ELIGIBLE` 的反例。
- **獨立性揭露**：與 Review 1 為同一 wave 的兩個分離 pass（方法論不同：此份以攻擊面為主），皆 freeze 後、read-only、獨立重跑驗證；執行者與 Phase A–E 作者同為一 agent session —— 此限制明確揭露，不誇大為人類獨立審查。
- **GUI_INPUT_COUNT**: `0`（未操作 LINE、未擷取新 frame、未派送任何輸入）。

---

## A. 攻擊面矩陣（每一條都實際做過檢查或重跑）

| # | 攻擊 | 嘗試/檢查方式 | 結果 |
|---|---|---|---|
| A1 | 偽造/錯位/缺失 ROI | 逐行檢視 `load_geometry()`；獨立重跑 selftest | 缺檔／非 JSON／缺欄／bool 冒充 int／負規格／越界／<200×200 → `WINDOW_ROI_MISSING_OR_INVALID`(7)；未綁本 frame SHA → 7；ROI 不含 title/右尾不足 → `IDENTITY_NOT_ROI_BOUND`(8)；全螢幕 ROI → `CARD_STRUCTURE_UNRESOLVED`(9)。全部 fail-closed。 |
| A2 | 惡意 frame 變造 | selftest 合成 + 我獨立重跑 | title 抹除→2；錯日期→2；count 讀值非 57→5（讀不到不 refuse＝v4 語意）；malformed PNG→6。 |
| A3 | 鄰卡冒充 target | 程式碼論證＋frame 目視 | strip 必含 title center_y（title 由本 frame OCR 得）；band 取最近 run；鄰卡 caption 在更高 y 不可能是此 strip。冒充須同時過日期＋count＋ROI 幾何（⋮ 在 strip 內距 ≥100px），實際上不可行；方向全為 refuse。 |
| A4 | 歷史座標注入 | grep decision source / 檢查 runtime 輸入面 | locator+extractor 無任何 forbidden 座標字面、無 attempt 路徑；geometry 必綁 frame SHA；selftest 內建注入禁止斷言（forbidden 清單只出現在測試檔，屬「檢查它不存在」）。 |
| A5 | 調鬆門檻求 pass | 常數對照＋負向控制重跑 | `SEP_MIN=max(24,title_h)=27 >` v4 的 10；負向控制（grid 位移、多 cluster、全螢幕 ROI）全部 refuse；「調鬆假說」被證偽。 |
| A6 | 對 attempt-09 特例化 | 檢視 source 分支＋跨 frame 行為 | source 無 attempt-09 專屬分支；同一規則讓 a08r1/a08r2 同樣 ELIGIBLE；常數理由全部記錄於 README，與 attempt-09 無關。 |
| A7 | v4 fallback | 檢視 import 與判定流 | 只 import v4 `vision_reader`（未修改）；**不**呼叫 v4 locator、無 fallback 分支；每個 verdict 記 `fallback_to_v4_candidate: false`。 |
| A8 | 派送路徑 | grep `dispatch/CGEvent/pyautogui/osascript/subprocess` in locator | 無任何輸入 API；唯一 dispatch 欄位為 `{"dispatched": false}`；本輪全部 outputs（3 replay）逐一檢視皆 false。 |
| A9 | 重跑不一致／掉包 | 獨立重跑 a09 replay＋全 selftest；101 檔 before/after 快照 | a09 replay byte-identical（modulo helper binary sha）；selftest 21/21、4/4；101 檔前後零差異 → 結果不可被「跑一次 pass 換一次」偷換。 |
| A10 | Reader 供應鏈 | 檢查 import 路徑與 SHA 宣告 | 以 sibling 絕對路徑載入 frozen v4 reader；source 內宣告其 SHA `22a4e9ef…`；每 verdict 記 reader 與 helper 資訊（helper binary sha 為本機重編譯之 volatile 值，已誠實標記）。 |
| A11 | `merge_close`/cluster 邏輯被小雜點鑽過 | 讀 `connected_components`→`merge_close` 流程與負向案例 | strip 內 cluster 必須**恰為 1**；多 cluster→10；單一 cluster 超過 48×80 或距 title/candidate <100px→10。方向正確。 |
| A12 | 座標空間混淆（pt vs px） | 檢視 README 座標轉換與 verdict `coordinate_space` | v6 只在 frame 像素空間判定；live 幾何輸入必須已是 frame px（2× window pt，attempt-07 screen-probe 佐證）；未在判定時做任何比例猜測。 |

## B. 反例搜尋記錄（主動找碴，保留最有價值的四條）

1. **「ROI 上緣誤含視窗上方 wallpaper」**：band 取「離 center_y 最近」的 run；較遠 wallpaper 不影響 margin。若 wallpaper 竟然更近（caption 上方 20 列內有 ≥45% 內容帶），margin 只會變小 → refuse(4)。無破口。
2. **「strip 內有照片殘影」**：strip rows 僅收 content fraction ≤0.30 的列；殘影列不被計入；kept rows <40 → refuse(9)。無破口。
3. **「⋮ 被 merge_close 與雜點併成巨塊」**：合併後尺寸超過界 → refuse(10)。無破口。
4. **「同一 frame、攻擊者自製 geometry 卻通過所有檢查」**：要通過 identity(8)、count(5)、band/strip(9)、cluster(10)、margin(4) 全部 frame-derived 檢查，該 ROI 必須與 frame 的真實卡片結構一致；此時判定語意仍是「以 frame 證據證明了候選點在卡片安全內」——殘餘問題退化為 **provenance 流程**（誰產生 geometry），不是判定邏輯破口。此風險由 R1/R2 承接（見 §D）。

## C. 八個必答問題（adversarial 視角）

### Q1 — frozen v4/v5 是否未被修改？
**是。[OBSERVED]** 重算 v4/v5 六個 source SHA-256 全部與 frozen_inputs 記載一致；`git status` 無 tracked modification；attempt-07/08/09、gate-6 artifact 皆未觸碰；本 review 的任何重跑（含 selftest）對 101 檔做 before/after 快照 → 零差異。

### Q2 — v6 是否使用 current-frame/local-window evidence？
**是。[OBSERVED]** 候選點由本 frame OCR title bbox 推導（三個 frame 的 click_point 均等於各自 bbox 的 `[x0+12, center_y]`）；band/strip/control 在 frame-SHA 綁定的 ROI 內、以本 frame 背景色量測；`coordinate_space` 欄位明示 current-frame 像素。

### Q3 — 是否有 historical coordinate leakage？
**無。[OBSERVED]** decision source 無 forbidden 座標／attempt 路徑；判定輸入只有（frame bytes、geometry 檔、expected 值）；跨 frame 重用 geometry 在 7 直接失效。唯一含 forbidden 字面的檔案是 selftest 的「禁止清單斷言」，其存在目的是證明 source 不含這些座標。

### Q4 — 是否降低安全 threshold 來追求 pass？
**沒有，且方向相反。[OBSERVED]** sep_min 由 v4 的 10px 提高到 27px；新增 5 類 refusal；負向控制會把「寬鬆假說」證偽；三個 replay 邊界 ≥1.6× 越過門檻。

### Q5 — 是否存在 target identity confusion？
**未發現新路徑。[OBSERVED/INFERRED]** title 規則逐字沿用 v4（最小 span）；count mismatch refuse；v6 另把 identity 釘進 ROI（8）——比 v4 更嚴。誤讀風險面與 v4 相同，無擴大。

### Q6 — 是否可能把 neighboring card 當作 safe target interior？
**不能（除非先通過全部 frame-derived 檢查，而那時它就是被 frame 證明的區域）。[INFERRED]** strip 幾何上必含 target title 列；band 取最近 run；鄰卡冒充需同時滿足日期、count、ROI 幾何；所有誤判方向都是 refuse。

### Q7 — 是否仍 fail closed？
**是。[OBSERVED]** 18 負向案例全 refuse、0 例 ELIGIBLE、0 例 dispatch；source 無 best-effort 分支；ELIGIBLE 是全條件交集。

### Q8 — 是否允許進入 future zero-input live S1-S3 test？
**允許「下一輪 zero-input live v6 S1-S3 的設計與執行」，且僅限 zero-input。** 任何 click 仍需：新 plan SHA＋新 v6 SHA＋fresh live frame SHA＋fresh ELIGIBLE 證據＋新 route attempt＋新的 owner 明確一次性授權（gate-6 不修改、不重用）。本 review 不放行任何 GUI input。

## D. 殘餘風險（adversarial view，與 Review 1 一致）

- **R1（中）**：offline ROI 來自本案自寫的 extractor——其為決定性（我實測 byte-identical），但 provenance 獨立性有限。**live 必須改用 read-only AX 觀測**，此為下一波硬性要求；本輪不接受任何 live 判定使用 extractor。
- **R2（低-中）**：SHA 綁定防跨 frame 重用，不防同 frame 偽造 geometry；防線是 frame-derived 檢查＋流程稽核。下一波需把 geometry 產生步驟併入 run ledger。
- **R3（低）**：unreadable count 不 refuse（v4 語意）；identity 由 title 承擔。
- **R4（低）**：extractor border-line heuristic 依賴主題色（offline-only 影響）。
以上皆不構成「錯誤點可變 ELIGIBLE」的具體路徑。

## E. Bottom-up grounding 檢查

- 佈局與 README 宣稱一致；refusal codes 與 `main()` 分支逐一對照無出入。
- 依賴：`/opt/homebrew/bin/python3` + Pillow + numpy；無新第三方依賴、無網路呼叫（source 掃描）。
- 決定性：三 replay + 全 selftest 重跑 byte-identical；本機唯一 volatile 值（Vision helper binary sha）已文件化。
- 座標轉換：只在 frame px 空間判定；live 幾何輸入必須已是 transformed frame px（README 明示，2× pt→px 由 attempt-07 screen-probe 佐證）。

## F. Gate

逐條攻擊（A1–A12）與反例搜尋（B1–B4）均未發現能讓「非安全 interior 的點」輸出 `ELIGIBLE` 的具體路徑；fail-closed 行為、決定性、freeze 完整性均已獨立重驗。核發：

PLAN_APPROVED
