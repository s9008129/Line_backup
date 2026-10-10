# 接手 Prompt：在新對話繼續 IMPLEMENT

你是接手的 IMPLEMENTER，正在新對話繼續 `TASK-20261010-catalog-diagnostic-continuity-replan`。工作 repository 為 `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`；以下 `T` 指 `harness-development/catalog-diagnostic-continuity-replan-20261010/`。先完整讀取本文件與引用材料，再於適用授權、契約及額度內完成固定候選修復、全部必要離線驗證與獨立 pre-live 審查交接。遇到不可解決的阻擋，保存可重現證據並交付精準問題提報單。不要只回覆計畫，也不要把尚未取得的結果寫成 PASS。

本文件是新的人工接手說明，不取代 `T/handoff.md`、`T/handoff.json` 或凍結契約，不是 controller receipt。本次使用者要求建立交接文件；沒有因此執行候選修復、測試、OCR 或 LINE。日期：2026-10-10。

## 1. 先釐清角色、版本與授權

- 接手角色是 IMPLEMENTER。角色切換本身不產生新方法或 live 授權；先完成以下啟動核對。
- 本案依適用的 AGENTS.md、immutable release、`schemas/v3/*.schema.json` 及本案凍結契約辦理。Harness 4.8 資源從 `/Users/hsiaojohnny/.codex/AGENTS.md` 相對解析；不可使用其他 task 的 4.9 invitation／stage packet，或套用舊模板的 v4.3 schema。
- 使用者轉交的 PLAN_REVIEW 結果只在 plan level 為 PASS：`execution_authorized=false`、`additional_method_slots_available=0`、`controller_admission=BLOCKED`。不得把這次 prompt 編寫或 Plan Review PASS 當成追加方法、修復候選、OCR 或 live 授權。
- 若後續對話已明確授權「一個固定修復候選的一次離線驗證及獨立 pre-live 審查」，核對其範圍與額度後沿用，不重複詢問；該授權不含 live input。若缺少此授權，先完成唯讀核對及可審閱交接，列出唯一必要的追加決策，再停止相依執行。

## 2. 啟動時必讀、核對與保存

完整讀取適用 AGENTS.md、其 workflow-routing 與 runtime defaults，以及 `T/diagnostic-spec.json`、`plan.md`、`plan-contract.json`、`handoff.json`、`handoff.md`、`results/attempt-ledger.json`、`results/pre-live-replan-01.md`、相關 Planner／Plan Review 結果、`results/high-reasoning-review-01.md` 與 `.result.json`、`results/implementer.result.json`、gate evidence manifest、FAIL packet 及候選來源。不存在的材料記 UNKNOWN，不自行補造。

先觀察 Git HEAD、branch、index、dirty／untracked 檔案與相關檔案 bytes／SHA-256，保存新 baseline；保留無關工作，不清理、不還原。核對來源與審查綁定：source SHA-256 `f9f5886e186c95c716210f65fcda94887c30644a480532cc451cf2e0fb4c43b8`；歷史 ledger 為 4110 bytes、SHA-256 `3f175c7f5a414f5fdff37c2b9236de7cfef80d03d26d75303d6fc671a62eb9f6`；歷史 plan-contract 與 handoff SHA-256 均為 `0c141010ecd092e3b2556bacf3488bd53d2897d5a234f2b4f4eb2c4945d0818d`。這些是歷史核對錨點，不代表未來修復契約已成立。

提供的審查稱 replan 文件當時不存在，但現在可能已保存；核對現況並標記時間與階段差異，不覆寫歷史、不把新文件當成已授權實作。binding、scope、版本或 reviewed artifact 不符時停止相依操作並提報。

## 3. 編製完整交接後才實作

逐字保留 reviewed machine contract 的 scope、四道 gates、owner、requiredness、classification、reuse、預算及停止規則。未來修復契約必須精確編碼已審查 replan；契約缺失、差異或 admission 所需材料缺失時，明列 blocker，不自行產生 controller receipt。依適用流程完成新契約的必要獨立審查後，才能使用它執行。

建立需求追蹤表：`需求／FAIL finding → 固定修復 → literal allowed path → 測例／命令 → expected behavior → evidence path／hash → verdict`。逐項覆蓋 replan 第 2–4 節、完整 FAIL finding 與 R01–R19，不能以本 prompt 摘要取代原規格。新候選與證據只新增於經授權的 `T/repair-01/`；原候選、replay、raw OCR、manifest、結果與審查封包不覆寫。helpers=0、writers=0，不委派候選工作。

實作必須全部涵蓋：局部 ROI 與非零原點座標轉換、modern／legacy 同 parser 的全候選衝突檢查、viewport 內唯一 metadata 配對、blocking ambiguity 與身份歷史、逐欄可信 binding、UNKNOWN／CONFLICT 停止 chain 與輸入、注入 clock 的共用 guard，以及 append-only 證據。runner 明確接收來源和新輸出根，不隱式寫回。維持凍結 profiles、confidence、RGBA、indicator、配對幾何、D／ordered overlap、五秒期限、兩次唯讀刷新與六次 input 上限；不更改公開 schema。

## 4. 驗證與交付不可遺漏

- 固定候選後，保存 candidate／fixture／build／profile／source hashes；執行已授權的 R01–R19 與 unittest，保存實際命令、cwd、stdout、stderr、exit code、expected／actual／verdict。R20 維持 NOT_RUN。每個行為結論綁同一候選與 fixture。
- 局部 OCR 依原 replan 四幀、每幀六次，共二十四次的固定方法；保存 crop、nearest 2× derivative、transform 與 raw OCR。R01 分開記錄歷史全圖與新局部結果；不改寫原始「相溥」，不以歷史 D 校正新結果。
- R06、R07／10／11、R08、R09／12／13、R17、R18、R19 必須取得 replan 表格指定的實際正負向行為證據，包括 dispatch=0、無新 chain edge、clock／readback、callback sequence、terminal state 與實際拒絕重用。測試數量、常數、hash 差異或編譯成功不能替代行為證據。
- 新 OCR 驗證前以不可覆寫事件記錄額度消耗並引用舊 ledger；保留歷史 3+1，若授權一次並實際消耗則完整累計為五。v3 meaningful_attempts 不重設、不超 schema 上限，完整歷史另欄明列。任何必要測例失敗，保存最小重現後停止；不調 ROI／profile／門檻、不換候選重試。
- 同候選離線結果交給獨立 pre-live reviewer；實作者不能自評獨立 PASS。缺少独立審查能力時交付 review packet，狀態保持 PENDING。此離線階段完成後停止交付，live 維持 0/6；後續 live 需另外適用授權、同候選 offline／pre-live PASS 及新前景協調。
- 保留 G_OFFLINE、G_LIVE、G_PRESERVE、G_ACCEPTANCE 全部 required。以新 baseline 做 preservation delta；漂移停止，不還原。視覺人工判讀為 OBSERVED，完整列表覆蓋保持 NOT_ESTABLISHED，除非取得契約要求的新證據。
- 更新 task 內 progress.md，交付變更與需求追蹤表、證據 manifest、剩餘阻擋及符合 `schemas/v3/result.schema.json` 的結果。六個 status 分開記錄；離線交付完成不能宣稱整體 DONE。固定本地 validator 的 VALID 只代表本地語義驗證，正式 validation／controller admission 依實際 receipt 記錄。

## 5. 卡關時交付精準問題提報單

適用停止條件立即生效：缺授權／額度／契約、binding 或 preservation 漂移、必要測例 FAIL、安全 UNKNOWN／CONFLICT、範圍或政策需變更。一般收斂沿用 task 的嘗試預算；兩次無新資訊就升級，重大 blocker 更早停止。本案一次固定驗證失敗即停止，不以一般三次上限增加方法額度。

在契約允許的 task evidence 路徑新增 `問題提報單-<阻擋指紋>.md` 與相關證據；未允許寫入時，先在回覆交付完整內容並說明寫入限制。蒐集只用已授權、必要且不消耗額外方法的方式，不為蒐證操作 LINE、聯絡外部服務或擴大 scope。

提報單必須含：

1. TASK／RUN／角色／stage、時間、repo／HEAD／release、適用 plan／handoff／candidate hashes。
2. 原目標、受阻需求與 gate、阻擋指紋、觸發條件、預期與實際行為、影響範圍。
3. 最小重現的前置條件、精確命令／輸入／fixture、stdout／stderr／exit code；未執行的步驟明確標示。
4. 嘗試表：歷史與本次額度、每次改動與觀察、獲得的新資訊、停止原因；保留失敗結果。
5. facts／inferences／unknowns 分開；根因假設及支持／反對證據，禁止把猜測寫成已確認根因。
6. 證據清單的相對路徑、bytes、SHA-256、candidate／fixture binding、相關 diff 與 baseline delta；敏感資料最小化且不改原證據。
7. 已證明成立的實作／核心事實、未通過與未執行 gates、六個 status，以及為何無法在現有範圍解決。
8. 下一位可直接執行的有界處置、需要的唯一決策、清楚選項與建議、所需新增授權／額度、成功證據及再次失敗時的停止點。

最終回覆提供實作或阻擋的明確結論、交付檔案連結、實際驗證與未完成項目。除非已有明確授權，不 commit、push、deploy 或存取 production。
