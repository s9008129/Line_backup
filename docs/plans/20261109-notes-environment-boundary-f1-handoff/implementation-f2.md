# v3 F2 Implementer Report

## 請求、核准與範圍

Owner 要求依 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md` 與已核准 v3 計畫接續 F2：補齊新 intent、inventory、普通／restart 發布、candidate／activation 重讀、發布後 staging 收尾、跨 Session 整合及指定操作文件，並執行完整最小回歸。本輪另明示必須使用更多平行子代理加速獨立核對。

核准來源是 v3 `plan.md`、Planner `handoff.md` 與 F1 Handoff；F1 Simplicity PASS 只覆蓋 `d5ce67d075c46fee2781b0d944b8ac5439bbb3e1`，不是產品接受。F2 沒有擴張至真實 reattest、LINE／GUI、下載、真實帳本／媒體、merge master 或 force-push。原任務仍 `BLOCKED`，原因是第二支影片的真實接續尚未證明。

## 來源、版本與接手狀態

| 項目 | 身分 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，主 worktree |
| Branch | `feature/line-notes-media` |
| 起始 HEAD／遠端 | `56d7cfd25036c1c9e5783431eb91bf951fb1419d`；`origin/feature/line-notes-media` 同值 |
| 核准設計 | `bdde2a07d6de3195996589ca4ceac871cceca80a` 的 v3 plan／Planner handoff |
| F1 Simplicity Review | `afb0fdd14807f8c9d334fbb06be790e6f59e1c069e66e8581a12333775edc53f`，只覆蓋 F1 候選 |
| 起始工作區 | 七個 F2 產品／測試／reference 檔案及手冊 modified；沒有其他 untracked |

來源 SHA-256：

| 來源 | SHA-256 |
|---|---|
| `docs/plans/20261108-notes-volume-identity-reattest/plan.md` | `7743d6f5910713e8e65540a8b1b6758cdf60f32d21898763b34df62c0e6bd75e` |
| `docs/plans/20261108-notes-volume-identity-reattest/handoff.md` | `84c6de506a2f209fcdf62bbebfc84e9209ea10dd5dd7d49c673ba191ec61923e` |
| `docs/plans/20261109-notes-environment-boundary-f1-handoff/Handoff.md` | `57506ff6dabf206d3809837c6f8ed1ca3979fa71b47322a8efa9e8a31cf81c44` |

最終候選檔案 hashes（HEAD 仍為 `56d7cfd25036c1c9e5783431eb91bf951fb1419d`，本輪 diff 尚未提交）：

| 路徑 | SHA-256 |
|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | `1df078694894e7b929aad5f0ddc32082faeda959711983ce001dcb2f58d3f371` |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | `51853641d0032b242efe14a6a4f76c281aab4ad0ea5ba0db170dded7b2771024` |
| `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md` | `d24ba71b422c95f844b3d5509839d32ba9fcb4f3977d6e8ffbb1caf3451d8bc1` |
| `docs/LINE相簿備份_使用手冊.md` | `63b20ee41b149eabe051c50f275fd5e852fa385955b1eb3a3f39f7fa75fba9ca` |
| `src/line_backup_batch/notes.py` | `ffdcf2595865ca54014df39156b4a248de0fc6bf3dd2ae0d3318cf537ce14484` |
| `tests/test_notes_e2e_media.py` | `d5eac7dfc57c2777fefeb9022f3197bc694cf9df65af5d4a27f8d41bab88c219` |
| `tests/test_notes_records.py` | `c9cc39c4545815d3651c9cb298a9143252c158176b57e291941976d5fb568eff` |
| `tests/test_notes_restart.py` | `b25378671dd6dd6b523d3ae0336de0d55332f0cbf978211dd1173ca6e2077295` |

接手時既有的七個候選路徑如下；本輪另補入 `SKILL.md` 的單行主入口限定。本輪沒有清理、reset、checkout 或覆寫任何無關工作。私有命令輸出、TMPDIR、前後失敗證據與本報告以外的原始證據留在 `.local/line-backup/tasks/notes-v3-f2-implementation-20261109/`，沒有 stage。

```text
.agents/skills/line-notes-agent-cua/references/download-and-ledger.md
.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md
docs/LINE相簿備份_使用手冊.md
src/line_backup_batch/notes.py
tests/test_notes_e2e_media.py
tests/test_notes_records.py
tests/test_notes_restart.py
```

`SKILL.md` 是本輪最後補入的單行主入口限定。

## 實作內容

### 產品

`src/line_backup_batch/notes.py` 只擴充既有環境附屬項分類的呼叫點，沒有改 schema、CLI、公共交易介面、媒體驗證器或事件格式。合格環境項的定義仍是：canonical、非 symlink 媒體容器內、精確 `.DS_Store`、regular file、`nlink=1`、未被帳本／manifest／證據／交易引用或保留，且受管理名稱與目標碰撞優先。

本輪套用到七個 F2 gate：

1. 新 intent 的 staging 空內容檢查。
2. recovery intent 的 staging 空內容檢查。
3. 普通發布候選目錄的內容檢查。
4. 普通發布目標目錄的內容檢查，保留原本 subset 語意。
5. 發布後 staging 收尾：只剩合格環境項時保留目錄與 bytes；真正空白才 `rmdir`，未知內容仍拒絕。
6. restart version directory 的內容檢查。
7. inventory 三次採樣：環境項不讀取、不計數、不進 manifest；未知 dotfile、symlink、directory、額外影片仍拒絕。

`_post_directory_for_publish` 的 reserved names 由既有事件推導；`reserved_names=set()` 在 staging／inventory 表示沒有保留名稱，不是 wildcard。環境 bytes 不進 witness、manifest 或事件。

### 測試

- `tests/test_notes_records.py`：新 intent 與 recovery intent 的環境項正例、未知檔／其他 dotfile／directory／symlink／hardlink／額外影片負例；inventory 與普通發布的環境變化；發布後 staging 保留；完成目錄與跨 Session 讀回。
- `tests/test_notes_restart.py`：restart intent、version directory、candidate／activation 的環境項正負例；未知 file／directory fail closed；既有 `restart-copy-plan` 的單筆既有語意保留。
- `tests/test_notes_e2e_media.py`：兩照片一影片走 production ImageIO／成對 Homebrew `ffmpeg`／`ffprobe`；post directory 與影片 staging 放環境項，manifest 只含媒體；截斷影片仍由 production verifier 拒絕並保留環境 bytes。
- `tests/test_notes_regressions.py`：既有單次限額、replay、stale tip、鎖、scope／generation、fresh scan、防重送與退出碼回歸纳入最終 `test_notes*.py` 全套。

### 操作文件

- `references/download-and-ledger.md`：新增合格環境附屬項定義，並限定 candidate、resume、完成目錄及 `LOCAL_CHANGED` 的「額外檔」。
- `references/verification-and-recovery.md`：同步限定額外檔與 `LOCAL_CHANGED` 語意。
- `SKILL.md`：只在主入口的完成／可用性句，把「額外檔」限定為「非屬合格環境附屬項的額外檔」。
- `docs/LINE相簿備份_使用手冊.md`：只修記事本衝突段落；沒有增加正式 Prompt 步驟，也沒有改相簿段落。

文件範圍以核准 `plan.md` 的完整清單及 F1 Handoff「完整計畫為準」處理；Planner handoff 的較窄摘要只用於核對，不取代 plan 的完整授權。

## 驗證與結果實錄

最終有效回歸在 repo 根執行，使用專案控制但不在 repo 內的隔離 synthetic `TMPDIR`：`/tmp/line-backup-f2-final.6oXray`。證據目錄：

`.local/line-backup/tasks/notes-v3-f2-implementation-20261109/final-regression-20261109-201152/`

| 命令 | Exit | Tests | 結果 |
|---|---:|---:|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 | OK，321.228s |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | N/A | 輸出使用說明 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 216 | OK，29.424s；無 skipped |

原始 argv、cwd、environment、stdout／stderr 見同目錄 `summary.txt`、`environment.txt` 與 `logs/`。`notes_help.stderr` 為空；`notes_all` 內含 `test_notes_e2e_media.py`，未顯示 skip。`git diff --check` 在最終文件補入前 exit 0；文件補入後再次以同一命令核對。

前一次在 repo 內設定 `TMPDIR` 的完整回歸 exit 1：`daily` 的 external-root 測試與 notes 的 private-output 測試把測試暫存區視為專案內路徑，因此沒有觸發預期拒絕。該次證據保留在 `final-regression-20261109-200538/`，判定為測試環境設定失效，不作為候選 PASS；候選產品未因此修改。改用 repo 外的隔離 TMPDIR 後三條命令全數通過。

## V1–V9 對映

| 項目 | 本輪證據與狀態 |
|---|---|
| V1 重新見證／可用性 | F1 reattest 合成覆蓋仍保留；F2 完成目錄、staging、list、witness 前後與環境 bytes 測試通過。`PASS_SYNTHETIC`，真實 reattest 仍 `NOT_RUN`。 |
| V2 跨 Session | 既有完成後新 Session 跳過、UNKNOWN 禁重送及 F2 新 intent／completion 讀回測試通過；不是 LINE 實機跨 Session。`PASS_SYNTHETIC`。 |
| V3 採樣到發布 | 普通發布、restart candidate／activation、inventory 三次採樣與影片環境變化測試通過；真影片 production verifier 的 manifest 只含媒體。`PASS_SYNTHETIC`。 |
| V4 收尾與重開 | 發布後只剩環境項的 staging 保留 bytes、真空目錄才 rmdir、正常 completion／讀回／resume 測試通過；未刪檔或新增清理事件。`PASS_SYNTHETIC`。 |
| V5 安全負例 | 缺檔、漂移、未知 staging、額外影片、未知檔／其他 dotfile、同名碰撞、異常同名環境項、symlink／hardlink、受管理名稱優先等負例通過。`PASS_SYNTHETIC`。 |
| V6 協議不變 | `test_notes_regressions.py` 53 tests 納入最終 216；單次限額、replay、stale tip、鎖、scope／generation、fresh scan、防重送與退出碼回歸通過。`PASS_SYNTHETIC`。 |
| V7 真解碼合成媒體 | `test_notes_e2e_media.py` 2 tests，production ImageIO＋成對 Homebrew ffmpeg／ffprobe；截斷影片拒絕，無 skip。`PASS_SYNTHETIC`。 |
| V8 文件與最小回歸 | 三條最小回歸 PASS；兩份 references、SKILL 主入口與手冊記事本衝突段落已限定，沒有新增 Owner 日常步驟。`PASS_DOCUMENT_AND_REGRESSION`。 |
| V9 真實日常／獨立接受 | `NOT_RUN`。Owner 尚未以手冊記事本正式 Prompt＋有效前景完成真實接續；獨立接受亦未執行。 |

## 已知、推論、未知與停止

**事實：** 起始與最終產品候選的 branch／HEAD 一致；七個產品／測試／文件候選均在授權路徑；三條最終回歸 exit 0；`git diff --check` 無輸出；沒有讀寫真實帳本、active hint、照片、影片或 LINE。

**推論：** 同一環境分類已沿 F2 gate 貫徹，合成資料可證明環境項不進 manifest／witness，且不讓 staging 收尾留下假 pending；這不證明真實 LINE 的來源、下載或跨 Session 行為。

**未知：** device 漂移原因、外部 writer、第二支影片是否晚到、原 OPEN_BATCH 當前適用性、修正後真實接續、跨模型重用、服務端原始位元一致性與 GUI exactly-once 均未消除。真實 V9 與獨立接受仍須 Owner 另啟。

**既有協議觀察：** 唯讀子代理指出 restart verify 會在 version directory 檢查前追加既有 `restart-copy-plan`，以及普通發布不會在 completion 前做第二次目標目錄全集重讀。diff 核對顯示兩者都是本輪以前已有的交易／有限觀測行為；本輪只新增環境項過濾，沒有擴張或改寫交易協議。若 Owner 要求改變這兩個既有行為，需另案決定，不應在 F2 默默修改。

## 停止條件與下一步

F2 到此停止。下一步由 Owner 核對本報告與精確 commit／diff，決定是否需要針對 F2 候選另行安排 implementation Simplicity 或直接進入 V9 真實日常；本 Session 不自行開始 V9、GUI、下載、merge master、force-push 或獨立接受。若真實來源／狀態不允許接續、前景中斷或出現未明派送，保留證據停止；exit 70 不是重送、改帳或換入口的理由。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: F2_IMPLEMENTED_AND_FULL_MINIMAL_REGRESSION_PASS
IMPLEMENTATION_STATUS: PASS_F2_WITHIN_APPROVED_PRODUCT_TEST_DOCUMENT_SCOPE
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_SECOND_VIDEO_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_FULL_MINIMAL_REGRESSION; V9_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN; SIMPLICITY_PASS_IS_NOT_PRODUCT_ACCEPTANCE
TASK_CLOSURE_STATUS: NOT_DONE; REAL_LINE_V9_AND_INDEPENDENT_ACCEPTANCE_PENDING
```
