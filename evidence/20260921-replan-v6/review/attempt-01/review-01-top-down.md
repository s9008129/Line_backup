# Phase F — Review 1：top-down safety review（v6 album-card S3）

- **受審對象（freeze 後、唯讀）**：`evidence/20260916-route/tools/v6/`（locator / extractor / selftest / README）與 `evidence/20260921-replan-v6/**`（Phase A–E 全部文件與 replay 證據）。
- **凍結錨點**：`evidence/20260921-replan-v6/attempt-01/artifact-freeze.json` sha256 `d6d705def55c052026d3045da7fd76e08c082517fd30e3cc8669aedae0eeb2db`（63 artifacts）。本 review 為 freeze 後 append-only 產物，未修改任何受審檔（§0 已逐檔 re-hash 驗證）。
- **方法**：top-down — 先重建 Goal Baseline，再檢查：必要性（每條檢查是否 trace 到目標）、critical-path 優先序、gate/veto 比例性、失效圍堵、耦合面、設計經濟。
- **獨立性揭露**：本 review 與 Review 2 為同一 wave 的兩個分離審查 pass（top-down vs adversarial），皆於 freeze 後執行、read-only、各自獨立重跑驗證；執行者與 Phase A–E 作者為同一 agent session——此為本輪可用資源下的最大獨立性，明確揭露而不假裝是人類獨立審查。
- **GUI_INPUT_COUNT**: `0`（本 review 全程離線；未操作 LINE、未擷取新 frame、未派送任何輸入）。

---

## 0. 本 review 實際執行的獨立再驗證（全部親自跑過）

| # | 動作 | 結果 |
|---|---|---|
| 1 | 重算 freeze manifest 內 63 檔 SHA-256 | 63/63 相符（bad=0） |
| 2 | 重算 frozen v4/v5 全部 source SHA-256 | 全部與 attempt-08/09 ledger 記載一致（v4 locate `bb52aff1…`、v4 reader `22a4e9ef…`、v5 ellipsis `6a015ea6…`、v5 verify `ffa82aed…`） |
| 3 | 重算 attempt-07/08/09 frozen evidence SHA-256 | 與各 ledger / 本 wave Phase A 記載一致 |
| 4 | 獨立把 v6 對 attempt-09 的 replay 重跑到 temp 目錄 | verdict 相同；輸出與已記錄 `replay/a09-v6.json` **逐位元組相同**（唯一差異欄位 `reader.helper.binary_sha256`＝本機重編譯的 macOS Vision helper 雜湊；已誠實記錄） |
| 5 | 獨立重跑整份 selftest | `cases 21/21 passed`、`global_assertions 4/4 passed` |
| 6 | selftest 前後對 101 檔（replan-v6＋tools v4/v5/v6＋attempt-07/08/09）快照 SHA-256 | **前後逐位元組零差異**——同時證明 (a) 判定決定性、(b) frozen 與已凍結證據未被任何重跑觸碰 |
| 7 | 目視 QC（離線，僅旁證） | 將 attempt-09 frame 局部放大並標出 candidate `[39,1109]` 與 below-band y=1210：肉眼確認 candidate 位於目標卡 caption strip 內、strip 上／下各為照片 grid、strip 右端為 ⋮ 控制點 |

以上皆為本 review 親自重跑/重算，非引用 Phase A–E 的轉述。

---

## 1. Goal Baseline（先重建目標，再看設計）

本波唯一主目標：**以 attempt-08/09 fresh evidence 重設計 album-card S3 的安全判定架構**，使其能在不降低安全要求、不修改 frozen v4、不依賴歷史座標的前提下，對 current frame 的實際局部畫面做「可證明的安全點判定」；GUI_INPUT_COUNT 永久保持 0。

S3 必須維持的性質（對應 Phase B B.1）：
A exact target identity；B expected count 不 mismatch；C candidate 由 immediate frame 推導；D candidate 位於 target card 安全內部區域；E 與上／下相鄰卡及 destructive UI 有足夠 separation；F 不使用 historical coordinate；G uncertainty ⇒ fail closed。

**Top-down 檢查**：v6 的每一個 refusal code（2/4/5/6/7/8/9/10/11）都 trace 回 A–G 至少一項；沒有發現「存在但不 service 任何 target 條件」的檢查，也沒有發現「A–G 有哪一項沒有被任何檢查覆蓋」。

---

## 2. 八個必答問題

### Q1 — frozen v4/v5 是否未被修改？
**是。[OBSERVED]** 逐一 re-hash：
`tools/v4/locate_album_card.py bb52aff1…`、`tools/v4/vision_reader.py 22a4e9ef…`、`tools/v5/locate_album_card.py bb52aff1…`、`tools/v5/locate_album_ellipsis.py 6a015ea6…`、`tools/v5/verify_album_open.py ffa82aed…`、`tools/v5/vision_reader.py 22a4e9ef…`——全部與 attempt-08/09 ledger 的 frozen_inputs 記載一致。`git status --porcelain=v1 --branch` 僅見 append-only 的 untracked 目錄，**無任何 tracked file modified**；attempt-08/09 與 gate-6 artifact 均未觸碰（d3728e7 未 amend）。

### Q2 — v6 是否使用 current-frame/local-window evidence？
**是。[OBSERVED]**（source 層核實）
- 候選點 `[tx0+12, (ty0+ty1)//2]` 由**本 frame 的 OCR title bbox** 導出（`locate_album_card.py` main() 內逐 frame 計算；a08r1 `[49,976]`、a08r2 `[49,939]`、a09 `[39,1109]` 皆等於各自 frame OCR bbox 的推導值）。
- band / strip / control cluster 全部在 `--window-geometry` 指定的 ROI 內量測，且以**本 frame 局部背景色**（title 右側取樣中位數；三 frame 皆 RGB(45,46,48)、MAD 0.0）為基準。
- geometry 必須綁定本 frame SHA-256（不符 → exit 7）；判定不含任何跨 frame 輸入。（唯一例外：offline replay 的 ROI 由本 frame 自身像素抽取，見 §3 殘餘風險 R1。）

### Q3 — 是否有 historical coordinate leakage？
**無。[OBSERVED]**
- grep v6 decision source（locator + extractor）：無 `[39,1109]`、`[49,939]`、`[42,895]`、`[304,50]`、`[305,50]` 或任何 attempt-07/08/09 路徑字面。
- 判定鏈上唯一的「歷史」數字是 freeze manifest 中記錄的既有候選點 SHA 化紀錄（evidence，不參與運算）。
- selftest 第 305–307 行出現的 forbidden 字串是**禁止清單斷言**（測試「source 不得含這些座標」本身），非被使用的座標——檢查方向正確。
- geometry SHA 綁定使「跨 frame 重用歷史 ROI」在 exit 7 直接失效（selftest `unbound_geometry_sha` 實測 7）。

### Q4 — 是否降低安全 threshold 來追求 pass？
**沒有。[OBSERVED]** 逐項：
- 上下 margin 下限：v4 = 10 px → v6 = `max(24, title_h)` = **27 px**（更高）。
- 新增 5 類 refusal（7/8/9/10/11），且全部 fail-closed。
- 反向控制實驗：grid 上移 30px → `UNSAFE_MARGINS`(4, 15<27)；grid 下移 100px → 4 (17<24)；strip 多加一 cluster → `STRIP_CONTENT_UNEXPECTED`(10)；ROI 換全螢幕 → `CARD_STRUCTURE_UNRESOLVED`(9)。若常數是「調鬆求 pass」，這些案例應照樣通過——事實相反。
- 三個 replay 的實際邊界（45/102、44/103、46/101）以 ≥1.6× 幅度越過較嚴的門檻，且這些邊界在 v4 的 full-row domain 下根本量不到（v4 margins 是 wallpaper/menu bar 的 904/338/1074）。

### Q5 — 是否存在 target identity confusion？
**風險維持在 frozen v4 同等級，且 v6 額外收緊。[OBSERVED/INFERRED]**
- title 匹配規則自 v4 **逐字沿用**（最小 span；`find_title()` 標註 copied verbatim）；count 可讀且非 57 → refuse(5)；unreadable count 不 refuse 屬 v4 原語意，未放寬。
- v6 新增 identity→ROI 綁定(8)：title 四側 inset ≥8px、count box 必須在 ROI 內、ROI 右尾 ≥120px。辨識錯誤的空間比 v4 更小。
- 誤讀「別處同日期」的風險面與 v4 相同（最小 span 規則），非新引入。

### Q6 — 是否可能把 neighboring card 當作 safe target interior？
**[INFERRED，有程式碼依據] 不能在不觸發 refusal 的情況下成立**：
- strip 由 `above_bottom < center_y < below_top` 夾出——**strip 必含 target title 所在列**（center_y 由本 frame 的 target title bbox 而來）。上鄰卡的 caption 只會落在更高的 y，不可能是這條 strip。
- band 取「離 center_y 最近的 run」（`above_bottom = max(r[1])`、`below_top = min(r[0])`）——較遠的干擾帶（wallpaper、別卡 grid）不影響 margin；若干擾帶更近，margin 只會變小 → refuse（fail-closed 方向）。
- 鄰卡若要冒充 target，需同時通過 title（日期）＋count＋ROI 幾何（含 ⋮ 在 strip 內、距離 ≥100px）——任一不合即 refuse。

### Q7 — 是否仍 fail closed？
**是。[OBSERVED]** selftest 18 個負向案例全部以預期 refusal code 結束、0 例 ELIGIBLE、0 例 `dispatch.dispatched` 非 false；source 無 best-effort/fallback 分支；ELIGIBLE 需通過全部檢查才可達（decision order 見 README）。4 項全域斷言（無歷史座標字面、候選點逐 frame 推導、負向零 eligible、attempt-07 不可 replay 的誠實記錄）全數成立。

### Q8 — 是否允許進入 future zero-input live S1-S3 test？
**允許進行「下一輪 zero-input live v6 S1-S3 的設計與執行」——但僅限 zero-input。** 任何 click 的前置條件不變：新 plan SHA＋新 v6 SHA＋fresh live frame SHA＋fresh v6 ELIGIBLE 證據＋新 route attempt＋新的 owner 明確一次性授權；gate-6 屬 attempt-08 歷史 artifact，不修改、不重用。本 review 不放行任何 GUI input；本輪 GUI_INPUT_COUNT 維持 0。

---

## 3. Top-down 分析

**必要性**：v6 每條檢查皆 service A–G；候選點公式與 v4 相同（同一 provenance 強度），差別在證據 domain。未發現為 pass 而存在的裝飾性檢查。

**Critical-path 優先序**：S3 是 route 的關鍵路徑；v6 未擴張到 ellipsis locator / S5 verifier / menu detector（scope 與 README 宣稱一致），符合「只解決當前 blocker」的紀律。

**Gate 比例性**：S3 refusal 只阻擋單一 album-card click（本地、低成本補救＝重新綁定/重擷取），沒有把非關鍵輸入升格為 global veto。

**失效圍堵**：所有 refusal 都發生在「派送之前」的判定期；`dispatch` 欄位恆為 `{"dispatched": false}`；本輪所有 verdict JSON 皆然（逐一檢視）。

**耦合**：v6 只以 sibling import 使用 frozen v4 `vision_reader`（source 內宣告其 SHA、不修改），**不**將 v4 locator 作為 fallback；`provenance.fallback_to_v4_candidate: false` 記於每個 verdict。耦合單向且面窄。

**設計經濟**：無新套件依賴（numpy/PIL 已在環境）、無網路、無 daemon/服務、無設定檔；9 個常數皆有記錄理由；整體是一個單檔決策函式＋一個決定性抽取器＋一份自測。

## 4. 殘餘風險（誠實揭露，全部指向 fail-closed 方向）

- **R1（中）— offline ROI provenance 的獨立性有限**：offline replay 的 ROI 由本 wave 新寫的 `extract_window_geometry.py`（frame 像素啟發式）產生，不是獨立於本案的外部來源。接受的依據是：抽取器為決定性、輸出 byte-identical、且 v6 對 ROI 有 frame-derived 交叉驗證（8/9/10 會拒絕不合結構的 ROI）。**live 路徑不得使用此抽取器**——必須使用 read-only AX window-bounds 觀測（獨立於 locator）並在 run ledger 記錄 provenance；此為下一波必要條件。
- **R2（低-中）— SHA 綁定的語意邊界**：frame SHA 綁定防「跨 frame 重用」，不防「對同一 frame 偽造 geometry」。真正防線是 frame-derived 檢查（identity/count/strip 結構）。future live wave 應把 geometry 的產生步驟（AX 觀測）併入 ledger，使 provenance 可稽核。
- **R3（低）— unreadable count 不 refuse**：沿用 v4 語意；identity 由 title（＋可讀時的 count）承擔。未擴大既有風險。
- **R4（低）— extractor 的 border-line heuristic 依賴主題色**：只影響 offline replay；live 用 AX 觀測即繞過。

以上風險不改變核心主張：**v6 的判定是 local、可重算、可解釋，且不確定時一律 refuse**。

## 5. 再驗證數據摘要（本 review 重跑/重算）

| frame | v4（frozen） | v6（offline） | v6 candidate | v6 margins |
|---|---|---|---|---|
| attempt-08 r1 | `UNSAFE_MARGINS`(4)，bottom `null` | `ELIGIBLE`(0) | `[49,976]` | 45 / 102 |
| attempt-08 r2 | `UNSAFE_MARGINS`(4)，bottom `null` | `ELIGIBLE`(0) | `[49,939]` | 44 / 103 |
| attempt-09 | `UNSAFE_MARGINS`(4)，bottom `null` | `ELIGIBLE`(0) | `[39,1109]` | 46 / 101 |

selftest：21/21 cases、4/4 global assertions；101 檔 before/after 逐位元組一致；a09 replay 獨立重跑 byte-identical（modulo helper binary sha）。

## 6. Gate

本 review（top-down）未發現任何違反 Goal Baseline A–G、降低安全標準、歷史座標洩漏、或 identity/neighbor 混淆的路徑；freeze 完整性與決定性均已獨立重驗。核發：

PLAN_APPROVED
