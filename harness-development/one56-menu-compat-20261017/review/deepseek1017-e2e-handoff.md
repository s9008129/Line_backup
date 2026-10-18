# DeepSeek 1017 Independent E2E Handoff

本檔是 Owner 原始目標與固定驗收條件的交接，不是執行 grant 或預設判定。只供 Owner 啟動的全新、獨立 Codex CLI Session 使用，模型為 Ollama Cloud BYOK `deepseek-v4.1-flash:1017`。記錄實際 Session／provider／model；未能確認實際模型或缺少受支援的 Mac CUA 工具時回報 BLOCKED，不冒稱已使用指定模型。Sol 不啟動該 Session，也不代操作或代寫結論。

## 目標與固定 AC

Owner 要求兩本不同、尚未備份且 eligible 的 LINE 相簿，實際 Save All、下載原圖、逐檔驗證與 durable VERIFIED 讀回。僅開啟選單、點擊、合成測試或 GUI 成功訊息不能滿足驗收。

| AC | 必要的真實證據 |
| --- | --- |
| AC0 執行身份 | 精確外部 Code Review 核准；同一已安裝 source／producer／runtime／grant；Owner 當次 LINE 前景交接；唯一 GUI 操作者為本 DeepSeek Session |
| AC1 A56 身份與資格 | 當下群組／process／window lineage、2024/05/27～05/31、56張；排除歷史 VERIFIED、人工65張及不明 intent；原備份群組名稱保留 |
| AC2 A 正式交易 | 核准入口的校準、2px／u+4／16×16安全條件、獨立空目的地、writer／durable original intent／at-most-once；Save All 最多一次，真實 chooser 與精確目的地 |
| AC3 A 原圖 | 獨立 inventory 正好56張穩定原始圖片；逐檔 SHA-256、完整 ImageIO 解碼；無空檔／partial／未知檔／symlink 等未解異常；不把 GUI 成功當成檔案 PASS |
| AC4 A 正式狀態 | 真正 VERIFIED commit/readback，對應 fingerprint／檔案證據與目的地，stop／release 成功 |
| AC5 B | A 完成後返回列表，至少一次真實向下捲動並保留前後位移證據；辨識不同且未備份的 B，張數以新鮮來源為準；取得新的獨立 B grant／入口／交易，再重複身份、一次派送、獨立空目的地、全檔驗證、VERIFIED/readback/release |
| AC6 保全與獨立判定 | 原239張歷史及既有 ledger 歷史受保護；不選人工 2024/06/02～06/07、65張，不重選 A；每項由自己的原始畫面／AX／SCK／檔案／狀態證據判定，保留副作用、未知與失敗 |

## 精確版本與目前尚缺的綁定

下列是本檔準備時的實際來源快照，不是可執行批准。正式 E2E 必須由 Owner 發放外部核准的完整40碼 execution Commit／review URL 與有效新 runtime/grant 身份；不得用浮動 branch 或此處未核准快照啟動。交付本檔的完整 Commit 列於同次 PR／Owner 交付訊息，文件更新不會使來源自動獲准。

| 項目 | 當前已記錄身份／狀態 |
| --- | --- |
| repository／PR | `s9008129/Line_backup`／Draft [#10](https://github.com/s9008129/Line_backup/pull/10) |
| 已完成的限定來源審查 | [Chief5561111099](https://github.com/s9008129/Line_backup/pull/10#pullrequestreview-5561111099)，reviewed HEAD `13b547aecf9204762b53c984ca3c6c09064cb569`：M5/M6=`ACCEPT_SCOPED_SOURCE`，transaction=`CHANGES_REQUIRED`；不是完整 `APPROVE_IMPLEMENTATION` |
| 本次變更前候選快照 | `13b547aecf9204762b53c984ca3c6c09064cb569`；正式 execution Commit 尚未發放 |
| candidate source closure | `be0c248ab231fd76e1e8fc7a42800391bc3134d19e12a29a6da676c894856b1d` |
| installed source closure | `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54`；與 candidate 不同 |
| actual native producer SHA-256 | `9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20` |
| ImageIO decoder SHA-256 | `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf` |
| 舊 pending bundle | `harness-development/line-two-album-pilot-20261014/private/authority-bundles/ONE56-20261017-8bebd23-PENDING-c6147d8f/` |
| 該 project-grant.json SHA-256 | `93dc5640e85512e49e50fe0d6613c3a15bd9c9a192315a1715dea5325b0149c7`；不可作為 candidate 有效授權 |
| 該 runtime-binding SHA-256 | `cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076`；只綁舊 installed 來源 |
| Code Review／fresh readiness／B grant | 尚未具備；不得預填批准 |

## 入口、目的地與隔離證據

- `project_root` 僅使用 Owner 在新 Session 明確交付的原 canonical `Line_backup` 主目錄。從該 root 讀 `config/line_backup_config.json`、`state/backup_state.json` 與原 ledger；不搜尋其他 registry、不複製 state、不改 config 群組名稱、不初始化 ledger。隔離 worktree 可唯讀查受審來源，不可混用 candidate sourceRoot 與 canonical projectRoot。
- A 既有入口為已安裝 `harness-development/line-two-album-pilot-20261014/mac_runtime.mjs` 的 `createMacRuntime(...)` → `runSingleAlbumPilot()`，底層 `two_album_entry.mjs` 同名入口。只在精確核准且 grant 綁定的 runtime 上執行；先檢查持久狀態再決定是否可執行，不把唯一 lifecycle 當觀察試跑。不要呼叫 `runPilot()` 自動啟動 B/C1；B 必須另行交付有效的獨立入口／grant。
- 備份目的地只能由該 root 的 config `backup_root` 派生，經核准 `prepare` 固定並讀回獨立空目的地。A／B 目的地尚未建立，不能猜路徑、沿用65張目錄或先寫照片。現有 config 上限為每次1本；A／B 分開授權，檔案穩定取樣／逾時以綁定 config 為準。
- 原始 E2E 證據只寫到 Owner 指定的隔離目錄：`<OWNER_PROJECT_ROOT>/harness-development/one56-menu-compat-20261017/private/independent-e2e-deepseek1017/<ACTUAL_SESSION_ID>/`。正式程式自己的既定證據／狀態寫入僅由核准入口處理，不手改 grant／ledger。不要寫入產品、原始測試標準、AC 或歷史資料。公開報告遮蔽照片、人名／群組、授權內容與個人絕對路徑，保留本機原始 bytes／SHA。
- Owner 本機必要環境索引在 `harness-development/one56-menu-compat-20261017/private/deepseek-e2e-role-20261018-01/environment.json`（未上傳 GitHub，僅含實際路徑與待綁定身份，不含 BYOK key）。可查受審來源、真實 provider review、有效 grant／state，以及 `private/formal-route-preflight-20261018-01/` 的原始命令輸出／畫面。舊截圖只作來源證據，不能重用為當次座標／身份／前景交接；不要導入 Sol 對話推理、Implementer 自評或過往 PASS 當結論。

## 安全停止與回報

開始前必須自行核對外部核准與執行綁定。缺有效 review／runtime／grant／工具／當次前景、身份或目標不明、2px等正式校準不能成立、目的地異常、無法取得唯一 writer，均停止相關輸入並記錄首個 literal refusal。不得因換成 DeepSeek 而繞過任何 guard、消耗觀察配額試探、修改交易條件或重新執行已停止的 NCC／shadow-click 研究。

每次 Save All 前後記錄持久 intent／reservation、實際 invocation／receipt、時間、source identity、畫面與 AX/SCK refs／SHA。結果不明即停止、不重送；換 Session、逾時、未見 chooser 也不例外。副作用或 foreground 中斷時保留證據。找不到合格 B 時回報 `NO_ELIGIBLE_TARGET`，保留 A 成果，整體兩本目標未完成。

獨立重讀實體檔案、逐檔 SHA-256／完整解碼、VERIFIED receipt／state readback；不得只採信 producer 的成功摘要。寫完整 `E2E測試報告.md` 與 manifest（相對及本機絕對證據路徑、hash、實際步驟、未知、失敗、副作用），交回 Sol 整合公開與 commit/push；不由 Sol 代寫判定。逐項填 `PASS|FAIL|BLOCKED|NOT_RUN`，不要預填 PASS：

```text
ACTUAL_SESSION_ID=
ACTUAL_PROVIDER_AND_MODEL=
IMPLEMENTATION_COMMIT=
EXTERNAL_CODE_REVIEW=
SOURCE_PRODUCER_RUNTIME_GRANT_IDENTITIES=
LINE_FOREGROUND_HANDOFF=
AC0= ; AC1= ; AC2= ; AC3= ; AC4= ; AC5= ; AC6=
ALBUM_A_SAVE_ALL_DISPATCH= ; ALBUM_A_FILES= ; ALBUM_A_SHA256_FULL_DECODE= ; ALBUM_A_VERIFIED_RELEASE=
ALBUM_B_IDENTITY= ; ALBUM_B_GRANT= ; ALBUM_B_SAVE_ALL_DISPATCH= ; ALBUM_B_FILES= ; ALBUM_B_SHA256_FULL_DECODE= ; ALBUM_B_VERIFIED_RELEASE=
HISTORICAL_239_PRESERVED= ; MANUAL_65_EXCLUDED= ; CANONICAL_HISTORY_INTEGRITY=
INDEPENDENT_E2E_VERDICT=
FIRST_ACTUAL_FAILURE_OR_BLOCKER=
EVIDENCE_MANIFEST_AND_SHA256=
NEXT_ACTION=
```
