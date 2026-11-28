# 記事本完成媒體與發布恢復：內容身分修復

基準：`feature/line-notes-media`，`f38b61b94bd8f7328f358cd5e44759402428e248`。
Owner 本次授權根因分析、產品／文件修復、離線回歸及指定 CLI 平行工作；未授權真實帳本變更或 LINE 下載。
本報告由修復主代理整合，不是獨立審查或正式 acceptance。

## 根因與證據層級

備份需要證明「授權位置的預期內容仍在」，以及「當次發布可安全執行」。這兩個命題需要不同證據。

`notes.py` 的 `_completion_availability()`、`_candidate_file_availability()` 把歷史 device／inode／時間等值當成已保存內容的必要條件。內容與布局相同也會因 metadata 不同變成 `LOCAL_CHANGED`。完成目錄的 exception 再影響同目錄 sibling，`_assert_no_local_changed()`、summary 與 settlement gate 將此投影為全局 blocker，restart scope 再納入整篇與額外複製。

這是本機可用性 predicate 的抽象錯誤；列表／貼文／媒體的來源 key 並未因此被改寫。修正應移除錯誤的內容判準，不能讓 Agent 忽略工具拒絕。

事故提報與作者釐清支持：P1 已完成，P2 只有 publish-plan、來源仍在、target 未建立，沒有 DIRECTORY_READY／FILE_LINKED／SOURCE_REMOVED。已觀測的拒絕是 completion 的通用 gate；不能從通用錯誤聲稱個別 file predicate 已在 runtime 被隔離。來源檔與 staging 的後續 device 阻擋是靜態因果推論，須另以合成 fixture 驗證。本修復不重新操作真實帳本以證明它。

`st_dev` 描述檔案所在 device，inode 的唯一性也有 device 範圍。它們不是媒體內容的永久指紋；mtime／ctime 也不等同於內容。[Python 官方 stat 文件](https://docs.python.org/3/library/os.html#os.stat_result) 支持這項欄位語意。token 為何變化、實體 volume 是否相同，無法僅靠這些欄位證明；本修復不新增這種證明需求。

相簿 `daily._check_completion_files()` 一般完成判定沒有歷史 device／inode equality，因此不會因單純 device 差異發生相同拒絕；它仍核對時間、內容與布局。記事本採內容／布局判準，並非宣稱兩條流程的每個 predicate 完全相同，也不修改相簿程式或交易防護。

## 責任與控制矩陣

| 層級 | 判定 | 修復責任 |
|---|---|---|
| notes 工具 | 主要根因；歷史環境值錯作完成內容必要條件 | 同步修 completion、candidate 與原 pending publish 鏈 |
| Skill/reference | 次要一致性缺口；曾明文要求 device 改變就 CHANGED | 說清已完成內容、進行中交易、當期 hardlink 三者差異 |
| 執行 Agent | 現有證據支持依工具拒絕停止，未證明理解錯誤 | 按修正後 Skill 使用原交易；不手繞 gate |
| Owner／裝置 | 沒有證據支持 Owner 操作是根因 | 不要求 Owner 解釋 device token、提供 UUID 或額外確認 |
| 修復主代理／helpers | 共同實作與回歸 | 自評不算獨立 acceptance；未測實機項如實保留 |

## 採納與否決

採納完成媒體／已驗證 candidate 的授權路徑、預期名稱與檔集、regular file、單一 link、非 symlink、size、穩定讀取及 SHA-256。歷史 metadata 留作診斷，不改舊事件。同次讀取期間的 device／inode／size／時間變動仍拒絕。

pending publish 仍是有來源移除動作的交易，須保留原路徑、inode、內容、允許的時間及 link 狀態、journal 與防覆寫；只解除歷史 device-only 差異。當下 hardlink 必須同 filesystem，source／target 必須是同一個當期 device＋inode，移除來源前仍核對。

否決 volume registry、永久 UUID、額外 confirmation／flag／warning schema、忽略 blocker、重下補帳與相簿 fallback。真正內容／布局或授權異常仍停止。全局 gate 本身不改成逐篇跳過；移除的是誤判來源，真正 UNKNOWN、活動下載、未完成命名與 scope 外 LOCAL_CHANGED 仍維持原保護。

## 按優先序的修復切片

1. 修 completion 與 candidate 的歷史 metadata predicate，保持穩定內容讀回與原事件不可變。
2. 修原 pending publish 的 staging、DIRECTORY_READY、來源讀回、FILE_LINKED 及發布結尾；涵蓋原交易不同中斷點，不新增 intent／verification／publish-plan／generation。
3. 修 active candidate 缺席分類：整篇版本目錄缺席才 MISSING，目錄仍在缺檔是 CHANGED；已存在 sibling 的必要檔不得被 allowed names 的上限掩蓋。
4. 同步 Skill/reference，修問題單兩處與原保護契約衝突的測試預期。
5. 對合成 fixture 執行正反例與最小回歸，保存實際命令、exit 與限制，建立功能分支 checkpoint。正式日常入口的實機確認仍留給具有效前景交接的任務。

## 問題單 §11 決策 1–12

| 題號 | 決策與界線 |
|---|---|
| 1 | 同意。completion／已驗證 candidate 的歷史 device 是診斷資料；當次操作仍使用 device。 |
| 2 | 同意。路徑、檔集、檔案型別、單一 link、size、穩定讀取及 SHA-256 一起成立，不能只看 hash。 |
| 3 | 同意。保留當期 same-device 與 link 後的當期身分核對。 |
| 4 | 完成媒體／已驗證 candidate 同意；進行中 publish 不能順帶解除 inode、時間與 journal 約束。 |
| 5 | 同意。完成目錄、完成檔、candidate 與 pending publish 的歷史 device 比對一起處理。 |
| 6 | 同意。可唯一核對時 resume 原 P2 交易；不新增 intent、重下或 generation。這不是本次真實交易已恢復的宣告。 |
| 7 | 同意。部分缺檔為 CHANGED，整篇目錄缺席才 MISSING；UNKNOWN／活動下載仍阻擋新派送。 |
| 8 | 同意拒絕。直接修 predicate，不增加持久資源識別或人工流程。 |
| 9 | 同意。同步 Skill、verification-and-recovery、download-and-ledger 及測試敘述。 |
| 10 | 同意對齊內容／布局抽象；相簿仍有時間核對，兩者不是逐行相同，且不修改相簿交易期規則。 |
| 11 | 同意拒絕手動繞過。所有可用性語意須在程式、測試與文件一致。 |
| 12 | 同意。分析、實作、離線回歸、真實 GUI、跨 Session 實機恢復、獨立 acceptance 分開列示。 |

問題單 §13 原「完成檔缺檔 → LOCAL_MISSING」錯誤，已更正；原「scope 外 UNKNOWN 只阻擋該項」亦與列表級禁止新派送契約衝突，已更正。保留問題單事故時狀態，不把本次修復結果回填成當時成功。

## 驗證紀錄

環境：Python 3.9.6、Darwin 27.2.0 arm64、Swift 6.3.3。相簿測試沿用既有測試選取的 matching SDK，未修改系統工具鏈。所有媒體與帳本都是合成 fixture。

| 實際命令 | 結果 | 證據範圍 |
|---|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS；exit 0；73 tests；318.257s | 相簿回歸，含既有真實 ImageIO 對合成檔案的檢查；沒有 LINE GUI |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | PASS；exit 0 | CLI 載入與命令介面 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_notes_identity_drift.py` | PASS；exit 0；11 tests；2.358s | 完成內容、原發布交易、verification-only、copy-plan replay、真異常與穩定讀取 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest tests.test_notes_restart` | PASS；exit 0；51 tests | helper 回歸；包含新增 6 項 candidate 案例 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest tests.test_notes_reattest` | PASS；exit 0；30 tests | helper 回歸；保留原 witness／有效 binding 邊界 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | PASS；exit 0；314 tests；40.869s | 主代理整合回歸；包含相容性與新增 17 個測試方法 |
| `git diff --check` | PASS；exit 0 | 完成回歸後核對 |

新增 17 個測試方法，另有多個 subTest 情境；不把 subTest 數量混充方法數。測試主體如下：

| 保護命題 | 正反例與結果 |
|---|---|
| 完成媒體只因歷史 metadata 改變 | PASS：device epoch、相同內容換 inode、mtime／ctime、完成目錄換 inode，仍 VERIFIED_PRESENT；summary 不產生假 blocker／restart |
| pending 原發布恢復 | PASS：plan-only、DIRECTORY_READY、FILE_LINKED、SOURCE_REMOVED 四個中斷點，跨 device epoch 後原交易完成並重新開帳本；P1 原檔與所有原事件 bytes 不變 |
| 不重送／不新建批次 | PASS：intent、outcome、verification、publish-plan 與 restart 事件計數不增，只追加合法發布 progress／completion；沒有 versions 目錄；重複 resume 無新事件 |
| verification 已保存、尚無 plan | PASS：原 download-check 接續，verification 仍只有原一筆，重開後可用 |
| restart copy-plan 已保存、尚無 target | PASS：當次 copy 使用 live source；candidate 保留 plan 原 source 引用；原 plan 只有一筆，重開 summary／activation 成立 |
| candidate metadata 與讀取中變動 | PASS：歷史 device／時間／inode 差異且內容一致可用；同次讀取變動仍 CHANGED |
| 缺檔分類與 sibling | PASS：整篇缺席=MISSING 並保留完成；目錄仍在缺 candidate=CHANGED；缺 sibling 不被 allowed names 掩蓋；未 copy 的 pending 計畫檔不誤列 required |
| 真實內容與布局異常 | PASS：同 size hash 改變、size 改變、部分缺檔、額外檔、symlink、hardlink 仍阻擋原發布並保留來源 |
| 交易與派送安全 | PASS：pending 來源 inode 替換、當期跨 device hardlink、UNKNOWN／無 outcome 仍拒絕；既有 reattest、跨列表、授權路徑防護由原 suite 覆蓋 |

基準對照：主代理以私有 `run_baseline_identity_tests.py` 將精確 `f38b61b` notes.py 載入記憶體，沿用專案根目錄與目前同一批合成測試，不改產品原檔、Git 或真實歷史。11 tests 對舊版為預期 FAIL（exit 1；11 failures、2 errors，含 subTest）；其中觀測到 completion 的假 CHANGED、staging 的 device 拒絕與 verification-only 的拒絕。candidate helper 另以隔離合成副本對舊版跑 6 項測試，3 failures：device／時間假 CHANGED、部分缺檔誤列 MISSING、缺 sibling 未阻擋。兩組對修正版均通過。

實作中期曾有舊 reattest fixture 的 32 個 subTest failure 與 restart 的 2 個 failure：前者共用 fixture 把 device-only 當損壞，後者是舊讀取故障注入點與舊 inode 判準。已修測試語意；真正 witness 的 device mapping／inode／時間／hash 負例仍保留。主代理新增 fixture 初次漏模擬 Python 3.9 pathlib 快取的 stat 入口，造成同次讀取混用 device；修正模擬一致性後 11 項通過，未以放寬產品即時檢查消除失敗。原始失敗輸出均留私有 task。

以下 SHA-256 對應整合驗證的實際檔案：

| 檔案 | SHA-256 |
|---|---|
| 基準 `f38b61b` notes.py | `f9636b19b24af6a66d271fd95f7a5c590e0bd6005472117edc9b58cfb1f22108` |
| 修正版 notes.py | `00020d3b2a5604df591630e184b95176166ae28d2a27251b5c2b1b04d4dde46a` |
| test_notes_identity_drift.py | `8abebed9a82e16c7d88bc29d0b85208abc31f4b11c1393bfd914339d213eb354` |
| test_notes_restart.py | `26cee69893bba7b8094e6838ae39c6acefa1568fb067d64722b8dfa19f878539` |
| test_notes_reattest.py | `1a01d41733297a6058c33197e81a25d324ca8574347f73b7b65ce6a0b8299b94` |

完整命令輸出、失敗分析、baseline runner、helpers 交接與啟動 argv 保存在本專案私有 task 目錄，未納入 Git。公開報告只保留匿名情境、程式與合成測試證據。整合 suite 的 argparse 錯誤文字來自預期拒絕測試，最終 unittest exit 0，不是被忽略的測試失敗。

## 平行工作與模型證據

主代理使用 Herdr 開啟兩個 sibling pane，core helper 僅改 notes.py，tests helper 改既有 restart／reattest 測試並新增 candidate 案例，主代理補新 identity-drift 測試並負責文件、整合、Git 與最終報告；左側原提報 Agent 提供事故釐清，未被當成獨立審查者。

首次只指定模型、max 與 --yolo 的 core 請求落到 ChatGPT 帳戶路徑而遭拒，未修改產品。Owner 隨後明示完整 Ollama Cloud 參數，兩個 pane 以該參數重新啟動並開始工作。請求為 deepseek-v4.1-flash:1017、max、--yolo，provider 為 ollama_cloud，base URL 為 https://ollama.com/v1，wire_api=responses；關閉該 provider 的 websocket 與 standalone web search，使用 Owner 指定的 multi_agent flags。啟動 argv 與 TUI 顯示是兩種證據；沒有 provider 回報的 backend 身分、完整 usage 或費用證據，不宣稱相關數值。

## 未知與風險

- 沒有真實 LINE GUI、chooser、下載或跨 Session 實機恢復結果；合成測試不能替代。
- 沒有對真實 P2 執行 resume、改寫 ledger、媒體或既有完成事實。
- 仍可能有外部程序改動來源；不承諾 OS 隔離、原子快照或 exactly-once。
- 已完成內容的 metadata 容忍不證明相同實體 volume，也不允許跨列表或未授權路徑認領。
- 有效 reattest 列表綁定仍採既有嚴格規則；不藉本修復解除其 witness／scan 要求。
- 待獨立審查及 Owner 用日常正式 Prompt 進行實際能力確認；不合併 master。

## 六項狀態

| 狀態 | 結果 | 範圍 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `PARTIAL` | 程式根因修正與離線回歸完成；真實備份恢復尚未執行 |
| `IMPLEMENTATION_STATUS` | `PASS` | 程式、測試、Skill/reference 與問題單勘誤已實作 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN` | 尚無正式日常入口的實機確認 |
| `REQUIRED_VERIFICATION_STATUS` | `PASS` | 本次最小離線回歸與 diff 檢查通過；不含 GUI |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | helpers 是共同實作者，不簽發獨立接受 |
| `TASK_CLOSURE_STATUS` | `NOT_DONE` | 待必要獨立審查與 Owner 日常實機確認，不合併 master |

後續交接沿用手冊的日常記事本正式 Prompt。取得真實任務授權與有效前景後，先查原帳本與原 attempt；P2 若仍能唯一核對，使用原 `resume`，不重下、不改歷史、不自行執行 restart confirm。若有真正內容／布局或授權異常，仍依原停止條件處理。這段交接不是新下載授權。
