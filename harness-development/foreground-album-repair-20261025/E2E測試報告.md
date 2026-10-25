# 前景相簿修復與專案整理：完整交接報告

task_id：FOREGROUND-ALBUM-20261025；Plan revision 2，見 [plan.md](plan.md)。
本輪是本機候選修復、離線測試與 archive-first 整理。**沒有新 LINE 下載，也沒有正式 AUTO 或獨立 E2E PASS。**

## 原始目標與正式恢復決策

使用者只需把正確 LINE 群組相簿列表交到前景，指定儲存位置；Agent 從頂到底盤點、逐本對帳、跳過已完成／排除、安全下載與驗證。不得要求 GROUP_NAME，不以中文 OCR 精確相等作必要條件。

Owner 正式選擇 `RECOVERY_STRATEGY=ALBUM_LEVEL`、`PHOTO_LEVEL_RESUME=FUTURE_RESEARCH`。完成相簿永不重下載；部分檔案與 intent 全部保留；前次已終止且派送狀態明確、獲該本恢復授權後，才使用另一個新空白目錄。UNKNOWN 不自動重送。照片級續傳不阻擋目前驗收。

Owner 追加由 GPT-6-luna 平行分析並實際執行整理，root 負責監督／分析／裁決；先封存再清理，實際搬移到開發專區由 Owner 之後執行。永久刪除封存資料仍由 Owner 決定，本輪未永久刪除。

## 已交付的行為

| 項目 | 實作與結果 | 實機狀態 |
|---|---|---|
| P0 前景／群組隔離 | `daily.py` 以目的地、目錄識別及本地 UUID 分隔；新 Session 重做前景對應。名稱不是 key，沒有 GROUP_NAME 參數 | NOT_TESTED |
| P1 完整盤點 | 新 scan 從頂端開始；頁間有序 suffix/prefix 重疊；同日期／張數另需視覺識別；底端需同一末頁、實際捲動紀錄與無位移；未定位或消失卡片阻止完整結論 | NOT_TESTED |
| P2 恢復與去重 | 完成／排除禁止新 intent；未知禁止重送；明確終止＋專屬恢復來源才建新空目錄，原檔保留。舊格式來源標 PROTECTED_HISTORY，既不重下也不當完成 | NOT_TESTED |
| P3 正常核准準備 | request 輸出群組 UUID／目的地／候選／來源 hashes 與缺件，保持 consent／review／runtime grant 未成立；不啟用 GUI | BLOCKED：一般跨群組 issuer 尚未受審實作 |
| P4 Skill／手冊 | 主要 Skill 精簡；情境載入 verified experience／daily reference；白話 Prompt 不輸入群組名稱；正式採相簿級恢復 | 本機文件檢查 PASS |

Agent 繼續使用原生 Mac Computer Use 的 metadata strip → 詳細頁核對 → fresh popup/menu → 單次 Save All → 新空白目錄 → SHA-256／既有 ImageIO 方法；沒有新增 GUI 框架或修改 Harness。

`daily` 是簿記及檔案驗證輔助工具，不觀察或操作 LINE，不授予權限。summary 明示 `AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED`、`AGENT_ATTESTED_ACCOUNTING_ONLY`。其簿記 PASS 不能取代真實畫面、正式交易或獨立驗收。

## 實際順序與來源

1. 唯讀確認 repo、dirty、分支及工具。起始主工作樹 `v43-ab/codex-rev28@5919de77373af834d96a0842cce07a310c2bfc13`；原有三份 tracked dirty 與大量 untracked 工作。
2. 讀 AGENTS、README、手冊、Skill、verified experience；讀 PR28 真實五本報告、PR32 原始觀察與 10/24 私有 batch summary。PR32 原始紀錄從仍存在的獨立 worktree 讀取，不把本分支缺檔誤判資料不存在。
3. 只讀 Mac app inventory、LINE AX／截圖；當時看到登入畫面，沒有相簿列表交接。Owner 表示正在使用電腦後停止 LINE 觀察；沒有任何輸入。影像未保存，不提供不存在的截圖 hash。
4. 寫入離線 daily 草稿及反例測試，追蹤真實失敗後修正；之後 Luna 在隔離 worktree 完成防護補強並整合。
5. 三位 Luna 分析分支／來源、檔案／依賴、文件／可攜性。發現主分支的文件較新不代表含最新產品；PR32 持有唯一接續實作。不能直接刪兩支未整合來源。
6. 建立完整外部工作樹 clone 快照及 all-refs.bundle；copy、bundle create、bundle verify 均 exit 0。
7. Luna 逐節點核對後，把凍結的 63 個項目移至外部 `removed-from-active`；另準備乾淨 master 候選，只帶 113 個必要產品 paths，不整支合入 PR31 的 1,900 個歷史檔案。
8. 整合本輪 daily／Skill／手冊／可攜 driver／整理說明至候選，進行本機驗證。來源／測試原始輸出與歷次失敗全部保留 private。

## 授權根因與停止邊界

`policies/line-two-album-pilot-v1.json` 的 `gui_authorized_by_this_profile=false` 刻意區分來源政策與執行權限；不是 typo。`src/line_backup_batch/cli.py:native_authorize` 只核對既存 project grant，回傳 `dispatch_authorized=false`，不是 issuer。現有 project／ONE56 route 還綁定舊 task、group/config、root、來源、runtime、Owner 決策、真實 review 與 ledger。

本輪不改 false、不挪用 ONE56、不重開 closed grant、不重置 ledger、不偽造同意或審查。新群組的正常正式 issuer／交易入口需要精確審查與實作；目前只提供不授權的核准準備入口。真實 51 張案例的目的地尚未掛載，當輪前景／L1／L2／runtime 亦未成立。因此沒有執行 Save All。

## 測試、首次拒絕與修復資訊

| 階段 | 實際結果 | 學到的事與處理 |
|---|---|---|
| 初版測試 1 | 0 tests，編譯 setup FAIL | CLT 預設 SDK 比 compiler 新；改選已安裝 SDK26.5，未改系統 toolchain |
| 初版測試 2 | 14/15 PASS | ImageIO 正例 exit2；實際探針確認 Foundation 將 `/private/var` 正規化成 `/var`，與 pathlib 相反 |
| 初版測試 3 | 15/15 PASS | fixture 使用 checkout 內真實隔離目錄；沒有放寬原 decoder 的 canonical guard |
| Luna 防護補強 1 | 18/19 PASS | 錯誤碼變更破壞既有拒絕契約；保留原 completed/excluded error，另給 protected-history 拒絕 |
| Luna 防護補強 2 | 19/19 PASS | 任意舊文字來源不可冒充完成；明確 UNKNOWN 不可普通解除；恢復保留原檔 |
| CUA adapter 離線 | 22/22 PASS | 合成 CUA I/O；沒有任何真實 click |
| 完整 Swift 首輪 | 333 tests／16 FAIL | 該次命令漏傳既有 fixture env；保留失敗，不把負面案例的 throw 當整體成功 |
| 完整 Swift 補 env | 330/333 PASS | 真實 producer 10 個來源、Swift 只認 9 個；加入來源後又揭露 manual-archive fact 契約差異 |
| Swift 有界修復 | 聚焦 17/17 PASS；完整 334/334 PASS | sourceNames 納入 manual_archive.py；對 manual_archive_match 嚴格要求 Boolean false，true／0／缺值皆拒絕；不啟用 manual archive 新能力 |
| 最後候選可攜檢查 | 19/19 PASS；四個 CLI help exit0 | 在另一個 repo 路徑驗證整合成果；正式 driver 只有 --help，沒有執行 verify 本體 |

關鍵實際命令：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
node --test tests/test_cua_adapter.mjs
PYTHONPATH=src python3 -B -m line_backup_batch.daily --help
PYTHONPATH=src python3 -B -m line_backup_acceptance --help
PYTHONPATH=src python3 -B -m line_backup_batch --help
python3 <bundled-skill-creator>/scripts/quick_validate.py .agents/skills/line-album-agent-cua
LINE_BACKUP_INSPECTION_FIXTURES=<private-six-case-fixtures> SDKROOT=<installed-SDK26.5> swift test <private-scratch-options>
```

Skill validator 實際使用本機既有 Python3.11／PyYAML，輸出 `Skill is valid!`、exit0，未安裝依賴。正式 reconciliation driver 只改成 repo 相對根與必要輸入參數；未執行正式 verify 本體。

## 真實業務計數與完整性

| 指標 | 本輪實際值 |
|---|---|
| LINE GUI 輸入／捲動／開相簿／選單 | 0／0／0／0 |
| Save All／chooser 確認／取消 | 0／0／0 |
| 新下載照片 | 0 |
| 51 張新案例 ImageIO | NOT_TESTED |
| 完整列表頂端／重疊／末卡 | NOT_TESTED |
| 真實相簿級中斷恢復 | NOT_TESTED |
| 照片級續傳 | FUTURE_RESEARCH，非目前完成前置條件 |
| 已下載 fixture ImageIO | 正例 2/2，非 LINE 照片；另有破損圖拒絕測試 |
| 正式 AUTO／兩本交易／VERIFIED readback／release | NOT_TESTED |

10/24 summary 記載舊群組新增 19 本／1,555 張／19 次 Save All，ImageIO 通過；本輪只讀歷史紀錄，沒有重新下載或重驗這 1,555 張。它不是本輪成果，也不證明新群組已完成。

## 整理、資料保護及搬移

實際由 Luna 移出 63 項、53,983 節點、3,662,301,514 bytes（約 3.41 GiB 邏輯容量）：18 Swift cache 目錄、7 Python cache、11 Finder metadata、27 舊根目錄文書。採 rename，保留完整快照及另一份原件；永久刪除 0。

原工作樹 1,275 份受保護 artifact hashes、原有三份 dirty 與核心 image_decode／rev28ctl／rev28probe 均保持一致；root 另做獨立 baseline 比對，0 差異。活躍固定 runtime、照片、正式 state／grant／ledger／contract、原始 evidence 保留。部分舊 task 的 cache 路徑不再原地可重播，需從封存恢復；不假稱所有歷史工具仍在原位。

候選主分支另移出原有 14 篇舊文書，其餘 13 篇本就不存在。source 與 workflow 的現役依賴不因檔名年齡整包刪除。

見 [整理與搬移](../../docs/專案整理與搬移.md)、[Owner 刪除決策清單](../../docs/封存資料_建議刪除清單.md)、[63 項精確 allowlist](public/cleanup-allowlist.csv)。99%／95% 是有條件工程判斷，非統計保證；APFS clone 不保證刪副本能回收同等實體空間。

本輪未把專案搬到 dev。修正 driver 的硬編碼開發根；歷史 state／grant／runtime 仍保留原始路徑與 hashes，將來搬移不可全域搜尋取代，正式執行需重新核對綁定及有效授權。

## 獨立審查與主分支

乾淨候選 base 為 `master@61f55595a96c58a3ca62a73ade82c6a308f98be2`；既存產品來源為 `v43@b17960594a15dc365cb040175095c2c6fd9a87bb`。Git wire 與 GitHub ref API 已交叉確認 master；PR API 的舊 base.sha 不是當前 ref。

PR31 的 [真實外審](https://github.com/s9008129/Line_backup/pull/31#pullrequestreview-5611062176) 明確擋整支大範圍 merge；PR32 的 [真實外審](https://github.com/s9008129/Line_backup/pull/32#pullrequestreview-5615459643) 仍要求先修正與重審。GitHub review state 為 COMMENTED，本文不將其冒稱新版本批准。Luna 技術檢查、root 裁決、本地測試皆不是外部 APPROVE_IMPLEMENTATION。

PR32 唯一實作仍由既存分支與 all-refs bundle 保存；未經核准不混入本輪主入口、不丟棄來源。新候選尚無真實外部 Plan／Code Review 或 DeepSeek 獨立 E2E。Owner 於 2026-10-25 明確給予綁定 PR #36／原候選 `af99c14459202cb148a3eceda8faa0b6871bb3f2` 的 merge-only exception，允許合併主分支，但正式下載仍停用；此決策不構成外部批准或 E2E PASS，也不改變 PR31／PR32 既有審查狀態。決策原文與範圍見 [Owner merge-only decision](owner-merge-decision.md)。在本文件更新時，PR #36 的 docs-only 決策紀錄提交與正常合併仍待完成。

## 證據、雜湊與狀態

私有原始資料位於本 task 的 `private/`；個人絕對路徑、原始 LINE 畫面／照片／檔名、grant 與來源明細不公開。公開報告使用 repo 相對路徑；絕對位置在 private receipts 可由實際 workspace 解析，未捏造不存在的影像 hash。

- `private/preservation-baseline.json`：`a5cfe69b2c6ed4a6686dcc67330f324fc8479d9459ba858fd879a422c650f4ef`。
- `private/cleanup-20261025-active-root-prune/receipt.json`：`1b35a65d79eb80d724ab31ffc7516b7e0c1b29c32223ab40509460e9d52ae719`。
- `private/luna-implementation/daily-records-test-02.stderr`：`2565068995ac9372e526ddaded4be0e5d31c0818e84e0f7801ad6ae5cb000c8e`。
- `private/luna-implementation/merged-receipt.json`：`276232bb7ad3c9c89d0ed48ab6ba3c5de201972431c91de4a8d0e17275b67025`。
- `private/luna-implementation/skill-quick-validate-output.txt`：`787186175b423742c379ba80ac4682f6fcec7e96750a04945ef3f1b5688d6668`。
- `private/luna-implementation/candidate-final-daily-portability-receipt.json`：`14c5e692827149258d1174445f5262b839a4394f596f0234593802243a1d7e49`。
- [source／測試／receipt 索引](public/evidence-index.json) 固定可公開來源 hashes 與私有原始 log 的相對識別；失敗 log 保留，不覆蓋成成功。Node 22/22 的首輪工具輸出未存成 raw log，此限制保留於整合 receipt，不補造紀錄。

### 交付前補充證據

- 乾淨候選另行實際執行 `node --test tests/test_cua_adapter.mjs`：22 tests、22 pass、0 fail、exit 0。此次補測有保留原始 stdout（1,848 bytes，SHA-256 `d793f2c16d1bd7315cf398b43aa71773a331213226cdd54fe7897d9a8a83c46f`）、stderr（0 bytes，SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）及 exit code；路徑／hash 在 `public/evidence-index.json`。這是補做的新測試，沒有覆寫「先前 22/22 工具輸出未保存」的歷史限制。沒有 GUI 操作。
- Owner 51 張案例的最新 offline preflight 只保留私有相對識別與 hash：`private/luna-implementation/owner-case-preflight.json`（3,850 bytes，SHA-256 `a34918021cbc41158b0d457b918a3c21194892b7c6da3806da75825e9e4e8941`）及 `.md`（3,142 bytes，SHA-256 `221d730394d92dfda99115c2cc2590c75850a5f4e63c38ff668737e8c8008cac`）。結果為 volume 未掛載、目的地不存在、容量 UNKNOWN，UUID／觀察／foreground／review／grant 均 null，正式 request 未產生；沒有列出或讀取照片，也沒有猜補前景或授權。
- 本索引目前 38 項：14 項 public source/document hash 在候選逐一相符，另有 1 項公開 Owner 決策紀錄，23 項 private 記錄僅發布相對識別、大小、hash 及種類，沒有發布私有內容。報告本身不加入索引，避免 self-hash 循環。

```text
PRIMARY_OUTCOME_STATUS=PARTIAL_LOCAL_FIX_AND_ARCHIVE
IMPLEMENTATION_STATUS=LOCAL_CANDIDATE_COMPLETE
CORE_ACCEPTANCE_STATUS=REAL_LINE_NOT_TESTED
REQUIRED_VERIFICATION_STATUS=LOCAL_PASS_REAL_LINE_NOT_TESTED
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
```

後續仍須區分本機候選交付、Owner 主分支決策、外部審查、新群組 issuer 與實機前景／交易授權。任何一項未成立，都不能寫成正式 AUTO PASS。
