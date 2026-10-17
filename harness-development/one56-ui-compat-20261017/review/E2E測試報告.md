# ONE56 真實介面相容性修正與審查交接

本輪是 Chief review 5557438694 的有限修正延續。原始目標仍為第一本 56 張相簿真正儲存、驗證、VERIFIED 讀回與釋放；成功後，第二本必須另有獨立授權及交易。本輪只完成來源修正、實際建置、待審授權資料包、唯讀檢查及公開審查交接，沒有執行真實備份。

## 本輪事實

- 精確實作 HEAD：`8bebd236d57bb80e39bfca163c67b9cecba1d36f`，父版本 `e35d67c33a82fa1690bc7b13dc17bee9b1fea437`。僅提交已審範圍的 8 個來源及 4 個測試檔。
- 已正常 fast-forward push 至 PR #10 的原分支。PR 維持 Draft，沒有 merge。提交與遠端讀回收據：`private/implementation-commit.json`、`private/push-receipt.json`。
- 公開審查包已發布且逐字讀回：[PR comment 6233460759](https://github.com/s9008129/Line_backup/pull/10#issuecomment-6233460759)。個人群組字串、照片與絕對使用者路徑已遮蔽；原始資料包的雜湊與遮蔽後展示內容有明確區別。
- 實際使用 GPT6Luna/high 進行最小實作，GPT6Luna/xhigh 獨立檢查保留的真實畫面、來源、測試與點擊資料流；Sol 整合了獨立檢查要求的 legacy group 及 multiple-Back 拒絕條件。`final-source-review.md` 為本地有限來源 PASS，不能代替外部 Chief 或正式真機驗收。
- 另依 Owner 要求，實際使用一個 GPT6Luna/xhigh 唯讀梳理上下文並提出白話說明；這不是外部 Chief 審查。
- 提交與實際 smoke 後，獨立 Luna/xhigh 再核對 canonical8檔、closure21檔、native62項、bundle12檔、原始 smoke streams、保護資料及公開審查包，回報有限 pre-live PASS。完整範圍與未執行項目見 `final-runtime-review.md`，SHA-256 `ffac999373eb797bcd01bd88aff946cca1a9f80e521ec9ac0b8457042693511a`。這仍不是 live／外部 Chief PASS。

## 修正及其根據

真正的 LINE 路徑已由舊真機證據證明：相簿名稱 → 獨立格子視窗 → 右上角功能表 → 儲存全部。此輪沒有重做捲動或列表三點選單研究，也沒有重用舊座標送出任何操作。

1. 獨立格子視窗使用明確的 `detail_identity`，以同一 LINE 程序啟動身份、先前列表、仍存在的列表視窗、不同且前景中的詳細視窗、日期與張數綁定。新路徑不要求詳細視窗重現 Back 或群組標題；它只接受零個 Back。原有 Back 路徑仍須群組文字。照片檢視器 `(1/56)`、錯誤或模糊日期／張數、缺少 lineage 與外來程序均拒絕。
2. 正式 `Service.prepare` 的 `click` 取自新鮮、已綁定的相簿名稱 OCR 矩形中心，再交給 hosted adapter。保留原來 2 px 誤差檢查、按鈕重疊拒絕與原生/SCK 綁定。這是來源及測試驗證；本版本的真實 `prepared.click` 尚未派送，不宣稱實機 PASS。
3. CUA 視窗截圖與 SCK 全螢幕的文字位置以既有 affine transform 對應，保留 2 px 殘差限制。先讀 OCR 再驗證身份；原始 `~` 日期文字保留，日期身份可核對 `~／～／〜`。加入同日期但錯位置的 SCK 拒絕案例。
4. 原始真機 AX 捲軸值為 225，原程式卻要求 0..1。最小 Swift 擴充保留同次原生快照的 AXMinValue／AXMaxValue 與原始值，僅在有效、有限且範圍內時換算。沒有推測最大值、捲動步長或新增捲動。
5. Owner 已確認中文 OCR 差異為同一群組並要求保留原備份名稱。只接受新資料包內精確且有雜湊的確認文件，decision／consent 使用同一 ref。原設定、group_key、備份名稱不變，沒有模糊比對或全域別名。

真實根據仍保留於原 `private/owner-list-menu-saveall-20261017-01/`：

- `<PRIVATE_IMAGE_FILENAME_REDACTED>` SHA-256 `2ac55fc03ac9ff3f0969807036f76dfbefea86c1391d975542bd35f3b4b8f6d3`。
- `14-name-target-binding.json` SHA-256 `d270ec435f071270c04a8b57732afc4b118f3eabf81c9de6e56dca505882d16e`。
- `15` 詳細頁原生證據 SHA-256 `37851e3d103ea59a78475106e72979417b44d20f76ec2078cc6a2f4408fd74ce`；歷史列表 window3766 → detail5798，日期 2024/05/27～05/31、56 張。

以上為歷史保留證據，不能充作當前新鮮前景、當前 window ID 或本版本的實機操作結果。

## 實際建置、雜湊及唯讀檢查

| 項目 | 實際結果 |
| --- | --- |
| 21 檔 product source closure | `ff717d721c9132abc2b22c738649e3cc4da34637a86fb794f549695e5cd3ca54` |
| Runtime binding | `cd41ee25387fb784f2aef5158d7dd6bbde27bd44a42d2d42c5a905767b1b6076` |
| 原生 producer | `9ef75efe4b217edd1049a623f26739bc0ea4d5950115e208f704976bb1efdf20`，10,869,296 bytes |
| Entry bytes | `726db9a876619aee66df57f0600f3ef07e40910c3f8285b266397800e12895f1`；ONE56 使用 `runSingleAlbumPilot` |
| ImageIO decoder | `1f5605225b9eae8dd0eea3cedaa089216a8f3674056b3ee226b0f4c10de99bcf` |
| 正式設定 | `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`，未改 |

Native build 使用現有 Xcode Swift6.3.3／SDK26.5，成功 exit0。`private/native-build-final3.json` 保存實際 argv、起訖時間、編譯器／SDK 雜湊、62 個 Package／原生來源 manifest entry 及原始輸出雜湊。所有 62 個來源、canonical 安裝及新精確 HEAD 逐檔一致，見 `private/native-exact-head-check.json`。舊建置和編譯錯誤仍保留，沒有改寫成成功。

聚焦測試：detail 5/5、adapter 42/42、Python observations 20/20、authority 11/11；語法與 diff 檢查通過。原始 stdout／stderr、exit、時間及指令保留在 `private/focused-tests-03`、`-04`、`-05`、`-06`；detail 最終為 -06，adapter 最終為 -05。較早失敗如實保存；最早未捕捉的 detail 輸出未事後重建。這 78 項只是 ENABLER，沒有 full CI PASS 宣稱。

Canonical root 只覆上經 preimage、exact commit、readback 檢查的 8 個來源檔；沒有覆蓋其他 dirty state。canonical Git HEAD、branch、index 未改，測試檔留在 isolated worktree。`canonical-source-staging.json` 記錄安裝與原始 preimage。

新 immutable bundle：`private/authority-bundles/ONE56-20261017-8bebd23-PENDING-c6147d8f/`。原始 canonical grant、ledger、init receipt、觀察計數、Owner／task 身份不變。新包的 decision／review／readiness／contract／runtime／consent／alias ref 在同一 bundle；gui_ledger 指向原 ledger。最大一相簿、一 lifecycle、一次原始 Save All、一次 chooser confirmation。review 明列 PENDING，readiness／live authority 為 false；沒有假 review 或重開舊 grant。

實際唯讀 smoke 見 `private/actual-readonly-smoke-01/receipt.json`：

- Python 正式 authorizer：`PROJECT_IMPLEMENTATION_REVIEW_REQUIRED`，符合待審預期。這是拒絕 gate 生效，不能稱 live authorization PASS。
- 真正新 producer `runtime-preflight` exit0；AX／screen capture permissions true，GUI inputs0、LINE observation false、native controller admission false。
- 真正新 producer `native-context` exit77，在 authorizer 拒絕後沒有進行原生觀察。
- State revision35／SHA `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6` 前後一致。沒有 writer、intent、ledger initialization 或 GUI 輸入。

## 保留與未知

`preservation-before.json`、`preservation-after.json`、`private/preservation-comparison.json`：245 個已列管保護檔逐檔 SHA-256 一致，包含 239 張歷史 VERIFIED 照片；八個原始 authority 文件一致；14 段範圍外原有 tracked dirty diff 一致。未宣稱完整 untracked tree 都有基線。原 ledger SHA `08aa18e42bfee7a8e4d0529bac5b793d830efc1127794dac4baa8f4bdb9864e2` 不變；歷史 `PAIR-A-DISCOVERY_SCROLL_1_BEFORE=2/2` 不變。

第一個未滿足的真實 Gate 仍是新精確版本的外部 Chief implementation review。另有明確、未解決的後續真機相容性：原始 detail AX 只有視窗／交通燈按鈕，沒有既有 ellipsis locator 要求的 AXButton；popup 原生 AX 也沒有既有 row locator 要求的 menu items。舊 hosted 截圖未涵蓋完整 popup，occlusion 檢查可能拒絕；舊 Escape 同時關閉 menu 與 detail，既有 calibration 卻期待仍在同一 detail。此次 B1/B2 範圍沒有修這些選單機制，不能宣稱 live-ready，也不能先消耗唯一 lifecycle／intent 再撞已知問題。

新 HEAD 的 [GitHub CI run39029557378](https://github.com/s9008129/Line_backup/actions/runs/39029557378) 實際為 failure：Deterministic Swift contract 在 `ProjectBackupBindingTests.swift:15` 的多個測試遭遇既有的 XCTUnwrap nil 錯誤，headed job 為 skipped。原始 failed log 及 exact head metadata 保留於 `private/github-ci-failed.log`、`private/github-ci-readback.json`。此範圍外問題未在本輪修理，沒有 full CI PASS。沒有 native Harness controller admission 證據，不以本地 review 取代正式 controller 或外部 Chief。沒有本輪即時 LINE screenshot、chooser、下載檔案或 VERIFIED 收據。

## Gate delta 與下一步

`GOAL_GATE_DELTA`：來源 B1/B2 修正與測試、本地獨立來源檢查、真實 native build、exact hashes、新待審 bundle、實際唯讀拒絕、保護比對、公開 B3 審查交接已完成。Save All／chooser／56 files／ImageIO／VERIFIED／release／第二本均沒有新增產品 PASS。

`INFORMATION_GAIN`：來源可依真實獨立 grid 與名稱點位表達；早期 OCR 次序／日期分隔符／SCK 座標問題已修；授權讀取到必需的外部 review gate；下游選單 AX／popup／Escape 不相容已明確保留。不是以重跑合成測試代替真機結果。

`NEXT_AUTHORIZED_REAL_STEP`：先取得外部 Chief 對此 exact HEAD 及已公開 runtime 證據的真實判定，依其 bounded disposition 處理已知選單相容性；如涉及來源變更，重綁實際來源／runtime 並重新精確審查。進入 transaction 前須取得新鮮 LINE 前景交接及真正可用的 menu observation/control 證據，再檢查 duplicate、目的地、Owner 與 intent。Owner 原本一次完整 56 張備份授權仍有效，不重複索取同範圍 consent。

舊定位／raw225 為已保留真機根因，不重啟捲動研究、不重置額度。程式修正各次實際錯誤與收據仍在原目錄；末段 independent review 補上的兩個 guard 均有資訊增益。沒有將換 worktree／模型當作重置根因額度。

本報告由本輪 Sol 主控整合；Luna 實作及獨立檢查已回報 Sol。外部 Chief 只收到公開待審包，尚無新核准。Planner/controller 正式 admission 未有證據，不宣稱已完成。

```text
PRIMARY_OUTCOME_STATUS=NOT_ACHIEVED
IMPLEMENTATION_STATUS=COMPLETE_FOR_BOUNDED_B1_B2_SLICE
CORE_ACCEPTANCE_STATUS=LIVE_NOT_RUN
REQUIRED_VERIFICATION_STATUS=INCOMPLETE
INDEPENDENT_ACCEPTANCE_STATUS=LOCAL_SOURCE_PASS_EXTERNAL_CHIEF_AND_LIVE_PENDING
TASK_CLOSURE_STATUS=PENDING

NEW_HEAD=8bebd236d57bb80e39bfca163c67b9cecba1d36f
DETAIL_GRID_FIX=SOURCE_AND_FOCUSED_TESTS_PASS_LIVE_NOT_RUN
ALBUM_NAME_CLICK_VALIDATION=SOURCE_BINDING_PASS_LIVE_PREPARED_CLICK_NOT_RUN
AUTHORIZE_ONE56_SMOKE=EXPECTED_PROJECT_IMPLEMENTATION_REVIEW_REQUIRED_NATIVE_PREFLIGHT_0_NATIVE_CONTEXT_77
CHIEF_IMPLEMENTATION_REVIEW=PENDING_NEW_EXACT_SOURCE_REVIEW
ALBUM_A_SAVE_ALL=NOT_RUN_DISPATCH_COUNT_0
ALBUM_A_FILES_VERIFIED=NOT_RUN
ALBUM_B_CANDIDATE=NOT_SELECTED
ALBUM_B_SAVE_ALL=NOT_RUN_SEPARATE_AUTHORITY_REQUIRED
ALBUM_B_FILES_VERIFIED=NOT_RUN
FIRST_REAL_BLOCKER=EXTERNAL_EXACT_SOURCE_REVIEW_PENDING_WITH_KNOWN_MENU_LOCATOR_INCOMPATIBILITY
NEXT_ACTION=EXTERNAL_CHIEF_REVIEW_PUBLIC_PACKET_THEN_BOUNDED_REAL_MENU_COMPATIBILITY_DISPOSITION_BEFORE_TRANSACTION
```
