# AGENT-RESUME-P0-20261022：M2 legacy CI B 驗證報告

- 日期：2026-10-22（Asia/Taipei）
- Plan revision：v2.1；SHA-256 `4ba9be2daf887aa8a65a0255e337da5bff8d0ae5aa2d5ada13990f5c85b76502`
- Handoff SHA-256：`d95c73fca8abcb631a2af56f1c376bbe4d899556eb521f425570038010326d9b`
- Owner 決策：`EXTERNAL_PLAN_REVIEW=OWNER_WAIVED`。本次豁免只涵蓋 Plan Review；External Code Review 與獨立 E2E 仍為必要關卡。
- CI B base：`1b9a010aeba2e75a406d842be123d7251501548c`
- CI B branch：`implement/agent-resume-ci-20261022`
- CI B 產品／測試 HEAD：`e0b77857eb77536329f9565bf65fa8087b73873d`
- CI B Draft PR：[PR #33](https://github.com/s9008129/Line_backup/pull/33)
- Feature 產品驗證來源維持 `cdf92ce94d6fb67080eadda0d4d182b84f83e0cc`；兩個 HEAD 的綠燈不得互相轉移。

## 1. 結論與狀態

本輪只處理 Plan §5.3／§9 的 legacy CI B 修復。已從目前 checkout 的 Python producer 實際產生六組公開合成 fixture，修正 Swift inspection consumer 的來源集合與 `manual_archive_match` 契約漂移，並在隔離暫存目錄完成 fixture、聚焦 Swift、完整非 Vision Swift、adversarial 與 historical replay 驗證。沒有操作 LINE、截圖、AX、OCR、Save All、Chooser、下載或真實照片。

```text
PRIMARY_OUTCOME_STATUS=PLANNED_NOT_IMPLEMENTED
IMPLEMENTATION_STATUS=M0_M1_OFFLINE_COMPLETE_M2_CI_B_COMPLETE
CORE_ACCEPTANCE_STATUS=PARTIAL_OFFLINE_ONLY
REQUIRED_VERIFICATION_STATUS=FEATURE_CI_PASS_LEGACY_CI_PASS
INDEPENDENT_ACCEPTANCE_STATUS=NOT_RUN
TASK_CLOSURE_STATUS=OPEN
EXTERNAL_PLAN_REVIEW=OWNER_WAIVED
EXTERNAL_CODE_REVIEW=NOT_RUN
FORMAL_TWO_ALBUM_AUTO=NOT_CLAIMED
```

CI B 的產品／測試 HEAD `e0b77857eb77536329f9565bf65fa8087b73873d` 已由遠端 [run 39785111593](https://github.com/s9008129/Line_backup/actions/runs/39785111593) 讀回：`deterministic` 與 `headed` 兩個 job 均 success。

本報告的 `PASS` 只對所列精確 HEAD 有效。docs HEAD `6a3e02f` 已由 [PR run 39786235147](https://github.com/s9008129/Line_backup/actions/runs/39786235147) 與 [manual run 39786239965](https://github.com/s9008129/Line_backup/actions/runs/39786239965) 讀回 SUCCESS；任何再新增的 docs commit 仍以自己的 checks 為準。

## 2. 修改範圍與來源

唯一受權產品路徑：

- `.github/workflows/rev28-macos27.yml`
- `tests/build_inspection_fixtures.py`
- `tests/fixtures/project_inspection/seed.json`
- `rev28/Sources/Rev28Core/Composition/ProjectBackupBinding.swift`
- `rev28/Tests/Rev28CoreTests/ProjectBackupBindingTests.swift`
- 本報告與同目錄 `progress.md`

生成 fixture 與 replay／測試 log 只留在未追蹤的暫存路徑，不進 Git。沒有修改 Python producer、native capture、Harness、正式 state／grant／ledger、legacy runtime 或其他無關檔案。

來源 SHA-256：

| 路徑 | SHA-256 |
|---|---|
| `.github/workflows/rev28-macos27.yml` | `4981283493b6d59d05c2ee70178a98e2cd2b4d566b782304296828dfc524d9a7` |
| `tests/build_inspection_fixtures.py` | `aab9eeb06ff4de123680966c1e5521637a0cc3cccc87e0d5f69d0841ed203550` |
| `tests/fixtures/project_inspection/seed.json` | `20e82b3b7b6155cb4879c31a7252f6ba6d09176dc6a9f0102e12d14f0343b514` |
| `rev28/Sources/Rev28Core/Composition/ProjectBackupBinding.swift` | `098f4eb5cf48908b24f201a016d7c87910109251e706c73f9887f47ef640d1df` |
| `rev28/Tests/Rev28CoreTests/ProjectBackupBindingTests.swift` | `99c42c5abedcd70b437943303708dc027a8e5712e3b55dc4994d86273e79becb` |

## 3. 實作內容

1. `tests/build_inspection_fixtures.py` 在指定 `--output` 下建立 `eligible`、`verified`、`busy`、`unresolved`、`ambiguous`、`destination` 六組 fixture。每組由當前 checkout 的 `line_backup_acceptance project-preflight` 真正執行並保存 stdout、config、state 與 manifest；沒有手工拼成 PASS report。
2. `tests/fixtures/project_inspection/seed.json` 只含公開合成群組、日期與張數，不含真實群組、人名、照片、歷史證據或個人絕對路徑。
   產生器也要求 seed 恰好列出六個已知 case 各一次，未知或重複 case 在建立／刪除任何目錄前即拒絕。
3. workflow 在 deterministic job 先產生 fixture、設定 `LINE_BACKUP_INSPECTION_FIXTURES`，再跑既有 build／test／adversarial／replay；artifact 加入 sanitized `manifest.json`。觸發 paths 包含 fixture generator、公開 seed 與 inspection consumer 的 Python 來源。
4. Swift producer source set 加入 `manual_archive.py`，維持來源 bytes 聚合與完整 closure 驗證。
5. `manual_archive_match` 必須存在且為真正的 JSON boolean `false`。`true`、缺欄位、字串 `"false"` 與數字 `0` 均 fail closed，不接受寬鬆轉型，也不把 boolean 當成可直接 SKIP 的授權。
6. 新增兩個聚焦負例：producer source set 不得移除 `manual_archive.py`；`manual_archive_match` 不得為 true／缺欄位／錯型。

## 4. 實際執行與結果

本機環境為 macOS 27.0.1（Darwin 27.0.0，arm64）；Python `3.9.6`，Xcode `26.6`，Swift `6.3.3`。公開 fixture 的 workspace 相對位置為：

```text
.tmp-project-inspection/run-20261022T131314Z/
```

私有絕對定位遮罩為：

```text
<WORKTREE>/.tmp-project-inspection/run-20261022T131314Z/
<WORKTREE>/.tmp-ci-evidence/
<WORKTREE>/.tmp-rev28-replay/
```

### 4.1 Fixture 生成

命令：

```bash
python3 tests/build_inspection_fixtures.py \
  --output .tmp-project-inspection/run-20261022T131314Z
```

實際結果：

- 六組全部生成，generator 回報 `status=PASS`、`case_count=6`。
- decisions 逐項為 `PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION`、`SKIP_VERIFIED`、`PROJECT_BUSY`、`BLOCKED_UNRESOLVED`、`AMBIGUOUS_FINGERPRINT`、`BLOCKED_DESTINATION`。
- 每組都由當前 Python producer 輸出，且 generator 驗證 `manual_archive_match=false`。

證據：

- `.tmp-project-inspection/run-20261022T131314Z/manifest.json`
- manifest SHA-256：`304c7b9db0bdb80318dc4c87af803aa2d1ebf711ad5568205062cdd6f42ac023`

### 4.2 聚焦 Swift

命令：

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk \
LINE_BACKUP_INSPECTION_FIXTURES="$PWD/.tmp-project-inspection/run-20261022T131314Z" \
xcrun swift test --package-path rev28 --filter ProjectBackupBindingTests
```

實際結果：`Executed 18 tests, with 0 failures`。

### 4.3 完整非 Vision suite

命令：

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk \
LINE_BACKUP_INSPECTION_FIXTURES="$PWD/.tmp-project-inspection/run-20261022T131314Z" \
xcrun swift test --package-path rev28 --skip OcrEngineTests
```

實際結果：`Executed 330 tests, with 0 failures`。log SHA-256：`9913f41ba6ccc4e8bcc3f88407785a848079d2971b3bdcd488880cdbc1e929de`。

### 4.4 Adversarial matrix 連跑兩次

命令：

```bash
xcrun swift test --package-path rev28 --filter AdversarialMatrixTests
```

實際結果：兩次均為 `Executed 27 tests, with 0 failures`。log SHA-256 分別為 `73af5eea46e167d594e3bec3825db0f78ac2906a065d7b191d22f7a632fcbe54`、`95c6cf9783862bd6b95d444733aa07ef3f5705f5bf7fa216debc9397a7c352a3`。

### 4.5 Historical replay

命令：

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk
env PATH="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:$PATH" \
  python3 rev28/Tools/replay_rev28.py --root . --output .tmp-rev28-replay/final-run-1.json
env PATH="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:$PATH" \
  python3 rev28/Tools/replay_rev28.py --root . --output .tmp-rev28-replay/final-run-2.json
cmp .tmp-rev28-replay/final-run-1.json .tmp-rev28-replay/final-run-2.json
```

實際結果：

- 兩次 replay 均 `verdict=PASS`、`fixture_count=20`、`failures=[]`。
- `save_all_locator=candidate`、`album_card_locator=candidate`。
- 兩份 JSON byte-identical，SHA-256 均為 `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261`。

### 4.6 遠端 CI B 精確 HEAD

[run 39785111593](https://github.com/s9008129/Line_backup/actions/runs/39785111593) 綁定 `e0b77857eb77536329f9565bf65fa8087b73873d`，`status=completed`、`conclusion=success`：

| Job | 實際結果 |
|---|---|
| `Deterministic Swift contract` | SUCCESS，3m6s；fixture 6/6、330/330、adversarial 27×2、replay 20/20 |
| `Headed macOS 27 capability + W2 item 5` | SUCCESS，1m50s；AX／screen／post event capability、SCK=OK、W2 item 5 與 bounded Vision limitation enforcement 依設計通過 |

遠端 fixture manifest SHA-256 為 `d4550967e48ef3f594cdd89de7a31abb40f974abbd1420fb12bceb3b9ad221b6`；`rev28-host.txt` 顯示 macOS 27.0.1、Xcode 27.0、Swift 6.4、SDK macOS 27.0。遠端 replay artifact 的兩份 JSON SHA-256 均為 `81f6da94ad18d601a21bf0b521d5a96869f13b5a0a3e96db66239b2f90a47261`，與本機一致。

Headed job 的 Vision parity diagnostic 實際是 `Executed 5 tests, with 5 failures`；該 diagnostic 以 `continue-on-error` 保留 Apple hosted Vision `ERROR/unknownError` 限制，再由 `Enforce bounded hosted Vision limitation` 驗證，不能把 5 個失敗測試寫成 PASS。W2 item 5 的實際輸出為 `PASS`，`monitorPosts=0`、`maxLatencyMs=67.047119140625`。

下載後的遠端證據 SHA-256：

- `rev28-project-inspection/manifest.json`：`d4550967e48ef3f594cdd89de7a31abb40f974abbd1420fb12bceb3b9ad221b6`
- `rev28-host.txt`：`a6adebd27e4617ecc1cd62f616d46d71853bcb862476868427eada3bbfb96f1e`
- deterministic job log：`8ee5e261e6a70e48ac982c16cfde5c53a73104ae64219e51fb6aa0d8dc4e562f`
- headed job log：`ce797de32c88f6a4ac61fb7542df29771993b1a32683aaa6ce9a168808436c51`

## 5. 嘗試歷史與環境挫折

第一次 replay 使用 Xcode toolchain PATH，但沒有固定 `SDKROOT`，得到三個 failure：Swift manifest compilation 失敗，以及兩個依賴 production replay 的 locator disagreement。錯誤顯示 SwiftPM 選到 `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`；該 SDK 由 Swift 6.4 建置，與目前 Swift 6.3.3 compiler 不相容。

這不是產品程式反例，也不是 replay 檢查應被放寬的訊號。保留失敗輸出後，只固定 `DEVELOPER_DIR`、`SDKROOT` 與 Xcode toolchain PATH 重跑；沒有修改 replay tool、測試、契約或降低檢查。失敗 JSON SHA-256 為 `104296c7edc84f1ea53190e700042fe37b0568701f4d04c9baac13b0b53deaac`。

## 6. 狀態前後、副作用與未執行項

- 狀態前：CI B 尚無 portable fixture／env；Swift source set 缺 `manual_archive.py`；`manual_archive_match` 未與 producer 契約同步。
- 狀態後：上述五個受權產品路徑已有本機 PASS；git tracked 變更之外只產生 `.tmp-*` 暫存 fixture／log／replay。
- GUI observations／inputs／Save All／Chooser／downloads：0。
- 真實 LINE、真實照片、正式 state／grant／ledger、protected runtime：未取得、未修改。
- 遠端 CI B：產品／測試 HEAD `e0b7785` 的 run 39785111593 全部 success；PR #33 仍為 Draft，報告 docs-only follow-up 仍需自己的 checks。
- External Code Review：NOT_RUN。
- 獨立 DeepSeek `deepseek-v4.1-flash:1017` 兩本相簿 E2E：NOT_RUN。

## 7. 下一個安全動作

CI B 產品／測試 HEAD `e0b7785` 與 PR #33 已建立並取得遠端全綠；report docs HEAD `6a3e02f` 的 PR／manual runs 也已 SUCCESS。下一步是把 feature PR #32 與 PR #33 的 exact HEAD、diff、報告及全部 PASS／FAIL／NOT_RUN 交 Owner 轉交外部 ChatGPT Code Review。在取得真實 `APPROVE_IMPLEMENTATION`、有效 runtime authorization 與當次 LINE 前景交接前，不得宣稱 `FORMAL_TWO_ALBUM_AUTO` 或整體 DONE。
