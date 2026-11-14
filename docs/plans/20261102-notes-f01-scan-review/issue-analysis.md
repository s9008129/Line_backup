# F01：記事本掃描完成偽陽性診斷

## 本角色結論

`ANALYSIS_COMPLETE`。單一診斷對象為 F01：同一列表的舊掃描只記 14 篇卻標為 `COMPLETE`，後續掃描記 15 篇。

**可定位的失敗是：原始畫面已涵蓋一張獨立卡片，但 Agent 將多張畫面整理成 page 2 時沒有把它登錄；CLI 隨後依已提交清單的內部一致性產生 `COMPLETE`。** 舊 page 2 保存的截圖就含有漏篇，並非只能從兩次總數差推測。最後的 key 合併沒有刪掉該篇；該 key 從未出現在舊五頁資料中。

唯一下一步建議為 **`PLANNER_REPLAN`**：由 Owner 在另一主 Session 啟動 Planner，限定 F01，定義「畫面卡片逐一入帳 → 頁面覆蓋對帳 → 完成宣告」的可核對契約及驗證條件。本建議不是執行授權、修復結果或驗收 PASS。本角色到此停止，不啟動 Planner／Implementer／Acceptance。

## 1. 任務、輸入及版本

- 人工交接：Owner 本輪明示使用 `06_high_reasoning_review_prompt.md`，只分析 F01；另授權分析完成後使用一個 GPT-6 Luna helper 撰寫詳細 commit 訊息，由主 Session commit／push。
- 使用者目前產品範圍：**只備份照片與影片；文件、PDF、網頁文件不下載。** 這是本輪明示決策；本診斷不改寫舊測試報告、不據此改帳本分類，也不視為新 plan／handoff 已核准。
- Repo／worktree：`Line_backup` 核心工作目錄；branch：`feature/line-notes-media`。
- 受測產品候選：`260a49612cb3f7570a57f135921b4101e2c8ee99`。
- 測試報告提交／本輪起始 HEAD／核對到的遠端 HEAD：`7a3045aa2ac5b13b4e0b9186f5884c846f402583`。報告提交只新增 `測試報告.md`；對 `src tests .agents AGENTS.md` 的候選差異檢查 exit 0。
- 起始 tracked、index、非忽略 untracked 均乾淨；其他 worktree 保留。本輪預定只有本目錄兩份去識別化文件進 Git。
- 參考規劃：[原 replan](../20261101-notes-all-issues-replan/replan.md) D.4／T5、[plan 入口](../20261101-notes-all-issues-replan/plan.md)、[handoff](../20261101-notes-all-issues-replan/handoff.md)，及 [S3 補充計畫](../20261102-notes-fieldtest-review/plan.md)／[交接](../20261102-notes-fieldtest-review/handoff.md)。前者約束已知貼文的細盤覆蓋、未決 attempt 與 scan 綁定；後者集中 bootstrap 及 GUI 證據。未提供專門修復 F01 的核准 plan／handoff，故本次只交診斷。
- 依據 [測試報告](../../../測試報告.md) F01、指定私有 packet、23 份相關 scan／page 事件、其已保存 evidence bundle，以及候選源碼／現行 Skill。沒有操作 LINE、讀取照片區、呼叫真實帳本 writer 或修改歷史。

本輪日誌與原件 manifest 留在專案私有任務目錄 `.local/line-backup/tasks/20261102-notes-f01-scan-review/`。以下 `$SOURCE_ROOT` 指 Owner 交接的原實機私有證據目錄，`$L01_RECORDS` 指該列表原帳本；完整位置只記私有 manifest，不公開人物、列表顯示名、原始附件名或截圖內容。P01–P15 沿用測試報告的**新掃描**別名；它們不是舊 identity 中的序號。

## 2. 最小失敗鏈與直接證據

| 階段 | 可核對內容 | 證據與限制 |
|---|---|---|
| 舊觀察 | 舊 finish statement 宣稱 14 篇、五頁重疊、頂底成立；聲明觀察區間為 15:48:21–15:53:30（UTC+8） | `$SOURCE_ROOT/statements/scan-finish.md`；時間是保存 statement 的聲明，不是本輪重新量測或原生 input receipt |
| 舊畫面 | `scan-down-04.png` 同時顯示 P05 下段、其互動列／時間、下一張獨立卡片的作者列與 P06 內容；`scan-down-05.png` 接續 P06 下段、其互動列／時間與 P07 開頭 | 本輪用本機影像檢視工具讀取保存截圖，記 `OBSERVED`；不從圖片單獨判定 PDF 檔案格式，也不冒充即時 GUI |
| 舊轉錄 | page-index 2／event sequence 6 的 posts 是 `[P04,P05,P07,P08,P09]`；P06 缺席 | `$L01_RECORDS/events/00000006.json`、原 `posts-page-2.json`／`statements/page-2.md`。該 page 聚合多個 viewport，statement 甚至描述 P05 後直接接 P07 |
| 舊完成 | scan `0b4ba23d7edf415d85ab992ffdca9464`，5 pages、14 unique posts；event sequence 9 為 `action=COMPLETE` | 舊五頁都沒有 P06；完成事件等於它們的去重有序聯集 |
| 新觀察與登錄 | 新 `scan2-p06.png` 可交叉辨識相同的 P05／P06 邊界；新頁 5 是 `[P05,P06]`，頁 6 是 `[P06,P07]` | 新畫面 `OBSERVED`；新掃描沿用原 14 個 post key，插入一個獨立 key，並非對全部舊項重新編碼 |
| 新完成 | scan `19150b6f9a244437a74bec83d95b04a1`，14 pages、15 unique posts；event sequence 45 為 `action=COMPLETE` | 15 個 key 互異，新舊集合差恰為 P06；新完成不證明完成判定缺陷已修正 |

舊五頁以新別名表達為：

```text
page 0: P01                         top=true
page 1: P01 P02 P03 P04              overlap=P01
page 2: P04 P05     P07 P08 P09      overlap=P04；P06 不在輸入
page 3: P09 P10 P11 P12 P13          overlap=P09
page 4: P13 P14 P15                  overlap=P13；bottom=true
finish: 14 posts，COMPLETE
```

這個失敗不需要重新下載或新建 scan 才能查證：唯讀比對舊 page 2 的保存圖像與 rows，即可看到「有該卡片的觀察原件，但沒有該篇的輸入資料」。兩張關鍵截圖的 SHA-256 都存在於**原 event sequence 6 所引用的保存 bundle assets**，不是事後把新截圖當成舊證據。

## 3. 程式上的可解釋機制

以受測候選 `notes.py` 的行號為準：

1. `post_key()`（157 起）對完整貼文 identity 及 list key 計算 key；並沒有以時間欄位單獨去重。本例 P06 的 key 與另外 14 個不同。
2. `_validate_page_overlap()`（233 起）只檢查傳入 key 的上一頁尾／下一頁頭與重複規則；舊 `[P04,P05,P07,P08,P09]` 與鄰頁的交接完全可以符合此規則。**跨頁錨點正確，不等於頁內沒有漏篇。**
3. `page()`（2013 起）驗證傳入 rows、依 identity 產生 key、保存證據，不把原始畫面的每張卡片解析成必須匹配的集合。把多個 viewport 合成一個 page 的清單是 Agent 提供的。
4. `finish_scan()`（2091 起）檢查 session、存在 pages、首頁 `top_reached=true`、末頁 `bottom_reached=true`，再把已提交 rows 取有序聯集，追加 `action=COMPLETE`。沒有獨立的來源貼文總數，也沒有從圖片驗證缺失卡片。
5. `_open_scan()`（1906 起）重播頁面結構及完成清單一致性；`summary()` 中 3165 起的 `scan_coverage` 由是否有 completion 事件投影為 `COMPLETE`。它不是另一個視覺覆蓋檢查。
6. `_coverage_errors()`（2612 起）對目前 scan 已知 posts 檢查 detail／media count。未曾登錄的 P06 不在迴圈裡；後續細盤 gate 無從發現這個整篇缺口。
7. `notes_evidence.py` 保存及驗證 bundle／子件的 bytes、SHA-256、結構與 context；其檔頭明示不證明 GUI 觀察真實。本例 evidence 完整，與 statement 語意過度宣告可以同時成立。

現有 `test_page_overlap_loader_rejects_invalid_shapes`、`test_adjacent_page_overlap_is_accepted`、`test_loader_rejects_scan_completion_posts_mismatch`（`tests/test_notes_regressions.py`）檢查的是給定 rows 的結構／聯集。T5 也要求已登錄貼文的細盤完整；這些都不是「從保存 viewport 逐卡比對沒有漏篇」的證明。本輪只讀測試源碼，未重跑並冒稱通過。

## 4. 事實、推論、未知與替代解釋

**已證事實：**舊原件含可區分的 P06 卡片；舊 rows 沒有 P06；舊完成清單與 rows 相符；新 rows 增加獨立 P06 key；舊／新事件在 `_open_scan()` 的唯讀重播均被接受。23 個相關 bundle 的保存 bytes 檢查均成功，選定事件前後 SHA-256 相同。

**因果判斷：**漏篇發生在 Agent 的觀察整理／page 輸入邊界；現行程式的 `COMPLETE` 是輸入自洽的結果，讓這個觀察缺口延續為完成宣告。這支持需要補足來源卡片到清單的核對責任，不能只修改最後的總數或增加同樣的跨頁 overlap 檢查。

**仍屬推論：**多個 viewport 合成一個 page，且 P05／P06 顯示同時刻，可能增加辨識或轉錄遺漏風險。但沒有 Agent 當時的完整推理／轉錄 trace，不能把「同時刻被合併」或「因文件不支援而故意略過」定為已確認心理原因。也沒有發現日期去重程式的證據。

| 替代解釋 | 本例證據的判斷／可推翻條件 |
|---|---|
| 兩次掃描之間才新增 P06 | 舊 page 自身已保存該卡片，故不是解釋本例集合差的必要原因。若原件來源綁定被證明錯誤，須重開診斷；本輪保存 ref／子件 hash 核對未發現此情況 |
| key 碰撞／finish 去重誤刪 | P06 key 互異，舊 page 輸入沒有該 key；若能找到舊五頁其實已含 P06 的反證，才需改查合併邏輯 |
| 只有最底端判錯 | 漏點位於列表中段且已入鏡；即使底端探測正確，也不修復頁內漏篇。頂底觀察的全面可靠性仍不由本分析簽發 |
| 因不下載 PDF，盤點可忽略 P06 | 現行 Skill 要完整盤點列表；貼文清單與照片／影片下載資格是不同判斷。若要求改成只列有下載資格的貼文，屬範圍／狀態語意變更，需另定計畫，不能倒改歷史 |

**未知：**當時每步原生輸入的完整 raw receipt、精確轉錄決策、是否還有其他未提供的同根因修復嘗試，以及來源列表的全時段原子狀態。本輪不承諾原子快照或證明所有其餘貼文均無漏項；這些未知不妨礙定位已保存的 P06 漏登錄。

## 5. 既有嘗試與新增學習

| 已知活動 | 新資訊 | 能否視為修復 |
|---|---|---|
| 舊五頁掃描，完成 14 篇 | 保存了中段卡片原件，但 page 2 與 finish 宣告覆蓋完整 | 否，是失敗基線 |
| 當次後續 14 頁重掃，完成 15 篇 | 新增 P06；較細的重疊鏈能呈現 P05→P06→P07 | 否，只修正該次 inventory；產品判定與 Skill 未改 |
| 本輪一次唯讀診斷 | 將缺口定位到原觀察→page rows；排除本例的 finish key 誤刪，證明兩種集合都符合 `_open_scan()` 的內部檢查 | 是診斷完成，並非產品修復／正式驗收 |

原 R1–R10／T5 的 scan binding、已知媒體細盤等成果不等同 F01 已修好。本 packet 沒有完整的 F01 修復嘗試帳；保留 `UNKNOWN`，不因換 Session 宣稱次數歸零或尚餘幾次。本輪沒有重新操作 GUI／重掃／重下，也不建議重複舊掃描只為得到相同總數。

## 6. 唯一路由：PLANNER_REPLAN

由 Owner 另行啟動 Planner，輸入本分析、精確候選、測試報告及目前「只下載照片／影片」決策。產出一份**僅針對 F01** 的有界 `plan.md`／`handoff.md`：

- **範圍：**盤點時每個 viewport 的完整／部分卡片、重疊錨點、可區分卡片到 post rows 的對應，以及 finish 前如何查核未解卡片。可評估 Skill／`references/gui-inventory.md` 的最小方法與既有 CLI 能檢查的結構；是否需要程式／事件變更，由 Planner 明列利弊與相容邊界，不由本診斷預先指定新 schema、sensor 或總數 oracle。
- **成功條件：**計畫明列可核對的來源→清單覆蓋準則及缺口停止規則；定義同時刻相鄰卡片、跨 viewport 的高卡片、頁內中間漏篇及來源變動案例；中間漏掉一篇照片／影片時，不能只因頂底與跨頁錨點成立就宣告盤點完整或進入新派送。保留無遺漏的正常案例，明列離線與真實 GUI 驗證各自能證明什麼。
- **產品邊界：**文件／PDF／網頁文件不下載；它們仍是辨識相鄰卡片與列表覆蓋的來源，不應靠跳過整篇消除 F01。F02–F18、M09 kind、`NO_MEDIA` 的分類改造、chooser／outcome 證據、既有完成事實與真實帳本更正均不併入本包。
- **相容與資料：**不得覆寫舊 `COMPLETE`、重建空帳、rekey、重下完成項或改寫 UNKNOWN。若提議機械變更完成語意／事件／公共介面，必須先明列並由 Owner 決定範圍及適用審查，不能在 Implementer 階段暗加。
- **停止條件：**需要另一 finding、真實資料更正／遷移、GUI 前景、下載授權、controller 或超出 F01 的狀態改造時，記錄具體邊界並交回 Owner。缺證據就保留未完成，不追加一個自我聲明來冒充視覺驗證。

待人工決定的是採納這條 F01 規劃路線並交接下一角色；本輪不替 Owner 核准新計畫、不啟動後續角色，也不要求現在送 Acceptance。

## 7. 實際診斷與證據 hashes

工作目錄為 repo 核心目錄；Python 3.9.6。本輪保存的診斷命令如下：

```sh
PYTHONPATH=src /usr/bin/python3 -B .local/line-backup/tasks/20261102-notes-f01-scan-review/diagnose_f01.py
```

實際執行 stdout／stderr 分別導向同目錄的 `diagnostic.stdout.json`／`diagnostic.stderr.txt`，**exit 0，stderr 0 bytes**。腳本只讀選定事件／證據，對記憶體事件呼叫 `_open_scan()`，並呼叫純讀取的 `load_saved_evidence()`；未建構 `NotesRecords` 實例、未執行帳本 CLI、未取得真實帳本鎖或寫 events。這不是完整 loader／整本 audit／正式最小回歸。

腳本內保存的 Git 命令均 exit 0：`git status --short --branch`、`git rev-parse HEAD`、`git diff --exit-code 260a49612cb3f7570a57f135921b4101e2c8ee99 7a3045aa2ac5b13b4e0b9186f5884c846f402583 -- src tests .agents AGENTS.md`、`git ls-remote --heads origin feature/line-notes-media`。argv／cwd／stdout／stderr／exit 在 `commands.jsonl`。本機圖像檢視無 shell exit code；其結果只記 `OBSERVED`。

| 來源／產物 | SHA-256 |
|---|---|
| `測試報告.md` | `8c718e33cdf85359897f39e086a118503d1600b5e765008746b68d5b575f2da6` |
| 候選 `notes.py` | `34ff6be9c6e9f74d2c450f3cc91aa8c6d1a0043cd0daef60f0680070b0e43247` |
| 舊 page 2 event（sequence 6） | `4f943f70864fd1d10dcb2aec435253038c0c47f8347900084421730d4e195664` |
| 舊 page 2 statement | `72c38d81b15c959d72b0e5c72f4f0373cb661d0f5fde5763bb72514b1904c0bd` |
| 舊觀察 `scan-down-04.png` | `9222a29b71ae4807c5b3243b15d8550bc8dcfff25dd23ed7f24b9cc5a9ee3fb3` |
| 舊觀察 `scan-down-05.png` | `2f7dbcd3ebbdcdfb495b14c2efce8e4894aaec8a46059c5ce8d2b6a6f280a8df` |
| 舊 finish statement | `cfc6796a6e9bf5dddf0812c116bd21418466b9758d585594edb4a04fb0af50ce` |
| 新 finish statement | `7407516a9ab68bab0b81431bff9797c0c1af995413be0c577436fbbebe6399f1` |
| 本輪 `diagnose_f01.py` | `c970fa0b374f12659ec6b5703f92e4cc7a193c2f86c600af9c3412bbe68a4d30` |
| 本輪 `diagnostic-result.json` | `f5b9add77d1fb06d179ef503db23fcf1eaf84fb19d1dac3fc0742e4740d062ac` |
| 本輪 `source-manifest.json` | `634d47215789112b2b83e614d77726eba6b4e7cc27ac56c0c618fcbaa42c7dc5` |

manifest 包含納入診斷的來源位置、證據及腳本 hashes，保留私有不提交。原報告中 73／136 tests、10 個照片完成與 audit 結果是**前輪報告的已保存成果**，本輪未重跑、未重新驗證照片，也未將其升格為 Acceptance。文件差異及交付檢查另見 [progress.md](progress.md)。

## 8. 六項狀態與交接

```text
PRIMARY_OUTCOME_STATUS: ANALYSIS_COMPLETE
IMPLEMENTATION_STATUS: FIX_REQUIRED
CORE_ACCEPTANCE_STATUS: NOT_RUN
REQUIRED_VERIFICATION_STATUS: NOT_RUN
INDEPENDENT_ACCEPTANCE_STATUS: BLOCKED
TASK_CLOSURE_STATUS: BLOCKED
```

診斷已可交接；`FIX_REQUIRED` 表示 F01 尚未修復。離線診斷成功只屬本角色證據，產品修復後回歸與正式 E2E 本輪均 `NOT_RUN`。原測試報告／產品的未解 finding、完成照片事實與 `external_copy_verified=false`／`real_line_e2e=NOT_TESTED` 均保留。Owner 下一步可攜本分析人工啟動限定 F01 的 Planner；不在本 Session 跨角色修復、重測或結案。
