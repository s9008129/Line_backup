# Issue #50 全問題修復重規劃 v1

本輪為 Owner 明示啟動的 **Planner**。這是待人工審查的 `replan.md`，尚未核准、實作或驗收；`plan.md` 僅指向本文，避免兩份需求漂移。本計畫取代舊計畫的「僅文件補強」作為下一次修復候選範圍，不追溯改變舊計畫、審查或完成事實。交接見 [handoff.md](handoff.md)。

## 1. 決策、成功定義與風險

Owner 要求 **MUST fix all issues**。修復範圍包括派送閉環與舊 UNKNOWN、控制可觀察性、種類延後及錯記、來源到期、證據錯引、輸出覆寫、鎖競爭、完整盤點、掃描綁定及未完成的真實 E2E；不能只再次更新文件便稱全部修好。

選定最小充分方案：沿用 Agent＋原生 CUA、notes 帳本與既有 outcome／reconcile，新增必要的證據位元核對、notes 專用輸出保存，以及保留原 key 的有界追加更正；收緊盤點／重掃 gate，修正恢復提示。**不縮小 UNKNOWN 的同列表 blocker、不新增下載重試、不另造 GUI controller。**

分級 **CRITICAL**：新增證據寫入契約、種類更正及來源不可用事件，涉及永久帳本相容性與禁止重送；不能沿用舊文件計畫的 PASS。需人工啟動計畫 Simplicity Review、獨立 Plan Review、首個實作切片 Simplicity Review，以及最終獨立 Acceptance／E2E。各角色均由 Owner 在獨立主 Session 啟動，本文不自派。

成功分開記錄：

1. **程式修復：**第 3 節每列均有候選差異與獨立驗證證據，舊帳本仍可讀，原始 events／key／completion 不改寫，新入口不繞過安全規則。
2. **既有資料處置：**已知錯種類及錯引用可證據化追加更正；未知不猜；原 UNKNOWN 只有可歸屬正面結果才調和。遺失的原件／輸出不可重建冒充，來源到期不可用程式重試恢復。
3. **原列表備份：**當次完整盤點成立，所有合格可取得媒體完成驗證、發布與 completion 讀回。到期、UNKNOWN、證據不可恢復、種類歧義及受保護歷史逐項列欠件；任一仍未解就不能稱整份完整、全部問題已修好或結案。

因此「程式能誠實處理來源不可用」可驗收其行為，但不等於到期檔案已取回。若原 UNKNOWN 沒有可用結果證據，本計畫可完成離線修補，**原列表新下載及整體結案仍 BLOCKED**；必須交 Owner 決定後續外部處置，不能把此條件從成功標準刪除。

非目標：LINE 私有 API／資料庫、讀聊天內容、相簿行為變更、任意模型／工具路由、全帳重建／rekey、全域別名系統、任意命令執行器、服務端原始位元等同性、外部副本驗證、master merge、強制 push 或自動關閉 Issue。

## 2. 基線、來源與本輪權限

- Repo／worktree：`Line_backup` 核心工作目錄；分支 `feature/line-notes-media`。
- 起始與遠端 HEAD：`d777c0148a17edc707826ff29f740dbad05f9fa7`。起始 tracked、index、非忽略 untracked 均乾淨；其他 worktree 不動。
- 驗收候選 `d41a859301d976ca62e11b75d7c8def8577e58f6` 到本輪基線沒有 src／tests／Skill 變更。`81d8138` 是驗收報告，`d777c01` 是再分析；不可把報告提交當成程式修復版本。
- [Issue #50](https://github.com/s9008129/Line_backup/issues/50) 本輪 connector 唯讀取得，仍 OPEN，含兩則留言；未寫入 Issue。
- 已讀 [原記事本計畫](../20261031-notes-media/plan.md)、[舊文件計畫](../20261101-issue50-evidence-flow/plan.md)／交接、實作及審查，並讀 [獨立驗收](../20261101-notes-media-acceptance/acceptance.md)、[最新根因分析](../20261101-notes-result-closure-review/issue-analysis.md) 及記事本 Skill／references。舊報告保持原版本綁定。
- 源碼 SHA-256：`notes.py` 為 `9cdb1f75d19ae61939b98fbea3c0fbe95367e8caef6f69b1c3724946804c36f9`；`media_verify.py` 為 `7c8051d1699449434dbaa41682a5a50f949858d593ee39cd2a1f38a1e1c6dd99`。
- 最新分析／驗收 SHA-256 分別為 `8fbc62765a8b6839db1831941e5a706a8977dda7e2c237d4d694674625a70f9d`、`daea808c08345b9254c81fa4c44cdf4f2e4c5f9f2fbfb9a3c5e8989e6321ed24`。完整來源 manifest 留本輪私有任務區。
- 示範錄影 SHA-256 `54fc234698a07ec6b36e43b50bc657ed37fe6ca3506e986a1ad0fad27ab1f0e6`，不是失敗當次。沿用前輪 PTS 判讀，本輪沒有重新擷取、解碼或操作 LINE。

本輪只可寫本計畫目錄文件及 `.local/line-backup/tasks/20261101-notes-all-issues-replan/` 診斷／交付紀錄，並依明示授權 add／commit／push。**本文下述程式與資料操作均是待審計畫，不是本輪執行授權。**

## 3. 第一性原理與完整問題矩陣

來源身分、控制定位、工具輸入、App 回應、結果歸屬、檔案驗證、帳本完成是不同命題。負面觀察「沒有 chooser／檔案」同時相容於未送達與已接受但未被觀察；本機 intent 不與 LINE 副作用形成原子交易。缺新證據就無法同時保證不重送與任意模糊結果後持續前進。[AWS 的 timeout／副作用說明](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)與[服務端冪等契約](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)支持此設計原則；套用到本案是分析推論，不是 LINE 有該契約。

| ID／問題 | 直接事實與根因界線 | 選定處置／不可省略的成功證據 |
|---|---|---|
| R1 舊 UNKNOWN 與閉環 | notes.py:2227–2312 有安全拒絕與 reconcile 出口；缺可歸屬結果，非已證實 mutex deadlock | 保留串行 gate；G0 取能力新證據、D1 唯讀核對原 attempt。只有正面結果才調和；無結果即外部 blocker，不再盲點或重送 |
| R2 控制／popup 範圍 | 舊 AX 未暴露下載節點，工具列可見性不穩定；原 click 觸發原因 UNKNOWN | G0 同 viewer 不同觀察來源／映射對照；未定位不建 intent；App acknowledgement、結果與控制定位各留原件。chooser 未存在時其可觀察能力仍 NOT_RUN |
| R3 延後種類與錯記 | kind 參與 key（:132–159）；19 項錯記報告稱尚無 attempt；record_media 不能以舊 missing＋新 key無痛更正（:1870–1947） | 未就緒不寫 media；追加保留 key 的種類更正；更正後 VIDEO 走影片驗證，媒體數／key／順序不變 |
| R4 影片來源到期 | 一項明確到期、STOPPED；resume 將所有 STOPPED／NOT_SENT 報成 RECOVERY_AVAILABLE（:2980 起） | 追加單項來源不可用，禁止一般 recovery、明列欠件；不批量推論另19項、不自動排除、不計完成 |
| R5 證據內部引用 | 外層 ref 僅 bytes／hash（:297–342），不核對文字引用；至少三個 page 有錯引報告 | 新寫入強制 structured bundle／子原件核對；舊文字可讀但未自動查核；已知錯引以原 event hash 追加 correction，缺原件不能偽補 |
| R6 輸出覆寫 | refusal／success 曾共用檔名 | notes 專用 capture 一次執行、全量 stdout／stderr／exit、唯一拒覆寫 receipt；先拒絕後成功兩份都可讀 |
| R7 summary EAGAIN | flock 非阻塞（:280–286），main 廣泛 OSError→exit4；原第一次 exit 未保存 | 僅 flock 尚未取得時分類 NOTES_LOCK_BUSY；一般 I/O 不冒稱可重試；0／2／4／70 契約不變 |
| R8 全媒體盤點 | 187 篇僅4篇詳細、183篇待盤為前輪觀察；summary 有 coverage gate，intent 僅要求scan complete及目標篇（:2195起） | 共用完整細盤判定；未完成不能派送。lazy-load／clamp 以重疊錨點補接，PNG hash不同不自動推可見內容不同 |
| R9 掃描／接續相容性 | 靜態風險：start_scan 無未決 gate（:1618），verify／resume 又要求原 scan 等於最新完成scan（:1769起、:2907） | 先恢復再重掃；未決／待驗／待命名禁止新scan；保留舊跨scan fixture，legacy mismatch明列待審，不重寫綁定 |
| R10 真實媒體與跨Session | 新影片、混合附件、chooser、popup及跨Session完整驗收皆未完成 | 在原列表 gate 合法收斂後，獨立做真實E2E，逐項來源／結果／完整解碼／completion讀回；不能用fixture、示範或另列表代替 |

R9 是本輪源碼推導風險，尚無本輪 fresh reproduction；不是宣稱又發生一次真實資料事故。187／219 events／48媒體／兩張完成照片與82／73 tests均是前輪結果，本輪未重測。

## 4. 待審修復契約

### A. 證據與輸出：機械核對，不冒充 GUI 感測

**A1 新 evidence 格式。** 保留 event 外層 ref 的 exact `{path,bytes,sha256}`，不在既有 ref 塞 attachments。新增 `line-notes-evidence/v2` 文件，固定top-level為 `schema`、`context`、`statement_ref`、`assets`。context固定五欄 `list_key/post_key/media_key/attempt_id/scan_id`；未提供值為字串UNKNOWN。statement_ref與assets的子ref固定為 `{role,source_path,bytes,sha256}`，source_path是pack時計算hash的專案內絕對原件路徑，僅作匯入來源／來源紀錄；新loader只用目前帳本evidence目錄＋digest讀取已保存子blob，**不在載入時跟隨source_path**。父bundle按原bytes保存，不改寫來源manifest，故搬走原件不影響已保存證據。僅支援一層原始資產；子JSON也只作leaf bytes，不遞迴解讀。不作自由文字hash regex parser。parent／statement及畫面／AX資產不可空，command stdout／stderr可為零bytes並照常核對其digest。

新增擬議 CLI `notes evidence-pack --statement FILE --asset ROLE PATH ... --output-dir NEW_DIR`，其中二參數flag `--asset ROLE PATH`可重複；role為statement／screenshot／ax／input_receipt／command_stdout／command_stderr／observation之一，statement由--statement提供。另以選用的 `--list-key`、`--post-key`、`--media-key`、`--attempt-id`、`--scan-id` 接收Agent從notes輸出讀回的已知context；Owner不填JSON或hash。它在專案私有任務區以排他建立新目錄、讀原件計算hash、生成bundle。接收事件的入口須傳入該命令**唯一主體**的已知context：適用的ID不能在bundle填UNKNOWN或另一ID；未分配或不適用才留UNKNOWN。page只綁list／scan，不把多個post硬塞單一post_key；post／media綁list／post／scan；outcome／reconcile綁原intent的list／post／media／attempt／scan，不改用現在最新scan。原件須安全regular file、無symlink路徑／逸出；已知schema／context／子ref錯誤須在init建立帳本／照片目錄／註冊等首個資料副作用**之前**拒絕，不能只在_preserve_evidence才查。事件接收時在持有帳本鎖內再次讀來源、比對ref，先保存子blob、再原bytes保存父文件、最後才可追加事件；若兩次檢查間外部writer改檔，後段失敗保留原件／中斷產物並停止，不宣稱原子保證。相同blob可重用，不能覆寫不同內容；未被事件引用的中斷blob保留，不在本修復清理。讀已保存v2時核對子blob，不要求原source_path仍存在。

**明確相容取捨：新 reader 讀舊 v1 opaque evidence；所有新 evidence 寫入改為要求 v2。** 原有 `--evidence FILE` 參數不改名，舊文字新寫入以 `EVIDENCE_BUNDLE_REQUIRED` exit4拒絕。新loader對明確 `line-notes-evidence/*` 家族的不支援版本拒絕；其他歷史不透明文字／JSON依舊按舊外層規則讀，標 `LEGACY_OPAQUE`，不得自動升格REFERENCE_VERIFIED。實作者須更新 notes 的新寫入fixture，不可把舊相容fixture換成新格式後聲稱相容。bundle的context只作已知ID一致性檢查，資產位元完整不證明畫面真實、控制命中或terminal outcome。

**A2 舊證據稽核／更正。** 新增唯讀 `notes evidence-audit --records-root ROOT`，共用loader的event結構／sequence／hash-chain檢查，列外層／子資產核對、legacy未查核與correction關係；不得只呼叫遇第一筆evidence漂移就停止的一般summary，也不得另造放寬帳本規則的parser。event chain本身不可信即停止；可解析時逐引用稽核、完整性錯誤exit4且不輸出可信業務狀態投影。只有legacy opaque並不算損壞，正常audit exit0仍需明列REFERENCE_CHECK_NOT_AVAILABLE，不能當原引用已核對。已知page錯引用 `notes evidence-correct` 追加 `line-notes-evidence-correction/v1`：target page event sequence＋SHA-256、原evidence SHA-256、replacement v2 ref、reason、session_id。僅對page evidence，bundle scan context比對**target page當時所屬scan**而非現在最新scan；不改page成員、順序、頂底或scan覆蓋。重複更正須顯式引用前筆correction sequence＋hash，拒絕覆寫／分叉。新摘要顯示原證據與更正鏈，不把外層hash當語意證明。原件若無法確定屬於原page，列UNRECOVERABLE，不補造舊成功。

**A3 不可覆寫輸出。** 新增小型 `notes_capture.py`，入口 `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes_capture --output-root PRIVATE_TASK_DIR -- <notes子命令及參數>`。固定以同一Python interpreter、專案src模組及argv陣列執行 `-B -m line_backup_batch.notes` 一次，記錄解析到的程式路徑／hash；不開shell、不接受其他執行檔、不支援capture遞迴、不操作GUI、不自動重試。先在專案私有任務根目錄建0700新UUID receipt目錄、以O_EXCL／安全regular-file檢查保存並讀回request，再啟動child；全量分別保存stdout、stderr及exit／signal、開始／結束時間與時鐘來源、程式版本，hash／fsync／讀回後最後發布complete receipt。成功、argparse拒絕、業務拒絕、exit70皆保留；child crash或receipt失敗留INCOMPLETE，絕不為補輸出再執行child。**只有capture完整成功才傳child exit**；任何捕捉／持久化失敗wrapper回70，已知child_exit仍照實保存，未知留null，不能把child=0冒稱整次成功。完整保存signal結果時以128＋signal作外層exit，另存真實signal、child exit=null。這只是簿記入口，沒有GUI派送權限。

### B. 種類：保留身分、在 attempt 前凍結

**B1 新項。** Skill以同一viewer連續脈絡及正面種類特徵確認就緒；disabled滑桿、00:00、黑畫面、placeholder或沒看到影片控制，均不足以判PHOTO。照片需有當次可區分的照片專用控制／脈絡，影片需正面播放／時長等證據；是否可取得足夠訊號由G0記錄，不能用固定sleep保證。未定種類保留私有觀察、讓該篇media coverage未完成；不先建PHOTO key，不新增第七類媒體狀態。

**B2 已有錯記。** 新增 `notes media-kind-correct`，事件 `line-notes-media-kind-correction/v1` 綁定media_key／post_key、最新scan、原inventory sequence＋SHA-256、from_kind／to_kind、前次correction ref（首筆null）、v2證據與session。只允目前存在、同篇可唯一辨識且**更正當時從未有任何attempt／verification／completion／exclusion／protection**的key；同值、舊scan、cross-list／post、hash錯、分叉、missing或來源歧義拒絕。寫入及load-time均按事件sequence核對此前事實與前值，不因更正之後合法建立的v2 attempt而拒讀整帳。原identity、media_key、event、source_order、媒體總數不變；新scan沿用原identity／key，不按新kind重建來源。

摘要保留原 `kind`／`identity.kind` 原義，新增 `effective_kind` 及correction ref；既有使用者明確改讀effective_kind，不靜默改舊欄語意。新intent寫 `line-notes-intent/v2`，保留舊欄位，另凍結 `effective_kind` 與 `kind_correction_ref`；無更正時ref=null。新reader仍讀合法舊intent/v1，按原identity.kind驗證；若該key此前已有kind correction卻出現v1 intent，load拒絕，不靜默忽略更正。v2必須等於該intent之前有效更正結果。verify、verification graph及發布副檔名採attempt凍結種類（修notes.py:1263、2927等相關讀取點），不用當前可變投影。completion／舊verification格式不變；attempt後種類矛盾停止，不把更正功能擴用到已派送項。

### C. 來源到期：不可取得與可恢復分開

沿用原attempt的STOPPED，不把到期當完成或默認排除。新增 `notes source-unavailable`，追加 `line-notes-source-unavailable/v1`，含media_key、post_key、原attempt_id、明確 `reason=SOURCE_EXPIRED`、v2 evidence、session。只允最新且已正面停止的attempt、同項無completion／pending naming／未決寫入且無既有到期標記；不能把UNKNOWN直接轉來源不可用。loader按該事件之前的歷史prefix核對當時最新attempt及來源鏈，拒絕到期標記後任何新intent／recovery，不只在writer加gate；後續合法重掃不讓既有到期事件失效。B2的最新scan／inventory亦按更正事件當時的prefix驗證。

摘要新增單項 `source_availability=EXPIRED`（無此事件為UNKNOWN，不宣稱AVAILABLE），六類仍為PREVIOUSLY_INCOMPLETE；current_incomplete不減。intent對此key拒絕 `SOURCE_UNAVAILABLE_NO_RECOVERY`，resume對此項列SOURCE_UNAVAILABLE而非RECOVERY_AVAILABLE；其他項仍受原UNKNOWN等列表gate約束。舊STOPPED／NOT_SENT若無可用性紀錄，resume改列RECOVERY_REVIEW_REQUIRED，不暗示可自動重下；實際恢復仍需原持久授權與新的、可歸屬恢復證據。排除或解除到期標記不在此計畫自動執行；若Owner後續要改，須另有明確資料決定及證據，不能用新attempt探測來源是否恢復。

### D. 盤點、scan 與恢復順序

1. 啟動先lists／memory及新增摘要 `unresolved_attempts` 對帳，再決定bind後恢復或重掃。每項須顯示intent的scan、has_outcome、最後結果、原目的地、pending naming及scan_binding_match；這是事實投影，不授予下載。
2. `start_scan` 在新事件前重用 `_assert_no_unknown_attempts` 並檢查pending naming，拒絕無outcome、UNKNOWN、DOWNLOAD_FINISHED待驗及待命名。已完成／正面停止項不因此被重下。未知未解時只可在當次授權內蒐集觀察，不能開新scan破壞舊綁定。
3. legacy已跨scan未決項仍可load／summary；resume對不符項回SCAN_BINDING_REVIEW_REQUIRED，不默改intent.scan_id、不隱藏它或自動新建scan。保留目前pending publish-plan分支在命名／發布前核對attempt scan的既有保護，並同步改為可辨識的待審結果；不能只改最後pending清單卻先執行發布。本案是否已發生此漂移UNKNOWN；若真實資料有此情況，停止該資料處置並交Owner另定有證據的綁定修復，不能套用本方案假稱已修復。
4. 抽出共同的細盤coverage判定供summary及intent使用。需列表頂底／重疊成立、所有現存篇有本scan detail、media數覆蓋一致、無stale。只攔coverage條件，不拿整份summary所有blockers粗暴套用，維持原attempt gate錯誤語意。純文字篇仍NO_MEDIA，不建立媒體。
5. 完整逐篇盤點是下載前必要階段；沒有未決attempt時，UNKNOWN以外的待盤篇以小步重疊補接。placeholder／clamp／單次無位移不當底端，PNG bytes不同不等於卡片語意不同；記清AX、卡片錨點與各截圖範圍。

### E. 鎖競爭與退出碼

只在 `_file_lock` 的flock呼叫且尚未yield時捕捉EAGAIN／EWOULDBLOCK，轉 `NOTES_LOCK_BUSY`，附collection／records scope。exit仍4、dispatch_authorized=false；只有lists／memory／summary／新的純唯讀evidence-audit在此精確條件下可標 `retry_safe=true`。resume可能執行發布，不屬唯讀allowlist。CLI／capture都不自動重送；Skill僅允相同唯讀命令有界再查，保留每次receipt，遵守既有兩次無新資訊停止。其他OSError維持既有業務拒絕契約，不假裝LOCK_BUSY；exit70保持INTERNAL_ERROR／UNEXPECTED_EXCEPTION，不可重試。不得刪lock、猜holder或根據mtime強解鎖。

## 5. 實機能力與既有資料：不得顛倒的 gate

**G0：不下載能力診斷。** Owner另行交接同列表的已知viewer並明確授權唯讀觀察及必要的單次viewer內移鼠；讀當次工具文件，以app-bound AX／畫面與工具支援的最小桌面區域對照，保存時間、來源範圍、像素、frame、座標映射、控制可見性與所有UNKNOWN。不點中央、下載、分享或chooser，不建intent。若沒有現成chooser，不能為測觀察而開下載，chooser能力保持NOT_RUN。成功是取得新的來源對照／映射能力結論，不是舊UNKNOWN已未送達；能力不足即停止依賴它的新派送。

**D1：原 UNKNOWN 調和前檢查。** 獨立於G0，唯讀查原intent、第一筆outcome、全部reconcile、原目的地及指定私有原件，不廣搜私人資料。下載完成需原attempt／viewer／目的地可唯一歸屬的終結結果＋穩定檔；停止／未送達需能正面排除原操作稍後繼續的證據。timeout、空目錄、工具成敗、目前無toolbar、關閉viewer或Owner口頭保證均不足。找到證據才在明確帳本授權內append reconcile；沒有就保留UNKNOWN，停止新下載。G0的成功不能跳過D1。

**D2：資料更正預覽及應用。** 完成程式切片與獨立資料相容核對後，由Owner另授權針對該帳本的唯讀預覽：列原event sequence／hash、確切更正對象、原件關係、預期追加事件、前後投影與不可恢復項；確認已知19項真的均未有attempt，不能只信舊報告。保全ledger及私有原件的獨立可讀快照、hash與恢復入口，禁止symlink，目的地不能是唯一原件；保存快照不改events。前景及帳本有新writer／event變動就使預覽失效。Owner批准**精確預覽**後，逐項以正式CLI追加kind、page證據與單項到期紀錄；每步讀回，prefix event bytes／hash及原完成不變。不得把未確認項一律改VIDEO或一律標到期。

**G1：真實下載門檻。** 僅在D1合法收斂、無活動／待驗／待命名／LOCAL_CHANGED、D2必要更正完成、當次盤點完整、G0可用且Owner具體下載任務與前景有效時進行。單項下載控制與chooser確認各最多一次，各有原始工具回傳；chooser須歸屬原viewer／attempt、讀回完整暫存路徑；API error亦不得再點。結果不明回UNKNOWN並停止，晚到結果只能先歸原attempt。

**G2：獨立實機驗收。** 在同原列表選實際可取得且來源已確認的照片、影片及混合附件篇；條件不存在就NOT_RUN而非改去另一列表。影片的播放結束／重播不是下載完成，照片toast不是所有媒體通用條件。驗證穩定檔集、預期1項、非空、SHA-256、ImageIO或成對Homebrew ffmpeg／ffprobe完整解碼，發布並讀回completion；跨Session以受控中斷的既有交易接續，不以故意再點製造UNKNOWN。無法安全安排chooser延遲／前景中斷時保留NOT_RUN，合成覆蓋另列。

## 6. 精確可寫範圍、相容與回復

待審實作白名單：

- `src/line_backup_batch/notes.py`：新證據入口、上述三類追加更正／來源事件、intent/v2及投影／gate／退出碼。
- 最多新增兩個notes專用模組 `src/line_backup_batch/notes_evidence.py`、`notes_capture.py`；前者只處理位元引用與不可覆寫資產，後者只包notes子程序。若現有函式內可清楚完成，無需為湊模組拆檔；不得擴成controller、任意runner或通用schema框架。
- `tests/test_notes*.py`、必要的新 `tests/test_notes_evidence.py`／`test_notes_capture.py`、去識別化合成 `tests/fixtures/notes_v1/`；保留原測試要證明的安全性，不刪除難通過的歷史案例。
- `.agents/skills/line-notes-agent-cua/SKILL.md` 及其references、`docs/LINE相簿備份_使用手冊.md` **記事本段落**；同步新證據產生／capture、先恢復後重掃、種類及到期處置，不要求Owner填內部JSON。
- 本任務目錄後續角色報告。審查後的replan／handoff不得被Implementer靜默改寫以迎合實作。

禁止修改相簿 `daily.py`、`image_decode.swift`、相簿Skill、離線OCR、相簿測試、現有驗證器 `media_verify.py` 的驗證標準、AGENTS／全域政策、舊任務與審查。不得直接寫 `backup/`、`backup-records/`、`notes-backup-records/`、active task或LINE；只有D1／D2／G1／G2各自另獲適用授權，才可按其最小範圍操作真實資料。所有原始來源、真實輸出與照片保持Git私有。

相容承諾是**新reader讀舊資料**；舊reader會對新事件或intent/v2 fail closed，不能宣稱雙向相容。僅含v2 evidence而未有新事件時，舊reader可能仍當opaque文字讀取而漏查子資產，亦不得視為安全相容。新格式初次落入真實帳本前須有獨立相容驗證、快照與Owner精確資料批准；此後不得只回退舊binary繼續寫該帳本。程式可在尚無新資料時回退；已有新格式資料時保留新reader、停止寫入，再交人決定向前修正，不刪除／截斷events，不回滾照片發布事實。

原生GUI、外部writer、檔案capture與App接受沒有共同原子鎖；本機flock只序列化合作程式。重複檢查、hash及fsync能檢出指定邊界的漂移，不能保證外部程序永不改檔、所有popup都被觀察、exactly-once或服務端位元等同。未提供的provider／CUA能力均UNKNOWN，不自行增加付費模型呼叫或新控制通道。

## 7. 實作切片、相依與檢查責任

| 階段 | 內容及相依 | Owner／必需證據／停止條件 |
|---|---|---|
| P0 計畫審查 | 此replan＋handoff＋精確提交，CRITICAL新邊界 | Owner啟動Simplicity Reviewer再啟動獨立Plan Reviewer；核對新寫入格式、三類事件、intent/v2與資料操作gate。拒絕就停止，不自修計畫或派實作 |
| S1 **首個可驗證切片** | A1新bundle／舊讀相容、A3 capture、E lock分類；獨立於真實GUI及資料 | Implementer僅合成fixture；證明新寫錯ref零event、v1讀取不變、輸出不覆寫、真flock競爭分類。交精確commit、diff、命令／exit後停止，由Owner啟動實作Simplicity Review |
| S2 帳本與安全gate | S1通過後做A2、B2、C、D，及Skill／CLI更新；G0可由另授權診斷平行取得，不是S2合成測試PASS前提 | Owner重啟Implementer；核對有效kind在attempt前凍結、舊scan／key保留、expired不恢復、coverage一致。任何需改白名單或資料語意即停止 |
| S3 操作契約與整合 | B1、全部Skill／手冊及最後回歸；保留唯一啟動範本 | Implementer交全部R1–R10矩陣；無實機證據者列NOT_RUN，不替自身提供獨立acceptance |
| A0 獨立本機相容驗證 | 最終精確候選；獨立於實作者／helpers | Acceptance核對所有合成檢查、v1golden、追加event順序及資料preview規則；錯誤不得追加有效事實event、派GUI、覆寫原件或改完成事實，明列的未引用中斷blob保留並回報。缺相容證據禁止D2 |
| G0／D1／D2 | 第5節的獨立授權與依賴 | 另行指定任務執行者；真實操作前由Owner給資料／前景授權，缺原件／新writer／缺能力即停止。D1無證據時不能進G1 |
| G1／G2 最終實機 | 所有下載gate成立及精確候選；不可藉另列表繞過 | Owner啟動獨立Acceptance／E2E，保留原始工具回傳、檔案與completion、六狀態及欠件。原列表無法完整處理則整體不結案 |

每個有程式改動的切片執行專案最小回歸，實際argv、stdout／stderr、exit與工具版本存專案私有任務區；不要預填測試數：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
git diff --check
```

必要針對性檢查（皆由Implementer先跑、Acceptance獨立核對；除實機列外只用合成隔離資料）：

- **T1 evidence：**v1 frozen資料新reader投影不變；完整v2重開且原source_path移走仍可讀；父／子缺件、錯hash、symlink、逸出、duplicate JSON key、不支援版本、context衝突皆拒絕；init已知無效bundle在建立資料前拒絕，鎖內再查漂移；寫入失敗零有效event、保留明列中斷產物；已保存子檔漂移load拒絕；legacy不自動升格；page correction原hash／鏈錯拒絕，正確更正不變page／scan語意；audit能列引用漂移且exit4，不以被拒絕的summary當可信投影。
- **T2 capture：**相同命令兩次各新目錄；refusal→success原兩份都在；完整保存0／2／4／70與signal；child=0但receipt磁碟失敗時wrapper=70、child_exit=0且只執行一次；中斷不能自動重執行；receipt目錄／檔名碰撞或symlink拒絕且child執行次數0（--output-root是可既存的安全父目錄）；正常情況child執行次數1。
- **T3 kind：**19項合成更正總數／key／source_order不變；cross-list／post、stale scan／inventory hash、歧義、attempt後或完成後更正均零追加；v2 intent／verification用VIDEO驗證器；重開／新scan仍沿原key；合法v1 intent與completion保持原行為；更正後偽造v1 intent、attempt前後錯序load拒絕，更正後合法v2 attempt可重開。
- **T4 expiry：**STOPPED＋單項到期事件維持PREVIOUSLY_INCOMPLETE並禁該項recovery；重複標記、偽造到期後intent／recovery在load拒絕；無資料不能推另19項到期；UNKNOWN不可用source-unavailable終結；舊STOPPED提示REVIEW_REQUIRED且不自動重送；未授權排除不改EXCLUDED／COMPLETED計數。
- **T5 coverage／scan：**summary與intent對全部細盤缺口一致；NO_MEDIA正確；UNKNOWN／無outcome／VERIFY_REQUIRED／pending naming禁止新scan；原scan仍可正常調和與verify；舊跨scanUNKNOWN保護案例保留為legacy fixture，不靠新writer製造舊bug，也不刪測試；resume對mismatch不改綁定，pending命名分支亦須零檔案mutation。
- **T6 lock／exit：**真正子程序持collection／records flock，另一唯讀命令精確LOCK_BUSY；釋放後可成功。非flock讀寫EAGAIN不能retry_safe，mutation／resume不能retry_safe，exit70不重試；保留0／2／4／70與UNKNOWN intent拒絕測試。
- **T7 真實：**G0來源範圍與映射、D1舊attempt結果、D2追加更正、照片與影片完整解碼、混合附件、chooser／popup、前景與跨Session接續及完整列表對帳逐項列證據；缺授權、能力、原件或可取得來源即BLOCKED／NOT_RUN，不准以單元測試替代。

## 8. 替代方案、止損與交接決策

只改Skill／固定sleep不能機械阻擋錯引，前輪已完成該切片；直接重點或縮鎖不能解決舊結果歸屬。rekey／alias全帳遷移會擴張去重風險，故採凍結identity＋只對未派送項追加kind。到期自動exclude會擅自改Owner目標，故來源可用性與六類狀態分離。任意manifest graph或GUI observer需要更多新能力，故只用一層資產與現有CUA。純shell命名規約較小但無一致拒覆寫保證，選notes專用capture；不擴成任意runner。

停止條件：缺基線／來源、版本漂移、審查拒絕、工具拒絕、身分／前景歧義、未決派送、已完成原件異動、需改相簿／decoder、需放寬不重送、需修正已派送種類、需改舊scan綁定、缺必要能力、資料preview與現況不符，均保存最小重現及已證結果交Owner。每根因最多三次有證據嘗試，連續兩次無新資訊停止；原實機歷史不完整，不因換角色重置或宣稱尚餘次數。不能用一般恢復授權概括新事件資料應用。

下一個人工決定是：以本次精確規劃提交啟動 **計畫Simplicity Review及獨立Plan Review**，明確審閱上述新格式／事件／intent版本／gate。通過後才由Owner另啟動S1；G0、D1、D2、G1/G2各自仍須適用授權。若外部證據不足，保留未解項與整體BLOCKED，不把「設計已有安全停止」當成已完成原列表備份。

## 9. 本輪實際工作及狀態

本輪執行Git狀態／branch／HEAD／worktree、遠端精確HEAD、來源讀取、SHA-256及基線diff核對，命令皆exit0；GitHub fetch_issue為isError=false。兩位同角色helper分別唯讀核對evidence／receipt／lock與kind／expiry／coverage／scan；dispatch未供model或effort override，沒有provider用量，不據此宣稱backend身分或成本。主Session已以源碼複核其關鍵結果；helpers不是獨立審查。

本輪未跑產品tests、未操作GUI、未讀寫真實帳本／照片、未執行本計畫。實際命令、來源manifest與進度保存在 `.local/line-backup/tasks/20261101-notes-all-issues-replan/`。文件檢查與Git交付結果另記實際輸出；不將提交／推送當產品acceptance。

```text
PRIMARY_OUTCOME_STATUS: PLAN_DRAFT_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

NOT_RUN指本重規劃的產品驗證尚未執行；原候選獨立驗收的BLOCKED與已證結果保留。本文具體定義全問題工作及不能越過的外部gate，不預先承諾不可取得證據或到期來源一定能恢復。
