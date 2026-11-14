# 記事本 S3b S3B-SIM-01 修正報告

## 角色、授權與精確版本

本輪以 Implementer 身分處理 Owner 指定的 S3B-SIM-01 修正。Owner 提供
`04_implement_prompt.md`、S3b 實作簡潔性審查的 `REVISION_REQUIRED` 結論與最小
修正方向，並明示完成後執行 add、commit、push。這是同一核定 S3 計畫內的文件
修正，不變更目標、架構、公共介面、資料語意或驗收標準，也不啟動另一個正式角色。

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`
- Branch：`feature/line-notes-media`
- 起始 HEAD：`2e13e857dd02884049b8a385b5cdc3dd3e52682f`
- 受審產品／文件候選：`b2cd3e103a187c0cf8232b93af2f458a3e468386`
- 起始 index、tracked 與非忽略 untracked：乾淨；其他 worktree 未變更
- 核定 plan：`75d4053332aa518a3e91e67b03dbd611e5efaf72`
  - SHA-256：`d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`
- 現行 handoff：`1cdb88bdff8a201173d2712ac827de6896181603`
  - SHA-256：`63fd3e530eee29688c14ede8f887dfc1a1b8b43ee1a2f85d3a66f208cf5c1ed8`
  - 該文件仍以 S3a 為主要交接；本輪 S3B-SIM-01 的修正授權來自 Owner 當次訊息與審查報告。
- S3b 實作簡潔性審查：`docs/plans/20261102-notes-fieldtest-review/s3b/simplicity-implementation-review.md`
  - SHA-256：`6a09b2e39e45ba48845f4b7952d9d8afb2f4e382daafc240337a112184b72f85`
  - 只涵蓋受審候選 `b2cd3e1`；不是修正版的複核或接受。
- 原 S3b 實作報告：`docs/plans/20261102-notes-fieldtest-review/implementation-s3b.md`
  - SHA-256：`618054edf00a6e4bea6520f5eb12fd2cfa225200e65429c90c15530193884686`
  - 本輪保留原件，不把修正追加進該報告而改寫已受審候選。

## 修正內容與根因

唯一行為文字修正位於
`.agents/skills/line-notes-agent-cua/references/download-and-ledger.md:224`。
原句要求 PathTextField、panel current directory／where 與 intent destination
一致指向「同一個尚不存在的新空白子目錄」；本輪移除 chooser 階段的「尚不存在」
條件，改為一致指向「該 intent 已建立、讀回且仍空白的原目的地」。

保留的保護不變：

- PathTextField、panel current directory／where 與 intent destination 三層分開
  觀察且必須一致。
- 來源貼文、viewer、process 與 attempt 必須可唯一歸屬。
- chooser 最終確認仍至多一次；出處不明、任一 `UNKNOWN`／不符或結果未知時停止。
- 不新增子目錄、不改建目錄、不改 CLI／schema／資料、不覆寫、不重送，也不降低
  `UNKNOWN` 不重送或其他安全 gate。

根因有既有程式生命週期直接支持：`notes.py:2697-2725` 的 `intent` 先以
`_new_unique_directory()` 建立空白目的地，再將同一 canonical path 與
device／inode 寫入 intent；`_new_unique_directory()` 在 `:404-413` 執行
`os.mkdir()`，回傳的目錄必然已存在。`_validate_staging()` 在 `:3256-3267`
也要求該目錄存在、不是 symlink，且 device／inode 與 intent 一致。因此舊句
要求 chooser 同時看到同一個 intent 路徑與「尚不存在」狀態，兩者不能同時成立。

`evidence-template.md:50` 只要求三層一致的新空白目的地，
`evidence-decision-cases.md:88,91` 也明示目的地是 intent 建立的新空白目錄；
兩者沒有「尚不存在」要求，本輪無須改寫。新增本報告是角色交付紀錄，不是產品
行為變更。

## 變更路徑

| 路徑 | 內容 | 修正後 SHA-256 |
|---|---|---|
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | chooser 第 5 步移除「尚不存在」，明確沿用 intent 原目的地；其餘三層核對、歸屬與單次確認保留 | `216e21b435e5aefd1f3aea180498602e9d4612b0130a158084afe6389ec190e2` |
| `docs/plans/20261102-notes-fieldtest-review/implementation-s3b-sim01-revision.md` | 本修正報告；不變更舊 implementation、審查或完成事實 | 由交付後私有檢查紀錄，不在檔案內預填自身 hash |

沒有修改 `src/`、`tests/`、CLI、schema、事件、identity、鎖 allowlist、使用手冊、
相簿 Skill／程式、原 plan／handoff、原 S3b 報告或審查報告。

## 實際驗證與結果

環境：macOS 27.0.1（26A434）、arm64、`/usr/bin/python3` 3.9.6、
Git 2.52.0、cwd `/Users/hsiaojohnny/dev/Line_backup`。私有證據保存在
`.local/line-backup/tasks/20261102-notes-s3b-sim01-revision/`，不加入 Git。

| 檢查 | 實際命令 | 結果 |
|---|---|---|
| 契約文字 | `sed -n '224p' …/download-and-ledger.md` 與 `rg` 核對新句、三層欄位、來源歸屬及單次確認 | 舊「尚不存在」在該步無匹配；必要 anchors 全部存在 |
| 來源生命週期 | 唯讀核對 `notes.py:404-413,2697-2725,3256-3267` | `intent` 建立、保存並驗證已存在的 canonical 空白目錄；與舊句互斥，支持本修正 |
| 文件／報告契約 | `check_revision.py` | exit 0；29／29 PASS，涵蓋舊字串移除、必要契約、來源、報告與變更白名單；結果見私有 `checks/revision-checks.json` |
| whitespace | `git diff --check` | exit 0；無 whitespace 錯誤 |
| 保護路徑 | `git diff --exit-code HEAD -- src tests …` | 除指定文件外無 tracked 差異；實際命令與輸出保存在私有 checks |
| staged 交付 | 逐檔 `git add`、`git diff --cached --check`、名稱白名單與 `git show -s --format=%B` | 交付前逐項讀回；不把 stage／commit 當作驗收 |

本輪沒有重跑 daily／notes 產品測試、CLI help、媒體解碼或 GUI。原因是修正只改
一份操作文件，`src/` 與 `tests/` 相對起始 HEAD 無差異；既有 73／136 項與
help exit 0 的結果仍只綁定受審候選 `b2cd3e1`，不自動升格為修正版 PASS。
本輪亦未建立 intent、未接觸真實帳本／照片、未操作 LINE 或 chooser。

## 事實、推論、未知與停止點

**事實：**舊句與 intent 已建立目錄的契約互斥；本輪只移除該 chooser 條件並明示
沿用原目的地。受保護產品程式、測試與其他既有文件未變。

**推論：**此修正消除文件中的流程阻斷，不應改變 notes 下載、驗證或 ledger 行為；
仍需由適用複核確認文字對照符合審查期待。

**未知／NOT_RUN：**真實 chooser／PathTextField 的當次可讀範圍、原始 CUA
envelope、焦點與幾何、A0、G0、D1、D2、G1、G2、真實 GUI／popup／spinner／
toast、影片／混合附件、跨 Session、產品回歸與獨立 Acceptance／E2E 均未於本輪
執行；`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 不變。

本修正交付後停止，不自行啟動 S3b 修正版的 Simplicity Review、Acceptance、外部
gate、GUI 或結案。下一步由 Owner 決定本修正版適用的複核與後續角色。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: S3B_SIM01_REVISION_IMPLEMENTED
IMPLEMENTATION_STATUS: S3B_DOCUMENTATION_REVISION_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: LOCAL_DOCUMENT_AND_SOURCE_CHECKS_PASSED; PRODUCT_AND_GUI_TESTS_NOT_RUN_THIS_ROLE
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_APPLICABLE_REVIEW_AND_GATES
```
