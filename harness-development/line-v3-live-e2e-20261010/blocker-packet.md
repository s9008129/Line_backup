# Blocker packet：live E2E 的 D1/D2 結構性阻塞（implement-02，2026-10-10 傍晚）

**Decision needed（一組兩個，需使用者/新 Planner 決定）：** live 相簿 E2E 在碰任何 LINE 前景之前，已被兩個凍結工具鏈的結構性缺口擋住，需要新的 Critical 計畫或明確的範圍決策；不得由 Implementer 自行繞過、降低 gate 或改用未經核准的 producer。

## D2：每個 observation frame 都需要 SCREEN_CAPTURE_KIT sidecar，但唯一 producer 是 menu-only

- `src/line_backup_batch/observations.py:124 frame()` 對每個 record 無條件呼叫 `_support(...)`（`:143`）；live root（非 `/fixtures/`）只接受 `fixture=false` 且 `provider=='SCREEN_CAPTURE_KIT'` 的 sidecar（`:53`,`:60`）。
- 唯一會產生該 sidecar 的程式是 `rev28ctl album-support`；它要求「menu 已打開」的 popup frame：`menu_bounds ∩ addressable_bounds ≥ 16×16`（`OcrEngine.swift:501,546`）且 OCR 恰有一列「儲存全部」（`OcrEngine.swift:500,551,581`）；`main.swift:752-806` 的參數與 capture 流程即此設計。
- catalog／ALBUM_DETAIL／chooser frame 上沒有打開的 menu，因此無法在該 frame 產生合法 sidecar；而選第一張卡又必須先有 fresh catalog frame（17-key record 內含 `mapping.sck_support`）。這是意圖層級的循環依賴，不是接線瑕疵。
- 決定性離線證據：`checks/live_support_requirement_proof.py`（4680 B，SHA-256 `22c0c1ee686860d43f807c24f2c595e966858e7c6c5d9ec953a009cfaf299c7d`）對 live-shaped scratch root 執行真正的 `observations._support`：V1 FIXTURE_ONLY sidecar 正確被拒（`SCK_PROVIDER_MISMATCH`），V2 SCREEN_CAPTURE_KIT sidecar 被接受（Python 只驗形狀/一致性，不驗 producer 來源）。輸出 `evidence/live-branch-proof.stdout`（567 B，SHA-256 `0888a21113843f21a5328ebf5e5601c8f9047e8508e2469e7883c5a2889bdb2f`）。
- 唯讀盤點（Beauvoir，18:15）在整個 workspace 找不到任何非 menu 的 SCK sidecar 樣本或 producer；舊的 10-09 實機資料（menu geometry、AX dump、inventory polls、native window packet）不足以構成 classifier 或非 menu sidecar。

## D1：沒有 grounded 的 AX→17-key observation classifier

- adapter 的唯一注入點是 `scripts/line_backup_cua_adapter.mjs:42-45,75`；repo 內沒有真實實作（`tests/test_cua_adapter.mjs` 全是 fakes），`live_runner.mjs` 以 `LIVE_CLASSIFIER_NOT_GROUNDED` fail closed。
- 可行的部分地基已盤點：`harness-development/catalog-diagnostic-20261010/agreement.py` 的 OCR 日期/張數原型（真實 screenshot，scan-002 有兩列）；menu 幾何 `menu-geometry-correspondence.json`（Save All app-relative `[588,244,230,54]`，center `[700,271]`）；chooser 的真實 AX ID（`GoToWindow`/`PathTextField`/`CloseButton`/確認 `OKButton`）。仍缺 card/photo/metadata/neighbor bounds、`boundary` top/bottom、`layout_key` 語意與跨視窗一般化。

## 決策選項（建議先做一次新的 Critical Planner 計畫）

- **A（建議）**：新計畫實作「非 menu frame 的 native sidecar producer ＋ live 幾何 provider ＋ grounded classifier ＋ chooser locators」，維持原凍結設計意圖；Swift 屬新 root issue，取得自己的 ≤3 次額度；grants 需加 sensor scope。
- **B**：新計畫修改 `observations.frame()` 的證據政策，catalog/detail frame 改採 CUA-only grounding（retained frame＋classifier），只保留 menu frame 的 SCK sidecar；屬產品/證據政策變更，需新計畫與明確核准。
- **C**：縮小專案目標為人工輔助的單本流程，完整自動 E2E 記為不可行（不建議）。

## 現況與停止條件

- 已 PASS 的部分：離線 Python 67/31/5、Node 10、Swift 325/0（授權單次例外已消耗並記錄）、source/config/native-binary freeze `07c4607d…`、兩個 execution grants `675165b3…`、G_OFFLINE `d5304dd3…`、schema2→3 migration `46098af9…`（rev35，readback `45505011…`；歷史原文 `evidence/state-schema2-snapshot-01.json` `ed8075e7…`）。
- 未執行且不得宣稱：live catalog、menu 校準、intent、Save All、chooser、download、scroll、第二本、獨立 Acceptance。Save All 派送 0、chooser 確認 0、GUI ledger 尚未建立（尚無任何 GUI reservation）。
- 在新計畫核准前：停止任何依賴 LINE 前景的操作（本輪確實未做）、不派送 Save All、不改 gate/政策、不刪資料。下一個精確動作＝使用者就 A/B/C 選項給出決定。
