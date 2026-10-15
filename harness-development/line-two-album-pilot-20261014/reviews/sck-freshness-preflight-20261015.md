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
