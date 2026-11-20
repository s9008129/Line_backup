# Issue #50：驗收阻塞後的下載閉環再分析

分析結果為 `ANALYSIS_COMPLETE`；產品與原備份仍為 `BLOCKED`。唯一建議路由是 `TARGETED_DIAGNOSTIC`：先以現有原生 Computer Use 做一個不下載的、能區分觀察能力缺口的有界診斷。這不是修復完成、舊 UNKNOWN 解鎖或新的驗收 PASS。

## 角色、版本與本輪範圍

Owner 指定 v4.9.0 `06_high_reasoning_review_prompt.md`，提供精確候選驗收封包及示範錄影，另要求分析完成後使用一個 GPT-6 luna helper 草擬詳細提交訊息並 add／commit／push。正式角色規則為：「This is diagnosis only: do not modify product files, execute the recommendation, waive a gate, start an Implementer, or trigger another review.」本輪依此完成分析與交付；「修復所有問題」尚未形成允許跨角色執行的修復計畫。本報告的建議不授予 GUI 或資料操作權限。

- Repository／branch：`Line_backup`／`feature/line-notes-media`；未切換或清理其他 worktree。
- 精確驗收候選：`d41a859301d976ca62e11b75d7c8def8577e58f6`。
- 本輪起始 HEAD：`81d813834dab525ec7902121374d5c8002991374`；起始工作樹及 index 乾淨，遠端精確 HEAD 相同。
- 兩版本差異只有既有 [acceptance.md](../20261101-notes-media-acceptance/acceptance.md)。本輪重新執行 `git diff --exit-code d41a859301d976ca62e11b75d7c8def8577e58f6 HEAD -- src tests .agents/skills`，exit 0。
- `git ls-tree -r <ref> src tests` 的 stdout SHA-256 在兩版本皆為 `ea3af92fd43cb22d792a47095731808e8dbfce4bd42d8562f5472adb760a9dac`。這是本輪明確定義的 listing 範圍，不與舊報告其他範圍的 digest 混比。
- 已讀專案 AGENTS、記事本 Skill／references、相簿隔離邊界、既有分析、計畫／實作／簡潔性報告、驗收及 Issue #50 原文與兩則留言。repo 沒有兩份指定 policy；本機全域的同版 `workflow-routing.md`、`subagent-model-policy.md` 存在且已讀，未建立 controller 或把全域政策當成日常依賴。
- 本輪沒有操作即時 LINE、讀寫真實 ledger、下載、建立 intent、outcome、reconcile 或更動完成事實。既有 219 events、187 篇、48 個已知媒體及兩張照片的現況數字均引用前輪驗收，沒有冒充本輪重新測得。

選定根因維持 **H50-OBS-01**：外部下載操作可能發生，但沒有足以歸屬及決定結果的證據，導致同列表後續新派送停止。來源為 [Issue #50](https://github.com/s9008129/Line_backup/issues/50) 與[後續技術補充](https://github.com/s9008129/Line_backup/issues/50#issuecomment-6555471050)。工具列隱藏、座標、滑鼠事件或 chooser 時序是候選觸發因素，仍未定位。其他 Issue 發現另列，不把它們硬併成同一根因。

## 第一性原理：缺的是什麼閉環

一項備份需分別成立：來源身分正確 → 控制當下可定位 → 輸入工具回傳 → App 有回應 → 結果屬於該 attempt → 檔案完整 → completion 保存與讀回。任一前項都不能直接證明後項。可歸屬的 chooser 是階段性 acknowledgement，檔案與終結訊號才支持進入驗證；不必宣稱每次滑鼠命中都可被獨立證明，才能承認已有正面結果。

目前負面觀測 O 是「未看到 chooser／進度／完成提示，原目的地空白」。O 同時相容於：

1. 輸入未命中／未送達，App 沒接受。
2. App 已接受，但 panel 延遲、觀察來源未涵蓋，或結果尚未落入目的地。

無法區分兩者時，重送可能重複副作用；宣告未送出可能錯誤解除保護；宣告完成可能製造假完成。`UNKNOWN` 因而是現有證據下的合理安全結果。增加等待、本機 UUID、dispatch marker 或空白目錄，本身都沒有區分兩種情況的新資訊。

**可證實的因果鏈**是：缺少可用結果證據 → 無法正當選 terminal outcome → UNKNOWN 保留 → 同列表新 intent 被拒絕。這解釋了停止前進；不證明原始點擊是哪個物理環節失敗，也不證明所有未完成項均由此造成。

## 錄影重新判讀

本輪重新讀取 Owner 提供的原檔。SHA-256 為 `54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6`，與前次研究相符；大小 270,929,956 bytes，時長 124.256667 秒，2294×1490，H.264，metadata 只有影像串流。`r_frame_rate=120/1` 不能用來假設每張來源影格等間隔。

先看完整時間範圍的 124 張每秒重採樣預覽，再針對 5–12、30–32、101–114 秒取得 43 張保留來源 PTS 的影格，另擷取三張原尺寸 PNG 確認 tooltip、chooser 與重播文字。這是分段取樣判讀，沒有宣稱看過每一張來源影格；預覽秒數不作精確事件時間，以下採來源 PTS。所有影像僅留專案私有任務區。

| 來源 PTS（秒） | 本輪影格所見 `OBSERVED` | 可支持／不可支持的結論 |
|---|---|---|
| 5.967 → 6.475 | 同一照片 viewer 由未呈現工具列，轉為呈現工具列與控制 | 控制可見性會改變；沒有事件 trace，不能指定由點擊、移鼠或等待觸發 |
| 9.258 → 11.033 | 控制附近有提示，後出現另存 chooser | 照片路徑存在可見的階段性回應；不能由兩影格差推定 App 延遲或保證未來時限 |
| 約 11–30 | 人工調整儲存位置、建立資料夾，最後確認儲存 | 包含人工路徑選擇；錄影沒有證明 Agent 已完成精確絕對路徑讀回 |
| 30.683、31.375 | chooser 關閉，viewer 呈現「下載完畢」 | 有正面 UI 終結提示；錄影未提供 SHA-256、完整解碼與 completion |
| 預覽約 34–47 | 切換另外兩張照片，各自再開 chooser、確認並返回 | 示範是逐項操作，不支持整份記事本可沿用相簿 Save All |
| 預覽約 55–68 | 另一篇照片再次走 viewer／chooser／儲存 | 不同貼文仍須分別核對來源，不能靠相似控制認領歷史 |
| 預覽約 73–101 | 列表捲動期間有 placeholder／載入，稍後縮圖才出現 | 空白或 placeholder 不足以判無媒體／已到底；沒有建立完整頂底及重疊覆蓋 |
| 102.133、102.642、103.658 → 104.167 | 影片 viewer 先黑畫面、spinner，後出現內容及時長／播放進度 | 延後訊號真實存在；不是本次錯記 19 項的失敗錄影，也沒有同步 AX |
| 105.683 → 106.700 | 原尺寸圖確認「另存新檔」tooltip，後有 chooser | 影片也存在單項另存路徑；不能證明本案舊 UNKNOWN 未送達 |
| 108.217 → 108.750 | chooser 隨後關閉；viewer 出現「重播」，播放時間到結尾 | 重播是播放終止，不能記 DOWNLOAD_FINISHED；沒有獨立影片檔驗證 |
| 111.792、112.800 → 113.300 | 下一項亦先載入，後出現內容及播放控制 | 再次支持等待就緒、重新觀察的必要性；不提供通用固定等待秒數 |

錄影是 10 月 26 日示範，UNKNOWN 發生於之後的實機工作。錄影未建立同篇照片／影片混合附件的完整覆蓋，未提供原始 CUA 呼叫／App 內部 receipt、失敗當時版本或下載後媒體檔；不能用示範片替 Issue 裡的媒體重新分類或解鎖原 attempt。

## 程式與證據直接核對

以下位置綁定本輪起始 HEAD 的 `src/line_backup_batch/notes.py`：

| 程式位置 | 直接事實 | 診斷含意 |
|---|---|---|
| 132–159 | kind 存於 media identity，identity 參與 media_key hash | 種類不是可任意更改的顯示欄位 |
| 297–342 | evidence 檔內容定址保存，讀回核對 bytes／hash | 保護已保存文字的位元；不解析文字內 screenshot 引用或判斷 GUI 真實性 |
| 1788–1832、1870 起 | post／media 有 session、scan、唯一盤點及一致性檢查 | UNKNOWN 的跨媒體拒絕不在這兩個盤點入口；183 篇未細盤不能全歸因於下載 blocker |
| 1984–2000 | 無 outcome 得到 None；已有 UNKNOWN outcome 得到 UNKNOWN | 兩者內部有區分；memory 的同名狀態不是原始點擊感測 |
| 2227–2247 | 同媒體 recovery 需 STOPPED／NOT_SENT；其他未完成 attempt 亦檢查 | blocker 是同一列表帳本，包含已下載但未完成驗證者，不是整機鎖 |
| 2254–2269 | intent 回傳 UNKNOWN、count=0、dispatch_authorized=false | 預寫保護不證明外部是否已派送，count 不是實際 GUI 次數 |
| 2279–2312 | 第一筆 outcome 不可重寫；UNKNOWN 可 reconcile 至允許的結果 | 不是 UNKNOWN 吸收態；缺外部證據，沒有少一個 escape flag |
| 2315–2354 | 有 attempt 的排除／保護須先為 STOPPED／NOT_SENT | 不能把 UNKNOWN 換成排除來繞過 |
| 2911–2913 | verify 前結果必須是 DOWNLOAD_FINISHED | 解碼或驗檔不能作為 UNKNOWN 的替代派送入口 |

**新增有界診斷：**本輪只呼叫純身分函式，以合成 list／post／visual_key 計算兩次，唯一差異為 PHOTO 與 VIDEO。輸出 `kind_change_changes_key=true`，exit 0，未載入 ledger、未寫 event。這只確認 key 設計；沒有重現真實分類錯誤。

由此推論：直接改種別再重新登錄，會產生另一 key，不能假設原 completion／attempt 自動跟隨。既有「種類錯記」若修復，需先處理歷史來源與關聯相容性；不可把錯記項當成全新的可下載項。尚未判定種類的新項，應先保留待辨識，不能以「沒看到影片訊號」等同 PHOTO；這不代表可在目前 schema 增加第七類狀態。

## 既往嘗試與本輪新增資訊

| 階段 | 已有結果／新資訊 | 不應重複的動作 |
|---|---|---|
| 原 attempt 的單次下載輸入、UNKNOWN outcome、再調和 UNKNOWN | 仍無可歸屬結果；下一 intent 回傳 ANOTHER_MEDIA_ATTEMPT_UNRESOLVED | 不再按同下載座標、重送 intent、換空目錄或重複等待來探測已知 gate |
| 先前工具列唯讀觀察 | 一次能顯示，另次不能，撤回「點一次必顯示」通則 | 不繼續點中央累積同樣負面資訊 |
| 前輪 H50-OBS-01 分析與規劃 | 已釐清有 reconciliation 出口、blocker 範圍、不可憑空目錄解鎖 | 本輪不把它們包裝成新發現 |
| 46225a2 文件切片及後續簡潔性審查 | 補控制預檢、觀察範圍、證據範本及判定案例；src／tests 沒改 | 審查 PASS 不等於下載閉環或舊資料修復 |
| d41a859 的獨立驗收，報告提交 81d8138 | 既有 UNKNOWN 仍阻擋；82 notes／73 daily 與兩張照片解碼是前輪結果 | 文件切片本就不承諾清除舊 UNKNOWN，不能把仍阻塞當成程式修復回歸 |
| 本輪重看示範及源碼、有界純函式計算 | 獨立確認影片載入／重播分界，具體確認 kind 改變 key；釐清未細盤不是 intent gate 的直接結果 | 不能用新示範證據補造原點擊瞬間事實 |

原根因嘗試總數與原始工具 trace 不完整；不宣稱還剩幾次額度。本輪新 GUI／下載／ledger attempt 均為 0。不建議重複已連續無新資訊的手法。

## 因果假說、替代原因與反證

| 假說 | 現有支持與限制 | 能區分它的證據 |
|---|---|---|
| 工具列隱藏導致未命中 | 錄影及舊觀察支持可見性變化，沒有原點擊同時證據 | 同一時序的畫面來源、有效映射、原始輸入紀錄及 App 後續結果 |
| scale／視窗位移／遮擋造成錯位 | 合理風險，未證實發生 | 來源像素、座標空間、frame／映射與前景的同次綁定 |
| App 已接受，但 chooser 未被觀察 | 未排除，也沒有證據證明確實發生 | 對比 app-bound 與工具支援的最小桌面區域觀察，保留各自範圍與時間 |
| 狀態機 mutex 死鎖 | 不支持；現有行為是業務拒絕且有合法出口 | 等待鏈才可支持 mutex 問題，現有 refusal 不足 |
| LINE 下載功能全面失效 | 示範與前輪成功照片反駁普遍性 | 仍不能由其他項成功推定本項結果 |

若取得原 attempt 可歸屬、可信的完成／停止／未送達正面證據，「本案無法選 terminal outcome」就必須更新，評估現有 reconcile；若只能找到按鈕存在或另一次成功，則沒有反證本案的未知。

縮小 blocker 也不是免費修法：下一項共用 LINE 前景、viewer／chooser 通道；舊 panel 晚到可能被誤歸下一項。只有先證明結果不會交叉認領，才可能重新評估串行邊界。新目錄或新 media_key 本身不提供此保證。

## 最佳實務與其他發現的處置約束

以下是分析約束與待規劃要求，不是第二條派送路由或本輪已執行修復。

- timeout／失敗不排除副作用；重試要依賴被呼叫方承認的冪等契約。AWS 描述由服務識別 caller 的 request ID；本機 attempt ID 未被 LINE 接收，不能類推為 LINE 已去重。[AWS timeout](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)、[AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)。套用到本案 GUI 的限制是本報告推論。
- AX hit-test 回答當時位置最上層的 AX object。這不建立「截圖→檢查→稍後輸入」的原子交易，也沒有證明現有 CUA 提供該 API。[Apple AX hit-test](https://developer.apple.com/documentation/applicationservices/1462077-axuielementcopyelementatposition?language=objc)。AX action 網頁只取得 JS 外殼，Markdown 連結 404；本輪不以其未讀到的正文新增事實。
- Apple 的 FSEvents 指南描述可合併的變更通知；不能把 filesystem observer 當成 LINE 的 request receipt 或內容完整證明。[Apple FSEvents](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/TechnologyOverview/TechnologyOverview.html)。本案檔案歸屬限制是推論，不是已實作 observer。

| Issue 未解項 | 應滿足的修復／驗證約束 | 本輪界線 |
|---|---|---|
| PHOTO／VIDEO 延後辨識 | 以正面種類訊號及 viewer 來源交叉核對；等待就緒不等於固定 sleep；舊 key／attempt／completion 關聯必須保全 | 合成 key 計算與示範觀察，沒有更正真實種類 |
| 影片來源期限已到 | 可歸屬的明確到期提示與無未決寫入才支持停止；單項不能推廣全篇。保留不可取得事實，不能靠重試創造服務端來源 | 沿用既有 STOPPED，沒有新到期重現；不自動排除或宣稱完成 |
| evidence 內部引用 hash 錯誤 | 區分外層文字完整與其所引原件完整；新引用應由工具計算、比對、保留原件，以唯一且拒覆寫的輸出保存 | 現有範本仍由 Agent 執行，非程式強制；本輪沒有新增 parser、整帳稽核或覆寫 correction |
| refusal／成功輸出覆寫 | 保存每次 argv、stdout／stderr、exit，輸出唯一且不可覆寫；覆寫後丟失的原資訊不能由成功輸出還原 | 未發現新覆寫事件，未補造缺失輸出 |
| summary EAGAIN | 唯讀 lock 競爭需保留當次退出碼及 holder 證據，不能推定與 GUI UNKNOWN 同根因 | 只有既有一次錯誤與後續成功報告，本輪未再執行 summary |
| 183 篇詳細盤點缺口 | 清單掃描、貼文內容、每項種類與下載結果分開對帳；UNKNOWN 不能把未盤項算完成 | 沒有 GUI 授權，未補盤；不可宣稱只解一筆就整份完成 |

針對所有問題直接加自動重試、強制解鎖、改 kind 或繼續其他項，都會先改變安全／身分邊界。目前沒有支持這些改動的核准計畫；不能把前輪「文件證據流程」計畫當成程式或資料遷移授權。

## 唯一建議路由：TARGETED_DIAGNOSTIC

**目的：**在已完成文件改進之後，取得之前沒有的「同一當前 viewer、不同觀察來源及工具座標契約」對照，判定現有原生 CUA 能否提供可用的當次控制定位與可明確描述的 popup 觀察範圍。先確認能力，避免再重寫相同證據文件。此診斷不承諾解除舊 UNKNOWN，也不聲稱會證明 App 下載 acknowledgement。

**有界範圍與產物：**由 Owner 在另一主 Session 明確授權一個不下載的診斷，交接同一列表的已知 viewer。讀當次工具文件，只使用已提供 API。保存起始頁面／前景、app-bound 畫面與 AX、工具文件允許且只涵蓋該 viewer 的桌面局部畫面，各來源的時間、範圍、像素與座標映射。若需要移鼠來觀察 hover，授權範圍僅為已定位的 viewer 內單次移鼠並重新觀察；不得點擊圖片中央、下載、分享、chooser 或猜快捷鍵。不讀 LINE 私有資料、不改產品、不寫真實 ledger、不建新 attempt。

這個實驗只測「同次觀察是否涵蓋真實可見控制、能否支持當次映射」。若沒有 chooser 正在存在，對 chooser 可觀察能力只能記 `NOT_RUN`；不能為了觀察而開啟新下載，也不能靠推論填滿能力表。

**成功檢查：**

1. 一份 observation pair 與 capability 表，清楚區分哪些資訊由工具提供、哪些 UNKNOWN，指出 app-bound 是否漏掉局部畫面中可見的控制，並有原件 hash。
2. 控制可見且映射有依據，或具體證明當次能力不足；兩者都比重複「沒看到 chooser」多出可用資訊，均不等於下載 PASS。
3. 下載控制／chooser 確認／新 attempt 為 0，沒有改變既有 UNKNOWN／完成事實。若仍無新資訊，記錄結果即停止，不展開顯示工具列的反覆輸入迴圈。

**停止條件：**前景中斷、身分／觀察範圍或映射不明、工具不支援所需能力、必須點下載才能繼續、需要新 controller／observer／私有 LINE 資料、需改 blocker 或資料語意、工具拒絕，立即停止依賴該前提的動作。不換列表或目的地、不重送原 UNKNOWN。

**所需人工決定：**是否在獨立主 Session 啟動上述診斷，並明示其觀察／單次移鼠及前景邊界。取得結果後，由 Owner 決定後續正式角色與程式／資料修復計畫；本輪不派送下一角色。

## 實際檢查與證據

原始診斷保存在 `.local/line-backup/tasks/20261101-notes-result-closure-review/`，包含 Issue 快照、source-identity、PTS extraction log、三張原尺寸影格、合成 identity 計算及 evidence manifest。公開文件不含原始影像、原始媒體檔名、人物／列表名稱、內部 ID 或真實帳本路徑。下表 `<SOURCE_VIDEO>` 是去識別化占位符，確切 argv 留本機命令紀錄。

| 實際動作／命令 | Exit／結果 | 證據限制 |
|---|---|---|
| `pwd`、`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list` | 各 exit 0；起始乾淨 | 未修改其他 worktree |
| `git ls-remote origin refs/heads/feature/line-notes-media` | exit 0，81d8138 完整 SHA 相符 | 提交前遠端身分核對 |
| 候選到 HEAD 的 src／tests／Skill diff、listing hash | exit 0；無差異 | 不是當前產品的重新驗收 |
| GitHub connector fetch issue／comments | 兩次皆 isError=false | 唯讀，沒有發布 Issue 留言或改狀態 |
| `ffprobe -v error -show_entries format=duration,size,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate -of json <SOURCE_VIDEO>` | exit 0；metadata 如上 | metadata 不是下載影片完整驗證 |
| Homebrew ffmpeg／ffprobe `-version` | exit 0；兩者皆 7.1.1 | PATH 裸 ffmpeg 另指其他位置，實際擷取使用 Homebrew 絕對路徑 |
| ffmpeg 每秒預覽、PTS select／showinfo／tile、原尺寸影格擷取 | 皆 exit 0；124 預覽、43 PTS、3 PNG | 離線示範判讀 OBSERVED；無即時 GUI |
| Python SHA-256 讀取示範／來源及私有 manifest | exit 0 | hash 不證明敘述語意或服務端位元 |
| `PYTHONPATH=src /usr/bin/python3 -B -` 合成 identity 計算 | exit 0；kind 改變 key | 純函式診斷，未讀真實帳本 |
| Pillow montage 準備 | 兩次 exit 1，ModuleNotFoundError | 環境沒有 PIL；停止此方法，改用既有 ffmpeg，未安裝套件 |
| 產品 unit tests、notes --help／summary／resume、ImageIO／下載媒體 ffmpeg | `NOT_RUN` | 前輪結果保留；報告分析沒有產品改動，不重做驗收 |
| 即時 LINE、chooser、popup、混合附件、跨 Session E2E | `NOT_RUN` | 本輪無對應備份與前景交接授權 |

本輪成果僅本任務的分析與 progress 文件。報告完成後，已使用一個 helper 讀取本輪分析、既有計畫／驗收與私有診斷 JSON，完成詳細提交訊息草稿；主 Session 已讀回複核。派送 request 明確指定 Owner 選擇的 `model=gpt-6-luna`，平台回傳 task 名稱並交付 helper 結果；沒有 provider usage 或可獨立驗證的 backend 身分。本輪沒有其他 helper，亦不把它當成獨立審查／acceptance，不宣稱成本或 token 節省。

交付前兩份文件相對連結解析檢查 exit 0；`git diff --check` exit 0；原尺寸影格由 `git check-ignore` 證實位於忽略範圍。Git 最終交付結果另保存在本機交付紀錄與回覆，避免文件自含未來 commit SHA。

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PARTIAL
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

獨立驗收 BLOCKED 延續精確候選的既有結論；本輪沒有進入新 Acceptance。PARTIAL 指有界診斷與來源核對完成，其他必需實機驗證未完成。「分析完成」不等於使用者最終目標已修復或任務 DONE。
