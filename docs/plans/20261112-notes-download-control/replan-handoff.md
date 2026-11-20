# Replan 交接：修正記事本原件保存誤判

- 規劃輸入 HEAD：`92c1ca61da62184f110ea8363ff54480f5f3c41c`。
- 計畫：[replan.md](replan.md)。本交接對應該檔 SHA-256：`7f07148f4787bc2943468714ee621916b2d7f57f8d2322f13f703b3164686cf4`。
- 交付 commit 以本輪實際 Git 收據為準；不要求新 commit 等於輸入 HEAD。
- 本輪結果：`PLAN_DRAFT_COMPLETE`；沒有產品實作、下載或獨立接受。

## 核心新證據

CUA 的同一次回傳含有效 Buffer 截圖，162,388 bytes；舊 `instanceof Uint8Array` 為 false，`Buffer.isBuffer` 與 `util.types.isUint8Array` 均為 true。同一份原件已保存並逐 bytes 讀回 MATCH，主代理看過記事本列表。先前「需要 Owner 修復 CUA 才能取得截圖」的結論不成立；舊報告保留，新文件明確更正。

私有證據：`.local/line-backup/tasks/20261112-notes-observation-replan/`。原圖／AX 不進 Git、不外傳；公開計畫已遮蔽私人畫面內容。精確 runtime 版本、目標帳本、五張來源資格、U1 viewer 控制、派送與 completion 仍未證實。

## 下一個實作切片

依 replan 第 6–8 節，主要只改 `evidence-template.md` 的原件保存範例；必要時在 `gui-inventory.md` 補短連結。使用可靠的 byte array 判斷、精確副本與可判別錯誤，保留不可覆寫／讀回／bind 前停止等保護。既有帳本流程已有明文，不再堆同義條文，不增加 CLI 或泛用 GUI adapter。

必須執行最終 Markdown 範例本身的一次原生唯讀 smoke，並以私有 fixtures 核對跨 realm、offset 子視圖、無效型別及失敗保護；再依計畫執行三條既有回歸。兩次舊／新 capture 歷史已記錄，下一次同根因原生 smoke 是第三次；仍失敗就保留證據停止，不換 Session 重置。

## 人工角色與授權

本輪只交接規劃，不自動啟動 Implementer、Review、下載或驗收。沿用 Owner 本任務不需要 Review 的選擇；實作者自檢與獨立接受仍分開。若 Owner 啟動實作且沿用既有助手要求，使用 GPT-6 luna、high，由主代理監督；請求參數不能當作 provider 身分或用量證據。

S1 之後沿手冊附錄 C 的既有日常入口完成 S2／S3，不要求 Owner 帶本計畫、UUID、JSON 或額外模式。原指定五張的窄 scope、有效前景、帳本禁止重送與所有原停止條件持續有效。規劃／實作角色不憑歷史授權轉為真實下載角色。

## 六項狀態

- PRIMARY_OUTCOME_STATUS: BLOCKED（照片未有完成證據）。
- IMPLEMENTATION_STATUS: NOT_RUN（本 replan 尚未實作，舊 S1 成果保留）。
- CORE_ACCEPTANCE_STATUS: BLOCKED（來源／派送／照片驗證尚缺）。
- REQUIRED_VERIFICATION_STATUS: PARTIAL（診斷及同筆原件讀回有證據；最終範例 smoke、回歸及真實備份 NOT_RUN）。
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN。
- TASK_CLOSURE_STATUS: BLOCKED（規劃可交付，修復與備份未結案）。
