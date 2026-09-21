# Phase A — frozen v4 根因重算（v4-failure-analysis）

- **TASK**: LINE Album Backup；group `旻謙允禎成長日記`；album `2024/05/13～05/17`；expected count `57`
- **REPLAN ROOT**: `evidence/20260921-replan-v6/`
- **GUI_INPUT_COUNT**: `0`（本輪全程零 GUI 輸入；純離線重算）
- **機器可讀版本**: `evidence/20260921-replan-v6/attempt-01/v4-failure-analysis.json`
- **輸入（disk 重新 re-hash）**: 見本文件末「輸入 SHA-256 表」；所有數字皆由 frozen 證據＋重跑產生，不採用任何記憶或轉述。

標籤語意：`OBSERVED` = 直接從 disk 證據或可重跑程式輸出觀察到；`INFERRED` = 由觀察推得（非直接觀察）；`UNKNOWN` = 現有證據無法判定。

---

## 1. Frozen v4 的判定機制（精確公式與 pixel domain）

來源：`evidence/20260916-route/tools/v4/locate_album_card.py`
sha256 `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162`（未修改）。
OCR 讀取器：`tools/v4/vision_reader.py` sha256 `22a4e9ef…`（macOS Vision）。

| # | 機制 | 精確規則（frozen 原文行號） |
|---|---|---|
| 1 | title 如何找到 | `find_title()` L68–L88：把 OCR words 中最多 4 個連續 word 的「數字字元」串接，保留含 `20240513` 且其後含 `20240517`（或末四碼 `0517`）的 span，取最小 span；bbox = 被選 words 的聯集（**full-frame pixel 座標**）。呼叫點 L150–L151。 |
| 2 | count 如何找到 | L175–L176：裁切框 `(x0-8, y1+2, x0+160, y1+32)`（相對 title bbox，**full-frame 座標**），scale 10 OCR，串接數字。`57` 在其中 → `MATCH`；可讀但不同 → `MISMATCH` 拒絕（exit 5）；不可讀 → 記錄但不拒絕。 |
| 3 | `band_top_bright_row` | L104–L112：從 `y0-1` **向上**掃到 y=0，第一個 `row_mean(y) ≥ bright` 的 y；找不到 = `null`。 |
| 4 | `band_bottom_bright_row` | L104–L112：從 `y1+1` **向下**掃到 `height-1`，第一個 `row_mean(y) ≥ bright` 的 y；找不到 = `null`。 |
| 5 | `row_mean` 的 spatial domain | L96–L101：`row_mean(im, y) = Σ_{x=0}^{W-1} gray(x,y) / W`，其中 `W = im.size[0]` = **傳入工具影像的整排寬度**。attempt-08/09 傳入的是 full-screen 截圖（2294×1490），因此 domain = **full screenshot 整排**，不是 LINE window、不是 album card。 |
| 6 | bright threshold | `bright = 100`（L104 預設值）。 |
| 7 | `UNSAFE_MARGINS` 完整 boolean condition | L196–L198：`click_point is None or margin_above_px is None or margin_below_px is None or margin_above_px < 10 or margin_below_px < 10`。其中 `margin_above_px = center_y - band_top`、`margin_below_px = band_bottom - center_y`（L172–L173）。 |
| 8 | candidate click point | L186–L190：`click_point = [x0+12, (y0+y1)//2]`，僅當 `0 ≤ x0+12 ≤ width-20` 且 `x0+12 ≤ x1+40`；否則 `null`。 |

`OBSERVED`：v4 對「影像」沒有任何 window 概念；同一份卡片的 row 統計會隨「餵進去的影像寬度」而變。attempt-08/09 餵入 full-screen → 整排平均。

## 2. 離線重算（attempt-08 r1 / r2、attempt-09）

方法：以 frozen v4 原檔、frozen 影像重跑（唯讀；未改 threshold、未改任何 frozen 檔），另用 `row-domain-recompute.json` 重算「full-row domain」與「LINE-window-local domain」兩種 row mean。

| 指標 | attempt-08 r1 | attempt-08 r2 | attempt-09 |
|---|---|---|---|
| frame sha256 | `9f0d35f1…` | `2226ded9…` | `ae0de47d…` |
| title bbox (full-frame px) | [37,963,267,990] | [37,926,263,953] | [27,1096,257,1123] |
| title readability / count | `MATCH 57` | `MATCH 57` | `MATCH 57` |
| v4 `band_top_bright_row` | 72 | 601 | 35 |
| v4 `band_bottom_bright_row` | **null** | **null** | **null** |
| v4 `margin_above_px` / `margin_below_px` | 904 / **null** | 338 / **null** | 1074 / **null** |
| v4 verdict（重跑 exit code） | `UNSAFE_MARGINS` (4) | `UNSAFE_MARGINS` (4) | `UNSAFE_MARGINS` (4) |
| FULL-ROW mean 在 title 下方之最大值 | 78.878 @ y=1101 | 91.836 @ y=1353 | 66.679 @ y=1168 |
| 同上，是否曾 ≥100 | 否 → `band_bottom=null` | 否 | 否 |
| LINE-window-local（ROI x 範圍）同規則 | band_bottom=**1078** | band_bottom=**1042** | band_bottom=**1210** |
| 同局部規則 margins | 45 / 102 px | 44 / 103 px | 46 / 101 px |
| v4 band_top 那一行的組成 | y=72：full-row mean **164.870**；該列屬 **window 上方的 wallpaper**（窗口上緣 ≈ y=123） | y=601：full-row mean **103.291**（grid 內部的一列，靠非窗口內容越線） | y=35：full-row mean **106.406**（**macOS menu bar** 列，窗口上緣 ≈ y=102） |
| LINE window ROI（本波離線抽取） | [10,123,663,1334] | [10,123,663,1334] | [0,102,653,1307] |
| 窗口寬度佔整排比例 | 28.51 % | 28.51 % | 28.51 % |

`OBSERVED` 補充：

- 決定性（determinism）：同一 frame 重跑 v4 兩次，輸出**逐位元組相同**（除 `reader.helper.binary_sha256` 這個本機重編 Vision helper 的雜湊）；attempt-09 的重跑輸出與 frozen 證據檔**完全逐位元組相同**（含 helper 雜湊）。
- 三個畫面的視窗配置不同（r1/r2 同位置不同捲動；a09 換位、換尺寸），但**同一 failure mode**。
- 三個畫面的局部卡片結構（上 grid / caption strip / 下 grid）**都完好**；只有 caption 下方的「整排」永遠達不到 100。
- 數學上界：`OBSERVED` 視窗寬度佔 28.51 %。即使整條窗口列全白（255），對整排 mean 的貢獻上限 = 0.2851×255 ≈ **72.7 < 100**——單靠 LINE window 內容永遠無法讓 full-row mean 越過 v4 門檻。
- 三個畫面的 GUI input 計數皆為 0（attempt-08 ledger：`gui_input_count: 0`、click/Save All/chooser/download 全 0；attempt-09 ledger：`CLOSED_BEFORE_INPUT`、0 input）。

## 3. attempt-07（歷史對照）

- `OBSERVED`：attempt-07 的 `album-card-locate.json` 記錄 `band_top=72`、`band_bottom=1002`、`margin_below=107`、verdict `ELIGIBLE`（frame `/tmp/route7_frame_pre.jpg`，sha `2897628770dd…`，full-screen 2294×1490）。
- `OBSERVED`：該 frame 檔已不存在（原在 `/tmp`，未保留；repo 內重掃所有影像檔無此 sha）。**無法**對 attempt-07 做局部重算，本文件不臆造其數字。
- `INFERRED`：即便在該畫面，caption 下方要讓「整排」mean ≥100，也必須有窗口外的亮內容共同參與（單窗口列貢獻上界 72.7）。因此 attempt-07 的 `margin_below=107` 是否量到真實 grid 邊界，還是螢幕上無關亮列湊巧越線，無法證明。
- `UNKNOWN`：y=1002 那一列由哪些像素構成（frame 未保存）。

## 4. 根因結論

1. `OBSERVED`：frozen v4 的 failure mechanism 已被證明＝**full-screenshot row domain 與 window-local card 內容的 spatial-domain mismatch**。三個不同配置都：title 可讀、count 57 MATCH、`band_bottom_bright_row=null`、`margin_below_px=null`、`UNSAFE_MARGINS`、GUI input 0；且重跑可完全重現。
2. `OBSERVED`：`margin_above`（904/338/1074 px）量到的是 wallpaper/menu bar，並非卡片局部訊號——v4 上方 margin 檢查在此架構下同樣失去語意。
3. `INFERRED`：問題**不是畫面擺放**（三個畫面的卡片局部結構都完好），而是**判定架構**：v4 對「影像寬度」沒有 window 概念，卻用整排平均當卡片邊界證據。任何依賴「整排 mean」的通過/失敗都受無關螢幕內容支配。
4. `INFERRED`（設計後果，供 Phase B）：安全架構必須讓「候選點是否位於目標卡安全 interior」的證據**只來自與該卡同視窗、同座標系、同 frame 的局部內容**，且在無法建立該局部域時 fail closed。

## 5. 輸入 SHA-256 表（全部自 disk 重讀）

| 檔案 | SHA-256 |
|---|---|
| attempt-08/album-card-locate.json | `07437fb8359a47be5fd6daaf0c4696a57bedb277402f19f83d56eb74b57f0585` |
| attempt-08/album-card-locate-r2.json | `55d088f8d3c12f7081312c3b33bc01b972b1f818dcb634d6630f822af28d6a5b` |
| attempt-08/run-ledger.json | `0df02dc4bd1b68694f76789a6cd6494fa2299bae26cc669145592d8e3d575469` |
| attempt-08/frame-pre.png | `9f0d35f1a59e1077aee9fbb4797da14e7754a3b946bc9a07aa6d244b76eaae18` |
| attempt-08/frame-pre-r2.png | `2226ded9c29c7ab99bb8126d21f625e6a65e61a6aa94c14eda8d5875a201d08a` |
| attempt-09/frame-pre.png | `ae0de47df43026af0ae851dfcda59c125a5f0f919f143f197a47fe6774667a5a` |
| attempt-09/album-card-locate.json | `c4b4443c1471c1671812b3e4f29214094e5fb7e46e7900e7e22b5ef1ade3d06a` |
| attempt-09/s1-s2-observation.json | `8b060348b77a3066cbb4d58064bb963b0943e2c914aef291f8d7c27cad91bfba` |
| attempt-09/s3-comparison-attempt08.json | `0115b5f10a3badba9741c57a1c360723e2bb4a0a6965e50776fea6eeb18034f7` |
| attempt-09/run-ledger.json | `229fcb30fb237c5ce0561333ab63ae293446e07b15b157a73dcfb205027cb9b6` |
| attempt-07/album-card-locate.json | `94694c921171f98c53b7fc79a350d0f7faf635c234ed17cf894b87f9fb0fd624` |
| attempt-07/screen-probe.json | `38130a6a540c099b3ca88e979a72684a467e158b4a78ce64bf4334ccdba6f77c` |
| tools/v4/locate_album_card.py | `bb52aff1dda8a03845fc82f253a801c010e1bfa6f4cf1d07e5ab4f1365421162` |
| tools/v4/vision_reader.py | `22a4e9ef86c419bdb80723484b3745fe61d848c77fc45c34e0b73e9d4b8801b8` |

（本波新增重算產物：`replay/v4-replay/a08r1.json` `ddd15fc4…`、`a08r2.json` `0f225413…`、`a09.json` `c4b4443c…`；`replay/row-domain-recompute.json` `7887b9d7…`；幾何檔 `geometry/a08r1.json` `2fa739c4…`、`a08r2.json` `3701746a…`、`a09.json` `8886ceb4…`。完整清單見 `evidence/20260921-replan-v6/attempt-01/artifact-freeze.json`。）
