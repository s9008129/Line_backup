# LINE 相簿與記事本備份專案工作規範

## 目前產品與入口

日常產品是 AI Agent＋本專案 Skill＋原生 Computer Use。Owner 人工開啟指定相簿列表、首次指定目的地並交接前景；Agent 自動查前次紀錄、完整盤點、逐本下載及驗證，直到指定列表的合格項完成。先讀 `.agents/skills/line-album-agent-cua/SKILL.md`，相關實機操作讀 `references/verified-experience.md`，並依當次畫面調整，不重用舊座標。

記事本照片／影片備份是另一條獨立流程。Owner 人工開啟單一記事本列表、指定目的地（未指定時用 `backup/記事本/`）並在正式 Prompt 中交接前景；Agent 使用 `.agents/skills/line-notes-agent-cua/SKILL.md` 與 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes` 自動查永久記憶、初始化或綁定列表、完整盤點貼文與媒體，逐項下載、驗證及恢復。只備份貼文內照片與影片；留言、貼圖及連結不納入。notes CLI 退出碼固定區分：0 成功、2 argparse／必填參數錯誤、4 已列業務拒絕、70 未預期內部錯誤；70 會輸出 `status=INTERNAL_ERROR`、`reason=UNEXPECTED_EXCEPTION`、`dispatch_authorized=false`，不是可重試業務拒絕，不得據此重送、改寫 ledger、建立新 attempt、換目的地或換入口繞過，應停止並保留證據回報。相簿與記事本的 Skill、工具、狀態及帳本不得互換，記事本也不得把相簿的 `⋯ → 儲存全部`、選單、按鈕、chooser 或座標當成 fallback。

不以群組中文名稱或中文 OCR 識別列表。不要求 Owner 選盤點／接續模式、逐本重新下令，或手填內部 JSON。盤點是備份必要階段；缺頁先小步補接，有具體且無法自行解決的歧義才問。

提示詞見 `docs/LINE相簿備份_使用手冊.md`；相簿與記事本各自使用對應的正式 Prompt。Owner 親自確認成果屬日常備份；正式 Harness 角色驗收僅在另行明示交辦時適用，不是日常下載前置條件。討論提示詞、審查 Skill、整理檔案或交出前景本身，不是下載授權。GUI 輸入只在真實任務授權及有效前景交接內執行；前景中斷就停止輸入。正常可逆導覽不逐點請示。主要入口為 Owner 先開好指定相簿或記事本列表，再提交該流程的正式 Prompt；該訊息可同時提供任務授權與當次前景交接，不另等第二則開始指令，但仍須核對真實畫面與列表身分。

專案常駐指令只維護邊界與資料保護；Skill／references 維護操作決策，使用手冊維護唯一 Owner 啟動範本。這是專案指引，不是平台 system prompt。日常備份不得為了繼續執行而修改產品程式、紀錄規則或啟動 Git／CI 工作；開發授權須另有交辦。

## 歷史與資料保護

- `Line_backup` 是唯一核心目錄。永久記憶預設在專案 `backup-records/<local_group_id>/`，與可搬走、可整個刪除的照片區 `backup/` 分開。啟動先用 `daily groups` 查全部帳本，再讀 `.local/line-backup/active-task.json` 與相符帳本的 `daily memory --records-root`；active-task 只協助定位，不是唯一歷史入口。日常流程不讀舊開發資料、封存索引、外層保存點或 Git 歷史。
- 記事本使用完全獨立的永久記憶：預設 `notes-backup-records/<local_list_id>/`，照片與影片預設在 `backup/記事本/`。啟動先以 notes CLI 查全部記事本帳本，再讀 `.local/line-backup/active-notes-task.json` 與相符帳本；索引只登錄位置，active 檔只協助定位，追加式 `events` 才是事實來源。不得把記事本寫入相簿 `backup-records/`、`daily` 索引或 active-task，也不得反向混帳。
- 備份事實以每份永久帳本 `events` 的追加式 JSON 為準；`backup-records/index.json` 只登錄位置，不複製狀態。必要歷史證據與校驗資料須保存在照片區外；已遷移舊副本不可繼續寫入。缺帳本或檔案異動不能當成空帳。開發方法留在 Skill／程式，歷程留在 Git。
- 已驗證完成的整本照片目錄缺席時保留完成與禁止重下，另報本機不可用，不要求外接硬碟在線或歸檔登記；不能據此聲稱外部副本已驗證。目錄仍存在但缺部分檔案、內容或身分漂移、symlink 等異常時保護原件並停止新派送。UNKNOWN、活動下載及未完成命名交易不因照片缺席而解鎖。新一批目的地透過追加綁定，不改舊完成路徑；不要求 Owner 手填 UUID 或 JSON。
- 已完成、已人工備份、已排除與受保護歷史不重下。完整盤點成立且無身分歧義時，僅個別舊證據不足的歷史受保護項可跳過，繼續其他已核對合格項；不把它計入完成或排除，也不稱整份列表全部完成。活動下載、未解派送與未完成命名交易不可跳過另送。日期／張數相同不能跨列表合併；舊格式或缺證據保持 `PROTECTED_HISTORY`，不升格為完成。人工備份是來源註記，不是第七類：工具以完整證據認定完成才計已完成，僅人工聲明或證據不足計受保護歷史；不覆蓋既有 UNKNOWN／pending，亦不默認排除，依 inventory 的六類歸類規則。合成 fixture 不是真實歷史。
- 一次一本。每次派送前保存並讀回 intent、新空白目的地及禁止重送紀錄；每個相簿 attempt 的 Save All 最多一次。結果未知先查證，不能用新目錄、零計數、重置 ledger 或改寫 UNKNOWN 解鎖。
- 記事本一次一項，身分固定為列表→貼文→媒體；中文名稱、日期、總數、序號或單一 hash 都不能單獨認領歷史。每個媒體 attempt 先保存並讀回 intent、新空白目的地及禁止重送紀錄；記事本當次下載控制最多派送一次，若 UI 顯示 Save All，須先證明它是本記事本自己的控制，不沿用相簿入口。有 `outcome` 才能驗證，未知先 `reconcile`，未收斂不得 verify、建新 intent 或重送。純文字貼文記貼文層 `NO_MEDIA`，不是第七類下載完成。完成後整篇目錄缺席記 `LOCAL_MISSING` 並保留完成；目錄仍存在但有缺檔、額外檔、hash／身分漂移或 symlink 記 `LOCAL_CHANGED` 並停止新派送。UNKNOWN、活動下載及未完成命名交易不因照片缺席解鎖。
- 初始任務已授權確認中斷後的相簿級恢復時，保留原檔，在另一個新空白目錄恢復；完成的跳過，未知的不重送。LINE 原生只補缺檔仍未實證。
- 不發訊息、刪除、分享、覆寫照片、變更舊完成事實或擴及其他列表。這些副作用不包含在一般備份、審查或整理授權內。

## 現有程式與驗證

保留 `src/line_backup_batch/daily.py`、`image_decode.swift`、離線 OCR 與日常測試。記事本新功能使用獨立的 `src/line_backup_batch/notes.py` 與媒體驗證器，不得改變相簿既有公共介面、事件格式或資料語意。小工具負責記錄、去重與檔案一致性；Agent 負責理解任務、辨識畫面與選擇操作。缺 locator／AX 標籤不是增加控制器的理由。

下載後核對預期數、穩定清單、非空檔、逐檔 SHA-256 與 ImageIO 完整像素解碼，保存完成並讀回。解碼成功本身不證明與服務端原始位元完全相同。完成紀錄損壞或仍在本機的照片異動時保留來源並停止，不重下補帳；整本目錄缺席依上述永久記憶規則處理。

日常工具不簽發 GUI 權限、不觀察 LINE，也不證明提交畫面真實。相簿摘要的 `sensor_verified=false` 與 `real_line_e2e=NOT_TESTED`、記事本摘要的 `external_copy_verified=false` 與 `real_line_e2e=NOT_TESTED`、簿記 PASS、實際 GUI、檔案驗證、正式 state 與獨立驗收須分開報告。人眼觀察是 OBSERVED，不能冒充工具 PASS 或豁免。

最小回歸：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

僅選本程序相符的現有 Swift SDK，不修改系統工具鏈。記事本照片沿用 ImageIO 完整像素解碼；影片固定使用成對的 Homebrew `ffmpeg`／`ffprobe`，檢查有效影像串流及完整解碼，不混用 PATH 中版本不同的工具。離線測試不能代替真實相簿備份、記事本 GUI、即時 popup、混合附件 chooser 或跨 Session 恢復驗收；這些未實測項目維持 `NOT_RUN`。

## 修改、風險與證據

先查 repo／worktree／branch／HEAD 與 Git 狀態，保留無關 dirty、untracked 與唯一版本。採最小安全修改；架構、對外行為、資料／授權邊界或驗收標準改變時先提出有界計畫。可重建與可刪除不是同義詞；移出唯一歷史資料前先核對封存與恢復入口。

例行可逆小修採相稱流程。真正涉及資料遺失、遷移或重要相容性風險時保留適用獨立審查；貢獻者不可把自評當獨立通過。本機唯讀核對、Owner 選定的外部雲端審查與獨立實機 E2E 各自記錄，不能互相替代或預填批准。

同一根因最多三次有證據嘗試；兩次無新資訊就停止相同修法，保留最小重現、已知／未知與所需決策。工具拒絕、身分歧義、寫入衝突或不明派送，停止依賴該前提的動作，不換入口繞過。

任務原始證據放本專案的私有任務目錄，不放全域 `.codex`。`progress.md` 用白話記錄目標、阻塞、嘗試與學習。必要報告保存 PASS／FAIL／BLOCKED／NOT_RUN、實際命令／環境、前後差異、來源與 hashes，不補造結果。PRIMARY_OUTCOME、IMPLEMENTATION、CORE_ACCEPTANCE、REQUIRED_VERIFICATION、INDEPENDENT_ACCEPTANCE、TASK_CLOSURE 分開呈現，適用關卡未滿足不得稱 DONE。

## 歷史 Harness 與正式 AUTO 已退役

Owner 於 2026-10-26 明確選擇保留日常 Agent 備份、一併退役舊程式，並要求日常運作與過去開發資料完全切割。舊 Harness、evidence、rev28、policies、config／state 與專屬交易／測試均不是日常依賴。現存備份事實轉入本專案結構化記憶；原 VERIFIED 與未知派送狀態不改，開發歷程由 Git 保存。

根目錄沒有可用的 Harness release controller／schemas／runtime-defaults；不新增框架來替代，也不聲稱 controller admission、OS sandbox、網路隔離或正式 IMPLEMENT／E2E PASS。舊 release 不可用別版 controller 冒充恢復。未來恢復正式研究須另定版本、範圍與適用獨立審查；封存與整理不授予 GUI 或重開 CLOSED grant。

## Git 與交付

產品以 master 為準。本次記事本新功能只在 `feature/line-notes-media` 開發與驗證；Owner 測試通過並明示合併前，不得合併到 master。必要時以暫存審查分支交付 Draft PR，未經另行指示不 merge、不 force-push、不改寫既有審查歷史。Owner 持續授權同範圍修改的 commit／push／Draft PR；不逐輪再問。這不擴張 GUI、相簿 Save All、記事本當次下載控制或 protected data 授權。

完成計畫、實作切片、重要驗證、交接或阻塞收尾前，檢查 Git。逐檔 stage 受權成果，不夾帶私人照片、群組／人名、原始檔名、憑證、grant 或未遮蔽原始證據。有成果就留下 checkpoint；無必要差異記 `NO_CHANGES_TO_COMMIT`，不造 empty commit。

每筆 Agent commit 的實際 message body 必須包含並填妥「意圖」、「做了什麼」、「下一步的建議」，另列真實「驗證與結果」。完成後用 `git show -s --format=%B` 核對本體，不能只把三要素寫在 PR。推送後核對遠端精確 HEAD，提供 PR、完整可讀報告與待審事項；公開報告先遮蔽私人資料。失敗如實回報 `COMMIT_OR_PUSH_BLOCKED`，不冒稱發布或外部審查完成。
