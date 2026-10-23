# LINE 五本相簿實機測試報告（MANUAL_DIAGNOSTIC）

- 報告 ID：`MANUAL-DIAGNOSTIC-FIVE-20261022-02`
- 日期：2026-10-22（Asia/Taipei）
- 測試類型：`MANUAL_DIAGNOSTIC`，不是 `TWO_ALBUM_AUTO`，也不是正式 `LINE_TWO_ALBUM_PILOT/1` 交易
- 最終狀態：**A45 唯讀恢復驗證 COMPLETE；B78、C77、D42、E87 各一次 Save All 且全部檔案驗證 PASS**
- 本輪新增驗證：**284/284 張**；含上一輪 A45 的完整五本結果：**329/329 張**
- 正式 AUTO：**NOT_CLAIMED**

## 0. Session 與執行來源

| 項目 | 實際值 |
|---|---|
| Model | `deepseek-v4.1-flash:1017` |
| Provider | `ollama_cloud` |
| Session ID | `01a1611a-cc0b-7ea1-a868-9b6ff98c9664` |
| Host | Mac 本機 |
| LINE App | `jp.naver.line.mac`，真實 macOS GUI |
| Repo | `https://github.com/s9008129/Line_backup` |
| Branch | `v43-ab/codex-rev28` |
| Repo HEAD at start | `7682a94d69dc5e031e3a61dc6a0d621d38e26077` |
| UI 方法 | Computer Use、fresh screenshot、AX observation、macOS Vision OCR、`screencapture` |
| Image decoder | `src/line_backup_batch/image_decode.swift`，SHA-256 `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b` |
| OCR source | `harness-development/catalog-diagnostic-20261010/modern_ocr.swift`，SHA-256 `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861` |
| OCR executable | `line_vision_ocr`，SHA-256 `fe25c9f7ce44b9ca59cfd693cbb5b7db4cfedbab2be7b3ffd4abc13787ea4324` |

本輪以既有 MANUAL_DIAGNOSTIC 路線操作，沒有呼叫正式 AUTO Authorizer，沒有重用 `ONE56` grant，沒有修改產品程式、Harness、正式 grant、ledger 或 state。工作樹在本輪開始前已有其他 dirty／untracked 工作；本輪只新增本測試包的私有證據與公開去識別化摘要。

## 1. 結果摘要

| 候選 | LINE 相簿 | 目標張數 | Save All 次數 | 檔案驗證 | 狀態 |
|---|---|---:|---:|---|---|
| A45 | `2024/04/22～04/26` | 45 | 本 Session 0；上一輪 1 | 45/45 PASS | `PREVIOUS_A45=COMPLETE` |
| B78 | `2024/4/21` | 78 | 1 | 78/78 PASS | PASS |
| C77 | `2024/04/08～04/12` | 77 | 1 | 77/77 PASS | PASS |
| D42 | `2024/04/01～04/03` | 42 | 1 | 42/42 PASS | PASS |
| E87 | `2024/03/25～03/29` | 87 | 1 | 87/87 PASS | PASS |

本輪四本合計：

- 真實新增檔案：`284`
- 真實新增 bytes：`98,633,984`
- SHA-256 manifest 行數：`284`
- ImageIO 完整 RGB 解碼：`284/284 PASS`
- 解碼失敗：`0`
- 未知下載結果：`0`
- 錯誤相簿或重複 Save All 派送：`0`

## 2. A45 唯讀恢復檢查

A45 在上一輪已實際派送 Save All；本 Session 沒有再次派送或覆寫。

| 驗證項目 | 實際結果 |
|---|---|
| 私有目的地 | `private/downloads/01-2024-04-22_2024-04-26_45/` |
| 檔案數 | `45/45` |
| 索引 | `1..45` 連續 |
| bytes | `14,433,233` |
| 零 byte 檔 | `0` |
| per-file SHA-256 manifest | `3e3f8253ca20aff2f5e464a7ad403d5458a6940c96fb4f99ef21f10632c1338c` |
| ImageIO decode | `45/45 PASS`、`0` failed |
| decoder receipt SHA-256 | `577d995610349c199113b82892935de0b0ec7bee8cf2207e2404a74a4ecbb0ce` |
| 本 Session Save All 派送 | `0` |

結論：`PREVIOUS_A45=COMPLETE`。A45 已保留在本機私有目錄，後續不得重下載。

## 3. 授權、保護資料與正式狀態不變性

Owner 本輪只授權 B78、C77、D42、E87 各一次真實 Save All；A45 僅允許唯讀檢查。受保護資料未被下載、覆寫或修改：

- 正式 VERIFIED：239 張。
- 既有 Manual Diagnostic：109 張（A56＋B53）。
- Owner 排除相簿：65 張。
- 上一輪已 Save All 的 A45：45 張。

操作前後 SHA-256：

| 檔案 | SHA-256 | 結果 |
|---|---|---|
| `state/backup_state.json` | `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6` | 不變 |
| `state/manual_archives.json` | `efe572afc9da1ae2123b3016430370f9ecd84ffb259f3bf73b0e5d26cd667bc5` | 不變 |
| `policies/line-two-album-pilot-v1.json` | `59d94b72f4fd59d829b56d21a494c9d83c6b91eb2513c15795a58021194a39e9` | 不變 |

因此本輪沒有正式 state、ledger、grant、manual registry 或 policy mutation。

## 4. 四本實際操作與身分核對

### 4.1 B78：`2024/4/21`、78 張

1. Fresh LINE 列表 OCR 同時讀到 `2024/4/21` 與 `78`，日期框 `[29.462,616.096,123.339,24.338]`、張數框 `[29.484,648.358,34.844,26.792]`。
2. 點擊日期 metadata strip，未點封面中心；詳細頁重新讀到 `2024/4/21`、`78張照片`、`2024.04.21`，並顯示 photo grid。
3. 開啟 `⋯`，native screenshot OCR 找到唯一 `儲存全部`；只派送一次。
4. Folder chooser 導向全新的 `private/downloads/02-2024-04-21_78/`，開啟前為空；只開啟 chooser 一次。
5. 下載完成後得到 78 個 JPEG；索引 `1..78` 連續，零 byte 與暫存檔皆為 0。
6. 返回列表後使用新的 fresh 畫面與 scrollbar 值 `2683` 繼續找下一本。
7. 主要證據：`private/evidence/10-B78-list.*`、`11-B78-preclick.*`、`12-B78-detail.*`、`14-B78-menu-native-screen.*`、`15-B78-post-saveall-cua.*`、`17-B78-chooser-correct-folder.*`、`18-B78-download-started.*`、`19-B78-download-complete.*`、`20-after-B78-back-to-list.*`。

### 4.2 C77：`2024/04/08～04/12`、77 張

1. 返回列表並實際捲動後，fresh OCR 在 scrollbar `3220` 同時讀到 `2024/04/08~04/12` 與 `77`，再於緊接的 fresh screenshot 核對相同框位。
2. 點擊日期 metadata strip；詳細頁讀到 `2024/04/08~04/12`、`77張照片`、`2024.04.14`，並顯示 photo grid。
3. 開啟 `⋯`，native screenshot OCR 找到唯一 `儲存全部`；只派送一次。
4. Folder chooser 導向全新的 `private/downloads/03-2024-04-08_2024-04-12_77/`；只開啟 chooser 一次。
5. 下載完成後得到 77 個 JPEG；索引 `1..77` 連續，零 byte 與暫存檔皆為 0。
6. 返回列表後保留 `31-after-C77-back-to-list.*`，再以 fresh 畫面尋找 D42。
7. 主要證據：`private/evidence/21-before-C77-scroll.*`、`22-C77-preclick.*`、`23-C77-detail.*`、`25-C77-menu-native-screen.*`、`26-C77-post-saveall-cua.*`、`28-C77-chooser-correct-folder.*`、`29-C77-download-started.*`、`30-C77-download-complete.*`、`31-after-C77-back-to-list.*`。

### 4.3 D42：`2024/04/01～04/03`、42 張

1. 第一次為 D42 取得的 fresh 列表畫面實際顯示的是 E87（`2024/03/25～03/29`、87），不是 D42；guard 在點擊前停止，沒有誤點或派送。
2. 重新取得列表並實際捲動至 scrollbar `3221`，fresh OCR 同時讀到 `2024/04/01~04/03` 與 `42`。
3. 點擊日期 metadata strip；詳細頁讀到 `2024/04/01~04/03`、`42張照片`、`2024.04.05`，並顯示 photo grid。
4. 開啟 `⋯`，native screenshot OCR 找到唯一 `儲存全部`；只派送一次。
5. Folder chooser 導向全新的 `private/downloads/04-2024-04-01_2024-04-03_42/`；只開啟 chooser 一次。
6. 下載完成後得到 42 個 JPEG；索引 `1..42` 連續，零 byte 與暫存檔皆為 0。
7. 主要證據：`private/evidence/32-D42-list.*`（錯誤候選，未點擊）、`33-D42-list-reacquired.*`（正確 D42）、`34-D42-detail.*`、`36-D42-menu-native-screen.*`、`37-D42-post-saveall-cua.*`、`39-D42-chooser-correct-folder.*`、`40-D42-download-started.*`、`41-D42-download-complete.*`、`42-after-D42-back-to-list.*`。

### 4.4 E87：`2024/03/25～03/29`、87 張

1. D42 完成後返回列表；fresh OCR 在 scrollbar `3757` 讀到 `2024/03/25~03/29` 與 `87`。
2. 本 Session 再次取得 fresh pre-click 畫面，日期框 `[26.674,783.334,240.070,26.854]`、張數框 `[30.009,819.500,30.009,20.500]`，兩者屬同一張卡片。
3. 點擊卡片 metadata strip `[140,672]`（Computer Use window-relative），未點封面中心。
4. 詳細頁 fresh OCR 讀到 `2024/03/25~03/29`、`87張照片`、`2024.03.30`，畫面為 photo grid，不是單張 viewer。
5. 點擊右上 `⋯` `[610,88]`；native screenshot OCR 找到唯一 `儲存全部`，框位 `[1297.044,380.000,106.698,30.000]`。依既有座標換算只點擊 `[635,273]` 一次。
6. Folder chooser 開啟且 initial destination 為 0 檔；以 Go to Folder 導向全新的 `private/downloads/05-2024-03-25_2024-03-29_87/`，再確認該目錄仍為 0 檔，按一次「打開」。
7. 下載期間以 3 秒間隔觀察：`20 → 27 → 34 → 39 → 45 → 52 → 59 → 63 → 67 → 72 → 78 → 81 → 85 → 87` 檔。87 檔後再等 3 秒，檔案大小集合 SHA-256 未變，判定寫入穩定。
8. 下載後實際為 87 個 JPEG；索引 `1..87` 連續，零 byte、非 JPEG、隱藏暫存與子目錄皆為 0。
9. 按 Escape 返回列表，AX scrollbar `3757`；實際向下捲動一次後變為 `4294`。fresh OCR 的新畫面顯示 `2024/03/18~03/22`、69 與 `2024/03/12~03/15`、46，證明列表內容已變化。
10. 主要證據：`private/evidence/43-E87-list.*`、`44-E87-preclick.*`、`45-E87-detail.*`、`46-E87-menu.*`、`47-E87-chooser-initial.png`、`48-E87-chooser-correct-folder.*`、`49-E87-download-started.png`、`50-E87-download-complete.png`、`51-after-E87-back-to-list.*`、`52-after-E87-scroll.*`。

## 5. 逐檔完整性驗證

| 相簿 | 檔案數 | bytes | 索引 | 零 byte | 非 JPEG／暫存 | manifest SHA-256 | decoder receipt SHA-256 | 解碼 |
|---|---:|---:|---|---:|---:|---|---|---|
| B78 | 78 | 29,297,748 | 1..78 | 0 | 0 | `b5eacb9771acfc1736b70b0f6538d8cd868c15faff92c8a244b3600a73f97394` | `420e8e2b68f8d7a83fbf8f8a08cef2d85f3eb9b432ceca152e1f63540af0663c` | 78/78 PASS |
| C77 | 77 | 29,449,320 | 1..77 | 0 | 0 | `b416958135dea250346d440141fb809344a003a0f1dfecb2552434f3d555abc4` | `332ea60328662fe4bbbecb9d1a373d86ef17b0d5dc72774906288656b0a0654d` | 77/77 PASS |
| D42 | 42 | 14,310,708 | 1..42 | 0 | 0 | `7be7abd30c25aa4e14af07f2c2396882af42c10677023e1f356c5ee1022ab613` | `899670388a92814913ff5b20a4fd8d34e64651cb9ab791d9eeef372eebec927f` | 42/42 PASS |
| E87 | 87 | 25,576,208 | 1..87 | 0 | 0 | `90c56a17070a9d57bf2ab6d73569bc4810f967676c509a0e73da75597e91fc4f` | `9556eb9d1a16f97bc9811e6c68431e3199a4bc501bf68825ef9853ec33e52fbf` | 87/87 PASS |

驗證方式：

- `SHA-256`：對每個實際 JPEG 計算 per-file hash，manifest 行數與目標張數一致。
- 完整性：manifest hash set、decoder 逐檔 hash set、實際目錄 hash set三者相同。
- 唯一性：每本 manifest 的 87／78／77／42 個 hash 均互不重複。
- 解碼：macOS ImageIO 載入後，再建立 full RGB bitmap；任一影像無法完整繪製即計為 failure。
- 下載完成性：檔數達標後至少再觀察 3 秒，期間檔數、檔名集合與大小集合均未再變。

公開的去識別化 manifests：

- `public/A45-manifest.sha256`
- `public/B78-manifest.sha256`
- `public/C77-manifest.sha256`
- `public/D42-manifest.sha256`
- `public/E87-manifest.sha256`

公開 manifest 以 `photo_001.jpg`～`photo_NNN.jpg` 取代原始下載檔名；只保留每張照片的 SHA-256 與安全索引。原始檔名與照片只存在本機 `private/`。

## 6. 第一個實際錯誤與 Expected vs Actual

- **Expected：** D42 的第一次 target grounding 應看到 `2024/04/01～04/03`、42 張。
- **Actual：** fresh 列表畫面顯示 `2024/03/25～03/29`、87 張（E87）。
- **處理：** 沒有點擊該卡片、沒有開啟菜單、沒有派送 Save All。重新取得 fresh 列表與 scrollbar，找到正確 D42 後才繼續。
- **影響：** 無錯誤相簿、無重複或錯誤 Save All；D42 最終仍只派送一次。

`FIRST_REAL_BLOCKER=NONE`。上述是 guard 擋下的可恢復辨識差異，不是交易阻塞。

## 7. 已證明與未證明

### 已證明

- 四本指定相簿都在真實 macOS LINE GUI 中被 fresh 畫面、OCR、AX／scrollbar 與詳細頁交叉核對。
- B78、C77、D42、E87 各只派送一次 Save All，且各進入獨立空白下載資料夾。
- 284 個新增 JPEG 全部存在、非零、索引連續、SHA-256 建檔，並通過 ImageIO 完整解碼。
- E87 下載後返回列表並實際捲動，scrollbar `3757 → 4294`，新畫面內容有可觀察變化。
- 正式 state／manual registry／pilot policy 的 SHA-256 前後完全相同。
- 沒有重下載 A45、239 張正式 VERIFIED、109 張既有 Manual Diagnostic 或 65 張排除相簿。

### 未證明

- 尚未以正式 AUTO Authorizer、grant、ledger、state commit、readback 與 release 流程完成 `TWO_ALBUM_AUTO`。
- 本報告尚未取得 Owner 指定外部 ChatGPT Chief Reviewer 的真實審查結果。
- Save All 的實體 exactly-once 保證仍不能由 MANUAL_DIAGNOSTIC 證據推導；本輪只能證明各本實際派送次數為 1 且沒有重送紀錄。
- 不宣稱 `FORMAL_TWO_ALBUM_AUTO=PASS`。

## 8. 檔案與正式狀態副作用

本輪新增／更新的實際副作用：

- 四個新的本機私有相簿資料夾，共 284 個照片檔。
- 本機私有下載進度與每本完成 checkpoint：`private/checkpoints.json`。
- 本機私有 fresh screenshots、OCR、AX、chooser、download、hash 與 decoder receipts。
- 公開報告、去識別化 evidence index、五本 sanitized manifests 與完整私有證據 hash manifest。
- 正式 state／grant／ledger／pilot policy：**0 mutation**。
- 既有 VERIFIED／Manual Diagnostic／A45／排除相簿：**0 overwrite、0 redownload**。

## 9. 隱私與證據邊界

公開 GitHub 只提交：

- 本 Markdown 報告。
- `public/evidence-index.json`。
- 每本 `public/<ID>-manifest.sha256`。
- `public/evidence-sha256.txt`，其中只列私有 evidence 的相對路徑與 hash。

不提交：

- 兒童或家庭照片。
- LINE 群組名稱、人名、聊天內容。
- 原始下載檔名。
- 原始全螢幕截圖、OCR 內文、AX 全檔。
- 本機絕對路徑、憑證、grant、token 或私人 transaction 資料。

## 10. 狀態矩陣

| 狀態 | 值 | 說明 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `PASS` | 本輪 B78＋C77＋D42＋E87 = 284/284 真實檔案驗證完成 |
| `IMPLEMENTATION_STATUS` | `NOT_CHANGED` | 沒有修改產品原始碼 |
| `CORE_ACCEPTANCE_STATUS` | `PASS` | 四本都以真實 LINE GUI 完成辨識、點開、一次 Save All、下載與驗證 |
| `REQUIRED_VERIFICATION_STATUS` | `PASS` | 檔數、索引、bytes、SHA-256、ImageIO、下載穩定性均通過 |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | 待外部 Chief Reviewer 與指定獨立審查 |
| `TASK_CLOSURE_STATUS` | `OPEN` | Evidence-only Draft PR 待外部審查；不代表正式 AUTO 核准 |

## 11. 精準下一步

1. 將本報告、`public/evidence-index.json`、五本公開 manifest 與 evidence hash manifest 隨 Draft PR 交付 Owner 指定的外部 ChatGPT Chief Reviewer。
2. Reviewer 核對精確 commit HEAD、四本各一次 Save All、284/284 檔案與 decoder hash、正式 state hash 不變。
3. 本 MANUAL_DIAGNOSTIC 不升級成正式 `TWO_ALBUM_AUTO`；若要正式自動化，另立有界 Plan，使用新的 eligible 相簿與新的交易授權，不重用本輪已下載的四本。

## 12. Owner 授權的一次取消診斷（未派送）

2026-10-23 另一次 MANUAL_DIAGNOSTIC 取得 Owner 明確前景交接後，以新的 LINE 列表與詳細頁核對指定候選身分。為該次測試建立新的隔離目的地，派送前確認為空。公開報告省略相簿日期、群組與本機目的地；原始畫面未上傳。

- 相簿詳細頁身分核對：PASS。
- 打開相簿溢位選單：BLOCKED；重新依當前畫面定位後仍未顯示選單，故停止輸入。
- Save All 派送：0 次；取消：未執行。
- 隔離目的地：派送前與停止後均為 0 檔、0 bytes；未產生部分下載。
- 繼續／重新下載選項：未觀察；原生缺檔接續：`NOT_TESTED`。
- 未觀察到重複下載或覆寫；正式 Task、checkpoint、VERIFIED 狀態與既有照片未操作。
- 去識別化本機證據備忘錄 SHA-256：`be4f2ad22bd052e964a1b94af38355e50394dd9a5bfe060ea054ed306c168fd0`。本次沒有下載照片；原始截圖未提交，僅於當次工具觀察。

下一步：以 fresh frame 重新定位並驗證選單控制項可正常打開；此校準確認前不得派送 Save All。此阻塞結果不改寫上方五本相簿已完成的歷史結果，也不代表中斷接續測試已執行。
