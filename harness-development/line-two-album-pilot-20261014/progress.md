# 進度（獨立正式 E2E 測試員 / Ollama Cloud `minimax-m3.1-flash`）

## 我們在解決什麼

目標是用正式產品入口 `runTwoAlbumPilot()`，在真實 Mac LINE 裡連續完成兩本相簿：A `2024/04/22～04/26`（45 張）與 B `2024/4/21`（78 張），各做一次 Save All、逐檔下載與原圖驗證，最後讀回正式 `VERIFIED`。本輪的目標**不是**把兩本跑完，而是把「在第一個閘門就被擋下」這件事的證據做到可被外部審查重現，並把證據包本身的不自洽處修掉。

## 目前狀態（白話）

- **正式 E2E 仍被阻塞，判定不變**：`FORMAL_TWO_ALBUM_AUTO=BLOCKED`。A、B 的 Save All／下載／正式 `VERIFIED` 與真實捲動全部**未執行**；Save All 派送 0、chooser 0、下載 0 檔、ledger／state 寫入 0、`state/backup_state.json` revision 35→35。既有 239 張正式 VERIFIED、109 張 Manual Diagnostic、65 張 Owner 排除相簿**完全未觸碰**。
- **第一真實阻塞**：`PROJECT_CONTRACT_DRIFT`，第一拒絕點在 `src/line_backup_batch/cli.py:437`。Expected `6258099c2afe7751f2888f28005e0232990db70ef23ec25562b466a7af189c29`、Actual `c2d70e2cb6a209478805169da453475ce2deb2c3cc9821402f5449acad32e5d5`。Authorizer 在讀任何 LINE 畫面、寫任何 ledger 或 state **之前**就以 exit 4 拒絕，所以 `runTwoAlbumPilot()` 從未被呼叫，也沒有用 raw CUA 取代正式 AUTO。
- **根因是「兩代 authority bundle 並存」**，不是單一檔案寫錯：grant 綁的是 `d5436e1` 世代的 contract／source／entry／runtime 雜湊，而現存的 `runtime-binding.json`、`implementation-review.json`、`live-readiness.json` 全指向 `22cee2b` 世代。**只改單一 sha 欄位只會讓下一個 gate 再失敗一次，必須整組重發 6 個 authority 檔。**
- **第二個獨立阻塞尚未觸發**：新 task 無法初始化 GUI ledger（固定路徑與不可重用的舊 one-scroll ledger 互斥，G13／G16 循環封閉）。證據等級 `SOURCE_STATIC_PROOF_NOT_LIVE_TRIGGERED`，已記於 GitHub Issue #27，**本輪未觸發**，不得混為本輪的失敗點。
- **本輪（證據精度第 4 輪）實際交付**：修正 3 個公開證據索引缺陷——①呼叫集／計數三者不一致（報告 §2 記 6 組、公開 JSON 索引 5 筆、私有證據實有 7 組 #10–#16）已三方對齊為 7 組；②gate 清單補上「非窮舉」標示並明列 4 個未列入的靜態 gate；③跨檔補上字面 `ledger_collision_status`。另外明文落地外部 Chief 要求 6（`eligible_candidates` 只是候選清單、**五本候選不等於五次下載同意**、唯一下一輪正式目標只有 A45 與 B78）與執行身分（branch／HEAD、installed closure digest、22/22 與 PR #24 head 位元組相同）。**未動**任何產品程式、grant、ledger、state、private 證據或 Harness。
- **獨立唯讀複核 9/9 PASS**：呼叫集一致、gate 非窮舉且 MD／JSON 行號逐字一致、要求 6 已落地、執行身分已記錄、判定數字逐字未變、私有證據 26 筆 bytes+sha256 索引逐字未變且獨立重算 26/26 相符、隱私掃描 7 類全部 0 命中、產品程式零改動、原始碼行號抽核零偏移。

## 嘗試與學到什麼

本輪證據修正是第 3 輪公開證據經一名**唯讀**稽核者複核後，逐項比對「報告 §2 呼叫表／公開 JSON 索引／私有證據實檔」三者才找出來的。學到的重點是：**證據包本身也會出錯**。前一版報告寫「6 次真實呼叫」、JSON 索引 5 筆、私有證據其實 7 組——三個數字互相打架，若不先修好就送審，外部 Chief 只會看到一份自相矛盾的報告。所以先花一整輪把證據對齊、複核，再交審。

另一個學到的點是：外部 Chief review 錨定在舊 head `5cd7914…`，本分支每推一個 commit 就會再過期一次。因此這輪把錨定敘述改成**不會過期的分支語意**（權威 SHA 改由 PR 說明欄與承載該檔案的 commit body 共同提供），並在報告新增 §1.11 把第 4 輪的修正前／後事實固定下來。

## 卡在哪裡、需要什麼決定

需要兩個明確決定：

- **（A，Owner）GitHub Issue #27 是否升級 `GPT-6.1-SOL X-High`。** 本 Agent 不得自行切換高階模型。升級理由是 task-scoped ledger 路徑碰撞牽涉 grant／ledger／state 三層的授權邊界設計，屬跨層決策；但本輪第一阻塞的根因已定位清楚且有最小修正路徑，**不升級也可以照下列順序推進**。
- **（B，Owner）選定單一 authority 世代並整組重發。** 這是 Implementor 的前置條件，必須由 Owner 決定以 `d5436e1` 世代為準還是以 `22cee2b` 世代為準，然後一次重發 `project-contract.json`、`runtime-binding.json`、`implementation-review.json`、`live-readiness.json`、`owner-decision.json`、`project-grant.json`（closure 須為 22 檔），並建立**新的** task／ledger／grant（`operations` 需涵蓋正式流程實際會呼叫的 14 個，quota 維持 `(2,1,2,2,23)`），**不得重用或重置舊 ledger**。

## 如果下一步失敗會怎樣

若重發後的 authority 仍被 `:437` 擋下，代表還有第四個未察覺的世代漂移點；那時先把新舊兩組 bundle 的逐欄位雜湊差異列成表再判斷，而不是繼續改單一欄位。若 Issue #27 的旋轉方案無法在「不得重用舊 ledger」的約束下被審查通過，則需要 Owner 明確決定放寬該約束（這是授權政策變更，不是實作細節）。無論哪一條，都不會用重送 Save All、跳過仍在生效的 gate、或偽造授權的方式繞過；證據包會保留本輪已驗證的完整鏈路，交回 Planner 與外部 Chief 重新裁決。
