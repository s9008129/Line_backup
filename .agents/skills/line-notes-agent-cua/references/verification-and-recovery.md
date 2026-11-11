# 驗證、狀態與恢復

本文件定義記事本照片／影片下載後的驗證標準、六類業務狀態、本機可用性及恢復決策。驗證只證明指定檔案的指定性質；不證明檔案與 LINE 服務端原始位元完全相同，也不代替 GUI 授權、真人觀察或獨立驗收。

## 四個證據層次

| 層次 | 能證明什麼 | 不能證明什麼 |
|---|---|---|
| notes CLI 簿記 | 事件、attempt、completion、summary 的輸入與投影一致；拒絕與重送限制依實作成立 | 畫面真實、下載派送成功、檔案可解碼或 LINE E2E |
| ImageIO／ffmpeg 解碼 | 指定本地檔案在指定工具與版本下通過完整解碼／驗證 | 等於服務端原始位元、畫面涵蓋完整或使用者已驗收 |
| 真人 `OBSERVED` | 某人於當次畫面看見的現象 | 工具 PASS、檔案完整、獨立 acceptance |
| 真實 LINE E2E | 當次正式任務、有效前景、完整操作與證據涵蓋的實機結果 | 不得由合成 fixture、文件或相簿案例推廣到所有版本／環境 |

`dispatch_authorized=false`、簿記成功、檔案可解碼或截圖存在都不會自動升格成其他層次。AX、截圖、Computer Use 原始回傳與真人觀察是不同來源；同一提示只出現在其中一種來源時，只能記該來源與當次範圍，不能用另一個來源補成存在或不存在。未執行或沒有證據的層次標 `NOT_RUN`。

## 證據與允許行為矩陣

下表是操作決策。新寫入的 `--evidence` 等參數要求 `evidence-pack` 產生的 `line-notes-evidence/v2` bundle；statement 可依 [證據範本](evidence-template.md) 撰寫，但 CLI 只核對 bundle 結構、context、保存子 blob 的 bytes／hash，不替 Agent 判斷欄位語意或畫面真實性。操作順序見 [下載與 notes CLI](download-and-ledger.md)。

| 證據來源 | 能證明的命題 | 允許行為／仍未知時 |
|---|---|---|
| intent、新空白目錄、`save_all_count=0` | 本機 attempt 與派送前保護已建立 | 不能證明未派送；維持禁止重送，不以零計數、空目錄或 marker 缺席解鎖 |
| 當次控制可見、作用及映射明確 | 具備單次輸入的定位依據 | 不推論已命中、App 已接受或下載已發生；視窗／頁面／來源改變即失效 |
| input API 的原始成功、錯誤或逾時回傳 | 工具回傳了該結果 | 未有排除副作用保證時不推 `NOT_SENT`；不得因 error／timeout 再點一次，結果不明記 `UNKNOWN` |
| 可歸屬同一 viewer／attempt 的 chooser | App 有階段性回應，可能延遲出現 | 核對精確來源與目的地；chooser 不是下載結果，出處不明時不確認 |
| 只有 timeout、畫面未變、空目錄或缺少 marker | 當下尚無足夠結果證據 | 尚無 outcome 時先以 `outcome` 記 `UNKNOWN`；已有 `outcome=UNKNOWN` 則保留。沒有新資訊就停止相同查證，不重送、不建新 attempt，也不派送下一項 |
| 可歸屬的正面下載終結訊號，加上原目的地的穩定結果檔 | 支持進入檔案驗證的候選結果 | 不同媒體不要求同一種 UI 訊號；但單一弱訊號不足以判完成，仍不能證明內容完整或 completion |
| 指定檔案的完整驗證，加上 completion 書寫與讀回 | 指定項目／目的地的完成條件成立 | 才可計 `COMPLETED`；不證明服務端原始位元相同、外部副本完整或整份列表完成 |
| 可歸屬且足以排除原操作稍後繼續的明確停止／未派送證據 | 可能安全終結原 attempt | 只有此類正面證據才可進 `STOPPED`／`NOT_SENT`；目前是否能取得此證據仍 `UNKNOWN`，不憑推測建立 |

### 可接受的完成與停止證據

- **下載結果。** 需要同時能歸屬原 attempt／viewer／原目的地，並具備當次正面終結觀察與穩定結果檔；照片的「下載完畢」提示只是可能的終結觀察之一，不是影片的必要條件。提示的截圖可見與 AX 文字必須分開記錄，當次瞬態時間／範圍不可得就記 `UNKNOWN`；不得為取得提示重新下載，提示本身也不取代同 attempt 終結、穩定檔、verify 與 completion。影片仍須有當次可歸屬的正面終結證據，不能因照片案例或播放結束而自行補規則。
- **檔案與 completion。** `DOWNLOAD_FINISHED` 只允許進入驗證；還要通過穩定檔集、預期數、非空、SHA-256、逐檔內容解碼、發布及 completion 讀回，才可計 `COMPLETED`。任何一層缺失都停在對應層次，不重下補帳。
- **停止／未派送。** 必須有可歸屬、能排除原操作稍後繼續的正面證據；`timeout`、API error、控制不見、空目錄、缺少 marker、舊計數為零與播放結束都不足。假設案例中的此類 receipt 不得寫成已取得；沒有證據就保留 `UNKNOWN` 並停止新派送。

## 證據稽核、頁面更正與類型更正

`evidence-audit` 是獨立於一般 `summary` 的唯讀引用稽核。它先要求 event 結構／sequence／hash chain 可讀，再逐引用檢查外層 bundle、context 與子資產；結構性引用不可信時直接停止，不產生可誤用的 row。引用漂移時仍列明錯誤並以 exit 4 結束，`business_projection_omitted=true`，不得把完成數、貼文狀態或 audit 局部結果當成下一步依據。legacy opaque 可為 `LEGACY_OPAQUE`／`REFERENCE_CHECK_NOT_AVAILABLE`：這表示未做位元核對，不是損壞，也不是已升級驗證。

`evidence-correct` 只處理 page evidence 的錯引，必須精確指向原 page 的 sequence／SHA-256、原 evidence SHA-256、context 相符的 replacement bundle 與 reason。它不修改 page 成員、順序、top/bottom、scan 覆蓋、貼文／媒體 key 或舊完成；page 以外有其他證據損壞時整筆拒絕。重複更正須串接前一筆 correction ref，不能分叉或覆寫。`summary.evidence_corrections` 顯示追加鏈，但不把 replacement 證明成原頁面的真實性或業務完成。真實帳本套用前仍須精確資料預覽與授權。

`media-kind-correct` 只適用最新完整 scan 中已盤點、且從未有 intent／verification／completion／exclusion／protection 的媒體。更正 append `media-kind-correction`，保留原 media key、貼文、數量、來源順序與原 inventory；投影另列 `kind`、`effective_kind`、`kind_correction_ref`。新 intent 使用 v2 並凍結更正後種類，照片與影片分別走嚴格驗證器。合法舊 v1 intent 仍可讀取，但更正後才出現、聲稱舊種類的 v1 intent 會被拒絕；不手改 schema、event 或 key。真實資料須先確認 19 項等精確清單均無 attempt，再依 D2 預覽授權套用，不得批次猜測。

## 照片驗證

每張照片至少要有：

- 穩定檔集與預期數量相符；不含未釐清 partial、暫存、非屬合格環境附屬項的額外檔或 symlink。
- 檔案存在、非空、大小／ SHA-256 與穩定前後樣本一致，且不與 completion manifest 衝突。
- 使用 ImageIO decoder，例如由本專案既有 `src/line_backup_batch/image_decode.swift` 建置的執行檔；`--decoder` 由呼叫端提供，實作者必須核對其建置來源、路徑與版本。notes CLI 只核對呼叫端提供的 SHA-256，並確認執行前後是同一個 binary、沒有內容漂移，不能證明它來自該 Swift 原始碼。使用時記錄 binary 路徑、SHA-256、真正 exit code、`verdict=PASS`、`readOnly=true`、expected／actual 數量及逐檔 decoded／SHA-256。
- 解碼器在只含本次單一目標檔的乾淨目錄執行，不讓同目錄其他檔案影響結果；逐檔調用與匯總由 notes verifier 負責。
- 目前嚴格照片驗證只接受 `.jpg`／`.jpeg`／`.png`，且檔案大小必須小於 512 MiB（等於 512 MiB 也拒絕）。HEIC／HEIF、WebP、TIFF、GIF 等其他格式雖可保留原檔，但列為未驗證且不得完成；不支援的格式、超限影像、解碼失敗或非空 stderr／異常輸出亦同，不跳過後宣稱全部通過。

ImageIO 完整解碼可排除部分壞檔，但不能單獨證明與服務端原始檔相同。照片的檔名、縮圖、hash 或解碼成功都不能取代列表→貼文→媒體身分。

## 影片驗證

固定使用成對的 Homebrew 絕對路徑：

```text
/opt/homebrew/bin/ffmpeg
/opt/homebrew/bin/ffprobe
```

不可使用裸 `ffmpeg`：目前 PATH 可能解析到不同版本，混用會使 probe 與完整解碼不是同一工具組。每次啟動先核對兩個檔案存在、可執行、來源版本一致，保存 `ffmpeg -version`／`ffprobe -version` 的關鍵版本行及 binary SHA-256；已知規劃版本為 7.1.1，但當次仍需重新核對，不把舊值當永久常數。

`media_verify` 實際支援的影片 suffix 與 `ffprobe format_name` alias 映射如下（suffix 以不分大小寫比對）：

| 影片 suffix | 可接受的 `format_name` aliases |
|---|---|
| `.mp4`／`.mov`／`.m4v` | `mov`、`mp4`、`m4a`、`3gp`、`3g2`、`mj2` |
| `.avi` | `avi` |
| `.mkv` | `matroska`、`webm` |

`format_name` 可以是逗號分隔的多個 alias；至少要有一個 alias 與 suffix 的允許集合相符。上表沒有列出 `.m4a` 作為可接受的檔案 suffix；`m4a` 只是 `.mp4`／`.mov`／`.m4v` 的容器 alias。suffix 不在支援表會以 `UNSUPPORTED_VIDEO_EXTENSION` 拒絕；probe 缺少 format 會以 `INVALID_PROBE_RESULT` 拒絕；`format_name` 空白／無法解析會以 `INVALID_CONTAINER_FORMAT` 拒絕；alias 與 suffix 無交集則以 `CONTAINER_FORMAT_MISMATCH` 拒絕。以上皆 fail closed：保留原檔、標為未驗證，不得重新命名、轉檔、跳過後宣稱成功或降格計為完成。

1. **Probe。** 以 `ffprobe` 讀取 streams 與 format metadata，保存 JSON 證據。必須至少有一個真正的影像串流；只找到 `attached_pic` 封面、沒有可解碼影像時 FAIL。`duration`、`nb_frames`、`codec_type` 等只是候選，不能取代解碼。
2. **逐 stream 完整解碼。** 對每一個實際影像與音訊 stream，用 probe 回傳的精確 index 顯式映射並完整解碼到 null 輸出；不只用可選 map，也不只讀 metadata。預定命令形狀如下，實際 flags／輸出解析須由 verifier 實作及測試：

   ```text
   ffprobe -v error -show_streams -show_format -of json <VIDEO>
   ffmpeg -nostdin -hide_banner -v error -err_detect explode -xerror \
     -i <VIDEO> -map 0:v:<VIDEO_INDEX> -map 0:a:<AUDIO_INDEX> \
     -progress pipe:1 -f null -
   ```

   `-err_detect explode` 必須在 `-i` 前；每個影像／音訊 stream 個別核對，不能因其中一個成功就宣稱其他 stream 成功。無音訊是允許情況，但影片本身仍必須有有效影像並完成解碼。
3. **成功判準。** 真正 exit code 為 0；progress／frame／duration 覆蓋足以支持已解碼到預期結尾。**不得只看到 `progress=end` 就判 PASS**；非零退出、截斷、解碼錯誤、frame／duration 覆蓋不足、時間跳躍或提前 EOF 均 FAIL。對帶有 `FFMPEG_DECODE_DIAGNOSTIC_V1` policy 的新證據，ffmpeg 逐 stream 解碼的非空 stderr 是必須原樣保存的診斷，不再單獨否決；仍須核對 `stderr_empty`、非負整數 bytes、SHA-256 與有限 preview 一致，且未知診斷不代表已證明無害。缺 policy 的 legacy 證據維持嚴格：非空 stderr 拒絕。`ffprobe` stderr 必須為空，工具版本／binary hash、嚴格 flags 與 loglevel 不得放寬或清洗。
4. **長影片。** 不套用相簿固定 120 秒限制。以 stall watchdog 判斷是否長時間沒有新進度，持續回報已處理秒數／frame 與目前狀態；不得因影片長就降低完整性標準。中止時保留原檔並標未驗證，不假裝完成。
5. **前後穩定。** 解碼前後重算大小、SHA-256、mtime／ctime 及檔集；任何漂移、替換、symlink 或寫入中狀態都停止並保留證據。

ffmpeg 完整解碼仍不能保證偵測所有靜默損壞，也不代表與服務端原始位元完全相同。無效、截斷、無有效影像、解碼失敗或工具版本不符的影片不得進 completion。

## 發布交易與 completion

- 驗證前先保存來源名、暫名、目標名、大小、SHA-256、mtime／ctime、預期 manifest 與 journal；發布使用不可覆寫交易，目標已存在就拒絕，不偷偷改名或覆寫。
- 每個貼文使用獨立目錄與逐媒體編號；檔名保留實際副檔名。重排不重命名舊完成檔；新媒體只取該貼文目前最大編號加一。
- 相同 basename、相同可見名稱、隱藏副檔名或缺少來源 metadata 只供顯示，不證明同一媒體、既有命名來源或可合併；每次 attempt 仍使用獨立空白目的地，metadata 不足記 `UNKNOWN`，不新增全域改名器。
- completion 必須保存可核對的來源身分、目的地、檔集、manifest、驗證工具與證據摘要，寫入後讀回。舊 completion 不改寫，新狀態以追加事件表達。
- 檔案驗證完成但 completion 寫入失敗時，回報「檔案已驗證、completion 尚未保存」；保留原檔，不重下、不手寫 completion。
- 命名／發布中斷使用 `resume`。只有來源、暫名、目標、journal 與 hash 可唯一對應才接續；目標既有內容、非屬合格環境附屬項的額外檔、symlink、inode／device 漂移或 hash 不符時 fail closed，保留原件，不重送下載。

## 六類狀態與貼文層 NO_MEDIA

媒體業務狀態只有以下六類：

| 狀態 | 意義與處理 |
|---|---|
| `COMPLETED` | 有完整下載、檔案驗證及不可變 completion；不重下。本機目錄缺席另以 `LOCAL_MISSING` 表示可用性，不改業務狀態 |
| `EXCLUDED` | 有同列表／貼文／媒體身分的有效排除決定；保留來源，不重下 |
| `PENDING` | 尚未派送的合格項；只有完整盤點與安全前置成立才排程 |
| `PREVIOUSLY_INCOMPLETE` | 前次明確停止但未完成；依原授權走恢復，不當普通新下載 |
| `UNKNOWN` | 可能已派送或結果無法確認；尚無 outcome 時先保存第一筆結果，已有 `outcome=UNKNOWN` 才調和；不重送、不建新 attempt 解鎖 |
| `PROTECTED_HISTORY` | 舊格式、證據不足、身分未定的歷史；保留來源，不升格完成、不默認排除、不重下 |

`NO_MEDIA` 是**貼文層級**標記，表示該貼文沒有照片／影片；它不是第七類媒體狀態，也不是下載完成。純文字貼文只保存必要索引，不建立 intent。

人工備份是來源註記，不是第七類。只有工具以完整證據認定完成才計 `COMPLETED`；只有人工聲明或證據不足時保留 `PROTECTED_HISTORY`。人工聲明不得覆蓋既有 `UNKNOWN`／pending，也不得自動變成 `EXCLUDED`。

## 本機可用性：LOCAL_MISSING 與 LOCAL_CHANGED

業務完成事實與目前照片區是否可用分開投影：

- `LOCAL_MISSING`：整篇完成目錄不存在。保留 `COMPLETED` 與禁止重下，回報「本機不可用；外部副本未驗證」。不要求外接硬碟在線或歸檔登記，也不因此把 completion 降格。
- `LOCAL_CHANGED`：目錄仍存在，但有部分缺檔、非屬合格環境附屬項的額外檔、檔名／大小／SHA-256／mtime／ctime 漂移、inode／device 改變、symlink、或 manifest／身分不符。此分類核對的是受管理完成媒體或其交易目錄；普通列表容器單獨的歷史 device 差異不會把媒體改列 `LOCAL_CHANGED`。保護原件，scope 外停止新派送並回報差異；只有 fresh `restart preview` 精確列出該篇且 Owner 明示確認該批後，才保留舊目錄並在新 `versions/gNNNNNNNN/` 目錄重建。仍不重下補帳、不原地覆寫、不重建空目錄、不手改紀錄。合格環境附屬項的存在、bytes 改變或消失不列入 witness、manifest 或媒體計數，也不改變 completion 或 `LOCAL_VERIFIED`。
- 目錄讀取權限異常、只有部分目錄可見或不能區分是缺席還是損壞時，不自動歸類為 `LOCAL_MISSING`；先保留阻塞並查證。

`LOCAL_MISSING`／`LOCAL_CHANGED` 都不是六類業務狀態，也不得自行解除 `UNKNOWN`、活動下載或未完成命名交易；只有精確 restart 批次可在已確認 scope 內以新版本重建 `LOCAL_CHANGED`。照片區可被 Owner 搬走或整個刪除；帳本、證據與 completion 必須留在照片區外。

`memory`／`summary` 的 `local_counts` 固定包含四類：`VERIFIED_PRESENT`、`LOCAL_MISSING`、`LOCAL_CHANGED`、`NOT_APPLICABLE`。回報本機可用性時應完整列示；只有 `LOCAL_MISSING`、`LOCAL_CHANGED` 是本機異常說明，四者都不是六類業務狀態。

## 恢復決策

| 前次實際情況 | 下一步 |
|---|---|
| `COMPLETED` 且檔案完整 | 跳過並讀回 completion；不重下 |
| `COMPLETED` 但整篇目錄缺席 | 保留完成，標 `LOCAL_MISSING`；不重下，不聲稱外部副本已驗證 |
| 完成目錄存在但部分缺檔／非屬合格環境附屬項的額外檔／漂移／symlink | 標 `LOCAL_CHANGED`，保護原件，scope 外停止新派送；只有 fresh restart preview 精確列出且 Owner 明示確認該批，才保留原檔並在新版本目錄重建 |
| 已下載完成、尚未 verify | 驗證現有檔案並保存 completion；不重下 |
| 命名／發布 journal 中斷 | `resume` 同一交易；不重送下載 |
| `STOPPED`／`NOT_SENT` 且未完成、原授權涵蓋恢復、帳本已持久化 `recovery_authorized=true` 且有充分停止證據 | 保留原檔，依 [下載與 notes CLI](download-and-ledger.md) 以 `intent --recovery-evidence` 建立另一個新空白恢復目錄及新 attempt；授權未持久化或證據不足時停止，已完成項跳過 |
| 已有 `outcome=UNKNOWN` 或 intent 尚無 outcome | 先以原事件、目的地與當次畫面／檔案查證；已有 outcome 才 `reconcile`，尚無 outcome 先保存第一筆真實結果。未收斂前不 verify、不重送、不建新 attempt、不派下一項；沒有新資訊就停止相同查證。只有 fresh restart preview 精確列出該媒體、Owner 明示確認該批，且 confirm 後完成新的完整 recovery scan，才可 `intent --restart-id`；舊 UNKNOWN／無 outcome 保留，不偽造 STOPPED |
| `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH` | Agent 出示精確列表、受影響貼文／媒體、已完成 sibling、舊版位置、新 `versions/gNNNNNNNN/`、額外空間及缺項／保留項；Owner 明示同意該 scope 才可 `restart confirm`。confirm 後以 `scan start --recovery` 完成新的完整 recovery scan，才逐項 `intent --restart-id`。同一已確認 scope 完成前再次中斷可從 `OPEN_BATCH` 找回，只對未完成或結果不確定的項目另建 attempt；scope／身分／目的地／版本策略改變要重新預覽與確認 |
| 普通 `created`／`destination` 列表只有歷史 device 值改變 | 沿原日常流程核對列表／貼文／媒體、path／inode／授權邊界及 ledger 狀態；不單獨拒絕、不呼叫 reattest。UNKNOWN、pending、已完成媒體或實際身分疑義仍照各自規則停止 |
| 有效 binding 已是 `list-directory-reattest`，path／inode 相同但 device 改變 | 執行唯讀 `reattest preview`。只在 `CONFIRMATION_REQUIRED`、完整 witness 與精確 scope 均可解釋，且 Owner 另行明示同意該 preview 後，才 `reattest confirm`。成功後完成新的 recovery scan，才接續原批次。每帳本最多一次；再次漂移或任何拒絕都停止，不換目的地或重送 |
| 單項來源已明確到期，最新 attempt 為 `STOPPED` | 以精確 attempt context 的 v2 evidence 追加 `source-unavailable`；該項列 `source_availability=EXPIRED`、`resume` 行動為 `SOURCE_UNAVAILABLE`，不建立新 intent、不排除、不計完成。不要推論其他項或把標記當成服務端已回收證明 |
| `scan_binding_match=false`／`SCAN_BINDING_REVIEW_REQUIRED` | 保留舊 scan、intent 與目的地；不改綁定、不自動新 scan、不另建 attempt。收集最小證據交人工審查 |
| 缺帳本、索引毀損或多個列表候選 | 保留原件與來源，停止相關寫入；不以空帳、重掃或改名解鎖 |
| 純文字貼文 | 記貼文層 `NO_MEDIA`，不做下載 attempt |

恢復只涵蓋原任務授權內未完成的項目，不重跑已完成清單，也不擴及另一個列表。新 attempt 的目的地必須是新的空白暫存／恢復目錄；原暫存、部分下載、舊 completion 與 evidence 全留。`STOPPED`／`NOT_SENT` 的 v2 recovery 與精確 restart 批次是兩條不同路徑：前者使用 `intent --recovery-evidence`，需要已持久化 `recovery_authorized=true` 與充分停止證據；後者需要 fresh preview、Owner 對精確 scope 的明示同意、`restart confirm`，以及 confirm 後新的完整 `scan start --recovery`。一般日常恢復授權、沉默、逾時或「繼續」都不是批次同意，`recovery_authorized` 也不能代替它。同一已確認批次涵蓋完成前再次中斷；scope、身分、目的地或版本策略改變須重新確認。即使有批次同意，也不宣稱舊 UNKNOWN 已停止；只有全部 candidate 驗證通過並 activation 後，新版本才成為目前結果。若原 Prompt 沒有涵蓋恢復、結果仍 UNKNOWN、帳本未持久化恢復授權或工具無法安全調和，停止並提出最小具體問題；不直接修改 ledger 取得授權。

## 合成測試與真實 GUI 的證據界限

notes 功能至少需以合成 fixture 覆蓋以下驗證，實際執行結果要保存命令、exit code、版本與輸出摘要。本文件不是測試報告；沒有當次實際命令與輸出證據時，這些項目一律 `NOT_RUN`，不得預填 PASS：

- 兩照片一影片端到端：初始化 → 盤點 → intent → outcome → verify → completion → 新 Session 查詢跳過。
- 重送拒絕、記事本當次下載控制（若 UI 顯示 Save All，須證明是本記事本自己的控制）單次限制、UNKNOWN `reconcile`、命名中斷 `resume`。
- 跨列表隔離、缺帳本、索引毀損與不開空帳。
- 完成後整個貼文目錄刪除仍不解鎖；部分缺檔、hash／身分漂移、非屬合格環境附屬項的額外檔與 symlink 保護。
- 來源重排、新增媒體、刪除媒體、編輯貼文與 `NO_MEDIA`。
- 有聲影片、無聲影片、截斷檔、解碼失敗、只有 attached picture／沒有有效影像、長影片 stall／等待。
- 舊 clean 與新 policy 非空 ffmpeg decode 診斷重開、legacy 非空拒絕、未知 policy／矛盾 stderr／偽造 coverage 拒絕；ffprobe stderr 仍嚴格。
- 照片完整解碼、非空檔、穩定前後 hash、非預期 stderr 與工具版本／binary hash。
- v2 evidence 父／子漂移、legacy 唯讀、page correction 與非目標 scope 拒絕；audit 完整性失敗 exit 4 且不投影業務狀態。
- 更正後 media key／數量／來源順序不變、v2 intent 使用 effective kind、合法 v1 相容與偽造 v1 拒絕。
- 單項 `SOURCE_EXPIRED` 維持欠件、禁止 recovery／intent，且未授權時不改完成／排除計數。
- 新 scan 的共享 coverage gate、未決 attempt／pending naming blocker，以及 resume scan binding mismatch 零檔案 mutation。

合成 fixture 的 PASS 只證明該次實作在該測試矩陣下的簿記、檔案與解碼行為；不證明真實 LINE 記事本畫面、下載按鈕、popup、chooser、混合附件、跨 Session 或使用者驗收。真實 GUI 場景必須另有一次正式任務及有效前景交接，才能標 `OBSERVED` 或進一步的 E2E；沒有當次執行就維持 `NOT_RUN`。

## 回報模板

每次完成、遇阻或暫停時分開列示：

```text
業務狀態：COMPLETED / EXCLUDED / PENDING / PREVIOUSLY_INCOMPLETE / UNKNOWN / PROTECTED_HISTORY
來源可用性：UNKNOWN / EXPIRED；未決 attempt：列出 action 或 NOT_APPLICABLE
貼文層：NO_MEDIA=...；本機可用性：VERIFIED_PRESENT=... / LOCAL_MISSING=... / LOCAL_CHANGED=... / NOT_APPLICABLE=...
工具簿記：命令、exit code、驗證範圍
檔案驗證：ImageIO / ffmpeg / manifest / completion
真人觀察：OBSERVED / 未觀察
真實 LINE E2E：PASS / FAIL / NOT_RUN（只在有當次證據時使用）
下一步：最小具體動作或阻塞
```

`dispatch_authorized=false` 不得寫成 GUI 已授權或 E2E 已通過；文件、合成測試與相簿既有經驗都不能替記事本實機結果背書。
