# PR #8 最小准入提案 — LINE_DIAGNOSTIC_ADMISSION/1

狀態：PROPOSAL_ONLY／INDEPENDENT_REVIEW_PENDING。基準 HEAD：c5862be7574afa80a54684a9872a9e3f938ff876。回應 [Owner 授權](https://github.com/s9008129/Line_backup/pull/8#issuecomment-6160186860)。這不是 Harness release、native receipt、Task 建立或 Implementer 准入；没有已實作的 executor、外部身份證明或 LINE 證據。

唯一提案：先以獨立審查、主管採納的版本化 external-review profile，使用既有 Controller 的 TRUSTED_OPERATOR provenance 入口；只有這條 bootstrap 路線真實成立，才准入 Luna 實作一個直接控制 macOS 原生 capture／input 邊界的版本化一次性組件。兩者一起解決 B05／B03，不重建 Harness。B01／B02 與 P01／D01／D02／D03 不變。

## 已查明的接口與限制

R = Mac 現有 pinned resources-luna，位於 harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/runtime/。所有以下行號對應 admission-validation.json 的實際 source SHA256。

| 項目 | 直接證據 | 結論 |
| --- | --- | --- |
| 模型設定 | /Users/hsiaojohnny/.codex/AGENTS.md §3；R/tools/harness/controller.py::_role_policy L300–312 | model／effort 可設定，但現有 pin 是 Luna/high，不能偷改。 |
| 外部資料入口 | R/schemas/v3/run.schema.json 的 invitation／completion；controller.py::_provenance L586–634 | 既有 descriptor source 固定 TRUSTED_OPERATOR；需真實 raw JSON、actor／session／nonce／model 與 result digest。這是可重用的結構，不是已證實的外部 ChatGPT 合法來源。 |
| immutable run | controller.py::_run L260–275；allocate_run L360–440 | active run 必須原 root／inventory；不同 profile 只能在符合 next_stage 的新 run 使用，不可把既有 run 換 pin。 |
| zero retry | R/schemas/v3/task.schema.json retry_policy；R/tools/harness/lifecycle.py::retry_delays L351–356 | schema 的 2／[10,30] 是 read-only eligibility；IMPLEMENTER 得空 tuple，但沒有 cua_repl 執行端綁定。 |
| hosted Computer Use | 本 session 的 mcp__cua_repl.js 公開介面僅 code／timeout_ms／title | 沒有公開 dispatch idempotency、retry 控制或傳輸／native input 源碼證據。未初始化工具，未探測 LINE。單次 API invocation 不能證明單次原生輸入。 |
| 可重用原生葉節點 | rev28/Sources/Rev28Core/Sensor/FrameCapture.swift::captureRetained L381–410；Actuation/QuartzActuator.swift::postClick L480–575 | captureRetained 直接呼叫一次 SCScreenshotManager；現有 postClick 有 hover 與 fresh revalidation，不能直接宣稱符合「只有兩次 capture」。它們是設計參考，並非本診斷已准入的完整執行器。 |

對 rev28 的檢視是 Mac 當前檔案的 source inspection，包含既有 dirty work；沒有吸收／修改這些檔案，也不把它們宣稱為受審後可用的 binary。

## B05 — 真實外部審查 evidence 與 bootstrap

提出 EXTERNAL_CHATGPT_REVIEW/1 profile。它只決定外部平台來源驗證、角色設定與逐 run 綁定；保留原 v3 result／Controller 判定、schema receipts、deterministic Handoff，並不把 GitHub PASS 轉為 native PASS。

外部 record 必須保留如下內容，全部由實際來源取得；缺少任何必要身份／請求證據即 BLOCKED：

- version、origin=EXTERNAL_CHATGPT_OPERATOR_CAPTURE、來源 export／transcript hash、provider conversation/session ID、invitation 與 completion message IDs／timestamps、提供與核對原件的 operator 身份與獨立 Reviewer 身份。
- 真實可核對的 requested model／effort，與新 profile 的角色設定完全一致。provider 未報 backend 時 reported_model／effort 保留 null；不能把 UNKNOWN 變成假 model，亦不能把任意外部模型命名成 Luna。
- allocated task_id、run_id、PLAN_REVIEW／PLAN_REVIEWER、invitation_nonce、source_sha256、精確 review HEAD、Plan／contract SHA256。nonce 必須先分配再出現在送交 ChatGPT 的 invitation 中，不得追認舊留言。
- ChatGPT 自己完成的 schemas/v3/result.schema.json bytes／SHA256、獨立 disposition、對應 completed assistant message 與來源。Sol 只可完整傳遞並驗證，不能代寫 Reviewer result、PASS、actor 或 completion。

原始平台證據保留本地私有／受保護位置，Git 只放允許的 redacted metadata／hash。將 provider 原件包入 operator capture 時明示 external origin、原件路徑及 hashes，不冒充 Codex delegation／Luna envelope。現有 descriptor 可用 TRUSTED_OPERATOR 的前提，是主管確認這種真實來源符合上層 §6「Native platform claims require actual records」及既有 trusted-capture 政策；目前此確認與可驗證 ChatGPT 原件均不存在。程式通過 JSON schema 不能證明來源受信。

Bootstrap 順序與硬停止：

1. ChatGPT 獨立審查本提案；Project Owner 與有權制定上層 Harness 來源／配置政策的主管，明確採納上述 external source 為既有 TRUSTED_OPERATOR 的合法實際平台來源，並批准新的 versioned role profile。這是必要的政策採納決定，不是 Controller admission，也不是豁免來源要求。Owner 若無該上層權限，須由真正主管決定。
2. **不寫新 adapter／Controller code 來 bootstrap。** 在已採納政策下，trusted operator 以原始 provider records 產生誠實 capture descriptors；新 profile 使用原 4.8.0 controller／schema／原政策 bytes，只改經批准的 role configuration，存於獨立版本化 resource root，完整 inventory/hash 凍結。新增的來源採納政策亦須 immutable/hash-bound，透過既有 allocate_run 的 policy_path／validation_sources 綁定，不能只依未凍結的文件。舊 R、舊 run、舊歷史完全不改。
3. active Planner run 仍須以其原 resource root、真實 Planner session、正式 publication／schema receipts／completion 完成；不能用新的 profile 匯入舊 run，不能把本 PR 候選 bytes 配上舊 completion。完成且 Controller 允許 next_stage 後，才可用新 profile 的 CandidateController.allocate_run 分配 PLAN_REVIEW。
4. 新 nonce invitation 送交獨立 ChatGPT；取得實際外部完成紀錄與 v3 result。按既有 register_schema_validation 驗證 pinned CONTRACT／RESULT；record_result 仍驗證原件 hashes、actor／session、model、nonce、run／Plan／contract／source、Reviewer 非 Planner 及其他必需證據。只有真正接受的 native review，才能由既有 _compile_handoff 原樣凍結 reviewed contract／准入 Implementer。
5. 如果既有 TRUSTED_OPERATOR 政策禁止此來源、無真實 export／model request 證據，或接口仍拒絕此 genuine provenance，停止在該拒絕；不能先讓 Luna 寫 importer 再回填 admission。此時 bootstrap 不成立，須主管另行批准明確的 versioned provenance policy／release，不能由 Sol／Luna審核。

此 profile 在權威採納與 genuine records 到位前為 VERSIONED_ROUTE_PROPOSED，非 SUPPORTED。若後續 CRITICAL 工程需要 ACCEPTANCE_REVIEWER，同一 truthful source 機制亦須由主管明確配置為獨立 ChatGPT 及該 stage 的新 nonce／實際 result，不得回退 Luna。沒有邀請、外部 receipt、schema admission 或 model mapping 變更已發生。

## B03 — 在實際 macOS 邊界限制一次性操作

現有 hosted cua_repl 的 transport／native dispatch 保證 UNPROVEN；禁止用一層 wrapper 包住它就聲稱解決。提出 LINE_ALBUM_ONE_SHOT/1：獨立版本化的本地原生組件直接呼叫 capture／AX／CGEvent 葉節點，agent／host 只提交綁定命令，不負責重送原生 UI 操作。不修 hosted 工具、不修改既有批次備份路徑。

| 邊界 | 必須可驗證的約束 |
| --- | --- |
| Schema eligibility | 4.8.0 固定 retry fields 不變；不得解讀為 IMPLEMENT 診斷 retry 許可。 |
| Agent logic | 單一 task／run／authorized execution ID，只有 LIST_OBSERVE → CLICK → DETAIL_OBSERVE → STOP；拒絕重啟、改 nonce 或第二個 command sequence。 |
| Host／transport | 即使重播同一請求、並行呼叫、client timeout 或 worker crash，原生端以同一持久 execution ID／跨 process lock 拒絕再次執行。新 ID 不能重新武裝同 Task 的一次預算。 |
| Native boundary | 每 phase 先獨占預算，寫 attempted／fsync／讀回，再進原生 API；最多一個 list screenshot／AX snapshot attempt、一對 mouseDown／mouseUp dispatch、一個 detail screenshot／AX snapshot attempt。直接呼叫 ScreenCaptureKit／AX／CGEvent，不委託未知重試的 hosted click。 |

一個 screenshot／AX attempt 指同一 phase 的一次 screenshot 請求及一次有界 AX snapshot traversal；逐屬性的 AX 讀取不是重抓整份 snapshot。不得有 capture polling、錯誤 fallback、重新取得 window／座標、hover 後額外 capture、diagnostic retry 或輸入重派。若現有葉節點含此類行為，不能直接重用。

Intent 保存 task／run／execution ID、fresh frame／AX hashes、canonical group、album 日期／張數／完整卡片及安全 metadata bounds、process/session/window lineage、座標與授權原文引用；在任何 mouseDown 前完成 durable intent 讀回與 consumed reservation。另以不重新 capture 的原生身份／frontmost／geometry／topmost／permission／TTL guard 核對 target。過期即 STOP，不能刷新 frame。直接 event 邊界最多 post 一次 down、一次 up，single-click event state 固定為 1；不可宣稱單個 CGEvent 或 tool call 自動證明 LINE 收到／成功。dispatch trace 與唯一 post-click observation 才能支持 D02 身份判斷。

若 crash 在 reservation 與 API 之間，允許零次實際輸入，永不重派；若 native outcome 不確定，保留不確定與 trace，最多使用尚未消耗的已授權 detail observation，然後 STOP。成功流程需各一次 pre／post attempt；提早拒絕可能只有零／一次 capture，不能為湊次數補抓。沒有跨進程 resume、repair 或再試。raw／intent／journal 均只放 private/，0700／0600；先 check-ignore 與 index preflight，無 raw 上 Git。

這是待實作／驗證的邊界，現在 B03=BLOCKED。Luna 只有在獨立 Plan Review、正式 schema／provenance／Handoff／Controller admission 成立後，才可 IMPLEMENT；此授權階段仍只做非 GUI 實作。針對性驗證只需既有測試工具檢查相同 execution ID 重播／並行／中斷永不多 capture 或 dispatch，以及不確定結果不能重新武裝；再檢視真正 native call sites 與 build hash。不是新的模擬 framework，也不是 LINE Gate PASS。涉及 actuation／authorization 邊界的新工程計畫按上層 §2 採 CRITICAL，需獨立 Acceptance；診斷自身既有四 gates 不因此增加。

### 不得忽略的 goal／provider 變更

本診斷已發佈 goal 明列「現有 cua_repl」。controller.py::publish_plan L456–457 要求 contract.goal 等於 state.goal；沒有已證實的 goal amendment 入口。原生替代組件不能藏在舊名字下執行，也不能直接改 state.goal。主管須先批准精確 provider／scope supersession，並指定合法的版本化 native transition：保留本 Task ID 與所有舊 Plan／run／hash／授權及未執行事實，只新增受審 revision／新 provider binding，既有單一診斷預算不變。若目前 Controller 無支援，最小版本化變更只加入此新 Task 的受權 supersession／admission 入口與一次性組件；不遷移／恢復 ML08，不改舊 Controller。該工程變更本身同樣必須先經上述真實外部 review bootstrap 與 native admission，不能 Sol 自行實作。未有合法 transition 前，不准部署替代組件到本 Task。

## B04 的條件保持

只允許本 TASK-55518bd9640d4ea59ab3a6414a171795 在隔離 state_root 中 one IMPLEMENT run／one valid result submission；真正 IMPLEMENT non-PASS 由現有 record_result L1643–1650 自動記帳／open 最多一 Issue。L1518–1530 completed-consumption 同 digest 去重、不同 digest 拒絕；IssueLedger.open L154–191 own-root lock／stable ID 防止完成路徑生成第二個 root Issue。提交不確定即 STOP，不自動重送；不能把 completed-only idempotency 誇大成跨 crash 原子交易。

_issue_packet L2160–2192 從目前 task／run 綁定 packet；IssueLedger.authorize L287–318 與 guard_task L320–358 需要額外明確條件，open 不隱式授權 continuation／retry／implementation。原 ML08 的 Task BLOCKED、Issue WAIT_HUMAN、c6 consumed=1／retries=0、28 gates／原 root 一律 read-only。本輪 Issues=0，未呼叫 record_result。

## 現在需要的唯一決策

請 Chief Reviewer 審查 LINE_DIAGNOSTIC_ADMISSION/1，明確判斷上述 truthful external-source profile 能否在有權主管採納後合法作為現有 TRUSTED_OPERATOR bootstrap，並審查 native one-shot／精確 provider supersession 的必要範圍。主管須明確批准該外部來源／配置政策與保留本 Task 歷史／單一預算的 provider transition；這兩項均不是 GUI consent 或 native PASS。

若 bootstrap 被拒絕或真實 provider records 不可取得，停止在該唯一來源／權威缺口，不建立工程 Task／PR／adapter。若被獨立批准且真正 native admission 可成立，再建立僅完成此必要組件／transition 的一個可追溯版本化工程工作項；不復用或重置原 ML08 continuation。最終 LINE 仍須新一輪明確前景交接與 screenshot／AX／一次點擊同意，並在真正詳細頁驗證後立即 STOP。
