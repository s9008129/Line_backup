# 全新證據驅動的 Rev28 修復

使用者要求重新規劃與執行修復，由 agent 自主處理，只有需要人介入（包括 LINE 前景）時再提出。這份計畫根據目前原始碼建立，不沿用舊根因或舊 PASS 作新驗收。保留現有 dirty work、歷史檔案與一次性權利；重新開始不代表清除它們。

## 問題與本輪目標

目前 NativeObservationSession 擷取前讀 process／signing／AX，擷取後卻以原 process 建構 FreshWindowObservation。擷取後 CG inventory 取兩次，WindowIdentity 和 bundle 可能使用不同快照；bundle 只確認目標存在，不核實 CG target 唯一性與 CG／SCK frame。CLI ProcessIdentity 在目標簽章讀取失敗時改用自身 executable 的簽章，會混淆 caller 和真正主體。這些根因由目前 source 直接發現，尚未宣稱測試重現或效能量測。

本輪可在本機修復與獨立驗收的目標：成功 bundle 有擷取前後一致的真正 process／AX／signing identity，identity 與 bundle 共用單一 CG snapshot；讀不到目標簽章維持 nil／UNKNOWN，不繼承 caller 簽章。真實 LINE composition 校準、popup／遮擋、chooser、檔案內容與生產權利／root 核實需要另有實機證據，本輪不把它们當成已完成。

## 授權、範圍與流程

分類 CRITICAL：影響不可逆 dispatch 前的身份證據，必須 fresh 獨立 Plan Review、byte-identical deterministic Handoff、root serial implementation、fresh 獨立 Acceptance。使用者已授權本機修復與檢查，不再詢問例行檔案修改或測試。修改只在 contract literal paths，helpers=0、writers=0；reviewers 不參與產品修改。

不修改持久權利、原 authorization、goal-slot／ledger／baseline／frozen rules／HarnessCalibration，不操作 LINE、下載、commit、push、網路／provider。不改 0.5pt 容差、freshness／deadline、窗口唯一性、OCR、click／Save All／chooser 語義。如需新 public／protected decision 或其他路徑，先 replan；真正需要人介入時準備具體內容再提出。

TASK-72f1aa0a445a4c27af10491fefe014f2 只建立了狹窄 observation 範圍，未凍結計畫、未產品修改、未實作嘗試。簽章錯置是後續新 source 發現，因此在凍結前另建本 task，不手改其 state 或 scope。歷史額度與權利不因新 task 重置。

## 最小修復

1. 以本 task start-snapshot 保護所有現有檔案、歷史 set、HEAD／branch／index、dirty patch；新取 source manifest，舊測試結果不當新 PASS。fresh reviewer 明確 PASS 後才修改產品。
2. 在現有 below-OS fake 增加 post process／signing／AX 變更及讀取 error、CG sequence／call counts／duplicate／bad frame。先保存目前產品的 red regression raw logs，證明 process swap 或 mixed inventory 可通過／取兩次。Replacement signing reader 的 unknown-target regression 對真正 native adapter 與 pure information parser 驗證，不以 fake PASS 代替 production 行為。
3. 擷取與 OCR 後重新讀 process instance、signing、bound AX，比較前後 equality，error 或不一致 typed refusal。nil signing 前後皆 nil 可維持 unknown，不提升為簽章 PASS。新增 bundle post-identity 欄位，validated() 重新驗證 equality，不假造 post-read。所有新增讀取時間计入原 absolute deadline，成功驗證後才增加 capture count。
4. 每個 completed capture 只讀一次 post CG inventory，該 snapshot 同時供 WindowIdentity 與 bundle。CG 同 window／pid／layer 必須唯一，SCK pre／post main window 必須唯一一致；CG 與 pre／post frame 用現有 0.5pt tolerance 交叉核對。拒絕 non-finite、empty／non-positive bounds、重複 window IDs、錯 owner／layer、frame drift。validated() 重算 stored CG entry 與同一 snapshot 一致，不取 first match 掩蓋衝突。
5. 新 Core ProcessCodeIdentity 封裝原 native Security 讀取指定 PID 簽章，CLI wrapper 使用它。guest／static／information／identifier 任一步失敗皆 nil，移除 caller static fallback。有效 target identifier／team 表達沿用原規則，缺失／空 identifier unknown；pid<=0 與不可用 target unknown。Core target 自動收新檔，不需改 Package.swift 或 chooser predicate。
6. 更新 ARCHITECTURE／CAPABILITY-MATRIX 只描述新實作與本輪實測。沒有觀察的實機事項保持 UNKNOWN／NOT_RUN；舊 digest 不能替新程式授權下載。

## 必要 gates

- G1_PLAN_REVIEW（PLAN，CORE／MUST_NOT_BREAK）：fresh 獨立 reviewer 對 exact frozen plan／contract 明確 PASS。contract 原樣複製為 handoff.json。
- G2_REGRESSIONS（IMPLEMENT，CORE／OUTCOME）：保存 red counterexamples；修復後 NativeObservationSessionTests／ProcessCodeIdentityTests 全 PASS。涵蓋穩定身份、穩定 nil signing、single CG read；process／AX／signing drift、read errors、CG duplicate／invalid／mismatch、deadline、拒絕不增 count。負向案例觸發真實缺口，不寫鏡像 implementation 的測試。
- G3_LOCAL_CHECKS（IMPLEMENT，SUPPORTING／REPOSITORY_HEALTH）：新執行 swift build --package-path rev28 --product rev28ctl；swift test --package-path rev28；rev28/Tools/replay_rev28.py --output 新 task evidence/replay.json；rev28/Tools/verify_pre_live_provenance.py；git diff --check。記錄 command／exit／raw logs／hash，任何 FAIL 不得省略或改記 PASS。
- G4_PRESERVATION（IMPLEMENT，CORE／MUST_NOT_BREAK）：against 本輪 snapshot，scope 外的既有 bytes、歷史 set、HEAD／branch／index 全保留，本輪新增／變更只在 literal paths。保留 scope 內原 dirty work，不 revert／clean。單列生成 .build caches；最終 source／patch 綁這輪 candidate。原 production state 不寫入。
- G5_INDEPENDENT_ACCEPTANCE（ACCEPTANCE，CORE／OUTCOME）：未參與 plan／tests／code／docs 的新唯讀 reviewer，讀 candidate、red-green、raw logs、scope／preservation，明確 PASS 或一項 bounded correction。只判定 local implementation，不代替 live／下載證據。

全部 HARD_CLEAN、NEVER reuse。記錄 format3 與六個獨立 status；原備份成功和 bounded local fix 分開。native transport completion receipts 若不可取得，只記錄 actual advisory results；不捏造 controller actor／admission，不手改 state.json。OS sandbox、network denial、root actual model 未有平台證據即 UNKNOWN。

## 收斂與下一階段

新 root issue 最多 3 次有證據實作，連續兩次無新資訊就升級，重大 blocker立即停止。保留 minimum reproduction、facts／unknowns、最後學到什麼及下一步失敗時的處理。獨立 reviewer 的一項原 scope correction可沿用本輪授權；新範圍或保護語義重新規劃，不重置歷史 dispatch／retry counters。

先自主完成本機修復及獨立驗收，現在不需要 LINE。通過後核實當下實機／原始資料可用性並規劃 precise capture／校準；第一次確實需要看 LINE 當下畫面時，才請使用者把指定目標視窗／相簿開到前景。配合前景不是 Save All 或下載授權。原權利／canonical root不明時不建立空 slot／ledger、不換 runID／destination、不改原 digest。平台或真實證據不足時保留已證明 local outcome，完整專案修復／原備份仍未完成。
