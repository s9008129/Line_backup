# v3 F1 Implementer Report

## 請求、核准與範圍

Owner 要求依 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md` 與本目錄 `Handoff.md` 執行已核准 v3 計畫的首個可驗證切片 F1，並明示本輪必須平行使用更多 subagent 加速。核准範圍只含：

- reattest 的 staging、completion、list 名稱集合與前後比較。
- active／completion 可用性。
- V1、V2、V5 在 F1 可達範圍的合成正負例。
- 產品只改 `src/line_backup_batch/notes.py`；測試只改三份指定檔案；另交付本報告。

F1 不含 F2、新 intent／inventory／普通與 restart 發布／收尾、真實 reattest、LINE／GUI、下載、真實帳本／媒體、完整 V3–V9、implementation Simplicity 或獨立接受。本輪沒有合併 master、force-push、清理或改寫舊歷史。

## 來源與版本

| 項目 | 身分 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，主 worktree |
| Branch | `feature/line-notes-media` |
| 起始 HEAD／遠端 | `0c348313b6c820f099b221cd18fb0ad17a8b2c9b`；`origin/feature/line-notes-media` 相同 |
| 核准設計 | `bdde2a07d6de3195996589ca4ceac871cceca80a` 的 v3 plan／Planner handoff |
| F1 交接 | `0c34831` 的 `docs/plans/20261109-notes-environment-boundary-f1-handoff/Handoff.md` |

核准來源 SHA-256：

| 來源 | SHA-256 |
|---|---|
| `plan.md` | `7743d6f5910713e8e65540a8b1b6758cdf60f32d21898763b34df62c0e6bd75e` |
| Planner `handoff.md` | `84c6de506a2f209fcdf62bbebfc84e9209ea10dd5dd7d49c673ba191ec61923e` |
| `planner-boundary-revision-report.md` | `bfcd78ba0cdac6392c59a9f1f1b6c6ea257718228055d06d0e000147ebec3ea2` |
| v3 Simplicity Plan Review | `e9b8da858e4aeb2ad7abc1de2a5e2a593633f9f488d3784469487aa6302f7698` |
| v3 CRITICAL Plan Review | `f41f873333754fbb5ce1809af5fdfcad15069d2103aeb44d880700d8c7ed407e` |
| F1 `Handoff.md` | `57506ff6dabf206d3809837c6f8ed1ca3979fa71b47322a8efa9e8a31cf81c44` |
| baseline `notes.py` | `0e542d73024f8f1b78238dcb9b331d890c89223281c5543f8acf45b7135aed7b` |

上述來源核對只證明版本與內容一致，不是產品 PASS 或獨立接受。

## 接手狀態與保留

本輪接手時，`HEAD` 與遠端均為 `0c34831`；工作區只有下列四個 F1 候選路徑為 modified，未見其他 dirty 或 untracked：

- `src/line_backup_batch/notes.py`
- `tests/test_notes_reattest.py`
- `tests/test_notes_records.py`
- `tests/test_notes_restart.py`

私有命令輸出、TMPDIR 與候選 evidence 留在 `.local/line-backup/tasks/notes-v3-f1-implementation-20261109/`，沒有 stage。本輪沒有清空、reset、checkout 或覆寫任何候選。

## 實作內容

### 共用分類

`src/line_backup_batch/notes.py` 新增 `_is_environment_attachment(path, *, directory, reserved_names)`。只有同時符合下列條件才分類為環境附屬項：

- basename 精確且大小寫敏感為 `.DS_Store`。
- `path` 是 `directory` 的直接 child。
- basename 不在 `reserved_names`；受管理名稱、目標碰撞及既有保留名稱優先。
- `directory` 存在、是目錄、非 symlink，且 canonical path 與自身一致。
- `path` 以 `lstat` 確認為 regular file、`nlink == 1`，且不是 symlink。
- 分類只讀 metadata，不開啟、不讀 bytes、不 hash、不保存內容。
- `OSError`、`RuntimeError`、`ValueError` 或其他不確定狀態一律 fail closed。

helper 沒有新增事件、CLI、狀態、schema、清理協議或公共交易介面。

### F1 call sites

同一分類套用到八個 F1 可達 gate：

1. reattest staging 第一次 children 名稱集合。
2. reattest staging 第二次 children 名稱集合；新增前後比較，若讀取期間出現未知 child，回 `STAGING_DIRECTORY_CHANGED_DURING_READ`。
3. reattest list 的 `names_before`，以 completion／present-empty staging 名稱作 reserved names。
4. reattest list 的 `names_after`，沿用同一 reserved names。
5. completion witness 前的 `directory_names`，以 expected completion files 作 reserved names。
6. completion witness 後的 `names_after`，沿用同一 reserved names。
7. `_candidate_file_availability` 的 active candidate 目錄實際名稱，保留原本 subset 語意。
8. `_completion_availability` 的 completion 目錄實際名稱，保留原本 exact-equality 語意。

`staging.children` schema 維持 `[]`；排除合格環境項不證明舊下載停止。舊事件 bytes、preview digest、expected tip、scope、generation、completion witness、replay、鎖與 UNKNOWN 防重送均未改寫。

### 測試

新增或調整的測試只使用既有 synthetic fixture，沒有修改舊 fixture 檔：

- `tests/test_notes_reattest.py`：list、completion、登錄 staging 的 `.DS_Store` 新增／改 bytes／消失；preview 純讀；witness／scope／digest 不變；preview 與 confirm 之間環境變化仍可確認；confirm 只新增一筆 transition；舊事件 bytes 不變；exact replay 不 append；新 Session 讀回原 UNKNOWN、fresh recovery scan 前不得建立新 v3 intent、scan 後才可建立 scoped v3；第一支完成 media inode／metadata／bytes 不變；其他 dotfile、同名 symlink／directory／hardlink、未知 staging、額外一般檔／影片及 staging 讀取期間新增 child 仍拒絕；reserved-name 碰撞優先。
- `tests/test_notes_records.py`：完成目錄 `.DS_Store` 新增／改 bytes／移除仍為 `COMPLETED`／`LOCAL_VERIFIED`；環境項不被 `read_file` 讀取；舊事件 bytes 不含環境名稱；同名 symlink／directory／hardlink 仍為 `LOCAL_CHANGED`；新 Session 無 UNKNOWN 路徑仍禁重下。
- `tests/test_notes_restart.py`：active candidate 目錄 `.DS_Store` 新增／改 bytes／移除仍為 `LOCAL_VERIFIED`；不被媒體讀取；事件 bytes 不變；同名 symlink／directory／hardlink 仍 `LOCAL_CHANGED`；同名 symlink 亦使 restart activation 拒絕；既有額外檔、symlink、hardlink、inode drift 負例保留。

本切片在同一個 Implementer 角色內使用 native subagent 做唯讀 mapping、測試設計與程式／證據稽核。這些 helper 找到 staging 缺少第二次 children snapshot 與額外測試覆蓋缺口；相應修正已納入本候選。最後一輪靜態稽核未發現已證實的 F1 錯誤放行、漏 gate 或 F2 超範圍改動；helper 回報不是獨立審查或正式 acceptance，TOCTOU 仍列未證實殘餘風險。

## 最終候選

產品與測試候選只含以下四個路徑，diff 為 `+501/-18`：

| 路徑 | SHA-256 |
|---|---|
| `src/line_backup_batch/notes.py` | `17ed5079803d1e46dab6637239e464a1361c803b4dc970fab03110ff42a471e5` |
| `tests/test_notes_reattest.py` | `44552648784cb112b41ef817edc14720b06a1342f482827a548dce5093d3b5c9` |
| `tests/test_notes_records.py` | `1e96a178f20fb7da3aa2fc69a3cd0bf958d34107332c04725e21651cba8b8c75` |
| `tests/test_notes_restart.py` | `4fd8f551180d35d022176dfad679a95512e023f32762ce566888815d5cf4c264` |

四檔 `git diff --binary` SHA-256：`9fea65401af08f6ae6df41c4925a3d875ad379af7c4d89c708dc69bd4105b767`。此 hash 不含後續新增的本報告。

`git diff --check` exit 0。最後 commit／push 後的完整候選與遠端 HEAD 另見交付 receipt。

## 指定檢查

cwd 均為 `/Users/hsiaojohnny/dev/Line_backup`。環境為 macOS 27.2 arm64、`/usr/bin/python3` 3.9.6、Git 2.52.0。所有命令均使用：

```text
TMPDIR=/Users/hsiaojohnny/dev/Line_backup/.local/line-backup/tasks/notes-v3-f1-implementation-20261109/tmp
PYTHONPATH=src
```

| 實際命令 | Exit | 結果 | 證據 |
|---|---:|---|---|
| `TMPDIR="$TMPDIR" PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py` | 0 | `Ran 29 tests in 6.438s`；`OK` | `.local/line-backup/tasks/notes-v3-f1-implementation-20261109/evidence/test_notes_reattest.final.stdout`、`.stderr` |
| `TMPDIR="$TMPDIR" PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py` | 0 | `Ran 25 tests in 2.738s`；`OK` | `.local/line-backup/tasks/notes-v3-f1-implementation-20261109/evidence/test_notes_records.final.stdout`、`.stderr` |
| `TMPDIR="$TMPDIR" PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py` | 0 | `Ran 37 tests in 7.123s`；`OK` | `.local/line-backup/tasks/notes-v3-f1-implementation-20261109/evidence/test_notes_restart.final.stdout`、`.stderr` |

`unittest` 結果寫入 stderr；三份 stdout 為空。`test_notes_records` stderr 另含既有 argparse 負例的 `INVALID_--_SIGNALS` 診斷文字，但測試總數與 exit 0 顯示 suite 成功，不是失敗。

## F1 覆蓋

| 項目 | 本輪可達證據 | 狀態 |
|---|---|---|
| V1 重新見證／可用性 | synthetic completion、原 v2 UNKNOWN intent、既有 OPEN_BATCH、device-only drift；list／completion／staging 環境項新增、改 bytes、消失；preview 純讀且 witness／scope／digest 不變；preview→confirm 間環境變化；confirm 精確一筆；舊事件 raw bytes 與第一支 media inode／metadata／bytes 不變 | F1 可達 synthetic subset PASS |
| V2 跨 Session | 兩次 synthetic Records session 讀同一帳本；原 UNKNOWN raw bytes 保留；fresh recovery scan 前禁建立新 v3 intent，scan 後才建立 scoped v3；exact replay 不 append；第一支仍完成且禁重下 | F1 可達 synthetic subset PASS |
| V5 安全負例 | `Thumbs.db`、`.AppleDouble`、`.DS_Store.backup`、未知 staging、額外一般檔／影片、同名 symlink／directory／hardlink、受管理名稱碰撞、staging 讀取期間新增未知 child 仍拒絕；active／completion 異常同名項 fail closed | F1 可達 synthetic subset PASS |

V3、V4、V6、V7、V8、V9 均 `NOT_RUN`。本輪沒有真實 LINE GUI、實際下載、真實 reattest、production media verifier、Homebrew ffmpeg／ffprobe、完整最小回歸或獨立接受；沒有新增人眼 `OBSERVED`。

## 殘餘工作

F2 仍需由後續 Implementer 依核准計畫處理：

- `_post_directory_for_publish`。
- `_ensure_publish_directory`。
- `_execute_publish`。
- `_ensure_restart_version_directory`。
- `_inventory_once`。
- 新 intent、三次採樣／manifest、普通／restart 發布、只剩環境項的 staging 保留收尾、candidate／activation 重讀與跨 Session 整合。
- 指定衝突文件；不得增加正式 Prompt 的日常步驟。

V3／V4 仍缺普通與 restart 的業務案例；V5／V6 完整負例與協議回歸、V7／V8 真解碼與最小回歸、V9 真實日常與獨立接受均未完成。原任務的核心結果仍阻塞，不能把 F1 綠燈或 helper 回報視為產品接受。

## 事實、推論與未知

**事實：** 核准來源與 baseline 相符；F1 產品只改 `notes.py`；三份指定 suite exit 0；工作區沒有其他 dirty／untracked 候選；本輪未讀寫真實帳本、active hint、媒體或 LINE。

**推論：** 共用分類沿既有 reattest 與 availability gate 套用，能在本輪 synthetic 可達路徑避免精確合格 `.DS_Store` 被誤當成未知媒體或交易內容；這不證明 F2 或真實流程已可接續。

**未知：** device 漂移原因、外部 writer、第二支影片是否晚到、原 OPEN_BATCH 當前適用性、修正後真實接續、跨模型重用、服務端原始位元一致性與 GUI exactly-once 均未消除。

## 停止條件與下一步

F1 到此停止。Owner 下一步是另啟 07 implementation Simplicity，交付本報告、精確候選／diff、三套證據及 V1／V2／V5 可達覆蓋。未經該檢查與人手續交，不開始 F2、不跨角色修復或重測、不執行真實 reattest／下載／GUI、不合併 master。

若後續出現來源／版本衝突、身分歧義、未明派送、寫入衝突、schema 原語不足、必須擴分類／路徑／scope／授權，應保留證據停交 Owner。退出碼 70 不是重送、改帳或換入口的理由。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: F1_IMPLEMENTED_AND_TARGETED_CHECKS_PASS
IMPLEMENTATION_STATUS: PASS_F1; V1_V2_V5_REACHABLE_SYNTHETIC_COVERAGE
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_SECOND_VIDEO_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: F1_THREE_SUITES_PASS; V3_V4_V6_V7_V8_V9_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN; HELPERS_ARE_NOT_INDEPENDENT_REVIEW
TASK_CLOSURE_STATUS: NOT_DONE; F1_DELIVERED_IMPLEMENTATION_SIMPLICITY_PENDING
```
