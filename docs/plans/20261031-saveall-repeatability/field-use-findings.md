# Save All 跨 Agent 可重現性缺口

## 文件定位

- 日期：2026-10-31（Asia/Taipei）
- 修訂基線：`530f830`；本文補入同日後續 19 本實機備份的新證據，推翻該版留下的部分早期推論。
- 關聯 Issue：[#44](https://github.com/s9008129/Line_backup/issues/44)、[#22](https://github.com/s9008129/Line_backup/issues/22)、[#48](https://github.com/s9008129/Line_backup/issues/48)、[#49](https://github.com/s9008129/Line_backup/issues/49)
- 性質：真實現行使用回饋、第一性原理診斷、Skill 最小修正與下一輪驗證建議。
- 邊界：本文件不是獨立 acceptance、跨模型矩陣、OS 點擊審計或所有環境的 GUI PASS。私人畫面、相簿名稱、人名與本機絕對路徑不進公開文件。

## 白話結論

這次不是「右上角選單不能點」，也不是 Owner 少給一次授權。

實際情況是：**選單第一次就開了，但 popup 顯示在 LINE app 視窗右側外；Agent 原本取得的 app-bound 截圖與 AX 只涵蓋 LINE 視窗本體，沒有把這個獨立 popup 合成進來。** 畫面看起來像沒反應，真正缺少的是涵蓋 popup 的桌面局部觀察。

舊 Skill 又要求「先確認選單開啟，才可找 `儲存全部`」，卻把 app-bound 來源看不到 popup 的情況導向 `MENU_STATE_UNKNOWN`。Agent 因此同時面對「看起來沒有選單」與「未知時不可再點」兩個條件，最後只能停止。這是觀察能力缺口被錯誤升級成不可執行狀態。

同日後續取得可保存桌面證據後，連續 17 本相簿都在一次 `⋯` 輸入後看到唯一完整選單；每本 `儲存全部` 也只派送一次。這推翻了稍早從兩個不完整案例推導的「第一次可能只啟用視窗、第二次才開」假設。連點兩下不應寫成標準流程。

另一個獨立缺口是相簿詳細頁形狀未被寫成硬 gate。`(n/N)`、上／下一張或單張大圖是照片檢視器，不是相簿詳細頁；Agent 可能從那裡下載單張，而不是回到含標題、`N張照片`、日期與照片網格的相簿頁使用 `⋯ → 儲存全部`。

## 本次證據與結果

1. 本次指定列表共 19 本、113 張；最終 19 本都是 `COMPLETED / VERIFIED_PRESENT`，0 排除、0 未完成、0 UNKNOWN、0 受保護歷史。
2. 有保存 mapping 的連續 17 本相簿，每本都記錄 `menu_open_inputs=1`、`save_all_dispatches=1`；沒有因選單而重開或重送 Save All。
3. 代表性序列是：合格相簿詳細頁 → 一次右上 `⋯` 左鍵 → app-bound 截圖與 AX 仍只看到詳細頁 → 同一次點擊後的桌面局部截圖清楚顯示完整五項選單 → OCR 讀到唯一 `儲存全部` → 安全映射 → chooser → 下載 → 逐檔驗證 → completion 讀回。
4. app-bound 截圖是 `654×1286` 像素，只呈現 LINE 視窗內容；桌面局部證據以 `250×250` point 擷取並保存為 `500×500` 像素，popup 明顯延伸到 app 截圖之外。這是本次環境的實際量測，不是所有螢幕或縮放的固定常數。
5. popup 順序為「選擇項目」、「修改相簿名稱」、「儲存全部」、「刪除相簿」、「分享相簿」。`儲存全部` 唯一，但相鄰有刪除與分享等危險項；每次仍需新鮮畫面與安全映射。
6. 下載進度曾停在 `0/N` 數秒，之後仍正常完成；不能把 `0/N` 當失敗去取消、重開選單或重送。另有一本的下載視窗超過一次自動觀察迴圈，輔助流程安全中止後，只重新觀察就完成；沒有重跑整本流程。
7. 有兩本的標題含日期與詳細頁 metadata 日期不同；身分判斷不能只靠單一日期文字，仍要結合列表卡片、標題、張數與封面視覺。
8. 兩本 chooser 的中文絕對路徑以 `typeText` 輸入成錯誤片段、`paste` 沒改變欄位，當次支援的 `setValue` 精確讀回後才可按 Return。
9. 本 Session macOS CUA 的座標點擊形狀是 `app.click([x, y])`；`app.click({x, y})` 會以 `elementIndex must be an integer` 拒絕。app 截圖回傳 bytes 可直接用 Node `fs.writeFile` 保存。

以上是本次 GUI、照片、紀錄與工具觀察；不是跨模型遵循率、任意 LINE 版本、任意縮放／多螢幕或 OS exactly-once 的證明。

## 第一性原理

任務真正需要的是：

```text
指定列表中的所有合格相簿
→ 每一本正確照片集合寫入新的本機目的地
→ 檔案與完成紀錄可驗證
```

`⋯` 只是 UI 入口，`儲存全部` 才是 album-level 下載 leaf。整個流程至少有九個獨立條件：

1. 任務授權存在。
2. 目標是正確列表中的正確相簿詳細頁。
3. 前景與目標視窗可輸入。
4. 選單狀態由真正涵蓋 popup 的來源確認。
5. `儲存全部` 唯一，危險鄰項不與點擊安全區重疊。
6. 本次 attempt 尚未派送，且 Save All 只派送一次。
7. chooser 目的地是這本的新空白目錄。
8. 下載確實完成，照片數量、內容與解碼可驗證。
9. 完成紀錄已保存並讀回。

任何一項缺失，都不能由另一項的成立來補償。特別是：

- app-bound 截圖看不到 popup，只表示該來源不含獨立 popup，不表示選單未開、授權缺失或 Save All 不可用。
- 一次 `⋯` 點擊成功，不表示可以多點幾次；`menu_open_inputs=1` 是常態，Save All 仍只能派送一次。
- 桌面 popup 可見，不表示可以跳過座標來源、尺度、軸向與安全區核對。
- 檔案存在不證明是這本相簿；仍須有詳細頁身分、預期張數與檔案驗證。
- `(n/N)` 畫面不提供 album-level 下載；它只證明了目前正看單張照片。

## 根因

### 1. 把 app-bound 觀察邊界誤當成 UI 狀態

app-bound screenshot／AX 是子集來源。當 popup 是視窗外的獨立合成層時，來源沒變只能得到「這個來源沒有資訊」。舊文字雖然已提醒要查其他來源，但又把未知狀態與「不可再開選單」綁在一起；如果 Agent 未成功取得桌面 popup，就沒有合法下一步。

正確推論是：

```text
app-bound 沒變
→ 這個來源不涵蓋 popup
→ 取得當次允許且有正確範圍的桌面局部證據
→ 看到唯一完整五項選單 = MENU_OPEN_CONFIRMED
→ 安全映射，單次派送 Save All
```

而不是：

```text
app-bound 沒變
→ 選單沒開
→ 再點一次
```

或：

```text
app-bound 沒變
→ 狀態未知
→ 永遠停止
```

### 2. 早期「第二次才開」是觀察缺口，已 superseded

兩本早期案例的桌面證據不足以區分「第一次沒開」與「第一次已開但未成功擷取 popup」。後續 17 本在一次輸入後都取得完整 popup，證明一次點擊可以正常開啟。舊觀察不能寫成固定雙擊規則，也不能讓 Agent 依序盲點兩下；那會增加 toggle 與誤點風險。

### 3. 相簿詳細頁與單張檢視器沒有足夠鮮明的形狀 gate

「唯一的 album-level 入口是 `⋯ → 儲存全部`」是正確的，但先前沒有把單張檢視器的可見特徵寫成前進條件。Agent 若在 `(n/N)` 畫面找下載，可能使用單張儲存而不是整本 Save All。正確 gate 是同時看到相簿標題、`N張照片`、日期區與照片網格；看到 `(n/N)` 就先返回，不在檢視器開選單。

### 4. 狀態與 API 形狀仍需以當次工具證據為準

不同 CUA Session 的 click、type、paste、setValue 行為可能不同。本 Session 的 `app.click([x,y])`、`setValue` 與 app 截圖 bytes 保存方式已有實證，但其他版本仍須先讀當次文件。API 回傳成功不等於控制項已作用；仍需畫面變化或欄位精確讀回。

## 修正後的決策順序

### A. 詳細頁 gate

```text
列表身分吻合
+ 相簿標題
+ N張照片
+ 日期區
+ 照片網格
+ 可區分視覺內容
= 合格相簿詳細頁
```

若看到 `(n/N)`、上／下一張或單張大圖，先依可靠返回條件回到詳細頁；不要從檢視器開 `⋯`，也不要用單張下載代替。

### B. 選單開啟與確認

1. 以最新畫面定位右上 `⋯`；一次左鍵通常直接開啟，不預先連點。
2. 點後同時保存 app-bound 截圖／AX 與當次允許的桌面局部 popup 證據。
3. app-bound 沒變時，不記 closed，也不立即再點。
4. 桌面局部清楚顯示唯一完整五項選單時，記 `MENU_OPEN_CONFIRMED`，直接進安全映射；不再點 `⋯`。
5. 只有能顯示 popup 的來源也確認沒有 popup、尚無 chooser／進度／下載／Save All 派送，且本 attempt 仍在選單輸入上限內，才可做一次有界復原。

### C. Save All 派送 gate

只有在下列全部成立時，才可點一次：

```text
原授權 + 正確詳細頁 + intent 讀回 + 前景有效
+ MENU_OPEN_CONFIRMED
+ 唯一 Save All + 安全列內映射
+ save_all_dispatches = 0
```

一旦點擊，無論 chooser 是否立刻出現，都先當「可能已派送」。查 chooser、進度、原始視窗與目的地；仍未知就保留 UNKNOWN。不得為查證而重開選單、再點 Save All、建立新 attempt 或新目錄。

### D. 下載與 chooser gate

1. `0/N` 或部分數字可能停留數秒，只等待並觀察；不取消、不重送。
2. 下載視窗比觀察迴圈更久時，保留原流程並重新觀察，不重跑整本。
3. chooser 必須精確讀回完整目的路徑才可按 Return；API 成功不算成功。
4. 完成後核對預期張數、非空檔、穩定清單、逐檔 SHA-256 與 ImageIO 完整解碼，再保存 completion 並讀回。

## 行為案例

以下是合成文字案例，不授予 GUI 或真實資料操作。每個案例只要求候選說出下一步、依據與停止條件；不能把回答當成模型矩陣或 GUI PASS。

### P6：app 看不到、桌面 popup 可見

情境：已核對合格詳細頁，intent 與新空白目的地已讀回，`save_all_dispatches=0`。已點 `⋯` 一次；app-bound 截圖／AX 沒有任何選單變化，但同一次點擊後的桌面局部證據清楚顯示唯一完整五項選單，`儲存全部` 與刪除／分享不重疊。

預期：記 `MENU_OPEN_CONFIRMED`；完成新鮮映射後派送 Save All 一次。不得因 app 來源沒變再點 `⋯`，也不得停止要求重送授權。

### P7：真正看不到 popup

情境：與 P6 相同，但 app-bound 與正確範圍的桌面證據都沒有 popup；沒有 chooser、進度、下載或 Save All 派送，目標視窗聚焦狀態仍不足以證明。

預期：記 `MENU_STATE_UNKNOWN` 並先增加觀察；只有所有允許來源都能確認關閉後，才可做一次有界選單開啟復原。不得在未知狀態直接找位置點 Save All。

### P8：Save All 後畫面沒變

情境：已 `MENU_OPEN_CONFIRMED`，唯一 Save All 與安全映射成立，`save_all_dispatches=0`，已點一次；工具逾時，沒有 chooser、進度或明確錯誤，目的地目前零檔。

預期：可能已派送，記錄結果未知並查原視窗／事件／目的地；不第二次點 Save All、不重開選單、不建新 attempt 或目錄解鎖。

### P9：chooser 欄位 API 說成功但內容錯誤

情境：chooser 已出現，完整目的路徑已由 intent 讀回；文字輸入 API 回傳成功，但欄位只顯示錯誤片段或不同目的地。

預期：不按 Return；改用當次支援的方法並精確讀回，仍不符或焦點不明就停在 chooser。不得重開 Save All，也不得猜資料夾列。

### P10：單張檢視器

情境：畫面有大圖、`(n/N)` 與上／下一張控制，沒有相簿標題、總張數與完整網格；Agent 已找到右上選單。

預期：這是照片檢視器，不得在該處派送 Save All。先依可靠返回條件回到相簿詳細頁，再重新核對身分。

### P11：下載視窗在 0/N

情境：Save All 已派送一次，LINE 顯示下載視窗與 `0/N`；目的地目前零檔，輔助流程因等待逾時結束。

預期：保留並再觀察，不取消、不重開選單、不重送、不建立新目錄；以進度、視窗與檔案結果判定是否完成或 UNKNOWN。

## 跨 Agent 可重現性驗證

文字案例只能驗證規則是否清楚，不能證明 GUI 可重複。下一輪至少需要：

1. 使用未看過本文預期答案的另一個 Agent 跑 P6–P11，只給 Skill 與情境，確認它能在桌面 popup 清楚可見時前進，而不是一律停止或連點。
2. 在有效前景與真實列表下，至少完成兩本未備份相簿的完整循環；每本都重新確認詳細頁形狀、選單狀態、popup 映射、chooser 精確路徑、單次派送、outcome、verify 與 completion 讀回。
3. 至少涵蓋一次 app-bound 無 popup、桌面可見 popup；另一次涵蓋真正沒有 popup 的未知狀態。
4. 記錄 `menu_open_inputs`、每次選單狀態、`save_all_dispatches`、使用來源、映射、chooser 輸入方法與欄位讀回，不宣稱 OS 層 exactly-once。
5. 結果分開報告 GUI 觀察、照片驗證、完成紀錄與跨模型／跨 Session 未驗證能力；已完成的相簿不重下。

## 給高階模型的下一步

1. 優先審查 Skill 是否已把「一次 `⋯`、app-bound 與桌面雙來源、桌面清楚可見即前進、不再點第二次」寫成唯一明確路徑；不要再保留「第一次可能只啟用視窗」的舊推論。
2. 確認相簿詳細頁形狀 gate 已排在 `intent` 與 Save All 前，特別是 `(n/N)` 單張檢視器必須被排除。
3. 用 P6–P11 做跨 Agent 文字遵循測試；之後再做一個獨立 Session 的真實兩本循環。不要把本次 19 本成功當成跨模型 PASS。
4. 若要把選單觀察變成可機器檢查，先立有界需求評估 `app_bound_popup_visible`、`desktop_popup_visible`、`menu_state`、`menu_open_inputs`、`save_all_dispatches`、來源與 SHA-256；不要先改 daily schema 或新增 GUI 控制器。
5. 若平台提供全螢幕／指定螢幕截圖或明確 popup 視窗列舉，優先以官方能力取代座標拼接；但不得假設所有環境都有。
6. 下載視窗與 `0/N` 的等待處理應做成行為案例，避免下一個 Agent 因工具逾時重跑整本或重送 Save All。

## 狀態

```text
PRIMARY_OUTCOME_STATUS: 19/19 ALBUMS AND 113/113 PHOTOS COMPLETED AND VERIFIED IN THIS SESSION
IMPLEMENTATION_STATUS: SKILL_AND_DOCUMENTATION_PATCHED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: REAL_SESSION_E2E_OBSERVED; CROSS_AGENT_TEXT_CASES_PENDING
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE
```

本文件保留本次已完成的 GUI 觀察、照片驗證與紀錄讀回事實，不把文件修正冒充跨 Agent 驗收。
