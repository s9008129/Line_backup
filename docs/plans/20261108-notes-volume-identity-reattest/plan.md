# 記事本 list directory 重新見證計畫（草案 v2）

## 決策摘要

角色結論：`PLAN_DRAFT_COMPLETE`。本文件是待審設計，不是計畫核准、產品實作或真實資料操作授權。

目標是為已診斷的 `CURRENT_NOTES_LIST_DIRECTORY_CHANGED` 提供一條**精確確認、追加事件、僅轉接目前 list directory binding** 的恢復路徑。現有事故有已確認但未 activation 的 `OPEN_BATCH`；新設計保留該批次，重新完整 recovery scan 後，讓其合格 v3 intent 可通過 directory gate，其他 gate 仍須各自成立。

分級為 **CRITICAL**：雖然程式範圍小，新增持久事件與可解除原有目錄拒絕的信任轉接涉及防重送及資料完整性。草案 v1 已獲計畫 Simplicity Review PASS，但獨立 Plan Review 判定 REVISION_REQUIRED（B1）。兩份歷史報告保留原樣，不自動涵蓋 v2；由 Owner 決定適用重審並另開主 Session。本 Planner 不派送下一正式角色，實作與 acceptance 仍未開始。

本次使用者已啟動 Planner 並授權文件 commit／push，且明示選擇「先停下來回報，這版只處理第一次變號」。v2 因此限制每份帳本至多一筆重新見證事件，不保留連續轉接能力。此選擇不是接受下述 witness-based 信任模型、計畫核准、實作或真實 binding 轉接授權；這些仍待人工決策。草案版本為 v2，首版產品協議與 schema 仍稱 v1。

## 基準、來源與寫入邊界

| 項目 | 身分／範圍 |
|---|---|
| Repo／worktree | `/Users/hsiaojohnny/dev/Line_backup`，使用目前主 worktree；不整理其他 worktree |
| 分支／本輪初始 HEAD | `feature/line-notes-media`／`0edf5cff88bb605b5c4608990ea6924c0d424e75`；v1 原始規劃基準為 `9027d8ea4df41480b785017a7c57a39813907e65` |
| 初始 Git 狀態 | `git status --short` 與 `--porcelain=v1` 無輸出；無需納入的既有 dirty／untracked 成果 |
| 主要證據 | 同目錄 `issue-analysis.md`、`problem-report.md`、`progress.md`，以及 `plan-review.md:43` 的 B1；原診斷校正原提報對 remount 的確定語氣 |
| 產品定位 | `notes.py` 的 `_current_destination_state()`、`_require_current_list_directory()`、事件驗證／graph、restart 與 scan gates；不是相簿路徑 |
| 本輪可寫 | 修訂本目錄 `plan.md`、`handoff.md`，新增 `planner-revision-report.md`，只追加 `progress.md`；私有產物放 `.local/line-backup/tasks/notes-volume-plan-20261108/planner-revision-b1/` |
| 本輪禁止 | 產品、Skill、手冊、測試、帳本、active hint、照片影片、原提報、原診斷、v1 planner-report 與兩份審查報告；不操作 LINE、不跑真實 notes 交易、不建立 intent |
| 待核准的實作路徑 | 僅 `src/line_backup_batch/notes.py`、新增 `tests/test_notes_reattest.py`、必要的 `tests/test_notes_restart.py`／`tests/test_notes_regressions.py`／`tests/test_notes_locks.py`；下列記事本文檔 |
| 待核准的文檔路徑 | `.agents/skills/line-notes-agent-cua/SKILL.md`、其 `references/download-and-ledger.md` 與 `references/verification-and-recovery.md`、`docs/LINE相簿備份_使用手冊.md` 的記事本說明 |

後續也不得修改 `daily.py`、相簿 Skill／Prompt／公開介面、`image_decode.swift`、`notes_evidence.py`／既有證據 schema、媒體驗證器、舊 fixture 或歷史事件。若既有 evidence 或交易原語不足，先提出具體缺口給人決定，不自行擴大路徑。

本輪沒有直接重查真實帳本或媒體。診斷記載的 28 events、2 個 v2 intents、1 completion、0 個 v3 intents、空 UNKNOWN staging 與 matching witness 均是**前輪證據**；不是本輪新觀察，日後真實 preview 必須重新取證。

## 方案取捨與信任目標

| 方案 | 取捨／決定 |
|---|---|
| 維持拒絕且沒有新入口 | 最少變更但無法接續本事故；保留為 Owner 不接受信任轉接時的結果 |
| list-only、現有 OPEN_BATCH、device-only 轉接 | **採用的草案**；只增加必要協議，舊 completion／candidate／staging guard 不變 |
| 每帳本一次轉接，第二次漂移停止 | **Owner 選定的 v2 能力界線**；原 witness 可直接比較，無須建立轉接 witness 鏈；代價是再次漂移須保留阻塞另議 |
| 支援連續轉接並追蹤最新 witness | 本版不採；需新增基準遞推、事件鏈與連續漂移驗證，Owner 已選較小範圍 |
| 全層 reattestation／通用 attestation 框架 | 不採；擴大舊 UNKNOWN、candidate 與發布的信任面，本事故未證明需要 |
| 忽略 `st_dev`、手改 ledger、換 destination／空帳 | 不可採；解除既有保護或改寫歷史 |
| 現在加 UUID、nonce 或 volume 指紋回證過去 | 不採；沒有歷史對照，不能補造同一實體物件的連續性 |

精確宣稱是：「目前同 canonical path、同 inode 的列表目錄及所列舊完成 witness 相符；Owner 接受把目前 list binding 轉接至這次觀測的 device。」**不宣稱**已證實 remount、同一實體 volume、排除 inode 重用或 byte-identical clone、服務端原始位元一致，亦不提升舊檔案的本機可用性。

若 Owner 的必要條件是排除完美 clone，本案既有證據不足，應保持 `BLOCKED`，不實作成可成功的放行選項。可辨識的 inode／內容／名稱／時間差異一律拒絕；不可辨識且全部 witness 相同的 clone 屬必須明示接受的剩餘風險，不能同時承諾自動識別並拒絕它。

## v1 適用範圍與 witness

先限制於本事故形狀，避免在首版處理所有歷史資料布局：

1. 帳本／註冊／事件鏈與既有 evidence 完整，當前 session 已合法 bind；恰有一個尚未 activation 的 restart confirmation。其精確 scope、generation、version 路徑及額外空間確認保持不變。
2. 該帳本尚無任何 v3 intent、restart-copy-plan、restart-candidate 或 restart-activation，也沒有未完成的普通 publish plan。若已進入這些階段，回報 v1 不支援並停止，不重認這些物件。
3. 現行 photo root 與 list directory 都存在、canonical、逐層無 symlink、仍在既有專案照片邊界；list inode 與有效舊 binding 相同，device 不同。inode／path 變動、路徑外移不屬本方案。device 相同回 `NO_CHANGE`，不建立確認。
4. 至少一個本 list directory 下、由 v2 intent 產生的 completion 具完整舊 witness；所有這類 completion 都必須參與，不能只選一個成功檔。現有 completion schema 本來就是 `line-notes-completion/v1`，不能以此誤判為 legacy；本版拒絕的是來自 v1 intent 的舊交易、缺 witness、完成目錄缺席或非支援布局，原 `LOCAL_MISSING`／保護事實仍保留。
5. completion 目錄應是 list 的直接子目錄。每目錄的實際名稱集合精確等於其中 completion 的 target 名稱聯集；檔案為 regular、`nlink=1`、非 symlink，path、inode、size、mtime_ns、ctime_ns、SHA-256 全同，只容許 device 依相同 old→new 對應變化。目錄 inode 同舊值，current device 同新 list device。使用無追蹤讀取及 hash 前後 stat／path 身分檢查。
6. list 層精確允許集合為：上述完成貼文目錄，加上帳本既有 v2 intent 所登錄且目前仍存在的 staging。完成後已移走的舊 staging 可以不存在；未解 attempt 的 staging 必須存在且為 canonical、同舊 inode、目前 device 為新 device，**內容為空**。只有 intent 登錄的目錄可列入，不以 `.line-notes-incoming-` 前綴認領。空白只描述這次 witness，絕不證明下載停止。其他檔案、`.DS_Store`、外來／額外目錄或 `versions/` 首版均拒絕，不刪除它們。
7. 未解的 v2 attempt 僅可屬於既有 confirmation scope，且只作封存狀態與結構觀測；scope 外 unresolved、scope 外 `LOCAL_CHANGED`、未完成 naming、未知物件／共享路徑歧義都拒絕。不得 blanket 拒絕所有 UNKNOWN，否則本事故仍無恢復路徑。
8. **整份帳本歷史沒有任何 `list-directory-reattest` 事件，才能建立首次 preview／新確認。** 限額不是每 session、batch、destination 或 binding 一次；後續 destination 不重置。若已有事件，新的 preview 或非精確 replay 的 confirm 一律以 exit 4、`REATTEST_UNSUPPORTED_STATE` 停止，附既有 event_ref 與「首版只支援一次轉接」說明；不建立第二筆。精確 replay 是查回，不是新轉接，依下節優先處理。

這是有意的能力界線；前輪沒有列出全 list 子項集合，故不能預填真實資料必定符合第 6 點。未來 preview 若拒絕，保留具體差異後交人決定，不在日常任務擴充支援布局。

## CLI、資料結構與確認協議

下列為**新增介面草案，現行 CLI 尚無這些命令，本輪不得執行**。沿用 `--preview @檔案` 及 v2 evidence bundle，不要求 Owner 填 key、JSON 或 UUID。

```text
notes reattest preview --records-root R --session-id S
notes reattest confirm --records-root R --session-id S --preview @P --evidence E
```

Agent 將 stdout 保存為專案私有 preview JSON，向 Owner 用白話展示列表、舊／新 binding、witness 摘要、未解狀態、既有 restart scope、新版本路徑與剩餘風險；Owner 必須明示接受這個精確轉接。既有 restart 同意、一般「繼續」或 Planner 啟動不是 reattest 同意。Agent 自行建立 v2 evidence：list_key context，其餘 context 保持既有 UNKNOWN 正規化；statement 保存 Owner 實際同意的來源與 preview digest，並用 `command_stdout` asset 封存精確 preview。CLI 驗 bundle／asset bytes 與 context，不能替人證明同意語意。

### 精確結構

序列化與 SHA-256 均沿用現有 `encoded()`／`digest()`；物件拒絕額外或缺少欄位，整數拒絕 bool，hash 為小寫 64 位 hex。`ref` 一律是既有 `{sequence, sha256}`，其 hash 語意沿用 `_event_ref()`；事件鏈仍使用原始 event bytes 的前序 hash，不互換兩者。

| 結構 | 固定欄位及規則 |
|---|---|
| `binding` | `{photo_root, list_directory, directory_device, directory_inode}`；canonical absolute paths 與嚴格 int |
| `root_snapshot` | `{path, device, inode}`；目前觀測，只用於本 preview／confirm 穩定性，不冒稱已有歷史 root witness |
| `open_batch` | `{confirmation_ref, restart_id, generation, scope_digest}`；均精確引用唯一既有 confirmation |
| `witness` | `{schema, completions, staging}`；schema=`line-notes-list-witness/v1`；兩陣列按相對 path 排序，完成同 path 再按 completion sequence 排序，無重複 |
| `completions[]` | `{completion_ref, directory_before, directory_after, file_before, file_after}`；directory 為既有 `{path, device, inode}`；file 精確欄位為 `{name, device, inode, size, sha256, mtime_ns, ctime_ns}`，before 逐字取 completion.target_file、after 取當次觀測；檔案 path 由 directory.path＋name 推導，regular／nlink=1 為讀取時必要條件 |
| `staging[]` | `{intent_ref, path, state, directory_before, directory_after, children}`；state=`PRESENT_EMPTY` 或 `ABSENT_COMPLETED`；前者 before 取 intent path/device/inode，after 為當次同形狀，children=`[]`；後者只限已完成 intent，after=`null`，children=`[]`，before 保留原值 |
| `scope` | `{list_key, root_snapshot, old_binding_ref, old_binding, new_binding, open_batch, witness, witness_sha256, trust_policy}`；witness_sha256=`digest(encoded(witness))`；trust_policy 固定 `OWNER_ACCEPTED_WITNESS_TRANSITION_V1` |
| preview JSON | `{schema, status, session_id, expected_tip, scope, preview_digest, dispatch_authorized, external_copy_verified, real_line_e2e}`；schema=`line-notes-list-reattest-preview/v1`；status=`CONFIRMATION_REQUIRED` 或 `NO_CHANGE`；後三值固定 false、false、`NOT_TESTED` |
| preview_digest | `digest(encoded({schema, session_id, expected_tip, scope}))`；不把 status 等呈現欄位混入摘要 |
| 新事件 | kind=`list-directory-reattest`；data 精確為 `{schema, session_id, expected_tip, scope, preview_digest, evidence}`，schema=`line-notes-list-reattest/v1`；confirmation 的唯一鍵為 preview_digest，不另增 UUID |

`directory_before/after` 的 path 一律相同，file before/after 除 device 外全同。每份 old device 都必須等於 old_binding device，每份 new device 必須等於 new_binding device；不接受任意多 device mapping。old_binding_ref 只可引用當時有效的 created／destination，不可引用 reattest。before 仍直接取原 completion／v2 intent；本版不遞推前次 after，也不將 witness 覆寫為 replacement manifest。首次若原 device 已不一致，仍拒絕，不因一次限額放寬 witness。

### preview／confirm／replay

| 階段 | 前置、效果與停止點 |
|---|---|
| preview | 既有 records lock 中載入／驗帳，檢查 session；若歷史已有 reattest，先拒絕（包括目前未漂移，不回 NO_CHANGE）。否則檢查狀態與路徑，建立完整 witness，重查物件身分／名稱集合穩定；不追加事件、不保存 ledger evidence、不建目錄、不改 active hint。只有 shell 重導向輸出寫私有檔。lock busy 屬唯讀，可回 retry_safe=true |
| 首次 confirm | 鎖內重新載入，核對 session、expected_tip、old_binding_ref、open_batch 與全部 digest；重新讀取完整 witness，須與 preview 完全相符，再驗精確 v2 evidence／preview asset；不接受過期 preview |
| 寫入順序 | 通過所有檢查後保存 evidence，重查最後的目錄／名稱／metadata snapshot，再以既有 create_json／append 原語追加單筆事件；重開讀回事件、驗 graph／有效 binding，回 `CONFIRMED`、replayed=false、event_ref。成功才向 Agent 報告轉接成立 |
| 精確 replay | confirm 先驗帳與 current session，再找相同 preview_digest；event 內容、scope、原 session 與 evidence ref 必須全同。此分支先於「已有 reattest」及首次 confirm 的 stale-tip／無 v3 適用檢查，才能在確認後查回；不可略過帳本完整性或 current session。可由新 session 查回原確認，結果列 original_session／current_session；不新增 evidence／事件，不改原 session，不把查回當成新 Owner 同意。不同 evidence 或同鍵不同內容依既有衝突 reason 拒絕；沒有精確匹配且已有 reattest，回 REATTEST_UNSUPPORTED_STATE |
| replay 的現況限制 | 完成事件可回讀，但必須另外檢查目前 list guard；若再次 drift 回 `REATTEST_CURRENT_BINDING_CHANGED` 並附既有 event_ref，保留原確認、不回稱現在可用。歷史 witness 不因日後新增合法 staging 而重新認證；replay 不建立 intent、scan 或 GUI |
| NO_CHANGE | preview scope 仍列目前 binding 與狀態，witness 可省計算但結構固定為空陣列與其 digest；confirm 拒絕 `REATTEST_NOT_REQUIRED`，不將正常 binding 加入歷史 |

為避免 replay 規則矛盾，呼叫的 `--session-id` 不要求等於舊 preview 的 session_id；**首次 confirm** 要相等，**找到既有精確事件後的 replay** 允許不同 current session，但原 preview／原 data 不變。原 evidence 只能查回，不能由另一份 bundle 替換。

### 拒絕與退出碼

保留既有 0／2／4／70 語意。0 僅代表 preview／confirmation／查回成功；`dispatch_authorized=false` 不變。缺必填或無效 JSON 為 argparse exit 2；已知業務拒絕 exit 4；未預期錯誤 exit 70、`INTERNAL_ERROR`／`UNEXPECTED_EXCEPTION`，停止，不作重試依據。

新增 exit 4 reason 固定為：`REATTEST_NOT_REQUIRED`、`REATTEST_OPEN_BATCH_REQUIRED`、`REATTEST_UNSUPPORTED_STATE`（已進入 v3／candidate／pending naming 等）、`REATTEST_BINDING_CHANGED`（path／inode／mapping）、`REATTEST_NO_WITNESS`、`REATTEST_WITNESS_CHANGED`、`REATTEST_UNSUPPORTED_LAYOUT`、`REATTEST_SCOPE_BLOCKED`（scope 外異常或身分歧義）、`REATTEST_EXPECTED_TIP_CHANGED`、`REATTEST_PREVIEW_CHANGED`、`REATTEST_CONFIRMATION_CHANGED`、`REATTEST_EVIDENCE_MISMATCH`、`REATTEST_CURRENT_BINDING_CHANGED`、`REATTEST_READBACK_FAILED`。既有帳本、session、evidence、lock 錯誤沿用既有 reason；不全包成可重試新錯誤碼。

`REATTEST_UNSUPPORTED_STATE` 不得用於 blanket 拒絕 scope 內舊 v2 UNKNOWN；`REATTEST_SCOPE_BLOCKED` 也不能替 UNKNOWN 產生 STOPPED。拒絕應附不含原始媒體 bytes 的差異分類及事件引用，私人細節留私有輸出。

## 投影、相容性與 OPEN_BATCH 接續

新增單一有效 list binding resolver，按事件序列處理 created／destination／list-directory-reattest。created／destination 開始一個 binding；唯一 reattest 的 old_binding_ref 必須指向該時點有效的 created／destination，路徑不變、old_binding 值一致，new device 不同且 inode 相同。之後 destination 正常開始另一個 binding，不讓舊轉接洩漏到新路徑；但整份帳本的一次限額不重置。歷史 resolver 必須用指定序列的 prefix，不能用最後一筆去解釋以前的 intent。

新事件 validator／graph 只按歷史 prefix、嵌入 witness、confirmation ref、前序 tip、digest 與 evidence 驗證合法性，不用今天的檔案存在與否決定歷史事件是否有效。`expected_tip.sequence` 必須等於新事件 sequence−1；open_batch 當時尚未 activation、尚未進入 v3、prefix 尚無任何 reattest 等適用性也以 prefix 驗證。第二筆 reattest 即使 payload 相同、換 batch／destination，或 old_binding_ref 指前一 reattest，均屬非法帳本，必須在載入 graph 時拒絕；不是可接受 replay。`evidence-audit` 收入唯一新 evidence 引用。

`_current_destination_state()` 保持既有路徑／destination 語意；`_require_current_list_directory()` 改用有效 list binding 比 device／inode。completion、candidate、staging、publish 與 availability 的 device 比較仍讀原事件，不使用這個 resolver。舊帳本沒有新事件時結果完全相同；舊 binary 讀到新 kind 仍拒絕 `UNKNOWN_NOTES_EVENT_KIND`，所以是**新 binary 可讀舊帳本，不保證舊 binary 可讀新帳本**。首次真實寫入前必須確認後續 session 使用相容版本；不以刪事件回滾。

只新增兩個必要 scan freshness gate：使用到 reattest binding 的 `_restart_intent()` 與 `_validate_restart_scope_current()`，要求本次完整 recovery scan 的 START sequence 晚於該 binding 的 reattest event，並保留晚於 restart confirmation、current session、coverage、媒體 identity 等原有要求。沒有 reattest 的帳本維持舊規則。這是必要的防止沿用轉接前舊盤點，不改 scan event schema。

| 狀態／事故階段 | 行為與不變量 |
|---|---|
| 已有 OPEN_BATCH | 保留 restart_id／confirmation_ref／scope_digest／generation／targets；reattest 是另一個獨立確認，不重跑 restart confirm，不開第二批 |
| confirm 之前／之後的舊 scan | 原事件全留；reattest 後若 scan 仍開啟，按既有 interrupt，再 start --recovery，重做頂底、重疊、post detail 與 media inventory |
| 舊完成目前 LOCAL_CHANGED | 保持舊 completion 與 LOCAL_CHANGED；只有原 restart 精確 scope 按既有 copy／new version 路徑處理，不升格 VERIFIED_PRESENT |
| scope 內 v2 UNKNOWN／無 outcome | reattest 不解除、不重認 staging；後續 v3 eligibility 完全依既有精確 restart 規則，非一般 intent／verify 解鎖 |
| scope 外 unresolved／LOCAL_CHANGED | v1 preview／confirm 拒絕，後續 dispatch gates 也保留 |
| LOCAL_MISSING／EXCLUDED／PROTECTED_HISTORY | 不取得重下資格；本轉接缺完整 witness 或布局不支援時保留阻塞 |
| candidate／pending naming／版本目錄 | 不在 v1 轉接範圍；已有時停止，不能用新的 list binding 重新認領 |
| 來源／scope／路徑／版本策略改變 | 原 restart 授權不足；停止交人決定，不刪舊 batch 或沿用其 scope |

確認 binding 後仍不得承諾下一個 intent 必定成功：前輪只定位最早 gate，其他 gate 未驗證。若新證據顯示必須修改 completion、staging 或 restart scope，停止在具體 gate，另提有界擴案。

## 交易、競態、crash 與回復

沿用每帳本既有鎖及 append 原語，不新增控制器／外部服務。lock 只序列化遵循它的 CLI；不鎖 LINE、Finder、其他帳本或任意外部 writer。不宣稱 OS 隔離、原子檔案系統快照或 exactly-once。

完整 witness 在 preview 與 confirm 各讀一次，confirm 讀取時驗 hash 前後 fd stat 與 path identity，整體重列名稱並核對節點 metadata；不做無限重讀。任何可見漂移立即拒絕。最後 metadata 核對到事件提交間仍有有限競態窗，不能抵抗惡意換回或不遵守鎖的 writer；Owner 確認時需讓來源目錄停止人工修改，但不能將此寫成平台強制保證。其他帳本路徑衝突只要被發現就拒絕，本版不宣稱跨所有帳本的原子所有權認證。

| 中斷／衝突 | 必要結果 |
|---|---|
| preview 後 tip、witness 或 batch 改變 | 首次 confirm 拒絕；不寫成功事件，不自動換 preview 接受原同意 |
| 同 preview 並行 confirm | 同鎖序列化；最多一筆新事件，第二筆精確 replay；不同 payload 拒絕 |
| evidence 保存後、event 前 crash | 可能留無事件引用的 immutable evidence；不投影成功、不清理、不建立 intent；後續先查證再決定是否重新精確確認 |
| event 完整保存後、回覆前 crash | 新 session 可用原 preview／evidence 精確查回；不追加第二個事件、不派送 GUI |
| event pending／半寫／readback 失敗 | 保留痕跡，`REATTEST_READBACK_FAILED` 或既有完整性拒絕；不得當作未寫入重送。若既有原語無法滿足，回報不足，不修改其通用語意 |
| 確認後再次 device 漂移 | 現行 guard 繼續拒絕，無論是否已有 v3 都停止。新 preview／非精確 replay confirm 回 REATTEST_UNSUPPORTED_STATE；原精確 replay 回 REATTEST_CURRENT_BINDING_CHANGED 並附原 event_ref。不新增確認、evidence、scan、intent 或 staging，不要求再次同意作為本版繞過；保留原件另交 Owner 決定 |
| 版本回退 | 未寫新事件前可回到舊 binary；寫過後保留 ledger 與檔案，以相容新版唯讀查證／停用新命令，不回寫歷史或復原成舊空帳 |

每個根因沿用既有最多三次有證據嘗試、連續兩次無新資訊即停止的限制。原事故拒絕不因新 session 歸零；本輪規劃沒有增加真實下載／恢復 attempt。

## 成功條件、切片與檢查責任

### 人工關卡

1. Owner 已選每帳本一次轉接；其餘 trust／核准仍待決定。因 v2 是實質能力收斂，由 Owner 決定是否重做 **Simplicity Reviewer（plan）**，不把 v1 PASS 轉成 v2 PASS。輸入為本文件、handoff、v1 兩份審查、修訂報告、診斷與精確 Git 候選，不啟動實作。
2. CRITICAL 的 **獨立 Plan Reviewer** 必須由人另開主 Session 重審 v2，核對 B1 的每帳本一次限制、精確 replay、schema、舊 binary 限制、OPEN_BATCH 與測試矩陣。B1 尚未獨立接受；拒絕時記證據並停止，不由本 Planner 修產品。
3. Owner 核准後另啟動 Implementer，只做首切片，然後由人啟動 **Simplicity Reviewer（implementation）**。
4. 人決定是否讓 Implementer 完成其餘切片。獨立 acceptance 檢查候選與需求；真實試用仍用手冊記事本正式日常 Prompt，不以 Acceptance／E2E 角色 Prompt 取代備份入口。

### 首個可驗證切片 S1

僅新增 read-only `reattest preview`、共用的 bounded witness builder、相應 CLI／lock 分類及 `test_notes_reattest.py`。此時不註冊新 kind、不改有效 binding、不提供可寫 confirm。合成案例應重現本事故形狀：v2 intent 的 completion＋v2 UNKNOWN＋已確認 restart＋device drift；preview 顯示 `CONFIRMATION_REQUIRED`，帳本、active hint 與照片樹內容清單不變。

目標命令（**尚未執行**）：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_reattest.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_locks.py
```

S1 完成不是產品修復。首切片審查後，S2 才加入 confirm、事件驗證／投影、每帳本一次與 replay 分支、fresh scan gates、整合測試與 Skill／references／必要手冊說明。含既有 reattest 的可載入 fixture 與第二次轉接拒絕驗證屬 S2；S1 不為測試而提早註冊新 kind。不把 S1 或 S2 自評當獨立 acceptance。

### 必要驗證矩陣

下表是未來要求，除本輪文件核對外全部 `NOT_RUN`。Implementer 只用隔離 synthetic 目錄，不改真實帳本或假裝掛載；原始 log、exit、候選 HEAD、檔案 hashes 與前後清單保存在專案私有任務目錄。

| ID／必要檢查 | Owner／通過證據 | 停止條件 |
|---|---|---|
| P1 文件與 scope | Planner；草案齊全、來源／SHA-256、git diff --check、產品 diff 空 | 缺基準、越界或私資外洩停止交付 |
| T1 preview 純讀 | Implementer；合成合法 device-only／NO_CHANGE、完整名稱集合與前後內容清單；無 event／staging／active hint mutation | 任一成功副作用或漏收 witness 即拒絕候選 |
| T2 witness 負例 | Implementer；逐一測 inode、hash、size、mtime、ctime、symlink（含祖先）、hardlink、缺／額外檔、未知／非空 staging、空 witness、不同 device mapping、scope 外異常 | 不符仍成功、只取部分 witness 即 FAIL |
| T3 事件／相容 | Implementer；嚴格 schema、prefix graph、event_ref／raw hash 分離、old ref 錯配、跨 list key、fork／缺 evidence 拒絕；第二筆 reattest（含相同 payload、old ref 指前一 reattest、其間有新 destination／batch）皆在 graph 拒絕；合法第一筆不受日後漂移失效；舊 v1 fixture／v2 replay 結果不變；舊 binary 拒新 kind 的限制明示 | 不合法事件可投影、歷史被 current FS 重新判失效即 FAIL |
| T4 確認／競態 | Implementer；stale tip／witness、兩個 process 同時 confirm、衝突 payload、不同 evidence、hash 中替換、再次 drift、寫前／寫後／讀回故障注入；證明最多單筆事件且無下載副作用 | 任何模糊提交後自動補寫、重送或覆蓋即停止 |
| T5 本事故整合 | Implementer；保留 OPEN_BATCH 精確 ref／scope／generation；轉接前舊 scan 仍拒絕；新 recovery scan 後合格 scoped v3 intent 建新空白 staging、原 completion／UNKNOWN／availability 不變；另測 scope／來源改變仍拒絕 | 需要改 batch／舊 staging／completion 或 scope 外放行即停止擴案 |
| T6 帳本查回／audit | Implementer；新 session 精確 replay 不增事件；新增事件被 evidence-audit 正確涵蓋；summary 六類與四類本機計數規則不變 | audit／讀回失敗不可宣稱可信業務投影 |
| T7 最小全回歸 | Implementer；下列三條命令當次 exit 0 與實際 counts，不引用前輪 PASS | 任一失敗報 evidence 停止，不能調低 exit 70 邊界 |
| T8 受控 macOS volume | Owner 另授權獨立驗證者；只在專案測試資料／測試 volume，記錄實際 device 是否變化及完整流程；不得卸載工作 volume | 無工具／未獲授權為 NOT_RUN；若 device 沒變只記 OBSERVED，不能稱重現本事故 |
| T9 真實日常／跨 Session | Owner 以正式記事本 Prompt＋前景啟動，另精確同意真實 reattest；保存 preview→confirm→新完整 scan→合格 intent→GUI 單次→outcome→解碼／candidate／activation→新 session memory 證據 | 前景中斷、未知副作用、scope／身分變動停止；未測 chooser／混合附件等維持 NOT_RUN |
| T10 獨立 acceptance | Owner 啟動獨立主 Session；逐條映射 P1／T1–T9／T11 的候選版本及未測範圍，分開簿記、檔案、OBSERVED 與真實 E2E | 任何適用要求缺證據不得 DONE；不由協作者或 commit helper 接受 |
| T11 B1 單次轉接邊界（S2） | Implementer；完整合成序列 D0→D1 確認→任何 v3 前 D1→D2。第一筆成功，第二次 preview／新 confirm 均 exit 4 REATTEST_UNSUPPORTED_STATE；精確原 replay exit 4 REATTEST_CURRENT_BINDING_CHANGED 並附原 event_ref；第一筆歷史仍合法。D1 未漂移時原 replay 成功且不加事件，新 preview 仍拒絕；舊 preview 配不同 evidence 仍衝突拒絕。換 session／destination／batch 不重置限額；後續已進 v3 的再次漂移同樣停止。記錄每條拒絕前後事件、evidence、媒體樹與 active hint 清單相同 | 任一第二筆轉接、拒絕分支寫入副作用、漂移 replay 宣稱當前可用、把 replay 當新授權即 FAIL；D1 新 recovery scan 前仍拒絕 intent，D2 不因重掃／同意解除 guard |

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

T5 的 synthetic v3 intent 只驗簿記與路徑，不操作 LINE；真實完整解碼仍用既有 ImageIO 與成對 Homebrew ffmpeg／ffprobe，不改系統工具鏈。測試必須分清「matching clone 在本信任模型下無法區分」與「可偵測差異必須拒絕」，不能造出不存在的 clone detection PASS。

## 非目標、未知與停止交接

不追溯 OS remount 原因、不補造第三次下載、不合併 Owner 兩本記事本與 scan 兩篇貼文語意、不為原歷史造 observations ledger、不實作連續轉接／witness 鏈／一般空帳／全層／部分重新見證、不做媒體搬移／清理、不新建 controller／daemon／雲端服務、不把開發計畫變成日常啟動依賴。

仍未知：device 改變的真正原因、同一物件連續性、舊 UNKNOWN 是否晚到、真實 root 的完整允許集合、轉接後其他 gate 能否通過、controlled mount 是否重現、LINE 與跨 Session 的實際可用性。這些未知限制對外聲明；不阻止提交具體待審草案，但不能當成已解。

若必須超出上述 writable paths、增加跨帳本鎖框架、修改證據 schema／相簿介面、認領舊 staging／candidate、擴 restart scope、刪／改舊 confirmation、略過 device／witness、宣稱可排除 clone 或操作真實資料，停止並交 Owner 決定。獨立審查拒絕或必要驗證阻塞時保留已證實成果，不自啟跨角色修復／重測／結案。

## 初始狀態（本輪 Planner）

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_STARTED; PRODUCT_UNCHANGED
CORE_ACCEPTANCE_STATUS: BLOCKED; ORIGINAL_BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_DOCUMENT_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_REVIEW_OF_V2
```

v2 文件檢查結果見 `planner-revision-report.md` 與私有交付紀錄；`planner-report.md` 是 v1 歷史。下一步由 Owner 決定適用的 Simplicity 重查並另啟動 CRITICAL 獨立 Plan Review；本角色到草案交付為止，不宣稱 B1 已獨立通過。
