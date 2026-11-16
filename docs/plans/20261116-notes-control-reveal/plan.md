# 記事本下載控制發現：有界修復計畫

> 初次執行曾因合成測試誤寫真實 active locator 而中止；Owner 已明示繼續，污染檔已隔離保留。實際修復、回歸與實機待測範圍見 [結果報告](report.md)。

## 基準與目的

- 基準：`feature/line-notes-media`，`d655025ae2c5ccb1129f740dafd0302e5456e4b2`。
- 依據：[問題提報單](../../../問題提報單.md) 與當次原碼核對；本次不操作 LINE、不改寫真實帳本或媒體；回歸保護比對僅唯讀核對帳本檔案清單與 bytes/hash。
- 交付：補齊 Skill 的可執行候選導覽、停止條件與永久證據指引，並以合成測試核對既有證據能力。
- 不宣稱已修復 C 的真實 viewer，不用離線測試替代日常正式入口。

## 根因與證據界線

第一個未成立條件是「當次 viewer 下載控制可見、歸屬與定位成立」，因此停在 intent 前。提報中 C/D 共 6 項為 PENDING，沒有下載失敗或 UNKNOWN 的證據。

1. GUI 規則原本只允許移入游標或明確工具列控制；提報的 CUA API 沒有 hover-only。歷史 B 的已選 filmstrip 邊緣導覽未列入 Skill，導致候選路徑缺失。
2. B 的工具列曾出現又消失；selected-filmstrip 點擊與可見狀態僅有時序關聯，不能保證成功。toggle、timeout、capture race 與 C viewer 差異仍未知。
3. AX 相同而截圖不同，故 AX 缺失不能否定視覺控制；當次 screenshot 仍須正面證明控制與映射。
4. `notes_evidence.py` 的 v2 已有 screenshot、ax、input_receipt、observation，可保存同角色多個原件與 statement。新增 navigation_receipt role/schema 不是必要條件。
5. `record_post`、`record_media` 同一 scan 各只允許一次；不能為附加 reveal 證據重寫既有細盤。尚未寫入的合法事件可涵蓋既有觀察；已寫入者的 intent 前阻塞先保留私有 task 原件。適用的後續事件必須用自身精確 context 重新封裝，不冒用未知 attempt context。

## 實作分工與界線

| 執行者 | 檔案與交付 |
|---|---|
| Leader | 根因整合、最小回歸、交接報告、逐檔 stage/commit/push |
| Worker1 | SKILL.md、gui-inventory.md、verification-and-recovery.md：一次候選導覽與 transient 停止規則 |
| Worker2 | evidence-template.md、download-and-ledger.md、focused synthetic tests：既有 v2 的證據保存與跨來源保留 |
| Worker3 | 實作與驗證後，以 GPT-6-luna 梳理上下文及撰寫提交訊息；不簽發獨立接受 |

Workers 是同一開發任務的 helper。左側既有 Tester 僅回答提報證據與限制，不被指派新正式角色。

Worker1/2 以 Owner 指定 Codex CLI DeepSeek model/provider/max request 啟動。request 參數、終端顯示、設定與 provider usage 分別記錄，不推論後端身分或成本。原始協作資料只保存在專案私有 task directory。

## 行為規則

- 只有有效授權/前景、同一 viewer/媒體、已選縮圖、可辨識非播放安全邊緣與新映射皆成立，才允許一次 NAVIGATION 候選點擊。
- 不是 hover 替代；主內容、播放控制、時間軸、倍速不碰。無安全區即停。
- 保存 before/input/after、可取得時間來源與 capture 能力，不承諾 atomic 或立即捕捉。
- `TOOLBAR_VISIBLE` 只支援後續當次 gate；`TOOLBAR_NOT_SHOWN` 不代表不存在。
- 曾可見後消失記 `REVEAL_TRANSIENT`；播放/索引/身分/幾何漂移、回傳未知也停。不重複同點、不換點探測、不重開 viewer 重設次數。
- intent 與下載 wrapper、一次派送、chooser、outcome、download-check 的既有要求保留。
- 不增加 CLI/schema/GUI controller、不改帳本或完成語意、不增加 Owner 日常啟動步驟。

## 驗證與交付

執行專案三項最小回歸、focused synthetic tests（納入 notes discover）與 diff 檢查；記錄實際 exit code、數量與適用限制。測試只證明 bytes/context/狀態投影，不證明視覺判讀或 GUI 因果。

真實 C reveal、C/D 下載、跨 Session GUI、混合附件 chooser、獨立 Acceptance/E2E 均待 Owner 依原日常正式 Prompt 交接，維持 NOT_RUN。這些不能由 commit/push 取代。

成果僅提交與推送功能分支；不 merge master、不 force-push。提交訊息含意圖、做了什麼、下一步的建議及真實驗證結果，提交後讀回 body，推送後核對遠端精確 HEAD。

## 授權接續與補強

Owner 明示「請繼續修復」後，Leader 依先前具體提議隔離污染 locator，保留檔案與精確雜湊，原路徑保持缺席；不冒稱精確還原，也不把 active 缺席當成空帳。後續日常入口仍先 lists 查全部帳本。

Worker2 已修 fixture locator 注入、外層 sentinel 與 cleanup boundary，經 Leader 檢查後執行三項最小回歸，皆 exit 0（73/315 tests OK 及 notes help）。Leader 的回歸 runner 比對真實 notes/album 永久記錄與兩個 active locator 的前後檔案清單/bytes/hash，異動即停；此保護不等於照片區或全系統稽核。
