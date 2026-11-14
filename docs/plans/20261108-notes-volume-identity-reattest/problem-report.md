# 問題提報單：記事本備份在 volume identity 變更後失去安全恢復入口

## 0. 提報摘要

### 一句話結論

本次失敗不是 LINE 下載按鈕或 chooser 失敗，而是 notes CLI 在建立恢復下載 intent 之前，將同一個正規路徑、同一個 inode 上的 `st_dev` 變化判定為 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED`；現行資料模型因此把合法的檔案系統 volume instance 變化視為目錄被替換，並在沒有 append-only 重新見證（reattest）入口的情況下永久停止。

這是一個**產品設計／恢復能力缺口**，不是單純的操作錯誤，也不是已證實的媒體損壞。失敗發生在 GUI 派送之前，因此本次沒有新增下載、沒有覆寫舊完成、沒有改寫 `UNKNOWN`。

### 提報分類

| 項目 | 判定 |
|---|---|
| 是否為 issue | **是**：可重現的日常備份／恢復阻塞 |
| issue 類型 | 檔案系統身分模型與 append-only 恢復協議缺口 |
| 失敗階段 | `restart confirm` 與 recovery scan 之後、第一個 v3 `intent` 之前 |
| 本次 GUI 下載控制派送 | **0 次** |
| 已證實的資料損壞 | **沒有** |
| 是否 fail-closed | **是，且拒絕本身合理** |
| 是否應提報高階模型 | **是**；需要設計選擇，而非直接修資料 |
| 建議優先級 | **HIGH（可用性／恢復）**；不是資料外洩或已確認資料遺失 |

### 需要的決策

高階問題分析模型不需要先決定「要不要忽略 `st_dev`」。它需要回答：

1. 什麼才是本專案應持久保存的目錄／完成物身分？
2. 當路徑與 inode 相同、內容 witness 相同、但 volume device token 改變時，如何在不改寫歷史的前提下重新見證？
3. 重新見證如何與 `UNKNOWN`、`LOCAL_CHANGED`、pending naming、restart scope、completion 與舊 staging 分離？
4. 在空目錄、內容相同副本、inode 重用與 volume clone 等不可完全區分的邊界下，系統要承認哪一種風險模型？
5. 如何用可重播事件、精確 scope、一次性確認與 crash recovery，避免把安全例外變成無限重送？

---

## 1. 提報範圍與敏感資料處理

- 產品：LINE 記事本照片／影片備份，不是相簿流程。
- 程式：`src/line_backup_batch/notes.py` 與既有 notes 測試。
- 分支：`feature/line-notes-media`；本次分析不會合併 `master`。
- 分析基準：`3fdad13838ab309103ff287f6bf18464b526e97f`；工作樹在本提報建立前為乾淨狀態。
- 本提報只新增 Markdown 文件，不修改產品程式、不修改 ledger、不建立下載 intent、不操作 LINE、不下載媒體。
- 完整私有證據保存在專案內未被 Git 追蹤的任務目錄，使用 `<TASK_ID>`、`<PRIVATE_LEDGER>`、`<LIST_A>`、`<POST_A>`、`<MEDIA_A>` 等 placeholder 呈現；不提交真實群組名稱、人名、媒體檔名、帳本 ID、原始截圖或證據 blob。
- 所有「已完成／未知／已完成本機不可用」的判定，均以永久帳本的追加事件與當次 GUI／scan 證據分層呈現，不把單一 hash、檔名、日期或畫面文字當成身分。

### 證據層級

| 層級 | 本提報可主張的內容 | 不可替代的內容 |
|---|---|---|
| GUI `OBSERVED` | 當次畫面確有入口、viewer、影片時長、單一底部縮圖等觀察 | CLI 簿記 PASS、檔案解碼 PASS、服務端原始位元 |
| notes CLI 簿記 | ledger、scan、inventory、restart confirmation、intent 拒絕與摘要投影 | 真實下載成功、media bytes、完成驗收 |
| 檔案系統 witness | 同一路徑、inode、大小、時間戳、SHA-256 等可核對條件 | 服務端原檔、外部副本、未來不會被改寫 |
| ffmpeg／ImageIO | 指定本地檔案的解碼結果 | LINE 原始位元、來源仍存在、跨 Session E2E |
| Owner 口述 | 三次下載、群組內記事本數量等背景 | 自動成為某個 attempt 的終態證據 |

---

## 2. 使用者補充與口徑校準

Owner 補充了兩項背景事實：

1. 所稱「專案」實際上是 LINE 群組名稱，不是 Git repository 名稱。
2. 該 LINE 群組內有兩個記事本列表，每個列表各有一支影片需要下載；先前已執行三次下載。

這些陳述只作為 **Owner `OBSERVED` 的背景**，不能用來合併列表、取代當次 GUI 身分，或直接把某個下載次數寫成帳本事實。

### 目前可核對的三層數字

| 來源 | 數字／狀態 | 能支持什麼 |
|---|---|---|
| Owner 口述 | LINE 群組內 2 個記事本，各 1 支影片；曾執行 3 次下載 | 任務背景與可能的重複執行 |
| 本次 active list 的 recovery scan | 1 個列表、2 篇貼文、2 個 VIDEO、`scan_coverage=COMPLETE`、`NO_MEDIA=0` | 本次單一列表的來源盤點完整 |
| active list 永久帳本 | 2 個 intent；1 個舊完成、1 個 `UNKNOWN` attempt | 目前只能安全歸屬這兩個 intent |
| git notes ledger collection | 4 個歷史 ledger 目錄 | 不能推論 LINE 群組內有 4 個記事本，也不能把舊 ledger 合併 |

### 三次下載的未解對應

Owner 說曾下載三次，但目前 active list 的 ledger 只能看到兩個 intent。第三次下載可能來自：

- 另一個歷史列表；
- 同一媒體的一次未形成新 intent 的人工重複；
- 舊 attempt 的重試或錯誤操作；
- GUI 行為未被帳本捕獲。

目前沒有證據能把第三次下載唯一歸給 `<MEDIA_A>`、`<MEDIA_B>` 或其他 ledger。因此：

- 不把「三次」直接寫成第三個 attempt；
- 不用「兩個影片剛好兩次」推論舊 `UNKNOWN` 已被覆蓋；
- 不用群組內「2 本」推翻單一 active list 的「2 篇貼文」觀察；
- 保留為 `UNRESOLVED_OBSERVATION`，待未來有可歸屬的 receipt 或使用者再次交接時再核對。

**設計含義：** 身分與 attempt 必須由 ledger key、當次 scan、來源媒體與可歸屬 evidence 共同支持；口述次數只能協助發現歷史缺口，不能成為重送或解鎖依據。

---

## 3. 事實、推論與未知

### 3.1 已證實事實

1. 指定列表已完成入口核對、帳本綁定與 recovery scan；`scan_coverage=COMPLETE`，2 篇貼文均有 inventory，兩者各有一個 VIDEO。
2. 兩個 video viewer 均重新觀察到 `1/1` 與單一底部縮圖；兩個影片長度各有當次 viewer 觀察記錄，本文不複製原始值。
3. `restart preview` 曾回報 `RESTART_REQUIRED`，並產生 Owner 已明示同意過的 `restart_id` 與 `scope_digest`。
4. `restart confirm` 成功，之後建立了新的完整 recovery scan；確認與 scan 的簿記流程成立。
5. 第一個 v3 `intent --restart-id` 被 CLI 以 exit code 4 拒絕：
   - `status=REFUSED`
   - `reason=CURRENT_NOTES_LIST_DIRECTORY_CHANGED`
   - `dispatch_authorized=false`
6. 拒絕後 ledger 仍停在原本的 sequence；沒有新增 intent、沒有新增空白 staging，也沒有 GUI 下載控制派送。
7. 舊媒體 A 的 completion 仍在；其完成檔的 inode、大小與 SHA-256 與舊 completion 記錄一致。
8. 舊媒體 A 的目前 directory／file `st_dev` 已與舊 completion 記錄不同；因此摘要投影把它列為 `LOCAL_CHANGED`，即使內容 witness 未改變。
9. 媒體 B 仍保留舊 `UNKNOWN` attempt、舊 outcome 與舊空 staging；本次沒有把它重送或重新分類。
10. 同一正規路徑、同一 inode、非 symlink、目錄仍存在；差異常只出現在 device token。

### 3.2 合理推論

- `st_dev` 是掛載／volume instance 的命名空間標識，不是檔案內容或永久資料夾身分的等價物。macOS／APFS 環境在 remount、volume 重新掛載、系統重啟或類似 volume instance 變化後，同一個持久物件的 `st_dev` 可能改變。
- 現行程式將 `(st_dev, st_ino)` 當成不可分割的歷史身分，因而把「同一路徑、同一 inode、內容 witness 不變」的合法變化誤判成「目錄被替換」。
- 因為 `_restart_intent()` 在建立 staging 前先呼叫 `_require_current_list_directory()`，這個身分 gate 直接阻止了已確認的 restart 批次。
- `completion` 投影也會把舊 device 不一致視為 `LOCAL_CHANGED`；這是第二個獨立但同源的影響面。
- 拒絕是正確的 fail-closed 行為；問題在於沒有受支援的 reattestation 路徑，讓已核對的同一物件在新 volume token 下重新被見證。

### 3.3 尚未證實或未知

- 本次 `st_dev` 變化的精確外部事件（重新掛載、重開機、volume restore、外部工具改動或其他原因）尚未取得系統層級證據。
- 媒體 B 的舊 `UNKNOWN` 是否真的沒有在背景完成，仍未知；本次沒有新的可歸屬終結證據。
- 媒體 A 的完成檔是否就是服務端原始位元，仍不能由本地 SHA-256／解碼證明。
- 第三次下載的 attempt 歸屬未知。
- 若存在與舊目錄「位元完全相同」的 clone，單靠路徑、inode、內容 hash 或 device 是否足以區分，屬於風險模型問題；不能假設現有 witness 能證明「同一個 volume」。
- 空目錄沒有任何完成檔可作內容交叉見證；此時是否允許 reattestation，尚未有安全答案。

---

## 4. 事故重現與時間線

### 4.1 前置狀態

| 項目 | 狀態 |
|---|---|
| 指定來源 | 一個已交接的 LINE 記事本列表；當次畫面與帳本已核對 |
| 貼文 | 2 篇；每篇 inventory 與媒體 inventory 均已記錄 |
| 媒體 | 2 個 VIDEO；舊 A 完成、舊 B `UNKNOWN` |
| restart | 已預覽、已確認；Owner 已對精確 scope 明示同意 |
| recovery scan | 已重新完成，時間順序在 confirmation 之後 |
| local state | A 舊 completion 仍存在但投影為 `LOCAL_CHANGED`；B 為 `UNKNOWN` |

### 4.2 最小時間線

1. 核對 LINE 列表與 active ledger。
2. 執行 restart preview，列出兩支影片、舊版本與新 `versions/gNNNNNNNN/` 路徑。
3. Owner 對精確 `restart_id`／`scope_digest` 表達同意。
4. 執行 `restart confirm`；確認事件寫入。
5. 完成新的完整 recovery scan；兩篇貼文與兩個 VIDEO inventory 寫入。
6. 針對第一個媒體建立 v3 intent。
7. CLI 在 `_require_current_list_directory()` 發現目前 `st_dev !=` 舊 destination event 的 `directory_device`。
8. CLI 回傳 exit 4／`CURRENT_NOTES_LIST_DIRECTORY_CHANGED`／`dispatch_authorized=false`。
9. 程序停止；沒有建立 staging，沒有派送下載，也沒有進入 chooser。

### 4.3 最小重現命令形狀

以下只展示形狀，所有私有識別碼以 placeholder 表示：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes intent \
  --records-root <PRIVATE_LEDGER> \
  --session-id <SESSION_ID> \
  --media-key <MEDIA_KEY> \
  --restart-id <RESTART_ID>
```

實際結果：

```text
exit 4
status=REFUSED
reason=CURRENT_NOTES_LIST_DIRECTORY_CHANGED
dispatch_authorized=false
```

預期但未發生的後續：

- 新空白 `.line-notes-incoming-*` staging；
- 新的 v3 intent事件；
- 當次下載控制與 chooser；
- outcome／verify／candidate／activation／completion。

---

## 5. 第一性原理拆解：我們到底在保存什麼身分？

### 5.1 六種不可混用的身分

| 身分層 | 例子 | 用途 | 單獨足以認領歷史？ |
|---|---|---|---|
| 邏輯列表身分 | `list_key`、`local_list_id` | 跨 Session 找到同一份永久帳本 | 不能脫離入口與 context |
| 貼文身分 | `post_key` | 將卡片／文字／順序綁到同一貼文 | 不能只靠日期或標題 |
| 媒體身分 | `media_key` | 將 viewer／縮圖／來源順序綁到同一媒體 | 不能只靠檔案 hash |
| 路徑身分 | canonical absolute path | 找到目前物件的位置 | 路徑可被替換，不能單獨使用 |
| 檔案系統物件身分 | `(st_dev, st_ino)` | 偵測同一次掛載中的替換、symlink、inode 重用 | `st_dev` 非永久；不能單獨跨 remount |
| 內容身分 | 大小、時間戳、SHA-256、manifest、解碼結果 | 證明目前 bytes 與已知 witness 相符 | 不能證明服務端原始位元或「同一個 volume」 |

### 5.2 目前模型的隱含假設

現行 `directory_info()` 與 destination／completion／intent 驗證把 `(st_dev, st_ino)` 當成一種**跨時間不變的 directory identity**。這個假設在單一掛載期間通常有效，但對下列情境過強：

- APFS volume 被重新掛載；
- 系統重啟造成 volume instance token 改變；
- 外部磁碟重新連接；
- 系統還原或 volume 重建；
- 同一個持久物件被新的 mount namespace 看見。

`st_dev` 可以協助回答「目前這個 mount namespace 裡的物件是否仍是剛才那個物件？」但它不適合單獨回答「這個路徑在多年後仍代表同一個邏輯備份目錄嗎？」

### 5.3 安全的 identity invariant

一個可接受的 reattestation 設計，至少應滿足以下不變量：

1. **不覆寫歷史**：舊 destination、completion、intent、outcome、staging 與 `UNKNOWN` 全部保留。
2. **不改寫完成事實**：舊 completion 的成功與時間不變；目前本機可用性是重新計算的投影。
3. **不自動解鎖**：reattestation 只處理「同一物件的新 device token」，不自動清除 `UNKNOWN`、pending naming、`LOCAL_CHANGED` scope 外異常或 restart 授權限制。
4. **需要 witness**：不能只接受「路徑相同」或「new device 看起來合理」。
5. **有精確 scope**：一次事件只能涵蓋 preview 中列出的路徑與 witness，不得順便擴及另一個列表或另一個貼文。
6. **可重播且冪等**：同一 preview／confirmation 重送不得建立第二個事件或第二個 staging。
7. **失敗保持原狀**：任一 witness 不符就拒絕，且不留下半套新目錄、半套 candidate 或半套完成紀錄。
8. **風險要明說**：若 clone、inode 重用或空目錄無法被區分，設計必須承認限制，不能把「hash 相同」誇大成「同一個 volume」。

---

## 6. 現行機制的 failure chain

### 6.1 程式定位

| 位置 | 行為 | 影響 |
|---|---|---|
| `src/line_backup_batch/notes.py:200` `directory_info()` | 取得路徑的 `st_dev`、`st_ino`，並要求前後不變 | 建立 destination 時固化 device |
| `src/line_backup_batch/notes.py:620-700` `init()` | 將目錄 device／inode 寫入 `created` 事件 | 形成第一次永久 binding |
| `src/line_backup_batch/notes.py:2183` `_require_current_list_directory()` | 以目前 `st_dev`／`st_ino` 對比 destination state | `st_dev` 改變即拒絕 |
| `src/line_backup_batch/notes.py:3231` `_completion_availability()` | 對完成目錄與完成檔比對 device／inode／時間／hash | 舊完成可能被投影成 `LOCAL_CHANGED` |
| `src/line_backup_batch/notes.py:3076` `_candidate_file_availability()` | 對 restart candidate 做 device／inode／時間／hash 檢查 | 同一問題會延伸到 candidate |
| `src/line_backup_batch/notes.py:3711` `_restart_intent()` | 建立 v3 intent 前先呼叫 current list directory gate | 已確認 restart 批次無法開始 |
| `src/line_backup_batch/notes.py:4468` `_validate_staging()` | staging 也要求 intent 中的 device／inode | intent 前的身分錯誤無法局部繞過 |
| `src/line_backup_batch/notes.py:4660-4710` 發布／目錄進度 | 保存 target directory 的 device／inode | 同源影響 completion 與 publish |

### 6.2 失敗鏈

```text
同一個 canonical path
        +
同一個 inode
        +
已知完成檔的 inode／size／hash witness 相符
        +
volume instance 的 st_dev 改變
        ↓
current list directory 比對失敗
        ↓
CURRENT_NOTES_LIST_DIRECTORY_CHANGED
        ↓
v3 intent 不建立
        ↓
沒有新 staging、沒有 GUI 派送
```

### 6.3 為什麼不能直接忽略 `st_dev`

直接忽略 `st_dev` 會讓以下情況失去保護：

- 同一路徑被另一個 volume 的目錄替換；
- 目錄被刪除後重新建立；
- inode 被重用；
- 惡意或誤操作建立的 byte-identical clone；
- 舊 completion 目錄被搬走後以相同名稱重建；
- candidate 的來源與目前路徑不再是同一個物件。

因此正確方向不是「移除檢查」，而是「將 ephemeral device token 與 logical witness 分層，並追加一個有範圍、可重播、不可解鎖其他 blocker 的 reattestation」。

---

## 7. 為什麼目前的 fail-closed 反而是正確的一部分

本次拒絕同時保護了：

- 不把舊 completion 目錄的內容錯誤地當成新結果；
- 不因 restart 授權而跳過 `UNKNOWN` 的歷史；
- 不在 chooser 或 GUI 尚未核對前按第二次下載；
- 不把 `LOCAL_CHANGED` 直接改寫成 `VERIFIED_PRESENT`；
- 不把 `dispatch_authorized=false` 誤用成 GUI 授權；
- 不建立新的空白 staging 來偽裝舊交易已停止。

問題是：**安全拒絕沒有配套的可恢復狀態。** 現行 CLI 只有 `destination` 可追加新的目的地，但 `destination()` 會拒絕未解的 `UNKNOWN`／`LOCAL_CHANGED`，而且它建立的是新 root／新 list directory，不是同一路徑的 device reattestation。

因此目前可行的所有「繞過」都不安全：

| 工作方式 | 問題 |
|---|---|
| 手改 ledger 的 `directory_device` | 改寫歷史、無法重播、違反追加式事實來源 |
| 換 `--records-root` 或建空帳 | 分裂身分、丟失舊完成與 `UNKNOWN` |
| 換 `--photo-root` | 舊 completion 路徑不改；且 destination 不會解鎖 blocker |
| 直接重送 intent | 沒有新的合法 staging／witness，且可能造成重複下載 |
| 忽略 `st_dev` | 失去同路徑替換與 inode 重用保護 |
| 重新啟動整個列表、當成新列表 | 跨列表合併風險與歷史覆蓋 |
| 以相簿 Save All 流程替代 | 產品入口錯誤，且不在本 Skill 授權內 |

---

## 8. 設計問題陳述

### 8.1 核心問題

如何在**不修改舊事件、不自動解除其他 blocker、不重送未知下載**的前提下，讓系統對「同一個 canonical path、同一個 inode、已知內容 witness 不變、但 `st_dev` 已因 volume instance 改變而不同」的目錄，追加一個可審計的重新見證，使已確認的 restart 或日常備份可以繼續？

### 8.2 設計目標

1. 保留所有歷史事件與舊 completion 的不可變性。
2. 讓 valid remount 不再造成永久 deadlock。
3. 讓偽造替換、內容漂移、symlink、缺檔、額外檔與 inode 重用仍然 fail closed。
4. 讓 reattestation 明確地與下載授權、`UNKNOWN` 收斂、`LOCAL_CHANGED` scope 例外分開。
5. 讓同一事件可重播、可 crash recovery、可在下一個 Session 唯讀核對。
6. 讓 summary 清楚區分「舊完成事實」「目前本機可用性」「新 device binding」。
7. 不要求 Owner 填 JSON、UUID 或座標；Owner 只需對精確 scope 做一次明示決定。

### 8.3 非目標

- 不把 `UNKNOWN` 自動變成 `NOT_SENT`、`STOPPED` 或 `COMPLETED`。
- 不把 `LOCAL_CHANGED` scope 外的媒體解鎖。
- 不修改舊 completion 的 hash、大小、inode、時間戳或路徑。
- 不把 `st_dev` 當成永久 ID，也不假裝它能證明「同一個 volume」。
- 不用 reattestation 取代新的完整 scan、media identity 核對或 restart confirmation。
- 不使用相簿入口、Save All 或相簿 chooser 當成 fallback。
- 不在本次提報中直接實作、遷移 ledger 或操作真實媒體。

---

## 9. 設計選項比較

### 選項 A：直接忽略 `st_dev`

**做法：** 只比對路徑、inode、size、hash。

**優點：** 最小改動；立即解除本次阻塞。

**缺點：** 把「不同 volume instance」與「同一個目錄」視為等價，無法防止同路徑替換、inode 重用或 clone；會破壞 fail-closed 的核心價值。

**判定：** 不建議。

### 選項 B：提供人工 rebind／手動更新 device

**做法：** 讓管理者直接輸入新 device 或改寫 destination 事件。

**優點：** 實作表面簡單。

**缺點：** 難以重播、容易誤填、沒有 witness、不能區分合法 remount 與替換；也讓 ledger 成為可手改狀態。

**判定：** 不建議作為正式方案；最多只能作為診斷工具，不能作為日常恢復入口。

### 選項 C：append-only directory reattestation（建議方向）

**做法：** 先做唯讀 preview，列出舊 binding、新 device、canonical path、inode、所有已知 witness 與精確 scope；再由明確確認建立只追加的 `directory-reattest` 事件。投影時使用新的有效 binding，但舊事件與舊 completion 全部保留。

**優點：** 保留歷史、可重播、可審計、能將 device token 與內容 witness 分離；可與 restart 與 local availability 的現有狀態機整合。

**缺點：** 需要新事件 schema、projection、preview／confirm 命令、測試與 crash recovery；空目錄與 byte-identical clone 的風險仍需明確界定。

**判定：** **推薦。**

### 選項 D：volume fingerprint／witness file／外部 volume UUID

**做法：** 建立時保存 volume 或 directory witness（例如不可偽造的 marker、volume UUID、專案私有 nonce），remount 後以 challenge／response 重新確認。

**優點：** 對 clone 與「同 inode 不同 volume」有更強區分力；可作為長期強化。

**缺點：** 既有 ledger 沒有 witness；需要遷移策略；marker 可能被複製；不同檔案系統對 volume ID 的穩定性與可取得性不同。

**判定：** 可作為 reattestation 的未來強化層，不宜單獨假設既有歷史已具備。

### 選項 E：換新目的地並重下

**做法：** 把整個列表搬到新 root，建立新版本。

**優點：** 不動舊目錄。

**缺點：** 不解釋舊 `UNKNOWN`、不改寫 completion、仍可能需要下載；對本次同路徑 remount 來說是過度且不精確的處理，且新增空間與版本複雜度。

**判定：** 不是本次問題的正確抽象。

### 選項比較摘要

| 選項 | 保留歷史 | 防替換 | 可重播 | 日常可操作 | 建議 |
|---|---:|---:|---:|---:|---|
| A 忽略 `st_dev` | 是 | 否 | 是 | 是 | 不建議 |
| B 手動 rebind | 部分是 | 否 | 否 | 低 | 不建議 |
| C append-only reattestation | 是 | 是（有 witness） | 是 | 是 | 推薦 |
| D witness／volume fingerprint | 是 | 更強 | 是（需新模型） | 需遷移 | 未來強化 |
| E 換新目的地 | 是 | 是 | 是 | 成本高 | 不作為 primary |

---

## 10. 推薦架構：scoped append-only reattestation

以下為供高階模型評析的候選架構，不是已核准實作。

### 10.1 兩個分離的概念

1. **Binding**：目前這個 logical list／directory 由哪個 device namespace 看見。
2. **Witness**：目前看到的物件與已知內容是否相符。

不能只用 binding 取代 witness，也不能只用 witness 取代 binding。

### 10.2 建議的事件

概念事件名稱：`line-notes-directory-reattest/v1`

概念欄位：

```json
{
  "schema": "line-notes-directory-reattest/v1",
  "reattest_id": "<deterministic or uuid>",
  "list_key": "<logical-list-key>",
  "session_id": "<fresh-session>",
  "prior_binding_ref": {"sequence": 1, "sha256": "<old-event-sha>"},
  "scope": {
    "path": "<canonical-path>",
    "old_device": "<old-token>",
    "old_inode": "<same-inode>",
    "new_device": "<new-token>",
    "new_inode": "<same-inode>",
    "reason": "VOLUME_INSTANCE_CHANGE"
  },
  "witnesses": [
    {
      "kind": "COMPLETION_FILE",
      "completion_ref": {"sequence": 17, "sha256": "<event-sha>"},
      "path": "<canonical-or-relative-path>",
      "old_device": "<old-token>",
      "new_device": "<new-token>",
      "inode": "<same-inode>",
      "size": 0,
      "sha256": "<content-hash>",
      "mtime_ns": 0,
      "ctime_ns": 0,
      "result": "MATCH"
    }
  ],
  "evidence": "<immutable evidence bundle reference>",
  "confirmation_ref": {"sequence": 0, "sha256": "<event-sha>"}
}
```

設計要點：

- 事件只追加，不改舊 destination／completion。
- `prior_binding_ref` 建立 chain，重播時可確認沒有 fork。
- `scope` 精確列出 path 與新舊 token。
- `witnesses` 必須覆蓋足以區分本次物件的已知內容；不能只放一個任意 hash。
- `confirmation_ref` 將 Owner／Agent 的精確決定與事件綁定。
- 事件不包含「已停止」、「已下載」或「complete」等業務結論。

### 10.3 建議的 preview／confirm 流程

1. **read-only preview**
   - 讀取最新 destination binding。
   - 確認目前 path 為 canonical、非 symlink、存在且為 directory。
   - 計算目前 `(new_dev, new_ino)`。
   - 找出所有舊 completion／candidate／staging／restart scope 的 witness。
   - 對每個已知檔案驗證：inode、size、mtime、ctime、SHA-256、parent path、regular file、nlink、symlink。
   - 列出缺少 witness、空目錄、異常檔案與 scope 外 blocker。
   - 回傳 status、expected tip、scope digest、old/new binding、witness 統計與不可處理原因。

2. **confirm**
   - 在同一 ledger lock 內重算 preview。
   - 檢查 expected tip、scope digest、session、舊 binding ref、new device／inode。
   - 要求精確 scope 的明示 Owner 授權；一般「繼續」、沉默或 timeout 不得視為授權。
   - 寫入單一追加事件，讀回後回傳新投影。
   - 若已存在相同 reattestation，回傳 replay；不得建立第二份 staging 或下載。

3. **post-condition**
   - summary 顯示新的 active binding。
   - 舊 completion 仍可追溯；只有全部 witness 重新成立時，本機可用性才可變回 `VERIFIED_PRESENT`。
   - `UNKNOWN`、pending naming、scope 外 `LOCAL_CHANGED` 與 restart 限制仍保留，除非另有合法流程處理。

### 10.4 建議的驗證演算法

對 list directory：

```text
canonical_path_matches
AND not_symlink
AND is_directory
AND inode_matches_old_binding
AND new_device != old_device
AND directory_witness_set_matches_expected
AND no_unexpected_entries
AND no_missing_required_witness
AND all_known_completion_files_match_old_content_fields
```

對 completion／candidate file：

```text
path_is_relative_to_attested_directory
AND regular_file
AND nlink == 1
AND not_symlink
AND inode_matches_old_record
AND size_matches
AND mtime_matches
AND ctime_matches
AND sha256_matches
AND expected_name_set_matches
AND extra_files == none
```

注意：`st_dev` 只允許在 reattestation scope 內被替換成新的 token；不得無條件忽略。舊事件的 `device` 欄位不得改寫。

### 10.5 與其他狀態的交互

| 狀態／操作 | reattestation 可以做什麼 | 不可以做什麼 |
|---|---|---|
| 舊 `COMPLETED` + `LOCAL_CHANGED` | 在 witness 全部通過時重新計算為 `VERIFIED_PRESENT`；保留舊 completion 與舊 local observation | 改寫 completion、刪除舊事件、假裝從未 `LOCAL_CHANGED` |
| 舊 `UNKNOWN` | 只解除「list directory device」這個 blocker；仍需既有 restart scope／新 scan／新 intent | 自動改寫 `UNKNOWN`、自動建立新 attempt |
| pending naming | 不改 pending transaction | 用 reattestation 取代 `resume` |
| restart batch | 在 confirmation 與 recovery scan 仍有效時，允許後續 intent 通過 directory gate | 自動擴 scope、跳過新 recovery scan、重送舊 attempt |
| scope 外 `LOCAL_CHANGED` | 仍阻擋依賴該項的派送 | 用 list-level reattestation 解鎖全部貼文 |
| `LOCAL_MISSING` | 仍保留完成事實與本機不可用 | 以 reattestation 重下補帳 |
| `EXCLUDED`／`PROTECTED_HISTORY` | 不變 | 解鎖或覆寫 |
| candidate | 只有對應 witness 成立才維持可用 | 用舊 candidate 取代新 device 下的檔案 |

### 10.6 交易與 crash recovery

- preview、confirm、scan、intent、outcome、verify、activation 各自是獨立事件，不可用單一「已修好」旗標取代。
- 若在 confirm 前 crash：舊 binding 與舊 blocker 不變，重跑 preview 取得 fresh expected tip。
- 若在 confirm 後 crash：重開 ledger 只投影已寫入的 reattestation；不得重送 GUI 或建新 staging。
- 若在 intent 前 crash：下次 intent 仍必須通過 current directory gate 與所有 restart／scan 條件。
- 若同一 reattestation 事件重播：回傳已存在結果，不新增事件。
- 若 new device 再次改變：產生新的 preview／confirmation；不得沿用舊 device 或舊 scope。

### 10.7 錯誤碼建議

至少需要可區分的 fail-closed 錯誤碼，避免把所有情況壓成 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED`：

| 錯誤碼 | 意義 |
|---|---|
| `REATTEST_PREVIEW_REQUIRED` | 尚未有有效的 preview／confirm |
| `REATTEST_SCOPE_CHANGED` | expected tip、path、device 或 scope 已漂移 |
| `REATTEST_PATH_REPLACED` | canonical path、symlink 或 directory type 異常 |
| `REATTEST_INODE_CHANGED` | inode 不再是舊物件 |
| `REATTEST_CONTENT_DRIFT` | size、time、hash、expected set 或 extra file 不符 |
| `REATTEST_NO_WITNESS` | 空目錄或沒有足夠的內容 witness |
| `REATTEST_UNRESOLVED_ATTEMPT` | scope 內仍有未解的 `UNKNOWN`／pending 交易 |
| `REATTEST_SCOPE_OUTSIDE` | 試圖涵蓋未列出的貼文、媒體或路徑 |
| `REATTEST_REPLAY_CONFLICT` | 同一 scope 出現不相容的 confirmation／binding |

---

## 11. 邊界案例與威脅模型

| 情境 | 期望結果 | 理由 |
|---|---|---|
| 正常 remount；路徑與 inode 同、witness 全同 | 允許 scoped reattestation | 本次事故的目標情境 |
| 同路徑但 inode 改變 | 拒絕 | 目錄可能被刪除重建或替換 |
| 同路徑、同 inode、任一完成檔 hash 改變 | 拒絕 | 內容已漂移 |
| 同路徑、同 inode、完成檔大小／時間改變 | 拒絕或要求 fresh verification | 不能以舊 completion 背書 |
| 有額外檔、缺檔、symlink、硬連結數量異常 | 拒絕 | 與 completion manifest 不符 |
| 空目錄、沒有完成 witness | 拒絕或要求更強 witness／人工限定方案 | 無法僅靠 stat 證明同一內容 |
| byte-identical clone，所有欄位都相同 | 需明示風險；不能宣稱已證明同 volume | 單靠內容 witness 無法區分 |
| inode 被重用 | 拒絕；若無法分辨則標記不確定 | 舊 inode 不代表舊物件 |
| 多個 ledger 指向同一路徑 | 拒絕跨列表 scope | 不得合併不同列表 |
| `UNKNOWN` 尚未收斂 | reattestation 可以解 device gate，但不得解 `UNKNOWN` | 舊下載仍可能晚到 |
| pending naming transaction | 不建立新 reattestation side effect 或下載 | 必須先 resume／保留原交易 |
| scope 外 `LOCAL_CHANGED` | 保持阻塞 | 不得用 list-level 例外解全列表 |
| `LOCAL_MISSING` | 保持完成與欠件 | 不重下、不只因新 device 改寫 |
| 只有媒體預覽變化／工具成功回傳 | 不能當成重新見證證據 | 需要檔案系統與 completion witness |
| 來源已到期 | 不因 reattestation 重送 | 仍依 `SOURCE_EXPIRED`／欠件規則 |
| 同一 scope 再次中斷 | 可接續原 reattestation／restart，但不自動重送 | 需 fresh expected tip／scan 條件 |

### 威脅模型要承認的限制

- `st_dev`／`st_ino` 只描述檔案系統視圖，不描述使用者意圖。
- 若攻擊者能複製 byte-identical 目錄並讓所有 witness 相同，單靠本機檔案見證不能區分來源。
- 若需要更強保證，必須引入 volume-level identity、硬體／OS 級 attestation、外部簽章或 Owner 明示風險接受；這些不是目前 ledger 已具備的證據。
- 因此設計文件應區分「操作安全（避免誤覆寫）」與「對抗性完整性（抵抗刻意偽造）」，不要用同一個 hash 宣稱兩者都已解決。

---

## 12. 測試矩陣

以下測試是設計提案的驗收骨架，**本提報沒有執行它們**。

### 12.1 事件與 projection

| 測試 | 驗證目標 |
|---|---|
| 同路徑同 inode、新 device、完成 witness 全同 | 建立一次 reattestation，projection 選新 binding |
| 重播同一 preview／confirm | 回傳 replay，不新增事件、不建 staging |
| expected tip 漂移 | 拒絕 `REATTEST_SCOPE_CHANGED` |
| 舊事件鏈 fork／前序 hash 不符 | 拒絕 |
| event 寫入前 crash | 舊狀態不變；可重建 preview |
| event 寫入後 crash | 只投影已保存事件；不重送下載 |
| 同一 scope 的第二個不相容 confirmation | 拒絕 |

### 12.2 內容與檔案安全

| 測試 | 驗證目標 |
|---|---|
| 完成檔 hash 改變 | 拒絕 |
| 完成檔 size／mtime／ctime 改變 | 拒絕或要求 fresh verification |
| 缺檔／額外檔 | 拒絕 |
| symlink／hardlink／nlink 異常 | 拒絕 |
| 同 inode、不同內容 | 拒絕 |
| 同路徑、不同 inode | 拒絕 |
| 空目錄無 witness | `REATTEST_NO_WITNESS`，不得靜默通過 |
| byte-identical clone | 依風險模型拒絕或標記不確定，不得宣告同 volume |

### 12.3 狀態機整合

| 測試 | 驗證目標 |
|---|---|
| `UNKNOWN` + reattestation | `UNKNOWN` 仍存在；不能直接 verify 或重送 |
| restart confirmation + recovery scan + reattestation | 仍須 fresh scan／exact scope；不可跳過 intent gate |
| scope 外 `LOCAL_CHANGED` | 仍阻擋依賴項 |
| `LOCAL_MISSING` | 仍保留完成與欠件，不觸發重下 |
| pending naming | 不建立新下載或新 staging |
| active candidate | 只有 witness 成立才維持可用 |
| activation 後再次 remount | 新 preview／新 confirmation；不可重用舊事件 |

### 12.4 真實環境驗證（本次 NOT_RUN）

1. 在 macOS 上對專案內測試 volume 做受控 remount，確認同一 inode／內容的 device token 變化。
2. 確認 reattestation 後 notes CLI 能建立新 intent，但不自動送 GUI。
3. 在真實 LINE 記事本畫面完成一次 viewer → 下載控制 → chooser → verify → completion 流程。
4. 在跨 Session 情況重新開啟同一列表，確認舊 completion、`UNKNOWN`、restart 與 reattestation 的投影。
5. 驗證 chooser 目的地、單次控制、晚到結果與 crash window。

沒有上述當次原始證據，全部維持 `NOT_RUN`；合成 fixture 的 PASS 不能代替真實 LINE E2E。

---

## 13. 驗收標準

### 13.1 產品／行為

- 合法的同路徑、同 inode、witness 相符 remount 可以經精確 preview／confirm 重新見證。
- 重新見證不需要 Owner 手填內部 JSON、UUID、座標或逐項命令。
- 重新見證不會自動建立 intent、下載、verify 或 activation。
- 舊 completion、舊 `UNKNOWN`、舊 staging、舊 restart confirmation 全部可追溯。
- `UNKNOWN`、pending naming、scope 外 `LOCAL_CHANGED` 與 `LOCAL_MISSING` 的保護不變。

### 13.2 資料與安全

- 任一內容 witness 不符時不寫入成功事件。
- 不發生 symlink、hardlink、inode、額外檔、缺檔或 hash 漂移的靜默通過。
- 所有事件追加式、可重播、可由下一個 Session 讀回。
- 事件不包含真實媒體內容、憑證、私人群組或人名；必要敏感資料仍留在私有 evidence bundle。
- 不使用相簿入口或手改 ledger 作為 fallback。

### 13.3 操作與證據

- `dispatch_authorized=false` 仍是簿記欄位，不會升格成 GUI grant。
- GUI、簿記、ffmpeg／ImageIO、真實 E2E 與 Owner 觀察分別回報。
- crash window、重播、並行寫入與 stale preview 都有明確結果。
- 若沒有真實 remount／LINE E2E 證據，不得宣告產品已完全修復。

---

## 14. 建議的後續設計切片

以下只是供高階模型排序，不是本輪實作授權。

### S1：只讀診斷

- 新增 `reattest` 的 read-only preview 或等價唯讀稽核。
- 不改 ledger、不建 staging、不派送 GUI。
- 輸出 old/new binding、witness 統計、空目錄／缺 witness／scope 外 blocker。

### S2：追加式事件

- 新增 `line-notes-directory-reattest/v1`。
- 實作 expected tip、scope digest、confirm、replay、crash recovery。
- 對所有 witness 做 fail-closed 驗證。

### S3：projection 與 availability

- 讓 list directory、completion、candidate 與 staging 的 device 比對使用有效 binding，而非永久寫死舊 device。
- 保留舊 completion 與舊 local observation；重新計算目前本機可用性。
- 不改寫 `UNKNOWN`、pending naming、scope 外 `LOCAL_CHANGED`。

### S4：restart／daily 入口整合

- 確認 restart confirm 與 fresh recovery scan 的順序。
- 定義 reattestation 是否需要重新 preview／confirm；避免 scope digest 漂移。
- 在 `intent` 前仍要求當前 session、完整 inventory、restart 條件與新空白 staging。

### S5：離線與真實環境驗證

- 先跑 unit／fixture／crash／concurrency 測試。
- 再做受控 remount 與真實 LINE 流程。
- 未執行的真實 E2E 明確標 `NOT_RUN`。

---

## 15. 給高階問題分析模型的開放問題

1. 應該把 `st_dev` 定義為「掛載期 guard」還是「可被 reattest 的 binding」，並如何在資料模型中清楚分離？
2. 目錄身分是否應升級為 `(logical list key, canonical path, witness manifest, optional witness nonce)`，而不再把單一 `(st_dev, st_ino)` 當永久 identity？
3. reattestation 是否應只由 Owner 明示授權，並是否需要在 preview 中列出精確老／新 device、inode、witness、scope 與受影響的舊完成項？
4. 是否需要讓 reattestation 在 restart confirm 之前完成，避免 confirmation 的 `local_files` 投影與 expected tip 漂移？或應允許在 confirm 後追加但要求重新 preview？
5. 空目錄沒有完成檔 witness 時，應採用：(a) 拒絕，(b) 需要 Owner 額外風險接受，(c) 建立不可偽造 witness file，還是 (d) 其他方案？
6. 若舊 completion 目錄同時有多個完成檔，是否要求全部 witness 通過，或允許逐檔 partial reattestation？兩者如何避免把部分成功誤當成整篇完成？
7. `LOCAL_CHANGED` 的歷史 observation 要如何保留，同時讓目前 availability 在完整 witness 通過後回到 `VERIFIED_PRESENT`？是否應新增 projection 狀態或只以事件鏈表達？
8. reattestation 是否可以解 list directory gate，但不得解 completion／candidate gate？還是應以一個精確 scope 同時處理所有層級？
9. 如何處理 owner 口述「三次下載」與 ledger 只看到兩個 intent 的歷史缺口？是否應設計一個唯讀 observations ledger，而非把口述寫入 attempt？
10. 未來若加入 volume fingerprint／witness nonce，舊 ledger 如何遷移而不改寫舊 completion？是否需要在 `created` 之外追加 versioned binding？

---

## 16. 建議高階模型輸出

請分析模型至少回傳：

1. 選定的身分模型與明確的信任邊界。
2. 是否採用 append-only reattestation；若否，哪一種替代方案能在不忽略 `st_dev` 的前提下避免 deadlock。
3. 精確的事件 schema、preview／confirm 狀態機、projection 規則與錯誤碼。
4. 與 `UNKNOWN`、`LOCAL_CHANGED`、pending naming、restart confirmation、scan、candidate、activation 的交互矩陣。
5. 空目錄、byte-identical clone、inode 重用與 volume replacement 的安全答案。
6. 最小實作切片、migration／backward compatibility、crash recovery 與並行寫入策略。
7. 離線測試與真實 macOS remount／LINE E2E 驗收矩陣。
8. 哪些結論只是推論、哪些仍未知，以及不得宣稱的能力。

---

## 17. 私有證據與不提交範圍

本次私有證據位於專案內未被 Git 追蹤的任務目錄，包含：

- `directory-identity-blocker.txt`：完整阻塞、舊／新 device、inode、完成檔 witness、CLI 拒絕與 GUI 未派送；
- `restart-preview-01.json`、`restart-confirm-result.json`；
- `recovery-scan-start.json`、`recovery-page-0-result.json`、`recovery-scan-finish.json`；
- `summary-after-intent-refusal.json`；
- viewer／AX／截圖與 restart 授權引用。

本提報刻意不複製：

- LINE 群組名稱、人名、貼文原文；
- 原始媒體檔名與完整任務絕對路徑；
- ledger ID、media key、原始 hash；
- 憑證、授權 grant 或任何可重放的個人資料。

---

## 18. 狀態聲明

```text
PRIMARY_OUTCOME_STATUS: PROBLEM_REPORT_READY_FOR_ESCALATION
IMPLEMENTATION_STATUS: NOT_APPLICABLE; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: REPORT_ONLY; REATTESTATION_TESTS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE
```

### 白話結論

這次不是「影片下載壞掉」，而是「本機同一個資料夾的檔案系統身分證換了號碼」。筆記工具目前只認舊號碼，沒有安全地重新核對同一個資料夾的入口，所以它在按下下載之前就停住了。停住本身是保護，但這個保護目前沒有恢復路徑；因此這是需要產品層設計的 issue，且值得交給高階模型分析。
