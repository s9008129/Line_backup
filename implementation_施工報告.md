# LINE 相簿命名實作施工報告

> 文件性質：這是 Implementer 的施工與流程檢討報告，不是獨立驗收報告，也不是 LINE 實機 E2E 報告。
> 報告基準：`master` 的 `7dfc30031f80885344f88584298dddfe2b05d692` 之後的群組校正修正候選。
> 生成日期：2026-10-27（Asia/Taipei）。

## 1. 結論摘要

先講結論：這次的「程式修正」本身是必要的，但「流程」確實有過度冗長的部分。兩者不能混在一起判斷。

1. 真正需要修改的是一個可重現的資料完整性問題：群組名稱校正成功事件寫入後，若同組 sibling 相簿的 outcome evidence、照片內容或目錄 inode 在此時漂移，舊流程仍可能把 operation 當成成功回傳。這是 fail-open，不只是理論上的潔癖。
2. 修正很小：在 `_execute_group_correction()` 的成功 append 前後各做一次既有 scope precheck，並增加三個 deterministic regression。這個大小是合理的。
3. 流程冗長的主要根因不是測試框架本身，而是責任邊界衝突：Implementer prompt 把角色限定在實作，但專案 handoff 同時要求實作者「安排未參與實作者獨立驗收」；在沒有 controller／stage packet 的情況下，這個責任被混進同一個 execution loop，造成實作、review、修正、再 review 反覆循環。
4. 使用者的「MUST use more subagents」放大了平行化與額外審查，但它不是獨立驗收條款的來源；獨立驗收條款來自本專案的 `plan.md`／`handoff.md`。
5. 離線測試不是沒有意義，但它們證明的是本機狀態機與檔案資料不變量，不是 LINE UI、popup、Save All 或跨 Session 行為。兩者必須分開回報。

本次候選的實際狀態：

- Targeted regression：3 tests，`OK`，49.308 秒，exit `0`。
- 完整回歸：已啟動，但在使用者明確要求「不要再做測試」後中止；沒有可宣稱的完整 PASS／FAIL。
- 上一版 `7dfc300` 的歷史完整回歸曾是 68 tests、`OK`；那是修正前的候選，不是本次候選的 fresh evidence。
- 未開啟 LINE 相簿、未操作真實照片、未按 Save All；`sensor_verified=false`、`real_line_e2e=NOT_TESTED`。
- 本次沒有執行獨立 acceptance，因此不能宣稱 `TASK_CLOSURE_STATUS=DONE`。

## 2. 授權與角色：文件實際怎麼寫

### 2.1 `04_implement_prompt.md` 的 Implementer 邊界

`04_implement_prompt.md` 第一行是 `# v4.8 Implementer`。第 3、5 行要求使用已核准的 Plan／Handoff 做最小實作與列出的 local checks；第 17 行才提到 reviewer，而且是條件式的：

> 「When the controller reports that the packet is ready and the active host supports native delegation, launch the configured HIGH_REASONING_REVIEWER once...」

這段不是說 Implementer 可以自行把每個 commit 都拿去做一次 review。它依賴 controller 回報 packet ready，且 reviewer 應該在 fresh、read-only context 中只做 bounded review。第 25 行也寫 `Acceptance stays read-only and independent when required`，但仍然是驗收契約，不是叫 Implementer 自己兼任 acceptance。

### 2.2 `03_handoff_prompt.md` 有沒有 review／E2E 意圖

有，但範圍很窄，不能解讀成產品 review 或 E2E 授權。

- 第 1 行標題是 `v4.8 Optional Handoff Reviewer`，本身就表明它是 optional handoff reviewer。
- 第 3 行明確說它在 `workflow_policy.handoff_review_required` 為真時使用；工作是核對 reviewed Plan 與 compiled Handoff 的 paths、checks、evidence owners、authorization summary 是否一致，回傳 discrepancy report 或 PASS，且 **Do not ... run implementation**。
- 第 5 行只允許 read-only helpers，且不能 author artifact。
- 第 7 行要求使用 stage packet 的 validation commands；本專案沒有 controller／stage packet。
- 第 9、11 行要求 format 3 result 與六個狀態欄位。

因此，`03_handoff_prompt.md` 有「review」字樣，但它是 **handoff contract consistency review**，不是程式碼 review，也不是 LINE E2E。它沒有授權任何人打開 LINE、按 Save All、或把離線測試冒充實機結果。

### 2.3 專案 `plan.md`／`handoff.md` 才是獨立驗收要求的來源

這是本次流程變長的核心來源之一。

`docs/line-album-naming/plan.md`：

- 第 7 行：「使用者指定不對本計畫做獨立 review；資料變更風險仍要求實作後的獨立驗收。沒有可用獨立驗收者時如實保留未完成關卡。」
- 第 22 行：「由未參與實作的審查者獨立驗收合併結果；不可用作者自評替代。」
- 第 23 行：實機 LINE 與跨 session 只有在另行授權及有效前景交接時執行；離線測試不得宣稱實機通過。

`docs/line-album-naming/handoff.md`：

- 第 4 行：「完成隔離回歸後安排未參與實作的人或 agent 獨立驗收。」
- 第 13 行：「使用者明確取消本計畫的獨立 review，沒有取消實作後的獨立驗收；實作者不能自評冒充獨立通過。」
- 第 22 行：本 repo 沒有可用的 v4.8 controller、schema 或 stage packet；這是人工交接，不要自行建立替代框架或偽造結果。
- 第 40 行：獨立驗收者不得參與計畫以後的實作；若不可用，記 `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`、`TASK_CLOSURE_STATUS=BLOCKED`。
- 第 44 行：handoff 不是 LINE GUI、Save All 或真實備份授權。

所以，本次若只依 `04_implement_prompt.md`，我應該在做完實作、local checks 與必要的 bounded repair 後停在 handoff-ready。專案文件卻把「安排獨立驗收」寫成 handoff 指令的一部分；在沒有 controller 的情況下，實作者很容易把這個指令自行執行，造成角色越界。

## 3. 第一原理：這個功能真正要防什麼

先把問題拆成不可混淆的四層：

| 層次 | 真正風險 | 目前可用的證據 | 不能證明什麼 |
|---|---|---|---|
| 資料交易 | 改名、投影或 append 後遺失／覆寫照片 | 合成 fixture 的 rename、manifest、SHA-256、append-only 測試 | 真實 Finder／外部 writer 的完整原子性 |
| 狀態正確性 | sibling 漂移後仍被投影成 `COMPLETED` | 三條 append-time drift regression、status precheck | LINE 畫面真的顯示成功 |
| 恢復性 | 中斷後重送 Save All、重下載或錯接 | journal、temp path、pending plan、resume 測試 | 真實 popup／chooser／跨 Session UI |
| LINE 整合 | selector、OCR、相簿辨識、下載流程 | 目前沒有實機 GUI 證據 | 需要另行授權的真實 E2E |

核心 invariant 只有三個：

1. 已存在的事實不能被新操作無聲改寫。
2. 觀測到漂移時必須 fail closed，不能把未知結果包裝成成功。
3. 中斷後只能接續唯一可證明的狀態，不能靠重下、重置或新目錄解鎖。

這次修正直接服務第 2 點：若成功事件已寫入，但函式返回前才觀測到 sibling drift，command 必須回報失敗；append-only event 不會被刪除，但這次 operation 不能被宣稱成功。

## 4. 實際循環與每一次的判斷

### 循環 0：初始大實作（`851a406`）

內容：具名分層、名稱正規化、排序、原子不覆寫改名、event projection、correction、resume、CLI、Skill 與手冊。當時完整回歸是 58 tests、`OK`。

性質：這是一個跨資料格式、檔案交易、CLI 與文件的整合功能；需要一定的一體化實作，不能只用一個小 patch 完成。這裡的複雜度來自產品需求，不全是流程過度。

流程問題：把功能一次做成大 slice，會讓 review 一次面對很大的 diff；日後若切成「核心 naming」「correction」「resume／docs」三個可獨立驗證的 slice，review 成本通常更低。但拆太細又會增加跨 slice 的交易耦合，所以不能說切成越小越好。

### 循環 1：outcome evidence 與文件缺口（`02d1025`）

獨立交付審查在 `851a406` 找到：

- 主 prompt 漏掉 outcome 步驟的描述。
- pending correction 的 resume 未重驗 outcome evidence。
- 手冊沒有清楚區分業務拒絕與 argparse 失敗的 exit code。

性質：是真實契約與安全缺口，修正有必要。

責任判斷：這不是 `04_implement_prompt.md` 要求 Implementer 自己反覆做 code review；它是由專案的獨立驗收條款觸發的。正確邊界應該是：Implementer 回報這個缺口，讓另一個 read-only acceptance context 驗證；若 controller 不存在，則 owner／下一個角色安排，而不是 Implementer 在同一個 loop 自行扮演 reviewer。

### 循環 2：album correction 的 sibling drift（`4476d81`）

審查發現 pending album correction 只重驗目標相簿；若同組已完成的 sibling 相簿的 outcome evidence、照片內容或目錄 inode 漂移，仍可能繼續改名。

性質：真實資料完整性問題，且可重現；三條 adversarial tests 有必要。

設計教訓：sibling scope 是一個「群組級」 invariant，不是單一 album 的局部檢查。這時候應該順手檢查 group correction 是否有同類缺口；當時只修 album，留下了下一個循環。

### 循環 3：album 的 mid-operation 漂移（`7dfc300`）

審查找到在第二次 precheck 之後、成功事件寫入之前，sibling 仍可漂移。修正加入 target proof 後、成功 append 前與 append 後的 scope 重驗，並讓 `status_map()` 在不 pending 時重驗 outcome evidence／目錄 inode。

性質：是可重現的 fail-open，不是純理論窗口；修正必要。

設計教訓：append 後重驗是正確模式，但當時沒有把它對稱套用到 group correction。這不是「要多跑幾次 review」可以解決，而是「同一個 invariant 要一次套用到所有 correction kind」。

### 循環 4：本次 group correction append-time drift

本次最小修正位於 `src/line_backup_batch/daily.py:1463-1472`：

1. 移動群組目錄並驗證 children。
2. append 前呼叫 `_precheck_group_plan()`，重驗 attempt outcome evidence、群組成員、child inode 與 content。
3. 寫入 `group-name` `CORRECT` 事件。
4. append 後再呼叫同一 precheck，才 return。

這使 command 在 append 後的 sibling drift 發生時 raise `DailyError`，不會回報成功。append-only 的 correction event 仍保留；本修正不嘗試 rollback、刪除或偽造原子交易，這是符合既有資料模型的。

新增三條測試，都故意在 `append()` 已寫入後、`correct_group_name()` 返回前注入漂移：

- sibling outcome evidence 改寫：預期 `EVIDENCE_DRIFT`。
- sibling 照片內容改寫：預期 `CORRECTION_CONTENT_CHANGED`。
- sibling 目錄換成同內容但新 inode：預期 `CORRECTION_DIRECTORY_CHANGED`。

每條測試都確認 operation 本身失敗、只留一筆 correction event、改名後群組與兩個 child 仍在，且後續 `status_map()` 仍 fail closed。

性質：這是必要的對稱補洞；五行程式修改加三條測試是合理比例。它同時證明前一個循環的問題不是「測試不夠多」，而是「同一個 class 的覆蓋不完整」。

## 5. 哪些是專案規則、哪些是 harness、哪些是我自己加的

| 動作 | 主要來源 | 性質 | 是否有必要 |
|---|---|---|---|
| 只修改授權路徑、保留既有照片與事件 | 專案 `AGENTS.md`／Plan／Handoff | 專案資料安全規則 | 必要 |
| 使用 append-only event、fail closed、不得重下 | 專案資料規則 | 產品 invariant | 必要 |
| 跑完整 `test_daily_records.py` | 專案 handoff 第 39 行、plan 第 21 行 | 指定 local check | 最終候選一次有必要；每次 micro-fix 重跑是流程浪費 |
| 隔離 fixture、ImageIO、SHA-256 驗證 | 專案 handoff／既有程式 | 離線資料驗證 | 必要，但不代表 LINE E2E |
| 實作後獨立 acceptance | 專案 plan 第 22 行、handoff 第 4／40 行 | 專案驗收規則 | 若 handoff 有效，應由獨立角色做一次；不應由 Implementer 自行扮演 |
| 每個 commit 都重新找 reviewer | 我的 orchestration，不是 04 明文 | 流程膨脹 | 過度 |
| 反覆跑 60／63／68 tests | 我的 orchestration；handoff 只要求列出命令與證據 | 流程膨脹 | 過度 |
| 開啟 LINE 做 E2E | 專案 plan 第 23 行、handoff 第 40／44 行 | 需要另行授權與前景交接 | 本次不應做 |
| 用 `03_handoff_prompt` 做 handoff consistency review | 該 prompt 第 1、3 行 | optional、條件式 | 本專案沒有 controller／stage packet，不能假裝已執行正式版本 |
| 使用多個 sub-agent | 使用者本次明示「MUST use more subagents」 | 使用者要求 | 可加速探索，但不應取代角色邊界 |
| 寫 `implementation_施工報告.md` | 使用者後續明示要求 | 本次交付物 | 必要 |

### 5.1 最深層的根因

根因不是「測試太多」這麼單一，而是三件事疊在一起：

1. **角色契約衝突**：Implementer prompt 說做實作；專案 handoff 要求實作後安排獨立驗收。兩份文件沒有指定「誰在什麼時候啟動 reviewer」，于是同一個 agent 把兩個角色塞進同一個 loop。
2. **沒有 controller／stage packet**：`04` 的 reviewer 與 receipt 流程依賴 controller；本專案 handoff 又明確說沒有 controller。沒有 deterministic stage transition，就很容易靠人工／agent 自己補流程。
3. **把「每次修正」誤當成「每次都要重新獨立驗收」**：真正需要的是最終候選的一次獨立 acceptance；中間 commit 可以由 Implementer 做 targeted checks。每次 review 找到新 bug 就重新 full review，會造成 review-fix-review 的長尾。
4. **測試成本沒有分層**：完整 suite 包含大量既有 legacy／migration 測試，單次數分鐘；對小 patch 每次都跑完整 suite，成本遠高於 targeted regression。這不是測試內容錯，而是執行頻率錯。

## 6. 離線測試在沒有打開 LINE 時到底有什麼意義

有意義，但只能在它證明的範圍內解讀。

### 能證明

- 名稱與 identity 分離，不會因中文名稱或 OCR 誤認列表／相簿。
- 原始檔名排序、編號寬度、碰撞與非法名稱處理符合契約。
- completion manifest、檔案大小、SHA-256、mtime／ctime 與 ImageIO 解碼能在合成 fixture 上重驗。
- correction 的 append-only projection、pending 狀態、中斷恢復與 sibling drift 都會 fail closed。
- 同一內容多檔、不同副檔名、目錄換置、symlink 與 foreign content 等 deterministic edge cases。

### 不能證明

- LINE macOS 的實際按鈕、selector、popup、chooser、Save All 時序。
- 實際 OCR 文字是否正確、網路下載是否完整、跨 Session 後 UI 是否回到正確位置。
- 真實外部 writer 與 append-only event store 之間的跨檔案原子性；advisory lock 不是 OS-wide transaction。
- SHA-256／ImageIO 解碼成功等於與 LINE 服務端原始位元完全相同；它只證明本機一致性與可解碼。

因此：

- 對於本次 group correction race，離線測試非常有意義，因為 bug 本身就是狀態機／檔案投影問題。
- 若要回答「LINE 相簿備份在真機是否可用」，必須另做實機 E2E；本次明確沒有授權，所以只能是 `real_line_e2e=NOT_TESTED`。
- 把 68 tests 當成實機 E2E 的替代品是錯的；把 68 tests 全部視為無意義也是錯的。

## 7. 是否過度工程化

### 必要且合理的部分

- 對 append 前後做 scope 重驗，因為這是實際可重現的 fail-open。
- 三條針對不同 drift 類型的 regression，因為 outcome、content、inode 是三種不同 invariant。
- 在最終候選跑一次完整 suite，確認沒有破壞 legacy／migration／naming／correction。
- 若 handoff 有效，安排一次真正獨立、read-only 的 acceptance。
- 若沒有實機授權，明確標記 `NOT_TESTED`，不偽稱 E2E。

### 真正偏重的部分

- 每次小修正後重新啟動 fresh reviewer，並把 review 當成 implement loop 的一部分。
- 每個 micro-fix 都跑一次數分鐘的完整 suite，而不是先跑 targeted regression，最後才跑完整 suite。
- 把「獨立 review」與「獨立 acceptance」混成同一個反覆循環；handoff 其實已說「獨立 review 取消、獨立驗收保留」。
- 在沒有 controller／stage packet 的情況下，讓 Implementer 自行扮演 controller 去調度 review，導致責任邊界失真。
- 讓 subagent 平行探索本身不是問題；問題是沒有把它限制在 read-only analysis／明確 write scope，且沒有把 review 與 edit 的角色分開。

### 結論

「一個名稱改變」不需要多輪 review 才能實作；但這個名稱改變落在一個會改寫檔案路徑、 completion 投影與可恢復交易的系統裡，不能只看成 UI 文案修改。正確做法不是把測試全部砍掉，而是：

> 小 patch 用 targeted tests；最終候選跑一次完整 suite；獨立 acceptance 由另一個角色在最終 commit 做一次；LINE E2E 另行授權。

## 8. 具體建議

### 8.1 立即修正 handoff 的角色設計

建議把 `handoff.md` 改成兩個明確階段：

1. **IMPLEMENTER**：完成程式、targeted tests，回傳 `HANDOFF_READY`、候選 HEAD、變更清單、local evidence。不得自行啟動 reviewer，也不得自行宣稱 acceptance PASS。
2. **ACCEPTANCE**：由 controller／owner 另行啟動 fresh read-only agent；只驗證最終候選，不修改程式；失敗才回報 bounded action，不由 implementer 在同一個 context 連跑多輪。

如果沒有 controller，至少要由 owner 明確指定下一次 acceptance invocation；不要用「實作者自己安排」假裝有獨立性。

### 8.2 把測試分層寫死

- 每次 code slice：只跑受影響的 targeted tests。
- 最終候選：跑一次完整 `test_daily_records.py`。
- 若完整 suite 失敗：只修該 failure 的 root cause；下一次只重跑相關 tests，再由 acceptance 跑一次完整 suite。
- 不在每次 micro-fix 後重跑完整 suite，除非該 fix 改變核心 event schema、檔案格式或全域 projection。

### 8.3 明確區分三種 review

- **Handoff consistency review**：只檢查 Plan／Handoff 路徑與授權一致；對應 `03_handoff_prompt.md`。
- **Independent acceptance**：read-only 驗證最終實作與證據；對應 `04` 的 acceptance，不由 implementer 自評。
- **LINE E2E**：需要真實任務授權、有效前景交接；不是 unit test，也不是 acceptance 自動附帶的項目。

### 8.4 改進 `03_handoff_prompt.md` 的命名或註解

它容易被誤讀成一般 review。建議在標題或第一段直接寫：

> 「本角色只審 handoff contract，不審產品程式碼、不執行 acceptance、不執行 E2E。」

並把 `workflow_policy.handoff_review_required` 與 controller/stage packet 的相依性寫成必要欄位；若沒有 controller，應明確回報 `NOT_APPLICABLE`，不要讓 agent 自行替代。

## 9. 本次變更與證據

### 程式

- `src/line_backup_batch/daily.py:1463-1472`：group correction 在 append 前後重跑 `_precheck_group_plan()`，並保留原 append-only 行為。
- `tests/test_daily_records.py:237-266`：共用的 append-time drift injection helper。
- `tests/test_daily_records.py:1519-1531`：三條 group correction append-time drift regression。

### 實際命令與結果

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py \
  -k group_correction_append_time -v
```

結果：`Ran 3 tests in 49.308s`、`OK`、exit `0`。

```sh
git diff --check
```

結果：exit `0`，無 whitespace error。

完整回歸命令原本已啟動，但收到使用者「不要再做 review 和測試」的直接指示後中止；因此本次不把它列為 PASS。上一版 `7dfc300` 的 68 tests `OK` 只作歷史背景，不能冒充本次候選結果。

### 邊界

- 未開啟 LINE 相簿、未按 Save All、未碰觸真實照片或既有備份。
- `sensor_verified=false`。
- `real_line_e2e=NOT_TESTED`。
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`。
- `TASK_CLOSURE_STATUS=BLOCKED`（直到另行安排的 acceptance 完成）。

## 10. 六狀態（本次 Implementer 視角）

- `PRIMARY_OUTCOME_STATUS=PARTIAL`：小修正已完成；最終完整候選驗證因使用者指示中止。
- `IMPLEMENTATION_STATUS=PASS`：程式與 targeted regression 已完成。
- `CORE_ACCEPTANCE_STATUS=NOT_RUN`：沒有由獨立角色完成 acceptance。
- `REQUIRED_VERIFICATION_STATUS=PARTIAL`：targeted tests PASS；完整 suite 未完成。
- `INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN`。
- `TASK_CLOSURE_STATUS=BLOCKED`：不把 Implementer 自評當成獨立通過。

## 11. 給下一個角色的交接

下一個角色若要完成正式驗收，應在本次 commit 的精確 HEAD 上：

1. 先確認 Git worktree 乾淨、commit message 包含意圖／做了什麼／下一步建議／驗證與結果。
2. 執行一次完整 `test_daily_records.py`，記錄命令、環境、exit code 與 raw log。
3. 以未參與本次實作的 read-only context 檢查本次 diff、三條 regression、append-only 行為與資料安全邊界。
4. 若沒有真實任務授權與有效前景交接，只記 `real_line_e2e=NOT_TESTED`；不要打開 LINE 或按 Save All。
5. 若 acceptance 失敗，回報一個 bounded action；不要讓 implementer 自行把同一 context 當成 reviewer。

這樣才能同時保留資料安全，又避免把「一個小修正」膨脹成多輪自我 review 的長尾流程。
