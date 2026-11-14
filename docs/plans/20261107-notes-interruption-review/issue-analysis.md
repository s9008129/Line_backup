# 記事本中斷後無法接續：高階根因分析

## 結論與範圍

`ANALYSIS_COMPLETE`。現存證據不足以把第二支影片的 `UNKNOWN` 追加收斂為 `NOT_SENT`、`STOPPED` 或 `DOWNLOAD_FINISHED`；不應刪除原 outcome、重建空帳或再按下載控制。

選定根因識別為 `NOTES-INTERRUPTION-RECOVERY-GAP`：**在下載控制已呼叫、chooser 尚未確認期間失去 CUA 可觀察性後，流程只有抽象的停止證據要求，沒有經實證、可由下一個 Agent 執行的安全終結與接續方法。** 這是目前能確認的恢復規格／操作知識缺口。它解釋第二次任務為何再次停住；不能單憑它判定底層網路、LINE 或 CUA 哪一個元件首先故障。

唯一下一步建議為 `PLANNER_REPLAN`：以既有追加式交易為基礎，為這一個中斷分支制定有界恢復方案。以下設計是供該方案採納的診斷建議，不是已核准實作、可直接執行的真實資料修復或正式驗收。

本輪依 Owner 指定的 `06_high_reasoning_review_prompt.md` 進行診斷；該角色明定不得修改產品或執行建議。Owner 新補充希望設計接續機制，納入本報告；未自行切換為 Planner／Implementer。帳本、原始證據、照片／影片與產品程式均未修改，沒有操作 LINE 或追加任何事件。

## 候選與證據身分

- 專案：`Line_backup`；分支：`feature/line-notes-media`。
- 調查起始 HEAD：`8108397ddc754db1d78d035edede38a0b017425f`；起始 `git status --short` 空白。
- 環境實際輸出：macOS 27.2／26B123；`/usr/bin/python3` 為 3.9.6。
- Owner 提供的 2026-11-07 私有提報、2026-11-06 原任務、指定 intent／outcome 與保存 evidence 均在專案內；完整路徑、hash 與命令原件留在對應私有任務目錄，不上傳私人畫面、群組名稱、原始媒體檔名或帳本識別碼。
- 原 intent 的 capture receipt 記錄當時 `notes.py` SHA-256；本次另保存目前 source hash，兩者相符。這只核對該程式檔版本，不把目前 HEAD 當成前次整個 Session 的版本證明，也不把 receipt 當成 CUA 輸入證明。

## 最小異常時間線

| 時點／階段 | 已有證據 | 能支持的結論 |
|---|---|---|
| 2026-11-06 第一支影片 | 原任務進度與 completion 記錄下載、完整解碼與完成讀回 | 當時第一支已完成；本輪沒有重跑影片解碼 |
| 同日 16:24:36（台北） | 第二支 intent 的 capture child exit 0；新 staging 寫入事件 | 建立 attempt 與禁止重送保護；不是已派送證明 |
| 16:29:59 | 保存的 input receipt 記一次 viewer 下載控制呼叫、無例外；之後 AX／截圖出現儲存面板 | 工具呼叫有回應、App 進入 chooser 階段；不是下載完成 |
| 16:30:08–09 | Go to Folder 的 AX／截圖顯示前次路徑字串；保存的快捷鍵 receipt 無錯誤 | PathTextField 有舊預填值；不代表 panel 已位於該目錄 |
| 16:30:18 | 保存的錯誤敘述記 `App.setValue` stale element／`-10005` | 路徑替換失敗，未成功讀回本 attempt 的正確目的地 |
| 16:30:50、至 16:31:25 | 保存的 recovery error／statement 記 `cgWindowNotFound`；目的地 entries=0；確認呼叫計數記 0 | 失聯後 chooser 狀態未知；沒有可歸屬終結證據 |
| 第一筆 outcome | 事件 19 保存 `UNKNOWN`，連接事件 18 | 當時保留不確定性；不是誤寫成完成，也不是「確定未送出」 |
| 2026-11-07 第二次日常任務 | 提報稱有新前景觀察，但未落成當次 assets、未 bind、未新增交易 | 此部分是前次 Agent 的提報，非本輪重新觀察 GUI；缺的是當次證據保存／綁定能力的證明，不是 Owner 沒授權 |
| 本輪 Owner 補充 | Owner 回憶整台電腦曾斷網；來源為兩篇貼文、每篇一支影片 | `OBSERVED` 的回溯人類陳述；總量與帳本 2 篇／2 影片相符，斷網精確時間未取得 |
| 本輪唯讀核對 | 19 筆鏈及 evidence-audit 通過；摘要仍為一支完成、一支 UNKNOWN | 本輪重現阻塞投影；另有已完成項 `LOCAL_CHANGED`，兩個 blocker 同時存在 |

這裡的「兩本記事本」對應同一列表中的兩篇貼文；不據口語差異推成兩份獨立列表，也不以總數相同單獨認領來源。

## 每份關鍵證據的證明力

| 證據 | 已證明／可直接讀到 | 未證明 |
|---|---|---|
| intent | attempt、原 staging、VIDEO 身分、scan 綁定及初始計數 | `save_all_count=0` 是帳務初始值，不是 GUI 呼叫計數 |
| viewer 截圖 | 當時 viewer 與可見下載圖示的定位脈絡 | 點擊已被 LINE 接受、服務端處理與最終落檔 |
| 下載控制 receipt | 保存內容記錄一次呼叫、null 回傳且無錯誤 | 全部未記錄輸入、其他操作者／程序或後續 App 行為；不是平台保證的全域計數 |
| chooser AX／截圖 | 原生儲存面板出現；另有 GoToWindow 舊預填路徑 | PathTextField、panel current directory、intent staging 三者一致；不能將舊預填值寫成已覆用舊目錄 |
| Go to Folder input receipt | 實際記的是 `super+shift+g` 成功 | 不是 `App.setValue` 成功的 receipt；檔名含 input 不改變其內容命題 |
| recovery errors／statement | 保存內容記載 stale element 與後續視窗查找失敗 | 不是完整平台呼叫 trace，也不能證明網路是該錯誤原因；沒有排除副作用保證 |
| `chooser_confirm_call_count=0` | Agent 紀錄中沒有最終確認呼叫 | 不能單獨排除晚到操作、未涵蓋的介面或其他程序；不是原操作已停止的正面證據 |
| staging 當時與本輪皆為空 | 指定目錄的查核範圍沒有結果檔；本輪 device／inode 與 intent 相符 | 沒有服務端傳輸、沒有 cache、沒有別處落檔或今後不會繼續 |
| outcome bundle 與 hash | 保存 bytes／context 可驗，statement 及 9 個 assets 共 10 個子 blob 與原件相符 | hash 不會把敘述提升成真實 sensor、停止證明或 acceptance |
| 第一支 completion／最新 `LOCAL_CHANGED` | 一個是歷史完成事實，一個是目前本機一致性投影 | 本輪未進一步定位 LOCAL_CHANGED 的具體原因；不可歸因第二支或斷網，也不可抹去原完成事實 |

因此，舊 bundle 不足以產生新的終態 reconcile。沒有新結果證據時，連重複追加 `reconcile UNKNOWN` 也不會增加資訊，沒有必要為了表示工作有做而寫入。

## 第一性原理：為何「斷網後重試」不能直接解鎖

此任務包含數個不能原子完成的系統：Agent／CUA 的輸入、LINE 的介面／下載處理、本機檔案系統與追加式帳本。intent 能先保留意圖，但不能與 LINE 點擊構成同一原子交易。電腦斷網可能同時影響來源傳輸與 Agent 工具通道；本機 LINE／儲存面板是否繼續存在是另一個命題。

這造成「呼叫可能已發生，但回覆或後續觀察遺失」的空窗。重新按下載不是讀取結果。現有資料沒有證明 LINE 提供可由本專案控制的服務端冪等 token；本地 attempt ID 只供本專案認領，不能強迫 LINE 對重複點擊去重。

這與 [AWS 對未知結果及冪等重試的分析](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) 所描述的風險相符：回覆遺失後，重試可能重複副作用；可安全自動重試的契約需要明確的去重／結果認領能力。此來源僅支持一般交易原則，沒有提供 LINE 的能力保證。

現有 UNKNOWN gate 保護了不重送的安全性，但文件對如何取得充分停止證據仍明示 `UNKNOWN`。這不是接續能力已經存在的證明。只反覆要求「補正面證據」而不提供已驗證的取得方法，會讓下一個 Agent 繼承無法推進的狀態。要修的是可觀察的恢復路徑，不能以刪除歷史或降低證據標準換取表面進度。

## 因果解釋、替代原因與可否證條件

1. **直接失敗鏈已支持：** chooser 路徑替換未成功 → CUA 視窗查找持續失敗 → 原 attempt 的目的地／終結無法觀察 → outcome UNKNOWN → 新任務不得重新派送。新前景沒有原件落檔，又使第二次無法完成當次 bind。兩個階段要分開處理。
2. **首發故障的根因仍不確定：** 整機斷網可能導致工具連線或 LINE 處理中斷，但沒有同步的網路事件、CUA server log、LINE 錯誤或 crash receipt。stale element 也可能來自視窗／模態介面切換或 handle 壽命，`cgWindowNotFound` 也不能單獨證明 LINE crash。不能將 Owner 的回憶降為無效，也不能把它寫成已完成技術歸因。
3. **不是缺少備份授權：** 提報及本輪補充都表達備份／恢復意圖；實際帳本 `recovery_authorized=true`。故這次不是「false 且沒有修改授權命令」的分支。仍須滿足當次前景、來源身分與停止證據。
4. **不是完全缺少恢復交易：** `notes.py` 已有 bind、reconcile、恢復 intent 與禁止重送規則。缺口主要是如何可靠取得／保存新觀察及證明原操作終結。現階段沒有足夠證據要求重寫 CLI、移除 gate 或增加控制器。
5. **Agent 不遵循與工具故障不能先混為一談：** Skill 已要求新鮮 AX／映射與輸入後再觀察。只有 stale error 的摘要，不能證明操作前用了舊索引；也不能由某一 Agent 無法存圖，推成所有 Session 都沒有保存能力。需要該次工具文件、實際呼叫／回傳與落檔證據才能判定。

若找到當時可歸屬原 attempt 的成功路徑讀回、最終確認／取消或下載終結證據，必須更新對 UNKNOWN 的判斷；若找到原工作階段已按文件成功完成同一恢復分支，則「未有實證恢復方法」需收窄。若同步網路／程序紀錄顯示當時未斷線或另一時間才斷線，則不能再以整機斷網解釋該分鐘故障。

## 既有嘗試與學到的事

- 原路徑替換：產生 stale element 新資訊；沒有成功目的地讀回，不再照原 handle 輸入。
- 原任務對 LINE 名稱、bundle ID 與舊 binding 的恢復查詢：保存的結果均為 `cgWindowNotFound`，未增加 chooser 現況。這些不是新的下載派送，但已反映同方法無法恢復觀察；本輪不再重播或重設嘗試額度。
- 隔日查摘要／空目錄：確認 UNKNOWN 與獨立 LOCAL_CHANGED；仍無正面終結證據。換 Session 並沒有讓原交易消失。
- 本輪來源／鏈／blob 稽核：排除本 packet 缺少保存資產或 hash chain 損壞的假說；沒有補出失聯後 UI 狀態。本輪未執行任何產品修復 attempt。
- 私有提報將帳本 hash 路徑當目錄：本輪讀取 `…/<hash>/bundle.json` 實際 exit 1（Not a directory）。依事件引用及 `notes_evidence.preserve_bundle()` 核對，帳本保存格式為 `evidence/<manifest-hash>` 與同層子 blob；任務區封裝才有 `bundle.json`。改讀真正 manifest 成功，這是定位錯誤，不是證據遺失。提報原件未改。

## 接續機制的有界設計建議

以下為唯一 `PLANNER_REPLAN` 路線的設計約束，不是本輪開始實作或執行恢復。

**目標：** 相同正式日常 Prompt 啟動的新 Agent，可自動找回原交易、判斷已證明層次，安全處理可收斂分支；無法收斂時只交給 Owner 一件具體可操作的事情。已完成不重下，原檔與 UNKNOWN 歷史不消失。

| 找回的狀態 | 方案應定義的安全接續 | 必須保留的停止條件 |
|---|---|---|
| 已有 completion | 保留已完成；先分辨 VERIFIED_PRESENT、LOCAL_MISSING、LOCAL_CHANGED | LOCAL_CHANGED 保護原件並阻止依賴該資料完整性的派送 |
| `DOWNLOAD_FINISHED`／pending naming | 對同一 attempt verify，或以 resume 接續同一發布交易 | 不重按下載，不另造結果歸屬 |
| UNKNOWN 且有可歸屬晚到結果 | 先核對原 attempt／目的地／正面終結及穩定檔，再提出追加 reconcile 的精確預覽 | 檔名、hash、空目錄或單一 UI 訊號不足 |
| UNKNOWN 且原 chooser 仍可唯一辨識 | 規劃並實證「安全取消原操作」的方法：當次工具支援、實際可靠控制、取消前後觀察、原目標與操作終結證據 | 不能只憑按了取消或視窗消失，就假定背景作業不會繼續；不得猜 Escape／Return 或強退 LINE |
| 已以充分證據收斂 STOPPED／NOT_SENT | 保留舊 attempt／檔案，append reconcile；在既有持久恢復授權與 gate 滿足後，建立連結原 attempt 的新空白恢復 intent | 新 attempt 的下載控制與 chooser 確認仍各最多一次；不續用舊 handle／座標 |
| 仍無法確認原操作是否存活／已停止 | 保存 UNKNOWN，輸出確切缺哪一份觀察或需 Owner 執行哪個已核對動作 | 不能用新 Session、新目錄、重新 init、exclude/protect 或刪事件解鎖 |

方案還須處理三個目前尚未實證的操作問題：

1. **先確認能保存證據，再開始新交易。** 在原生 CUA 當次文件允許的能力內，實際將當次 AX／截圖保存為專案內 regular files，並用現有 evidence-pack 讀回。必要方法應收進 Skill references，不能依賴下一個 Agent 去找本開發報告。既有 notes_capture 只包 CLI，不會自動保存 CUA 畫面。
2. **將可重做的觀察／路徑準備與不可盲重送的控制分開。** stale element 後先取得新狀態與焦點，若當次工具能力允許、原 chooser 仍唯一且前景有效，才評估同一 chooser 的路徑修正。每個步驟均要讀回，PathTextField 的確認與儲存面板最終確認不可混為同一步；不得重按 viewer 下載控制。視窗失聯時停止輸入。這不是現在重播原故障的授權。
3. **恢復所需的 checkpoint 與證據必須持久可找回。** 至少能還原原 attempt／intent／staging、來源身分、已呼叫控制的已知／未知範圍、chooser 三層目的地、最後可靠觀察與錯誤。先盤點現有 intent、capture、bundle、summary 已提供的欄位；只有確認缺少必要事實，才提出最小追加式變更。不得把尚未取得 receipt 的呼叫記為零，也不要求 Owner 填內部資料。

「原操作已停止」須針對本任務可觀察的原 LINE 操作與本機寫入生命週期作明確界定，不要求 Agent 證明不可見的整個服務端從未傳輸；也不能由此反推未派送。取消後若仍可能續寫原目錄，必須保留 UNKNOWN 或另由 Owner 決定必要環境處置與驗證邊界。這個界定會影響資料安全，不能在 Implementer 中暗改標準。

**成功檢查：** 有界方案要為「儲存面板前、Go to Folder 中、最終確認回覆遺失、下載中、完成後」各列出可取得的觀察、使用既有命令的前置條件、真正停止條件及未可實作的分支。優先實證本次 Go to Folder 中斷分支。實作若有必要，再按變更內容安排相稱回歸；真實接續仍使用同一日常正式 Prompt，不能用離線測試代替。

**範圍與停止：** 本路線只為本中斷根因重規劃；不自動派發下一正式角色，不操作真實帳本／LINE，不處理另一支 LOCAL_CHANGED 的修復，不擴大到相簿或其他列表。必要能力缺失、同一方法兩次無新資訊，或必須放寬 UNKNOWN／資料界線時，記明未解並交 Owner 決定，不能繼續試到成功。

**所需人類決策：** 由 Owner 決定是否將本報告交給另一主 Session 制定上述方案；真實取消、終止應用程式、帳本 reconcile 或恢復下載，須另有精確範圍與當次有效前景。既有 `recovery_authorized=true` 保留，不再要求重複授予相同備份意圖。本輪沒有啟動此路線。

## 其他發現及不可混併的問題

- **獨立的 LOCAL_CHANGED：** 最新摘要確實指出第一支已完成影片目前的本機一致性異常。本輪只確認投影與分開列示，沒有定位差異、刪額外檔、覆寫影片或重寫 completion。即使第二支收斂，這個 blocker 仍然存在，不能承諾即可派送。
- **文件與目前查詢輸出不同：** Skill、下載 reference 及手冊敘述 memory 不含 staging 目的地；實際 `_unresolved_attempts()` 及本輪輸出已含 `destination`，仍不含完整 attempt 歷史／completion manifest。這是可確認的文件漂移，應於後續方案中列為最小文件修正，不是造成原 CUA stale error 的根因。本輪未改產品文件。
- **證據保存阻塞尚未定位到能力層：** 前次 Agent 說無法落檔，只支持該次未完成保存。原任務有保存成功的 screenshot／AX，排除「專案從未能保存」；無法據此證明不同 Session 的工具能力相同。
- **刪除尾事件也不可接受：** 本輪確認事件 19 是當前鏈尾。刪除它未必立即造成現存後繼 hash 斷鏈，因為目前沒有後繼事件；但會抹去已記錄結果，留下仍須保護的 intent，也不能變出安全的 NOT_SENT。無 CLI 刪除命令；不建議人工例外或重算鏈。

## 實際查核與界限

本輪在私有任務區保存 `diagnose_readonly.py`、命令 receipt、stdout／stderr、前後保護清單與 findings。診斷腳本僅向該任務新增檔案，對既有帳本與來源唯讀。

| 實際命令／查核 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0 |
| 同入口 `lists` | exit 0 |
| 同入口 `reconcile --help` | exit 0；允許四個既有 result |
| 同入口 `evidence-audit --records-root <原帳本>` | exit 0；19 events、event_chain VERIFIED、integrity_ok true；不是業務／GUI 驗收 |
| 同入口 `memory --records-root <原帳本>` | exit 0；COMPLETE scan、COMPLETED=1、UNKNOWN=1、LOCAL_CHANGED=1，兩個 dispatch blockers |
| `/usr/bin/python3 -B <私有任務>/diagnose_readonly.py` | exit 0；鏈與 10 個子 blob 校驗、429 份受保護來源前後 SHA-256／大小一致、原 staging entries=0 |
| 3 張指定原始截圖的離線閱圖 | `OBSERVED`；不冒充當次 LINE 畫面或獨立驗收 |
| 產品單元回歸、GUI 重現、取消操作、reconcile、恢復 intent、影片重新解碼、跨 Session 接續 E2E | `NOT_RUN`；此角色未實作或操作產品 |

另外，專案內 `policies/` 不存在，初次 rg exit 2；已讀 Owner 指定的全域 v4.9.0 workflow／subagent policy，未拿舊 controller 替代。分支未設定 upstream 的查詢 exit 128；不是 push 失敗，後續使用明確 origin／branch ref。這些調查命令問題不算原下載根因的新修復 attempt。

前後保護清單是在本輪診斷腳本執行前後比對，不能聲稱涵蓋此前所有時間；未全面重新驗證私人影片或外部副本。檔案校驗通過也沒有把 UNKNOWN 轉為已停止。

## 六項狀態與交接

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: NOT_RUN
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: PASS（本輪唯讀鏈／引用／來源不變查核）；產品回歸與 GUI 恢復 NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED
```

分析已完成；接續機制尚未實作，原備份未完成，不標 DONE。Owner 授權的 commit／push 僅交付去識別化診斷文件，不是修復執行、獨立接受或真實帳本解鎖。
