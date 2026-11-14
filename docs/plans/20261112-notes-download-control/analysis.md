# 記事本下載控制：Planner 證據分析

日期：2026-11-12。分析基準：`feature/line-notes-media`／`40a7b09e9900eddab2df9bfd81aad9ec25b89c1f`。事件產品基準：`02db924fd89ff79067cd4958729a3ac6b8157437`；兩者只差問題提報單，產品來源相同。來源雜湊見 [source-manifest.json](source-manifest.json)。

## 結論與證據限制

**立即停止原因已知：intent 前的記事本下載控制出處、可見性與定位未成立。底層 UI 根因仍為 UNKNOWN。** 現有證據不支持修改 notes CLI、放寬 intent 或增設控制器。最小下一步是取得同一 viewer 的觀察範圍／狀態對照；若找到可驗證的操作知識缺口，再決定是否只補 reference。

本輪直接核對版本、公開提報單、Skill、references 與程式；**未讀私人截圖、原始 AX、真實帳本或照片，也未操作 LINE**。下文的事件數量與 GUI 描述來自 [問題提報單](問題提報單.md:16)，不是本輪重做實機觀察。提報單第 6 節原件 SHA-256 本輪未重新驗證，不把已列 hash 當成已重讀原件。原件不足以公開判讀時，應由 Owner 決定提供遮蔽版本或另行交接觀察，不能由規劃角色廣搜私人資料。

## 1. 最小證據鏈與本次缺口

| 節點 | 最小可支持證據 | 本事件依提報單的結果 |
|---|---|---|
| 任務及前景 | 實際備份 Prompt、當次有效交接、當前列表角色 | 當次成立；不延伸為本規劃 Session 的 GUI 授權 |
| 歷史及列表 | 全帳本查詢、唯一匹配、未決交易核對 | 已選原帳本；active 指另一列表但未造成混帳；無 unresolved attempt |
| 來源覆蓋 | 頂底、逐頁雙向對帳、有序重疊、逐篇細盤 | 2 篇；1 篇 5 個 PHOTO，另 1 篇 NO_MEDIA；scan COMPLETE |
| 媒體與 viewer | 列表→貼文→媒體的連續脈絡、就緒及種類正面證據 | 已盤 5 筆；本輪未重新驗證種類或來源原件 |
| **控制與定位** | 控制屬此 Notes 媒體、可見可用、觀察範圍及當次映射 | **未成立，故停在 intent 前** |
| intent／派送 | 持久化並讀回 intent、新空白 staging、重新定位、下載控制至多一次 | NOT_RUN；沒有 attempt，不適用 reconcile 或 restart |
| chooser／結果 | 同 attempt 歸屬、精確目的地、確認至多一次、可歸屬終結結果 | NOT_RUN |
| 驗證／完成 | 穩定檔集、數量、非空、SHA-256、ImageIO 解碼、completion 讀回 | NOT_RUN；5 筆仍 PENDING，已驗證下載為 0 |

流程依據：`references/download-and-ledger.md:260–270`。控制未知時先建 intent，會憑空引入「可能已派送」交易，不能用來發現控制。也不能把 `scan_coverage=COMPLETE` 延伸成下載、解碼或 E2E 已完成。

## 2. 根因候選與鑑別順序

下表是按現有支持程度與低風險鑑別價值排列的查證順序，不是測量所得機率。候選可同時成立。

| 順位／候選 | 支持與反向限制 | 信心與仍缺的鑑別證據 |
|---|---|---|
| 1. viewer 狀態或觀察來源未涵蓋控制 | 提報單只證明當次 AX／畫面未識別控制；未取得 hover 狀態。reference 已明示 AX／app-bound 圖片可能漏獨立層。尚未證明本次確有 popup、hover 控制或被漏區域。 | 中：值得先查；真正原因仍 UNKNOWN。需同一 viewer 的來源範圍、焦點、幾何、工具能力與可允許狀態對照。 |
| 2. 所需控制在其他 Notes 上下文 | 停在第 5/5 viewer；未證明此 viewer 必定含下載入口。references 是要求核對控制，沒有為本 viewer 指定已驗證入口。也未證明貼文卡片或其他頁確有控制。 | 低至中。只在可靠返回／導覽證據成立時，補同貼文上下文觀察；不能猜關閉、右鍵或換相簿。 |
| 3. Skill／reference 缺少能重用的操作知識 | `gui-inventory.md:85–99,110–137` 有核對與停止規則，未給本版 viewer 已實測的控制發現方法；`download-and-ledger.md:260–263` 同樣以控制已能證明為前提。 | 高：此來源集合沒有已驗證方法；中：它是否是本次失敗的必要成因。需先取得實際方法，才能確認應補哪條 reference，不能編造 hover 或固定座標。 |
| 4. LINE 版本、服務、焦點或來源狀態造成不可用 | 未記錄當次 LINE／macOS 精確版本、服務狀態與控制條件，故不能排除。沒有錯誤提示、到期或版本對照證據。 | 低；需版本與可歸屬的畫面訊息。現在查到的版本只能標現在，不能回填事發版本。 |

「Agent 未遵循既有指示」目前**未獲證明**。停止點符合 intent 前預檢。是否漏用當時可取得且允許的觀察來源，仍缺工具能力與原始操作 trace；沒有 hover API 不能要求 Agent 猜方法。反過來，安全停止也不能證明探索已充分、Skill 無缺口或原列表已完成。

「notes CLI 故障」不列優先根因：沒有提出 CLI 拒絕、exception 或能解釋控制不可見的程式路徑。這是針對本事件的排查結論，不是宣告 CLI 全面無缺陷。

## 3. 三個摘要欄位的精確語意

| 欄位 | 來源事實 | 本事件解讀 |
|---|---|---|
| `dispatch_blockers=[]` | `notes.py:5372–5409` 從 scan、盤點、交易與本機狀態建立清單，沒有觀察 LINE。`5410–5419` 另算 incomplete。 | 帳本未列 blocker；不等於 GUI 全部前置成立。PENDING=5 仍令 all_known_media_complete=false。 |
| `dispatch_authorized=false` | `notes.py:7156–7162` 在 CLI 結果固定加入 false；模組 `1–5` 明定不授 GUI 權限。 | 能力／授權分界，不是 Owner 授權被撤回，也不是這次 GUI 的業務拒絕。 |
| `source_availability=UNKNOWN` | `notes.py:5194–5195` 僅在已有 source-unavailable 投影時給 EXPIRED，否則 UNKNOWN。 | 未被記為到期；與媒體業務 UNKNOWN、未知 attempt、是否可下載是不同命題。 |
| capture 的 `status=COMPLETE` | `notes_capture.py:306–326` 是固定命令及收據擷取契約。 | 不代表媒體備份完成；仍須讀 child exit 與業務結果。 |

目前只需在分析與回報說明上述範圍；**沒有證據支持改 summary schema、添加虛構 GUI blocker、改 false 值或改事件模型**。如日後有可重現的程式違約，須以新證據與修訂範圍交 Owner 決定，不能利用本計畫直接擴編。

## 4. 最小新增證據及分流

優先由 Owner 提供同 viewer 的遮蔽 AX／截圖及來源範圍，或另行授權一次有界、intent 前的觀察。這是本次根因診斷，不增加日常備份的固定啟動步驟。

1. 記錄當次 app/window 身分、就緒、焦點、截圖範圍與幾何、工具文件支援的能力，以及當前 LINE／macOS 版本；事發時未知值仍保留 UNKNOWN。
2. 在相同 viewer、沒有輸入的基線下取得 AX 與當次允許的最小局部畫面。若有差異，分別歸屬兩個觀察來源，不混填。桌面截圖能力不存在或平台拒絕時停止該方法。
3. 只有工具明確支援移鼠、Owner 授權與有效前景都成立、且移入位置是可靠的無派送區域時，才比較一次移鼠前後觀察。沒有 API 就記 NOT_RUN；不以 click、drag、右鍵、其他程式或猜 API 模擬 hover。固定等待不是修復。
4. 如仍需核對其他 Notes 上下文，只能依當次可靠返回控制導覽一次後重觀察。無此證據則停止，不能為研究猜 Escape、Command-W 或關閉。

觀察遇到可見控制就記錄**它的出處、作用依據及定位條件**，不點控制驗證；本次診斷不得建 intent、chooser 或下載。看見一個圖示只能證明候選存在；若缺作用或 Notes 歸屬，結論仍為 UNKNOWN。

分流規則：

- 能從現有 references 直接完成且操作條件齊備：無產品修改，回報觀察結果；Owner 另以日常正式 Prompt 做實際可用性確認。
- 找到 references 未記載的、可重用且有來源的方法：交 Owner 決定 reference 的最小修正，再由人啟動 Implementer；不是本 Planner 自行修復。
- 方法依賴 Owner 臨時教學或開發計畫：仍是尚未整合缺口，不能把這次手動成功當成固定入口已可重用。
- 仍無控制或能力不足：保留 UNKNOWN 與五筆 PENDING，交回具體缺項，不造空實作、不換下載入口。
- 出現具體 CLI 缺陷：另提精確重現、允許修改路徑與回歸，停止本計畫的文件範圍；不能直接改 notes.py。

## 5. 最小修正方向與可接受證據

若需要修正，優先只改 `.agents/skills/line-notes-agent-cua/references/gui-inventory.md`：加入已證明的頁面角色、控制發現條件、當次來源選擇及失敗分流，避免版本普遍化、固定座標及相簿 fallback。Skill 主文件只有在入口連結不夠可發現時才加一個定位連結。下載交易順序與使用手冊正式 Prompt 維持既有規則；若要改它們，先回 Owner 決定，不能順手擴寫。

文件修改的驗證是來源與敘述能逐條對應、與單次派送／UNKNOWN／前景規則一致、日常 Skill 能找到方法。若沒有產品程式變更，不新增鏡射文件的單元測試；文件核對不替代實機。

實際能力確認必須由 Owner 使用手冊 B 區的日常正式 Prompt，重新交接**單一記事本列表**，讓 Agent 自動查歷史、重新盤點並完成合格項。若仍是原兩篇／五張，應得到五份可歸屬完成與 ImageIO 驗證、NO_MEDIA 不下載文件、無未決交易；來源變動則按實際盤點列差異，不能硬湊五張。未下載、未解碼、未讀回 completion 均不可計完成。若 intent 後發生 UNKNOWN，依既有 outcome／reconcile 規則停止，絕不因本計畫重送。

影片、混合附件 chooser、跨 Session 恢復、所有模型皆可完成、服務端位元相同及外部副本完整，本輪都沒有證據，維持 NOT_RUN／UNKNOWN。同一入口的一次成功也不能外推全部環境。
