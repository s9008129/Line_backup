# 離線實作唯讀複核

日期：2026-10-10。三位唯讀 helper 沒有修改檔案、操作 LINE、執行測試或寫入 canonical state。

## Transaction / authority

- `src/line_backup_batch/store.py:20-32,138-145` 有 operation→頂層欄位 allowlist，但只比較 top-level changed keys；對 `active_batch`、`runs` 的巢狀任意修改仍可能通過。既有 authority test 只覆蓋未授權 top-level 欄位。
- `src/line_backup_batch/service.py:215-234` 接受 caller 提供的 dispatch evidence、chooser 與 `download_started`，沒有驗證 adapter retained receipt、事件順序、SCK support ref 或 ref bytes/hash。`src/line_backup_batch/cli.py:120` 直接把 caller JSON 傳進 Service。
- `scripts/line_backup_cua_adapter.mjs:15,34-37,63-85,104-116,136-139` 的 GUI event trace 只保存在記憶體；`src/line_backup_batch/cli.py:79-81` 只核對授權上限，沒有累計／消耗 1,000 次可逆 GUI invocation 額度。
- `src/line_backup_batch/service.py:120-137` 先建立 destination/group 目錄，canonical state commit 在 `store.py:169-189` 後續發生；中間失敗可留下無 state run、無 durable side-effect receipt 的目錄。
- `service.py:262-265` 對最終 inventory 有一次 close-to-commit 比對，但 state replacement/readback 尚未完成；目的地沒有排他 lease，該間隙有檔案漂移競態。
- 已解決部分：fixture intent 標為 `fixture=true` 並回 `dispatch_authorized=false`；adapter 拒絕 fixture authority。`content.py` 對 `other_entries` 使用陣列，缺鎖測試比對 `SHARED_LOCK_UNAVAILABLE`。

## SCK / live callback

- `rev28/Sources/Rev28Core/Perception/OcrEngine.swift:90-117` 有 Vision OCR；本輪 mapper 在該檔 `:215-269` 以 native bounds 推導映射並檢查自動配對 anchor，合成 mapper tests 有跑到。
- `rev28/Sources/Rev28Core/Sensor/FrameCapture.swift:243-267,355-401` 擷取的是單一 LINE 視窗或選定 LINE 視窗聯集；目前未找到 full-display popup capture producer，也沒有把 CUA 與 SCK 兩份圖、Vision OCR、manifest/metadata 輸出成可供 Python validator 驗證的 live sidecar。
- 全 repository 搜尋 `captureMenuSupport`、`guardMenu` 顯示只有 adapter 定義與 Node fake tests，沒有 production callback wiring。
- `scripts/line_backup_cua_adapter.mjs:65-75` 在 ellipsis 後擷取 menu support，卻要求 support.frameId 等於 ellipsis 前 CUA capture hash；真實 popup image 應有自己的 capture hash，目前 frame binding 不能誠實表示。
- Node 的 10 項通過只驗證 fake I/O 下的 permit/順序/拒絕行為；不證明 SCK capture、OCR、frame mapping 或 live popup guard。

## Package / baseline

- `plan-contract.json` 與 `handoff.json` bytes/hash 相同；Plan Review waiver 引用該 contract hash；`native-admission.json` 明確記錄 `NOT_RUN`。
- canonical state baseline 仍 schema 2/revision 34/hash `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`；config hash `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`，未發生 migration。
- 11 個既有 tracked diff 路徑仍存在；目前 index 無 staged files。新增 tracked 修改位於核准路徑。任務包內 build/cache、`__pycache__`、`bin/image_decode` 均為本機產物，依計畫不得 stage。
- Swift receipt `85355bab929e445c8719cd6056e3c591` 未被早先 ledger 收錄；補回後按時間序列為第四次同一 Swift test root issue run（668ea、5b378、85355、24fb），超過每 root issue 三次上限。每次均保留原 receipt；同 root issue 禁止再跑。
- 尚未形成 execution grant、source-freeze digest/receipt、migration/live evidence、完整 E2E 報告（本輪離線報告另建立）、implementer result、獨立 Acceptance 或 Delivery receipt。
