# 問題提報單：LINE 記事本下載控制的 TOCTOU 與 reveal／dispatch 抽象錯置

> 文件編號：`NOTES-DISPATCH-TOCTOU-RCA-20261119-01`
> 提報日期：2026-11-19（Asia/Taipei）
> Repo：`/Users/hsiaojohnny/dev/Line_backup`
> Branch：`feature/line-notes-media`
> 分析時 HEAD：`e321d7a`（只代表本次唯讀分析的 checkout，不代表事故當時的執行 HEAD）
> 主要來源：`/Users/hsiaojohnny/.codex/sessions/2026/11/17/rollout-2026-11-17T21-38-08-01a1e9ba-afe5-7c31-a052-1800c913800d.jsonl`
> 文件性質：第一性原理分析、證據整理與修復方向；不是下載授權、GUI 操作授權、Acceptance／E2E 或獨立驗收
> 本輪邊界：沒有操作 LINE、沒有下載、沒有建立 intent、沒有修改帳本、照片、影片、程式或 Skill

**隱私與代稱**

本文以 `G`、`Gis` 作為兩個記事本列表的代稱，不重述列表顯示名稱、作者、貼文正文、媒體內容或原始檔名。為了讓後續模型能回到精確證據，保留 `local_list_id`、`attempt_id`、事件序號、觀察 ID 與 SHA-256；不把私人內容放入報告。

**與既有文件的關係**

根目錄既有 `問題提報單.md` 在本文件分析時是工作樹中的 dirty 修改；本文沒有覆寫它。該檔後續已由 `d655025`、`221eabd`、`d23cb52` 等提交更新，本文保留為 2026-11-19 的唯讀分析快照。舊文保留其既有證據與音訊分析；本文只重新排列因果優先級，並把「下載控制何時可用」與「下載何時真正派送」拆成兩個不同問題。

**文件時效與目前狀態**

本文的分析 HEAD 是 `e321d7a`，只代表當時的 checkout，不是事故執行 HEAD，也不代表目前工作樹。文中的 `M 問題提報單.md`、`?? .playwright-mcp/`、`NOT_APPLICABLE` 與其他工作樹／狀態描述都是當時快照；若與目前 Git 狀態或後續報告不同，以當時證據索引與後來保存的實機報告分別判讀，不把本文當成最新現況宣告。2026-11-20 的當次實機阻塞與 B1／CUA 視窗綁定分析見根目錄 `問題提報單.md`。

---

## 0. 執行摘要

### 0.1 最小結論

**本案的直接阻塞不是下載 API 失敗，也不是音訊 MIME 分類失敗；而是下載控制在真正派送前消失。**

更精確地說：

1. G 的兩個 attempt 都已持久化 intent，但在下載控制派送前，同一個 viewer 的下載工具列不再可見；帳本分別記為 `NOT_SENT`。
2. Gis 的 attempt 也出現相同的前後可見性差異；因為缺少足以排除延遲派送的完整證據，帳本記為 `UNKNOWN`。
3. 三個 staging 目錄在本次唯讀核對時都是 0 個 entry；沒有 chooser、沒有檔案、沒有 completion。
4. 目前流程要求「先看到 transient 工具列 → 寫入 intent → 讀回 → 模型／工具回合 → 再觀察 → 點下載」。這是一個典型的 TOCTOU（time-of-check to time-of-use）問題：檢查時可見，使用時未必仍可見。
5. 流程又把兩種本質不同的動作放進同一個一次性 candidate 邊界：
   - **reveal**：移入游標或安全區操作，只是讓工具列出現，可逆、通常不產生下載；
   - **dispatch**：按下下載控制，會產生不可逆副作用，才是真正需要一次限制的動作。
6. 因此目前的 `intent` 同時承擔交易紀錄、下載授權、可能已派送假設與 UI 凍結鎖，語意過載。安全邊界應該從「intent 已寫入」移到「第一個 dispatch-capable input 已開始」。

一句話版本：

> **系統把一次瞬時可見性當成持久交易門票，並把可逆的 reveal 與不可逆的 dispatch 綁進同一個一次性資源；只要工具列壽命短於觀察到派送的時間窗，完全遵守規則的執行也會在派送前失敗。**

### 0.2 三個必須分開的層次

| 層次 | 問題 | 目前證據 | 是否為本次直接原因 |
|---|---|---|---|
| F1：派送前控制鏈 | intent 前後工具列不可見，沒有可歸屬的下載控制 | G 兩次 `NOT_SENT`、Gis `UNKNOWN`、三個空 staging、無 chooser | **是。直接阻塞在此。** |
| F2：交易協議 | 要求 transient 控制跨越 intent、讀回、模型回合後仍存在 | 首次無控制的觀察窗為 40.375～101.901 秒；G 首案到最後無控制觀察約 195.168 秒；同 viewer、同 AX hash、截圖不同 | **是。系統層結構性根因。** |
| F3：抽象邊界 | 把 reveal 與 dispatch 視為同一種 consumable candidate | Skill 要求 intent 前準備延後候選骨架；intent 後才允許極窄的一次重現 | **是。設計層根因。** |
| F4：完成分類 | 若未來取得音訊 bytes，現行模型只承認 `PHOTO`／`VIDEO` | 合成 WAV／MP3／M4A 會被 `UNSUPPORTED_MEDIA_MIME` 拒絕 | **不是本次原因。** 本次尚未產生檔案。 |
| F5：驗證 | 文件修正、離線測試與真實 GUI 成功率不是同一件事 | `e321d7a` 明確標示 GUI、音訊、chooser、跨 Session 均 `NOT_RUN` | **是覆蓋缺口，不是下載因果。** |

### 0.3 六項狀態

| 狀態欄位 | 值 | 範圍 |
|---|---|---|
| `PRIMARY_OUTCOME_STATUS` | `BLOCKED` | 沒有成功下載、沒有 completion；G／Gis 的未解狀態保留。 |
| `IMPLEMENTATION_STATUS` | `NOT_APPLICABLE` | 本輪只做唯讀分析，沒有修改產品程式或 Skill。前次 `e321d7a` 的文件變更不在本輪重新實作。 |
| `CORE_ACCEPTANCE_STATUS` | `NOT_RUN` | 沒有使用正式日常 Prompt 完成一次真實備份。 |
| `REQUIRED_VERIFICATION_STATUS` | `NOT_RUN` | 沒有真實 GUI 驗證、沒有 chooser、沒有 `download-check` 或 completion。 |
| `INDEPENDENT_ACCEPTANCE_STATUS` | `NOT_RUN` | 沒有獨立 Reviewer／E2E 對本次修復方向作接受。 |
| `TASK_CLOSURE_STATUS` | `BLOCKED` | 根因方向已收斂到協議層，但尚未經實機區辨實驗與實作驗證。 |

本輪完成的只是「唯讀證據核對」與「分析」。它不是 `CORE_ACCEPTANCE`，也不是 `REQUIRED_VERIFICATION` 的替代品。

---

## 1. 證據邊界與可相信的範圍

### 1.1 Session 可讀性

使用者提供的 JSONL 已確認可讀、可解析：

| 項目 | 數值 |
|---|---|
| 路徑 | `/Users/hsiaojohnny/.codex/sessions/2026/11/17/rollout-2026-11-17T21-38-08-01a1e9ba-afe5-7c31-a052-1800c913800d.jsonl` |
| 大小 | `3,786,894` bytes |
| 行數 | `1,023` |
| SHA-256 | `9f2d7765518593c79e16413c4a6f8485bf71dc45205e936adc4b31db1c131af8` |
| 事件統計 | `event_msg` 454、`response_item` 427、`token_usage_record` 129、`world_state` 6、`turn_context` 3、`inter_agent_communication_metadata` 3、`session_meta` 1 |

這證明檔案不是空的、不是無法開啟的損壞檔，且本次分析能讀到其中的事件、工具輸出與紀錄。它不證明事故當時的 checkout HEAD，也不把 session 顯示冒充 provider 或 OS 證據。

### 1.2 帳本事實

本次直接核對的持久事件如下。事件序號、attempt ID 與 outcome 均取自帳本事件檔，不從對話推測。

| 列表 | 事件 | 類型 | Attempt ID | 結果 |
|---|---|---|---|---|
| G | `00000014.json` | intent | `8d3298205f724a7eba1e1fdbc9f889d8` | 尚未有 outcome |
| G | `00000015.json` | outcome | 同上 | `NOT_SENT` |
| G | `00000016.json` | intent（recovery） | `ff29966a2af9444f90d8213b31cc057f` | 尚未有 outcome |
| G | `00000017.json` | outcome | 同上 | `NOT_SENT` |
| Gis | `00000024.json` | intent | `e115c839f7b348dd993223eac0dcd8f3` | 尚未有 outcome |
| Gis | `00000025.json` | outcome | 同上 | `UNKNOWN` |

G 的帳本路徑是 `notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/`；Gis 的是 `notes-backup-records/1bed1cdc-4cde-47d1-a718-088eb2d38de3/`。本文不重述完整目的地或顯示名稱，只保留 staging 的短識別碼。

三個 staging 目錄在本次核對時都是空目錄：

| 代稱 | staging 尾碼 | entry 數 |
|---|---|---|
| G 第一次 | `.line-notes-incoming-c0e1bd2739f24519997e6b2b0e0f50b4` | `0` |
| G recovery | `.line-notes-incoming-1707f3d2589045f686a5e633bfba1ce6` | `0` |
| Gis | `.line-notes-incoming-73bc32664ec8421983ecd0ae5dce4ed7` | `0` |

本次沒有找到 chooser、下載檔案或 completion。**空 staging 不能單獨證明從未派送**；它只能證明在讀取當下沒有檔案。G 的 `NOT_SENT` 來自既有私有 receipt 稽核與帳本事實；Gis 的 `UNKNOWN` 則是因為缺少足以排除延遲派送的證據。兩者不可合併。

### 1.3 觀察與截圖

| 觀察 | UTC 時間 | 可見性結論 | 截圖 SHA-256（短） | AX SHA-256（短） |
|---|---|---|---|---|
| G `obs-G-reveal-after-01` | `2026-11-17T04:38:06.020Z` | 工具列可見 | `4113adc8…` | `33d55bea…` |
| G `obs-G-download-pre-01` | `2026-11-17T04:39:10.064Z` | 工具列不可見 | `18023418…` | `33d55bea…` |
| G `obs-G-post-intent-nocontrol-01` | `2026-11-17T04:41:21.188Z` | 工具列不可見 | `f78f773d…` | `33d55bea…` |
| G `obs-G-reveal-after-02` | `2026-11-17T04:43:22.320Z` | 工具列可見 | `ae6dc8d1…` | `33d55bea…` |
| G `obs-G-download-after-recovery-intent-03` | `2026-11-17T04:45:04.221Z` | 工具列不可見 | `d4dbdf10…` | `33d55bea…` |
| Gis pre-intent reveal | `2026-11-17T15:17:47.853Z` | 工具列可見 | `52e0ed31…` | `f27c5fd6…` |
| Gis post-intent gate | `2026-11-17T15:18:28.228Z` | 工具列不可見 | `b6c91141…` | `f27c5fd6…` |

最重要的不是「AX 有沒有列 toolbar」，而是：**G 的五個觀察共用同一個 AX hash；Gis 的前後兩個觀察也共用同一個 AX hash，但截圖明顯不同。** 這表示 toolbar 的出現／消失沒有可靠地反映在 AX 樹中。AX 缺少節點不能單獨證明 toolbar 不存在；截圖有 toolbar 也不能替 AX 補成節點。兩者是不同證據層。

### 1.4 不能由現有證據推出的東西

- 不能證明工具列消失的精確觸發是 hover timeout、焦點變化、重繪、fullscreen 過場或 CUA capture race 中的哪一個。
- 不能證明 LINE 完全沒有做任何內部動作；G 的 `NOT_SENT` 是既有帳本與 receipt 的結論，不是 OS event trace。
- 不能證明事故當時執行的是哪一個 commit；G／Gis 都沒有持久保存當次 checkout HEAD。
- 不能把音訊分類器的拒絕當成這次控制消失的原因，因為本次根本沒有檔案、沒有 chooser、沒有 `download-check`。
- 不能把空 staging 當成「沒有延遲派送」的普遍證明。

---

## 2. 第一性原理：成功下載到底需要什麼？

### 2.1 能力鏈

把「媒體成功保存」拆成不可跳過的能力鏈：

| 步驟 | 必要條件 | 本次狀態 |
|---|---|---|
| S0 身分 | 列表、貼文、媒體三層身分可唯一核對 | 有帳本與觀察證據；本輪未重新操作 LINE |
| S1 覆蓋 | 指定列表完整卡片覆蓋；目標貼文細盤完整 | 既有任務有覆蓋紀錄；本輪不重跑 |
| S2 穩定 viewer | 同一 viewer、同一媒體、有效前景，且沒有播放／導覽漂移 | 多數觀察支持同一 viewer；精確前景連續性仍以既有原件為限 |
| S3 安全 reveal 方法 | 有當次工具支持、可歸屬的安全 hover 或 selected-thumbnail 非播放邊緣操作 | Skill 有方法；本次未執行 |
| S4 intent 持久化 | 先保存並讀回 intent、attempt、空白 staging、禁止重送紀錄 | G／Gis 都成立 |
| S5 派送時控制可見 | **在 click 的當下**，控制可見、啟用、可歸屬、可映射 | **不成立或未證實** |
| S6 單次 dispatch | 受支持的 helper 只送出一次下載控制輸入 | G 沒有 receipt；Gis 不足以排除延遲 |
| S7 chooser | chooser 可歸屬同一 attempt，目的地等於空白 staging，最終確認一次 | 未觀察到 |
| S8 檔案落盤 | staging 出現非空、穩定、唯一 regular file | 三個 staging 均為空 |
| S9 分類與 completion | magic MIME／suffix 分類、SHA-256、防覆寫、completion | 未到達 |
| S10 本機可用性 | 後續檔案存在與身分核對 | `NOT_APPLICABLE` |

關鍵是 **S5 不是 S2 或 S4 的同義詞**。S4 是一次交易授權；S5 是某個瞬間的執行條件。把 S5 放進 S4 的前置條件，等於要求一個瞬時狀態跨越整個持久交易。

### 2.2 持久前置條件 vs 瞬時執行條件

安全前置條件應該盡量是「不因時間經過而失效」的性質，例如：

- 目標列表／貼文／媒體身分；
- 空白 staging 的 inode／device／canonical path；
- 沒有 chooser、沒有未解 outcome、沒有活動下載；
- 已知且可重複的安全 reveal 方法；
- 有效前景交接。

相反地，下列性質是瞬時的：

- 工具列現在是否可見；
- 某個 pixel 區域現在是否仍是下載圖示；
- 滑鼠是否還在觸發 hover 的位置；
- viewer chrome 是否正在顯示。

把瞬時性質當成持久門票，會產生兩個壞結果：

1. **太早檢查**：intent 還來不及寫完，工具列已消失。
2. **太晚使用**：即使 intent 成功，click 時 control 已不存在，或位置／歸屬已漂移。

### 2.3 TOCTOU 形式化

令：

- `V(t)`：工具列在時間 `t` 可見且可歸屬；
- `t_o`：觀察到 `V(t_o)=true` 的時間；
- `t_c`：真正送出下載 click 的時間；
- `L`：工具列從 `t_o` 起能維持可見的壽命（未知）；
- `G = t_c - t_o`：從 check 到 use 的總延遲，包含 intent CLI、讀回、模型回合、證據保存與再觀察。

安全點擊要求：

```text
V(t_o) = true  且  t_c - t_o < L
```

但目前流程只能保證第一項。若 `G >= L`，就會出現：

```text
觀察時：V(t_o) = true
使用時：V(t_c) = false
```

這不是 Agent 大意，而是協議允許的時序造成的。即使 Agent 完全遵守 Skill，只要 `G >= L`，仍會在下載前失敗。

本次觀察到的 `t1 - t0` 上界如下。注意：這不是精確的 `L`，只是「至少在這段時間內已經看不到」的觀察上界。

| 案例 | 可見觀察 | 無控制觀察 | 時間差 | 可證明的上限 |
|---|---|---|---|---|
| G 第一次 | `04:38:06.020Z` | `04:39:10.064Z` | `64.044s` | 工具列壽命 `< 64.044s` 或觀察／擷取另有問題 |
| G recovery | `04:43:22.320Z` | `04:45:04.221Z` | `101.901s` | 工具列壽命 `< 101.901s` |
| Gis | `15:17:47.853Z` | `15:18:28.228Z` | `40.375s` | 工具列壽命 `< 40.375s` |

帳本檔案的 mtime 只能作粗略定位，不是正式事件時鐘。以 mtime 粗略估計，G recovery 的 intent 約在可見觀察後 `69.362s` 完成；Gis 約在 `16.886s` 後完成。這不改變上面的 observation 上界，也不應被寫成精確的 LINE 內部時間。

### 2.4 為什麼「再多等一下」或「固定 sleep」不是解法

固定 sleep 只會增加 `G`，不會保證 `V(t_c)`。它還可能讓畫面進入下一個狀態，造成：

- 控制消失後點到錯誤區域；
- viewer chrome 重新出現但幾何位置已變；
- 同一個 viewer 的其他控制被誤認為下載控制；
- 逾時後無法區分「沒派送」與「已派送但延遲」。

真正需要的是**在 click 前重新取得新鮮證據，並把 click 緊接在該證據之後**，而不是把舊觀察往後拖。

---

## 3. 抽象錯置：reveal、dispatch、chooser 不是同一種資源

### 3.1 三個動作的性質

| 動作 | 是否可逆 | 是否可能產生檔案 | 是否應消耗「下載一次」額度 | 正確的保護方式 |
|---|---|---|---|---|
| Reveal（hover／安全區操作） | 通常可逆 | 通常不會 | **不應消耗 dispatch 額度** | 有界、可重現、限制次數、每次重新核對身分與幾何 |
| Dispatch（下載控制 click） | 不可逆 | 是 | **是，最多一次** | intent 後、fresh after、立即 click、保存 receipt |
| Chooser 確認 | 不可逆 | 是（目的地與檔名） | 是，最終確認一次 | 驗證 chooser 歸屬、完整 staging 路徑、只確認一次 |

目前把 reveal 與 dispatch 都放進「candidate」與同一個 intent 邊界，導致：

- 為了避免第二個下載，連「讓工具列重新出現」也被視為第二個下載；
- 一旦 intent 寫入，流程就不能再做安全的 bounded reveal，除非事前已準備一個很窄的候選 2 骨架；
- Agent 被迫在第一眼看到工具列時就預測「之後可能會消失」，但這不是可靠的可觀察事實。

這是範疇錯誤：**一次性保護應該綁在不可逆副作用，不是綁在可逆的顯示操作。**

### 3.2 現行 B1 的窄例外

目前 Skill 允許 intent 後重新顯示一次，但要求 intent 前先保存候選 2 骨架，且必須有：

- 同一三層身分；
- 同 scope／viewer／有效前景連續；
- 候選 1 的 request／raw／after 完整讀回；
- 仍有第二候選額度；
- 已知安全方法、作用區與 mapping。

這個例外在安全上很保守，但其代價是：

- 把「預測工具列會消失」變成必要條件；
- 增加 intent 前的 CLI／證據工作，反而拉長 `G`；
- 若 Agent 沒有預測，事後就不能安全補做 reveal；
- 即使預測正確，實作仍要跨多個工具回合，`G` 依然可能大於 `L`。

`e321d7a` 把「若預計可能使用」改成客觀條件，是正確的文件修正，但它仍然保留這個基本結構，沒有把 reveal 與 dispatch 真正拆開。

### 3.3 intent 的語意過載

目前 `intent` 同時被當成：

| 角色 | 目前效果 | 問題 |
|---|---|---|
| 交易紀錄 | 保存 attempt、staging、身分 | 合理 |
| 下載授權 | 允許一次下載 | 合理 |
| 「可能已派送」假設 | 沒有 outcome 前不得再送 | 安全，但太早 |
| UI 凍結鎖 | intent 後禁止一般 reveal／導覽 | 把可逆動作也鎖住 |
| 重送防護 | 阻止以新目錄、零計數解鎖 | 必要 |

更精確的狀態應該是：

```text
ATTEMPT_OPEN（intent 已持久化，尚未 dispatch）
  -> REVEALED（安全 reveal 後，工具列可見）
  -> DISPATCH_STARTED（第一個 dispatch-capable input 已送出）
  -> CHOOSER_OBSERVED
  -> OUTCOME_RECORDED
```

真正的 freeze 點是 `DISPATCH_STARTED`，不是 `ATTEMPT_OPEN`。這樣才能同時保留：

- intent 先於任何可能的下載；
- 一次 dispatch；
- 一次 chooser 確認；
- bounded reveal 的恢復能力；
- 不因缺證據而誤記 `NOT_SENT`。

注意：上述是設計方向，**不是現有 schema 已支援的欄位，也不是本輪已實作的變更**。

---

## 4. 時間線與證據判讀

### 4.1 G 第一次 attempt

- `04:38:06.020Z`：`obs-G-reveal-after-01`，工具列與下載圖示可見。
- 之後 intent `8d3298205f724a7eba1e1fdbc9f889d8` 持久化。
- `04:39:10.064Z`：`obs-G-download-pre-01`，同 viewer，工具列不可見。
- `04:41:21.188Z`：`obs-G-post-intent-nocontrol-01`，仍無工具列。
- 帳本 outcome：`NOT_SENT`。

可支持的結論：工具列在可見觀察後 `64.044s` 內已經不可見；本次沒有下載控制 receipt。不能支持的結論：精確 timeout 是 64 秒，或 LINE 一定沒有做任何內部動作。

### 4.2 G recovery

- `04:43:22.320Z`：`obs-G-reveal-after-02`，工具列可見。
- 約 `04:44:31Z`：recovery intent `ff29966a2af9444f90d8213b31cc057f` 持久化（mtime 僅供粗略定位）。
- `04:45:04.221Z`：`obs-G-download-after-recovery-intent-03`，工具列不可見。
- 帳本 outcome：`NOT_SENT`。

可支持的結論：即使重新進入 recovery，仍在可見觀察後 `101.901s` 內失去控制；recovery 沒有自動解決時間窗。不能支持的結論：recovery 本身造成控制消失。

### 4.3 Gis

- `15:17:47.853Z`：pre-intent reveal，工具列可見。
- 約 `15:18:04Z`：intent `e115c839f7b348dd993223eac0dcd8f3` 持久化。
- `15:18:28.228Z`：post-intent gate，工具列不可見。
- 帳本 outcome：`UNKNOWN`。

Gis 的 stop reason 明寫：intent 後 toolbar 消失，且 intent 前沒有保存第二候選 request 骨架；窄例外不可用。因為沒有足夠 receipt 排除延遲派送，第一個 outcome 是 `UNKNOWN`，不是 `NOT_SENT`。

### 4.4 三個案例共同說明什麼

三者都支持同一個結構性命題：

> **「先看到 toolbar，再完成一個持久交易，再期待 toolbar 還在」不是可靠協議。**

三者都不足以單獨判定 LINE 為什麼隱藏 toolbar。這個「為什麼」仍是 `UNKNOWN`，但即使不知道原因，協議也已經可被判為不穩健，因為它沒有容錯能力。

---

## 5. 根因候選與反證

| 候選 | 支持證據 | 反證／限制 | 判定 |
|---|---|---|---|
| C1：TOCTOU／交易順序 | 多次可見→不可見；intent、讀回、模型回合都在中間；G／Gis 不同 Session 重現 | 沒有精確 `L` 量測 | **已足以判定為系統層根因。** |
| C2：toolbar 是 transient hover／idle UI | 同一 viewer 保持，截圖 chrome 與工具列消失；AX 不變 | 沒有事件 log 證明是 timeout | **高度合理，但精確觸發未知。** |
| C3：焦點／前景／重繪／fullscreen 過場 | 可見截圖有視窗 chrome，不可見截圖只剩 viewer 內容 | 沒有逐事件焦點或 window state 證據 | **可能，未證實。** |
| C4：CUA capture race | 截圖與 AX 非原子；AX 不变 | 在多個 Session 重現；Gis 40 秒後仍不可見，單一 capture race 較難解釋全部 | **不能排除，但不是唯一解釋。** |
| C5：Agent 沒有預測 toolbar 消失／沒有準備骨架 | Gis stop reason 明寫未準備；`e321d7a` 修正可重複性 | G 也失敗；即使準備了骨架，`G` 仍可能大於 `L` | **次要不變量，不是完整根因。** |
| C6：音訊 MIME 分類缺口 | 合成音訊會被拒絕；模型只有 `PHOTO`／`VIDEO` | 本次沒有檔案、沒有 chooser、沒有 `download-check` | **下游、條件式，不是第一因。** |
| C7：下載 API／chooser 失敗 | 無 | 本次沒有觀察到 chooser 或 API 回應 | **不成立。** |
| C8：重複派送 | G 沒有 receipt；Gis `UNKNOWN` 不能排除延遲 | 沒有成功檔案；沒有 completion | **不能說已重複，也不能說一定沒有。** 保持 fail-closed。 |
| C9：身分／列表錯誤 | 帳本有 key、viewer 有觀察 | 本輪沒有重新操作 LINE 驗證 | **沒有支持證據。** |

### 5.1 已證實 vs 未證實的根因層級

**已證實：協議層缺陷。** 現行順序要求瞬時 UI 狀態跨越多個持久化與模型回合；一旦超過壽命，合法執行仍會阻塞。這個缺陷不依賴 LINE 內部實作細節。

**未證實：LINE 內部消失機制。** 可能是 idle timeout、hover 狀態、焦點、重繪或 CUA capture；目前沒有足以排序的事件證據。

這個區分很重要：我們不需要先知道 LINE 為什麼隱藏 toolbar，才能判定「把 toolbar 當成持久門票」是錯的。

---

## 6. `e321d7a` 的準確定位

### 6.1 它做了什麼

`e321d7a` 的 commit message 與 `docs/plans/20261118-notes-deferred-preparation/report.md` 顯示：

- 只修改四份 Skill Markdown；
- 把「若預計可能使用」改成依客觀條件準備延後候選骨架；
- 要求候選 1 的 request／raw／after 完整讀回、同 scope／viewer／有效前景連續、仍有第二候選額度、安全方法與 mapping 有證據時，intent 前保存並讀回骨架；
- 沒有改 helper／composition 執行碼、`src`、`tests`、CLI、schema、帳本或日常 Prompt；
- 明確承認 `PRIMARY_OUTCOME_STATUS=BLOCKED`、`CORE_ACCEPTANCE_STATUS=NOT_RUN`；
- 真實 GUI、音訊、chooser、跨 Session 恢復均 `NOT_RUN`。

### 6.2 它修正了什麼

它修正了一個真實的指示缺口：Agent 不應被迫預測 transient 狀態，才決定是否準備候選 2。這是可重複性與文件一致性的改善。

### 6.3 它沒有修正什麼

它沒有：

- 改變「先看到 toolbar，再 intent，再重新觀察，再 click」的基本順序；
- 消除從觀察到派送的時間窗；
- 把 reveal 與 dispatch 拆成不同狀態；
- 把 freeze 點從 intent 移到 dispatch；
- 提供一個不需事前骨架的 bounded post-intent reveal；
- 以真實 GUI 證明成功率提升。

更進一步說，若客觀準備要求在 intent 前增加額外的保存／讀回工作，它可能**增加** `G`，使某些原本勉強可用的時序更容易超過 `L`。這不是說補丁有害；而是說它解的是指示缺口，不是時序根因。

**結論：`e321d7a` 是有效的文件補丁，但不是本案的 root-cause fix。**

---

## 7. 修復原則與建議序列

以下都是設計建議，尚未實作；任何 schema、CLI、Skill 或 GUI 流程變更都需要 Owner 另案授權。

### 7.1 首選方向：intent 先行，reveal 後行，dispatch 緊接 fresh after

建議把順序改成：

```text
P0  preflight（持久前置）
    - 三層身分、viewer 穩定、前景有效
    - 已知安全 reveal 方法
    - 空白 staging、無 chooser、無未解 attempt
    - 尚有一次 dispatch 額度

P1  persist intent + read back
    - 標記 attempt OPEN、dispatch_started=false
    - 保存 empty staging 的 identity

P2  bounded reveal（最多一次）
    - 只使用已證明的安全 hover／非播放邊緣操作
    - 保存 request／raw
    - 立即取得 after screenshot／AX

P3  if toolbar absent
    - 依證據記 NOT_SENT／UNKNOWN
    - 關閉此 attempt；不建立新 intent 解鎖

P4  if toolbar visible
    - 用最新 after 重新核對 viewer、身分、前景、幾何、歸屬、enabled
    - 不在 after 與 click 之間插入額外 CLI、長篇推理或證據整理

P5  immediate dispatch
    - 透過既有 grounded helper 只送出一次 click
    - 保存 input receipt；標記 dispatch_started

P6  chooser
    - 確認 chooser 屬於本 attempt
    - 精確核對完整 staging 路徑
    - 最終確認最多一次

P7  outcome / download-check / completion
```

這個序列的關鍵不是「先 intent 就比較快」，而是：

- intent 先建立，確保沒有「先按了下載才補紀錄」；
- reveal 是可逆的準備，不消耗 dispatch 額度；
- dispatch 前仍有 fresh after；
- click 緊貼 fresh after，最小化 TOCTOU；
- 真正 freeze 發生在 `dispatch_started`，不是 intent 本身。

### 7.2 替代方向：保留 intent 為授權，但拆出獨立狀態機

如果不改順序，至少要明确拆成：

```text
ATTEMPT_OPEN
  -> REVEAL_ALLOWED（有界、一次）
  -> CONTROL_GROUNDED
  -> DISPATCH_STARTED
  -> CHOOSER_CONFIRMED
  -> OUTCOME
```

並定義：

- `ATTEMPT_OPEN` 不代表已派送；
- `REVEAL_ALLOWED` 不是第二個下載候選；
- `DISPATCH_STARTED` 才是不可逆邊界；
- `UNKNOWN` 只在有足夠不確定性時使用，不因空 staging 自動降級為 `NOT_SENT`。

這需要 schema／事件語意或至少 evidence 狀態的變更，不能只改幾句 Markdown 就宣稱完成。

### 7.3 observation lease／fresh-after adjacency

可以考慮為每個 after 觀察加上「可用於 action 的新鮮度」概念，但不要發明沒有量測根據的固定秒數。較安全的原則是：

- click 只能使用**最近一次** after；
- after 與 click 之間不得有另一個模型回合、CLI 寫入或無關工具呼叫；
- 若期間發生前景變化、viewer 身分變化、幾何變化或 toolbar 消失，重新開始；
- 任何超過已量測安全窗的觀察都只能作歷史證據，不能作 click 依據。

這比較像「相鄰性」而不是任意 TTL。若未來要定 TTL，必須用 E1／E3 實測，不可直接寫死。

### 7.4 不建議的修法

- **不要加固定 sleep。** 它增加 `G`，不是降低 TOCTOU。
- **不要點下載圖示來叫出工具列。** 這可能直接派送，破壞一次限制。
- **不要用 AX 缺少節點證明 toolbar 不存在。** 本次 AX hash 在可見與不可見時相同。
- **不要用空 staging 證明 `NOT_SENT`。** Gis 的 `UNKNOWN` 正是反例。
- **不要放寬兩次候選上限來繞過。** 這會增加重送風險，且沒有解決時間窗。
- **不要把音訊分類塞進這次修復。** 音訊是下游、條件式範圍問題。
- **不要用相簿的 Save All、選單或座標作 fallback。** 記事本與相簿是不同產品流程。

---

## 8. 最小區辨實驗（全部 `NOT_RUN`）

下列實驗都需要 Owner 明確授權、有效前景交接與安全的測試媒體；本輪沒有執行，不能把它們寫成 PASS。

### E1：toolbar 存活時間

**問題：** 在不移入游標、不點擊、不開 chooser 的條件下，reveal 後 toolbar 能維持多久？

**方法：** 對同一個已核對 viewer，做一次安全 reveal，之後以固定間隔截圖但不點下載；記錄第一次不可見的時間。重複數次，區分 hover／idle／焦點／重繪假說。

**可推翻什麼：** 若多次都遠長於模型回合，則 TOCTOU 可能不是唯一瓶頸；若很快消失，則支持 C1／C2。

**狀態：** `NOT_RUN`。

### E2：intent 後 bounded reveal 是否安全可重現

**問題：** 在 intent 已持久化、`dispatch_started=false` 的前提下，安全 reveal 能否讓 toolbar 重新出現，且不產生檔案／chooser？

**方法：** 只在 Owner 授權的測試 attempt 中，先 intent，再一次安全 reveal，保存 request／raw／after；不點下載。檢查 staging、chooser、receipt。

**限制：** 這會建立一個未完成 attempt，必須有明確的關閉與 `NOT_SENT`／`UNKNOWN` 規則；不能拿來解鎖舊 UNKNOWN。若無法安全關閉，不應執行。

**狀態：** `NOT_RUN`。

### E3：fresh after 到 click 的延遲

**問題：** 成功派送的案例中，最後一個 after 到 click request 的時間差是多少？失敗案例是否顯著較長？

**方法：** 在已授權的單次下載 attempt 中，量測 after 捕獲時間、helper request 時間、click 回傳時間與 chooser 時間；不以檔案 mtime 冒充事件時間。

**可推翻什麼：** 若成功與失敗的 `G` 沒有差異，則需重新評估 C3／C4；若 `G` 是主要差異，支持 TOCTOU。

**狀態：** `NOT_RUN`。

### E4：音訊 chooser（僅在 Owner 擴大產品範圍時）

**問題：** 若未來真的要支援音訊，LINE chooser 是否提供可分類的音訊檔？現行 `download-check` 的 MIME／suffix 規則是否足夠？

**方法：** 只用合成測試或 Owner 明確指定的測試素材，不碰私人媒體；先做離線 classifier 測試，再做受控 chooser。

**狀態：** `NOT_RUN`；且不應與 F1 混為一案。

---

## 9. 建議的工程變更邊界

若 Owner 決定修復，建議把變更限制在：

1. **Skill 流程語意**：把 intent 定義為 attempt 授權，而不是立即 freeze；把 reveal 與 dispatch 分開描述。
2. **B1 狀態**：允許 intent 後一次 bounded reveal，不再要求事前預測式骨架；或保留骨架但改成純客觀、低延遲的準備。
3. **Evidence 欄位**：記錄 `attempt_open`、`dispatch_started`、`reveal_count`、最後 after 與 click 的時間關係；不得用手寫事件繞過 CLI。
4. **Helper／CLI**：只有現有 schema 無法表達 `dispatch_started` 時才做最小擴充；不可用新目錄、零計數或改寫舊 UNKNOWN 解鎖。
5. **測試**：新增合成狀態機測試，覆蓋「intent 後 reveal 成功／失敗」「toolbar 消失」「after 過期」「dispatch 只一次」「chooser 路徑錯誤」。
6. **實機驗證**：另以正式日常 Prompt 與 Owner 交接完成；離線測試與文件審查不能代替。

任何架構、schema、對外行為或資料邊界變更，都應先提出有界計畫並取得 Owner 同意；本報告不構成實作授權。

---

## 10. 事實、推論與未知

### 10.1 事實

- Session 檔可讀、可解析，大小與 SHA-256 已核對。
- G 有兩個 intent、兩個 `NOT_SENT` outcome。
- Gis 有一個 intent、一個 `UNKNOWN` outcome。
- 三個 staging 目錄在讀取時都是空的。
- 沒有觀察到 chooser、下載檔案或 completion。
- G 的可見／不可見截圖共用同一 AX hash；Gis 亦然。
- Gis 的 stop reason 明寫 intent 後 toolbar 消失，且 intent 前未保存第二候選骨架。
- `e321d7a` 只改文件，沒有改執行碼；其報告明示真實 GUI `NOT_RUN`。

### 10.2 推論

- 高度可信：目前協議假設 transient toolbar 可跨越 intent、讀回與模型回合，但實際不一定成立。
- 高度可信：reveal 與 dispatch 被錯誤地放進同一個一次性 candidate 邊界，造成不必要的凍結。
- 中度可信：工具列是 transient hover／idle UI，或受焦點／重繪影響；精確觸發未證實。
- 中度可信：`e321d7a` 改善了指示缺口，但因增加 intent 前準備，未必改善甚至可能加重時間窗。
- 低度可信：單一 CUA capture race 足以解釋全部案例；多次不同時間的觀察使其較不充分。

### 10.3 未知

- toolbar 消失的精確觸發與可重現壽命。
- 事故當時實際執行的 HEAD。
- G 的 `NOT_SENT` 是否能完全排除延遲 app action；帳本已保存此結果，但 receipt 不是 OS trace。
- Gis 是否有未觀察到的延遲派送；因此必須保留 `UNKNOWN`。
- intent 後 bounded reveal 的實際成功率。
- 音訊是否在產品範圍內；即使納入，也不是本次 F1 的原因。

---

## 11. 與舊提報單及 commit 的校準

### 11.1 舊 `問題提報單.md`

舊文目前在工作樹中是 dirty 修改，本文沒有覆寫。舊文提供了音訊 classifier、下載 API、chooser 與多個歷史嘗試的重要背景；其較新的內容也已指出「直接失敗點在派送之前」。

本文的校準是：

- 保留舊文的音訊下游分析；
- 不把音訊當成第一因；
- 把 TOCTOU 與 reveal／dispatch 抽象錯置提升為系統層主軸；
- 不重述私人貼文、作者或列表名稱。

### 11.2 `e321d7a`

- 它是有效的文件補丁；
- 它修正「Agent 必須預測 toolbar 會消失」的指示缺口；
- 它不是 GUI 根因修復，也不是下載成功修復；
- 它沒有消除時間窗；
- 它的真實 GUI、音訊、chooser、跨 Session 恢復均 `NOT_RUN`。

### 11.3 不能互相替代的證據

| 證據 | 能證明 | 不能證明 |
|---|---|---|
| 文件 diff | 指示已更新 | 真實 GUI 成功率 |
| 離線單元測試 | helper／狀態機的合成行為 | LINE viewer 的 toolbar 壽命 |
| 帳本事件 | intent／outcome 已持久化 | 畫面控制現在可見 |
| 空 staging | 讀取當下沒有檔案 | 從未派送或不會延遲落盤 |
| `NOT_SENT` | 本次受支持 helper 沒有 dispatch receipt | OS 層完全沒有動作 |
| 截圖 | 某時點的像素狀態 | AX 節點存在或控制可點 |
| AX | 某時點的無障礙樹 | toolbar 一定存在／不存在 |

---

## 12. Owner 決策點

以下不是本輪已執行的事項，而是後續要推進時需要 Owner 明確選擇的邊界：

1. **是否採用 `intent → bounded reveal → immediate dispatch` 的協議方向？**
   - 這是本文首選，但會改變現有 intent 的 freeze 語意，屬於架構／Skill 行為變更。
2. **是否先做 E1～E3 的實機區辨實驗，再決定實作？**
   - 需要指定測試列表、有效前景與明確授權；不能拿私人資料做非必要實驗。
3. **是否保留目前「intent 前必須先看到 toolbar」的規則，接受較高阻塞率？**
   - 這是保守但已知會反覆失敗的選項；若選此項，至少要把它記為產品限制，而不是宣稱流程可重複。
4. **音訊是否納入產品範圍？**
   - 這是獨立的產品決策；若納入，才需要設計 `AUDIO`／MIME 分類與 chooser 驗證。不要用它解釋本次 F1。
5. **是否授權後續程式／Skill 修改與真實 GUI 驗證？**
   - 本報告與分析不授予 GUI、下載、Save All、chooser 或 ledger 變更權限。

---

## 13. 實際唯讀命令與結果

本輪實際執行過的命令如下；全部是唯讀查詢或檔案核對，沒有 GUI 操作、沒有下載、沒有建立 intent、沒有修改帳本。

staging 與 observation 的迴圈以下用 redacted 等價形式表示，避免把顯示名稱寫入報告；實際核對使用同一組路徑。

```sh
git status --short
git branch --show-current
git rev-parse --short HEAD
```

結果：branch `feature/line-notes-media`、HEAD `e321d7a`；工作樹保留既有 `M 問題提報單.md` 與無關 `?? .playwright-mcp/`。

```sh
wc -l -c /Users/hsiaojohnny/.codex/sessions/2026/11/17/rollout-2026-11-17T21-38-08-01a1e9ba-afe5-7c31-a052-1800c913800d.jsonl
shasum -a 256 /Users/hsiaojohnny/.codex/sessions/2026/11/17/rollout-2026-11-17T21-38-08-01a1e9ba-afe5-7c31-a052-1800c913800d.jsonl
```

結果：`1023` 行、`3,786,894` bytes、SHA-256 `9f2d7765518593c79e16413c4a6f8485bf71dc45205e936adc4b31db1c131af8`。

```sh
jq -c '{sequence,kind,list:.local_list_id,attempt_id:.data.attempt_id,outcome:.data.outcome,session_id:.data.session_id}' \
  notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000014.json \
  notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000015.json \
  notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000016.json \
  notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000017.json \
  notes-backup-records/1bed1cdc-4cde-47d1-a718-088eb2d38de3/events/00000024.json \
  notes-backup-records/1bed1cdc-4cde-47d1-a718-088eb2d38de3/events/00000025.json
```

結果：G 兩個 intent 對應兩個 `NOT_SENT`；Gis 一個 intent 對應 `UNKNOWN`。

```sh
for d in <三個 staging 路徑>; do
  printf '%s | entries=%s\n' "$d" "$(find "$d" -mindepth 1 | wc -l | tr -d ' ')"
done
```

結果：三個 staging 的 `entries` 均為 `0`。

```sh
jq -r '.created_at.value + " | ax=" + .assets.ax.sha256 + " | shot=" + .assets.screenshot.sha256' \
  .local/line-backup/tasks/notes-daily-20261117-foreground02/observations/<observation>/<observation>.diagnostic.json
```

結果：G 五個觀察的 AX hash 同為 `33d55bea…`，截圖 hash 不同；Gis 前後觀察的 AX hash 同為 `f27c5fd6…`，截圖 hash 不同。

```sh
git show -s --format='%H%n%ad%n%B' --date=iso-strict HEAD
```

結果：HEAD `e321d7aa956a6203fbb877cc4ff7bcf57de68162`；commit message 明確承認文件補丁、`PRIMARY_OUTCOME_STATUS=BLOCKED`、GUI 與音訊 `NOT_RUN`。

本輪**沒有**執行：

- LINE GUI 操作、hover、click、chooser、下載、Save All；
- `intent`、`outcome`、`reconcile`、`download-check`、`verify`、`restart`；
- 修改任何帳本、媒體、程式、Skill 或既有 dirty 提報單；
- 讀取私人媒體內容或播放任何檔案。

---

## 14. 最終判讀卡

**直接阻塞**

> 下載控制可見後，在 intent／讀回／模型回合完成前就消失；G 記 `NOT_SENT`，Gis 記 `UNKNOWN`，三個 staging 皆空，沒有 chooser 或檔案。

**系統層根因**

> 目前協議把 transient toolbar 可見性當成持久交易門票，形成 check-to-use 時間窗；同時把可逆 reveal 與不可逆 dispatch 綁進同一個一次性 candidate 與 intent freeze 邊界。

**不是什麼**

> 不是已證實的下載 API 失敗；不是已證實的音訊 MIME 失敗；不是已證實的重複派送；也不是可以用固定 sleep 解決的單一延遲。

**最短安全修復方向**

> 先建立 intent，再做一次有界安全 reveal，最後以最新 fresh after 立即 dispatch；把 freeze 點移到 `dispatch_started`，而不是 intent 寫入。此方向尚未實作、尚未實機驗證。

**目前狀態**

> `PRIMARY_OUTCOME_STATUS=BLOCKED`；`CORE_ACCEPTANCE_STATUS=NOT_RUN`；`REQUIRED_VERIFICATION_STATUS=NOT_RUN`；`TASK_CLOSURE_STATUS=BLOCKED`。

---

## 15. 證據索引

### 15.1 Session

```text
/Users/hsiaojohnny/.codex/sessions/2026/11/17/rollout-2026-11-17T21-38-08-01a1e9ba-afe5-7c31-a052-1800c913800d.jsonl
SHA-256 9f2d7765518593c79e16413c4a6f8485bf71dc45205e936adc4b31db1c131af8
```

### 15.2 G 帳本

```text
notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000014.json
notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000015.json
notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000016.json
notes-backup-records/77b34207-625c-4d9d-ad21-62741f8f2d81/events/00000017.json
```

### 15.3 Gis 帳本

```text
notes-backup-records/1bed1cdc-4cde-47d1-a718-088eb2d38de3/events/00000024.json
notes-backup-records/1bed1cdc-4cde-47d1-a718-088eb2d38de3/events/00000025.json
```

### 15.4 觀察／截圖

```text
.local/line-backup/tasks/notes-daily-20261117-foreground02/observations/obs-G-reveal-after-01/
.local/line-backup/tasks/notes-daily-20261117-foreground02/observations/obs-G-download-pre-01/
.local/line-backup/tasks/notes-daily-20261117-foreground02/observations/obs-G-post-intent-nocontrol-01/
.local/line-backup/tasks/notes-daily-20261117-foreground02/observations/obs-G-reveal-after-02/
.local/line-backup/tasks/notes-daily-20261117-foreground02/observations/obs-G-download-after-recovery-intent-03/
.local/line-backup/tasks/20261117-notes-daily-backup/observations/04-media01-reveal-after-20261117T2318/
.local/line-backup/tasks/20261117-notes-daily-backup/observations/04-media01-intent-gate-20261117T2319/
```

### 15.5 規格／報告

```text
.agents/skills/line-notes-agent-cua/SKILL.md
.agents/skills/line-notes-agent-cua/references/gui-inventory.md
docs/plans/20261118-notes-deferred-preparation/report.md
```

### 15.6 既有文件

```text
問題提報單.md   # 既有 dirty 修改，本輪保留、未覆寫
```

---

**本文件結束。**
