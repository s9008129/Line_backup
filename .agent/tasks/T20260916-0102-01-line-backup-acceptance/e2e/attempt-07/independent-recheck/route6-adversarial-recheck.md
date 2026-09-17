# route6 對抗式複核摘要（Rev23 / attempt-06 路線波；本報告屬 e2e/attempt-07/independent-recheck）

- 角色：對抗式複核者（唯讀＋離線重放）。零 GUI 輸入（不點擊、不截圖、不寫 AX）、零凍結成品修改、零 git commit、python 一律 `-B`、對話中零圖片。
- 時間：2026-09-17T23:46:21+0800。工作目錄：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。
- 結構化資料：`route6-adversarial-recheck.json`（24 項 checks：23 PASS、1 UNKNOWN、0 FAIL）。

## 結論（兩句話）

- **風險 1 — PASS（無沿用／無偽造跡象）**：兩張 post 幀位元相同是「同一畫面內容被兩次獨立真截圖」的結果；兩次擷取各有執行環境本身的 journal 紀錄可獨立佐證，不是沿用舊檔。
- **風險 2 — PASS（決定性；停止屬規則幾何，不是讀取能力）**：3 次重放皆 exit 3 / `NO_ELLIPSIS_FOUND`，輸出與凍結 JSON 位元相同；唯一的非文字三點候選在 band 上緣之上 22–33 px，band 內候選為 0（規則層與原始像素層都為 0）。

## 風險 1：post frame 是否真截圖

| 檢查 | 觀測 | 判讀 |
|---|---|---|
| `stat`（4 檔） | 6pre inode 124696053 / 62,644 B / mtime=birth=ctime 23:17:28；**6post inode 124696180 / 66,686 B / 23:18:58**；5rpre 18:32:32；**5rpost 18:43:22**；全部 nlink=1 | 兩個不同建立時間（18:43 vs 23:18）；非 `cp -p`（否則會保留 18:43）；非 hardlink |
| sha / `cmp` | 6post 與 5rpost 皆 `4cb8a6b4…`（cmp identical）；6pre `3dd1a3bf…` 與 5rpre `3d926e7d…` 不同（首個差異 byte 8661） | 位元相同是事實且 attempt-06 ledger event 7 自己揭露；pre 兩檔確為不同影像 |
| ledger event 7 | `/tmp/route6_frame_post.jpg` 66,686 B、[327,643]、`4cb8a6b4…`、23:18:58..23:19:07 | 帳實相符 |
| ledger（attempt-05 event 12） | 同一 sha、同一 bytes、post_ax `e17385e3…`（232 B）；其 v3 判決 `TARGET_MISMATCH`、count 讀成 `75`、changed_fraction 0.646749 | attempt-05 確實已開相簿，只是讀錯張數（讀取層問題） |
| 我自己的 Pillow 重算（凍結規則：L 轉灰、`abs(diff) > 12`） | **changed_pixels 131,493 / fraction 0.62538 / bbox [12,9,314,643]**（131493/210261=0.625379885…） | 完全重現 S5 數字；`>=12` 會變 132,640（0.630835）、RGB 逐通道會變 141,663，證明記的是凍結規則本值 |
| pre 幀差異性質 | 6pre vs 5rpre：109,137 px（0.519055）；垂直位移 dy=26 時 MAD 2.140（dy=0 時 54.494）；卡標題中心 460→482，兩次 click [29,460] vs [27,482] | 兩次 pre 是「清單被捲動位移」的真實畫面，非同檔重用 |
| **執行環境 journal（獨立於路線作者）** | attempt-06：`rollout-2026-09-17T23-14-51…jsonl` L266 ts=15:18:58.493Z `getScreenshot` → `writeFileSync("/tmp/route6_frame_post.jpg", shot)`，L269 輸出 `saved post frame bytes=66686`；attempt-05：`rollout-2026-09-16T19-28-38…jsonl` L7719 ts=10:43:21.711Z click[29,460]＋`getScreenshot`，L7722 回報 `shotBytes 66686 / postSha 4cb8a6b4…` | **兩次都是當時的真擷取**；位元相同是因為畫面內容（同相簿、窗框原點皆 [0,78]、擷取不含游標、327×643 窗內無時鐘、相簿視圖與清單捲動無關）逐像素一致 |
| journal 內有無複製 | 對兩條 post 路徑的寫入只有上述兩個 `writeFileSync`；未見 `cp/mv/ditto/rsync/install` | 未發現複製操作（且 23:46 檢查時 mtime 仍為 23:18:58，未被重寫） |
| 純檔案鑑識極限 | EXIF 無 DateTime（ExifIFD 僅 0xA002/0xA003=327×643）；ICC=Apple「Color LCD」；`com.apple.provenance` 在兩個 run 的 6 個 /tmp 檔皆為同一 token | **UNKNOWN（R1-13）**：無內嵌時間戳時，純離線檔案鑑識無法區分「真截圖」與「同時刻覆寫的複製」；此點由 journal 佐證補上 |
| attempt-05 凍結件完整 | `album-open-verify.json` sha `ffa5d963…`、verdict `TARGET_MISMATCH`、mtime 18:43、僅 1 個 commit（e53f67b 18:46:53）；attempt-06 收尾 commit e1658b7 未觸及任何 attempt-05 路徑；git status clean | 未被 attempt-06 覆寫 |

### R1 判讀（不預設結論後的結果）

- mtime／ledger 時序／pre 不同三類證據：全部指向「同一畫面、兩次獨立真截圖」；但三類都不足以單獨排除「不保留時間的複製」。
- 決定性補強來自 **執行環境 journal**：兩次 post 檔各由一次 live `getScreenshot()` 寫出，且 attempt-06 那次寫入 66,686 B 與現存檔案一致（`fs.writeFileSync` 直接寫入該 buffer）。
- 因此 R1 結論：**真截圖（SUPPORTED，非僅未發現反證）**；無偽造、無沿用、無誤導跡象。

## 風險 2：S6 `NO_ELLIPSIS_FOUND` 的幾何與決定性

- 凍結 v4 `locate_album_ellipsis.py` 對 `/tmp/route6_frame_post.jpg` 重放 3 次：**exit 3 / `NO_ELLIPSIS_FOUND`**，三次 stdout sha256 皆 `433e8693b1e23336628fab919042eca2c4903b0476c5a5ef22ff15f7d74edfb6`，與凍結 `attempt-06/album-ellipsis-locate.json` 位元相同（完全決定性）。
- 以 journal 記錄的原始 argv（`--expect-group-title 「旻謙允禎成長日記」`）再跑一次：仍 exit 3、位元相同。**附帶發現**：工具只去空白、不去括號，因此括號形式永遠無法匹配 OCR token；本幀本來就看不到群組標題（`group_title_bbox: null`）所以無影響，但這是潛在的參數銳利度問題（非本波錯誤宣稱）。
- 三點普查（`census`: rows 643 / flat_rows 283 / marked_pixels 8139 / large_components 58；58 個 dot 連通塊）：本幀共 **6 組三點候選**：

| # | region | 中點 (cx,cy) | 三點 (cx,cy)×3 | 被拒原因 |
|---|---|---|---|---|
| 1 | above_album_title_band | (304.5, 49.5) | (304.5,44.0)(304.5,49.5)(304.5,55.0) | 不在 band y[77..121] 內（非文字、無 OCR 阻擋） |
| 2 | inside_text | (21.0, 126.0) | (19.5,122.0)(21.0,126.0)(19.8,129.8) | 可讀多字 token `57張照片` conf 1.0 |
| 3 | inside_text | (72.6, 144.5) | (73.0,141.0)(72.6,144.5)(73.0,148.7) | `2024.05.18` conf 1.0 |
| 4 | inside_text | (20.7, 144.7) | (18.2,141.7)(20.7,144.7)(18.5,148.5) | `2024.05.18` conf 1.0 |
| 5 | inside_text | (54.0, 145.0) | (52.0,142.0)(54.0,145.0)(56.0,148.0) | `2024.05.18` conf 1.0 |
| 6 | inside_text | (54.0, 145.0) | (52.0,142.0)(54.0,145.0)(51.0,149.0) | `2024.05.18` conf 1.0 |

- `album_title_band = {x0:206, x1:326, y0:77, y1:121}`（由 S5 標題 bbox [15,83,204,111] 推得）；band 內合格候選 = **0**。
- 我另做原始像素普查（row median、flat_tol 25、flat_fraction 0.6、delta 45）：band [206..326]×[77..121] 內 marked pixels = **0**；且候選確實存在——x=304–305 有三個小連通塊 y43–45 / y49–50 / y54–56（垂直 ⋮ 字形，ASCII map 已存於執行輸出）。
- 與 band 上緣距離：dot cy 44.0 → 33.0 px、49.5 → **27.5 px**、55.0 → 22.0 px（中點在 band 上緣之上 27.5 px；候選 cx 在 band x 範圍內）。
- 另兩支 v4 工具重放（各 2 次，共 4 次）：`locate_album_card.py` → exit 0 / `ELIGIBLE` / click_point **[27,482]** / count `57` `MATCH`（sha `b822012d…`）；`verify_album_open.py` → exit 0 / `ALBUM_OPEN_VERIFIED` / count `57` / `post_ocr_words_seen` 含 **57張照片**（sha `a1e5fa49…`）。全部與凍結 JSON 位元相同。
- reader block：三支 v4 JSON 皆有 `reader.helper.source_sha256 = 4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32`、binary `c7087d98…`；helper 實體 `/var/folders/0r/…/vision_ocr_v4_build/vision_ocr` **存在**（67,200 B），未觸發 fail-closed。
- journal argv 交叉核對：L252（23:18:35 卡片定位）、L280（23:19:13 開簿驗證 `--delta 12`）、L287（23:19:18 ⋮ 定位 `--title-bbox 15,83,204,111`）與 runbook／execution-rev22.md 記載一致。

### R2 關鍵判讀：讀取能力 vs 規則幾何

- **屬「規則幾何」**：停止來自凍結規則的 band 判定（要求 ⋮ 與標題同一列、且在標題右方）；本幀唯一的非文字 ⋮ 字形在該列帶之上（中點高 27.5 px），band 內為 0。
- **不是讀取能力問題**：同一 run 中 reader 正常（標題 conf 1.0、張數 `57` MATCH、`57張照片` conf 1.0、58 個 dot 塊），且未出現任何 reader 失敗路徑；attempt-05 的 `75` 才是讀取層問題。
- **本波無法判定（UNKNOWN）**：x≈304.5、y≈44–55 那個 ⋮ 究竟是不是「相簿層級選單」——本波從未點擊／hover、也未開任何選單；LINE 是否只在 hover 才顯示相簿層級 ⋮、或是否根本沒有可達路徑，現有證據無法回答。

## 不確定處（明確列出）

1. UNKNOWN：唯一 ⋮ 字形（x 304.5, dots y 44.0/49.5/55.0）的身分（是否為相簿層級選單）——未點擊、未 hover、未開選單。
2. UNKNOWN：此凍結 band 規則是否可達 LINE 相簿層級選單的真實位置（可能需 hover 或另一列），本波無證據。
3. 潛在（未觸發）：`--expect-group-title 「…」` 括號形式永不匹配（工具只去空白）；本幀無群組標題故無影響。
4. 限度：no-copy 檢查只覆蓋 Codex session store；未被記錄的程序所為之複製無法單憑日誌排除（但 mtime 23:18:58 未再變動、且 journal 有真擷取紀錄，無任何可疑跡象）。
5. 註記：attempt-05 的 journal 落在 2026-09-16 起始的長 session 檔（非 09-17 目錄），僅做日期範圍搜尋會漏掉。

## 最有價值的一個發現

執行環境自身 journal 對「兩張 post 幀」各有一筆 live `getScreenshot()` 擷取紀錄（attempt-06：23:18:58.493Z，shot bytes **66686**；attempt-05：18:43:21.7Z，`postSha 4cb8a6b4…`）——這是路線作者之外、機器自動寫下的來源證據，把「位元相同」從可疑訊號轉成「同一畫面被兩次真擷取」的可證事實。

## 重放指令（唯讀；stdout 直接與凍結 JSON diff，不落任何成品）

```
/opt/homebrew/bin/python3 -B evidence/20260916-route/tools/v4/locate_album_ellipsis.py /tmp/route6_frame_post.jpg \
  --expect-start 2024/05/13 --expect-end 2024/05/17 --title-bbox 15,83,204,111 --expect-group-title 旻謙允禎成長日記
/opt/homebrew/bin/python3 -B evidence/20260916-route/tools/v4/verify_album_open.py /tmp/route6_frame_pre.jpg /tmp/route6_frame_post.jpg \
  --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57 --delta 12
/opt/homebrew/bin/python3 -B evidence/20260916-route/tools/v4/locate_album_card.py /tmp/route6_frame_pre.jpg \
  --expect-start 2024/05/13 --expect-end 2024/05/17 --expect-count 57
```

- 重放輸出 sha256：ellipsis `433e8693…`、verify `a1e5fa49…`、card `b822012d…`（皆等於凍結成品檔的 sha256）。
