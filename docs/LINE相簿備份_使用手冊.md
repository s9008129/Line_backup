# LINE 相簿備份使用手冊

適用 Mac，更新日期：2026-10-24。

## 1. 這個系統可以幫我做什麼？

指定一個 LINE 群組和照片資料夾後，由 Codex 裡的 AI Agent 使用 Computer Use 操作 Mac LINE，逐本下載尚未備份的相簿、檢查照片、留下完成紀錄。已完成和已排除的相簿會跳過。

真正入口是 **啟動 Codex，再貼上下方的日常啟動 Prompt**。這需要有 Mac Computer Use 能力的 Session；只有終端機指令執行能力還不夠。Agent 必須持續參與畫面判讀，請保留 Mac 前景供它操作。這不是完全無人值守的備份軟體。

## 2. 第一次使用前需要準備什麼？

- Mac 已登入 LINE，能看到目標群組及相簿，網路正常。
- 本機已有 Line_backup 專案、Codex CLI、可用的登入與額度。
- 此次 Codex Session 能使用原生 Mac Computer Use；螢幕錄製、輔助使用等權限由您確認。權限不足時依系統提示自行處理，再讓 Agent 重新檢查。
- 選好空間充足、您可寫入且會長期保留的照片資料夾。
- 告知 Agent 舊照片及完成紀錄的位置。以前備份過的群組，不能把全新目錄當作從未備份的證明。
- 備份時不要同時操作 LINE、切換群組、關閉視窗或讓電腦睡眠。需要使用 Mac 時，先請 Agent 安全暫停。

不用自行安裝新的 GUI 控制器，也不用填寫視窗座標。

## 3. 如何啟動 Codex CLI？

打開 Mac「終端機」，輸入 `cd `（包含後面的空格），把 Finder 裡的 **Line_backup 專案資料夾**拖入終端機，按 Enter。接著執行：

```sh
codex --version
codex
```

第一行預期顯示版本號；本輪本機檢查為 `codex-cli 0.164.0`。第二行會啟動互動介面，必要時依畫面完成登入，然後貼上第 6 節的 Prompt。[官方 CLI 說明](https://learn.chatgpt.com/docs/cli)。

若出現 `command not found`，表示目前終端機找不到 Codex；先處理安裝或 PATH，再開始。不要改用驗收 CLI 代替。

`codex mcp list` 可在終端機查看工具設定，但顯示 enabled 不代表 GUI 已實測可用。啟動 Prompt 會要求 Agent 唯讀確認原生 Mac 工具與 LINE；若只有瀏覽器工具，必須停下。可改用已配置 Computer Use 的 Codex Session，開啟同一專案並貼相同 Prompt。

## 4. 如何指定要備份的 LINE 群組？

將 Prompt 的 `GROUP_NAME` 改成 LINE 顯示的完整名稱。若有同名群組，先由您指出正確群組，再讓 Agent 核對當下畫面。群組改名也要先確認與舊紀錄的對應。

不同群組必須各有自己的識別與紀錄，不能因相簿日期、照片張數相同就共用完成標記。LINE 沒有可靠 ID 時，Agent 需綜合群組脈絡、標題、日期、張數與畫面證據；仍無法區分就停止。

## 5. 照片會儲存在哪裡？

`BACKUP_ROOT` 是您指定的正式備份目錄。建議每個群組各用一個資料夾；範例為 `~/Pictures/LINE相簿備份/我的群組`，請換成您實際想用的位置。Agent 會先展開 `~`、確認實際路徑、可寫入與容量，避免誤存到暫存資料夾。

新任務採以下簡單安排，由 Agent 建立與維護，不需要您手動填 JSON：

```text
您指定的備份目錄/
  albums/                 每本相簿各自的新空白資料夾
  backup-records/
    group.json            群組識別與舊紀錄來源
    progress.md           可閱讀的進度與阻塞
    albums/               每本的 intent、操作事件、manifest、解碼結果、完成紀錄
```

這是日常 Agent 的檔案保存約定，並非已安裝的新控制器。相簿紀錄放在照片目錄外，避免 ImageIO 檢查把 JSON 當照片。相簿資料夾名可含日期、張數及唯一流水號，但名稱本身不是身分證明。

舊照片與舊紀錄一律保留原位。本輪不搬移歷史照片。再次啟動時，Agent 同時讀取正式目錄紀錄及專案既有紀錄；舊紀錄若在別處，保留來源連結。沒有找到舊紀錄時先詢問，不直接重下載。

## 6. 如何開始備份？

先把 LINE 切到目標群組，讓 Mac 保持可操作，再貼上整段 Prompt。通常只需修改前兩行；不排除相簿時保留 `EXCLUSIONS=[]`。

### 可以直接複製的日常啟動 Prompt

```text
GROUP_NAME=我的群組
BACKUP_ROOT=~/Pictures/LINE相簿備份/我的群組
EXCLUSIONS=[]

請在目前 Line_backup 專案，使用 AI Agent＋原生 Mac Computer Use＋既有 LINE Skill，備份上述群組所有尚未完成且未排除的相簿。不要新增控制器或 GUI 框架。

本次我授權：在核對上述群組、實際保存位置與當次前景交接後，自主擷取畫面、辨識、捲動、開啟相簿、返回列表，以及對確定未完成且符合資格的相簿執行 LINE 原生「儲存全部」，寫入上述 BACKUP_ROOT 下的新空白相簿目錄，驗證並新增本次完成紀錄。一般導覽不需逐步請示。這不是授權操作其他群組、發訊息、刪除、搬移或覆寫任何舊照片，也不是授權變更正式 VERIFIED、grant、ledger、Harness 或既有排除紀錄。不要 push、merge、啟動 GitHub Actions 或雲端 CI。

先讀 AGENTS.md、README.md、docs/LINE相簿備份_使用手冊.md、.agents/skills/line-album-agent-cua/SKILL.md 及其 references/verified-experience.md。沿用 PR28 的列表 metadata strip→詳細頁雙重身分核對→新鮮選單定位→新空白目錄下載→完整驗證，以及 PR32 的即時列表捲動與過期 AX 重新觀察方法。不得重用舊座標。

啟動前：唯讀確認當次 Session 確實有原生 Mac GUI 工具並可觀察 LINE；line_backup_acceptance CLI 不會操作 LINE。確認 GROUP_NAME、展開後的 BACKUP_ROOT、容量、權限與前景交接。參數仍是範例、有同名群組、工具缺失或權限不明時先停止並說明需要我做的一件事，不假裝已開始。

先查該群組在 BACKUP_ROOT/backup-records 的紀錄，並讀專案 state/backup_state.json、state/manual_archives.json、既有私有 checkpoint、逐本 completion-record、最新 batch summary 與 Owner 排除紀錄。只對符合此群組的紀錄去重；來源沒有群組識別時先查證來源脈絡，不跨群組套用。舊 COMPLETED、FILES_VERIFIED、VERIFIED 與人工封存均須保護，不重下載。若無法找到或安全對應舊紀錄，停下問我，不能當作未備份。

在正式保存位置建立或沿用 backup-records/group.json，保存可靠群組 ID（若有）、完整名稱、辨識證據與舊紀錄來源；沒有可靠 ID 時使用持久的群組本地識別及實機脈絡，同名或改名不可猜配。每群組紀錄分開，BACKUP_ROOT 已屬另一群組時停止。以既有完成紀錄格式為範本，在 backup-records/albums 逐本保留身分、目的地、預期張數、操作與驗證證據及來源分類；progress.md 供我查看。不要只把完成紀錄放 /tmp 或臨時測試目錄。

從相簿列表頂端逐步看到底端，記錄每本身分與狀態，跨畫面去重。COMPLETED 或 EXCLUDED 直接跳過；不只憑相同日期或張數判斷。每本新候選進詳細頁再次核對群組、標題／日期、總張數與當下畫面。存在兩本同日期同張數時加查可辨識證據，無法唯一確認即停止。

儲存全部前：通過仍適用的授權、去重、目的地、安全及 at-most-once gate，先持久寫入本次 intent 與「可能已派送、禁止自動重送」事件，再用新鮮畫面確認唯一「儲存全部」，只派送一次。確認 chooser 的實際目的地為新空白目錄後才確認下載。若主畫面看不到選單，依現有工具能力檢查獨立 popup，不能假定未派送並盲點。不可重置 ledger、重開 closed grant 或以本 Prompt 冒充 runtime grant；既有 gate 拒絕時停止回報。

下載後觀察完成狀態及檔案穩定，核對張數、所有檔案非空、逐檔 SHA-256 manifest，以及 macOS ImageIO 完整像素解碼。沿用 src/line_backup_batch/image_decode.swift 或已確認相同來源的既有工具，檢查真實退出碼與每檔結果；不要只看縮圖或檔頭。允許不同檔案具有相同 SHA-256。全部通過才保存 status=COMPLETED、execution_lane=MANUAL_DIAGNOSTIC、formal_auto_verified=false 的完成紀錄，附實際目的地、檔案清單、manifest hash、解碼結果與證據，寫後讀回核對。失敗記 INCOMPLETE；派送結果不明記 UNKNOWN，不寫 COMPLETED。這些日常紀錄不改寫正式 AUTO VERIFIED。

返回列表繼續，直到有實際到底證據、所有候選均有完成或排除對應，INCOMPLETE=0、UNKNOWN=0，才回報 ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS，並說明是本次可見列表範圍。列表中途變動、數量對不上或新增照片時，保留差異並停止或重新唯讀核對，不覆寫原完成事實。

中斷時保留部分檔案與 intent。重新啟動先查先前派送、LINE 狀態與目的地；結果不明禁止自動重派。已確認停止但未完成、不能安全逐張接續時，先向我說明並取得該本整本恢復授權，再用另一個新空白目錄重下載該未完成相簿；原目錄保留，不移除。每次恢復有自己的 intent，不重下載 COMPLETED。

遇到身分歧義、前景中斷、儲存位置不符、覆寫風險、工具失效、writer guard 或任何未知派送，停止依賴該前提的操作，保存證據並告知最小下一步。進度定期告訴我已完成／跳過／排除／未完成／未知本數與照片數。結束或暫停前保存可持續使用的進度與回報；不宣稱正式 AUTO 或完全無人值守驗收完成。
```

此 Prompt 提供當次有界授權，不能取代執行中的交易 gate。Agent 若報告缺少必要 runtime 授權，先處理具體缺項，不能要求它略過保護。

## 7. 如何查看備份進度？

看 Codex 回報，或用 Finder 開啟 `BACKUP_ROOT/backup-records/progress.md`。請 Agent 顯示已完成、既有跳過、排除、未完成與未知本數，以及驗證通過的照片數。看到 LINE 下載視窗消失，還不代表檔案已驗證。

## 8. 怎麼知道所有相簿都下載完成？

Agent 須真的走到底端，將看到的所有不同相簿逐一對帳；相簿總數應等於完成加排除，未完成與未知均為零。相同卡片重複出現在多張截圖只計一次。AX row 數可能含其他項目，不能直接當相簿總數。

完成報告應包含 `ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS`、範圍與時間、總本數、完成張數、排除及驗證證據。這表示當次可見清單的備份完成，不保證日後新照片已備份，也不代表正式 AUTO VERIFIED。

## 9. 中途停止後，如何繼續？

正常停止前告訴 Agent：「請停止新增下載，保存目前進度。」若它正在下載，不要立即關閉 LINE，先讓它確認狀態。突然斷電也不要刪除留下的目錄。

下次用相同 GROUP_NAME、BACKUP_ROOT 貼同一份 Prompt。Agent 先查完成紀錄，跳過已完成相簿。部分下載保留；先確定舊操作結果，再決定是否需要您授權整本重下載到另一個新空白目錄。結果未知時不能自行重試，也不假設 LINE 能只補缺漏照片。

## 10. 如何排除不想備份的相簿？

將 `EXCLUSIONS=[]` 改成明確描述，例如：

```text
EXCLUSIONS=[「相簿名稱：不需保存的活動；日期：請填實際日期；張數：請填實際張數」]
```

Agent 核對後記錄該群組的 EXCLUDED 與 Owner 原因。重啟時留空不會自動取消既有排除；若要變更請明確提出。名稱或日期相近但不能區分時，先由您確認。

## 11. 如何更換另一個 LINE 群組？

先讓目前任務安全停止，再修改 GROUP_NAME 與 BACKUP_ROOT，切到新群組並貼 Prompt。建議不同群組各用一個正式目錄。不同群組的完成紀錄不互相套用；不要刪除前一群組的紀錄或照片。

## 12. 發生常見錯誤時怎麼辦？

| 遇到的狀況 | 怎麼做 |
|---|---|
| Agent 沒有原生 GUI 工具 | 換到已配置 Mac Computer Use 的 Session；必要時人工開啟 LINE 和正確群組。只執行 CLI 無法代替 GUI。 |
| LINE 登出或系統要求權限 | 您自行登入或處理系統權限，再交回前景。 |
| 找不到群組／同名群組 | 您先打開正確群組，讓 Agent 重新核對。 |
| 按選單後主視窗沒有選單 | Agent 先觀察獨立 popup；不要連續盲點。工具無法觀察時停止請您協助。 |
| 磁碟空間不足、磁碟離線 | 暫停，不改用未核准目錄；處理空間後重新確認路徑。 |
| 張數不足、檔案無法解碼 | 留 INCOMPLETE 及原檔，不標完成；確定前次結果後再討論整本恢復。 |
| 不知道儲存全部是否送出 | 留 UNKNOWN，查原下載與目的地；不要再次點擊。 |
| 舊紀錄遺失或不在新目錄 | 告訴 Agent 舊位置；先唯讀查證，不能整群重下。 |
| guard 或 grant 拒絕 | 保留錯誤，處理明確授權或受審修補；不重置計數或繞過 gate。 |
| 已完成相簿後來新增照片 | 保留舊完成版本，先核對差異與新的授權；不直接覆寫。 |

## 13. 如何將完成的照片複製到外接硬碟？

等 Agent 停止寫入後，在 Finder 將整個正式備份資料夾「複製」到外接硬碟的新資料夾，包含 `backup-records`。不要用搬移，也不要選取取代既有資料。複製完成後，請 Agent 唯讀比較來源與副本的檔案數、大小及 SHA-256，確認副本無誤後再退出硬碟。若來源引用別處的歷史資料，複製目前資料夾並不包含它們，應先列出缺少的資料，再另行授權複製。

本輪沒有執行複製，也沒有授權刪除來源照片。

## 14. 系統目前有哪些已驗證能力及限制？

- 已有真實 Mac LINE 的列表辨識、詳細頁核對、原生儲存全部、新空白目錄下載、SHA-256 與 ImageIO 完整解碼成功案例。
- Owner 提供的既有群組成果為 99 本中完成 98 本、9,306 張、排除 1 本、未完成及未知均零。本輪只讀既有資料，沒有重跑全部照片驗證；成果保留原本證據層級。
- PR28 方法包括日期／張數核對、metadata strip 開啟、單次儲存全部、檔案驗證；PR32 方法包括真實捲動與重新取得 AX。兩者各自成功不等於同一 runtime 已正式整合驗收。
- 現有 `line_backup_acceptance` 用於驗收及狀態控制，README 明載不派送儲存全部；`scripts/line_backup_cua_adapter.mjs` 是需真實 CUA App 及回呼的輔助模組，不是可獨立啟動的備份程式。
- 本輪已確認 Codex CLI 可啟動，且此 Session 的 Computer Use 可唯讀列出執行中的 LINE；未測試新群組下載，也未測試下一個 CLI Session 的完整 GUI 權限。
- 多群組 Prompt 與保存約定已備妥，其他群組的實際 E2E 尚待有界授權後驗證。既有歷史紀錄仍可能分散在專案私有目錄，不會自動搬到正式目錄。
- 原生逐張接續不是通用已驗證能力；ImageIO 工具有格式、單圖張數與尺寸限制，遇到不支援檔案必須如實回報，不能跳過後稱完成。
- 日常完成紀錄維持 `MANUAL_DIAGNOSTIC`，不升格正式 AUTO VERIFIED。Formal AUTO 的既有獨立審查、runtime、grant 與 E2E 條件仍適用。
