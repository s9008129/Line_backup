# Pre-live 審查 FAIL：bounded replan 01

本文件保存 Planner 在對話提出的完整 bounded replan。後續使用者已明確要求保存文件並執行 add、commit；這是文件發布授權，不是候選修復、新方法驗證或 live input 授權。規劃階段未寫檔的事實，與後續保存／提交階段分開記錄。

依據：[獨立審查摘要](high-reasoning-review-01.md)、[完整審查結果](high-reasoning-review-01.result.json)、[凍結交接](../handoff.md)、[凍結契約](../plan-contract.json)。本文件不是 controller receipt，也沒有取代或修改上述材料。

## 1. 摘要與本輪範圍

本計畫只產出 `results/pre-live-replan-01.md`。修復候選、重新驗證及 LINE 操作均不在本輪授權內。以下以 `T` 代表 `harness-development/catalog-diagnostic-continuity-replan-20261010/`。

- 保留原候選、結果、審查封包、凍結契約、門檻及四道 required gates。
- 保留歷史 **3+1 方法、live 0/6**；沒有可自行使用的新方法額度。
- 沿用 STANDARD、獨立 Plan Review、同候選 pre-live 審查及最終獨立 Acceptance；候選工作 helpers、writers 均為零。
- 若後續取得新方法授權，候選與證據全部新增於 `T/repair-01/`，不覆寫舊材料。此路徑是待審查與授權的修復提案，不是本次可執行範圍。
- 使用者要求的 GPT6-luna（xhigh）子代理只讀上下文並草擬文件提交訊息；沒有參與候選修復，也不是 Plan Review 或 Acceptance。

本次文件發布沿用現有 HEAD 作提交基底；先前保存的 Git 基線與審查時 HEAD 都只保留為歷史，不要求回寫或還原。不得納入無關產品修改、快取或其他 task。

## 2. 候選修復規格

以下全部是待授權後的修復規格；本次沒有實作。

| 項目 | 固定修復方式 |
|---|---|
| 局部 ROI | 回放沿用 scan-000 bootstrap 的文字 guard 與列表 viewport，分別裁切後 nearest 2×。兩 API 的身份 profile 分別處理標題帶及列表；兩個標籤 profile 處理標題帶，共每幀六次、四幀二十四次。保存 crop、derivative、轉換及 raw OCR；不再以全圖 OCR 代替局部方法。這些座標只供 replay。 |
| 身份候選與配對 | modern、legacy 使用相同 parser，解析全部實際候選。best 不合法不得挑次候選補救；不同有效候選立即衝突。兩 API 的日期／張數框都必須完整位於 viewport、同 metadata block，符合既定唯一配對規則。禁止跨卡或從 viewport 外配成 agreement。 |
| Ambiguity 與歷史 | blocking ambiguity 必須阻止 scroll 與 chain。保存已確認身份歷史，檢查同幀 duplicate、跨幀日期張數漂移及非相鄰 reappearance；正常相鄰重疊仍可成立。partial／unconfirmed 行不得作橋。 |
| Binding | 依可信凍結 manifest 核對實際 candidate、profile、source、RGBA、OCR、decoder/build bytes；重算 binding hash。檢查 run、mode、provider/session、geometry、scale、mapping 及 previous evidence。bootstrap ID 與每幀 observation ID 分開；安全與 OCR 必須綁當前 frame。未知必要欄位不能回 VALID。群組 key 與名稱來自 config／既有確認證據，移除 placeholder 與硬編碼身份。 |
| Chain 與停止 | 集中彙整阻擋原因；indicator 非 PASS、身份衝突／ambiguity、binding 失效或必要證據未知時，不延伸 chain、不允許下一次輸入。停止後晚到結果只補證據。維持既定 D／overlap 公式；NO 只用於已證明 metadata raster／layout 未變，其餘未能證明 YES 的情況記 UNKNOWN／CONFLICT。 |
| 輸入流程 | 新增共用 guard，注入 clock、保存／讀回、觀察及 dispatch callbacks，供離線測試。後續 live adapter 必須使用同一 guard；未完成接線驗證前，不得以這些測試宣稱實機安全。 |
| 不可覆寫證據 | frame manifest 一次建立後保持不變。evaluation、metadata、chain state 另存新檔，以路徑與 hash 串接；禁止 write-mode 回寫 manifest。新狀態說明另存，保留原問題單與 PASS 記錄並標明其歷史地位及審查限制。 |

公開 schema 不變。候選本地介面新增可信 candidate manifest 與 previous evaluation 輸入；runner 明確接收來源與新輸出根目錄，禁止隱式寫回原驗證目錄。

原 profiles、confidence 政策、RGBA 零差異、indicator 信號處理、配對幾何、D、ordered overlap、五秒期限、兩次唯讀刷新及六次 input 上限維持凍結規則。此 replan 修復的是實作未遵守規則及欠缺行為證據的部分，不允許失敗後調整政策。

## 3. 實際驗證與成功條件

以下均是**待授權後的檢查**，本輪不執行。所有 fixture 只處理獨立測試材料，不修改原始照片、回放或凍結文件；fixture PASS 不代表 native 或 live PASS。

| 測例 | 必須取得的行為證據 |
|---|---|
| R06 | 先建立其他條件全部成立的 fresh 正向 fixture，再逐一改為 viewer、dialog、menu、editing、occluded 或 safety UNKNOWN；每例 dispatch=0，保存明確安全阻擋原因。 |
| R07／R10／R11 | 隔離測試 legacy 次候選衝突、框位於 viewport 外、缺讀，以及每個 binding 欄位漂移／全零 hash；不得取得 agreement、scroll 或 chain 權限。 |
| R08 | 用可控 clock 與實際新檔保存／讀回，使 age 跨過五秒；驗證 dispatch 前拒絕、刷新最多兩次、第三次不執行。另測 readback 不符與刷新成功路徑。 |
| R09／R12／R13 | 透過完整 evaluator 驗證 ambiguous count、duplicate、跨幀 count drift、非相鄰 reappearance、順序缺口及反序；斷言停止、無新 chain edge、無 scroll。 |
| R17 | 實際處理非零 x/y crop origin 的 fixture，逐像素核對 crop＋nearest 2×，並核對 helper 輸出的座標轉換。保留 JPEG 內容辨識、歷史全圖轉換及四角方向檢查。 |
| R18 | 驅動共用 guard，注入 UNKNOWN、error、可能已發送後 crash、late result、重啟及第七次請求。保存 callback 序列、輸入計數與 terminal state；驗證不 resend、不 resume、不超六次，UNKNOWN 最多在 10／30 秒作兩次唯讀觀察。 |
| R19 | 在獨立 fixture 中改 replay、required immutable input、profile、candidate 或 previous result，實際呼叫拒絕重用流程，記錄拒絕原因及退出結果；不能只比較 hash。歷史 Git 的 PROVENANCE_ONLY 記錄維持原分類。 |
| 全套 | 新候選重新執行 R01–R19 及 unittest，保存真實 stdout、stderr、exit code、expected／actual／verdict。R01 分開驗證舊 OCR 回放與新局部 OCR；原始「相溥」不改寫。R20 保持 NOT_RUN。 |

每個測例綁定同一凍結候選與 fixture hash。任何必要測例失敗，保存最小重現後停止，不換 ROI、profile、門檻或候選重試。不能以 unittest 方法數量、政策常數、hash 不同或編譯成功取代所宣稱的行為證據。

四幀新局部 OCR 的結果獨立保存與評估，不用新辨識文字覆寫歷史 raw OCR，也不拿歷史 D 值校正新結果。每份 artifact 都須能核對来源、crop、scale、profile、API 及 candidate。

## 4. 額度、證據失效與交接

建議的後續決策是：**另行授權一個固定修復候選的一次離線驗證及獨立 pre-live 審查，完成後停止交付；不包含 live input。** 這只是具體提案，尚未授權。若未取得該決策，不建立修復候選、不重跑 OCR。

- 新候選會使舊候選測試及 pre-live 審查不可重用；原正向回放與歷史保存事實仍保留。
- 新 ledger 以不可覆寫事件引用舊 ledger。追加驗證消耗後，完整累計為五次；v3 `meaningful_attempts` 仍保留歷史三次，另欄說明完整累計。開始新固定候選的新 OCR 驗證前記錄該次消耗，不以 task／process／frame 名稱重設額度。
- 新計畫須重新獨立審查；舊 Plan Review 不替新計畫背書。四道 gate 的 requiredness、owner、classification 與 reuse 原樣保留。
- 保存 gate 使用後續實作開始時的新 baseline，涵蓋舊任務、凍結文件、產品、config、state、registry、backups 及 Git；遇漂移停止，不還原使用者工作。
- live 仍為 0/6。本 replan 不啟動或重綁 live；任何後續 live 階段須有明確適用的授權、同候選離線及 pre-live PASS、新前景就緒與原停止規則。
- controller admission 保持 BLOCKED。沒有 stage packet、發布回應及固定驗證命令時，正式 validation 維持 NOT_RUN，不自行組裝 validator 或 receipt。

| Gate | Required／owner／phase／source | GOAL_CRITICALITY／EVIDENCE_ROLE／CLOSURE_GATE／reuse |
|---|---|---|
| G_OFFLINE | true／ROLE／IMPLEMENT／ROLE_OBSERVATION | CORE／OUTCOME／HARD_CLEAN／SAME_BUILD |
| G_LIVE | true／ROLE／IMPLEMENT／ROLE_OBSERVATION | CORE／OUTCOME／HARD_CLEAN／NEVER |
| G_PRESERVE | true／ROLE／IMPLEMENT／ROLE_OBSERVATION | SUPPORTING／MUST_NOT_BREAK／BASELINE_DELTA／NEVER |
| G_ACCEPTANCE | true／ROLE／ACCEPTANCE／ROLE_OBSERVATION | CORE／OUTCOME／HARD_CLEAN／NEVER |

此表逐項保留原契約分類，沒有新增 PASS、waiver 或 gate receipt。原 G_OFFLINE／G_PRESERVE 的歷史記錄不改寫；審查對完整 required 證據的不足另行保留。視覺／人工判讀維持 OBSERVED；完整列表覆蓋維持 NOT_ESTABLISHED。

本輪成功條件是交付上述完整 bounded plan；沒有相依實作、驗證或 UI 輸入。文件提交完成不代表診斷 TASK_CLOSURE_STATUS=DONE。

## 5. Planner 結果草案（format 3）

以下保存規劃階段提出的結果草案；其中「未寫檔／commit」描述當時的唯讀規劃階段，不描述本文件後續發布。草案未經 controller 發布或正式驗證，hash=null 不可解讀為有效新契約或 Handoff。所列 run ID 僅沿用使用者轉交材料的來源綁定。

`needs_human=false` 只指本輪 bounded 計畫準備不需重複授權；新方法執行仍須第 4 節明列的額度決策，不得由此欄推論已授權。

```json
{
  "result_format_version": "3",
  "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
  "run_id": "2d52b72c-e184-5204-9a42-ff032631d6f6",
  "role": "PLANNER",
  "stage": "PLAN",
  "candidate_fact": "PARTIAL",
  "validation_fact": "NOT_RUN",
  "routing_fact": "PLAN_REVIEW",
  "statuses": {
    "PRIMARY_OUTCOME_STATUS": "NOT_ACHIEVED",
    "IMPLEMENTATION_STATUS": "IN_PROGRESS",
    "CORE_ACCEPTANCE_STATUS": "NOT_RUN",
    "REQUIRED_VERIFICATION_STATUS": "INCOMPLETE",
    "INDEPENDENT_ACCEPTANCE_STATUS": "PENDING",
    "TASK_CLOSURE_STATUS": "REPLAN_REQUIRED"
  },
  "gate_results": [],
  "evidence_ids": ["ATTEMPT_LEDGER"],
  "plan_sha256": null,
  "handoff_sha256": null,
  "source_sha256": "f9f5886e186c95c716210f65fcda94887c30644a480532cc451cf2e0fb4c43b8",
  "plan_contract_sha256": null,
  "analysis": {
    "facts": [
      "唯讀來源核對的五個方法檔案 aggregate hash 仍為 646145c69265cc33aae2ceaa860efa97048b04cc0e4c17c6bdea69902e11a5b6。",
      "ledger 記錄歷史三次加已消耗追加一次，live 為 0/6。",
      "本輪只讀取材料與核對來源身份；未寫檔、執行 runner、重跑 OCR、操作 LINE、commit 或 push。"
    ],
    "inferences": [
      "修復超出原語法／路徑小修例外；開始新候選驗證需要明確追加方法授權。",
      "舊測試與 pre-live 審查不能作新候選的 required 證據。"
    ],
    "unknowns": [
      "沒有本輪 controller stage packet、publication receipt 或固定驗證命令。",
      "修復後的離線結果與實機結果尚未取得。"
    ],
    "evidence": [
      "使用者轉交的 HIGH_REASONING_REVIEW FAIL。",
      "handoff.md 第 5–12 節及候選 evaluator、runner、測試來源。",
      "results/attempt-ledger.json 的已消耗方法與 live 計數。"
    ],
    "confidence": "HIGH：規劃依據已讀取；未宣稱修復或驗收通過。",
    "controller_admission": "BLOCKED",
    "execution_authorized": false,
    "additional_method_slots_available": 0,
    "run_id_note": "沿用來源綁定，不代表新的 controller invocation。",
    "future_execution_decision": "另行授權一個固定修復候選的一次離線驗證及獨立 pre-live 審查；不包含 live input。"
  },
  "evidence_manifests": [
    {
      "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
      "run_id": "2d52b72c-e184-5204-9a42-ff032631d6f6",
      "stage": "PLAN",
      "role": "PLANNER",
      "source_sha256": "f9f5886e186c95c716210f65fcda94887c30644a480532cc451cf2e0fb4c43b8",
      "evidence_id": "ATTEMPT_LEDGER",
      "path": "harness-development/catalog-diagnostic-continuity-replan-20261010/results/attempt-ledger.json",
      "bytes": 4110,
      "sha256": "3f175c7f5a414f5fdff37c2b9236de7cfef80d03d26d75303d6fc671a62eb9f6",
      "contract_sha256": null,
      "observation": "唯讀核對歷史 3+1 與 live 0/6；不是新 gate receipt。"
    }
  ],
  "handoff_summary": "已準備 bounded replan，涵蓋局部 ROI、身份衝突、ambiguity、binding、chain、輸入 guard 及實際負向驗證。保留原候選、證據、四道 required gates 與 3+1／live 0/6。本輪沒有新方法授權，亦未寫檔或開始相依操作。下一步只可審查此計畫；新候選驗證須另有明確額度決策。正式 validation NOT_RUN，controller admission BLOCKED。",
  "needs_human": false,
  "human_decisions": [],
  "convergence": {
    "meaningful_attempts": 3,
    "consecutive_no_progress": 0,
    "last_attempt": "唯讀準備 bounded replan；未新增方法嘗試。完整歷史 3+1 仍以原 ledger 為準。",
    "information_gain": true,
    "stuck": true
  }
}
```
