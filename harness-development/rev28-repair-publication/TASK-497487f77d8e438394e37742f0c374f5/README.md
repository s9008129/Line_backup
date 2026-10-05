# 修復發布與證據使用界線

這個 QUICK 子任務依使用者明示授权將既有已驗收修復 add、commit、普通 push；不實作新產品變更，也不替代原 CRITICAL 獨立審查。發布前 HEAD 是 c19fc90b22791f417f31d31fd57a4191aa628c42；source aggregate 維持 097ed57f97ed9d22ff0919e75bc116237877b84e7b1e78ef505cce7f6d311b19。

根目錄 handoff.md 是下一個 Agent 的交接入口。accepted-product-paths.json 列出原樣發布的 23 個已接受檔案；historical-evidence-paths.json 列出 88 個選定歷史文字紀錄；publication-paths.json 是這次精確 stage allowlist。evidence/publication-index.json 列出除索引自己之外的交付 bytes/SHA。

evidence/accepted-source-verification.json 是本次核對：49 個來源檔案、第一輪 patch 重建的 16 個未被取代 postimage、fresh repair 的 7 個接受後檔案、62 筆歷史 manifest entry、選定文字紀錄及 format3 role schema。這些是本次讀檔核對；22/0 focused、268/0 full、20 fixtures 等仍是原 task 已實際執行的歷史驗證。没有本次 Swift 重跑或新獨立 Acceptance。

原歷史 Plan、PASS/FAIL、命令及 log 原樣发布，絕不改其 source/contract/role 欄位以假裝本次重新驗收。部分原路徑仍指向只存在同一 Mac 的 binary、snapshot、live registry、GUI 原圖或完整 trace。這個選定文字集合不具完整 evidence dependency closure，也不是 production permit；新 clone 可以取得程式，不能繼續既有實機 transaction 或復原未知 authority。

照片、config/state、桌面截圖、raw Computer Use trace 與編譯 cache 保留本機。初始完整 snapshot、提交後 Git receipt／保留性及 advisory Implementer result 也留在本機 task；提交檔案不包含未來的 post-push receipt，避免自己的 commit hash 循環。

57 張單一相簿 task 已 DONE；整套原生自動化仍待修復與驗收，native Phase A geometry/popup 的直接證據與舊 entitlement 未知仍保留。這次 Git 交付没有 LINE GUI、下載或新 live attempt。
