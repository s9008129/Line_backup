# 記事本列表目錄 device 綁定：根因分析

## 本角色結論與範圍

**角色結論：`ANALYSIS_COMPLETE`；產品問題仍 `BLOCKED`。**

選定根因為 **NOTES-LIST-DEVICE-PERSISTENCE**：把列表容器建立時的 `st_dev` 作為後續各次操作的必要恆定值；現有重新見證只接受已有 restart 批次的狀態，首次下載無可用路徑。這可確認是本次拒絕的程式原因；作業系統為何回傳不同 device 值仍是未知。

本輪按 Owner 指定的 `06_high_reasoning_review_prompt.md` 做診斷，未實作修正。該角色明文要求 “This is diagnosis only: do not modify product files, execute the recommendation”，並要求交付後停止。Owner 同則提出修復目標及 add／commit／push；本輪完成診斷與可公開報告的 Git 交付，不自行切換成 Implementer，也不把審查報告稱為修復成果。

本報告是遮蔽版。未包含群組、人名、私人目錄、貼文內容、媒體檔名、原始 GUI 或帳本識別碼。完整來源與診斷原件由 Owner 在專案私有任務目錄保存。未啟動 LINE、未輸入 GUI、未重跑真實 intent／reattest，也未改寫帳本、active hint、照片、Skill 或 AGENTS.md。

## 候選與輸入身分

| 項目 | 已核對內容 |
|---|---|
| Repo／分支 | `Line_backup`／`feature/line-notes-media` |
| 受分析 HEAD | `5c3b937b1a2ca2bc3321777a5fd8d7fcacbd088c` |
| 起始遠端 | `git ls-remote origin refs/heads/feature/line-notes-media` 與上述 HEAD 相同 |
| 起始工作樹 | 沒有 tracked 差異；一份既存未追蹤 Owner 檔案，原樣保留、不 stage |
| 來源提報單 | `problem-report-notes-directory-device-binding-20261111-180522.md`；SHA-256 `9345ec3b965815b0ec18e9d56d6ee7e0656bbd7df4f9e17470c30bb8be5012da` |
| 拒絕原件 | `attempt1-intent.json`；SHA-256 `77001aad372b575d058de01acc77c75c6fd7fdc866d85993296f601599d4174a` |
| 盤點及拒絕後摘要 | 兩份原件 bytes 相同；SHA-256 `456ff7393b09e5efe936a46df33d2eb6aa7443dd090dd19d7f8ae09dcee565a4` |
| 診斷環境 | macOS 27.2／26B123／arm64；`/usr/bin/python3` 3.9.6；Node v24.22.1 |

輸入已足以分析此一 gate：Owner 意圖、失敗描述、來源、目前版本及先前修正均可定位。沒有核准此新修正的有界實作計畫；既有 v3 計畫明列 device／witness 協議不可順手變更。這不阻止診斷，但影響下一步路由。

## 最小時間線與證據層級

| 階段 | 可確認內容 | 證據／限制 |
|---|---|---|
| 建帳 | created 保存列表路徑與 device／inode | 讀取本次指定帳本的事件；不掃描其他私人列表 |
| 本次 Session 綁定與盤點 | 2 篇貼文；5 張照片；另一篇為 `NO_MEDIA` | 事件與已保存摘要；GUI 內容是前次 Agent 的觀察紀錄，本輪沒有親自重新觀察 |
| 首次 intent | `REFUSED / CURRENT_NOTES_LIST_DIRECTORY_CHANGED / dispatch_authorized=false` | 直接讀取拒絕 JSON；歷史退出碼 4 見提報及 progress，未找到獨立 shell receipt，故不冒稱本輪實測退出碼 |
| 拒絕後 | `COMPLETED=0`、`PENDING=5`，其餘四類為 0；無未解 attempt／OPEN_BATCH | 摘要與 16 筆事件一致；事件只有 created、binding、scan、page、post、media |
| 本輪唯讀 metadata 核對 | canonical、非 symlink、目錄為空；路徑與 inode 相符，device 不相符 | 當次直接 stat；不讀取照片內容；精確私人值留私有報告 |
| 本輪隔離重現 | 正常值能完成一項及下一項 intent；歷史 device-only 差異即拒絕 | 未修改產品，沿用既有 synthetic fixture；詳下節 |

事件中沒有 intent，支持「此帳本未建立下載交易」；前次 Agent 記錄未按下載控制、未操作 chooser。帳本本身不能證明使用者或外部程序從未做過其他 GUI 操作，故不把事件缺席寫成全系統未派送的證明。

## 第一性原理與因果鏈

產品要保證三件不同的事：選對來源及授權目的地、避免重複派送、保存已完成檔案的完整性。列表目錄的 metadata 是輔助證據；它不承擔 GUI 來源辨識，也不取代追加式交易歷史。

`st_dev` 描述檔案所在的裝置／檔案系統，並非 Mac 硬體序號。[Apple stat(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html) 沒有保證它是跨 Session 永久業務身分。另一方面，inode 的唯一性有檔案系統範圍；把 device 拿掉後，同一 inode 數字不能單獨保證同一物件，參見 [GNU C Library 的檔案屬性說明](https://www.gnu.org/software/libc/manual/html_node/Attribute-Meanings.html)。這是修正需要明確信任邊界的理由。

本次程式因果鏈可確認如下，行號綁定上述 HEAD：

1. `notes.py:233` 的 `directory_info` 取得當下 device／inode；前後相同的檢查保護的是同一次讀取，不應與長期綁定混為一談。
2. 建帳 `:686–708` 將兩值存進 created。`_current_destination_state` 與 `_effective_list_binding` 決定目前適用綁定；不是每次 Session bind 都重設目的地。
3. `intent → _require_current_list_directory`（`:4806`、`:2522–2542`）要求舊 device／inode 與現在完全相等。本次只有 device 條件不成立，因此在建立 staging／intent 之前拒絕。
4. `reattest preview` 在判斷 `NO_CHANGE` 之前先呼叫 `_reattest_open_batch`（`:3033`）；沒有 restart-confirm 就回覆 `REATTEST_OPEN_BATCH_REQUIRED / NO_OPEN_BATCH`（`:2636–2640`）。device 有變時還需要 completion witness，首次下載也沒有這份證據。
5. 因而產生完整覆蓋缺口：合法首次派送遇到 device-only 差異時，既無普通路徑，也不符合為「既有資料轉接」設計的恢復路徑。

**根因是檢查責任與時間範圍混用，加上首次狀態覆蓋缺口。** 不是沒有完成盤點，也不是 LINE 下載、影片解碼、chooser 或 Agent 忽略既有停止規則。程式沒有宣稱在驗硬體序號；問題在於長期相等條件的實際效果，不應將未出現在程式中的意圖當成事實。

## 先前嘗試及新資訊

| 既有工作 | 學到什麼 | 本次適用性 |
|---|---|---|
| `81d9db40a702a145cd2e2e9004cc01ce6df912e3` 初始流程 | 引入目的地與交易的 device／inode 紀錄 | 目前 gate 的來源 |
| `d7e8cfe81109ee6e3b8cb776d92b5d1be16b5a98` preview | 可唯讀見證既有批次的 device-only 漂移 | 不涵蓋零 attempt |
| `15b919bfcb475d1b088d8776cf7123f7456eebbe` confirm | 可追加一次精確轉接，保留歷史 | 仍要求 OPEN_BATCH 與 witness |
| 後續 v3 環境附屬項修正 | 讓合格 `.DS_Store` 不冒充媒體／交易內容 | 明確保留 device／witness 協議；本次目錄為空，不是附屬項造成 |
| 前次日常任務 | 提報稱遇到反方向 device 差異，當時有 OPEN_BATCH，後來另遇影片 stderr | 本輪只核對所交報告及程式歷史，未重開另一真實帳本；不得把影片問題算成本根因 |
| 本次日常任務 | 第一次下載無可轉接批次 | 新的狀態組合；不是要求再做同一 reattest |

上述是同根因的歷史；不因本輪換 Session 而重置。舊 preview／confirm 是分期能力，不等於兩次失敗修補。提報未提供所有歷史現場嘗試數，故完整累計 `UNKNOWN`；本輪未再對真實資料執行任何修復嘗試。

## 本輪實際診斷與命令

在 repo 根執行：

```sh
PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/<本次私有任務>/directory-binding-review/diagnose.py
```

上式公開版本遮蔽任務識別碼；可直接執行的完整命令與 stdout／stderr 在私有 `issue-analysis.md`。未改產品，僅使用 `tests/test_notes_reattest.py` 的既有 fixture，建立兩份會清除的隔離 synthetic 帳本；active hint writer 以 fixture mock 隔離，不寫真實 active hint。只在 synthetic 帳本重建歷史 device 值，沒有調整真實掛載或事件。

| 執行 | 結果 | 範圍 |
|---|---|---|
| 診斷腳本第 1 次 | exit 1，讀到未載入的 fixture instance 屬性 | 診斷 harness 問題，不是產品內部錯誤 70 |
| 第 2 次 | exit 1，改用內部讀取仍需先載入 | 學到 helper 重開 instance 後需 `summary()`；兩次原始 stderr 均保存 |
| 第 3 次 | exit 0，`PASS_SYNTHETIC` | 修正診斷腳本，未改產品；不再重跑 |
| 無漂移對照 | 1 completion、2 intents | production 解碼器用 fixture verifier 替代；不等於照片可解碼或 GUI 成功 |
| device-only 漂移 | intent 拒絕；reattest `NO_OPEN_BATCH` | 拒絕前後 synthetic 事件及列表 children 不變 |
| 來源保護 | 131 個來源檔案 SHA-256 前後相同 | 包括本次真實帳本檔案、索引、active hint、原提報／progress、產品 Python、notes 測試及既存 Owner 未追蹤檔；不代表全磁碟原子快照 |

診斷 stdout SHA-256：`7989350892089cc5f450dbbb584fd29957764daa1da899d4e64966b3e24da2c6`。診斷腳本 SHA-256：`0242a9bf5b2c0dbc4ebee34b4eacc47aae46dee39e61cd888cba18c333508a68`。完整產品回歸與真解碼 `NOT_RUN`，因為本輪只分析、不改產品。

Git 身分、歷史及狀態命令已執行：`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git worktree list`、`git log`、`git show -s`、`git diff --quiet`、`git ls-remote`，相關有效命令 exit 0。探索不存在的 `docs/reviews` 曾由 rg 回報錯誤，未以它推導產品結論。未使用其他版本 controller，也未聲稱平台隔離或獨立接受。

## 替代解釋與可否證條件

| 解釋 | 判斷與可否證條件 |
|---|---|
| 只有 device 條件造成當前拒絕 | 已由程式分支、當次 metadata 及隔離正負例支持；若路徑／inode／型態也不符，或實際使用別一 binding，則需推翻或擴充此判斷 |
| 本機硬體被更換 | 沒有證據；Owner 表示未更換屬 `OBSERVED` 的人類陳述；device 變化不能證明換硬體 |
| 相同路徑和 inode 就是原資料夾 | 只能作連續性推論；另一檔案系統可能有相同 inode，不能據此宣稱零風險 |
| macOS 重掛載／虛擬存取層造成 | 可能，但缺少兩時點 mount／volume 及程序環境記錄，保持 `UNKNOWN`；本次不為此拆裝磁碟或擴大環境調查 |
| 恢復功能壞掉 | 現有實作符合 OPEN_BATCH／witness 合約；缺的是首次狀態路徑，不能靠捏造批次解決 |
| 只放行第一筆 intent 即可 | 不成立：verify 的 `_validate_staging`（`:5467`）及發布會再用同一列表 gate；第一筆事件寫入後仍將撞上舊 device |

## 唯一建議路由：`PLANNER_REPLAN`

**由 Owner 另啟有界計畫修訂，僅重定義「列表容器」歷史 device-only 差異的處理；不要重做整套備份架構。** 本輪不啟動下一角色。選此路由是因既有 v3 計畫明文保留 device／witness 協議，而本次確實改變目的地信任政策；不是為補角色順序而製造新工作。

給下一角色的具體方向已可審查：普通列表容器的歷史 device 值不應單獨否決本次已核對的授權路徑；保留 canonical 路徑、授權根目錄、非 symlink、inode 與列表身分核對。不另加首次下載 reattest、永久 marker、volume registry 或一般化身分框架。所有舊事件保持原 bytes，新的 staging 照現有 intent 記錄當下 device／inode。

### 必須分開保護的物件

| 物件 | 後續方案要保留的檢查，位置綁定本次 HEAD |
|---|---|
| 同一次讀取／原子操作 | `:233–242` 的前後 device／inode；`:470` 的同檔案系統要求及 link 身分 |
| 新 staging | `:4856–4882` 的唯一空白目錄及當下 metadata |
| 舊 staging | `:5459–5469` 與原 intent 的 device／inode、父目錄歸屬 |
| completion／active version | `:4210–4286`、`:4051–4081` 的檔案／目錄、metadata、hash 與內容保護 |
| pending 發布 | `:5675–5703` 的原交易／來源快照與不覆寫保護 |
| UNKNOWN／活動下載 | `:4833–4855` 等原有禁止重送規則；不因列表 gate 調整解鎖 |
| 曾 reattest 的列表 | 既有一次性、再次漂移停止、fresh recovery scan、scope／generation 合約；不把普通路徑變成轉接後漂移的旁路 |

列表 gate 在 `:4710`、`:4806`、`:5467`、`:5473`、`:5592`、`:5642`、`:5932`、`:5950`、`:6009` 被共用。後續方案要有一致規則，不能只在某一次呼叫跳過 device。

### 有界可寫範圍與成功檢查

待計畫核定的產品範圍限 `src/line_backup_batch/notes.py` 的列表容器判定；測試沿用 records／reattest／restart 的既有 fixture。Skill 及 references 只修與已核定行為衝突的說明。Owner 要求的 AGENTS.md 原則應聚焦「非危害性 metadata 不單獨阻擋、檢查說清保護物件」；不要將「只有能證明重大危害才停止」擴成工具拒絕、身分不明或資料完整性失敗都可由 Agent 主觀略過。日常 Prompt、CLI／schema、六類狀態、相簿與實際資料都不在此最小修改範圍。

最低成功證據是「新列表、零 attempt、device-only 歷史差異」的完整合成業務路徑：第一項 intent → outcome → verify／發布 → completion 讀回 → 新 Session 保留完成與禁止重下 → 第二項可 intent；並保留 inode／symlink／越界、UNKNOWN／pending、舊 staging／completion／active 漂移、曾 reattest 再漂移的拒絕負例。兩項完成及列表摘要對帳宜沿同一 fixture 完成，避免只測首 gate。現有 `prepare_batch` 一定先建 UNKNOWN 及 restart-confirm；`include_completion=False` 仍不是本案的零 attempt 情境。

後續產品候選需跑 AGENTS.md 的三條最小回歸；必要獨立審查由 Owner 按新計畫風險啟動。真實能力確認仍由 Owner 使用手冊中的記事本正式日常 Prompt 與有效前景交接，不增加日常啟動步驟，也不以此報告或合成結果替代實機。

**停止條件：** 若需要改寫歷史、解除舊 UNKNOWN、放寬已完成／pending／active 的 device 檢查、改 schema、增加持久 binding、擴大到 inode／路徑漂移，或無法保留既有 reattest 合約，立即回報超界，由 Owner 決定；不得靠新目的地、空帳或捏造 OPEN_BATCH 繞過。

**需人決定：** 是否接受「同一授權路徑及列表證據充分時，列表容器的 device-only 差異可容忍」的明確剩餘風險，並以此修訂原計畫的限定條款。這不等於接受所有 metadata 漂移；過去對既有批次 clone 風險的同意也不自動擴張至新政策。

## 六項狀態與交接

| 狀態 | 結果 | 範圍 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `BLOCKED` | 指定列表尚未完成下載；本角色分析為 `ANALYSIS_COMPLETE` |
| `IMPLEMENTATION_STATUS` | `NOT_RUN` | 產品未修改，只有診斷及報告 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN` | 未對新產品候選做接受檢查 |
| `REQUIRED_VERIFICATION_STATUS` | `NOT_RUN` | 修正候選的完整回歸／真實檔案驗證未執行；本輪隔離診斷另記 `PASS_SYNTHETIC` |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | 同角色助手不構成獨立接受 |
| `TASK_CLOSURE_STATUS` | `NOT_DONE` | 等待 Owner 決定有界修訂與下一角色 |

研究助手僅做程式影響點及測試覆蓋的唯讀梳理，未執行測試或寫檔；主代理整合證據並對結論負責。依 Owner 指定另請 GPT-6-luna 梳理提交訊息；模型請求、平台顯示與供應商 usage 分開記錄於私有交付證據，不宣稱未取得的後端身分、成本或節省量。

交付本報告後停止。本報告不代表修正已實作、計畫已核准或任何接受關卡 PASS。
