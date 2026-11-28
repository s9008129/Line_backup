# issue-analysis：記事本 viewer 控制發現鏈中斷

## 判定與下一個角色

**ANALYSIS_COMPLETE；唯一建議路線：`TARGETED_DIAGNOSTIC`。** 本輪已直接檢查事發原件，取得比前輪規劃更強的診斷依據；仍不把尚未驗證的 hover、LINE 缺陷或 Agent 違規宣告為已確認根因。

**下一個角色是「有界診斷執行 Agent」**：由 Owner 另開原生 Computer Use Session，僅執行本文件第 7 節的控制可觀察性對照，不改產品、不建 intent、不下載。這是一次事故診斷任務，不是新設 Harness 正式角色，也沒有虛構的第 08 號角色 Prompt；目前沒有已證明、可直接交給 Implementer 的產品修復。`06_high_reasoning_review_prompt.md` 只做診斷，本輪不自行執行建議。

最深、可支持的因果解釋是：**現有流程已能取得媒體內容及帳本資格，卻尚未建立從當前 Notes viewer 到可辨識下載控制的實證方法；事發觀察只隨縮圖切換改變媒體與焦點，沒有隔離 viewer 外框顯示狀態及觀察來源。安全閘門因此保持關閉。** 前半的流程／證據缺口可確認；究竟由哪個 UI 機制使控制不可見，仍須下述最小對照才能判定。這不是把「缺證據」冒充 LINE 本身的物理根因。

## 1. 單一問題、版本及授權

- 問題身分：`R-NOTES-CONTROL-OBSERVABILITY-01`，沿用原問題，不因換角色／模型重新計算嘗試。要解釋的失敗是五個媒體仍 PENDING，無法安全建立第一筆 intent。
- 工作區：`/Users/hsiaojohnny/dev/Line_backup`，分支 `feature/line-notes-media`；本輪輸入 HEAD `e8586aa42f9a3600936adf4b58577eef696e5e99`。
- 事發產品 HEAD：`02db924fd89ff79067cd4958729a3ac6b8157437`；問題提報 HEAD：`40a7b09e9900eddab2df9bfd81aad9ec25b89c1f`；前輪規劃 HEAD：`e8586aa42f9a3600936adf4b58577eef696e5e99`。後兩次只有文件新增，未修產品。
- 本輪來源包：原問題提報單、前輪 plan／handoff／analysis、同次事發 AX／截圖／輸入紀錄、命令收據、來源規範與必要官方文件。不是全域私人資料搜尋，也沒有讀真實帳本 events 或下載媒體目錄。
- Owner 本輪明示高推理根因診斷與矯正計畫，並要求告知下一角色及 add／commit／push；允許保存診斷文件。不包含 LINE 新輸入、真實資料變更、產品修正或派另一正式角色。
- 可寫：本任務的 issue-analysis、來源 manifest、progress，以及專案私有診斷 artifacts。既有提報單、plan、handoff、Skill、程式、帳本與照片均保留。
- 主代理參與前輪 Planner，因此本報告不是獨立 acceptance，也不以研究助手當正式獨立審查。

## 2. 第一性原理：哪個必要條件尚未成立？

完整備份至少需要六件互不替代的事：

| 必要條件 | 要證明的命題 | 本次證據狀態 |
|---|---|---|
| 來源身分 | 這是授權列表的指定貼文／媒體 | 有事發來源脈絡與盤點紀錄；不以名字／總數單獨認領 |
| 不重複 | 沒有受保護完成或未決派送阻擋本項 | 事發 summary 無 unresolved attempt，五筆 PENDING |
| 可執行控制 | 當前可辨識、可定位且作用屬此 Notes 媒體的下載控制 | **未證明** |
| 可追溯派送 | intent／目的地先持久化，單次控制與 chooser 輸入有原件 | NOT_RUN |
| 可歸屬結果 | 同 attempt 的正面終結結果及穩定檔案 | NOT_RUN |
| 完成驗證 | 數量、非空、hash、解碼與 completion 讀回 | NOT_RUN |

因此，更多 scan／post／media 簿記不能補上控制；修改 summary 文字不能讓控制出現；先建 intent 只會新增可能已派送的交易負擔。安全停止保護了資料，但不證明整個產品已具備自主完成能力。

需要分開兩種產品要求：**安全性**是沒有可靠控制就不派送；**可完成性**是存在工具能執行、Agent 能從日常 Skill 找到的安全操作路徑。現有證據支持安全閘門有作用；可完成性尚未有此 viewer 的實證見證。矯正必須補這條路徑，不能靠放寬安全閘門換取表面進度。

## 3. 直接原件的新發現

事發來源根目錄為 `.local/line-backup/tasks/daily-notes-20261112-3972c6285a/`；公開報告只列技術檔名與遮蔽結論，不提交原圖、作者／群組名稱或貼文內容。完整來源 hash 留本機 private manifest，關鍵引用另列於 [issue-analysis-sources.json](issue-analysis-sources.json)。

### 3.1 原圖與 AX 並不呈現相同的 UI 可見性

| 原件 | 本輪直接檢視所得 | 可支持與不可支持 |
|---|---|---|
| `observations/photo-open-after.screenshot.bin`，1/5 | 有原生標題列與三個視窗鈕；下方有五格縮圖 | 支持此時外框可見；仍未見能辨識為 Notes 下載控制的項目 |
| `observations/viewer-02..viewer-05.screenshot.bin` | 後四張沒有同樣可見的標題列，內容／黑色區域與縮圖仍在 | 支持外框呈現改變；不證明 hover、自動隱藏、焦點或截圖方式哪個造成 |
| 上述五份 `.ax.txt` | 扣除視窗標題與 focused-element 敘述後，元素列逐字相同；五份均有關閉／縮小／縮放角色，均無下載／儲存標籤 | **AX 結構相同不能代表視覺外框相同**；也不能證明下載控制存在或不存在 |
| 五份 AX 焦點 | 依序為視窗 0、縮圖文字 5／7／9／11 | 焦點與媒體同時改變，不是控制單一變項的實驗 |

這個新發現直接限制了「最後一次 AX／截圖沒有控制，所以已充分排查」的解釋：至少已知 viewer 的外框可見性不是常數。**但視窗標題列不是下載工具列**，不能從標題列有變就推導下載按鈕一定能被 hover 叫出。

### 3.2 操作紀錄只證明已做媒體切換

`photo-open.input.json` 記錄從已展開卡片的第一格進 viewer；`viewer-02..viewer-05.input.json` 記錄各按下一格縮圖，raw return 均記為 undefined。原件支持來源序列與輸入紀錄存在，不能由 undefined 推導成功派送或未派送。

在此 task 保存的 viewer 原件中，沒有同一媒體、同一幾何下的「不同觀察來源」或「只有指標位置改變」對照；也沒有保存事發 CUA 完整能力文件。因此不能說當時一定有 hover API、一定沒有其他安全方法，或已經耗盡所有可用觀察。

`inventory/media-C0-items.json` 的種類理由包含「photo toolbar」與「沒有影片播放控制」的 Agent 敘述；本輪不能將這些自述當成已驗證下載工具列存在的證據。媒體種類是否需要更正不是本輪選定根因，不擴張成帳本更正任務。

### 3.3 關鍵事發來源已重新核對

提報單列出的五份 SHA-256 均與本輪讀回相符：第 5 張 AX、第 5 張截圖、final summary、source card ledger、media CLI stdout。這次有原件讀回支持，不再只轉述前輪報告。hash 相符只證明 bytes 身分，不證明 Agent 的文字判讀必然正確。

final summary 實際內容：scan COMPLETE、PENDING=5、COMPLETED=0、UNKNOWN=0、unresolved_attempts=[]、restart_batch_open=false、all_known_media_complete=false。NOT_APPLICABLE=5，沒有可供驗證的下載成果。

## 4. 最小失敗軌跡與既有嘗試

以下是從保存紀錄重建的失敗軌跡，**本輪沒有重播**：

1. 當次綁定記事本列表，完成 scan；`scan finish` 的命令收據 recorded_at 為 2026-11-11 18:19:00 UTC（臺灣 11 月 12 日 02:19），child／outer exit 均 0。
2. 保存兩篇貼文；一篇 NO_MEDIA，另一篇進 viewer，依序觀察五格來源。
3. viewer 縮圖切換後仍未辨識下載控制；保存五項 media，命令收據為 18:29:37 UTC，child／outer exit 均 0。
4. 在 intent 前停止；final summary 收據為 18:33:41 UTC，child／outer exit 均 0。

精確 GUI 輸入時刻仍 UNKNOWN；CLI recorded_at 不是 GUI 時鐘，不用檔案 mtime 反推。保存的 22 份 CLI request／result 均 child_exit=0、outer_exit=0，沒有 intent／outcome／reconcile／verify／restart 命令；此結論只涵蓋已保存收據，不是 OS 層無副作用保證。

| 先前工作 | 已取得的新資訊 | 不能推論／本輪處置 |
|---|---|---|
| 原日常任務：完整盤點與五格 viewer | 來源序列、帳本狀態、intent 前停止 | 五次換圖不是五次控制發現實驗；不以換圖次數充當方法對照 |
| 問題提報單 40a7b09 | 整理停止點與原件引用 | 不等於根因已證實 |
| 前輪 Planner e8586aa | CLI 語意與安全邊界、候選及草稿 | 未直接看原圖；不能把規劃完成叫根因完成 |
| 本輪診斷 | 原件 hash 讀回、五圖／AX 對照、22 收據、規則因果核對與官方範圍查證 | 有實質新資訊；仍欠受控的控制顯示對照 |

目前未做產品修復或新 GUI 控制揭露實驗，沒有證據可聲稱已用掉精確幾次根因修復額度，也不能宣告額度歸零。下一執行者須沿用可得嘗試歷史；最多三次有證據嘗試、兩次連續無新資訊即停止，不以新 Session 重置。

## 5. 因果主張、反證與替代解釋

**選定主張 C1（推論，信心中）：控制發現所需的 UI 狀態／觀察來源未被區分，現有操作知識亦未提供已驗證的揭露路徑，使流程停留在「有媒體、無可證明控制」。**

支持鏈不是單純「沒找到」：原圖顯示外框狀態有變；AX 卻不反映這個變化；輸入紀錄改變媒體及焦點而沒有隔離變項；reference 只提供控制判定與觀察分界，沒有此 viewer 的實證發現方法。這些共同支持先修補觀察／能力證據，不支持先改 CLI。

| 替代解釋 | 現有證據如何約束 | 能推翻／改判 C1 的證據 |
|---|---|---|
| 本來就有明顯控制，Agent 漏看 | 本輪五張原圖未辨識明確 Notes 下載控制；圖片內容中的其他系統按鈕不能算 LINE | 指出原圖中可唯一歸屬 LINE 的真實控制，並證明作用及當次映射；改判感知遺漏 |
| hover／焦點導致控制隱藏 | 外框有變、焦點有變，但媒體與時間也改變 | 同一 viewer／幾何，單一指標／焦點變項使控制穩定出現；才能確認具體機制 |
| 下載入口在別的 Notes 上下文 | 未取得必要對照；現有 AX 關閉鈕不等於返回後必定有下載入口 | 有當次可靠返回與同貼文連續證據，且該處控制可證明；改判入口選擇問題 |
| CUA 捕捉來源漏獨立層 | app-bound 原圖不能代表整個桌面；沒有桌面來源對照 | 同狀態、相同時間範圍下，允許的局部桌面畫面顯示控制而 app-bound 不顯示 |
| LINE／來源真的不可下載 | 沒有可歸屬的到期／服務／限制訊息；精確版本未記 | 有當次直接狀態訊息或可重現的版本能力限制；才可改判環境／來源阻塞 |
| 安全規則形成邏輯死結 | `gui-inventory.md:112–119` 仍允許有據導覽、更換觀察來源；沒有先 intent 才能觀察的條文 | 必須證明所有必要的非派送觀察都依賴被禁操作；目前沒有這項證據 |
| notes CLI 出錯造成控制消失 | 22 份 child exit 0；模組不操作 GUI；原圖在 media 命令前已呈現差異 | 需具體 GUI 副作用程式路徑／可重現 trace；固定 false 或空 blockers 都不是 |

「不得猜關閉」也不能讀成「所有當次 AX 關閉鈕都禁止」。但 AX 有關閉角色，只證明該角色存在，不保證一定返回原貼文；本輪不替沒有當次作用證據的關閉／右鍵背書，也不據此判定 Agent 違規。

官方範圍核對同樣沒有替 hover 提供 Notes 的因果證據：[LINE 記事本說明](https://help.line.me/line/?contentId=20000246&lang=zh-Hant) 確認 Windows／Mac 可夾帶圖片與影片，該頁未給本 viewer 儲存入口；[相簿說明](https://help.line.me/line?contentId=20000248) 的移鼠儲存流程屬相簿。這兩份一手資料不能把相簿 hover／Save as 移植到記事本，也不能因官方文章未寫就斷言功能不存在。

## 6. 矯正目標與可保證邊界

矯正目標是補出一條**不派送、能區分觀察來源與顯示狀態、可回到原件檢驗的控制發現鏈**。這個目標直接針對 C1，成功標準不是「有再點一次」或「再加一份報告」。

不改 intent／UNKNOWN／禁止重送規則，不將 GUI gate 塞進 CLI summary，不加控制器，不加固定座標或相簿 fallback。普通可逆導覽在真實日常授權與有效前景內本已可自主進行，不新增每點請示；本輪診斷沒有新的前景，故不操作。

無法保證外部 writer 不變、服務端快照、焦點持續、未被截取的 UI 不存在，或原生 exactly-once。診斷結果只涵蓋指定版本／viewer／來源／輸入條件。媒體載入就緒、實際派送、chooser、下載結果、檔案驗證與獨立接受仍是不同命題。

## 7. 唯一建議路線：TARGETED_DIAGNOSTIC

### 執行角色、輸入及路徑

由 Owner 另開**有界診斷執行 Agent**，使用原生 Mac Computer Use；這是一次診斷交辦，不是用 04 Implementer 或 05 Acceptance 啟動真實備份，也不替換日常正式 Prompt。此角色名稱是任務責任描述，不新增 Harness 檔案或流程框架。

Owner 提供本報告精確 commit，手動開啟同一 Notes 貼文的可核對 viewer，明示本次只做下列非下載觀察並交接前景。正常備份之後仍從單一記事本列表使用手冊 B 區正式 Prompt 開始，不要求日常使用者攜帶本報告。

診斷只可新增本任務 `control-observation-report.md` 與來源 metadata；原件放新的專案私有 task 子目錄，不修改歷史資料、Skill 或程式，不寫真實帳本。作用與列表連續性有歧義時，停下釐清，不依中文名稱認領。

### 一次有界實驗

1. **先讀當次工具文件。** 記錄能否取得 app-bound AX／截圖、指定局部桌面畫面、window frame 及無點擊移鼠。不存在的 API 標不支援，不猜名稱、不以 click／drag 模擬 hover，不換執行器繞過能力缺口。
2. **固定同一個媒體，不再切五格。** 記錄當前 app/window、來源脈絡、就緒、焦點、幾何、觀察範圍、時間及已知指標狀態。以當次支援來源取得一組基線；未知欄位保持 UNKNOWN。
3. **先做來源對照，不輸入。** 同一 viewer 狀態取得工具允許的最小局部畫面與 app-bound 來源，核對窗口／媒體／焦點沒有改變。不同來源不是同一原子快照，應記時間差與漂移，不能互相補造控制。若只有一種來源，明示來源對照 NOT_RUN。
4. **只有能力及目標作用有據，才做一次狀態對照。** 若仍未定位控制且工具明確支援無點擊移鼠，在可靠、非下載／分享控制的 viewer 區域移入一次，立即重觀察；保持同媒體與幾何，記前後焦點、指標及時間。無法成立就停止該方法，不猜右鍵、關閉、快捷鍵或點照片中央；本次不擴展探索其他頁面。
5. **交回判定並停止。** 有候選控制就列它屬於 LINE／此 Notes 媒體的依據、作用、可見／可用狀態及映射；僅見圖示而作用未知仍記 UNKNOWN。無控制則列來源與能力已實測邊界。全程不建 intent、不點下載、不開 chooser、不分享、不更動帳本。

這份實驗不是要求一定證明 hover 有效，而是用最少新資訊分開「AX 缺標籤」「app-bound 範圍」「viewer 狀態」與「沒有可用能力」。不重做全列表盤點、五格切換、空 summary 或相同靜態截圖來充當進展。

### 成功檢查與停止條件

- 必須交付至少一項原件可重核的新區辨：來源不同造成控制可見性差異、單一狀態變化造成差異、當前已清楚控制但前輪漏看，或工具能力明確不足以執行必要對照。
- 若主張某方法是矯正方法，必須能說明它如何在未建 intent 的同一 Notes viewer 取得控制歸屬及定位；沒有證據只能交回診斷結果，不能將方法寫成已驗證。
- 前景中斷、身分／作用／映射不明、工具拒絕、非預期 chooser／派送、來源變動或需要越過此路徑／權限時立即停止；不得用新目錄、重掃或換入口續送。
- 同根因最多三次有證據嘗試；相同方法連續兩次無新資訊立即停。不得為用完額度重試。本次沒有許可下載測試或影片／混合附件／跨 Session 擴測。

診斷結束後由 Owner 決定後續修改。若它證明可重用方法只缺於 reference，才有依據把具體方法整合至日常 Skill；沒有方法時不造空實作。**本報告不另外推薦第二條角色路線，也不派 Implementer／Reviewer。**

## 8. 命令、證據與本輪限制

本輪實際執行的類別及結果：

| 命令／工具 | 結果 | 證據範圍 |
|---|---|---|
| `pwd`、Git status／branch／HEAD／worktree | exit 0；基準 e8586aa，僅既有 untracked | 私有 preflight；未碰其他 worktree |
| `cat` 06 Prompt、全域 policies、AGENTS、前輪文件；`rg`／`sed`／`nl` 相關 references | exit 0 | 規則與來源閱讀；不是產品測試 |
| Python 列舉選定 task、讀原件 hash、提取 summary／request／result | 成功讀回；5 份既有 hash 相符 | 私有 source manifest、遮蔽 timeline |
| `file .../viewer-05.screenshot.bin` | exit 0；JPEG，1280×960 | 實際影像格式／大小，不能因副檔名是 bin 當作無法檢視 |
| `view_image` 五張原始 viewer 圖 | 全部成功；本輪直接檢視保存影像 | 不是當前 LINE 實機觀察；不標人眼 OBSERVED 或 E2E PASS |
| Python 比較五份 AX 元素與焦點 | exit 0；非視窗元素列 hash 一致，焦點 0／5／7／9／11 | 私有 viewer-comparison.redacted.json；不抹除視覺差異 |
| 首次 timeline 工具使用一層 glob | exit 1，IndexError；只產生不完整診斷 artifacts | 本輪工具呼叫錯誤，不能據空清單宣稱沒有收據；未派送產品命令 |
| 修正為兩層 glob 讀回 | exit 0；22 份 child／outer exit 都為 0 | 修正只作用於診斷 artifacts；保留該錯誤，不誤報產品 exit 70 |
| 官方網頁查證與兩名原生繼承派送助手 | 已回傳可引用來源與規則分析 | 同角色研究；沒有 model override、沒有獨立 acceptance |

私有診斷目錄：`.local/line-backup/tasks/20261112-notes-download-control-high-reasoning/`。原件不修改、不提交；本輪 metadata 收尾需重算已讀來源 hash，確認診斷未更動它們。Git 交付只涵蓋本報告、遮蔽來源 metadata 及 progress；提交／推送結果由實際收據與最終回覆補足，不預填成功。

未知仍包括：事發精確 LINE／macOS 版本、原始 CUA 完整能力文件、精確 GUI 時間／指標／幾何、控制真正位置及觸發條件。這些未知阻止「hover 已證實」之類結論，**不妨礙給出上述有界、能取得新資訊的診斷建議**，所以本角色判 ANALYSIS_COMPLETE，而非產品根因已全部確定。

## 9. 六項狀態

- PRIMARY_OUTCOME_STATUS: BLOCKED（五張未備份；底層控制顯示機制未實證）
- IMPLEMENTATION_STATUS: NOT_RUN
- CORE_ACCEPTANCE_STATUS: NOT_RUN
- REQUIRED_VERIFICATION_STATUS: PARTIAL（事發原件／hash／來源核對；真實下載、解碼與 completion NOT_RUN）
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
- TASK_CLOSURE_STATUS: BLOCKED

本輪診斷文件已可交接；產品回歸、GUI 實驗、下載、chooser、解碼、completion、跨 Session、正式獨立接受均 NOT_RUN。不以文件、hash、Git 或研究助手結果替代實機接受。
