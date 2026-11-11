---
name: line-notes-agent-cua
description: 由 AI Agent 以原生 Mac Computer Use 判讀使用者交接的 LINE 記事本列表，完整盤點貼文與照片／影片，逐項下載、驗證、跨 Session 接續及恢復中斷；亦用於審查與優化此備份流程。
---

# LINE 記事本照片與影片備份

本 Skill 由 AI Agent 使用原生 Mac Computer Use 判讀當次畫面、選擇下一步，並以輔助 CLI 保存追加式紀錄與驗證結果。目標是完整、可核對且可接續地保存**單一指定記事本列表內所有貼文的照片與影片**；貼文文字只作索引，留言、貼圖、連結及其他聊天內容不納入。

LINE 記事本與相簿是不同的產品物件、畫面入口與操作流程。本 Skill 不修改、放寬或替代相簿 Skill 的 `⋯ → 儲存全部` 唯一入口，也不把相簿的選單、按鈕、chooser 或座標當成記事本流程的 fallback。記事本若出現批次下載控制，仍須依本 Skill 與當次畫面重新證明其出處與作用。

本 Skill 的落檔本身不代表 notes CLI、GUI 操作或真實 LINE E2E 已驗證。未實際執行的能力一律標 `NOT_RUN`，不把文件規範寫成 PASS。

## 日常入口與 Agent 責任

Owner 先人工開啟指定的 LINE 記事本列表，指定目的地（未指定時使用本專案 `backup/記事本/`），並在同一次正式 Prompt 中授權備份及交接有效前景。這次提交同時是任務授權與當次前景交接，不要求 Owner 再選盤點／接續模式、逐篇下令，或手填 UUID、內部 key、JSON。

Agent 的任務是完成整份列表，而不是等 Owner 逐步操作：

1. 自動查全部記事本帳本、目前任務與相符的永久記憶，先讀 `summary` 的 `unresolved_attempts`、`dispatch_blockers` 與掃描覆蓋。
2. 核對列表；證明是新列表且沒有缺損歷史或候選歧義時自動初始化，既有列表則綁定原帳本。新掃描前先處理舊 attempt；掃描綁定不符時只做唯讀查證並停止待人工審查。
3. 先建立來源卡片台帳，從頂端到底端完整盤點貼文，頁前雙向對帳，再逐篇核對照片／影片；盤點是下載前必要階段。
4. 依紀錄跳過已處理項，對每個合格項只送出一次下載派送，並在結果後驗證、發布及讀回 completion。
5. 遇到已授權的中斷恢復時，保留原檔並自動接續或建立新的空白恢復 attempt；UNKNOWN、活動下載及未完成命名交易先查證，不以重下解鎖。
6. 最後重新對帳，主動回報總數、逐篇狀態、缺項、已驗證內容及未測範圍。

只有「實際備份任務授權＋有效前景交接」才允許 GUI 輸入。討論 Prompt、審查 Skill、整理文件或單純交出前景本身都不是下載授權；前景中斷時停止所有 GUI 輸入，重新交接也不解除既有 UNKNOWN。

查歷史、初始化或讀寫紀錄不是下載授權；notes CLI 回傳的簿記成功也不是 GUI 授權。若 notes CLI 尚未存在、`--help` 失敗或當次 repo 沒有相符實作，停止依賴該命令的動作，如實回報 `IMPLEMENTATION_NOT_AVAILABLE`；不得手寫事件 JSON、另建空帳或換入口繞過。

## 永久記憶與路徑邊界

- 永久紀錄預設在 `notes-backup-records/`，依 `local_list_id` 分帳本；`index.json` 只登錄位置，追加式 `events` 才是事實來源。
- 每份帳本包含 `list.json`、`store.json`、`events/`、`evidence/` 與 `.lock`；必要證據與 completion 不放在照片區。
- `.local/line-backup/active-notes-task.json` 只協助定位最近任務，不是唯一歷史入口。
- 照片與影片預設在 `backup/記事本/<列表顯示名與短識別碼>/<貼文日期摘要與短識別碼>/`；顯示名稱只供顯示與目錄，不作身分認領。
- 目的地以追加綁定處理；新目的地不得解除 UNKNOWN、pending 或現存檔案異常，也不得重寫舊 completion 路徑。
- 不讀舊開發資料、封存索引或 Git 歷史作日常狀態，不用名稱、日期、張數、序號或單一檔案 hash 跨列表合併。

## 三層身分與不可重下原則

身分固定分為**列表 → 貼文 → 媒體**三層。Agent 保存當次觀察，CLI 產生並回傳對應 key；Owner 不接觸內部 JSON。任何中文標題、日期、貼文文字、總數、畫面序號或檔案 SHA-256 都不能單獨認領歷史。

- 列表身分須由本次連續入口、當次畫面／AX 脈絡及相符帳本共同支持；疑似另一個列表時停整份工作，不用群組中文名稱或 OCR 搜尋、選擇、核准。
- 貼文身分須交叉核對卡片位置、相鄰貼文、日期、媒體縮圖、更多指示及貼文內容脈絡；來源順序可以變動，舊完成事實不因重排而改寫。
- 媒體身分須交叉核對所屬貼文、媒體順序、縮圖及 viewer 脈絡；外觀、內容 hash 或檔名相同仍可能是不同來源項，不得自動去重。
- 新增媒體只補可唯一辨識者；完成後重新編號取該貼文目前最大編號加一，不重命名舊完成檔。
- 局部貼文歧義時保護該篇並繼續其他已核對項；列表覆蓋、入口或列表身分不明時停止整份新派送。

## 工作流程

1. **找回前次任務。** 先查全部記事本帳本與 active-notes-task，再讀相符帳本的 `memory` 摘要。不能用缺少帳本、索引缺失或 active-task 不存在推論為空帳。新列表須有完整、無歧義的新列表證據：固定同一組 identity 先執行 `list-key`，以該 key context 建立兩份 v2 evidence，再以相同 identity `init` 並讀回 key。新／既有列表都須核對當次入口與有效前景後 `bind`，再依 [下載與 notes CLI](references/download-and-ledger.md#啟動與帳本對帳) 處理舊 attempt／命名交易。普通情境先收斂舊項再 `scan start`；若已確認 restart 批次，則在 `restart confirm` 後先中斷尚未結束的 scan，再以 `scan start --recovery` 建立新的完整 recovery scan，普通 scan 不得用來掩蓋舊問題。不能在未綁定時先寫 outcome／reconcile，也不重用舊 Session ID 繞過綁定拒絕。`memory` 不含完整 attempt、staging 目的地或 completion manifest；交易細節以 `intent`／`verify` 結果及追加事件為準。新一批目的地以 `destination` 追加，保留舊完成路徑。
2. **判定入口。** 在有效前景交接內用當次 AX／畫面確認目標是記事本列表，不是相簿、聊天、貼文檢視器或出處不明頁面。需要返回時只使用當次可靠控制項或已證實且符合角色／焦點的快捷鍵；不得猜 Escape、Command-W 或關閉。入口未確認前不捲動、不盤點、不下載。
3. **完整盤點與頁面覆蓋。** 依 [GUI 導覽與盤點](references/gui-inventory.md) 從頂端到底端，以有序重疊避免漏篇；先保存來源逐卡紀錄，再產生 page rows，呼叫 `page` 前完成來源↔rows 雙向對帳。逐篇核對媒體縮圖、更多指示、viewer 與來源順序；viewer 尚未就緒時不定位下載控制、不先建媒體身分，也不以黑底、disabled slider、`00:00` 或缺少影片控制判定種類。只有來源覆蓋、頂底、重疊、篇數與逐篇媒體覆蓋已成立，才可產生合格下載排程。純文字貼文記 `NO_MEDIA`，不得當成下載完成。
4. **一次一項下載。** 依 [下載與 notes CLI](references/download-and-ledger.md) 在 intent 前確認資格、來源及記事本控制；為每次 attempt 保存並讀回 intent、新空白暫存目錄及禁止重送紀錄，讀回後在輸入前再次定位同一列表／貼文／媒體／viewer／控制。**每個 attempt 的下載控制呼叫與 chooser 最終確認各最多一次**，兩者分開保存真實工具回傳；若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不得沿用相簿入口。chooser 須可歸屬同一 attempt、精確讀回完整暫存路徑後才確認一次。
5. **結果、驗證與命名。** 先查該 attempt 是否已有 outcome／UNKNOWN：沒有 outcome 時用 `outcome` 記錄第一筆真實結果（可為 UNKNOWN）；已有 `outcome=UNKNOWN` 才用 `reconcile`。沒有精確確認批次時，未收斂不得 verify、建立新 intent、重下或派下一項；只有 `DOWNLOAD_FINISHED` 才能 `verify`。命名／發布交易中斷用 `resume` 接續同一交易，絕不重下。若完整盤點後 `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH`，依下列確認取代流程處理；檔案驗證見 [驗證與恢復](references/verification-and-recovery.md)。
6. **逐項循環與結束對帳。** 完成一項後保存並讀回 completion，重新觀察原貼文／列表，再定位下一個合格項。遇到新媒體、重排、刪除、編輯或檔案異常時先更新盤點與狀態，不覆寫舊完成事實。最後先重讀本輪原件，依 GUI 本文核對各 page 讀回與有序去重聯集，再以 `summary` 與當次畫面交叉核對；只有覆蓋完整且所有未解類別已誠實列出，才回報本次工作結果。

page 前的來源卡片台帳、部分／高卡片、雙向對帳及 finish 前原件重核，以 [GUI 導覽與盤點](references/gui-inventory.md) 為唯一操作本文。CLI 只檢查已提交 rows 的內部一致性；來源對帳未成立時，即使工具能接受，也不得提交 page／finish 或開始新派送。

## 下載與恢復的硬邊界

- 一次只處理一個貼文／媒體 attempt；不得平行派送多個下載。
- intent 一旦持久寫入，就按「可能已派送」對待；在 `outcome` 有正面證據前，禁止第二個下載派送，也不得把工具逾時、畫面未變或舊計數為零當成 `NOT_SENT`。
- `outcome` 的第一筆結果不可任意改寫。尚未寫 outcome 時先以 `outcome` 保存第一筆真實結果；只有帳本已有第一筆 `outcome=UNKNOWN` 時才用 `reconcile` 查原事件、目的地與當次狀態。未收斂前不得 `verify`、建立新 attempt 或重下。
- 定位、input 原始回傳、App 階段性回應、下載結果、檔案驗證與 completion 是不同命題；只有可歸屬的正面證據組合能前進。timeout、畫面未變、空目錄、缺少 marker、API 成敗或播放結束都不足以判未派送或完成，詳見 [證據與允許行為矩陣](references/verification-and-recovery.md#證據與允許行為矩陣)。
- 新寫入的事件證據必須是 `evidence-pack` 產生且由 CLI 回傳的 `line-notes-evidence/v2` bundle；不手寫 bundle、不改內部 JSON／hash。`evidence-audit` 只作唯讀引用稽核；完整性失敗時 exit 4，且不得把一般 `summary` 或 audit 的局部結果當成可信業務投影。`evidence-correct` 只修 page 引用，保留 page 成員、順序、頂底與 scan 覆蓋；`media-kind-correct` 只處理尚無任何 attempt 的已盤點媒體，不改 key、貼文、順序或數量。兩者都不是日常自動動作，真實帳本仍須精確資料授權與證據。
- 只有原 attempt 已確認 `STOPPED`／`NOT_SENT`、原檔保留、帳本已持久化 `recovery_authorized=true`，且具充分停止證據時，才可依 [下載與 notes CLI](references/download-and-ledger.md) 以 `--recovery-evidence` 建立該項的新空白恢復 attempt；現行 CLI 沒有事後改寫此授權的命令，未持久化時停止，不手改 ledger。已完成項跳過。
- 沒有精確確認批次時，`UNKNOWN`、活動下載、未完成命名交易與 `LOCAL_CHANGED` 仍依原規則停止。若 `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH`，Agent 先用白話列出精確列表／受影響貼文與媒體／舊版位置／新 `versions/gNNNNNNNN/` 路徑／額外空間／缺項與保留項，取得 Owner 明示同意後才可 `restart confirm`；沉默、逾時或一般「繼續」不是同意。confirm 後必須完成新的 recovery scan，才可逐項 `intent --restart-id`；同一媒體的新 generation 可成為目前 active，舊 confirmation、candidate、activation、completion 與 UNKNOWN 歷史全部保留。同一確認批次涵蓋完成前再次中斷；scope、身分、目的地或版本策略改變須重新預覽與確認，不能把一次同意擴成無限重送。`dispatch_authorized=false` 不是 GUI grant；新 attempt 仍使用新的空白 staging，不沿用舊 chooser、路徑或座標。
- 普通 `created`／`destination` 列表綁定的 path、inode、canonical、非 symlink 或授權邊界不符時停止。只有列表容器歷史 `device` 值與目前不同，不單獨阻擋 intent；notes 仍逐項核對 staging、完成檔、active version 與發布交易的身分及完整性。UNKNOWN、活動下載、pending 命名交易及跨列表風險照原規則停止，不能藉此重送或覆寫。
- 若有效 binding 已是 `list-directory-reattest`，依既有 `reattest` 規則保留 device／inode 嚴格核對：只處理合格既有 OPEN_BATCH，必須有完整 witness 與 Owner 對精確 preview 的明示同意，confirm 後完成新的完整 recovery scan。每帳本至多一次；轉接後再次漂移、preview 拒絕或 session／scope 不符時停止，不換目的地、不重送。普通新下載不新增 reattest 或 Owner 確認步驟。
- confirm 會寫入新版事件；舊版 CLI 讀到後會拒絕。首次真實 confirm 前核對後續 session 使用相容版本；寫入後不刪事件、不回退成空帳。
- 來源已明確到期且原最新 attempt 為 `STOPPED` 時，才可追加 `source-unavailable`；它只記 `SOURCE_EXPIRED`，不是完成、排除、重試授權或服務端已回收的證明。該項不得再建立 intent，其他項仍受列表級 blocker 約束。
- 命名交易、暫名與目標身分可唯一核對時用 `resume`；無法唯一下一步時保留原檔與 pending 證據並停止，不手動改資料夾或重下。
- 已完成事實與本機可用性分開：整篇目錄缺席記 `LOCAL_MISSING` 並保留完成、禁止重下；目錄仍存在但有缺檔、非屬合格環境附屬項的額外檔、hash／身分漂移或 symlink 時記 `LOCAL_CHANGED`。`LOCAL_CHANGED` 僅可在精確確認批次 scope 內保留原檔並複製到新版本目錄重建；scope 外仍停止新派送。
- 六類業務狀態為 `COMPLETED`、`EXCLUDED`、`PENDING`、`PREVIOUSLY_INCOMPLETE`、`UNKNOWN`、`PROTECTED_HISTORY`。`NO_MEDIA` 是貼文層級標記，不是第七類，也不是下載完成。
- 不發訊息、刪除、分享、覆寫照片或變更舊完成事實；不擴及其他列表。工具拒絕、身分歧義、寫入衝突或不明派送時停止依賴該前提的動作，不換入口繞過。

同一根因最多三次有證據嘗試；連續兩次沒有新資訊就停止相同方法，不用重試消耗次數。外部成員或程序可能改動來源，不能承諾原子快照、OS 隔離或 exactly-once。

## 回報與證據界限

在「歷史／入口核對完成、完整盤點完成、每個貼文／媒體完成或遇阻、最終對帳」節點主動用繁體中文回報，內容至少包含：

- 列表與貼文總數、來源逐卡對帳結果、未解卡片／缺頁、`NO_MEDIA` 篇數、六類媒體狀態及目前項目。
- 已驗證照片數、已驗證影片數、未解缺項及下一步。
- 工具簿記結果、ImageIO／ffmpeg 解碼結果、真人 `OBSERVED` 與真實 LINE E2E 分別列示。
- `dispatch_authorized=false` 只是簿記欄位，不是 GUI grant、實機 PASS 或獨立驗收。

工具簿記 PASS 只證明帳本／摘要的輸入與投影一致；ImageIO／ffmpeg 只證明指定檔案可解碼及其驗證範圍；真人觀察只能記 `OBSERVED`；真實 LINE 記事本下載、混合附件、跨 Session 與 chooser 在沒有當次正式任務及有效前景時一律 `NOT_RUN`。合成 fixture 的測試通過不代表真實 LINE 已支援。

審查本 Skill 時只做文件、格式與離線檢查，不啟動 LINE、不讀私人照片／帳本，也不把審查意見寫成 E2E 或 acceptance。

## 參考文件

- [GUI 導覽與盤點](references/gui-inventory.md)：入口、三層身分、已展開卡片／縮圖／viewer 交叉、B1 載入與種類就緒、AX／capture 來源分界、工具列觀察、popup、時鐘、座標映射、控制與輸入規則。
- [下載與 notes CLI](references/download-and-ledger.md)：目前子命令與參數、`list-key` 建帳前 bootstrap、絕對證據路徑、`lists`→`summary` 查詢、capture、intent 前後核對、下載／chooser 各最多一次、outcome／reconcile 分流、更正與命名恢復。
- [驗證與恢復](references/verification-and-recovery.md)：證據稽核／更正、完成／停止證據組合、AX／截圖提示分離、檔名歸屬、類型更正、來源到期、照片／影片解碼、六類狀態與本機可用性。
- [證據範本](references/evidence-template.md)：供 `evidence-pack` statement 使用的私有紀錄欄位、AX scope、chooser 三層目的地與唯一檔名規則；不是可直接傳給 `--evidence` 的自由文字 schema。
- [證據判定案例](references/evidence-decision-cases.md)：控制隱藏、API error、chooser 延遲／預填路徑、晚到結果、播放結束、crash window 與充分／不足證據的假設案例。
