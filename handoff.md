# 給下一個 DeepSeek Implementor 的啟動 Prompt

```text
你是 s9008129/Line_backup 的 Implementor，指定模型 deepseek-v4.1-flash:1017、provider ollama_cloud。任務為 AGENT-RESUME-P0-20261022：沿用 PR #28 已成功的 Computer Use／AX／Vision OCR／Save All／Chooser／ImageIO，實作跨 Codex Session、斷線與 Mac 重啟的批次接續。核心案例是 100 本在 #50 中斷；絕不重下載完成相簿，任何既有 intent 或未知 Save All 結果不得重送。

完整讀取本文件和 plan.md v1.1，先核對 plan.md SHA-256 為 8ff887a153e5a363979bbd3e622dc998db4ae9e4f705ef45a5a4ba975c5f646b。記錄實際模型、provider、Session、repo／worktree／branch／base commit與dirty狀態；模型或來源不符、無法取用指定模型時先報問題，不暗中替換或冒稱符合。

Owner已明確免除本次外部獨立審查，可以直接依凍結計畫開始離線實作；記為OWNER_WAIVED，不能生成review PASS。不要等待舊版Luna實作或外部Plan/Handoff核准。實機測試未豁免、GUI前景與新相簿下載授權未自動成立。你不能自填獨立E2E PASS；獨立實機驗收由Owner在離線交付後另啟全新DeepSeek Session。

只在本次文件交付commit的乾淨外部worktree實作，交付分支為docs/agent-resume-handoff-20261022，parent為64515eb56b04accc40ade9e2db2fe0ad18c1ced3。解析並記錄實際交付SHA，不直接拿原v43-ab/codex-rev28當產品base，不整支合併PR28，不reset／clean／stash或更改原dirty工作樹分支。只改plan第4節允許路徑。

優先核對並原樣納入兩個既有Swift來源：ImageIO SHA 238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b；本機未tracked OCR SHA 19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861。缺少或hash不符，不重寫替代引擎，先提報。

先以零LINE GUI input證明CUA模組載入、Python長生命週期controller、真實程序身分與全域session flock可用，再實作固定私有root的單一原子checkpoint、凍結ordered manifest、邏輯append-only events、generation／checksum、只讀history import／inspect／reconcile及薄型CUA包裝。固定root是~/Library/Application Support/LineBackup/agent-resume；原圖不搬動，舊checkpoint不改寫，舊目的地以原測試包解析。

Save All真正click前必須durable intent成功並readback；同一原始執行在記憶體消耗一次資格後只呼叫一次app.click。loaded intent、重複request、工具timeout、回覆遺失、換Session／task／目的地均不重獲資格。Chooser確認也有獨立單次屏障。NOT_STARTED只能由有效完整歷史推導；空目錄或零計數不能證明intent後未派送。

#50完整80/80且來源綁定、hash、ImageIO、穩定性均通過，才在鎖內提交VERIFIED，下一次僅#51；32/80或UNKNOWN就BLOCK_AND_PRESERVE，#50～100零自動派送。inspect/reconcile純只讀、不建鎖檔、不改checkpoint、不操作GUI，先輸出建議；受控session重核generation與檔案後才提交。

禁止修改Coding Agent Harness、正式AUTO程式／State／Grant／Ledger／policy、舊adapter／two_album_entry、歷史checkpoint／照片；不以正式Authorizer或Issue25/27作必要依賴，不建排程、相簿內續傳、force/retry/reset或跳過partial功能。

依plan完成TC01～20、100本fixture、32/80保留、80/80補提交後僅#51、重複request零click、雙Session／跨task鎖與storage fault tests；macOS用真實ImageIO，stub與kill -9不得冒稱真實LINE或實體掉電PASS。先交付離線程式與證據，不自行操作LINE或重開Mac。

實作中任何無法解決的問題，必須立即保全證據、停止依賴該前提的操作，寫harness-development/agent-resume-20261022/issues/ISSUE-<UTC>-<slug>.md，附精確commit／plan SHA、受影響AC/TC、最小重現、原始錯誤、expected/actual、每次嘗試及新資訊、GUI派送／UNKNOWN、狀態差異、證據SHA、已知/推論/未知，以及高階模型需裁決的精確問題。交由Owner轉GPT-6.1-SOL/xhigh或Owner指定高階模型分析，送達前記PENDING_OWNER_FORWARD，不虛稱已分析。每根因最多三次有證據嘗試，連續兩次無新資訊或material blocker即提前提報；不得換Session重置計數、改AC、放寬guard或假造PASS。

逐項回報AC完成/未完成/BLOCKED，分開實作、離線測試、真ImageIO、真GUI與獨立驗收。更新本task的progress.md與完整E2E測試報告.md。按既有Git授權逐檔add/commit/push並建立或更新同範圍Draft PR；commit body必有意圖、做了什麼、驗證與結果、下一步的建議。不merge、不amend/force-push。完成交付不等於AGENT_BACKUP_RESUME_P0=PASS。

開始先用白話告知接手目標、保留成果與第一個零GUI檢查，接著執行環境對帳與有界離線實作。不要先要求Owner開LINE，也不要為重複確認已授權的離線範圍而停下。
```

# LINE Agent 恢復功能：實作交接文件

## 1. 文件身分、優先序與保存的歷史

- Task：`AGENT-RESUME-P0-20261022`。
- Handoff revision：v1.1／2026-10-22，對應`plan.md` v1.1。
- Plan SHA-256：`8ff887a153e5a363979bbd3e622dc998db4ae9e4f705ef45a5a4ba975c5f646b`。
- 產品目標：PRD v1.0的方案A／人啟動Agent後自主備份與恢復，非無人值守排程。
- 本輪只交付文件，產品程式、故障注入、GUI及E2E都未執行。不要把文件完整解讀成產品完成。

有效指令順序：Owner本對話最新指令→plan v1.1→本handoff的執行細節。PRD其餘要求保留；舊handoff要求的原相簿／舊位置／舊模型與外部review等待，不適用本工作包。若兩份新文件在功能、scope或AC上衝突，不自行挑較寬鬆版本，提報差異。

根目錄舊handoff沒有未提交修改，已由Git保存：原工作分支`72dae704...:handoff.md`，blob `84c8d43d757ab6659027e79fcb0258f4d7385959`，舊bytes SHA `b5c7b92ce1bd694b1bdebef29ec61c71e0004b4e1ec602ee9211d912cd4b19e5`。乾淨master基線的舊handoff另存於`64515eb...:handoff.md`，blob `e77cd3eacdc31d8478fcbb31c4b7d238e8f39ba7`。更新入口不刪除任何Git歷史／交易證據，也不恢復舊的authority。

本文件將公開交付，不包含人名、群組原文、原圖檔名、原始OCR／AX或個人絕對路徑。下列`~`路徑供同一台Owner Mac使用；其他機器缺少資料時不做廣泛搜尋或假造來源。

## 2. Owner已確定的決策與仍未授權的動作

| 項目 | 有效決策 |
|---|---|
| 實作者 | DeepSeek `deepseek-v4.1-flash:1017 / ollama_cloud`；真實執行身分須記錄 |
| 外部審查 | 本工作包OWNER_WAIVED，不阻擋離線實作；不是任何review批准／工具Gate PASS |
| 新資料位置 | `~/Library/Application Support/LineBackup/agent-resume/`；本輪沒有建立runtime store |
| 歷史資料 | 原處只讀；239正式、109 manual、329五本、65排除均不得重下載／覆寫 |
| 驗收 | 100本離線；兩本新相簿真實E2E，中間由Owner重開Mac |
| partial／unknown | 停全任務、保留照片；不自動重送或跳過至後續 |
| 未解問題 | 必須書面提報高階模型，不只聊天、不無限同樣重試 |
| Git | 逐檔add／commit／push與同範圍Draft PR；禁止擅自merge／改寫歷史 |

本輪授權文件與Git交付；下一Session依此接手的是離線Implementation。LINE GUI仍須Owner當次有效前景交接，新相簿須具體可核對授權。Mac重啟由Owner當次確認並執行，不使用reboot命令。Agent不得以舊前景、舊grant或本handoff取代這些條件。

## 3. 精確Git與環境接手步驟

### 3.1 位置與基線

| 符號 | Mac預期位置／值 |
|---|---|
| 原資料／證據工作樹 | `~/Documents/ChatGPT/Line_backup`（Owner本次選定專案） |
| 本次乾淨文件worktree | `~/Documents/ChatGPT/Line_backup_agent_resume_handoff_20261022` |
| 文件分支 | `docs/agent-resume-handoff-20261022` |
| 建議新產品worktree | `~/Documents/ChatGPT/Line_backup_agent_resume_implement_20261022` |
| 建議產品分支 | `feature/agent-backup-resume` |
| Remote | `https://github.com/s9008129/Line_backup.git` |
| 原工具來源HEAD | `72dae704a9a5f3dbdee21e33178201350b6e7a06` |
| 文件分支parent | `64515eb56b04accc40ade9e2db2fe0ad18c1ced3` |
| 實作base | 包含本plan／handoff的文件交付commit，接手時解析並記錄精確SHA |

不要把原工具來源HEAD、文件base與實作commit混稱同一版本。不要直接以本機`master`命名推定SHA；本機master先前與origin/master不同。文件自含其commit SHA會產生自引用，因此用固定branch＋plan bytes digest綁定交付；以Git讀回真正commit並記入新task報告。

### 3.2 開始順序

1. 讀取當前root／remote／branch／HEAD／status／staged paths。確認選定路徑屬同一repo，沒有不明的scope內變更。
2. 取得文件分支的實際commit，確認root plan digest符合本文件。沒有符合的plan就停止，不能只相信分支名稱。
3. 新建外部產品worktree自該交付commit；若已有分支／目錄，先查狀態及獨有commit，不覆蓋或刪除。
4. 只讀原工作樹的私有來源；產品編輯只在新worktree。原工作樹有19項既存tracked修改與大量untracked資料，不清理、不一併stage、不切換其branch。
5. 記錄Python、Node、Swift、macOS版本及實際模型／Session。規劃時Python3.9.6，新增程式要相容3.9；不是要求安裝新框架。
6. 新task進度／測試證據固定置於`harness-development/agent-resume-20261022/`，private先加入精確ignore再寫。不要把task證據放全域`.codex`。
7. 本次文件副本也會同步到原選定專案的root，方便Owner開啟；原分支中的這兩份副本不等於該分支已取得文件commit。以乾淨文件分支的commit／bytes為交付依據，不把原工作樹其他dirty內容帶入新分支。

## 4. 最短必讀順序與取證表

1. `plan.md`，完整讀取，尤其§0／§4／§5～10。
2. 本handoff的開頭Prompt、取證與問題提報規則。
3. `~/Downloads/LINE_backup_PRD_Agent_Interrupted_Resume_v1.0_20261022.md`，SHA `0d69c560490504f1b2af5466db680768e27924c4416c879d8c0545f1224a75d5`。若檔案不可得，不能聲稱已完整讀PRD；本計畫仍可供有界環境檢查，需求疑義提報。
4. [PR28固定HEAD報告](https://github.com/s9008129/Line_backup/blob/72dae704a9a5f3dbdee21e33178201350b6e7a06/harness-development/line-five-album-manual-20261022/E2E測試報告.md)、`public/evidence-index.json`與[舊review](https://github.com/s9008129/Line_backup/pull/28#pullrequestreview-5608322661)。
5. 只讀下表原Mac來源。不必先重跑整個repo測試／正式AUTO。

| 來源 | 取用與限制 |
|---|---|
| 原repo `src/line_backup_batch/image_decode.swift` | tracked於72dae704；SHA `238e97415d84cdc9c426ef7d0b1f52f4786329b06d91616ad10b5a2bbb44ff8b`；複製原bytes到新scripts/agent_resume，原檔不改 |
| 原repo `harness-development/catalog-diagnostic-20261010/modern_ocr.swift` | 本機未tracked；SHA `19f6787f4523332b5eb8a4235c4461fee5e49314c615b4865cc9ec848f2a2861`；GitHub主線／HEAD不保證有此檔 |
| 原repo PR28 `private/checkpoints.json` | 相對測試包`harness-development/line-five-album-manual-20261022/`；SHA `69d385ac9ccf3f5ba139ca45b6d0412c17499ce9e3e6c44eb50b62cb786f548e`；只讀，不升級原檔 |
| 原repo `state/backup_state.json` | 規劃時SHA `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`；239張參照，只讀 |
| 原repo `state/manual_archives.json` | 規劃時SHA `efe572afc9da1ae2123b3016430370f9ecd84ffb259f3bf73b0e5d26cd667bc5`；109張manifest／verification參照，只讀 |
| 原repo `policies/line-two-album-pilot-v1.json` | 歷史保護hash `59d94b72f4fd59d829b56d21a494c9d83c6b91eb2513c15795a58021194a39e9`；不作新方案grant、不修改 |

來源若在規劃後合理新增資料，不能用舊hash強行回退。保留新舊diff，判斷影響；無法證明映射與屏障完整就提報／停相依動作。已發布hash只是基線，不能當未讀來源的驗證替身。

PR28相簿結果是歷史manual-diagnostic：A45前Session已Save All、本次零新派送；B78／C77／D42／E87各報一次，共新增284，五本329。規劃本輪只查checkpoint結構、目錄存在及檔數，沒有重做329張ImageIO／照片hash驗收。舊public review核對公開manifest／index，不是外部重解碼私有照片。

私有checkpoint目的地`private/downloads/...`必須相對原測試包解析；相對repo cwd解析會誤報不存在。它的FILES_VERIFIED字串不證明durable intent、原子寫入或新功能READY。

## 5. 不可變工作契約與實作里程碑

### 5.1 凍結內容

權威scope／AC／狀態機／CLI／測試完整定義在plan，handoff不得擴張。產品允許修改檔案與test evidence位置以plan§4為準；只有該列表內的根目錄文件可以為必要交付澄清更新，不能自行降低AC／requiredness。

禁止改Harness／controller／schema、正式AUTO package、State／Grant／Ledger／policy、原adapter／two_album_entry、歷史checkpoint／照片。新sidecar不能import正式交易package，不能繞過仍有效的guard。舊max_albums_per_run=1不適用新獨立manifest的批次控制，也不得修改原config來擴大它。

實作模型是DeepSeek，不承接舊「Luna產品實作」角色。這一輪Luna只做已獲Owner授權的read-only上下文／commit message工作，不是獨立審查、E2E或產品writer。後續預設不派子代理；不以另一模型／新Session重置失敗預算。

### 5.2 M1：先驗證接線，零GUI

- 先編譯原樣Swift工具至隔離build目錄，保留source／binary hashes；新binary不必等於歷史binary，但必須如實重新綁定。
- 用fake app驗CUA模組載入及callback，實際Python controller持全域flock，零LINE input。
- 確認controller長活、GUI host程序身分可核對、transport斷線與helper死亡行為可測，不假稱平台隔離。
- 能力不成立時寫具體問題單，不先花大量程式做依賴未證實能力的完整GUI整合。

### 5.3 M2：持久化／只讀恢復

- 固定root單一checkpoint，同revision含manifest／狀態／events／ownership；events只追加。
- atomic write＋fsync／F_FULLFSYNC＋replace＋dir sync＋readback；unknown commit不發dispatch資格。
- schema／checksum／generation／identity／路徑不合法則BLOCK；不從較舊snapshot自動恢復許可。
- history import只建立只讀參照；五本用public identity與private證據交叉，65 exclusion需完整身分，不以張數猜。
- inspect／reconcile不寫store、不建lock、不操作GUI；session持鎖後重核，才提交promotion／SKIP。

### 5.4 M3：薄型GUI包裝與驗證

- 保存PR28metadata／detail／實際menu OCR流程，不引入新定位框架或硬編碼舊座標。
- wrapper自己單次app.click；intent成功前不得click，重複request與回覆遺失不重發資格。
- chooser最終確認有獨立intent及單次呼叫；新Session不接續舊chooser。
- 新下載目錄必須獨立空白；逐檔hash、穩定取樣、ImageIO full RGB、post-decode核對與durable readback才VERIFIED。
- image同內容hash合法，不得把舊報告的329 distinct digests擴大成產品唯一性要求。

### 5.5 M4：離線交付與獨立實機交接

按plan§10跑局部必要測試。每個里程碑更新報告，AC逐項列完成／未完成／BLOCKED。程式與測試提交後交Owner，不由實作者自填獨立E2E。真正live僅使用兩本未備份新相簿，Mac重啟由Owner實行；329／239／109／65均不重跑。

## 6. 恢復決策表：實作者不可重新詮釋

| 觀察 | 必須行為 |
|---|---|
| #1～49完成且重核有效，#50有效歷史中無intent | fresh定位#50；#1～49零新dispatch |
| #50 durable intent後crash，目錄為空 | UNKNOWN，停止；不把0檔／0count當未派送證據 |
| #50 32／80 | BLOCKED_PARTIAL，保留32張與證據；#50～100零自動派送 |
| #50 80／80、來源綁定及全檔驗證都成立 | session鎖內重核generation／檔案並提交VERIFIED；下一本#51 |
| #50滿額但缺身分／目的地來源關聯 | AMBIGUOUS；不能靠80張推定來源 |
| 已VERIFIED但現少檔／hash變／壞檔 | BLOCKED；不得自動補下載 |
| 舊GUI host仍活／狀態不明 | 不接管，不TTL／kill／unlink；告知安全停止舊Session之必要動作 |
| store壞／未知version／digest不符／孤立tmp | BLOCKED_STORAGE_INTEGRITY，不init／downgrade／擦掉障礙 |
| 找不到新相簿或65 exclusion身分不足 | 保留無關離線進度，停止live，提報缺的精確資料 |

## 7. 問題提報與高階模型分析：強制契約

### 7.1 何時必須提報

無法解決、當前工具能力不足、scope外改動才可能解、架構／資料／AC／授權邊界不明、來源hash或證據互相矛盾、持久化結果不明、疑似副作用、未知Save All、兩次同根因無新資訊，均不能只在聊天說「卡住」。material blocker立即提報，不必湊滿次數。最多三次有證據嘗試；禁止新Session／換模型重算。

### 7.2 檔案與可直接使用的格式

建立`harness-development/agent-resume-20261022/issues/ISSUE-<UTC>-<slug>.md`。公開版遮蔽原圖名、群組／人名、敏感授權與個人絕對路徑；原始證據留private。報告需含：

```text
# 問題提報：<具體、可觀測的問題>
TASK_ID=AGENT-RESUME-P0-20261022
PLAN_REVISION=v1.1
PLAN_SHA256=<實讀>
IMPLEMENTATION_COMMIT=<精確HEAD及dirty diff識別>
EXECUTOR_MODEL=<真實模型/provider/session；不可得寫unknown>
ISSUE_STATUS=BLOCKED
HIGH_MODEL_HANDOFF=PENDING_OWNER_FORWARD

## 意圖與受影響AC／TC
<正要達到什麼、何項未完成、其餘已證明結果>
## 環境與最小重現
<OS／runtime／worktree／命令／輸入；只列必要片段>
## Expected / Actual / First Failure
<原始錯誤、exit code、第一拒絕，不用二手摘要替代>
## 事實／推論／未知
<逐類清楚分開；列派送實際次數或UNKNOWN>
## 嘗試歷史與資訊增益
<每次方法、結果、證據SHA、新學到什麼；保留全部失敗>
## 狀態／副作用／保全
<前後generation／digest／照片是否不變；已停止的相依操作>
## 證據索引
<repo-relative、安全公開識別、private本機定位與SHA；不公開原敏感值>
## 已排除方案與安全可繼續工作
<不能force／重送／改guard的原因；不影響阻塞前提之離線工作>
## 請高階模型裁決的精確問題
<一個明確決策、候選做法／代價／已知限制，不只寫請幫我看看>
## 下一步與停止條件
<等待何種分析／Owner資料；再次失敗時如何停止>
```

將問題單commit／push至同scope Draft PR（private raw不stage），在回報提供完整報告連結與精確版本，交Owner轉高階模型分析。指定GPT-6.1-SOL／xhigh，或Owner明確改指定的高階模型。沒有實際送達管道就如實記PENDING_OWNER_FORWARD；不得自己虛構分析結果或啟動未授權外部模型服務。此高階診斷不是恢復被免除的例行外部審查關卡。

取得分析後記錄真實來源／日期／結論／scope影響。可在原plan內解決的有界修復接續原授權；要改目標、AC、架構或資料／授權邊界，先提出精確差異交Owner決策，不擅自改掉阻塞。

## 8. 驗收、報告與狀態分層

離線必須分別有：100本恢復、intent前後crash、GUI／chooser邊界回覆遺失、32／80、80／80、storage各提交點、stale generation、雙task／雙Session、identity collision、symlink／traversal、重複reconcile零mutation、protected hashes。fixture必須執行新產品模組，而不是另寫一份測試替身通過。

測試入口是未來待建立的測試，文件交付時尚不存在／未執行：

```text
python3 -m unittest discover -s tests -p 'test_agent_resume.py'
node --test tests/test_agent_resume_cua.mjs
```

真ImageIO須有macOS編譯及decoder輸出；Linux stub不是ImageIO PASS。kill -9只代表程序crash注入；Owner實機重啟另列。CLI邏輯PASS、ImageIO PASS、真GUI PASS、真Save All、逐檔驗證與獨立E2E判定不可混用。

正式報告：`harness-development/agent-resume-20261022/E2E測試報告.md`，持續保留步驟順序、工具／命令／關鍵片段、環境／資料、expected／actual、PASS／FAIL／BLOCKED／NOT_RUN、狀態前後、side effects、嘗試與資訊增益、停止原因、證據定位及SHA。進度用同task的progress.md簡短更新，不能以大量文件／重複synthetic測試代替實際進展。

六狀態分開回報。交接當下：

```text
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=NOT_RUN
CORE_ACCEPTANCE_STATUS=NOT_RUN
REQUIRED_VERIFICATION_STATUS=NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
EXTERNAL_REVIEW_STATUS=OWNER_WAIVED_FOR_THIS_WORK_PACKAGE
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
HIGH_MODEL_ANALYSIS_STATUS=NOT_REQUESTED_NO_IMPLEMENTATION_ATTEMPT_YET
```

獨立live E2E由Owner另啟、未參與產品修改的DeepSeek Session，提供原始目標、固定AC、精確commit／來源與資料位置、隔離證據輸出及停止條件；不傳實作者完整推理或預設PASS。該Session不得改產品／AC／grant／ledger／歷史資料。FAIL／BLOCKED保留否決權；修復後新版本需必要重驗。

## 9. Git交付與不污染原工作樹

- 本次docs分支只包含plan.md／handoff.md；不要把原dirty工作樹stage。產品修正後只逐檔stage本工作包路徑，private照片／證據／授權不得加入。
- commit訊息用準確subject，body必有「意圖／做了什麼／驗證與結果／下一步的建議」，寫真正跑過的測試，不將未跑寫PASS。
- 每次有意義的階段完成或BLOCKED停止做checkpoint commit檢查；有實際成果就保存，沒必要變更不造empty commit。
- push後核對遠端HEAD及真正commit body，提供PR與完整報告連結；不只在PR描述補三要素。
- 使用乾淨同scope Draft PR，不重開／合併原1,887檔PR28；不merge、不amend、force-push或順手清repo。
- 若push／PR失敗，保留commit與錯誤，回報COMMIT_OR_PUSH_BLOCKED，不冒稱已發布。

## 10. Harness prompt的實際適用性

Owner指定`03_handoff_prompt.md`的內容為v4.8 Optional Handoff Reviewer：只在workflow要求時核對Plan／Handoff契約，不擴路徑／gates、不執行Implementation，使用stage packet發出的固定CONTRACT／RESULT命令。

本task沒有已發出的controller stage packet、frozen plan-contract.json或該task固定validator命令；因此不虛構handoff.json、compiler PASS、format3 schema validation或角色admission，也不借用歷史其他task的命令。這份Markdown是Owner要求的advisory實作交接；不修改Harness，不以缺少正式AUTO authorizer／grant／ledger阻擋方案A。

## 11. 第一個具體next_action

接手DeepSeek先核對plan SHA／文件交付commit、建立乾淨產品worktree、核對原樣Swift來源，做零GUI runtime／lock preflight。成功後連續完成有界離線實作與TC矩陣；第一個無法解決問題立即按§7成單交高階模型。現在不需要LINE前景，也不執行任何Save All。
