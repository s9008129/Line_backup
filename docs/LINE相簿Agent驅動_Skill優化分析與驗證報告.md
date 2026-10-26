# LINE 相簿 Agent 驅動：Skill 優化分析與驗證報告

日期：2026-10-26。範圍：本專案 Skill 與直接相關說明文件；不操作 LINE、不改產品程式、不變更備份紀錄／照片、不 push、merge 或啟動 CI。此次是日常 Skill 優化，不是舊正式 AUTO 研究／獨立 E2E。下述文件修訂不會解除既有可執行拒絕。

## 目標與驗收界限

使用者的核心目標是由 AI Agent 取得一項有界備份任務後，自主判讀畫面、規劃、以 CUA 操作、逐本驗證及保存進度，直到指定列表的合格相簿完成。使用者提供對象、目的地和操作授權，Agent 承擔選單定位、清單、下載結果與接續判斷。

本輪可交付的條件：既有授權不重問、popup 缺觀察先查證、輸入必須有即時定位證據、每 attempt Save All 一次、完成讀回後自主進下一本、原授權涵蓋恢復就不逐本問、工具拒絕與實測未知如實保留。Skill 修改完成不等於新版多本實機已驗證；要裁定端到端機制達成，仍需要未備份候選、有效交接及真實循環證據。

## 第一性原理

一次可靠備份必須同時具備四類條件：使用者允許的作用範圍、當下可確認的相簿與畫面、能將輸入送至正確目標的工具、能證明照片及完成事實的持久紀錄。Prompt 表達第一類，Skill 提供決策方法，CUA 提供觀察與輸入，檔案／紀錄工具處理可重複核對。任一缺口都不能由另一類的成功取代。

原始 Prompt 已授權整份合格列表下載至新空白目錄、一次 Save All、驗證及相簿級恢復。這足以支持在已交接範圍內自主下載；不需要逐本再要求「請點儲存全部」。更長的 Prompt 或更強的授權字句，不能使工具突然看見 popup，也不能證明座標或下載結果。

## 根因與修正

| 根因／證據 | 對自主性的影響 | 此次落實 |
|---|---|---|
| 主視窗 CUA screenshot／AX 漏掉獨立 popup；本機桌面截圖卻看得到 | 把觀察缺口誤報成要 Owner 代操作，雖已獲下載授權仍中止 | 新增 visual-grounding 參考：先分辨授權、觀察、輸入映射與派送結果；依當次能力補觀察 |
| 舊文只說查 popup API，缺乏其他允許觀察來源的判斷 | 缺少某個 API 就太早交還使用者 | 有條件使用平台允許的唯讀桌面截圖；GUI 輸入仍經 CUA；拒絕不可繞過 |
| 本次重開 popup 後沿用稍早位置，chooser 雖成功開啟 | 成功結果不能證明輸入前定位可靠，無法通用到視窗變動 | 明確要求重開／移動後重新擷取，驗證截圖原點、縮放、視窗 geometry 與輸入單位；不足即停止 |
| 工作流程說處理下一本，但缺少完成後具體循環 | 模型可能把單本完成當整份任務結束 | 完成事件讀回→返回同列表→新畫面定位下一本→詳細頁核對→新 intent→下載驗證，直到清單收斂 |
| verified-experience 尚寫「取得該本恢復授權」 | 可被理解成即使原任務涵蓋恢復仍逐本詢問 | 改成引用真實初始授權，由 Agent 整理逐本綁定資料，不捏造事後批准 |
| macOS typeText 指定 index 被拒，paste 無畫面變化 | 對 API／焦點的誤判可能造成錯路徑 | 加入先確認欄位聚焦、採當次支援輸入形式及讀回完整路徑的經驗 |
| 明確 UNKNOWN 只有第一筆 outcome；complete 又要求 DOWNLOAD_FINISHED | 後來取得完整照片仍可能不能提交完成；無法保證所有中斷都自主結案 | 讀源碼確認限制，文件明示可唯讀解碼並保留新證據，但不得改 UNKNOWN、重送或假稱 completion 成功 |

最後一項是程式能力缺口，不是新增文件就能解決。若未來需修正，應另做保留原 UNKNOWN、追加新查證證據、仍禁止重送的有界對帳設計與相應驗證；本輪不修改既有交易語意或批准此設計。

## Skill 設計方法與檔案

採用本機 skill-creator 的原則：只加入會改變 Agent 決策的內容、保留使用者意圖、按風險精確規範、將條件細節放在 references、用實際失敗及獨立情境推演檢查。沒有為了 BEST practice 新增控制器、腳本框架或第二套授權系統。

- `SKILL.md`：保留精簡入口，增加 Agent 決策責任及按問題載入參考的表格；明確單本完成後繼續整份列表。
- `references/visual-grounding.md`：新增 popup 畫面來源、視覺／AX／OCR 分工、座標映射、動作後觀察及停止條件。
- `references/backup-and-resume.md`：接上 popup 方法、chooser 輸入經驗、跨本循環及 UNKNOWN 提交限制。
- `references/verified-experience.md`：抽取可重用經驗，去除逐本恢復授權的歧義，明確先自主查證再提問。
- `references/daily-backup.md`：同步既有工具的 UNKNOWN 收斂限制。
- `docs/LINE相簿備份_使用手冊.md`：說明不需逐本口令，將真實單本 51 張成果與新版尚待實測能力分開。
- 原測試報告：只更正一筆重新計算確認的截圖 SHA-256，保留當次操作、缺陷及結論。

## 使用者真正需要提供的資訊

首次需要可唯一對應的保存位置，以及人工選好列表後的前景交接；後續位置可由可信 active-task 找回。任務語意需涵蓋指定列表合格相簿的下載、空目錄、驗證、保存進度及想要的中斷恢復範圍。排除與禁止事項沿用已確認來源，不因 EXCLUSIONS=[] 就清除既有排除。

不需要使用者提供群組中文名稱、座標、API 名稱、JSON、逐本批准或下載結果判斷。既有長 Prompt 已給足操作範圍，本輪沒有再加入「magic words」。工具無法安全定位或事件不可收斂時，應解決具體能力缺口，不能要求 Owner 用更詳細 Prompt 承擔 Agent 的操作工作。

## 驗證與評估

本輪沒有 LINE GUI 操作、Save All、照片下載或新的解碼結果。先前單本 51 張驗證只作為根因分析來源。

採 skill-creator 建議的一個獨立唯讀 forward-testing 子代理，實際只讀 Skill 及其相關 references，未操作 GUI／修改檔案。它獨立評估七個情境：有映射的不可見 popup、沒有映射、click timeout、跨本繼續、已授權 STOPPED 恢復、只優化 Skill、明確 UNKNOWN 後找到完整檔案。前六項能導出符合範圍的下一步；第七項發現 UNKNOWN 收斂缺口，另指出未知時提問過早的文字歧義。本 Agent 讀源碼確認前者並補寫限制，修正後者；此評估是文件行為推演，不是外部雲端審查或正式獨立 E2E。

同一唯讀評估代理第二次核對修訂及 `daily.py` 後，確認上述兩點已準確處理，並確認本報告未將推演或歷史單本結果當作新版實機成功。這次覆核證明文件對工具限制的描述一致，沒有證明 UNKNOWN 的程式能力已修復。

官方 `quick_validate.py` 首次因系統 Python 缺少 PyYAML 而無法執行；查既有環境時發現 venv Python 指向不存在的 Homebrew interpreter，未安裝依賴或修改環境。此檢查為 BLOCKED，不寫成 PASS。

替代文件檢查實際結果：以系統 Ruby 標準庫 YAML.safe_load 解析 frontmatter，核對名稱、description 與允許欄位，PASS；以系統 Python 核對 Skill 全部參考及使用手冊，共 8 份文件、25 個本地連結，缺失 0；`git diff --check` PASS。這些檢查只驗證文件結構及可發現性，不替代官方 validator 全部檢查，也不證明 GUI 行為。文件修改不需重跑產品測試套件；本輪未新增測試或修改產品源碼。

## 證據與可重現查核

相對路徑以專案根目錄為準；本機根目錄為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`。私有證據不加入 Git。

| 證據 | 可重現識別／用途 |
|---|---|
| `AI Agent使用Prompt驅動LINE相簿備份測試報告.md` | 原本分析提交 `577d8fb7106dea40541515d10e20e24d33628f63`；本輪只訂正截圖 hash |
| `.local/line-backup/evidence/current-task/E2E測試報告.md` | 當次原始操作敘述，保持原檔 |
| `.local/line-backup/evidence/current-task/menu-popup-context.png` | SHA-256 `d617f4ff8fddbccc5c93d5d62b6562c34bb12890f5e74a77953019b32b58b6b0`，本輪重新計算相符 |
| `.local/line-backup/evidence/current-task/post-progress-line.png` | SHA-256 `b415ee42eafe567998de3a5d26d0a203ef4317011dbf137c7fbd252437db83e4`，本輪重新計算並訂正前份分析報告 |
| `.local/line-backup/evidence/current-task/summary-final.json` | SHA-256 `9dac804e8eee3c234f7c9ca9a5c9916c3e64d6ac40278abed8070baad2bf6684`，本輪讀檔重算，非重新執行 summary |
| `.local/line-backup/evidence/current-task/verify-output.json` | SHA-256 `1c0b574264c495fd4b4c7abf0de63b70200b2fd426b3e3661ca2ff5dcbc49676`，本輪讀檔重算，非重新驗證照片 |
| `src/line_backup_batch/daily.py` 的 `intent/outcome/complete` | 基準 HEAD `577d8fb`；`outcome` 僅接受第一筆，`complete` 需 DOWNLOAD_FINISHED；本輪未修改 |

## 結果與下一步

Skill 已落實 Agent 自主決策、補觀察、可靠定位、逐本循環與原授權內恢復的規範。已證明的實機結果仍只有前次一份列表、一本 51 張；新版 popup 即時映射、多本循環、跨 Session 及中斷恢復皆未實測。不能因文件已完成就宣告全自動機制端到端達標。

下一次使用者另行提交真實備份任務及有效前景交接時，依新版 Skill 處理新的合格相簿，保存 popup 即時畫面／映射、逐本 Save All 次數、chooser 目的地、逐檔驗證及完成讀回；第一本完成後自主返回並處理下一本。若只有已完成項則跳過，不為湊驗收重下。若出現明確 UNKNOWN 或映射缺口，保存原始證據並報具體能力限制，不重複請求已給的下載授權。
