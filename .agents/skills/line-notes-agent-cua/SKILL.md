---
name: line-notes-agent-cua
description: 由 AI Agent 以原生 Mac Computer Use 判讀使用者交接的 LINE 記事本列表，完整盤點貼文與照片／影片，逐項下載、基本檔案檢查、跨 Session 接續及恢復中斷；亦用於審查與優化此備份流程。
---

# LINE 記事本照片與影片備份

本 Skill 由 AI Agent 使用原生 Mac Computer Use 判讀當次畫面、選擇下一步，並以輔助 CLI 保存追加式紀錄與基本檔案檢查結果。目標是完整、可核對且可接續地保存**單一指定記事本列表內所有貼文的照片與影片**；貼文文字只作索引，留言、貼圖、連結及其他聊天內容不納入。

LINE 記事本與相簿是不同的產品物件、畫面入口與操作流程。本 Skill 不修改、放寬或替代相簿 Skill 的 `⋯ → 儲存全部` 唯一入口，也不把相簿的選單、按鈕、chooser 或座標當成記事本流程的 fallback。記事本若出現批次下載控制，仍須依本 Skill 與當次畫面重新證明其出處與作用。

本 Skill 的落檔本身不代表 notes CLI、GUI 操作或真實 LINE E2E 已驗證。未實際執行的能力一律標 `NOT_RUN`，不把文件規範寫成 PASS。

## 固定任務與允許操作

日常任務只做：核對指定目標 → 找到下載控制 → 下載一次 → 基本檔案檢查 → 保存結果 → 下一項。Agent 不自行擴充成播放、內容檢視、來源種類取證或完整解碼任務。

允許列表導覽、展開貼文、開啟目標 viewer、切換目標媒體、使用明確工具列控制顯示下載工具列、下載／chooser 確認、返回及觀察下載結果。任何 reveal 都只依 B1 在既有 intent 讀回後、以同一新 attempt 送出一次；不得在 intent 前先 hover／pointer move／click 探索。click 候選僅限已選 filmstrip 縮圖的非播放安全邊緣；hover 候選則要有該 hover 自身的可歸屬作用區、非播放安全區與映射，不要求 filmstrip 或同一邊緣。同一 `list_key + post_key + media_key` 最多兩次已派送 reveal 候選，跨 viewer、reopen、Session 與 restart 累計；工具列隱藏時，intent 前必須已有可歸屬的當次安全方法及完整可核對的 `0`／`1` 額度，否則停止該項，不得建立該項 intent 或送出 reveal。任一前置不足、額度不可核對或沒有該方法的安全證據就停止該項輸入，不點主內容、播放／暫停、時間軸或其他控制。Agent 播放輸入恆為 `NONE`：不播放／暫停、不拖曳時間軸、不切換倍速、不點媒體內容切換播放控制、不分析畫面內容，也不為種類或播放狀態取證而操作 viewer。來源播放狀態只從既有當次觀察正面記 `NOT_PLAYING`／`AUTOPLAYING`／`UNKNOWN`，不為確認另加操作，且不得把 `UNKNOWN` 當 `NOT_PLAYING`；`AUTOPLAYING` 本身不是獨立 blocker，但來源／選取／幾何／映射仍須可正面核對且無漂移，控制被遮住或證據不足仍停止，不追認舊 attempt。找不到可靠下載控制就記具體阻塞，不自行嘗試播放或另一下載方式。

Reveal 的 intent 前方法與額度 gate、固定 slot、intent 後直接定位或同一新 attempt 一次 reveal、同次 input → after、狀態判讀、幾何界限與停止，只依 [B1](references/gui-inventory.md#目標與下載控制就緒b1)。充分當次視覺映射不要求 AX 節點，AX 缺節點也不否決充分視覺；但截圖不得補成 AX 節點，viewer 涵蓋、控制可見／歸屬／啟用、選取、幾何與完整座標映射仍須全部成立。工具列不需在 intent 前可見；隱藏時，只有當次安全方法可歸屬、B1 的 ordinal／前次引用／新證據條件與額度均成立，才可建立既有 intent，intent 前不得送出 reveal，intent 後也只可走直接或一次 reveal 其中一條。舊 `UNKNOWN`、舊無 outcome、crash、額度不明、前景中斷與 exact restart 限制照 B1；兩次 reveal 總額不因新 Session 或 restart 增加。兩個相依 API 不是 atomic，也不保證固定時間；可執行 composition 與固定 slot 見 [單次輸入與直接 after 觀察](references/evidence-template.md#單次輸入與直接-after-觀察)。

新媒體來源種類不明時使用 `identity.kind=UNCLASSIFIED`；已有媒體一律沿用原 key／identity，不為改種類重建媒體或去重。`UNCLASSIFIED` 是種類尚未分類，不是派送結果 `UNKNOWN`。下載後由 `download-check` 辨識實際檔案種類，不要求 Agent 證明來源原先是照片或影片。

日常完成的保證範圍為 `assurance=DOWNLOAD_ONLY`：該次下載結果已保存並通過基本檔案檢查，不代表內容可完整解碼、來源種類已證明或與服務端原始位元相同。舊完整驗證與完成紀錄保留，不自動降級或重下。

## 日常入口與 Agent 責任

Owner 先人工開啟指定的 LINE 記事本列表，指定目的地（未指定時使用本專案 `backup/記事本/`），並在同一次正式 Prompt 中授權備份及交接有效前景。這次提交同時是任務授權與當次前景交接，不要求 Owner 再選盤點／接續模式、逐篇下令，或手填 UUID、內部 key、JSON。

Agent 的任務是完成整份列表，而不是等 Owner 逐步操作：

1. 自動查全部記事本帳本、目前任務與相符的永久記憶，先讀 `summary` 的 `unresolved_attempts`、`dispatch_blockers` 與掃描覆蓋。
2. 核對列表；證明是新列表且沒有缺損歷史或候選歧義時自動初始化，既有列表則綁定原帳本。每個新 Session 在 `bind` 前，依[證據範本](references/evidence-template.md#cua-觀察原件落地)把同次 CUA 回傳的完整 AX 與截圖 bytes 寫入專案私有 task directory，讀回核對後才封裝 observation／handoff bundle；無法取得或保存原件就停在 `bind` 前，不手寫或補造。新掃描前先處理舊 attempt。已 `DOWNLOAD_FINISHED` 的原交易若只因新 scan 而 `scan_binding_match=false`，依 `resume` 分流：`VERIFY_REQUIRED` 使用原 attempt 的 `download-check`，`SCAN_BINDING_REVIEW_REQUIRED` 才保留資料交人工審查；不改綁定或重下。
3. 先建立完整來源卡片台帳，從頂端到底端盤點貼文並完成頁面雙向對帳；之後逐篇細盤媒體並處理合格項，不要求其他貼文的媒體細盤先全部完成。
4. 依紀錄跳過已處理項，對每個合格項只送出一次下載派送，並在結果後做基本檔案檢查、發布及讀回 completion。
5. 遇到已授權的中斷恢復時，保留原檔並自動接續或建立新的空白恢復 attempt；UNKNOWN、活動下載及未完成命名交易先查證，僅符合〈結果不明的單次恢復〉時才可另建一次補下載。
6. 最後重新對帳，主動回報總數、逐篇狀態、缺項、已保存檔案及未測範圍。

只有「實際備份任務授權＋有效前景交接」才允許 GUI 輸入。討論 Prompt、審查 Skill、整理文件或單純交出前景本身都不是下載授權；前景中斷時停止所有 GUI 輸入，重新交接本身也不解除既有 UNKNOWN。

查歷史、初始化或讀寫紀錄不是下載授權；notes CLI 回傳的簿記成功也不是 GUI 授權。若 notes CLI 尚未存在、`--help` 失敗或當次 repo 沒有相符實作，停止依賴該命令的動作，如實回報 `IMPLEMENTATION_NOT_AVAILABLE`；不得手寫事件 JSON、另建空帳或換入口繞過。

若 Owner 明確更新同一日常任務的授權狀態（例如由診斷改為指定備份、解除明示的「不下載」限制，或接受目前版本），只更新明確涵蓋的範圍與被取代限制，保留較窄目標（如指定五張）。依當次畫面與帳本判斷下一個安全步驟；在授權、前景與來源身分支持的範圍內，可繼續唯讀查證、卡片盤點及開啟已核對的目標 viewer，不必先證明下載控制。若授權／前景／身分不明，只停止依賴該前提的輸入，仍可做安全的唯讀查證並回報具體缺口。

下載派送前先依 B1 判斷：控制可直接定位，或工具列隱藏但同一 viewer／選中項的當次安全 reveal 方法、ordinal／前次引用／新證據條件與完整可核對的 `0`／`1` 額度均成立；兩者皆無、額度不明或任何未決時，只在該項 `intent` 前停止輸入並保留未完成。若可靠返回契約（實際 entry anchor、`expected_return_role`、一次一層、可歸屬返回控制）成立且無全域 blocker，可返回已核對列表後一次一項處理其他合格項。未隔離 `UNKNOWN`／無 outcome、活動下載、pending naming、`LOCAL_CHANGED`、列表覆蓋或身分不明、前景／返回歧義仍是停止所有新派送的條件，不藉排程跳過；既有 `UNKNOWN` 不改寫成 `NOT_SENT`。隱藏分支只代表可建立既有 intent，`intent` 前不得送出 reveal。`bind`／`scan` 等前序步驟仍各自遵守原有 gate。一般「繼續」不解除未明示取消的限制；接受版本只處理版本差異，不解除資料異常、UNKNOWN、活動下載或未完成命名交易。日常授權更新不取代正式角色的當次人工交接，Planner／Reviewer 不因引用歷史下載授權而轉為下載角色。詳見[啟動與帳本對帳](references/download-and-ledger.md#啟動與帳本對帳)。

## 結果不明的單次恢復

1. **先分流。** 「尚無 outcome」不是已記 `UNKNOWN`：前者先用 `outcome` 保存第一筆真實結果，後者先有限查證，取得新結果證據才用 `reconcile`。有可靠的原下載完成證據就接續原 attempt。命名中斷、已下載待檢查、來源到期與本機檔案變動走各自既有路徑，不套用本節補下載。
2. **安全隔離。** 先以當次有限 AX／截圖核對舊目標與前景；這不是完整重掃。只有同一 `list_key + post_key + media_key`、同一已授權目的地、有效前景仍對應目標列表／viewer、最新觀察無舊 chooser／modal、無可歸屬活動下載、舊 staging 與身分可精確核對且為空、無 pending naming／檔案異常／開放的手動 restart 批次，且當次 CLI 摘要明確支持這條路徑時，才可由 CLI 的追加隔離事件保留舊 attempt。隔離本身零消耗、不建立 scan／新 attempt，也不派送；只有之後一次 `line-notes-intent/v5` 的單次 append 才消耗該媒體跨 Session 僅一次的補下載額度。隔離不是 `STOPPED`／`NOT_SENT`，不證明舊操作已停止，不改寫舊 outcome，也不解除其他 UNKNOWN。
3. **單次補下載。** 隔離事件保存並讀回後，仍須由目前綁定 Session 完成隔離後才開始的新普通完整卡片掃描與目標貼文細盤；再由一次 v5 intent 的 append 消耗額度，以新空白 staging 建立一次補下載。補下載須重新通過 B1、當次下載控制與 chooser 各最多一次、本 attempt 一次派送；只有 `download-check` 與 completion 讀回才算完成。舊 attempt、路徑、證據與晚到檔全部留在舊 staging，不發布、不清理、不合併；接受背景晚到仍可能發生的殘留風險。
4. **再次不明與其他項。** 補下載再 `UNKNOWN` 時，只有上述安全前提仍成立才可再追加一次隔離，記 `RECOVERY_EXHAUSTED` 並保留欠件；若出現 chooser、可歸屬活動下載、舊 staging 無法核對或仍在變動、命名交易、檔案異常、身分／授權／覆蓋不明，停止依賴該前提的派送。`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 是未完成報告狀態，不計完成；安全耗盡的單項不阻止其他已核對合格項，也不得誤報成全列表完成。未隔離或無法安全處理的 UNKNOWN／no-outcome 仍是全域 blocker。
5. **獨立路徑。** 精確確認的 `restart`／`reattest`、`STOPPED`／`NOT_SENT` 恢復、已完成、排除與受保護歷史各自保留原 gate。自動單次路徑不能用於批次 scope、換目的地、`LOCAL_CHANGED` 或來源種類取證。

## Viewer 返回與中斷恢復

viewer 進入前由實際 entry anchor 保存預期返回角色：通常由貼文詳細頁進入時是 `POST_DETAIL`，只有實際由列表或其他角色進入時才填該角色，不固定預設 `LIST`。進入後依唯一本文[返回契約與有限恢復](references/gui-inventory.md#返回契約與有限恢復)核對控制歸屬，再開始下載交易。每次只返回一層並重新觀察；同頁未變或資訊不足記 `RETURN_NOT_OBSERVED`，只有正面證明頁面角色／身分／入口連續性已失去才記 `ENTRY_LOST`，且與 `INPUT_UNAVAILABLE` 分開、可同時成立。通道失效後，只做工具文件支持的唯讀 app／window 列舉與 handle reacquire；沒有新證據不重試。無法恢復時，只請 Owner 把同一指定列表帶回前景。

同一有效前景內重取 CUA handle 不重跑 notes `bind` 或更換帳本 Session。真正前景中斷後，Owner 重新交接就建立新的 notes Session ID。新 bind 不會 interrupt 舊 open scan：先收斂舊交易，再明確 interrupt 舊 scan，之後以普通完整掃描接續；不得以 scan 解鎖 UNKNOWN，亦不自行使用 restart／recovery scan 繞過普通阻塞。

每次導覽／輸入的原件保存方式依[單次輸入證據範本](references/evidence-template.md#單次-cua-輸入保存-helper)；input receipt 不是 OS event trace。狀態案例見[證據判定案例](references/evidence-decision-cases.md#d1-viewer-返回契約在進入後核對)。

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

1. **找回前次任務。** 先查全部記事本帳本與 active-notes-task；`lists` 已回全部帳本摘要，只有需要刷新選中帳本時才序列讀一次 `summary`（`memory` 是同一摘要的別名）；不能用缺少帳本、索引缺失或 active-task 不存在推論為空帳。新列表須有完整、無歧義的新列表證據：固定同一組 identity 先執行 `list-key`，以該 key context 建立可供 init 使用的證據，再以相同 identity `init` 並讀回 key。新／既有列表都須核對當次入口與有效前景後 `bind`；若歷史帳本已有 context 且當次未提供 context，沿用已保存值，明示不同值仍須拒絕。依 [下載與 notes CLI](references/download-and-ledger.md#啟動與帳本對帳) 處理舊 attempt／命名交易。`summary`／`resume` 中保留的 legacy `VERIFY_REQUIRED` 標記，日常解讀為待 `download-check`；不可因此呼叫舊 `verify` 或進行來源種類取證。普通情境先收斂未決項；安全隔離事件讀回後，才可由目前 Session 開新的普通完整 scan，若已確認 restart 批次則保留精確 scope、新 recovery scan 與其前置條件。上一個已結束 scan 若只有部分貼文媒體細節未完成，且沒有未隔離的未決 attempt／命名交易，也可重新開始普通 scan；尚 open 的 scan 須先明確 interrupt。不能在未綁定時先寫 outcome／reconcile，也不重用舊 Session ID 繞過綁定拒絕。`summary` 不含完整 attempt、staging 目的地或 completion manifest；交易細節以 `intent`／`download-check` 結果及追加事件為準。新一批目的地以 `destination` 追加，保留舊完成路徑。
2. **判定入口。** 在有效前景交接內用當次 AX／畫面確認目標是記事本列表，不是相簿、聊天、貼文檢視器或出處不明頁面。需要返回時只使用當次可靠控制項或已證實且符合角色／焦點的快捷鍵；不得猜 Escape、Command-W 或關閉。入口未確認前不捲動、不盤點、不下載。
3. **完整卡片盤點與逐篇媒體細盤。** 依 [GUI 導覽與盤點](references/gui-inventory.md) 從頂端到底端，以有序重疊避免漏篇；先保存來源逐卡紀錄，再產生 page rows，呼叫 `page` 前完成來源↔rows 雙向對帳。完整卡片覆蓋、頂底與重疊是任何下載的共同前置。再逐篇核對媒體縮圖、更多指示、viewer 與來源順序；目標或 B1 的 intent 前前置尚未成立時不建立 intent／下載；黑底、disabled slider、`00:00` 或影片控制不作來源種類判定，不為種類點播放。普通下載只要求目標貼文的最新細盤、媒體數量／順序及目標媒體身分完整；`dispatch_blockers` 中的 `POST_DETAIL_PENDING`、`STALE_POST_DETAIL` 等局部貼文資訊不會自動阻止其他合格貼文。另一貼文尚待細盤時可先處理合格目標，不得把待盤貼文記成 `NO_MEDIA`、排除或完成。列表覆蓋／身分不明、未隔離且無法安全處理的 attempt／UNKNOWN／no-outcome、活動下載或 pending naming 等全局阻塞仍須停止新派送；`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 只列未完成，不是其他合格項的全域阻擋。純文字貼文記 `NO_MEDIA`，不得當成下載完成。
4. **一次一項下載。** 依 [下載與 notes CLI](references/download-and-ledger.md) 與 [B1](references/gui-inventory.md#目標與下載控制就緒b1) 在 intent 前確認資格、來源及當次途徑：控制正面可定位，或工具列隱藏但安全 reveal 方法可歸屬、ordinal／前次引用／新證據條件與額度完整成立；隱藏分支若無方法、無額度或未決就停在 intent 前，且不得先送 reveal。為每次 attempt 保存並讀回既有 intent、新空白暫存目錄及禁止重送紀錄；讀回後取得最新當次原件，控制可見就用該份直接定位，否則只在 B1 完整成立時用固定 `notes-reveal-c2-<attempt_id>` 送一次 reveal 並保存同一份 after。下載控制座標點擊一律經[單次 CUA 輸入保存 helper](references/evidence-template.md#單次-cua-輸入保存-helper)的 `persistGroundedDownloadClick`，使用同一 attempt 唯一的 `notes-download-<attempt_id>` slot：Agent 仍自行判定 control region、候選點、座標映射與下一步；helper 只驗證 request、保存 request／raw，並以持久讀回的 target 呼叫一次 `app.click([x, y])`，不是 native hit-test，也不提供 native receipt。普通導覽、返回與 chooser 仍按原路徑；helper 不可用、欄位缺失、slot 已存在或讀回不符時停在輸入前，不得退回任意 `invoke`、手動 `app.click`、另一個 slot 或舊點擊入口。**每個 attempt 的下載控制呼叫與 chooser 最終確認各最多一次**，兩者分開保存真實工具回傳；若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不得沿用相簿入口。chooser 須可歸屬同一 attempt、精確讀回完整暫存路徑後才確認一次。
5. **結果、基本檢查與命名。** 先查該 attempt 是否已有 outcome／UNKNOWN：沒有 outcome 時用 `outcome` 記第一筆真實結果；已有 `outcome=UNKNOWN` 才用 `reconcile`。只有最終結果為 `DOWNLOAD_FINISHED` 才執行 `download-check`，核對 magic MIME 與 suffix 分類、唯一非空穩定 regular file、SHA-256、防覆寫及身分後發布並讀回 completion。原 intent 的 PHOTO／VIDEO 分類不限制實際檔案種類，不為種類取證、改種類或重下。若 MIME 明確為 `text/plain`、`text/html`、`application/pdf` 或 `application/zip`，記為 `EXCLUDED`（schema `line-notes-download-exclusion/v1`）並保留 staging；不寫 completion，也不宣稱來源本身不是媒體。未知 MIME、`application/octet-stream` 或 MIME／suffix 不相符時保留 pending 並拒絕完成，不猜種類、不改 key、不重下。命名中斷以 `resume` 接續；已確認 restart 批次使用 `restart resume --download-only`，不重新授權、不自動派送；scope candidate 為明確非媒體時回報 `RESTART_SCOPE_NON_MEDIA`，不自動改動已確認 scope。舊 `verify` 與種類更正入口保留供歷史相容，不是日常操作。
6. **逐項循環與結束對帳。** 完成一項後保存並讀回 completion，重新觀察原貼文／列表，再定位下一個合格項。遇到新媒體、重排、刪除、編輯或檔案異常時先更新盤點與狀態，不覆寫舊完成事實。最後先重讀本輪原件，依 GUI 本文核對各 page 讀回與有序去重聯集，再以 `summary` 與當次畫面交叉核對；只有覆蓋完整且所有未解類別已誠實列出，才回報本次工作結果。

page 前的來源卡片台帳、部分／高卡片、雙向對帳及 finish 前原件重核，以 [GUI 導覽與盤點](references/gui-inventory.md) 為唯一操作本文。CLI 只檢查已提交 rows 的內部一致性；來源對帳未成立時，即使工具能接受，也不得提交 page／finish 或開始新派送。

## 下載與恢復的硬邊界

- 一次只處理一個貼文／媒體 attempt；不得平行派送多個下載。
- intent 一旦持久寫入，就按「可能已派送」對待；在 `outcome` 有正面證據前，禁止第二個下載派送，也不得把工具逾時、畫面未變或舊計數為零當成 `NOT_SENT`。
- `outcome` 的第一筆結果不可任意改寫。尚未寫 outcome 時先以 `outcome` 保存第一筆真實結果；已有第一筆 `outcome=UNKNOWN` 時，先唯讀查原事件、目的地與當次狀態，取得新結果證據才用 `reconcile`。只對收斂為 `DOWNLOAD_FINISHED` 的原 attempt 做 `download-check`。未收斂時須完成本 Skill 的安全隔離與新盤點，才可另外建立補下載。
- 定位、input 原始回傳、App 階段性回應、下載結果、檔案驗證與 completion 是不同命題；只有可歸屬的正面證據組合能前進。timeout、畫面未變、空目錄、缺少 marker、API 成敗或播放結束都不足以判未派送或完成，詳見 [證據與允許行為矩陣](references/verification-and-recovery.md#證據與允許行為矩陣)。
- 新寫入的事件證據必須是 `evidence-pack` 產生且由 CLI 回傳的 `line-notes-evidence/v2` bundle；不手寫 bundle、不改內部 JSON／hash。`evidence-audit` 只作唯讀引用稽核，完整性失敗就停止。`evidence-correct` 只修 page 引用，不改來源成員或覆蓋。`media-kind-correct`／`media-kind-reconcile` 保留為歷史嚴格驗證的相容入口，不是日常動作；日常 `download-check` 不要求來源種類更正或 GUI 種類證據。真實帳本更正仍需精確資料授權，不以本流程改寫舊歷史。
- 只有原 attempt 已確認 `STOPPED`／`NOT_SENT`、原檔保留、帳本已持久化 `recovery_authorized=true`、當次正式 Prompt 明示涵蓋此次恢復、前景有效，且具充分停止證據時，才可依 [下載與 notes CLI](references/download-and-ledger.md) 以 `--recovery-evidence` 建立該項的新空白恢復 attempt。`recovery_authorized=true` 只是舊恢復路徑的持久資格，不能代替當次正式 Prompt 授權；`false` 保留，不由單次 UNKNOWN 路徑改寫或拿來繞過，也不因此解除 `STOPPED`／`NOT_SENT` 的原 gate。現行 CLI 沒有事後改寫此授權的命令，未持久化時停止，不手改 ledger。已完成項跳過。
- 除本 Skill「結果不明的單次恢復」外，沒有精確確認批次時，未隔離的 `UNKNOWN`、活動下載、未完成命名交易與 `LOCAL_CHANGED` 仍依原規則停止。若 `restart preview` 回報 `RESTART_REQUIRED`／`OPEN_BATCH`，Agent 先用白話列出精確列表／受影響貼文與媒體／舊版位置／新 `versions/gNNNNNNNN/` 路徑／額外空間／缺項與保留項，取得 Owner 明示同意後才可 `restart confirm`；沉默、逾時或一般「繼續」不是同意。confirm 後必須完成新的 recovery scan，才可逐項 `intent --restart-id`；同一媒體的新 generation 可成為目前 active，舊 confirmation、candidate、activation、completion 與 UNKNOWN 歷史全部保留。精確 `restart confirm` 前的既有 `UNKNOWN`，可在 confirm 後由此 scope 的第一個新 v3 attempt 首次替代；confirm 後同一批次任何新增 v3 attempt 尚無 outcome 或結果 `UNKNOWN`（包括後來被 supersede 的舊版），不得再建立新 intent 或 activation；先依[下載與 notes CLI](references/download-and-ledger.md#恢復與不可解鎖狀態)查原 attempt，若現行 latest-only `reconcile` 無法處理已被 supersede 的舊版，保留證據、回報具體資料阻塞，不反覆呼叫或擴寫更正入口。`STOPPED`／`NOT_SENT` 仍按既有恢復授權，`DOWNLOAD_FINISHED` 仍用原 attempt 基本檢查，不能誤擋這些既有結果路徑。同一確認批次涵蓋完成前再次中斷；scope、身分、目的地或版本策略改變須重新預覽與確認，不能把一次同意擴成無限重送。`dispatch_authorized=false` 不是 GUI grant；新 attempt 仍使用新的空白 staging，不沿用舊 chooser、路徑或座標。
- 普通 `created`／`destination` 列表綁定的 path、inode、canonical、非 symlink 或授權邊界不符時停止。列表容器歷史 `device` 值與目前不同，不單獨阻擋 intent。完成媒體與已驗證 candidate 以授權路徑、預期檔名／檔集、regular file、`nlink=1`、非 symlink、size、穩定讀取及 SHA-256 核對可用性；歷史 device／inode／mtime／ctime 不單獨判 `LOCAL_CHANGED`，也不改寫保存值。pending 發布仍核對原交易的路徑、inode、時間、內容與 journal，容忍歷史 device-only 差異；hardlink 當下的同檔案系統與 source／target 身分檢查仍須成立。未隔離的 UNKNOWN、活動下載及 pending 命名交易繼續阻擋新派送；可唯一核對的 pending 交易以原 `resume` 接續，不能藉此重送或覆寫。
- 若有效 binding 已是 `list-directory-reattest`，依既有 `reattest` 規則保留 device／inode 嚴格核對：只處理合格既有 OPEN_BATCH，必須有完整 witness 與 Owner 對精確 preview 的明示同意，confirm 後完成新的完整 recovery scan。每帳本至多一次；轉接後再次漂移、preview 拒絕或 session／scope 不符時停止，不換目的地、不重送。普通新下載不新增 reattest 或 Owner 確認步驟。
- confirm 會寫入新版事件；舊版 CLI 讀到後會拒絕。首次真實 confirm 前核對後續 session 使用相容版本；寫入後不刪事件、不回退成空帳。
- 來源已明確到期且原最新 attempt 為 `STOPPED` 時，才可追加 `source-unavailable`；它只記 `SOURCE_EXPIRED`，不是完成、排除、重試授權或服務端已回收的證明。該項不得再建立 intent，其他項仍受列表級 blocker 約束。
- 命名交易、暫名與目標身分可唯一核對時用 `resume`；無法唯一下一步時保留原檔與 pending 證據並停止，不手動改資料夾或重下。
- 已完成事實與本機可用性分開：整篇目錄缺席記 `LOCAL_MISSING` 並保留完成、禁止重下；目錄仍存在但有缺檔、非屬合格環境附屬項的額外檔、size／hash／路徑身分不符或 symlink／非預期 hardlink 時記 `LOCAL_CHANGED`。完成檔與 active candidate 都遵守這項缺席／缺檔區分。`LOCAL_CHANGED` 僅可在精確確認批次 scope 內保留原檔並複製到新版本目錄重建；scope 外仍停止新派送。
- 六類業務狀態為 `COMPLETED`、`EXCLUDED`、`PENDING`、`PREVIOUSLY_INCOMPLETE`、`UNKNOWN`、`PROTECTED_HISTORY`。`NO_MEDIA` 是貼文層級標記，不是第七類，也不是下載完成。
- 不發訊息、刪除、分享、覆寫照片或變更舊完成事實；不擴及其他列表。工具拒絕、身分歧義、寫入衝突或不明派送時停止依賴該前提的動作，不換入口繞過。

一般查證維持同一根因最多三次有證據嘗試；B1 reveal 候選另限兩次。連續兩次沒有新資訊就停止相同方法，不用重試消耗次數。外部成員或程序可能改動來源，不能承諾原子快照、OS 隔離或 exactly-once。

## 回報與證據界限

在「歷史／入口核對完成、完整盤點完成、每個貼文／媒體完成或遇阻、最終對帳」節點主動用繁體中文回報，內容至少包含：

- 列表與貼文總數、來源逐卡對帳結果、未解卡片／缺頁、`NO_MEDIA` 篇數、六類媒體狀態及目前項目；六類狀態以 `status_counts_scope` 與 `all_known_media_status_counts` 分開回報，舊 `status_counts` 不可當全列表或本批次 attempt 成功。
- `open_restart.scope_unresolved_attempts` 與 `dispatch_blockers` 的 restart 阻塞要明列；restart 欄位語意見[下載與 notes CLI](references/download-and-ledger.md#恢復與不可解鎖狀態)。
- 已保存圖片數、已保存影片數及其 `DOWNLOAD_ONLY` 範圍、未解缺項及下一步。
- 單次自動恢復的舊 attempt 隔離、補下載額度已用或已耗盡、舊 staging 晚到檔風險與仍未完成項要分開列示，不把安全耗盡計入完成。
- 工具簿記結果、基本檔案檢查結果、真人 `OBSERVED` 與真實 LINE E2E 分別列示。
- `dispatch_authorized=false` 只是簿記欄位，不是 GUI grant、實機 PASS 或獨立驗收。

工具簿記 PASS 只證明帳本／摘要的輸入與投影一致；基本檔案檢查只證明指定檔案的非空、穩定、種類及 hash 等已檢查性質，不證明內容可解碼；真人觀察只能記 `OBSERVED`；真實 LINE 記事本下載、混合附件、跨 Session 與 chooser 在沒有當次正式任務及有效前景時一律 `NOT_RUN`。合成 fixture 的測試通過不代表真實 LINE 已支援。

審查本 Skill 時只做文件、格式與離線檢查，不啟動 LINE、不讀私人照片／帳本，也不把審查意見寫成 E2E 或 acceptance。

## 參考文件

- [GUI 導覽與盤點](references/gui-inventory.md)：入口、三層身分、卡片盤點與對帳、B1 的 intent 前方法／額度 gate、intent 後直接定位或單次 reveal、同次 after、viewer 返回契約、入口遺失與輸入失效的有限恢復、視覺控制映射、popup、座標與輸入規則。
- [下載與 notes CLI](references/download-and-ledger.md)：目前子命令與參數、`list-key` 建帳前 bootstrap、絕對證據路徑、`lists`→`summary` 查詢、capture、intent 前後核對、下載／chooser 各最多一次、outcome／reconcile 分流、更正與命名恢復。
- [驗證與恢復](references/verification-and-recovery.md)：證據稽核／更正、完成／停止證據組合、AX／截圖提示分離、檔名歸屬、類型更正、來源到期、基本檔案檢查與歷史解碼相容、六類狀態與本機可用性。
- [證據範本](references/evidence-template.md)：供 `evidence-pack` statement 使用的私有紀錄欄位、原件保存 helper、`persistGroundedDownloadClick` 單次輸入 request／raw／diagnostic 落地與 chooser 目的地核對；不是可直接傳給 `--evidence` 的自由文字 schema。
- [證據判定案例](references/evidence-decision-cases.md)：控制隱藏、V1／V2 前置差異、直接路徑、固定 slot／額度、跨 Session、slot 衝突、同次 input→after、after 保存缺口、API error、chooser 延遲／預填路徑、晚到結果、未授權的播放取證、crash window、舊 UNKNOWN／exact restart 與充分／不足證據的假設案例。
