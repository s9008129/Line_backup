# 進度（implement-02 / live-bridge 這輪）

## 我們在解決什麼

目標是用唯一 v3 writer 完成兩本不同、尚未 VERIFIED 相簿的完整下載與狀態提交，並實際驗證第一本完成後的 bounded scroll 與第二本重新定位。這一輪把「離線與授權前置」全部做完，並把 live 分支還缺什麼用可重跑的方式證明出來；LINE 前景沒有被操作，任何點擊、Save All、chooser、下載次數都是 0。

## 目前狀態（白話）

- **已完成且有收據**：source freeze（21 個產品檔、`7e7f124a…`）、兩份 live grants、G_AUTH 全 operation PASS、G_OFFLINE 四組收據（Python 67/31/5、Node adapter、Node --check、Swift 26.5 325 項 0 失敗，用的是使用者核准的唯一一次例外額度）、schema 2 rev34 → schema 3 rev35 遷移（快照 `ed8075e7…` 保存、讀回 `45505011…`，只有 schema_version/revision/active_batch 改變，歷史 runs 與兩本 VERIFIED 完全相同）。
- **live runner 已建好**：`live_runner.mjs`（`d3936b1f…`）通過 `node --check`，adapter 形狀的假 I/O 測試 11/11，capture/guard 兩種模式的 routing 測試也 PASS。它是把既有 CLI、adapter、rev28ctl producer 接起來的橋，不改產品行為。
- **新發現的兩個結構性阻塞（D1/D2）**：任何 observation frame 都必須附一張 SCREEN_CAPTURE_KIT sidecar 影格；但我們唯一的 producer `rev28ctl album-support` 只能在「相簿選單打開、且 OCR 看得到『儲存全部』」時工作。catalog、detail、chooser 這些畫面沒有開選單，因此拿不到 sidecar。另外，把 LINE 的 AX 畫面轉成 17-key observation 的 classifier 目前只有測試假件，沒有可上線的實作。證據可重跑：`checks/live_support_requirement_proof.py`（`22c0c1ee…`）與 `evidence/live-branch-proof.stdout`（`0888a211…`）。
- **狀態沒有被破壞**：遷移前快照、舊 runs、兩本 VERIFIED、目的地 239 個既有檔案、802 條 dirty/untracked 工作全部保全；index 仍是空的、HEAD 仍是 `7172604d…`（G_PRESERVE 檢查：baseline 648 條 untracked 與 11 條 dirty 全數還在）。

## 嘗試與學到什麼

本輪 ledger（`attempt-ledger.json`，現為 28 筆，最新 sha `d67fdaf7…`）新增兩筆：第 27 筆是 live runner 建置＋三個唯讀 helper 的平行複核（介面稽核確認最後一個 routing 缺陷已修、沒有新缺陷；smoke 11/11）；第 28 筆是 D1/D2 的可執行結構證明。兩筆都有新資訊，沒有連續無進展。第 28 筆教會我們：現在缺的不是「再接一條線」，而是一個新的 producer 能力與 classifier，必須由新計畫決定，不能由實作端臨時補。

## 卡在哪裡、需要什麼決定

需要一個明確決定（D1/D2，詳見 `blocker-packet.md` 與 `E2E測試報告.md`）：

- **A（建議）**：開一個新的 Critical Planner 計畫，新增非選單畫面的 full-display SCK sidecar producer、真實 menu geometry provider、可上線的 AX classifier 與 chooser locator。Swift 預算視為新的 root issue（舊 issue 的四次收據不刪不改）。
- **B**：由新計畫改寫 observation 證據政策，允許非選單畫面用 CUA 影格而不再強制每格 SCK sidecar——這是證據政策變更，需要使用者明確同意。
- **C**：暫停／縮小 live E2E 範圍，只保留已完成且有證據的離線、授權與遷移成果。

## 如果下一步失敗會怎樣

若 A 案的新計畫仍拿不到可用的 non-menu sidecar，或 classifier 無法用真機畫面接地，live 分支會再次停在同一個 material blocker；我們會保留新的事實與收據，回到使用者面前重新選 B 或 C，不會私下放寬 gate、不會重送 Save All、也不會用測試假件冒充實機證據。
