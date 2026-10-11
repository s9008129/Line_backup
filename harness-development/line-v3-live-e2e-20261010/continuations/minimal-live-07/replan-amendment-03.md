# ML07 Amendment 03：以雙 freeze family 延續 e01 的 B01 阻塞

日期：2026-10-11；角色：根 Planner 核准、本輪 Implementer 執行。此修訂只補充並精確取代本輪交接中 e02 實施細節；不覆寫 `plan.md`、`handoff.md` 或 machine contract，不變更產品／資料邊界及必要 gates。

## 已核實結果與累計狀態

- e01 的正式 `E01-evidence-policy` 與 `E02-runner-selftest` 均有完成收據並 PASS（分別 8 tests、3 tests）。正式 `B01-baseline-pair` 也已 launch、reap，exit 1／FAIL；其 compare 為 `BLOCKED / ANCHOR_OR_BOOTSTRAP_MISMATCH`，唯一問題是已知 FIFO 的 anchor kind `S`／`SPECIAL` 與 scanner kind `FIFO` 表示不同。e01 三個正式 IDs 均已消耗且不得重跑或改寫。原始 receipts、輸出與 compare 保留為歷史證據。
- `LIVE_CLASSIFIER_CHOOSER` 已消耗 3 次；額外授權 collection 是 `AUTHORIZED_NOT_STARTED`、`consumed=false`。此時 cumulative consumed 為 3。root issue 本輪僅 B01 attempt 1 可明確核實；其他 attempt 數保持未知，不當成 0，也不宣稱已耗盡上限。
- Native Harness Python 3.14 缺失已核實。使用者選擇不修 Harness；目前由 GPT-6 luna/high 的本輪主實作者 `context_history` 串行寫入，root 僅監督、協調與問題分析。不配置 native writers、不自製 controller、不偽造 native validation。Native required verification/closure 仍 BLOCKED。Plan Review 保留 `USER_WAIVED_NOT_RUN`；最後獨立 Acceptance 必須由未參與貢獻者完成，未取得前不宣稱 PASS。
- e01 隔離 Python 3.13 的七個 pinned wheels 與本機 dependency 安裝收據已存在；不覆寫、不重裝、不改全域環境。e01 source/policy/spec/output/claim/receipt 均保留。

## e02 有界實作與 freeze family

僅延續 e02 的 evidence 準備；e03 只留給一次有新增資訊的有界修正，epochs 上限不擴。先以唯讀 fresh baseline 核對 HEAD、index、dirty preimages、protected content、namespace 與正式收據，再將舊報告及 draft attempt ledger 更正為 append-only 歷史，不刪除舊 FAIL。新實作資料只寫本 continuation 的核准 R 路徑；不修改既有 user-dirty 檔、canonical state/ledger 或既有照片。

本階段允許 `context_history` 寫工具、evidence、報告及 attempt ledger；不修改 Swift 五個 literal paths：`rev28/Sources/rev28ctl/main.swift`、`rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift`、`rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift`、`rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift`、`rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift`。這五個路徑由 `implementation_feasibility` 保留，須等明確交接後才寫。這是作者／階段分配，不改原核准產品 allowlist。

e02 建立兩組互相獨立且 CREATE_ONCE 的來源閉包、policy、spec 與 freeze：

1. **Evidence family** 固定以 `source-freeze.json`、`check-specs.json`、`check-specs-freeze.json`、`output-policy.json` 命名。只含證據工具、E01/E02 fixtures、inventory scanner/runner、固定 Python 依賴及其精確 bootstrap inputs。`E01-evidence-policy`、`E02-runner-selftest`、`B01-baseline-pair`、`B02-preservation-pair` 僅綁定此 family。
2. **Production family** 使用 `production-source-freeze.json`、`production-check-specs.json`、`production-check-specs-freeze.json`、`production-output-policy.json`。production modules 完成後、首個 production check 前才 freeze。`N01-syntax-01..07`、`N02-tests`、`P01-batch` 至 `P04-v2`、`S01-build`、`S02-tests` 僅綁定此 family。

Runner 按 frozen check ID 決定唯一 family；拒絕任意 profile、spec、root、argv、epoch override、未知 ID、跨 family source/policy drift。兩個 family 的 source membership 分離；E01/E02 fixtures 必須驗證缺少 family、錯綁及漂移都被拒絕。正式 check ID 在 claim 持久化後即消耗，任何同 epoch ID 不重用。

唯一已核實 FIFO 由 path、device、inode、實際 lstat 類型、mode、uid/gid、size、mtime/ctime 一併確認。掃描只 lstat，不 open/read/hash FIFO。SPECIAL/FIFO 正規化只消除表示差異；不能掩蓋身份、類型或 metadata 變化。新增反例證明這些任一變化仍使 B01 BLOCKED；未知 special 仍 BLOCKED。

Policy 必須以精確 normalized paths、producer、phase、type/cap、lifecycle、receipt/readback 規則涵蓋已知輸入、兩組 freeze/spec、production publication、D01 CUA-host check/producer、各自 bounded registration/artifacts、報告/recorder/current 與舊 e01 immutable receipts。未知規則拒絕；不採用 flat filename、整個 R 豁免或事後 allowlist。Recorder 的已完成 log 是獨立 producer 寫入物，必須依其實際路徑與已觀察 hash 登記；不得修改該檔。兩掃期間停止全部寫入，包含 report、attempt ledger 及 recorder。

`prepare_epoch.py` 和 `prepare_dependencies.py` 必須先修為安全的 exact e02 binding；不得直接執行仍硬編 e01 或會碰撞既有 publication 的版本。e02 dependency 如確有需要，只複用已驗證七 pins，寫入 e02 隔離 root、local pip、hash lock、exclusive/readback；禁止 network fetch 或全域 install。所有正式 publication 先完成純讀 preflight，之後 exclusive/no-follow/fsync/readback。

## 驗收順序與停止

在 e02 中 E01→E02→B01 各執行一次；必須完成 pair、anchor/bootstrap/protected/Git 對帳及 B01 publication tail readback，全部 PASS 才停止並交 root。B01 未 PASS 前不執行 D01/CUA、不碰 LINE、不修改四個由另一作者保留的 Swift 路徑，也不進入 production check。B01 掃描期間任何工作區寫入均停止。

D01 需獨立 frozen CUA-host spec、exact producer/path/cap/registration/readback；不得把 D01 假裝成 `live_entry` dynamic artifact。D01 不 acquire owner、不建 destination、不寫 state/intent、不派送 UI。任何會要求 LINE 前景的動作先由 Implementer 告知 root 精確 app/surface 與下一個 capture；root 待使用者明確交接後再回覆。未交接不可執行該操作。

本輪此委派先完成可審查的 e02 evidence preparation，停於 B01 PASS 後向 root 交接或第一個 material blocker；此停止點不取消原 plan 授權的後續兩本 E2E。直到該交接前，不執行 D01/CUA、產品交易、Save All 或 GUI input。連續兩次沒有新增資訊即停止；root issue attempts／epoch 消耗如實記錄，unknown 保持 unknown。本階段不執行 commit/push；已完成的 artifacts 交 root 作 review 與後續流程協調。
