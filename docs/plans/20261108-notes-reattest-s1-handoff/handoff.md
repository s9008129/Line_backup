```text
你是由 Owner 在另一個主 Session 啟動的 Implementer。請在 /Users/hsiaojohnny/dev/Line_backup 的 feature/line-notes-media 分支，依 /Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md、AGENTS.md 與本文件，實作已核准 v2 計畫的首切片 S1。

Owner 已明示：「我核准並接受信任模型與 clone 剩餘風險」。v2 的獨立 Plan Review 與計畫 Simplicity Review 均已 PASS；不要把原草案中的歷史「待核准」當成仍缺批准，也不要要求 Owner 重複同意。這不授權真實帳本轉接、LINE、下載、S2 或合併 master。

先核對 repo、branch、HEAD、Git 狀態、本交接的交付 commit，以及本文件列出的來源 hashes；保留既有 dirty／untracked，勿讀取未追蹤 Session Markdown 內容。詳讀 docs/plans/20261108-notes-volume-identity-reattest/plan.md、原 handoff.md、plan-review-v2.md、simplicity-plan-review-v2.md 與本文件，再讀診斷及現有程式。核對交接提交相對 c99ff874f6f809536a412e59050c50c5990649a4 沒有產品或受審文件漂移；不要要求交接後 HEAD 仍等於 c99ff87。

只新增 read-only `notes reattest preview --records-root R --session-id S`、供後續共用的 bounded witness builder、相應 CLI／lock 分類與合成測試。嚴格實作 plan.md 的適用條件、witness、preview schema／digest、NO_CHANGE、拒絕與退出碼。preview 必須鎖內驗帳及 session，驗完整物件集合且拒絕可見漂移；不得保存帳本 evidence、追加事件、建 staging／媒體目錄或改 active hint。保持 dispatch_authorized=false、external_copy_verified=false、real_line_e2e=NOT_TESTED。

產品僅改 src/line_backup_batch/notes.py；新增 tests/test_notes_reattest.py，必要時才修改本文件列出的既有測試。所有執行案例只用專案內隔離 synthetic 資料；不讀或操作真實帳本、active hint、照片影片或 LINE。既有測試可以在合成 fixture 中建立既有交易；不能把這誤作對真實資料的授權。

不得實作 confirm、新事件 kind／validator／graph／有效 binding projection、轉接後 freshness gate、T11 或連續 witness 鏈；不得為測試而提早註冊新 kind。不得改 notes_evidence.py、daily.py、舊 fixture、媒體驗證器、Skill、手冊、歷史事件或任何既有安全與授權邊界。完整 witness 不得簡化成單一 hash，也不能 blanket 拒絕 scope 內 UNKNOWN；空 staging 不證明已停止。

執行本文件 S1 的三條指定檢查，記錄實際命令、exit、環境、counts 與合成資料前後清單；未執行項一律 NOT_RUN。完成後寫 docs/plans/20261108-notes-reattest-s1-handoff/implementation.md，交付精確候選與證據。依既有同範圍 Git 授權逐檔 add、commit、普通 push，核對 commit 本體四要素與遠端精確 HEAD，保留無關檔案。不要 merge、force-push 或改寫歷史。

遇到缺來源、版本衝突、必須擴案、既有原語不足或未解阻塞時，保留證據並停止，不換入口繞過。產品 CLI exit 70 不是可重送業務拒絕；同一根因最多三次有證據嘗試、兩次無新資訊即停止。S1 交付後停下，由 Owner 另開 Simplicity Reviewer（Implementation）；不得自行做 S2、正式接受、真實 E2E 或結案。
```

# Implementer 交接：記事本重新見證 S1 唯讀預覽

## 目前決定與本文件效力

**v2 計畫已獲 Owner 核准，下一正式角色為 Implementer，僅執行 S1。** 本文件開頭為可複製到下一主 Session 的啟動 prompt；使用者親自啟動該 Session，本輪不派送正式角色或開始產品實作。

Owner 於 2026-11-08、本輪訊息明示：「我核准並接受信任模型與 clone 剩餘風險」，並要求本交接與 add／commit／push。此決定承接前輪列出的 v2、witness-based trust、無法排除完美 clone 及既有首版界線；沒有要求新增 clone detection、支援第二次漂移或調低防護。

原 plan 標題仍為「草案 v2」，原 Planner handoff 與審查報告仍記各自當時的「待核准」。這些是保留的歷史快照。**本文件記錄其後的 Owner 決定，不改寫已審查設計、不覆寫原 handoff 或兩份審查，也不要求重走已完成的 v2 計畫關卡。** 若內容或候選再有實質變更，才由 Owner 決定適用重查。

本輪授權是撰寫、驗證及提交交接文件。下個實作 Session 的範圍承接已核准計畫的 S1；不是整個 S2 或真實備份授權。對任何真實 list binding 的轉接，未來仍需當次精確 preview 與 Owner 另行明示同意。

## 目標、基準與需保留的工作

整體目標：為 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED` 的第一次 device-only 漂移提供受控、追加式、list-only 的恢復協議，保留既有 OPEN_BATCH 與所有舊歷史。S1 只產生可核對的預覽，**不解除目前 binding gate，原備份仍阻塞**。

| 項目 | 精確身分 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`；目前主 worktree，其他 worktree 不整理 |
| 分支 | `feature/line-notes-media`；不得合併到 master |
| 本交接起始 HEAD | `c99ff874f6f809536a412e59050c50c5990649a4`；當次即時遠端 HEAD 相同 |
| 核准計畫 | `../20261108-notes-volume-identity-reattest/plan.md` v2，設計提交 `2b742b9ef670a6b618b794432e11d1af6c009f1b` |
| 原受審 handoff | `../20261108-notes-volume-identity-reattest/handoff.md`；保留原內容及 hash，不與本文件混稱 |
| 目前交接 | `docs/plans/20261108-notes-reattest-s1-handoff/handoff.md`；本文件所在交付 commit 是下一實作起點 |
| 起始工作樹 | 無 tracked dirty；既有 `codex-session-01a1bab6-c1b6-75b0-a7e0-bcf9dbf72d2c.md` 為 untracked，未讀內容、未修改、不得納入提交 |
| 本輪文件差異 | 新增本 handoff，原任務 progress 僅追加；產品、測試、Skill、原 plan／handoff、診斷與審查不變 |

交付 commit 的完整 SHA、commit 本體與遠端核對記於本輪私有 `delivery-receipt.md` 及最終回覆；避免在尚未生成的提交內自我引用。接手先執行 `git log -1 --format=%H -- docs/plans/20261108-notes-reattest-s1-handoff/handoff.md` 找到本交接提交，再核對 HEAD 與來源。若有後續提交或同路徑 dirty，先釐清精確候選；產品或計畫實質漂移時停止回報，不自行換基準。

### 來源 SHA-256

下表是本輪重新核對的工作樹 bytes，均與起始 HEAD 對應 blob 相同。前四份來源位於 `docs/plans/20261108-notes-volume-identity-reattest/`。

| 來源 | SHA-256 |
|---|---|
| `plan.md` v2 | `937e86eb276ed025c41617d7a5fafc6c80259ea7bc0314e31fa5fc84eb3a858b` |
| 原 `handoff.md` | `a6bd06190ca677363ecb2e08847d9863d5daf99c24bb79135f3a8ae9752d71e8` |
| `plan-review-v2.md` | `aa97bfe28f113123331ed3a4eb05724db6ba876f487d71fb8cfebe81ba3eba21` |
| `simplicity-plan-review-v2.md` | `3e09bc50544d535f1979e10086eef3092d24e53153e2fffeb85e15107a4d6f01` |
| `src/line_backup_batch/notes.py` | `80d0ab5b61b27eee4b5ee9727eef6176ba5a489365ae1651e27f0295fc1170b0` |

## 已完成工作與證據強度

| 已完成項 | 結果／來源 | 不代表什麼 |
|---|---|---|
| 原因診斷 | `issue-analysis.md`：定位 list directory device gate，提出 list-only 方向 | 沒有證明 remount 或同一持久 volume |
| v1 Plan Review | `plan-review.md`：B1 要求修訂，原 witness 與連續轉接基準矛盾 | 不把這份舊拒絕刪除或改成 PASS |
| v2 能力選擇與修訂 | `planner-revision-report.md`：每帳本至多一次；保留 before，新增 T11 | 不是連續轉接或全層重新認領 |
| CRITICAL 獨立 Plan Review v2 | `plan-review-v2.md`：PASS；交付提交 `1818701da49f6092c989f34f6bc01607837878b5` | 不是產品或獨立 acceptance |
| 計畫 Simplicity 重審 v2 | `simplicity-plan-review-v2.md`：PASS；交付提交 `c99ff874f6f809536a412e59050c50c5990649a4` | 不是 S1 實作審查 |
| Owner 核准 | 本輪明示原話，私有 `owner-approval.md` 保存來源說明 | 不是精確真實轉接同意或 GUI 前景交接 |

真實資料的 28 events、2 個 v2 intents、1 completion、0 個 v3 intents、空 UNKNOWN staging 及 matching witness 均是**既有診斷來源**，本輪未重查。S1 必須建立獨立合成案例，不以這些舊數字假稱當前觀察或把真實帳本複製成測試 fixture。

## S1 的最小可寫範圍與行為

以下是已核准 `plan.md:163–175` 的首切片，不是修改設計。

| 路徑／工作 | S1 範圍 |
|---|---|
| `src/line_backup_batch/notes.py` | 只新增 readonly preview、供後續共用的 bounded witness builder、必要 CLI 與 lock busy 分類；維持現有命令及 guard 語意 |
| `tests/test_notes_reattest.py` | 新增隔離 synthetic 的 preview、witness、拒絕與無副作用測試 |
| `tests/test_notes_locks.py` | 僅必要的 preview lock 分類覆蓋，不改通用 lock 語意 |
| `tests/test_notes_restart.py`、`tests/test_notes_regressions.py` | 計畫容許的必要最小測試調整；無具體需要就不改，不修改舊 fixture |
| 本 S1 任務文件與原 progress | 寫 `implementation.md`、追加進度；私有測試／日誌／hash／前後清單放專案任務目錄 |

preview 命令形狀：`PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes reattest preview --records-root R --session-id S`。本句描述**待新增的命令**，目前尚無實作；本交接沒有執行它。S1 完成後也僅能在合成 records-root 執行。

實作時依 plan 的完整結構及規則，不從本摘要推造較寬 schema：

- 適用範圍：`plan.md:47–60`。唯一 OPEN_BATCH 尚未 activation、沒有 v3／candidate／pending publish，合法 session；path／inode 不變，僅 device 變化。所有 v2-intent completion 與已登錄 staging 的完整 witness 都要參與，不能選一個成功樣本。`line-notes-completion/v1` 不等於舊 v1 intent。
- witness：`plan.md:54–56`、`:75–90`。精確名稱集合、regular／nlink=1／無 symlink、inode／size／mtime_ns／ctime_ns／hash 與單一 device 對應；無追蹤讀取及 hash 前後檢查。scope 內 UNKNOWN 可觀測但不解鎖；scope 外異常、未知或非空 staging、額外子項及不支援布局均拒絕。
- preview 輸出：`plan.md:79–87`、`:96`、`:101`。固定 schema／scope／排序／digest，`CONFIRMATION_REQUIRED` 或 `NO_CHANGE`；NO_CHANGE 的 witness 維持固定空結構。`dispatch_authorized=false`、`external_copy_verified=false`、`real_line_e2e=NOT_TESTED`。preview 的成功不代表目前帳本可派送。
- 只讀：既有 records lock 中載入／驗帳與檢查 session；不追加事件、不保存帳本 evidence、不建 staging／媒體目錄、不改 active hint。建立合成 fixture、測試輸出與私有 stdout 檔屬開發產物，不是 preview 可修改被觀測樹的例外；依既有 lock 原語，不加第二套鎖。
- 錯誤：`plan.md:107–111`。維持 exit 0／2／4／70 與已定 reason，不將已知拒絕全包成內部錯誤，也不把 exit 70 當可重送拒絕。lock busy 為 preview 的 read-only 分類，可回 retry_safe=true。
- 每帳本一次仍是整體協議界線，但 S1 不註冊新 kind；含已成立 reattest 歷史的可載入 fixture、confirm replay、第二筆 graph 拒絕與 T11 明定留 S2，不為測它們提早擴大 S1。

### 本切片不能提前做的部分

S2 才加入可寫 confirm、`list-directory-reattest` kind 與 validator／graph、有效 binding resolver 投影、精確 replay／一次限額寫入分支、轉接後 fresh scan gates、整合測試及 Skill／references／手冊。S1 不以「幾行順便完成」提前加入。

整個計畫仍禁止修改 `daily.py`、相簿 Skill／Prompt／公開介面、`image_decode.swift`、`notes_evidence.py`／既有證據 schema、媒體驗證器、舊 fixture 或歷史事件。Skill 與手冊雖列於全計畫可寫範圍，S1 仍不修改。不得建立 controller、daemon、全域協調或連續 witness 鏈。

## S1 指定檢查與成功證據

由 **Implementer** 在 repo 根、僅使用專案內隔離 synthetic 資料執行，記錄 stdout／stderr、實際 exit、測試 counts、環境與精確候選，不引用前輪 PASS：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py
```

三條命令必須各自記 exit，不能只記最後一條。S1 的 T1／T2 以新測試覆蓋；不為多跑檢查而自行擴大測試範圍。T7 全回歸與 T3–T6／T11 中需可寫轉接的部分留完整實作階段；未做就標 NOT_RUN，不把切片檢查冒充全計畫通過。

| 驗證責任 | S1 必要通過證據 |
|---|---|
| T1 純讀／事故形狀 | 合成 v2 completion＋v2 UNKNOWN＋既有 restart confirmation＋device drift；回 CONFIRMATION_REQUIRED。無漂移回 NO_CHANGE。成功及拒絕前後，events／evidence／active hint 與媒體樹內容清單無變；不新建 staging，不解除舊狀態 |
| T2 witness 負例 | 依 plan T2 覆蓋 inode、hash、size、mtime、ctime、symlink 含祖先、hardlink、缺／額外檔、未知／非空 staging、空 witness、不同 device mapping、scope 外異常；不得不符仍成功或只取部分 witness |
| CLI／lock | 新命令 help、必填、已知拒絕及 read-only lock busy 分類符合既有契約；沒有可派送／可寫 confirm 路徑 |
| 現有相容邊界 | 原 list gate、completion／staging／availability 與 UNKNOWN 防護未變；新增 preview 不藉忽略 st_dev 讓舊命令放行 |

合成 device drift 必須明記為測試資料或測試替身，不能寫成真實 remount／受控 volume PASS。正常 pytest／unittest 測試資料操作不授權接觸 `notes-backup-records/`、`backup-records/`、`backup/` 或真實 active 檔；既有真實資料不作為測試輸入。

S1 新私有產物建議放 `.local/line-backup/tasks/notes-volume-reattest-s1-20261108/`；若已存在，另取新子目錄保留舊證據。日誌、diff、候選 HEAD、hash 與前後清單留專案內，不放全域 `.codex`。不用原始媒體、群組／人名、原始檔名、憑證或未遮蔽證據填公開報告。

## 風險、未知與停止條件

**已接受的模型：** matching witness 與精確 Owner 決策支持 list-only binding 轉接；不能辨識完全相符的 clone。這不是證實 remount、同一 volume、排除 inode 重用或服務端原始位元一致。

**仍成立的限制：** 有限布局、既有鎖只協調守鎖 CLI、最後 snapshot 核對到提交仍有有限競態窗、舊 binary 拒絕新 kind。S1 尚不寫新事件；後續也不能藉版本回退刪事件或改寫歷史。

**未知：** 漂移外部原因、舊 UNKNOWN 是否晚到、真實 list 完整允許集合、轉接後其他 gate 能否通過、受控 volume 與 LINE／跨 Session 的實際可用性。接受風險不把未知升格為已驗證。

遇到來源缺失、產品／計畫版本漂移、必須改 completion／candidate／staging guard、擴 restart scope／資料布局／schema／可寫路徑、既有原語不足或其他未解阻塞時，保留現況與證據交 Owner，不修計畫或跨角色 repair／retest。同一根因最多三次有證據嘗試，連續兩次無新資訊停止；新 Session 不重置。範圍內有新證據的例行機械修正不必逐次再問。

真實帳本 preview／confirm／bind／scan／intent、T8 volume、T9 LINE／chooser／下載／解碼、跨 Session 實機及獨立 acceptance 均未在本輪授權或執行。使用者接受設計風險不解除這些當次操作邊界。

## 實作交付與下一個人工關卡

Implementer 交付 `implementation.md`，至少含：起始及最終 HEAD、核准來源與 hashes、逐檔差異、實際行為與 S2 未完成項；三條命令的 exit／counts／環境／日誌；合成樹前後清單；六項狀態、未知及停止原因。成果是 S1 候選，不是整個備份修復或 DONE。

依 AGENTS.md 既有同範圍授權逐檔 stage、commit、普通 push 至 `feature/line-notes-media`；不夾帶既有 untracked 或私有資料。每筆 commit 本體填「意圖」「做了什麼」「下一步的建議」「驗證與結果」，以 `git show -s --format=%B` 核對，推送後用 `git ls-remote` 核對遠端精確 HEAD。失敗如實標 COMMIT_OR_PUSH_BLOCKED，不 force-push、merge 或改寫歷史。若無必要差異，寫 NO_CHANGES_TO_COMMIT，不造 empty commit。

S1 完成後，**由 Owner 另啟動 Simplicity Reviewer（Implementation）**，傳遞核准 plan、本 handoff、`implementation.md`、精確候選／diff 及當次證據。該角色未完成前不自動進 S2。後續 S2、獨立 acceptance 與真實日常試用各保留人工交接；日常試用仍使用手冊記事本正式 Prompt，不用 Harness Acceptance／E2E Prompt 替代。

## 必須攜帶的文件與本輪檢查

下一 Session 需能讀取：本 handoff、原任務的 `plan.md`／原 `handoff.md`／`plan-review-v2.md`／`simplicity-plan-review-v2.md`／`planner-revision-report.md`／`issue-analysis.md`／`problem-report.md`／`progress.md`，以及 AGENTS.md、04_implement_prompt 與全域同版本 policies。原 v1 `plan-review.md`、`simplicity-plan-review.md` 供查 B1 沿革，不作 v2 PASS。

repo 根沒有可用 Harness controller；若 repo 的 policies 路徑不存在，讀 `/Users/hsiaojohnny/.codex/policies/v4.9.0/workflow-routing.md` 與 `subagent-model-policy.md`，不借用別版或恢復退役框架。角色／model 由人選；同角色助手繼承，不加 model／effort override、不宣稱無證據的後端身分或 token 節省。助手不得作正式獨立接受。

本輪交接文件檢查由主 Session 負責，原始紀錄位於 `.local/line-backup/tasks/notes-volume-plan-20261108/s1-handoff/`：

| 當次已執行 | Exit／證據 |
|---|---|
| Git repo／branch／HEAD／status／worktree、即時 ls-remote | 各 0；起始本地與遠端精確 HEAD 相同，保留既有 untracked |
| 原始碼與來源 SHA-256／commit blob 核對 | 0；八份來源 matches_start_commit=true，見 `source-and-version-checks.json` |
| 閱讀角色 checklist／template／Implementer prompt、plan 與兩份 v2 審查 | 0；03_handoff 是人工 checklist，沒有因此啟動另一正式角色 |
| 同角色來源助手 | 回報兩次唯讀 exec 各 0；只整理 S1／S2 及歷史版本界線，未作正式審查或接受 |

交付前的文件格式、只追加 progress、允許路徑與受保護來源不變檢查，以及 commit／push／遠端回讀，另記同目錄 `document-checks.json`、`delivery-receipt.md`；以實際輸出為準，不預填成功。本輪不執行產品測試，S1 三條命令及 T1–T11 全部 NOT_RUN，無新增實機 OBSERVED。

## 交接時六項狀態

```text
PRIMARY_OUTCOME_STATUS: V2_PLAN_APPROVED_BY_OWNER; S1_HANDOFF_PREPARED
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_SOURCE_AND_VERSION_CHECKS_ONLY; S1_AND_PRODUCT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_START_OF_IMPLEMENTER_S1
```

本輪文件提交與遠端完整性不代表獨立 acceptance。Owner 的計畫與風險核准已有效，不需要重問；真實精確轉接與後續正式角色仍依各自邊界另行啟動。
