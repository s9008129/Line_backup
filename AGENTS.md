# LINE 相簿備份專案工作規範

## 目前產品與入口

日常產品是 AI Agent＋本專案 Skill＋原生 Computer Use。Owner 人工開啟指定相簿列表、首次指定目的地並交接前景；Agent 自動查前次紀錄、完整盤點、逐本下載及驗證，直到指定列表的合格項完成。先讀 `.agents/skills/line-album-agent-cua/SKILL.md`，相關實機操作讀 `references/verified-experience.md`，並依當次畫面調整，不重用舊座標。

不以群組中文名稱或中文 OCR 識別列表。不要求 Owner 選盤點／接續模式、逐本重新下令，或手填內部 JSON。盤點是備份必要階段；缺頁先小步補接，有具體且無法自行解決的歧義才問。

提示詞見 `docs/LINE相簿備份_使用手冊.md`。討論提示詞、審查 Skill、整理檔案或交出前景本身，不是下載授權。GUI 輸入只在真實任務授權及有效前景交接內執行；前景中斷就停止輸入。正常可逆導覽不逐點請示。主要入口為 Owner 先開好指定列表，再提交使用手冊的正式 Prompt；該訊息可同時提供任務授權與當次前景交接，不另等第二則開始指令，但仍須核對真實畫面與列表身分。

專案常駐指令只維護邊界與資料保護；Skill／references 維護操作決策，使用手冊維護唯一 Owner 啟動範本。這是專案指引，不是平台 system prompt。日常備份不得為了繼續執行而修改產品程式、紀錄規則或啟動 Git／CI 工作；開發授權須另有交辦。

## 歷史與資料保護

- `Line_backup` 是唯一核心目錄。啟動時讀 `.local/line-backup/active-task.json`、其真實 backup-records／目的地，並用 `daily memory` 讀取結構化進度。日常流程不讀舊開發資料、封存索引、外層保存點或 Git 歷史。
- 備份記憶保存在 `backup-records/events` 的追加式 JSON；歷史來源只在一次性轉入時評估，必要事實與證據內嵌後不再依賴來源。開發方法留在 Skill／程式，歷程留在 Git。缺記憶或檔案異動不能當成空帳。
- 已完成、已人工備份、已排除與受保護歷史不重下。完整盤點成立且無身分歧義時，個別受保護歷史可跳過，繼續其他已核對合格項；不把它計入完成或排除，也不稱整份列表全部完成。活動下載、未解派送與未完成命名交易不可跳過另送。日期／張數相同不能跨列表合併；舊格式或缺證據保持 `PROTECTED_HISTORY`，不升格為完成。合成 fixture 不是真實歷史。
- 一次一本。每次派送前保存並讀回 intent、新空白目的地及禁止重送紀錄；每個 attempt 的 Save All 最多一次。結果未知先查證，不能用新目錄、零計數、重置 ledger 或改寫 UNKNOWN 解鎖。
- 初始任務已授權確認中斷後的相簿級恢復時，保留原檔，在另一個新空白目錄恢復；完成的跳過，未知的不重送。LINE 原生只補缺檔仍未實證。
- 不發訊息、刪除、分享、覆寫照片、變更舊完成事實或擴及其他列表。這些副作用不包含在一般備份、審查或整理授權內。

## 現有程式與驗證

保留 `src/line_backup_batch/daily.py`、`image_decode.swift`、離線 OCR 與日常測試。小工具負責記錄、去重與檔案一致性；Agent 負責理解任務、辨識畫面與選擇操作。缺 locator／AX 標籤不是增加控制器的理由。

下載後核對預期數、穩定清單、非空檔、逐檔 SHA-256 與 ImageIO 完整像素解碼，保存完成並讀回。解碼成功本身不證明與服務端原始位元完全相同。完成紀錄或檔案異動時保留來源並停止，不重下補帳。

日常工具不簽發 GUI 權限、不觀察 LINE，也不證明提交畫面真實。`sensor_verified=false`、`real_line_e2e=NOT_TESTED`、簿記 PASS、實際 GUI、檔案驗證、正式 state 與獨立驗收須分開報告。人眼觀察是 OBSERVED，不能冒充工具 PASS 或豁免。

最小回歸：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
```

僅選本程序相符的現有 Swift SDK，不修改系統工具鏈。離線測試不能代替真實多本備份、即時 popup 或跨 Session 恢復驗收。

## 修改、風險與證據

先查 repo／worktree／branch／HEAD 與 Git 狀態，保留無關 dirty、untracked 與唯一版本。採最小安全修改；架構、對外行為、資料／授權邊界或驗收標準改變時先提出有界計畫。可重建與可刪除不是同義詞；移出唯一歷史資料前先核對封存與恢復入口。

例行可逆小修採相稱流程。真正涉及資料遺失、遷移或重要相容性風險時保留適用獨立審查；貢獻者不可把自評當獨立通過。本機唯讀核對、Owner 選定的外部雲端審查與獨立實機 E2E 各自記錄，不能互相替代或預填批准。

同一根因最多三次有證據嘗試；兩次無新資訊就停止相同修法，保留最小重現、已知／未知與所需決策。工具拒絕、身分歧義、寫入衝突或不明派送，停止依賴該前提的動作，不換入口繞過。

任務原始證據放本專案的私有任務目錄，不放全域 `.codex`。`progress.md` 用白話記錄目標、阻塞、嘗試與學習。必要報告保存 PASS／FAIL／BLOCKED／NOT_RUN、實際命令／環境、前後差異、來源與 hashes，不補造結果。PRIMARY_OUTCOME、IMPLEMENTATION、CORE_ACCEPTANCE、REQUIRED_VERIFICATION、INDEPENDENT_ACCEPTANCE、TASK_CLOSURE 分開呈現，適用關卡未滿足不得稱 DONE。

## 歷史 Harness 與正式 AUTO 已退役

Owner 於 2026-10-26 明確選擇保留日常 Agent 備份、一併退役舊程式，並要求日常運作與過去開發資料完全切割。舊 Harness、evidence、rev28、policies、config／state 與專屬交易／測試均不是日常依賴。現存備份事實轉入本專案結構化記憶；原 VERIFIED 與未知派送狀態不改，開發歷程由 Git 保存。

根目錄沒有可用的 Harness release controller／schemas／runtime-defaults；不新增框架來替代，也不聲稱 controller admission、OS sandbox、網路隔離或正式 IMPLEMENT／E2E PASS。舊 release 不可用別版 controller 冒充恢復。未來恢復正式研究須另定版本、範圍與適用獨立審查；封存與整理不授予 GUI 或重開 CLOSED grant。

## Git 與交付

產品以 master 為準。必要時以暫存審查分支交付 Draft PR，未經另行指示不 merge、不 force-push、不改寫既有審查歷史。Owner 持續授權同範圍修改的 commit／push／Draft PR；不逐輪再問。這不擴張 GUI、Save All 或 protected data 授權。

完成計畫、實作切片、重要驗證、交接或阻塞收尾前，檢查 Git。逐檔 stage 受權成果，不夾帶私人照片、群組／人名、原始檔名、憑證、grant 或未遮蔽原始證據。有成果就留下 checkpoint；無必要差異記 `NO_CHANGES_TO_COMMIT`，不造 empty commit。

每筆 Agent commit 的實際 message body 必須包含並填妥「意圖」、「做了什麼」、「下一步的建議」，另列真實「驗證與結果」。完成後用 `git show -s --format=%B` 核對本體，不能只把三要素寫在 PR。推送後核對遠端精確 HEAD，提供 PR、完整可讀報告與待審事項；公開報告先遮蔽私人資料。失敗如實回報 `COMMIT_OR_PUSH_BLOCKED`，不冒稱發布或外部審查完成。
