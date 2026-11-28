# LINE 記事本 Pre-Bind「零同名候選」誤判與 `evidenceTools` 未載入歸因實作與安全審查紀錄

- 審查日期：2026-11-25（Asia/Taipei）
- 審查候選：分支 `feature/line-notes-media`（基準 HEAD `ab525d3284f801df3508e328619c3df245f77261`），候選工作樹 `git diff` SHA-256 `dc41e6275c1afc614a7cda9a00c80be9e2a0ab0c7d501ecd8b384b676e116978`
- 對應計畫：`docs/plans/20261125-notes-prebind-misread-fix/plan.md`（v2，SHA-256 `34a6eb36116ecfe2163538b513640baf0a7824296766927ccf84997f940c310a`）
- 審查角色：獨立 Reviewer（Herdr pane `w9:pD`，唯讀審查）
- 審查依據：`code-reviewer` Skill 與 `AGENTS.md` Independent Review Constitution（Code Review ＋ Security Review）
- 補記全量相簿相容回歸（Worker1 於同一凍結工作樹實跑）：`PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` 73 tests OK（零 `src/` 更動）。

## Code Review

### Review Verdict: APPROVE
- **Review Type**: Code
- **Core Goal Alignment**: 變更忠實實作 plan v2，消除同名門檻誤讀並統一未載入歸因，支撐跨模型無人值守備份。
- **Diff / Scope Hygiene**: 僅 6 白名單檔（57+/23-），零 `src/`／手冊／`AGENTS.md` 異動，標題錨點全保留，無膨脹。

### Findings
None

### Verification Evidence
- 唯讀核對：`git status --short --branch`（6 檔 M＋既有未追蹤未動）、`git diff --stat`、`git diff --check`（exit 0）、逐檔 diff 比對 plan v2（`SKILL.md` 三處、`download-and-ledger.md` L232／L245 原子對齊＋步驟 2＋過濾禁令＋對稱規則＋Route A／C、`gui-inventory.md` 列表＋顯示名稱限制、D6／D7、`evidence-template.md` 預載唯一本文＋單一 js fence＋註記、`test_notes_input_helper.py` `tools_mode`＋新回歸測試）。
- 錨點完整：`## 啟動與帳本對帳`、`### 候選帳本展開（唯讀）`、`## CUA 觀察原件落地`、`### 列表` 皆保留；單一 js fence＝1、guard 存在、`emitImage`＝1；Python 候選腳本本體零增刪（僅圍籬前說明句）。
- 實測：`notes --help`（exit 0）、新防護兩測試 OK（0.076s）、`test_notes_input_helper.py` 64 tests OK（4.836s，主控端另測 4.592s）；全量 `test_notes*.py` 388 tests OK（主控端 59.961s，Worker1 實跑通過）；`test_daily_records.py` 73 tests OK（Worker1 實跑通過）。

## Security Review

### Review Verdict: APPROVE
- **Review Type**: Security
- **Core Goal Alignment**: 資料保護紅線全保留，零寫入／零派送停止條件與 `NOT_RUN` 界限未放寬。
- **Diff / Scope Hygiene**: 無新增依賴、無動態執行擴張，僅文件判讀收緊與測試參數化。

### Findings
None

### Verification Evidence
- 紅線：仍禁單憑名稱／OCR／`active_hint`／單一日期張數認領、禁未完成 N 份核對即 `init`、真實歧義零帳本寫入停 `init`／`bind` 前、D6／D7 缺少證據 `NOT_RUN` 保留；guard fail-closed（`captureCalls==0`、`emits==[]`、`writes==[]`、空目錄）由新測試證實。
- 隱私：diff 無真實群組名稱／個人姓名／`local_list_id` UUID（UUID／`records_root` 樣式掃描零命中）；`CUA_EVIDENCE_TOOLS_NOT_LOADED` 全域統一 7 處一致。
- 信任邊界：無新增網路／套件／`eval`／shell 插值；測試僅既有 `subprocess node --input-type=module`＋`tools_mode` 分支，無權限擴張。

## 證據界限
- 以上全部屬離線自動化回歸與靜態核對結果；真實 LINE 記事本 GUI、CUA 實機 `captureAndPersist`、實機多候選交叉核對、`bind`／`init`、下載與跨 Session 恢復均維持 `NOT_RUN`。
