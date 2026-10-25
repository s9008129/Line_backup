# LINE 相簿備份使用手冊

適用 Mac，更新日期：2026-10-25。

把正確群組的「相簿列表」開在前景，告訴 Agent 照片要存在哪裡，就可以開始準備。不用輸入群組名稱，也不用核對中文辨識結果是否一字不差。

**目前版本狀態：**已有真實 LINE 的導覽、儲存全部與照片驗證案例。本機 P3 候選可產生綁定來源／runtime／群組／相簿／目的地的審查準備資料、驗證受審與 Owner 簽章介面、持久預留一次 attempt，並用既有 ImageIO 驗證後寫回 `MANUAL_DIAGNOSTIC` 紀錄。正式執行所需的 reviewer／Owner／runtime 公鑰與可信外部簽發通道尚未由受信任管理者配置；任意 JSON、Agent 自選公鑰及測試 fixture 都不構成授權。故 production CLI 目前會 fail closed，Save All 與 CUA receipt bridge 尚未接通；不得把 P3 離線通過寫成實機或正式 AUTO 驗收。

## P3 授權入口（目前 fail closed）

P3 的準備、預留與完成讀回入口為：

```sh
PYTHONPATH=src python3 -m line_backup_batch.daily p3-prepare --root "$BACKUP_ROOT" --input <受信任準備資料>
PYTHONPATH=src python3 -m line_backup_batch.daily p3-reserve --root "$BACKUP_ROOT" --input <受審核准資料>
PYTHONPATH=src python3 -m line_backup_batch.daily p3-finalize --root "$BACKUP_ROOT" --input <runtime收據資料>
```

`prepare` 只整理待審資料，不授權下載。`reserve` 必須核對與實作版本綁定的獨立 implementation review、Owner 當輪 L2 範圍、群組 UUID、相簿身份、前景／歷史證據、目的地 mount/device/inode、runtime closure、有效期限、唯一 nonce 及一次 attempt 配額；完成檔案與 ImageIO 驗證後，`finalize` 才能寫回既有的人工診斷記錄。程式會在建立 intent 前做目的地與檔案系統檢查，並在預留不明或 crash 後永久阻止同 nonce 重送。

一般使用者不可自行填 JSON、貼入聊天中的核准文字、修改目的地路徑或提供自選公鑰來取得授權。Production CLI 不接受測試 fixture 或 caller 自選 verifier；reviewer、Owner、runtime 三種簽章需由獨立角色的受信任公鑰驗證。目前尚無受信任管理者配置與外部簽發通道，production reserve／finalize 會停止。CUA runtime 尚未產生 P3 簽章收據，亦沒有可執行 Save All 的 P3 bridge；在這兩項完成並獲獨立實作審查前，禁止正式下載。

## 第一次 51 張正式 E2E 的人工交接

目標 51 張相簿尚未完成實機身份核對。既有唯讀 preflight 記錄目的地磁碟未掛載、目的地尚不存在，且群組 UUID、前景證據、審查與 runtime grant 都缺少；本輪沒有讀取照片或操作 LINE。開始正式 E2E 前，Owner 需在當輪指定：

1. 將正確群組的相簿列表交到 Mac 前景，並指定實際備份目的地；**不需要輸入 GROUP_NAME**。前景交接成立後，Agent 以當下畫面核對群組與日期／張數，不沿用舊座標。
2. 確認真正目的地磁碟已掛載。Agent 在寫入前重新檢查 canonical path、mount、device、inode、空白新 attempt 目錄及硬連結／原子建立／fsync／flock 能力；實際 NTFS 尚未驗證，能力檢查失敗就停止。
3. 先完成核准來源、runtime closure 與三個獨立簽章角色的可信配置，再取得精確 implementation commit 的外部 Code Review 和 Owner 對此群組／相簿／目的地的一次 L2。手動 Prompt 或一般 JSON 不代替 grant。
4. 只在所有 gate 通過且 fresh 詳細頁再次核對為 51 張後派送一次 Save All。下載完成後逐檔核對數量、SHA-256、既有 ImageIO 完整像素解碼及持久狀態讀回；不得把人工測試升格正式 AUTO。
5. Save All 派送結果若為 `UNKNOWN`，立即停止且不重送。只有清楚記錄 `STOPPED`／`NOT_SENT`、保留原始部分檔案，並取得對原 attempt 的新 scoped recovery 授權後，才能用另一個新空白目錄開始恢復。

目前因可信 authority channel 與 P3/CUA receipt bridge 未接通，51 張正式 E2E 是 `BLOCKED`；以上是之後的人工交接條件，不構成本輪授權或已完成證據。

## 第一次使用前

準備已登入的 Mac LINE、具有原生 Mac Computer Use 的 Codex Session，以及可寫入、容量充足的備份資料夾。只有終端機或瀏覽器工具，無法代替 Mac 操作能力。

先告訴 Agent 舊備份、完成紀錄與排除項在哪裡；不知道時可以請它先找。新資料夾是空的，不代表這個群組從未備份。

打開終端機，輸入 `cd `，將 Finder 中的專案資料夾拖進去，按 Enter，再輸入 `codex`。進入後貼下方 Prompt。之後搬到開發專區時，用新的專案位置啟動即可；搬移注意事項見後文。

## 日常啟動 Prompt

通常只要改第一行的儲存位置；沒有排除項目就保留 `EXCLUSIONS=[]`。

```text
BACKUP_ROOT=~/Pictures/LINE相簿備份/這次選定的資料夾
EXCLUSIONS=[]
RECOVERY_STRATEGY=ALBUM_LEVEL
PHOTO_LEVEL_RESUME=FUTURE_RESEARCH

請使用目前 Line_backup 專案的 $line-album-agent-cua，備份我交到前景的 LINE 群組相簿列表。不要求我輸入群組名稱，不用精確中文 OCR 比對決定群組是否正確；路徑名稱只是我選的儲存位置。

先讀 AGENTS.md、README.md、使用手冊、Skill，按情境讀 verified-experience.md 與 daily-backup.md。先完成可離線做的檢查；真正需要操作 LINE 時，再請我交出正確群組的相簿列表前景。未交接前不要切換或操作我的 LINE。

本次範圍是交接的這個群組與 BACKUP_ROOT。我授權在有效交接後觀察、捲動、開啟相簿、返回列表，並在合法 L2 與正式交易 gate 全數成立時，對確認未完成且未排除的相簿各執行一次儲存全部，寫入新空白目錄及新增本次紀錄。這份 Prompt 不是 runtime grant；不得偽造 consent、審查或 grant，不重開 closed grant、不重置 ledger。沒有合法 L2 就停在 Save All 前，給我正常核准需要的最小資料與一個下一步。

查正式 state、manual archive、私有 completion／intent、最新批次紀錄及排除項，只使用已確認屬於本群組的資料。在指定位置建立或沿用持久本地群組 UUID；新前景與舊 UUID 有歧義才請我確認，不能跨群組套用完成紀錄。用現有 daily 輔助入口記錄，不新增 GUI 框架。

先確認列表頂端，再用有序重疊的捲動逐張盤點、去重及對帳，直到同一末卡向下捲動仍無位移。AX 子項數不是總本數；日期及張數相同也不能直接視為同一本。未辨識卡片要記未知，不能省略。

沿用 metadata strip→詳細頁核對→fresh menu→持久 intent→合法單次 Save All→chooser 核對新空白目錄→下載穩定→逐張 SHA-256／ImageIO 完整像素解碼→完成紀錄寫後讀回。主視窗看不到選單時先查獨立 popup，不盲點。已完成或人工備份相簿永不重下載，檔案異動就停止核對。

中斷保留所有部分檔案與 intent。UNKNOWN 不自動重送。只有先前下載已確認終止、派送狀態明確，且另取得我對該本的恢復授權後，才以另一個全新空白目錄重下未完成相簿；不覆寫、不刪除原目錄。照片級續傳是未來研究，不阻擋目前相簿級功能驗收。

所有卡片都已完成或有明確排除、從頂到底證據完整，且 INCOMPLETE=0、UNKNOWN=0，才回報日常列表完整。回報實際 GUI／Save All／取消次數、下載張數、ImageIO 張數與狀態、完整性、阻塞及唯一下一步；未實測標 NOT_TESTED，不宣稱正式 AUTO PASS。

不要發訊息、刪除或覆寫舊照片、變更受保護 state、操作其他群組、push／merge 或啟動雲端 CI。前景被我使用或中斷時停止 GUI 輸入，先保存紀錄。
```

## 照片和紀錄存在哪裡？

每個群組建議使用不同資料夾。資料夾內的 `albums` 保存照片，每次下載各有獨立目錄；`backup-records/group.json` 保存本地群組識別，`backup-records/events` 保存逐本盤點、intent、結果及完成證據。

這些紀錄跟著備份位置保存，不只存在聊天記憶或 `/tmp`。同一群組改名、中文辨識少一個字，不會因此自動建立另一組完成紀錄；不同群組也不能因日期／張數相同就共用紀錄。仍無法判斷時，Agent 會請你確認當前畫面與既有紀錄的對應，不需要你輸入完整名稱。

## 如何知道全部完成？

Agent 必須實際從頂端走到底端，頁與頁有重疊，同一張卡片只計一次。最後還要確認末卡並再次向下捲動沒有位移。照片下載視窗消失，或 AX 顯示很多列，都不代表全部完成。

查看 Agent 的逐本結果：已完成、排除、未完成、未知、受保護歷史。只有全部都有對應、`PROTECTED_HISTORY=0`、未完成和未知均為零，才可回報 `ALL_ELIGIBLE_ALBUMS_BACKED_UP=PASS`，並附本次盤點時間與範圍。PASS 僅表示 Agent 提交的日常簿記完整；summary 同時標示 `evidence_role=AGENT_ATTESTED_OBSERVATIONS`、`sensor_verified=false`、`real_line_e2e=NOT_TESTED` 和 `pass_scope=AGENT_ATTESTED_ACCOUNTING_ONLY`。它不是工具驗收或實機 LINE E2E，也不等於正式 AUTO VERIFIED，且不保證之後新增的照片已備份。

需要時請 Agent 用現有 `daily summary` 入口讀取進度；一般使用者不必編輯 JSON。

## 中途停止後怎麼繼續？

告訴 Agent：「停止新增下載，保存目前進度。」再次啟動時，使用相同備份位置並交回相同群組相簿列表。已完成相簿直接跳過，不重新下載。

未完成相簿的原檔與紀錄全部留下。Agent 必須先確認舊下載已終止、知道前次操作的結果，再向你提出該本的恢復授權。你同意後，它使用另一個新空白目錄重下該本；原目錄仍保留。

若不知道「儲存全部」是否送出，狀態是 UNKNOWN。明確記錄的 UNKNOWN 不可再由一般 outcome 改成 STOPPED／NOT_SENT，也不能因換 Session、換資料夾或再次下指令就重送。只有 intent 尚無 outcome 時，才可記錄第一個實際已知結果；前次明確終止仍須該本 Owner 恢復授權和正式交易 gate，才能在新空白目錄恢復。也不假設 LINE 能只補少掉的幾張照片。**相簿級恢復就是目前正式功能基準，照片級續傳列為未來研究。**

## 如何排除或換群組？

排除時提供足以區分相簿的描述，例如日期、張數、封面或用途。Agent 核對後保存原因；下次沒有重填排除項，也不會自動取消舊排除。

換群組前先安全停止舊任務，再打開新群組相簿列表、指定另一個備份資料夾，貼相同 Prompt。不必輸入群組名稱。不要讓 Agent 同時操作兩個群組，也不要刪掉前一群組的完成紀錄。

## 常見狀況

| 狀況 | 怎麼處理 |
|---|---|
| 你正在用電腦 | 先讓 Agent 做離線檢查；它需要前景時再交接。 |
| LINE 顯示登入畫面 | 你自行登入並開到正確相簿列表，再交回前景。 |
| 外接磁碟未掛載 | 先接好磁碟，確認真正目的地；Agent 不改存其他地方。 |
| 目的地已有別群組紀錄 | 停止，改選正確位置；不覆蓋群組識別。 |
| 找到舊照片但沒有完成證據 | 先唯讀核對，不當作未備份而重下。 |
| 主畫面看不到選單 | Agent 先查獨立 popup，不能連續盲點。 |
| 張數不足或 ImageIO 失敗 | 留未完成及全部原檔，不跳過錯誤後宣稱完成。 |
| 缺正式授權簽發入口／外部審查 | 保存核准資料，停在儲存全部之前；不修改 false 或繞過 gate。 |

## 之後搬到開發專區

本輪先整理與修正可攜路徑，**不替你搬移專案**。預定新位置為 `~/dev/Line_backup/`。停止所有下載與寫入後，先保留完整封存，再搬移，並從新位置啟動 Codex。`tests/formal_reconciliation_driver.py` 以自身檔案位置推導 repo root；正式 project、destination、group key、日期與張數必須由操作者明確提供，不含可直接沿用的私人預設值。

程式和一般文件使用 repo 相對路徑；歷史 state、照片目的地、grant 和 runtime 綁定可能仍含舊路徑。不能全域搜尋取代，或把已關閉 grant 搬過去重用。搬移後先做唯讀路徑檢查與本地 fixture 測試；正式執行仍需新 root 的正確設定、來源／runtime 綁定及有效授權。備份照片放在外接磁碟時，搬專案不代表要搬照片。

## 驗證限制

PR28 有多本真實 Save All、檔案 SHA-256 與完整 ImageIO 成功案例；PR32 有實際列表捲動與詳細頁核對。10/24 私有 batch summary 記載新增 19 本、1,555 張通過 ImageIO；本輪只讀紀錄，沒有重驗這些舊照片。

這些歷史成果不能直接推導新群組 51 張案例、全列表遍歷、相簿級中斷恢復或新授權路徑已實機通過。本輪狀態以 [完整報告](../harness-development/foreground-album-repair-20261025/E2E測試報告.md) 為準；正式 AUTO 的外部審查及獨立 E2E 仍未完成。
