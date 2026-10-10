# LINE 相簿盤點診斷：替代證據規則

## 目標與邊界

修正「每幀分頁 OCR 必須完全一致」造成的停止，分別驗證介面連續性、metadata 身份、捲動效果與相鄰覆蓋。

使用者已授權一次固定新方法的追加驗證：離線回放、反向測試，以及一次最多六次無下載捲動。保留原有三次嘗試，不再要求重複授權。

- 唯一新增寫入範圍：harness-development/catalog-diagnostic-continuity-replan-20261010/。候選程式、建置、快取、暫存及證據均放在此處。
- 舊診斷、產品草稿、config、state、registry、照片及既有 Git 工作保持原樣；不修改公開schema。
- 採 STANDARD；必須有獨立 Plan Review、實機前的獨立程式／證據審查，以及最後的獨立 Acceptance。實作採單一作者，不配置 helpers 或 writers。
- 本輪為計畫工作，尚未實作、重跑 OCR 或操作 LINE。

## 證據與判定方式

保存回放來源

將 scan-000 至 scan-003 原圖、既有兩 API 輸出、轉換紀錄、AX、動作紀錄及舊結果複製為不可覆寫材料，保存來源／副本 SHA-256。所有後續輸出使用獨立名稱及 exclusive creation，禁止覆盖。

四張 .png 原圖實際是 JPEG；依檔案內容識別格式，使用 ImageIO 解碼，保留原始 bytes。統一比較格式為 RGBA8、sRGB、不預乘 alpha、左上原點；ROI 邊界採 floor／ceil，轉換資訊全部保存。歷史缺失的來源或時間欄位維持 UNKNOWN，回放不能取得 live 操作許可。

建立本次介面 binding

從新的 fresh 畫面確認設定群組、既有群組名稱確認證據、相簿分頁、選中指示及列表結構。ROI 由這張畫面定位，禁止使用研究座標。

- 群組使用整個可用標題文字槽；分頁使用完整文字槽，不能依目前 OCR 結果縮小。
- 文字本體與整槽 guard 的 RGBA 必須和基準完全相同，避免漏掉新增、低對比或細小字元。陰影及分隔線另存；排除區只能在初始化時確認並凍結。
- 選中指示獨立比對其位置、形狀及像素，必須仍位於相簿下方。
- 每幀使用同一 documented CUA binding，保存實際可取得的來源、時間、尺寸、scale 與幾何；不得捏造 PID 或 window ID。
- 安全畫面判讀保留為 OBSERVED。必要來源、幾何或安全事實未知時停止，不能靠文字 hash 補足。

上述條件成立時，單次「相溥」只記為輔助 OCR 不確定性。群組、分頁或安全狀態有實質衝突仍立即停止。

按用途配置 OCR

使用 task-local Swift helper，僅處理保存影像：

- 固定標籤：局部 ROI、.accurate、zh-Hant 優先、語言校正開啟，customWords 限「相簿／記事本」。另做一次預先固定的關閉校正比較，僅供離線診斷；不依失敗調參。Apple customWords 文件 (https://developer.apple.com/documentation/vision/recognizetextrequest/customwords)
- 群組、日期、張數：關閉語言校正，不加入預期名稱或身份詞典。
- 保存前三候選、原始 confidence、bounding boxes、API／系統版本及影像轉換；不使用未校準的 0.95 門檻。
- 新版 Vision 為主要辨識器，舊版為診斷比較。任何有效日期／張數身份衝突均停止；兩 API 不宣稱為獨立模型。

分開判斷移動與覆蓋

完整身份為 group_key＋起訖日期＋正整數張數。日期與張數必須完整、唯一且位於同一 metadata 區域。partial metadata 不參與身份或重疊；外圍 partial 卡片可以記錄，不能當作已覆蓋。

- 相鄰完整身份依畫面順序，必須存在 suffix／prefix 重疊；缺口不得延伸覆蓋鏈。
- 對共同身份的日期及張數框，計算位移支持區間：
  D = [目前 ymin − 前次 ymax, 目前 ymax − 前次 ymin]。
- 所有框的 D 上界均須小於零、共同交集非空，且水平投影重疊，才能記為「metadata 明顯向上，位移範圍相容」。
- D 是 OCR 框提供的支持範圍，不能宣稱為校準過的真實位移誤差界限。AX 值及 transport 結果只作輔助。
- 集合相同不代表沒有移動。相關畫面確實未變才記 NO；證據不足或互相矛盾記 UNKNOWN。

診斷輸出分別保存 OCR、binding、連續性、身份歧義、移動及重疊結果。完整列表覆蓋固定為 NOT_ESTABLISHED；不產生相簿開啟或 Save All 許可。

## 實作與實機順序

1. 建立有效 v3 計畫契約、保存基線及回放材料，完成獨立 Plan Review；deterministic Handoff 原樣複製審查後契約。
2. 實作固定候選方法，完成回放與反向測試。獨立審查者核對程式、原始輸出及來源／候選 hash；全部通過後才安排 LINE 前景。
3. 從新的相簿列表起點開始，不要求回頂、不取得聊天導航權。只允許 documented getApp、getAXStateAndScreenshot、App.scroll。
4. 每步最多一次向下 .25 page scroll，全部輸入上限六次。順序為：分析 → fresh 再觀察與安全確認 → pretrace 保存／讀回 → 單一輸入 → fresh post-observation → 保存與判定。
5. 最後安全觀察、來源、幾何及機械核對必須綁在同一幀。實際輸入前檢查畫面年齡不超過五秒，包含保存／讀回耗時；過期最多兩次唯讀刷新。
6. UNKNOWN effect 最多追加兩次唯讀觀察，間隔 10／30 秒；不重送輸入。NO、衝突、缺口、未知來源、viewer／dialog、預算用完或中斷均停止，不重啟同次實機測試。

禁止 click、鍵盤、Page Down、setValue、選單、開相簿、下載及 canonical state 寫入。

## 測試與驗收

| 情境 | 必要結果 |
|---|---|
| 四幀原始回放；第四畫面 scan-003 保留「相溥」 | 影像連續性、三段移動及完整 metadata 重疊成立；歷史 live binding 不補造 |
| 可見集合相同，但 metadata 向上 | 移動成立，不以集合增量作門檻 |
| 標題改字／新增低對比字、切記事本、viewer／dialog | 停止 |
| 混入舊 run、過期觀察、来源／幾何變動 | binding 失效 |
| 日期／張數衝突、重複身份、跨卡配對 | 拒絕身份及覆蓋延伸 |
| 唯一重疊 metadata 不完整，或順序重疊缺口 | 拒絕延伸覆蓋鏈 |
| OCR 不一致且像素／結構不足 | UNKNOWN，停止 |
| 中斷、晚到結果或 uncertain input | 原輸入計數保留，不重新派送 |
| 六次實機輸入 | 每步有 fresh 證據、明確位移及重疊；無禁止操作或 state 寫入 |

凍結離線、實機、保存及獨立驗收 gate。採實際 v3 enum：CORE/OUTCOME/HARD_CLEAN；保存 gate 為 SUPPORTING/MUST_NOT_BREAK/BASELINE_DELTA。每項 required gate 必須有明確 PASS 及實際證據，schema VALID 不等於驗收通過。

保存檢查涵蓋舊診斷、受保護路徑、既有照片及 Git HEAD／branch／index 的前後基線。六步未全部取得成功證據時，實機結果依事實記 PARTIAL、FAIL 或 BLOCKED；保留已證明的離線及成功步驟，不宣告完成。

## 嘗試額度與正式狀態

追加方法只執行一次。舊三次嘗試及六狀態原封保留；新 task-local ledger 明確記錄「歷史 3＋已授權追加 1」與實際使用情況。失敗後保存最小重現、學習及剩餘未知，不調參開始第五種方法。

v3 meaningful_attempts 上限仍為 3，不能描述為完整累計 4。現有 4.8 controller 未發現能忠實 admission 此追加額度及新契約的機制；正式 admission 保持 BLOCKED，不修改 controller、不利用 PASS 分支繞過限制。本地診斷證據與獨立審查可如實交接，但不得宣稱 controller-native DONE。

驗收只證明此固定方法的有限診斷結果；不宣稱完整盤點、通用介面可靠性或全自動備份完成。
