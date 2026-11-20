# 記事本 S3b GUI／B1 文件與 C5 整合報告

## 角色、授權與精確版本

本輪以 Implementer 身分完成核定計畫的 S3b 文件切片與 C5／R1–R10 整合
報告。範圍只含記事本 Skill／references 的來源、就緒、chooser、提示、檔名
及已展開卡片契約，以及既有 S1／S2 行為的證據對帳；沒有修改產品程式、
CLI、schema、事件或真實資料。

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`
- Branch：`feature/line-notes-media`
- 起始本機與遠端 HEAD：`72132263ce25aa55e3e6f48626f5c3a73f938fad`
- 核定 plan：`docs/plans/20261102-notes-fieldtest-review/plan.md`
  - 提交：`75d4053332aa518a3e91e67b03dbd611e5efaf72`
  - SHA-256：`d13b492c0dbd98bbad7522ab5a475692067571e507d1b5d9de10da6c0614c899`
- 現行 handoff：`docs/plans/20261102-notes-fieldtest-review/handoff.md`
  - 提交：`1cdb88bdff8a201173d2712ac827de6896181603`
  - SHA-256：`63fd3e530eee29688c14ede8f887dfc1a1b8b43ee1a2f85d3a66f208cf5c1ed8`
- S3a implementation Simplicity Review：`docs/plans/20261102-notes-fieldtest-review/simplicity-implementation-review.md`
  - 提交：`72132263ce25aa55e3e6f48626f5c3a73f938fad`
  - SHA-256：`e79aa81e4d3dbca205b16808c6d646d2e12cf6f327bbcf9ffb9607801ea68b7e`
  - 只涵蓋 S3a 候選 `c8f1088820d835590d4a54b66de9c73b0308bac5` 的簡潔性；不是 S3b、產品、GUI、A0 或 Acceptance 通過。
- S3a 實作報告 SHA-256：`245425c3859a02031a3b018242312e4d6c570854b6a8cd223049fa79b029ae75`
- 受測產品基線：`8814d6db0e0a7f368fa5b241fc5ab0010540ea63`

起始分支的本機與遠端完整 HEAD 相同。交付候選只包含下列六個文件與本報告；
沒有 reset、clean、切換 worktree、合併 master 或改寫既有完成事實。

## 候選身分與逐檔差異

六個文件相對起始 HEAD 的完整 diff SHA-256 為
`22dc085d472665ed1ccf06dd15a9196506a87cfe10a75b1a7b7800f1149b0c86`，
合計 `42 insertions(+), 15 deletions(-)`。本報告與這六個文件應在後續同一
交付提交；提交 SHA 由交付後讀回，不在文件內預填。

| 路徑 | +／− | 候選檔 SHA-256 |
|---|---:|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | +5／−5 | `9186f1923528f1f585c3ff5b6c656fb7a1fb27414eeba3e444fc006936b42ba3` |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | +2／−2 | `232815f35816d079973029ef403c9e9f8d28d41ccc3af41fba82e1a7f557947b` |
| `.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md` | +9／−0 | `1269e0132893b1d5396160411a1a35409c7fbdeabd4542717adfea01ca67853c` |
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` | +14／−4 | `c760838f08e04d226c610adfbec95b649f3359a63d45e3da8ce90be43c5d374c` |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md` | +9／−2 | `c8972f81b3511f62cfc0bb77243ae122a552e2e6ef1460e7762782103d537784` |
| `.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md` | +3／−2 | `27e3ee97aa13caa9cd4174f9e9b0311955abfaadfa7066733509dfc191a213ff` |

`src/`、`tests/`、使用手冊、`AGENTS.md`、相簿 Skill／程式與 `media_verify.py`
相對起始 HEAD 均無差異。沒有新增 schema、locator、controller、固定 sleep、
全域改名器或下載重試入口。

## S3b 七項 N26 對應

| ID | 本次文件處置 | 可支持的命題 | 尚缺證據 |
|---|---|---|---|
| `N26-AX` | `gui-inventory.md` 與 `evidence-template.md` 分開 AX／CUA client、API scope、app／window 綁定、role／children 與 raw return；相同 AX 不得推定控制未變，截圖與 AX 不得互相補值 | 後續觀察可保存可比較的來源範圍；缺欄位會落 `UNKNOWN`／`BLOCKED` | 同 viewer 的原始 AX／CUA 輸出、request ID 與獨立 client 對照仍 `NOT_RUN`；G0 未執行 |
| `N26-TOOLBAR` | `gui-inventory.md` 明示 intent 前後只屬觀察順序，不能推定因果；比較須有焦點、hover／輸入、幾何與等時長靜置對照 | 不把順序或舊點位當成 intent 專屬觸發證據 | 可控時序對照與實際工具列根因 `UNKNOWN`；沒有重播 intent 或右鍵 |
| `N26-PANEL` | `download-and-ledger.md`、C10 與證據範本分開 PathTextField、panel current directory／where 與 intent staging；三者一致且可歸屬才可確認一次 | 舊預填值不再被當成目前目錄或本次目的地 | 真實 chooser 的三層讀回、原始確認回傳與畫面覆蓋 `NOT_RUN` |
| `N26-NAME` | 下載文件、完成規則與證據範本保留獨立空白 attempt；相同 basename／可見名稱／隱藏副檔名只供顯示，不建立同媒體、去重或全域改名器 | 檔名與出現順序不能單獨歸屬 attempt；metadata 不足保留 `UNKNOWN` | 真實同名／隱藏副檔名案例及平台命名中繼資料 `NOT_RUN` |
| `N26-TOAST` | `verification-and-recovery.md` 與證據範本把截圖、AX、原始回傳及真人觀察分開，新增終結提示 `terminal_observed_at`；瞬態時間／範圍不足記 `UNKNOWN`，不得為提示重下 | 單一來源的提示不能由另一來源補成存在或不存在，也不取代終結、穩定檔、verify／completion | 真實 popup／toast 的原始截圖、AX、時間與範圍 `NOT_RUN` |
| `N26-SPINNER` | Skill 與 `gui-inventory.md` 新增 B1 就緒 gate：spinner、黑底、空白縮圖、disabled slider、`00:00` 或缺少影片控制不判種類；未就緒不定位、不先建 PHOTO key | 延後種類直到 viewer／內容／所屬貼文穩定，不以等待秒數修復 | 真實載入瞬態、影片控制與 viewer 種類判定 `NOT_RUN` |
| `N26-CARD` | `gui-inventory.md` 容許已展開卡片直接以「卡片 → 縮圖 → viewer」交叉，不強迫虛構詳情頁 | 當次畫面可支持同一貼文與媒體序的交叉核對 | 真實已展開卡片的多媒體覆蓋與版本差異 `NOT_RUN` |

以上「已補文件」只表示操作契約已寫入受測候選，不是 GUI 現象已重現、根因
已定位或實機 PASS。七項的 G0、真實畫面、能力與跨 Session 證據仍分開管理。

## C5：R1–R10 整合矩陣

既有 S1 程式候選為 `423b00e`，S2 程式／安全 gate 候選為 `8814d6d`；本輪
沒有重跑 S1／S2 當時的個別 targeted 命令。現行候選的完整 notes 回歸已涵蓋
下表測試檔，但合成測試 PASS 仍不是真實 GUI、資料或獨立 Acceptance。矩陣沿用
前輪結果時均保留來源候選及「未重跑」界線。

| ID | 需求 | 既有程式／測試來源（未重跑單項） | S3b 文件整合 | 目前證據狀態 |
|---|---|---|---|---|
| `R1` 舊 UNKNOWN 與閉環 | 無可歸屬結果不得猜測、重送或解鎖 | S2 `test_unknown_is_blocked_until_reconcile`、`test_unbound_intent_verify_and_resume_fail_closed`；原 UNKNOWN 資料未重跑 | 下載文件保留 outcome→reconcile、停止與禁止新 attempt 順序 | 合成安全 gate 在現行 notes 回歸中通過；原 attempt、G0／D1 與晚到結果 `NOT_RUN`／`BLOCKED` |
| `R2` 控制／popup 範圍 | 控制來源、範圍與 App／attempt 歸屬須可追溯 | 無可代替 G0 的合成測試 | AX provenance、工具列非因果、popup 缺席範圍及 chooser 三層目的地契約已補 | 文件契約成立；真實控制可見性、原始 AX／CUA 與 popup 能力 `NOT_RUN`／`BLOCKED` |
| `R3` 延後種類與錯記 | 未就緒不寫種類；更正保留 key／順序並改走有效種類驗證 | S2 `test_media_kind_correction_preserves_nineteen_items_and_v2_attempt`、scope／stale／after-attempt 拒絕案例 | B1 就緒 gate 與 viewer／縮圖種類規則已寫入 Skill／GUI reference | 合成更正與現行 notes 回歸通過；真實 viewer 種類與 19 項資料未操作 |
| `R4` 影片來源到期 | 單項到期保留欠件，禁止一般 recovery、批次推論或計完成 | S2 `test_source_unavailable_preserves_incomplete_without_recovery`、`test_source_unavailable_rejects_unknown_and_forged_recovery` | 下載／驗證 reference 維持 `EXPIRED`、`SOURCE_UNAVAILABLE` 與禁止重送 | 合成到期 gate 在現行回歸中通過；真實到期項與外部來源 `NOT_RUN` |
| `R5` 證據內部引用 | 新 bundle 機械核對；舊錯引只能以精確原事件追加 correction | S1／S2 `test_evidence_audit_*`、`test_evidence_correction_*` | evidence 範本補來源 provenance、raw return、瞬態時間與 chooser 欄位 | 合成 audit／correction 在現行回歸中通過；已知真實錯引與 D2 未處理 |
| `R6` 輸出覆寫 | 一次 child、全量 stdout／stderr／exit、新 receipt 不覆寫舊 receipt | S1 `test_request_precedes_one_child_and_each_capture_uses_new_receipt`、`test_refusal_then_success_keeps_both_receipts` | 文件繼續區分 capture receipt、CUA 原始回傳與 GUI input | 合成 capture 規則通過；真實 capture 與 popup 證據 `NOT_RUN` |
| `R7` 鎖競爭 | 只有真實 flock 尚未取得時可標 `NOTES_LOCK_BUSY`；其他 I/O 不標 retry-safe | S1 `test_flock_contention_errnos_map_to_exact_lock_busy`、`test_non_flock_eagain_is_not_marked_retry_safe`、`test_internal_error_is_not_marked_retry_safe` | CLI／錯誤界線未改，沒有新增重試入口 | 合成 lock 分類通過；真實 ledger 競爭 `NOT_RUN` |
| `R8` 全媒體盤點 | 頂底、重疊、逐篇 detail 與 media 數量一致才可派送 | S2 `test_summary_blocks_detail_pending_even_when_known_media_complete`、`test_summary_blocks_media_count_coverage_mismatch`、`test_start_scan_and_intent_share_coverage_gate` | 盤點、B1、已展開卡片、重疊錨點與 NO_MEDIA 規則已整合 | 合成 coverage gate 通過；真實 187 篇／lazy-load 盤點未重跑 |
| `R9` 恢復掃描相容性 | 先處理未決／待驗／待命名，再重掃；scan binding 不符交人工 | S2 `test_start_scan_blocks_unresolved_attempts_and_verify_required`、`test_start_scan_blocks_pending_naming_transaction`、`test_verify_and_pending_resume_reject_attempt_after_new_scan` 與 legacy fixture | 恢復／scan 文件保留原事件、原 scan 與禁止改綁定 | 合成 gate 與 legacy fixture 通過；真實跨 Session 與 binding mismatch `NOT_RUN` |
| `R10` 真實媒體與跨 Session | 真實影片、混合附件、chooser、popup、完整解碼、completion 與恢復均須獨立 E2E | 無合成案例可替代 | 文件只提供停止、證據與操作邊界，未宣稱實作完成 | `NOT_RUN`；保留 `external_copy_verified=false`、`real_line_e2e=NOT_TESTED` |

C5 的整合結論是：R1–R9 均有既有程式／測試或 S3 文件承接，R10 與所有需要
真實來源的命題仍缺證據。此結論不是十項需求全部 PASS，也不把文件契約升格為
資料修復、GUI 能力或實機完成。

## 實際驗證與結果

環境：macOS 27.0.1（26A434）、arm64、`/usr/bin/python3` 3.9.6、
Git 2.52.0、cwd `/Users/hsiaojohnny/dev/Line_backup`。命令均帶
`PYTHONPATH=src`；完整 stdout／stderr／時間／hash 保存在
`.local/line-backup/tasks/20261102-notes-s3b-implementation/checks/`，不加入 Git。

| 檢查 | 實際命令 | 結果 |
|---|---|---|
| daily 回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | exit 0；`Ran 73 tests in 318.937s`、`OK`；stderr 174 bytes、SHA-256 `0a206c8a2b319e1b43dc0ecccb1880ec3278ce3cacc1a00c9cc9bfc855356330` |
| notes CLI | `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | exit 0；stdout 2,410 bytes、SHA-256 `bdc976599f5475df72d28f7d6da813d6183f205aef87053fd2138db7c9e0fa96`；stderr 空 |
| notes 全回歸 | `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | exit 0；`Ran 136 tests in 14.232s`、`OK`；stdout SHA-256 `67abaa53f75705a4b3222042d9da8903fb630a176ef60e39b3680c789ecfbf76`，stderr SHA-256 `2f36b89584333260dcd402878bef9d2a1128089946546c6abb8c7e942f99b9c9` |
| whitespace | `git diff --check` | exit 0；stdout／stderr 空 |
| 文件契約 | 白名單、受保護檔案、七個 N26、B1、chooser 三層、提示來源、檔名及十個 R ID 的 `rg` 核對 | exit 0；輸出 SHA-256 `d860aacaf6952108c8bc8da96302efafd501e048c46caeb1e5d61b613f4b5bfa` |
| staged 文件檢查 | `git diff --cached --check`、七檔白名單、無 unstaged／untracked、受保護檔與 cached 報告 ID | 檢查當時 exit 0；七檔白名單且無其他變更；輸出 SHA-256 `a09c5bb177415bdc3d8cad78d14c1562774c08abe9b36dee25914eec96b1d44f` |

notes stderr 含測試刻意觸發的 `--signals` 語法錯誤輸出，但 unittest 最終
為 `OK`；不能把該預期 stderr 當成 CLI 失敗。上述 PASS 只涵蓋本機回歸與
文件契約。

報告契約檢查第一次以 zsh 保留變數 `status` 作迴圈名稱，wrapper 在執行後續
檢查前即 exit 1；沒有修改檔案。改用 `status_name` 後同一檢查 exit 0，七個
N26、十個 R ID 與六項狀態均存在。這是 shell wrapper 錯誤，不是產品或文件
拒絕。

## 資料隔離、相容與未變更界線

- 本輪未讀寫真實 `backup/`、`backup-records/`、`notes-backup-records/`、
  active task、ledger、照片、影片或既有完成事實。
- 未操作 LINE GUI、前景、viewer、popup、chooser、Save All，未建立 intent、
  下載、重送、reconcile、verify、resume 或變更任何 ledger。
- 未修改產品 `src/`、`tests/`、使用手冊、AGENTS、相簿 Skill、schema、
  identity、事件、鎖 allowlist 或 v1 fixture。
- AX／截圖／Computer Use／真人觀察仍分層；相同 AX、舊預填路徑、檔名或單一
  toast 都不被升級成跨來源或完成證據。
- `dispatch_authorized=false` 仍只是 CLI 欄位；文件或合成測試不證明 GUI
  派送授權。`external_copy_verified=false` 與 `real_line_e2e=NOT_TESTED` 不變。

## 未知、未完成與停止點

- A0 獨立本機相容驗證：`NOT_RUN`。
- G0、D1、D2、G1、G2：`NOT_RUN`；沒有新的實際前景、原始工具 envelope、
  chooser／popup 或真實資料授權。
- 真實 LINE 記事本七項 N26 現象、即時 spinner／toast、混合附件、Save All、
  影片下載、完整盤點、跨 Session、前景中斷與真實 E2E：`NOT_RUN`。
- 原 R1 的舊 UNKNOWN、R4 的真實到期項、R5 的真實錯引、R10 的真實媒體與
  completion 均未取得新證據；不得以本報告或合成回歸宣稱收斂。
- implementation Simplicity Review（S3b 候選）、獨立 Acceptance 與 Task
  Closure：`NOT_RUN`／`BLOCKED`。

本切片交付後停止。下一步由 Owner 決定是否交適用角色執行 S3b Simplicity
Review、A0 及外部 gate；A0 與真實 GUI／E2E 未完成前不得進正式 Acceptance、
合併 master 或宣稱整體任務完成。

## 六項狀態

```text
PRIMARY_OUTCOME_STATUS: S3B_CANDIDATE_READY
IMPLEMENTATION_STATUS: S3B_DOCUMENTATION_IMPLEMENTED
CORE_ACCEPTANCE_STATUS: BLOCKED
REQUIRED_VERIFICATION_STATUS: LOCAL_REGRESSIONS_PASSED; REAL_GUI_AND_APPLICABLE_GATES_NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
TASK_CLOSURE_STATUS: BLOCKED_PENDING_A0_AND_EXTERNAL_GATES
```
