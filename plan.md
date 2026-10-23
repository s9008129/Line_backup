# LINE Agent 100 本相簿中斷接續：最小修正 Plan

- Task：`AGENT-RESUME-P0-20261022`；revision：`v2.1 / 2026-10-22`。
- 範圍：PR #31 B01～B04、完整過度工程化審查、Agent 模式 A 跨 Session／Mac 重啟接續。
- 本輪只交付文件。產品實作、零 GUI runtime preflight、故障注入、新 ImageIO、LINE 操作及獨立 E2E 均 `NOT_RUN`。
- 請求的 Planner：GPT-6.1-SOL／xhigh；沒有可獨立核對的模型／effort 收據，不冒稱 runtime attestation。
- 本版承接 `82773cffee7b1ffdabcd14ca0d688a682a3be24f` 的 v2.0，依Owner最新明確指示「本次 Plan 不需要獨立審查」取消本次獨立Plan／設計audit等待關卡；v1.1、v2.0與原裁決保留Git歷史。

## 0. 裁決、授權與第一個動作

```text
OVERENGINEERING_AUDIT=PASS
OVERENGINEERING_AUDIT_SCOPE=PLAN_V2_1_MINIMAL_DESIGN
OVERENGINEERING_AUDIT_ROLE=PLANNER_NOT_INDEPENDENT
PR31_SOURCE_OVERENGINEERING_AUDIT=NEEDS_SIMPLIFICATION
MINIMAL_IMPLEMENTATION_PLAN=READY
EXTERNAL_PLAN_REVIEW=OWNER_WAIVED
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

Owner最新明確決定：「本次 Plan 不需要獨立審查。」本版據此將獨立Plan Review記為OWNER_WAIVED，不生成APPROVE_PLAN或獨立review PASS，也不以另一個獨立設計audit名稱保留同一等待關卡。強制Overengineering Audit仍保留；§4.3對已完成的最小設計逐項收斂覆核，Planner判定設計層PASS，並完整保留PR31產品來源NEEDS_SIMPLIFICATION。免審本身不是audit通過的證據。

MINIMAL_IMPLEMENTATION_PLAN=READY只表示本版有界離線工作包可交實作者接手，先做M0零LINE接線實證；不表示runtime能力、程式、CI、檔案或實機已通過。當下本Session仍只更新文件與Git；下一位受派Implementor可在固定scope依序做M0／M1／M2，不必再等待獨立Plan批准或重問相同授權。

本次豁免僅限Plan層。實作後External Code Review、必要離線／遠端CI與獨立DeepSeek E2E保留；LINE前景、新相簿Save All及Mac重啟仍需原有當次條件。不改Harness、執行grant、quota、ledger或CLOSED authority，不擴張產品範圍。

第一個next_action：交付本版精確commit／Plan SHA與Handoff；接手Implementor唯讀對帳後直接從M0開始。M0若能力不成立，保全第一失敗成單，不新增bridge或GUI引擎。

## 1. GOAL／SCOPE／NON-GOALS

保留 PR28 已成功的 DeepSeek Agent Computer Use、fresh screenshot、AX、Vision OCR、metadata 點擊、detail 核對、真實 menu OCR、Save All、Chooser、SHA-256／ImageIO；增加最少的持久化控制。使用者每次自行啟動 Agent；新 Session 從 Mac 本機資料恢復，不依賴舊對話。

核心案例：100 本清單的 #1～49 已完成，#50 中斷。#50 完整且來源證據足夠，重驗並提交後只續 #51；#50 partial／仍 unknown，保留照片，整個 task 停止，不重送、不跳過。

沿用既有決策：runtime root 為 `~/Library/Application Support/LineBackup/agent-resume/`；歷史照片原處只讀；最小真實 E2E 為兩本未備份新相簿，第一本完整後由 Owner 重開 Mac，再由新獨立 DeepSeek Session 接續第二本。

不做：相簿內續傳、強制 retry／reset／skip blocker、排程、開機自動執行、新 GUI／OCR／capture 引擎、Native Diagnostic 修復、正式 TWO_ALBUM_AUTO 修復、Harness 重設計、SQLite／新大型 framework、通用 migration、歷史照片搬移或大分支合併。

## 2. SOURCE-VERIFIED BASELINE／事實與未知

### 2.1 固定來源

| 來源 | 已核對的事實與限制 |
|---|---|
| 原始需求 | 本機 `~/Downloads/LINE_backup_PRD_Agent_Interrupted_Resume_v1.0_20261022.md`；SHA `0d69c560490504f1b2af5466db680768e27924c4416c879d8c0545f1224a75d5`；FR01～16、TC01～20仍適用 |
| [PR31](https://github.com/s9008129/Line_backup/pull/31) | exact HEAD `1b9a010aeba2e75a406d842be123d7251501548c`；單筆 commit 31檔、+6911／-193；整個PR 177 commits／1900檔，不可直接merge |
| [PR31 Chief Review](https://github.com/s9008129/Line_backup/pull/31#pullrequestreview-5611062176) | `BLOCKED_FOR_RESUMABLE_AGENT_FEATURE`／`NOT_APPROVED_TO_MERGE`，B01～B04；不是新方案批准 |
| [PR30](https://github.com/s9008129/Line_backup/pull/30) | 既有文件commit `aa415ef6a2f665bf866631762154dc4b0470d3a3`；舊Plan SHA `8ff887a153e5a363979bbd3e622dc998db4ae9e4f705ef45a5a4ba975c5f646b`；本輪更新同範圍Draft PR |
| master | 本輪remote讀回 `64515eb56b04accc40ade9e2db2fe0ad18c1ced3`；接手時重讀最新base並記SHA，不憑分支名稱推定 |
| [PR28 Chief Review](https://github.com/s9008129/Line_backup/pull/28#pullrequestreview-5608322661) | 接受manual-diagnostic公開證據；私有照片解碼／GUI操作仍為本機Agent報告，不等於外部重現 |
| PR28工具來源 | `72dae704a9a5f3dbdee21e33178201350b6e7a06`；完整[報告](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/harness-development/line-five-album-manual-20261022/E2E測試報告.md)；master經PR29只收八個證據檔，不能假設全部工具已存在 |
| 正式batch | PR31 HEAD `src/line_backup_batch/coordinator.py:13`遇active batch返回；`service.py:1015`只有RECONCILE_ONLY、不dispatch；不修改 |
| 正式transaction | `src/line_backup_acceptance/transaction.py:380` resume保留UNKNOWN屏障；參考不變條件，不調用正式授權流程 |
| ImageIO | `src/line_backup_batch/image_decode.swift`；SHA `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b`；原樣重用 |
| OCR | 本機 `harness-development/catalog-diagnostic-20261010/modern_ocr.swift`；SHA `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861`；未tracked來源須原bytes納入乾淨PR，不假稱從master取得 |
| 內容驗證方法 | `src/line_backup_batch/content.py:14`；穩定inventory、hash／decoder交叉比對、post-decode核對；因正式package／backups containment耦合，不整包import |

行號綁定上述commit，之後改動需使用新SHA／行號，不轉移舊PASS。

### 2.2 PR28私有checkpoint已實際讀取

來源：原repo `harness-development/line-five-album-manual-20261022/private/checkpoints.json`；1783 bytes；SHA `69d385ac9ccf3f5ba139ca45b6d0412c17499ce9e3e6c44eb50b62cb786f548e`。

頂層為 `albums/model/provider/repo_head_at_start/session_id/test_type/totals/updated_at`。albums為A45／B78／C77／D42／E87 object；欄位包含destination、expected_images、verified_images、status、unknown_outcome、save_all_dispatches_this_session，A45另有previous_session_save_all_dispatches。五本記FILES_VERIFIED。

它缺schema_version、ordered manifest、durable pre-intent、generation及writer ownership。只建立唯讀參照；不原地升級、不把字串狀態直接當新VERIFIED。相對目的地以原測試包解析，不能相對新worktree或cwd解析。

### 2.3 未知與證據限制

- 本輪沒有重新計算歷史照片SHA或ImageIO，不宣稱329張新驗證PASS。
- 既有成功不能證明任意crash點的耐久性或實體exactly-once。
- hosted CUA runtime能否安全維持子程序stdio／長生命週期controller尚待M0；不預設工具能力。
- macOS filesystem的directory sync／F_FULLFSYNC及照片flush回傳語義須M0／M1實測，不靜默降級。
- 65張完整日期指紋可從既有manual_archive常數取得候選，但其當前群組／Owner排除關聯仍須與私有來源核對；不能只靠「65」排除。缺少只阻擋live，不阻擋獲准的合成測試。
- 新clone不含私有checkpoint、照片及原始GUI證據；缺少就報來源不足，不重建假歷史。

## 3. B01～B04根因與修正邊界

| Finding | 根因 | 最小修正／不做事項 |
|---|---|---|
| B01 | 正式coordinator／resume只對帳，沒有Agent A continuation | 新獨立Agent A入口；不放寬正式resume、不清active_batch |
| B02 | A45／B78 allowlist、兩本quota、單本lifecycle是正式pilot範圍 | Owner凍結ordered manifest至少100本；不改quota、不套A45/B78當一般資格 |
| B03 | CI缺環境與可攜fixtures；另有Python／Swift契約漂移 | 生成六組合成fixtures＋env／precondition＋有界consumer修復；不skip，不引入新診斷架構 |
| B04 | 小commit位於177 commits／1900檔分支 | 新feature自最新master逐檔移植；CI維修另target legacy；不merge／整筆cherry-pick PR31 |

CI新發現：Python `project_binding.py:18,391`已新增manual_archive.py來源與manual_archive_match事實；Swift `ProjectBackupBinding.swift:57,327`仍要求舊集合。這是源碼可見的不相容，尚未在本輪執行重現；不能說只補env即可全綠。

## 4. 完整Overengineering Audit

分類針對本次100本恢復的採用範圍；DEFER不等於刪歷史，KEEP不等於移入feature。REMOVE_CANDIDATE需另證明caller與移除安全性，本Plan不授權刪除它。

縮寫：C=`rev28/Sources/Rev28Core/`，X=`rev28/Sources/rev28ctl/`，T=`rev28/Tests/Rev28CoreTests/`，B=`src/line_backup_batch/`，A=`src/line_backup_acceptance/`。下表31列與指定commit的實際changed-file list逐一對應。

| 模組／檔案 | 實際用途 | 過度工程化證據／範圍判斷 | 分類 | 最小調整 | 風險 |
|---|---|---|---|---|---|
| `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/live_classifier.mjs` | boundary排序修復 | 歷史classifier，不提供恢復 | DEFER | 留原支線 | 低 |
| `rev28/ARCHITECTURE.md` | 診斷架構文件 | 多數內容無關本PRD | DEFER | 不移植 | 低 |
| `rev28/CAPABILITY-MATRIX.md` | 診斷能力限制 | 非task continuation | DEFER | 保留歷史 | 低 |
| `C/Composition/LiveComposition.swift` | 拒診斷進正式路徑 | 必要隔離，非冗餘 | KEEP | 原處維持 | 刪除破壞隔離 |
| `C/Composition/PassiveNativeDiagnostic.swift` | 三版本packet／重建 | 510行獨立診斷系統 | DEFER | 不作Agent依賴 | packet相容性 |
| `C/Composition/ProductionObservationSource.swift` | descriptor及capture | 診斷擴展，不是checkpoint | DEFER | 原處維持 | native耦合 |
| `C/Observation/NativeObservationSession.swift` | v3 binding | 擴展觀察契約，無下載接續 | DEFER | 不移入 | 高耦合 |
| `C/Observation/PassiveContextObservation.swift` | AX／CG／OCR collector | 631行另一觀察流程 | DEFER | 用PR28既有方式 | 避免重建引擎 |
| `C/Observation/VisualDiagnosticContract.swift` | capture／clock配對 | 334行獨立診斷契約 | DEFER | 不作前置 | 診斷不能授權 |
| `C/Perception/AlbumVisualWitness.swift` | 完整卡片safe-area | 查無production呼叫；已有metadata成功流程 | REMOVE_CANDIDATE | feature不納入；刪除另審 | 外部caller未知 |
| `C/Sensor/ExplicitLineCaptureSelection.swift` | 特殊capture集合 | 新診斷架構 | DEFER | 不移入 | 與恢復無關 |
| `C/Sensor/RunEpochAuthority.swift` | descriptor epoch | 診斷目錄生命週期 | DEFER | 不當album進度 | epoch不是intent |
| `X/PassiveCaptureDiagnostic.swift` | passive CLI | 額外診斷入口 | DEFER | 不移入 | 低 |
| `X/PilotNativeAuthority.swift` | Swift→Python authorizer | 重複grant／runtime檢查、ONE56與特定Python路徑 | DEFER | Agent不調用 | 正式guard不可刪 |
| `X/VisualDiagnostic.swift` | CUA／SCK／OCR診斷 | 增加跨capture契約 | DEFER | 不移入 | 中 |
| `X/main.swift` | 多診斷CLI接線 | 旁支依賴閉包大 | DEFER | 不整包移植 | 隱含依賴 |
| `T/AlbumVisualWitnessTests.swift` | 幾何單測 | 功能不在本PRD | DEFER | 不計恢復AC | 非E2E |
| `T/ExplicitLineCaptureSelectionTests.swift` | capture負例 | 同上 | DEFER | 留原支線 | 低 |
| `T/LiveCompositionTests.swift` | 診斷隔離負例 | 必要安全測試 | KEEP | 原處維持 | 不可刪隔離 |
| `T/NativeObservationSessionTests.swift` | v3／mapping負例 | 不對應100本恢復 | DEFER | 不當核心Gate | 非恢復證據 |
| `T/PassiveContextObservationTests.swift` | schema roundtrip | 不驗真capture／恢復 | DEFER | 留原支線 | 有限覆蓋 |
| `T/PassiveNativeDiagnosticTests.swift` | packet／filesystem負例 | 479行服務旁支功能 | DEFER | 不列恢復成果 | 保留歷史 |
| `scripts/line_backup_cua_adapter.mjs` | 正式session／chooser／scroll | PNG decoder、兩套viewport比較、V2／V3／hooks混合 | SIMPLIFY | 本輪不原地重構；新wrapper只包副作用 | 原地精簡高風險 |
| `A/manual_archive.py` | 歷史109防重複 | writer、硬編碼allowlist及重複JSON／原子寫入 | REUSE | 只讀資料與證據；不呼叫writer | 漏歷史會重送 |
| `A/project_binding.py` | inspection／歷史判斷 | Python／Swift契約重複且已漂移 | SIMPLIFY | Agent無新Swift consumer；CI獨立修 | 不可寬鬆解析 |
| `B/cli.py` | grant／ONE56 | 約500新增行硬綁PR10／actor／paths | DEFER | 不納入Agent | 正式guard保留 |
| `B/observations.py` | grounding／lineage | native鏈及56張特例 | DEFER | 不泛化到100本 | 特例非授權 |
| `B/service.py` | A／C1／B交易 | 與ledger重複workflow；resume仍不續跑 | DEFER | 原樣維持 | 不擴正式AUTO |
| `B/store.py` | CAS／GUI ledger | 雙檔phase／slots／quota，非Agent需求 | KEEP | 正式保留；Agent不複製 | 原子與防重送必要 |
| `tests/test_batch_authority.py` | 正式authority負例 | 不驗100本新Session | KEEP | 不當核心AC | 數量非完成 |
| `tests/test_cua_adapter.mjs` | adapter／scroll合成 | 無100本持久化；該檔未見requireV3測例 | KEEP | 另測新wrapper | 22/22非全路徑 |

### 4.1 直接依賴審查

| 模組／檔案 | 實際用途 | 過度工程化證據／必要性 | 分類 | 最小調整 | 風險 |
|---|---|---|---|---|---|
| PR28 private checkpoint | 五本摘要 | 缺pre-intent與durability | KEEP | 只讀reference | 不可直接升VERIFIED |
| B/coordinator.py | 正式協調 | active直接返回 | DEFER | 不改 | 不放寬AUTO |
| A/transaction.py | UNKNOWN屏障 | 真正必要不變條件 | KEEP | 參考語義 | 不可移除 |
| A/common.py | 原子JSON | dir fsync失敗可降級 | REUSE | 參考算法；新store嚴格失敗 | 不直接沿用降級 |
| B/content.py | 內容驗證 | 綁正式package／backups | REUSE | 重用順序，不整包import | 不可只數檔案 |
| B/image_decode.swift | 完整RGB解碼 | 已實測成熟工具 | REUSE | 原bytes納入 | stub非解碼PASS |
| modern_ocr.swift | Vision OCR | 已實測但未tracked | REUSE | 原bytes納入 | 缺來源須停 |
| B/state_v3.schema.json | 正式schema | 與新store無關 | DEFER | 不增加正式版本 | 不污染state |
| C/Composition/ProjectBackupBinding.swift | inspection consumer | 與Python集合漂移 | SIMPLIFY | CI範圍有界修復 | 保持canDispatch=false |
| T/ProjectBackupBindingTests.swift | strict consumer負例 | fixtures未供應 | KEEP | 生成合成資料，不skip | 防CI假綠 |
| plan.md／handoff.md v1.1 | 恢復方案 | 多份持久狀態、固定重複核驗、tmp一律阻塞 | SIMPLIFY | 本版單真相／推導結果／明確tmp規則 | 設計覆核見§4.3；實作待驗 |

### 4.2 方案A／B與必要複雜度

| 評估 | A：既有工具＋薄持久化控制 | B：正式AUTO擴張／新架構 |
|---|---|---|
| 必要功能 | ordered scope、intent、verify、single writer | 仍需相同核心 |
| 範圍 | 兩個控制／接線檔、原樣工具與聚焦測試 | Python／Swift／CUA／grant／ledger |
| 跨Session | 單一控制真相＋不可撤intent | 多份契約一致性負擔 |
| 測試／維護 | 對應TC01～20 | 額外版本、mapping、capture組合 |
| 回歸 | 正式AUTO隔離 | 觸及凍結邊界 |

選A。反向驗證答案為「可以用最少新控制及既有工具完成」，因此明確不採B。沒有實際失敗案例支持新增capture／service／ledger架構。

必要新增控制不可再刪：原checkpoint在click後摘要前crash無法區分是否派送；跨Session無單writer會雙派送；跨task無共同屏障可換ID重下載。保留原子寫入、sync、readback、generation、schema及intent，不因行數精簡刪安全性。

精簡決策：單checkpoint內保存tasks／歷史reference／邏輯append-only事件；task phase、next_index、VERIFYING及PARTIAL結果由事實推導，沒有第二份可寫狀態機。獨立reconcile供預覽，resume持鎖呼叫同一核對函式一次，不要求先預覽再必重做兩次全量解碼。事件不作通用event-sourcing重播。

### 4.3 v2.1最小設計收斂覆核（Planner，非獨立審查）

此覆核針對本Plan的實際設計與固定檔案契約，不對尚未修改的PR31程式發出PASS。逐項依據如下：

| 必要複雜度／原疑慮 | 本版實際收斂與必要性證據 | 設計判定 |
|---|---|---|
| 多套狀態／ledger／registry | §6～§8只有一份控制checkpoint；phase／next_index／驗證結果推導；歷史只讀reference，不建第二可寫真相 | PASS |
| 新CUA／Native／OCR架構 | §5.2只新增控制器與副作用wrapper，兩Swift原樣；31檔audit的旁支不納入feature | PASS |
| wrapper／跨語言必要性 | PR28是工具驅動Agent，Python負責本機durability，既有Node app呼叫保留；§8限定單一stdio，不引入service／daemon／framework。click後摘要前crash的具體缺口要求pre-intent控制 | PASS |
| 重複驗證成本 | §6與§8.4重用同一verifier；resume一次持鎖核對，不強制先跑另一份preview；in-flight完整穩定性、已完成前後inventory／hash／decode各有資料安全理由 | PASS |
| 過度保守tmp規則 | §7區分有效canonical與壞／缺canonical，temp永不當許可；不因孤立temp一律癱瘓，也不刪掉必要intent | PASS |
| 過多測試／無業務效果 | §10僅固定TC01～20及新wrapper／真ImageIO，100本用小fixture，實機只兩本新目標；不反覆要求旁支全repo回歸 | PASS |
| CI修復擴scope | §5.3及§9獨立legacy工作包，六case＋consumer小修，不將依賴閉包帶入feature，不為過綠放寬guard | PASS |
| 不可刪的持久化控制 | 無pre-intent會重送、無共用鎖會雙writer、無跨task歷史可換ID重下載；sync／readback／decode均對應已列故障，不因精簡刪除 | PASS |

反向驗證仍為「最少兩個新控制／接線檔加既有工具即可完成」，因此選A，沒有新增架構的必要性。本版沒有未說明的設計層複雜度：OVERENGINEERING_AUDIT=PASS／scope=PLAN_V2_1_MINIMAL_DESIGN。M0可用性、來源實作精簡與全部驗收仍NOT_RUN；M0失敗是執行阻塞，不以本設計PASS掩蓋。

## 5. AC與最小檔案契約

| AC | 必須成立 |
|---|---|
| AC01 | 至少100本固定ordered manifest跨新程序／Session恢復，不靠chat |
| AC02 | 前49有效且#50無intent：前49零重送，#50 fresh開始 |
| AC03 | #50滿額且來源成立、未提交VERIFIED：重驗補提交，下一次僅#51；#1～50增量0 |
| AC04 | #50 32/80或仍UNKNOWN：保留原bytes，全task停止，#50～100零自動派送 |
| AC05 | intent、重複request、遺失回覆、crash／reboot不解除屏障；單writer跨task成立 |
| AC06 | 只操作Owner manifest且當次前景授權有效；新Session不用舊座標／PID／AX引用 |
| AC07 | 239／109／329與65排除不重下載／覆寫；正式State／Grant／Ledger／Harness不變 |
| AC08 | 兩本新eligible相簿：第一本完整→Owner Mac重啟→新獨立Session→跳第一本→第二本完整 |
| AC09 | CI fixtures可攜、現producer契約受測、遠端必要checks綠；各HEAD分開 |
| AC10 | 乾淨PR、逐檔最小diff、完整報告／hash、本次Plan免審決策、實作後External Code Review及獨立E2E可追溯 |

### 5.1 本輪文件寫入範圍

僅根目錄 `plan.md`、`handoff.md`；在既有乾淨文件worktree更新並同步原repo已核對同bytes的副本。原branch／HEAD／index及其他dirty檔保留。不另外建立相同內容的Plan.md大小寫副本。

### 5.2 Feature A固定允許檔案

| 路徑 | 唯一責任 |
|---|---|
| scripts/line_backup_agent_resume.py | 標準庫store／嚴格JSON／鎖／read-only history／verify／next-safe／CLI／stdio session |
| scripts/line_backup_agent_resume_cua.mjs | 既有app單次副作用邊界與stdio接線；不做新locator／OCR／capture |
| scripts/agent_resume/image_decode.swift | 指定SHA原樣工具 |
| scripts/agent_resume/modern_ocr.swift | 指定SHA原樣工具 |
| tests/test_agent_resume.py | 核心100本／storage／identity／process故障測試 |
| tests/test_agent_resume_cua.mjs | 真wrapper＋fake app，實際呼叫／失聯測試 |
| .github/workflows/agent-resume.yml | 新功能乾淨checkout的Python／Node／Mac ImageIO checks |
| plan.md、handoff.md | 僅必要澄清提案；固定版本不回填執行狀態，不改AC／授權／Gate |
| harness-development/agent-resume-20261022/E2E測試報告.md | 單一完整報告，分離offline／ImageIO／GUI／independent判定 |
| 同task progress.md／issues/ | 既有規範要求的短進度及有真實問題才新增的提報；不複製報告 |
| .gitignore | 僅必要時追加該task private忽略規則 |

不import正式交易package；不增加framework／另一decoder／另一OCR。原樣工具可因master缺少而納入新路徑，需逐bytes驗SHA，不維護兩套不同實作。

版本綁定：本次免獨立Plan審查，仍固定本版Plan／Handoff的bytes與digest供執行對帳；進度與結果寫task報告，不為回填進度改契約。必要澄清建立新revision並作影響分析，同一Owner已授權範圍內不重加獨立Plan Review；scope／AC／授權／Gate／架構有實質變更先回Owner決策。實作後Code Review仍綁精確來源commit，不能把舊來源批准轉移至新程式。

### 5.3 CI B獨立允許檔案

CI分支base固定PR31 HEAD，target原legacy分支，僅以下範圍：`.github/workflows/rev28-macos27.yml`、`tests/build_inspection_fixtures.py`、`tests/fixtures/project_inspection/`（純合成seed）、`rev28/Sources/Rev28Core/Composition/ProjectBackupBinding.swift`、`rev28/Tests/Rev28CoreTests/ProjectBackupBindingTests.swift`、`harness-development/agent-resume-ci-20261022/E2E測試報告.md`與必要progress／issues。不改Python producer來隱藏現有輸出，不改native capture／Harness／正式執行State。

Feature與CI兩個工作包序列交付，不需平行writer。不得把CI legacy依賴閉包移入feature。

## 6. Checkpoint、身分、歷史與檔案核對

固定root：`~/Library/Application Support/LineBackup/agent-resume/`。只有checkpoint.json及固定.session.lock是控制檔；tasks/<task_id>/下放downloads、evidence、verification。private目錄0700、檔0600，runtime store與原圖不進Git。

| 持久事實 | 最低資料 |
|---|---|
| Store | schema_version=1、generation、payload_sha256、last_event_seq、session ownership記錄 |
| Task | task_id、建立時間、固定scope、Owner authorization reference、ordered albums、排除項、manifest_sha256 |
| Album | ordinal、scope-bound album_key、日期起訖／預期數／消歧資料、固定destination、save_all_intent或null、chooser_confirm_intent或null、結果事實與verification reference |
| History | 原來源種類／基準root／digest、身份、目的地、驗證參照或deny原因；只讀正式／manual／PR28 |
| Event | seq、UTC、session／task／album、動作、前後推導結果、證據reference；只追加 |

canonical JSON為UTF-8、排序keys、固定separators，拒duplicate keys／NaN／未知schema。digest排除自身欄位，不把checksum稱簽章或防惡意rollback保證。沒有外部anchor時不能宣稱偵測人為還原整份store；P0不提供restore／rollback／force入口。

manifest建立後scope／identity／order／destination不可原地改；新需求建新task，仍查同store的全部歷史及intent。album_key是scope與canonical身份摘要，不能只用title／ordinal／照片hash。日期相同張數改變、同日期張數多候選、Unicode群組歧義均BLOCK。相同照片bytes可合法重複，以逐檔mapping／multiset核對，不要求hash全唯一、不刪重圖。

歷史匯入只建立reference及deny barrier。完整性／來源成立才能SKIPPED_EXISTING；資料缺失不推定未下載。PR28目的地相對原測試包解析。所有manifest目標需對照239正式、109 manual、329五本、65排除及新tasks；換task／目錄／owner不解除屏障。

新下載獨立空目錄，禁止symlink／traversal／非一般檔／未知額外檔／零byte／partial／temp。新下載穩定性沿用三次相同inventory、3秒間隔、上限600秒；逐檔SHA與原樣ImageIO完整RGB結果對應，再post-decode inventory。已完成album在新resume中重hash／decode；穩定舊完成項不必強制逐本再等兩次3秒，使用前後相同inventory及解碼hash確認；in-flight仍做完整穩定取樣。不新增驗證快取。

完整張數／hash不單獨證明LINE來源。#50 promotion需intent前fresh detail／menu身份、空目的地、固定destination及chooser目標證據。缺證據，即使80張皆decode仍BLOCK。新照片提交前flush照片及目的地，具體可用primitive須在Mac驗證；失敗不能提交VERIFIED。

## 7. 原子提交與恢復決策

每次控制寫入：持全域鎖重讀與驗generation／schema／前提 → 同目錄唯一O_EXCL／no-follow temp → 完整寫入、flush、fsync及目標Mac F_FULLFSYNC → atomic replace → directory durability → 重開解析與generation／digest readback。全部成功才回committed。失敗／回覆不明不產生click資格，不靜默降級。

Apple說明一般fsync未必flush裝置buffer；F_FULLFSYNC適合更嚴格順序，但不保證任意硬體故障：[fsync](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html)。M0/M1記錄實際OS／filesystem／primitive回傳；不因文件提及即稱durability PASS。

temp規則：temp永不當authority、不自動promotion、不覆蓋canonical。canonical有效且可證明所有GUI均在完整提交後才呼叫時，保留孤立temp並依canonical revision決策；canonical缺少／損壞／無法判斷則BLOCK，不從舊backup初始化。temp存在本身不推翻有效intent，也不當第二次派送許可。

對外NOT_STARTED／VERIFIED／SKIPPED_EXISTING／BLOCKED_PARTIAL／BLOCKED_AMBIGUOUS由持久事實和本輪核對推導，不另持久化獨立task phase／next_index／VERIFYING狀態。事件仍記轉移以滿足PRD診斷需求。

| #50事實 | 決策 |
|---|---|
| 有效完整store無intent，合法空目的地 | fresh定位#50可開始；前49零派送 |
| 有intent、0檔／工具回覆遺失 | UNKNOWN，全task停，不重送 |
| 有intent、32/80 | BLOCKED_PARTIAL，保留32及證據；#50～100零派送 |
| 有intent、80/80＋來源／chooser關聯及完整驗證 | 持鎖提交VERIFIED；下一次只#51 |
| 滿額但來源／目標關聯不足 | BLOCKED_AMBIGUOUS |
| VERIFIED後缺檔／hash變／decode失敗 | BLOCK，無補下載 |
| manifest／history衝突、壞canonical、多個未解in-flight | 停止，不推定安全 |

PARTIAL後LINE自然完成可再次唯讀reconcile並重驗promotion；這不是重送。全task有未解blocker時，不自動開始任何後續item。

## 8. 固定CLI與wrapper／controller生命週期

### 8.1 最小公開CLI

`init`（明確首次建立，resume不自動init）、`import-history`（只寫新store reference）、`create-task --manifest FILE`、`inspect --task ID`、`reconcile --task ID`、`session --task ID`。root固定且與task綁定，不自動搜尋／另建store規避歷史。inspect／reconcile不建lock檔、不寫checkpoint／照片、不需LINE／網路／模型；讀取期間generation變化回報不穩定，不拿舊結果授權。

輸出至少含generation／manifest digest、完成／未知／未開始本數、照片數、first blocker、next safe action、gui_dispatches=0（僅唯讀命令）。退出碼0成功、2輸入錯誤、3安全阻塞、4writer busy、5storage／runtime不足。

### 8.2 最小接線契約，不建新transport framework

既有hosted CUA Node wrapper以標準 `node:child_process.spawn` 啟動本地Python `session`，用單一stdio JSON-lines request／response；不經shell、不開socket／HTTP／daemon、不修改CUA或Harness。此能力目前UNVERIFIED；M0若host不允許spawn／穩定stdio／可靠host身分，立即成單停止，不能改用shell GUI或自行研發另一bridge。

wrapper建構接收既有app handle與已批准操作所需的新鮮grounding資料；不接收可任意loop派送的callback。保留PR28辨識與chooser順序，不import原正式adapter，不編造新的app API。M0只能用fake app核對接線，不取得LINE app／畫面。

每個request明確含version=1、request_id、session_id、task_id、expected_generation、operation及限定data；controller驗shape／scope／generation。操作只限session內的reconcile、prepare_save_all、record_save_all_result、prepare_chooser_confirm、record_chooser_result、verify_album、close；不提供獨立prepare／重播token CLI。重複request只返回已存在事實／拒絕，不能再次返回可click的資格。

controller在session開始持固定root非阻塞exclusive flock，涵蓋GUI與所有task。hello記controller PID／start、GUI host PID／start、boot identity；不接受虛構PID。只有stdio原連線與同wrapper原始promise內的首次成功ack可進click；ack含task／album／action_id／generation／checkpoint digest，純檔案或JSON不能重建記憶體資格。

### 8.3 單次副作用與失聯

1. fresh list／detail／menu與Owner清單／當次前景一致，歷史與空目的地通過。
2. wrapper向controller申請intent；controller持鎖durable commit／readback後首次ack。
3. wrapper驗binding、ack未重用、controller仍連線且非closed；在記憶體消耗一次資格，自己呼叫既有app.click一次。
4. 保存RETURNED／exception／timeout事實；任何不確定不retry。不得把RETURNED當下載完整。
5. chooser最終確認同樣先intent再一次app呼叫；未完成chooser的新Session只reconcile，不接續舊操作。
6. wrapper內所有LINE輸入入口均序列化，檢查session alive／未停止；controller EOF／exit／protocol錯誤使wrapper永久closed，不再開始後續GUI。已發出input不能撤回，記UNKNOWN。

controller死後OS釋放flock不代表舊GUI已結束。接手先查boot＋host process instance；舊host仍活／身分未知／pending input無法排除就拒接管，不TTL、不kill、不unlink lock。Owner先正常關閉舊作業並提供新的前景交接。新boot可排除舊boot程序，仍不能解除album intent。

正常close：停止新輸入→等待已發出呼叫結束→保存事實→close ack→釋放鎖；失聯保留未解owner／intent。flock僅合作式鎖，不聲稱阻止人工或其他不合作工具：[flock](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html)。

### 8.4 resume演算法

新Session讀固定store／scope／history → 持鎖核對最近in-flight與所有完成項（同一verify函式一次） → 有blocker就輸出並停止 → 完整#50在鎖內補提交 → 推導第一個NOT_STARTED → 取得當次Owner前景／目標授權 → fresh定位／核對 → 單次Save All／chooser → 完整verify／checkpoint readback → 返回列表並fresh定位下一本。獨立preview不作許可、不要求另跑一次preview；若使用者先做preview，resume仍以當下事實重新核對。

## 9. B03 CI的有界修正

[run39743196793](https://github.com/s9008129/Line_backup/actions/runs/39743196793)的job119705214521：build成功、328 executed／16 failed；16項同在ProjectBackupBindingTests.swift:15缺env。adversarial／replay與headed後續未跑。實際checkout為PR merge commit `3394dfa1ddb83d73b9cde189b4363e89c2435299`，不是直接branch HEAD。這是已讀遠端log，非本輪重跑。

1. build_inspection_fixtures.py由repo位置及明確--output定位，在RUNNER_TEMP生成eligible／verified／busy／unresolved／ambiguous／destination。seed為可公開合成資料，不攜本機照片、群組、人名、歷史證據或絕對個人路徑。
2. 重用既有六case的構造語義，不直接執行私人check_driver／舊Harness腳本；source closure來自當前checkout。verified case所需join／verification要合成一致並重新綁digest，不能弱化校驗。
3. 以當前Python producer實際產生stdout；不是手工PASS或舊report。生成後檢查六組config.json／state.json／stdout.json及引用資料，設定絕對LINE_BACKUP_INSPECTION_FIXTURES到GITHUB_ENV；缺少即precondition FAIL。
4. 必要consumer修復限同步來源清單、嚴格接受新增manual_archive_match=false；true明確拒絕unsupported，不信任boolean直接SKIP，不擴展manual權限或放寬canDispatch=false。補false正常、true拒絕、缺／錯型欄位、來源缺少／改動負例。若需要更大wire／state改版，保全第一失敗提報，不自行擴scope。
5. 維持既有非Vision deterministic suite、adversarial、replay及原required checks；不skip／continue-on-error／調低requiredness。記錄實際測試數，不能硬填333。上傳sanitized fixture index／測試log／toolchain。
6. 遠端新run精確綁CI修復HEAD及merge SHA。feature自己的乾淨CI獨立驗Python／Node／Mac ImageIO；兩個HEAD的綠燈不互相轉移。

## 10. 測試矩陣與證據

fixture至少100個不同album identity，前49完整、#50 expected80、其餘小型；允許合法相同照片bytes。fault injection僅隔離fixture／test seam，不開production略過驗證或stub dispatch旗標。每個重啟用新程序，不只重建object；外部fake app記實際呼叫，不能以intent預留計數替代click。

| TC | 注入／案例 | 斷言／AC |
|---|---|---|
| 01–02 | #50 intent前退出／開相簿後退出 | 前49增量0；#50 fresh；AC01/02 |
| 03 | durable intent後click前kill | UNKNOWN、重啟零click；AC05 |
| 04 | Save All後／chooser前失聯 | 不重送、保留證據；AC04/05 |
| 05 | 32/80中斷 | 32 bytes/hash不變，#50～100零派送；AC04 |
| 06 | 80/80後VERIFIED前kill | 真核對補提交、下一次只#51；AC03 |
| 07 | VERIFIED後少檔／改檔／截斷 | BLOCK、不補下載；AC07 |
| 08 | temp／file sync／replace／dir sync／readback各前後故障 | 完整revision或BLOCK，intent不消失；AC05 |
| 09 | 413／timeout／重複request／遺失ack | 實際click至多1；AC05 |
| 10 | 舊PID／AX／window／尺寸／Session | stale拒絕；fresh不符零click；AC06 |
| 11 | 同task／跨task雙程序，controller死、舊host活、pending input | 只有一writer；wrapper停；不接管未知；AC05 |
| 12 | 同名／同日期異張數／重命名／碰撞 | 不猜SKIP；AC06 |
| 13 | 非空目錄／未知照片／額外檔案 | SKIP或BLOCK，不覆寫；AC07 |
| 14 | scope／manifest／owner／generation改動 | stale拒絕；AC06 |
| 15 | ENOSPC／sync failure／decoder timeout／chooser缺證據 | 第一失敗保留、不重送；AC04/05 |
| 16 | 歷史239／109／329／65與跨新task | 零重下載、排除不操作；AC07 |
| 17 | #50恢復後#51～100完成 | 100/100，前50增量0；AC01/03 |
| 18 | 壞JSON／duplicate keys／未知schema／checksum／symlink／traversal／orphan temp | 零GUI／零覆寫，按§7區分canonical有效與損壞；AC05/07 |
| 19 | 重複inspect／reconcile、讀期間generation變化 | 零mutation；變化報不穩定；AC01 |
| 20 | 全流程禁止範圍／歷史baseline | protected bytes不變；AC07 |

實作後驗證命令：`python3 -B -m unittest discover -s tests -p 'test_agent_resume.py'`；`node --test tests/test_agent_resume_cua.mjs`。目前檔案／測試尚未建立，不宣稱執行。

macOS編譯原樣decoder，至少正常、截斷、post-decode變動及錯誤目的地負例；記source／binary hashes。stub不是ImageIO PASS，kill -9不是實體掉電PASS。不為本功能反覆重跑無關全repo suites；舊Rev28 CI依原required checks跑。

### 10.1 最小獨立真實Mac E2E

G0～G3成立後，由Owner另啟全新獨立DeepSeek V4.1 Flash1017／ollama_cloud Session；實作者不可自填獨立判定。只交原目標、AC、精確來源／runtime／root／目標授權、隔離evidence位置及stop規則，不交實作者完整推理。

新F/G均未備份、manifest及65 exclusion已核對。保存protected baseline；第一Session完成F一次Save All／chooser、全檔SHA／ImageIO、durable readback。正常close後Owner自行重開Mac。新Session只靠task ID／固定store恢復，唯讀核對F，F增量0；新前景交接後fresh定位G並各一次操作、完整verify。保留返回列表及至少一次有界真實scroll前後AX／OCR／畫面變化；跨重啟不要求相同PID／window連續，分別綁各Session，禁止假造跨boot連續性。

不刻意中斷新相簿partial下載，不重跑舊329／239／109／65湊數。無eligible新目標就NO_ELIGIBLE_TARGET。此功能驗收AGENT_RESUMABLE_BACKUP，不升格正式TWO_ALBUM_AUTO。

## 11. 階段、角色、Gate與失敗處理

本功能後續風險CRITICAL（重送／照片污染）；依Owner本次明確決定，Plan Review為OWNER_WAIVED，必要實作後Code Review及獨立Acceptance保留。本輪只是文件，不把豁免改寫成Harness內建Gate PASS。Harness resources不在root對應路徑，無本task stage packet／emitted validation commands；不修改Harness、不借歷史task製造admission／format3驗證收據。

| 階段 | 執行者與出口 |
|---|---|
| D0文件交付 | Sol保存本版、Luna唯讀梳理並擬詳細commit；root逐檔commit/push／更新Draft PR |
| G0 Plan交接 | OWNER_WAIVED；設計層audit依§4.3由Planner覆核PASS，非獨立批准；核對本版SHA後可M0，不等待外部Plan Review |
| M0最短接線 | 指定Implementor，fake app、原樣工具來源、spawn／stdio／長鎖／host身分／EOF／sync能力；零LINE app取得／capture／input。失敗即停，不造新bridge |
| M1核心 | 同一Implementor，store／history／同一verifier／wrapper及TC01～20；先薄切片再完整100本，不先建旁支框架 |
| M2交付 | root整合最小diff、本地證據、feature與CI兩個精確HEAD／Draft PR；不當功能PASS |
| G1 Code Review | 外部Chief真實APPROVE_IMPLEMENTATION，源碼／負例／scope完整；不以本機自評代替 |
| G2離線／G3遠端CI | TC及ImageIO實證、feature CI與legacy CI各自精確HEAD；缺一保留未完成 |
| G4獨立Mac | Owner啟新DeepSeek Session，兩本＋reboot＋no-replay，FAIL/BLOCKED否決 |
| G5結案 | 全AC、保護、不重送、必要review／checks成立，才AGENT_BACKUP_RESUME_P0=PASS |

Implementor依當前AGENTS預設GPT-6 luna／high，由Sol明確派包；若Owner另明確指定實作模型，記錄決策及真實Session再執行，不沿用舊文件私自改角色。DeepSeek1017為獨立E2E指定者。本輪提交訊息子代理GPT-6 luna只讀，不是產品writer／review批准。後續產品工作包 `max_parallel_read_only_helpers=0, max_parallel_writers=0`；需delegation先按既有Harness合法分配，不嵌套。

Gate PASS須實際證據。Owner前景／reboot觀察記OBSERVED，不替代工具驗證。未讀私有內容標operator-reported。僅貼審查請求不代表已送達外部模型。

同根因至多三次有證據attempt，連續兩次無新資訊或material blocker提前停。保全最小重現／原錯誤／未完成AC／每次學到什麼；寫task issues/ISSUE-<UTC>-<slug>.md，交Owner轉高階模型，送達前PENDING_OWNER_FORWARD。不得換Session重算預算、降AC、放寬guard。rollback只停用新程式，保留store／intent／照片，不還原舊checkpoint。

## 12. Git／PR交付、報告與保護

本文件更新既有乾淨 `docs/agent-resume-handoff-20261022`／PR30；其parent為master64515eb，只有plan／handoff，不混原dirty樹。先驗遠端未前進再提交，不amend／force-push。原repo副本只在確認舊bytes與文件分支相同後同步，保留其他dirty、原HEAD／index與protected hashes。

未來feature自當時最新master建乾淨外部worktree，逐檔帶入本版文件／必要原樣工具；記base SHA與文件commit，不以PR31為base。CI sibling分支自1b9a010建，PR target v43-ab/codex-rev28，只審§5.3修復，不自動merge或改原分支。兩包可序列做，避免多writer。不得把兩支一起merge master。

有實際成果就逐檔stage、commit body填「意圖／做了什麼／驗證與結果／下一步的建議」、push並更新同scope Draft PR。讀回真正commit body、遠端HEAD／PR head與檔案；不只貼PR摘要。不提交照片、群組／人名、原圖檔名、raw OCR／AX／截圖、grant／憑證或個人絕對路徑。

本輪完整規劃／審查報告即本Plan；文件檢查紀錄寫handoff末段，不另造E2E成功報告。未來實測更新task現有E2E測試報告.md，含順序、環境、命令／片段、expected／actual、狀態前後、副作用、attempt／資訊增益、未知／stop、證據相對與私有絕對定位／bytes／SHA。公開版遮蔽，私有raw留本機。progress只短記，不複製多份長文。

## 13. 03_handoff_prompt.md的適用方式

已讀Owner指定 `~/.codex/prompts/v4.8.0/03_handoff_prompt.md`；SHA `e27860d1da047ec1d9ece6440d9ec3f19014b0cefbb2e7b6ff00f8d564ebde37`。它是Optional Handoff Reviewer，只有workflow_policy.handoff_review_required=true才執行；不能重寫／擴scope／執行implementation，只核對已審Plan與compiled handoff，使用stage packet emitted CONTRACT／RESULT命令。

本task無controller stage packet、未有已審frozen contract、未發出fixed validator命令，因此交付的是Owner要求的Markdown advisory handoff。它必須逐項與本Plan相同，不能宣稱deterministic compilation／optional reviewer PASS／format3 schema validation／controller admission。取得真實packet後才依其命令，不自行拼validator或建立假的handoff.json。不因這個缺口新增Harness研發。

## 14. 固定結論與下一個可驗收動作

本版最小設計已由Planner按§4.3覆核，Owner明確免除獨立Plan Review；runtime feasibility與實作／驗收尚未發生。沒有未決產品選擇要重問Owner；live仍缺新F/G身分、當次授權／前景及reboot時點。先查已有私有資料，缺少只阻擋相依live。

```text
TASK_ID=AGENT-RESUME-P0-20261022
PLAN_REVISION=v2.1
PRD_VERSION=v1.0
OVERENGINEERING_AUDIT=PASS
OVERENGINEERING_AUDIT_SCOPE=PLAN_V2_1_MINIMAL_DESIGN
OVERENGINEERING_AUDIT_ROLE=PLANNER_NOT_INDEPENDENT
PR31_SOURCE_OVERENGINEERING_AUDIT=NEEDS_SIMPLIFICATION
MINIMAL_IMPLEMENTATION_PLAN=READY
DESIGN_DECISION=MINIMAL_A_SINGLE_CHECKPOINT_EXISTING_TOOLS
PARTIAL_DOWNLOAD_POLICY=BLOCK_AND_PRESERVE_WHOLE_TASK
EXTERNAL_PLAN_REVIEW=OWNER_WAIVED
EXTERNAL_CODE_REVIEW=NOT_RUN
ZERO_GUI_PREFLIGHT=NOT_RUN
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
FORMAL_AUTO_CODE_TOUCHED=NO_IN_FEATURE
HARNESS_TOUCHED=NO
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

下一步交接本版精確revision／SHA；受派Implementor完成環境對帳後直接M0，毋須獨立Plan審查。M0失敗保全第一阻塞並成單，不擴架構；產品交付後仍完成Code Review及獨立E2E。
