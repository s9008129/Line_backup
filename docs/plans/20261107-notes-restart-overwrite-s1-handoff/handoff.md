# 給下一位 Implementer 的精準啟動 Prompt（由 Owner 親自提交）

```text
請在 /Users/hsiaojohnny/dev/Line_backup，以 /Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md 擔任 Implementer，只完成記事本中斷恢復計畫的 S1 離線首切片。

我採納 c3c8827cea817db633736d9f8303c43f454fa7cd 的 plan.md 三項預設：
1. 恢復以單一列表內需要重新開始的受影響貼文為批次，每篇涵蓋全部可備份照片／影片，包含同篇既有完成項；其他正常完成、純 LOCAL_MISSING、排除及受保護項不因批次解除。
2. 新實體版本路徑在完整驗證後成為目前結果；舊原件留原位，舊 UNKNOWN／completion 保留，不原地覆寫、搬動或刪除，接受有界重複傳輸。
3. 真實恢復批次的明確確認可涵蓋同範圍完成前再次中斷；來源／身分／範圍／目的地策略改變須重新確認，歷史嘗試限制不重設。
我授權依此設計實作並驗證 S1。這是開發授權，不是任何真實批次的下載／取代同意，沒有 LINE／CUA 操作或真實帳本／媒體處置授權。

先完整讀取 docs/plans/20261107-notes-restart-overwrite-s1-handoff/handoff.md，按其版本表與來源清單取得原 plan、Planner handoff、Owner 意圖、計畫 Simplicity Review 及獨立 Plan Review。plan／原 handoff 共同提交為 c3c8827cea817db633736d9f8303c43f454fa7cd，簡潔性報告提交為 2292aecc706105116ca4bd1745bb208e74cb3126，獨立 Plan Review／產品基準為 97a1cbc0c44d2050b942aab3a88baed716fbda84。本次交接文件提交另由 git log 定位，不把歷史基準誤當當前 HEAD。

先核對 repo／worktree／feature/line-notes-media／HEAD／Git 狀態、原文件 hashes 及產品基準；保留無關 dirty／untracked／其他 worktree，不 reset／clean。來源、授權或版本實質不符時停止並回報；符合後直接完成已授權 S1，不再要求第二次開始確認。

S1 只修改 notes.py、必要的 media_verify.py copy 小工具、test_notes_restart.py、直接受影響的 test_notes_records.py／test_notes_regressions.py。implementation.md 與可公開成果放原 docs/plans/20261107-notes-restart-overwrite-replan/，原始證據放專案私有任務區。不要改 plan／既有報告、AGENTS、Skill、手冊、Swift、相簿或共用帳本層。

完成 preview／confirm → scope 內單項新 attempt → 持久獨立 candidate → 整批單筆 activation → 新物件重開投影，包含中斷 scan／session。以一篇舊完成但 LOCAL_CHANGED、另一篇 UNKNOWN 的合成資料走完整路徑，至少一張照片與一支影片。確認前拒絕；舊事件與原檔不變；候選全部驗證後才改目前版本。

依 plan L158、L196 完成 V1 及 C01、C02、C06–C09、C11 直接路徑，至少另跑真實合成照片／影片解碼。覆蓋 PR-N01–N04：舊 verification／completion 在新 attempt 後仍可重放；跨 Session 新觀察另立引用；新版本後新增媒體命名相容；skip 不能冒充解碼 PASS。按本文檢查清單保存命令、環境、exit、manifest／hash、故障與重開結果。未跑的完整矩陣、回歸或實機逐項 NOT_RUN，不造通過。

維持 notes CLI 的 0／2／4／70 語意；exit 70、chain 損壞、鎖衝突、不安全新路徑或白名單外需求時停止依賴動作並保全證據。同根因最多三次有證據嘗試，連續兩次無新資訊就停；新 Session／restart 不重設歷史次數。

交付 S1 implementation.md、精確候選 SHA／diff、V1／已完成 C 項及未完成清單，逐項報告六狀態，按 AGENTS 留下授權 Git checkpoint。S1 完成即交回 Owner，由 Owner 另開首切片 Simplicity Review；不得自行啟動該角色或進入 S2，不把本切片當成日常可用、真實 E2E、獨立接受或整體 DONE。
```

**上方是供 Owner 在下一個主 Session 親自提交的完整範本。** 本輪要求是撰寫交接文件及 add／commit／push；產生、讀取或提交這個 Markdown，不等於 Owner 已提交範本內的採納／S1 授權。若下一個 Session 收到的只有文件整理或唯讀要求，仍依實際要求辦理；若 Owner 已提交上述完整 Prompt，就直接沿用其中授權，不重問相同事項。

# 記事本中斷恢復 S1 實作交接

## 任務與目前階段

根因識別：`NOTES-INTERRUPTION-RECOVERY-GAP`。Owner 要的是同一份日常記事本正式 Prompt，在預期／非預期中斷後自動找回進度；無法直接接續時，先確認整批重下與取代範圍，再產生可驗證的新結果；再次中斷仍可接續，流程不依賴內部 key 或開發文件。

本輪是依 `03_handoff_prompt.md` 檢查清單整理交接材料，不建立「Handoff Agent」正式角色，不延長前輪 Reviewer 的獨立接受範圍，也不開始 Implementer。已交付兩個計畫關卡：簡潔性 **PASS（僅限簡潔性）**、獨立 Plan Review **PASS（計畫審查）**。**尚無本方案產品實作。** 下一個可由 Owner 啟動的正式角色是 Implementer S1；開發前的三項預設採納由文件開頭的可提交 Prompt 明列，不冒填為既有批准。

本文件是新的實作導向交接，不是原 P2／P3 逐字審過的文件。只整理既有計畫、審查與授權界線，沒有修改設計或增加接受 gate。原 `20261107-notes-restart-overwrite-replan/handoff.md` 留原 bytes／版本，仍是計畫審查的標的；本文件取代的是「接下來攜帶哪些材料」的導引，不改寫歷史結論。

## 精確版本與接手核對

| 層次 | 精確身分／用途 |
|---|---|
| Repo／worktree／分支 | `/Users/hsiaojohnny/dev/Line_backup`；`feature/line-notes-media` |
| 本輪起始 HEAD／查得遠端 HEAD | `97a1cbc0c44d2050b942aab3a88baed716fbda84`；初始 index、dirty、untracked 均空，其他 worktree 保留 |
| 待實作產品基準 | 上述 `97a1cbc…` 的源碼／測試／Skill／手冊；本輪只新增本文件，產品不變 |
| 新 plan／Planner handoff 共同提交 | `c3c8827cea817db633736d9f8303c43f454fa7cd` |
| 計畫簡潔性報告交付 | `2292aecc706105116ca4bd1745bb208e74cb3126` |
| 獨立 Plan Review 交付 | `97a1cbc0c44d2050b942aab3a88baed716fbda84` |
| 本交接文件候選 | 新增 `docs/plans/20261107-notes-restart-overwrite-s1-handoff/handoff.md` 的提交；最終完整 SHA 見本輪交付回覆與私有 Git receipt，亦可用下列 `git log` 唯一定位 |

| 來源 | SHA-256（本輪逐 bytes 對照入口提交） |
|---|---|
| 原 plan.md | `86e89b5a62d12ea64fb6e75a31d394ea9fba1413677a951055d2b4114914c391` |
| 原 Planner handoff.md | `b444bb7c79323631e9df60b07efcaf0724e9880502e22b2f5f40e63263e02ca1` |
| simplicity-plan-review.md | `db8b561ce7a727f49f57f9be2a8b4acd8ab3fba16a84d437b76a0e78faa2795a` |
| plan-review.md | `3ce38f652edd1e28c71d78f0c30b7412a7bdf962795dda9c1af2c7148f6235e5` |
| notes.py | `34ff6be9c6e9f74d2c450f3cc91aa8c6d1a0043cd0daef60f0680070b0e43247` |
| media_verify.py | `7c8051d1699449434dbaa41682a5a50f949858d593ee39cd2a1f38a1e1c6dd99` |

接手第一個具體動作是在 repo 根目錄核對以下 Git 身分與保護範圍，再讀來源；不要先啟動 LINE 或日常帳本 CLI：

```sh
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch
git worktree list --porcelain
git log -1 --format=%H -- docs/plans/20261107-notes-restart-overwrite-s1-handoff/handoff.md
git diff --exit-code 97a1cbc0c44d2050b942aab3a88baed716fbda84 HEAD -- src tests .agents AGENTS.md docs/LINE相簿備份_使用手冊.md
```

原文件用 `git show <表列提交>:<repo 內路徑>` 取精確版本，並核對上表 hashes。本文件的文件提交預期是產品基準之後的文件提交，不是版本錯誤；不能為了讓 HEAD 等於舊審查入口而 reset。若 HEAD 另有未交接的產品變更、原計畫／審查來源不同，或 dirty／untracked 與本切片重疊，保留現況並將具體差異交 Owner；不自行切換 worktree、覆寫或把不同候選當已批准版本。

## 必須一併傳遞的來源與閱讀順序

| 順序 | 輸入 | 用途 |
|---|---|---|
| 1 | [Owner 意圖與重規劃要求](../20261107-notes-interruption-replan/plan-review-owner-intent.md) | 認清重新下載與覆蓋前詢問的來源；不能回到單純文件限定／永久不支援 UNKNOWN |
| 2 | [新版 plan.md](../20261107-notes-restart-overwrite-replan/plan.md)、[原 Planner handoff](../20261107-notes-restart-overwrite-replan/handoff.md) | 整體契約、白名單、S1／S2 與 C01–C12；行號以下都綁定 `c3c8827…` |
| 3 | [計畫簡潔性報告](../20261107-notes-restart-overwrite-replan/simplicity-plan-review.md)、[獨立 Plan Review](../20261107-notes-restart-overwrite-replan/plan-review.md) | 各自 PASS 的範圍與 PR-N01–N04；不代替實作授權／產品接受 |
| 4 | [根因分析](../20261107-notes-interruption-review/issue-analysis.md) | 原故障／嘗試與未知；不把摘要視為本輪重新觀察私人資料 |
| 5 | [舊 Plan Review](../20261107-notes-interruption-replan/plan-review.md) | PR-B01 的原版本綁定；只作歷史來源，不作新版實作規格 |
| 6 | [記事本 Skill](../../../.agents/skills/line-notes-agent-cua/SKILL.md) 及其五份 references、[使用手冊](../../LINE相簿備份_使用手冊.md) | 現行日常契約與待 S2 整合的差距；S1 只讀、不藉開發動作取得日常 GUI 權限 |
| 7 | `notes.py`、`media_verify.py`、`notes_evidence.py` 與三份既有 notes 測試 | 實際源碼依賴、可注入邊界與嚴格驗證路徑；必要共用程式只讀，不擴修改白名單 |

角色與政策讀取 `/Users/hsiaojohnny/.codex/prompts/v4.9.0/04_implement_prompt.md`、專案 `AGENTS.md`，以及全域同版 `workflow-routing.md`／`subagent-model-policy.md`。本專案沒有可用的 release controller，不建立框架補件、不要求 controller／schema receipt。

私有前輪原件在專案 `.local/line-backup/tasks/` 的 replan／simplicity-review／plan-review 同名任務區；本輪原件在 `20261107-notes-restart-overwrite-s1-handoff/`。公開文件已提供需求、候選與來源定位；跨機器不要求搬出私人帳本／照片／原始 GUI。若缺的是某個必要、無法從已提交來源取得的證據，精確列明該缺項，只停止依賴它的工作，不從檔名或總數補造。

## 上下文：已知問題與新版選擇

歷史報告記錄同一列表兩篇各一支影片：一篇有完成歷史但目前 LOCAL_CHANGED，另一篇在 chooser 路徑處理失聯後保留 UNKNOWN。當時零檔案或沒有最終確認呼叫，不能證明原作業停止；本輪沒有重新讀取該私人帳本或確認異常原因。

舊計畫要求先取得終結／停止證據，但缺可操作訊號，故保留舊 PR-B01／BLOCKED。Owner 後續明確接受重新下載、要求覆蓋前詢問。新版改採**批次確認 → 新 raw → 獨立持久 candidate → 完整驗證 → 單筆 activation**，不再把舊下載已停止當作允許重新開始的必要前提。這不是 PR-B01 已補證、UNKNOWN 變 STOPPED、斷網已技術歸因或 CUA 失聯已解決。

新 raw、candidate 與舊檔各有不同作用：raw 是交給 LINE 的每 attempt 空白下載位置；candidate 是從未交給 chooser、不同 inode 的獨立副本；舊原件／舊結果是保留歷史。單純 rename、換資料夾或沿用現有 hard link 發布，仍可能被持有舊 fd 的 writer 改到新結果，不能當作隔離。

## S1 可改路徑與明確非範圍

plan L158 的首切片白名單比 L27–40 整體白名單小，按切片執行，不為湊檔案而修改。

| S1 路徑 | 允許用途 |
|---|---|
| `src/line_backup_batch/notes.py` | 新事件／graph／投影、scan 中斷與 session 引用、preview／confirm／intent／candidate／activation／重開摘要，保留既有退出碼 |
| `src/line_backup_batch/media_verify.py` | 僅有必要時共用既有 exclusive copy 小工具，不降低照片／影片驗證規格 |
| `tests/test_notes_restart.py` | 新增 S1 合成恢復整合與故障／負例 |
| `tests/test_notes_records.py`、`tests/test_notes_regressions.py` | 只改直接受影響的 graph／gate／相容性斷言，保留未確認的原拒絕 |
| `docs/plans/20261107-notes-restart-overwrite-replan/implementation.md` 與同目錄必要成果 | S1 實作報告、候選與可公開檢查摘要；**仍放原計畫目錄**，不因新增本交接目錄而移動原指定位置 |
| 新的專案私有任務區 | 命令／exit／環境、合成 fixture／manifest、故障注入、hashes、進度及 Git receipt；不可覆寫舊任務證據 |

**S1 不修改** `AGENTS.md`、notes Skill／references、手冊正式 Prompt；它們留待 plan L162 的 S2，須首切片審查後由 Owner 另交辦。`test_notes_media_verify.py` 是可執行的既有驗證來源，未列入可改檔案。

禁止修改 `daily.py`、`record_store.py`、`relocation.py`、Swift decoder、相簿 Skill／事件／公共介面、全域政策／角色 Prompt、舊 plan／handoff／報告；不遷移或寫入真實 `backup/`、`backup-records/`、`notes-backup-records/`、index／active 檔，不手寫事件或 v2 bundle，不改舊完成事實，不 merge／force-push／改寫歷史。S1 不操作 LINE、chooser、下載控制，也不取消舊視窗、重啟／強退 App 或斷網製造故障。

## S1 必須維持的產品契約

本節是 plan L69–156 的定位摘要，實作時仍讀完整原文；事件欄位名與小函式可按既定邊界決定，不另創第二份狀態真相庫或通用交易框架。

| 契約 | 實作必須成立的行為 |
|---|---|
| 恢復範圍／確認 | 完整盤點受影響貼文全部可備份媒體；預覽列 completed sibling、舊／新路徑、未知／異常、空間與欠項。未確認／拒絕／沉默／假回覆／錯 scope 沒有新 intent 或 activation |
| 確認持久性 | v2 evidence 綁 list、scope digest、舊版本／attempt refs、路徑策略與 Owner 回覆；expected tip＋鎖內重算，確認重入只讀回。S1 的回覆及來源全為明示 SYNTHETIC，不假造真人同意 |
| 新 attempt | 只在確認 scope 內，唯一新空 raw、prior attempt／generation 可追溯；舊 UNKNOWN 不改，沒有假 STOPPED。沒有 outcome 先 outcome，已有 UNKNOWN 才 reconcile，UNKNOWN 不 verify |
| 舊 pending／scan | 只讓批次明列舊交易退出候選／不能再被一般 verify／resume 發布；未列者仍擋。中斷 scan 明確終結但不假 COMPLETE，保留 pages；新 scan 不改舊 attempt 的 scan／認領 |
| 跨 Session | 新綁定／新觀察另立驗證引用以證明 frozen scope，writer／replay 都檢查；不沿用舊 Session ID、座標或單憑舊完整 scan |
| 獨立 copy | copy 前持久計畫；exclusive create、no-follow、bytes copy、fsync、來源前後身分／hash與副本 hash。拒絕 symlink／hardlink／變動／額外檔／不安全路徑，不把 raw hard link 或 rename 成 candidate |
| 候選驗證／啟用 | 檢查持久 candidate 本身的穩定清單、預期數、非空、SHA-256、ImageIO／固定 ffprobe＋ffmpeg 完整解碼；整批可備份候選齊全且引用仍符，才在鎖內追加單筆 activation，不另造 current 指標檔 |
| 歷史／投影 | activation 前舊 active 不變；之後每媒體一個目前版本，不重複計數。保留舊 completion／UNKNOWN／LOCAL_CHANGED；不新增第七類媒體業務狀態，批次未啟用不能稱批次完成 |
| 範圍內外保護 | scope 內舊 LOCAL_CHANGED 只安全 lstat／歷史引用，不修補、不跟 symlink、不作 raw；scope 外仍擋。純 LOCAL_MISSING、排除、受保護及來源欠項不被確認解除，缺項不算完成 |
| 重開／再次中斷 | 回覆遺失讀回既有批次／activation；保留已驗 candidate，只對未完成／不確定項依有效同批確認建立新 attempt。半檔不猜、不續寫、不清理；磁碟不足停，不刪資料騰空間 |
| 相容性／退出碼 | 舊事件 bytes／schema／completion／路徑不遷移；無 restart 的原 gate 不變；舊 CLI 遇新格式應拒絕，不能退版寫入。維持 0／2／4／70，70 不是可重試業務拒絕 |

命令 `restart preview`、`restart confirm`、`intent --restart-id`、`restart resume` 是 plan L91–110 的候選名稱，**目前尚未實作**。不得先拿來操作日常帳本；實作報告列最終 help／欄位對照。CLI 只處理檔案／事件，不提供 GUI 權限、不自行下載。

## 審查後四項注意與源碼起點

這四項來自原 Plan Review 的非阻塞建議，均屬既有契約，不把它們另升為新 gate 或擴功能。

| ID | 基準來源位置 | S1／相容性核對方向 |
|---|---|---|
| PR-N01 | `notes.py:1635`、`:1668`、`:1761`；plan L110、123、156／C11 | 現 graph 將舊 verification／publish／completion 和全帳本 latest attempt 比較；必須驗證「先有舊 verification＋completion，再追加 restart attempt，重開仍能重放完整歷史」 |
| PR-N02 | `notes.py:2155–2184`；plan L98、110／C05–C07 | 新 Session 的觀察引用與原 attempt scan 並存，不只放寬 verify，不改寫舊 scan |
| PR-N03 | `notes.py:3269–3320`；plan L29、117、156／C11 | 新版本啟用後，同篇後續新增媒體的目的地／編號仍能運作；不能只改 summary 而使發布模型卡在舊直接子目錄 |
| PR-N04 | `test_notes_media_verify.py:42–66`、`:216–245`；plan L158、196 | 現照片建置與固定影片工具檢查可 SkipTest；exit 0 必須分列 skips，缺真實解碼證據仍 NOT_RUN |

其他直接依賴：`notes.py:1818` bind、`:1991` scan、`:2414` completion projection、`:2447` pending publish、`:2562` LOCAL_CHANGED、`:2646` intent、`:3583` verify、`:3646` resume；`media_verify.py:252–281` exclusive copy、`:325` 起照片暫存隔離。這些是基準行號，不是新實作的函式名約束；源碼移動後在報告補新位置。

## 檢查清單、責任與成功條件

所有合成帳本、evidence、照片／影片與暫存都放專案隔離目錄，patched active hint／collection 不觸及真實資料。既有影片測試有未指定 `dir` 的 `tempfile`，執行子程序時將 `TMPDIR` 指向先建立的專案私有測試暫存目錄，避免合成資料落到專案外；這不需改白名單外測試或系統設定。

| 檢查／owner | S1 要交的證據與成功標準 |
|---|---|
| V1／Implementer | 兩篇合成來源：舊完成且 LOCAL_CHANGED、另一篇 UNKNOWN；至少照片＋影片。未確認拒絕→確認→新 candidate→單筆 activation→新物件重開；舊原件／事件 bytes／hash 不變，只有新 active 計數 |
| C01、C02／Implementer | 拒絕／假確認等零新派送；UNKNOWN 與無 outcome 兩分支可由確認關聯重開，不偽造終態 |
| C06、C07／Implementer | scan／bind／pending 舊交易關聯；確認／intent／outcome 回覆遺失及新 UNKNOWN 重開，保留原引用、不在同 attempt 再送 |
| C08、C09／Implementer | copy／fsync／驗證／manifest／activation 邊界故障；候選不完整不啟用、回覆遺失不重複；實際持有舊 fd 寫入、舊 path 重建、copy 中變動，確認 candidate inode／hash 保護 |
| C11／Implementer | 舊 chain／v2 evidence／completion bytes 不變，舊 fixture 可讀、原拒絕不變，新 summary 一媒體一 active；包含 PR-N01 的既有完成歷史及相關版本相容性 |
| 真實合成媒體解碼／Implementer | 不只 mock：至少一張照片 ImageIO 完整像素解碼、一支影片固定成對 Homebrew ffprobe／ffmpeg 全解碼。保存工具來源／hash、實際命令與結果；解碼成功不證明服務端原始位元 |
| V3／Owner 啟動首切片 Simplicity Reviewer | S1 精確 SHA、implementation.md、V1／已完成 C 項、剩餘清單；即使首切片已是最後候選也不略過此關，由人決定後續 |

plan L196 的 S1 最低範圍是 **V1＋C01、C02、C06–C09、C11 的直接路徑**，不是要求此時全部 C01–C12 都通過。其他分支／未完成矩陣逐項 NOT_RUN，在 S2 最終候選補齊；全部 C 項仍是整體接受必需。

在 repo 根目錄使用既定新測試命令：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
```

真實合成解碼可執行既有 `test_notes_media_verify.py` 測試；直接改動的 records／regressions 使用相符既有測試核對。沿用同一 unittest discover 入口選定對應 `-p`，不新增外部 E2E 或測試框架。只用本程序相符的既有 Swift SDK，不更動系統工具鏈；影片固定 `/opt/homebrew/bin/ffmpeg`／`ffprobe` 配對，不混用 PATH 裸命令。

最終候選須執行專案最小回歸，保留 plan L205–207 的三個命令：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

不每個 commit 重跑全套；以相符候選的有效證據交付，相關變更、失敗或證據失效才重跑。S1 與最終整合不是同一關：S1 已跑與尚待的回歸各自列清楚，不能用切片 PASS 假稱 V4 已完成，也不能以最終全矩陣尚未齊全而擅自略過首切片交接。

## Implementer 的交付與停止點

在原計畫目錄新增 `implementation.md`；記錄開發授權來源、採納 plan／本交接版本、起始及結束 repo／branch／HEAD、實際差異與允許路徑、保留的既有工作。逐項列檢查命令、cwd／環境／工具、exit、輸出位置、測試／skips／故障與重開結果、前後 manifest／hash、最終 help／候選欄位對照、事實／推論／未知、未完成項及六狀態。

證據綁定實際 S1 完整 commit SHA；有未提交差異則逐檔列明及保存可識別 diff，不以 plan SHA 當產品候選。依既有同範圍授權逐檔 add／commit／push，提交本體含「意圖」「做了什麼」「下一步的建議」及真實「驗證與結果」，以 `git show -s --format=%B` 核對，推送後查遠端精確 HEAD；不夾帶私有資料。Git checkpoint 不等於正式接受。

**完成 S1 即停並交 Owner。** 不自動進 S2、不代簽 Simplicity／Acceptance、不自動派發正式角色、不因拒絕而跨角色修補／重測。普通且在已授權範圍內的機械修正可自行完成，不逐點再問；架構、範圍、安全／資料／公共介面／驗證邊界改變才交人決定。

依賴前提失效時立即停止該動作：版本／授權不符、chain／v2 證據損壞、scope／來源身分漂移、無唯一引用、新寫入根不安全、鎖衝突、exit 70、白名單外需求。保留已驗 candidate 與全部歷史，不能改帳、換目的地／入口／Session 或退版繞過；同根因最多三次有證據嘗試，兩次無新資訊停止，原計數不重設。

## 未來 S2、日常實機與獨立接受

S2 由 Owner 在首切片審查後另交辦：補完整矩陣，按整體白名單整合 AGENTS／Skill／references／手冊，消除新舊規則矛盾，保持單一日常正式 Prompt，完成 V4 及相符回歸後，才進 Owner 日常試用。這些不是本次 S1 的自動續作授權。

G1–G2 真實 LINE 測試要 Owner 另指定允許重下的測試列表，使用手冊第 5 節的日常正式記事本 Prompt，加當次有效前景與精確批次確認；不用 Implementer／Acceptance Prompt 代替備份入口。以允許的暫停／交接產生中斷，不強退或斷網。CUA 通道失效／未決輸入、modal 不明或原件不能保存就停；取消 chooser 不是舊寫入停止證明。

A1 由 Owner 另開獨立接受者，逐條映射精確候選、離線與實機證據；實作者及其 helper 不接受自己。分別報離線機制、指定環境恢復、原列表實際完成三層。保留 `dispatch_authorized=false`、`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 原意；簿記、GUI、檔案解碼、真人 `OBSERVED`、獨立接受不可互換。

## 本輪交接文件檢查與證據界線

本輪實際完成 Git repo／branch／HEAD／worktree／乾淨狀態及遠端查詢，命令 exit 0；逐 bytes 對照 17 份 repo 來源與入口提交，另保存 6 份全域 Prompt／政策／模板／HTML Skill 的大小／SHA-256，共 23 份。原 plan／handoff／審查／產品來源未改，唯一公開新增本文件；來源清單、實際 argv／stdout／stderr／exit、文件檢查與 Git 交付在私有任務區保存。

同角色 inherited native helper 僅提取 S1 邊界與審查注意，不是正式 reviewer；本文件完成後依 Owner 明示另請 `gpt-6-luna` helper 梳理提交訊息，主 Session 執行 Git。請求參數與平台顯示、provider usage 分開；沒有顯示／usage 的後端身分、用量與成本為 UNKNOWN，不從設定推定，也不宣稱 token 節省。

本輪文件檢查包括 UTF-8／相對連結／六狀態／空白、來源不變、唯一新增與首段 Prompt。產品回歸、S1／C01–C12、編譯／解碼、真實帳本／媒體／GUI、Owner 試用、最終接受均 **NOT_RUN**；沒有新 GUI `OBSERVED`。前輪工具 hashes／SDK 存在的查核不變成本輪解碼 PASS。

## 交接狀態快照、事實與待決事項

```text
PRIMARY_OUTCOME_STATUS: HANDOFF_DOCUMENT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

PRIMARY 只描述本輪交接文件交付；先前 PLAN_REVIEW_PASS 仍是原版本的歷史結果。REQUIRED 指產品／行為／實機必要檢查，INDEPENDENT 指最終產品接受。原備份及新機制尚未完成，不標 DONE。

- **事實：** 新版 plan 與兩份計畫審查均存在且版本相符；沒有 S1 實作，本輪只新增交接材料，未操作真實資料。
- **推論：** 依既定設計，確認接受重複傳輸與獨立副本／單筆啟用可構成有界恢復方向；仍待實作與實機證明，不保證任意外部干擾或所有模型每次成功。
- **未知：** 新 schema／graph／投影／copy 正確性、來源可用性、舊 LOCAL_CHANGED 成因、實際 chooser／晚到輸入、空間需求及跨 Session 實機表現。
- **待 Owner 決定：** 是否採納文件開頭三預設並提交 S1 Prompt；若調整原地路徑、範圍、刪除或驗證標準，先決定適用重規劃／重審，不由下一 Implementer 靜默改設計。這不妨礙本輪完成交接及已授權 Git 交付。
