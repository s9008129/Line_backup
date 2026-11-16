# 記事本下載控制發現：修復與重測交接

## 交付結果與適用範圍

開發修復與離線回歸已完成，可由 Owner 交回 Tester，使用原日常正式記事本備份 Prompt 與新的有效前景交接重測。這不是已證明 C/D 可以下載；真實 viewer 成效、跨 Session 與獨立驗收仍為 NOT_RUN。

基準為 `feature/line-notes-media` 的 `d655025ae2c5ccb1129f740dafd0302e5456e4b2`。起始工作樹乾淨。本次沒有操作 LINE、沒有建立真實 intent、沒有下載，沒有改寫真實永久帳本或媒體。

## 根因與修復

Leader 與左側 Tester 完成兩次證據釐清。第一個未成立條件是當次下載控制的正面可見、歸屬與定位；流程停在 intent 前。C/D 共 6 項 PENDING 是原提報事實，本次未重新執行真實列表投影。

歷史 B 的 selected-filmstrip 操作與 toolbar 出現只有時序關聯。toggle、timeout、capture race 及 C viewer 差異尚未分離；本次沒有重新探測 CUA 能力，不把原提報的 hover-only 缺口當成永久平台事實。

| 缺口 | 本次修改 |
|---|---|
| Skill 未明列可用導覽候選 | 在沒有可用 hover-only、且授權/前景/來源/返回控制/已選目標/安全邊緣/新映射均有據時，允許 intent 前一次 NAVIGATION 候選 |
| 對 transient 與未知的判定不完整 | 統一 TOOLBAR_VISIBLE、TOOLBAR_NOT_SHOWN、REVEAL_TRANSIENT 與觀察 UNKNOWN；曾可見後消失或播放/身分/索引/幾何/輸入不明即停，不重點/換點/reopen 重設 |
| reveal 方法與時序不易跨 Session 使用 | 方法與停止條件直接保存在 Skill；以既有 v2 screenshot/ax/input_receipt/observation 保存前後原件、時序與 receipt |
| 私有 bundle 被誤稱為永久事實的風險 | 明列合法事件引用後才永久保存；同 scan post/media 已寫入時，只留私有 blocker 原件，不製造交易或重寫細盤 |
| 導覽與下載控制混用風險 | NAVIGATION 沿用 persistSingleInput；下載仍用原 persistGroundedDownloadClick，保留一次派送與 intent 讀回要求 |

沒有新增 CLI、schema、event、GUI controller 或媒體業務狀態。AX 缺少 control 不得否定截圖；MIME/download-check、完成、排除與禁止重送語意保留。候選次數與視覺判斷由 Agent 遵循，CLI 不提供 GUI sensor 或原生命中證明。

## 測試隔離事件與已授權處置

初輪 Worker2 在未隔離 notes._active_task_path 的情況下執行新合成測試；bind 誤寫真實 active-notes-task.json，使其指向已清理的 fixture。當時 focused test 雖 exit 0/1 test OK，因副作用不作有效驗證。Leader 停止後，Owner 明示「請繼續修復」。

Leader 核對污染檔 SHA-256 `16d4f4bd3670db580946cdb16563f1a23e06743e57a33b3ad86acc4c08887746`、synthetic session 與 regular-file 身分後，將其移入本任務私有 quarantine；讀回一致，原 active 路徑缺席。沒有冒稱精確還原覆寫前 bytes；先前的 locator-before-tests.json 是事後 guard，不是原值備份。

新測試已在任何 create/bind 前注入 fixture locator，保留外層 sentinel，透過 addCleanup 在成功/失敗時清理 fixture、還原 patch 並核對 sentinel。永久歷史仍由 notes lists 與原帳本讀取；active 缺席不等於空帳，日常正式 bind 依既有流程建立新的提示定位。

## 驗證結果

| 實際命令 | 結果 |
|---|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | PASS；exit 0；73 tests OK |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | PASS；exit 0 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | PASS；exit 0；315 tests OK |
| `git diff --check` | PASS；exit 0 |
| 新增文件相對連結核對 | PASS；4 個目標檔存在 |
| 三階段前後帳本/locator 保護比對 | PASS；各階段均一致 |

新合成案例驗證 opaque TOOLBAR_VISIBLE/REVEAL_TRANSIENT statement 與 timeline 可保存、同 AX/不同 screenshot refs 能並存、來源移除後仍可讀、context mismatch 與 child drift 被拒絕，媒體仍 PENDING 且無 intent/outcome。這是 bytes/context/投影驗證，不是視覺判讀、reveal 效果或 GUI 因果測試。

回歸前後比對真實 notes/album 永久紀錄的檔案清單、bytes/hash 及兩個 active locator，結果一致；notes active 仍缺席，隔離副本雜湊保持一致。此比對不包含照片區與全檔案系統，不是獨立驗收。

環境：macOS arm64，`/usr/bin/python3` 3.9.6，Apple Swift 6.3.3；沿用既有測試選用的 SDK，沒有變更系統工具鏈。原始命令、stdout/stderr、exit code、hash 與保護比對位於私有 task directory。

## 協作與模型證據

Worker1/2 使用 Herdr Codex CLI，啟動 request 含 Owner 指定 DeepSeek BYOK/model/provider/responses/max 與其餘完整參數；終端顯示 deepseek-v4.1-flash:1017 max。兩人只在同一開發任務內協作，不簽發獨立接受。Worker3 依 Owner 要求以 GPT-6-luna 梳理差異與實際結果，撰寫提交訊息；Leader 執行逐檔 add/commit/push。

Request、session display、配置預設與 provider-reported usage 分開；本次未取得 provider usage，不宣稱實際後端身分、成本或 token 節省。

## 六個狀態

| 狀態 | 值與範圍 |
|---|---|
| PRIMARY_OUTCOME_STATUS | READY_FOR_TESTER_RETEST（開發交付） |
| IMPLEMENTATION_STATUS | PASS（Skill/證據規則及合成測試） |
| CORE_ACCEPTANCE_STATUS | NOT_RUN（真實列表） |
| REQUIRED_VERIFICATION_STATUS | PASS（本次規定的離線回歸及保護比對） |
| INDEPENDENT_ACCEPTANCE_STATUS | NOT_RUN |
| TASK_CLOSURE_STATUS | AWAITING_OWNER_TRIAL |

沒有以 commit/push 或測試成功標記整體 DONE。

## Tester 下一步與未測範圍

Owner 使用 [手冊](../../LINE相簿備份_使用手冊.md) 的記事本正式日常 Prompt，交接同一列表與有效前景。Tester 從 lists/永久帳本重新定位與盤點，跳過已完成 B；active locator 缺席不得當成空帳，也不靠開發報告才能完成日常流程。

新觀察支持已選目標與非播放安全邊緣時，依更新 Skill 做一次候選導覽；安全區、定位或控制仍不明就保留 PENDING。工具列可見且下載控制歸屬/啟用/映射成立，才按原 intent、一次下載、chooser、outcome、download-check 與 completion 流程。曾出現後消失即停止，不靠重點重送解鎖。

真實 C reveal 與下載、D 的 5 項、影片式 viewer 入口、跨 Session GUI、混合附件 chooser、獨立 Acceptance/E2E 均為 NOT_RUN。Tester 的後續結果需獨立記錄，不由本次離線結果推定。

交付僅功能分支，不 merge master、不 force-push。提交訊息含意圖、做了什麼、下一步的建議、驗證與結果；讀回 commit body，推送後核對遠端精確 HEAD。原始私有證據、污染定位檔、帳本、媒體與憑證不納入 Git。
