# Review request: diagnostic SCK freshness readiness

## Purpose and requested decision

請 ChatGPT 獨立審查：既有真實時序及核准來源，是否足以支持在下一次 Owner consent 前停止 diagnostic 安裝及 acquisition。請區分「本次 readiness 的操作性阻塞」與「所有未來執行必然失敗」；本報告僅主張前者。

這個 PR 只發布審查報告及去識別化的時序摘要，沒有來源修正、權限變更、時間放寬或實機執行。它以 PR10 的精確核准 HEAD `2bd94af4e5f0d0d070983b270f49691968c18788` 為基底；PR10 本身的 HEAD 保持不變。[Chief Review](https://github.com/s9008129/Line_backup/pull/10#issuecomment-6188644429) 只批准可回復安裝，要求先檢視既有 timing evidence；新 live consent 尚未授予。

## Genuine observations reported by the operator

下表是操作者從既有 G1-04 原始私有檔案讀出的值；該次執行使用 `218a025e8006bacf21e7c7f6023a07627b0f7667`。沒有重跑 LINE，也沒有新 benchmark。

| Evidence | Retained value |
| --- | --- |
| JPEG retention filesystem mtime | `2026-10-15T07:23:47.823102310Z` |
| JPEG filesystem birthtime | `2026-10-15T07:23:47.8229597Z` |
| Native AFTER embedded `observedAtUnixMilliseconds` | `1792049040965` (`2026-10-15T07:24:00.965Z`) |
| Native AFTER `complete` / `truncated` | `true` / `false` |
| Native AFTER `visual.sourceSHA256` | Matches the retained JPEG SHA-256 in the JSON companion |
| Actual prior invocation result | `DISPLAY_GEOMETRY_AMBIGUOUS`, stopped without retry |
| Independent original hosted request-start receipt | Not separately retained; exact request-start age UNKNOWN |
| Isolated native AFTER process duration | UNKNOWN |

Exact integer arithmetic from the recorded nanosecond mtime and millisecond native timestamp gives:

```text
native_after_ns = 1792049040965 * 1000000
retention_mtime_ns = 1792049027823102310
difference_ns = 13141897690
difference_ms = 13141.897690
original_freshness_limit_ms = 5000
```

操作者據此推論：hosted request-start 先於 JPEG retention；native AFTER 內嵌 timestamp 時，從 retention 起已約 13.142 秒，因此原始 request-start 至該點的 age 至少同樣長。新 diagnostic 的分析及 SCK 還在其後，這個既有樣本已超過原始五秒 gate 約 8.142 秒。

**Evidence limitation:** 檔案 mtime/birthtime 是這個下限的部分依據，並非獨立保存的 monotonic capture receipt；沒有證明不存在 wall-clock discontinuity 或 metadata 變動。這是單次歷史執行，不能證明每次未來執行的效能下限，也不能把 13.142 秒全歸因於 Vision。公開的 JSON 是私有證據的摘要，不是原始 native packet，更不是可直接授權動作的證據。私人 JPEG、AX、OCR、群組／相簿內容、Owner 資訊、grant、state、絕對路徑均未上傳。Reviewer 可在 GitHub 核對算術與來源順序；原始資料及雜湊重算仍需 Owner 管理的私人證據移交，不能宣稱已獨立驗證。

## Source ordering at the reviewed HEAD

下列連結全部固定於核准 HEAD，避免後續 branch 變動改變審查依據。

1. [Navigation observer: request-start → hosted capture → retain → native AFTER → classify](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/scripts/line_backup_cua_adapter.mjs#L755-L776)。`capturedAt` 是原始 hosted request-start；在 `afterCapture` 完成前不會呼叫 classifier。
2. [Native observation: `loadVisual()` precedes the embedded timestamp](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift#L230-L237)。這個 timestamp 位於 ImageIO/Vision 的 visual 分支之後。
3. [Separate one-shot read-only diagnostic entry](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/harness-development/line-two-album-pilot-20261014/mac_runtime.mjs#L237-L260)。它使用上述 observer 及 native before/after hooks，要求精確 `operations=['gui_observe']`，並維持 failure retention／one-shot latch。
4. [Diagnostic classifier and SCK support](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/harness-development/line-two-album-pilot-20261014/mac/classifier.mjs#L304-L398)；[producer forwards the original `capturedAt`](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/harness-development/line-two-album-pilot-20261014/mac/producer.mjs#L30-L43)。SCK 是分析及 geometry retention 之後才呼叫，沒有重新起算 timestamp。
5. [Native pre-capture freshness gate](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1192-L1194) 要求 `abs(now-cuaDate)<=5`；[hosted OCR → SCK capture and end-time gate](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1255-L1264) 要求 SCK end 距同一原始 `cuaDate` 不超過五秒；[final OCR/support deadline](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1331-L1333) 仍採同一時間原點。不是每階段各有新的五秒。

操作者逐一核對既有 build record 的 60 份 native source 與核准 HEAD 及正式專案來源，並核對既有 producer binary；均相符。這支持 native prefix 未改變，但不是效能保證或新的 build PASS。

## NO-LINE preflight outcome

| Check | Operator-observed result |
| --- | --- |
| PR10 actual HEAD | Exact approved HEAD; OPEN, unmerged |
| Approved diagnostic installed | No; stopped before source overlay or binding refresh |
| Existing installation | `218a025e8006bacf21e7c7f6023a07627b0f7667`; three diagnostic source hashes differ from approved HEAD |
| Existing source/build/binary/decoder/runtime closure | Verified; 60 native source files and 162 dependency bindings |
| Native `runtime-preflight` | Once, exit 0; Accessibility and ScreenCapture permission true; zh-Hant/en-US listed; LINE observation false, GUI inputs 0 |
| CLI `native_authorize` | Once, expected exit 4, `PROJECT_LIVE_READINESS_REQUIRED` |
| Current grant | Exactly `operations=['gui_observe']`; prior consent closed, not rearmed |
| Preservation | 383 protected files unchanged, including 239 historical photo hashes; rev35/cap1, existing state/intents/receipts, dirty work and logical index preserved |
| Acquisition/input/ledger | No LINE acquisition, no input, no live GUI ledger initialization |

`NO_LINE_PREFLIGHT=FAIL` 以下是完整 approved-runtime readiness 的結果；個別 permission probe 和 closed-admission negative probe 均 PASS。`SOURCE_BINARY_BINDINGS=BLOCKED` 表示新版綁定未刷新，並非現有 binary 或 decoder 雜湊失配。這些檢查本身沒有真實 SCK、card witness 或 E2E 的產品 PASS。

```text
SOURCE_HEAD=2bd94af4e5f0d0d070983b270f49691968c18788
INSTALLATION=BLOCKED
SOURCE_BINARY_BINDINGS=BLOCKED
NO_LINE_PREFLIGHT=FAIL
SCK_FRESHNESS_READINESS=KNOWN_BLOCKER
NEW_OWNER_CONSENT=NOT_GRANTED
REAL_DIAGNOSTIC=NOT_RUN
SCK_REAL_CAPTURE=NOT_RUN
VISUAL_CARD_WITNESS=BLOCKED
G1_ACTIONABLE_IDENTITY=BLOCKED
HISTORICAL_239_PHOTOS=PROTECTED
PRODUCTION_STATE_MODIFIED=NO
LINE_INPUT_ACTIONS=0
NEXT_ACTION=REPORT_ACTUAL_BLOCKER
```

## Focused questions for ChatGPT

1. 上述單次真實 evidence 與 filesystem/clock 限制，是否足以支持「本輪先停止，不消耗新的 consent」？若不足，請精確指出仍缺哪一項證據，不要假定原始 hosted request-start 或每次效能已知。
2. Source ordering 是否證實 diagnostic 在 native AFTER 之後才開始 SCK，且所有五秒 gate 都綁定同一 request-start？13.142 秒推論是否有 clock、metadata、pairing 或 stage 歸因上的缺口？
3. 發現阻塞後，在 source overlay/binding refresh 前提前停止是否符合 Chief Review 與 Owner 的停止條件？請獨立評估此操作決策。
4. 如果需要修正，請只指出保持原始 timestamp、五秒 gate、source/window identity、read-only/evidence-only/non-actionable 語義的最小既有程式切入點與必要驗收證據；本 PR 沒有實作、批准或要求直接執行這個修正。

這份報告不授權 LINE capture/input，不重用 consent，不執行 `observeG1()`／`runPilot()`，不改 OCR threshold、不猜 geometry、不建立 AXImage、不初始化 ledger、不變更 Harness、不 merge。239 張歷史照片、rev35/cap1、receipt3、durable intents、B03 UNKNOWN 與 no-replay 邊界均保留。任何將來 action-capable pilot 仍需其自身 focused source review 和 Owner 授權。

本輪 current live attempts=0；舊 G1-04=1，原始第一失敗仍為 `DISPLAY_GEOMETRY_AMBIGUOUS`，從未實際發生新 diagnostic 的 freshness refusal。`retained CUA frame is outside the five-second pre-capture window` 是由來源和歷史 age 推得的預期拒絕，不是本輪已觀測到的錯誤。

原始私有收據的 SHA-256 與最小時序欄位見 [JSON companion](sck-freshness-preflight-20261015.evidence.json)。本報告是送審材料；沒有宣稱 ChatGPT 已完成審查、獨立 Acceptance 通過或完整備份 E2E 完成。

## Latest findings: one existing offline original-image measurement

**DOCS_ONLY / NO_PRODUCT_PATCH.** 上文保留前一輪歷史 triage 及其證據限制。[Chief Review of the previous documentation HEAD](https://github.com/s9008129/Line_backup/pull/11#issuecomment-6191777827) 接受一次有界停止，不是軟體修正批准。本節發布其後已完成的私有離線量測；本次發布沒有重跑 OCR 或 LINE，沒有修改 PR10、產品來源、時間戳或五秒 gates。

以下數值全部是 **operator-observed，未由獨立 Reviewer 重現**。原始私有報告、執行 stdout/stderr、編譯／source/object bindings 與 retained JPEG 在本機重新計算雜湊並核對既有 manifest 相符；這是操作者本機的 integrity check，不是遠端驗證原始證據。

### Tested implementations and input

來源 commit 固定為 `2bd94af4e5f0d0d070983b270f49691968c18788`。

| Tested call | Exact implementation and source |
| --- | --- |
| `LegacyVisionOcrParityEngine().recognize(image:)` | [OcrEngine.swift:126–153](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Perception/OcrEngine.swift#L126-L153)：`VNRecognizeTextRequest`、`VNImageRequestHandler(cgImage:orientation:.up,options:[:])`，包含結果轉為 `OcrItem` |
| `VisionOcrEngine().recognize(image:)` | [OcrEngine.swift:90–118](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Perception/OcrEngine.swift#L90-L118)：Swift `RecognizeTextRequest`、`await request.perform(on:)`，包含結果轉為 `OcrItem` |
| Shared geometry conversion | [OcrGeometry.item:41–88](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Perception/OcrEngine.swift#L41-L88)：quad／capture-pixel bounding-box 的轉換發生於 wrapper 返回之前，因此包含在各自區間內 |
| Separate pixel-detector stage | [EllipsisPixelDetector:59–177](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Perception/AlbumEllipsisLocator.swift#L59-L177)；沒有把其成本算成 Legacy 或 Swift OCR 的成本 |

`OcrEngine.swift` 的 source SHA-256 是 `d0dcab179db7311853857eeaf065339eb4f74c64976dd2b5104ef9fa280cec00`。兩 wrapper 都使用 `.accurate`、`zh-Hant`／`en-US`、`usesLanguageCorrection=false`、`topCandidates(2)`；API 與回傳 observation 型別不同，**相同設定不等於輸出等價**。

兩個 OCR call 收到同一個由原始 JPEG 建立的 `CGImage`，無 crop/resize/影像編輯。輸入長度 184,297 bytes，SHA-256=`da605c7d71557e1cade2c15d74e8c697f4d8970b0940508c154c23bea2c36c42`，與前述 retained original JPEG 相符。操作者重讀原檔、probe reservation 與 read/hash stdout 三者核對一致。沒有公開影像、AX、OCR 文字、群組或相簿內容。

這是一個執行程序、同一影像、每 backend **一次呼叫**，不是重複樣本或統計分布。程序內順序為 read/hash → ImageIO → Legacy OCR → dots → Swift OCR → total。未控制 framework／Vision service／model／OS cache、冷啟動或背景負載，沒有清 cache、重啟服務或 counterbalance 順序；Legacy 是本程序第一個 OCR，不能因此稱為受控 cold-start，Swift 則可能受前一 OCR 暖機影響。Probe 連結既有 42 個 Rev28Core objects，沒有新編譯產品；私有 compile receipt 記錄 `-swift-version 5`、MacOSX26.5 SDK，probe argv 沒有 `-O`。完整私有路徑與原始 argv 不發布。

### Exact observed values and timer boundaries

| Stage, in actual order | Operator-observed duration (ms) | Returned count |
| --- | ---: | ---: |
| Read original bytes + SHA check | 1.759875 | 184,297 bytes |
| ImageIO source/image creation | 3.342000 | one image |
| Legacy Vision parity wrapper | **12944.114333** | 5 OCR items |
| Ellipsis detector | 364.447500 | 9 components |
| Swift Vision wrapper | **113.389041** | 6 OCR items |
| In-probe total | 13439.753292 | one process invocation |

這些是原 stdout 的 floating-point milliseconds，以六位小數顯示；不是對量測準確度的保證。回傳摘要中 `12944 ms`／`113 ms` 僅為四捨五入。Timer 使用 `DispatchTime.now().uptimeNanoseconds`，計算 `Double(end-start)/1_000_000`；這個新 offline duration 不使用歷史 filesystem mtime，也沒有回填 capture timestamps。

以下是私有 probe 的**不含私人資料之計時邊界摘錄**，不是新的程式 patch，也不是原始私有程式全文；私有全文 SHA-256=`86ab5c2525dd2f5296e720e2d0fd5e41016114d9467c59351e68f7c5541ced26`。

```swift
static func now() -> UInt64 { DispatchTime.now().uptimeNanoseconds }
// Inside emit(), after copying details and assigning the stage label:
value["duration_ms"] = Double(now() - start) / 1_000_000
// JSON encoding and stdout writing occur after this duration sample.

let legacyStart = now()
let legacy = try await LegacyVisionOcrParityEngine().recognize(image: image)
try emit("existing_legacy_vision_parity", legacyStart, ["item_count": legacy.count])
// A separately timed EllipsisPixelDetector.detect(image:) runs here.
let modernStart = now()
let modern = try await VisionOcrEngine().recognize(image: image)
try emit("existing_swift_vision", modernStart, ["item_count": modern.count])
```

兩個 OCR interval 的 start 都在各自 wrapper 呼叫之前；end 都在 wrapper 返回後、`emit` 內複製 details／設定 stage label 後取樣。包含 wrapper 初始化、request 設定、辨識／await／scheduling、候選與 quad/bounds mapping、返回陣列、`.count` 和少量計時 bookkeeping。**不包含**程序啟動、前面獨立量測的 read/hash 或 ImageIO creation call、dots stage、該 stage 自己的 JSON encode/stdout write、SCK、AX traversal 或 private support retention。

辨識區間內的 framework/service 初始化、deferred pixel realization 是否存在及各自耗時 **UNKNOWN**；ImageIO creation 計時不證明所有像素工作已被隔離。原始 start/end uptime tick 值也未保存，均為 **UNKNOWN**；只有計算後的 duration。此結果不能再拆成「純 OCR model」或其他未量出的 process phases。Total 從讀檔前到最後 `emit` 的 duration sample，包含中間 logging／bookkeeping，排除程序啟動、最後 total JSON write 與 teardown，不等於完整 subprocess 或 LINE pipeline。

Text、confidence、candidate-count field、quads、bounding boxes、canonical group/date/count 及 anchors 的**逐項跨 backend equivalence 都沒有檢查／保存比較結果**。5 和 6 是回傳 item 總數，不是 `candidateCount` 欄位；只能說這次回傳長度不同，不能指出某段私人文字辨識錯誤、也不能宣稱 parity。113 ms 不足以支持直接替換。

### Relationship to native AFTER and all three deadlines

真正 native AFTER 的 [loadVisual:552–572](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Observation/PassiveContextObservation.swift#L552-L572) 也使用 Legacy `VNRecognizeTextRequest` 及相同 recognition 設定，但它直接將 observation 的 `boundingBox` 轉成自己的 `OCRItem`，不是呼叫 parity wrapper；之後還有 dots。兩者不能視為逐階段完全等價。Offline probe **沒有呼叫 native-context 或 LINE**；12.944 秒不是歷史 13.142 秒的精確分解，也不是新量出的 native AFTER 程序時間。

| Existing gate | Pinned source and exact time origin |
| --- | --- |
| Before SCK | [main.swift:1189–1194](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1189-L1194)：`abs(Date().timeIntervalSince(cuaDate)) <= 5`，`cuaDate` 由原始 `--cua-captured-at` 解析 |
| SCK acquisition completion | [main.swift:1255–1264](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1255-L1264)：先做 CUA Swift OCR，再 capture；`sckStart >= cuaDate`、`sckEnd >= sckStart`、`sckEnd-cuaDate <= 5` |
| Final OCR/support completion | [main.swift:1274–1333](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1274-L1333)：SCK OCR、anchor mapping、uncertainty/safe-margin evaluation、OCR/support/manifest encode/sync write 後，仍要求 `Date()-cuaDate <= 5` |

原始 UTC 來源與傳遞鏈仍是 [observer:759–776](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/scripts/line_backup_cua_adapter.mjs#L759-L776) → [diagnostic collector:304–359](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/harness-development/line-two-album-pilot-20261014/mac/classifier.mjs#L304-L359) → [producer:30–43](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/harness-development/line-two-album-pilot-20261014/mac/producer.mjs#L30-L43)。沒有改成 SCK 開始時重設 t0。Support sidecar 本身另有 SCK request-start 欄位（[main.swift:1304–1306](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1304-L1306)），**不會改變三個 guards 使用的 CUA `cuaDate`**。

早拍 SCK 可能減少第二個 gate 前的延遲，卻不會取消最後 gate。把 mandatory OCR 或 support 寫入移到原始 t0+5 之後，仍不能在不變的第三 gate 下當成完成。現行 [CLI geometry/identity prerequisites](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/rev28ctl/main.swift#L1196-L1248) 要求同幀 geometry/AX/layout、exact PID/window/display 及獨立 scale；低層 [captureFullDisplayRetained:501–566](https://github.com/s9008129/Line_backup/blob/2bd94af4e5f0d0d070983b270f49691968c18788/rev28/Sources/Rev28Core/Sensor/FrameCapture.swift#L501-L566) 可被重新安排，但只有存在此 primitive 並不足以證明端到端完成期限可行。

### Root-cause boundaries and next decision

| Classification | Supported statement |
| --- | --- |
| `OBSERVED_TIMING` | Operator-observed、一次離線 Legacy parity wrapper 12944.114333 ms；較後執行的 Swift wrapper 113.389041 ms。沒有獨立重現，沒有 controlled cold-start |
| `SOURCE_CONFIRMED_EXECUTION_ORDER` | 公開 source 顯示 native AFTER/visual 先於 diagnostic/SCK，且所有三個 guards 綁定原始 request-start；可由固定 commit 的程式獨立檢視 |
| `INFERRED_FUTURE_FAILURE` | 相似 latency 若再出現，原始五秒前綴／完成期限會有風險。不是所有未來執行必然失敗的證明；沒有新的 real SCK 或 freshness refusal |
| `UNPROVEN_REPLACEMENT_PERFORMANCE` | 未證明 Swift 在可比 cold/initial-service 條件和完整 pipeline 內仍能達標；不可把這次 113 ms 當成無條件效能承諾 |
| `UNPROVEN_OCR_EQUIVALENCE` | 未做 text/confidence/candidate counts/quad/bounds/identity/anchor equivalence；不同 item 數不提供 replacement approval |

技術建議：請 Chief 在「先補足狹窄的 offline cold-state／輸出等價驗證」與「提出一個嚴格 evidence-only 的 capture/completion 語義修正供明確 source review」之間作出來源層決策。任何候選都應保留 original UTC/monotonic provenance、fresh native identity、影像 SHA pairing、獨立 SCK scale/correlation 與 `VISUAL_CARD_DIAGNOSTIC,evidence_only=true,actionable=false`。如果將來容許 late diagnostic analysis，須另外明示其 validity contract，不能默默放寬既有 action-capable guarantees。本 PR 不選定／實作 replacement、不要求新 consent，也不新增 scheduler、Harness 或更多 review PR。

### Required questions for independent ChatGPT Chief Reviewer

1. Does the 12.944-second Legacy Vision measurement establish a genuine current critical-path problem, and what are its limitations?
2. Does the 113 ms Swift Vision result provide sufficient evidence to replace Legacy Vision? If not, what exact cold-start and OCR-equivalence proof is missing?
3. Does the current five-second contract require full OCR/support completion from the original request-start, and would an earlier SCK capture alone remain insufficient?
4. What is the smallest safe correction to the existing pipeline that preserves accurate source timestamps, native identity, hash pairing, SCK correlation and evidence-only semantics?
5. Is additional offline verification necessary before implementation, or should a strictly scoped diagnostic-only correction be proposed?
6. Which conclusions are independently verifiable from public source and which still depend on private operator evidence?

公開可驗證的是 pinned code、摘要算術、方法摘錄與其主張是否一致；真實執行時間、私有原圖/objects/receipts 的相符性和 preservation 結果仍是 operator evidence，hash reference 不能取代 Reviewer 取得原件或獨立重現。最新數據位於 JSON 的 `latest_offline_measurement`，原有歷史欄位原樣保留。`COLD_START_EQUIVALENCE=NOT_PROVEN`、`OCR_OUTPUT_EQUIVALENCE=NOT_PROVEN`、`FULL_FIVE_SECOND_PIPELINE=NOT_PROVEN`、`REAL_SCK=NOT_RUN`、`OWNER_CONSENT=CLOSED`、`G1_ACTIONABLE_IDENTITY=BLOCKED`。沒有新的產品 PASS 或獨立 Acceptance。
