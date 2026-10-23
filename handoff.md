# 接手 Agent 啟動 Prompt（先讀此段）

```text
你是 s9008129/Line_backup 的接手 Implementor，任務 AGENT-RESUME-P0-20261022，Plan v2.1。目標是沿用 PR28 已成功的 Agent 模式 A，可靠恢復100本相簿在#50中斷的工作；#1～49不重下載，#50完整且來源成立才重驗補提交並續#51，partial／unknown保留照片並停止全task，不重送。

先完整讀本文件與同目錄plan.md，核對Plan SHA-256：4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502。記錄真實模型／effort（不可得寫unknown）、Session、repo／remote／branch／HEAD／dirty狀態。依現行AGENTS預設由Sol派給GPT-6 luna／high實作；DeepSeek deepseek-v4.1-flash:1017／ollama_cloud保留給Owner另啟的獨立E2E。Owner若另明確指定實作模型，附真實決策再用，不依舊v1.1擅改角色。

Owner最新明確指示「本次 Plan 不需要獨立審查」。EXTERNAL_PLAN_REVIEW=OWNER_WAIVED，不生成APPROVE_PLAN或獨立review PASS。Plan§4.3完成設計層最小化覆核，OVERENGINEERING_AUDIT=PASS（scope=PLAN_V2_1_MINIMAL_DESIGN，Planner非獨立）；PR31來源仍NEEDS_SIMPLIFICATION，未宣稱程式已改。MINIMAL_IMPLEMENTATION_PLAN=READY，接手對帳後可直接從M0有界離線實作，不再等待外部Plan／獨立設計audit。Code Review、必要測試與獨立E2E保留；本次豁免不建立LINE前景／新下載或reboot授權。

依本次Owner免審決定，只依plan§5.2的Feature A及§5.3的CI B工作包操作。Feature從當時最新master的乾淨外部worktree開始，逐檔移入本版文件與必要原樣工具；CI sibling從1b9a010開始、PR target原legacy分支。不要把177 commits／1900檔PR31或整筆1b9a010帶入master，不reset／clean／stash原dirty樹，不覆寫已存在worktree。兩包序列做，不新增writer／reviewer代理樹。

M0先以fake app證明現有hosted CUA Node可用node:child_process.spawn＋單一stdio連接Python長活session，固定root全域flock、真實host/controller/boot身分、EOF即永久停止新輸入、pending input／舊host活拒接管，以及目標Mac sync能力。零LINE觀察／操作。spawn／stdio能力不成立就保全第一錯誤提報，不另造bridge、GUI引擎或修改Harness。

核心只有一份checkpoint、固定ordered Owner manifest、跨task歷史／intent屏障、同一reconcile／verify函式與薄wrapper。root固定為~/Library/Application Support/LineBackup/agent-resume/，不另建store繞歷史。init只可明確首次執行；resume缺store不初始化。inspect／reconcile純只讀，不寫checkpoint、照片或lock。task phase／next_index／VERIFYING／PARTIAL由事實推導，不建第二ledger、registry或event-sourcing framework。

Save All：fresh list／detail／menu及當次Owner前景／清單核對→檢查歷史及獨立空目的地→controller持鎖durable intent、readback→同wrapper原始promise驗首次ack並消耗記憶體資格→自己呼叫一次既有app.click。不得接受可迴圈派送的任意callback；不得公開可重播prepare token CLI。loaded intent、重複request、timeout、遺失ack、換Session／task／目錄不重獲資格。Chooser最終確認同樣單次intent；新Session不接續舊chooser。RETURNED不等於下載完成。

完整#50需來源／空目錄／固定destination／chooser關聯、滿額檔數、逐檔SHA、原樣ImageIO完整RGB、穩定性與post-decode核對，持鎖補VERIFIED再只續#51。32/80、空目錄但有intent、來源不足、失效VERIFIED、壞canonical均BLOCK_AND_PRESERVE_WHOLE_TASK。孤立temp不當authority；依plan§7區分有效canonical與損壞，不自動promotion／restore／清障。

原樣核對並納入decoder SHA 238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b；OCR SHA 19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861。原圖／PR28 checkpoint只讀，239／109／329及65排除不重下載。不得改正式AUTO、State／Grant／Ledger／pilot policy、舊adapter／two_album_entry、Native Diagnostic或Harness；CI唯一有界例外是plan§5.3列明的inspection consumer／測試／workflow。

依plan§10完成TC01～20、100本新程序故障注入、wrapper實際呼叫計數、跨task雙writer及Mac真ImageIO。CI由當前Python producer產生六組可攜合成fixtures，設定LINE_BACKUP_INSPECTION_FIXTURES；處理Python/Swift來源與manual_archive_match契約漂移，true保持拒絕，不能寬鬆解析、skip測試或用舊stdout假綠。Feature CI與legacy CI各綁精確HEAD，不轉移PASS。

同根因最多三次有證據attempt，連續兩次無新資訊或material blocker提前停。未解問題必須成單：原錯誤、重現、AC、每次學到什麼、GUI實際呼叫／UNKNOWN、狀態／副作用、證據bytes／SHA及一個待裁決問題；送達前PENDING_OWNER_FORWARD，不換Session重算。rollback只停新程式，保留store／intent／照片。

交付逐項AC／TC真實PASS/FAIL/BLOCKED/NOT_RUN、精確HEAD／Plan SHA／source/runtime hashes、完整E2E測試報告與first blocker。按既有Git授權逐檔add/commit/push、同scope Draft PR；commit body含意圖／做了什麼／驗證與結果／下一步的建議，不merge、不amend／force-push。外部Code Review與獨立Mac E2E是不同Gate，不以自評或離線測試冒充完成。

開始先白話回報接手目標與本次Plan免審，完成環境／SHA唯讀對帳後直接M0；不重問Plan批准，不再等待外部Plan Review。不要要求Owner先開LINE，不執行Save All或reboot，不新增無關研究循環。
```

# LINE Agent 恢復功能交接（v2.1）

## 1. 文件與來源綁定

| 項目 | 值 |
|---|---|
| Task | AGENT-RESUME-P0-20261022 |
| Plan／Handoff revision | v2.1／2026-10-22 |
| Canonical Plan | 同目錄`plan.md`；沿用repo既有小寫檔名，沒有另一份Plan.md |
| Plan SHA-256 | `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502` |
| PRD | `~/Downloads/LINE_backup_PRD_Agent_Interrupted_Resume_v1.0_20261022.md` |
| PRD SHA-256 | `0d69c560490504f1b2af5466db680768e27924c4416c879d8c0545f1224a75d5` |
| 文件交付分支／PR | docs/agent-resume-handoff-20261022／[PR30](https://github.com/s9008129/Line_backup/pull/30) |
| 舊文件commit | aa415ef6a2f665bf866631762154dc4b0470d3a3；本版以新commit追加，不amend |
| 受審產品baseline | 1b9a010aeba2e75a406d842be123d7251501548c／[PR31](https://github.com/s9008129/Line_backup/pull/31) |
| 文件分支原parent／本輪master讀回 | 64515eb56b04accc40ade9e2db2fe0ad18c1ced3；接手時重讀，不假設不變 |
| 產品實作commit | 尚未產生；不可把文件commit當產品版本 |

本版承接82773cffee7b1ffdabcd14ca0d688a682a3be24f的v2.0，依Owner最新明確決定免除本次獨立Plan審查；完整audit仍保留，設計層覆核見Plan§4.3，不新增產品功能。舊v1.1／v2.0指令保留Git歷史，以本次明確決定為準，角色不因此改變。Owner最新指令優先；若Plan／Handoff矛盾，停止相依操作並列出差異，不自行選較寬鬆版本。

本文件不自含自己的新Git commit SHA，以免自引用；交付時從Git／PR讀回精確commit。Plan digest綁定實際bytes，任何Plan變更都須更新本文件兩處digest並重核，舊review不自動轉移。本次Plan免獨立審查仍固定本版bytes／SHA；進度寫task報告，必要澄清建立新revision及影響分析，不再加獨立Plan等待；實質scope／AC／授權／Gate／架構變更先回Owner決策。實作後Code Review仍綁精確來源，不轉移舊批准。

## 2. 當下允許與不得冒稱的狀態

```text
OVERENGINEERING_AUDIT=PASS
OVERENGINEERING_AUDIT_SCOPE=PLAN_V2_1_MINIMAL_DESIGN
OVERENGINEERING_AUDIT_ROLE=PLANNER_NOT_INDEPENDENT
PR31_SOURCE_OVERENGINEERING_AUDIT=NEEDS_SIMPLIFICATION
MINIMAL_IMPLEMENTATION_PLAN=READY
EXTERNAL_PLAN_REVIEW=OWNER_WAIVED
EXTERNAL_CODE_REVIEW=NOT_RUN
ZERO_GUI_PREFLIGHT=NOT_RUN
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

本Session仍只更新文件及Git。受派Implementor可依本次Owner免審決定，核對本版SHA後從M0開始有界離線實作；不等待External Plan Review或獨立設計audit。設計層PASS有Plan§4.3的逐項收斂理由，非免審即PASS；M0／產品／CI／實機均未執行。

本輪文件與Git授權不建立Mac前景、目標manifest、Save All或重啟授權。所有實機仍待Code Review／必要測試及Owner當次交接；重開Mac由Owner執行。Implementor不可自填獨立E2E PASS。

## 3. 最短必讀與取證順序

1. 完整讀本Plan，尤其§0、§4～§11，核對digest及固定AC。
2. 讀[PR31 Chief Review](https://github.com/s9008129/Line_backup/pull/31#pullrequestreview-5611062176)，核對B01～B04。
3. 讀原始PRD；若本機檔缺少，明示UNAVAILABLE，不宣稱已讀，不猜需求。
4. 讀[PR28完整報告](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/harness-development/line-five-album-manual-20261022/E2E測試報告.md)、public/evidence-index.json及[接受範圍](https://github.com/s9008129/Line_backup/pull/28#pullrequestreview-5608322661)。不重跑已下載相簿。
5. 只讀下表Mac來源；原資料root為`~/Documents/ChatGPT/Line_backup`，不用新worktree cwd解析歷史目的地。

| 來源 | 取用方式／限制 |
|---|---|
| PR28 private/checkpoints.json | 原repo的harness-development/line-five-album-manual-20261022/private/checkpoints.json；1783 bytes；SHA 69d385ac9ccf3f5ba139ca45b6d0412c17499ce9e3e6c44eb50b62cb786f548e；只讀reference，不升級原檔 |
| PR28 private目的地 | 以原測試包為base；FILES_VERIFIED字串不是durable intent或新VERIFIED |
| ImageIO source | 原repo src/line_backup_batch/image_decode.swift，指定SHA如開頭Prompt；來自72dae704基線 |
| OCR source | 原repo harness-development/catalog-diagnostic-20261010/modern_ocr.swift，指定SHA如開頭Prompt；本機未tracked，不假稱GitHub已有 |
| 正式state | state/backup_state.json，只讀歷史239與屏障，不寫入 |
| manual archives | state/manual_archives.json，只讀109及manifest／verification，不呼叫registry writer |
| 五本329 | checkpoint＋公開身份索引＋私有manifest／decoder／身份證據；不只信summary |
| 65排除 | 既有常數是候選映射，須核對私有scope／Owner關聯；不能只靠數字排除 |
| pilot policy／grant／ledger | 只作保護基線；不用它授權Agent A，不改、不reset |

來源hash若合理前進，保存差異，不強行回退舊資料。缺少歷史映射就保留deny barrier，不把缺資料當從未下載。

## 4. Git／worktree接手

目前原repo為v43-ab/codex-rev28／1b9a010，含無關dirty與大量untracked；不切branch、不stage該樹其他內容。文件在乾淨兄弟worktree `~/Documents/ChatGPT/Line_backup_agent_resume_handoff_20261022` 更新，同scope PR30。若接手時狀態已不同，先對帳。

未來Feature A從當時最新master建外部乾淨worktree，記精確base SHA，再逐檔納入本版Plan／Handoff及指定原樣工具；不能直接從PR31或把整筆1b9a010 cherry-pick。CI B另從1b9a010建sibling分支，PR target v43-ab/codex-rev28，不帶進feature，不自動merge。兩工作包序列完成，不新增平行writer。

分支／worktree已存在時先查HEAD、dirty與獨有commit，不覆蓋。Git授權涵蓋逐檔commit/push／Draft PR交付，不涵蓋merge、force-push、原照片或protected資料寫入。

## 5. 範圍與接口對照（不擴寫Plan）

| 本項 | 唯一權威位置／要求 |
|---|---|
| 本輪文件範圍 | Plan§5.1：只plan.md／handoff.md |
| Feature A檔案 | Plan§5.2；兩新控制／接線檔、原樣Swift、聚焦測試／workflow、必要報告；無正式package import |
| CI B檔案 | Plan§5.3；workflow／generator／合成seed／inspection consumer與負例／報告 |
| AC | Plan§5 AC01～AC10，不能刪減或自行重定義 |
| 資料契約 | Plan§6，單checkpoint；結果／next_index由持久事實推導 |
| 原子提交／tmp | Plan§7；正式canonical是authority，失敗無click資格，保留temp不自動promotion |
| CLI／JSON-lines／生命週期 | Plan§8；同session stdio，單writer，EOF永久停止，舊host活／pending不明拒接管 |
| CI | Plan§9；當前producer六case，缺env precondition FAIL，strict consumer修復不擴權 |
| 測試 | Plan§10 TC01～20；新程序100本，不只object重建 |
| 階段／Gate／角色 | Plan§11；G0→M0→M1/M2→Code Review／offline／CI→獨立Mac→結案 |
| 交付與隱私 | Plan§12；逐檔stage、真實commit body、遠端讀回、private不公開 |

禁止路徑：Harness／controller／runtime defaults／既有schema、正式AUTO service／coordinator／adapter／two_album_entry、正式State／Grant／Ledger／pilot policy、歷史checkpoint／證據／照片、Native Diagnostic程式。CI唯一產品來源例外只有Plan§5.3明列的ProjectBackupBinding.swift有界修復；不能藉此改native capture或正式授權。

## 6. 恢復結果速查

| 持久事實及檔案 | 必須行為 |
|---|---|
| 前49有效、#50完整store無intent且空目的地 | #50 fresh開始；前49零新增Save All |
| #50有intent，0檔／遺失ack | UNKNOWN，停止，不重送 |
| #50 32/80 | BLOCKED_PARTIAL，保留32全部bytes，#50～100零自動派送 |
| #50 80/80且身份／目的地／chooser關聯完整 | SHA／ImageIO／穩定性／post-decode通過，鎖內補VERIFIED，下一次只#51 |
| 滿額但來源不足 | BLOCKED_AMBIGUOUS |
| 已VERIFIED後缺檔／hash變／decode失敗 | BLOCK，不補下載 |
| 舊host活／pending input不明 | 不接管、不TTL／kill／unlink；先安全關閉舊Session |
| canonical壞／缺、scope變／多個未解in-flight | BLOCK，無自動init／舊backup回退 |
| canonical有效但有孤立tmp | 按Plan§7保留tmp、依canonical判斷；tmp不是authority或派送許可 |

實際input、RETURNED／UNKNOWN、intent預留、檔案完成與VERIFIED分開計數。相同照片hash合法；不得要求329不同digest的歷史特性成為產品限制。

## 7. 接手後最短里程碑

- M0（無獨立Plan前置）：核對原樣工具source；fake app＋真stdio controller／flock／EOF／host與boot身分／storage primitive。無LINE app取得、截圖或input；失敗只提報，不重研發CUA。
- M1：單一store、固定manifest、history reference、同一verifier、單次Save All／chooser及fault tests；禁止新框架／冗餘狀態機。
- M2：100本TC矩陣與Mac ImageIO；Feature CI及legacy CI各精確HEAD。完整報告與Draft PR供External Chief看實際源碼。
- G4：只有Code Review及必要Gate成立、Owner新F/G與前景交接後，另啟獨立DeepSeek1017 Session完成兩本＋Mac重啟。實作者不操作正式E2E或代寫判定。

M0能力是待驗證事項，不能在報告把「Plan設計了stdio」填成runtime PASS。兩本真實結果也不能證明所有100本故障點；兩層證據各自成立。

## 8. 阻塞提報與交付格式

同根因至多三次有證據attempt；兩次無新資訊／material blocker提前停，保留失敗。提報最少：

```text
TASK_ID / PLAN_REVISION / PLAN_SHA256 / IMPLEMENTATION_COMMIT
ACTUAL_MODEL / PROVIDER / SESSION / WORKTREE / RUNTIME
AFFECTED_AC_TC / EXPECTED / ACTUAL / FIRST_FAILURE
REPRODUCTION / RAW_ERROR / EXIT_CODE
ATTEMPTS_AND_NEW_INFORMATION / FACTS_INFERENCES_UNKNOWNS
GUI_CALLS_RETURNED_UNKNOWN / STATE_BEFORE_AFTER / SIDE_EFFECTS
EVIDENCE_RELATIVE_AND_PRIVATE_ABSOLUTE_PATHS_BYTES_SHA256
STOPPED_DEPENDENT_ACTIONS / SAFE_REMAINING_ACTIONS
ONE_PRECISE_DECISION_NEEDED / NEXT_ACTION
HIGH_MODEL_HANDOFF=PENDING_OWNER_FORWARD
```

寫在Plan允許task issues/，raw留private，公開版去識別化。問題未實際送達就不稱已提交高階模型。修復超出scope／架構／AC／資料或授權邊界先交Planner，不自行降低Gate。

每次實測更新task E2E測試報告.md，progress短記第一阻塞與attempt，不重複多份長報告。交付六狀態，附精確HEAD／來源hash及AC逐項PASS／FAIL／BLOCKED／NOT_RUN；IMPLEMENTATION_DONE不等於整體PASS。

## 9. 指定03_handoff_prompt.md的實際適用

已讀 `~/.codex/prompts/v4.8.0/03_handoff_prompt.md`；SHA `e27860d1da047ec1d9ece6440d9ec3f19014b0cefbb2e7b6ff00f8d564ebde37`。其Optional Handoff Reviewer只在workflow要求時核對已審Plan／compiled handoff，不得改契約、增Gate／路徑或執行Implementation；只用該task stage packet emitted CONTRACT／RESULT命令。

本task尚無已審frozen contract、controller stage packet或固定validation命令，因此本文件是Markdown advisory handoff；不生成假handoff.json，不宣稱deterministic compiler、optional review PASS、format3 validation或controller admission。文件一致性檢查只是本地文件檢查，不是該角色的正式Gate。

## 10. 文件階段驗證紀錄（v2.0歷史及v2.1追加）

以下v2.0紀錄保留歷史，不自動轉作v2.1驗證；兩版皆只更新兩份Markdown。完整規劃／審查報告在plan.md，不另造E2E成功報告。

- 本地文件一致性檢查11/11 PASS：UTF-8／無NUL、code fences成對、Plan digest兩處相符、開頭Prompt、AC01～10、TC01～20、六狀態／裁決一致、無個人絕對路徑、僅兩檔差異、audit精確對應指定commit全部31個不同路徑。首次TC檢查因regex未補零誤報，修正檢查器為03～20後通過；沒有修改AC／TC湊PASS。
- Plan／Handoff的scope／Gate／狀態／工具SHA已讀回核對。Luna指出核准後文件回填可能造成SHA漂移；本版已收窄：已審bytes凍結、進度寫報告／收據，修訂需新revision與External Chief確認新SHA適用性。
- 已執行git diff --check、git diff --cached --check及staged blob讀回，PASS；stage只有plan.md／handoff.md。原repo同名副本逐bytes相同；本節回填後在提交前再核對最終bytes與stage。
- 已對照本輪恢復時baseline：原repo branch／HEAD／index hash、其他tracked dirty bytes、backup_state／manual_archives／pilot policy／PR28 private checkpoint hashes均相同。只同步Owner指定的兩份文件，不stage原repo的既有dirty／untracked。
- 已依Owner明確要求用collaboration.spawn_agent設定gpt-6-luna／high、fork_turns=none，執行luna_commit_context唯讀梳理完整Plan／Handoff、原PRD、指定prompt與diff，回報版本綁定疑慮及含意圖／做了什麼／驗證與結果／下一步的建議之commit草稿。root修正疑慮並負責最終Git；此協作不是External Review或獨立E2E。
- 產品測試／新ImageIO／LINE GUI／Save All／Mac重啟／獨立E2E：NOT_RUN。

### v2.1追加

- Owner明確免除本次獨立Plan Review；G0記OWNER_WAIVED，並保留Code Review／獨立E2E。Plan§4.3為Planner設計層audit，未冒充獨立批准或產品PASS。
- 本版本地文件檢查16/16 PASS：UTF-8／無NUL、fences、Plan digest兩處綁定、開頭Prompt、AC01～10、TC01～20、具scope裁決、六狀態、無個人絕對路徑、兩檔範圍、31檔audit精確對應指定commit、免審語義、Code Review／E2E保留、設計必要性理由、無runtime PASS、工具／指定prompt hashes。git diff --check亦PASS；這不是產品測試或獨立審查。
- 原repo branch／HEAD／index、兩個其他tracked dirty檔與四個protected hashes已對照本次修改前baseline，PASS；同步前兩份原文件亦與前版相同。最終同步／stage後仍由root讀回核對，Git／PR遠端結果以實際commit為準。
- 已由原gpt-6-luna／high唯讀子代理luna_commit_context續梳理本版完整Plan／Handoff、相對82773cf的diff與Owner免審語義，確認沒有隱藏Plan等待條件，提供含意圖／做了什麼／驗證與結果／下一步的建議之詳細commit message；root負責最終文件及Git。此協作不是Independent Plan Review。
- M0／產品測試／ImageIO／CI重跑／LINE GUI／Save All／Mac重啟／獨立E2E：NOT_RUN。

## 11. 第一個next_action

root完成文件檢查、Luna提交訊息與逐檔Git交付後，提供更新PR30／精確commit／Plan SHA。接手Agent核對Owner本次明確免審、角色、scope與SHA，直接M0，不再停在Plan送審。實作交付後仍交External Chief Code Review與獨立DeepSeek E2E。
