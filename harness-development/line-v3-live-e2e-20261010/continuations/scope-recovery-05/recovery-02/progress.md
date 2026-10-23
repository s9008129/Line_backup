# Recovery 02 進度（Implementer → Planner）

日期：2026-10-11 ｜ 任務：TASK-20261011-line-baseline-recovery-02 ｜ run_id：a8e86935-d398-4e9c-b860-03f52cba8fec ｜ stage：IMPLEMENT

## 我們在解決什麼

修復本專案本地的「完整檔案系統基線工具」與「固定 root 的 check runner」，並對維持不變的 CUA adapter 做一次離線驗證；同時保留所有歷史證據與無關工作。本輪不碰 LINE、不下載、不改產品／狀態／config／ledger、不 commit／push、不用網路。

## 現在到哪裡了（本輪結果）

- G_BASELINE PASS（37 checks）：兩次一致的 host anchor、4 份完整 inventory（FIFO 僅 lstat、從未開啟）、3 個一致性／差異比對全部 PASS。
- G_RUNNER PASS（11 checks）：固定 root 的 preflight 與 12/12 runner selftest 通過。
- G_ADAPTER_OFFLINE PASS（15 checks）：`node --check` 通過；`node --test` 31/31 通過、0 fail。
- G_PRESERVE **FAIL**（23 checks 中僅 `compare_preservation` 失敗）：p1→p2 一致性比對判定 2 筆 `ADDED_NOT_ALLOWED`（`tmp/inventory-preservation-02.stdout`、`.stderr`）與 5 筆 `FIELD_MISMATCH`（`tmp/inventory-preservation-01.stdout` 的 bytes／ctime_ns／mtime_ns／sha256／size）。機制是 host 捕捉自身 stdout 的完成時序，與比對政策未宣告 host-capture 檔之間的互動；不是保存內容真的被改動。
- 底層保存事實乾淨：baseline b1→p2 的 35 筆新增全部落在 RUNROOT 內且與計畫宣告一致；RUNROOT 外 0 變動、0 移除、0 欄位變更；FIFO 在 4 份 inventory 中完全一致（content_read=false、content_hash=null）；239 筆 backups 全部為 REGULAR 且逐檔唯讀驗證。
- 尾檔（E2E測試報告.md、attempt-ledger-recovery-02.json、report-manifest.json、implementation-result.json）正在定稿；由使用者授權的平行子代理起草、root 逐項核對後凍結。

## 卡在哪（blocker）

preservation 比對政策與 host 擷取檔的互動：`SELF_OUTPUTS` 只宣告 `evidence/` 下四份 inventory JSON，未把 `tmp/` 的 host-capture 檔計入，導致同一掃描在重複執行時把「自己剛寫出的捕捉檔」判為違規新增。這是可重現的政策問題；G_PRESERVE 的 FAIL 如實保留，需要新計畫修正政策後再驗——不得降低 gate、不得重跑已用盡的 check。

## 嘗試次數與額度

- 本輪 5 個官方 check 各只執行一次（receipt 獨佔、永不重跑）；4 份 inventory 與 4 個 compare 亦各只執行一次。
- 產品嘗試 `LIVE_CLASSIFIER_CHOOSER` 已 3/3 用盡（於 `node-adapter-syntax-02` 啟動時消耗）；任何進一步產品檢查都需要明確的新決策。
- baseline helper 的 2 次歷史失敗保留、不重置；本輪以修正後的新工具完成 fresh baseline。

## 上一次嘗試學到什麼

兩次一致的 host anchor 加上全新 inventory 工具（FIFO 只 lstat、完整掃描不中途回空），可以完整覆蓋工作區並證明 RUNROOT 外零變動。G_PRESERVE 的失敗來自工具／政策的自我參照（self-capture）時序，而非保存被破壞；這帶來明確的新資訊：需要把 host-capture 檔納入宣告，或改為不落地捕捉。

## 是否更接近完成

是。五個 gate 中四個已有明確結果（3 PASS／1 FAIL；G_REPORT 待 manifest 讀回後 PASS），runner 與 adapter 的離線路徑已證明可用；剩下是 preservation 政策修正，以及（下一輪才有權規劃的）LINE 現場 E2E。

## 下一步與失敗後果

- 需要的決策：核准新計畫修正 capture／compare policy（建議：把 host-capture 檔納入宣告，或改為不落地捕捉），並以 fresh lineage 重新驗證 preservation。若再次 FAIL 且無新資訊，依 Harness 升級人工決策；不重複重試、不降低 gate。
- 本輪不需要 LINE 前景；SCROLL_TEST_NOT_RUN、兩本交易未執行；parent 狀態維持 NOT_ACHIEVED／BLOCKED／BLOCKED／INCOMPLETE／PENDING／REPLAN_REQUIRED。

## 交接狀態

`E2E測試報告.md` 是本輪的正式證據交接物，交付對象為下一輪 Planner。目前執行環境沒有可用的 Planner 通道，因此 Planner 交接尚未完成；報告與本進度記錄保存在 RUNROOT 內待交付。
