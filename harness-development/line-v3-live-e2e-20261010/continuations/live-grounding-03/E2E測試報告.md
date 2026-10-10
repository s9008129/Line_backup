# E2E 測試報告 — live-grounding-03

更新時間：2026-10-10T14:07:31.085Z（UTC）  
Task：`TASK-20261010-line-v3-live-e2e`  
Plan：`harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan.md`，SHA-256 `001b90861631fe27b0d21ec871be5fc19446bf3070e88bb116350a0f3690708c`  
Handoff：`harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/handoff.md`，SHA-256 `d44fa1eb21fd15b50fcc2131c5a5499be69ce3b40bbf69b128f6f3cc8ee4df03`  
Contract：`harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan-contract.json`，SHA-256 `d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219`  
Project root：`/Users/hsiaojohnny/Documents/ChatGPT/Line_backup`

## 本輪結果

離線實作與驗證已取得部分進展：Swift 全套 329/0、Python 與 Node 必要 suites 通過；新 runtime binding、兩份 v2 grants 及 producer binary 的雜湊／membership／quota 驗證也通過。完整兩本 LINE 相簿 E2E **未執行**。目前沒有使用者明確交還 LINE 前景的紀錄，且 native CUA frame／AX analyzer 尚未以當下真實畫面完成 grounding；因此沒有點擊、滾動、Save All、chooser confirmation、下載或 state mutation。`G_CATALOG`、`G_MENU`、`G_FIRST`、`G_SCROLL`、`G_SECOND` 均未通過；獨立 Acceptance 尚未執行。

本報告引用的機器證據均在 workspace 內，並列 relative path、absolute path、bytes 與 SHA-256。完整測試收據索引見 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-offline.json`；授權綁定見 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-auth.json`；state／preservation 觀察見 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/state-continuity.json`、`harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/preservation.json`。

## 變更與邊界

本輪在核准路徑內新增／更新 non-menu frame support、native capture timing、grounded classifier、chooser locator、session runner、下載開始觀察、v2 grant source/runtime binding，以及 GUI ledger 類型。主要來源包括：

- `rev28/Sources/Rev28Core/Perception/OcrEngine.swift`：non-menu surface geometry、frame bounds、intersection、uncertainty 與 safe-margin fail-closed checks。
- `rev28/Sources/Rev28Core/Sensor/FrameCapture.swift`、`rev28/Sources/rev28ctl/main.swift`：full-display capture timing、native frame-support 命令與 sidecar/manifest 產出；producer 不建立 GUI input。
- `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/live_classifier.mjs`、`chooser_locators.mjs`、`live_runner.mjs`：同一 capture 綁定、嚴格 17-key frame、typed chooser phase、下載 evidence 與 bounded scroll checks。
- `src/line_backup_batch/observations.py`、`service.py`、`store.py`、`cli.py` 與 `scripts/line_backup_cua_adapter.mjs`：live v2 phase/evidence validation、fresh empty baseline、shared quota 與 runtime source closure。
- `rev28/Tests/Rev28CoreTests/FrameSupportTests.swift`：把 clipping fixture 寬度由剛好 100 改為 101，以確實超出 100px frame；這是測試資料修正，不是降低檢查。

授權綁定在最終來源碼完成後重建。`Store.snapshot()` 觀察到 source SHA `6acdec34fbfd163e560bbe8ec93661a64a4bd8fcb24f0ced9e27971e99b69064`、config SHA `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`、state revision `35`。兩個 grants 分別綁定 owner `live-grounding-03-g1`、`live-grounding-03-g2`，各自保留雙 lifecycle 共用 quota；`acceptance_evidence` 為 `null`，因 Acceptance 尚未發生。驗證只證明本地 bytes／契約／權限 shape，沒有建立 native Harness admission。

授權程式修正的關鍵片段：

```python
def validate_runtime_binding(reader, grant):
    from .observations import artifact
    from .store import SOURCE_PATHS
```

且 Swift membership 遞迴將 `NotADirectoryError` 視為 leaf file，才可建立完整 Swift source list。這兩項錯誤由 `grant-validation-02` 暴露，修正後 `grant-validation-03` 通過。

## 實際執行順序與離線驗證

所有 test stdout、stderr、exit code、bytes 與 SHA-256 留在 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence`。`run_command.py` 的 invocation 記錄 argv；下表補列實際環境：

| 檢查 | 命令／環境 | 結果與證據 |
|---|---|---|
| Node syntax | `/opt/homebrew/bin/node --check` adapter、classifier、locators、runner 和 tests | PASS；最新 receipts：`node-check-adapter`、`node-check-classifier`、`node-check-locators`、`runner-syntax-04`、`classifier-syntax-01`、`node-check-test`。 |
| Node suites | `/opt/homebrew/bin/node --test tests/test_cua_adapter.mjs`；`--test harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/checks/test_live_classifier.mjs`；`--test harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/checks/test_live_runner.mjs` | PASS：18 + 3 + 4 tests。Receipts：`adapter-suite-04` stdout SHA `deb797edf09e3047df6ddf62ff4852037e70135d51e67986041df3ed15f6db58`；`classifier-suite-04` stdout SHA `eb4aa6b4171eed6e750947a4648c051b0868002601303ca61082bf5af08cf81b`；`runner-suite-03` stdout SHA `843c6b5b3ae6a097739d6c14d6927778373ddc6bc904cc371ce41913b9a352f9`。 |
| Python batch | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 LINE_BACKUP_BATCH_TASK=harness-development/line-v3-live-e2e-20261010 LINE_BACKUP_INSPECTION_TEST_ROOT=harness-development/line-v3-live-e2e-20261010/fixtures /Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3 -B -m unittest discover -s tests -p 'test_batch_*.py' -v` | PASS：70 tests；receipt `batch-python-06`，stderr SHA `0d0ceb1ad142485d043005d256069791beaa61906c6e55b78d8136960d2c1533`。 |
| Python binding | 同環境，`-p test_project_binding.py` | PASS：31 tests；receipt `binding-python-04`，stderr SHA `4b304b2b1b987821f9ec2f2faf6037d072ec04464e65767f3c2db02d0535bad7`。 |
| Python transaction | 同環境，`-p test_transaction_core.py` | PASS：5 tests；receipt `transaction-python-02`，stderr SHA `55f760c20d3525ae53c2a120e64e3a39d3fe649e75c3640f06d1ed72201badbe`。 |
| Authority regression | 同 interpreter；`LINE_BACKUP_BATCH_TASK=harness-development/line-v3-live-e2e-20261010`、fixture root `harness-development/line-v3-live-e2e-20261010/fixtures`；`-p test_batch_authority.py` | PASS：24 tests after final CLI fixes；receipt `auth-suite-02`，stderr SHA `a930116d5626303c2c8decff8ca54afa1a7988084af4b4b294a7030e3dba745a`。 |
| Swift full suite | `/usr/bin/swift test --package-path rev28 --sdk /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk --scratch-path /Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/swift-build-26.5`; module cache、clang cache、TMPDIR 均在 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03`，fixture env `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/fixtures/swift-inspection` | 最終 PASS：329 tests / 0 failures；receipt `swift-full-suite-03`，stdout SHA `d1aaa94f715d456c1908cd481315a0f46397a76e4b7a2b47cdca8227cba4dda6`，stderr SHA `3b955a3a547eaac6435e0581b09d275b3eeca934e51b0edbed773117b17c596e`。 |
| V2 grants | fixed Python runtime；呼叫 `authorize(root, grant, fixture=False, operation='begin')`，對兩個 owner 各驗一次 | PASS：contract/source/config/runtime membership、producer bytes、authorization／waiver／user decision、quota 與 sensor scope；receipt `grant-validation-03` stdout SHA `d68adc625135c1fc547d9bbd9d08609439a4ae5d9b30e0b8f51babaad364679b`。 |
| Producer startup | 啟動 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/bin/rev28ctl` 無參數，檢查預期 usage 輸出與 exit 64 | PASS（process-start diagnostic only）；receipt `producer-cli-preflight-01` stderr SHA `7663b1a47cc0efab613a6b8ef5857db07e81619251aa367926bbb53dcb7ade07`。這不等於 live capture/preflight PASS。 |

`/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3` 是 `/Users/hsiaojohnny/.codex/harness-runtime/4.8.0/.venv/bin/python3`；`/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk` 是 `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk`。完整 invocation/environment receipts見 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-offline.json`。

## 失敗嘗試與新資訊

失敗原始輸出都保留，沒有覆寫：

| 嘗試 | 實際結果／得到的新資訊 | 後續 |
|---|---|---|
| `swift-full-suite-01` | 編譯錯：grant `Any?` 比較型別、throwing `resourceValues`、menu receipt 缺 `manifestReference`；測試未執行。stderr 87,240 B，SHA `9d823d2abaa039af878e847d309bc020dedd4557e5e23ed7dc807f7390eb0e65`。 | 修正 Swift 型別／錯誤處理並補 menu manifest reference。 |
| `swift-full-suite-02` | 編譯成功，329 tests 中 17 failed。16 項因漏傳 `LINE_BACKUP_INSPECTION_FIXTURES`；1 項測試座標 `[0,0,100,40]` 實際剛好落在 frame 內，並未裁切。stderr SHA `281ca32744e89aa6cb5f168cd4bac9813a70a40de9713f219963fd5634dad149`。 | 綁定 fixture 環境，並將 clipping test width 調為 101；第三次 full suite 全通過。 |
| `auth-suite-01` | 測試啟動缺 `LINE_BACKUP_BATCH_TASK`；無產品斷言失敗。 | 補齊核准 task／fixture env，`auth-suite-02` 24/0。 |
| `grant-validation-02` | v2 grant 實際預檢暴露未匯入 `artifact()`；修正後再揭露 Swift membership traversal 未攔截 `NotADirectoryError`。 | 兩處修正、source digest／binary／runtime-binding／auth/grants 重新凍結，`grant-validation-03` PASS。 |
| 早期 Node/Python receipts | `classifier-suite-01` boundary ordering、`runner-suite-01` timestamp equality、Python fixture env/root 與一個 fixture `Path` import 問題；每項新結果後都有修正。 | 最新 suites 為 Node adapter/classifier/runner 18/3/4 PASS、Python 70/31/5 PASS；舊失敗收據仍保留。 |

`attempt-ledger.json` 記錄三次 Swift full-suite reservation：兩次失敗均消耗額度，第三次通過；沒有再啟動 Swift build/test。`grant-validation-03`、`auth-suite-02` 是後續針對新 runtime source binding 的有界回歸檢查。

## Preservation、副作用與差異

- state SHA `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6`、revision `35`，與凍結 Plan baseline 相同；config SHA `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362`，與 Plan baseline 相同。Schema-3 snapshot/history validation PASS；2 runs、2 verified albums、active batch/writer/context lock 均 null。
- Branch `v43-ab/codex-rev28`、HEAD `77b83c4eb8f9bafdf86fda625e6ecd3a85b32ddb`、Git index SHA `ea9eda76bebcec2c39f9d99ed08ef64ea7fcf466ba020660fd37a04f8a2bbdae` 均未改；沒有 stage、commit、push。原有大量 dirty/untracked 工作沒有 reset/checkout。
- `harness-development/line-v3-live-e2e-20261010/gui-ledger.json` 在 frozen baseline 不存在，舊報告已記錄 0 GUI reservations。現在按 Plan 建立正式 ledger，`entries=[]`、`cap=1000`，目前 GUI input 仍為 0。
- 本輪沒有任何 CUA/LINE input、Save All、chooser、下載、scroll 或備份路徑寫入命令；因此 backup files 未由本輪操作改寫。內容逐檔 inventory 未執行，不能宣稱內容解碼／整體備份驗收。
- Preservation 檢查發現 14 個 baseline 之外的 untracked files 落在 allowed paths 外：task-root `evidence/` 8 個檔案、`src/.../__pycache__/` 6 個 `.pyc`。它們出現在測試／Store snapshot 之後；歸因於 batch tests 和一次未帶 `-B` 的 snapshot 是有時間與路徑支持的推論。檔案未刪、未移、未再改；逐檔 bytes/hash 見 `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/preservation.json`。因此 `G_PRESERVE=PARTIAL`，不掩蓋範圍偏差。

這是本輪的實際副作用與 scope issue。後續不得再執行會往 task-root `evidence/` 寫入的 Python suites，除非先由 Planner 凍結一個在允許路徑內的 test artifact root；不得自行清除上述文件。

## Gate 狀態與未執行項目

| Gate | 本輪狀態 | 證據／原因 |
|---|---|---|
| `G_PLAN_REVIEW_WAIVER` | PASS（waiver） | `plan-review-waiver.json` 綁 contract；Plan Review 本身仍是 `WAIVED_NOT_RUN`，不是 reviewer PASS。 |
| `G_AUTH` | PASS（local） | `evidence/g-auth.json`；native Harness admission 未執行。 |
| `G_OFFLINE` | PASS | `evidence/g-offline.json`；只適用離線檢查。 |
| `G_MIGRATION` | PASS（continuity） | `evidence/state-continuity.json`；未再次 migrate，原 state bytes/history 不變。 |
| `G_CATALOG` | BLOCKED | 缺當下 LINE full-display/AX capture；沒有候選卡證據。 |
| `G_MENU` | BLOCKED | 未觀察真實 menu row／SCK popup pair／latency。 |
| `G_FIRST` | BLOCKED | Save All、chooser、download、content verification、VERIFIED/readback 全部未執行。 |
| `G_SCROLL` | NOT_RUN | first owner 未完成釋放；沒有真實 scroll before/action/after。 |
| `G_SECOND` | BLOCKED | first transaction/scroll 未完成；第二本全流程未執行。 |
| `G_PRESERVE` | PARTIAL | state/config/index 保持不變，但有 14 個 allowed paths 外新 untracked files，見 preservation evidence。 |
| `G_REPORT` | PASS | 本報告、`progress.md`、ledger 與 evidence index 已落檔。 |
| `G_ACCEPTANCE` | NOT_RUN | 仍需未參與本候選實作的 Acceptance Reviewer；helpers 不算。 |
| `G_DELIVERY` | PARTIAL | 離線程式與資料已保存；完整 E2E、required gates 與 Acceptance 未完成。 |

另有 native admission/stage publication/CONTRACT/RESULT validation 均 `NOT_RUN`；本地 schema check 只驗結構，不等同 controller PASS。Planner handoff 尚未完成，因本環境沒有 controller-backed Planner stage。

## 阻塞與下一步

1. 需要使用者把 LINE app 切到前景，開啟「旻謙允禎成長日記」相簿列表並明確回覆「前景已交還」。拿到交接後，第一個動作只會是一次新鮮唯讀截圖＋AX 擷取，用來驗證實際 capture shape；不會在該步點擊、滾動或下載。後續每個 GUI 動作仍會先公告精確動作並取得當次前景交接。
2. 目前分類器仍需要用真實 CUA capture 確認 analyzer/frame references 的實際結構；沒有該觀察就不能接上真實 UI 或宣稱 live grounding。
3. 14 個範圍外 untracked outputs 維持原位；下一輪 Planner 必須決定只調整測試輸出 root 至 `$CON`，以及如何處理已存在 outputs。不得由 Implementer自行刪除或移動。
4. 真機資料補齊後，才可執行 first transaction → release → downward bounded scroll → second transaction。最後再交給獨立 Acceptance；其審查不是本輪額外獨立 Plan Review。

### 證據索引

| 證據 | Relative path | Absolute path | Bytes | SHA-256 |
|---|---|---|---:|---|
| g-auth.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-auth.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-auth.json` | 8114 | `56567d6cad77be998a5c10952920ac36f5e3421e48c53e152ff59ec5ea668a38` |
| g-offline.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-offline.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/g-offline.json` | 50807 | `8b091b837286e27356743e722cc23b44c76a06a80945c7b09e63711c02eefacb` |
| state-continuity.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/state-continuity.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/state-continuity.json` | 1206 | `638bedbb7b41f91328703a8ff3891f983d36ff8fe0aad46feae7fca73f543702` |
| preservation.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/preservation.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/preservation.json` | 9109 | `e735a2f44b28bb988e74895af0f4dd0883c1d60729720d0d4f19a5083d375207` |
| swift-full-suite-03.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.receipt.json` | 685 | `17f40c3c70ebcdf9ae203c3f7df7b98762ed76e119dc5604339363bb8b69d01f` |
| swift-full-suite-03.stdout | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.stdout` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.stdout` | 85955 | `d1aaa94f715d456c1908cd481315a0f46397a76e4b7a2b47cdca8227cba4dda6` |
| swift-full-suite-03.stderr | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.stderr` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/swift-full-suite-03.stderr` | 298 | `3b955a3a547eaac6435e0581b09d275b3eeca934e51b0edbed773117b17c596e` |
| batch-python-06.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/batch-python-06.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/batch-python-06.receipt.json` | 671 | `517d2494bf29ab8bf796b02043ac7640f1b5bb8072b020aaed06ae76a6abc318` |
| batch-python-06.stderr | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/batch-python-06.stderr` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/batch-python-06.stderr` | 10460 | `0d0ceb1ad142485d043005d256069791beaa61906c6e55b78d8136960d2c1533` |
| adapter-suite-04.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/adapter-suite-04.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/adapter-suite-04.receipt.json` | 673 | `414c7ce936ae5a757309f9655b4afacda81d80bce5498f43c431c9ee80855441` |
| classifier-suite-04.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/classifier-suite-04.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/classifier-suite-04.receipt.json` | 681 | `a078424547f6bd5b7bc24b6de2453bf2f68644db074d07ba0579e4c6af620a68` |
| runner-suite-03.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/runner-suite-03.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/runner-suite-03.receipt.json` | 669 | `b141cfaaa9de9d96b17931eac7d9e1ed3de50e68b3e033f64b9488427b75c04f` |
| auth-suite-02.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/auth-suite-02.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/auth-suite-02.receipt.json` | 664 | `dfba63ae7cc38328525a3e65269a2fb50442b3a1a3c14c370843054296186993` |
| grant-validation-03.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/grant-validation-03.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/grant-validation-03.receipt.json` | 681 | `2a5eecb54de879ab6c2e5dc0cbfb9e4eac2cfc718aba2f7950886ef547110f67` |
| producer-cli-preflight-01.receipt.json | `harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/producer-cli-preflight-01.receipt.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/evidence/producer-cli-preflight-01.receipt.json` | 699 | `0b5824836a62a1be2bc2a590723c6f554aa99df5a902c512ab5520c9c779a570` |
| state source | `state/backup_state.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/state/backup_state.json` | 252115 | `455050110dbdcfcafda4a712a36dfcf840efcdfaf828cd3d6201107c93888ee6` |
| config source | `config/line_backup_config.json` | `/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/config/line_backup_config.json` | 384 | `5e4f769ddf3cb359f6810f80770eddc0643e95e95e03ce6f2d74699c4d6df362` |
