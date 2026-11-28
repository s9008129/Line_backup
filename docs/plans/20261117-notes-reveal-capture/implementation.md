# 記事本 reveal 觀察修復交付報告

修復已實作並通過計畫及程式碼審查。Agent 現在有可直接執行的範例，在一次 reveal 輸入後，於同次 CUA invocation 取得 after，避免輸入後另開 shell 或跨模型回合才觀察。真實 toolbar 的唯一成因及實機下載成效尚未確認。

## 修改與原因

本次只修改五個產品檔案：notes Skill 入口、B1 導覽規則、證據判定案例、證據範本與 `test_notes_input_helper.py`。

- B1 保持唯一決策本文；入口改為簡短摘要與連結，案例增加 C16／C17。
- reveal 前準備 input／after 目錄與唯一 ID。沿用現有 `persistSingleInput`，request 讀回後只送一次 click，接著直接取得同一 app 的 AX／截圖。
- capture 物件留在 closure，callback 原樣返回 input return，包含 typed `undefined`。之後分別保存 input raw 與同份 after，不重新 capture。
- input raw／diagnostic 保存失敗仍保留已取得的 after；本地 `fail_closed=true` 阻止後續輸入。after 自身完整不代表 input 完整、控制可見或可建立 intent。
- input error、capture error、保存失敗與未知來源時間分開記錄。兩個相依 API 不是 atomic，也沒有固定延遲上限。
- 新增八項直接執行文件程式的合成行為測試，涵蓋順序、原 return、兩類 error、同 bytes、request gate、raw 及 diagnostic 保存失敗。

沒有修改 core helper、`src/`、CLI、事件格式、六類狀態、completion、restart、相簿 Skill 或正式日常 Prompt。沒有 GUI 輸入、下載、真實帳本或照片修改；沒有新增控制器、viewer registry、API 或額度。

## 根因證據及限制

Tester 核對事故原件：C／B2 的 input helper 已完成後，另開 shell，之後才 capture；B1 的精確跨回合序列保持 `UNKNOWN`。mtime 只證明落檔先後及間隔，不能證明 OS click 到 screenshot 的精確延遲。歷史正向邊緣、hover 與 toolbar 壽命仍是未分離假設，未硬編碼為通用規則。

當次 CUA 文件支持同次 action 後取得 state，並明示觀察 API 有內部等待；未列 hover／move。未來 Agent 仍須讀當次工具文件，不能把這次能力視為所有環境保證。

每媒體最多兩次候選及同根因最多三次、連續兩次無新資訊即停，同時保留。此次開發沒有重置舊事故額度或授予新的實機嘗試。未解 input、UNKNOWN、活動下載與未完成命名交易仍按原規則保護。

## 實際驗證

環境為專案既有 macOS 工作樹、`feature/line-notes-media`，基礎 HEAD `2a98a60bee9fdf5f070f49484bb18866ab799f72`。以下命令的 stdout／stderr、argv、開始／結束 UTC 與 exit code 均留專案私有 task。

| 實際命令 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS，73 tests，exit 0，319.412 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | PASS，exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | R1：326 tests；R2：327 tests，均 exit 0；R2 44.775 秒 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_input_helper.py` | Worker2 focused：R1 27 tests；R2 28 tests，均 exit 0 |
| `git diff --check` | PASS，exit 0 |
| Skill Creator `quick_validate.py` | PASS；初次缺 PyYAML，隔離依賴後 exit 0 |

Skill validator 的隔離命令如下；只遮蔽安裝路徑，其餘參數與實際命令一致：

```sh
UV_CACHE_DIR="$TASK_PRIVATE_DIR/uv-cache" uv run --no-project --python /usr/bin/python3 --with PyYAML "$SKILL_CREATOR_DIR/scripts/quick_validate.py" .agents/skills/line-notes-agent-cua
```

`TASK_PRIVATE_DIR` 是已核對的專案私有 task 絕對路徑；`SKILL_CREATOR_DIR` 代表既有 Skill Creator 安裝目錄，原始 argv 留私有 task。沒有改系統 Python 或工具鏈。R2 只改 composition／測試與說明，重跑 notes 全套；沒有無故重跑未受影響的相簿回歸。測試輸出的 argparse error 屬合成錯誤案例，suite 最終為 `OK`，不是日常真實資料錯誤。

## 獨立審查

計畫由 Owner 授權的 Codex 備援 reviewer 接受；後續依 Owner 指示全部交新 Copilot reviewer。實作 R1 初判 PASS，Leader 提出原件遺失疑點後，同一 reviewer 更正為一項中度 `CHANGES_REQUESTED`。原 Worker2 修復後，R2 複審 PASS。完整界限與版本見 [review.md](review.md)。

最終受審的五檔 full diff SHA-256 為 `795d552ea402fadb657a937fec77943400736e853680e507721586396640a1a6`。審查接受不代表真實 LINE E2E。

## 狀態與下一步

| 狀態 | 結果 |
|---|---|
| PRIMARY_OUTCOME_STATUS | PASS（本次授權的最小修復） |
| IMPLEMENTATION_STATUS | PASS |
| CORE_ACCEPTANCE_STATUS | NOT_RUN（正式日常備份的實機結果） |
| REQUIRED_VERIFICATION_STATUS | PASS（本次離線回歸與靜態檢查） |
| INDEPENDENT_ACCEPTANCE_STATUS | PASS（僅計畫及上述版本實作） |
| TASK_CLOSURE_STATUS | PARTIAL（開發交付已備妥；實機確認未執行） |

真實 reveal／toolbar、chooser、下載、混合附件、跨 Session 及獨立實機驗收均為 `NOT_RUN`。後續由 Owner 沿用手冊既有正式記事本 Prompt 試用，Agent 再依當次畫面、歷史與有效前景決定下一步；不增加日常啟動步驟。

Git 交付限五個產品檔案與本任務計畫／報告；既存提報單、untracked、私人原件、帳本及照片均排除。只交付 `feature/line-notes-media` 與既有 Draft PR #51，不合併 master。實際 commit／push 及遠端精確 HEAD 收據由主 Session 完成後留在私有 task，最終回覆提供對應連結。
