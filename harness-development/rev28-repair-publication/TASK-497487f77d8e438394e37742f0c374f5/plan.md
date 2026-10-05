# 已驗收修復的 Git 發布計畫

目標是完成使用者明示要求的 add、commit、push，發布已通過獨立審查的 Rev28 修復、測試、必要文件與選定文字證據。上一筆 c19fc90 只發布根目錄 handoff.md；這次補齊已接受的產品版本，更新交接文件的 Git 狀態，提交訊息完整記錄意圖、完成內容與下一步。

這是 QUICK 發布子任務：Planner → byte-identical machine Handoff → Implementer。產品修復本身已走原 CRITICAL 獨立審查；本次不改任何產品、測試、安全、授權或持久化語意，也不以新任務覆蓋原本必要的獨立 Acceptance。發布前必須核對最後接受的 49-file source aggregate、fresh repair 7 個檔案、首輪 patch 的其餘 postimage，以及原結果與 verification manifest 的真實 bytes。若發現不同，停止發布該 candidate，不自行修程式或沿用旧 PASS。

允許產品路徑由初始 dirty tracked 21 個檔案加 ProcessCodeIdentity.swift 與對應 test 共 23 個凍結。這 23 個只讀及入庫，不改 bytes。另可更新根目錄 handoff.md 與舊 navigation HANDOFF 文件的最新狀態入口。三個歷史修復／原生診斷／相簿任務內只挑原樣文字紀錄入庫：Plan/contract/Handoff、實際 reviewer result、PASS/FAIL、manifest、反例、測試／build／replay／provenance 紀錄及 source binding。完整 stage allowlist 另存本 task 的 publication-paths.json，加入前逐一核對。禁止批量 git add -A 或整個 harness-development。

新 task 目錄可建立計畫、驗證紀錄、提交訊息及來源／發布索引。初始 snapshot 保存所有既有 dirty/untracked 檔案、symlink payload 與 mode。照片、桌面截圖、原始 Computer Use trace、live config/state、編譯 cache 不發布、不更動。所選證據只是可攜文字追溯集，並非完整實機證據包；引用未發布的本機檔案保持明確，不重認證歷史驗收。

四個 IMPLEMENT gates：G1 接受來源／原始文字證據／schema 核對；G2 交接一致性與精確 staged blobs/path allowlist；G3 原有檔案與 symlink bytes/mode 保留（只有兩個明示 navigation 文件可變）；G4 實際同分支 commit、完整訊息、普通 push 及 ls-remote identity 核對。來源的既有驗證為 focused 22/0、full 268/0、20-fixture replay PASS；本次不重跑 Swift 或任何 LINE GUI／下載。Git diff --check 與新證據核對是本次实际檢查。

使用者已明示授權本範圍提交及 origin 同分支普通 push。遇遠端分歧不 rebase、不 force、不 reset；保留 commit 與精確阻擋。network allowlist 只是宣告範圍，沒有 OS sandbox／proxy enforcement 證明。Controller admission 不可用時以誠實 advisory format3 role results 記錄，不手動推進舊 controller。

本子任務 DONE 只表示發布完成。57 張相簿保持已完成且不得重下載；整套原生自動化仍 NOT_ACHIEVED，capture geometry／popup evidence 與舊 authority UNKNOWN、PRIMARY_NATIVE_COMPOSITION 3/3 仍保留。下一個 Agent 依根目錄 handoff.md 規劃續修與獨立驗收。
