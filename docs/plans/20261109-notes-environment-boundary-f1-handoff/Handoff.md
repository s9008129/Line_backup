```text
你是由 Owner 另開主 Session 啟動的 Implementer。請在 /Users/hsiaojohnny/dev/Line_backup 的 feature/line-notes-media 分支，依 /Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md、AGENTS.md 及本 Handoff.md，實作已核准 v3 計畫的首個可驗證切片 F1。

Owner 本輪明示：「這份交接文件是我批准執行的，要直接提供給下一個 agent 來進行 implementation。」v3 計畫 Simplicity Review 與 CRITICAL 獨立 Plan Review 均 PASS。此交接記錄其後的核准；原 plan／Planner handoff 的「待核准」是保留的歷史狀態，不再向 Owner 要求相同核准。既有 v2 trust／clone 剩餘風險同意仍有效；這不授權真實 reattest、帳本／媒體操作、LINE、下載或合併 master。

先查 repo／worktree／branch／HEAD／dirty／untracked／遠端，保留現有工作，不 reset／clean／覆寫。用 git log -1 --format=%H -- docs/plans/20261109-notes-environment-boundary-f1-handoff/Handoff.md 找本交接提交，核對本文件來源 hashes 與交付後 diff。受審設計是 bdde2a07d6de3195996589ca4ceac871cceca80a 的 v3 plan／handoff；本交接提交只是後續文件交付，不要求 HEAD 停在舊設計提交。產品或計畫若實質漂移，保留證據停止，不自行換基準。

詳讀 docs/plans/20261108-notes-volume-identity-reattest/ 的 plan.md、handoff.md、planner-boundary-revision-report.md、reviews/v3-bdde2a0/simplicity-plan-review.md、reviews/v3-bdde2a0/plan-review.md，以及 docs/根因調查報告.md、本 Handoff.md 全文與現有 notes.py／指定測試。不要沿舊 S1／S2 未來式重新新增 preview／confirm，兩者已實作；也不要把舊 v1／v2 PASS 當 v3 接受。

只先做 v3 F1：修正 reattest 的 staging、completion、list 名稱集合與前後比較，以及 active／completion 可用性，建立 V1、V2、V5 在 F1 的可達業務正負例。以最小內部共用分類排除精確 .DS_Store：已確認 canonical 非 symlink 媒體容器內、不跟隨連結確認 regular file、nlink=1、未被帳本／manifest／證據／交易引用或保留。每個 gate 先辨識受管理／保留名稱及目標碰撞；不得 blanket 忽略 dotfile、未知檔、未知 staging、額外影片或異常連結，不讀環境檔內容、不把環境 bytes 放進 witness 或 manifest。

環境項新增／改 bytes／消失不得使第一支完成／可用性改變；受管理媒體的 path、device／inode、size、mtime／ctime、hash 與既有驗證仍保留。staging.children 維持 schema，排除合格環境項；children=[] 不證明舊下載停止。保留單次 list-only/device-only reattest、原 completion witness、expected tip／digest／evidence／精確 replay、OPEN_BATCH scope／generation、轉接後 fresh recovery scan、鎖、事件 graph、退出碼及 UNKNOWN 防重送。舊事件 bytes 不改寫。

F1 產品只改 src/line_backup_batch/notes.py 的上述行為及必要最小共用分類；測試只改 tests/test_notes_reattest.py，必要才改 tests/test_notes_records.py、tests/test_notes_restart.py。既有 fixture 可沿用，不修改舊 fixture 檔。不改 plan／歷史報告、AGENTS.md、daily.py、相簿、notes_evidence.py、schema、公共介面、媒體驗證器、工具鏈或真實資料。F2 的新 intent、inventory、普通／restart 發布與保留 staging 收尾、操作文件仍須列殘餘清單；不要為 F1 的綠燈而弱化其保護或自動擴做 F2。

只用專案新建隔離 synthetic TMPDIR，執行本文件三條 F1 指定 unittest discover；保存原始 argv、cwd、環境、exit、counts、候選 diff、前後清單及業務斷言。不只測名稱分類 helper：比較第一支完成事件／inode／hash、第二支原 attempt／UNKNOWN、witness、scope、媒體鍵、attempt 數、讀回及防重送。不能偽造 STOPPED；合成兩 Session 讀回不是 LINE 實機跨 Session。

寫本目錄 implementation.md，交付精確候選、已改路徑、V1／V2／V5 覆蓋、三條命令結果、所有殘餘 gate 及 V3–V9 未測項。六狀態分開，未跑標 NOT_RUN，人眼標 OBSERVED；不簽發接受或原任務 DONE。沿用同範圍 Git 授權逐檔 add／commit／普通 push，message body 含意圖、做了什麼、驗證與結果、下一步的建議，查回 commit 本體及遠端精確 HEAD。不得夾帶既有 dirty／私人原始證據，不 merge／force-push。

F1 交付即停，由 Owner 另啟 07 implementation Simplicity。即使首切片已是完整候選，也不跳過該檢查；審查後有剩餘工作才由人續交 F2，不造空切片。缺來源、版本／身分衝突、必須擴案、schema 原語不足或未解 blocker 時留證停交人決定；不自行啟動另一正式角色、跨角色修復、重測或結案。同根因最多三次有證據嘗試，兩次連續無新資訊即停；exit 70 不是重送或換入口理由。
```

# Implementer 交接：v3 環境附屬項邊界 F1

## 核准、目標與本文件效力

**Owner 已核准此交接供下一位 Agent 執行 implementation，下一角色為 04 Implementer，先做 F1。** 核准來源為本輪明示：「我要你寫一份交接文件，這份交接文件是我批准執行的，要直接提供給下一個 agent 來進行 implementation。」本文件記錄該決定，不重寫已審 plan／handoff 或舊報告。

原任務是同一列表兩篇記事本各一支影片：保留第一支完成事實，中斷後依第二支真實狀態合法接續。已定位根因為把媒體完整性擴成容器全集純淨；刪單一 `.DS_Store` 不是根治。F1 修正重新見證與完成可用性的責任邊界；整條流程與真正第二支接續仍待後續證據。

本輪依 03 人工交接 checklist 撰寫文件，不建立新的正式角色或實作。Owner 既有 v2 trust／clone 同意保留；本次 v3 開發核准不等於真實 preview digest 的精確 reattest 同意，也不授權 GUI、下載、真實帳本、照片影片、清理或合併。

## 任務與精確版本

| 項目 | 綁定 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，主 worktree；其他 worktree 不整理 |
| 分支／本輪起始 HEAD | `feature/line-notes-media`／`89111a932ae61ad811e326534b9f221eb4d4081a`，當次遠端相同 |
| 受審及核准設計 | `bdde2a07d6de3195996589ca4ceac871cceca80a` 的 v3 plan／Planner handoff |
| 原計畫目錄 | `../20261108-notes-volume-identity-reattest/`，下表來源均相對 repo 根目錄 |
| 本交付 | 本 `Handoff.md`、本目錄 `progress.md`；Plan Review 已由原 Session 提交於 `270bd5f712080a57ae857045071a9e22605a09a1`；本交付 SHA 在提交後私有 receipt／最終回覆 |
| 接手定位 | `git log -1 --format=%H -- docs/plans/20261109-notes-environment-boundary-f1-handoff/Handoff.md`，再查其後產品及計畫 diff |

起始已有兩項工作：原任務 `progress.md` 是 tracked dirty，包含 02 進度及一處空白刪除；`reviews/v3-bdde2a0/plan-review.md` 是 untracked。後者是 Owner 指定交接來源。本輪撰稿期間，原 Session 以 `270bd5f712080a57ae857045071a9e22605a09a1` 完成兩項文件提交及推送，並補充既有進度的助手失敗紀錄、恢復原空白；本輪未覆寫它們。已核對新增提交只有兩份審查文件，plan／handoff／notes.py 及 Plan Review 原文 hash 未變；本輪交接以此提交為父基準，不將其當產品漂移，也不重複提交審查來源。本輪自有進度另放本目錄，接手仍須保留當時任何 dirty。

### 來源 SHA-256

前五個相對路徑位於 `docs/plans/20261108-notes-volume-identity-reattest/`。交接檢查確認與受審來源一致；Plan Review 以起始原文 hash 綁定；起始未提交，後由原 Session 完成 270bd5f 交付。

| 來源 | SHA-256 |
|---|---|
| `plan.md` | `7743d6f5910713e8e65540a8b1b6758cdf60f32d21898763b34df62c0e6bd75e` |
| `handoff.md` | `84c6de506a2f209fcdf62bbebfc84e9209ea10dd5dd7d49c673ba191ec61923e` |
| `planner-boundary-revision-report.md` | `bfcd78ba0cdac6392c59a9f1f1b6c6ea257718228055d06d0e000147ebec3ea2` |
| `reviews/v3-bdde2a0/simplicity-plan-review.md` | `e9b8da858e4aeb2ad7abc1de2a5e2a593633f9f488d3784469487aa6302f7698` |
| `reviews/v3-bdde2a0/plan-review.md` | `f41f873333754fbb5ce1809af5fdfcad15069d2103aeb44d880700d8c7ed407e` |
| `src/line_backup_batch/notes.py` | `0e542d73024f8f1b78238dcb9b331d890c89223281c5543f8acf45b7135aed7b` |

## F1 的工作與必要證據

行號以來源 hash 為準；後續按函式行為定位。計畫全貌仍以核准 plan 為準，不能只讀開頭 Prompt。

| F1 工作 | 現有 gate | 成功證據 |
|---|---|---|
| reattest staging／list | notes.py :2762–2770、:2800–2815、:2941–2956 | 合格環境項存在／改 bytes／新增／消失不造成空內容或集合誤判；未知 staging 仍拒絕；原 intent 認領不變 |
| reattest completion | :2867–2927 | 全部登錄媒體 witness 仍完整，環境 bytes 不參與；preview 純讀、confirm 精確單筆、replay 不重寫 |
| active／completion 投影 | :4026–4029、:4210–4235 | 第一支維持完成／LOCAL_VERIFIED；真缺檔／內容／身分漂移仍 LOCAL_CHANGED；整篇缺席 LOCAL_MISSING 且禁重下 |
| V1 可達部分 | 合成第一支完成＋第二支原 attempt＋OPEN_BATCH＋device-only drift | 覆蓋 witness 前後及 preview→confirm 之間環境變動；scope／媒體 witness 不變，保留原事件 raw bytes |
| V2 可達部分 | 兩個合成 Records session 讀同一帳本 | 無 UNKNOWN 的合法路徑與 UNKNOWN 禁重送分開；僅原精確批次＋fresh scan 可建 scoped v3，不偽造 STOPPED |
| V5 可達部分 | 真媒體漂移、未知項、異常同名／連結、碰撞、證據／帳本損壞 | 正例排除無關變化，負例說清保護物件與具體損害；不以「原測試要求」單獨證明拒絕必要性 |

正例適用範圍限 canonical 非 symlink 媒體容器內的精確 `.DS_Store`、regular、nlink=1、未引用／保留。受管理名稱與碰撞先判定。其他 dotfile、AppleDouble、Thumbs.db、未知檔、額外影片、特殊檔或分類失敗均不放行。不得新增分類資料格式、CLI、事件、狀態或新清理協議。

### F1 可寫路徑

- `src/line_backup_batch/notes.py`：只限上述判定及必要最小內部共用分類。
- `tests/test_notes_reattest.py`；必要才改 `tests/test_notes_records.py`、`tests/test_notes_restart.py`。
- 本目錄後續 `implementation.md`、進度追加、候選與檢查證據；原始證據留專案 `.local/line-backup/tasks/`。

F2 的 `tests/test_notes_regressions.py`／`test_notes_e2e_media.py` 及操作文件在完整計畫中獲列，但不因此成為 F1 順手擴做範圍。不得改 `AGENTS.md`、`daily.py`、相簿 Skill／Prompt、`notes_evidence.py`、Swift／媒體驗證器、事件／證據 schema、公共交易介面、舊 fixture 檔、真實帳本／active hint／媒體或工具鏈。

### F1 指定命令

在 repo 根執行，以專案新建 synthetic TMPDIR 隔離合成資料；選相符現有環境，不改系統設定。

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_records.py
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
```

Implementer 保存實際 argv／cwd／環境／exit／counts／stdout／stderr、精確候選 diff／hashes、合成前後清單及業務斷言。單次 fixture 成功、分類 helper PASS 不等於跨流程通過。F1 不預跑整套最終回歸，不以 mock 解碼簽發 V7。

## F1 後仍須交接的殘餘工作

| 後續責任 | 必傳內容與成功條件 |
|---|---|
| 07 implementation Simplicity，由 Owner 啟動 | F1 implementation.md、精確候選／diff、三項 suite 證據、V1／V2／V5 覆蓋、殘餘 gate；即使 F1 為最終候選也適用 |
| 後續 Implementer F2，僅人續交且有剩餘工作時 | 新 intent :4709／:4798、inventory :6560–6580、普通發布 :5452–5459／:5598–5601、收尾 :5720–5725、restart :5894–5896 與 candidate／activation 重讀、跨 Session 整合、指定衝突文件 |
| V3／V4 | 普通及 restart 各有業務案例；三次採樣／manifest 只含媒體。已發布後只剩合格環境項的 staging 保留 bytes、正常 completion／讀回、無假 pending／額外派送；不刪檔 |
| V5／V6 完整覆蓋 | 真媒體與未知項／碰撞仍拒絕；原單次、第二次漂移、replay、stale tip、鎖、scope／generation、fresh scan、防重送、0／2／4／70 語意不變 |
| V7／V8 | 沿 e2e_media 用 production verifier、成對 Homebrew ffmpeg／ffprobe 與原 ImageIO；截斷影片仍拒絕。依 plan 最終候選跑完整最小回歸、指定文件只修記事本衝突文字，正式 Prompt 不增加步驟 |
| V9 真實日常及獨立接受 | Owner 用手冊記事本正式 Prompt＋有效前景另啟；保留第一支並查第二支真實狀態。真實 reattest 仍需精確同意。保存實際派送／outcome／發布／新 Session 記憶，獨立者映射 V1–V9；不是本輪或 F1 授權 |

最終完整回歸由後續 Implementer 依計畫執行一次：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

## 已知、未知、風險與停止

事實：v3 兩份計畫審查 PASS；Owner 本輪核准交接實作；notes.py 仍是未修根因的基準。現場刪除單一環境檔是根因報告的歷史事實，本輪沒有再刪或重跑 preview。舊 preview／confirm 已存在，不應重做。

推論：相同環境項可在多個後段 gate 再阻塞，所以完整修正必須保持同一分類邊界；F1 只是首個可驗證切片。靜態可達分析不是每個 gate 的實機重現。

未知：device 漂移原因、外部 writer、第二支是否晚到、當前 attempt／來源／OPEN_BATCH 適用性、修正後實際接續及跨模型重用。records lock 不鎖 Finder／LINE；不承諾原子整樹快照、未知下載已停止、GUI exactly-once、OS 隔離或服務端原始位元一致。

缺來源／版本衝突／身分歧義／寫入衝突／未明派送／schema 無法滿足／必須擴路徑、分類、scope 或授權均停交人決定。普通範圍內機械修正可依 04 進行，但不得跨正式角色自動修復或重測。同根因至多三次有證據嘗試；兩次連續無新資訊即停，換 Session 不重置。exit 70 應留證停止，不能據此重送、改帳、換路徑或改入口。

## 本輪檢查與交付狀態

本輪只完成交接、核准記錄及文件核對；產品測試、V1–V9、解碼、真實交易、LINE／下載、真實跨 Session 與獨立接受全部 NOT_RUN，無新增 OBSERVED。文件檢查 argv／exit、來源／保留 hashes 及最終 commit／push receipt 存 `.local/line-backup/tasks/notes-v3-f1-handoff-20261109/`。最終文件檢查 12／12 PASS、exit 0；191 份其他來源 bytes 不變，外部進度與 270bd5f 完全一致，git diff --check exit 0。首次保留檢查 exit 1 的外部進度變動已保留紀錄並釐清；未改寫失敗。所有 checks 只證明文件／來源一致，不能冒充產品接受。

```text
PRIMARY_OUTCOME_STATUS: APPROVED_V3_F1_HANDOFF_PREPARED
IMPLEMENTATION_STATUS: NOT_STARTED; NO_PRODUCT_CHANGES_THIS_TURN
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_SECOND_VIDEO_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: DOCUMENT_CHECKS_ONLY; PRODUCT_V1_V9_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN; PLAN_REVIEWS_ARE_NOT_PRODUCT_ACCEPTANCE
TASK_CLOSURE_STATUS: NOT_DONE; IMPLEMENTER_F1_AND_LATER_GATES_PENDING
```

接手須收到本文件全文、Owner 原請求及本輪核准、精確 v3 plan／Planner handoff／兩份 review／Planner 修訂報告／根因報告、交付 commit／diff、來源 hashes、04 Prompt、AGENTS.md、同版本 policies。第一動作是 Git 與來源核對，之後才做 F1。完成 F1 後交付 implementation.md 與精確證據並停待人啟動 07，不自行開始 F2 或實機備份。
