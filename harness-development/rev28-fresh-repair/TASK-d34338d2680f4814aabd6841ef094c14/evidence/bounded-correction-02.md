獨立 Acceptance 對 candidate 1 回傳 REVISION_REQUIRED，指出原前後 process 讀取沒有包住最前面的 SCK 與最後面的 signing／AX／CG。

本輪 attempt 2/3 沿用 exact frozen Plan／contract。只更動已列明的 NativeObservationSession、既有測試、ARCHITECTURE 與本 task 證據；不改 scope、gate、容差、public chooser／dispatch 語義或生產權利。原 Plan 第 3 點要求真正 process-before/after，這是同一根因的讀取順序補正。這份核對是本機 advisory scope check，不冒充 native controller admission。

已在 candidate 1 實際重現：新 stateful regression 保持 PID、簽章、AX、window ID 和 frame 相同，分別在 preInventory、postSigning、postAX、cgInventory 中把 process start 從 7 改成 8。1 個測試共 8 個 assertion 失敗，四種情況皆錯誤接受、capture count 增至 1。原始 red log 與 exit 1 保留。

最小修正：第一次 process read 在 initial SCK 前，最後一次在 post signing／AX／CG 後；保留實讀前後值、比較 equality，typed refusal／原 deadline／成功才增 count 不變。這仍不保證 OS 原子快照。下一步跑本 candidate 的必要檢查並交回独立 Acceptance；若仍有 material 缺口則按同一根因額度處理，不重設歷史權利或預算。
