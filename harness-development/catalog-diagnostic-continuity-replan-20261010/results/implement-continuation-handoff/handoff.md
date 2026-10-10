# 接手指示：在新的對話中繼續實作

你是接手本案的 IMPLEMENTER，請在新的對話中接續 `TASK-20261010-catalog-diagnostic-continuity-replan`。工作儲存庫為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；以下以 `T` 代表 `harness-development/catalog-diagnostic-continuity-replan-20261010/`。先讀完本文件及所列資料，再依適用的授權、契約與方法額度，完成固定修復候選、必要的離線驗證，並備妥同一候選的獨立 pre-live 審查資料。遇到無法排除的阻礙時，保存可重現的證據並撰寫完整的問題提報單。請逐項完成要求，也不要把尚未取得的結果寫成 PASS。

本文件是供新對話接手使用的說明，不取代 `T/handoff.md`、`T/handoff.json` 或凍結契約，也不是 controller receipt。本次只建立交接文件，沒有執行候選修復、測試、OCR 或 LINE 操作。文件日期：2026-10-10。

## 1. 先確認角色、版本與授權

- 接手角色為 IMPLEMENTER。角色改變不會自動增加方法額度，也不會授權操作 LINE；開始前先完成下列核對。
- 依適用的 AGENTS.md、immutable release、`schemas/v3/*.schema.json` 及本案凍結契約辦理。Harness 4.8 資源依 `/Users/hsiaojohnny/.codex/AGENTS.md` 所在位置解析；不得套用其他 task 的 4.9 invitation／stage packet，或沿用舊模板中的 v4.3 schema。
- 使用者提供的 PLAN_REVIEW 結果只表示計畫審查通過：`execution_authorized=false`、`additional_method_slots_available=0`、`controller_admission=BLOCKED`。不得把這次撰寫交接文件或計畫審查通過，當成已獲准新增方法額度、建立修復候選、執行 OCR 或操作 LINE。
- 若目前對話中已有明確授權「一個固定修復候選的一次離線驗證及獨立 pre-live 審查」，核對授權範圍與額度後即可沿用，不必重複詢問；這項授權不包含 LINE 操作。若沒有這項授權，先完成唯讀核對和可供審閱的資料整理，列出仍需決定的事項，停止所有仰賴該授權的工作。

## 2. 開始前必讀、核對並保存狀態

完整閱讀適用的 AGENTS.md、workflow-routing 與 runtime defaults，以及下列本案資料：`T/diagnostic-spec.json`、`plan.md`、`plan-contract.json`、`handoff.json`、`handoff.md`、`results/attempt-ledger.json`、`results/pre-live-replan-01.md`、相關 Planner／Plan Review 結果、`results/high-reasoning-review-01.md` 與其 `.result.json`、`results/implementer.result.json`、gate evidence manifest、FAIL packet 及候選程式碼來源。若資料不存在，記為 UNKNOWN；不可自行補寫成已知事實。

開始任何變更前，記錄 Git HEAD、分支、索引區、已修改及未追蹤檔案，以及相關檔案的位元組數與 SHA-256，作為新的 preservation baseline。保留其他工作，不清理、不還原。核對來源與審查綁定：source SHA-256 為 `f9f5886e186c95c716210f65fcda94887c30644a480532cc451cf2e0fb4c43b8`；歷史 ledger 為 4110 bytes、SHA-256 `3f175c7f5a414f5fdff37c2b9236de7cfef80d03d26d75303d6fc671a62eb9f6`；歷史 plan-contract 與 handoff 的 SHA-256 均為 `0c141010ecd092e3b2556bacf3488bd53d2897d5a234f2b4f4eb2c4945d0818d`。這些只是歷史核對基準，不能證明後續修復契約已建立。

審查紀錄指出，當時 replan 文件尚不存在；現在該文件可能已建立。請查明目前狀態並註明時間與階段差異，不得改寫歷史紀錄，也不能把新文件視為已獲准實作。若來源綁定、範圍、版本或受審查的文件不一致，停止相依工作並提報。

## 3. 依審查內容完成修復

完整遵守已審查 machine contract 中的範圍、四道 gates、負責角色、requiredness、classification、reuse、額度及停止規則。後續修復契約必須精確納入已審查的 replan。若契約不存在、內容不符，或入場所需資料不足，明確記錄阻礙；不可自行製作 controller receipt。須依適用流程完成新契約所需的獨立審查，才能據以執行。

建立需求追蹤表，逐項記錄：`需求／FAIL finding → 固定修復方式 → literal allowed path → 測例／命令 → expected behavior → evidence path／hash → verdict`。完整對照 replan 第 2 至 4 節、所有 FAIL findings 與 R01–R19，不可只依本交接摘要實作。取得授權後，新候選與證據只能新增於 `T/repair-01/`；不得覆寫原候選、replay、raw OCR、manifest、結果或審查封包。helpers=0、writers=0，不委派候選實作。

修復必須完整涵蓋：局部 ROI 與非零原點的座標轉換；modern／legacy 使用相同 parser 檢查全部候選並處理衝突；只接受 viewport 內唯一的 metadata 配對；blocking ambiguity 與身份歷史；逐欄核對可信 binding；遇到 UNKNOWN／CONFLICT 時停止 chain 與輸入；使用注入 clock 的共用 guard；證據採 append-only。runner 必須明確接收來源與新的輸出根目錄，不得隱式寫回。維持凍結的 profiles、confidence、RGBA、indicator、配對幾何、D／ordered overlap、五秒期限、最多兩次唯讀刷新及六次 input 上限；不得更改公開 schema。

## 4. 完成驗證並交付證據

- 固定候選後，保存 candidate／fixture／build／profile／source hashes。依授權執行 R01–R19 與 unittest，並保存實際命令、工作目錄、stdout、stderr、exit code、expected／actual／verdict。R20 維持 NOT_RUN。每項行為結論都必須綁定同一候選與 fixture。
- 局部 OCR 依原 replan 固定方式處理四個畫面，每個畫面六次，共二十四次。保存 crop、nearest 2× derivative、transform 與 raw OCR。R01 分開記錄歷史全圖與新局部結果；不可改寫原始「相溥」，也不可用歷史 D 值校正新結果。
- R06、R07／10／11、R08、R09／12／13、R17、R18、R19 必須取得 replan 所列的實際正向與負向行為證據，包括 dispatch=0、沒有新增 chain edge、clock／readback、callback sequence、terminal state，以及實際拒絕重用的結果。測試數量、常數、hash 差異或編譯成功，都不能代替行為證據。
- 新 OCR 驗證開始前，以不可覆寫事件記錄本次額度消耗並引用舊 ledger；保留歷史 3+1。若已獲准且確實使用一次，完整累計為五次。v3 `meaningful_attempts` 不重設，也不可超過 schema 上限；完整歷史另行記錄。任何必要測例失敗，保存最小重現後立即停止；不可調整 ROI／profile／門檻，也不可更換候選重試。
- 將同一候選的離線結果交由獨立 pre-live reviewer 審查；實作者不得自行宣稱獨立 PASS。若無法取得獨立審查，交付 review packet 並維持 PENDING。完成這個離線階段後停止；live 維持 0/6。後續任何 live 工作都須另有適用授權、同一候選的 offline／pre-live PASS，以及新的前景協調。
- 四道 required gates `G_OFFLINE`、`G_LIVE`、`G_PRESERVE`、`G_ACCEPTANCE` 全部保留。以新的 baseline 核對 preservation delta；發現漂移就停止，不得還原。視覺人工判讀記為 OBSERVED；完整列表覆蓋維持 NOT_ESTABLISHED，除非取得契約要求的新證據。
- 更新 task 內的 progress.md，交付變更與需求追蹤表、證據 manifest、未解決阻礙，以及符合 `schemas/v3/result.schema.json` 的結果。六個 status 分別記錄；離線階段交付完成不代表整個 task 已 DONE。本地 validator 的 VALID 只代表本地語義驗證通過；正式 validation／controller admission 必須依實際 receipt 記錄。

## 5. 無法解決時，提交完整問題提報單

遇到下列情況立即停止受影響的工作：缺少授權／額度／契約、binding 或 preservation 漂移、必要測例 FAIL、安全狀態為 UNKNOWN／CONFLICT，或必須變更範圍與政策。一般收斂依 task 的嘗試額度辦理；連續兩次沒有新資訊就升級，重大阻礙則更早停止。本案固定驗證只要失敗一次就停止，不得援引一般三次上限增加方法額度。

在契約允許的 task evidence 路徑新增 `問題提報單-<阻擋指紋>.md` 及相關證據。若契約不允許寫入，先在回覆中提供完整提報內容並說明限制。只用已授權且必要的方式蒐集資料；不得為了蒐證而操作 LINE、聯絡外部服務或擴大工作範圍。

問題提報單必須包含：

1. TASK／RUN／角色／stage、時間、儲存庫／HEAD／release，以及適用 plan／handoff／candidate hashes。
2. 原定目標、受阻需求與 gate、阻擋指紋、觸發條件、預期與實際行為，以及影響範圍。
3. 最小重現所需的前置條件、精確命令／輸入／fixture、stdout／stderr／exit code；未執行的步驟須明確標示。
4. 嘗試紀錄：歷史及本次額度、每次變更與觀察、取得的新資訊、停止原因；保留失敗結果。
5. 分開列出 facts／inferences／unknowns；列出根因假設及支持或反對的證據，不可將推測寫成已確認的根因。
6. 證據清單：相對路徑、bytes、SHA-256、candidate／fixture binding、相關 diff 與 baseline delta；敏感資料應減至必要範圍，原始證據不得修改。
7. 已證實的實作／核心事實、未通過及未執行的 gates、六個 status，以及為何無法在現有範圍內解決。
8. 下一位接手者可直接採取的有限處置、唯一待決事項、清楚選項與建議、所需新增授權／額度、成功證據，以及再次失敗時的停止點。

最後回覆須明確說明完成結果或阻礙，提供交付檔案、實際驗證結果及未完成事項。沒有明確授權時，不得 commit、push、deploy 或存取 production。
