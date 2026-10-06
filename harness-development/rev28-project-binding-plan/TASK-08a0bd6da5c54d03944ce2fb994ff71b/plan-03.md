# 本機整合第一個可驗收單元：專案、相簿與已備份紀錄的共同綁定

2026-10-06。使用者要求繼續完成可重用的 native LINE 備份。已授權自主規劃與同範圍普通本機修復；本 Plan 的新公開 project-preflight 報告與專案 authority 契約屬 protected data/public decision，獨立 P1 PASS、exact Handoff 後才提出一個 I0 明示決策。本次規劃只寫本 task；未修改產品。實作限定本機程式與 task-only offline checks，不做 native/GUI/input/activation/navigation/TCC request/network/download/state mutation/commit/push。

## 現況與最小範圍

接受的 source52=02b17aaa488c80f77056ed7e34f03d0a0d51ce4dd0a165d4dda0a65f999037b0，實際 v3 native menu packet/strict loader與獨立 partial-report A1 PASS。影像日期2024/05/06~05/10、182張、儲存全部已證；current native group proof I2 BLOCKED，certifications UNKNOWN，不能豁免。新資訊使精確擷取 channel有實證，沒有帶來 production permission。

正式 native 入口仍 hard-coded canonical group、May13~17/57、17,924,900 bytes 與舊 content multiset；其 immutable authorization/staging verifier/owner 都以此 known-baseline 契約驗證。v3被LiveCompositionFactory拒絕，且closed group/list/detail無candidate child時不能套用同一explicit profile。ComposedNativeAdapter目前detail/menu還要求同frame group文字，本次實際detail沒有group header。Python project config/state 已另有schema2/RC2 authority、writer/registry/barrier；nativeowner是另一個ledger/goal-slot，兩者沒有共同commit join。這些不是刪除一個guard或換成182即可解決。

本輪只建立第一個必需且可獨立驗收的**唯讀共同資料邊界**：正式 Python product entrypoint可從explicit selected project root讀canonical config/state，對指定date/count推導project-bound target與duplicate/barrier facts，輸出non-dispatch report；Swift core有相同report的嚴格typed consumer供後續native整合。它不使目前live-execute可用、不更改57 known-baseline、nativeI2、state schema/歷史或v3 diagnostic-only guard。後续sharedwriter/content-policy/context/calibration和native接線另有具體Plan，不能聲稱這個單元就是整個第一段或whole workflow完成。

新 root issue PROJECT_AUTHORITY_NOT_BOUND_TO_NATIVE_TARGET_REPORT：缺少供native消費的explicit project/config/state/target snapshot receipt。source surface與驗收不同於已凍結explicit capture implementation；本issue local product candidate0→最多3，連續2次無新資訊停止。原explicit產品3/3、production3/3、passive cumulative3、count1/1不重設，native額度0。

CRITICAL（會成為正式備份使用的authority/duplicate語意，不是一般文件美化）：Planner→獨立P1→exactHandoff→I0→root串行Implementer→獨立A1。helpers/writers/nesting0。只使用pinned Harness4.7.0 local schemas/v3與advisory角色UUID；controller/provider admission unavailable/unknown，無OS sandbox/enforced network denial宣稱。

## 精確產品路徑

1. NEW `src/line_backup_acceptance/project_binding.py`：唯讀producer/library與CLI handler。
2. `src/line_backup_acceptance/cli.py`：新增`project-preflight` parser/dispatch branch及usage；原commands/exit meanings保持。
3. NEW `rev28/Sources/Rev28Core/Composition/ProjectBackupBinding.swift`：typed report/request/digest與strict inspection-only consumer，不能產生ReadinessPermit/owner/GoalSlot/dispatch eligibility。
4. NEW `tests/test_project_binding.py`：task-root fixtures的實際producer/CLI拒絕案例。
5. NEW `rev28/Tests/Rev28CoreTests/ProjectBackupBindingTests.swift`：consumer一致性/forgery/freshness拒絕案例。
6. `rev28/ARCHITECTURE.md`；7. `rev28/CAPABILITY-MATRIX.md`：說清integration foundation已建和runtime closure未建。

除7個literal paths與本task以外全部只讀。保存cli/docs原dirty preimages，新檔required absent；不改common/authority/transaction/owner/engine/PhaseA/PhaseB/capture/ledger/GoalSlot/StagingPolicy/state/config/backups。禁止package外global evidence。新public command與report才是I0決策，未批准前不實作。

## 公開唯讀 producer 契約

入口`python -B -m line_backup_acceptance project-preflight --project-root <explicit-root> --start-date YYYY-MM-DD --end-date YYYY-MM-DD --expected-images N`。只stdout/stderr；不建output、lock、state、run-log、destination/evidence dir或owner。不呼叫現有transaction/duplicate-check CLI，因其可能建立locks/result；可重用已接受`common.validate_state_strict`/pure binding-reference grammar及pure fingerprint helpers，不能 import 或call native。新module import沒有side effect。未提供root、relative/symlink root、缺canonical files就refuse，無cwd/WORK_ROOT/env/替代根搜尋；读取及引用全部只explicit root canonical descendants，reject symlink各component與traversal。backup_root本scope必須是该root/backups（歷史state格式不改）。

canonical`config/line_backup_config.json`與`state/backup_state.json`按目前accepted格式驗證，不用installed-skill schema替換RC2真實state，不遷移或初始化。config keys/types完整、fixed bundle jp.naver.line.mac、nonempty group_name、group_key與bundle/name精確一致；dates實際Gregorian且start<=end、count為正整數（bool/fraction/NaN/negative拒絕）；group identity只來自config，不能用OCR或argv改名字。

canonical dirs/files先no-follow確認，再讀兩輪同bytes的config/state與stable file identity，以SHA256/size與revision建立**read-only snapshot**；change/truncation/replacement/malformed JSON拒絕。這不是writer lease／OS atomic two-file snapshot或dispatch permission：報告固定`dispatch_authorized=false`,`writer_acquired=false`,`native_observation_performed=false`,`state_modified=false`，futurecaller必須重新驗證當前hash並在sharedwriter commit boundary重做preconditions；不能因兩輪相同就宣並發寫入被禁止。

不盲用舊`transaction._evaluate_preconditions(duplicate_check=False)`：它以current_run_id非null拒絕已terminal且ownernull的現在專案。也不以任何同fingerprint一筆release解放其他run。新唯讀evaluator：

- current_run pointer唯一可解析；run IDs唯一；owner/contextnull且currentrun terminal允許檢查，owner或lock非null一律PROJECT_BUSY／BLOCKED，不做cleanup。dangling/current crossrecord/registry-link矛盾INVALID_PROJECT_HISTORY。
- group-scoped完整fingerprint由start/end/count形成；該fingerprint任何VERIFIED run或registry/user_attestation都SKIP_VERIFIED／noneligible，不論destination、是否有release或換run。核對filesystem_verification registry與exact verified run/group/fingerprint/destination/verification/evidence關係；nullverified_run只合法user_attestation，不捏造machine verification。
- 同group/date/count變更為AMBIGUOUS_FINGERPRINT／BLOCKED。相同fp任何nonterminal/loaded intent/FAILED with intent/SAFE_ABORT with unknown dispatch或reconciliation皆BLOCKED_UNRESOLVED。不同fp nonterminal或ownership conflict也PROJECT_BUSY。
- 第一版對同fp有任何歷史intent而未VERIFIED均BLOCKED_UNRESOLVED，**即使宣稱已有release**也不放行；把possibly released狀態回報但不採納為permission。這是inspection producer的保守支援界線，不改舊reconciliation的effective語意、原歷史record或既有command。後續採納release需另明定exact run/action/原execution／persisted証據驗證，不得global boolean。
- 所有decision只描述project資料；不存在于歷史且project健康時PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION，`dispatch_authorized=false`始終不變。INVALID/BUSY/UNRESOLVED/AMBIGUOUS不是可下載，SKIP也不是新操作许可。

目的地只是`root/backups/<exact config group>/YYYY-MM-DD_YYYY-MM-DD_N張`的derived string，component合法性/實根及existing symlinks須檢查，reject unsafe groupname/path；不mkdir。nonempty existing destination、nonregular/symlink、parent drift拒絕；VERIFIED目標先SKIP且不掃/讀圖片，不重新decode57。empty/not-yet-existing只表示future path proposal，非reserved空目錄。confighash/statehash/target/source producer hash/actual inspected root paths以同report綁定，state revision16只是當前測量不hardcode。

## report v1 與 Swift consumer

固定`report_format_version=1`,`scope=PROJECT_PREFLIGHT_READ_ONLY`；exact request(projectRoot,startDate,endDate,expectedImages)、authority(config/state relativepaths/bytesSHA/revision/group/bundle/backupRoot)、target(fingerprint/canonical proposed destination)、decision+reasons、state ownership/history facts、producer source-file ordered digests/hash、`expected_total_bytes=null`,`expected_content_multiset_sha256=null`,`content_expectation=MEASURE_AFTER_DOWNLOAD_NOT_YET_VERIFIED`及上列false flags。unknown只null/UNKNOWN，不用0/emptysha替代。Report不收native PNG/PID/window/epoch或current group proof，不能把configauthority當nativecontext。

用明確 version/discriminator及strict key/type/enum/UTF8 parsing（duplicate JSON keys拒絕）；producer input及report hash不符／矛盾都拒絕。新公開decision exit：0只適用PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION與SKIP_VERIFIED，2 usage/invalidproject/history/path、4 busy/unresolved/ambiguous/nonempty。stdout完整machine report且stderr短原因；無raw privatephoto或global-window metadata。程式錯誤不得以0回傳eligible。

Swift純consumer傳入originalrequest、原始config/state bytes及實際producer stdout/外部stdoutSHA，核對literal selectedroot/configstate digests/revision/group/bundle/fingerprint/destination/flags/contentnulls/source aggregate與strictversion/enum／unknownkeys。它只回`ProjectBackupInspectionBinding`，明確`canDispatch=false`；producer provenance／external anchor是來源關聯證據，不是OS code attestation、writer lease或nativepermit。不能重新封裝為ImmutableRunAuthorization，不能創造PhaseA/B或降低legacy驗證。report可以供未來native共用資料，但真正執行仍須fresh authoritative recomputation，不得離線report直接放行。

## offline驗證與隔離

required core checks用有意義的反例：實際project57即便新destination仍SKIP，182只inspection-eligible但neverdispatch；terminal pointer不誤判busy，activeowner/lock/unknownintent/FAILEDintent/legacyunknown/foreignrelease不放行，registrydangling/mismatch/crossgroup/count矛盾拒絕；非法date/count/types/duplicatekeys/nullhistory/缺root/wrongroot/改group/traversal/symlink/nonempty／stable-read race拒絕。Swift forgedflags/target/statehash/revision/root/reanchored contradictions與unknown/nulls/producer source tamper拒絕，不把自我reanchoredhash当auth。

新tests及compiler/cache/temp只寫task。Swift以task-local exact Package/Sources/Test copy執行：所有source/Package逐bytes相同，舊tests只同一literal temp-root substitution（目前26occurrences，實作時實讀盤點，不改assert），新tests顯式task temp root；4個active #filePath fixtures依先前proof逐bytes拷到task/evidence精確roots。無system tmp默認、symlink資源、skip、tests降低。Pythonfixtures全部TemporaryDirectory(dir=taskroot)，-B、不跑會寫private/tmp的舊acceptance driver，不calltransactionmutators，不decode真實57圖片。

先newPythonfocused、newSwiftfocused加相關legacytests，再一次fullSwiftsuite(current302+newtests)/actual CLIbuild/Pythonparser compatibility focused；不重跑irrelevant acceptancewaves/GUI/productioncommands。實際newCLI對root57與182一次唯讀each，以及 task fixture argv failures；source+test manifest於每check前後綁定。舊passivev1與retainedv3actual current-source strict loader只在source有新變化需要相容性核對時各一次，external anchor維持原stdout，無新capture。僅成功checks之後不重複。

7 paths變更與全outside-task/off-literal baseline逐hash/mode/type/Git/57inventory preservation；source/preimages exact join。root最多3 evidence-bearing candidates，首次failure preserved；連續2無新資訊或scope drift停止。真正獨立 A1閱讀mergedsource/diff/實際checklogs/CLI/隔離/保存證據；不自驗收。L0 human grant單獨記record，不以elapsed替代同意。任何更改writer/dispatch/legacyauthorization/contentverification/calibration/gatepolicy都超此Plan，replan而非mechanicaldetail。

## 本輪與後續界線

本單元成功只代表project/native共享的唯讀authority基礎成立。whole primary NOT_ACHIEVED/closure IN_PROGRESS；目前nativeI2BLOCKED/UNKNOWN certs與所有舊預算保留，不能宣布第一段整套或可下載完成。

完整整合下一段需另freeze：shared project writer/intent commit与nativeledger/GoalSlot crash-safe ordering、動態target的fresh group→card→detail continuity、每state選擇primary或explicit且不fallback、新target內容驗證（count+decode+stable+zeroabnormal且record actual hashes，而非下載前未知multiset）、current native PhaseA/ownership/occlusion/calibration與新productionauthorization/budget。不能使用本次单frame去宣nativegroup或calibrationPASS。所有實機導航、觀察、SaveAll/chooser/下載與state寫入需後續明確範圍；這個Plan不批准。


## Plan02 精確 wire schema 與離線審查 recovery

原 Plan/contract/baseline/P1全文保持原bytes；原P1 semantic PASS含一次network schema lookup，root admission BLOCKED未waive，詳review-01-admission.json。此次只精確化公開report schema並修正review工具設定，不改產品7paths、phase範圍、authority/duplicate/barrier/readonly/gates/budgets/I0 requiredness。

`project-binding-report.schema.json`是本task frozen wire contract v1：REPORT與REFUSAL兩個discriminator branches、所有nested exact required/allowed keys/type/enum/null/false flags已固定，實作不得自選rename或增加欄位。argparse usage錯誤可stderr/exit2而無完整report；validargs的讀取/驗證錯誤輸出REFUSAL（INTERNAL_ERROR=exit1，其他error=exit2），Swift一律拒絕REFUSAL為binding。REPORT eligible/SKIP=exit0，busy/unresolved/ambiguous/destination=exit4；error與decision不能混成eligible。

schema只形狀：consumer仍須originalrequest/configstate bytes与external actualstdoutanchor、same selectedroot/path/hash/revision/group/target/destination、一致decision/state_facts/nulls/falseflags/sourcefile sorted uniqueness+path-NUL-bytes-NUL aggregate等semantic checks；JSON Schema不給writer lease、native auth或OSattestation。producer與consumer的config/state keys沿實際accepted格式；未知nativegroup不新增到publicreport或轉PASS。consumer不將任何REPORT轉dispatchpermission。保守duplicate precedence固定：invalid authority/history→REFUSAL；health/ownership/nonterminalotherfp busy→PROJECT_BUSY；健康samefp verified→SKIP_VERIFIED；samegroupdate不同count→AMBIGUOUS_FINGERPRINT；samefp未verified歷史intent→BLOCKED_UNRESOLVED；不安全或nonempty proposed destination→BLOCKED_DESTINATION；其他→inspectioneligible。已有verified時不讀圖片；busy skip不掃destination，destination_status=NOT_INSPECTED_BLOCKED或NOT_INSPECTED_VERIFIED。

檢查rawconfig/state duplicate JSON keys及proper types與foreigngroup/date/path/source mismatch；stateRevision不能bool，config path一定config/line_backup_config.json、state path一定state/backup_state.json，producer digests paths為explicit projectrepo src/line_backup_acceptance字面sourcefiles，不作外部roots搜尋。格式與source aggregate重算是關聯證據，不證明來源安全attestation；新type保持inspection-only。

review2使用prepare_review_02.offline_validators：preload全部pinned schemas/v3及本schema並用Registry(retrieve=refuse)；不能用裸jsonschema.validate/Draftvalidator造成remote$ref。未命中localresource立即fail且不network。root已用此Registry作完整result/task schema validation與full77871項/critical/source/Git preservation；此新核對不抹舊lookup。P1獨立只read同fixed resources，不重跑checks；新的fullrole result若PASS才admit exact Handoff与I0提問。原lookupfacts UNKNOWN的external effects仍保留，無OSnetworkdenialclaim。


## Review 前 source material 接口澄清（Plan03）

Swift consumer additional explicit input `producerSourceMaterial` 為 caller從本explicit project repository regular/no-follow讀取的ordered `(relativePath, rawBytes)`完整producer Python source set，與originalrequest/config/state rawbytes及externalactualstdoutSHA一同提供。它核對report producer source_files的sorted唯一完整paths/bytes/SHA並以真正rawBytes重算path+NUL+bytes+NUL aggregate；**不能從單一file hash或digest list假裝算出raw-byte aggregate**。缺raw material、少一個file、foreign source path或每一條digest/source bytes不匹配均refuse。Caller的selected-root与regular-file/digest source provenance仍需actualofflineCLI/fixture證據；外部anchor/raw material只是binding，不能稱authentic code attestation。

此澄清不新增wire fields（report schema SHA保持6269d2721ff6a68ff855195d49376291f84ae56d1ae0f76805c3a94f7b25c18d）、不改product7paths、machinecontract f0bd7bea76510a7cb6fecc90124aefa554d06d50331180e4f983653d59a5895d或readonly/I0/gates/budgets。Plan02及其preparation/planner記錄仍原bytes保留；尚未有對Plan02的獨立review，不把此工作草稿修訂計成productcandidate。Review以Plan03的explicit raw-material input為準，所有consumer output依然inspection-only/canDispatch=false。
