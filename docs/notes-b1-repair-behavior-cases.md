# LINE 記事本 B1 修復行為案例

## 用途與證據界限

本文件把已核准的 B1 修復判準整理成可重複核對的行為矩陣。全部內容都是**匿名文件假設**；沒有使用真實列表名稱、貼文名稱、媒體、帳本 ID、截圖、雜湊或交易結果，也不是本次 LINE 操作、實機 `OBSERVED`、acceptance 或 E2E PASS。案例中的時間、畫面、欄位值與結果若未由當次工具提供，實際紀錄必須記 `UNKNOWN`；本文件不補成已發生的事實。

本文件不是第二份規範。B1、[證據判定案例](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md)、[驗證與恢復](../.agents/skills/line-notes-agent-cua/references/verification-and-recovery.md) 與 [下載與 notes CLI](../.agents/skills/line-notes-agent-cua/references/download-and-ledger.md) 仍是判準來源；以下矩陣只列後續審查應重現的輸入、預期決策與禁止推論，不新增 helper、schema、slot、hover API、Owner 啟動步驟或另一個 gate。

共通假設：

- 有效前景與同一 app／window 均由當次交接與原件支持；案例未另說明的話，不得把舊座標、舊截圖或背景視窗當成新狀態。
- 目標以 `M1` 等匿名代號表示；三層身分、列表覆蓋、返回錨點與入口角色仍須在當次畫面核對。
- Agent 播放輸入固定為 `NONE`；此為案例描述，不是新事件欄位。不得為了確認播放狀態、種類或進度而送出播放／暫停／拖曳／倍速／內容切換或內容分析輸入。
- 所有「可繼續」都以 B1 的完整前置、最新原件、有效映射與交易 gate 為必要條件；本文件不保證任何實際下載。

## 視覺與 AX

| 編號 | 假設觀察 | 預期決策 | 禁止推論 | 對照 |
|---|---|---|---|---|
| B1-V1 | AX 沒有下載節點；同一 viewer 的當次截圖充分涵蓋控制，控制歸屬、啟用、作用區，以及像素／點數／螢幕座標、視窗位置、縮放與 mapping 完整且仍有效。 | AX 缺節點不否決充分視覺；若 B1 其餘條件成立，可在 intent 後走直接路徑，保存同一份原件，不能補造 AX 節點。 | 截圖只看見箭頭就猜點；視覺存在等於 native hit-test；AX 沒有節點等於控制不存在。 | C22、D3 |
| B1-V2 | AX 沒有節點；截圖只有局部、控制歸屬／啟用或座標映射不完整、過期或 `UNKNOWN`。 | intent 前先保留本項。唯讀觀察若真正補足完整的 viewer 覆蓋、控制歸屬、啟用與映射，才可依 B1 備妥直接路徑。intent 後只用 B1 指定的當次原件；若直接與已稽核的 reveal 路徑皆不成立，保留原件與缺口，依既有 outcome 規則停止。 | 自行補 mapping、用近似圖示或舊座標；在 intent 後重拍、重開或重新尋找控制；把截圖不足當成控制不存在或 `NOT_SENT`。 | C23 |
| B1-V3 | 當次充分視覺與映射成立，但沒有 AX 節點，也沒有新的 reveal 方法；控制本身可直接可見。 | 直接路徑不需要 candidate 2；保留視覺原件與 mapping 後依 B1 處理。 | 把 AX／API 當成唯一入口；把充分視覺錯誤降級為 `CONTROL_LOCATION_UNAVAILABLE`；用截圖偽造 AX。 | C22、C14 |

## 播放三維

| 編號 | 三個維度 | 預期決策 | 禁止推論 | 對照 |
|---|---|---|---|---|
| B1-P1 | Agent 播放輸入 `NONE`；來源狀態 `AUTOPLAYING`；來源、選取、幾何、mapping 與控制遮蔽均未漂移，且其他 B1 前置正面成立。 | 依 B1 記錄狀態與原件；自動播放本身不是 Agent 違規，也不單獨阻擋。只有在其他 B1 條件仍成立時才可繼續當次路徑。 | `NONE` 就代表畫面靜止；`AUTOPLAYING` 是 Agent 播放；播放狀態可取代選取／幾何／映射核對。 | C24 |
| B1-P2 | Agent 播放輸入 `NONE`；來源 `AUTOPLAYING` 或狀態 `UNKNOWN`；但 viewer／選取／幾何／mapping 漂移或控制被遮蔽。 | 立即停止依賴該輸入，保存漂移與證據不足；不得把它記成 Agent 播放違規，也不得沿用舊狀態。 | 播放本身一定阻擋；漂移可用重拍、重開或返回解鎖；控制被遮住仍可猜點。 | C24、C13 |
| B1-P3 | Agent 播放輸入 `NONE`，來源狀態 `UNKNOWN`。比對已保存的 before 或前次有效觀察與當次原件，正面確認同一 viewer 的來源、選取、viewer 區域邊界、視窗位置、縮放及映射一致。 | 記錄 `UNKNOWN`。比對一致且其餘 B1 前置成立才可繼續。缺比對原件或無法證實一致時，停止該項輸入。 | 猜成 `NOT_PLAYING`、為了確認而操作播放、用 `UNKNOWN` 或僅未見漂移代替比對。 | C24 |

## Candidate 2 與額度

| 編號 | 假設觀察 | 預期決策 | 禁止推論 | 對照 |
|---|---|---|---|---|
| B1-N1 | 同一媒體 cross-Session 已有完整 1 次 reveal 紀錄、prior refs 完整、預算 `budget_before=1`；當次工具文件確實提供原先未知的無點擊方法，且當次安全區與映射可正面歸屬，因而改變方法／映射判準。 | 只有控制仍隱藏、intent 已讀回且所有 B1 gate 成立時，才可用同一固定 slot 的 `candidate_ordinal=2`；新證據不保證成功或恢復舊項。 | 文件存在就解鎖；新 evidence 可直接建立第三候選；新 attempt 自動符合新證據。 | C18、C25 |
| B1-N2 | 同一媒體已有 1 次 reveal；只有新 capture、重開 viewer、new Session、時間流逝、只換一個座標或事後補 request，沒有改變方法／映射的正面新內容。 | 不算 candidate 2 新證據；保留該項未完成，停在輸入前，不建立第三次或重設額度。 | 新畫面本身就是新證據；重開可把 ordinal 重置為 1；只換點位等於安全區重建。 | C18、C25 |
| B1-N3 | 同一三層身分跨 viewer、reopen、Session 或 restart 查回已送出 `1` 次 reveal，且當次仍在 hidden branch。 | 額度跨邊界累計：`0→1` 是首次候選，`1→2` 需新證據；每個 attempt 最多一次 intent 後 reveal、每個媒體最多兩次。 | 新 Session／restart 重置額度；以直接路徑名義再送 hidden budget 不明的 reveal；第三次候選可繞過耗盡。 | C18、C13 |
| B1-N4 | `notes-reveal-c2-<attempt_id>` 或 `notes-download-<attempt_id>` 已存在，或 `wx` 建立遇到並行競爭／讀回不符，尚無新的 input receipt。 | 零 input／零下載控制呼叫；保留原 intent 與碰撞證據，不改固定 slot 字面、ordinal、taskDir、Session 或目錄。 | 刪除／覆寫 slot 可重試；改 ordinal 可建立新 slot；helper 前失敗等於未派送；重開入口可繼續。 | C19 |

## 局部排程與全域停止

| 編號 | 假設觀察 | 預期決策 | 禁止推論 | 對照 |
|---|---|---|---|---|
| B1-S1 | 完整列表仍可核對；`M1` 在 intent 前因 B1 控制映射不足而局部阻塞；沒有未隔離 `UNKNOWN`、no outcome、活動下載、pending naming、`LOCAL_CHANGED`、覆蓋缺口或身分歧義。entry anchor、`expected_return_role`、一次一層的返回控制與有效前景均成立。 | 保留 `M1` 與 blockers，依契約返回並重新核對入口，再一次一項處理其他合格項；列表仍標未完成。`REDOWNLOAD_REQUIRED`／`RECOVERY_EXHAUSTED` 只把項目留為欠件，不單獨構成全域停止。 | 局部阻塞可跳過全域 blocker；返回成功等於下載成功；可平行派送或改寫 `M1` 歷史。 | C26 |
| B1-S2 | 任一未隔離 `UNKNOWN`／no outcome、活動下載、pending naming、`LOCAL_CHANGED`、列表覆蓋或身分不明；另一項看似合格。 | 全域 blocker 存在時不建立新 intent、不派送、不排程繞過；保存原件與原 attempt，只有符合既有安全隔離／精確 restart 路徑才另案處理。 | 換 Session、重開、重掃、空 staging、零計數或先做別項即可解鎖；返回成功可清除 `UNKNOWN`。 | C27、C7、C20 |
| B1-S3 | `UNKNOWN` 的現有證據只有 timeout、畫面未變、控制隱藏、空目錄、缺少 marker、零計數或播放結束；尚無可歸屬且排除原操作稍後繼續的停止 receipt。 | 在沒有新結果證據時保留 `UNKNOWN`，並依既有有限查證／安全隔離分流；不得改寫 `NOT_SENT`／`STOPPED`，也不得建立替代 attempt 後宣稱完成。 | 新 capture、等待、空目錄或控制重新出現等於未派送；隔離等於停止或可無限重送。 | C7、C9、C20 |

## 後續核對

- 以 [B1](../.agents/skills/line-notes-agent-cua/references/gui-inventory.md#目標與下載控制就緒b1) 對照上表的可繼續、停止與禁止推論，確認三份同步文件的摘要沒有另立 gate。
- 以 [C18](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md) 與 [C19](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md) 核對跨 Session 額度與固定 slot；以 [C7](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md)、[C9](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md) 與 [C20](../.agents/skills/line-notes-agent-cua/references/evidence-decision-cases.md) 核對 `UNKNOWN` 不改寫。
- 本文件沒有新增可執行 helper、事件欄位、slot 命名、GUI 控制、hover API 或 Owner 步驟；若後續需要改動這些項目，應另立有界計畫並另行審查。
- 真實 LINE 下載、混合附件 chooser、跨 Session 成功恢復、completion 與 `download-check` 均為 `NOT_RUN`；文件案例與離線檢查不能替代實機結果或獨立 acceptance。
