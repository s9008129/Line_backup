# 接手 Agent 的交接 Prompt（可直接貼給下一個 Implementer）

你是本任務的 IMPLEMENTER。請在 /Users/hsiaojohnny/Documents/ChatGPT/Line_backup 工作，先完整讀取本文件、同目錄的 diagnostic-spec.json、plan-contract.json、handoff.json、authorization.json、source-manifest.json，以及 plan-as-submitted.md、plan-review-01.result.json。先核對 source-manifest.json 的來源雜湊及 plan-contract.json 與 handoff.json 的逐位元等值，再依下面的順序實作；不要執行舊 agreement.py、analyze.py 或舊 OCR binary，因為它們會寫回舊 task。

目標是完成一次固定新方法的「LINE 相簿盤點診斷：替代證據規則」，修正把波動的分頁 OCR 當成每幀必要條件的問題。只可在 harness-development/catalog-diagnostic-continuity-replan-20261010/ 新增候選程式、建置與驗證材料，不可改產品、config、state、registry、舊 task、照片或公開 schema。既有三次根因方法嘗試已用完；使用者另外明確授權一次固定新方法的離線回放、反向測試及一次最多六次無下載 scroll。新 task、process、frame 名稱都不能重設這個額度。不得自行增加第二個候選方法、重新跑一次實機、調整失敗後的判定政策，或派出 helpers/writers。

先建立不可覆寫回放副本，再實作固定候選與離線測試。介面連續性用本次初始化後凍結的完整文字槽 RGBA 比對，選中指示獨立檢查，日期／張數身份、位移及順序重疊分開判定。保留 scan-003 的原始「相溥」，不可替換成「相簿」或以 confidence 門檻篩掉。集合相同仍可能有移動；transport RETURNED 與 AX 值都不能單獨證明效果。所有負向測試及四幀回放通過，且獨立程式／證據審查 PASS 並綁定同一 candidate hash 後，才協調使用者就緒並取得新的 LINE 前景。這是就緒協調，不是重問既有群組、路徑或追加驗證授權。

實機只允許 documented CUA getApp、getAXStateAndScreenshot 與 App.scroll。每步一次向下 0.25 page，總輸入上限六次；禁止 click、鍵盤、Page Down、setValue、相簿開啟、選單、Save All、chooser、下載及 canonical state 寫入。每步先保存／讀回 pretrace，單一輸入後 fresh 觀察、保存，再驗證。UNKNOWN effect 只允許兩次唯讀觀察，不可重送任何輸入。必要 binding、安全、身份、移動或重疊未知／衝突，立即停止；不要為了達成六步而補捲。

本輪已有其他模型的本地獨立 Plan Review PASS；原審查四份材料不可改寫。實機前獨立程式／證據審查與最終獨立 Acceptance 仍必須完成。controller admission 為 BLOCKED，本地文件不能解除它；不得偽造 stage packet、native identity、validation receipt、controller-native PASS 或 DONE。如果正式 runner 不可用，保存本地結果和可轉交封包，明確區分離線、實機、保存及正式 admission 的狀態。完成後交付實際證據及六狀態，不宣稱完整相簿列表、通用可靠性或自動備份完成。文件交付時的 Git 提交只授權文件作者發布本交接；你後續實作沒有新的 commit/push 授權。

---

# LINE 相簿盤點診斷：替代證據規則 — 精準實作交接

## 1. 文件地位、優先順序及現在的事實

這是交給下一個 Implementer 的本地實作封包，不是已入場的 controller Handoff。03_handoff_prompt.md 的預設角色是 Optional Handoff Reviewer；使用者明確改為直接撰寫交接，因此本次沒有再啟動独立 Handoff Review。補充訊息確認已由其他模型完成 Plan Review，並要求保留其全部生效條件。

規則優先順序：使用者最新指示 → 本次授權記錄與已審查計畫 → 本交接的機械細節 → runtime 的 documented CUA API。機械細節不得改變審查後的路徑、四道 gate、證據政策、追加額度或停止規則。若發現文件互相衝突，停止相依操作並保存具體衝突，不自行選擇較寬鬆的版本。

已取得的事實：
- plan-as-submitted.md 已存檔；完整 SHA-256 以 source-manifest.json 為準，已知值為 d8e0031fa8ef1d7a0a0f260de3682db26421d5779dffc1d1fd1a124969bc5387。
- plan-review-01.result.json：PLAN_REVIEWER / PLAN_REVIEW，candidate_fact=PASS、validation_fact=VALID、routing_fact=HANDOFF；僅計畫層級。本地 fixed offline validator 紀錄另存，不是 controller receipt。
- 原始六狀態為 NOT_ACHIEVED / NOT_STARTED / NOT_RUN / NOT_RUN / PENDING / IN_PROGRESS。
- 四個 scan-000..003 原圖實際都是 JPEG 654×1286；.png 副檔名不能當格式。scale2 derivatives 才是 PNG 1308×2572。
- scan-003 是第四個画面、第三次 scroll；modern 原結果為「相溥」，legacy 為「相簿」。舊 failure 是 header/tab agreement missing。
- 審查者保存的探針顯示歷史畫面 display y 0..192 的標題／分頁帶 bit-exact；y 192..200 附近有 JPEG 耦合差異。這些座標只說明歷史材料，禁止當新執行 ROI 或操作座標。
- 原診斷已使用三次根因方法嘗試，三次實機 scroll；前兩步成功、第三步 FAIL。原結果與六狀態保持原樣。
- 所有新方法實作、OCR 回放、反向測試、六步實機及 final Acceptance 尚未由本交接執行。

必讀原始材料只限相關來源：
- 舊 task：harness-development/catalog-diagnostic-20261010/。
- 現有批次集合進展的整合風險：src/line_backup_batch/observations.py 的 catalog()。本單元不修改它；只以測試避免在新診斷重製 keys!=prior 的錯誤。
- Harness 4.8 資源從 /Users/hsiaojohnny/.codex/AGENTS.md 相對解析；不可使用另一個 task 的 4.9 invitation 或 stage packet。
- LINE 技能的 fresh/context/single-input/effect/overlap 安全規則適用；本單元不是 backup/resume transaction，沒有 writer、intent 或下載權限。

## 2. 授權、四道 gate 與流程

唯一可寫目錄：
harness-development/catalog-diagnostic-continuity-replan-20261010/

現有 handoff／spec／contract／authorization／manifest／審查材料為凍結輸入，不可覆寫。Implementer 只能新增下列子目錄中的檔案：
- candidate/：Python evaluator、Swift offline helper、測試、固定 profiles。
- replay/：原始材料的不可覆寫副本與來源 manifest。
- build/、module-cache/、tmp/：編譯輸出和暫存。
- offline-validation/：一次固定方法的回放、測試和 stderr/stdout。
- live/：唯一一次實機的 observations、trace、OCR、判定與 manifest。
- results/：進度、preservation、attempt ledger、獨立審查與角色結果。

STANDARD；max_parallel_read_only_helpers=0；max_parallel_writers=0。不能自行使用 subagent 做實作，也不建立 worktree、改 branch 或 index。

四道 required gate：
| Gate | Owner / phase | 證據及 PASS 條件 |
|---|---|---|
| G_OFFLINE | ROLE / IMPLEMENT | 副本 hash、固定 source/build/profile、四幀回放和全部反向測試均有實際 PASS |
| G_LIVE | ROLE / IMPLEMENT | 同 candidate 的實機前独立審查 PASS；新就緒與 binding；最多六次輸入中六步皆有實際 fresh continuity、身份、位移、順序重疊證據 |
| G_PRESERVE | ROLE / IMPLEMENT | old task、產品／config／state／registry／照片與 Git 的實際 baseline delta 為零；本次文件發布的已授權 commit 先完成，Implementer 再建立自己的起始 Git baseline |
| G_ACCEPTANCE | ROLE / ACCEPTANCE | 非 contributor 的獨立 reviewer 只讀最終 candidate 與實際證據，核對上述三道 gate、範圍及六狀態，明確 PASS |

前三道 gate 的 CORE/OUTCOME/HARD_CLEAN（保存為 SUPPORTING/MUST_NOT_BREAK/BASELINE_DELTA）及最後 Acceptance 的 enum 詳見 plan-contract.json。全部 evidence_source=ROLE_OBSERVATION。視覺／人工判讀單項只記 OBSERVED，不冒充機械 detector PASS。

流程順序不得交換：
1. 核對封包和授權；基線保存。
2. 建立 replay 副本。
3. 實作並固定一個 candidate。
4. 一次離線方法驗證：保留舊 OCR 回放、新局部 OCR及全部負向測試。
5. 獨立程式／證據審查；root 不得自行代簽。未取得 PASS，就保留離線事實並停止在前景之前。
6. 就緒協調、fresh bootstrap、唯一六步上限實機。
7. 保存核對與獨立 Acceptance，按實際 gate 結果報告。

獨立角色可由適用的已註冊獨立 session 或使用者轉交本地封包完成。沒有可核對的實際結果就標 PENDING/BLOCKED，不能以審查者名稱或 shell exit 代替完成。controller admission 另行保持 BLOCKED。

## 3. 實作檔案與命令介面（只在 candidate/ 新建）

使用 macOS 已有 Swift、Foundation、ImageIO、CoreGraphics、Vision，Python 3 標準函式庫。不要安裝 Pillow、OpenCV 或其他套件，不使用 AppleScript、shell GUI automation 或直接 AX 輸入。

實作以下檔案，名稱固定：
- candidate/offline_vision.swift：只讀影像；decode、crop、recognize；不得擷取螢幕或輸入 UI。
- candidate/catalog_diagnostic.py：artifact binding、ROI 比對、OCR parser、row pairing、位移／overlap、決策。
- candidate/run_offline_once.py：建立固定驗證 manifest，執行一次已宣告的方法組合，不調參搜尋。
- candidate/test_catalog_diagnostic.py：stdlib unittest，使用 in-memory 改動的測試資料，不修改任何原圖。
- candidate/profiles.json：本章與第5章的固定 OCR profiles，驗證前凍結。
- candidate/README.md：實際編譯／執行命令和依賴；不要以 README 聲稱尚未執行的 PASS。

必須提供的 CLI（以下是待實作的介面，不是現有命令）：
~~~
python3 -B candidate/catalog_diagnostic.py prepare-replay --source OLD_TASK --out replay
python3 -B candidate/catalog_diagnostic.py verify-packet --packet-root TASK
python3 -B candidate/catalog_diagnostic.py evaluate --mode replay|live --binding FILE --frame-manifest FILE --modern FILE --legacy FILE --previous FILE_OR_NONE --out NEW_DIRECTORY
python3 -B candidate/run_offline_once.py --task-root TASK
python3 -B -m unittest discover -s candidate -p 'test_catalog_diagnostic.py'
~~~

Swift subcommands：
~~~
offline_vision decode --input IMAGE --out NEW_DIRECTORY
offline_vision recognize --input IMAGE --profile PROFILE_JSON --roi ROI_JSON --out NEW_DIRECTORY
~~~

所有命令：
- 只接受正規檔案，不跟隨來源／輸出 symlink；輸出使用 exclusive creation。已存在代表不能重跑覆寫，立即非零退出。
- 檢查每個 subprocess exit code，保存真實 stdout/stderr；禁止命令失敗後印出假成功。
- 無參數或不支援格式要清楚失敗，不能隱式使用其他 task、root、profile、OCR binary。
- 不從 cwd 或歷史文字猜群組／備份路徑；唯一 project_root 是本文件所列根目錄，身份來自其 config 與原有 user-confirmed alias 證據。
- Swift compiler 的 -module-cache-path 指向 TASK/module-cache；TMPDIR 指向 TASK/tmp；Python 加 -B 並關閉 bytecode 寫入。已無 global package 安裝或 global cache 修改授權。
- 建置本身不算方法成功。freeze candidate-manifest 後任何 source/profile 改動都使舊測試與 pre-live review 不可重用。

## 4. 回放材料與基線

replay/ 必須逐 bytes 複製：
- scan-000..003.png、各自 .scale2.png、.ocr.json、.modern_ocr.json、.transform.json、.ax.txt。
- step-001..003.pre.json 和 .action.json。
- scan-000..002.agreement.json、scan-003.failure.json。
- baseline.json、preservation.json、report.md、implementer.result.json、plan.md、plan-contract-02.json、handoff-02.json。
- 需要初始化來源確認時讀取 initial.png、frame-000.png 及 baseline.json 的 historical_user_confirmation；不要把歷史時間缺失補成現在。

manifest 每筆包含 source_path、copy_path、bytes、source_sha256、copy_sha256、實際內容格式。副本與來源 hash 必須相等；複製期間來源漂移就停止。

在任何 candidate 或驗證前，保存 IMPLEMENT 起始 preservation baseline：
- config/line_backup_config.json、state/backup_state.json、state/run_log.md。
- 全部舊診斷原始材料、現有產品 dirty/untracked 檔案，以及 backups/ 與 registry 所在 state 的檔案清單／逐檔 SHA-256。
- Git HEAD、branch、index bytes hash、git diff、git diff --cached、tracked/untracked 清單。
- 新 task 的既有凍結文件清單／hash。
- source-manifest.json 內標為 PROVENANCE_ONLY 的 .git/index，以及文件發布前 HEAD／branch，是歷史來源證據，verify-packet 不要求它們等於 commit 後的值；其餘 REQUIRED_CURRENT_HASH 記錄必須核對。接手的 Git 保存 gate 使用接手時新建的 baseline。

本次交接的文件 commit 是使用者另行明確授權的發布工作；低階 Implementer 的保存基線須在接手時重新讀取當時 Git 狀態，不拿 10/10 原診斷的 HEAD/index 當可回寫目標。若期間有其他使用者改動，記 BASELINE_DRIFT／BLOCKED，不還原、不 stash、不覆寫。

## 5. 解碼、ROI 與 OCR profiles

### 5.1 解碼與座標

- 用 ImageIO 依內容格式解碼，保存 CGImageSource 的實際 type、EXIF orientation、decoded dimensions、色彩空間與 alpha處理。
- canonical raster：RGBA8、sRGB、top-left origin，alpha=255（本次 opaque screenshots），每列 stride=width×4。
- 實作方向測試，用合成四角不同顏色 raster 確認上下／左右不翻轉；不能照抄 probe 的 CGContext transform 後誤用 buffer_y。
- 若來源需無法支持的 orientation／alpha／color transform，保持 UNKNOWN，停止；不要猜。
- ROI 用原始 capture pixels。min edge floor、max edge ceil，half-open [x0,x1)×[y0,y1)；不得超界或悄悄 clamp 掉字。
- 新 OCR 固定為：原 raster 裁切局部 ROI，再做 nearest-neighbor 2× derivative；crop origin、scale=2、derivative hash及 API coordinates 保存。轉回原圖：source_x=roi.x0+derivative_x/2；source_y=roi.y0+derivative_y/2。不得再除一次2，或把全圖歷史bbox當局部bbox。
- 原歷史 OCR 1308×2572 是全圖2×，使用舊 transform 的 scale與crop origin單獨轉換。新舊資料不得混用座標轉換。

### 5.2 初始化 binding

replay 用 scan-000 建立一次 replay-only bootstrap；live 用實際新的第一幀建立另一個 live bootstrap。兩者的 run ID、來源、幾何及權限不可互用。

bootstrap.json 保存：
- mode、run_id、observation_id、source_artifact/hash、decoder/profile/build hash。
- provider 與同一 App object/session binding 的實際 provenance；僅保存 documented 可取得欄位。pid/window ID 不可得可記 null，但不能聲稱通過產品 frame() validator。
- request_started_at／returned_at、monotonic start、timestamp origin。capture timestamp 無法取得時 freshness 採 request start 的保守上界，不能用檔案 mtime或OCR完成時間。
- width/height、documented capture-to-input mapping、實際可確認 scale／window geometry。必要 mapping/source/geometry未知就不能 scroll。
- canonical group_key、configured name、原 confirmation artifact/hash及本幀顯示名原文；不把已知 alias 硬編碼到程式。
- group full text-slot guard、兩個 tab text-slot guard、文字 tightrect、indicator search region、列表 viewport及安全 scroll target 的初始化來源。
- 非文字 shadow/divider exclusions 逐矩形列出原因與證據。排除區不能跨任何字元、不能依後續FAIL調整。
- fresh surface／group／selected tab／no-dialog／no-viewer／no-editing／no-occlusion 的 OBSERVED 記錄，全部綁同一 observation ID。

槽位寬度取 fresh layout 中整個可用標題槽及各 tab 槽，不能沿用初始字 bbox 的寬度，也不能依目前 OCR 收縮。初始字框只定位文字帶；文字 tightrect 原圖 floor/ceil 後加1 capture pixel padding，越界、截字或與排除區重疊即 UNKNOWN。如果不能明確分出完整槽位或列表 viewport，停止；不使用歷史固定座標當替代。

### 5.3 固定 OCR profiles

三個用途 profile 皆 accurate、recognitionLanguages順序為 zh-Hant,en-US、automatic language detection關閉（API支持時；不支持必須如實記錄）：
| 用途 | language correction | customWords |
|---|---|---|
| fixed-label-live | true | 相簿、記事本 |
| fixed-label-offline-comparison | false | 空 |
| identity-header-metadata | false | 空 |

固定標籤的關閉校正比較只在已宣告的離線驗證做一次，不因此選擇新的 live profile。群組、日期及張數的 identity profile 不受詞典補正。

新版 RecognizeTextRequest為主；legacy VNRecognizeTextRequest為診斷比較。兩者保存 topCandidates(3) 的實際結果，不補出不存在的候選。記錄 raw text／confidence／bbox／API／revision（能取得才填）／OS／SDK／recognition configuration／source與derivative hashes。confidenceCalibration=UNKNOWN，apis_independent=false。

不使用 confidence>=0.95，不做相溥→相簿替換，不用預期群組／日期／張數強迫辨識。若首次 bootstrap 的群組或相簿表面無法可靠確認，停止；此容錯只支持已確認本次基準的後續連續性。

## 6. 每幀連續性與選中指示

文字連續性：
1. 確認當前 frame 與bootstrap的 run、source binding、dimensions、geometry、scale相同。
2. 對 group full-slot guard及兩個tab文字槽（已凍結的非文字exclude另處理）比較 canonical RGBA，必須零不同像素；同時比對文字tightrect。
3. full-slot監視不能只用初始glyph mask或luma threshold，避免新增低對比字／微小點畫在舊字框外被漏掉。
4. 任何文字槽異動、缺失或无法取樣均 UNKNOWN／CONFLICT，停止；不在執行後加像素相似度容差。

選中指示獨立檢查：
- 保存每幀 indicator raw RGBA，不要求 content-adjacent整帶與baseline逐bytes相等。已知JPEG耦合差異不可被重新加為全域文字gate。
- 初始化在兩tab文字槽下方、列表viewport上方的單獨 search region，從本幀確認相簿下有唯一水平指示、記事本下無指示。
- 固定信號處理：luma=(54R+183G+19B)>>8；luma>=128為bright；8-connectivity，不丟弃小component、不做dilate/erode。這只用於指示結構，不能用於群組文字guard。
- 初始指示component須唯一、寬>高且其水平中心位於相簿槽內；記錄其bbox、bright mask及相簿／記事本位置關係。不能可靠隔離則UNKNOWN。
- 後續要求同region的指示bright mask／bbox／相对位置與baseline相同，記事本槽仍沒有選中指示；rawRGBA有變化保留為diagnostic。不能添加幾何／luma容差讓失敗通過。
- 結構不一致、第二個可疑指示、指示移到記事本或看不清，停止。即使文字guard完全相同也不例外。

只有 source/geometry、文字guard、相簿選中、有效metadata及當前安全觀察全成立，才可把單次tab OCR誤讀列為 auxiliary uncertainty。日期／張數衝突永遠不能使用這個例外。

## 7. metadata 身份、配對與歧義

parser 只做格式正規化，不做字元猜測：
- 日期格式：YYYY/MM/DD [~～〜-] [YYYY/]MM/DD，容許空白；省略結束年只取起始年，不自動推算跨年。
- 使用真正 calendar date驗證；start<=end。
- 張數只接受完整ASCII十進位正整數；不將 O/l/S 等字元替成數字。正規化後去除前導零可用int值，但保留原文。
- identity=(group_key,start ISO,end ISO,positive count)。群組不使用顯示名作跨run替代 key。

日期與張數配對：
- 全部框須在當前viewport內完整可見，使用original pixel coordinates。
- date行之下、下一個date行之前選count；date/count不得重用或跨不同metadata block。
- count.ymin >= date.ymax；vertical gap <= 2×max(date.height,count.height)；abs(count.xmin-date.xmin)<=max(date.height,count.height)。這是局部文字幾何配對，不是confidence或點擊安全margin。
- 需唯一候選；多count、跨卡、clipped date/count均partial或ambiguous，不可造完整identity。
- 沒有complete row時停止。縮圖／整卡可部分可見；這不授權開啟。

每個有效候選分別parse。best不合法時不可挑較低候選修補best；記partial。best合法但任一候選有不同的有效日期或count，停止。當前frame同日期出現不同count、同identity重複、已見日期count漂移或非相鄰reappearance，也停止。

legacy比較：
- 在同metadata block中若legacy與modern產生不同有效日期／count，立即IDENTITY_CONFLICT。
- 缺讀不叫agreement，不能寫成兩API一致。只有兩API都完整讀到同identity的行，才作本診斷的qualified complete overlap identity；沒有legacy對應的行保留unconfirmed，不當覆蓋橋。
- 日期框／張數框的實際位移使用modern主結果；legacy不取代主結果、不聲稱模型獨立。
- 歷史legacy只存1候選時，候選完整性保留UNKNOWN，不補造3候選。

## 8. 移動、顺序重疊及覆蓋鏈

ordered_complete_ids依modern date框y排序，不依日期排序猜畫面位置。

順序重疊：
~~~
matches = [k for k in 1..min(len(previous),len(current))
           if previous[-k:] == current[:k]]
overlap = PASS iff matches is not empty
~~~
集合完全相同允許overlap PASS。不能把集合相同判成NO_COLLECTION_PROGRESS。partial/unconfirmed行不能提供橋。缺口、順序相反或身份歧義不能延伸chain。

對所有共同qualified identity的date和count框：
~~~
D.low  = current.ymin - previous.ymax
D.high = current.ymax - previous.ymin
joint.low  = max(all D.low)
joint.high = min(all D.high)
movement = YES iff
    every D.high < 0
    and joint.low <= joint.high
    and every paired box has positive horizontal projection overlap
~~~

另保存各框center delta及原始bbox；D稱為「OCR框支持的位移範圍」，不稱confidence interval、真實位移誤差界或rigid motion proof。

歷史modern結果的預期（允浮點正常輸出，不以此修正parser）：
- scan000→001：共同65身份；joint約[-292.029,-243.804]。
- scan001→002：共同65身份；joint約[-292.029,-243.804]。
- scan002→003：共同56身份；joint約[-292.029,-246.483]。
- 第三步date center約-267.917、count center約-269.256；不得強制兩者只差1px而誤拒絕。

相關metadata raster／layout及identity確實未變時可記NO；其他不符合YES者記UNKNOWN／CONFLICT，不能從transport、AX或新增identity推出YES。NO及UNKNOWN都停止實機輸入。只有binding/continuity/identity/effect/ordered-overlap全部成立才追加chain edge。

full_collection_coverage永遠NOT_ESTABLISHED；top/bottom observations可保留但不增加本單元宣稱。不得把AX 101 items當101張相簿。

## 9. evaluator I/O與權限

evaluate的result至少分開保存：
- mode、run/frame/previous IDs、各來源hash、candidate/profile/decoder/binding hash。
- raw_ocr_artifacts、auxiliary_ocr_uncertainty及未覆寫的raw文字。
- binding_validity、continuity、selected_indicator、identity_status、complete_rows、partial_rows、conflicts。
- movement=YES/NO/UNKNOWN及D、center deltas、horizontal overlap。
- ordered_overlap、chain_extended、chain_edges及full_collection_coverage=NOT_ESTABLISHED。
- safety_observation=OBSERVED/UNKNOWN並綁exact當前frame。
- scroll_eligible（僅live/current）、can_open_album=false、can_save_all=false、live_state_write_allowed=false。
- stop_reason及未能取得的事實；不能用true/0/空字串補UNKNOWN。

replay永遠scroll_eligible=false，即使image_continuity/movement/overlap為PASS。歷史frame timestamp/source未知不能注入live binding。

scroll_eligible只是一個短效diagnostic判定，不可持久化後復用。最後還須第10章的fresh revalidation、pretrace readback及實際input前deadline check。

## 10. 唯一一次最多六次實機

前置條件：G_OFFLINE PASS，同一candidate hash的pre-live独立程式／證據審查明確PASS，且使用者新的前景就緒協調已完成。不能拿舊「已就緒」或已送審圖片當現在就緒。

首次 CUA 呼叫按tool規則只用 documented入口，例如取得config.app_identifier所指的App；先閱讀該次回傳的runtime documentation，再使用支持的snapshot/scroll API。不要猜 getWindowBounds、隱藏AX或截圖座標轉換。能力缺失就是BLOCKED。

不要點選到相簿、不要回頂、不要從main chat尋找群組。起始畫面不是已確認安全的指定群組Albums列表就停止。

每步：
1. 在live/建立新step目錄，保存analysis frame、raw screenshot實際bytes、AX/tool結果、OCR及evaluation。
2. 做一張新的final pre-input snapshot。來源、geometry、文字槽、indicator及所有已分析完整metadata區／位置必須重新核對。安全OBSERVED必須来自這張final frame，不能復用前一張。有任何metadata/reflow異動就停止；不以舊分析結果對新布局發送輸入。
3. final pre-input證據age<=5秒，以capture時間或request-start保守上界計算；保存／讀回耗時也計入。過期最多兩次唯讀重新觀察，仍无法完成就停止；不把OCR結束／檔案mtime改成capture time。
4. 從同final frame完整metadata日期文字框的中心導出scroll target；必須有documented capture→input mapping且位於safe viewport，避開ellipsis、浮動加號、遮罩及文字編輯；不click。若該API不支持安全定位，停止，不使用舊[180,1065]或猜Retina除2。
5. pretrace以exclusive creation保存、readback hash確認。記step ordinal、run/candidate/binding、final frame/hash/time、target來源、direction=down、pages=0.25、各前置條件、planned postcondition、inputs_used、剩餘budget。
6. 在真正呼叫前再次檢查5秒。呼叫一次App.scroll；所有已發送或無法確定是否發送的input計入六次上限。不能把預先寫的pending trace當已取得postcondition。
7. 立即fresh post-observe，保存原bytes、AX與transport result；先記effect UNKNOWN pending verification，後續判定另存，不回寫。
8. 執行固定OCR及continuity/identity/movement/overlap判定。YES且全部preconditions成立才可準備下一步。

任何transport error也保留原文並停止後續輸入；即使讀回觀察支持已有移動，也不能抹去error或重送。UNKNOWN effect只允许最多兩次唯讀post-observation，分別等待10秒、30秒，不改transport、不scroll。若仍unknown就終止。

NO、viewer/dialog/menu、group/tab變化、blocking ambiguity、binding drift、overlap gap、用完六次或中斷均terminal stop。中斷後不得resume剩餘scroll；這個live slot已使用，晚到結果只補證據不增加權限。

## 11. 必要測試矩陣

所有testcase輸出記真實expected／actual／verdict、fixture或historical來源、source/candidatehash。測試材料的in-memory mutation只能作fixture；永遠不能當native證據。

| ID | 輸入/操作 | 必要結果 |
|---|---|---|
| R01 | 四原圖＋舊兩API raw OCR逐frame replay | 保留scan003相溥；文字連續性、選中、3段movement及overlap成立；live權限false |
| R02 | 相同visible identity集合，bbox全部大幅向上 | YES，不以集合相同拒絕 |
| R03 | raw confidence=0.3/0.5但身份／幾何完整一致 | 不因0.95門檻失敗；raw scores保留 |
| R04 | baseline舊glyph不變，但title槽外新增低對比像素／小字 | full-slot guard拒絕；不只查glyph mask |
| R05 | 改group字／tab字；指示移到記事本或雙指示 | 停止 |
| R06 | final safety為viewer/dialog/menu/editing/occluded，文字ROI仍相同 | input禁止；不能靠hash覆蓋安全未知 |
| R07 | old run/frame混入、source/token/geometry/scale/mapping改變 | binding invalid；無scroll權限 |
| R08 | capture過期；persist/readback讓age超5秒 | 不dispatch；唯讀refresh最多2 |
| R09 | 日期無效、start>end、count非正整數、跨卡／兩count | 拒絕完整identity或ambiguity停止 |
| R10 | 同cell兩API不同有效identity；候選有效身份不同 | 停止；不套tab容錯 |
| R11 | 缺讀legacy或只有partial共同行 | 不寫agreement；不能用該行延伸coverage |
| R12 | duplicate、同日期count變動、nonadjacent reappearance | ambiguity停止 |
| R13 | ordered-overlap缺口／反序，雖集合有交集 | 不延伸chain |
| R14 | date向上但count不向上，D無共同交集或x無重疊 | 不得YES |
| R15 | 未變metadata／layout，transport RETURNED或AX改變 | 不以transport/AX推出YES |
| R16 | tab OCR錯且文字像素／選中／來源證據不足 | UNKNOWN、input禁止 |
| R17 | JPEG命名.png、history全圖2x、新局部ROI2x、方向四角fixture | 真格式／轉換正確；不翻轉、不二次除2 |
| R18 | UNKNOWN/error/crash/late result或第7次input請求 | 不resend、不resume、不超6 |
| R19 | 修改原回放、immutable文件、profile或candidatehash | 拒絕舊結果重用；原失敗保留 |
| R20 | 六個真正live steps | 每步實際fresh/action/effect/overlap；0 click/key/open/download/statewrite |

R01使用已保存舊OCR；新OCR也需對同四張副本執行固定profiles、保存rawoutputs並評估，不以新正字覆蓋舊錯字。legacy候選缺失忠實記UNKNOWN，不能造資料。必要反向test失敗或新方法無法取得正向結果，就保存最小repro停止；不能為使R01通過修改ROI排除／threshold／位移政策。

## 12. 追加額度、機械修正與失敗路由

results/attempt-ledger.json必須append-only events：
- historical_meaningful_method_attempts=3；source指向舊結果。
- authorized_additional_method_slots=1；authorization指向本次使用者明確訊息。
- additional_method_slot_used=false/true；在第一次固定candidate的新OCR驗證開始前消耗，保存該candidate/profile hashes。
- historical+實際追加總數依事實為3或4；live_slot使用與input_calls計數另存。
- method hypothesis、falsifiable expected result、實際學習、information_gain及stop_reason。

v3 convergence.meaningful_attempts上限3，不得填4，也不能把新task field=0說成根因預算重置。角色result若保留historic3須在analysis說清楚它不是包含追加的總數；正確總數以ledger為準。沒有正式controller支援，不能以PASS分支漏洞進場。

直接理解的純語法／路徑接線錯誤最多一次小修及focused check，保留失敗；這不是新的OCR方法。任何會改辨識profile、ROI／排除政策、身份、gate requiredness、位移／overlap、來源／安全、輸入重試或scope的修正都不屬小修，停止並寫replan packet。禁止第五種方法或無資訊重試。

失敗封包至少包含：最小原始frame/outputs、frozen candidate/profile/contract hashes、facts/inferences/unknowns、歷史3及追加使用、最後學習、已通過gate、失敗gate、停止原因與需要的精確下一步。不要把BLOCKED誤報DONE，也不要把已通過offline／保存事實改成FAIL。

## 13. 交付物與六狀態

必要交付物：
- replay/manifest.json。
- candidate的實際source、profiles、build logs與candidate-manifest.json。
- offline-validation/results.json及全部raw OCR/stdout/stderr/testcase結果。
- results/pre-live-review.result.json與candidatehash（真正独立review，不是root自評）。
- live/trace與逐frame evidence（未進live時NOT_RUN並說明原因）。
- results/preservation.before.json、preservation.after.json、preservation.delta.json。
- results/attempt-ledger.json、progress.md、四道gate evidence manifest。
- results/implementer.result.json與最終独立acceptance.result.json。

狀態規則：
- Implementer尚未開始：NOT_ACHIEVED / NOT_STARTED / NOT_RUN / NOT_RUN / PENDING / IN_PROGRESS。
- offline通過但live未跑：保留offline PASS；CORE_ACCEPTANCE不冒充全目標PASS；REQUIRED_VERIFICATION=INCOMPLETE或BLOCKED，TASK_CLOSURE=PENDING_REQUIRED_VERIFICATION或IMPLEMENTATION_BLOCKED，依實際原因。
- live只成功少於6步：G_LIVE=PARTIAL/FAIL/BLOCKED，原成功prefix保存；不以「安全停止」宣告六步驗證成功。
- 六步、所有負向tests、保存均PASS：獨立Acceptance仍PENDING；不能由root補PASS。
- final Acceptance PASS只支持有限診斷。本地語意結果可如實報告，但controller admission仍BLOCKED，不能聲稱controller-native DONE。
- 舊診斷六狀態永遠保持 NOT_ACHIEVED / BLOCKED / BLOCKED / FAIL / NOT_REQUIRED / IMPLEMENTATION_BLOCKED。

如果取得真正適用的stage packet，只執行它發出的固定CONTRACT/RESULT驗證命令並保留exact bytes/receipts；沒有packet時validation_fact=NOT_RUN，不自造validator、invitation、model/session completion或使用其他task的4.9命令。本封包的JSON parse與handoff逐byte比對不等於schema VALID。

## 14. Implementer 的完成核對清單

- [ ] 未改任何scope外檔案；source/root/authority與frozen package一致。
- [ ] 原材料copy/hash完整，JPEG實際格式與上下方向驗證正確。
- [ ] 固定一個candidate；三用途OCR與raw候選／分數完整。
- [ ] group/tab fullslot guard含低對比新增字；indicator不誤用整带RGB等值。
- [ ] 完整metadata唯一；兩API有效identity衝突立即停，缺讀不算一致。
- [ ] 全部共同date/count D與順序overlap分開，集合相同仍可移動。
- [ ] 全部必測cases真實通過；未執行者NOT_RUN。
- [ ] 真正獨立pre-live review綁same candidate；新的前景就緒。
- [ ] 六次上限、single input、fresh final safety、5秒與pretrace/readback完整。
- [ ] UNKNOWN/error不resend；沒有open/menu/download/statewrite。
- [ ] preservation delta及accurate attempt ledger完整；未重設historic3。
- [ ] 最終獨立Acceptance與六狀態依證據；未宣稱complete collection／native admission。
