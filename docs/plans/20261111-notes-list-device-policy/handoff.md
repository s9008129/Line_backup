# 有界重規劃交接 v1（待審，非實作核准）

## 精確任務與版本

目標是修正普通記事本列表把歷史 device 當永久容器身分的問題，讓首次下載及後續完整流程可執行，保留受管理媒體／交易與禁止重送保護。

- 基準：`feature/line-notes-media`／`60c1a251b6bff7e9d3b5e72c455cc01228657242`；主 worktree，不處理其他 worktree。
- 待審文件：本目錄 `plan.md` 與本 `handoff.md` v1；來源 hashes 見私有任務 `source-before.json`，交付版本 hashes 見 `delivery-receipt.json`。
- 必讀需求：Owner 最新「進行 re-plan、符合意圖與核心目標、切勿過度工程化」及原問題提報。Owner 同時提供 02 角色，但明示工作為重規劃，本輪採 Planner 產物，不聲稱獨立計畫審查。
- 原始根因：`docs/diagnostics/20261111-notes-directory-device-binding/issue-analysis.md`；既有 v3 plan／handoff 保持不變。
- 起始只有既存 Owner 未追蹤檔；不得吸收或改動。私有證據、帳本及照片不提交。

## 已完成與未完成

已讀最新需求、02 與 01 角色邊界、4.9 routing、原診斷及舊計畫／交接，核對共用 list gate、有效 binding 的事件種類、可用性與操作文件。確定不需要首次下載專用 reattest 或新持久身分機制。

本次只規劃與文件核對，未改產品／AGENTS.md／Skill，未讀其他私人列表、未重跑真實 CLI、未操作 LINE。舊合成診斷是既有證據，本輪產品測試、真實下載與獨立審查全部 `NOT_RUN`。

本版的政策選擇是：普通 created／destination 綁定允許 list-only device 差異；有效 list-directory-reattest 綁定仍嚴格核對，保留再次漂移停止。staging／completion／active／pending 自身 metadata 不放寬；UNKNOWN 不解鎖。舊 v3 的不可改 device 限制只在普通 list gate 的這一點被提出修訂，尚待適用核准。

## 下一個人工步驟

建議 Owner 以本版 plan／handoff、原診斷、精確產品基準及文件 hashes，另啟計畫 Simplicity Review，再進行 CRITICAL 獨立 Plan Review。審查應檢查：範圍是否僅共用判定與必要文件，是否保留舊轉接合約，V1 是否真的涵蓋完成兩項及跨 Session，是否有不必要的新狀態或日常步驟。

Owner 需決定本版限定的列表容器信任取捨：授權路徑／來源辨識加 inode 不等於證明實體 volume；此方案不偵測匹配 clone。這個開發決定不轉成每次日常下載的再次確認。

核准與必要關卡完成後，由人交 Implementer 做**一個完整切片**；不是現在啟動實作。首切片含共用判定、V1–V5 及一致文件，完成後交 implementation Simplicity Review。V6 由 Owner 使用原日常 Prompt＋有效前景產生實機證據，V7 獨立接受；不得用本計畫代替實際任務授權。

超界條件及所有 V1–V7 owner／證據／停止條件以 `plan.md` 為準。拒絕或新根因時保存證據交還 Owner，不自動跨角色修復、重測或結案。

## 六項狀態

PRIMARY_OUTCOME_STATUS: BLOCKED（規劃 PLAN_DRAFT_COMPLETE；備份未完成）

IMPLEMENTATION_STATUS: NOT_RUN

CORE_ACCEPTANCE_STATUS: NOT_RUN

REQUIRED_VERIFICATION_STATUS: NOT_RUN

INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN

TASK_CLOSURE_STATUS: NOT_DONE
