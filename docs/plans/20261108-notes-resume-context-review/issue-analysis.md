# 記事本接續停在 bind：單一根因診斷

## 本角色結論

**`ANALYSIS_COMPLETE`；唯一建議路線為 `TARGETED_DIAGNOSTIC`。原備份仍為 `BLOCKED`。**

本輪選定根因 `NOTES-BIND-CONTEXT-OMITTED`，只解釋前次 `bind` 的 `WRONG_NOTES_CONTEXT`。目前帳本具有非空 `context_id`；現行程式在呼叫省略該參數時，以預設 `None` 與帳本原值比較並拒絕。這個輸入條件與提報的失敗相符。前次完整 argv 沒有保存；「漏傳」來自當時轉錄及提報，本輪沒有重跑真實 bind，不把轉錄冒充原始工具日誌或動態重現。

Owner 持續使用同一裝置，與 filesystem device 數值改變並不矛盾。`st_dev` 沒有硬體永久序號的語意；目前沒有歷史 OS 證據足以確定變動原因。同 inode 也不能單獨證明跨不同 device 的物件相同。device 漂移是後續仍須查證的獨立條件，不能用它解釋這次較早發生的 context 比對拒絕。

下一個最小動作是：由 Owner 重新透過手冊的記事本正式日常入口交接，讓 Agent 核對當次列表後，帶入帳本原有 `context_id` 完成當次 bind，再取得一次 `reattest preview`，保存輸出後停止於 confirm 前。這是待人啟動的診斷建議，**本輪未執行，也不保證 preview 通過或備份已可繼續**。

## 輸入、候選與角色範圍

| 項目 | 本輪綁定 |
|---|---|
| 角色 | Owner 指定的 `06_high_reasoning_review_prompt.md`；僅診斷 |
| 交接提報 | `docs/notes-backup-resume-issue-20261108.md` |
| Repo／分支 | `Line_backup`／`feature/line-notes-media` |
| 起始精確 HEAD | `e07d8f7257867522c74d9395dd7e80d01ce05517` |
| 即時遠端核對 | `git ls-remote` exit 0；同分支遠端 HEAD 與上述值一致 |
| 起始 Git 狀態 | `git status --porcelain=v1` exit 0、空輸出；已檢查 worktree 清單，未操作其他 worktree |
| 目前產品版本 | 包含 `15b919b` 的一次 list-directory reattest；不能沿用舊版「沒有 reattest 入口」的結論 |
| 獲准內容 | 閱讀提報與所列本機證據、公開技術來源研究、保存診斷與提交可公開報告 |
| 停止邊界 | 不操作 LINE、不改產品／Skill／帳本／active hint、不建立 attempt、不執行建議、不啟動下一正式角色 |

repo 內無同版本 policies，使用全域 `policies/v4.9.0/workflow-routing.md`、`subagent-model-policy.md` 與 `role-report.template.md`。沒有啟動或恢復退役 controller。

原始診斷產物保存在專案私有任務目錄 `.local/line-backup/tasks/notes-resume-context-review-20261108/`。本報告是可公開版本；不含群組／人名、媒體原名、帳本識別值或原始 AX。私有 `source-map.json` 提供提報所指各項證據的絕對路徑與 SHA-256。

## 最小時間線與證據強度

| 次序／來源 | 可核對內容 | 邊界 |
|---|---|---|
| 帳本 #1 `created`、`list.json` | 保存非空 context 與舊 directory device／inode；兩處 context 相同 | 本輪直接讀取原 JSON，不是新建資料 |
| #10–#17 | 一項 v2 intent 已有 completion | 保存的完成事實；本輪未重驗媒體或解碼 |
| #18–#19 | 另一項 v2 intent 已記 `outcome=UNKNOWN` | UNKNOWN 仍存在；不推定已停止 |
| #20–#21 | 既有 session binding、restart confirmation；context 與目前 list.json 一致 | 舊同意不是本次 reattest 同意 |
| #22–#28 | restart 後的 scan、page、post、media 記錄 | 不是本輪完整盤點或 GUI 覆蓋驗證 |
| 前次 progress／followup | bind 回覆 `REFUSED`、`WRONG_NOTES_CONTEXT`、exit 4，並記錄漏傳參數 | 人工整理的轉錄；缺完整 argv 與原始 receipt |
| 前次 AX／statement／bundle | 有當時記事本前景與交接的說明 | AX 只有通用 row；沒有保存當次 screenshot，不能在本輪獨立重驗列表身分 |
| 本輪靜態觀察 | 仍為 28 個事件、1 completion、1 UNKNOWN outcome、1 restart confirmation；0 reattest、0 activation | JSON 計數，不等於重跑 `summary` 或完整 evidence-audit |
| 本輪 `lstat` | 舊新 directory device 不同，inode 數值相同，與提報方向一致 | 只讀該目錄 metadata，沒有讀媒體內容；完整 witness 未查 |

前次 `COMPLETED=1`、`UNKNOWN=1`、`LOCAL_CHANGED=1` 是其 progress 記錄的摘要投影，本輪未重新執行可用性檢查。前次 audit exit 0／28 events 同樣是轉錄結果，不能列為本輪 audit PASS。

### 最小失敗條件（靜態推導，未執行）

1. 已有帳本的 `context_id` 為某個非空字串 C。
2. 呼叫 `bind` 時省略 `--context-id`；argparse 的值與方法預設值都是 `None`。
3. `NotesRecords.bind()` 在 `notes.py:2478–2480` 比較 `None == C`，拒絕 `WRONG_NOTES_CONTEXT`。

以原值 C 呼叫，只會消除此項比較失敗，不能推論證據、session、目錄 witness 或後續派送 gate 一定通過。本輪沒有用真實帳本重試來補造重現。

## 因果說明、替代解釋與可推翻條件

| 解釋 | 證據判斷 |
|---|---|
| 呼叫漏傳已有 context | 原始碼與實際帳本條件支持；當時轉錄也如此記錄。歷史 argv 未獨立確認 |
| Owner 沒有交接／目前必是錯列表 | 該錯誤碼不檢查真實 GUI，不能由 context 拒絕推出這些結論；下次仍須重新確認入口 |
| device 改變造成這次 WRONG_NOTES_CONTEXT | bind 的此比較不使用 device；目錄 device gate 另在 `notes.py:2502–2521` |
| 需要放寬 CLI 的 context guard | 沒有證據支持。guard 正在執行既有身分契約，不應自動補值掩蓋呼叫缺漏 |
| 新增通用 attestation 架構才能接續 | 現行候選已有 preview／confirm，尚未取得這份真實帳本的 preview；目前不支持擴架構 |

若找到完整原 argv 證明已傳入與當時帳本完全相同的原值，或找到不同候選版本／當時 list.json，漏傳的歷史歸因就須重評。若新 bind 在正確 context 下仍拒絕，保存原始回傳並停止；不把新的 reason 併成本根因，也不直接修產品。

## 同裝置為何仍可能變號

Apple 將 `st_dev` 定義為檔案所在的 device ID。Python 將 `st_ino` 的唯一性限定在給定 `st_dev` 之內。因此這組值不是電腦或硬碟永久序號；跨 device 相同 inode 不足以證明同物件。[Apple stat(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html)、[Python os.stat_result](https://docs.python.org/3/library/os.html#os.stat_result)。

Apple 的 XNU 原始碼把 filesystem 提供的 `va_fsid`／`va_fileid` 填入 `st_dev`／`st_ino`；另有執行期 fsid 配號及 storage device minor ID 分配機制。這支持「同硬體但執行期配號改變」作為可查候選，沒有證明本機 APFS 曾走哪條路徑。[XNU vfs_vnops.c](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/vfs/vfs_vnops.c)、[XNU vfs_subr.c](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/vfs/vfs_subr.c)、[IOMediaBSDClient.cpp](https://github.com/apple-oss-distributions/IOStorageFamily/blob/main/IOMediaBSDClient.cpp)。

| 可檢查候選 | 需要的辨別證據 | 本案判定 |
|---|---|---|
| 重開機、重新發布 media 或重新建立 mount 後重新配號 | 事件前後的 boot／mount／device mapping 記錄 | `UNKNOWN`；不能把重掛載寫成已發生 |
| 同一路徑在不同時點指向不同 filesystem／volume | 兩時點的 canonical path、mount 及持久 volume 身分資料 | `UNKNOWN`；現在才查一次不能回推出過去 |
| 目錄替換、內容相符的 clone 或其他物件變動 | 完整舊新 witness、來源沿革及精確人工決策 | 本輪未核對；相同 inode 無法排除 |

Owner 的同裝置說明保留為使用者陳述／`OBSERVED`，不擴成「同一實體 volume 已驗證」。上述公開原始碼是研究時讀取的上游版本，沒有建立與本機 Darwin binary 的逐位元對應。本輪不為追查 OS 根因新增重掛載實驗、改寫 device 值或導入新 volume-ID 架構。

## 既有指引是否有缺口

**有一個具體的文件提示缺口，尚未證實產品程式缺陷。** `download-and-ledger.md:66–67` 與 bind help 只列可選 `[--context-id ID]`；啟動節雖說明 identity 與 bind 順序，未明說「既有帳本有 context 時，bind 必須回填同一原值」。`memory` 已輸出該欄位（`notes.py:5366`），無須新增查詢介面或放寬 guard。

若 Owner 後續另行交辦指引小修，最小內容應是：「完成列表身分核對後，從相符帳本的 memory 取得 context_id；非 null 時將原字串傳入 bind，不裁切、不重新產生；為 null 才省略。缺少欄位、無法對應列表或比對不明即停止。」context 相同本身不證明 GUI 列表身分，也不是下載授權。

這是診斷 finding，沒有在本輪改 Skill、references、help 或手冊；不能據此聲稱其他模型從相同入口必然成功。單次漏傳也不足以把整份 Skill 判為可靠或不可靠。

## 歷次嘗試與新增學習

| 已知活動 | 對本根因的學習／次數界線 |
|---|---|
| 較早的 v3 intent 因 directory device 不符拒絕 | 屬不同根因；保留舊分析與三次上限歷史，不挪用為本次 bind 嘗試 |
| 本次提報前的一次 bind 拒絕 | 知道具體 reason；完整 argv 未保存。現有交接只列此一次，不宣稱全歷史沒有其他嘗試 |
| 拒絕後唯讀原始碼核對 | 找到條件性必要參數；沒有再派 bind 或下載 |
| 本輪來源／metadata／help 核對 | 確認目前候選、context 一致、preview 命令已存在，以及原始證據界限；新增執行嘗試為 0 |

不因換 Session 或換模型重置根因嘗試歷史。未授權本輪重試；後續若連續兩次沒有新資訊，依專案規則停止，不為用滿三次而重送。

## 唯一建議路線：TARGETED_DIAGNOSTIC

**範圍：同一帳本、同一列表、既有目的地與 OPEN_BATCH；僅完成當次綁定並取得 preview。**

- 由 Owner 使用 `docs/LINE相簿備份_使用手冊.md` 的記事本正式日常 Prompt 重新交接當次前景，將本次診斷附作「到 preview 即停」的邊界。不要求改用 Acceptance／E2E Prompt，也不要求 Owner 填 UUID 或 JSON。
- Agent 自行查全部帳本與相符 memory，核對當次連續入口、可辨識的列表內容與有效前景；不能僅憑中文名稱、舊 statement、舊 session 或 context 字串認領列表。
- 使用當次 observation／handoff bundle、新 session 與原 context 值執行一次 bind，保存 argv、stdout、stderr、exit。**bind 會追加 binding、保存 evidence 並寫 active hint，不是純唯讀命令；需在後續實際任務授權內執行。**
- 成功後執行一次 `reattest preview`，將完整 JSON、exit、候選版本與前後 ledger tip 保存於私有任務區；preview 本身不追加帳本事件。此處停止，不 confirm、不 scan、不 intent。

**成功檢查：** bind 不再因 context 拒絕；preview exit 0 且輸出完整。`CONFIRMATION_REQUIRED` 只代表可交付精確預覽，`NO_CHANGE` 只代表當次不需此轉接；都不代表備份完成或授權派送。UNKNOWN、原 completion、restart scope／generation 不得被改寫，preview 前後帳本內容不得改變。

**停止條件：** 入口／帳本歧義、任一拒絕／exit 70、witness 不完整、額外／缺失／異動項、不支援布局、scope 或候選版本改變、再次 device 漂移，均保留證據交 Owner；不換目的地、舊 session 或入口繞過。這條路線未執行，不新增失敗嘗試。

**後續人工決策：** 若 preview 要求確認，Owner 必須針對該 preview digest、舊新 binding、witness 與剩餘風險另行明示同意。既有 restart 同意與本報告均不能替代。只有之後成功 confirm 並完成新的完整 recovery scan，才可能按原 OPEN_BATCH 逐項恢復、驗證及 activation；這是既有協議的條件說明，非本輪授權、結果或第二條建議路線。尚有未解項時不得稱整份列表完成。

## 本輪實際檢查與證據

環境：repo 根目錄；macOS 27.2／Darwin 27.2.0 arm64、`/usr/bin/python3` 3.9.6、Node v24.22.1。下表只列實際執行的檢查；私有輸出見同任務目錄。

| 實際命令／操作 | 結果／證據 |
|---|---|
| `git status --porcelain=v1`、`git branch --show-current`、`git rev-parse HEAD`、`git ls-remote --exit-code origin refs/heads/feature/line-notes-media` | 各 exit 0；`preflight.json` 保存逐命令原輸出 |
| Python 讀取指定 JSON／statement、比對 context、計數 events、對 list directory 執行 `Path.lstat()` | exit 0；`ledger-metadata-observation.json`；未讀媒體 bytes |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；`cli-help-checks.json` |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes bind --help` | exit 0；同檔，列出可選 context 參數 |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes reattest preview --help` | exit 0；同檔；這不是執行 preview |
| 原始碼／references 行號查讀與來源 SHA-256 | exit 0；`public-source-hashes.json`、`source-map.json` |
| 受保護來源前後雜湊、公開文件／允許路徑／敏感字串／whitespace 核對 | 最終結果見 `document-checks.json`；只證明本次文件與資料保全範圍 |

本輪未跑 unittest、合成 bind 重現、evidence-audit、真實 bind／preview／confirm、新 scan、intent、下載、chooser、解碼或跨 Session E2E，全部 `NOT_RUN`。歷史報告中的測試 PASS 不算本輪結果。

| 公開來源 | SHA-256（起始候選） |
|---|---|
| 提報單 | `2ddc4a462f4b479f09eb65920f09febd299d228f367c0f672194cc7530f5a680` |
| `src/line_backup_batch/notes.py` | `0e542d73024f8f1b78238dcb9b331d890c89223281c5543f8acf45b7135aed7b` |
| 記事本 `SKILL.md` | `bdb50e3c953918bfcc02e45fd8d403e9f360ab79cfa8f910afd3391a79f60afa` |
| `references/download-and-ledger.md` | `2ff4fc22bfd4ac6fc0fdeb85e61f6fc68b7080d227659beb6a2f31a354a595dc` |

一位沿用主 Session 設定的同角色助手研究公開 Darwin／Python 來源，未參與正式接受。交付完成後，依 Owner 明示另請求 `gpt-6-luna` 提交訊息助手；其模型請求、平台回傳與 provider usage 分層記錄在私有交付 receipt，不用設定檔或請求參數宣稱實際後端身分。助手不啟動下一正式角色，亦不能授予獨立接受。

## 六項狀態與人工交接

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE; ORIGINAL_BACKUP_BLOCKED
IMPLEMENTATION_STATUS: NOT_APPLICABLE_THIS_ROLE; PRODUCT_AND_RECORDS_UNCHANGED
CORE_ACCEPTANCE_STATUS: NOT_RUN; BACKUP_NOT_RESUMED
REQUIRED_VERIFICATION_STATUS: PASS_METADATA_SOURCE_AND_HELP_CHECKS_ONLY; PRODUCT_AND_REAL_ENVIRONMENT_CHECKS_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: NOT_DONE; AWAITING_HUMAN_START_OF_BOUNDED_DIAGNOSTIC
```

本輪交付止於此診斷、可公開文件與 Git checkpoint。完整提交訊息、push 後遠端精確 HEAD、文件檢查及助手派送結果另存私有 `delivery-receipt.md`；推送成功不代表下一步已執行、外部審查完成或原備份結案。
