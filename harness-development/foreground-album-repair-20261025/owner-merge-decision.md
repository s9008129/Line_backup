# Owner merge-only decision record

- 日期：2026-10-25（Asia/Taipei）
- Owner 決策原文：「我明確豁免本次候選的合併阻擋，先合併主分支；正式下載仍停用」
- 來源：Owner direct message in active conversation。未提供或宣稱 signed record、第三方審查或 review URL。
- 綁定候選：PR #36，原程式候選 commit `af99c14459202cb148a3eceda8faa0b6871bb3f2`；其 base 為 `master@61f55595a96c58a3ca62a73ade82c6a308f98be2`。

## 決策範圍

Owner 明確給予本次 PR #36 的 merge-only exception，允許將綁定候選合併至主分支。正式下載仍停用；此決策不授權 LINE GUI、L1/L2 操作、Save All、grant 建立或其他執行時資料變更。

此例外不是外部 `APPROVE_PLAN` 或 `APPROVE_IMPLEMENTATION`，也不是獨立 E2E PASS。PR31／PR32 的既有外審狀態與 blocker 不因此改寫為批准。

## 記錄時狀態

本紀錄建立時，PR #36 仍為 OPEN/DRAFT，head 為原候選 `af99c14459202cb148a3eceda8faa0b6871bb3f2`，merge 尚待完成。後續僅以 GitHub 實際讀回的 PR 狀態及 merge commit SHA 記錄完成；本文件本身不宣稱已 MERGED。
