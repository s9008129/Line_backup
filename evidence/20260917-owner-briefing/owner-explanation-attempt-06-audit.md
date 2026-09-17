# 稽核報告（claim-by-claim）— `evidence/20260917-owner-briefing/owner-explanation-attempt-06.md`

- 稽核角色：白話說明稽核者（獨立、唯讀＋離線重放；未載入規劃／實作角色上下文）。
- 稽核日期：2026-09-17（Asia/Taipei）。
- 被稽核檔案（唯一稽核對象）：
  - 路徑：`evidence/20260917-owner-briefing/owner-explanation-attempt-06.md`
  - bytes：**7,993**
  - SHA-256：**`6557ff299155f4be3010f7fc096eac96e6cb51faf22eb64606a36bfc8d91bbcb`**
  - mtime：2026-09-17 23:49:53 +0800（支持文件自述「撰寫時間：2026-09-17（Asia/Taipei）」）。
- 寫入紀律：本稽核只寫出本檔一個檔案（唯一寫入）；被稽核檔與所有凍結成品皆未被編輯；未跑 GUI；未 git commit；未把任何圖片放進對話；除唯讀檢查外，只做了離線重放（重算目的地 SHA-256、重跑凍結 v4 工具輸出到 `/tmp`、未寫入 repo）。
- 判定詞彙：`MATCH`（與凍結來源一致）／`MISMATCH`（與來源不符）／`UNVERIFIABLE`（無從查核）。

## 一、來源識別表（本次稽核實際重算 SHA-256）

| ID | 來源（相對 repo 根） | SHA-256（本次重算） | 角色 |
|---|---|---|---|
| F1 | `evidence/20260916-route/attempt-06/run-ledger.json` | `906c14330605122e9b600359892d4400171d62564707d50af26ef8d8bb32fa2c` | 凍結原始檔（主） |
| F2 | `evidence/20260916-route/attempt-06/album-card-locate.json` | `b822012d28e2efeb268b5cd602c956afaf87fa666301aa67452ba597c3b81493` | 凍結原始檔 |
| F3 | `evidence/20260916-route/attempt-06/album-open-verify.json` | `a1e5fa491ac83f844f748683e51baf56e1b6d6f968e6f9d675a2fcb19486164d` | 凍結原始檔 |
| F4 | `evidence/20260916-route/attempt-06/album-ellipsis-locate.json` | `433e8693b1e23336628fab919042eca2c4903b0476c5a5ef22ff15f7d74edfb6` | 凍結原始檔 |
| F5 | `evidence/20260916-route/attempt-06/screen-probe.json` | `d696f442a9a835dc62f506722351d009690426db5afd748ecc9527782f27b07b` | 凍結原始檔 |
| F6 | `evidence/20260916-route/attempt-06/gate-4-authorization.json` | `e32ccd882b93b784e1faf3f3ea1df9732ab093e26f74a89622ac857159876272` | 凍結原始檔 |
| F7 | `evidence/20260917-owner-decisions/owner-decisions-rev22.json` | `0664b5fba0fc73b3516a790b8b2e783819892ffea3cf078c087cd68c09374b32` | 凍結原始檔 |
| F8 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/execution-rev22.md` | `c9b590802c7b27f34796c8623005ad106343bcf0c43b23b799cdb94fcfade131` | 凍結原始檔 |
| F9 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/plan.md`（§22.5／§22.7 與 header） | `4337e2b5c105901ce7c56956ecea5469894df2d2a29f099068c979584c71b6b2` | 凍結原始檔（計畫） |
| F10 | `evidence/20260916-route/attempt-06/route-runbook.md`（本稽核用來核對 S5／S6 規則原文） | `716bca926dcb76663afc9b937479da480dd9d1841fbb52b1224945e25e1963a8` | 凍結原始檔（pre-freeze，F1 `frozen_inputs` 同值） |
| F11 | `evidence/20260916-route/attempt-05/album-open-verify.json` | `ffa5d9633804f819473674f57a9979d56e849882f32dfcfa4a2b5b1326083a9b` | 凍結原始檔（前輪） |
| F12 | `evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json` | `d3ebbaed3db446cfbecd01d74d132764b6a675232b9db9edd2d1af3071dd6d5b` | 凍結原始檔（前輪） |
| F13 | `evidence/20260916-baseline/attempt-01/baseline-pre.json` | `ab6747f28b22557458baba2f38e9af6770257ce4cee27a26d78f3726761685b5` | 凍結原始檔（基準） |
| F14 | `evidence/20260916-route/tools/selftest/v4/selftest-summary.json` | `5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d` | 凍結原始檔（v4 自測摘要） |
| F15 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/e2e/attempt-06/e2e_report.md` | `14b44c949b7e0062936cdfd7f33bd1352b4953996c0c47ce1014a2fc61d15b95` | 凍結原始檔（Rev21 波獨立驗收報告） |
| F16 | `.agent/tasks/T20260916-0102-01-line-backup-acceptance/e2e/attempt-07/independent-recheck/route6-adversarial-recheck.json` | `4ea32764d1d68d27e626afd174de32b7d687157b6dc392e4e4c8719e98972882` | **另一個獨立對抗式複核（引用來源，非本稽核自身的重放；引用處皆標明）** |
| F17 | `evidence/20260917-vision-reader/phase0/baseline.json` | `894006f31854b274d36e323de1dfd6e6d45ebd887e1e214a33c883b7839736e6` | 凍結原始檔（相位0 基準；見下方來源對映註記） |

來源對映註記：F17 經查**不含**「57 檔／17,924,900 bytes」之目的地欄位（無 `destination`／`17924900`／`regular_file` 欄位；其「57」僅出現在雜湊與 OCR 讀值）。該主張的實際承載來源是 F13（`destination.regular_files=57`、`total_bytes=17924900`）、F8 與 F15（獨立重數）。被稽核文件本身亦未引用 F17；此為來源對映說明，不影響判定。

## 二、稽核方法與獨立驗證（實際執行）

1. 全數重算上表 SHA-256（`shasum -a 256`）與文件文末清單逐字比對：11/11 相符（見 C94a–C94k）。
2. 逐位元比對：`cmp` F13 對 `/tmp/route6_baseline_current.json` 與 `/private/tmp/line-backup-acceptance-baseline/current.json` → 三者 byte-identical（`ab6747f2…`）。
3. **唯讀重算目的地**（稽核當時）：`/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57` → 57 檔、17,924,900 bytes、57/57 檔 SHA-256 與 F13 逐檔相符、0 個額外檔案、0 個大小不符。
4. **離線重放（唯讀，stdout 導向 `/tmp`，未寫入 repo；未產生 `__pycache__`）**，重跑凍結 v4 工具：
   - `locate_album_card.py /tmp/route6_frame_pre.jpg …` → exit 0，stdout SHA-256 `b822012d…`＝F2 原檔（byte-identical）。
   - `verify_album_open.py /tmp/route6_frame_pre.jpg /tmp/route6_frame_post.jpg … --delta 12` → exit 0，stdout SHA-256 `a1e5fa49…`＝F3 原檔。
   - `locate_album_ellipsis.py /tmp/route6_frame_post.jpg … --title-bbox 15,83,204,111` → exit **3**，stdout SHA-256 `433e8693…`＝F4 原檔；實測 band `{x0:206,x1:326,y0:77,y1:121}`、帶內候選 0、唯一非文字候選 dots `[304.5,44.0]/[304.5,49.5]/[304.5,55.0]`。
   - 產物：`/tmp/audit_card_stdout.json`、`/tmp/audit_verify_stdout.json`、`/tmp/audit_ellipsis_stdout.json`（僅稽核用暫存；非凍結成品）。
5. 讀取 F14：`cases_total=16`、`cases_failed=0`、`result=PASS`（16/16 cases passed）。
6. 讀取 F15：報告自帶 wave-scoped tuple「ACHIEVED／COMPLETE／PASS／PASS（wave subject accepted）」；檔頭為「Stage 05, attempt-06（Rev21 Vision-reader wave）」。
7. 引用 F16（獨立對抗複核，標明來源）：R1-06（0.62538 逐像素精確重現）、R2-03／R2-04（triples 列舉與原始像素層帶內 0）、R2-09（RULE-GEOMETRY stop、非讀取能力失敗；⋮ 本體身分與可達性保留 UNKNOWN）。
8. 未執行任何 GUI、未點擊、未截圖、未執行 git commit。

## 三、稽核結果總表（claim-by-claim）

> 原文引句為逐字節錄（必要時以「…」節略）。行號：`Lxx`＝被稽核文件行號；來源側以欄位路徑（JSON）或行號（md）標示。

### A. 開頭與「一句話」（L3、L7）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C01 | L3：撰寫時間：2026-09-17（Asia/Taipei） | 被稽核檔 mtime；F1–F16 皆 2026-09-17 | 檔案 mtime 2026-09-17 23:49:53 +0800；所有來源同日 | MATCH |
| C02 | L3：本文只做說明、不授權任何動作 | 全文檢視（無授權語句）；F6（授權僅在 gate-4） | 文件內無任何新授權或指示動作之語句 | MATCH |
| C03 | L3：提問逐字見 `owner-decisions-rev22.json` 第 1034 行 | F7 L9–15 `question_message_transcript.line=1034`、`verbatim=「請深度梳理上下文後，用白話、一般人或非技術人員可以理解的方式告訴我，為什麼這一次做的測試失敗了，以及它的瓶頸是什麼。」` | 提問逐字的確記錄於該 JSON，且 `line=1034`。註：1034 是 **transcript 行號**（記錄於該 JSON 內）；該檔本身只有 140 行，「第 1034 行」不是該檔的實體行號 | MATCH |
| C04 | L3：事實來自文末已凍結檔案 | 文末 11 檔實測 SHA-256（見 C94a–C94k） | 11/11 與磁碟一致 | MATCH |
| C05 | L7：照片與備份都沒問題（一個位元都沒被動到） | F13＋步驟二.2（逐位元）＋步驟二.3（57/57 SHA-256 重算）；F1 `route_outcome`（無 destination 寫入） | 基準重跑 JSON 逐位元相同；目的地 57 檔逐檔 SHA-256 全等 | MATCH |
| C06 | L7：「失敗」的只是相簿內 ⋮ 這一輪嘗試 | F1 `run_status=STOPPED_AT_S6_NO_ELLIPSIS_FOUND`、`route_outcome.route_status`；F8 L29 | 路線嘗試確為唯一未取得肯定結果的環節；整體狀態另見 C67 | MATCH |
| C07 | L7：流程在點 ⋮ 前照規定自我檢查，發現畫面上唯一的 ⋮ 候選不在規則允許的位置，於是安全煞車 | F4（帶內 0、唯一非文字候選在帶外）；F10 S6；F1 events[7] | 前置檢查在送 ⋮ 輸入前執行並停止；無 ⋮ 點擊 | MATCH |
| C08 | L7：這次「眼睛」讀對了 57 張 | F2 `count_digits_read=57`／`count_text=MATCH`；F3 `count_digits_read=57`、`post_ocr_words_seen` 含「57張照片」 | v4 讀取鏈在 S3／S5 皆讀出 57 | MATCH |
| C09 | L7：卡住的是位置規則 | F16 R2-09：「RULE-GEOMETRY stop, not a reading-capability failure」 | 獨立對抗複核同結論 | MATCH |

### B. 「這次實際發生什麼（照順序）」（L11–L18）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C10 | L11：畫面裡確實有個像 ⋮ 的候選，但它在格子外，流程依規定踩煞車 | F4 triples（唯一非文字三點候選 middle (304.5,49.5) 在帶外）；F10 S6 | 措辭為「像 ⋮ 的候選」（未宣稱身分），與來源一致 | MATCH |
| C11 | L13：原話「1 選 B；2 用更正版紀錄」 | F6 L43 `context_authorization.verbatim`；F7 L48 `answer_verbatim` | 逐字相符 | MATCH |
| C12 | L13：只做兩個動作、各最多一次——點開目標相簿卡，再對相簿裡的 ⋮ 點一次、只觀察；其他都不准 | F6 `decided_interpretation.authorized_inputs_in_order`（2 inputs、`click_count=1`、observation only）、`nothing_else` | 授權封套＝恰兩個輸入、各最多一次、其餘禁止 | MATCH |
| C13 | L14：唯讀觀察找到目標相簿卡（2024/05/13~05/17、57 張）→ ELIGIBLE | F2 L15–16 `title.texts`、L45–46 count 57／MATCH、L52 `verdict=ELIGIBLE`；F1 events[4] `action_class=read` | 標題、張數、裁決皆相符；S3 為唯讀 | MATCH |
| C14 | L14：送出唯一一次點擊（[27,482]） | F2 L47–51 `click_point=[27,482]`；F1 `final_counts.album_card_input=1`、events[5] `click_count=1` | 本 run 唯一一次點擊，座標相符 | MATCH |
| C15 | L14：相簿打開 | F3 L151 `verdict=ALBUM_OPEN_VERIFIED` | 與 S5 裁決一致 | MATCH |
| C16 | L15：標題讀到 | F3 L30–35 `target_title_in_post.texts`＋reader block | 目標標題在 post 幀可讀 | MATCH |
| C17 | L15：畫面 62.5% 像素改變 | F3 L55 `changed_fraction=0.62538`；F16 R1-06（131493/210261=0.6253798…，round6） | 0.62538＝62.538%，一位小數四捨五入為 62.5%（原文為四捨五入值） | MATCH |
| C18 | L15：規定只要求 5% 以上 | F3 L12 `min_diff_fraction=0.05`；F10 S5「變動像素比例 ≥5%（凍結 `--delta 12`）」 | 門檻確為 ≥5% | MATCH |
| C19 | L15：張數 57 相符（MATCH） | F3 L51–52 `count_digits_read=57`、`count_text=MATCH` | 相符 | MATCH |
| C20 | L15：→ ALBUM_OPEN_VERIFIED | F3 L151 | 相符 | MATCH |
| C21 | L16：規則要求恰好一個三點候選落在標題那一橫列、靠右範圍 | F10 S6：「`ELIGIBLE` 僅當**恰有一個**候選落在「目標標題同一列帶」內且位於標題右方」；F1 events[7].`runbook_rule_applied` | 規則原文相符 | MATCH |
| C22 | L16：（x 206～326、y 77～121） | F4 L503–507 `album_title_band`；稽核重放實測同值 | 相符。註：此為該幀由 S5 標題 bbox 推導出的帶位（非規則常數） | MATCH |
| C23 | L16：結果範圍內 0 個 | F4（triples 無 in-band）；F1 L504「eligible candidates inside the album-title row band: 0」；稽核重放實測 0；F16 R2-04 原始像素層亦 0 | 相符（規則層與像素層皆 0） | MATCH |
| C24 | L16：唯一「非文字」候選在更高處（x≈304.5、y≈44～55） | F4 L39–55 `dots`（304.5,44.0/49.5/55.0）；L511–513 triple #1 `region=above_album_title_band`、`overlapping_ocr_token=null`；稽核重放實測同值 | 相符 | MATCH |
| C25 | L16：另 5 組壓在文字上 | F4 L533–657：恰 5 個 `inside_text` triple，blocker 為 '57張照片'／'2024.05.18' conf 1.0 | 相符（5 組、皆與 OCR 文字重疊） | MATCH |
| C26 | L17：判定 NO_ELLIPSIS_FOUND（找不到符合規則的 ⋮；結束碼 3） | F4 L658 `verdict`；F1 L489 `locator_exit_code=3`；稽核重放 exit 3 | 相符 | MATCH |
| C27 | L17：不可送 ⋮ 點擊、不可重試、不可換座標 | F1 events[7].`runbook_rule_applied`（record, notify, stop—no retry, no alternate coordinates, no improvisation）；`budgets.retry_budget=0` | 相符 | MATCH |
| C28 | L17：流程停下回報（⋮ 點擊 0/1） | F1 `final_counts.ellipsis_input=0`；`inputs.ellipsis=UNSPENT (0/1) - never sent` | 相符 | MATCH |
| C29 | L17：整場恰一次輸入（打開相簿） | F1 `final_counts`：album_card_input 1、navigation_input 1（同一擊）、app/menu/keyboard/retry 0 | 相符 | MATCH |
| C30 | L17：其餘零副作用 | F1 events 各 `allowed_budget_after`（menu_item/save_all/chooser/backup_state_write 全 false）；`route_outcome.no_side_effects_beyond_authorized_click` | 相符 | MATCH |
| C31 | L17：畫面停在「相簿已打開」，無選單被開或留著 | F1 L609 `surface_state_now`（album view open；no menu/dialog opened by us；no menu left open）；events[7].`menu_opened_by_us=false` | 相符；S5 post AX 亦無選單 | MATCH |
| C32 | L18：全螢幕唯讀探查（只截圖、0 輸入） | F5 L18 `probe.input_events_sent=0`；probe（`screencapture -x`、exit 0） | 相符 | MATCH |
| C33 | L18：screen_scope=UNAVAILABLE | F5 L122 `acceptance.screen_scope`；F1 events[2] | 相符 | MATCH |
| C34 | L18：非關卡、不擋路 | F5 L5「SUPPORTING / non-gating」；F9 §22.6 `V22_SCREEN_SCOPE_PROBE`（SUPPORTING／DIAGNOSTIC／NON_GATING）＋L202；F8 L71 | 相符 | MATCH |
| C35 | L18：官方流程照原定方式續行 | F5 L124「the run continues window-scoped with the frozen v4 reader as the official chain」；F1 events[3] | 相符 | MATCH |

### C. 「為什麼算失敗／不算失敗」與瓶頸（L22–L35）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C36 | L22：算失敗的只有一件事：這一輪要拿到的「機器看得見的肯定結果」沒拿到 | F1 `stop_reason`（did not reach a machine-observable AFFIRMATIVE）；`route_outcome.route_status` | 相符 | MATCH |
| C37 | L22：「相簿內 ⋮」路線仍是未關閉的卡點 | F1 `route_outcome`（the route stays a scoped CORE blocker, owner-reserved）；F8 L88–97（BLK-02） | 相符 | MATCH |
| C38 | L22：這不等於「LINE 沒有這個 ⋮」——只是「依規則找不到可合法點的 ⋮」 | F1 `stop_reason`；F16 R2-09 note（⋮ 本體身分未經點擊驗證＝UNKNOWN；未證明存在、亦未證明不存在） | 相符（未把候選身分講成事實，亦未過度否定） | MATCH |
| C39 | L25：照片沒有失敗、備份沒有被動到 | C05；F15（destination read-only PASS） | 相符 | MATCH |
| C40 | L25：57 個備份檔案（17,924,900 bytes） | F13 `destination.regular_files=57`、`total_bytes=17924900`；稽核步驟二.3 重算 57／17,924,900；F15（57 files／17,924,900 bytes） | 相符（三方一致） | MATCH |
| C41 | L25：與基準逐位元一致 | F13 對兩份 literal 重跑 JSON `cmp` byte-identical（`ab6747f2…`）；稽核重算 57/57 檔 SHA-256 全等 | 相符 | MATCH |
| C42 | L25：沒被碰、沒被改，也沒寫入任何檔案或您的設定／正式狀態 | F1 `route_outcome`（no destination/formal-state write）；F8 L77／L117（no formal config/state/registry/run-log write） | 相符；範圍限「備份檔案／設定／正式狀態」——本 run 確實寫了自己的證據紀錄（文件 L58 已自述） | MATCH（範圍註） |
| C43 | L26：這是流程在「對 ⋮ 動手之前」的自我檢查停住，不是按錯或弄壞東西 | F1 events[7]（S6 唯讀）；input #2 never sent；F10 停止政策 | 相符 | MATCH |
| C44 | L26：⋮ 一次都沒被點 | F1 `inputs.ellipsis=UNSPENT (0/1)`；`final_counts.ellipsis_input=0` | 相符 | MATCH |
| C45 | L27：上一輪舊讀取器（tesseract）把 57 讀成 75 | F11 L70 `count_digits_read="75"`；F12 L23 `reader=tesseract 5.5.1` | 相符 | MATCH |
| C46 | L27：這次換成 macOS Vision（v4）後 57、日期都讀對 | F2／F3／F4 reader block（helper source `4fc9fa2b…`）；F3 count 57 MATCH、目標標題可讀；F16 R2-08（標題與日期 OCR conf 1.0） | 相符 | MATCH |
| C47 | L27：停住的是「位置規則」：⋮ 被要求長在相簿標題那一排，畫面上唯一像 ⋮ 的候選卻在更高處 | F10 S6；F4（候選在帶上方）；F16 R2-04（距帶頂 22.0／27.5／33.0 px） | 相符 | MATCH |
| C48 | L31：規則把「⋮ 該在哪裡」寫死成「標題那一橫列、靠右範圍內」 | F10 S6；F4 `album_title_band`（由 S5 標題 bbox 推導） | 相符 | MATCH |
| C49 | L31：規則沒有「位置不同、形狀吻合」的備援判定 | F10 S6：帶內恰一且靠右才 ELIGIBLE，其餘輸出（NO_ELLIPSIS_FOUND 等）一律「不送輸入、停止」；F1 events[7]（no improvisation） | 相符（規則確無形狀吻合備援） | MATCH |
| C50 | L31：不是讀不到，是「讀到了，但位置不合規則」 | F16 R2-09；F1 events[7]（reader 正常：title conf 1.0、count 57、58 個 dot components） | 相符 | MATCH |
| C51 | L32：零容錯。任何自我檢查沒過就整場停止——不重試、不換路、不臨場發揮 | F1 `budgets`（retry 0）、events[7]；F10 停止政策 | 相符 | MATCH |
| C52 | L32：這是安全設計，代價是一旦不合就要請您出面 | F1 `owner_decision_required=true`、`stop_reason`（owner is notified immediately）；F10 停止政策 | 相符（設計性質描述，來源支持） | MATCH |
| C53 | L33：授權是事前給的「每個動作最多一次」 | F6（授權時間 21:38 早於 run 23:17；`click_count_per_input=1`） | 相符 | MATCH |
| C54 | L33：關卡沒過就作廢、不能沿用補發 | F1 `next_action`（input #2 is never re-authorizable） | 相符 | MATCH |
| C55 | L33：要再來得走「新修訂＋新授權＋新審查」 | F1 `next_action`（NEW plan revision, a new one-shot authorization, a fresh review） | 相符 | MATCH |
| C56 | L35：讀取能力這次不是瓶頸（v4 Vision 已讀對 57）；上一輪才是（舊引擎把 57 讀成 75） | C46＋C45（同來源） | 相符 | MATCH |

### D. 「三個結果分開看」（L39–L41）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C57 | L39：① 相簿資料本身：仍未結案 | F9 L15／L17／L20（UNKNOWN／BLOCKED／CORE_ACCEPTANCE_BLOCKED）；F15（result ① UNKNOWN） | 相符 | MATCH |
| C58 | L39：57 個檔案在原位、與基準一致 | C40／C41（同來源；稽核時目的地仍在原位） | 相符 | MATCH |
| C59 | L39：「這批檔案即該相簿的合法備份」的正式認定尚未完成 | F8 L82（SOURCE_CORRESPONDENCE 維持 UNRESOLVED）；F15（residual risk：result ① remains UNKNOWN） | 相符 | MATCH |
| C60 | L39：更正版紀錄已採用 | F7 `decisions.item_2.adopted_record`（v1.1 `a8c10551…`）；F8 L109 | 相符 | MATCH |
| C61 | L39：重算由獨立驗收處理 | F8 §11（Stage 05 re-derives both closure facts，含 §16.4 over v1.1）；F7 `item_2.consequence` | 相符（描述階段分工，未預告結果） | MATCH |
| C62 | L39：「相簿內 ⋮」的機器驗證未取得肯定結果，卡點未關、收尾保留給您 | F1 `route_outcome`、`owner_decision_required`；F9 L199（owner notified；ROUTE_NOT_NEEDED not taken） | 相符 | MATCH |
| C63 | L40：② 可重複使用的能力：已完成並通過獨立驗收 | F9 L21 `REV21_WAVE_STATUS`（independently accepted by e2e/attempt-06）；F15（wave-scoped tuple ACHIEVED／COMPLETE／PASS／PASS；wave subject accepted） | 相符（指已封閉之上一波） | MATCH |
| C64 | L40：v4 Vision 工具鏈自測 16 項全過（0 失敗） | F14 `cases_total=16`、`cases_failed=0`、`result=PASS`（16/16 passed）；F15（self-test 16/16 PASS） | 相符 | MATCH |
| C65 | L40：上一波已在獨立驗收通過（`e2e/attempt-06`，`14b44c94…`） | F15 檔 SHA-256=`14b44c949b7e0062…`；F9 L21；F8 L17（series note：e2e/attempt-06＝已消耗的 Rev21 波驗收） | 相符 | MATCH |
| C66 | L40：就是這次讀對 57 的眼睛 | F2／F3／F4 reader block（同一 frozen v4 工具鏈）；F8 L108（reused byte-identical） | 相符 | MATCH |
| C67 | L41：③ 整體結案：CORE_ACCEPTANCE_BLOCKED | **F9 L20 `TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED`**；**F8 L29 `STAGE_04_REPORTED_TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED`**（輔：F8 L26／L36；F9 L2085 路由規則） | 相符（出處見 §四.8） | MATCH |
| C68 | L41：實作完成、規定驗證也通過 | F8 L25 `IMPLEMENTATION_STATUS: COMPLETE`、L27 `REQUIRED_VERIFICATION_STATUS: PASS`；F9 L16／L18 | 相符 | MATCH |
| C69 | L41：核心卡點還擋著，整體還不能宣告結案（不是 DONE） | F8 L36（never DONE）；F9 L20／L199 | 相符 | MATCH |
| C70 | L41：本波獨立驗收（`e2e/attempt-07`）是下一棒 | F8 L17／L28（PENDING；Stage 05 fresh role, not pre-claimed）；F9 L11；時間線註（見 §四.7） | 相符 | MATCH |

### E. 「您手上的兩條路」與「最大風險」（L45–L51）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C71 | L45：A：記成「這條路不需要」，用它關閉卡點 | F6 L53（option presentation 逐字「A 記成「這條路不需要」關閉卡點」）；F6 `not_authorized`（該結案 owner-reserved、絕不自動執行） | 相符 | MATCH |
| C72 | L45：等於放棄「相簿內 ⋮ 由機器驗證」這項證據 | 推導：A＝不取該路線之觀測；F6／F9 L199（`ROUTE_NOT_NEEDED`＝放棄該路線並由 owner 結案） | 相符（推導） | MATCH |
| C73 | L45：不需新授權、不再動畫面，零接觸檔案 | 推導：A 不涉任何 GUI 輸入（F1 `next_action`：任何「再觀測」才需新 gate）；F6 `not_authorized`；凍結來源未描述 A 需要新授權或需接觸檔案 | 相符（推導；來源未逐字描述 A 的各項性質，但無矛盾） | MATCH |
| C74 | L46：B：開新修訂＋再授權一次「⋮ 只觀察」 | F1 `next_action`；F6 L53 | 相符 | MATCH |
| C75 | L46：重新走一輪規劃與獨立審查 | F1 `next_action`（NEW plan revision…fresh review） | 相符 | MATCH |
| C76 | L46：拿新的一次性「只觀察」授權 | F1 `next_action`（a new one-shot authorization）；F6（observation only 封套） | 相符 | MATCH |
| C77 | L46：再打開相簿看一眼 ⋮（絕不點任何選單） | 推導自授權封套（F6：album-card click 為 ⋮ 之前置；⋮ 僅觀察）；F6 L53「不點任何選單項目」 | 相符（推導） | MATCH |
| C78 | L46：代價：多一輪流程時間；會再打開相簿 | 推導（新修訂＋審查＋再跑＝流程時間；開相簿＝該觀測之前置） | 相符（推導） | MATCH |
| C79 | L46：新授權同樣一次性、不重試 | F6 `budgets`（retry 0、`click_count_per_input=1`）；F1 `budgets` | 相符 | MATCH |
| C80 | L47：兩條都不會自動執行 | F9 L199（neither branch may run automatically）；F6 `not_authorized` | 相符 | MATCH |
| C81 | L47：舊授權已用掉（相簿卡點擊 1/1、⋮ 0/1） | F1 `inputs.album_card=SPENT (1/1)`、`inputs.ellipsis=UNSPENT (0/1) - never sent`、`next_action`（input #2 never re-authorizable） | 相符。註：⋮ 為「未送出而失效」，非已點 | MATCH |
| C82 | L47：要再來一定是新的授權 | F1 `next_action` | 相符 | MATCH |
| C83 | L51：不是判斷力或照片問題，而是「⋮ 的位置」與規則假設不合 | F16 R2-09 | 相符 | MATCH |
| C84 | L51：風險不涉及資料：動作只是「看」 | F6（observation only）；F1 `route_outcome.no_side_effects_beyond_authorized_click` | 相符 | MATCH |

### F. 「全程絕對不會發生的事」與證據清單（L55–L76）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C85 | L57：不會點任何選單項目（包含「儲存全部」） | F1 `final_counts.menu_item_input=0`；F6 `not_authorized`（including Save All）；F8 §9 | 相符 | MATCH |
| C86 | L57：不會開檔案選擇器 | F1（各 events `chooser_interaction=false`）；F6 `budgets`／`not_authorized` | 相符 | MATCH |
| C87 | L57：不會送任何鍵盤輸入 | F1 `final_counts.keyboard_input=0` | 相符 | MATCH |
| C88 | L58：不會寫入您的設定或正式狀態 | F1（`backup_state_write=false`）；`route_outcome`（no formal-state write） | 相符 | MATCH |
| C89 | L58：流程寫的是它自己的證據紀錄，不是您的設定或備份狀態 | F1 events[8].`artifacts_written`（本 run 4 個 JSON＋ledger）；F8 L77 | 相符 | MATCH |
| C90 | L59：不會重新下載、不會改您的原檔（57 張照片與備份檔不寫入、不刪除、不搬動） | F1 `route_outcome`（no re-download、no destination write）；稽核步驟二.3（57/57 未變、無新增刪除） | 相符 | MATCH |
| C91 | L60：不會把任何畫面圖片放進對話 | F1 `budgets.conversation_images=0`；F8 L3（no image data） | 相符 | MATCH |
| C92 | L60：也不會重試、改用未授權座標、臨場改規則 | F1 `budgets.retry=0`＋events[7]（no alternate coordinates／improvisation）；F5（crop click points NEVER used） | 相符 | MATCH |
| C93 | L60：或自動幫您選 A 或 B | F1 `next_action`（do not act autonomously）；F9 L199 | 相符 | MATCH |
| C94a | L64：`run-ledger.json` — `906c1433…`（STOPPED_AT_S6_NO_ELLIPSIS_FOUND） | F1 實測 SHA-256；F1 `run_status` | 相符 | MATCH |
| C94b | L65：`album-card-locate.json` — `b822012d…` | F2 實測 SHA-256（稽核重放 stdout 亦同值） | 相符 | MATCH |
| C94c | L66：`album-open-verify.json` — `a1e5fa49…` | F3 實測 SHA-256（稽核重放 stdout 亦同值） | 相符 | MATCH |
| C94d | L67：`album-ellipsis-locate.json` — `433e8693…` | F4 實測 SHA-256（稽核重放 stdout 亦同值） | 相符 | MATCH |
| C94e | L68：`screen-probe.json` — `d696f442…` | F5 實測 SHA-256 | 相符 | MATCH |
| C94f | L69：`gate-4-authorization.json` — `e32ccd88…` | F6 實測 SHA-256 | 相符 | MATCH |
| C94g | L70：`owner-decisions-rev22.json` — `0664b5fb…` | F7 實測 SHA-256 | 相符 | MATCH |
| C94h | L71：`execution-rev22.md` — `c9b59080…` | F8 實測 SHA-256 | 相符 | MATCH |
| C94i | L72：`plan.md`（§22.5、§22.7）— `4337e2b5…` | F9 實測 SHA-256；§22.5 在 L192、§22.7 在 L215 | 相符 | MATCH |
| C94j | L73：`attempt-05/album-open-verify.json` — `ffa5d963…`（讀成 75） | F11 實測 SHA-256；`count_digits_read="75"` | 相符 | MATCH |
| C94k | L74：`attempt-05/vision-ocr-crosscheck.json` — `d3ebbaed…`（57，信心 1.00） | F12 實測 SHA-256；觀察 `57張照片 conf=1.00` | 相符 | MATCH |
| C95 | L64：（STOPPED_AT_S6_NO_ELLIPSIS_FOUND） | F1 `run_status` | 相符 | MATCH |
| C96 | L76：本波獨立驗收由另一組人負責（`e2e/attempt-07/`）；本文件不預先宣稱其結果 | 文件內 0 處 attempt-07 結果宣稱；F8 L28（Stage 05 fresh role；not pre-claimed）；時間線註（見 §四.7） | 相符（文件未預告成績，亦未引用其任何產物） | MATCH |

### G. 風險／可能性語句（條件式陳述，逐條標明性質；不構成本文可查核之事實宣稱）

| Claim ID | 原文引句 | 來源檔案＋行／欄位 | 觀察值 | 判定 |
|---|---|---|---|---|
| C97 | L46：且規則不保證會變，仍可能停在同一條幾何規則上 | F10（規則凍結）；F16 R2-09（對「⋮ 本體是否可達、可否以允許的觀測觸及」保留 UNKNOWN） | 條件式可能性陳述，與來源無矛盾；文件以「不保證／可能」限定，未誇大 | MATCH（性質：可能性陳述） |
| C98 | L51：同樣的 LINE 視窗配置下，很可能再得到同樣結果 | 同上；C17（同幀幾何可由重放 byte-identical 重現） | 條件式風險預測，已明確以「很可能」限定；未被表述為保證 | MATCH（性質：風險預測） |

## 四、八個特別關注點逐項核對

1. **「57 個檔案、17,924,900 bytes、與基準逐位元一致」→ MATCH。** F13 `regular_files=57`／`total_bytes=17924900`；兩份 literal 重跑 JSON 與 F13 逐位元相同（`ab6747f2…`）；稽核時唯讀重數目的地 57 檔、17,924,900 bytes、57/57 檔 SHA-256 全等、0 額外檔（C40、C41）。F17 不含此欄位（見來源對映註記）。
2. **「62.5% 像素改變」與 5% 門檻 → MATCH。** F3 `changed_fraction=0.62538`（62.538%，四捨五入 62.5%）、`min_diff_fraction=0.05`；稽核重放重現同值；F16 R1-06 逐像素精確重現（C17、C18）。
3. **「⋮ 候選 x≈304.5、y≈44～55、band [206..326]×[77..121]、帶內 0 個、其餘 5 組壓在文字上」→ MATCH。** F4 dots／triples／band 全數相符；稽核重放實測 band `{206,326,77,121}`、帶內 0、唯一非文字候選 `(304.5,44.0/49.5/55.0)`、5 組 `inside_text` 被 '57張照片'／'2024.05.18' 阻擋（C22–C25）；F16 R2-03／R2-04 另以原始像素層複核 0（引用來源）。
4. **「只點一次、⋮ 0/1、無重試、零副作用、沒有選單被開」→ MATCH。** F1 `final_counts`（album_card_input 1；navigation 1＝同一擊；ellipsis 0；retry 0；menu/keyboard/app 0）、`inputs.ellipsis=UNSPENT (0/1)`、events[7] `menu_opened_by_us=false`、`route_outcome.surface_state_now`（no menu/dialog opened by us；no menu left open）（C29–C31）。
5. **「v4 自測 16/16、0 失敗」與「e2e/attempt-06（Rev21 波）已獨立驗收通過、報告 14b44c94…」→ MATCH。** F14 `cases_total=16`、`cases_failed=0`、`result=PASS`；F15 檔 SHA-256＝`14b44c94…`，報告自載 wave-scoped tuple「ACHIEVED／COMPLETE／PASS／PASS（wave subject accepted）」；F9 L21 同述（C63–C65）。系列不混稱：文件正確區分「路線 attempt-06」與「e2e/attempt-06（上一波驗收）」。
6. **「screen_scope=UNAVAILABLE 且非關卡」→ MATCH。** F5 `acceptance.screen_scope=UNAVAILABLE`、`purpose`「SUPPORTING / non-gating」、`consequence`（non-gating；run continued window-scoped）；F9 §22.6 該列為 SUPPORTING／DIAGNOSTIC／NON_GATING；F1 events[3] 同值（C33–C35）。
7. **「把未經點擊驗證的 ⋮ 身分講成事實」或「預先宣稱獨立驗收結果」→ 0 處。** 
   - ⋮ 身分：文件一律用「候選」措辭（L7「唯一的 ⋮ 候選」、L11「像 ⋮ 的候選」、L16「唯一『非文字』候選」、L31「像 ⋮ 的候選」），並在 L22 明確反面聲明「這不等於『LINE 沒有這個 ⋮』」；未出現「那個位置就是相簿選單鈕」等斷言（C10、C24、C38）。與 F16 R2-08/R2-09 的 UNKNOWN（身分與可達性未證）一致。
   - 獨立驗收結果：唯一「已通過」語句指**已完成之上一波**（e2e/attempt-06，F15 為現存檔案）；對本波 e2e/attempt-07 只說「是下一棒」，且 L76 明示「本文件不預先宣稱其結果」；全文 0 處引用或預告 attempt-07 之成績（C70、C96）。
8. **「③ CORE_ACCEPTANCE_BLOCKED」出處 → F9 L20 ＋ F8 L29。** F9（plan.md）header L20：`TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED`；F8（execution-rev22.md）L29：`STAGE_04_REPORTED_TASK_CLOSURE_STATUS: CORE_ACCEPTANCE_BLOCKED`（輔助出處：F8 L26 `CORE_ACCEPTANCE_STATUS: BLOCKED (scoped)`、F8 L36「never `DONE`」、F9 L2085 路由規則「completed implementation with CORE blocked uses TASK_CLOSURE_STATUS=CORE_ACCEPTANCE_BLOCKED」）。文件 L41 的「實作完成、規定驗證也通過」對應 F8 L25、L27（C67–C69）。

## 五、時間線旁註（透明記錄；不構成判定變更）

- 被稽核檔 mtime：2026-09-17 23:49:53 +0800。
- 獨立對抗複核（F16）：23:46:21 產生（json 檔 mtime 23:47）——早於本文件 mtime；但本文件未引用它，也未因此改動任何宣稱。
- 本波 e2e/attempt-07 之 `e2e_report.md`（稽核時已存在；mtime 23:54）**晚於**本文件 mtime。本文件對它 0 宣稱；其「是下一棒」「不預先宣稱結果」在文件凍結時點與其自我約束下皆為真（C70、C96）。

## 六、MISMATCH／UNVERIFIABLE 清單

- MISMATCH：**0**。
- UNVERIFIABLE：**0**。
- 備註：本表有兩類經明文標註的項目仍判 MATCH——(a) 條件式風險／可能性語句（C97、C98；非事實宣稱，與凍結來源無矛盾）；(b) 由凍結來源直接推導之敘述（C72、C73、C77、C78；已逐條標「推導」）。另有兩處判 MATCH 但附範圍／語意註記：C03（「第 1034 行」＝該 JSON 內記錄的 transcript 行號，非該檔實體行號）、C17（62.5%＝0.62538 之四捨五入）、C42（「沒寫入任何檔案」之範圍限備份檔／設定／正式狀態；run 自身證據紀錄如 L58 所述）、C81（⋮ 為未送出而失效）。

## 七、總結

**`AUDIT_PASS`**（0 MISMATCH、0 UNVERIFIABLE）。被稽核文件 `evidence/20260917-owner-briefing/owner-explanation-attempt-06.md`（7,993 bytes、SHA-256 `6557ff29…`）之所有可查核具體宣稱，均與凍結原始檔一致；八個特別關注點全數通過；未發現誇大、身分斷言或預先宣稱獨立驗收結果之語句。
