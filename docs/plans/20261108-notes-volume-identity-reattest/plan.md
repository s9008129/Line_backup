# 記事本重新見證計畫 v3：環境附屬項的檢查邊界（待核准）

## 決策摘要

角色結論：`PLAN_DRAFT_COMPLETE`。本輪只修訂舊計畫的檢查責任與防再發驗證，不修產品、不操作真實資料、不簽發產品 PASS。

Owner 要求同一列表兩篇記事本、各一支影片：保留第一支完成事實，中斷後接續第二支。[根因調查報告](../../根因調查報告.md) 已指出，舊設計把媒體完整性擴成容器全集純淨要求；`.DS_Store` 觸發 `UNREGISTERED_LIST_ENTRY`。刪除現場單一檔案尚未根治。

**最小方案：沿用現有 notes 交易與重新見證協議，讓明確界定的環境附屬項退出媒體、交易內容與穩定性判斷，並沿同一流程貫徹。** 不只放行 preview 第一個 gate，也不忽略全部未知項目。

分級維持 **CRITICAL**：雖然不新增介面或事件，拒絕條件會影響完成可用性、接續資格及發布收尾。保留由人啟動的計畫 Simplicity Review、獨立 Plan Review、首切片後 implementation Simplicity Review 與獨立接受。核准後交 Implementer（04），本 Planner 不啟動下一角色。這些開發關卡不增加日常入口。

## 範圍、版本與既有決定

| 項目 | 綁定與效力 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，目前主 worktree；不整理其他 worktree |
| 分支／起始 HEAD | `feature/line-notes-media`／`b635218da3ba4dbcfe563897e0d94515fe713414`；本輪即時遠端相同 |
| 起始 Git | `git status --porcelain=v1` 無輸出；沒有待吸收的 dirty／untracked |
| v2 設計來源 | `2b742b9ef670a6b618b794432e11d1af6c009f1b` 的 plan／handoff。舊 plan SHA-256：`937e86eb276ed025c41617d7a5fafc6c80259ea7bc0314e31fa5fc84eb3a858b` |
| 現有產品 | `15b919b` 已加入一次性 list reattest。本輪起始 `notes.py` SHA-256：`0e542d73024f8f1b78238dcb9b331d890c89223281c5543f8acf45b7135aed7b`；不再把 preview／confirm 當待新增功能 |
| 已有同意 | 2026-11-08 S1 交接記錄 Owner 已核准 v2、接受 witness trust 及無法排除完美 clone 的剩餘風險；不要求重複同意原決定 |
| 本版效力 | v3 待核准，取代下列邊界及切片安排；舊 PASS 只適用舊版，原審查報告不改寫 |
| 私有證據 | `.local/line-backup/tasks/notes-environment-boundary-plan-20261109/`：來源 hashes、原文快照、命令、文件檢查及交付 receipt |
| 現場證據 | 根因報告及 `notes-preview-20261108/` 既有 receipt。本輪不重讀真實帳本／媒體，不重跑 preview |

未變協議以該精確 v2 提交及現有介面為相容約束：每帳本一次 list-only、device-only 轉接，完整 completion witness，精確 preview digest／evidence／replay，原 OPEN_BATCH scope／generation，轉接後新完整 recovery scan，原鎖、事件 graph、退出碼與防重送。只取代下表，不重新設計協議。

| 舊條款／假設 | v3 取代內容 |
|---|---|
| 適用範圍第 5、6 點：完成目錄與 list 只容許登錄名稱，特別拒絕 `.DS_Store` | 受管理及未分類項目維持原檢查；合格環境項不參與名稱集合判斷 |
| 第 6 點、staging.children 的「全空」 | 是沒有媒體、交易內容或未分類項目；可只有合格環境項。children 保持原 schema，只列非環境項；環境 bytes 不進 witness |
| preview／confirm 前後全集、T1「完整名稱集合」、T2「額外檔」 | 比較受管理與未分類物件，不因合格環境項新增／變更／消失拒絕；未分類額外檔仍保護 |
| 舊 S1 新增 preview、S2 新增 confirm | 已是歷史工作，不重做；改採本版 F1／F2 |
| `test_extra_list_entry_is_refused` 用 `.DS_Store` 當必拒絕樣本 | 改成合格環境項可接續正例；另保留未知項與同名異常項的負例 |
| 舊 T1–T11 與實機要求 | 未變協議保留對應回歸；本案使用 V1–V9。不重做受控 volume 測試；若必須修改 device／witness 協議已超界，須停 |

v2 原文可從其原提交還原。原診斷、審查、報告與歷史切片 handoff 保留原綁定；本版不把它們的 PASS 擴張成新邊界已通過。

## 精確的環境分類

每個 gate 先辨識帳本引用、交易保留與預定目標，才分類其餘項目。**受管理名稱或目標碰撞優先，不得被環境分類遮蔽。**

本版只界定：位於已確認 canonical、非 symlink 的 notes 媒體容器內，精確名稱為 `.DS_Store`，以不跟隨連結的 metadata 確認為一般檔案、`nlink=1`，未被帳本、manifest、證據或交易引用／保留。適用容器限 list、完成貼文、已登錄 staging、普通發布目標及 restart candidate／版本目錄。

- 只為分類檢查型態，不解讀其內容，不對其 bytes 做媒體 hash 或穩定性見證。
- 合格環境項的存在、改 bytes、出現或消失，不改媒體計數、manifest、完成事實、本機可用性與合法派送資格；不列為影片或下載結果。
- 不泛指 dotfile、AppleDouble、`Thumbs.db`、一般未知檔、未知目錄或額外影片；擴分類須另有證據與核准。
- 同名 symlink、目錄、特殊檔、異常 hardlink、受管理名稱碰撞或分類失敗均不適用。按原規則拒絕，不藉改名掩蓋媒體變動。
- 受管理媒體仍驗 path、device／inode、size、mtime／ctime、SHA-256、完整解碼與原 witness，不能為容忍環境變化略過。
- 此分類不推廣到帳本 collection、events、evidence 或照片驗證器自行建立的隔離目錄。

不新增事件／schema、CLI、公共交易介面或狀態類別。staging 的 `children=[]` 只表示無受管理／未分類內容，不證明舊下載停止。舊事件原 bytes 不改寫；digest、expected tip、confirmation 與 replay 規則不變。若既有結構無法滿足，停止交 Owner，不擅改 schema。

## 同一流程的一致行為

行號綁定起始 HEAD，後續以函式／行為識別，不要求維持行號。

| `src/line_backup_batch/notes.py` | 必要結果與保留保護 |
|---|---|
| reattest staging :2762–2770，list :2800–2815／:2941–2956 | 環境項不影響空內容或前後集合；staging 仍只由既有 intent 認領，不按前綴認領 |
| reattest completion :2867–2927 | 見證全部登錄媒體；環境項不參與名稱全集及穩定性比較 |
| active :4026–4029，completion :4210–4235 | 環境項不使 `LOCAL_VERIFIED` 降成 `LOCAL_CHANGED`；真實缺檔／漂移仍保護；整篇缺席仍 `LOCAL_MISSING` 並禁止重下 |
| 新 intent staging :4709／:4798 | 保持新建、唯一、空白 staging 與 intent 讀回；只有合格環境項不阻擋。舊 UNKNOWN 不因此重送 |
| 普通發布 :5452–5459／:5598–5601 | 排除環境項；既有路徑／目錄認領、逐檔碰撞與不覆寫保護不變，不擴大目錄認領規則 |
| 發布後收尾 :5720–5725 | 媒體安全發布後，staging 若只剩合格環境項，保留目錄與原檔，正常保存／讀回 completion；真空目錄才沿原 rmdir。不遞迴刪除、搬移或新增清理協議 |
| restart :5894–5896 及 candidate／activation 重讀 | 同一分類，保留獨立 copy、hash／decode、generation／scope／單次 activation 與晚到原 staging 保護 |
| inventory :6560–6580 | 三次採樣、預期數與 manifest 只含真正媒體；環境變化不冒充媒體不穩定 |

保留的 staging 不得造成假 pending、活動下載、未知新媒體或重送資格。由既有 completion／事件認領完成 attempt，後續 memory、resume、新 session 與下一合格項一致讀回。不靠改歷史或先刪附屬檔達成。

## 可寫路徑與非目標

| 階段 | 可寫範圍 |
|---|---|
| 本輪 Planner | 本目錄 plan／handoff、新增 `planner-boundary-revision-report.md`、progress 只追加；私有 task 證據及摘要頁 |
| 待核准產品 | 僅 `src/line_backup_batch/notes.py` 上述判定及最小內部共用分類 |
| 待核准測試 | `tests/test_notes_reattest.py`、`tests/test_notes_records.py`、`tests/test_notes_restart.py`、`tests/test_notes_regressions.py`、`tests/test_notes_e2e_media.py` |
| 待核准操作文件 | `.agents/skills/line-notes-agent-cua/SKILL.md`、其 `references/download-and-ledger.md`／`verification-and-recovery.md`；`docs/LINE相簿備份_使用手冊.md` 僅記事本衝突敘述 |
| 後續交付 | 本目錄角色報告、progress、專案私有 tasks；公開成果須遮蔽且逐檔 stage |

禁止改 `AGENTS.md`、`daily.py`、相簿 Skill／Prompt、`image_decode.swift`、`notes_evidence.py`、媒體驗證器、事件／證據 schema、既有公共交易介面、舊 fixture、真實帳本／active hint／照片影片。共用手冊只補記事本註解，不改相簿語意。

不新增恢復協議、連續 reattest、清理工具、daemon、controller、一般檔案管理或 Owner 日常步驟。不追查 device 原因或附屬檔建立者，不把開發計畫變成日常必讀，不 merge master／force-push。

## 方案取捨與風險

| 方案 | 決定與理由 |
|---|---|
| 只刪現場檔案 | 已有刪除證據；環境可再建立，不能防再發 |
| 只放行 preview | 不採；後續可用性、採樣、發布與收尾仍會再擋 |
| notes 內明確分類、保留受管理物件檢查 | 採用；直接修責任邊界，不重做交易 |
| 忽略全部未知項／dotfile | 不採；會遮蔽額外影片、未知 staging、碰撞與連結 |
| 新環境 manifest、清理協議或 schema | 不採；附屬項無須變成備份物件 |

records lock 不鎖 Finder 或 LINE。僅承諾在既有觀測／驗證邊界檢出受管理物件可見變動，不能保證整樹原子快照、未知下載已停、GUI exactly-once、OS 隔離或 provider 行為。有限前後檢查不擴成無限 recheck。合格環境項若變成非合格型態或碰撞目標，保留現況並拒絕。

程式回退限相容版本，不刪事件或清空帳本；已新增的完成事實不能藉回退消除。

## 首切片與必要驗證

**F1**：修正 reattest（staging、completion、list 及前後比較）、active／completion 可用性，在 reattest、必要的 records／restart 測試建立業務正負例，完成 V1、V2、V5 的可達部分。沿用現有協議與 fixtures，不宣稱整條已修好。交付候選、證據、殘餘 gate 清單後停止，由人啟動 implementation Simplicity Review。

**F2**：有剩餘工作才由人續交 Implementer，補齊新 intent、inventory、普通／restart 發布、保留 staging 收尾、跨 Session 整合及衝突文件，完成 V1–V8。若 F1 已涵蓋全部且檢查完整，仍做首切片 review，不製造空切片／重複角色。

以下均為後續要求，本輪全部 `NOT_RUN`：

| ID | 責任人／滿足證據／停止條件 |
|---|---|
| V1 重新見證、可用性 | Implementer：合成第一支 completion＋第二支原 attempt＋既有 OPEN_BATCH＋device-only drift。環境項在 list、completion、登錄 staging 新增／改 bytes／消失，含 witness 前後、preview→confirm 間；媒體 witness／scope 不變，第一支完成／可用性不變，preview 純讀、confirm 仍精確單筆。需新 schema 或重新確認無關 scope 即停 |
| V2 跨 Session | Implementer：A 完成第一支，B 讀同一帳本、依第二支當時狀態前進。分別測無 UNKNOWN 的合法路徑及有 UNKNOWN 仍禁重送；只有原精確 OPEN_BATCH 例外＋新 recovery scan 才可建 scoped v3。比較 completion／UNKNOWN raw bytes、第一支 inode／hash、媒體鍵、attempt 數與最終有效完成；不偽造 STOPPED。GUI 次數由 V9 證實 |
| V3 採樣到發布 | Implementer：三次採樣、驗證、普通發布、restart copy／candidate／activation 前後注入環境變化；manifest／數量只有影片，hash／完整解碼仍必要。普通與 restart 各有業務案例，不能只測分類函式；真影片漂移被放行即 FAIL |
| V4 收尾與重開 | Implementer：來源移除後、completion 前留下環境項，保留其 bytes、正常完成且無假 pending；回覆遺失後新 Session 讀回／resume，不多 completion／派送。restart active version 及下一合格項同樣一致；需刪檔或新清理事件即停 |
| V5 安全負例 | Implementer：缺檔、hash／inode／mtime／ctime 漂移、未登錄 staging、非空未知內容、額外影片、一般未知檔／其他 dotfile、同名目標、異常同名環境項、祖先 symlink、受管理名稱優先、帳本／證據損壞仍拒絕；整篇缺席仍完成且禁重下，真 naming pending 不解除。新增／調整拒絕須指出保護物件、具體損害與正負例 |
| V6 協議不變 | Implementer：現有單次限額、再次 drift 停止、精確 replay、stale tip／媒體 witness 拒絕、鎖、session／scope／generation、fresh scan、v2／v3 防重送及 0／2／4／70 語意回歸。沿現有案例，不新建協議；失敗留證停止 |
| V7 真解碼合成媒體 | Implementer：沿 `test_notes_e2e_media.py` 入口，用隔離合成影片走 production verifier，manifest 不含附屬檔、截斷影片仍拒絕。照片既有回歸不變；用原 ImageIO、成對 Homebrew ffmpeg／ffprobe，不改工具鏈；無工具記 NOT_RUN／阻塞，不能改成 mock PASS |
| V8 最小回歸、文件 | Implementer：以下三條完整回歸當次 exit 0 與 counts；記事本衝突文字明確界定額外檔，正式 Prompt／日常步驟不增加。失敗記錄證據停止，不自開跨角色修復 |
| V9 真實日常、獨立接受 | Owner 以手冊記事本正式 Prompt＋有效前景另啟備份，保留第一支、查明第二支真實狀態；真實 reattest 若必要，仍需原精確同意，計畫不代替。保存實際派送次數、outcome、驗證／發布與新 Session memory。獨立者映射 V1–V9 及未測項，不用 Acceptance／E2E 角色 Prompt 取代日常入口。來源／狀態不允許接續、前景中斷或未明派送時停，不為測試重下第一支 |

F1 指定局部命令，在 repo 根只用合成資料：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
```

F2 開發依變更選上述局部檢查及相同 discover 格式的 `test_notes_regressions.py`／`test_notes_e2e_media.py`。最終候選一次執行完整最小回歸，已包含局部檔，不無故重跑：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

原始命令／cwd／環境／exit／counts、候選 HEAD／diff、hashes、前後清單及業務斷言留專案私有 task。既有測試若預設系統暫存區，使用專案新建 synthetic TMPDIR，不用真實照片區。合成呼叫次數不等於 LINE 實際派送次數；解碼不證明服務端原始位元一致。

## 人工交接、成功條件與停止

Owner 決定 v3 與適用重審；建議另啟計畫 Simplicity、CRITICAL 獨立 Plan Review，核准及必要關卡完成後交 04 做 F1。既有 v2 trust 同意保留；此次只核准改正邊界。拒絕或未解 blocker 應回報後停止，不自動跨角色修復。

產品成功須同時證明第一支完成事實／原檔未變，第二支依真實狀態合法接續、同 attempt 當次控制最多一次，環境變化不錯算、不誤降、不留假 pending，真實資料異動仍保護。合成測試、簿記、解碼、OBSERVED、LINE 及獨立接受分開報告。缺 V9 不稱原任務 DONE，也不宣稱所有模型每次已驗證。

未知：當前真實附屬項、device 原因、第二支是否晚到、來源可用性、原 OPEN_BATCH 現在是否適用及外部 writer 行為。本輪未重查，不預填成功。

若需超出可寫路徑、改 schema／公共介面／媒體驗證器／相簿、擴環境分類或 restart scope、取消 witness／單次限額、改舊歷史、操作真實資料或新增 Owner 日常手工步驟，停在具體證據交人決定。同根因最多三次有證據嘗試，兩次連續無新資訊即停，換 Session 不重置。exit 70 不是重送理由。

## 本輪狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NO_PRODUCT_CHANGES_THIS_ROLE; BOUNDARY_FIX_NOT_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: NOT_RUN; ORIGINAL_SECOND_VIDEO_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; V1_V9_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_V3_APPROVAL_AND_APPLICABLE_REVIEWS
```
