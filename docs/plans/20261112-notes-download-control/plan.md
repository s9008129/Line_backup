# plan：記事本下載控制的有界查證與修正決策（草稿 v1）

## 決策摘要

**先補控制可觀察性的證據，不預先修改程式或放寬安全條件。** [analysis.md](analysis.md) 回答提報單六個分析問題；根因仍 UNKNOWN，沒有可核准的程式修復候選。本計畫是可執行的查證與分流草稿，不是產品 PASS 或實作授權。

- 使用者目標：釐清五張照片卡在 intent 前的原因，選出最小必要處置，使同一日常記事本入口可以自主完成合格備份。
- 本輪可觀察交付：有來源與版本的分析、明確查證步驟、可寫路徑、首個可驗證切片、停止與人工交接；另按使用者指定以 GPT-6-luna 助手撰寫 commit 訊息，提交及推送規劃成果。
- 分級：**STANDARD**。本輪只寫文件，風險可逆；但後續涉及真實 GUI 控制歸屬及可能的不可重試派送，尚有高影響未知，不能當成已知的一行修正。現階段不改資料／公共介面，不以抽象風險升為 CRITICAL。若後續需要事件格式、資料遷移、UNKNOWN 例外或授權邊界改變，停止並由 Owner 重新定級與核准，不沿用本範圍。
- 選定方案：一次有界的 intent 前觀察；有明確方法才決定是否 reference 修正。能依現有規則完成則 NO_CHANGES_TO_COMMIT，不造空實作。
- 非目標：本 Planner 不下載五張照片、不讀真實帳本／私人影像、不解 UNKNOWN、不啟動 LINE、不改 notes/daily 程式、控制器、正式 Prompt 或帳本語意；不承諾所有模型／版本每次成功。

### 真正替代方案

| 方案 | 取捨／選擇 |
|---|---|
| 只重貼日常 Prompt 或重跑同一觀察 | 可保留既有流程，但無新證據可能在同點停止；不能當根因解答或重試理由。待查證有具體方法後再做日常確認。 |
| 有界觀察，必要時補 reference | **採用**；直接針對缺失的控制鏈，保持 intent、資料及 public interface 不變。 |
| 先改 CLI summary 或新增 GUI 狀態 | 不採用；程式欄位語意一致，沒有已證明違約；CLI 無法自行觀察 LINE。 |
| 降低 intent 門檻、先建 attempt、猜控制／搬相簿入口 | 不採用；擴張派送與資料風險，沒有證據支持，也不在授權內。 |

## 範圍與基準

- Repo／worktree：`/Users/hsiaojohnny/dev/Line_backup`，非切換中的 worktree。
- 分支／基準 HEAD：`feature/line-notes-media`／`40a7b09e9900eddab2df9bfd81aad9ec25b89c1f`；規劃前遠端同 SHA。事件基準為 `02db924fd89ff79067cd4958729a3ac6b8157437`，兩版只差提報單。
- 既有工作：一份不屬本任務的根目錄 untracked Markdown；不讀內容、不 stage、不移動、不刪除。其精確路徑及初始 hash 僅記本機 private preflight。
- 本輪可寫且可提交：本任務目錄新增 `analysis.md`、`plan.md`、`handoff.md`、`planner-report.md`、`progress.md`、`source-manifest.json`。既有問題提報單保持不變。
- 私有規劃證據：`.local/line-backup/tasks/20261112-notes-download-control-planning/`，保存 preflight、命令與驗證紀錄、助手參與與提交訊息；不提交原件或私人內容。HTML 使用 Skill 全域外觀設定，只放遮蔽摘要；不將原始 task 證據移往全域 `.codex`。
- S1 待 Owner 核准的寫入：任務目錄新增 `control-observation-report.md`、必要 manifest；原始觀察只能放 Owner 核准的專案私有新子目錄，不能覆寫事發原件。S1 不寫真實帳本。
- S2 條件式候選路徑：僅 `references/gui-inventory.md`；必要時 Skill 主文件加定位連結。**目前未核准修改，需 S1 證據及 Owner 決定。** 其他 reference、手冊、程式、測試若需改，先修訂計畫。
- 禁止：`backup/`、`notes-backup-records/`、相簿 `backup-records/`、active 檔及索引寫入；事發私有原件／舊完成／UNKNOWN 改寫；LINE 輸入、外傳影像、增設控制器；merge master、force-push、改寫舊 commit。

## 風險與成功條件

### 不可放寬的保障

保留列表→貼文→媒體身分、全列表卡片覆蓋、目標細盤、就緒與種類證據、當次控制歸屬／可見性／映射。控制未知即停在 intent 前；intent 一旦成立即保護為可能已派送；每 attempt 下載控制與 chooser 最終確認各最多一次。無 outcome 先 outcome，已有 UNKNOWN 才 reconcile，不以新目錄或 restart 解除。相簿流程與資料完全獨立。

本事件沒有 attempt，故查證不得引入恢復交易。當次最新帳本若顯示不同事實，停止使用提報單作現況，回到正式日常流程核對；不得把歷史五筆 PENDING 當成永遠不變的授權。

### 證據、風險及緩解

| 風險 | 可驗證緩解／停止 |
|---|---|
| 圖片內按鈕誤當 LINE 控制 | 控制必須在 viewer 外框／AX／可靠 Notes 脈絡有獨立作用依據；只有圖示或照片像素不足。 |
| AX／截圖不涵蓋獨立層 | 保存來源 scope、app/window 綁定、幾何與時間；範圍不足記 UNKNOWN，不推論不存在。 |
| hover 不支援，卻用 click／drag 模擬 | 查當次工具文件；不支援即 NOT_RUN，不換 API、執行器或輸入替代。 |
| 探索誤觸下載／分享／關閉 | S1 只做已核對的低風險觀察與導覽；沒有可靠作用或定位就停止。任何不明派送立即停，不追加新控制。 |
| 規劃文件變成日常依賴 | 可重用操作知識只整合 Skill/reference；正式入口仍是手冊 B 區 Prompt，不要求 Owner 帶開發計畫。 |
| 外部成員、其他 Session 或程序改動來源／Git | 每階段重核版本與當前來源；有差異停下交人決定，不覆蓋或宣告原子性。 |

無法保證服務端靜態快照、外部 writer 不存在、UI 一直保持焦點、未觀察的 popup 不存在、原生派送 exactly-once、OS 隔離或 provider 身分。模型配置、dispatch 參數、平台顯示及 provider usage 分層記錄；沒有用量就不聲稱節省 tokens／費用。

## 檢查與交接

### S1：首個可驗證切片——控制觀察與分流報告

Owner 先決定提供遮蔽現存原件，或授權一次有界診斷與有效前景。這是診斷選項，不是新增日常啟動模式；本計畫與提報單都不能授權 GUI。

執行者依 `analysis.md` 第 4 節保存基線→來源範圍對照→如工具支援且已授權的一次安全移鼠對照；只有可靠返回控制成立才觀察同貼文其他 Notes 上下文。**全程停在 intent 前，不點下載／分享、不開 chooser、不寫帳本。** 沒有可用能力或控制歸屬仍未知，就交回 BLOCKED 與精確缺項，不耗盡次數。

S1 合格交付不要求一定找到控制，而要求：

- 每項結論可回到原件與 hash，來源、時間、viewer 脈絡、焦點、幾何、工具能力及未知值明列。
- 分清觀察到候選控制、已證明作用與可定位三件事；未證明則 UNKNOWN，不能升為下載成功。
- 有實際命令／輸入與 exit／回傳清單；沒有 intent、下載控制呼叫及 chooser 確認，無帳本寫入。
- 明確選擇「既有知識足夠／需要 reference 修正／環境或能力阻塞／具體程式違約需改計畫」之一並列證據。只是重述原 AX 不算新增鑑別資訊。

### S2：只有具體知識缺口成立，才有人啟動文件實作

Owner 核准精確證據與 reference 範圍後，Implementer 交付最小可驗證文件切片：記錄本版已證實控制的頁面角色、觀察與定位條件、可靠導覽、失敗分流、未測限制；不寫死座標、不虛構通用 hover、不改下載交易順序。來源直接列於任務證據，Skill 可獨立引導日常 Agent 找到方法。

切片完成後由人啟動第二個 Simplicity Review；若已是最終候選，不再造剩餘實作。若 S1 已證明不需修改，就記 NO_CHANGES_TO_COMMIT，沒有實作切片，不為角色順序製造空變更。

### 檢查矩陣

| 檢查／owner | 命令或方式／合格證據 | 停止條件／本輪結果 |
|---|---|---|
| Planner 版本及來源 | Git root/branch/HEAD/status/worktree、遠端精確 HEAD、source manifest SHA-256 | 版本或既有工作變動須核對；已做唯讀 preflight，見 report |
| Planner 文件交付 | `git diff --check`；本機文件連結、來源 hash、實際可提交路徑及隱私核對 | 缺來源／越權範圍不交付可實作批准；只給草稿 |
| S1 執行者證據切片 | 前述原件、範圍對照、輸入紀錄、無派送聲明與可追溯記錄 | 缺前景／資料授權、工具拒絕、控制不明、兩次無新資訊即停；NOT_RUN |
| S2 Implementer 文件一致性 | 逐條對來源、Skill 連結可發現、無相簿 fallback／固定座標／放寬 gate | 證據不支持的規則不得寫；NOT_RUN |
| 若另核准程式修改：Implementer 回歸 | 下列專案最小三命令，exit 0 與完整輸出；另按具體缺陷選針對測試 | 不屬本輪／S2 文件範圍；須先修訂計畫，本輪 NOT_RUN |
| 實際可用性：Owner 日常入口 | 手冊 B 區正式 Prompt＋新有效前景；Agent 自動讀歷史、盤點、單項下載及逐檔驗證；Owner 確認成果 | 控制未知／未決交易等依 Skill 停；本輪 NOT_RUN，不能用 Harness Acceptance Prompt 替代 |
| 正式獨立接受（若後續風險要求）：人另開 Session | 核准版本與相稱的獨立文件／程式安全核對，不冒充日常下載能力 | 本輪 NOT_RUN；助手與 Implementer 自評不能簽發 |

程式修改另經核准後的最小回歸：

```sh
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py
PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help
PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'
```

本輪僅規劃，未執行以上命令；既有測試名稱及語意位置見 analysis／助手來源核對，並非測試通過證據。S2 若只改文件，不要求無關全量回歸。

### 日常備份的觀察成功條件

在來源仍為原兩篇／五張且沒有其他 blocker 的前提下，正式日常流程完成：5 個照片媒體各有可歸屬的終結結果、檔數與非空檢查、SHA-256、ImageIO 完整解碼、completion 寫入及讀回；文件連結保持 NO_MEDIA、不下載附件；無 unresolved attempt／pending naming。來源變動就先重盤並列差異，不能以舊數字作 oracle。

只有上述實機與檔案證據才能支持該列表的備份結果。單元測試、S1 找到控制、S2 文件核對或簿記 PASS 不能代替。影片、混合附件、跨 Session 恢復及其他模型／環境未測維持 NOT_RUN，不為本次照片修正另擴任務。

### 人工檢查點、停止與下一步

1. **現在由 Owner 啟動計畫 Simplicity Review**，傳精確 commit 與本目錄；本 Planner 不派正式角色、不替計畫接受。
2. 由 Owner 決定 S1 證據來源及授權；S1 有結果後決定需不需要 S2。必要的獨立 Plan Review 由人依風險決定；若升 CRITICAL 則保留獨立計畫審查及接受。
3. 只有核准 S2 後才啟動 Implementer；首個實作切片後由人啟動第二次 Simplicity Review。
4. 實際可用性由 Owner 另交接日常正式 Prompt，不改成 Harness Acceptance/E2E 入口；文件／程式審查與日常成果分開記錄。

同一根因最多三次有證據嘗試，連續兩次無新資訊即停止相同方法，不靠換 Session／API／目的地重置。出現工具拒絕、身分歧義、未知派送、寫入衝突、exit 70、缺授權或越過本計畫路徑／資料／介面邊界，保存證據並交 Owner 決定；不能自動修復、再測或結案。

## 草稿狀態

以下是產品目標的狀態，不是 Planner 文件是否交付；本角色文件結論另記 `PLAN_DRAFT_COMPLETE`。

- PRIMARY_OUTCOME_STATUS: BLOCKED（5 張仍待下載，根因尚未實證）
- IMPLEMENTATION_STATUS: NOT_RUN
- CORE_ACCEPTANCE_STATUS: NOT_RUN
- REQUIRED_VERIFICATION_STATUS: PARTIAL（僅來源／規劃核對；下載、解碼與 completion NOT_RUN）
- INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN
- TASK_CLOSURE_STATUS: BLOCKED
