# 實作交付：記事本 CUA 原件保存範例

## 授權、範圍與版本

本輪依 Owner 指定的 Implementer Prompt 執行 [handoff.md](handoff.md) 所述 replan S1。Owner 已明示本計畫不需要獨立審查；本報告只記錄實作者完成的有限切片與自檢證據，不簽發 Acceptance、Simplicity Review 或獨立 PASS。

Repo／worktree 為 `/Users/hsiaojohnny/dev/Line_backup`，分支 `feature/line-notes-media`。起始 HEAD 為 `09a28b266204319603d7de876f39b223e1696c1b`，其祖先 `9dbd5a906754f32246f6a66ac336afa67b8d63d6` 是 replan 交付版本。含本報告的提交是 S1 最終候選；精確 commit 與遠端 HEAD 以交付時的 `git show`、`git ls-remote` 收據及最終回覆為準。

核定計畫 SHA-256 為 `7f07148f4787bc2943468714ee621916b2d7f57f8d2322f13f703b3164686cf4`；本 handoff SHA-256 為 `b024b05eb0f00c4446e27f6278bcc2fd09ce745874f3a09a7a6451e0981c98e4`。實作前後核對的產品來源如下：

| 路徑 | 實作前 SHA-256 | 實作後 SHA-256 |
|---|---|---|
| `.agents/skills/line-notes-agent-cua/SKILL.md` | `633824c00a5692dab87d3f2cfc03d1f08ec502d38a8ee8321b7c6f22b1408511` | 同左 |
| `.agents/skills/line-notes-agent-cua/references/evidence-template.md` | `04e64a88e0aceb897b864757bf4a95aa70e168f0f7e6eb63662b8a0b5c8db974` | `018c5a0f4664772fe329ff2ed4000d2da60e89d964d7b10603e0c6deb1de03ae` |
| `.agents/skills/line-notes-agent-cua/references/gui-inventory.md` | `c9ae089352825198519ca03e167ee5c49aec7e750c5f88a6497e319994b6651d` | 同左 |
| `.agents/skills/line-notes-agent-cua/references/download-and-ledger.md` | `6238e5fe26b67b17518c3c973b82fa66ed86eeb4c5d13317a36caad8495fc365` | 同左 |

既存未追蹤 `issue提交單.md` 未讀正文、未 stage、未修改；其他 tracked dirty 在實作前不存在。未修改 `src/`、Python tests、CLI／事件 schema、相簿流程、正式 Prompt、AGENTS、真實帳本、active hint、照片或 LINE 資料。

## 修改與原因

唯一產品修改為 [`evidence-template.md`](../../../../.agents/skills/line-notes-agent-cua/references/evidence-template.md)：+301／-31 行。`gui-inventory.md` 經核對後維持不變；既有證據範本入口已足以定位，沒有必要為補連結增加同一輪的額外文件變更。

### 1. 可靠辨識 bytes 並複製精確 view

- 範例明示匯入 `node:buffer` 與 `node:util`，以 `util.types.isUint8Array` 取代會漏接 Buffer／跨 realm Uint8Array 的 `instanceof Uint8Array`。
- `copyExactUint8Array` 只接受真正的 uint8 view；使用 `Buffer.allocUnsafe(value.byteLength)` 與 `byteOffset`／`byteLength` 複製 view 的精確範圍，不把整個 backing buffer 當成影像。
- 字串、Array、DataView、Uint16Array、constructor 名稱偽裝與任意 array-like 均不會被當成 bytes。這個修正直接對應已證實的 162,388-byte Buffer 被舊 predicate 錯拒，不是要求 Owner 修復 CUA。

### 2. 失敗階段可判別，部分原件可保存

- `stages` 分開記錄 `OBSERVATION_ID`、`PRIVATE_PATHS`、`CAPTURE`、`CAPTURE_SHAPE`、`AX`、`SCREENSHOT_TYPE`、`SCREENSHOT_LENGTH` 及各 asset 的 persistence。
- AX 合格但截圖缺失、型別錯、空值或寫入失敗時，合格 AX 仍可保存；反向情況亦然。失敗會留下 diagnostic metadata 與適用的部分原件。
- 只有 AX 與非空截圖都存在、兩者都以 `wx` 寫入並逐 bytes 讀回 MATCH，且 diagnostic 也寫入／讀回 MATCH，runtime 輸出的 `ready_for_bind` 才是 `true`。任何 blocker 都不會進入 bind。
- 未實測的 `regions` 形狀會保存可用部分並回報 `UNSUPPORTED_REGIONS`，不建立泛用 adapter、不猜測多截圖映射。

### 3. 私有路徑、不可覆寫與逐 bytes 讀回

- `TASK_PRIVATE_DIR`、`OBSERVATION_DIR` 與 `OBSERVATION_ID` 都在終端機先核對；範例拒絕 non-canonical 路徑、observation directory 跑出 task directory、以及含路徑穿越字元的 ID。
- 每個 asset 與 diagnostic 使用 `flag: 'wx'`、`mode: 0o600`，既有檔名碰撞不覆寫，也不是重試成功訊號。
- 寫入後重新讀取檔案，逐 bytes 比對長度與 SHA-256；寫入或讀回失敗不會被記成 MATCH。

## 指定委派與模型證據

Owner 要求以 `model=gpt-6-luna`、`reasoning_effort=high`、`fork_turns=none` 監督原生實作助手。主代理建立了兩個互斥唯讀範圍的 spawn 請求；兩個 session 都在輸入階段回報：

```text
input[0]: unknown input item type: "additional_tools"
```

兩個 turn 的狀態均為 `systemError`，沒有助手回合內容，亦未讀寫檔案、執行 Git 或接觸 LINE／帳本。依專案規則，沒有改用其他模型、`codex exec`、SDK、API 或背景 LLM 繞過；主代理在原授權內接手完成 S1。指定委派因此記為 **未完成**，不能說已由 GPT-6 luna 完成實作。

| 證據層 | 可證明內容 |
|---|---|
| 配置預設 | `NOT_INSPECTED`；沒有以配置推論本次實際模型 |
| 請求參數 | 兩個 spawn 都明示 `gpt-6-luna`、`high`、`fork_context=false` |
| 平台顯示／回傳 | 兩個 session 均為 `systemError`，錯誤為 `unknown input item type: "additional_tools"` |
| Provider 用量 | `UNKNOWN`；未取得 backend 身分、用量或成本 |

## 驗證與結果

所有指令工作目錄均為上述 repo。私有證據位於 `.local/line-backup/tasks/20261112-notes-cua-evidence-s1/`，不提交；公開報告不含原始 AX、截圖、帳本或私人資料。

### 最終範例身分

從最終 Markdown 的標記與 code fence 精確擷取，去除 fence 本身後：

| 項目 | 長度 | SHA-256 |
|---|---:|---|
| helper 程式碼 | 10,226 bytes | `ca16d55c6d0dfb929296a3aedd342c96a3cd634faf45942be17ccd3784d5a973` |
| execution 程式碼 | 363 bytes | `80b122b10ea2ea67153492724e0fb4a0a9e1373bf7cbe8f86cb1ceee82d87b3f` |

`example-block-manifest.json` 另記錄 helper 與 smoke 前 fixture 擷取一致。最後的文件敘述調整沒有改變 helper／execution bytes。

提交前機械核對亦通過：`git diff --check` exit `0`；報告中的三個相對連結都存在；六個來源／交付 hash 與 helper／execution manifest 全部 MATCH；公開報告六項狀態齊備。第一次連結檢查器把 Markdown `#` 錨點誤當檔名的一部分而回報缺檔，修正檢查器後重跑為 0 缺檔；沒有因此修改產品或連結內容。

### 私有離線 fixtures

實際指令：

```sh
node --test --test-reporter=spec .local/line-backup/tasks/20261112-notes-cua-evidence-s1/fixtures/evidence-tools.test.mjs
```

最終執行 exit `0`：13 tests、13 pass、0 fail；stdout／stderr／exit 存在 `fixtures/offline.*`。fixture 直接讀取最終 Markdown 並擷取 helper，沒有另寫相似演算法。涵蓋：

- 本機 Buffer、跨 realm Uint8Array、非零 offset 子視圖及精確 bytes 副本。
- 字串、Array、DataView、Uint16Array、array-like 與 constructor-name 偽裝拒絕。
- AX／截圖的部分原件保存、空值、型別錯、檔案碰撞、寫入失敗與讀回失敗。
- canonical 私有路徑、路徑穿越拒絕，以及未支援 `regions` 時保存可用部分但不 bind。

第一次 fixture 實際執行 exit `1`、12／13 pass；失敗原因是測試以 `notStrictEqual` 比較不同 view 物件，錯誤假設 Node 會共享同一 backing ArrayBuffer。修正 fixture 假設後重跑得到 13／13，產品 helper 未因此修改。另有一次 shell 在測試啟動前因 zsh 的唯讀變數 `status` 中止，沒有執行測試，不記為產品失敗。

### 原生 CUA 唯讀 smoke

直接使用最終 Markdown 的 helper 與 execution 程式碼，在 CUA Node runtime 呼叫一次 `getAXStateAndScreenshot`。執行期間沒有 click、scroll、按鍵、bind、intent、下載、帳本或照片操作。

第一次以字串組合後 `eval` 的方式在 capture 前被 runtime 以 `Code generation from strings disallowed for this context` 拒絕，沒有取得新畫面；之後直接執行 Markdown 的原始程式碼並成功。這是同一次最終範例 smoke 的前置執行方式失敗，不重複 GUI capture，也不換 Session／API。

取得 Observation ID `cua-smoke-20261112T071127Z-a7b2da36-7a43-42cc-8761-d24091927a92`。Runtime 最終輸出為 `ready_for_bind: true`、`blockers: []`；同一輸出另證明：

| Asset | bytes | SHA-256 | 寫入／讀回 | mode |
|---|---:|---|---|---|
| AX | 353 | `88cc970dd73264a9a05cecef3669cfb2610b39d997b6a4806f8c1ccb26534b41` | WRITTEN／MATCH | `0600` |
| Screenshot | 162,388 | `a304059c4f06a03a1526fcada3275f3ac2ac21aa19fe2149ea83806bc1c31c51` | WRITTEN／MATCH | `0600` |
| Diagnostic | 3,038 | `ea02b7e8000019a09721dae1c60812c0ec4c64ad457828522394343d9b2f492a` | WRITTEN／MATCH | `0600` |

截圖 signature 為 JPEG 654×1286。`diagnostic.json` 內的 `ready_for_bind: false` 是它在 metadata persistence 完成前寫下的初始快照；runtime 最終輸出才是 `true`，而三個檔案的事後 `stat`／`shasum`／JSON parse 均與 runtime 結果一致，並非 smoke 失敗。原始 AX／JPEG 只留私有 task，公開報告不重製。

### 指定回歸

三條命令各執行一次，原始 stdout／stderr／exit 存在 `regressions/`：

| 實際命令 | Exit | 結果 |
|---|---:|---|
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p test_daily_records.py` | 0 | 73 tests，318.246 秒，OK |
| `PYTHONPATH=src /usr/bin/python3 -B -m line_backup_batch.notes --help` | 0 | 正確輸出 CLI 說明 |
| `PYTHONPATH=src /usr/bin/python3 -B -m unittest discover -s tests -p 'test_notes*.py'` | 0 | 228 tests，32.607 秒，OK |

`03-notes-tests` 的 stderr 含有測試刻意觸發 argparse 錯誤的原文，但 unittest 最終 exit `0`、228 tests OK；不把該預期錯誤文字冒充產品失敗。

## 未測、已知限制與下一步

- S1 只修好 CUA 原始 observation 保存範例；Notes viewer 的實際下載控制 U1 仍是 **UNKNOWN**。沒有證實 chooser、派送、五張照片解碼、completion、影片／混合附件或跨 Session 恢復。
- 沒有讀寫真實帳本、active hint、照片或 LINE 資料，也沒有執行真實下載、獨立 Review 或外部雲端審查。這些均 `NOT_RUN`。
- 指定助手派送失敗是本輪平台輸入錯誤；不能記成助手完成，也不能推論 CUA 或產品缺陷。
- 下一步由 Owner 使用[使用手冊附錄 C](../../../LINE相簿備份_使用手冊.md#附錄-c記事本正式-prompt)的日常正式 Prompt，在真實列表中完成 S2 來源／列表／五張媒體核對，再依當次控制完成單次派送、outcome、逐檔驗證與 completion。S1 成功不代表五張照片完成，也不需要新增開發計畫、內部 JSON 或第二則開始指令。

## 六項狀態

- `PRIMARY_OUTCOME_STATUS: BLOCKED`：指定五張照片仍無下載、驗證與 completion 證據。
- `IMPLEMENTATION_STATUS: COMPLETE`：S1 的範例、私有 fixtures、一次原生 smoke 與三條回歸均有實際證據；只代表本有限切片。
- `CORE_ACCEPTANCE_STATUS: BLOCKED`：缺來源唯一核對、下載與照片 completion。
- `REQUIRED_VERIFICATION_STATUS: PARTIAL`：S1 指定檢查完成；S2／S3、真實 Notes GUI 下載、chooser、五張檔案驗證與 E2E 未執行。
- `INDEPENDENT_ACCEPTANCE_STATUS: NOT_RUN`：Owner 明示本計畫不需要獨立審查，本報告不是獨立接受。
- `TASK_CLOSURE_STATUS: BLOCKED`：S1 產品切片可交付，但照片任務及 U1 未結案。
