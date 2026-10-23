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

## Implementer 執行附記 — 2026-10-10 UTC／2026-10-11 Taipei

本次依凍結 Plan 開始 IMPLEMENT。HEAD 為 b06b47b717da1aa9ae63e70d6d86c24d34282bba，branch 為 v43-ab/codex-rev28。在核准範圍內既有的 tests/test_cua_adapter.mjs 未提交內容已保留並在其後追加測試案例；其他 dirty/untracked 檔案未重設、清理或整批 stage。

### 實際順序、結果與新資訊

1. 使用一名唯讀 subagent 盤點核准檔案、既有 diff 與函式接點。它未修改檔案、未執行測試或 GUI；結論確認 adapter 兩條 capture 路徑都以 instanceof Uint8Array 驗證，Python v2 grounding 仍有 v1 AX-only 假設，且新 passive native-context source 尚不存在。
2. 修改 scripts/line_backup_cua_adapter.mjs：新增跨 realm Uint8Array/Buffer byte-view normalizer，拒絕 DataView、非 byte views、空值及超過 16 MiB 的資料，依實際 byteOffset/byteLength 複製；transaction 與 navigation capture 都記錄 request 前後 UTC 及 monotonic interval，並在分類前核對保留檔 reference 的 bytes/hash/AX reference。
3. 在原已 dirty 的 tests/test_cua_adapter.mjs 後追加跨 realm view、Buffer subarray offset、拒絕型別、hash 與 capture interval 案例。這些新案例尚未執行，不能判定 PASS。
4. 將既有 checks/run_command.py 複製到 CON 根目錄並用計畫指定的 Python 3.13 路徑啟動 Node syntax check。該工具假設自己位於 CON/checks/；放在 CON 根目錄使它把 repository root 算成 /Users/hsiaojohnny/Documents/ChatGPT。命令因此在 scripts/line_backup_cua_adapter.mjs 前停止，Node 回報 MODULE_NOT_FOUND。這不是 adapter syntax 結果。
5. 上述工具錯誤在核准範圍外新增四份收據至 harness-development/line-v3-live-e2e-20261010/continuations/evidence/。依 Plan 的 preservation failure route，停止後續產品修改、測試與 GUI 操作；四份檔案留原位，未嘗試搬移或刪除。詳見 scope-incident-001.json。

### 命令、環境與證據

實際命令為：

    /opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -B harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04/run_command.py node-adapter-syntax-01 -- /opt/homebrew/bin/node --check scripts/line_backup_cua_adapter.mjs

Python executable SHA-256 為 34af8eed630f46919dcb77457077ae3564f7cd25f5d83c56530e64d00de78804；Node 為 v26.7.0。實際 cwd 是 /Users/hsiaojohnny/Documents/ChatGPT，不是固定 project root。Exit code 1，錯誤原文與 stdout/stderr/hash 均保存在範圍外 receipt 中，引用如下：

| 證據 | Relative path | Absolute path | Bytes | SHA-256 |
|---|---|---|---:|---|
| scope incident | harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04/scope-incident-001.json | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04/scope-incident-001.json | 5976 | 0fa1e0d11325bdbc15290b98d178cd808e89ae9aaf3c773bf106ee3f8c56418f |
| failed invocation | harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.invocation.json | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.invocation.json | 303 | e6af579520a315edb79877c4fb7fb6ecab8066cd9f1c4c9fccd396d296bc9e3e |
| failed receipt | harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.receipt.json | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.receipt.json | 678 | e1d16b370f6f7c9d7d6275e8afd21fe77946dececef290ebc64a740914637719 |
| failed stderr | harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.stderr | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.stderr | 318 | 8948d951d254f345d8f1ce65686618a314622897641a6a037058ed782bff1fa4 |
| failed stdout | harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.stdout | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/evidence/node-adapter-syntax-01.stdout | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| adapter after edit | scripts/line_backup_cua_adapter.mjs | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/scripts/line_backup_cua_adapter.mjs | 39953 | bf83dd93e8fd53ace40d6a65f09bcfa9bf31ffa0fbfff92dfb2e8f43459026d2 |
| adapter tests after edit | tests/test_cua_adapter.mjs | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/test_cua_adapter.mjs | 18529 | 0bb0d99636f35150272fc952b6efa84261e1e9c68375225787221b8b389662bd |
| prior attempt ledger | harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/attempt-ledger.json | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/attempt-ledger.json | 10014 | 205461d838d4d1b4d596c5637e03ea087373d229837c3b4aec57fe5a4cdeba1a |

state/backup_state.json 仍為 252115 bytes、SHA-256 455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6、revision 35、2 VERIFIED；config/line_backup_config.json 仍為 384 bytes、SHA-256 5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362。本輪沒有發送 LINE input、Save All、chooser confirmation、下載或 state/config 寫入。Backup inventory 未重跑，不能聲稱逐檔內容驗收。

### Gates、嘗試與停止點

| Gate／狀態 | 實際判斷 |
|---|---|
| G_AUTH | 未完成本輪 grant/runtime/source closure 驗證；不得 PASS。 |
| G_OFFLINE | BLOCKED；Node syntax check 在錯誤 cwd 失敗，產品 syntax 與新測試均未知。 |
| G_MIGRATION | 只重新讀取 state hash/revision；本輪完整 history/migration continuity 驗證未執行。 |
| G_CATALOG、G_MENU、G_FIRST | BLOCKED；沒有 fresh LINE frame/native pair，也沒有 UI 操作。 |
| G_SCROLL | SCROLL_TEST_NOT_RUN。 |
| G_SECOND | BLOCKED；兩本交易未執行。 |
| G_PRESERVE | FAIL/BLOCKED；四份新收據超出 frozen allowed paths。原位置保留。 |
| G_REPORT | PARTIAL；本附記與 incident packet 已落在 CON，完整測試證據不足。 |
| G_ACCEPTANCE | NOT_RUN。 |
| G_DELIVERY | PARTIAL；未完成離線 gates、實機 E2E 與 Acceptance。 |

LIVE_CLASSIFIER_CHOOSER 已知一次舊 issue attempt；本次是第 2 次有界實作嘗試，但未取得產品驗證資訊。最後一次教訓是本地收據工具依賴所在子目錄，複製到不同位置前必須先核對它計算的 root 和輸出目錄。新增 PASSIVE_NATIVE_CONTEXT 歷史額度仍須按原 ledger 核對，不能因新 continuation 將未知歷史設為零。下一步必須先由 Planner 審查這次範圍外寫入並凍結修復／收據處置方案；此環境沒有 controller-backed Planner stage。LINE 前景尚未要求交接，因前置離線與證據 gates 尚未通過。
