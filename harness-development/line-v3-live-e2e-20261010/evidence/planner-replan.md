# 唯讀 Planner 複核

日期：2026-10-10。本複核由未參與本輪實作的唯讀 subagent `/root/planner_replan` 完成；沒有修改檔案、跑測試或操作 LINE。

## 已核實事實

- 本輪凍結計畫是 CRITICAL 任務：唯一 v3 writer、schema 2→3 遷移、兩個不同 cap=1 lifecycle，且 G_OFFLINE 全套測試 PASS 是 migration/live 的前置條件。
- Python 77 項與 Node 10 項的收據 exit code 均為 0；Swift 26.5 最新收據執行 320 項，317 PASS、3 FAIL。
- Swift mapper/test 同一 root issue 的實際執行序列為 `668ea46f205c42f1b5d5ba5aa3f966e4`、`5b37804c7b314bdeb80238d415d2fc1f`、`85355bab929e445c8719cd6056e3c591`、`24fbfc8ff57743af97e60a9edc25ba23`。這是四次，超出三次上限；不得透過改名、換模型或新 task 把它清零。
- Canonical state 仍 schema 2/revision 34，hash `ed8075e71d22f13c4d1f2394c896bdda4696dcfbd4e7cb9d7f29c0fff59bf3a9`；config、production destination、LINE UI 均未變更。
- 使用者已交出 LINE 前景，但沒有 fresh capture，也沒有輸入；因 G_OFFLINE/G_AUTH 未過，此交接未使用。

## 未知與阻塞

- 巢狀 state transition 權限、可信 dispatch receipt、1,000 次 GUI invocation 持久計數、prepare 目錄 side-effect receipt、commit/readback 間 destination 漂移保護仍不足。
- 沒有 full-display SCK popup capture/paired CUA-SCK-Vision sidecar producer 或 production `captureMenuSupport`/`guardMenu` callbacks；既有 adapter 對 menu support frame 的識別綁定錯在 ellipsis 前影格。
- 因同一 Swift root issue 已超額執行，當前 G_OFFLINE 沒有符合既定 attempt policy 的重跑路徑。更早未知歷史仍是 UNKNOWN。

## 建議下一步與停止條件

Planner 建議保留四次 Swift 收據，停止同 root issue 的任何後續執行，不得把 317/320 升格為 G_OFFLINE PASS。若要重跑或修改 G_OFFLINE 的驗證方法，先由新 Planner 計畫列明四次歷史、所需 gate/attempt policy 變更，再取得使用者明確授權；critical gate 若改動，還須獨立 Plan Review 或該新計畫的明確 waiver。不得 migration 或 live input。

若新計畫允許繼續其他離線實作，Planner 建議順序是：先補 transaction authority、receipt、GUI quota、副作用收據和內容穩定性；再建立帶獨立 post-ellipsis frame identity 的 full-display SCK sidecar/guard pipeline；之後才處理合法 G_OFFLINE 驗證途徑。任何未解 transaction 或 live mapping 都須 fail closed。
