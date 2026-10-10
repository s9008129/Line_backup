# E2E 測試報告 — live-grounding-04／Planner 文件階段

目標：正式證據鏈修復後兩本LINE完整E2E。實際本階段：唯讀研究、使用者決策、計畫與Handoff文件交付。產品實作及E2E尚未執行。

## 實際順序與工具

1. 讀取AGENTS、01_plan_prompt、03_handoff_prompt、line-album-backup skill、原live-grounding-03報告／blocker／plan／程式及原始receipts。
2. exec_command唯讀讀取安裝bridge binaries、file／SHA、codesign、otool／strings／nm、外部候選來源、deployment manifest、既存readiness，及launchctl print／ps。沒有執行request／navigation／readiness。
3. CUA getState讀取工具文件；同persistent kernel唯讀import node:fs/promises／crypto及readFile。getApp、getAXStateAndScreenshot唯讀觀察當前相簿。capture值只在記憶體做bytes/hash/type检查，沒有writeFile。
4. GPT-6 luna read-only research helper查核官方Apple／Node docs；沒有product edits或independent review。
5. 使用者選定兩本E2E、v2視覺證據、允許調整版面；之後明確授權文件落檔與add/commit/push。
6. exec_command與apply_patch只在新CON產生文件／本地delivery scratch。publish_documents.py保存contract、waiver、來源hash與results，從frozen contract直接複製Handoff；驗證與發布結果見document-verification.json及Git收據。

## 觀察、結果及限制

跨realm screenshot、schema key defect、intersection缺失、chooser phase等原始資料與識別資訊見research.md／research-facts.json。CUA screenshot尚無workspace原件，所以只記OBSERVED，不將記憶體hash當retained-frame PASS。native配對、production detector、menu／latency／第一本／scroll／第二本／content驗收／獨立Acceptance全部NOT_RUN。

| 項目 | 本階段結果 |
|---|---|
| 唯讀binary/source研究 | 已完成，可重验來源refs與hash見input-manifest.json |
| bytes記憶體相容性 | OBSERVED；copy bytes/hash相同，未寫raw screenshot |
| 文件JSON／hash／readback／handoff equality | 依實際document-verification.json，不當native schema PASS |
| Native Harness admission/publication／CONTRACT/RESULT validators | NOT_RUN；原Python3.14 runtime失效，無stage invitation |
| 產品離線suites | NOT_RUN；329/0等舊PASS僅歷史，不認證新candidate |
| G_CATALOG/G_MENU/G_FIRST/G_SCROLL/G_SECOND/G_ACCEPTANCE | NOT_RUN／產品仍受prerequisites阻擋 |
| 真實LINE input/SaveAll/chooser confirmation/download | 0／0／0／0 |
| State/config／backup內容改動 | 本階段無mutation；state/config/ledger hashes重新核對 |

## Preservation、副作用與嘗試

baseline.json與本地preexisting-status.z在新增文件前保存HEAD/index/11個tracked dirty hashes及完整Git status識別資訊。文件驗證須保證所有新增repository paths在CON、舊dirty bytes不變、state/config/gui-ledger不變。外部daemon.status為活資料，不能用heartbeat改變宣稱本輪寫入。

本輪沒有修改product源碼、舊報告、十四個scope-drift artifacts、外部bridge、global Harness或TCC。預期副作用限CON文件和Git index/commit/push。normal push一併發佈目前分支既有兩個相關commits，新增commit仍只含CON文件。

原root-issue歷史及所有失敗保留在live-grounding-03/attempt-ledger.json，本階段沒有新增產品／GUI attempt。一次唯讀研究用舊Python3.14 launcher時收到no such file or directory，接著確認Python3.13可啟動；這是runtime阻塞新資訊，不是產品test PASS或重置額度。

## 證據索引與下一步

input-manifest.json／document-manifest.json逐筆列repo-relative（external來源為明確絕對）、absolute、bytes與SHA-256。所有引用來源原件應依各自ref重新讀取，舊人眼frame沒有PNG ref就維持缺失。document-manifest不自引用；Git提交與遠端readback收據另記於本地.local/git-publication.receipt.json，發布後保全於.local/post-publication-verification.json。這兩項本機交付收據保留在workspace，不加入提交以避免自引用commit hash。

Implementer每輪實測須新增或更新本報告，保留原failure history及每次的新資訊，列實際commands/environment/action order/pre/post/state/readback及effects。每個live gate需自身原始證據。任何所需capability/authority不具備即保存精確blocker，返回Planner重新規劃。沒有兩本＋實際scroll＋獨立Acceptance全部PASS前，整體目標NOT_ACHIEVED。
