# F01 實機驗證重規劃進度

Owner 本次指定 Planner，要求讀補充診斷及其交接來源，先評估既有規則，再制定有界實機驗證方案；交付後停止，不進行 GUI／下載／實作／驗收。Owner 另明示規劃完成後使用 GPT-6 Luna 子代理梳理上下文與提交訊息，主 Session 執行 add／commit／push。

起始本機為 `f64ba8dc5875fdb88f2e4ac5b9107896ed90cf87`，兩份前輪診斷文件尚未提交。未動這兩檔；唯讀核對期間觀察到外部工作已提交為 `7c71a3f1f3fc23eb0a745f09545f6b0a2d121b32`，本機／遠端一致、樹乾淨，才將此版本記為規劃基準。沒有 reset、clean、merge 或改寫他人提交。

repo 沒有指定的 policies 路徑；找到並讀取全域既存 v4.9.0 原檔。首次嘗試讀範本時使用 `plan.md` 檔名失敗，檔案清單顯示實際為 `plan.template.md` 等，改讀正確檔名。未修改全域政策、範本或恢復 controller。

讀補充／原診斷、前輪驗收、兩份私有 packet、原 F01 plan／handoff／implementation／重審、現行記事本 Skill／GUI 本文及歷史工具文件。原始 calls 證實 stale index，正確索引又能往返；仍沒有真實底端、來源／歷史對應或下載結果。既有規則已涵蓋新鮮 AX、輸入後觀察、逐卡對帳與停止，故不先安排產品修改。

本輪 hash 核對第一次以通用格式讀舊 extra 清單，把註解列當檔名而 exit 1。實讀前幾行後確認該清單有註解，且其路徑是 task-relative；其餘兩份是 repo-relative。第二次按各清單原有基準、只解析 hash rows，86／14／50 項全部相符，exit 0。清單重疊，不加總成獨立檔案數。這是本輪核對腳本錯誤，不是證據損壞或產品缺陷；沒有新 GUI 嘗試。

文件核對第一次把新檔的 `git diff --no-index --check /dev/null <path>` 預期差異 exit 1 誤當檢查失敗。單獨重讀回傳確認 stdout／stderr 為空、無空白錯誤；第二次腳本依 no-index 的實際差異語意記錄，另以逐行空白檢查及 stage 後的正常 `git diff --cached --check` 核對，不改文件來掩蓋工具退出碼。

草案選定沿用既有產品，Owner 先釐清來源／歷史關係；定義有效位移、可靠邊界、載入未定、工具拒絕及 F01-V0／V1／V2。原列表的 184 迴圈不恢復，歷史嘗試不重置。只有 Owner 能核定後續角色、來源、前景與盤點寫入範圍；沒有下載或新實作預授權。

本輪原始命令、source hashes、文件檢查、helper 請求／回覆及 Git 回傳留私有同名任務區；公開只提交本目錄四份去識別化規劃文件。提交訊息需由指定 Luna helper 在草案完成後提供，主 Session 核對事實後才使用；實際提交與遠端 SHA 以私有交付證據及最終回覆為準，不在此預填成功。

產品回歸、新 GUI／下載／E2E、正式計畫審查及新獨立 Acceptance 皆 NOT_RUN。計畫草案完成，核心驗收、獨立驗收及結案保留 BLOCKED；細節與六狀態見 [角色報告](role-report.md)。
