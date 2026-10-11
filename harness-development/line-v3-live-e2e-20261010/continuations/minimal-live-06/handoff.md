> **給接手 Agent 的精準執行 prompt（IMPLEMENTER）**
>
> 你是這一輪的 Implementer。使用者指定 project root 為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；你的唯一執行計畫是同目錄的 `plan.md`（minimal-live-06）。先完整讀本交接、Plan、ROOT/AGENTS.md、上一輪 recovery-02 的 E2E 報告、implementation-result、attempt-ledger、83 筆 report-manifest 原始證據，以及其 `檢討報告.md`，再動手。你要把真正的 CUA LINE 畫面接到正式 capture→原樣留存/讀回→native/SCK/OCR→strict 17-key frame→Python validator；先用同一 production entry 的唯讀 probe 證明真實連接可用，再在必要離線 gates 全 PASS 後，完成第一本真實備份、全檔驗證與 canonical 狀態讀回，釋放 owner，實際向下捲動 0.25 view-height 到新內容，再完成不同 eligible 第二本。不得把 fixture、空 cards、歷史成功、人工作業觀察或只完成單本交易流程寫成兩本 E2E PASS。
>
> 原產品 root issue 的 3/3 已用盡；使用者已明確核准「一次有界延續，接到兩本 E2E（建議）」。保留原歷史，本輪只有額外 1 個驗證集合，每個正式 check ID 只 launch 一次；必要檢查失敗就停止依賴它的步驟，保留原始證據、收保全與報告，交回 Replanner，不在同輪改後重跑。先兩次 prewrite metadata anchors，再依事前 exact output policy materialize 本輪工具及相同契約，完成完整成對基線，才修改產品／擷取產品證據；inventory/streams/compare 全先在 host 記憶體完成，最後 exclusive 發布並讀回，FIFO 只 lstat，partial scan 只能 BLOCKED。不要再讓檢查自己寫出的 stdout 造成保全誤判。
>
> 只可串行修改 Plan §4 的 9 個產品 literal paths、本輪 task dir 與其列出的正常交易 state/ledger/destination；不更換 writer、不 migrate、不改 config、不降低 gate、不清除既有 dirty/untracked/ignored 或舊 FAIL。GUI 只用 documented CUA，repo native 只 passive observe/capture/OCR/decode；不增加 AppleScript、AX actuator、shell GUI、外部 daemon。GUI ledger 共用原檔與原 quota；固定 temp 要 exclusive create，碰撞不刪，只有本次建立且 dev/ino 仍相同才可 cleanup。
>
> 在第一個產品證據動作前登記本輪 extension/attempt；最早 raw CUA capture/retain 是診斷，不是 G_REAL_LINK。CUA host 的 ambient `process` 不可用、`node:process` import 被阻擋，不把 CLI Node 版本當 host 版本；實作真正 host hooks，不注入 fixture callback。保留 state schema 3、17-key frame、5 秒 freshness、600 秒 catalog age、at-most-once Save All、一次 chooser confirm及既有 shared CAS/readback。Chooser 每階段以真實當下控制與 full-path/destination continuity 判定，leaf alone 不足。任何 input 前先透過提問管道請使用者交還 LINE 前景並等待明確回覆；這是操作前提，不能假設已完成。Save All 不確定永不重送。
>
> Plan Review 已由使用者明示豁免，記 USER_WAIVED_NOT_RUN，不安排獨立 Plan/Handoff Review；父任務獨立 Acceptance 仍 required。缺 native Harness stage packet／固定 runtime 時如實記 NOT_RUN，不自行補 validator，也不藉此推遲本契約已授權的安全產品實證；正式 closure 未滿足就不能 DONE。最後必交本輪 E2E測試報告.md、progress.md、attempt ledger、format 3 implementation result及逐檔 hash/絕對路徑 manifest，分列六個狀態與每本／scroll／保全 gate，保留部分成功和所有失敗，交回指定 Replanner。你沒有本輪產品 commit/push 授權，不提交其他人的工作。

# HANDOFF：minimal-live-06 精準執行交接

日期：2026-10-11；來源角色：PLANNER／Replanner；接手角色：IMPLEMENTER。

## 1. 位置、權威與文件關係

| 名稱 | 精確值 |
|---|---|
| ROOT | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup |
| PLAN | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/plan.md |
| HANDOFF | /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06/handoff.md |
| R | harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06 |
| TP | harness-development/line-v3-live-e2e-20261010 |
| P | harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02 |
| 父 task_id | TASK-20261010-line-v3-live-e2e |
| 新 run_id | 接手時建立並持久保存的 fresh UUID；不要使用上一輪 a8e86935-d398-4e9c-b860-03f52cba8fec。 |
| owners | minimal-live-06-g1、minimal-live-06-g2 |
| 當前出版錨點 | HEAD 7cea58d42072d9da6140c36157aa1580fe320bdb；branch v43-ab/codex-rev28；接手必重新核對。 |

本交接依 `/Users/hsiaojohnny/.codex/prompts/v4.8.0/03_handoff_prompt.md` 的要求採**確定性契約複製**：附錄 A 與 Plan 附錄 A 原始 bytes 完全相同，不擴範圍、不改 gates/check owners。該 prompt 是 Optional Handoff Reviewer 的規範，不是要求每次額外跑模型審查；本契約 handoff_review_required=false，沒有獨立 Handoff Reviewer PASS。此文件是 root 編寫並做本地 equality/readback 的交接包，不冒稱 controller-generated native packet。

Plan 是唯一完整的決策／argv／scope／gates 規格。本文件明列接手順序及易錯處，不取代 Plan，不產生另一組權限。讀兩份附錄 block、計算 raw hash，若不相同先停；不能挑一份繼續。

## 2. 要繼承的事實，不要重做或誤判

### 2.1 上一輪已證明的部分

recovery-02 基線37/37、runner11/11、adapter離線15/15（Node31/31）已PASS。FIFO只lstat且四份觀察一致，239既有backupregularfiles逐檔read_verified。保留這些歷史成果；本輪因source/build不同且reuse=NEVER，新的formal checks仍需本輪證據。

G_PRESERVE仍FAIL：p1→p2漏列兩個自身stdout/stderr，且第一個stdout完成時從0到725bytes，出現5項欄位不一致。工具輸出生命週期與allowlist不合，是可重現的直接原因。既有FAIL不改PASS、不覆寫收據。b1→p2「scope外零差異」是已觀測保存事實，但事後從diff組成的planned-additions不能證明所有寫入在事前已核准。

83-entrymanifest與implementation-result實際存在、hash讀回完成；舊報告/進度仍寫tailPENDING。以新reconciliation保留兩者時間與來源，不能修改歷史敘述裝成一直一致。68個removedpaths屬baseline-selftest；runner只列fixture根1個；failed-smoke兩樹缺刪除收據仍UNKNOWN。

### 2.2 尚未證明的部分

目前這輪production analyzer／nativegeometry／catalog／chooser／scroll／兩本下載狀態鏈未實機完成。現有emptyALBUM_DETAILfixture不能證明合法ALBUMS；keysortbug與intersection欄位遺失仍需本輪接線修正。不要說「完全沒有備份成功」：canonicalstate已有兩本歷史VERIFIED，但它們不是本版兩本E2E證據。

既有state3/revision35、owners/context/batchnull、configcap1；參考hash見Plan§3.2。開始必fresh核對及完整baseline；未知writer/intent與config身份變化都需要停下來，不能直接寫回參考值。

### 2.3 根因與本輪驗證重心

真正缺口是正式程式**怎麼把當下看到的對象轉成可以安全點擊、下載與提交的證明**。大量mockPASS沒有填補producer缺口，工具失敗又消耗了產品嘗試。Plan03不是完全沒有早期capture要求，而是沒在實際時序取得可用proof。本輪最早拿raw真實樣本，接通同一productionentry後立刻probe，再執行完整offline與下載。最終答案由實機證據決定。

## 3. 必讀原始證據與核對順序

先讀以下絕對路徑，不只讀此交接摘要：

1. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/AGENTS.md`
2. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/E2E測試報告.md`
3. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/evidence/implementation-result.json`
4. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/evidence/attempt-ledger-recovery-02.json`
5. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/evidence/report-manifest.json`（全部83項files[].absolute_path；逐筆bytes/hash）。
6. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/scope-recovery-05/recovery-02/檢討報告.md`
7. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-04/plan.md`
8. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan.md` 及該目錄 live_runner.mjs／live_classifier.mjs／chooser_locators.mjs。
9. `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/implement-02/user-decision-A.json`
10. `/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md`；如進入GUI／驗證，讀其state-contract/evidence/state-machine/ui-procedure/verification references。Skill的歷史state2說明不能覆寫本專案已採用的canonicalstate3；本輪明確禁止migration。

Plan§3提供主檔bytes/hash；完整inputmanifest需列relative＋absolute＋hash＋讀取結果。manifest引用不是使用者再授權修改其路徑。來源不在預期位置、hash不合、檔案型別不合，先保存差異，不自動換一個來源。

manifest 的83筆為81筆專案內檔案與2筆固定外部Python／Node runtime。對外部項只用Plan§7精確路徑唯讀核對bytes/hash，不把它們當repo內檔或取得環境修改權。

## 4. 先完成授權與保全 bootstrap

### 4.1 Git與filesystem

接手先inspect HEAD／branch／index、11個原有trackeddirtypaths及全部untracked/ignorednamespace；不可reset/checkout/clean或整批stage。Plan出版commit使HEAD變動是正常繼承，需要freshbaseline，不以出版前HEAD硬拒所有後繼。

兩份doc已存在於R，`.local`是出版只讀現場；先在記憶體取得兩次prewriteanchors，事前列bootstrapexactoutputs。extract附錄A原bytes（LF規則見附錄），exclusive建立`R/plan-contract.json`、bytecopy`R/handoff.json`；記hash，先本地equality/readback。不聲稱nativevalidation。

同時建立新`input-manifest/reconciliation/attempt-extension/plan-review-waiver`及bootstrappolicy；建工具後跑E01/E02；B01完整成對掃描PASS才可做產品source修改及D01。這個順序避免「要工具先完成基線，但工具又要基線才能寫」的循環。prewriteanchors不是G_BASELINE替代品。

### 4.2 保全工具實作重點

新`tools/inventory_pair.py`重用P純readscan，不調舊self-writingmain。所有scanrecords/streams/compare留hostmemory，兩掃描間不落地輸出；完成後按immutableexactpolicy發布/readback/directorydelta。超時或partial只BLOCKED，不能對空records計missing。計時從scan前開始。knownFIFO只lstat；未知speciallstat留證並stop。

新`checks/run_command.py`固定ROOT，不用parents推導；source/runtime/spec/id/cwd/HEAD/branch/indexpreflight；argvarray/shell=false；明示env、每childtimeout/cap、launchclaim、stdout/stderr/readback，正式ID不重用。oldMODULE_NOT_FOUND不當adapter語法失敗。

allowpolicy先凍結，observedmanifest後產生；frame/action等每個動態檔需先登記exactnormalizedpath，kind/sequence/cap依Plan§5。不免除整個tmp/evidence目錄；report/manifest/result尾檔按預宣告順序處理自我引用，不能事後回填許可。保全失敗收據不覆寫。

## 5. 任務實作地圖

### 5.1 Product scopes（與Plan相同9檔）

| 檔案 | 最小必要工作 |
|---|---|
| scripts/line_backup_cua_adapter.mjs | 保留現有cross-realmnormalize；phase/version-awarechooser；無fixtureauthority，atomicpair不插入觀察/持久化。 |
| src/line_backup_batch/cli.py | R contract/hash/continuation、正式sourceclosure/grants、sensorbinding一致；read-onlyprivateframe_supportwrapper不新開publicmutateAPI。 |
| src/line_backup_batch/observations.py | strictv2raw/native/visualwitness與chooser階段語義，JS/Python一致；17-keyframe不變；v1歷史read-only。 |
| src/line_backup_batch/store.py | sharedlock下固定ledger-temp安全exclusivecreate/identitycleanup；原schema/quota/CAS/replace/readback不變。 |
| rev28/Sources/rev28ctl/main.swift | native-context與R/hash綁定，mandatorybefore/after/frame/ref/grantargs，重用support/guard/decode，不加actuator。 |
| rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift | actualAX/SC/CG/process/display/permission原始觀察與identityinterval；unknown/null/truncation不補造。 |
| rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift | AX_NATIVE或已核准單欄VISUAL_NATIVE的pixel/nativecontainercard/thumbnail/metadata證明與OCR。 |
| rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift | permission、identity、window/crop/scale/displaydrift、null/truncation及ref測試。 |
| rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift | legalnonemptycard、boundaries/thumbnailexclusion/safemargin/date/count/partial/duplicate/mismatch測試。 |

其他productfilesreadonly。新檔已存在先stop，不覆蓋未辨識工作。Package.swift／dirtyComposition/Sensor/tests不在scope；新測試可用taskchecks及上述兩個Swift檔。必要變更若超出scope，寫明確newplan需求，不偷偷改。

### 5.2 Task host modules 與真實資料流

R內：`host_io.mjs`→`live_entry.mjs`（probe/runTwoAlbums共用）→`live_runner.mjs`／`live_analyzer.mjs`／`live_classifier.mjs`／`chooser_locators.mjs`／`checks/validate_real_frame.py`。producer在`R/bin/rev28ctl`。

接口必須真實接上：

- 真正CUA app（`cua.getApp('jp.naver.line.mac')`；新runtime首調依其tool規定先只做entryAPI），documentedcapture/input。先讀返回文档，再使用API。
- filesystem/processhooks支援readback、exclusive/no-follow、固定cwd/argvarray/env/caps；不假定ambientprocess，CUAhost與CLINode版本分開。
- nativebefore→CUAretain→nativeafter→SCKsupport/OCR/analyzer→strictclassifier/Pythonframevalidator；同一process/window/display/layout與實測mapping。
- analyzeCapture／captureCatalog／prepareCandidates／finalRecords／locateMenu／locateBack／producerGeometry／scrollTarget／preparePostReleaseScroll全部await真正productioncallbacks，非fixtureclosures。
- decoder/read-onlypoll及canonicalCLIcommand；JS不可直接寫canonicalstate或改rawJSONnumeric歷史。

rawsample先驗證crossrealmbytes/offset/length/PNG/hash/readback。formalprobe是同一entry，不另做一条「只為測試能PASS」的pipeline；非空ALBUMS、完整唯一card、native/CUAprovenance與fullPythonvalidation要在真實樣本成立。probe不可begin/prepare/intent/UIinput；state/config/ledgerhash應未改。

### 5.3 Grounding固定要求

17keys精確沿Plan§6.3；strictv2auxiliaryevidence同步JS/Python。boundarykeyset一致排序、forwardintersectionPx。before/after真實原生dump，不fakeAXenabled/index/image/bounds；CUA與nativeindex不能以ordinal對接。只對支援的單欄layout提出VISUAL_NATIVE。日期文字只定位候選，真實container/pixel/thumbnail/exclusion/鄰卡/safeerosion完整後才能click。

保留5秒freshness、600秒catalogage、3non-collinearuniqueanchors、trianglearea≥0.02、residual≤2sourcepx、uncertainty≥2、margin≥uncertainty+4、intersection≥16×16。遮蔽/croporigin/PID/window/display/scale不唯一即stop；timestamps不隨OCR/retention更新。parse rawdate/count/group不猜缺年/跨年/近似群組。未知focus不改NONE；LOW_GHOST只用原class1政策。

### 5.4 Chooser phase 接手核對表

APPEARED需真實root/ownercontinuation；GO_TO_FOLDER需uniquefocusedfield；PATH_FILLED需exact完整absolutepath；DESTINATION_SELECTED需current-directory或明確完整路徑導航結果＋連續性、leaf/confirm/bounds，**leafalone不能PASS**，不要求closedfield仍存在；CONFIRM_ATTEMPTED只一次currentcontrolinvocation，下載開始另用FilesystemDelta證據。每phasefreshframe，不reuseoldindex；wrongowner/path/focus/unknown全部stop，不用closedchooser推成功。

### 5.5 Ledger暫存安全細節

唯一sharedledger=`TP/gui-ledger.json`；temp=`TP/.gui-ledger-v3.tmp`。Storereserve/consume持有原stateguard，保留CAS/quota/atomicreplace/fsync/readback；不另開authority。O_EXCL失敗，不unlink現場。成功create保存fd的dev/ino，cleanup前以no-followsamelstat身份比對，只清本次createdtemp；替換/碰撞未知不刪。fixtures必測preexistingregular/symlink、openfailure、replacement、write/replace/readbackfailure。不要對真實state注入fault。

## 6. 正式檢查：直接採Plan§7，不另發明集合

先 materialize `check-specs.json`（literalargv、cwd、env、runtimehash、timeout/cap、automatic_retry=false、exclusiveID/outputpaths），sourcefreeze後`check-specs-freeze.json`及runtime-binding。每個正式spec與invocation需互相hash綁定；不存在的sourcehash不得預填，只有實際讀回值可以使用。

順序和IDs：

1. E01-evidence-policy、E02-runner-selftest → B01-baseline-pair。
2. D01-raw-cua（早期診斷，第一次產品collection動作）。
3. 必要實作/freeze → S01-build一次 → G_AUTH_RUNTIME／R01-real-link。
4. N01-syntax的7個FILE各一次；N02-tests一次；P01-batch、P02-binding、P03-transaction、P04-v2各一次；S02完整Swift一次。
5. 本輪交易完成或materialstop → B02-preservation-pair／tailreadback／reports。

用Plan列出的固定PY/NODE/SWIFT/SDK/decoder，childtmp/modulecache/scratch全部R內；Swift用--package-path/--scratch-path/--sdk及固定cacheflags，不能root .build新輸出。大suite有300/1200秒deadline，poll/wait單次≤60秒並更新進度；不改HOME/CODEX_HOME。stdout/stderr分別cap，任何截斷／nonzero／0cases／protocolerror不PASS。

N02必含existingdirty`tests/test_cua_adapter.mjs`原樣＋本輪host/classifier/runner/chooser測試；Python existingbatch/binding/transaction及新v2；Swift完整suite，不只新tests。Tests所需newfixtureexactroot在寫前登記，cleanup僅ownedfixtures。沒有permission/runtime能力只留truthfulblocker，不裝全域runtime/依賴或改上游release。

## 7. 兩本 E2E 的逐步操作與收據

### 7.1 前景與首次catalog

獲明確交接前完成所有不依賴input的工作。請求例意是「接下來在LINE『旻謙允禎成長日記』相簿列表，先擷取新畫面核對，再做一次小幅捲動／開啟已辨識卡片，請交還前景」；實際訊息按下一精確動作改，不含多個不明確後續承諾。等待明確回覆；取回前景立刻停。

canonicalAlbums起點由user準備，程式仍驗group/Albums/currentcards。人工調整layout屬已核准配合，但不是toolPASS，freshrebind後再用。freshfullcatalog實際top/bottom、≤0.25viewheight每次scroll、全連續orderedoverlap；每action獨立before/invocation/after。局部可見不等於完整catalog。

新g1grant/owner，inspect→begin→catalog→admit；manifestorder排除VERIFIED與barrier。candidatefulluniquevisible、同幀dates/count/fingerprint、safenonthumbnailmetadata及鄰卡separation，persist/readbackbinding後click；freshpostopenMATCH，否則SAFE_ABORT，不開intent。

### 7.2 Menu與第一本派送

在intent前實測SaveAlllabel/itemorder/row/margin/provenance/nativeSCKguard/latency，安全close無commandactivation。不得公式推坐標、舊frame/高confidence單独PASS、postintentcalibration。emptyexactdestination/resolvedowner/duplicate/freshbinding全PASS，persistentintent/readback/at-most-once後，同execution只派送一次atomicpair。

ellipsis→既定wait→SaveAllclick，之間沒有capture/getState/persist/keyboard/appswitch；invocationboundarybookkeeping不等於多一步GUI觀察。派送不確定保留barrier，不resend。chooser各phasefresh，再GoToFolderexactpath/leaf/navigationproof、oneconfirm；獨立downloadstartdelta。

### 7.3 第一本內容與狀態驗收

downloadstarted後不再LINEGUI，poll5秒／3完全相同inventory及bytes／max600秒。hiddenentries全部列、nofollow；actualcontentimages=expected、zero/partial/temp/unknown=0、無異常dir/symlink，fullImageIOdecode每個file，pre/postreadidentity/hash穩定。失敗不刪檔、不下載第二次。

canonicalfinalize VERIFIED＋registry＋active_writer/contextnull同revision，完整state readback。FilesystemPASS但statepending分別保留，不能叫overallVERIFIED。回listnav-only觀測、freshfinalcatalog、finish/releasebatchowner；firstretiredowner不可再普通write。獨立保存inputbefore/stateafter/revisions/owner釋放與ledgerquota。

### 7.4 必需的實際scroll（G_SCROLL）

第一本VERIFIED/readback且owner/lifecycle釋放後，freshAlbumscapture，實際downward0.25viewheight。保存before/scrollinvocation/after；同group/surface/session/PID/processinstance/window/display/layout，至少一張完整唯一相鄰card有序overlap＋實測movedeffect＋新完整card dates/count。

第二張本來已可見仍不能跳scroll。NO/UNKNOWNeffect/nooverlap/newpartial不再連續輸入；無eligible=NO_ELIGIBLE_TARGET；未scroll=SCROLL_TEST_NOT_RUN/PARTIAL。不要reopen已VERIFIED來湊兩本，舊坐標不可沿用。

### 7.5 第二本與終點

建立freshg2、cap1、新run；differentfingerprint，重跑freshcompletecatalog、duplicate/fullcard/openMATCH、emptydestination、menu/intent/onceSaveAll/chooser/download/decode/terminalstate/finish/release。總quota2SaveAll/2confirm、sharedreversiblecap1000carryhistory，不重置。

第二本PASS後仍需G_PRESERVE_06、G_REPORT、獨立Acceptance及原nativeclosure要求；兩本可用結果與正式TASK_CLOSURE分別回報，不能互相掩蓋。

## 8. Attempt、停止與回交

歷史LIVE_CLASSIFIER_CHOOSER=3/3；本輪1個額外collection＝累計第四，userquote原文與scope/checkset/hash寫attempt-extension。D01launch前persistattemptstart；R01/offline/兩本為同collectionsubsteps，不能用新ID或freshlineage重新給自己3次。Toolsissue/preservationfailure另列已知與unknown歷史，smoke不是0。

第一個requiredFAIL後只收保存/報告，不依賴它繼續；不codefix+rerun、換writer、更改gate。Unexpectedwrite、source/grantdrift、permissions、window/crop/scaleidentity、focus/path、5秒過期、intent/dispatchuncertainty、前景被取回均stop相應input／交易。失敗傳播到依賴gatesBLOCKED，不抹已證明singlealbum/filesystem/corefacts。

preintent按原canonicalstop/terminalprotocolSAFE_ABORT；postintent/dispatchunknown保留intent/barrier/retry=false，emptyfolder/closedchooser不是non-dispatchproof。只有原proof＋canonicalresolution/readback才可解除block，仍不在本collection重送。canonicalguard/finalizationuncertainty不直接改JSON或另換writer。

回交要回答：哪個firstrequiredcheck/step失敗、精確rawerror、使用的file/hash/argv/invocation、實際狀態前後、是否有GUI/派送/下載副作用、rootissueattempt及新資訊、最小reproduction、下一個決策及其可驗收方式。沒有Planner通道就交文件給使用者供指定Replanner接收，標handoffpending，不聲稱已完成外部交接。

## 9. Gate對應與狀態回報

凍結15個gate：G_BASELINE_06、G_EVIDENCE_POLICY、G_AUTH_RUNTIME、G_REAL_LINK、G_OFFLINE、G_CATALOG_1/2、G_MENU_1/2、G_FIRST、G_SCROLL、G_SECOND、G_PRESERVE_06、G_REPORT、G_ACCEPTANCE。詳情與criticality/evidence-role/closure在Plan§9及下方contract完全一致。每gate explicitPASS＋actualevidence；OBSERVED是人類觀察，不當PASS，不把waiver改reviewerPASS。

父獨立Acceptance仍required，接手Implementer及任何artifactcontributor不能擔任自身獨立Reviewer。保留CRITICAL/plan_review_required=true＋USER_WAIVED_NOT_RUN的separatedecision；不重新提問。缺stagepacket/nativefixedruntime時nativeNOT_RUN；禁止constructsubstitutevalidator，取得controllerpacket才用其emittedcommands。這個限制阻止formalDONE，不能抹除已完成的產品實證。

六軸分列：PRIMARY_OUTCOME_STATUS、IMPLEMENTATION_STATUS、CORE_ACCEPTANCE_STATUS、REQUIRED_VERIFICATION_STATUS、INDEPENDENT_ACCEPTANCE_STATUS、TASK_CLOSURE_STATUS。單本PASS/第二本BLOCKED=partial；兩本產品PASS/native未驗/Acceptancepending=產品成功但正式closurepending。完整群組project尚需後續iteration，不能宣布全群組完成。

## 10. 最終產物與報告最低內容

本輪必交Plan§11完整列表：contract/handoffjson、fixedcheckspecs/freeze、input/reconciliation/bootstrap/policy/observedmanifest、extension/waiver/authorization/grants/runtimebinding、原始frame/AX/native/SCK/OCR/mapping/chooser/action/catalog/scroll/download/content/state/ledger、command/gatereceipts、完整E2E報告／progress／attemptledger／format3implementationresult／manifest。末尾reportmanifest/result順序依事前tailpolicy，不fabricateselfhash。

每證據relative及absolute path、bytes/SHA256、producer/invocation/phase、facts/inferences/unknowns、判定支持哪些claim；每本獨立SaveAll/confirm/download/content/VERIFIEDreadback。報告包含完整步驟順序、工具/argv/env及關鍵片段、資料環境、expectedvsactual、pass/fail/notrun、狀態前後、sideeffects/cleanup/attemptlearning、限制及停止原因。`progress.md`白話說目前在解什麼、卡點、用了幾次、有無新資訊、是否更近、下一次失敗會怎樣。

本次 git 出版只交Plan/Handoff，不測產品。後續Implementer無產品commit/push權；這些交付準備完再交指定Replanner。user已授權本輪工作，不每個角色重新討批准；只有真實擴scope／受保護決策改變／未授權破壞或外部動作才需要精確新決策。

## 附錄 A：逐 byte 複製的 format 3 contract

與Plan附錄A相同。opening/closing code fence之間UTF-8 bytes含末尾1個LF，exclusive materialize到plan-contract.json與handoff.json。不得重新serialize、加BOM、改空白/keyorder；原hash由真實bytes計算後綁Python/Swift/JS。下面的本地結構與一致性核對不是native schema validation。

<!-- FROZEN_CONTRACT_START -->
```json
{
  "format_version": "3",
  "task_id": "TASK-20261010-line-v3-live-e2e",
  "goal": "In one user-authorized additional bounded collection, repair task evidence publication and the real CUA/native observation pipeline, prove the shared production probe, then complete two distinct eligible LINE album transactions in separate cap-one lifecycles with an actual post-release 0.25-view-height scroll, complete content/state verification, preservation, reporting and independent Acceptance; preserve historical failures and unrelated work.",
  "task_class": "CRITICAL",
  "allowed_paths": [
    "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-06",
    "scripts/line_backup_cua_adapter.mjs",
    "src/line_backup_batch/cli.py",
    "src/line_backup_batch/observations.py",
    "src/line_backup_batch/store.py",
    "rev28/Sources/rev28ctl/main.swift",
    "rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift",
    "rev28/Sources/Rev28Core/Perception/AlbumVisualWitness.swift",
    "rev28/Tests/Rev28CoreTests/PassiveContextObservationTests.swift",
    "rev28/Tests/Rev28CoreTests/AlbumVisualWitnessTests.swift",
    "state/backup_state.json",
    "state/.line-backup-state.lock",
    "state/.line-backup-v3.tmp",
    "harness-development/line-v3-live-e2e-20261010/gui-ledger.json",
    "harness-development/line-v3-live-e2e-20261010/.gui-ledger-v3.tmp",
    "backups/旻謙允禎成長日記"
  ],
  "required_evidence": [
    "E_BOOTSTRAP_06",
    "E_INPUT_RECONCILIATION_06",
    "E_ATTEMPT_EXTENSION_06",
    "E_PLAN_REVIEW_WAIVER_06",
    "E_EVIDENCE_POLICY_06",
    "E_BASELINE_06",
    "E_AUTH_RUNTIME_06",
    "E_RAW_CUA_06",
    "E_REAL_LINK_06",
    "E_OFFLINE_06",
    "E_CATALOG_1_06",
    "E_MENU_1_06",
    "E_FIRST_06",
    "E_POST_RELEASE_SCROLL_06",
    "E_CATALOG_2_06",
    "E_MENU_2_06",
    "E_SECOND_06",
    "E_PRESERVATION_06",
    "E_REPORT_06",
    "E_INDEPENDENT_ACCEPTANCE_06"
  ],
  "gate_specs": [
    {
      "gate_id": "G_BASELINE_06",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "BASELINE_DELTA",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_EVIDENCE_POLICY",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_AUTH_RUNTIME",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_REAL_LINK",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_OFFLINE",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_CATALOG_1",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_CATALOG_2",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_MENU_1",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_MENU_2",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_FIRST",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_SCROLL",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_SECOND",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_PRESERVE_06",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "MUST_NOT_BREAK",
      "closure_gate": "BASELINE_DELTA",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_REPORT",
      "required": true,
      "owner": "ROLE",
      "phase": "IMPLEMENT",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "SUPPORTING",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    },
    {
      "gate_id": "G_ACCEPTANCE",
      "required": true,
      "owner": "ROLE",
      "phase": "ACCEPTANCE",
      "evidence_source": "ROLE_OBSERVATION",
      "goal_criticality": "CORE",
      "evidence_role": "OUTCOME",
      "closure_gate": "HARD_CLEAN",
      "reuse": "NEVER"
    }
  ],
  "capability_policy": {
    "network": "OFF",
    "browser": false,
    "destinations": []
  },
  "retry_policy": {
    "transient_read_only_retries": 2,
    "delays_seconds": [
      10,
      30
    ]
  },
  "resource_policy": {
    "prompt_bytes": 65536,
    "state_bytes": 524288,
    "inspect_bytes": 16384,
    "log_bytes": 134217728
  },
  "workflow_policy": {
    "plan_review_required": true,
    "independent_acceptance_required": true,
    "max_parallel_read_only_helpers": 0,
    "max_parallel_writers": 0,
    "handoff_review_required": false
  }
}
```
<!-- FROZEN_CONTRACT_END -->
