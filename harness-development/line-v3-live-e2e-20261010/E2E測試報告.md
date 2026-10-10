# LINE v3 交易整合與兩本相簿實機 E2E 測試報告

**狀態：PARTIAL / BLOCKED；本輪未操作 LINE、未遷移 canonical state、未開始任何相簿下載。**

## 目標、計畫與目前結論

本輪依 Harness 4.8.0、format 3 計畫，目標是以唯一 v3 writer 完成兩個不同未 VERIFIED 相簿的兩個獨立 cap=1 lifecycle，並實證第一本釋放 owner 後的實際 bounded scroll 和第二本 fresh 定位。Plan Review 依使用者 waiver 記為 WAIVED/NOT_RUN；事後獨立 Acceptance 仍為必要 gate。

本輪只完成部分離線整合及讀收據。Python 回歸 77 項與 Node adapter 10 項有 PASS 收據；Swift 26.5 全套執行 320 項、317 項通過、3 項失敗。後續盤點發現同一 Swift root issue 實際已跑四次，超出每 issue 三次限制，因此停止該 issue，不再重跑。另有獨立唯讀複核指出 live SCK sidecar producer/callback 未接線及多項 transaction authority 缺口。G_OFFLINE 與 G_AUTH 未 PASS，依序不得進入 migration 或 live LINE 操作。

## 基線與環境

- 使用者計畫列出的前一版 HEAD 是 `faf5b298cf563b87baa5adf2ba9cc651a8739991`；本輪保存的實際 implementation baseline 是其直接子 commit `7035809c695dd7410bc919ed791914137c87174a`（`建立 LINE 相簿 v3 批次備份基礎並封鎖舊 writer`），分支為 `v43-ab/codex-rev28`。該 v3 基礎已在本輪開始前的 Git 歷史中，未在本輪重寫。
- Canonical state：schema 2、revision 34、SHA-256 `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`。Config SHA-256 `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`。本輪未寫 state/config。
- 舊歷史與相片 baseline 仍依原件保留；state/config hash 與 baseline 相符。目的地目錄未在本輪重新準備，舊的 65 張候選目的地只採用計畫中的歷史唯讀記錄，本輪未以它做下載目的地。
- 工作樹開始時已有大量 dirty/untracked 工作；本輪未清理、未 stage，index 維持空。baseline 中 11 個既有 tracked diff 路徑仍存在；新增修改落在核准路徑。build/cache 留在本機。
- Python：`/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python`；Node：`/opt/homebrew/bin/node`；Swift 使用 `/usr/bin/swift` 與明確 SDK `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk`。所有 task-local fixtures、Swift scratch/module cache、stdout/stderr/receipt 均位於本任務封包。
- 目前觀察到的 product/source/test digest 為 `bdeab5da447fcfad71a1afb1aa9a8c3138f279f865e68ab75017a128d907a284`。這是報告快照，不是 migration 前 source freeze。

## 實作差異與離線結果

已完成的部分整合包含：內容 inventory 將 `other_entries` 輸出為 schema 所需陣列；缺 lock 測試核對 `SHARED_LOCK_UNAVAILABLE` code；project-binding fixture/schema 改由 task-local 資料供應；`Store.update` 改為內部 `_update`，Store 依 operation 核對頂層 transition 欄位，migration 限定只變更 schema_version 與新增的 null active_batch；fixture intent 明確標為不可 dispatch；Node adapter 加入五秒 freshness、單次 token 消耗、SCK menu guard callback seam、chooser destination 驗證和每次 scroll 最多 0.25 viewport；Python observation validator 要求可追溯的 SCK sidecar、native window metadata、至少三個自動 OCR anchor、residual/margin/交集限制。這些差異的目前 source/test 列表及 hash 在觀測快照內。

Python 命令由 `run_python_attempt.py` 執行三個 unittest 群組：`test_batch_*.py` 41 項、`test_project_binding.py` 31 項、`test_transaction_core.py` 5 項，exit code 均為 0。PASS receipt 是 `evidence/python-attempt-f3ee5d7423a24d8199ba2f33cc8781ca.json`（相對路徑；絕對路徑 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/evidence/python-attempt-f3ee5d7423a24d8199ba2f33cc8781ca.json`；bytes 5337；SHA-256 `fc10698afcf472bf5315da2fd863b303b8141603c070eb3569b9434b5c376d83`）。Receipt 記載實際 argv、cwd、環境覆寫與各組 stdout/stderr bytes/hash。測試資料由 task-local fixture root 提供；沒有讀寫 production state 或相片。

Node 命令 `/opt/homebrew/bin/node --test /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/tests/test_cua_adapter.mjs` 通過 10 項，exit code 0。Receipt `evidence/node-adapter-4b0b62cd61364344a68f047a56d20276.json`（bytes 1085；SHA-256 `55abfd7a46c9215ff30b4dddc947ecedb51274c971231eb829f13e5af3f55fb6`）；stdout SHA-256 `75d9b6cca24170157dc76030ab171db3631bbd7cadb8f5545cf516d72ce6017b`，stderr 為空檔。這組使用 fake I/O，只證明 adapter sequencer 的離線拒絕與順序行為。

Swift 命令使用 `swift test --package-path /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/rev28 --sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk --scratch-path /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/swift-build-26.5`，環境綁定 task-local fixture root 和 module cache。最新執行 `24fbfc8ff57743af97e60a9edc25ba23` 的 320 項中有 3 項 `ProjectBackupBindingTests` 以 `inconsistentAuthority` 失敗；出錯原因是巢狀 fixture `state.json` 的 `runs[].destination` 與 `runs[].intent.destination` 仍指向舊任務絕對路徑。Receipt JSON bytes 1939、SHA-256 `21f9bcddb45baf27fe3c41bf2cc090d0d5b6ea860b854d106224e388d9a66087`；stdout SHA-256 `1726c9819d72eaad035cd422e1e29342695df26062f1f7c945a4d2d3be750719`；stderr SHA-256 `da72972a9a381c98e1be3633905300e8ddb81127c4f2528b2bd4018ed641e77a`。同一失敗亦見於 `85355bab929e445c8719cd6056e3c591`：320 項、3 項相同失敗，receipt JSON SHA-256 `7df2c49cca55b3091dcd1056f204335225a16898dc7f8afc544da9b6614b0b1b`，stdout `c898fe1775f4dd89da7c2c86efcda5c441fba96c822bfbe94704f4072c19357a`。

實際 attempt 時序已記於 `attempt-ledger.json`：668ea 編譯錯、5b378 fixture env 缺漏、85355 nested authority 失敗、24fb 同問題重跑失敗。前三次中的 85355 收據原先漏登，後來由唯讀 audit 發現；故實際總數為四次，超過三次上限。本輪已如實補錄並標記 policy overrun；不再執行同 root issue 的 Swift 測試。未知的更早歷史數量仍為 UNKNOWN，沒有記作零。

## 交易與感測風險複核

本輪唯讀稽核結果保存在 `evidence/offline-audit.md`（相對路徑；絕對路徑 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/evidence/offline-audit.md`；SHA-256 `d17f0f2d2179dc118df6084ce3f3b8ec42e743381960473e6908456860388716`）。主要未解項目：

- transition allowlist 只看 top-level 差異，不能限制 `active_batch`/`runs` 巢狀欄位，也未證明只改當前 active run。
- `Service.dispatch` 與 CLI 信任 caller JSON，尚無 retained adapter receipt 的完整 hash/事件順序/SCK evidence 驗證。
- 授權允許最多 1,000 次可逆 GUI invocation，但 adapter trace 只留記憶體，未持久消耗額度。
- `prepare` 在 canonical run commit 前建立目錄；中間失敗時沒有 durable side-effect receipt。
- finalize 在 commit 前重掃 inventory，但 destination 沒有排他 lease，最終比對與 state replacement/readback 之間仍有 drift race。
- 有 Vision OCR 和 native-bound anchor mapper，但沒有 full-display popup SCK producer 或 live paired CUA/SCK sidecar pipeline，亦沒有接線 `captureMenuSupport`/`guardMenu` 的正式 live callback。Adapter 現在把 menu support frame id 綁到 ellipsis 前 CUA hash；這不能代表 ellipsis 後 popup 的真實影格。

## E2E 步驟、GUI 動作與副作用

1. 建立/使用核准 task package，保存基線、fixtures、測試 runner、原始收據及 ledger。此步已執行。
2. 執行 Python、Node、Swift 離線檢查；Python/Node PASS、Swift FAIL 並發現 attempt-policy overrun。此步部分完成，G_OFFLINE 不通過。
3. 執行前置 gate/review：`plan-contract.json` 與 `handoff.json` 完全相同，waiver hash 對齊；native admission 保持 `NOT_RUN`。無 migration grant 或 source freeze。
4. Schema 2→3 migration 未執行。原因是 G_OFFLINE 未通過且 G_AUTH execution grant/source freeze 缺漏。
5. 使用者表示 LINE 群組相簿列表目前已在前景，並授權在實作後繼續測試；但 live preflight、catalog、menu calibration、任何 LINE foreground input 均未執行。因 G_OFFLINE 未通過，此次前景交接未被用於任何擷取或輸入；未來若新計畫通過前置 gate，需先再次確認畫面/前景仍新鮮，再開始輸入。
6. 第一本 transaction、Save All、chooser、download、內容驗收/VERIFIED 均未執行。
7. 第一本釋放後 bounded scroll 與第二本定位/transaction 均未執行。
8. 本報告已保存；獨立 Acceptance 未執行。報告與 blocker packet 完成後，使用者另行明確指示先建立本機部分 checkpoint；root 只 stage 本輪核准差異與 task package，建立了一個 local commit。沒有 push 或 remote readback；因此 G_DELIVERY 仍為 PARTIAL，不代表 Acceptance 或 E2E 完成。

本輪由 CUA 觸發的 GUI input invocation = 0；Save All = 0；chooser confirmation = 0；download = 0。Canonical state、config、production backup files 均未寫入。本輪寫入只限核准的產品 source/test 路徑與 task package 的 fixture/evidence/report/progress/ledger；Swift build/cache outputs 留在本機。未刪除或覆寫舊工作。

## Gate 判定

| Gate | 本輪判定 | 證據/原因 |
|---|---|---|
| G_AUTH | BLOCKED | 缺本輪 structured execution grant 與 source freeze；dispatch receipt、GUI cap、nested transition authority 尚未驗證。 |
| G_OFFLINE | FAIL | Python 77 項與 Node 10 項 PASS；Swift suite 320 項中 3 項失敗，且同 root issue 有四次執行超額。 |
| G_MIGRATION | NOT_RUN | G_AUTH/G_OFFLINE 未通過；revision 仍 34。 |
| G_CATALOG | NOT_RUN | 未做 live foreground handoff。 |
| G_MENU | BLOCKED | 無 full-display SCK popup sidecar producer、production callbacks 或 post-ellipsis CUA/SCK frame binding。 |
| G_FIRST | NOT_RUN | 沒有 intent、Save All、chooser、下載或 state transaction。 |
| G_SCROLL | NOT_RUN | 第一本未完成，未做任何 scroll；不標記通過。 |
| G_SECOND | NOT_RUN | 第二本未定位或執行。 |
| G_PRESERVE | PARTIAL | state/config hash 及 dirty-path presence 符合基線；尚未完成整輪 preservation/delivery 驗收。 |
| G_REPORT | PARTIAL | 本輪離線活動、收據、未知與停止原因已索引；完整兩本 E2E 報告內容未產生。 |
| G_ACCEPTANCE | BLOCKED | 尚無可供獨立 reviewer 驗收的合併完成產物。 |
| G_DELIVERY | PARTIAL | 依使用者明確指示建立本機部分 checkpoint；未 push，沒有 remote readback，且 Acceptance／其他必要 gates 未通過。 |
| G_PLAN_REVIEW_WAIVER | PASS（decision only） | 明確使用者 waiver 已記錄；Plan Review 仍是 WAIVED/NOT_RUN，並非 review PASS。 |

## 下一步交接

此報告與原始收據交給唯讀 Planner helper 做阻塞後的 replan 分析，記錄於 `evidence/planner-replan.md`。這不是正式獨立 Plan Review；正式 Plan Review 依使用者 waiver 記為 WAIVED/NOT_RUN。Planner 建議保留四次 Swift 收據、停止同 root issue、先提出能在既有 attempt policy 下完成 G_OFFLINE 的路徑；若沒有合法路徑，須先請使用者決定是否建立新 Critical 計畫及處理 gate/policy 的方式。最小阻塞與下一個精確決策記於 `blocker-packet.md`。本輪沒有使用已交接的 LINE 前景，也不宣稱任何 album backup complete 或 task DONE。

Format 3 role result 保存在 `results/implementer.result.json`。該 JSON 依 immutable Harness 4.8 `result.schema.json` 做了直接 JSON Schema 檢查並通過；因 native admission=`NOT_RUN`，stage packet/native controller 的專用 validation command 未提供，因此 controller validation/admission 仍記為 NOT_RUN。

## 證據索引

本報告主要證據的相對路徑均位於 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/`：

- Plan: `plan.md` SHA-256 `aed61bd406116eefcbd1c81fb146ec71f8d5584f25e56013265384492074bcc7`。
- Contract/handoff: `plan-contract.json`, `handoff.json` 各 5866 bytes，SHA-256 `ffef63e5ce295910cf0b07a5cc5615bc2719dc651e425306677666b5d8a68ab1`。
- Waiver/policy: `plan-review-waiver.json` SHA-256 `fadf73d6b97813a7a3df4a8dac45f51e3647af7f45217dfd88ef5b1d6aec5491`; `gate-policy.json` SHA-256 `0ec524480fe0037449d42a4573bcbca508a47683f46cfe629d7e92831fc4e85a`。
- Source snapshot (not freeze): `evidence/observed-source-snapshot.partial.json`, 7611 bytes, SHA-256 `5f84e8d0d3d21fac0a4adf88b92ade04b5862cdb955510101c21419e89dee245`, aggregate source SHA-256 `bdeab5da447fcfad71a1afb1aa9a8c3138f279f865e68ab75017a128d907a284`.
- Transaction/sensor/package reviews: `evidence/offline-audit.md`, SHA-256 `d17f0f2d2179dc118df6084ce3f3b8ec42e743381960473e6908456860388716`.
- Planner replan note (not Plan Review): `evidence/planner-replan.md`; blocker packet: `blocker-packet.md`, 3191 bytes, SHA-256 `78f5e5435c1c7789dee4b33d361e800998790fc1e9ee2bb798561425c465b3cc`, 說明 overrun、未過 gates 與下一步。
- Attempt ledger: `attempt-ledger.json`; records Python/Node/Swift runs, omitted Swift receipt recovery, actual overrun, failures, and unknown history.
- 尾端空白敏感的兩份 baseline diff 與三份原始 stdout/stderr 保持原字節，並以可無損解壓的 gzip 副本納入提交；路徑、原始 bytes/hash、壓縮 bytes/hash 及 roundtrip 結果見 `delivery/raw-text/manifest.json`。原始文字檔仍留在工作目錄。暫存快照的 `git diff --cached --check` 通過。
- Baseline: `baseline/state-facts.json`, `baseline/source-hashes.json`, `baseline/git-status-porcelain.txt`, `baseline/preexisting-tracked.diff`, `baseline/preexisting-index.diff`, and `baseline/backup-inventory.json`.
- Python command outputs: `evidence/python-{batch,project_binding,transaction_core}-f3ee5d7423a24d8199ba2f33cc8781ca.{stdout,stderr}` and `evidence/python-attempt-f3ee5d7423a24d8199ba2f33cc8781ca.json`.
- Node outputs: `evidence/node-adapter-4b0b62cd61364344a68f047a56d20276.{stdout,stderr,json}`.
- Swift output: `evidence/swift-26.5-{85355bab929e445c8719cd6056e3c591,24fbfc8ff57743af97e60a9edc25ba23}.{stdout,stderr,json}`.
