# 給下一位實作 Agent 的 Prompt

你是本任務的 Implementer。請先閱讀本專案 AGENTS.md、本目錄 plan.md 與本文件全文，再檢查 repo/worktree/branch/HEAD、dirty/untracked，保留所有無關工作。使用者已核准記事本媒體備份計畫，並明示本任務不需要獨立計畫審查、Simplicity Review 或獨立 acceptance；不要新增審查等待或再次詢問已授權事項。保留必要本機測試與誠實回報。

請依 plan.md 實作專案內 line-notes-agent-cua Skill、notes CLI、逐媒體永久紀錄與照片/影片驗證，更新手冊及必要測試，完成第一離線切片後繼續交付整個核准範圍。以目前相簿成功方法為依據，保留相簿既有行為和帳本，不泛化成新控制器。所有產品變更以核准計畫為準，不以本文件摘要取代原文。

研究、搜尋及簡單任務請明確派送 GPT-6 Luna 原生 sub-agent，由你親自設定邊界、監督並核對輸出；不能把助手當獨立審查。模型請求參數不證明 provider 實際用量或後端身分。不自選其他模型或提高推理 effort。派送失敗可由主 Agent 接手，不繞 SDK/API/背景LLM。

本次開發授權不包含操作 LINE/GUI、真實照片或帳本。先用合成 fixture 完成簿記、未知結果保護、發布恢復及完整解碼驗證。真實 GUI 由 Owner 另交正式任務與前景；未測標 NOT_RUN，不假填 PASS。發現需修改既有相簿公共介面、遷移真實資料或超出計畫時，保存證據並停止依賴該前提的工作。

完成後提供可讀實作報告、實際命令/exit code/證據、六項狀態及未驗證場景；逐檔 stage 同範圍成果，不帶私人資料。依持續授權 commit/push，核對 commit body 包含「意圖」「做了什麼」「下一步的建議」「驗證與結果」，並核對遠端精確HEAD；不merge或force-push。

# 交接正文

## 任務與版本

- 本目錄 plan.md 為 Owner 已核准對話計畫的 v1 落檔版；本文件為 v1 實作交接。
- 專案：Line_backup；規劃與本輪落檔前基線 master / 56d0e0fdd1f4d44630af8966141bf40f2e9c8383。
- 落檔前 git status --short --branch 顯示 master...origin/master，無 dirty/untracked。
- 文件候選由提交本目錄兩檔的 commit 識別；下一 Agent 以實際 git log/status核對，不假設HEAD仍等於產品基線。
- 本輪只落檔與Git交付，未實作產品、未操作LINE。下一角色由Owner另開主Session啟動，不由本輪助手自動開始。

## 意圖與已決策事項

真正目標是完整、可核對且可接續地保存所有貼文照片/影片，避免大量重複點擊、漏存、重下及無法查進度。Owner已選：媒體限定、backup/記事本/專區、每列表每篇分目錄、自動補唯一識別的新增媒體、明確缺項記錄後繼續。文字只作索引，不含留言/貼圖/連結。

Owner最新明示免除本任務獨立審查及獨立acceptance，取代初始規劃的審查節點；不是免除測試或允許將未測寫成成功，也不改其他任務的規範。

## 已研究來源與證據強度

已讀專案AGENTS、現有相簿Skill及references、daily.py、record_store.py、image_decode.swift與既有測試/現場回饋。重要來源：

- .agents/skills/line-album-agent-cua/references/verified-experience.md：當次視覺定位、可靠返回、chooser路徑讀回與單次操作。
- 同Skill visual-grounding.md：app-bound漏popup不代表點擊失敗，需新觀察及可靠映射。
- docs/plans/20261031-issue-48/field-use-findings.md：新列表初始化缺口不可誤當需要再次下載授權。
- daily.py 的album_key/intent/verify_directory與record_store直接綁相簿；不能只放寬影片副檔名。
- ImageIO decoder是單張完整像素解碼，不能當影片驗證。

Owner提供的本機錄影已唯讀分析：124.256667秒、2294x1490、H.264、無音訊串流；SHA-256為 54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6。原始位置見Owner本對話，勿將私人檔名或畫面寫入公開commit。

錄影觀察：照片viewer可見1/19、2/19、3/19；照片另存視窗與下載完成提示可見。主Agent補查精確106秒可見影片1/20下載圖示，107–108秒另存視窗，109秒回viewer且末端圖示改變。這些是錄影觀察，不是已驗證本機檔案成功，也未證明viewer涵蓋整篇混合附件。不可沿用錄影座標。

官方來源：
- https://help.line.me/line/desktop/pc?contentId=20000246&lang=zh-Hant ：Windows/Mac可夾帶照片影片、貼文可編輯；沒有證明記事本下載細節。
- https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffmpeg.texi
- https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/codecs.texi
- https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/doc/ffprobe.texi

FFmpeg文件支持完整解碼及錯誤偵測；probe只讀metadata不足。可評估 -xerror、輸入前 -err_detect explode、顯式映射影像與音訊、null輸出。可選map不因缺流報錯，故須另外驗有效影像與實際解碼證據。完整解碼仍不能保證偵測所有靜默損壞或與服務端原始位元一致。

## 已執行與未執行

上一規劃回合實際執行：Git狀態/HEAD/worktree清單、rg/文件讀取、ffprobe錄影metadata、ffmpeg唯讀取格、shasum、工具版本查核。影格以管線檢視，未保存研究截圖或原始測試log；原始來源為錄影及對話工具紀錄，不假稱已有私有證據檔。

指定GPT-6 Luna助手執行既有回歸：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
```

結果：73 tests、319.945秒、OK、exit 0；助手回報前後git status --short皆空。這是既有產品基線，非新記事本驗收。本輪未重新執行該回歸。

成對工具已核對：/opt/homebrew/bin/ffmpeg及ffprobe均指向Homebrew ffmpeg/7.1.1_3，version 7.1.1。PATH優先的另一ffmpeg為7.0，不可混用而不記錄。下一實作開始應再核對環境，不安裝或改系統工具鏈。

新CLI、影片驗證器、Skill行為、真實記事本下載、混合媒體覆蓋與跨Session接續均NOT_RUN。沒有獨立審查或acceptance；Owner本次明示不要求。

## 風險、停止與下一步

身分對帳須處理重複外觀與重排；不能僅按n/N認領舊媒體。已完成事實與本機可用性分開；整篇缺席不重下，仍存在但缺檔/漂移則阻止派送。缺帳本不能開空帳、UNKNOWN不能以新目錄解鎖。來源持續變動、外部writer及工具限制均不承諾原子快照或OS隔離。

下一 Agent 首先核對實際候選與plan，讀現有核心入口及測試，再以合成兩照片一影片完成第一切片。依核准範圍繼續，不等待已免除的審查。若需真正GUI或資料操作，先完成所有離線可交付內容，再清楚指出具體必要授權；不得把本文件當前景交接。

## 六項狀態

PRIMARY_OUTCOME_STATUS: PLAN_AND_HANDOFF_RECORDED
IMPLEMENTATION_STATUS: NOT_STARTED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN（新功能；既有73項基線通過）
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN（Owner本次免除）
TASK_CLOSURE_STATUS: IN_PROGRESS

Git提交/推送結果以本次工具實際回報及最終回覆為準；不預填成功。
