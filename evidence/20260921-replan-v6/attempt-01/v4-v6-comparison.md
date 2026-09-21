# Phase E — v4 與 v6 比較（v4-v6-comparison）

- **TASK**: LINE Album Backup；`旻謙允禎成長日記` / `2024/05/13～05/17` / count 57
- **GUI_INPUT_COUNT**: `0`
- 引用：Phase A `v4-failure-analysis.md/.json`；Phase B `architecture-decision.md`；v6 源與自測見 `evidence/20260916-route/tools/v6/`、`evidence/20260921-replan-v6/replay/selftest/results.json`。

## 1. v4 為什麼在三個畫面都得到 null bottom margin？

因為 v4 的 band 判定是「**整張截圖每一列的像素平均值 ≥100**」，而 attempt-08/09 餵入的是 full-screen 影像（2294×1490），LINE window 只佔每列寬度 **28.51%**。
`OBSERVED`（重算）：

| frame | title 下方 full-row mean 最大值 | 是否 ≥100 | 結果 |
|---|---|---|---|
| a08r1 | 78.878 @ y=1101 | 否 | `band_bottom=null` → `margin_below=null` |
| a08r2 | 91.836 @ y=1353 | 否 | 同上 |
| a09 | 66.679 @ y=1168 | 否 | 同上 |

數學上界：即使窗口內整列全白，貢獻上限 0.2851×255 ≈ **72.7 < 100**——**單靠 LINE window 內容永遠無法觸發 v4 的下方 band**。同一份規則改在窗口 x 範圍內計算，三道畫面的下方 band 立刻出現在 y=1078 / 1042 / 1210。故 `null` 是 domain 造成，不是畫面內容缺失。

## 2. v6 的 spatial domain 與 v4 有何不同？

| | v4 | v6 |
|---|---|---|
| Row 統計範圍 | 傳入影像的**整排**（full screenshot 2294px） | `--window-geometry` 指定的 **LINE-window ROI**（本 replay：a08 x[10,663]、a09 x[0,653]） |
| 邊界訊號 | 單一 row mean ≥ bright=100 | 每列「與**本 frame 背景色**（中位數，實測 RGB 45,46,48，MAD=0）差異 ≥60 的像素占 ROI 寬度比例」 |
| 上方/下方 band | 從 title 往外第一個亮列 | 內容佔比 ≥0.45 且 ≥20 列的連續 run（ROI 內、candidate ±500px clamp） |
| 中間帶驗證 | 無 | caption strip：介於兩 band、內容佔比 ≤0.30、≥40 列 |
| 控制點驗證 | 無 | strip 內除 title/count 外**恰好一個** cluster（⋮），距 title/candidate ≥100px、大小 ≤48×80 |
| 座標系 | 影像像素（無 provenance） | current-frame 像素；ROI 必須綁 frame SHA-256 |
| 候選點 | `[x0+12, (y0+y1)//2]` | 同左（逐字沿用；由本 frame OCR 導出） |

## 3. v6 是否降低了安全標準？

沒有。逐項比較：

| 檢查 | v4 | v6 |
|---|---|---|
| 上下 margin 下限 | 10 px（且只在 full-row 亮列上有效） | **max(24, title_h) = 27 px**（a08r1/r2/a09；合成案例中 title_h=23/24 時為 24）——**數值更高** |
| 身分驗證 | title 可讀 + count 不 mismatch | 相同（逐字沿用 title/count 規則與 frozen reader） |
| 候選點來源 | 本 frame | 本 frame（相同公式；無歷史座標） |
| ROI 綁定 | 不存在（無域概念） | frame SHA-256 綁定；未綁定/缺檔/越界/過小 → refuse |
| 相鄰卡片/控制點分離 | 無 | strip 唯一 cluster + 距離/大小界線（v4 完全沒有這一層） |
| 不確定時 | 只有 4/5/2/6 | 7/8/9/10/11 共 5 種新 refusal |

新門檻 **沒有**任何一項比 v4 寬鬆；v6 只是把同一批安全要求搬到「與該卡同座標系的局部證據」上。

## 4. v6 是否只是讓既有 frame 比較容易 PASS？

不是「調鬆以求 pass」：`OBSERVED` v6 的三個 replay 邊界（45/102、44/103、46/101 px）以 **1.6×–4×** 幅度越過 27px 下限，且這些邊界值在 v4 的 domain 下根本量不到（v4 的上 margin 904/338/1074 是 wallpaper/menu bar；下 margin 不存在）。
反向證據（負向控制）：把同一批 frame 餵給 v6 但刻意破壞局部結構，全部 refuse——grid 上移 30px → `UNSAFE_MARGINS`（15<27）；grid 下移 100px → `UNSAFE_MARGINS`（17<24）；strip 多加一個控制點 → `STRIP_CONTENT_UNEXPECTED`；ROI 換成整個螢幕 → `CARD_STRUCTURE_UNRESOLVED`。若 v6 只是「比較寬鬆」，這些案例應照樣通過。

## 5. 是否存在新的 false-positive path？

逐一檢視可能的新風險與其防線：

- **偽造/誤配 ROI 使 band 位置錯誤**：v6 要求 candidate 距 ROI 邊 ≥16px、title 四側內縮 ≥8px、ROI 右尾 ≥120px、strip 內必須看到 ⋮（該卡右端控制點）且距 candidate ≥100px。這些條件把 ROI 寬度逼到「必須同時容納 x≈39 的 candidate 與 x≈617–621 的 ⋮」——截窄、位移、跨界到其他視窗的 ROI 都會在 7/8/9/10 之一 refuse（自測 6 例覆蓋）。
- **把相鄰卡片當成 target 的 strip**：candidate 錨在**本 frame OCR 的 target title**（A 條件）；strip 是包住該 title 的那一條；上/下 band 是「離開這條 strip 後最近」的內容 run。上鄰卡的 caption 也是低內容列——若 target title 不可讀就 refuse（2），不會滑到別的卡。
- **ROI 內出現比真鄰居更近的假 band**：假 band 只會讓 margin 變小 → refuse（fail-closed 方向）。
- **偽造 frame-SHA 綁定的「歷史座標 ROI」**：這是**輸入真實性**問題（任何輸入都可被偽造，例如換一張圖）。v6 的防線是：就算使用了外來 ROI，仍必須在原 frame 上通過局部結構驗證；且流程上 geometry 必須綁 SHA，歷史幾何檔在 SHA 檢查即 refuse（`unbound_geometry_sha` 自測）。
- **OCR 讀到別處的同名日期**：title 規則取最小 span（v4 逐字沿用），且 count 必須同時不 mismatch；偽造風險與 frozen v4 相同，未放寬。

`INFERRED`：目前沒有已知的新 false-positive path 能在不違反上述任一檢查的情況下把「非安全 interior 的點」輸出為 ELIGIBLE；此結論的驗證方式是自測矩陣與兩份獨立 review（Phase F）。

## 6. v6 是否仍 fail closed？

是。`OBSERVED`：自測 20 例中 17 例負向案例全部以預期 refusal code 結束、0 例 ELIGIBLE、0 例任何 dispatch 欄位為 true；4 項全域斷言（無歷史座標字面、候選點逐 frame 推導、負向零 eligible、attempt-07 不可 replay 的誠實記錄）全部成立。v6 沒有任何「best effort」或 fallback 分支。

## 7. attempt-09 在 v6 的 offline replay verdict？

`OBSERVED`：`ELIGIBLE`，exit 0，click `[39,1109]`（= 本 frame OCR title `[27,1096,257,1123]` 的 `x0+12, center_y`），margins 46/101 px（sep_min 27），bands 1063/1210，背景色 (45,46,48) MAD=0，strip 內唯一 cluster 寬 5、高 26，距 title 350px、距 candidate 568px；`dispatch.dispatched=false`。
其他兩張：a08r1 `ELIGIBLE` 45/102、a08r2 `ELIGIBLE` 44/103。

## 8. 即使 offline ELIGIBLE，為什麼仍不能作為 live click 授權？

1. **座標空間未經 live 綁定**：ELIGIBLE 是對「已凍結的舊 frame」的判定；live 需要 fresh frame + 與其綁定的 fresh ROI（AX 觀測或離線抽取）重新推導候選點。
2. **輸入真實性未證**：offline ROI 由本波抽取器導出；live 路徑要求 read-only AX window bounds 或等價 current-frame provenance。
3. **未經 fresh S1-S4**：live 需先做零輸入 S1-S2（視窗/身分讀取）、fresh S3（v6 判定），流程與歷史 gate 無關。
4. **授權仍須重新建立**：gate-6 屬 attempt-08 歷史 artifact、已 CLOSED，不得重用；任何 live click 需要「新 plan SHA + 新 v6 SHA + fresh frame SHA + fresh ELIGIBLE 證據 + 新 route attempt + 新的單次 owner 明確授權」。
5. **ELIGIBLE 的語意**：只代表「新 safety architecture 值得進行下一輪 fresh zero-input live verification」，不代表「可以點相簿」。

## 附：本比較的負向控制實測（自測編號）

| 案例 | 期望 | 實測 |
|---|---|---|
| insufficient_upper_separation | 4 | 4（15 < 27） |
| insufficient_lower_separation | 4 | 4（17 < 24） |
| ambiguous_strip_cluster | 10 | 10（2 clusters） |
| roi_is_full_frame | 4/9/10 | 9 `CARD_STRUCTURE_UNRESOLVED` |
| target_near_roi_edge | 8 | 8 |
| geometry SHA 不綁定 | 7 | 7 |
