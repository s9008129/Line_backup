# Notes 全問題重規劃：S2 Implementer 報告

## 本角色結論

- 角色／階段：S2 Implementer，只執行核定 replan 的 A2、B2、C、D 與相應 notes CLI／Skill 更新。
- 使用者目標／核定版本：依 [replan.md](replan.md)、[plan.md](plan.md) 與現行 `handoff.md`。S1 的 Simplicity Review PASS 只適用提交 `423b00e`；本報告是後續 S2 候選，不沿用該 PASS 當自身審查。
- Repo／worktree：`Line_backup` 核心目錄；分支 `feature/line-notes-media`。
- 起始本機與遠端 HEAD：`31bb7326ada11fd3e7a7bd4a4a162fd1e44d4b44`。
- 起始工作樹已包含同一 S2 的未提交草稿；本角色保留並核對全部內容，沒有 `reset`、`clean`、覆寫無關工作或建立替代 worktree。最終候選另新增本報告。
- 候選身分：本報告與下列產品／測試／文件位於同一交付 commit；commit 不能在自身內容預填自己的 SHA，交付後以 `git rev-parse HEAD` 與遠端 ref 讀回。

## S2 變更與需求映射

| 路徑 | 行為 | S2 對應 |
|---|---|---|
| `src/line_backup_batch/notes.py` | 新增唯讀 `evidence-audit`、page `evidence-correct`、attempt 前 `media-kind-correct`、`STOPPED` 後 `source-unavailable`；`intent` 升為 `line-notes-intent/v2` 並凍結 `effective_kind` 與 correction chain；summary／intent 共用細盤 coverage gate；新 scan 前阻擋 pending naming、未決／待驗 attempt 與 coverage 缺口；resume 對 scan binding 不符回 `SCAN_BINDING_REVIEW_REQUIRED`。 | A2、B2、C、D |
| `src/line_backup_batch/notes_evidence.py` | 新增只供 audit 使用的逐引用稽核；沿用嚴格 bundle 解析與父子 digest 核對，個別 child drift 記入 row，不讓第一個錯誤掩蓋其他引用。 | A2 |
| `tests/test_notes_regressions.py` | 覆蓋 audit 外層／子資產 drift、page correction 精確 scope／chain、kind 更正保留 19 項 key／順序、intent-v2／偽造 v1 拒絕、來源到期、coverage／scan／resume gate 與舊相容案例。 | T1、T3、T4、T5 |
| `tests/test_notes_evidence.py` | 補充 v2 稽核分類、legacy opaque 與完整性路徑。 | T1 |
| `tests/test_notes_locks.py` | 將 `evidence-audit` 納入真正 records lock 的唯讀 allowlist 實測。 | T6 |
| `.agents/skills/line-notes-agent-cua/SKILL.md` 與三份 references | 更新 S2 CLI、audit 失敗投影、page／kind correction 邊界、`SOURCE_EXPIRED`、coverage／scan 阻擋與 v2 evidence 操作契約。 | S2 操作面 |
| `docs/LINE相簿備份_使用手冊.md` | 只更新記事本入口、新命令與證據／到期／scan 規則，保留唯一 Owner 啟動範本與相簿段落。 | S2 操作面 |
| `docs/plans/20261101-notes-all-issues-replan/implementation-s2.md` | 本報告，不覆寫 S1 的 `implementation.md`。 | 交付 |

關鍵行為：

- `evidence-audit` 在 event chain／結構性引用不可信時直接拒絕；可解析但 evidence／child 不完整時 exit 4、`business_projection_omitted=true`，不產出可信業務 summary。
- `evidence-correct` 只接受精確 page sequence／SHA-256 與原 evidence SHA-256；replacement 的 v2 scan context 綁 target page 當時 scan，不改 page 成員、順序、頂底或 scan 覆蓋。已有 correction 必須顯式接續前一筆。
- `media-kind-correct` 只允許目前 scan 可唯一辨識、尚無任何 attempt／verification／completion／exclusion／protection 的已盤點媒體；保留 media key、貼文、source order 與數量。新 intent 以 v2 凍結 effective kind，舊合法 v1 仍可讀。
- `source-unavailable` 只接受同項最新且已 `STOPPED` 的 attempt；summary 保留 `PREVIOUSLY_INCOMPLETE` 並加 `source_availability=EXPIRED`，loader 與 intent 均拒絕其後的新下載／恢復，不自動計入完成或排除。
- `start_scan` 在新事件前檢查 pending naming、未決 attempt、待驗結果與上一 scan coverage；summary 與 intent 使用同一細盤 coverage 判定。binding 不符時交人工審查，不自動改綁定或新建 scan 掩蓋。

受保護檔案未修改：`src/line_backup_batch/media_verify.py` SHA-256 仍為 `7c8051d1699449434dbaa41682a5a50f949858d593ee39cd2a1f38a1e1c6dd99`。`daily.py`、Swift decoder、OCR、相簿 Skill／測試、AGENTS、全域政策與真實備份資料均不在本差異內。

## 實際檢查與結果

環境：macOS；工作目錄 `/Users/hsiaojohnny/dev/Line_backup`；`/usr/bin/python3` 為 Python 3.9.6。私有輸出保存在 `.local/line-backup/tasks/20261102-notes-s2-implementation/`，不進 Git。

| 檢查 | 實際命令 | Exit | 結果與證據 |
|---|---|---:|---|
| daily 回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | `Ran 73 tests in 319.551s`、`OK`；`final-daily-records-r2.txt` |
| notes CLI | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 成功列出全部新命令與 0／2／4／70 契約；`final-notes-help.txt` |
| notes 全回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | `Ran 128 tests in 12.363s`、`OK`；`final-notes-tests.txt` |
| whitespace／patch | `git diff --check` | 0 | 無輸出；`final-git-diff-check.txt` |

執行註記：daily 第一次命令本體同樣顯示 `Ran 73 tests ... OK`，但外層 zsh wrapper 誤用唯讀變數 `status` 而回 1；改用 `rc` 重跑取得上述 exit 0。此 wrapper 錯誤不是產品測試失敗，也沒有修改產品後重跑。

實際測試涵蓋 A2 audit／page correction、B2 kind correction／intent-v2、C source expiry、D coverage／scan gate 及 S1 回歸；但全部使用合成隔離資料。

## 事實、推論與未知

事實：

- 上述四個命令在最終產品／測試內容上均 exit 0；notes 全體測試同時涵蓋 evidence、locks、regressions 與 capture。
- `git diff --check` 無輸出；工作樹的 tracked 差異只在核定的 notes 產品、測試、Skill／手冊與本報告。
- S2 沒有修改 `media_verify.py`、daily、Swift decoder、OCR、相簿 Skill 或真實帳本／照片。

推論：

- 合成測試提高新增事件、拒絕條件、投影與 scan gate 的一致性信心，但不證明真實 LINE 畫面、下載結果或服務端檔案。

未知／限制：

- 沒有真實 notes ledger、原始 media、GUI 前景、D1 舊 attempt 結果或 D2 更正授權可供本角色核對。
- S1 PASS 只對 `423b00e`；本 S2 尚未取得獨立 implementation review／Acceptance。

## 未執行項

以下全部維持 `NOT_RUN`，沒有以單元測試冒充：

- S3 剩餘操作契約、B1 的實機種類判定能力、完整 R1–R10 整合報告與所有 Skill／手冊最終回歸。
- G0、D1、D2、G1／G2、真實帳本／媒體預覽與應用、GUI、chooser／popup、混合附件、影片下載、跨 Session 恢復及完整列表對帳。
- S2 的獨立實作簡潔性審查、本機相容 Acceptance、獨立 Acceptance 與 Issue 關閉。
- merge master、force-push、部署或任何真實資料副作用。

## 停止條件與人工交接

本角色在交付 S2 候選後停止。建議 Owner 以另一個正式主 Session 讀取本報告、精確 commit 與私有證據，先決定是否啟動 S2 實作審查或後續 S3；不得由本 Implementer 自行簽發 Acceptable／Acceptance、開始真實 E2E、merge master 或關閉 Issue。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: S2_IMPLEMENTATION_CANDIDATE_READY
IMPLEMENTATION_STATUS: S2_IMPLEMENTED_LOCAL_CHECKS_PASSED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: REAL_E2E_AND_INDEPENDENT_ACCEPTANCE_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

這些狀態彼此分離；S2 候選完成不表示全目標、真實備份或正式驗收已 DONE。
