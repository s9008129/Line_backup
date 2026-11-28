# 記事本中斷後重新下載與確認取代：新版計畫草案

## 決策摘要

**目標：下次使用同一份日常記事本正式 Prompt，Agent 自動找回進度；遇到無法直接接續的中斷，提出整批恢復範圍，使用者確認後重新下載，驗證後取代目前使用的備份結果；再次中斷仍可由永久記憶接續。** 不再要求 Owner 先找出舊下載的停止證據，也不把 UNKNOWN 分支永久不支援當成完成目標。

本輪是 Planner，僅新增規劃與交接文件。需求依據是 [Owner 意圖及重規劃要求](../20261107-notes-interruption-replan/plan-review-owner-intent.md)；根因識別沿用 `NOTES-INTERRUPTION-RECOVERY-GAP`。舊計畫與兩輪審查均保留原版本綁定，新版不沿用舊 Simplicity PASS，也不宣稱 PR-B01 已取得停止證據。

**分級 CRITICAL。** 新方案會改變記事本的禁止重送例外、完成版本投影與 LOCAL_CHANGED 處置，屬資料與授權邊界變更。需要 Owner 採納有界方案、計畫 Simplicity Review、獨立 Plan Review、首切片 Simplicity Review，以及最終獨立接受。各正式角色由 Owner 在另一個主 Session 啟動。

選定候選是「**一次確認受影響貼文的完整恢復批次 → 每項下載到新 raw 暫存 → 複製成獨立檔案並驗證 → 一筆追加事件啟用整批新版本**」。這裡的「覆蓋」是新結果成為目前備份；實體檔採新版本目錄，舊檔與舊紀錄保留，不原地覆寫、搬動或刪除。確認畫面須明示此效果與新舊路徑。這是供 Owner 採納的具體預設，不把它冒充 Owner 已確認的真實資料覆蓋。

此選擇刻意避免「舊目錄搬開、再把新目錄放回相同路徑」：舊下載可能持有原 inode 或舊路徑；保留原路徑、使用從未交給 LINE 的新發布目錄，可以讓已知晚到寫入留在舊區。使用者若要求相同實體路徑原地覆寫，須重新決定方案與風險，不能由 Implementer 偷換為 rename 覆蓋。

非目標：相簿流程、其他列表、整個備份庫重建、刪舊檔／自動清理、改寫舊 UNKNOWN／completion、修復舊媒體內容、技術歸因整機斷網、強退或重啟 LINE、背景重試服務、GUI 控制器、下載 API、合併 master。整篇目錄僅 LOCAL_MISSING 的已完成項仍不因缺席自動重下。

## 範圍、基準與授權

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`；分支 `feature/line-notes-media`。
- Planner 起始 HEAD 與當次遠端 HEAD：`7df6830728cb448052de0a2c065d4d039158e204`。初始 index、dirty、untracked 為空；其他 worktree 與忽略資料全部保留。
- 舊 plan／handoff 版本為 `414e61db1cd42e85c27d1edeef3cbb06d77bc2c2`；最新需求報告在起始 HEAD。來源 SHA-256／大小存本專案私有任務區 `sources-before.json`，不以目前 HEAD 冒充舊 GUI Session 的完整版本。
- 本輪可寫：本目錄 `plan.md`、`handoff.md`、`progress.md`、`role-report.md`；私有證據 `.local/line-backup/tasks/20261107-notes-restart-overwrite-replan/`。本輪不改產品或既有規劃文件。
- Owner 已授權本輪規劃與成果 commit／push；未授權本輪操作 LINE、取消 chooser、下載、真實帳本追加或真實媒體取代。計畫採納與每批真實資料確認是不同授權。

以下是計畫經採納後的 Implementer 白名單，不是本輪寫入許可；只改有必要的檔案，不為湊範圍修改：

| 路徑 | 必要用途／限制 |
|---|---|
| `src/line_backup_batch/notes.py` | 新恢復批次／版本事件與 replay；scan 中斷找回；命令、gates、copy／驗證／啟用與摘要；維持現有 CLI 退出碼 |
| `src/line_backup_batch/media_verify.py` | 僅在共用既有 exclusive copy 有必要時抽出小工具；不降低 ImageIO／影片解碼規格 |
| `tests/test_notes_restart.py`（新增） | 恢復、確認、隔離、crash／重開、版本與負例；合成資料 |
| `tests/test_notes_records.py`、`tests/test_notes_regressions.py` | 更新直接受影響的相容性／graph／gate 斷言；保留未確認時原拒絕行為 |
| `AGENTS.md` | 只調整記事本經精確批次確認後的重下／取代例外及新舊版本保護；相簿與其他邊界不變 |
| `.agents/skills/line-notes-agent-cua/SKILL.md` | 正常啟動自動找回及恢復例外的入口導引 |
| 同 Skill `references/download-and-ledger.md` | 唯一交易順序、CLI 命令與參數、批次確認及跨 Session 操作 |
| 同 Skill `references/verification-and-recovery.md` | 中斷矩陣、raw／candidate 分界、歷史與目前版本、本機可用性 |
| 同 Skill `references/gui-inventory.md` | 新觀察落檔／讀回、舊 chooser 的有界導覽、新掃描與來源對帳 |
| 同 Skill `references/evidence-template.md`、`references/evidence-decision-cases.md` | 確認來源、範圍引用與再次中斷／晚到結果案例；重用 v2 bundle |
| `docs/LINE相簿備份_使用手冊.md` | 只更新記事本說明與第 5 節正式 Prompt 的恢復／確認條款；維持單一日常啟動入口 |
| 本計畫目錄 | 實作報告、行為結果、候選清單與後續角色報告；不得改寫本輪已交付的結論冒充批准 |

禁止：修改 `daily.py`、`record_store.py`、`relocation.py`、Swift decoder、相簿 Skill／Prompt／事件／公共介面、全域政策／角色 Prompt、舊 plans／tasks；修改或遷移真實 `backup/`、兩種 records／index／active 檔；手改事件、手寫 v2 bundle、抹除或降格 exit 70。測試只在專案內隔離合成目錄執行。需要白名單外產品檔、資料遷移或額外副作用時先停交 Owner。

## 已有能力、需改變之處與替代方案

下列定位以 Planner 起始 HEAD 為準，實作接手須核對版本；是源碼事實，不是執行測試。

| 事實／來源 | 設計含義 |
|---|---|
| `notes.py:732` 載入 chain／schema／graph；`:3076` 摘要已有未決 attempt、destination、scan 等 | 保留單一追加式永久記憶；擴充 summary，不另造控制器、索引狀態庫或 active 真相來源 |
| `notes.py:2677` 與 `:1591` 的 writer／graph 均只允許 STOPPED／NOT_SENT 後 recovery | 新增正式的「已確認重新開始、舊結果仍未知但退出本次候選」關聯；兩邊同步驗證，不只放寬 writer gate |
| `notes.py:2414` 目前每媒體只允許一筆 completion；`:2665`、`:3594` 拒絕已完成重下 | 需要有版本的新結果與啟用投影；舊 completion 原 bytes 不變，無新批次的行為保持相容 |
| `notes.py:2483`／`:2562` LOCAL_CHANGED 是列表級 blocker | 只有確認批次明列的異常貼文能進入新版本恢復；未涵蓋的異常仍阻塞，不能全域忽略 |
| `notes.py:1822` 開放 scan 阻擋 bind；`:1995` UNKNOWN／pending 擋新 scan；`:2155` 驗證綁原 scan | 要處理盤點本身中斷及恢復前重新核對來源；不能藉新 scan 改認領舊 attempt |
| `notes.py:2447` pending publish 與 `:3322` 起的 journal 已能找回命名 | 可唯一恢復且不重下者優先接續；若使用者選擇重下，須追溯保留舊 plan，不讓它永遠擋住新批次或被舊命令再執行 |
| `notes.py:3492` hard link source→target，`:3514` 後 unlink source；完成檔仍為同 inode | 新批次不能沿用這個 raw→正式發布方法；rename incoming 也不能隔開已開 fd 的 writer |
| `media_verify.py:252` exclusive copy 已做獨立副本與前後核對；`:325` 照片暫存副本會隨驗證刪除 | 可重用 copy 邏輯，但需持久 candidate；照片與影片都驗證將來啟用的獨立檔案 |
| `notes.py:275`、`:718` flock 只保護合作 CLI | 可鎖住批次事件與啟用；不能把鎖說成 LINE／GUI／外部程序隔離 |

| 方案 | 決定與取捨 |
|---|---|
| 文件限定、先收斂舊 STOPPED 才重下 | 不採：無法承載 Owner 的新方向；舊審查已指出必要停止訊號缺口 |
| 同意後直接清空／覆寫原目錄 | 不採：再次中斷可能毀掉唯一可用資料，且無法隔開晚到寫入 |
| 暫存後將舊目錄搬開、原路徑換新 | 不採：多個 rename 與帳本無共同交易，原路徑仍可能被舊 chooser／writer 使用 |
| 獨立版本目錄＋追加式啟用 | 選定：多占一份恢復資料的空間，但不搬舊原件；單一啟用事件是目前版本的唯一提交點，容易在重開後判讀 |

不新增常駐服務、通用 transaction framework、第二份 manifest 真相庫或自動垃圾回收。低影響 helper 抽取、私有函式名與測試組織可由 Implementer 決定；批次範圍、確認語意、獨立複製、版本提交點與相容性不可自行更改。

## 恢復範圍與使用者確認

### 「所有資料」的具體預設

Agent 完整盤點後，自動建議**此單一列表內需要重新開始的全部貼文**作一批：有無 outcome／UNKNOWN、不可直接接續的未完成下載／發布，或 LOCAL_CHANGED 的貼文。每篇包含整篇已核對且來源可用的照片與影片，包含同篇先前已完成的媒體；不是只重下某一檔。其他正常完成貼文跳過，純 LOCAL_MISSING 的完成項不納入。原問題中兩篇各一支影片、其中一篇 LOCAL_CHANGED／另一篇 UNKNOWN 的情況，可在同一預覽明列兩篇，而非要求先另修第一篇才能重下第二篇。

既有 EXCLUDED／PROTECTED_HISTORY 不因批次解除；來源已到期／缺失也不默認排除。預覽逐項列出保留或不可取得者；有未解保護／來源缺項時不稱整篇或整列表全部完成。要更改排除／保護或擴及正常完成的其他貼文，另決定精確範圍。本計畫不提供整庫覆蓋選項。

### 確認內容、時機與持續效力

在**第一個新恢復 intent 前**，Agent 出示由帳本與當次盤點產生的唯讀預覽：列表、每篇可讀識別、照片／影片數、包含哪些既有完成項、舊／新目錄、舊 UNKNOWN 與異常、所需額外空間估算、保護／到期項與不受影響範圍。不得公開私人名稱；真實確認留私有任務與 v2 evidence。

建議白話確認如下；括號內容由 Agent 從預覽填入，不能原樣當使用者已同意：

> 要重新下載這份列表中列出的（N）篇、（P）張照片及（V）支影片嗎？這會重下這些貼文內列出的所有可備份媒體，包含（C）個先前完成項。全部驗證後，新版本會成為目前備份，位置是（新版本目錄）；原有資料及未知下載留在（舊路徑），不刪除或原地覆寫。其他貼文、排除／受保護項與永久紀錄不被覆蓋。若同一批再次中斷，會保留已驗證的新檔，對未完成或結果不確定的項目另建暫存重下，可能再次傳輸；範圍改變會再問。是否同意？

Owner 可以同意、拒絕／取消，或調整範圍。沉默、逾時、啟動 Prompt、舊 `recovery_authorized=true`、一般「繼續」、工具成功或 Planner 本計畫都不是這批確認。拒絕時不建立恢復批次／新 intent、不改目前版本；只保留原進度與唯讀預覽，不以 exclude 或 protect 代替拒絕。

確認來源封裝成 v2 evidence，綁 list／scope digest／舊版本與 attempt 引用／新版本路徑策略／重下範圍／同批中斷恢復條款／Owner 回覆。同範圍批次完成前再中斷，確認持續有效；不逐檔或逐 Session 重問。來源集合、身分、排除／保護、取代目標或目的地策略改變時舊確認失效，先重做預覽並取得新確認，不把「同意」擴成無限重試或整庫權限。保留既有同根因最多三次、兩次無新資訊停止的限制及歷史計數。

## 執行設計與持久狀態

以下是待核定的新產品契約；命令名稱為計畫候選，實作報告須列最終 help／欄位對照。未實作前不得在日常任務嘗試不存在的命令。

### 自動找回、盤點與綁定

1. 維持 `lists → active-notes 輔助定位 → 相符 memory／evidence-audit`，先核對完整 chain／證據。摘要提供目前版本、開放恢復批次、已驗證 candidate、未決 raw attempts、原／新目的地、未完成發布與唯一建議下一步；不靠聊天、開發文件、Owner 手填 key。
2. 有效日常授權及新鮮前景內核對三層身分後 bind。對前 Session 的未完成 scan，新增明確追加式「盤點中斷」終結，保留舊 pages，不偽造 COMPLETE；再 bind 與從頂重盤點。同 Session 可按既有連續性證據補接。中斷標記與 bind 之間 crash 後須可讀回再續，不重標或刪 pages。
3. 允許恢復評估用的新 scan 在舊 UNKNOWN／pending 尚存時盤點，但**不解除任何下載／發布 gate**。舊 attempt 永遠引用原 scan；新盤點不賦予舊 attempt 新 binding。不得沿用舊座標、舊 Session ID 或把不完整 scan 當完整。
4. 在改開新 scan 前先判斷原交易是否已有可歸屬 DOWNLOAD_FINISHED、完整候選或唯一發布下一步；原 binding 可核對時先接續，不必為恢復而重下。不能直接續的才重新盤點並納入確認。新批次跨 Session 時，以新綁定／新觀察證明 frozen scope 與媒體身分仍相同，明確記錄當次驗證引用；不重標原 attempt 的 scan，也不把舊完整 scan 單獨當新前景證據。來源判讀、CUA 原件落檔／讀回方法必須整合回 Skill，不能靠本計畫當日常依賴。

### 新增最小操作面與事件

| 操作面候選 | 必要契約 |
|---|---|
| `restart preview` | 唯讀，從完整盤點與目前記憶產生精確 scope、舊 chain tip／引用、目標、缺項及大小估算；不建立目錄、intent 或確認事件 |
| `restart confirm` | 要求剛才 scope／expected tip、有效 session 與真正同意的 v2 evidence；持鎖重算並精確相符才追加確認批次；同一確認重入只讀回，不新增分叉 |
| `intent --restart-id` | 只處理已確認 scope 中的一項；建立全新 raw 目錄與新 attempt，記 restart／generation／prior attempt。舊 UNKNOWN 保留結果；新關聯只讓它退出本批次目前派送候選，不聲稱它停止 |
| 原 `outcome`／`reconcile`／`verify` | 新 attempt 仍遵守第一筆 outcome、UNKNOWN 不驗證、單次 GUI 控制；verify 對獨立 candidate 作檢查及保存已驗證候選，不提前改目前版本 |
| `restart resume` | 重開後純檔案／事件恢復複製、驗證與啟用；回傳需重新觀察／重下的項目讓 Agent 走同一 intent 流程；CLI 不按 GUI、不自動下載 |

確認、candidate manifest、啟用與中斷 scan 使用版本化的新事件；新 intent／verification 以明確版本區別。事件至少有 batch／generation ID、scope digest、原始 event refs（sequence＋SHA-256）、目前舊版本、當次來源 scan、保留路徑、candidate manifest／驗證引用及確認證據。拒絕未知欄位、錯 context、循環／分叉、跨列表引用及未確認恢復。實際欄位名與小函式可實作時決定，不能用鬆散 JSON 代替 graph 驗證。

`restart confirm` 先追加一筆批次事件，明列被取代候選的舊 attempts／pending plans；未完成檔案不刪、不搬。這讓後續 writer 與 replay 同樣知道哪些舊交易不可再由一般 verify／resume 發布。未列入者仍阻塞；不得僅因存在任何 restart 就放寬全列表。舊 raw 晚到只能記歷史觀察，不自動認領為新 candidate，不改舊第一筆結果。

### 獨立檔案、整批驗證與啟用

- raw 使用每 attempt 唯一新空目錄；已交給 LINE 的所有目錄／inode 永不復用。即使 attempt 被替代，也保留其原位置與實際已知／未知結果。
- candidate 放同一允許 photo root 內的獨立版本目錄，例如 `<列表>/versions/<generation>/<貼文>/media_001.ext`；命名由工具產生，不靠中文名稱認領。此目錄不交給 chooser、不與 raw hard link、不把 raw rename 過來；舊貼文路徑不改成 symlink。
- 每次 copy 前先持久保存計畫，固定來源引用、唯一目標與 generation；重開時只從該計畫找檔，不掃目錄猜認。未完成副本留存為未採用，另記新唯一 copy 計畫；manifest 尚未提交的完整副本也須重新核對／驗證才可採用。
- 每項先等可歸屬的 DOWNLOAD_FINISHED；從 raw 以 exclusive create、no-follow 及串流 bytes copy 建立新 inode，fsync 後檢查來源前後身分／hash 與副本 hash。copy 途中變動、symlink、hardlink、額外檔、磁碟不足或路徑身分改變時不接受。只把「複製後沒有共用 inode」作有界隔離，不承諾 raw 以後不變。
- 對**持久 candidate 本身**檢查穩定清單、預期數、非空、逐檔 SHA-256、照片 ImageIO 完整像素解碼、影片成對固定 Homebrew ffprobe／ffmpeg 有效影像串流與完整解碼，寫入並讀回驗證。現有 photo／video 驗證規格不降級；hash／解碼不證明服務端原始位元。
- 整批所有可備份候選齊全，排除／保護／到期缺項已明列，candidate manifest 與 frozen scope、當下來源／舊有效版本仍相符，才在鎖內追加**一筆 batch activation**，引用全部已驗證候選及舊版本。該事件是目前結果的唯一提交點；不另寫可競爭的 current 指標檔。
- activation 只替換 scope 中已有完整新候選的媒體；排除／保護維持原分類，缺失／到期仍是欠項，不建立假 completion。批次候選啟用與整列表全部完成是不同命題；scope 明列不可取得者時摘要仍保留欠項。
- activation 前舊版仍是目前結果；activation 後摘要選新版本，每 media 只計一次。原 completion、原 UNKNOWN、舊 LOCAL_CHANGED 觀察都在歷史中；不能把它們改成成功或消失。新增恢復階段／候選進度欄位，不創第七類媒體業務狀態。只要開放批次未啟用，不能因舊 completion 齊全而回報本批次完成。
- 同批 scope 內 LOCAL_CHANGED 的舊路徑只做安全 lstat／歷史引用，不跟隨 symlink、不修補、不作 raw。新版本啟用後其異常成為保留歷史的警告；scope 外 LOCAL_CHANGED 仍阻塞新派送。僅偵測到 symlink／路徑逸出影響新寫入根或無法唯一綁定資料時拒絕，不能為恢復穿越舊異常路徑。
- 不自動清理 candidate、raw 或舊版本。磁碟不足是明確阻塞，不刪唯一資料騰空間；清理／回復舊 active version 是另行精確授權，不在本計畫增加回滾命令。

### 再次中斷的唯一下一步

| 中斷點 | 下次啟動的處理 | 不得發生 |
|---|---|---|
| 盤點／預覽、尚未確認 | 找原帳本、保留中斷盤點、重新核對；沒有真實確認就停在預覽 | 自動當同意或建立恢復 intent |
| 確認寫入後回覆遺失 | 依 scope／確認引用讀回既有 batch；不重複確認事件 | 新開空帳、複製 batch 以繞過舊狀態 |
| 新 intent 無 outcome／UNKNOWN | 優先查可歸屬晚到結果；有結果則走原 attempt；無法續時在同批既有授權下追加取代關聯、新 raw／新 attempt | 同 attempt 再按下載；虛構 STOPPED；沿用舊 raw |
| 新 raw 下載中又中斷 | 保留可驗證候選；只重下結果不確定／未驗證項，所有舊 attempt 可追溯 | 整批已驗證檔無故全重下、無限重試 |
| copy 途中／候選驗證失敗 | 部分 copy 不算完成；保留並記不採用，以新唯一副本重做；原 raw 可用且結果明確時不需重下 | 續寫不明半檔、啟用未驗候選 |
| 候選驗證完成、啟用前 | 讀回同一 manifest，再核對 candidate；其餘未完成者接續 | 把 candidate 當目前結果或跳過整批 gate |
| activation 寫入時 crash／回覆遺失 | 重讀 chain：已存在唯一有效 activation 就採新版本；若未追加且 candidate 完整則重做檢查後追加一次 | 同時出現兩個 active、重複計數或重下 |
| activation 後再中斷 | 下次從新版本找回，跳過完成；新版本缺席／異動依本機可用性規則另報 | 因 receipt 遺失再下載、清舊歷史 |

檔案完成但事件尚未寫入的窗口，由持久計畫／manifest 及檔案身分唯一判讀；不明半檔或多候選不猜。事件原子追加／fsync 沿用既有工具，需測「已提交但回覆遺失」，不承諾任意硬體損壞或截斷帳本都能自修；chain 損壞仍停止保全。

## 並行寫入與 GUI 的保證界線

**不必證明舊下載已停止才可確認重下。** Owner 確認接受重複傳輸；新設計藉獨立版本保存結果，舊 UNKNOWN 留在歷史，不透過 reconcile 偽造終態。這是有界政策變更，必須由 Owner 採納並經獨立 Plan Review；不是既有規則已允許的動作。

能保證的範圍：在合作 CLI 持鎖、candidate 路徑未交給 LINE、沒有任意外部寫入 candidate 的前提下，舊 raw 路徑或已開 fd 的晚到 bytes 不會改動獨立 candidate inode；單筆有效 activation 可唯一選目前版本。以測試實際持有舊 fd 寫入驗證此性質，不能只斷言資料夾不同。

不能保證：LINE／CUA 沒有服務端去重契約；可能重複傳輸；沒有共同 GUI／檔案／帳本原子交易、來源原子快照、OS 隔離或 exactly-once。若外部程序刻意寫入新 candidate、Owner／其他 Agent 同時操作、來源在盤點後改動或平台晚到 GUI 輸入改變目前畫面，可能使任務阻塞或歸屬失效；hash 與重查不能永久排除此類干擾。

Agent 不以 app 重啟或「等 N 秒」當隔離證明。恢復 GUI 前先保存當次新鮮 AX／畫面與真實輸入回傳，辨識現有 modal 層級；只有可唯一定位且作用明確時才取消舊 chooser 返回可靠入口，不把取消宣稱為舊寫入已停止。已知尚未返回的 CUA 輸入不與新輸入並行；通道失效、仍有可能作用於當前 UI 的未決輸入而無法建立新鮮可歸屬入口時停止 GUI，報具體工具／前景問題，由 Agent 做有界查證，不把證明舊下載停止的責任丟給 Owner。

新 attempt 仍要當次列表→貼文→viewer→控制→chooser→raw 目的地的連續證據；不沿用舊 handle／座標、不以可解碼檔案代替來源身分。未授權前景、無法保存原件或 chooser 不明時不派送。此限制是當次輸入可靠性，與允許舊下載未停止的重下政策分開驗證。沒有真實 LINE／CUA 實證前不保證該環境各種失聯都能自動恢復。

## 相容性與首個可驗證切片

舊事件 bytes、schema、completion 與保存路徑不遷移。新程式能重放合法舊帳本，沒有 restart 時沿用原禁止重送／LOCAL_MISSING／LOCAL_CHANGED gate。新格式帳本由舊版 CLI 讀取不支援時必須明確拒絕，不得退版繼續寫；回退程式不等於可回滾新事件。至少一組合成舊 fixture 前後 hashes 不變；新增 graph 必須拒絕偽造確認、舊版繞過與跨世代認領。

**S1 首切片：離線可驗證的恢復批次核心。** 在 `notes.py`、必要 copy helper、三份允許測試與本目錄實作報告中，做出 preview／confirm、單項新 attempt、獨立 candidate、整批 activation、重開投影與中斷 scan／session 的最小垂直路徑。使用兩篇合成來源：一篇舊完成且 LOCAL_CHANGED、一篇 UNKNOWN；未確認拒絕，同意後完成新候選，重開後只計新 active，原歷史保持。第一批涵蓋至少一張照片與一支影片的既有驗證路徑；便宜的故障注入可 mock 外部 decoder，但至少另跑真實合成媒體解碼。

S1 不先開 GUI、改正式 Prompt 或碰真實 records；仍未宣稱功能可日常使用。完成即交 Owner 啟動首切片 Simplicity Review。若切片需超出已核定設計、發現 activation／版本模型無法保持相容，停交 Owner，不做跨角色修補。

**S2（需 Owner 在首切片審查後另交辦）：** 補完負例／故障矩陣；在允許的 AGENTS／Skill／references／手冊整合唯一操作本文與正式 Prompt，移除記事本舊規則的矛盾、保留相簿規則。日常 Agent 不讀 plan；CLI 不簽 GUI grant。候選經回歸與適用獨立檢查後，才進入 Owner 日常實機試用。

## 檢查、成功條件與責任

| ID／owner | 實際要證明什麼／證據 | 停止條件 |
|---|---|---|
| P1／Planner（本輪） | Git 身分、來源 hashes；新四份文件 UTF-8／連結／差異／範圍；私有命令與 exit | 必要來源／基準缺失則 BLOCKED；不代簽產品 PASS |
| P2／Owner 啟動計畫 Simplicity Reviewer | 對本版精確提交判斷批次＋獨立副本＋單筆 activation 是否最小充分 | 拒絕交 Owner；不自修或改角色 |
| P3／Owner 啟動獨立 Plan Reviewer | 核定批次範圍／明示確認、未知結果例外、LOCAL_CHANGED、非原地版本取代、GUI／writer 界線與測試可操作性 | 不能只沿用舊 PASS；若要求原地路徑、刪除或新環境處置先改計畫 |
| V1／Implementer S1 | 兩篇整合 fixture 的未確認拒絕→確認→新 candidate→單一 activation→新物件重開；舊 bytes／hashes 不變 | 任一步繞過確認、共享 raw inode 或改寫舊事實即 FAIL |
| V2／Implementer | 下列 C01–C12 故障／相容性矩陣，命令、輸出、exit、前後 manifest／hash | 不能唯一判讀、不完整結果可啟用或 scope 漂移仍可派送即 FAIL |
| V3／Owner 啟動首切片 Simplicity Reviewer | S1 精確 SHA 與 V1／已完成 V2；核對沒有框架／重複狀態庫 | 拒絕或未解 blocker 停交 Owner，不同角色自修 |
| V4／Implementer 最終候選 | 專案最小回歸、文件／help 對照、唯一日常 Prompt、既有相簿結果未變 | 產品拒絕／exit 70、範圍外差異或必要測試未跑如實阻塞 |
| G1／Owner 日常任務 Agent | 原日常入口自動找帳／找進度；正常完成貼文跳過；拒絕／同意批次確認；不需 key 或本開發文件 | 無精確日常任務／前景／確認時 NOT_RUN；不可在本 Planner 製造授權 |
| G2／Owner 日常任務 Agent | 允許的測試列表：照片＋影片、未決 chooser／下載中斷、重新下載又中斷、跨 Session；原件落檔與 candidate 完整驗證／啟用／再次跳過 | 工具拒絕、modal 不明、來源變更或未測情境分開記，不以離線結果代替 |
| A1／Owner 啟動獨立接受者 | 精確候選逐條映射 V1–V4、G1–G2；檢查歷史、目前版本、確認、再次中斷與最終可用結果；必要操作另有日常授權 | 實作者／helper 不可接受自己；實機缺項維持 NOT_RUN |

必要離線矩陣（每例保存合成來源、操作、故障位置、重開後下一步及禁止副作用）：

| ID | 情境與必須成立的結果 |
|---|---|
| C01 | 未確認／拒絕／沉默／假回覆／錯 scope：零新 intent、零 activation、原資料不變 |
| C02 | UNKNOWN 與無 outcome 都可在真實確認後建立新 attempt；舊結果原樣保留，無假 STOPPED |
| C03 | 完整貼文含已完成 sibling；scope 外正常完成／LOCAL_MISSING／排除／受保護不重下；缺項不能稱全完成 |
| C04 | LOCAL_CHANGED 在 scope 內保留舊檔並重建版本；scope 外仍擋；異常含缺檔、額外檔、hash 漂移、symlink |
| C05 | 預覽後來源／目的地／舊版本改變、同意過期、跨列表／媒體／scan 引用、同時 CLI 寫入：拒絕，無隱性擴權 |
| C06 | scan／bind 中斷、pending publish 與舊 scan：新盤點不改認領舊交易；僅批次明列的舊 plan 不再阻塞／發布 |
| C07 | 確認、intent、outcome 回覆遺失；新下載再次 UNKNOWN：新物件找回原批次，同 attempt 不重按，只換未完成項 |
| C08 | 每個 copy／fsync／驗證／manifest／activation 邊界前後故障注入：不啟用半成品；提交回覆遺失只讀回一次 |
| C09 | 舊 raw 持有 fd 晚到寫入、舊 path 重建、copy 中變動：新 candidate inode 不同；新版本 hash 不受舊 fd 改寫 |
| C10 | 磁碟滿、權限／hash／解碼失敗、candidate 額外檔、nlink／symlink／inode 漂移：停止、舊 active 保留，不自動清理 |
| C11 | 歷史 chain／v2 bundle／completion 原 bytes 不變；新 summary 一 media 一 active；舊版 fixtures 可讀，未確認舊拒絕不變 |
| C12 | exit 0／2／4／70 與單次 capture、兩次無新資訊停止；active hint 遺失仍由 lists 找回；相簿資料與介面不變 |

S1 至少完成 V1 與 C01、C02、C06–C09、C11 的直接路徑；其餘在 S2 最終候選補齊。所有 C 項都是整體接受必需，不能因分切片省略。新檔測試命令：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_restart.py
```

最終候選最小回歸沿用專案要求，不在本 Planner 執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

真實 GUI 中斷不靠整機斷網、強退 LINE 或破壞資料製造；Owner 在正式日常任務中明示可暫停／交接的階段，Agent 保存原件，另一 Session 用同一 Prompt 接續。硬斷電與磁碟故障窗口以離線注入覆蓋；未真實發生／實測的類別不能稱 GUI PASS。首次實機採另行指定且允許重下的測試列表；原私人列表是否套用新版恢復，要在當次預覽後由 Owner 精確確認，規劃本身不寫原帳本。

成功分三層：離線機制有相符證據；指定 LINE／CUA 環境用同日常入口完成中斷→確認→重下再中斷→跨 Session 啟用；原列表實際備份完成。三層各自報告。簿記 `dispatch_authorized=false`、`external_copy_verified=false`、`real_line_e2e=NOT_TESTED` 保留原意；GUI 原件／檔案驗證／真人 OBSERVED／獨立接受不可互相替代，也不保證所有模型每次成功。

## 人工檢查點、未知與停止條件

下一步建議 Owner 攜本版共同提交另開主 Session 啟動**計畫 Simplicity Review**；其後由 Owner 決定獨立 Plan Review 與是否授權 Implementer S1。Planner 不派發其他正式角色。Owner 需在實作前採納或調整三項具體預設：受影響貼文全媒體的批次範圍、獨立新路徑成為目前結果且舊檔保留、同批確認涵蓋完成前再次中斷重下。這是審閱標的，不要求 Owner 現在確認任何真實批次。

未知：原 chooser 現況、未觀察晚到 GUI 輸入、LINE 特定版本的實際下載落點與來源可用性、舊 LOCAL_CHANGED 成因、新機制真實跨 Session 表現；本輪沒有新 GUI OBSERVED。源碼支持獨立 copy 的候選方向，不等於已實作或外部能力已證明。

基準不符、chain／證據損壞、來源／列表歧義、確認缺失／scope 漂移、新寫入路徑不安全、前景失效、CUA 拒絕／未決輸入、exit 70、鎖衝突或需白名單外修改時停止依賴該前提的動作。原故障歷史嘗試不重設；同根因最多三次有證據嘗試、連續兩次無新資訊停止相同方法。新事件允許重新開始不代表無限自動重試；不足以繼續時保留已驗證 candidate、完整歷史與具體決策交 Owner。

## 本輪狀態

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

PRIMARY 只代表本規劃草案可供審閱；CORE 保留原任務阻塞與新能力尚未驗證。REQUIRED 指產品／行為／GUI 必要驗證；本輪文件與來源檢查另記報告。整體未達 DONE。
