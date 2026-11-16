# 記事本工具列阻塞：根因裁決與修復交付

日期：2026-11-16；分析基準 `dfaf99bb009dadd5c3f463535af6e6aa4b72a78f`。本文件為同一開發任務的分析與交付，不是獨立接受。

## 一頁式根因結論

**直接失敗點是控制發現／可操作性 gate，並非 LINE 下載失敗。** 提報時五個媒體沒有 intent；chooser、outcome、download-check 均未到達。C 有工具列正面可見證據，之後才消失；D 四項只證明保存的 after 畫面未見工具列，不能推論整段時間都沒有出現。

**可修的根因是 Skill 未把正面可操作證據接成交易窗口，且 transient／一次未顯示後沒有安全、有限的接續。** Agent 的再次觀察是 C 的近因；非原子擷取與 LINE 短暫狀態放大這個缺口。LINE auto-hide 的實際因果、D 的 reveal 是否無效仍未知。未證實的 CUA 或 LINE 程式缺陷不當成已知 bug。

**`dfaf99b` 是新硬停規則的主要回歸候選，不是整起事故的唯一主要根因。** 它的 parent `d655025` 在 13:38 已記錄 C／D 控制發現阻塞，早於 14:26 的提交；parent 也已禁止 body／右鍵探索。`dfaf99b` 增加安全候選，同時加入單次及 transient 硬停，能解釋這次為何無法接續，不能解釋首次為何看不到控制。最強替代解釋是既有操作允許集合與 CUA 可用能力不匹配，加上 Agent／capture 延遲漏過短暫可見狀態。

**最小修復保留 intent 與一次下載限制。** 先完成可預備工作；正面可見後接續 intent，讀回後仍重新定位；消失發生在 intent 前，才可按持久額度和新證據考慮一次 re-arm。intent 後消失不能 re-arm、新建 attempt 或推定 NOT_SENT。D 若仍沒有安全控制，保留具體阻塞。

## 證據推理

### 事實與推論的界線

| 命題 | 分類 | 證據／限制 |
|---|---|---|
| 報告時 4 篇、3 COMPLETED、5 PENDING、0 UNKNOWN，無未決 attempt／restart | FACT（提報時觀測） | `問題提報單.md` §1.2、§7.1；本次不藉測試刷新或改寫帳本 |
| C 工具列在 16:11:30.030 可見，16:11:46.679 不見 | FACT | 提報單 §3.2；截圖 SHA-256 分別 `9ff059ec68c441c06cf99fb4c38b8aa0292212f74d04cfa647f44f2091055337`、`2086ace45dc84ed613152ad8953254f96f95c20997f160d850272cf02772fd0b` |
| 這證明 LINE 有精確 16 秒 timeout | UNKNOWN | 兩次觀察只形成區間，沒有連續畫面或隔離變項 |
| C 的間隔是固定 sleep | 不成立於目前抽樣 | Tester 核對 `call_4ju2i55x`（reveal 與 after 同 call）、`call_6tkp8lrb`（看圖）、`call_bj47cd3k`（再 capture）；16:11:40.564 的 reasoning 選擇 persistent recheck 並明寫 No explicit delay；間隔 16.649 秒 |
| D 四項從來沒顯示工具列 | UNKNOWN | 提報單 §3.4 只有 after 畫面；不能排除取得畫面前已消失 |
| D 四項的 after 未見工具列 | FACT | `observations/post4-{1,2,3,5}of5-after-reveal-20261116-001/`；雜湊見提報單 §3.4 |
| 同時期 D 4/5 能完成 | FACT | 提報單 §3.1：15:17:06 可見，15:17:12 intent，15:18:45 下載；後有 outcome／基本檢查／completion。成功鏈缺少首次 reveal 完整輸入，不能反推固定方法 |
| raw undefined 是唯一根因 | 不支持 | 提報單 §2.1：11/02 成功同樣 undefined。當次保存缺口會放大不確定性，卻不等於 GUI 未執行 |
| notes CLI／ledger 擋住五項 | 不支持為主因 | gate 位於 intent 前；提報單 §7.1 的 event chain／integrity 通過不等於所有時點資格永遠有效，未來仍照普通 preflight |

C 最有力的近因是 Agent 選擇再做 stability 觀察，錯過已觀察到的窗口；原 Skill 沒要求等 16 秒，也沒清楚排除這次冗餘 capture。Skill 的 action-on-positive 留白是可修的系統性條件。不能說「重新觀察把工具列關掉」：擷取造成關閉、游標離開、toggle 或 LINE 自動隱藏均未分離。

D 必須先確認 viewer 類型、當前選取／索引、控制範圍與來源連續性，再核對工具能力及 capture 時序。不能先把歷史 secondary click／中央點擊恢復為通用手段；它們可能影響播放，歷史成功也沒有排除 context menu 或其他變項。

### Tester 新釐清的時序與獨立缺陷

Tester 對原始 session 的唯讀抽樣（來源 51,925,056 bytes，SHA-256 `8fc45d0a63b6ff4ab15d3d7f4fcdaebaafbe09794bfbfbf1e24834076671b9ad`）進一步支持下列判斷；私有釐清全文與來源定位保存在本任務目錄，不提交全域 session 或私人畫面。

| D 項目 | click call→capture call（host 起點間） | click call 結束→diagnostic created_at | 額外等待 |
|---|---:|---:|---|
| 1/5 | 3.697 秒 | 3.821 秒 | 無 sleep |
| 2/5 | 3.911 秒 | 5.414 秒 | capture code 有 1.2 秒 timer |
| 3/5 | 4.158 秒 | 5.652 秒 | capture code 有 1.2 秒 timer |
| 5/5 | 7.901 秒 | 7.989 秒 | 無 sleep |

以上不是 OS click 時刻或真正 UI 延遲。2/5、3/5 的 timer 是 Agent 當次選擇，Skill 沒要求；它擴大漏拍風險，但不能證明控制曾出現。C reveal 與 capture 已在同一個 call，亦不能據此宣稱 atomic。

返回錯值的來源已釐清：`call_dkaaobvp` 的 VIEWER request literal 直接填 `expected_return_role=LIST`，request SHA-256 `edd161252fee9fc1d50124d9bbdd0a16812678dd11aa005dbda0fe634a3c7642`；helper 原樣保存，無 default 或角色推導。Agent 後續 reasoning 自認應為 POST_DETAIL。故主要是 Agent 未遵循既有返回描述，另有缺少持久硬核對的防禦缺口，不是「wrapper 自動填錯」的已知缺陷。

D 四項回傳 `ready_for_bind=true, blockers=[]`，落地 diagnostic 卻是 `ready_for_bind=false`。repo 模板亦有同根因：初始化 metadata=false，只在最後更改回傳 output，未同步寫入 metadata。這是可直接驗證的證據保存缺陷；當次 Agent 看到 true，沒有證據顯示它造成五項停 intent，跨 Session 的實際影響未知。本次最小修正並測落地與回傳，保留 diagnostic 自身 persistence 失敗時的拒絕，不修寫舊檔。

錯名與業務身分也已分離：D 4/5 completion event `00000069.json` SHA-256 `7e2890dfbdac32c14c441a66becf2539a25af4edfcb075a3e83032e8704dc851` 仍綁正確 post/media，evidence-audit exit 0；錯誤在 label／provenance，不據此重下或改 completion。hover 的 NOT_AVAILABLE 目前只證明 Agent 如此宣告且未使用；未取得 API 能力清單或成功 hover receipt，真能力仍 UNKNOWN。

### 回歸檢驗

| 時點 | 規格／行為 | 可支持的裁決 |
|---|---|---|
| 11/02、11/11、11/12 | 曾有 secondary click 後工具列／下載成功 | 證明能力曾存在；不證明可安全泛用，也不是本次相同條件 A/B |
| 11/16 13:38 `d655025` | 先前事故已停控制就緒 gate | `dfaf99b` 不可能是首次阻塞的必要原因 |
| `dfaf99b^` B1 | 只允許移鼠或明確工具列控制，禁內容點擊 | 允許集合與缺少 hover 的矛盾早已存在 |
| 14:26 `dfaf99b` | 新增 filmstrip 安全邊緣候選及單次／transient 停止 | 一面擴大方法，一面使失去窗口後無接續；屬可修限制 |
| 15:17–15:18 D 4/5 | 在新提交後仍成功 | 排除新提交使所有下載鏈必定失效的假說 |
| 16:11 C、16:29–16:32 D | C 可見後未接交易；D after 未顯示 | 支持 action window、有限接續及捕捉證據修正；未建立唯一 GUI 因果 |

`b2cd3e1` 與 `92c1ca6` 不是本次單次／transient 規則來源，不能用它們替代精確 diff。真實同條件 A/B、LINE timeout／toggle／pointer-leave 因果測試均 `NOT_RUN`。

## 責任／修正層級

| 層級 | 責任與最小修改 | 優先度 |
|---|---|---|
| Skill／操作契約 | 明列狀態機、先準備再 reveal、正面可見直接接交易、有限 re-arm | P0 |
| Agent 決策 | 去除無新增 gate 價值的 stability capture；每步保留角色／身分與映射核對 | P0，由 Skill 引導，非增加 Owner 指令 |
| 證據契約 | list/post/media／viewer／n/N／entry anchor 核對表及硬拒絕；label 不能取代 keys | P0 |
| 返回契約 | expected_return_role 從進入來源建立；一次一層，未返回與 ENTRY_LOST 分開 | P0 |
| 本地證據保存 helper | 普通輸入頂層 undefined 沿用 typed 記法；nested 缺口仍不完整；修正落地 readiness 與回傳不一致 | P0 的小修；不代表 CUA 派送修復 |
| CUA primitive／捕捉 | 查 hover-only 真能力、分開 screenshot／AX 時間；證實不足才另改 wrapper | P1；真 GUI `NOT_RUN` |
| LINE 本身 | 原生 transient 行為待診斷；無證據不能宣告產品 bug 或修改 LINE | 未解條件 |
| notes CLI／ledger | 不改狀態、completion、MIME、歷史或下載次數 | 無本次修正證據 |

一般最佳實務支持「按條件檢查可操作性」及「副作用不明時不能盲重試」。[Playwright actionability](https://playwright.dev/docs/actionability) 只提供比對清單，並不讓 Mac CUA 具有 DOM hit-test 或 atomic 保證；[AWS retries](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) 說明 timeout 不排除副作用，因此不能把下載當作安全可重試 API。

## P0 修復步驟

1. 保留原事故證據與使用者 dirty 提報單；先做歷史／盤點／資格／返回錨點及呼叫參數準備，不在可見窗口中臨時建資料夾或整理長報告。
2. 由當次工具文件及畫面決定安全候選。hover 未知就記未知，不以 click 冒充；無安全區就停，不試播放或相簿方法。
3. `READY → REVEAL → TOOLBAR_VISIBLE → intent 持久讀回 → 當次重新定位 → 單次 DOWNLOAD_CONTROL → chooser`。此為 Agent 操作狀態，非新增 ledger state。正面證據充分就接續，無固定 stability 等待；沒有動畫結束／映射證據仍不輸入。
4. intent 前 `TOOLBAR_NOT_SHOWN`／`REVEAL_TRANSIENT` 先保留事實。只有同一三層身分、有效前景、無 intent／chooser／未解輸入且有相關新證據時，才可在初次加一次的總額內 re-arm。新觀察本身不是安全性或有效性的證明；reopen／Session／新任務目錄不能洗額度，額度未知就停。
5. intent 已寫入後消失或映射失效，保留原 attempt，停止輸入，依原 outcome／reconcile 路徑查證。禁止 re-arm、替代 intent、推定 NOT_SENT 或重下。
6. 在 statement 保存完整身分對帳與來源。衝突原件仍保存作診斷，但不得歸為合格 evidence。舊 post3-* 錯名只在新的關聯說明引用真實 post/media 與原 hash，不改原件／event／completion。
7. viewer 返回使用進入來源的 role／anchor；從 POST_DETAIL 進入就回 POST_DETAIL。若從已展開 LIST 卡片直接進入，才以當次來源證據預期 LIST。回一層成功後再決定下一步，不再把關閉詳細頁當作必回列表。

## 驗證計畫

### 本次離線開發驗證

helper 合成測試核對頂層 undefined、nested 缺口、request 讀回及一次呼叫；既有最小回歸與 `git diff --check` 的實際結果另列交付紀錄。測試前後核對永久紀錄／active locator 的檔案清單、bytes／hash。這是有限保護核對，不能證明照片區、OS 隔離或獨立接受。

### 最小真實 GUI E2E（本次 NOT_RUN）

使用手冊的記事本正式日常 Prompt 與有效前景，不能改用 Acceptance／E2E 角色 Prompt。重讀所有永久紀錄；只對當時仍合格、未派送的項目執行。若資格已變，記錄差異而非照本表強制下載。

| 個案 | 必要證據與通過條件 |
|---|---|
| C 唯一待處理項 | 當次 viewer／keys 對帳、第一次可見工具列→intent／重新定位→單次下載完整鏈；不得故意等 16 秒再聲稱通過 |
| D 1/5 | 本項獨立 before/input/after 時序、明確下載控制、自己 attempt 與 completion |
| D 2/5 | 同上；不得用 D 4/5 的成功畫面代替 |
| D 3/5 | 同上；若從未取得正面控制則具體 BLOCKED |
| D 5/5 | 同上；只靠 latest after 看不到控制不歸為下載失敗 |
| 既有完成項保護 | 原有三個 completion 不變；D 4/5 不新建 intent／下載，檔案完整性另依日常原規則 |
| 返回 | 每項 viewer→實際進入來源，必要時再回指定列表；保留 role 與 anchor；聊天則 ENTRY_LOST、有限恢復，不盲關第二層 |
| 接續 | 新 Session 只依正式 Prompt／Skill／永久記憶與持久 reveal 紀錄重建，重取當次座標；不依賴本次聊天補充指示 |

每一下載各保存 intent 讀回、新空白 staging、下載一次、chooser 最終確認一次、可歸屬 outcome、download-check 及 completion 讀回。五項若皆仍合格且全成功，原 3+5 才可投影為 8 COMPLETED；仍須分開全列表細盤／待解狀態，不只看計數。

有限 re-arm 的真實分支只在自然發生 transient／未顯示且符合新證據條件時執行；不能為了覆蓋分支而重下五項或已完成項。未觸發就 `NOT_RUN`，另在獲授權測試來源上驗證，不假造本次覆蓋。混合附件 chooser、跨 Session 真實恢復及來源 timeout 因果各自記錄，不能由五項成功外推全部 PASS。

## 風險與未解問題

- GUI 可見窗口與 intent 持久化之間沒有原子保證。先準備能減少延遲，不能保證控制在 intent 後還在；此時保護優先並保留原 attempt。
- re-arm 上限是安全設計選擇，非已量測的最佳成功率。沒有新資訊或額度來源不明就停；不因修了規格重置歷史計數。
- 只有 Agent 能交叉判讀截圖／viewer 與來源；本地 helper 能驗 bytes/context 及宣告的一致性，不能證明畫面真實或 enabled。硬 gate 不冒稱獨立 sensor。
- D 可能仍無可用安全 reveal；若是 CUA 缺能力，文檔與 typed raw 小修不會憑空新增 hover。需 P1 實測後才有進一步修改依據。
- 不以 LINE 全面故障、帳本壞掉、精確 16 秒 timeout、某種 click 穩定有效作前提。未測過模型／Session／viewer 不承諾普遍可靠。
- 無真實 GUI 授權，本次不讓 Tester 操作下載；若未來入口／前景失效而無法恢復，仍照日常停止條件處理。

## 交付紀錄

最終修改為六份記事本 Skill／references、一份現有 helper 測試及本計畫／報告；不改 `src/`、相簿 Skill、正式日常 Prompt、CLI 或事件格式。P0 已落地：action window、intent 前有限 re-arm、持久身分核對、返回角色、typed undefined 及 diagnostic readiness 保存一致性。GUI 能力與 LINE 因果的 P1 沒有假裝完成。

環境：Darwin 27.2.0 arm64、Python 3.9.6、Node v24.22.1、Git 2.52.0。

| 實際命令／核對 | 結果 | 任務內原始輸出 |
|---|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0；73 tests／320.309 秒，OK | `daily-tests.stdout`、`daily-tests.stderr` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0 | `notes-help.stdout`、`notes-help.stderr` |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'`（首輪） | exit 0；316 tests／43.887 秒，OK；新發現 diagnostic 修正前 | `notes-tests.stdout`、`notes-tests.stderr` |
| 同命令（最終 helper／測試定稿後） | exit 0；319 tests／40.930 秒，OK | `notes-final.stdout`、`notes-final.stderr` |
| Worker 2 的 `test_notes_input_helper.py -v` | helper 回報 exit 0；20 tests OK；非獨立接受 | `worker2-handoff.md`；主線最終全套包含此檔 |
| `git diff --check` | exit 0 | 提交前另核對 staged diff |
| 紀錄根目錄與兩個 active locator 的清單／bytes／SHA-256 | PASS；前後各 4,916 entries，changed=[] | `protected-before.json`、`protected-after.json`、`protected-comparison.json` |
| 原 dirty 提報單 hash | 仍為原始輸入 hash；不 stage | `issue-report-snapshot.md`（私有讀回副本） |

notes 全套中 argparse 的 INVALID_--SIGNALS stderr 來自既有負向案例；測試 runner 最終為 OK、exit 0，沒有將該字串當新業務拒絕或真實 CLI 任務重送。保護清單不含照片區／OS 狀態，不能外推為全系統完整性或獨立通過。

Tester 的完整釐清見 `tester-clarification.md`（SHA-256 `77bc1168596d7a04ff70fc962591b56abe48d86a92f624306b6b4fe32878386f`）；31 個原始 event 的私有抽樣 `tester-session-samples.json`（SHA-256 `6ebc51562983c3b6ef368ab47a0d70268975e348f9dccde4305706a9da85237a`）保留來源行號與逐行 hash。原 session 持續增長，前述整檔 hash 只綁分析當時的 snapshot，日後以已保存抽樣逐行核對，不能用 live 整檔 hash 不同判來源被改寫。

| 狀態 | 結果與範圍 |
|---|---|
| `PRIMARY_OUTCOME_STATUS` | `BLOCKED`：C／D 五項真實備份成效尚未驗證 |
| `IMPLEMENTATION_STATUS` | `PASS`：本次有界 P0 開發修改及離線測試已完成 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN`：未操作 LINE／未下載 |
| `REQUIRED_VERIFICATION_STATUS` | `PARTIAL`：開發回歸 PASS；C／D、返回、re-arm、跨 Session 真實 GUI／download-check 均 NOT_RUN |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN`：兩個 Worker／Luna 都是同任務 helper |
| `TASK_CLOSURE_STATUS` | `BLOCKED`：不宣稱五項已修復、列表已完成或整體 DONE |

模型證據分層：原 Herdr Workers 的 UI 顯示保留不變；Owner 指定的 GPT-6 Luna helper 以 native spawn 的 `model=gpt-6-luna` 參數派送。這是 request parameter 證據，不由此聲稱 provider backend、usage、成本或節省量。Git 交付以後續實際 commit／push 回讀為準，不以測試或 helper 報告冒充遠端發布。

原始分析輸入：根目錄使用者改寫 `問題提報單.md`，SHA-256 `84f64c4ea5a05b03b27f6d45613ad0cd55310e0d9b77dfc50de1387648fec382`（保留未提交）。私有任務證據：`.local/line-backup/tasks/20261116-toolbar-repair/`。公開文件不含私人標題、作者、媒體內容或原始檔名。
