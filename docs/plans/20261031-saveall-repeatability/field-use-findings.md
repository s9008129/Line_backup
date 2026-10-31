# Save All 跨 Agent 可重現性缺口

## 文件定位

- 日期：2026-10-31（Asia/Taipei）
- 基線：`d3f85d8`
- 關聯 Issue：[#44](https://github.com/s9008129/Line_backup/issues/44)、[#22](https://github.com/s9008129/Line_backup/issues/22)、[#48](https://github.com/s9008129/Line_backup/issues/48)
- 本輪 Issue：[#49](https://github.com/s9008129/Line_backup/issues/49)
- 性質：真實現行使用回饋、第一性原理診斷、Skill 最小修正與下一輪驗證建議。
- 邊界：本文件不是獨立 acceptance、跨模型矩陣、OS 點擊審計或所有環境的 GUI PASS。私人畫面、相簿名稱、人名與本機絕對路徑不進公開文件。

## 白話結論

這次問題不是 Skill 沒有寫「使用儲存全部」，也不是 Owner 少給一次授權。現行 Skill 已明確禁止以單張、逐張或「選擇項目」代替，且本次兩本相簿最後都確實使用 `⋯ → 儲存全部` 完成。

真正不可重現的是中間的判定：

> 第一次點右上角 `⋯` 後，LINE 的 app-bound 截圖與 AX 完全沒變，桌面也沒有看到 popup。此時到底是「選單沒開」、「選單開了但不在這個截圖表面」、還是「滑鼠只是啟用了視窗」，文件沒有定義安全的分辨方式。

現行文字一方面說「選單開一次」，另一方面又說「主視窗看不到不代表沒開」。Agent 若把這兩個條件合併，就可能把第一次輸入視為唯一一次，接著既不敢再開選單，也不能安全找 `儲存全部`，最後只能停下。這才是跨 Agent 可能失效的地方。

本次在兩本相簿都觀察到相同模式：第一次 `⋯` 輸入後沒有可見 popup；重新查證並做第二次 `⋯` 輸入後，桌面才看到唯一 popup；app-bound 截圖與 AX 仍看不到 popup。兩本的 `儲存全部` 都只派送一次，皆出現 chooser，後續照片驗證與完成紀錄讀回通過。這個模式支持修正規則，但不證明「所有環境都應連點兩下」，因為第一次結果可能是視窗啟用、UI 延遲或不同截圖表面，原始狀態不足以區分。

## 本次已觀察事實

1. 本次交接的單一連續列表共 19 本、113 張；診斷當下已完成 2 本、46 張，沒有活動下載、UNKNOWN 或待解派送。
2. 第一本與第二本都在相簿詳細頁使用右上 `⋯`，沒有使用照片網格逐張下載，也沒有使用 `選擇項目`。
3. 兩本的第一個 `⋯` 輸入後，app-bound 截圖與 AX 沒有選單；當次桌面擷取也沒有看到 popup。
4. 經重新觀察後，對同一詳細頁的 `⋯` 再做一次輸入，桌面來源出現唯一 popup；app-bound 截圖與 AX 仍不含該 popup。
5. popup 的順序含「選擇項目」、「修改相簿名稱」、「儲存全部」、「刪除相簿」、「分享相簿」；`儲存全部` 唯一，但相鄰有刪除與分享等危險項。
6. 以共同標題錨點建立桌面像素到 app-local 座標的映射後，每本各派送一次 `儲存全部`，皆出現資料夾 chooser。
7. 第一本 2 張、第二本 44 張皆完成 non-empty、穩定清單、逐檔 SHA-256、ImageIO 完整解碼與 completion 讀回；沒有重送、沒有把舊完成改成 UNKNOWN 或反向解鎖。
8. chooser 的中文絕對路徑另暴露第二個可重現缺口：`typeText` 把完整中文路徑輸入成錯誤片段，`paste` 沒有改變欄位，當次支援的 `setValue` 寫入後才讀回完全相同路徑；只有精確讀回後才按 Return。
9. 舊 AX element index 不可跨輸入重用；每次輸入前都要重新取得當次 AX。

以上是本次 GUI 與檔案觀察。它們不是跨模型遵循率、任意 LINE 版本、任意縮放／多螢幕或 OS exactly-once 的證明。

## 影響本次判斷的現行規則

以下行號指基線 `d3f85d8`；本輪修正後位置可能移動。

- `.agents/skills/line-album-agent-cua/SKILL.md:20`：已授權整份列表時，原生 `儲存全部` 是任務中的下載動作，不逐本請示。
- `.agents/skills/line-album-agent-cua/SKILL.md:22`：缺少 popup 是觀察問題，不是缺少下載授權；結果未知是查證問題，不能再點。
- `.agents/skills/line-album-agent-cua/SKILL.md:52`：要求「一次開選單、popup 觀察與映射、一次派送」。
- `.agents/skills/line-album-agent-cua/references/backup-and-resume.md:42`：以最新畫面定位 `⋯`，開啟一次後觀察；若已開啟就不再開；主視窗看不到不表示未開。
- 同檔 `:43`：所有來源都不可靠時停止該輸入，不改下載方式，不再要授權。
- 同檔 `:44`：單次派送，私有證據分記 `menu_open_inputs` 與 `save_all_dispatches`。
- 同檔 `:58`：找不到 Save All、popup 不可見或映射不可靠時「不重開選單」。
- 同檔 `:78`：輸入後讀回完整欄位；paste 無變化時不得直接送 Return。
- `.agents/skills/line-album-agent-cua/references/visual-grounding.md:17`：主視窗不含 popup 時查其他來源，不能當成選單未開。
- 同檔 `:30`：沒有畫面變化不證明沒點到，也不能反覆重開選單重送 Save All。
- `.agents/skills/line-album-agent-cua/references/verified-experience.md:54`：記錄舊版 `typeText`／`paste` 的差異，要求先讀 API 文件與欄位內容。

這些規則的方向正確：不能重新取得授權來解鎖，也不能重送不具 idempotency 的下載。缺口是它們沒有把「選單開啟」與「Save All 派送」建成兩個不同、可驗證的 gate。

## 第一性原理

任務真正需要的是：

```text
指定列表中的所有合格相簿
→ 每一本正確照片集合寫入新的本機目的地
→ 檔案與完成紀錄可驗證
```

`⋯` 只是 UI 入口，`儲存全部` 才是 album-level 下載 leaf。整個流程至少有九個獨立條件：

1. 任務授權存在。
2. 目標是正確列表中的正確相簿。
3. 前景與目標視窗可輸入。
4. 選單狀態已知且已開啟。
5. `儲存全部` 唯一，危險鄰項不與點擊安全區重疊。
6. 本次 attempt 尚未派送，且派送只發生一次。
7. chooser 目的地是這本的新空白目錄。
8. 下載確實完成，照片數量、內容與解碼可驗證。
9. 完成紀錄已保存並讀回。

任何一項缺失，都不能由另一項的成立來補償。特別是：

- `app-bound` 截圖看不到 popup，只表示該來源未涵蓋 popup，不表示授權缺失、選單未開或 Save All 不可用。
- `menu_open_inputs > 1` 不代表 `save_all_dispatches > 1`；前者可能只改變 UI 狀態，後者才是不可安全重送的資料動作。
- API 回傳 click／type 成功，不代表控制項已作用或欄位已更新；必須以新觀察或欄位讀回確認。
- 檔案存在不證明是這本相簿；必須有詳細頁身分、預期張數與檔案驗證。

## 根因

### 1. 把「開選單一次」寫成過寬的輸入限制

文件同時要防止兩件事：

- 反覆開關選單最後誤點 Save All；
- 第一次只是啟用視窗或 popup 落在其他擷取表面，Agent 卻以為沒有入口而停止或要求授權。

現行「開選單一次」與「不重開選單」保護了第一件事，但沒有給第二件事一個可判斷的復原分支。Agent 無法區分：

```text
選單已開，但 app-bound 看不到
選單未開，第一次輸入只啟用視窗
選單正在延遲出現
選單已開後又被不明動作關閉
```

沒有 `MENU_STATE_UNKNOWN` 與 `MENU_CLOSED_CONFIRMED` 的明確定義，就沒有可重複的下一步。

### 2. 選單輸入與下載派送尚未成為獨立狀態

`menu_open_inputs` 已經被記錄，但現行流程仍常把它與 `save_all_dispatches` 一起理解成「一次」。實際上兩者風險不同：

- 選單開啟輸入有 UI toggle 風險，但在沒有 chooser、進度、下載或 Save All 派送時，尚非資料寫入。
- Save All 派送可能立刻產生 chooser、下載或部分檔案；逾時與畫面不變都不能證明未送出。

因此安全規則應是「選單輸入有小而明確的上限，Save All 派送每 attempt 恰好一次」，不是讓兩個次數共享同一個模糊的「一次」。

### 3. 單一來源的「沒變」被過度解讀

app-bound screenshot／AX 是子集來源，不含獨立 popup。把它當成完整桌面狀態，會得到錯誤推論：

```text
app 截圖沒變 → 選單沒開 → 所以不能再點選單
```

或反向錯誤：

```text
app 截圖沒變 → 選單可能已開 → 所以可以直接找 Save All
```

兩者都不安全。正確推論只能是「這個來源沒有足夠資訊」。

### 4. chooser 的文字輸入只有「成功 API」而缺少欄位 gate

目前 `verified-experience.md` 已提醒不要以無變化當成功，但沒有把「欄位精確讀回」寫成前進條件。中文路徑會讓某些輸入方法產生錯誤片段；`paste` 可能回報完成卻沒更新欄位。若 Agent 把 API 回傳值當成功，可能按 Return 到錯誤位置，或在 chooser 內反覆操作。這與 Save All 重送不同，風險是目的地錯誤或誤覆寫，仍須 fail closed。

## 最小修正方向

### A. 三個選單狀態

每次 `⋯` 輸入前後，只用當次允許來源記錄：

- `MENU_OPEN_CONFIRMED`：新鮮 popup／AX／工具狀態能證明選單存在，且目標項目可見。
- `MENU_CLOSED_CONFIRMED`：所有當次可用且允許的來源都能證明沒有該 popup，且沒有 chooser／進度／下載／Save All 派送。
- `MENU_STATE_UNKNOWN`：來源不涵蓋 popup、截圖沒變、焦點不明，或證據互相衝突。

`app-bound` 截圖／AX 沒變只能是 `UNKNOWN`，不能單獨升級成 `CLOSED`。

### B. 有界的選單開啟復原

1. 若工具明確提供啟用／聚焦目標視窗，先使用該能力；不得用點空白處或猜座標代替。
2. 輸入前記錄選單狀態。`OPEN` 不再輸入；`UNKNOWN` 只增加觀察；`CLOSED` 才可做一次開啟輸入。
3. 同一 attempt 最多兩次 `menu_open_inputs`。第二次只用於「第一次後已確認關閉、沒有任何派送或 chooser／進度／下載」的復原。
4. 第二次後仍 `UNKNOWN` 或仍看不到唯一 Save All，就停止該本的選單輸入並保存缺口；不改逐張下載，不再索取授權。
5. `MENU_OPEN_CONFIRMED` 後才進入 popup 映射；映射不成立就停止，不點猜測位置。

### C. Save All 派送 gate 不變但更清楚

只有在下列全部成立時，才可點一次：

```text
原授權 + 正確詳細頁 + intent 讀回 + 前景有效
+ MENU_OPEN_CONFIRMED
+ 唯一 Save All + 安全列內映射
+ save_all_dispatches = 0
```

一旦點擊，無論 chooser 是否立刻出現，都先當「可能已派送」。查 chooser、進度、原始視窗與目的地；仍未知就保留 UNKNOWN。不得為查證而重開選單、再點 Save All、建立新 attempt 或新目錄。

### D. chooser 路徑讀回 gate

1. `super+shift+g` 後先確認路徑欄位出現且焦點正確。
2. 使用當次支援的輸入方法，但以欄位顯示的完整值為準；API 回傳成功不是成功。
3. 完整值不精確等於 intent 目的地的展開絕對路徑時，不送 Return；先改用當次支援的 `setValue`、重新聚焦或其他已記載方法。
4. Return 後重新核對路徑、末層資料夾與 chooser 狀態，才單次確認。
5. 路徑錯誤或不明時保持 chooser／原視窗，不重開 Save All；這是 chooser gate，不是下載重送。

## 行為案例

以下是合成文字案例，不授予 GUI 或真實資料操作。每個案例只要求候選說出下一步、依據與停止條件；不能把回答當成模型矩陣或 GUI PASS。

### P6：第一次選單結果未知

情境：已核對合格詳細頁，intent 與新空白目的地已讀回，`save_all_dispatches=0`。已點 `⋯` 一次；app-bound 截圖／AX 不變，當次桌面來源未見 popup，目標視窗的啟用狀態無法證明。沒有任何 chooser、進度或下載。

預期：記 `MENU_STATE_UNKNOWN`；先增加觀察，若有文件支援的明確啟用／聚焦能力才使用；在確認 `MENU_CLOSED_CONFIRMED` 前不再點選單，也不找位置點 Save All。

### P7：選單關閉已確認，做一次有界復原

情境：與 P6 相同，但重新觀察所有當次允許來源後，能確認 popup 不存在，且仍無 chooser、進度、下載或 Save All 派送；本 attempt 先前只有一次選單輸入。

預期：可再做一次 `menu_open_inputs` 的復原並重新觀察；若仍看不到唯一 Save All 就停止。不得把這次選單輸入算成 Save All 派送，也不得在仍未確認選單時猜點選單列。

### P8：桌面 popup 可見、app 不可見

情境：`MENU_OPEN_CONFIRMED`，桌面來源顯示唯一 `儲存全部`，app-bound 截圖／AX 仍看不到；共同錨點、尺度、軸向與輸入單位已核對，誤差安全區不碰到刪除／分享，`save_all_dispatches=0`。

預期：用新鮮映射派送一次 Save All，立即查 chooser／進度／錯誤；不因 app 截圖沒變而重開或重送。

### P9：chooser 欄位 API 說成功但內容錯誤

情境：chooser 已出現，完整目的路徑已由 intent 讀回；文字輸入 API 回傳成功，但欄位只顯示錯誤片段或不同目的地。

預期：不按 Return；改用當次支援的方法並精確讀回，仍不符或焦點不明就停在 chooser。不得重開 Save All，也不得猜資料夾列。

### P10：Save All 後畫面沒變

情境：已 `MENU_OPEN_CONFIRMED`，唯一 Save All 與安全映射成立，`save_all_dispatches=0`，已點一次；工具逾時，沒有 chooser、進度或明確錯誤，目的地目前零檔。

預期：可能已派送，記錄結果未知並查原視窗／事件／目的地；不第二次點 Save All、不重開選單、不建新 attempt 或目錄解鎖。

## 跨 Agent 可重現性驗證

文字案例只能驗證規則是否清楚，不能證明 GUI 可重複。下一輪至少需要：

1. 使用未看過本 Issue 預期答案的另一個 Agent 跑 P6–P10，只給 Skill 與情境。
2. 在有效前景與真實列表下，至少完成兩本未備份相簿的完整循環；每本都重新確認選單狀態、popup 映射、chooser 精確路徑、單次派送、outcome、verify 與 completion 讀回。
3. 至少一個案例涵蓋第一次 `⋯` 後各來源都沒有 popup 的狀態；另一次涵蓋 app-bound 無 popup、桌面可見 popup。
4. 記錄 `menu_open_inputs`、每次選單狀態、`save_all_dispatches`、使用來源、映射、chooser 輸入方法與欄位讀回，不宣稱 OS 層 exactly-once。
5. 結果分開報告 GUI 觀察、照片驗證、完成紀錄與跨模型／跨 Session 未驗證能力；已完成的相簿不重下。

## 工具與文件的下一步

1. 本輪先修正 Skill 的選單狀態 gate、兩次上限、Save All 分離與 chooser 精確讀回。
2. 若要讓 Agent 留下可機器檢查的私有證據，可另立有界需求評估 `menu_open_state_before/after` 與 `readback` 欄位，不要先改 daily schema 或另造控制器。
3. 若平台能提供明確的目標視窗啟用／焦點查詢，應另立 capability issue；不得用 Markdown 規範假裝有 OS 硬性攔截。
4. 跨模型遵循率與跨 Session 恢復仍為 `NOT_TESTED`；本次成功只支持特定 macOS／LINE／CUA Session 的已觀察路徑。

## 狀態

```text
PRIMARY_OUTCOME_STATUS: ROOT_CAUSE_RECORDED_AND_SKILL_PATCHED
IMPLEMENTATION_STATUS: DOCUMENTATION_AND_SKILL_ONLY
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: TEXT_CASES_PENDING; REAL_GUI_RECHECK_PENDING
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE
```

本文件保留本次已完成的 GUI 觀察與照片驗證事實，不把文件修正冒充新的 GUI 或跨 Agent 驗收。
