# 驗收缺陷修正 01：根因、邊界與實作證據

## 交辦及候選

Owner 提供 FIX_REQUIRED 後明示「深度分析問題的根因，並徹底修復」，作為新的有界實作交辦。本輪不是原 Reviewer 自行修復，也不啟動獨立重驗或宣稱新候選已通過 acceptance。

- 起始 HEAD：`5873db760fcbe561707c77f2b9049e447bfaf5fe`
- repository：`/Users/hsiaojohnny/dev/Line_backup`
- branch：`fix/save-all-gate-20261030`
- 來源報告：`acceptance.md`（Owner 新增、仍未追蹤），SHA-256 `4d16be0b9d83ad2e4594bd32f056245adee06e4eb049136d0ccc1007aa09e2bf` 已核對相符。
- 原另一未追蹤 `docs/plans/20261030-save-all-gate/acceptance.md` SHA-256 `672ddf5e1f414d077baadd7cfd0aa1fda1082fe03f46b2aab32dfcd19a9ab37c`。兩份均保留、不改寫、不 stage；前者作為唯讀交辦來源，後者不讀內容。

## 第一性原理與根因

完成宣稱必須來自可對帳的事實，而不是操作人的身分。「誰備份」是來源；「證據是否足夠、是否有未解交易」才決定狀態。把人工備份與六類狀態並列卻未定義映射，是 F-01 的根因。解法是使用既有證據門檻歸類，不新增第七類、不默認人工聲明等於完成或排除。

是否能跳過，取決於造成保護的原因及是否仍有活動交易，而不只看 PROTECTED_HISTORY 標籤。F-02 的根因是精簡 Prompt 時刪掉了決定行為的必要限定；上輪只修 reference、未同步唯一 Owner 入口，局部正確並未形成端到端一致的契約。這是前次實作遺漏，不是模型等級或 Owner 授權不夠。

F-03 屬交接阻塞：前景是當下環境，不能代替實際下載同意；標題又不是列表身分。不能以放寬 gate 修成通過。另一方面，已接受的預設 root 及無新增排除是有效輸入，不應把未另填非預設值當成缺授權；實際任務的語意優先，不要求逐字口令。

F-04／F-06 是多份入口文件更新不同步；F-05 是把 OS 能力、Owner 同意與觀察資料範圍混在一起。修正須讓使用者知道桌面截圖可能暫含其他可見內容，同時限縮持久保存、OCR 及用途。

## 本輪有界方案與實作

Owner 本次要求處理報告中的問題，納入同一文件切片的 README、觀察同意及歷史範本註記；不增加下載方式、資料格式或簽章／控制器，不更改既有完成與 UNKNOWN 事實。

| Finding | 實作處置 | 未改變的證據邊界 |
|---|---|---|
| F-01 | inventory 為六類人工來源歸類的單一規格：工具已有完整 completion／正規 history 證據才 COMPLETED；僅聲明／證據不足為 PROTECTED_HISTORY；既有 UNKNOWN／pending 優先。AGENTS、Skill、daily reference 與 Prompt 引用同規則 | 不把舊保護項升格、不捏造證據、不用人工聲明當排除、不寫真實記錄 |
| F-02 | Owner Prompt 與各入口限「個別舊證據不足的歷史」，明文排除活動下載、UNKNOWN／未解派送與 pending 命名交易 | 不改現有全批交易阻塞 |
| F-03 | 手冊新增實機驗收交接檢查，使用同一正式範本；接受已明示預設，不要求特定口令；名稱異同不足以認領或重建任務 | 真實 E2E 仍須實際任務及有效前景，本輪 NOT_RUN |
| F-04 | README 預設路徑改 backup/，記憶入口以已核對 active-task 的實際 root 為準，例子限預設 root | 不遷移或改寫任何入口／資料 |
| F-05 | Prompt 明示 AX、LINE／popup 截圖、本機離線 OCR 及必要桌面觀察；reference 要求當次同意＋平台允許，優先指定視窗／區域，僅留任務相關區域，不主動辨識其他應用或上傳外部服務 | 不授予全桌面無差別研究；本輪沒有擷取任何畫面 |
| F-06 | 原 handoff 頂部追加歷史／已取代註記及手冊連結 | 下文歷史原文不重寫 |

## 嘗試與本機驗證

本輪是收到正式驗收後第一個有新證據的修正切片。前輪 12 例文字推導漏掉人工來源映射與 Prompt 局部過寬；不把它作本輪通過證據，也不重置同根因的既有修正歷史。新增檢查聚焦這兩個漏項，而非再跑相同問題索取自評 PASS。

同角色助手只讀產品文件，未讀 acceptance 或本實作報告，對 10 個情境推導：人工無 manifest、正規 history 完整、人工聲明＋UNKNOWN、pending 保護、普通舊歷史保護、root 空值／[]、僅前景驗收、桌面含其他視窗、平台拒絕、名稱不同。回答均符合既定邊界；助手指出三處措辭，實作者已就地補足「舊證據不足／當次同意」，並把「停止查證」改為「停止派送並唯讀查證」。這是實作自查，沒有授予獨立 PASS；這些小修後未重跑助手。

本機檢查命令及退出碼、結果見下方完成紀錄。原始輸出與腳本在 `.local/line-backup/tasks/20261031-skill-precision-fix01/`。只使用 synthetic fixture；不讀真實相簿、active-task 或 backup-records，不操作 LINE。

## 後續交接

保留原 acceptance 的 FIX_REQUIRED 與所有已證實結果，不改成 PASS。新候選由 Owner 另開 independent acceptance，使用 [交接提示詞](fix-01-acceptance-prompt.md)。若發現需要改動資料／程式或取消安全門檻，停止並交回 Owner；不自動啟動修復／重測。

## 完成本機檢查（實作自驗）

cwd 均為本專案；私有目錄簡寫為 `.local/line-backup/tasks/20261031-skill-precision-fix01/`。

| 實際檢查命令 | 退出碼／結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0；73 tests / 318.059s，OK；daily-tests.log |
| `.local/line-backup/tasks/20261031-skill-precision-acceptance/venv-quick-validate-20261031/bin/python /Users/hsiaojohnny/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/line-album-agent-cua` | exit 0，Skill is valid!；沿用前次隔離環境，未安裝新套件；quick-validate.log |
| `python3 .local/line-backup/tasks/20261031-skill-precision-fix01/check_docs.py` | exit 0；18 份 Markdown、59 個本地連結／錨點有效；frontmatter 與原基線一致；doc-checks.log |
| `git diff --check`、`git diff --cached --check` | exit 0，最終提交前核對 |
| `git diff --exit-code -- src tests` | exit 0，沒有 source／test 差異 |
| `shasum -a 256` 兩份未追蹤 acceptance | 前後與本報告起始記錄一致，不 stage |

回歸使用原測試的 macOS ImageIO synthetic fixture 與既有相符 Swift SDK，沒有變更工具鏈。73 tests 不能證明真實 GUI 或跨 Session 恢復。

以下 hashes 綁定本輪私有檢查證據：

- `daily-tests.log`：`f3f388a42ad41f912296d0e877dc775ac2ccc7b9c4785394c9cd126a6fc5a7ce`
- `quick-validate.log`：`db349825903d66adffea3ecf1bd8e1803043e8a71cf1a051235dabc5371f5bb0`
- `doc-checks.log`：`f8801f7caadf22435ec3e82bfd52f0776d4c12668d249366b8499802acedbfda`
- `check_docs.py`：`a5c04d5e8891eef119739b7888ecef01055bd9d249bb1c9f9e793c22bcfe8b15`
- `behavior-results.md`：`8fbfa914d86fae59e605889a936c4c77d9e7c76b4fefdc00c0ef4e6bb1ed7fb2`

```text
PRIMARY_OUTCOME_STATUS: ACCEPTANCE_DOCUMENT_FINDINGS_ADDRESSED_IN_NEW_CANDIDATE
IMPLEMENTATION_STATUS: BOUNDED_DOCUMENT_FIX_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: NOT_RUN_FOR_NEW_CANDIDATE
REQUIRED_VERIFICATION_STATUS: REGRESSION_73_PASS; SKILL_VALIDATOR_PASS; DOC_CHECKS_PASS; REAL_GUI_E2E_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN_FOR_NEW_CANDIDATE
TASK_CLOSURE_STATUS: PENDING_OWNER_HANDOFF_TO_INDEPENDENT_ACCEPTANCE
```
